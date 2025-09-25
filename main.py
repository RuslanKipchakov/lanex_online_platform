import asyncio
import logging

import uvicorn
from aiogram import Bot, Dispatcher

from lanex_online_platform.server import app  # твой FastAPI
from lanex_online_platform.database.config import settings
from lanex_online_platform.telegram.handlers import register_handlers


logging.basicConfig(level=logging.INFO)


async def start_bot():
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    register_handlers(dp)
    logging.info("🤖 Telegram бот запущен...")
    await dp.start_polling(bot)


async def start_server():
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8000,
        reload=False,   # reload нельзя в комбинированном режиме
        log_level="info"
    )
    server = uvicorn.Server(config)
    logging.info("🌐 FastAPI сервер запущен...")
    await server.serve()


async def main():
    # Запускаем и сервер, и бота параллельно
    await asyncio.gather(
        start_server(),
        start_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
