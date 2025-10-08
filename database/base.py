import asyncio
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Базовый класс для моделей"""
    ...


# Асинхронный движок
engine = create_async_engine(settings.db_url, echo=False)

# Фабрика для сессий
AsyncSessionLocal = async_sessionmaker[AsyncSession](
    bind=engine, expire_on_commit=False
)


# Генератор сессий (для зависимостей в FastAPI)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
