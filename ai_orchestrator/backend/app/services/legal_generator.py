import os
import json
from datetime import datetime
from pydantic import BaseModel, Field

class OrderContent(BaseModel):
    header: str = Field(description="Шапка документа (наименование школы)")
    order_number: str = Field(description="Номер приказа")
    order_date: str = Field(description="Дата приказа")
    preamble: str = Field(description="Преамбула (на основании каких приказов/ситуации)")
    order_body_ru: str = Field(description="Текст приказа на русском языке — нумерованные пункты")
    order_body_kz: str = Field(description="Текст приказа на казахском языке — нумерованные пункты")
    signatories: str = Field(description="Подписи (Директор, ознакомленные)")


# RAG-контекст: ключевые выжимки из нормативных актов МОН РК
RAG_CONTEXT = """
=== Приказ МОН РК №110 (Замены учителей) ===
Замена временно отсутствующих учителей производится специалистами той же предметной области.
При отсутствии возможности — учителями смежных дисциплин.
Все замены фиксируются в журнале учета пропущенных и замещенных уроков (ЖУПЗ).
Оплата производится за фактически проведенные часы согласно квалификации замещающего педагога.

=== Приказ МОН РК №130 (Документооборот) ===
Факт замещения обязательно фиксируется внутренним приказом директора.
Основание приказа: сообщение о нетрудоспособности / служебная записка.
Замещающий педагог обязан внести записи в электронный журнал (Күнделік).
Данные о замене направляются в бухгалтерию для начисления оплаты.

=== Приказ МОН РК №76 (Квалификация педагогов) ===
Замену должен производить педагог, соответствующий квалификационным требованиям по данному предмету.
"""

MOCK_PREAMBLE_TEMPLATE = (
    "В связи с временной нетрудоспособностью учителя {missing_teacher} и в целях "
    "обеспечения выполнения государственных общеобязательных стандартов образования, "
    "недопущения срыва учебного процесса и соблюдения норм Приказа МОН РК №110,"
)

MOCK_BODY_RU_TEMPLATE = """1. Произвести замену учебных занятий в {class_name} классе, кабинет {room}, {lesson_number}-й урок.
2. Возложить временное исполнение обязанностей по проведению урока на учителя {substitute_teacher} согласно утвержденному расписанию.
3. Оплату за фактически проведенные часы замещения произвести в соответствии с нормативными правовыми актами РК и внутренним положением об оплате труда, исходя из квалификации и стажа замещающего педагога — согласно Приказу №110 МОН РК.
4. Учителю {substitute_teacher} обеспечить качественное проведение занятий и своевременное внесение записей в электронный журнал (Күнделік) — согласно Приказу №130 МОН РК.
5. Секретарю передать копию настоящего приказа в бухгалтерию для начисления доплаты.
Основание: Приказ МОН РК №130, сообщение о временной нетрудоспособности от {date}."""

MOCK_BODY_KZ_TEMPLATE = """1. {class_name} сыныбындағы, {room} кабинетте, {lesson_number}-сабақты ауыстыруды жүзеге асыру.
2. Сабақты өткізу бойынша міндеттерді уақытша атқаруды бекітілген кесте бойынша {substitute_teacher} мұғаліміне жүктеу.
3. Ауыстыру сағаттары үшін ақы төлеуді ҚР нормативтік-құқықтық актілеріне сәйкес жүзеге асыру — МОН РК №110 бұйрығына сәйкес.
4. {substitute_teacher} мұғаліміне сабақтарды сапалы өткізуді және Күнделік электрондық журналына жазбаларды енгізуді қамтамасыз ету — МОН РК №130 бұйрығына сәйкес.
5. Хатшыға осы бұйрықтың көшірмесін қосымша төлем есептеу үшін бухгалтерияға жеткізу.
Негіздеме: МОН РК №130 бұйрығы, {date} күнгі уақытша еңбекке жарамсыздық туралы хабарлама."""


def generate_substitution_order(
    missing_teacher: str,
    substitute_teacher: str,
    lesson_number: int,
    class_name: str,
    room: str,
) -> OrderContent:
    """
    Generates an official substitution order using Gemini LLM with RAG context.
    Falls back to a high-quality template if the API key is not set.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY", "mock")
    current_date = datetime.now().strftime("%d.%m.%Y")

    # --- Attempt real LLM generation via Gemini ---
    if api_key and api_key not in ("mock", "test_mock") and not api_key.startswith("sk-abcdef"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            prompt = f"""
Ты профессиональный юрист-документовед в системе образования Казахстана.

Нормативная база (RAG):
{RAG_CONTEXT}

Задача: составь официальный приказ о замене учебных часов.

Исходные данные:
- Школа: Образовательный комплекс «Aqbobek International School», г. Актобе
- Отсутствующий учитель: {missing_teacher}
- Замещающий учитель: {substitute_teacher}
- Класс: {class_name}
- Кабинет: {room}
- Номер урока: {lesson_number}
- Дата: {current_date}

Требования к документу:
1. Преамбула: начинается с «В связи с временной нетрудоспособностью учителя {missing_teacher}...»
2. Распорядительная часть (поле order_body_ru): 5 нумерованных пунктов (замена, исполнитель, оплата, Күнделік, секретарю), со ссылками на Приказ №110 и №130.
3. Казахская версия (поле order_body_kz): точный перевод пунктов.
4. Строго официально-деловой стиль.

Верни JSON строго в следующем формате без лишних слов:
{{
  "preamble": "...",
  "order_body_ru": "1. ...\n2. ...\n3. ...\n4. ...\n5. ...",
  "order_body_kz": "1. ...\n2. ...\n3. ...\n4. ...\n5. ..."
}}
"""
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)

            return OrderContent(
                header="КГУ «Начальная школа образовательного комплекса Aqbobek» г. Актобе",
                order_number=f"78-{lesson_number}",
                order_date=current_date,
                preamble=data.get("preamble", MOCK_PREAMBLE_TEMPLATE.format(missing_teacher=missing_teacher)),
                order_body_ru=data.get("order_body_ru", ""),
                order_body_kz=data.get("order_body_kz", ""),
                signatories=f"Директор школы: __________ / Сарсенбаев А.Т.\nОзнакомлен(а): __________ / {substitute_teacher}",
            )
        except Exception as e:
            print(f"[LegalGen] Gemini error, falling back to template: {e}")

    # --- High-quality template fallback (works without API key) ---
    return OrderContent(
        header="КГУ «Начальная школа образовательного комплекса Aqbobek» г. Актобе",
        order_number=f"78-{lesson_number}",
        order_date=current_date,
        preamble=MOCK_PREAMBLE_TEMPLATE.format(missing_teacher=missing_teacher),
        order_body_ru=MOCK_BODY_RU_TEMPLATE.format(
            class_name=class_name,
            room=room,
            lesson_number=lesson_number,
            substitute_teacher=substitute_teacher,
            date=current_date,
        ),
        order_body_kz=MOCK_BODY_KZ_TEMPLATE.format(
            class_name=class_name,
            room=room,
            lesson_number=lesson_number,
            substitute_teacher=substitute_teacher,
            date=current_date,
        ),
        signatories=f"Директор школы: __________ / Сарсенбаев А.Т.\nОзнакомлен(а): __________ / {substitute_teacher}",
    )
