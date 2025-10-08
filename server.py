import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import check_api, application_api
from aiogram import Bot, Dispatcher
from telegram.handlers import register_handlers
from database.config import settings
from database.utils import init_db  # 👈 добавляем импорт

BASE_DIR = Path(__file__).resolve().parent

# === Aiogram bot ===
logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()
register_handlers(dp)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Фаза запуска и завершения FastAPI"""
    # === Инициализация БД ===
    try:
        logging.info("⏳ Проверка и создание таблиц в базе данных...")
        await init_db()
        logging.info("✅ Таблицы успешно созданы или уже существуют.")
    except Exception as e:
        logging.error(f"❌ Ошибка при инициализации базы данных: {e}")
        raise e

    # === Запуск Telegram-бота ===
    asyncio.create_task(dp.start_polling(bot))
    logging.info("🚀 Aiogram бот запущен вместе с FastAPI")

    yield  # --- здесь FastAPI работает ---

    # === Остановка Telegram-бота ===
    await bot.session.close()
    logging.info("🛑 Aiogram бот остановлен")


app = FastAPI(lifespan=lifespan)

# === FastAPI static and routes ===
app.mount(
    "/html_pages",
    StaticFiles(directory=BASE_DIR / "html_pages"),
    name="html_pages",
)

app.include_router(check_api.router)
app.include_router(application_api.router)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Root endpoint ===
@app.get("/")
async def root():
    return {"status": "ok", "bot": "running"}
