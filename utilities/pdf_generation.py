"""
Утилиты для генерации PDF-файлов (заявки и отчёта о тестировании).

Версия: V2 — унифицированные стили, безопасная регистрация шрифтов,
единый формат временных меток и аккуратное логирование.

Функции:
    - generate_application_pdf(...)
    - generate_test_report(...)
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    FrameBreak,
    Image,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from logging_config import logger

# ---------------------------------------------------------------------
# Конфигурация шрифтов и стилей
# ---------------------------------------------------------------------
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
FONT_REGULAR_PATH = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

DEFAULT_FALLBACK_FONT = "HeiseiKakuGo-W5"  # надёжный CID-шрифт как fallback


# Регистрация шрифтов с безопасным fallback
def _register_fonts() -> None:
    """Пытается зарегистрировать DejaVu шрифты, при ошибке использует CID-фонт."""
    try:
        if os.path.exists(FONT_REGULAR_PATH):
            pdfmetrics.registerFont(TTFont("DejaVuSans", FONT_REGULAR_PATH))
        if os.path.exists(FONT_BOLD_PATH):
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", FONT_BOLD_PATH))
        else:
            # если bold отсутствует, регистрируем regular с другим именем
            if os.path.exists(FONT_REGULAR_PATH):
                pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", FONT_REGULAR_PATH))
    except Exception as exc:  # pragma: no cover - защитный fallback
        logger.warning(
            "Не удалось зарегистрировать DejaVu шрифты, использую CID-фонт: %s", exc
        )
        pdfmetrics.registerFont(UnicodeCIDFont(DEFAULT_FALLBACK_FONT))


def _safe_font(name: str) -> str:
    """Возвращает имя шрифта, если он зарегистрирован, иначе fallback."""
    try:
        pdfmetrics.getFont(name)
        return name
    except Exception:
        return DEFAULT_FALLBACK_FONT


# Выполняем регистрацию при импорте
_register_fonts()

FONT_REGULAR = _safe_font("DejaVuSans")
FONT_BOLD = _safe_font("DejaVuSans-Bold")

# Единый формат временной метки для имён файлов
TIMESTAMP_FMT = "%Y-%m-%d_%H-%M-%S"


# ---------------------------------------------------------------------
# Унифицированные стили Paragraph/Table
# ---------------------------------------------------------------------
def _make_styles() -> Dict[str, ParagraphStyle]:
    """Создаёт и возвращает словарь часто используемых ParagraphStyle."""
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Heading1"],
            fontName=FONT_BOLD,
            fontSize=16,
            alignment=1,
            spaceAfter=12,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            fontName=FONT_BOLD,
            fontSize=13,
            alignment=1,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.darkblue,
        ),
        "Section": ParagraphStyle(
            "Section",
            fontName=FONT_BOLD,
            fontSize=12,
            leftIndent=0.2 * cm,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "Body": ParagraphStyle(
            "Body",
            fontName=FONT_REGULAR,
            fontSize=11,
            leading=14,
        ),
        "Small": ParagraphStyle(
            "Small",
            fontName=FONT_REGULAR,
            fontSize=9,
        ),
    }


_STYLES = _make_styles()


def _p(text: str | List[str]) -> Paragraph:
    if isinstance(text, list):
        text = ", ".join(text)
    return Paragraph(text.replace("\n", "<br/>"), _STYLES["Body"])


# ---------------------------------------------------------------------
# Вспомогательные функции для табличек и логотипа
# ---------------------------------------------------------------------
def _add_logo_to_elements(elements: list, logo_name: str = "logo_header.png") -> None:
    """Добавляет логотип в начало элементов, если файл логотипа существует."""
    logo_path = os.path.join(os.path.dirname(__file__), logo_name)
    if os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=3 * cm, height=1 * cm)
            img.hAlign = "CENTER"
            elements.append(img)
            elements.append(Spacer(1, 6))
        except Exception as exc:
            logger.debug("Не удалось добавить логотип в PDF: %s", exc)


def _make_table(
    data: List[List[Any]],
    col_widths: Optional[List[float]] = None,
    repeat_header: bool = False,
    align: str = "CENTER",
) -> Table:
    """Создаёт таблицу с единым стилем для проекта."""
    table = Table(data, colWidths=col_widths, repeatRows=1 if repeat_header else 0)
    table_style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), align),
            ("WORDWRAP", (0, 0), (-1, -1), "CJK"),
        ]
    )
    # если есть header — делаем ему фон
    if data and isinstance(data[0], (list, tuple)):
        table_style.add("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke)
    table.setStyle(table_style)
    return table


def _add_background_and_border(canvas, doc) -> None:
    """Единый фон и рамка страницы для всех PDF."""
    canvas.saveState()
    canvas.setFillColorRGB(0.99, 0.99, 0.97)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    margin = 20
    canvas.setLineWidth(1)
    canvas.setStrokeColorRGB(0.8, 0.78, 0.7)
    canvas.rect(
        margin, margin, A4[0] - 2 * margin, A4[1] - 2 * margin, fill=0, stroke=1
    )
    canvas.restoreState()


# ---------------------------------------------------------------------
# Функция перевода слов
# ---------------------------------------------------------------------
TRANSLATIONS = {
    "school": "Школа",
    "university": "Университет",
    "self_study": "Самостоятельное обучение",
    "courses": "Курсы",
    "never": "Никогда",
    "individual": "Индивидуальный",
    "pair": "Парный",
    "group": "Групповой",
    "online": "Онлайн",
    "offline": "В классе",
    "friends": "Друзья",
    "internet": "Интернет",
    "telegram": "Телеграм",
    "other": "Другое",
}


def _tr(value: str | None) -> str:
    if value is None:
        return "—"
    return TRANSLATIONS.get(value.lower(), value)


# ---------------------------------------------------------------------
# Основные публичные функции
# ---------------------------------------------------------------------
def generate_application_pdf(
    applicant_name: str,
    phone_number: str,
    applicant_age: int,
    preferred_class_format: List[str],
    preferred_study_mode: List[str],
    level: Optional[str],
    possible_scheduling: List[Dict[str, List[str]]],
    reference_source: Optional[str],
    studied_at_lanex: bool,
    previous_experience: Optional[List[str]],
    telegram_id: int,
    notes: str = "",
    need_ielts: Optional[bool] = None,
    output_dir: Optional[str] = None,
    is_update: bool = False,
) -> str:
    """
    Генерирует PDF-файл заявки и возвращает путь к файлу.

    Args:
        applicant_name: Имя заявителя.
        phone_number: Телефон.
        applicant_age: Возраст.
        preferred_class_format: Список форматов (strings).
        preferred_study_mode: Список режимов (strings).
        level: Уровень (может быть None).
        possible_scheduling: Список словарей {"day": str, "times": [str]}.
        reference_source: Откуда узнал пользователь.
        need_ielts: Нужен ли IELTS.
        studied_at_lanex: Брал ли ранее занятия в Lanex.
        previous_experience: Список предыдущего опыта.
        telegram_id: Telegram ID пользователя.
        notes: Дополнительные заметки администратора.
        output_dir: Папка для сохранения (по умолчанию ./generated_pdfs).
        is_update: Флаг — это обновлённая заявка.

    Returns:
        str: Абсолютный путь к сгенерированному PDF.
    """

    try:
        out_dir = output_dir or os.path.join(os.getcwd(), "generated_pdfs")
        os.makedirs(out_dir, exist_ok=True)

        timestamp = datetime.now().strftime(TIMESTAMP_FMT)
        prefix = "UPDATED_APPLICATION" if is_update else "NEW_APPLICATION"
        safe_name = applicant_name.replace(" ", "_")
        filename = f"{prefix}_{safe_name}_{timestamp}_{telegram_id}.pdf"
        filepath = os.path.join(out_dir, filename)

        doc = BaseDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        elements: List[Any] = []

        # Верх страницы
        _add_logo_to_elements(elements)
        elements.append(Paragraph("Заявка на обучение в Lanex", _STYLES["Title"]))
        elements.append(Spacer(1, 10))

        # Основная таблица
        ielts_display = "Да" if need_ielts else ("Нет" if need_ielts is False else "—")
        data = [
            ["Полное имя", _p(applicant_name)],
            ["Номер телефона", _p(phone_number)],
            ["Возраст", _p(str(applicant_age))],
            ["Формат занятий", _p(", ".join(_tr(x) for x in preferred_class_format))],
            ["Режим обучения", _p(", ".join(_tr(x) for x in preferred_study_mode))],
            ["Уровень", _p(level or "—")],
            [
                "Источник информации",
                _p(_tr(reference_source) if reference_source else "—"),
            ],
            ["Нужен IELTS", _p(ielts_display)],
            ["Ранее обучался(-ась) в Lanex", _p("Да" if studied_at_lanex else "Нет")],
            [
                "Предыдущий опыт",
                (
                    _p(", ".join(_tr(x) for x in previous_experience))
                    if previous_experience
                    else "—"
                ),
            ],
        ]
        elements.append(_make_table(data, col_widths=[6 * cm, 9 * cm], align="LEFT"))
        elements.append(Spacer(1, 12))

        # Расписание
        elements.append(Paragraph("Доступное расписание", _STYLES["Subtitle"]))
        schedule_data = [[_p("День"), _p("Предпочтительные часы")]]
        for slot in possible_scheduling:
            schedule_data.append(
                [
                    _p(slot.get("day", "—")),
                    _p(", ".join(slot.get("times", [])) or "—"),
                ]
            )
        elements.append(
            _make_table(schedule_data, col_widths=[4 * cm, 11 * cm], repeat_header=True)
        )

        # ОБЯЗАТЕЛЬНЫЙ ПЕРЕКЛЮЧАТЕЛЬ НА НИЖНИЙ ФРЕЙМ
        elements.append(FrameBreak())

        # === Нижний блок: ЗАМЕТКИ ===
        elements.append(Paragraph("Заметки администратора", _STYLES["Subtitle"]))
        elements.append(Spacer(1, 6))

        # Таблица заметок фиксированной высоты
        notes_table = Table(
            [[Paragraph(notes or "", _STYLES["Body"])] for _ in range(4)],
            colWidths=[doc.width],
            rowHeights=[1.2 * cm] * 4,
        )
        notes_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
                ]
            )
        )
        elements.append(notes_table)

        # Frame'ы
        frame_notes_height = 7 * cm
        frame_main_height = (
            A4[1] - frame_notes_height - doc.topMargin - doc.bottomMargin
        )

        frame_main = Frame(
            doc.leftMargin,
            doc.bottomMargin + frame_notes_height,
            doc.width,
            frame_main_height,
            id="main",
        )

        frame_notes = Frame(
            doc.leftMargin, doc.bottomMargin, doc.width, frame_notes_height, id="notes"
        )

        doc.addPageTemplates(
            [
                PageTemplate(
                    id="app_template",
                    frames=[frame_main, frame_notes],
                    onPage=_add_background_and_border,
                )
            ]
        )

        doc.build(elements)
        return filepath

    except Exception as exc:
        logger.exception("Ошибка при генерации PDF заявки: %s", exc)
        raise


def generate_test_report(
    test_taker: str,
    level: str,
    closed_answers: Dict[str, Dict[str, Any]],
    open_answers: Optional[Dict[str, Dict[str, Any]]],
    score: Dict[str, Any],
    output_dir: Optional[str] = None,
) -> str:
    """
    Генерирует PDF-отчёт о тестировании и возвращает путь к файлу.

    Args:
        test_taker: Имя участника.
        level: Уровень теста.
        closed_answers:
            Структура закрытых ответов вида:
            {
                "task1": {
                    "1": {
                        "answer": "...",
                        "status": "correct"
                    }
                }
            }
        open_answers: Открытые ответы (может быть None).
        score: Словарь с баллами по заданиям.
        output_dir: Папка для сохранения (по умолчанию ./generated_reports).

    Returns:
        str: Путь к сохранённому PDF.
    """

    try:
        reports_dir = output_dir or os.path.join(os.getcwd(), "generated_reports")
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime(TIMESTAMP_FMT)
        safe_taker = (test_taker or "unknown").replace(" ", "_")
        filename = f"TEST_REPORT_{safe_taker}_{level}_{timestamp}.pdf"
        filepath = os.path.join(reports_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        elements: List[Any] = []

        # Верхняя часть
        _add_logo_to_elements(elements)
        elements.append(Paragraph("LANEX TEST REPORT", _STYLES["Title"]))
        elements.append(Spacer(1, 8))
        info_style = _STYLES["Body"]
        elements.append(Paragraph(f"<b>Test taker:</b> {test_taker}", info_style))
        elements.append(Paragraph(f"<b>Level:</b> {level}", info_style))
        elements.append(
            Paragraph(
                f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                info_style,
            )
        )
        elements.append(Spacer(1, 10))

        # Closed tasks
        elements.append(Paragraph("Closed Tasks", _STYLES["Subtitle"]))
        for task, questions in closed_answers.items():
            elements.append(Paragraph(task, _STYLES["Section"]))
            elements.append(Spacer(1, 6))

            table_data = [["Question", "Answer", "Status"]]
            for q_num, q_data in questions.items():
                user_answer = q_data.get("answer", "")
                status = q_data.get("status", "unchecked")

                if not user_answer:
                    answer_display = "—"
                    status_display = "No answer"
                else:
                    answer_display = user_answer
                    status_display = status.capitalize()

                table_data.append([q_num, answer_display, status_display])

            table = _make_table(
                table_data, col_widths=[2.5 * cm, 11 * cm, 3.5 * cm], repeat_header=True
            )
            elements.append(table)
            elements.append(Spacer(1, 6))

            # Score for task if exists
            if task in score:
                elements.append(Paragraph(f"Score: {score[task]}", _STYLES["Section"]))
            elements.append(Spacer(1, 8))

        # Open tasks
        if open_answers:
            elements.append(Paragraph("Open Tasks", _STYLES["Subtitle"]))
            for task, answers in open_answers.items():
                elements.append(Paragraph(task, _STYLES["Section"]))
                for q_num, user_answer in answers.items():
                    if isinstance(user_answer, str):
                        formatted_answer = user_answer.replace(
                            "\n\n", "<br/><br/>"
                        ).replace("\n", "<br/>")
                    else:
                        formatted_answer = str(user_answer)

                    answer_paragraph = Paragraph(
                        f"<b>Q{q_num}:</b> {formatted_answer}", info_style
                    )
                    ans_table = Table([[answer_paragraph]], colWidths=[doc.width])
                    ans_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
                            ]
                        )
                    )
                    elements.append(ans_table)
                    elements.append(Spacer(1, 6))

        # Feedback / overall
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Overall Feedback", _STYLES["Subtitle"]))
        feedback_table = Table([[""]], colWidths=[doc.width], rowHeights=[4 * cm])
        feedback_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(feedback_table)

        doc.build(
            elements,
            onFirstPage=_add_background_and_border,
            onLaterPages=_add_background_and_border,
        )
        logger.info("PDF отчёт о тесте сгенерирован: %s", filepath)
        return filepath

    except Exception as exc:
        logger.exception("Ошибка при генерации PDF отчёта: %s", exc)
        raise
