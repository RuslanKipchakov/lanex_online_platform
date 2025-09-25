import asyncio
import logging
from aiogram import Bot, Dispatcher
from lanex_online_platform.database.config import settings
from lanex_online_platform.telegram.handlers import register_handlers

# Включаем логи, чтобы видеть, что бот работает
logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    register_handlers(dp)

    logging.info("🚀 Бот запущен и слушает обновления...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
