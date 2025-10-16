from datetime import datetime
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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
            # Если жирный шрифт отсутствует, подставляем обычный
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", FONT_PATH))
    except Exception:
        # fallback на универсальный CIDFont
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
    """Фон и рамка для каждой страницы"""
    canvas.saveState()
    canvas.setFillColorRGB(0.96, 0.97, 1)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    margin = 20
    canvas.setLineWidth(1)
    canvas.setStrokeColorRGB(0.7, 0.7, 0.8)
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
    """
    Генерирует PDF-заявку на русском языке с датой и временем в имени файла.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%d-%m-%Y_%H%M%S")
    filename = f"{username}_{timestamp}_{telegram_id}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    # === Стили ===
    title_style = ParagraphStyle(
        "Title",
        fontName=safe_font("DejaVuSans-Bold"),
        fontSize=16,
        alignment=1,
        spaceAfter=14,
    )

    normal_style = ParagraphStyle(
        "Normal",
        fontName=safe_font("DejaVuSans"),
        fontSize=11,
        leading=14,
    )

    # === Содержимое ===
    elements = [Paragraph("Форма заявки Lanex", title_style), Spacer(1, 12)]

    # Основная таблица данных
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
        ["Предыдущий опыт изучения", ", ".join(previous_experience) if previous_experience else "—"],
    ]

    table = Table(data, colWidths=[6 * cm, 9 * cm])
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), safe_font("DejaVuSans")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # === Таблица расписания ===
    elements.append(Paragraph("Доступное расписание", title_style))
    schedule_data = [["День", "Предпочтительные часы"]]
    for slot in possible_scheduling:
        day = slot.get("day", "—")
        times = ", ".join(slot.get("times", []))
        schedule_data.append([day, times])

    schedule_table = Table(schedule_data, colWidths=[4 * cm, 11 * cm])
    schedule_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), safe_font("DejaVuSans")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ]))

    elements.append(schedule_table)
    elements.append(Spacer(1, 24))

    # === Заметки администратора ===
    elements.append(Paragraph("<b>Заметки администратора:</b>", normal_style))
    elements.append(Paragraph(notes or "—", normal_style))

    # === Сборка PDF ===
    doc.build(elements, onFirstPage=_add_background_and_border, onLaterPages=_add_background_and_border)
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
    """
    Генерация PDF-отчета о тесте.
    """
    reports_dir = output_dir or os.path.join(os.getcwd(), "generated_reports")
    os.makedirs(reports_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"TEST_REPORT_{test_taker}_{level}_{date_str}.pdf".replace(" ", "_")
    filepath = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName=safe_font("DejaVuSans-Bold"),
        alignment=1,
        spaceAfter=20,
        textColor=colors.darkblue,
    )
    info_style = ParagraphStyle(
        "InfoStyle",
        parent=styles["Normal"],
        fontName=safe_font("DejaVuSans"),
        spaceAfter=6,
    )

    elements.append(Paragraph("LANEX TEST REPORT", title_style))
    elements.append(Paragraph(f"<b>Test taker:</b> {test_taker}", info_style))
    elements.append(Paragraph(f"<b>Level:</b> {level}", info_style))
    elements.append(Paragraph(f"<b>Date:</b> {date_str}", info_style))
    elements.append(Spacer(1, 12))

    # Закрытые задания
    elements.append(Paragraph("<b>Closed Tasks</b>", styles["Heading2"]))
    for task, questions in closed_answers.items():
        data = [["Question", "Answer", "Status"]]
        for q_num, q_data in questions.items():
            data.append([q_num, q_data["answer"], q_data["status"]])
        t = Table(data, colWidths=[80, 250, 100])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, -1), safe_font("DejaVuSans")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        elements.append(Paragraph(f"<b>{task}</b>", info_style))
        elements.append(t)
        if task in score:
            elements.append(Paragraph(f"Score: {score[task]}", info_style))
        elements.append(Spacer(1, 12))

    # Открытые задания
    if open_answers:
        elements.append(Paragraph("<b>Open Tasks</b>", styles["Heading2"]))
        for task, answers in open_answers.items():
            elements.append(Paragraph(f"<b>{task}</b>", info_style))
            for q_num, user_answer in answers.items():
                elements.append(Paragraph(f"Q{q_num}: {user_answer}", info_style))
                elements.append(Spacer(1, 6))
            elements.append(Spacer(1, 8))

    # Итоговый результат
    total_score = score.get("total")
    if total_score is not None:
        total_table = Table(
            [[f"TOTAL SCORE: {total_score}"]],
            colWidths=[440],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.lightblue),
                ("BOX", (0, 0), (-1, -1), 1, colors.darkblue),
                ("FONTNAME", (0, 0), (-1, -1), safe_font("DejaVuSans-Bold")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 14),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.darkblue),
            ]),
        )
        elements.append(total_table)

    doc.build(elements, onFirstPage=_add_background_and_border, onLaterPages=_add_background_and_border)
    return filepath
