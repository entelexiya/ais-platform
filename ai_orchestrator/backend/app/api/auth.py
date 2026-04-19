from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import TimeoutError as SATimeoutError
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import User
import hashlib
import os
import sqlite3

router = APIRouter()

class AuthRequest(BaseModel):
    email: str
    password: str

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _resolve_sqlite_path() -> str:
    # backend/app/api/auth.py -> backend/orchestrator.db
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(backend_dir, "orchestrator.db")


def _sqlite_find_user(email: str) -> tuple[int, str] | None:
    db_path = _resolve_sqlite_path()
    conn = sqlite3.connect(db_path, timeout=10)
    try:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ? LIMIT 1",
            (email,),
        ).fetchone()
        if not row:
            return None
        return int(row[0]), str(row[1])
    finally:
        conn.close()

@router.post("/register")
def register(req: AuthRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == req.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    new_user = User(email=req.email, password_hash=get_password_hash(req.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Успешная регистрация", "user_id": new_user.id}

@router.post("/login")
def login(req: AuthRequest, db: Session = Depends(get_db)):
    # --- ХАКАТОН-ФОЛБЭК: Гарантированный вход для демо ---
    # Очищаем от возможных пробелов и приводим к нижнему регистру для надежности
    clean_email = req.email.strip().lower()
    clean_pass = req.password.strip()

    if clean_email == "admin@school.kz" and clean_pass == "qwerty_1":
        return {"message": "Успешный вход (Master)", "token": "fake-jwt-token-admin"}

    try:
        db_user = db.query(User).filter(User.email == req.email).first()
    except SATimeoutError:
        # Если SQLAlchemy-пул временно исчерпан, пробуем прямое подключение к SQLite.
        fallback_user = _sqlite_find_user(req.email)
        if not fallback_user or fallback_user[1] != get_password_hash(req.password):
            raise HTTPException(status_code=400, detail="Неверный логин или пароль")
        return {"message": "Успешный вход", "token": f"fake-jwt-token-{fallback_user[0]}"}

    if not db_user or db_user.password_hash != get_password_hash(req.password):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")
    
    return {"message": "Успешный вход", "token": f"fake-jwt-token-{db_user.id}"}
