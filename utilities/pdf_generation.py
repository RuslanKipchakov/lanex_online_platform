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

    # --- Рамка ---
    margin = 20
    canvas.setLineWidth(1)
    canvas.setStrokeColorRGB(0.8, 0.78, 0.7)
    canvas.rect(
        margin, margin, A4[0] - 2 * margin, A4[1] - 2 * margin, fill=0, stroke=1
    )
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
    Генерирует PDF-заявку с динамическим нижним блоком 'Заметки администратора'.
    """
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
    title_style = ParagraphStyle(
        "Title",
        fontName=safe_font("DejaVuSans-Bold"),
        fontSize=16,
        alignment=1,
        spaceAfter=14,
    )

    subtitle_style = ParagraphStyle(
        "ScheduleTitle",
        fontName=safe_font("DejaVuSans-Bold"),
        fontSize=13,
        leading=15,
        alignment=1,
        spaceBefore=16,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "Normal",
        fontName=safe_font("DejaVuSans"),
        fontSize=11,
        leading=14,
    )

    elements = []

    # === Верхний контент ===
    logo_path = os.path.join(os.path.dirname(__file__), "logo_header.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=3 * cm, height=1 * cm)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 6))
    elements.append(Paragraph("Форма заявки Lanex", title_style))
    elements.append(Spacer(1, 12))

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
        [
            "Предыдущий опыт изучения",
            ", ".join(previous_experience) if previous_experience else "—",
        ],
    ]

    table = Table(data, colWidths=[6 * cm, 9 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), safe_font("DejaVuSans")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 12))

    # === Расписание ===
    elements.append(Paragraph("Доступное расписание", subtitle_style))
    schedule_data = [
        [
            Paragraph("<b>День</b>", normal_style),
            Paragraph("<b>Предпочтительные часы</b>", normal_style),
        ]
    ]
    for slot in possible_scheduling:
        day = Paragraph(slot.get("day", "—"), normal_style)
        times = Paragraph(", ".join(slot.get("times", [])) or "—", normal_style)
        schedule_data.append([day, times])

    schedule_table = Table(schedule_data, colWidths=[4 * cm, 11 * cm])
    schedule_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), safe_font("DejaVuSans")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ]
        )
    )
    elements.append(schedule_table)

    elements.append(FrameBreak())

    # === Нижний блок (заметки администратора) ===
    elements.append(Paragraph("Заметки администратора", subtitle_style))
    elements.append(Spacer(1, 6))
    if notes:
        notes_table = Table(
            [[Paragraph(notes, normal_style)]],
            colWidths=[15 * cm],
            rowHeights=[4 * 1.2 * cm],
            style=TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, -1), safe_font("DejaVuSans")),
                ]
            ),
        )
    else:
        notes_table = Table(
            [[""] for _ in range(4)],
            colWidths=[15 * cm],
            rowHeights=[1.2 * cm] * 4,
            style=TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, -1), safe_font("DejaVuSans")),
                ]
            ),
        )
    elements.append(notes_table)

    # === Определяем фреймы ===
    page_height = A4[1]
    frame_notes_height = 7 * cm
    frame_main_height = page_height - frame_notes_height - doc.topMargin - doc.bottomMargin

    frame_main = Frame(
        doc.leftMargin,
        doc.bottomMargin + frame_notes_height,
        doc.width,
        frame_main_height,
        id="main_frame",
    )

    frame_notes = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        frame_notes_height,
        id="notes_frame",
    )

    page_template = PageTemplate(
        id="application_template",
        frames=[frame_main, frame_notes],
        onPage=_add_background_and_border,
    )
    doc.addPageTemplates([page_template])

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
    """
    Генерация PDF-отчёта о тесте.
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

    # --- Closed Tasks ---
    elements.append(Paragraph("<b>Closed Tasks</b>", styles["Heading2"]))
    for task, questions in closed_answers.items():
        data = [["Question", "Answer", "Status"]]
        for q_num, q_data in questions.items():
            answer = q_data.get("answer", "—")
            status = q_data.get("status", "unchecked")
            data.append([q_num, answer, status.capitalize()])

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

    # --- Open Tasks ---
    if open_answers:
        elements.append(Paragraph("<b>Open Tasks</b>", styles["Heading2"]))
        for task, answers in open_answers.items():
            elements.append(Paragraph(f"<b>{task}</b>", info_style))
            for q_num, user_answer in answers.items():
                elements.append(Paragraph(f"Q{q_num}: {user_answer}", info_style))
                elements.append(Spacer(1, 6))

            elements.append(Paragraph("Teacher's notes:", info_style))
            notes_box = Table(
                [[" " * 100]],
                colWidths=[440],
                rowHeights=[60],
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]),
            )
            elements.append(notes_box)
            elements.append(Spacer(1, 20))

    # --- Feedback ---
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>Overall Feedback:</b>", info_style))
    feedback_box = Table(
        [[" " * 100]],
        colWidths=[440],
        rowHeights=[100],
        style=TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]),
    )
    elements.append(feedback_box)
    elements.append(Spacer(1, 25))

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

    doc.build(elements, onFirstPage=_add_background_and_border)
    return filepath
