import os
import json
import openai
import re
from pydantic import BaseModel, Field
from typing import Optional, List
from app.ai.rag_service import check_compliance, translate_to_checklist
from app.services.scheduler import find_substitution

# Setup OpenAI
api_key = os.getenv("OPENAI_API_KEY", "mock")
openai.api_key = api_key

class ParsedMessage(BaseModel):
    type: str = Field(description="Тип сообщения: 'absence' (болезнь/отсутствие), 'incident' (драка, поломка), 'food' (питание) или 'other'")
    urgency: str = Field(description="'high', 'medium', 'low'")
    summary: str = Field(description="Краткая суть для дашборда директора (1-2 предложения)")
    entities: List[str] = Field(description="Имена упомянутых учителей или учеников (например: 'Иванов', 'Смирнова')")
    rag_insights: Optional[dict] = Field(default=None, description="Инструкции и чек-листы из приказов (если применимо)")
    substitution_plan: Optional[list] = Field(default=None, description="План замен, если учитель заболел")
    is_acceptance: bool = Field(default=False, description="True, если сообщение является подтверждением/принятием задачи (Ок, Принял, Хорошо)")


def parse_with_llm(text: str) -> ParsedMessage:
    if openai.api_key == "mock" or openai.api_key == "test_mock":
        # Возвращаем заглушку для MVP без реального ключа
        parsed = ParsedMessage(
            type="incident" if "сломал" in text.lower() or "драка" in text.lower() else "other",
            urgency="high",
            summary=f"Тестовое извлечение: {text[:50]}...",
            entities=["Mock User"]
        )
        
        orders_found = re.findall(r'76|110|130', text)
        if orders_found:
            rag_info = {}
            for order in set(orders_found):
                explanation = check_compliance(f"Приказ {order}")
                checklist = translate_to_checklist(f"приказ {order}")
                rag_info[f"order_{order}"] = {
                    "explanation": explanation.get("analysis", "Правила по данному приказу"),
                    "checklist": checklist
                }
            parsed.rag_insights = rag_info
            
        # Детектор подтверждения (Ок, Принял, Сделаю)
        acc_keywords = ["ок", "ok", "принял", "хорошо", "будет сделано", "сделаю", "понял", "сделаем"]
        if any(w in text.lower() for w in acc_keywords):
            parsed.is_acceptance = True
            parsed.summary = "✅ Подтверждение задачи"
            
        return parsed

    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты голосовой ассистент школы Aqbobek. Твоя задача — извлекать структурированные данные из сообщений учителей и помогать директору."},
                {"role": "user", "content": f"Извлеки факты из сообщения:\n{text}"}
            ],
            functions=[
                {
                    "name": "extract_data",
                    "description": "Извлечение структурированной информации из сообщения",
                    "parameters": ParsedMessage.schema()
                }
            ],
            function_call={"name": "extract_data"}
        )
        
        args = response.choices[0].message.function_call.arguments
        data = json.loads(args)
        
        # Автоматическая интеграция с RAG: если упомянуты приказы 76, 110, 130
        orders_found = re.findall(r'76|110|130', text)
        if orders_found:
            rag_info = {}
            for order in set(orders_found):
                # Ищем точный чек-лист по номеру приказа
                rag_query = f"Приказ {order}"
                explanation = check_compliance(rag_query)
                checklist = translate_to_checklist(f"приказ {order}")
                rag_info[f"order_{order}"] = {
                    "explanation": explanation.get("analysis", "Правила по данному приказу"),
                    "checklist": checklist
                }
            data["rag_insights"] = rag_info
            
        # Автоматическая интеграция со Smart Substitutions
        if data.get("type") == "absence":
            entities = data.get("entities", [])
            # Если LLM нашла имя заболевшего, передаем его в шедулер. Иначе дефолт 'Болат' для теста
            absent_teacher = entities[0] if entities else "Болат"
            data["substitution_plan"] = find_substitution(absent_teacher)
            
        return ParsedMessage(**data)
    except Exception as e:
        print(f"LLM Error: {e}")
        return ParsedMessage(type="other", urgency="low", summary="Ошибка парсинга", entities=[])
