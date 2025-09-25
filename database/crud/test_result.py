from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from lanex_online_platform.logging_config import logger
from lanex_online_platform.database.models import TestResult, LevelEnum

async def create_test_result(
        session: AsyncSession,
        user_id: int,
        level: str,
        closed_answers: dict,
        open_answers: dict,
        score: dict,
        pdf_path: str,
):
    try:
        level = LevelEnum(level)
    except ValueError:
        raise ValueError(f"Недопустимый уровень: {level}")
    try:
        new_test_result = TestResult(
            user_id=user_id,
            level=level,
            closed_answers=closed_answers,
            open_answers=open_answers,
            score=score,
            pdf_path=pdf_path
        )
        session.add(new_test_result)
        await session.commit()

    except SQLAlchemyError as e:
        logger.error("Database error in create_test_result: %s", e)
        raise e


async def read_test_result_by_id(session: AsyncSession, id: int):
    try:
        result = await session.execute(select(TestResult).where(TestResult.id == id))
        test_result = result.scalar_one_or_none()
        return test_result
    except SQLAlchemyError as e:
        logger.error("Database error in read_test_result_by_id: %s", e)
        raise e
