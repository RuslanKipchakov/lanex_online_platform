import asyncio
from sqlalchemy import text

from .base import engine, AsyncSessionLocal, Base
from . import models


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
