"""
Zero-dependency document generator.
Returns a beautifully styled print-ready HTML document.
Browser renders it natively with full Cyrillic support.
User can Ctrl+P → Save as PDF, or we trigger window.print() automatically.
"""

from datetime import datetime


def create_order_html(
    missing_teacher: str,
    substitute_teacher: str,
    lesson_number: int,
    class_name: str,
    room: str,
    order_date: str,
    order_number: str,
    ai_preamble: str,
    ai_body: str,
    ai_body_kz: str = "",
) -> str:
    """Returns a print-ready HTML string (no external deps needed)."""

    body_items_ru = [p.strip() for p in ai_body.split("\n") if p.strip()]
    body_items_kz = [p.strip() for p in ai_body_kz.split("\n") if p.strip()]

    body_ru_html = "".join(
        f'<div class="item"><span class="num">{i+1}.</span><span>{item.lstrip("0123456789. ")}</span></div>'
        if not item[0].isdigit() else
        f'<div class="item"><span>{item}</span></div>'
        for i, item in enumerate(body_items_ru)
    )

    body_kz_html = "".join(
        f'<div class="item-kz"><span>{item}</span></div>'
        for item in body_items_kz
    )

    kz_section = f"""
        <div class="kz-block">
          <div class="kz-label">Казахша нұсқасы / Казахская версия:</div>
          {body_kz_html}
        </div>
    """ if ai_body_kz else ""

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Приказ № {order_number} — AI-Завуч</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=PT+Serif:ital,wght@0,400;0,700;1,400&display=swap');

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'PT Serif', Georgia, 'Times New Roman', serif;
      font-size: 12pt;
      color: #1a1a2e;
      background: #f5f7fa;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      padding: 40px 20px;
    }}

    .page {{
      background: white;
      width: 210mm;
      min-height: 297mm;
      padding: 25mm 22mm 20mm;
      box-shadow: 0 8px 40px rgba(0,0,0,0.12);
      border-radius: 4px;
      position: relative;
    }}

    /* TOP STRIPE */
    .top-stripe {{
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 6px;
      background: linear-gradient(90deg, #1a3a8f 0%, #2563eb 50%, #16a34a 100%);
      border-radius: 4px 4px 0 0;
    }}

    .school-name {{
      text-align: center;
      font-size: 10pt;
      color: #555;
      line-height: 1.5;
      border-bottom: 1px solid #d1d5db;
      padding-bottom: 10px;
      margin-bottom: 14px;
      letter-spacing: 0.02em;
    }}
    .school-name strong {{ color: #1a1a2e; }}

    .title-block {{
      text-align: center;
      margin-bottom: 6px;
    }}
    .title-block h1 {{
      font-size: 20pt;
      letter-spacing: 0.04em;
      color: #1a3a8f;
      font-weight: 700;
      margin-bottom: 4px;
    }}

    .meta-row {{
      display: flex;
      justify-content: space-between;
      font-size: 10pt;
      color: #6b7280;
      margin-bottom: 6px;
    }}

    .subject-line {{
      text-align: center;
      font-size: 13pt;
      color: #1e40af;
      margin-bottom: 14px;
      font-weight: 700;
      letter-spacing: 0.01em;
    }}

    .compliance-badge {{
      background: #f0fdf4;
      border: 1px solid #86efac;
      border-radius: 6px;
      padding: 7px 14px;
      text-align: center;
      color: #166534;
      font-size: 9pt;
      font-family: Arial, sans-serif;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }}
    .compliance-badge .checkmark {{
      font-size: 13pt;
      color: #16a34a;
    }}

    .preamble {{
      font-size: 11pt;
      line-height: 1.7;
      text-align: justify;
      margin-bottom: 14px;
      color: #374151;
    }}

    .decree-header {{
      font-size: 14pt;
      font-weight: 700;
      color: #1a3a8f;
      margin-bottom: 10px;
      letter-spacing: 0.05em;
    }}

    .item {{
      display: flex;
      gap: 10px;
      font-size: 11pt;
      line-height: 1.65;
      margin-bottom: 8px;
      text-align: justify;
      color: #1f2937;
    }}
    .item .num {{
      min-width: 20px;
      font-weight: 700;
      color: #1a3a8f;
    }}

    .basis {{
      font-size: 9.5pt;
      color: #6b7280;
      margin-top: 4px;
      margin-bottom: 16px;
      font-style: italic;
      line-height: 1.5;
    }}

    .divider {{
      border: none;
      border-top: 1px solid #e5e7eb;
      margin: 16px 0;
    }}

    .kz-block {{
      background: #f8fafc;
      border-left: 3px solid #93c5fd;
      border-radius: 0 4px 4px 0;
      padding: 10px 14px;
      margin-bottom: 16px;
    }}
    .kz-label {{
      font-size: 8.5pt;
      color: #6b7280;
      font-family: Arial, sans-serif;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .item-kz {{
      font-size: 10pt;
      color: #374151;
      line-height: 1.6;
      margin-bottom: 4px;
    }}

    .control-line {{
      font-size: 10pt;
      color: #6b7280;
      margin-bottom: 24px;
      font-style: italic;
    }}

    .signatures {{
      margin-top: 8px;
    }}
    .sig-row {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      margin-bottom: 20px;
      font-size: 11pt;
    }}
    .sig-label {{ color: #374151; }}
    .sig-line {{
      flex: 1;
      border-bottom: 1px solid #9ca3af;
      margin: 0 12px;
      min-width: 80px;
    }}
    .sig-name {{ color: #1a1a2e; font-weight: 700; }}

    .footer {{
      margin-top: 30px;
      padding-top: 8px;
      border-top: 1px solid #e5e7eb;
      text-align: center;
      font-size: 7.5pt;
      color: #9ca3af;
      font-family: Arial, sans-serif;
    }}

    .print-btn {{
      position: fixed;
      bottom: 30px;
      right: 30px;
      background: #1a3a8f;
      color: white;
      border: none;
      border-radius: 50px;
      padding: 14px 28px;
      font-size: 13pt;
      font-family: Arial, sans-serif;
      font-weight: bold;
      cursor: pointer;
      box-shadow: 0 4px 20px rgba(26,58,143,0.4);
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .print-btn:hover {{ background: #1e40af; transform: translateY(-2px); }}

    @media print {{
      body {{ background: none; padding: 0; }}
      .page {{ box-shadow: none; border-radius: 0; width: 100%; min-height: 0; }}
      .top-stripe {{ display: none; }}
      .print-btn {{ display: none !important; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <div class="top-stripe"></div>

    <div class="school-name">
      <strong>Образовательный комплекс «Aqbobek International School»</strong><br>
      КГУ «Начальная школа» &nbsp;|&nbsp; г. Актобе, Республика Казахстан
    </div>

    <div class="title-block">
      <h1>ПРИКАЗ № {order_number}</h1>
    </div>
    <div class="meta-row">
      <span>г. Актобе</span>
      <span>«{order_date}»</span>
    </div>
    <div class="subject-line">О замене учебных занятий</div>

    <div class="compliance-badge">
      <span class="checkmark">✓</span>
      <span>Проверено AI на соответствие Приказу МОН РК №130 и №110 &nbsp;|&nbsp; Сформировано: AI-Завуч</span>
    </div>

    <div class="preamble">{ai_preamble}</div>

    <div class="decree-header">БҰЙЫРАМЫН / ПРИКАЗЫВАЮ:</div>

    <div class="items-block">
      {body_ru_html}
    </div>

    <div class="basis">
      Основание: Приказ МОН РК №130 «Об утверждении Перечня документов, обязательных для ведения педагогами»,
      сообщение о временной нетрудоспособности от {order_date}.
    </div>

    {kz_section}

    <hr class="divider">
    <div class="control-line">Контроль за исполнением настоящего приказа оставляю за собой.</div>

    <div class="signatures">
      <div class="sig-row">
        <span class="sig-label">Директор начальной школы AIS:</span>
        <span class="sig-line"></span>
        <span class="sig-name">/ Сарсенбаев А.Т.</span>
      </div>
      <div class="sig-row">
        <span class="sig-label">С приказом ознакомлен(а):</span>
        <span class="sig-line"></span>
        <span class="sig-name">/ {substitute_teacher}</span>
      </div>
    </div>

    <div class="footer">
      Сгенерировано автоматически системой Aqbobek AI Orchestrator | {datetime.now().strftime('%d.%m.%Y')}
    </div>
  </div>

  <button class="print-btn" onclick="window.print()">
    🖨️ Печать / Сохранить PDF
  </button>

  <script>
    // Auto-trigger print dialog after a short delay
    setTimeout(() => window.print(), 800);
  </script>
</body>
</html>"""
