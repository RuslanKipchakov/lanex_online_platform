"""Основная точка входа в приложение Lanex Online Platform.

Запускает FastAPI-сервер и Telegram-бот на одном event loop.

Компоненты:
    - FastAPI-приложение (REST API, статические файлы, CORS)
    - Aiogram-бот (асинхронный Telegram-бот)
    - Единый lifespan для управления жизненным циклом приложения
"""

import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher

from api import check_api, application_api
from telegram.handlers import register_handlers
from config import settings
from logging_config import logger

# Основные константы
BASE_DIR = Path(__file__).resolve().parent

# Инициализация Telegram-бота
bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()
register_handlers(dp)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управляет фазами запуска и завершения FastAPI-приложения.

    Действия при запуске:
        - Запуск Telegram-бота на фоне.

    Действия при завершении:
        - Корректное закрытие сессии Telegram-бота.
    """
    try:
        asyncio.create_task(dp.start_polling(bot))
        logger.info("🚀 Aiogram бот запущен вместе с FastAPI.")
    except Exception as e:
        logger.error(f"Ошибка при запуске Telegram-бота: {e}")
        raise e

    yield  # --- Приложение работает ---

    await bot.session.close()


# Инициализация FastAPI
app = FastAPI(lifespan=lifespan)


# Статические файлы
app.mount(
    "/html_pages",
    StaticFiles(directory=BASE_DIR / "html_pages"),
    name="html_pages",
)


# Подключение маршрутов
app.include_router(check_api.router)
app.include_router(application_api.router)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["null"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT"],
    allow_headers=["*"],
)


# Корневой эндпоинт
@app.get("/")
async def root():
    """Возвращает базовый статус работы приложения."""
    return {"status": "ok", "bot": "running"}
