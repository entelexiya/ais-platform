# AIS — AI School Orchestrator

Интеллектуальная система управления школой для AIS Hack 3.0.

## Стек
- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: React, TypeScript, Tailwind CSS
- **AI**: OpenAI Whisper, GPT, FAISS RAG
- **Боты**: Telegram Bot API, WhatsApp Web JS

## Запуск

```bash
# Backend
cd ai_orchestrator/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd ai_orchestrator/frontend
npm install
npm run dev
```

Открыть: http://localhost:5173
