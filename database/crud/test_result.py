from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from logging_config import logger
from database.models import TestResult, LevelEnum


async def create_test_result(
    session: AsyncSession,
    user_id: int,
    test_taker: str,
    level: str,
    closed_answers: dict | None,
    open_answers: dict | None,
    score: dict | None,
    pdf_path: str,
):
    """Создание записи о результате теста."""
    try:
        try:
            level_enum = LevelEnum(level)
        except ValueError:
            raise ValueError(f"Недопустимый уровень теста: {level}")

        new_test_result = TestResult(
            user_id=user_id,
            test_taker=test_taker,
            level=level_enum,
            closed_answers=closed_answers,
            open_answers=open_answers,
            score=score,
            pdf_path=pdf_path,
        )
        session.add(new_test_result)
        await session.commit()
        await session.refresh(new_test_result)

        return new_test_result

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error("Ошибка при создании TestResult: %s", e)
        raise e


async def read_test_result_by_id(session: AsyncSession, id: int) -> TestResult | None:
    """Чтение результата теста по ID."""
    try:
        result = await session.execute(
            select(TestResult).where(TestResult.id == id)
        )
        return result.scalar_one_or_none()

    except SQLAlchemyError as e:
        logger.error("Ошибка при чтении TestResult по ID: %s", e)
        raise e


async def read_test_results_by_user(session: AsyncSession, user_id: int) -> list[TestResult]:
    """Чтение всех результатов тестов пользователя."""
    try:
        result = await session.execute(
            select(TestResult).where(TestResult.user_id == user_id)
        )
        return result.scalars().all()

    except SQLAlchemyError as e:
        logger.error("Ошибка при чтении TestResult по user_id: %s", e)
        raise e
