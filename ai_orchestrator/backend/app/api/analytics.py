"""
API: Генерация аналитического отчёта для директора.
Собирает реальные данные из БД, строит структуру через AI (или fallback),
возвращает готовый HTML для печати/PDF.
"""
import os
import json
import sqlite3
from fastapi import APIRouter
from datetime import datetime, timedelta
from app.api.bot_feed import _get_conn, _ensure_table

router = APIRouter()

def _get_stats(date_from: str, date_to: str) -> dict:
    """Собирает статистику из orchestrator.db за указанный период."""
    _ensure_table()

    try:
        conn = _get_conn()

        # Всего сообщений
        total_msgs = conn.execute(
            "SELECT COUNT(*) FROM tg_messages WHERE date(created_at) >= ? AND date(created_at) <= ?", (date_from, date_to)
        ).fetchone()[0]

        # По типам
        type_rows = conn.execute(
            "SELECT parsed_type, COUNT(*) as cnt FROM tg_messages WHERE date(created_at) >= ? AND date(created_at) <= ? GROUP BY parsed_type",
            (date_from, date_to)
        ).fetchall()
        type_counts = {r[0]: r[1] for r in type_rows}

        # Свод питания
        food_rows = conn.execute(
            "SELECT food_class, SUM(food_count) as total FROM tg_messages "
            "WHERE parsed_type='food' AND food_count IS NOT NULL AND date(created_at) >= ? AND date(created_at) <= ? GROUP BY food_class",
            (date_from, date_to)
        ).fetchall()
        food_data = {r[0]: r[1] for r in food_rows if r[0]}
        total_food = sum(food_data.values())

        # Задачи
        tasks = conn.execute("SELECT COUNT(*) FROM task_reminders").fetchone()[0]
        tasks_done = conn.execute("SELECT COUNT(*) FROM task_reminders WHERE is_completed=1").fetchone()[0]
        tasks_accepted = conn.execute("SELECT COUNT(*) FROM task_reminders WHERE is_accepted=1 AND is_completed=0").fetchone()[0]
        tasks_pending = tasks - tasks_done - tasks_accepted

        # Инциденты с локациями
        incidents = conn.execute(
            "SELECT sender, text, location, created_at FROM tg_messages "
            "WHERE parsed_type IN ('incident','medical') AND date(created_at) >= ? AND date(created_at) <= ? ORDER BY id DESC LIMIT 5",
            (date_from, date_to)
        ).fetchall()
        incidents_list = [{"sender": r[0], "text": r[1], "location": r[2], "time": r[3]} for r in incidents]

        # Отсутствия
        absences = conn.execute(
            "SELECT COUNT(*) FROM tg_messages WHERE parsed_type='absence' AND date(created_at) >= ? AND date(created_at) <= ?",
            (date_from, date_to)
        ).fetchone()[0]

        conn.close()
        return {
            "period": f"{date_from} — {date_to}",
            "total_messages": total_msgs,
            "type_counts": type_counts,
            "total_food_portions": total_food,
            "food_by_class": food_data,
            "tasks_total": tasks,
            "tasks_done": tasks_done,
            "tasks_accepted": tasks_accepted,
            "tasks_pending": tasks_pending,
            "incidents": incidents_list,
            "absences": absences,
        }
    except Exception as e:
        print(f"[Analytics] DB error: {e}")
        return {}


def _generate_report_html(stats: dict, ai_summary: str) -> str:
    today_str = datetime.now().strftime("%d.%m.%Y")
    efficiency = round((stats.get("tasks_done", 0) / max(stats.get("tasks_total", 1), 1)) * 100)

    # Извлекаем в переменные ДО f-строки, чтобы избежать проблем с {{}}
    tc = stats.get("type_counts") or {}
    cnt_food     = tc.get("food", 0)
    cnt_absence  = tc.get("absence", 0)
    cnt_incident = tc.get("incident", 0)
    cnt_medical  = tc.get("medical", 0)
    cnt_other    = tc.get("other", 0)
    period       = stats.get("period", "—")

    food_rows = "".join(
        f"<tr><td>{cls}</td><td><b>{cnt}</b></td></tr>"
        for cls, cnt in (stats.get("food_by_class") or {}).items()
    )
    incident_rows = "".join(
        f"<tr><td>{i.get('time','')[:16]}</td><td>{i.get('sender','')}</td><td>{i.get('text','')[:60]}</td><td>{i.get('location') or '—'}</td></tr>"
        for i in (stats.get("incidents") or [])
    )

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Аналитический отчёт — Aqbobek AI Orchestrator</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', Arial, sans-serif; background: #f0f4f8; display: flex; justify-content: center; padding: 40px 20px; color: #1e293b; }}
    .page {{ background: white; width: 210mm; min-height: 297mm; padding: 18mm 16mm; box-shadow: 0 8px 40px rgba(0,0,0,0.12); position: relative; border-radius: 6px; }}
    .stripe {{ position: absolute; top: 0; left: 0; right: 0; height: 8px; background: linear-gradient(90deg, #1d4ed8, #2563eb, #7c3aed); border-radius: 4px 4px 0 0; }}
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 20px; }}
    .logo-block h1 {{ font-size: 22pt; font-weight: 900; color: #1d4ed8; letter-spacing: -0.5px; }}
    .logo-block p {{ font-size: 9pt; color: #64748b; margin-top: 2px; }}
    .meta {{ text-align: right; font-size: 8.5pt; color: #64748b; line-height: 1.6; }}
    .meta b {{ color: #1e293b; }}
    .ai-block {{ background: linear-gradient(135deg, #eff6ff, #f5f3ff); border: 1px solid #bfdbfe; border-radius: 12px; padding: 14px 18px; margin-bottom: 20px; }}
    .ai-block .label {{ font-size: 7.5pt; font-weight: 900; text-transform: uppercase; letter-spacing: 0.12em; color: #2563eb; margin-bottom: 6px; }}
    .ai-block p {{ font-size: 10.5pt; color: #1e293b; line-height: 1.65; }}
    .section-title {{ font-size: 12pt; font-weight: 900; color: #1e293b; text-transform: uppercase; letter-spacing: 0.06em; margin: 18px 0 10px; border-left: 4px solid #2563eb; padding-left: 10px; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }}
    .kpi {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; text-align: center; }}
    .kpi .val {{ font-size: 22pt; font-weight: 900; color: #1d4ed8; line-height: 1; }}
    .kpi .lbl {{ font-size: 7.5pt; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px; font-weight: 600; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 9.5pt; }}
    th {{ background: #1d4ed8; color: white; padding: 7px 10px; text-align: left; font-weight: 700; font-size: 8.5pt; text-transform: uppercase; letter-spacing: 0.06em; }}
    td {{ padding: 6px 10px; border-bottom: 1px solid #f1f5f9; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:nth-child(even) td {{ background: #f8fafc; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 8pt; font-weight: 700; }}
    .badge-green {{ background: #dcfce7; color: #166534; }}
    .badge-amber {{ background: #fef3c7; color: #92400e; }}
    .badge-red {{ background: #fee2e2; color: #991b1b; }}
    .sig-block {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-between; font-size: 9.5pt; }}
    .sig-line {{ border-bottom: 1px solid #94a3b8; width: 120px; display: inline-block; margin: 0 8px; }}
    .footer {{ margin-top: 16px; text-align: center; font-size: 7.5pt; color: #94a3b8; }}
    .print-btn {{ position: fixed; bottom: 28px; right: 28px; background: #1d4ed8; color: white; border: none; border-radius: 50px; padding: 12px 26px; font-size: 12pt; font-family: 'Inter', Arial, sans-serif; font-weight: 700; cursor: pointer; box-shadow: 0 4px 20px rgba(37,99,235,0.4); z-index: 999; }}
    @media print {{ body {{ background: none; padding: 0; }} .page {{ box-shadow: none; border-radius: 0; width: 100%; min-height: unset; }} .print-btn {{ display: none !important; }} }}
  </style>
</head>
<body>
<div class="page">
  <div class="stripe"></div>

  <div class="header">
    <div class="logo-block">
      <h1>Aqbobek AI Orchestrator</h1>
      <p>Аналитический отчёт директора</p>
      <p style="margin-top:4px;font-size:8pt;color:#64748b">Образовательный комплекс «Aqbobek International School»</p>
    </div>
    <div class="meta">
      <div><b>Дата генерации:</b> {today_str}</div>
      <div><b>Период:</b> {period}</div>
      <div style="margin-top:6px"><span class="badge badge-green">✓ Сформировано системой Aqbobek AI Orchestrator</span></div>
    </div>
  </div>

  <div class="ai-block">
    <div class="label">🧠 AI-анализ ситуации</div>
    <p>{ai_summary}</p>
  </div>

  <div class="section-title">📊 Ключевые показатели недели</div>
  <div class="kpi-grid">
    <div class="kpi"><div class="val">{stats.get("total_messages",0)}</div><div class="lbl">Сообщений</div></div>
    <div class="kpi"><div class="val">{stats.get("total_food_portions",0)}</div><div class="lbl">Порций питания</div></div>
    <div class="kpi"><div class="val">{stats.get("absences",0)}</div><div class="lbl">Отсутствий</div></div>
    <div class="kpi"><div class="val">{efficiency}%</div><div class="lbl">Задач выполнено</div></div>
  </div>

  <div class="section-title">✅ Статус задач</div>
  <table>
    <tr><th>Категория</th><th>Кол-во</th><th>Статус</th></tr>
    <tr><td>Выполнено</td><td><b>{stats.get("tasks_done",0)}</b></td><td><span class="badge badge-green">Закрыто</span></td></tr>
    <tr><td>Принято исполнителем</td><td><b>{stats.get("tasks_accepted",0)}</b></td><td><span class="badge badge-amber">В работе</span></td></tr>
    <tr><td>Ожидает подтверждения</td><td><b>{stats.get("tasks_pending",0)}</b></td><td><span class="badge badge-red">Ожидание</span></td></tr>
  </table>

  <div class="section-title">🍽 Свод по питанию (за неделю)</div>
  <table>
    <tr><th>Класс</th><th>Порций</th></tr>
    {food_rows if food_rows else '<tr><td colspan="2" style="color:#94a3b8;text-align:center">Нет данных за период</td></tr>'}
    <tr style="background:#eff6ff"><td><b>Итого</b></td><td><b>{stats.get("total_food_portions",0)}</b></td></tr>
  </table>

  <div class="section-title">🚨 Инциденты и медицинские случаи</div>
  <table>
    <tr><th>Время</th><th>Отправитель</th><th>Описание</th><th>Локация</th></tr>
    {incident_rows if incident_rows else '<tr><td colspan="4" style="color:#94a3b8;text-align:center">Инцидентов не зафиксировано</td></tr>'}
  </table>

  <div class="section-title">📋 Итоги недели</div>
  <table>
    <tr><th>Тип событий</th><th>Количество</th></tr>
    <tr><td>Отчёты о питании</td><td>{cnt_food}</td></tr>
    <tr><td>Отсутствия учителей</td><td>{cnt_absence}</td></tr>
    <tr><td>Инциденты</td><td>{cnt_incident}</td></tr>
    <tr><td>Медицинские случаи</td><td>{cnt_medical}</td></tr>
    <tr><td>Прочие сообщения</td><td>{cnt_other}</td></tr>
  </table>

  <div class="sig-block">
    <div>Директор: <span class="sig-line"></span> / Сарсенбаев А.Т.</div>
    <div>Ознакомлен(а): <span class="sig-line"></span></div>
  </div>

  <div class="footer">Сформировано автоматически системой Aqbobek AI Orchestrator &nbsp;|&nbsp; {today_str} &nbsp;|&nbsp; AIS Hack 3.0</div>
</div>
<button class="print-btn" onclick="window.print()">🖨️ Печать / PDF</button>
<script>setTimeout(() => window.print(), 800);</script>
</body>
</html>"""


@router.get("/report")
def generate_analytics_report(
    date_from: str = None,
    date_to: str = None,
):
    """Генерирует HTML-отчёт с AI-анализом. Принимает date_from и date_to (YYYY-MM-DD)."""
    today = datetime.now().strftime("%Y-%m-%d")
    if not date_to:
        date_to = today
    if not date_from:
        # Дефолт — неделя
        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    stats = _get_stats(date_from, date_to)
    ai_summary = _generate_ai_summary(stats)
    html = _generate_report_html(stats, ai_summary)
    return {"html": html, "stats": stats}


def _generate_ai_summary(stats: dict) -> str:
    """Генерирует 2-3 предложения аналитического резюме через OpenAI (с fallback)."""
    api_key = os.getenv("OPENAI_API_KEY", "mock")

    incidents = stats.get("type_counts", {}).get("incident", 0)
    medical = stats.get("type_counts", {}).get("medical", 0)
    absences = stats.get("absences", 0)
    food = stats.get("total_food_portions", 0)
    tasks_done = stats.get("tasks_done", 0)
    tasks_total = stats.get("tasks_total", 1)
    efficiency = round((tasks_done / max(tasks_total, 1)) * 100)

    if api_key and api_key != "mock" and len(api_key) > 10:
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            prompt = f"""Ты аналитический ассистент школьного дашборда Aqbobek. 
На основе данных за неделю сформируй краткое аналитическое резюме на русском (3-4 предложения) для директора школы.
Данные: сообщений={stats.get("total_messages",0)}, порций питания={food}, отсутствий={absences}, инцидентов={incidents}, медицинских случаев={medical}, задач выполнено={tasks_done} из {tasks_total} ({efficiency}%).
Будь конкретным, дай оценку и 1 рекомендацию."""
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                timeout=10,
                max_tokens=250
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[Analytics AI] fallback: {e}")

    risk_status = "остается управляемой" if incidents + medical < 2 else "требует оперативного внимания администрации"
    if efficiency < 70:
        recommendation = "Рекомендуется сократить долю неподтверждённых поручений и усилить контроль по исполнительской дисциплине."
    else:
        recommendation = "Исполнительская дисциплина находится на приемлемом уровне, фокус можно сместить на профилактику инцидентов и замещений."

    return (
        f"За выбранный период платформа зафиксировала {stats.get('total_messages', 0)} рабочих сообщений, "
        f"в том числе {food} заявок по питанию и {absences} случаев отсутствия сотрудников. "
        f"Операционная обстановка в школе {risk_status}: зарегистрировано {incidents} хозяйственных инцидентов и "
        f"{medical} медицинских ситуаций. Доля завершённых поручений составила {efficiency}% от общего объёма задач. "
        f"{recommendation}"
    )
