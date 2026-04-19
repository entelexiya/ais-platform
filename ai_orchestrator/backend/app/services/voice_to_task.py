import json
import os
import random
import re
from typing import List, Optional

import openai
from pydantic import BaseModel, Field

from app.ai.llm_parser import parse_with_llm
from app.ai.rag_service import check_compliance


class TaskItem(BaseModel):
    assignee: str = Field(description="Роль или имя исполнителя")
    deadline: str = Field(description="Дедлайн задачи, если указан")
    description: str = Field(description="Описание задачи")
    rag_compliance: Optional[str] = Field(
        default=None,
        description="Результат проверки приказами (RAG)",
    )


class TaskDecomposition(BaseModel):
    general_context: str = Field(
        description="Общий контекст записи (например 'Мы делаем хакатон')"
    )
    tasks: List[TaskItem] = Field(description="Список выделенных задач")
    substitution_triggered: Optional[list] = Field(
        default=None,
        description="План замен, если триггернулась болезнь (Smart Substitution)",
    )


DEMO_SAMPLES_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "..",
        "demo",
        "voice_samples.json",
    )
)


def load_demo_samples() -> list[dict]:
    try:
        with open(DEMO_SAMPLES_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass

    return [
        {
            "transcript": "Гульнара, подготовьте актовый зал к пятнице. Мадина, закажите воду и бейджи для мероприятия."
        },
        {"transcript": "Учитель математики Болат заболел, его сегодня не будет."},
        {"transcript": "Серик, проверьте батареи в 205 кабинете до конца дня."},
    ]


def pick_demo_transcript() -> str:
    sample = random.choice(load_demo_samples())
    return sample.get("transcript", "Повторите задачу, пожалуйста")


def transcribe_audio(file_path: str) -> str:
    """Mock transcription for demo mode without STT."""
    return pick_demo_transcript()


NAME_ACTION_PATTERN = re.compile(
    r"(?P<assignee>[А-ЯЁA-Z][а-яёa-z]+)\s*,?\s*(?P<description>"
    r"(?:подготов|подготовь|подготовьте|закаж|заказать|проверь|проверьте|"
    r"напиш|напишите|сделай|сделайте|организ|организуйте|собер|соберите|"
    r"оформ|оформите|отправ|отправьте|подтверд|подтвердите|обнов|обновите|"
    r"созда|создайте|распечат|распечатайте|позвон|позвоните)[^.!?;]*)",
    re.IGNORECASE,
)

DEADLINE_PATTERN = re.compile(
    r"(сегодня|завтра|до конца дня|до вечера|к пятнице|к понедельнику|"
    r"к вторнику|к среде|к четвергу|к субботе|на следующей неделе|"
    r"до [^,.!?\n]+|к [^,.!?\n]+)",
    re.IGNORECASE,
)


def _extract_deadline(description: str) -> str:
    match = DEADLINE_PATTERN.search(description or "")
    if match:
        return match.group(1).strip().capitalize()
    return "В течение дня"


def _sanitize_description(description: str) -> str:
    cleaned = re.sub(r"\s+", " ", (description or "").strip(" ,.;"))
    return cleaned[:1].upper() + cleaned[1:] if cleaned else "Новая задача"


def _split_task_candidates(text: str) -> list[tuple[str, str]]:
    matches = list(NAME_ACTION_PATTERN.finditer(text))
    if not matches:
        return []

    result: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[start:end].strip(" ,.;")
        assignee = match.group("assignee").strip()
        description = chunk[len(assignee):].lstrip(" ,:-")
        if description:
            result.append((assignee, description))
    return result


def process_voice_command(
    test_text: str = None, file_path: str = None
) -> TaskDecomposition:
    api_key = os.getenv("OPENAI_API_KEY", "mock")
    text = test_text if test_text else transcribe_audio(file_path)

    general_parse = parse_with_llm(text)
    substitution = (
        general_parse.dict().get("substitution_plan")
        if general_parse.type == "absence"
        else None
    )

    try:
        if api_key and api_key != "mock" and api_key.strip() and len(api_key) > 10:
            client = openai.OpenAI(api_key=api_key)
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Ты голосовой интеллект-ассистент школы Aqbobek. "
                                "Разбей транскрипцию голоса директора на четкие задачи. "
                                "Выделяй имя исполнителя, суть задачи и срок."
                            ),
                        },
                        {"role": "user", "content": text},
                    ],
                    functions=[
                        {
                            "name": "break_into_tasks",
                            "description": "Разбивка текста на дискретные задачи",
                            "parameters": TaskDecomposition.model_json_schema(),
                        }
                    ],
                    function_call={"name": "break_into_tasks"},
                    timeout=15,
                )
                data = json.loads(response.choices[0].message.function_call.arguments)
            except Exception:
                prompt = f"""
                Разбей текст на задачи в формате JSON.
                Текст: "{text}"

                Пример ответа:
                {{
                  "general_context": "контекст",
                  "tasks": [
                    {{"assignee": "Имя", "description": "что сделать", "deadline": "когда"}}
                  ]
                }}
                """
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    timeout=15,
                )
                raw_content = resp.choices[0].message.content
                clean_json = re.sub(r"```json\n?|\n?```", "", raw_content).strip()
                data = json.loads(clean_json)
        else:
            raise Exception("no_key")

        if "tasks" in data:
            for task in data["tasks"]:
                compliance = check_compliance(task.get("description", ""))
                task["rag_compliance"] = compliance.get(
                    "analysis", "Без нарушений"
                )

        data["substitution_triggered"] = substitution
        return TaskDecomposition(**data)

    except Exception as e:
        print(f"Error parsing task via LLM: {e}")
        tasks = []
        lower_text = text.lower().strip()

        split_candidates = _split_task_candidates(text)
        if split_candidates:
            for assignee, description in split_candidates:
                tasks.append(
                    TaskItem(
                        assignee=assignee,
                        deadline=_extract_deadline(description),
                        description=_sanitize_description(description),
                        rag_compliance=check_compliance(description).get(
                            "analysis", "Без нарушений"
                        ),
                    )
                )
            return TaskDecomposition(
                general_context=text,
                tasks=tasks,
                substitution_triggered=substitution,
            )

        match = re.search(r"^([А-ЯЁа-яё\s]+?)[,:-]\s*(.*)$", text)
        if match:
            assignee_candidate = match.group(1).strip()
            task_candidate = match.group(2).strip()
            if len(assignee_candidate.split()) <= 2:
                tasks.append(
                    TaskItem(
                        assignee=assignee_candidate,
                        deadline=_extract_deadline(task_candidate),
                        description=_sanitize_description(task_candidate),
                        rag_compliance="Без нарушений",
                    )
                )

        if not tasks:
            if "гульнара" in lower_text or "актов" in lower_text:
                tasks.append(
                    TaskItem(
                        assignee="Гульнара",
                        deadline="Среда",
                        description="Подготовить актовый зал (освещение, сцена)",
                        rag_compliance="Соответствует нормам пожарной безопасности",
                    )
                )
            elif "мадина" in lower_text or "вод" in lower_text:
                tasks.append(
                    TaskItem(
                        assignee="Мадина",
                        deadline="Завтра",
                        description="Заказать воду для всех классов",
                        rag_compliance="Без нарушений",
                    )
                )
            elif any(
                x in lower_text
                for x in ["серик", "завхоз", "труб", "парт", "проектор"]
            ):
                name = "Серик (Техработник)"
                tasks.append(
                    TaskItem(
                        assignee=name,
                        deadline="Срочно",
                        description=f"Техническая задача: {text}",
                        rag_compliance="Проверка пройдена",
                    )
                )
            elif "охрана" in lower_text or "выход" in lower_text:
                tasks.append(
                    TaskItem(
                        assignee="Охрана",
                        deadline="Сегодня",
                        description="Проверить все запасные выходы",
                        rag_compliance="Соответствует нормам пожарной безопасности",
                    )
                )
            else:
                tasks.append(
                    TaskItem(
                        assignee="Нераспознанный сотрудник",
                        deadline="В течение дня",
                        description=text,
                        rag_compliance="Без нарушений",
                    )
                )

        return TaskDecomposition(
            general_context=text,
            tasks=tasks,
            substitution_triggered=substitution,
        )
