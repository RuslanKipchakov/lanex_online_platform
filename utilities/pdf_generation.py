import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))


def _add_background_and_border(canvas, doc):
    """Фон и рамка для каждой страницы"""
    canvas.saveState()
    canvas.setFillColorRGB(0.96, 0.97, 1)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)

    margin = 20
    canvas.setLineWidth(1)
    canvas.setStrokeColorRGB(0.7, 0.7, 0.8)
    canvas.rect(
        margin,
        margin,
        A4[0] - 2 * margin,
        A4[1] - 2 * margin,
        fill=0,
        stroke=1,
    )
    canvas.restoreState()


def generate_test_report(
    test_taker: str,
    level: str,
    closed_answers: dict,
    open_answers: dict | None,
    score: dict,
    output_dir: str | None = None,
):
    """
    Генерация PDF-отчета о тесте.
    :param test_taker: имя пользователя
    :param level: уровень теста
    :param closed_answers: словарь с закрытыми вопросами
    :param open_answers: словарь с открытыми вопросами (опционально)
    :param score: словарь с баллами (включая total)
    :param output_dir: путь к папке, где сохранить файл
    """
    reports_dir = output_dir or os.path.join(os.getcwd(), "generated_reports")
    os.makedirs(reports_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{test_taker}_{level}_{date_str}.pdf".replace(" ", "_")
    filepath = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName="HeiseiKakuGo-W5",
        alignment=1,
        spaceAfter=20,
        textColor=colors.darkblue,
    )
    info_style = ParagraphStyle(
        "InfoStyle",
        parent=styles["Normal"],
        fontName="HeiseiKakuGo-W5",
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
            data.append([q_num, q_data["answer"], q_data["status"]])

        t = Table(data, colWidths=[80, 250, 100])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, -1), "HeiseiKakuGo-W5"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
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
            elements.append(Spacer(1, 8))

            elements.append(Paragraph("Teacher's notes:", info_style))
            notes_box = Table(
                [[" " * 100]],
                colWidths=[440],
                rowHeights=[60],
                style=TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ]
                ),
            )
            elements.append(notes_box)
            elements.append(Spacer(1, 20))

    # --- Feedback section ---
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>Overall Feedback:</b>", info_style))
    feedback_box = Table(
        [[" " * 100]],
        colWidths=[440],
        rowHeights=[100],
        style=TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        ),
    )
    elements.append(feedback_box)
    elements.append(Spacer(1, 25))

    # --- Total Score ---
    total_score = score.get("total")
    if total_score is not None:
        total_table = Table(
            [[f"TOTAL SCORE: {total_score}"]],
            colWidths=[440],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.lightblue),
                    ("BOX", (0, 0), (-1, -1), 1, colors.darkblue),
                    ("FONTNAME", (0, 0), (-1, -1), "HeiseiKakuGo-W5"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 14),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.darkblue),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]
            ),
        )
        elements.append(total_table)

    # --- Build PDF ---
    doc.build(
        elements,
        onFirstPage=_add_background_and_border,
        onLaterPages=_add_background_and_border,
    )

    return filepath
