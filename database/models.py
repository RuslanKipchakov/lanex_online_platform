"""
Модели базы данных для системы Lanex Online Platform.

Содержит:
- модели пользователя (UserSession)
- модели заявок (Application)
- модели результатов тестирования (TestResult)
- перечисления (Enum) и константы

Все модели используют SQLAlchemy ORM и типы PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

# =============================================================================
# Константы
# =============================================================================

MIN_APPLICANT_NAME_LENGTH = 2
MAX_APPLICANT_NAME_LENGTH = 50
PHONE_NUMBER_LENGTH = 20


# =============================================================================
# ENUM типы
# =============================================================================


class PreferredClassFormatEnum(str, Enum):
    """Формат занятий, выбранный пользователем."""

    individual = "individual"
    pair = "pair"
    group = "group"


class PreferredStudyModeEnum(str, Enum):
    """Формат обучения."""

    online = "online"
    offline = "offline"


class LevelEnum(str, Enum):
    """Уровни владения английским языком."""

    starter = "Starter"
    elementary = "Elementary"
    pre_intermediate = "Pre-Intermediate"
    intermediate = "Intermediate"
    upper_intermediate = "Upper-Intermediate"
    advanced = "Advanced"


class ReferenceSourceEnum(str, Enum):
    """Источник, откуда пользователь узнал о школе."""

    friends = "friends"
    internet = "internet"
    telegram = "telegram"
    other = "other"


class PreviousExperienceEnum(str, Enum):
    """Опыт изучения английского языка."""

    never = "never"
    school = "school"
    university = "university"
    courses = "courses"
    self_study = "self_study"


# =============================================================================
# Модель сессии пользователя
# =============================================================================


class UserSession(Base):
    """
    Запись о пользователе, взаимодействующем с платформой через Telegram.

    Атрибуты:
        telegram_id: Telegram ID пользователя (PK).
        telegram_username: Username пользователя.
        application_ids: Список ID созданных пользователем заявок.
        started_at: Время начала первой сессии.
        dropbox_folder_id: Индивидуальная папка пользователя в Dropbox.
    """

    __tablename__ = "user_sessions"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_username: Mapped[str | None] = mapped_column(nullable=True)

    application_ids: Mapped[list[int] | None] = mapped_column(
        PG_ARRAY(Integer), nullable=True, comment="Список ID заявок пользователя."
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    dropbox_folder_id: Mapped[str | None] = mapped_column(
        String(), nullable=True, comment="Персональная Dropbox-папка пользователя."
    )


# =============================================================================
# Модель заявки
# =============================================================================


class Application(Base):
    """
    Модель заявки пользователя на обучение.

    Содержит основную информацию о заявителе, параметрах обучения,
    предпочитаемом формате занятий, а также ссылку на PDF-файл заявки,
    загруженный в Dropbox (по уникальному file_id).

    Attributes:
        user_id (int): Telegram ID пользователя (внешний ключ).
        applicant_name (str): Имя заявителя.
        phone_number (str): Номер телефона в формате +998XXXXXXXXX.
        applicant_age (int): Возраст заявителя (1–99).
        preferred_class_format (list[PreferredClassFormatEnum]):
            Желаемые форматы обучения (индивидуально, группы и т. д.).
        preferred_study_mode (list[PreferredStudyModeEnum]):
            Режимы обучения (online/offline).
        level (LevelEnum | None): Уровень английского по шкале CEFR.
        possible_scheduling (list[dict]): Удобное время (“day”, “times”).
        created_at (datetime): Время создания заявки.
        dropbox_file_id (str): Уникальный Dropbox file_id PDF-файла заявки.
        file_name (str): Имя PDF-файла заявки, сохранённого в Dropbox.
        reference_source (ReferenceSourceEnum | None):
            Как пользователь узнал о школе.
        need_ielts (bool | None): Нужен ли IELTS курс.
        studied_at_lanex (bool): Учился ли ранее в Lanex.
        previous_experience (list[PreviousExperienceEnum] | None):
            Предыдущий опыт изучения английского.
    """

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_sessions.telegram_id"), nullable=False
    )

    applicant_name: Mapped[str] = mapped_column(
        String(MAX_APPLICANT_NAME_LENGTH), nullable=False
    )

    phone_number: Mapped[str] = mapped_column(
        String(PHONE_NUMBER_LENGTH), nullable=False
    )

    applicant_age: Mapped[int] = mapped_column(
        Integer, CheckConstraint("applicant_age BETWEEN 1 AND 99"), nullable=False
    )

    preferred_class_format: Mapped[list[PreferredClassFormatEnum]] = mapped_column(
        PG_ARRAY(
            SqlEnum(
                PreferredClassFormatEnum,
                name="preferred_class_format_enum",
                native_enum=False,
            )
        ),
        nullable=False,
    )

    preferred_study_mode: Mapped[list[PreferredStudyModeEnum]] = mapped_column(
        PG_ARRAY(
            SqlEnum(
                PreferredStudyModeEnum,
                name="preferred_study_mode_enum",
                native_enum=False,
            )
        ),
        nullable=False,
    )

    level: Mapped[LevelEnum | None] = mapped_column(
        SqlEnum(LevelEnum, name="level_enum", native_enum=False), nullable=True
    )

    possible_scheduling: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, comment='Например: [{"day": "Monday", "times": ["Any"]}]'
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    dropbox_file_id: Mapped[str] = mapped_column(
        String(), nullable=False, comment="Уникальный Dropbox file_id PDF-файла заявки."
    )

    file_name: Mapped[str] = mapped_column(
        String(), nullable=False, comment="Имя PDF-файла заявки, сохраняемое в Dropbox."
    )

    reference_source: Mapped[ReferenceSourceEnum | None] = mapped_column(
        SqlEnum(ReferenceSourceEnum, name="reference_source_enum", native_enum=False),
        nullable=True,
    )

    need_ielts: Mapped[bool | None] = mapped_column(Boolean(), nullable=True)

    studied_at_lanex: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, default=False
    )

    previous_experience: Mapped[list[PreviousExperienceEnum] | None] = mapped_column(
        PG_ARRAY(
            SqlEnum(
                PreviousExperienceEnum,
                name="previous_experience_enum",
                native_enum=False,
            )
        ),
        nullable=True,
    )


# =============================================================================
# Модель результата теста
# =============================================================================


class TestResult(Base):
    """
    Результат прохождения теста пользователем.

    Хранит уровень тестируемого, ответы на задания,
    итоговый балл, а также ссылку на PDF-файл результата,
    загруженный в Dropbox (через уникальный file_id).

    Attributes:
        user_id (int): Telegram ID пользователя (FK).
        test_taker (str | None): Имя участника теста.
        level (LevelEnum): Уровень теста (Starter — Advanced).
        closed_answers (dict | None): Ответы на закрытые вопросы.
        open_answers (dict | None): Ответы на открытые задания.
        score (dict | None): Баллы за задания.
        dropbox_file_id (str): Уникальный Dropbox file_id PDF результата.
        file_name (str): Имя PDF-файла результата теста.
        submitted_at (datetime): Дата и время отправки результата.
    """

    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_sessions.telegram_id"), nullable=False
    )

    test_taker: Mapped[str | None] = mapped_column(
        String(MAX_APPLICANT_NAME_LENGTH), nullable=True, comment="Имя участника теста."
    )

    level: Mapped[LevelEnum] = mapped_column(
        SqlEnum(LevelEnum, name="level_enum", native_enum=False), nullable=False
    )

    closed_answers: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment='{"task_1": {"Q1": {"answer": "A", "status": "correct"}}}',
    )

    open_answers: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment='{"Q5": "текст ответа"}'
    )

    score: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment='{"task_1": 7, "task_2": 4}'
    )

    dropbox_file_id: Mapped[str] = mapped_column(
        String(),
        nullable=False,
        comment="Уникальный Dropbox file_id PDF результата теста.",
    )

    file_name: Mapped[str] = mapped_column(
        String(), nullable=False, comment="Имя PDF-файла результата теста."
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
