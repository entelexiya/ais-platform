from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import parser, rag, schedule, voice, auth, tasks, bot_feed, notify, analytics
from app.ai.rag_service import init_rag
from app.db.database import engine, Base
from dotenv import load_dotenv
import os

# Загружаем ключи из .env (который лежит на папку выше)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path)

# Авторегистрация таблиц БД
Base.metadata.create_all(bind=engine)

# Авто-миграция: добавляем колонку is_accepted, если её нет (для хакатона)
from sqlalchemy import text
try:
    with engine.connect() as migration_conn:
        migration_conn.execute(text("ALTER TABLE task_reminders ADD COLUMN is_accepted BOOLEAN DEFAULT 0"))
        migration_conn.commit()
        print("✅ База данных дополнена колонкой is_accepted")
except Exception:
    # Ошибка обычно значит, что колонка уже существует
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Инициализация RAG Vectorstore...")
    init_rag()
    # Автоматический seed базы данных (безопасно — пропускает уже существующие записи)
    try:
        from app.db.seed_data import seed
        from app.db.demo_fixes import apply_demo_fixes
        from app.db.database import SessionLocal
        db = SessionLocal()
        seed(db)
        apply_demo_fixes(db)
        db.close()
    except Exception as e:
        print(f"Seed warning: {e}")
    yield
    print("Завершение работы...")

app = FastAPI(title="Aqbobek AI Orchestrator API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parser.router, prefix="/api", tags=["parser"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["schedule"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(bot_feed.router, prefix="/api/bot", tags=["bot-feed"])
app.include_router(notify.router, prefix="/api/notify", tags=["notify"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Backend is running!"}
