from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.ai.llm_parser import parse_with_llm, ParsedMessage

router = APIRouter()

class MessagePayload(BaseModel):
    text: str
    user_id: int

@router.post("/parse-message", response_model=ParsedMessage)
async def parse_message(payload: MessagePayload, db: Session = Depends(get_db)):
    from app.db.models import TaskReminder
    parsed_data = parse_with_llm(payload.text)
    
    # ─── ЛОГИКА ПОДТВЕРЖДЕНИЯ (FEEDBACK LOOP) ───
    if parsed_data.is_acceptance:
        # Находим последнюю задачу, которая еще не принята
        task = db.query(TaskReminder).filter(TaskReminder.is_accepted == False, TaskReminder.is_completed == False).order_by(TaskReminder.id.desc()).first()
        if task:
            task.is_accepted = True
            db.commit()
            parsed_data.summary = f"Принято: {task.title}"
    
    return parsed_data

