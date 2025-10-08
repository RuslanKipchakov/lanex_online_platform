from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from logging_config import logger
from database.models import (
    Application,
    LevelEnum,
    PreferredClassFormatEnum,
    PreferredStudyModeEnum,
    ReferenceSourceEnum,
    PreviousExperienceEnum,
)


def validate_enum_fields(data: dict) -> dict:
    """
    Валидирует поля Enum. Для полей, которые являются списками, проверяет каждый элемент.
    """
    single_enum_fields = {
        "level": LevelEnum,
        "reference_source": ReferenceSourceEnum,
    }

    list_enum_fields = {
        "preferred_class_format": PreferredClassFormatEnum,
        "preferred_study_mode": PreferredStudyModeEnum,
        "previous_experience": PreviousExperienceEnum,
    }

    validated = {}

    # одиночные поля
    for field, enum_cls in single_enum_fields.items():
        value = data.get(field)
        if value is None:
            validated[field] = None
            continue
        try:
            validated[field] = enum_cls(value)
        except ValueError:
            raise ValueError(f"Недопустимое значение поля '{field}': {value}")

    # поля-списки
    for field, enum_cls in list_enum_fields.items():
        values = data.get(field)
        if values is None:
            validated[field] = None
            continue
        if not isinstance(values, list):
            raise ValueError(f"Поле '{field}' должно быть списком, got {type(values).__name__}")
        try:
            validated[field] = [enum_cls(item) for item in values]
        except ValueError:
            raise ValueError(f"Недопустимое значение в поле '{field}': {values}")

    return validated


async def create_application(
    session: AsyncSession,
    user_id: int,
    applicant_name: str,
    phone_number: str,
    applicant_age: int,
    preferred_class_format: list[str],
    preferred_study_mode: list[str],
    level: str | None,
    possible_scheduling: list[dict[str, object]],
    reference_source: str | None,
    need_ielts: bool | None,
    studied_at_lanex: bool,
    previous_experience: list[str] | None,
    pdf_path: str,
):
    validated = validate_enum_fields({
        "level": level,
        "preferred_class_format": preferred_class_format,
        "preferred_study_mode": preferred_study_mode,
        "reference_source": reference_source,
        "previous_experience": previous_experience,
    })

    try:
        new_application = Application(
            user_id=user_id,
            applicant_name=applicant_name,
            phone_number=phone_number,
            applicant_age=applicant_age,
            preferred_class_format=validated["preferred_class_format"],
            preferred_study_mode=validated["preferred_study_mode"],
            level=validated["level"],
            possible_scheduling=possible_scheduling,
            reference_source=validated["reference_source"],
            need_ielts=need_ielts,
            studied_at_lanex=studied_at_lanex,
            previous_experience=validated.get("previous_experience"),
            pdf_path=pdf_path,
        )
        session.add(new_application)
        await session.commit()
        return new_application

    except SQLAlchemyError as e:
        logger.error("Database error in create_application: %s", e)
        await session.rollback()
        raise e


async def update_application_by_id(
    session: AsyncSession,
    id: int,
    user_id: int,
    applicant_name: str,
    phone_number: str,
    applicant_age: int,
    preferred_class_format: list[str],
    preferred_study_mode: list[str],
    level: str | None,
    possible_scheduling: list[dict[str, object]],
    reference_source: str | None,
    need_ielts: bool | None,
    studied_at_lanex: bool,
    previous_experience: list[str] | None,
):
    validated = validate_enum_fields({
        "level": level,
        "preferred_class_format": preferred_class_format,
        "preferred_study_mode": preferred_study_mode,
        "reference_source": reference_source,
        "previous_experience": previous_experience,
    })

    try:
        old = await read_application_by_id(session, id)
        if not old:
            raise HTTPException(status_code=404, detail="Application not found")

        has_changes = False
        fields_to_update = {
            "user_id": user_id,
            "applicant_name": applicant_name,
            "phone_number": phone_number,
            "applicant_age": applicant_age,
            "preferred_class_format": validated["preferred_class_format"],
            "preferred_study_mode": validated["preferred_study_mode"],
            "level": validated["level"],
            "possible_scheduling": possible_scheduling,
            "reference_source": validated["reference_source"],
            "need_ielts": need_ielts,
            "studied_at_lanex": studied_at_lanex,
            "previous_experience": validated.get("previous_experience"),
        }

        for field, new_value in fields_to_update.items():
            if getattr(old, field) != new_value:
                setattr(old, field, new_value)
                has_changes = True

        if has_changes:
            await session.commit()

        return old

    except SQLAlchemyError as e:
        logger.error("Database error in update_application_by_id: %s", e)
        await session.rollback()
        raise e


async def read_application_by_id(session: AsyncSession, id: int):
    try:
        result = await session.execute(select(Application).where(Application.id == id))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error("Database error in read_application_by_id: %s", e)
        raise e


async def read_application_by_user_id(session: AsyncSession, user_id: int):
    try:
        result = await session.execute(select(Application).where(Application.user_id == user_id))
        return result.scalars().all()  # список заявок
    except SQLAlchemyError as e:
        logger.error("Database error in read_application_by_user_id: %s", e)
        raise e

