"""
CRUD-операции для работы с моделью Application.

Содержит функции для создания, чтения и обновления заявок.
Выполняет валидацию Enum-полей, преобразуя входные строки
в соответствующие объекты перечислений.

Используемые компоненты:
    - SQLAlchemy AsyncSession
    - Модель Application
    - Перечисления LevelEnum, PreferredClassFormatEnum и др.
    - Логирование через logging_config.logger
"""

from typing import Any, Dict, List, Optional, Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Application,
    LevelEnum,
    PreferredClassFormatEnum,
    PreferredStudyModeEnum,
    PreviousExperienceEnum,
    ReferenceSourceEnum,
)
from logging_config import logger


def validate_enum_fields(data: dict) -> dict:
    """
    Валидирует и преобразует строковые значения полей в Enum-поля модели.

    Args:
        data (dict): Словарь входных данных с полями заявки.

    Returns:
        dict: Словарь тех же полей, но преобразованных в объекты Enum.

    Raises:
        ValueError: Если какое-либо значение не соответствует Enum.
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

    validated: dict = {}

    # одиночные Enum
    for field, enum_cls in single_enum_fields.items():
        value = data.get(field)
        if value is None:
            validated[field] = None
            continue
        try:
            validated[field] = enum_cls(value)
        except ValueError as err:
            raise ValueError(
                f"Недопустимое значение '{value}' для поля '{field}'"
            ) from err

    # Enum-списки
    for field, enum_cls in list_enum_fields.items():
        values = data.get(field)
        if values is None:
            validated[field] = None
            continue

        if not isinstance(values, list):
            raise ValueError(
                f"Поле '{field}' должно быть списком, получено: {type(values).__name__}"
            )

        try:
            validated[field] = [enum_cls(item) for item in values]
        except ValueError as err:
            raise ValueError(
                f"Недопустимые значения в поле '{field}': {values}"
            ) from err

    return validated


async def create_application(
    session: AsyncSession,
    user_id: int,
    applicant_name: str,
    phone_number: str,
    applicant_age: int,
    preferred_class_format: List[str],
    preferred_study_mode: List[str],
    level: Optional[str],
    possible_scheduling: List[Dict[str, Any]],
    reference_source: Optional[str],
    need_ielts: Optional[bool],
    studied_at_lanex: bool,
    previous_experience: Optional[List[str]],
    dropbox_file_id: str,
    file_name: str,
) -> Application:
    """
    Создаёт новую заявку.

    Args:
        session (AsyncSession): Асинхронная сессия БД.
        user_id (int): Telegram ID пользователя.
        applicant_name (str): Имя заявителя.
        phone_number (str): Номер телефона.
        applicant_age (int): Возраст.
        preferred_class_format (list[str]): Форматы занятий.
        preferred_study_mode (list[str]): Режимы обучения.
        level (str | None): Уровень английского.
        possible_scheduling (list[dict]): Доступные дни и время.
        reference_source (str | None): Источник информации о школе.
        need_ielts (bool | None): Нужен ли IELTS.
        studied_at_lanex (bool): Учился ли ранее.
        previous_experience (list[str] | None): Предыдущий опыт.
        dropbox_file_id (str): file_id PDF заявки в Dropbox.
        file_name (str): Имя PDF файла.

    Returns:
        Application: Созданная заявка.

    Raises:
        SQLAlchemyError: Ошибка взаимодействия с базой данных.
    """
    validated = validate_enum_fields(
        {
            "level": level,
            "preferred_class_format": preferred_class_format,
            "preferred_study_mode": preferred_study_mode,
            "reference_source": reference_source,
            "previous_experience": previous_experience,
        }
    )

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
            dropbox_file_id=dropbox_file_id,
            file_name=file_name,
        )

        session.add(new_application)
        await session.commit()
        return new_application

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error("❌ Database error in create_application: %s", e)
        raise e


async def update_application_by_id(
    session: AsyncSession,
    id: int,
    user_id: int,
    applicant_name: str,
    phone_number: str,
    applicant_age: int,
    preferred_class_format: List[str],
    preferred_study_mode: List[str],
    level: Optional[str],
    possible_scheduling: List[Dict[str, Any]],
    reference_source: Optional[str],
    need_ielts: Optional[bool],
    studied_at_lanex: bool,
    previous_experience: Optional[List[str]],
    dropbox_file_id: Optional[str] = None,
    file_name: Optional[str] = None,
) -> Application:
    """
    Обновляет заявку по её ID.

    Args:
        session (AsyncSession): Асинхронная сессия БД.
        id (int): ID заявки.
        user_id (int): Telegram ID пользователя.
        applicant_name (str): Имя заявителя.
        phone_number (str): Номер телефона.
        applicant_age (int): Возраст.
        preferred_class_format (list[str]): Форматы занятий.
        preferred_study_mode (list[str]): Режимы обучения.
        level (str | None): Уровень английского.
        possible_scheduling (list[dict]): Доступные дни и время.
        reference_source (str | None): Источник информации о школе.
        need_ielts (bool | None): Нужен ли IELTS.
        studied_at_lanex (bool): Учился ли ранее.
        previous_experience (list[str] | None): Предыдущий опыт.
        dropbox_file_id (str): file_id PDF заявки в Dropbox.
        file_name (str): Имя PDF файла.

    Returns:
        Application: Обновлённая заявка.

    Raises:
        HTTPException: Если заявка не найдена.
        SQLAlchemyError: Ошибка БД.
    """
    validated = validate_enum_fields(
        {
            "level": level,
            "preferred_class_format": preferred_class_format,
            "preferred_study_mode": preferred_study_mode,
            "reference_source": reference_source,
            "previous_experience": previous_experience,
        }
    )

    try:
        app = await read_application_by_id(session, id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

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

        # обновление файлов — если переданы
        if dropbox_file_id:
            fields_to_update["dropbox_file_id"] = dropbox_file_id
        if file_name:
            fields_to_update["file_name"] = file_name

        for field, new_value in fields_to_update.items():
            if getattr(app, field) != new_value:
                setattr(app, field, new_value)

        await session.commit()
        return app

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error("❌ Database error in update_application_by_id: %s", e)
        raise e


async def read_application_by_id(
    session: AsyncSession, id: int
) -> Optional[Application]:
    """
    Возвращает заявку по её ID.

    Args:
        session (AsyncSession): Сессия БД.
        id (int): ID заявки.

    Returns:
        Application | None: Найденная заявка.
    """
    try:
        result = await session.execute(select(Application).where(Application.id == id))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error("❌ Database error in read_application_by_id: %s", e)
        raise e


async def read_application_by_user_id(
    session: AsyncSession, user_id: int
) -> Sequence[Application]:
    """
    Возвращает все заявки пользователя.

    Args:
        session (AsyncSession): Сессия БД.
        user_id (int): Telegram ID пользователя.

    Returns:
        list[Application]: Список заявок.
    """
    try:
        result = await session.execute(
            select(Application).where(Application.user_id == user_id)
        )
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error("❌ Database error in read_application_by_user_id: %s", e)
        raise e
