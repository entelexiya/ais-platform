"""
RAG сервис — семантический поиск по приказам МОН РК.
Работает в двух режимах:
  1. Без API ключа: keyword-matching по реальным текстам приказов (DOCS_DIR/*.txt)
  2. С OpenAI ключом: полноценный векторный FAISS поиск
"""
import os
import glob
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "rag", "documents")

vectorstore = None
_docs_cache: dict = {}  # filename -> text


def _load_docs() -> dict:
    """Загружает все .txt файлы приказов в память."""
    global _docs_cache
    if _docs_cache:
        return _docs_cache
    for path in glob.glob(os.path.join(DOCS_DIR, "*.txt")):
        name = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as f:
                _docs_cache[name] = f.read()
        except Exception as e:
            print(f"Ошибка загрузки {name}: {e}")
    print(f"RAG: загружено {len(_docs_cache)} документов из {DOCS_DIR}")
    return _docs_cache


def _keyword_search(query: str, top_k: int = 2) -> list[dict]:
    """
    Простой keyword-поиск по загруженным документам.
    Считает количество совпадений ключевых слов и возвращает top_k лучших фрагментов.
    """
    docs = _load_docs()
    query_words = set(re.findall(r'\w+', query.lower()))
    results = []

    for filename, text in docs.items():
        # Разбиваем на параграфы
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
        for para in paragraphs:
            para_words = set(re.findall(r'\w+', para.lower()))
            score = len(query_words & para_words)
            if score > 0:
                results.append({"text": para, "source": filename, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def _order_label(filename: str) -> str:
    mapping = {
        "prikaz_76_attestaciya.txt": "Приказ №76 МОН РК (Аттестация)",
        "prikaz_110_zamena.txt": "Приказ №110 МОН РК (Замены)",
        "prikaz_130_pitanie.txt": "Приказ №130 МОН РК (Питание)",
    }
    return mapping.get(filename, filename)


def _format_answer(query: str, fragments: list[dict]) -> dict:
    """Формирует финальный ответ на основе найденных фрагментов."""
    if not fragments:
        return {
            "compliant": True,
            "query": query,
            "relevant_orders": [],
            "analysis": "Соответствующих норм в базе приказов не найдено.",
        }

    sources = list({_order_label(f["source"]) for f in fragments})
    combined = "\n\n".join(f["text"] for f in fragments)

    # Базовый анализ: ищем нарушения
    violation_keywords = ["запрещено", "недопустимо", "не допускается", "нарушение", "ответственность"]
    is_violation = any(kw in combined.lower() for kw in violation_keywords) and \
                   any(kw in query.lower() for kw in violation_keywords)

    return {
        "compliant": not is_violation,
        "query": query,
        "relevant_orders": sources,
        "analysis": combined[:600] + ("..." if len(combined) > 600 else ""),
    }


# ─── Публичные функции ────────────────────────────────────────

def init_rag():
    """Запускается при старте FastAPI. Пробует FAISS, иначе keyword режим."""
    global vectorstore
    api_key = os.getenv("OPENAI_API_KEY", "mock")

    _load_docs()  # Всегда загружаем документы

    if api_key in ("mock", "test_mock"):
        print("RAG: keyword-режим (без OpenAI). Документы загружены.")
        return

    try:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from langchain_community.document_loaders import TextLoader
        from langchain_text_splitters import CharacterTextSplitter
        from langchain_community.vectorstores import FAISS

        documents = []
        for path in glob.glob(os.path.join(DOCS_DIR, "*.txt")):
            loader = TextLoader(path, encoding="utf-8")
            documents.extend(loader.load())

        splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        texts = splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        vectorstore = FAISS.from_documents(texts, embeddings)
        print("RAG: FAISS vectorstore инициализирован.")
    except Exception as e:
        print(f"RAG: FAISS недоступен ({e}). Используем keyword-режим.")


def check_compliance(query: str) -> dict:
    """Проверяет запрос на соответствие приказам."""
    api_key = os.getenv("OPENAI_API_KEY", "mock")

    # FAISS режим
    if vectorstore and api_key not in ("mock", "test_mock"):
        try:
            from langchain_openai import ChatOpenAI
            docs = vectorstore.similarity_search(query, k=2)
            context = "\n".join([d.page_content for d in docs])
            llm = ChatOpenAI(temperature=0, openai_api_key=api_key)
            analysis = llm.predict(
                f"Официальные приказы:\n{context}\n\nОцени ситуацию: \"{query}\". Нарушает ли это приказы?"
            )
            return {
                "compliant": "нарушает" not in analysis.lower(),
                "query": query,
                "relevant_orders": [d.metadata.get("source", "Unknown") for d in docs],
                "analysis": analysis,
            }
        except Exception as e:
            print(f"FAISS error: {e}")

    # Keyword режим — реальный поиск по текстам
    fragments = _keyword_search(query)
    return _format_answer(query, fragments)


def translate_to_checklist(order_text: str) -> list:
    """
    Превращает запрос в чек-лист.
    Если есть API-ключ — через LLM. Иначе — извлекаем пункты из реального текста.
    """
    api_key = os.getenv("OPENAI_API_KEY", "mock")

    if api_key not in ("mock", "test_mock"):
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(temperature=0, openai_api_key=api_key)
            result = llm.predict(
                f"Переведи бюрократический текст в простой пошаговый чек-лист для учителя:\n{order_text}"
            )
            return [line.strip("- *1234567890.").strip() for line in result.split("\n") if line.strip()]
        except Exception:
            pass

    # Keyword режим — достаём пронумерованные пункты из реальных документов
    fragments = _keyword_search(order_text, top_k=3)
    checklist = []
    for frag in fragments:
        # Вытаскиваем строки которые похожи на правила (начинаются с цифры или тире)
        lines = frag["text"].split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped and (stripped[0].isdigit() or stripped.startswith("-") or stripped.startswith("а)") or stripped.startswith("б)")):
                clean = re.sub(r'^[\d\.\-\)а-яa-z]\s*', '', stripped).strip()
                if len(clean) > 20:
                    checklist.append(clean)

    # Fallback если ничего не нашли
    if not checklist:
        order_map = {
            "130": [
                "Передать данные о посещаемости до 09:00 ответственному за питание",
                "Указать: класс, общее кол-во, присутствующих, льготников",
                "При отсутствии >3 дней — связаться с родителями и сообщить соцпедагогу",
                "Данные по льготному питанию — соцпедагогу до 10:00",
            ],
            "110": [
                "В день отсутствия подобрать замещающего педагога (сначала — той же специализации)",
                "Издать приказ/распоряжение о замещении с указанием ФИО, часов и даты",
                "Внести запись в Журнал учёта пропущенных и замещённых уроков (ЖУПЗ)",
                "Уведомить замещающего не позднее чем за 1 час до урока",
                "Оплата — за фактически проведённые уроки по тарифной ставке",
            ],
            "76": [
                "Аттестация проводится раз в 5 лет — директор ведёт реестр сроков",
                "Уведомить педагога не позднее чем за 6 месяцев до аттестации",
                "Педагог загружает Портфолио в систему за 2 месяца до экзамена",
                "Категории: модератор/эксперт (+30% БДО), исследователь/мастер (+50% БДО)",
                "Отказ от аттестации = рассмотрение вопроса о соответствии должности",
            ],
        }
        for num, items in order_map.items():
            if num in order_text:
                return items
        return ["Нормы по данному запросу: соответствуйте профилю замещающего учителя", "Ведите ЖУПЗ", "Уведомляйте заменяющего за 1 час"]

    return checklist[:6]
