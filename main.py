import asyncio
import logging
import os

import uvicorn
from aiogram import Bot, Dispatcher

from server import app
from database.config import settings
from telegram.handlers import register_handlers


logging.basicConfig(level=logging.INFO)


async def start_bot():
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    register_handlers(dp)
    logging.info("🤖 Telegram бот запущен...")
    await dp.start_polling(bot)


async def start_server():
    port = int(os.environ.get("PORT", 8000))  # Railway сам задаёт PORT
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",  # обязательно для внешнего доступа
        port=port,
        reload=False,
        log_level="info"
    )
    server = uvicorn.Server(config)
    logging.info(f"🌐 FastAPI сервер запущен на 0.0.0.0:{port} ...")
    await server.serve()


async def main():
    # Запускаем и сервер, и бота параллельно
    await asyncio.gather(
        start_server(),
        start_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
