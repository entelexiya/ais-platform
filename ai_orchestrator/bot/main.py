"""
AI-Завуч Telegram Bot (aiogram version)
========================================
Запуск: python ai_orchestrator/bot/main.py

Команды:
  /start    — Приветствие
  /svod     — Сводка посещаемости за сегодня
  /incidents — Список инцидентов
  /zamena <имя> — Найти замену учителю
  /demo     — Загрузить тестовые данные для питча
"""

import asyncio
import os
import re
import sqlite3
import aiohttp
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

# Загружаем .env из родительской директории
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("bot")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# БД — ищем файл рядом с backend/main.py
_base = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_base, "..", "backend", "orchestrator.db")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# ─── SQLite helpers ───────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()

def save_message(chat_id, sender, text, mtype, summary, food_class=None, food_count=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO tg_messages (chat_id,sender,text,parsed_type,parsed_summary,food_class,food_count) VALUES (?,?,?,?,?,?,?)",
        (chat_id, sender, text, mtype, summary, food_class, food_count)
    )
    conn.commit()
    conn.close()

def get_food_svod():
    conn = sqlite3.connect(DB_PATH)
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT food_class, food_count FROM tg_messages WHERE parsed_type='food' AND date(created_at)=?",
        (today,)
    ).fetchall()
    conn.close()
    total = sum(r[1] for r in rows if r[1])
    classes = {r[0]: r[1] for r in rows if r[0]}
    return {"total": total, "count": len(rows), "classes": classes}

def get_incidents():
    conn = sqlite3.connect(DB_PATH)
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute(
        "SELECT sender, parsed_summary, created_at FROM tg_messages "
        "WHERE parsed_type='incident' AND date(created_at)=? ORDER BY created_at DESC LIMIT 10",
        (today,)
    ).fetchall()
    conn.close()
    return [{"sender": r[0], "summary": r[1], "time": r[2]} for r in rows]

def seed_demo(chat_id):
    demo = [
        ("Абенова Г.",   "1А — 24 детей, 1 болеет",            "food",     "Явка: 24 чел. (1А)",                   "1А", 24),
        ("Сейткали М.",  "1Б: 22 ребёнка",                     "food",     "Явка: 22 чел. (1Б)",                   "1Б", 22),
        ("Нурланова Д.", "2А — 26 детей, все пришли",           "food",     "Явка: 26 чел. (2А)",                   "2А", 26),
        ("Касымова А.",  "2Б — 23 человека",                   "food",     "Явка: 23 чел. (2Б)",                   "2Б", 23),
        ("Жаксыбеков",  "3В — 20 детей, 2 болеют",            "food",     "Явка: 20 чел. (3В)",                   "3В", 20),
        ("Смирнова Е.", "4А — 25 человек",                    "food",     "Явка: 25 чел. (4А)",                   "4А", 25),
        ("Аскар Б.",    "Аскар заболел, не приду",            "absence",  "Отсутствует: Аскар. Требуется замена.", None, None),
        ("Ахмет З.",    "В кабинете 302 сломался проектор",   "incident", "Инцидент: сломан проектор в каб.302",  None, None),
    ]
    conn = sqlite3.connect(DB_PATH)
    today = datetime.now().strftime("%Y-%m-%d")
    conn.execute("DELETE FROM tg_messages WHERE date(created_at)=?", (today,))
    for sender, text, mtype, summary, cls, cnt in demo:
        conn.execute(
            "INSERT INTO tg_messages (chat_id,sender,text,parsed_type,parsed_summary,food_class,food_count) VALUES (?,?,?,?,?,?,?)",
            (chat_id, sender, text, mtype, summary, cls, cnt)
        )
    conn.commit()
    conn.close()

# ─── Парсер текста ────────────────────────────────────────────

def extract_food_info(text):
    class_match = re.search(r"(\d+[АаБбВвГг])", text, re.IGNORECASE)
    count_match = re.search(r"(\d+)\s*(детей|ребёнка|ребенка|человек|учеников|порций)", text, re.IGNORECASE)
    food_class = class_match.group(1).upper() if class_match else None
    food_count = int(count_match.group(1)) if count_match else None
    return food_class, food_count

def local_classify(text):
    t = text.lower()
    food_class, food_count = extract_food_info(text)
    if food_class or food_count or any(w in t for w in ["детей", "ребёнок", "порций", "столовая"]):
        return "food", f"Явка: {food_count or '?'} чел." + (f" ({food_class})" if food_class else ""), food_class, food_count
    if any(w in t for w in ["заболел", "болеет", "не придёт", "не придет", "нетрудоспособ"]):
        return "absence", f"Отсутствие, требуется замена: {text[:60]}", None, None
    if any(w in t for w in ["сломал", "поломка", "не работает", "протечка", "авария", "драка", "конфликт"]):
        return "incident", f"Инцидент: {text[:80]}", None, None
    return "other", text[:100], None, None

# ─── Команды ─────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(
        f"👋 <b>Привет, {msg.from_user.first_name}!</b>\n\n"
        "Я — <b>AI-Завуч Оркестратор</b> школы Aqbobek 🏫\n\n"
        "<b>Учителям — просто напишите:</b>\n"
        "• <i>«1А — 25 детей, 2 болеют»</i>\n"
        "• <i>«В каб. 302 сломался проектор»</i>\n"
        "• <i>«Аскар заболел, не придёт»</i>\n\n"
        "<b>Директору:</b>\n"
        "/svod — 📊 Сводка по питанию\n"
        "/incidents — 🚨 Инциденты сегодня\n"
        "/zamena [имя] — 🔄 Найти замену\n"
        "/demo — 🎬 Загрузить тестовые данные\n\n"
        "Всё остальное разберу сам!",
        parse_mode="HTML"
    )

@dp.message(Command("demo"))
async def cmd_demo(msg: Message):
    seed_demo(msg.chat.id)
    await msg.answer(
        "🎬 <b>Демо-данные загружены!</b>\n\n"
        "Добавлено:\n"
        "• 📋 6 отчётов об явке (1А–4А) → итого 140 порций\n"
        "• 🚨 1 инцидент (проектор каб. 302)\n"
        "• 🔴 1 отсутствие (Аскар Болатов)\n\n"
        "Теперь введите <b>/svod</b> или <b>/incidents</b> 🎯",
        parse_mode="HTML"
    )

@dp.message(Command("svod"))
async def cmd_svod(msg: Message):
    data = get_food_svod()
    if data["count"] == 0:
        await msg.answer("📊 <b>Сводка за сегодня</b>\n\nСообщений пока нет. Введите /demo для теста.", parse_mode="HTML")
        return
    lines = [f"📊 <b>Сводка по питанию — {datetime.now().strftime('%d.%m.%Y')}</b>\n"]
    for cls, cnt in sorted(data["classes"].items()):
        lines.append(f"  {cls}: <b>{cnt}</b> порций")
    lines.append(f"\n🍽 <b>ИТОГО: {data['total']} порций</b>")
    lines.append(f"📝 Отчётов получено: {data['count']}")
    lines.append("\n✅ <i>Сформировано автоматически AI-Завуч</i>")
    await msg.answer("\n".join(lines), parse_mode="HTML")

@dp.message(Command("incidents"))
async def cmd_incidents(msg: Message):
    incidents = get_incidents()
    if not incidents:
        await msg.answer("🚨 <b>Инциденты за сегодня</b>\n\nИнцидентов не зафиксировано ✅", parse_mode="HTML")
        return
    lines = [f"🚨 <b>Инциденты — {datetime.now().strftime('%d.%m.%Y')}</b>\n"]
    for i, inc in enumerate(incidents, 1):
        t = inc["time"][-8:-3] if len(inc["time"]) > 8 else ""
        lines.append(f"{i}. [{t}] <b>{inc['sender']}</b>: {inc['summary']}")
    await msg.answer("\n".join(lines), parse_mode="HTML")

@dp.message(Command("zamena"))
async def cmd_zamena(msg: Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("❓ Укажите имя: <code>/zamena Аскар</code>", parse_mode="HTML")
        return
    teacher = parts[1]
    await msg.answer(f"🔄 Ищу замену для <b>{teacher}</b>...", parse_mode="HTML")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BACKEND_URL}/api/schedule/substitute",
                                    json={"teacher_name": teacher}, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    plan = (await r.json()).get("substitution_plan", [])
                    if not plan:
                        await msg.answer(f"⚠️ Свободных учителей для <b>{teacher}</b> не найдено.", parse_mode="HTML")
                        return
                    lines = [f"✅ <b>План замен для {teacher}:</b>\n"]
                    for sub in plan:
                        lines.append(f"• Урок {sub.get('lesson_number')} | {sub.get('class_name')} "
                                     f"| <b>{sub.get('substitute_teacher')}</b>")
                    await msg.answer("\n".join(lines), parse_mode="HTML")
    except Exception as e:
        log.error(f"Zamena error: {e}")
        await msg.answer("⚠️ Бэкенд недоступен.", parse_mode="HTML")

# ─── Обычные сообщения ────────────────────────────────────────

@dp.message()
async def handle_message(msg: Message):
    if not msg.text:
        return
    text = msg.text.strip()
    sender = (msg.from_user.first_name or "") + " " + (msg.from_user.last_name or "")
    sender = sender.strip() or msg.from_user.username or "Аноним"

    # Сначала пробуем бэкенд, затем локальный классификатор
    mtype, summary, food_class, food_count = local_classify(text)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BACKEND_URL}/api/parse-message",
                                    json={"text": text, "user_id": msg.from_user.id},
                                    timeout=aiohttp.ClientTimeout(total=4)) as r:
                if r.status == 200:
                    data = await r.json()
                    mtype = data.get("type", mtype)
                    summary = data.get("summary", summary)
                    food_class_b, food_count_b = extract_food_info(text)
                    food_class = food_class or food_class_b
                    food_count = food_count or food_count_b
    except Exception:
        pass  # используем local_classify

    save_message(msg.chat.id, sender, text, mtype, summary, food_class, food_count)

    responses = {
        "food": f"✅ Принято{f' ({food_class})' if food_class else ''}: <b>{food_count or '?'} порций</b>\nДобавлено в сводку директора.",
        "absence": f"🔴 <b>Отсутствие зафиксировано.</b>\n{summary}\nДиректор уведомлён. AI ищет замену...",
        "incident": f"⚠️ <b>Инцидент зафиксирован.</b>\n{summary}\nКарточка создана на дашборде.",
        "other": f"📝 Принято. Сообщение добавлено в журнал."
    }
    await msg.answer(responses.get(mtype, "📝 Принято."), parse_mode="HTML")

# ─── Запуск ───────────────────────────────────────────────────

async def main():
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "mock_token":
        log.error("❌ TELEGRAM_BOT_TOKEN не задан в .env")
        return
    init_db()
    log.info("🤖 AI-Завуч Bot запущен")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Бот остановлен.")
