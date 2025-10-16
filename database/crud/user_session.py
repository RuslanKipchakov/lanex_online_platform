from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from logging_config import logger
from database.models import UserSession, SessionStatusEnum


async def create_user_session(session: AsyncSession, telegram_id: int, telegram_username: str = None):
    try:
        user_session = await read_user_session(session, telegram_id)
        if not user_session:
            new_user_session = UserSession(
                telegram_id=telegram_id,
                telegram_username=telegram_username,
            )
            session.add(new_user_session)
        await session.commit()
    except SQLAlchemyError as e:
        logger.error("Database error in create_user_session: %s", e)
        raise e


async def read_user_session(session: AsyncSession, telegram_id: int):
    try:
        result = await session.execute(select(UserSession).where(UserSession.telegram_id == telegram_id))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error("Database error in read_user_session: %s", e)
        raise e


async def update_user_session_status(session: AsyncSession, telegram_id: int, new_status_str: str):
    try:
        new_status = SessionStatusEnum(new_status_str)
    except ValueError:
        raise ValueError(f"Недопустимый статус: {new_status_str}")

    try:
        user_session = await read_user_session(session, telegram_id)
        if not user_session:
            raise HTTPException(status_code=404, detail="UserSession not found")

        user_session.status = new_status
        await session.commit()
    except SQLAlchemyError as e:
        logger.error("Database error in update_user_session_status: %s", e)
        raise e


# ✅ Новая функция: добавление ID заявки в user_session
async def append_application_id(session: AsyncSession, telegram_id: int, application_id: int):
    """
    Добавляет ID новой заявки в список application_ids пользователя.
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
        logger.info(f"🟢 Добавлен application_id={application_id} пользователю {telegram_id}")
    except SQLAlchemyError as e:
        logger.error("Database error in append_application_id: %s", e)
        raise e
