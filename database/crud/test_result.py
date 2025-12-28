"""
CRUD-операции для работы с моделью TestResult.

Содержит функции для:
    - создания результата теста.

Используемые компоненты:
    - SQLAlchemy AsyncSession
    - Модель TestResult
    - Перечисление LevelEnum
    - Логирование через logging_config.logger
"""

from typing import Any, Dict, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import LevelEnum, TestResult
from logging_config import logger


async def create_test_result(
    session: AsyncSession,
    user_id: int,
    test_taker: Optional[str],
    level: str,
    closed_answers: Optional[Dict[str, Any]],
    open_answers: Optional[Dict[str, Any]],
    score: Optional[Dict[str, Any]],
    dropbox_file_id: str,
    file_name: str,
) -> TestResult:
    """
    Создаёт запись результата теста.

    Args:
        session (AsyncSession): Асинхронная сессия БД.
        user_id (int): Telegram ID пользователя.
        test_taker (str | None): Имя участника теста.
        level (str): Уровень теста (Starter — Advanced).
        closed_answers (dict | None): Ответы на закрытые задания.
        open_answers (dict | None): Ответы на открытые задания.
        score (dict | None): Баллы по заданиям.
        dropbox_file_id (str): Уникальный file_id PDF результата.
        file_name (str): Имя PDF файла.

    Returns:
        TestResult: Созданный объект результата теста.

    Raises:
        ValueError: Если уровень теста некорректен.
        SQLAlchemyError: Если произошла ошибка БД.
    """
    try:
        try:
            level_enum = LevelEnum(level)
        except ValueError as err:
            raise ValueError(f"Недопустимый уровень теста: {level}") from err

        new_result = TestResult(
            user_id=user_id,
            test_taker=test_taker,
            level=level_enum,
            closed_answers=closed_answers,
            open_answers=open_answers,
            score=score,
            dropbox_file_id=dropbox_file_id,
            file_name=file_name,
        )

        session.add(new_result)
        await session.commit()
        await session.refresh(new_result)

        logger.info(
            "🟢 Создан TestResult для user_id=%s, уровень=%s, file_id=%s",
            user_id,
            level_enum.value,
            dropbox_file_id,
        )

        return new_result

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error("❌ Ошибка БД в create_test_result: %s", e)
        raise e
