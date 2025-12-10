"""
База данных: движок, фабрика сессий и базовый класс моделей.

Этот модуль предоставляет:
    - Base — базовый класс для всех моделей SQLAlchemy.
    - engine — асинхронный движок PostgreSQL.
    - AsyncSessionLocal — фабрику асинхронных сессий.
    - get_db — генератор сессий для зависимостей FastAPI.

Используется во всех модулях БД.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей ORM."""
    pass


# Асинхронный движок PostgreSQL
engine = create_async_engine(
    settings.db_url,
    echo=False,
)


# Фабрика асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный генератор сессий базы данных.

    Используется в зависимостях FastAPI:
        Depends(get_db)

    Returns:
        AsyncGenerator[AsyncSession, None]: сессия БД.
    """
    async with AsyncSessionLocal() as session:
        yield session
