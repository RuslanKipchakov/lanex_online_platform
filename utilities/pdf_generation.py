from datetime import datetime
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Frame,
    PageTemplate,
    FrameBreak,
    Image,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


# === Безопасная регистрация шрифтов ===
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONT_PATH = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")


def safe_register_fonts():
    """Безопасная регистрация шрифтов с fallback."""
    try:
        if os.path.exists(FONT_PATH):
            pdfmetrics.registerFont(TTFont("DejaVuSans", FONT_PATH))
        if os.path.exists(FONT_BOLD_PATH):
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", FONT_BOLD_PATH))
        else:
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", FONT_PATH))
    except Exception:
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))


def safe_font(name: str) -> str:
    """Проверяет, зарегистрирован ли шрифт, и при необходимости делает fallback."""
    try:
        pdfmetrics.getFont(name)
        return name
    except KeyError:
        return "HeiseiKakuGo-W5"


# Регистрируем шрифты при импорте
safe_register_fonts()


def _add_background_and_border(canvas, doc):
    """Добавляет фон и рамку вокруг страницы."""
    canvas.saveState()
    canvas.setFillColorRGB(0.99, 0.99, 0.97)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    margin = 20
    canvas.setLineWidth(1)
    canvas.setStrokeColorRGB(0.8, 0.78, 0.7)
    canvas.rect(margin, margin, A4[0] - 2 * margin, A4[1] - 2 * margin, fill=0, stroke=1)
    canvas.restoreState()


# === Генерация PDF заявки ===
def generate_application_pdf(
    applicant_name: str,
    phone_number: str,
    applicant_age: int,
    preferred_class_format: list[str],
    preferred_study_mode: list[str],
    level: str | None,
    possible_scheduling: list[dict[str, list[str]]],
    reference_source: str | None,
    need_ielts: bool,
    studied_at_lanex: bool,
    previous_experience: list[str] | None,
    telegram_id: int,
    username: str,
    notes: str = "",
    output_dir: str | None = None,
) -> str:
    """Генерация PDF заявки с блоком 'Заметки администратора'."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%d-%m-%Y_%H%M%S")
    filename = f"{username}_{timestamp}_{telegram_id}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = BaseDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    # === Стили ===
    title_style = ParagraphStyle("Title", fontName=safe_font("DejaVuSans-Bold"), fontSize=16, alignment=1, spaceAfter=14)
    subtitle_style = ParagraphStyle("Subtitle", fontName=safe_font("DejaVuSans-Bold"), fontSize=13, alignment=1, spaceBefore=16, spaceAfter=8)
    normal_style = ParagraphStyle("Normal", fontName=safe_font("DejaVuSans"), fontSize=11, leading=14)

    elements = []

    # === Логотип и заголовок ===
    logo_path = os.path.join(os.path.dirname(__file__), "logo_header.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=3 * cm, height=1 * cm)
        logo.hAlign = "CENTER"
        elements += [logo, Spacer(1, 6)]
    elements += [Paragraph("Форма заявки Lanex", title_style), Spacer(1, 12)]

    data = [
        ["Полное имя", applicant_name],
        ["Номер телефона", phone_number],
        ["Возраст", str(applicant_age)],
        ["Формат занятий", ", ".join(preferred_class_format)],
        ["Режим обучения", ", ".join(preferred_study_mode)],
        ["Уровень", level or "—"],
        ["Источник информации", reference_source or "—"],
        ["Необходим IELTS", "Да" if need_ielts else "Нет"],
        ["Ранее обучался(-ась) в Lanex", "Да" if studied_at_lanex else "Нет"],
        ["Предыдущий опыт", ", ".join(previous_experience) if previous_experience else "—"],
    ]

    table = Table(data, colWidths=[6 * cm, 9 * cm])
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), safe_font("DejaVuSans")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
    ]))
    elements += [table, Spacer(1, 12)]

    # === Расписание ===
    elements.append(Paragraph("Доступное расписание", subtitle_style))
    schedule_data = [["День", "Предпочтительные часы"]]
    for slot in possible_scheduling:
        schedule_data.append([
            slot.get("day", "—"),
            ", ".join(slot.get("times", [])) or "—",
        ])
    schedule_table = Table(schedule_data, colWidths=[4 * cm, 11 * cm])
    schedule_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), safe_font("DejaVuSans")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ]))
    elements.append(schedule_table)
    elements.append(FrameBreak())

    # === Нижний блок ===
    elements += [Paragraph("Заметки администратора", subtitle_style), Spacer(1, 6)]
    notes_table = Table(
        [[Paragraph(notes, normal_style) if notes else ""] for _ in range(4)],
        colWidths=[15 * cm],
        rowHeights=[1.2 * cm] * 4,
        style=TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]),
    )
    elements.append(notes_table)

    # === Фреймы ===
    frame_notes_height = 7 * cm
    frame_main_height = A4[1] - frame_notes_height - doc.topMargin - doc.bottomMargin

    frame_main = Frame(doc.leftMargin, doc.bottomMargin + frame_notes_height, doc.width, frame_main_height, id="main")
    frame_notes = Frame(doc.leftMargin, doc.bottomMargin, doc.width, frame_notes_height, id="notes")

    doc.addPageTemplates([PageTemplate(id="app_template", frames=[frame_main, frame_notes], onPage=_add_background_and_border)])
    doc.build(elements)
    return filepath


# === Генерация отчёта о тесте ===
def generate_test_report(
    test_taker: str,
    level: str,
    closed_answers: dict,
    open_answers: dict | None,
    score: dict,
    output_dir: str | None = None,
) -> str:
    """Генерация PDF-отчёта о тесте с таблицами и отзывом."""
    reports_dir = output_dir or os.path.join(os.getcwd(), "generated_reports")
    os.makedirs(reports_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"TEST_REPORT_{test_taker}_{level}_{date_str.replace(':', '-').replace(' ', '_')}.pdf"
    filepath = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    elements = []

    # === Стили ===
    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontName="DejaVuSans-Bold", alignment=1, spaceAfter=14, textColor=colors.darkblue)
    info_style = ParagraphStyle("InfoStyle", parent=styles["Normal"], fontName="DejaVuSans", fontSize=11, spaceAfter=4)
    subtitle_style = ParagraphStyle("Subtitle", fontName="DejaVuSans-Bold", fontSize=13, leading=15, alignment=1, spaceBefore=16, spaceAfter=8)
    task_title_style = ParagraphStyle("TaskTitle", fontName="DejaVuSans-Bold", fontSize=12, leftIndent=0.7 * cm, spaceBefore=10, spaceAfter=4, textColor=colors.darkblue)

    # === Верхняя часть ===
    logo_path = os.path.join(os.path.dirname(__file__), "logo_header.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=3 * cm, height=1 * cm)
        logo.hAlign = "CENTER"
        elements += [logo, Spacer(1, 6)]
    elements += [
        Paragraph("LANEX TEST REPORT", title_style),
        Spacer(1, 10),
        Paragraph(f"<b>Test taker:</b> {test_taker}", info_style),
        Paragraph(f"<b>Level:</b> {level}", info_style),
        Paragraph(f"<b>Date:</b> {date_str}", info_style),
        Spacer(1, 14),
    ]

    # === Closed Tasks ===
    elements.append(Paragraph("Closed Tasks", subtitle_style))
    for task, questions in closed_answers.items():
        elements += [Paragraph(task, task_title_style), Spacer(1, 6)]
        data = [["Question", "Answer", "Status"]]
        for q_num, q_data in questions.items():
            data.append([q_num, q_data.get("answer", "—"), q_data.get("status", "unchecked").capitalize()])
        table = Table(data, colWidths=[80, 250, 100], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        elements += [table, Spacer(1, 6)]
        if task in score:
            elements.append(Paragraph(f"Score: {score[task]}", task_title_style))
        elements.append(Spacer(1, 10))

    # === Open Tasks ===
    if open_answers:
        elements.append(Paragraph("Open Task", subtitle_style))
        for task, answers in open_answers.items():
            for q_num, user_answer in answers.items():
                answer_table = Table([[Paragraph(f"Q{q_num}: {user_answer}", info_style)]], colWidths=[440])
                answer_table.setStyle(TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ]))
                elements += [answer_table, Spacer(1, 8)]

    # === Feedback ===
    feedback_title = Paragraph("Overall Feedback", subtitle_style)
    feedback_table = Table(
        [[""] for _ in range(4)],
        colWidths=[15 * cm],
        rowHeights=[1.2 * cm] * 4,
        style=TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]),
    )
    elements.append(KeepTogether([Spacer(1, 20), feedback_title, Spacer(1, 6), feedback_table]))

    doc.build(elements, onFirstPage=_add_background_and_border, onLaterPages=_add_background_and_border)
    return filepath
