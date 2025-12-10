"""
CRUD-операции для работы с моделью UserSession.

Содержит функции для:
    - создания пользовательской сессии,
    - чтения сессии по Telegram ID,
    - добавления ID заявок к пользователю,
    - сохранения уникального Dropbox folder_id.

Используемые компоненты:
    - SQLAlchemy AsyncSession
    - Модель UserSession
    - Логирование через logging_config.logger
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from logging_config import logger
from database.models import UserSession


async def create_user_session(
    session: AsyncSession,
    telegram_id: int,
    telegram_username: Optional[str] = None
) -> None:
    """
    Создаёт новую пользовательскую сессию, если она ещё не существует.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        telegram_id (int): Telegram ID пользователя.
        telegram_username (Optional[str]): Опциональный Telegram username.

    Raises:
        SQLAlchemyError: В случае ошибки работы с базой данных.
    """
    try:
        user_session = await read_user_session(session, telegram_id)

        if not user_session:
            new_user_session = UserSession(
                telegram_id=telegram_id,
                telegram_username=telegram_username
            )
            session.add(new_user_session)

        await session.commit()
    except SQLAlchemyError as e:
        logger.error("❌ Ошибка БД в create_user_session: %s", e)
        raise e


async def read_user_session(
    session: AsyncSession,
    telegram_id: int
) -> Optional[UserSession]:
    """
    Возвращает объект UserSession по Telegram ID.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        telegram_id (int): Telegram ID пользователя.

    Returns:
        Optional[UserSession]: Найденная сессия или None.

    Raises:
        SQLAlchemyError: В случае ошибки работы с базой данных.
    """
    try:
        result = await session.execute(
            select(UserSession).where(UserSession.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error("❌ Ошибка БД в read_user_session: %s", e)
        raise e


async def append_application_id(
    session: AsyncSession,
    telegram_id: int,
    application_id: int
) -> None:
    """
    Добавляет ID заявки в список application_ids пользователя.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        telegram_id (int): Telegram ID пользователя.
        application_id (int): ID новой заявки.

    Raises:
        HTTPException: Если пользовательская сессия не найдена.
        SQLAlchemyError: Ошибка работы с базой данных.
    """
    try:
        user_session = await read_user_session(session, telegram_id)
        if not user_session:
            raise HTTPException(status_code=404, detail="UserSession not found")

        if user_session.application_ids is None:
            user_session.application_ids = [application_id]
        else:
            if application_id not in user_session.application_ids:
                user_session.application_ids.append(application_id)

        await session.commit()
        logger.info(
            "🟢 Добавлен application_id=%s пользователю %s",
            application_id, telegram_id
        )
    except SQLAlchemyError as e:
        logger.error("❌ Ошибка БД в append_application_id: %s", e)
        raise e


async def update_dropbox_folder_id(
    session: AsyncSession,
    telegram_id: int,
    folder_id: str
) -> None:
    """
    Сохраняет или обновляет Dropbox folder_id для пользователя.

    Args:
        session (AsyncSession): Асинхронная сессия базы данных.
        telegram_id (int): Telegram ID пользователя.
        folder_id (str): Уникальный Dropbox folder_id.

    Raises:
        HTTPException: Если пользовательская сессия не найдена.
        SQLAlchemyError: Ошибка работы с базой данных.
    """
    try:
        user_session = await read_user_session(session, telegram_id)
        if not user_session:
            raise HTTPException(status_code=404, detail="UserSession not found")

        user_session.dropbox_folder_id = folder_id
        await session.commit()

        logger.info(
            "🟢 Dropbox folder_id сохранён для пользователя %s: %s",
            telegram_id, folder_id
        )
    except SQLAlchemyError as e:
        logger.error("❌ Ошибка БД в update_dropbox_folder_id: %s", e)
        raise e
