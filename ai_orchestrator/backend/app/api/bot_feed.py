"""
API роутер для Telegram-бот данных.
Позволяет дашборду получать реальные сообщения учителей из SQLite.
"""
import json
import sqlite3
import os
from fastapi import APIRouter
from datetime import datetime

from app.db.database import SessionLocal
from app.db.models import TeacherAbsenceEvent, ScheduleEntry, TimeSlot, Class, Room, TaskReminder
from app.ai.llm_parser import parse_with_llm
from app.services.notification_service import build_absence_reply, resolve_whatsapp_target, send_to_school_group
from app.services.scheduler import process_teacher_absence_event

router = APIRouter()

# Ищем orchestrator.db в корне папки backend
_api_dir = os.path.dirname(os.path.abspath(__file__))
_app_dir = os.path.dirname(_api_dir)
_backend_dir = os.path.dirname(_app_dir)
DB_PATH = os.path.join(_backend_dir, "orchestrator.db")
WHATSAPP_AUTO_REPLY_ENABLED = os.getenv("WHATSAPP_AUTO_REPLY_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}



def _get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    # Включаем WAL режим для стабильной одновременной записи
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except:
        pass
    return conn


def _ensure_table():
    try:
        conn = _get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tg_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                sender TEXT,
                text TEXT,
                parsed_type TEXT,
                parsed_summary TEXT,
                food_class TEXT,
                food_count INTEGER,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.commit()

        # Авто-миграции: добавляем колонки, которые могут отсутствовать в старой БД
        for col, col_type in [
            ("chat_id", "INTEGER"),
            ("parsed_type", "TEXT"),
            ("parsed_summary", "TEXT"),
            ("food_class", "TEXT"),
            ("food_count", "INTEGER"),
            ("location", "TEXT"),
            ("parsed_confidence", "REAL"),
            ("parsed_payload", "TEXT"),
            ("review_status", "TEXT"),
        ]:
            try:
                conn.execute(f"ALTER TABLE tg_messages ADD COLUMN {col} {col_type}")
                conn.commit()
                print(f"✅ Миграция: добавлена колонка tg_messages.{col}")
            except Exception:
                pass  # Колонка уже существует — это нормально

        conn.close()
    except Exception:
        pass


import re
from pydantic import BaseModel

class WhatsAppWebhookReq(BaseModel):
    sender: str
    text: str
    source: str
    chatId: str

def _extract_food_info(text):
    class_match = re.search(r"(\d+[АаБбВвГг])", text, re.IGNORECASE)
    count_match = re.search(r"(\d+)\s*(детей|ребёнка|ребенка|человек|учеников|порций)", text, re.IGNORECASE)
    food_class = class_match.group(1).upper() if class_match else None
    food_count = int(count_match.group(1)) if count_match else None
    return food_class, food_count

def _extract_location(text):
    """Извлекает локацию/кабинет из текста с учётом аббревиатур и именованных мест."""
    t = text.lower().strip()
    
    # 1. "кабинет фм 201", "каб фм201", "комната 10", "кабинет 201" — с необязательной аббревиатурой
    m = re.search(
        r"(?:каб(?:инет)?\.?|комнат[аыеу]?)\s*([а-яa-z]{1,4}\s*)?\s*(\d{1,3}[а-яa-z]?)",
        t, re.IGNORECASE
    )
    if m:
        prefix = (m.group(1) or "").strip().upper()
        room = m.group(2).strip()
        return f"{prefix} {room}".strip() if prefix else f"Каб./Комн. {room}"
    
    # 2. "в кабинете 201", "в 201 кабинете", "в 10 комнате"
    m = re.search(r"(?:в|на)\s+(\d{1,3})\s*(?:каб|кабинет|офис|аудитор|класс|комнат[аыеу])", t, re.IGNORECASE)
    if m:
        return f"Каб./Комн. {m.group(1)}"
    
    # 3. Именованные локации: библиотека, спортзал, актовый зал, столовая, и т.д.
    named = re.search(
        r"(?:в|на)\s+(библиотек\w*|спортзал\w*|актов\w+\s*зал\w*|столов\w*|медпункт\w*|учительск\w*|холл\w*|коридор\w*|склад\w*|фойе\w*)",
        t, re.IGNORECASE
    )
    if named:
        loc = named.group(1).strip()
        # Приводим к именительному падежу (простая нормализация)
        loc = re.sub(r"е$", "", loc)  # библиотеке -> библиотек -> Библиотека
        return loc.capitalize()
    
    return None

def _local_classify(text):
    t = text.lower()
    food_class, food_count = _extract_food_info(text)
    if food_class or food_count or any(w in t for w in ["детей", "ребёнок", "порций", "столовая"]):
        return "food", f"Явка: {food_count or '?'} чел." + (f" ({food_class})" if food_class else ""), food_class, food_count
    if any(w in t for w in ["заболел", "болеет", "не придёт", "не придет", "нетрудоспособ"]):
        return "absence", f"Отсутствие, требуется замена: {text[:60]}", None, None
    # Медицинский случай (приоритет выше обычного инцидента)
    if any(w in t for w in ["плохо", "упал", "упала", "без сознания", "рвота", "температура", "травм", "скорую", "медик"]):
        return "medical", f"🚑 Медицинский случай: {text[:80]}", None, None
    if any(w in t for w in ["сломал", "поломка", "не работает", "протечка", "авария", "драка", "конфликт", "принтер", "проектор"]):
        return "incident", f"Инцидент: {text[:80]}", None, None
    return "other", text[:100], None, None

def _detect_recurrence(text: str) -> str:
    """
    Returns 'recurring' if the text implies a repeated/scheduled task,
    or 'spontaneous' for one-off requests.
    """
    t = text.lower()
    recurring_keywords = [
        "раз в", "ежедневно", "еженедельно", "ежемесячно", "каждый день",
        "каждую неделю", "каждый месяц", "по понедельникам", "по вторникам",
        "по средам", "по четвергам", "по пятницам", "регулярно",
        "weekly", "daily", "monthly", "по графику", "по расписанию", "по плану",
        "постоянно", "всегда", "always",
    ]
    for kw in recurring_keywords:
        if kw in t:
            return "recurring"
    return "spontaneous"

def _send_wa_reply(chat_id: str, text: str):
    """Отправляет авто-ответ в WhatsApp через локальный bridge (порт 3000)."""
    import urllib.request, json
    if not WHATSAPP_AUTO_REPLY_ENABLED:
        print("[AutoReply] skipped: WHATSAPP_AUTO_REPLY_ENABLED is false")
        return
    try:
        target_chat_id = resolve_whatsapp_target(chat_id)
        payload = json.dumps({"chatId": target_chat_id, "text": text}).encode('utf-8')
        req = urllib.request.Request("http://localhost:3000/send", data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=2):
            pass
    except Exception as e:
        print(f"[AutoReply] Не удалось отправить: {e}")

def _resolved_assignee(parsed) -> str:
    return parsed.assignee or parsed.assignee_role or "Нераспознанный сотрудник"


def _queue_manual_review(conn, req: WhatsAppWebhookReq, parsed, summary: str):
    review_reason = parsed.review_reason or "manual_review_required"
    conn.execute(
        "INSERT INTO task_reminders (title, assignee, deadline, is_accepted, is_completed) VALUES (?, ?, ?, ?, ?)",
        (
            f"Проверить сообщение из WhatsApp: {summary[:80]}",
            "Завуч",
            "Сейчас",
            0,
            0,
        ),
    )
    _send_wa_reply(
        req.chatId,
        "Aqbobek AI: сообщение получено, но требует подтверждения администратора. "
        f"Причина: {review_reason}. После проверки задача появится в системе.",
    )


# Global state for WA authentication
wa_auth_state = {
    "status": "pending",  # pending, qr, ready, error
    "qr_data": None
}

from typing import Optional

class WhatsAppAuthReq(BaseModel):
    status: str
    qr_data: Optional[str] = None

@router.post("/whatsapp-auth")
def update_whatsapp_auth(req: WhatsAppAuthReq):
    """Обновляет состояние авторизации WhatsApp из Node.js клиента."""
    wa_auth_state["status"] = req.status
    wa_auth_state["qr_data"] = req.qr_data
    return {"ok": True}

@router.get("/whatsapp-auth-status")
def get_whatsapp_auth_status():
    """Фронтенд опрашивает этот эндпоинт для показа QR-кода."""
    return wa_auth_state

@router.post("/whatsapp-webhook")
def whatsapp_webhook(req: WhatsAppWebhookReq):
    """Принимает сообщения от реального WhatsApp и вставляет в ту же базу."""
    _ensure_table()
    parsed = parse_with_llm(req.text, sender=req.sender)

    # Фильтр: нерелевантные сообщения не попадают на дашборд
    if not parsed.school_relevant and parsed.type == "other" and not parsed.is_acceptance:
        print(f"[Filter] Нерелевантное сообщение от {req.sender}: {req.text[:60]}")
        return {"status": "filtered", "reason": "not_school_relevant"}

    raw_type = parsed.type
    stored_type = "other" if raw_type == "task" or parsed.is_acceptance else raw_type
    task_subtype = parsed.recurrence or _detect_recurrence(req.text)
    summary = parsed.summary
    if raw_type == "task" and not parsed.is_acceptance:
        summary = f"[{task_subtype}] {parsed.task_title or parsed.summary}"

    food_class = parsed.class_name
    food_count = parsed.food_count
    location = parsed.location or _extract_location(req.text)
    payload_json = json.dumps(parsed.model_dump(), ensure_ascii=False)
    review_status = "needs_review" if parsed.requires_review else "approved"

    # Показываем только суть — clean_text если есть, иначе summary, НЕ сырой текст
    display_text = parsed.clean_text or parsed.summary or req.text[:120]

    try:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO tg_messages
               (chat_id, sender, text, parsed_type, parsed_summary, food_class, food_count, location, parsed_confidence, parsed_payload, review_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                req.chatId,
                req.sender,
                display_text,
                stored_type,
                summary,
                food_class,
                food_count,
                location,
                parsed.confidence,
                payload_json,
                review_status,
            ),
        )

        if parsed.is_acceptance:
            search_sender = f"%{req.sender}%"
            cursor = conn.execute(
                """UPDATE task_reminders
                   SET is_accepted = 1
                   WHERE is_completed = 0 AND is_accepted = 0
                   AND (assignee LIKE ? OR ? LIKE '%' || assignee || '%')
                   AND id = (
                       SELECT id FROM task_reminders
                       WHERE is_completed = 0 AND is_accepted = 0
                       AND (assignee LIKE ? OR ? LIKE '%' || assignee || '%')
                       ORDER BY id DESC LIMIT 1
                   )""",
                (search_sender, req.sender, search_sender, req.sender),
            )
            if cursor.rowcount == 0:
                conn.execute(
                    """UPDATE task_reminders
                       SET is_accepted = 1, assignee = ?
                       WHERE is_completed = 0 AND is_accepted = 0
                       AND (assignee LIKE '%РќРµСЂР°СЃРїРѕР·РЅР°РЅРЅС‹Р№%' OR assignee LIKE '%РќРµРёР·РІРµСЃС‚РЅРѕ%' OR assignee = '')
                       AND id = (
                           SELECT id FROM task_reminders
                           WHERE is_completed = 0 AND is_accepted = 0
                           AND (assignee LIKE '%РќРµСЂР°СЃРїРѕР·РЅР°РЅРЅС‹Р№%' OR assignee LIKE '%РќРµРёР·РІРµСЃС‚РЅРѕ%' OR assignee = '')
                           ORDER BY id DESC LIMIT 1
                       )""",
                    (req.sender,),
                )
            conn.commit()
            conn.close()
            return {"status": "ok", "parsed_type": "acceptance", "confidence": parsed.confidence}

        if parsed.requires_review and raw_type in {"task", "incident", "absence"}:
            _queue_manual_review(conn, req, parsed, summary)
            conn.commit()
            conn.close()
            return {
                "status": "review_required",
                "parsed_type": stored_type,
                "confidence": parsed.confidence,
                "analysis": parsed.model_dump(),
            }

        if raw_type == "medical":
            loc_str = f" ({location})" if location else ""
            msg = f"🚑 *Медицинский случай{loc_str}*\n{parsed.summary}\nТребуется немедленное внимание администрации."
            _send_wa_reply(req.chatId, msg)
            send_to_school_group(msg)

        elif raw_type == "incident":
            assignee = _resolved_assignee(parsed)
            deadline = parsed.deadline or "Срочно"
            task_title = parsed.task_title or parsed.issue or parsed.summary
            conn.execute(
                "INSERT INTO task_reminders (title, assignee, deadline, is_accepted, is_completed) VALUES (?, ?, ?, ?, ?)",
                (task_title, assignee, deadline, 0, 0),
            )
            loc_str = f" ({location})" if location else ""
            msg = f"🔧 *Инцидент{loc_str}*\n{parsed.summary}\nИсполнитель: *{assignee}*. Срок: {deadline}."
            _send_wa_reply(req.chatId, msg)
            send_to_school_group(msg)

        elif raw_type == "absence":
            db = SessionLocal()
            try:
                absence_result = process_teacher_absence_event(
                    teacher_name=parsed.teacher_name or req.sender,
                    reason="whatsapp_absence",
                    source="whatsapp",
                    raw_message=req.text,
                    db=db,
                )
            finally:
                db.close()

            reply = build_absence_reply(
                teacher_name=absence_result.get("teacher_name", parsed.teacher_name or req.sender),
                day=absence_result.get("day", "сегодня"),
                substitutions_count=absence_result.get("substitutions_count", 0),
                unresolved_count=absence_result.get("unresolved_count", 0),
            )
            # Групповое уведомление уже отправляется внутри process_teacher_absence_event
            _send_wa_reply(req.chatId, reply)

        elif raw_type == "task" or (stored_type == "other" and (parsed.assignee or parsed.task_title)):
            assignee = _resolved_assignee(parsed)
            deadline = parsed.deadline or "В течение дня"
            task_title = parsed.task_title or req.text.strip()
            conn.execute(
                "INSERT INTO task_reminders (title, assignee, deadline, is_accepted, is_completed) VALUES (?, ?, ?, ?, ?)",
                (task_title, assignee, deadline, 0, 0),
            )
            subtype_label = "🔁 Цикличная" if task_subtype == "recurring" else "⚡ Разовая"
            msg = f"📋 *Новая задача [{subtype_label}]*\nИсполнитель: *{assignee}*\nСрок: {deadline}\n{task_title}"
            _send_wa_reply(req.chatId, msg)
            send_to_school_group(msg)

        conn.commit()
        conn.close()
        return {
            "status": "ok",
            "parsed_type": stored_type,
            "confidence": parsed.confidence,
            "analysis": parsed.model_dump(),
        }
    except Exception as e:
        print(f"[Webhook LLM Flow] {e}")
        return {"status": "error", "message": str(e)}

    mtype, summary, food_class, food_count = _local_classify(req.text)
    location = _extract_location(req.text)

    # ─── ЛОГИКА ПОДТВЕРЖДЕНИЯ (Acceptance) ───
    confirm_keywords = ["принял", "оке", "ок", "готов", "сделаю", "хорошо", "+", "понял", "взял", "поняла", "взяла", "оки"]
    is_confirmation = any(k == req.text.lower().strip() or f" {k} " in f" {req.text.lower()} " for k in confirm_keywords)
    
    try:
        conn = _get_conn()
        
        # 1. Сохраняем в лог
        conn.execute(
            """INSERT INTO tg_messages 
               (chat_id, sender, text, parsed_type, parsed_summary, food_class, food_count, location) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (req.chatId, req.sender, f"[WA] {req.text}", mtype, summary, food_class, food_count, location)
        )

        # 2. Авто-ответ для инцидентов и медицинских случаев
        if mtype == "medical":
            loc_str = f" (каб. {location})" if location else ""
            reply = (
                f"🚑 *Медицинский случай зафиксирован{loc_str}!*\n"
                f"Описание: {req.text[:80]}\n"
                f"📌 Дашборд уведомлён. Вызовите медработника!"
            )
            _send_wa_reply(req.chatId, reply)
        elif mtype == "incident":
            loc_str = f" ({location})" if location else ""
            reply = (
                f"🔧 *Aqbobek AI: инцидент зафиксирован{loc_str}!*\n"
                f"{summary}\n"
                f"Назначен: Завхоз.\nОжидайте, специалист уже в пути."
            )
            _send_wa_reply(req.chatId, reply)
            # Автоматически создаём задачу для завхоза
            try:
                conn.execute(
                    "INSERT INTO task_reminders (title, assignee, deadline, is_accepted, is_completed) VALUES (?, ?, ?, ?, ?)",
                    (f"Инцидент: {summary}", "Серик", "Срочно", 0, 0)
                )
            except Exception as _te:
                print(f"[Task] Не удалось создать задачу: {_te}")
        elif mtype == "absence":
            db = SessionLocal()
            try:
                absence_result = process_teacher_absence_event(
                    teacher_name=req.sender,
                    reason="whatsapp_absence",
                    source="whatsapp",
                    raw_message=req.text,
                    db=db,
                )
            finally:
                db.close()

            reply = build_absence_reply(
                teacher_name=absence_result.get("teacher_name", req.sender),
                day=absence_result.get("day", "сегодня"),
                substitutions_count=absence_result.get("substitutions_count", 0),
                unresolved_count=absence_result.get("unresolved_count", 0),
            )
            _send_wa_reply(req.chatId, reply)
        elif mtype == "other" and not is_confirmation:
            loc_str = location if location else "Не указано"
            priority = "high" if "срочно" in req.text.lower() else "medium"
            task_subtype = _detect_recurrence(req.text)
            subtype_label = "🔁 Цикличная" if task_subtype == "recurring" else "⚡ Разовая"
            reply = (
                f"Aqbobek AI: задача создана. [{subtype_label}]\n"
                f"{req.text.strip()}\n"
                f"Место: {loc_str}\n"
                f"Приоритет: {priority}."
            )
            # Store subtype in parsed_summary for frontend filtering
            summary = f"[{task_subtype}] {req.text[:80]}"
            _send_wa_reply(req.chatId, reply)
        if is_confirmation:
            search_sender = f"%{req.sender}%"
            cursor = conn.execute(
                """UPDATE task_reminders 
                   SET is_accepted = 1 
                   WHERE is_completed = 0 AND is_accepted = 0 
                   AND (assignee LIKE ? OR ? LIKE '%' || assignee || '%')
                   AND id = (
                       SELECT id FROM task_reminders 
                       WHERE is_completed = 0 AND is_accepted = 0 
                       AND (assignee LIKE ? OR ? LIKE '%' || assignee || '%')
                       ORDER BY id DESC LIMIT 1
                   )""",
                (search_sender, req.sender, search_sender, req.sender)
            )
            if cursor.rowcount == 0:
                conn.execute(
                    """UPDATE task_reminders 
                       SET is_accepted = 1, assignee = ? 
                       WHERE is_completed = 0 AND is_accepted = 0 
                       AND (assignee LIKE '%Нераспознанный%' OR assignee LIKE '%Неизвестно%' OR assignee = '')
                       AND id = (
                           SELECT id FROM task_reminders 
                           WHERE is_completed = 0 AND is_accepted = 0 
                           AND (assignee LIKE '%Нераспознанный%' OR assignee LIKE '%Неизвестно%' OR assignee = '')
                           ORDER BY id DESC LIMIT 1
                       )""",
                    (req.sender,)
                )
                print(f"✨ Задача самоназначена на {req.sender} (была нераспознана).")
            else:
                print(f"✅ Задача для {req.sender} помечена как Принятая.")

        conn.commit()
        conn.close()
        return {"status": "ok", "parsed_type": "acceptance" if is_confirmation else mtype}
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/messages")
def get_bot_messages(limit: int = 50):
    """Последние сообщения от учителей — дедупликация по (sender, parsed_type)."""
    _ensure_table()
    try:
        conn = _get_conn()
        # Берём последнее сообщение от каждого отправителя по каждому типу
        rows = conn.execute(
            """SELECT id, sender, text, parsed_type, parsed_summary, food_class, food_count,
                      created_at, parsed_confidence, parsed_payload, review_status
               FROM tg_messages
               WHERE id IN (
                   SELECT MAX(id) FROM tg_messages
                   GROUP BY sender, parsed_type
               )
               ORDER BY id DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        conn.close()
        result = []
        for row in reversed(rows):
            item = dict(row)
            payload = item.get("parsed_payload")
            if payload:
                try:
                    item["parsed_payload"] = json.loads(payload)
                except Exception:
                    pass
            result.append(item)
        return result
    except Exception as e:
        return []

@router.delete("/clear")
def clear_feed():
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM tg_messages")
        conn.commit()
        conn.close()
        return {"status": "ok", "message": "Feed cleared"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/svod")
def get_food_svod():
    """Сводка по питанию за сегодня."""
    _ensure_table()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = _get_conn()
        rows = conn.execute(
            "SELECT food_class, food_count FROM tg_messages "
            "WHERE parsed_type='food' AND date(created_at)=?",
            (today,)
        ).fetchall()
        incidents = conn.execute(
            "SELECT COUNT(*) as cnt FROM tg_messages "
            "WHERE parsed_type='incident' AND date(created_at)=?",
            (today,)
        ).fetchone()
        absences = conn.execute(
            "SELECT COUNT(*) as cnt FROM tg_messages "
            "WHERE parsed_type='absence' AND date(created_at)=?",
            (today,)
        ).fetchone()
        conn.close()

        total = sum(r["food_count"] for r in rows if r["food_count"])
        classes = {r["food_class"]: r["food_count"] for r in rows if r["food_class"]}
        return {
            "total_portions": total,
            "report_count": len(rows),
            "classes": classes,
            "incidents_today": incidents["cnt"] if incidents else 0,
            "absences_today": absences["cnt"] if absences else 0,
            "date": today,
        }
    except Exception as e:
        return {"total_portions": 0, "report_count": 0, "classes": {}, "incidents_today": 0, "absences_today": 0}


@router.get("/ops-summary")
def get_ops_summary(limit: int = 6):
    """Оперативная сводка для главной панели директора."""
    _ensure_table()
    db = SessionLocal()
    try:
        raw_events = (
            db.query(TeacherAbsenceEvent)
            .order_by(TeacherAbsenceEvent.created_at.desc(), TeacherAbsenceEvent.id.desc())
            .limit(limit * 4)
            .all()
        )

        recent_events = []
        seen_pairs = set()
        for event in raw_events:
            key = (event.teacher_id, event.day)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            recent_events.append(event)
            if len(recent_events) >= limit:
                break

        absences = []
        total_substitutions = 0
        total_unresolved = 0

        for event in recent_events:
            substitution_entries = (
                db.query(ScheduleEntry, TimeSlot, Class, Room)
                .join(TimeSlot, ScheduleEntry.time_slot_id == TimeSlot.id)
                .outerjoin(Class, ScheduleEntry.class_id == Class.id)
                .outerjoin(Room, ScheduleEntry.room_id == Room.id)
                .filter(
                    ScheduleEntry.original_teacher_id == event.teacher_id,
                    ScheduleEntry.is_substitution == True,
                    TimeSlot.day == event.day,
                )
                .order_by(TimeSlot.lesson_number)
                .all()
            )

            unresolved_entries = []
            if (event.unresolved_count or 0) > 0:
                unresolved_entries = (
                    db.query(ScheduleEntry, TimeSlot, Class, Room)
                    .join(TimeSlot, ScheduleEntry.time_slot_id == TimeSlot.id)
                    .outerjoin(Class, ScheduleEntry.class_id == Class.id)
                    .outerjoin(Room, ScheduleEntry.room_id == Room.id)
                    .filter(
                        ScheduleEntry.teacher_id == event.teacher_id,
                        TimeSlot.day == event.day,
                        ScheduleEntry.is_substitution == False,
                    )
                    .order_by(TimeSlot.lesson_number)
                    .all()
                )

            substitutions_preview = []
            for entry, slot, class_obj, room_obj in substitution_entries[:3]:
                substitutions_preview.append(
                    {
                        "lesson_number": slot.lesson_number,
                        "class_name": class_obj.name if class_obj else "—",
                        "room": room_obj.number if room_obj else "—",
                        "subject": entry.subject,
                    }
                )

            if not substitutions_preview and (event.substitutions_count or 0) > 0:
                substitutions_preview.append(
                    {
                        "lesson_number": 0,
                        "class_name": f"{event.substitutions_count} слот(а)",
                        "room": "назначено",
                        "subject": "Замена проведена",
                    }
                )

            unresolved_preview = []
            for entry, slot, class_obj, room_obj in unresolved_entries[:3]:
                unresolved_preview.append(
                    {
                        "lesson_number": slot.lesson_number,
                        "class_name": class_obj.name if class_obj else "—",
                        "room": room_obj.number if room_obj else "—",
                        "subject": entry.subject,
                    }
                )

            if not unresolved_preview and (event.unresolved_count or 0) > 0:
                unresolved_preview.append(
                    {
                        "lesson_number": 0,
                        "class_name": f"{event.unresolved_count} слот(а)",
                        "room": "требует решения",
                        "subject": "Ручная обработка",
                    }
                )

            total_substitutions += event.substitutions_count or 0
            total_unresolved += event.unresolved_count or 0
            absences.append(
                {
                    "event_id": event.id,
                    "teacher_name": event.teacher.short_name or event.teacher.full_name if event.teacher else "Неизвестно",
                    "day": event.day,
                    "status": event.status,
                    "reason": event.reason,
                    "source": event.source,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                    "substitutions_count": event.substitutions_count or 0,
                    "unresolved_count": event.unresolved_count or 0,
                    "substitutions_preview": substitutions_preview,
                    "unresolved_preview": unresolved_preview,
                }
            )

        pending_tasks = (
            db.query(TaskReminder)
            .filter(TaskReminder.is_completed == False)
            .order_by(TaskReminder.id.desc())
            .limit(5)
            .all()
        )

        pending_incidents = sum(1 for task in pending_tasks if "инцидент" in (task.title or "").lower())

        return {
            "totals": {
                "absent_teachers": len(absences),
                "substitutions_found": total_substitutions,
                "unresolved_slots": total_unresolved,
                "pending_tasks": len(pending_tasks),
                "pending_incidents": pending_incidents,
            },
            "absences": absences,
            "pending_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "assignee": task.assignee,
                    "deadline": task.deadline,
                    "is_accepted": task.is_accepted,
                }
                for task in pending_tasks
            ],
        }
    except Exception as e:
        return {
            "totals": {
                "absent_teachers": 0,
                "substitutions_found": 0,
                "unresolved_slots": 0,
                "pending_tasks": 0,
                "pending_incidents": 0,
            },
            "absences": [],
            "pending_tasks": [],
            "error": str(e),
        }
    finally:
        db.close()


@router.post("/send-food-report")
def send_food_report():
    """Отправляет свод питания в столовую (симуляция)."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = _get_conn()
        rows = conn.execute(
            "SELECT food_class, food_count FROM tg_messages "
            "WHERE parsed_type='food' AND date(created_at)=?",
            (today,)
        ).fetchall()
        conn.close()
        total = sum(r["food_count"] for r in rows if r["food_count"])
        classes = {r["food_class"]: r["food_count"] for r in rows if r["food_class"]}
        sent_at = datetime.now().isoformat()
        print(f"[СТОЛОВАЯ] Отправлен свод: {total} порций в {sent_at}")
        return {"sent": True, "report": {"total_portions": total, "classes": classes, "date": today}, "sent_at": sent_at}
    except Exception as e:
        return {"sent": False, "error": str(e)}


from fastapi import BackgroundTasks
import time as _time

def _run_demo_scenario():
    """Засеивает базу цепочкой реалистичных сообщений с задержками."""
    _ensure_table()
    scenario = [
        ("Айжан Т.", "1А — 26 детей, 1 отсутствует. На питание 25.", "food", "Явка: 25 чел. (1А)", "1А", 25),
        ("Гульмира С.", "2Б: 24 ученика, все на месте.", "food", "Явка: 24 чел. (2Б)", "2Б", 24),
        ("Назгуль М.", "3В — 21 ребёнок, двое болеют, на питание 19.", "food", "Явка: 19 чел. (3В)", "3В", 19),
        ("Айман К.", "Сегодня не выйду, высокая температура, прошу поставить замену на мои уроки.", "absence", "Отсутствие учителя, требуется замена.", None, None),
        ("Руслан А.", "В кабинете 205 не включается проектор, нужен техспециалист до третьего урока.", "incident", "Инцидент: проектор в кабинете 205", None, None),
        ("Секретарь", "Распечатайте обновлённое расписание для учительской к 15:00.", "other", "[spontaneous] Распечатать расписание для учительской", None, None),
        ("Охрана", "После обеда проверьте запасной выход в левом крыле.", "other", "[spontaneous] Проверить запасной выход", None, None),
        ("Завуч", "К 16:30 подготовить актовый зал к собранию родителей 5-х классов.", "other", "[spontaneous] Подготовить актовый зал", None, None),
    ]
    for sender, text, mtype, summary, cls, cnt in scenario:
        try:
            conn = _get_conn()
            conn.execute(
                "INSERT INTO tg_messages (chat_id, sender, text, parsed_type, parsed_summary, food_class, food_count) "
                "VALUES (?,?,?,?,?,?,?)",
                (0, sender, text, mtype, summary, cls, cnt)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        _time.sleep(2)  # 2 секунды между сообщениями для эффекта "живой ленты"


@router.post("/demo-scenario")
def start_demo_scenario(background_tasks: BackgroundTasks):
    """Запускает автоматический демо-сценарий: 8 сообщений с задержкой 2 сек."""
    # Сначала очищаем старые данные
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM tg_messages")
        conn.commit()
        conn.close()
    except Exception:
        pass
    background_tasks.add_task(_run_demo_scenario)
    return {"status": "ok", "message": "Demo scenario started (8 messages, ~16 seconds)"}

