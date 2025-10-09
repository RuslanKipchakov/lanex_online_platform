from __future__ import annotations

from enum import Enum
from datetime import datetime, timezone

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    CheckConstraint,
    JSON,
    Boolean,
    DateTime,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY

from .base import Base


# --- Константы ---
MIN_APPLICANT_NAME_LENGTH = 2
MAX_APPLICANT_NAME_LENGTH = 50
PHONE_NUMBER_LENGTH = 13  # Формат: +998XXXXXXXXX


# --- ENUM классы ---
class SessionStatusEnum(str, Enum):
    initiated = "initiated"
    in_progress = "in_progress"
    completed = "completed"


class PreferredClassFormatEnum(str, Enum):
    individual = "individual"
    pair = "pair"
    group = "group"


class PreferredStudyModeEnum(str, Enum):
    online = "online"
    offline = "offline"


class LevelEnum(str, Enum):
    starter = "starter"
    elementary = "elementary"
    pre_intermediate = "pre-intermediate"
    intermediate = "intermediate"
    upper_intermediate = "upper-intermediate"
    advanced = "advanced"


class ReferenceSourceEnum(str, Enum):
    friends = "friends"
    internet = "internet"
    telegram = "telegram"
    other = "other"


class PreviousExperienceEnum(str, Enum):
    never = "never"
    school = "school"
    university = "university"
    courses = "courses"
    self_study = "self_study"


# --- Модель сессии пользователя ---
class UserSession(Base):
    __tablename__ = "user_sessions"

    telegram_id: Mapped[int] = mapped_column(primary_key=True)
    telegram_username: Mapped[str] = mapped_column(nullable=True)

    # Список ID заявок, созданных пользователем
    application_ids: Mapped[list[int]] = mapped_column(
        PG_ARRAY(Integer),
        nullable=True,
        comment="Список ID заявок, связанных с этим пользователем"
    )

    status: Mapped[SessionStatusEnum] = mapped_column(
        SqlEnum(SessionStatusEnum, name="session_status_enum", native_enum=False),
        nullable=False,
        default=SessionStatusEnum.initiated
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


# --- Модель заявки ---
class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_sessions.telegram_id"), nullable=False)

    applicant_name: Mapped[str] = mapped_column(String(MAX_APPLICANT_NAME_LENGTH), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(PHONE_NUMBER_LENGTH), nullable=False)

    applicant_age: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("applicant_age BETWEEN 1 AND 99"),
        nullable=False
    )

    preferred_class_format: Mapped[list[PreferredClassFormatEnum]] = mapped_column(
        PG_ARRAY(SqlEnum(PreferredClassFormatEnum, name="preferred_class_format_enum", native_enum=False)),
        nullable=False
    )

    preferred_study_mode: Mapped[list[PreferredStudyModeEnum]] = mapped_column(
        PG_ARRAY(SqlEnum(PreferredStudyModeEnum, name="preferred_study_mode_enum", native_enum=False)),
        nullable=False
    )

    level: Mapped[LevelEnum] = mapped_column(
        SqlEnum(LevelEnum, name="level_enum", native_enum=False),
        nullable=True
    )

    possible_scheduling: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        comment='Example: [{"day": "Monday", "times": ["Any"]}]'
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    pdf_path: Mapped[str] = mapped_column(String(), nullable=False)

    reference_source: Mapped[ReferenceSourceEnum] = mapped_column(
        SqlEnum(ReferenceSourceEnum, name="reference_source_enum", native_enum=False),
        nullable=True
    )

    need_ielts: Mapped[bool] = mapped_column(Boolean(), nullable=True)

    studied_at_lanex: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)

    previous_experience: Mapped[list[PreviousExperienceEnum]] = mapped_column(
        PG_ARRAY(SqlEnum(PreviousExperienceEnum, name="previous_experience_enum", native_enum=False)),
        nullable=True
    )


# --- Модель результата теста ---
class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_sessions.telegram_id"),
        nullable=False
    )

    # Имя тестируемого (из формы или Telegram username)
    test_taker: Mapped[str] = mapped_column(
        String(MAX_APPLICANT_NAME_LENGTH),
        nullable=True,
        comment="Имя участника теста (из формы или Telegram)"
    )

    level: Mapped[LevelEnum] = mapped_column(
        SqlEnum(LevelEnum, name="level_enum", native_enum=False),
        nullable=False
    )

    closed_answers: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment='{"task_1": {"Q1": {"answer": "A", "status": "correct"}}}'
    )

    open_answers: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment='{"Q5": "user answer", "Q6": "another answer"}'
    )

    score: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment='{"task_1": 7, "task_2": 4} — баллы по частям'
    )

    pdf_path: Mapped[str] = mapped_column(
        String(),
        nullable=False
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
