import logging
import os
from typing import Dict, Optional

import requests
from sqlalchemy.orm import Session

from app.db.models import Teacher

log = logging.getLogger("notification-service")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BASE_TG = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""
SCHOOL_BROADCAST_CHAT = int(os.getenv("SCHOOL_CHAT_ID", "0"))
WHATSAPP_DEMO_CHAT_ID = os.getenv("WHATSAPP_DEMO_CHAT_ID", "").strip()
WHATSAPP_OUTGOING_ENABLED = os.getenv("WHATSAPP_OUTGOING_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _send_tg(chat_id: str | int, text: str) -> bool:
    if not BOT_TOKEN or not chat_id:
        return False
    try:
        response = requests.post(
            f"{BASE_TG}/sendMessage",
            json={
                "chat_id": str(chat_id),
                "text": text,
                "parse_mode": "HTML",
            },
            timeout=5,
        )
        return response.status_code == 200
    except Exception as exc:
        log.warning("Telegram send failed: %s", exc)
        return False


def _normalize_phone(phone: Optional[str]) -> str:
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def resolve_whatsapp_target(chat_id: Optional[str]) -> Optional[str]:
    if WHATSAPP_DEMO_CHAT_ID:
        return WHATSAPP_DEMO_CHAT_ID
    return chat_id


def _send_whatsapp(chat_id: str, text: str) -> bool:
    if not WHATSAPP_OUTGOING_ENABLED:
        log.info("WhatsApp send skipped: WHATSAPP_OUTGOING_ENABLED is false")
        return False
    chat_id = resolve_whatsapp_target(chat_id)
    if not chat_id:
        return False
    try:
        response = requests.post(
            "http://localhost:3000/send",
            json={"chatId": chat_id, "text": text},
            timeout=3,
        )
        return response.status_code == 200
    except Exception as exc:
        log.warning("WhatsApp send failed: %s", exc)
        return False


def _build_whatsapp_chat_id(teacher: Optional[Teacher]) -> Optional[str]:
    if not teacher or not teacher.whatsapp_number:
        return None
    digits = _normalize_phone(teacher.whatsapp_number)
    if not digits:
        return None
    return f"{digits}@c.us"


def build_substitution_message(
    substitute_teacher: str,
    missing_teacher: str,
    class_name: str,
    lesson_number: int,
    room: str,
    day: str,
    subject: str,
) -> str:
    return (
        f"📢 <b>Замена назначена</b>\n\n"
        f"<b>{substitute_teacher}</b>, вам назначена срочная замена.\n"
        f"• День: <b>{day}</b>\n"
        f"• Урок: <b>{lesson_number}</b>\n"
        f"• Класс: <b>{class_name}</b>\n"
        f"• Предмет: <b>{subject}</b>\n"
        f"• Кабинет: <b>{room}</b>\n"
        f"• Вместо: <b>{missing_teacher}</b>\n\n"
        f"Изменение уже внесено в расписание."
    )


def build_absence_reply(
    teacher_name: str,
    day: str,
    substitutions_count: int,
    unresolved_count: int,
) -> str:
    if substitutions_count and not unresolved_count:
        return (
            f"✅ Отсутствие {teacher_name} на {day} зафиксировано.\n"
            f"Все замены подобраны автоматически: {substitutions_count}."
        )
    if substitutions_count and unresolved_count:
        return (
            f"⚠️ Отсутствие {teacher_name} на {day} зафиксировано.\n"
            f"Подобрано замен: {substitutions_count}, требуют ручного решения: {unresolved_count}."
        )
    return (
        f"⚠️ Отсутствие {teacher_name} на {day} зафиксировано.\n"
        f"Автоматическая замена не найдена, директору отправлено уведомление."
    )


def dispatch_substitution_notification(
    db: Session,
    substitute_teacher_name: str,
    missing_teacher_name: str,
    class_name: str,
    lesson_number: int,
    room: str,
    day: str,
    subject: str,
) -> Dict:
    teacher = (
        db.query(Teacher)
        .filter(
            (Teacher.full_name == substitute_teacher_name)
            | (Teacher.short_name == substitute_teacher_name)
        )
        .first()
    )

    message = build_substitution_message(
        substitute_teacher=substitute_teacher_name,
        missing_teacher=missing_teacher_name,
        class_name=class_name,
        lesson_number=lesson_number,
        room=room,
        day=day,
        subject=subject,
    )

    telegram_sent = False
    whatsapp_sent = False

    if teacher and teacher.telegram_chat_id:
        telegram_sent = _send_tg(teacher.telegram_chat_id, message)
    elif SCHOOL_BROADCAST_CHAT:
        telegram_sent = _send_tg(SCHOOL_BROADCAST_CHAT, message)

    wa_chat_id = _build_whatsapp_chat_id(teacher)
    if wa_chat_id:
        whatsapp_sent = _send_whatsapp(wa_chat_id, message.replace("<b>", "*").replace("</b>", "*"))

    return {
        "recipient": substitute_teacher_name,
        "telegram_sent": telegram_sent,
        "whatsapp_sent": whatsapp_sent,
        "status": "sent" if telegram_sent or whatsapp_sent else "queued",
        "message": message,
        "whatsapp_chat_id": resolve_whatsapp_target(wa_chat_id),
    }


def send_to_school_group(text: str) -> bool:
    """Отправляет сообщение в школьную WhatsApp-группу (WHATSAPP_DEMO_CHAT_ID)."""
    if not WHATSAPP_DEMO_CHAT_ID:
        return False
    plain = text.replace("<b>", "*").replace("</b>", "*").replace("<i>", "_").replace("</i>", "_")
    return _send_whatsapp(WHATSAPP_DEMO_CHAT_ID, plain)


def dispatch_director_alert(db: Session, text: str) -> Dict:
    director = (
        db.query(Teacher)
        .filter(Teacher.role.in_(["Директор", "Завуч"]))
        .order_by(Teacher.id)
        .first()
    )

    telegram_sent = False
    recipient = director.short_name if director and director.short_name else "Администрация"
    if director and director.telegram_chat_id:
        telegram_sent = _send_tg(director.telegram_chat_id, text)
    elif SCHOOL_BROADCAST_CHAT:
        telegram_sent = _send_tg(SCHOOL_BROADCAST_CHAT, text)

    return {
        "recipient": recipient,
        "telegram_sent": telegram_sent,
        "status": "sent" if telegram_sent else "queued",
        "message": text,
    }
