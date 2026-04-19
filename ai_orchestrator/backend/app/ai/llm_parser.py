import json
import logging
import os
import re
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from app.ai.rag_service import check_compliance, translate_to_checklist
from app.services.scheduler import find_substitution

log = logging.getLogger("llm-parser")

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_CURRENT_DIR)))
_DOTENV_PATH = os.path.join(_PROJECT_DIR, ".env")
load_dotenv(_DOTENV_PATH)


FOOD_CLASS_RE = re.compile(r"(\d+\s*[А-ЯA-Z])", re.IGNORECASE)
FOOD_COUNT_RE = re.compile(
    r"(\d+)\s*(?:дет(?:ей|и)|реб[её]н(?:ка|ок|ка)|человек|ученик(?:ов|а)?|порц(?:ий|ии|ия))",
    re.IGNORECASE,
)
ABSENT_COUNT_RE = re.compile(
    r"(\d+)\s*(?:боле(?:ют|ет)|отсутств(?:уют|ует)|не приш(?:ли|ел|ла))",
    re.IGNORECASE,
)
LOCATION_RE = re.compile(
    r"(?:в|на)\s+(?:кабинет(?:е)?|каб\.?|аудитории|комнате|зале)?\s*([A-Za-zА-Яа-яЁё]{0,4}\s*)?(\d{1,3}[A-Za-zА-Яа-яЁё]?)",
    re.IGNORECASE,
)
ASSIGNEE_RE = re.compile(
    r"^(?P<assignee>[А-ЯЁA-Z][а-яёa-z]+|секретарю|охране|завхозу|завучу|директору|администратору)\s*[:,\-]\s*(?P<body>.+)$",
    re.IGNORECASE,
)
DEADLINE_RE = re.compile(
    r"(сегодня|завтра|до конца дня|до вечера|к\s+[а-яё0-9 :\-]+|на следующей неделе|после обеда|срочно)",
    re.IGNORECASE,
)
INCIDENT_KEYWORDS = (
    "сломал",
    "сломался",
    "не работает",
    "протечка",
    "авария",
    "проектор",
    "принтер",
    "парта",
    "розетка",
    "свет",
)
MEDICAL_KEYWORDS = (
    "без сознания",
    "скорая",
    "травм",
    "температур",
    "плохо",
    "рвота",
)
ABSENCE_KEYWORDS = (
    "не приду",
    "не выйду",
    "не будет",
    "заболел",
    "заболела",
    "болею",
    "болеет",
    "температура",
)
TASK_KEYWORDS = (
    "подготов",
    "закаж",
    "проверь",
    "распечат",
    "собер",
    "подтверд",
    "создай",
    "оформ",
    "отправ",
    "обнов",
)
ACCEPTANCE_PATTERNS = (
    "ок",
    "окей",
    "принял",
    "приняла",
    "сделаю",
    "сделаем",
    "понял",
    "поняла",
    "хорошо",
    "готово",
    "+",
)
ROLE_NORMALIZATION = {
    "секретарю": "Секретарь",
    "охране": "Охрана",
    "завхозу": "Завхоз",
    "завучу": "Завуч",
    "директору": "Директор",
    "администратору": "Администратор",
}
KAZAKH_SPECIFIC_CHARS_RE = re.compile(r"[ӘәІіҢңҒғҮүҰұҚқӨөҺһ]")
KAZAKH_COMMON_WORDS = (
    "бүгін",
    "ертең",
    "келмеймін",
    "келмейдi",
    "келмеймін",
    "ауырып",
    "ауырып қалдым",
    "мұғалім",
    "сынып",
    "тапсырма",
    "дайында",
    "тексер",
    "жібер",
    "оқушы",
    "балалар",
    "жиналыс",
    "сабақ",
    "асхана",
)
ABSENCE_KEYWORDS = ABSENCE_KEYWORDS + (
    "келмеймін",
    "келмейді",
    "ауырып қалдым",
    "ауырып қалды",
    "жұмысқа шыға алмаймын",
    "сабаққа келе алмаймын",
)
MEDICAL_KEYWORDS = MEDICAL_KEYWORDS + (
    "есінен танып",
    "жедел жәрдем",
    "құсып",
    "жағдайы нашар",
)
INCIDENT_KEYWORDS = INCIDENT_KEYWORDS + (
    "істемейді",
    "сынып қалды",
    "жанып тұрған жоқ",
    "жөндеу керек",
)
TASK_KEYWORDS = TASK_KEYWORDS + (
    "дайында",
    "тапсырыс бер",
    "тексер",
    "жөнде",
    "шығарып бер",
    "хабарла",
)
ACCEPTANCE_PATTERNS = ACCEPTANCE_PATTERNS + (
    "жақсы",
    "түсіндім",
    "қабылдадым",
    "орындаймын",
)


FOOD_CLASS_RE_SAFE = re.compile(r"(\d+\s*[А-ЯA-Z])", re.IGNORECASE)
FOOD_COUNT_RE_SAFE = re.compile(
    r"(\d+)\s*(?:детей|реб[её]н(?:ка|ок)?|человек|ученик(?:ов|а)?|порц(?:ий|ии|ия)|бала(?:лар)?|оқушы(?:лар)?)",
    re.IGNORECASE,
)
ABSENT_COUNT_RE_SAFE = re.compile(
    r"(\d+)\s*(?:боле(?:ют|ет)|отсутств(?:уют|ует)|не приш(?:ли|ел|ла)|келмеді|жоқ)",
    re.IGNORECASE,
)
LOCATION_RE_SAFE = re.compile(
    r"(?:в|на)\s+(?:кабинет(?:е)?|каб\.?|аудитории|комнате)?\s*([A-Za-zА-Яа-яЁё]{0,4}\s*)?(\d{1,3}[A-Za-zА-Яа-яЁё]?)",
    re.IGNORECASE,
)
ASSIGNEE_RE_SAFE = re.compile(
    r"^(?P<assignee>[А-ЯЁA-Z][а-яёa-z]+|секретарю|охране|завхозу|завучу|директору|администратору)\s*[:,\-]\s*(?P<body>.+)$",
    re.IGNORECASE,
)
DEADLINE_RE_SAFE = re.compile(
    r"(сегодня|завтра|до конца дня|до вечера|к\s+[а-яё0-9 :\-]+|на следующей неделе|после обеда|срочно|бүгін|ертең|күн соңына дейін|кешке дейін)",
    re.IGNORECASE,
)

ABSENCE_KEYWORDS = ABSENCE_KEYWORDS + (
    "не приду",
    "не выйду",
    "не будет",
    "заболел",
    "заболела",
    "болею",
    "болеет",
    "температура",
    "мен ертең келмеймін",
    "ертең келмеймін",
    "ауырып қалдым",
)
MEDICAL_KEYWORDS = MEDICAL_KEYWORDS + (
    "без сознания",
    "скорая",
    "травма",
    "температура",
    "плохо",
    "рвота",
    "жедел жәрдем",
)
INCIDENT_KEYWORDS = INCIDENT_KEYWORDS + (
    "сломал",
    "сломался",
    "не работает",
    "протечка",
    "авария",
    "проектор",
    "принтер",
    "парта",
    "розетка",
    "свет",
    "істемейді",
)
TASK_KEYWORDS = TASK_KEYWORDS + (
    "подготов",
    "закаж",
    "проверь",
    "распечат",
    "собер",
    "подтверд",
    "создай",
    "оформ",
    "отправ",
    "обнов",
    "дайында",
    "тапсыр",
    "тексер",
)
ACCEPTANCE_PATTERNS = ACCEPTANCE_PATTERNS + (
    "ок",
    "окей",
    "принял",
    "приняла",
    "сделаю",
    "сделаем",
    "понял",
    "поняла",
    "хорошо",
    "готово",
    "жақсы",
    "түсіндім",
)
ROLE_NORMALIZATION.update(
    {
        "секретарю": "Секретарь",
        "охране": "Охрана",
        "завхозу": "Завхоз",
        "завучу": "Завуч",
        "директору": "Директор",
        "администратору": "Администратор",
    }
)


class ParsedMessage(BaseModel):
    type: str = Field(description="food, absence, incident, medical, task или other")
    urgency: str = Field(description="high, medium или low", default="medium")
    summary: str = Field(description="Короткое резюме для дашборда")
    entities: List[str] = Field(default_factory=list)
    rag_insights: Optional[dict] = None
    substitution_plan: Optional[list] = None
    is_acceptance: bool = False
    confidence: float = 0.0
    teacher_name: Optional[str] = None
    class_name: Optional[str] = None
    food_count: Optional[int] = None
    present_count: Optional[int] = None
    absent_count: Optional[int] = None
    location: Optional[str] = None
    issue: Optional[str] = None
    assignee: Optional[str] = None
    assignee_role: Optional[str] = None
    deadline: Optional[str] = None
    recurrence: str = "spontaneous"
    task_title: Optional[str] = None
    requires_substitution: bool = False
    requires_review: bool = False
    review_reason: Optional[str] = None
    analysis_provider: Optional[str] = None
    detected_language: Optional[str] = None


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    clean = text.strip()
    clean = re.sub(r"^```json\s*|^```\s*|\s*```$", "", clean, flags=re.IGNORECASE | re.MULTILINE)
    start = clean.find("{")
    end = clean.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(clean[start : end + 1])
    except json.JSONDecodeError:
        return None


def _detect_language_route(text: str) -> str:
    normalized = (text or "").lower()
    if KAZAKH_SPECIFIC_CHARS_RE.search(normalized):
        return "kazakh"

    hits = sum(1 for word in KAZAKH_COMMON_WORDS if word in normalized)
    if hits >= 2:
        return "kazakh"
    if hits == 1:
        return "mixed"
    return "default"


def _clean_secret(value: Optional[str]) -> str:
    return (value or "").replace("\n", "").strip()


def _valid_api_key(value: Optional[str]) -> bool:
    cleaned = _clean_secret(value)
    return bool(cleaned and cleaned not in {"mock", "test_mock"} and len(cleaned) >= 10)


def _provider_config(
    provider: str,
    *,
    api_key: Optional[str],
    model: Optional[str],
    base_url: Optional[str],
    timeout_seconds: Optional[str],
) -> Optional[Dict[str, object]]:
    cleaned_key = _clean_secret(api_key)
    cleaned_model = (model or "").strip()
    cleaned_base_url = (base_url or "").strip()
    if not _valid_api_key(cleaned_key) or not cleaned_model:
        return None

    if not cleaned_base_url:
        cleaned_base_url = "https://api.openai.com/v1"

    return {
        "provider": provider,
        "api_key": cleaned_key,
        "model": cleaned_model,
        "base_url": cleaned_base_url.rstrip("/"),
        "timeout": float(timeout_seconds or "8"),
    }


def _provider_candidates(route: str = "default") -> List[Dict[str, object]]:
    candidates: List[Optional[Dict[str, object]]] = [
        _provider_config(
            "kazllm",
            api_key=os.getenv("KAZLLM_API_KEY") or os.getenv("KAZLLM_BEARER_TOKEN"),
            model=os.getenv("KAZLLM_MODEL") or "kazllm",
            base_url=os.getenv("KAZLLM_BASE_URL") or "https://llm.alem.ai/v1",
            timeout_seconds=os.getenv("KAZLLM_TIMEOUT_SECONDS") or os.getenv("CHAT_ANALYSIS_TIMEOUT_SECONDS") or "8",
        ),
        _provider_config(
            "chat_analysis",
            api_key=os.getenv("CHAT_ANALYSIS_API_KEY") or os.getenv("OPENAI_API_KEY"),
            model=os.getenv("CHAT_ANALYSIS_MODEL") or os.getenv("OPENAI_CHAT_MODEL") or "gpt-4o-mini",
            base_url=os.getenv("CHAT_ANALYSIS_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            timeout_seconds=os.getenv("CHAT_ANALYSIS_TIMEOUT_SECONDS") or "8",
        ),
        _provider_config(
            "gemma",
            api_key=os.getenv("GEMMA_CHAT_API_KEY") or os.getenv("GEMMA_API_KEY"),
            model=os.getenv("GEMMA_CHAT_MODEL") or os.getenv("GEMMA_MODEL") or "",
            base_url=os.getenv("GEMMA_CHAT_BASE_URL") or os.getenv("GEMMA_BASE_URL") or "",
            timeout_seconds=os.getenv("GEMMA_TIMEOUT_SECONDS") or os.getenv("CHAT_ANALYSIS_TIMEOUT_SECONDS") or "8",
        ),
    ]

    if route == "kazakh":
        priority = ["kazllm", "gemma", "chat_analysis"]
    elif route == "mixed":
        priority = ["kazllm", "chat_analysis", "gemma"]
    else:
        priority = ["chat_analysis", "gemma", "kazllm"]

    indexed = {config["provider"]: config for config in candidates if config}
    return [indexed[name] for name in priority if name in indexed]


def _request_llm_completion(
    provider: Dict[str, object],
    normalized: str,
    sender: Optional[str],
    route: str,
) -> Optional[ParsedMessage]:
    payload = {
        "model": provider["model"],
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты анализатор школьных рабочих сообщений. "
                    "Возвращай только один JSON-объект без пояснений."
                ),
            },
            {"role": "user", "content": _analysis_prompt(normalized, sender, route)},
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{provider['base_url']}/chat/completions",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider['api_key']}",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=float(provider["timeout"])) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        log.warning("%s HTTP error %s: %s", provider["provider"], exc.code, error_body[:300])
        return None
    except Exception as exc:
        log.warning("%s request failed: %s", provider["provider"], exc)
        return None

    try:
        result = json.loads(raw)
        content = result["choices"][0]["message"]["content"]
    except Exception as exc:
        log.warning("%s returned unexpected payload: %s", provider["provider"], exc)
        return None

    parsed_payload = _extract_json(content)
    if not parsed_payload:
        log.warning("%s returned non-JSON content", provider["provider"])
        return None

    parsed_payload = _sanitize_llm_payload(parsed_payload)
    try:
        parsed = ParsedMessage(**parsed_payload)
    except ValidationError as exc:
        log.warning("%s returned schema-mismatched JSON: %s", provider["provider"], exc)
        return None
    parsed.analysis_provider = parsed.analysis_provider or str(provider["provider"])
    parsed.detected_language = parsed.detected_language or route
    return parsed


def _sanitize_llm_payload(payload: dict) -> dict:
    cleaned = dict(payload or {})

    def _scalar(value):
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            for nested in value.values():
                nested_scalar = _scalar(nested)
                if nested_scalar not in (None, "", [], {}):
                    return nested_scalar
            return None
        if isinstance(value, list):
            for nested in value:
                nested_scalar = _scalar(nested)
                if nested_scalar not in (None, "", [], {}):
                    return nested_scalar
            return None
        return str(value)

    entities = cleaned.get("entities")
    if isinstance(entities, list):
        normalized_entities = []
        for item in entities:
            value = _scalar(item)
            if value is None:
                continue
            normalized_entities.append(str(value))
        cleaned["entities"] = normalized_entities[:12]
    elif entities is None:
        cleaned["entities"] = []
    else:
        value = _scalar(entities)
        cleaned["entities"] = [str(value)] if value is not None else []

    string_fields = [
        "type",
        "urgency",
        "summary",
        "teacher_name",
        "class_name",
        "location",
        "issue",
        "assignee",
        "assignee_role",
        "deadline",
        "recurrence",
        "task_title",
        "review_reason",
        "analysis_provider",
        "detected_language",
    ]
    for field in string_fields:
        if field in cleaned:
            value = _scalar(cleaned.get(field))
            cleaned[field] = str(value) if value is not None else None

    int_fields = ["food_count", "present_count", "absent_count"]
    for field in int_fields:
        value = _scalar(cleaned.get(field))
        if value in (None, ""):
            cleaned[field] = None
            continue
        try:
            cleaned[field] = int(float(str(value).replace(",", ".")))
        except Exception:
            cleaned[field] = None

    float_value = _scalar(cleaned.get("confidence"))
    try:
        cleaned["confidence"] = float(float_value)
    except Exception:
        cleaned["confidence"] = 0.0

    bool_fields = ["is_acceptance", "requires_substitution", "requires_review"]
    for field in bool_fields:
        value = _scalar(cleaned.get(field))
        if isinstance(value, bool):
            cleaned[field] = value
        elif isinstance(value, (int, float)):
            cleaned[field] = bool(value)
        elif isinstance(value, str):
            cleaned[field] = value.strip().lower() in {"1", "true", "yes", "да"}
        else:
            cleaned[field] = False

    if not cleaned.get("recurrence"):
        cleaned["recurrence"] = "spontaneous"

    return cleaned


def _extract_location(text: str) -> Optional[str]:
    match = LOCATION_RE_SAFE.search(text or "") or LOCATION_RE.search(text or "")
    if not match:
        named = re.search(
            r"(актовый зал|спортзал|библиотек[аеи]|учительск[аяой]|столов[аяой]|медпункт|коридор|левое крыло|правое крыло)",
            text or "",
            re.IGNORECASE,
        )
        return named.group(1).capitalize() if named else None
    prefix = (match.group(1) or "").strip().upper()
    number = match.group(2).strip()
    return f"{prefix} {number}".strip() if prefix else f"Каб. {number}"


def _extract_task_bits(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    normalized = _normalized_text(text)
    match = ASSIGNEE_RE_SAFE.match(normalized) or ASSIGNEE_RE.match(normalized)
    assignee = None
    assignee_role = None
    body = normalized

    if match:
        assignee_raw = match.group("assignee").strip()
        body = match.group("body").strip()
        lowered = assignee_raw.lower()
        if lowered in ROLE_NORMALIZATION:
            assignee_role = ROLE_NORMALIZATION[lowered]
            assignee = assignee_role
        else:
            assignee = assignee_raw

    deadline_match = DEADLINE_RE_SAFE.search(body) or DEADLINE_RE.search(body)
    deadline = deadline_match.group(1).strip().capitalize() if deadline_match else None
    task_title = re.sub(DEADLINE_RE_SAFE, "", body)
    task_title = re.sub(DEADLINE_RE, "", task_title).strip(" ,.;")
    task_title = task_title[:1].upper() + task_title[1:] if task_title else None
    recurrence = "recurring" if any(
        marker in normalized.lower()
        for marker in ("каждый", "ежедневно", "еженедельно", "по графику", "регулярно")
    ) else "spontaneous"
    return assignee, assignee_role, deadline, recurrence if task_title else "spontaneous"


def _build_fallback(text: str, sender: Optional[str] = None) -> ParsedMessage:
    normalized = _normalized_text(text)
    lowered = normalized.lower()

    if lowered in ACCEPTANCE_PATTERNS or len(lowered) <= 12 and any(word in lowered for word in ACCEPTANCE_PATTERNS):
        return ParsedMessage(
            type="other",
            urgency="low",
            summary="Подтверждение получения задачи",
            entities=[sender] if sender else [],
            is_acceptance=True,
            confidence=0.96,
        )

    class_match = FOOD_CLASS_RE_SAFE.search(normalized) or FOOD_CLASS_RE.search(normalized)
    count_match = FOOD_COUNT_RE_SAFE.search(normalized) or FOOD_COUNT_RE.search(normalized)
    absent_match = ABSENT_COUNT_RE_SAFE.search(normalized) or ABSENT_COUNT_RE.search(normalized)
    if class_match and (count_match or "питани" in lowered or "дет" in lowered):
        class_name = class_match.group(1).replace(" ", "").upper()
        main_count = int(count_match.group(1)) if count_match else None
        absent_count = int(absent_match.group(1)) if absent_match else None
        food_count = main_count
        if "на питание" not in lowered and main_count and absent_count:
            food_count = max(main_count - absent_count, 0)
        return ParsedMessage(
            type="food",
            urgency="low",
            summary=f"Сводка по питанию для {class_name}: {food_count or main_count or '?'} порций",
            entities=[class_name],
            confidence=0.78,
            class_name=class_name,
            present_count=main_count,
            absent_count=absent_count,
            food_count=food_count,
        )

    if any(keyword in lowered for keyword in MEDICAL_KEYWORDS) and not any(keyword in lowered for keyword in ABSENCE_KEYWORDS):
        location = _extract_location(normalized)
        return ParsedMessage(
            type="medical",
            urgency="high",
            summary="Медицинский случай требует немедленной реакции",
            entities=[sender] if sender else [],
            confidence=0.72,
            location=location,
            issue=normalized,
        )

    if any(keyword in lowered for keyword in ABSENCE_KEYWORDS):
        teacher_name = sender
        found_name = re.search(r"учитель\s+([А-ЯЁA-Z][а-яёa-z]+)", normalized)
        if found_name:
            teacher_name = found_name.group(1)
        return ParsedMessage(
            type="absence",
            urgency="high",
            summary=f"Отсутствие сотрудника: {teacher_name or 'не указано'}, требуется замена",
            entities=[teacher_name] if teacher_name else [],
            confidence=0.8,
            teacher_name=teacher_name,
            requires_substitution=True,
        )

    if any(keyword in lowered for keyword in INCIDENT_KEYWORDS):
        location = _extract_location(normalized)
        return ParsedMessage(
            type="incident",
            urgency="high",
            summary=f"Инцидент в школе: {normalized[:90]}",
            entities=[sender] if sender else [],
            confidence=0.77,
            location=location,
            issue=normalized,
            assignee="Серик",
            assignee_role="Техработник",
            deadline="Срочно",
            task_title=(normalized[:1].upper() + normalized[1:]) if normalized else "Устранить инцидент",
        )

    if any(keyword in lowered for keyword in TASK_KEYWORDS) or ASSIGNEE_RE_SAFE.match(normalized) or ASSIGNEE_RE.match(normalized):
        assignee, assignee_role, deadline, recurrence = _extract_task_bits(normalized)
        task_title = re.sub(r"^[^:,]+[:,-]\s*", "", normalized) if (ASSIGNEE_RE_SAFE.match(normalized) or ASSIGNEE_RE.match(normalized)) else normalized
        task_title = task_title[:1].upper() + task_title[1:] if task_title else "Новая задача"
        return ParsedMessage(
            type="task",
            urgency="medium",
            summary=f"Поручение: {task_title[:80]}",
            entities=[entity for entity in [assignee or assignee_role, sender] if entity],
            confidence=0.68,
            assignee=assignee,
            assignee_role=assignee_role,
            deadline=deadline or "В течение дня",
            recurrence=recurrence,
            task_title=task_title,
        )

    return ParsedMessage(
        type="other",
        urgency="low",
        summary=normalized[:100] or "Сообщение без явного действия",
        entities=[sender] if sender else [],
        confidence=0.45,
    )


def _analysis_prompt(text: str, sender: Optional[str], route: str = "default") -> str:
    language_hint = (
        "Сообщение может быть на казахском языке или на смеси казахского и русского. "
        "Корректно нормализуй казахские имена, роли сотрудников и школьные формулировки."
        if route in {"kazakh", "mixed"}
        else "Сообщение может быть на русском языке или на смеси русского и казахского."
    )
    return f"""
Проанализируй сообщение сотрудника школы и верни только один JSON-объект.

Контекст:
- sender: {sender or "unknown"}
- text: {text}
- language_hint: {language_hint}

Допустимые type: "food", "absence", "incident", "medical", "task", "other".
Допустимые urgency: "high", "medium", "low".
recurrence: "spontaneous" или "recurring".

Правила:
1. Если это отчет по классу и питанию, извлеки class_name, present_count, absent_count, food_count.
2. Если это отсутствие учителя/сотрудника, укажи teacher_name и requires_substitution=true.
3. Если это инцидент, извлеки location и issue.
4. Если это поручение, извлеки assignee или assignee_role, deadline и task_title.
5. Если это краткое подтверждение вроде "ок", "принял", "сделаю", поставь is_acceptance=true.
6. confidence должен быть числом от 0 до 1.
7. summary должен быть коротким, понятным директору.
8. Если данных нет, ставь null или [].

Структура JSON:
{{
  "type": "task",
  "urgency": "medium",
  "summary": "Короткое описание",
  "entities": [],
  "confidence": 0.0,
  "teacher_name": null,
  "class_name": null,
  "food_count": null,
  "present_count": null,
  "absent_count": null,
  "location": null,
  "issue": null,
  "assignee": null,
  "assignee_role": null,
 "deadline": null,
  "recurrence": "spontaneous",
  "task_title": null,
  "requires_substitution": false,
  "is_acceptance": false,
  "requires_review": false,
  "review_reason": null,
  "analysis_provider": null,
  "detected_language": null
}}
""".strip()


def _enrich_with_regulations(parsed: ParsedMessage, text: str) -> ParsedMessage:
    orders_found = re.findall(r"\b(76|110|130)\b", text)
    if orders_found:
        rag_info = {}
        for order in set(orders_found):
            rag_info[f"order_{order}"] = {
                "explanation": check_compliance(f"Приказ {order}").get("analysis"),
                "checklist": translate_to_checklist(f"приказ {order}"),
            }
        parsed.rag_insights = rag_info

    if parsed.type == "absence" and parsed.teacher_name:
        try:
            parsed.substitution_plan = find_substitution(parsed.teacher_name)
        except Exception:
            parsed.substitution_plan = []

    return parsed


def _review_threshold(message_type: str) -> float:
    if message_type in {"absence", "incident", "medical"}:
        return 0.72
    if message_type == "food":
        return 0.62
    if message_type == "task":
        return 0.68
    return 0.55


def _finalize_result(parsed: ParsedMessage, fallback: ParsedMessage, normalized: str) -> ParsedMessage:
    if parsed.type == "medical" and parsed.requires_substitution and fallback.type == "absence":
        promoted = fallback.model_copy(deep=True)
        promoted.analysis_provider = (
            f"{parsed.analysis_provider}+absence_bridge" if parsed.analysis_provider else "absence_bridge"
        )
        promoted.detected_language = parsed.detected_language or fallback.detected_language
        return _enrich_with_regulations(promoted, normalized)

    if (
        fallback.type != "other"
        and parsed.type != fallback.type
        and fallback.confidence >= 0.75
        and parsed.confidence <= max(fallback.confidence, 0.86)
    ):
        guarded = fallback.model_copy(deep=True)
        guarded.analysis_provider = (
            f"{parsed.analysis_provider}+guardrail" if parsed.analysis_provider else "fallback_guardrail"
        )
        guarded.detected_language = parsed.detected_language or fallback.detected_language
        return _enrich_with_regulations(guarded, normalized)

    if parsed.type == "other" and fallback.type != "other" and parsed.confidence < 0.7:
        parsed.type = fallback.type
        parsed.summary = fallback.summary

    if not parsed.summary:
        parsed.summary = fallback.summary
    if parsed.confidence <= 0:
        parsed.confidence = 0.51
    if parsed.type == "food" and not parsed.food_count:
        parsed.food_count = fallback.food_count
    if parsed.type == "food" and parsed.present_count and parsed.absent_count is not None and not parsed.food_count:
        parsed.food_count = max(parsed.present_count - parsed.absent_count, 0)
    if not parsed.class_name:
        parsed.class_name = fallback.class_name
    if not parsed.location:
        parsed.location = fallback.location
    if not parsed.teacher_name:
        parsed.teacher_name = fallback.teacher_name
    if not parsed.assignee:
        parsed.assignee = fallback.assignee
    if not parsed.assignee_role:
        parsed.assignee_role = fallback.assignee_role
    if not parsed.deadline:
        parsed.deadline = fallback.deadline
    if not parsed.task_title:
        parsed.task_title = fallback.task_title
    if not parsed.entities:
        parsed.entities = fallback.entities
    if parsed.type == "incident" and not parsed.assignee:
        parsed.assignee = "Серик"
        parsed.assignee_role = parsed.assignee_role or "Техработник"
        parsed.deadline = parsed.deadline or "Срочно"

    threshold = _review_threshold(parsed.type)
    if not parsed.is_acceptance and parsed.confidence < threshold:
        parsed.requires_review = True
        if not parsed.review_reason:
            parsed.review_reason = f"confidence_below_threshold:{threshold:.2f}"

    return _enrich_with_regulations(parsed, normalized)


def parse_with_llm(text: str, sender: Optional[str] = None) -> ParsedMessage:
    normalized = _normalized_text(text)
    fallback = _build_fallback(normalized, sender=sender)
    route = _detect_language_route(normalized)
    fallback.detected_language = route
    client, model, provider = _build_client(route)
    if not client or not model:
        fallback.analysis_provider = "fallback"
        return _enrich_with_regulations(fallback, normalized)

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты анализатор школьных рабочих сообщений. "
                        "Твоя задача — превращать сообщения учителей и сотрудников в строгий JSON без пояснений."
                    ),
                },
                {"role": "user", "content": _analysis_prompt(normalized, sender, route)},
            ],
        )
        content = response.choices[0].message.content or ""
        payload = _extract_json(content)
        if not payload:
            raise ValueError("llm_returned_non_json")

        parsed = ParsedMessage(**payload)
        parsed.analysis_provider = parsed.analysis_provider or provider or "llm"
        parsed.detected_language = parsed.detected_language or route
        return _finalize_result(parsed, fallback, normalized)
    except Exception as exc:
        print(f"[LLM Parser] fallback triggered: {exc}")
        fallback.analysis_provider = "fallback"
        return _finalize_result(fallback, fallback, normalized)


def parse_with_llm(text: str, sender: Optional[str] = None) -> ParsedMessage:
    normalized = _normalized_text(text)
    fallback = _build_fallback(normalized, sender=sender)
    route = _detect_language_route(normalized)
    fallback.detected_language = route

    providers = _provider_candidates(route)
    if not providers:
        fallback.analysis_provider = "fallback"
        return _enrich_with_regulations(fallback, normalized)

    for provider in providers:
        parsed = _request_llm_completion(provider, normalized, sender, route)
        if parsed:
            return _finalize_result(parsed, fallback, normalized)

    fallback.analysis_provider = "fallback"
    return _finalize_result(fallback, fallback, normalized)
