"""
API для отправки уведомлений из дашборда.
"""

import logging
import os

import requests
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.notification_service import (
    dispatch_director_alert,
    dispatch_substitution_notification,
)

router = APIRouter()
log = logging.getLogger("notify")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BASE_TG = f"https://api.telegram.org/bot{BOT_TOKEN}"
TEACHER_CHATS: dict[str, int] = {}
SCHOOL_BROADCAST_CHAT = int(os.getenv("SCHOOL_CHAT_ID", "0"))
WHATSAPP_DEMO_CHAT_ID = os.getenv("WHATSAPP_DEMO_CHAT_ID", "").strip()


def _send_tg(chat_id: int, text: str) -> bool:
    if not BOT_TOKEN or chat_id == 0:
        log.warning("Telegram not configured (chat_id=%s)", chat_id)
        return False
    try:
        response = requests.post(
            f"{BASE_TG}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=5,
        )
        return response.status_code == 200
    except Exception as exc:
        log.error("Telegram error: %s", exc)
        return False


class SubstitutionNotifyRequest(BaseModel):
    substitute_teacher: str
    missing_teacher: str
    class_name: str
    lesson_number: int
    room: str
    day: str = "Сегодня"
    subject: str = "Урок"


class TaskNotifyRequest(BaseModel):
    assignee: str
    title: str
    deadline: str


class BroadcastRequest(BaseModel):
    message: str


@router.post("/substitution")
def notify_substitution(req: SubstitutionNotifyRequest, db: Session = Depends(get_db)):
    result = dispatch_substitution_notification(
        db=db,
        substitute_teacher_name=req.substitute_teacher,
        missing_teacher_name=req.missing_teacher,
        class_name=req.class_name,
        lesson_number=req.lesson_number,
        room=req.room,
        day=req.day,
        subject=req.subject,
    )
    result["wa_link"] = (
        "https://wa.me/?text="
        + requests.utils.quote(
            result["message"].replace("<b>", "*").replace("</b>", "*").replace("\n", "%0A")
        )
    )
    return result


@router.post("/task")
def notify_task(req: TaskNotifyRequest):
    text = (
        f"📋 <b>Новая задача от директора</b>\n\n"
        f"Уважаемый(ая) <b>{req.assignee}</b>!\n\n"
        f"Вам поставлена задача:\n"
        f"<b>{req.title}</b>\n\n"
        f"⏰ <b>Срок выполнения:</b> {req.deadline}\n\n"
        f"Пожалуйста, подтвердите получение, ответив на это сообщение.\n"
        f"<i>AI-Завуч Aqbobek</i>"
    )

    chat_id = TEACHER_CHATS.get(req.assignee, SCHOOL_BROADCAST_CHAT)
    sent = _send_tg(chat_id, text) if chat_id else False

    return {
        "status": "sent" if sent else "queued",
        "message": text,
        "recipient": req.assignee,
    }


@router.post("/broadcast")
def broadcast(req: BroadcastRequest):
    if SCHOOL_BROADCAST_CHAT:
        _send_tg(SCHOOL_BROADCAST_CHAT, req.message)
    return {"status": "sent", "chat_id": SCHOOL_BROADCAST_CHAT}


@router.post("/director-alert")
def notify_director_alert(req: BroadcastRequest, db: Session = Depends(get_db)):
    return dispatch_director_alert(db, req.message)


@router.get("/status")
def notify_status():
    return {
        "telegram_configured": bool(BOT_TOKEN),
        "broadcast_chat": SCHOOL_BROADCAST_CHAT,
        "whatsapp_demo_chat": WHATSAPP_DEMO_CHAT_ID or None,
        "registered_teachers": list(TEACHER_CHATS.keys()),
        "tip": "Чтобы получать уведомления — привяжите telegram_chat_id сотрудникам или настройте SCHOOL_CHAT_ID",
    }
