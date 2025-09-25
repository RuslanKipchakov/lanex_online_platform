import asyncio
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Базовый класс для моделей"""

    ...


engine = create_async_engine(settings.db_url, echo=False)
AsyncSessionLocal = async_sessionmaker[AsyncSession](
    bind=engine, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Создаёт сессию для асинхронной работы с базой данных"""
    async with AsyncSessionLocal() as session:
        yield session


from database.models import *  # noqa: F401, E402, F403


async def test_async_db() -> None:
    """Проверяет асинхронное соединение с базой данных"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        if result.scalar() == 1:
            print("Асинхронное соединение установлено!")
        else:
            print("ОШИБКА: Асинхронное соединение не установлено!")


async def init_db() -> None:
    """Проверяет соединение с базой данных и создаёт таблицы"""
    await test_async_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Таблицы успешно созданы.")


if __name__ == "__main__":
    asyncio.run(init_db())