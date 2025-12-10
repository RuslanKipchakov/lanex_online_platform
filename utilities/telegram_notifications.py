"""
Утилиты для отправки уведомлений в Telegram.

Содержит функции для:
    - отправки PDF-файлов администраторам.
"""

import os
from typing import Optional

import aiohttp

from config import settings
from logging_config import logger


async def send_pdf_to_admin(file_path: str, caption: Optional[str] = None) -> None:
    """
    Асинхронно отправляет PDF-файл администратору в Telegram.

    Аргументы:
        file_path (str): Путь к PDF-файлу.
        caption (Optional[str]): Подпись к сообщению. По умолчанию:
            "Новая заявка получена 📄".

    Примечания:
        - Использует TELEGRAM_BOT_TOKEN и ADMIN_TELEGRAM_ID из настроек.
        - Логирует ошибки в случае проблем с соединением или API.
    """
    bot_token = settings.telegram_bot_token
    admin_id = settings.admin_telegram_id

    if not bot_token or not admin_id:
        logger.error("❌ TELEGRAM_BOT_TOKEN или ADMIN_TELEGRAM_ID не указаны в настройках.")
        return

    caption = caption or "Новая заявка получена 📄"
    send_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("chat_id", str(admin_id))
                form.add_field("document", f, filename=os.path.basename(file_path))
                form.add_field("caption", caption)

                async with session.post(send_url, data=form) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(
                            f"❌ Ошибка при отправке PDF админу: {response.status} — {text}"
                        )
    except Exception as e:
        logger.exception(f"❌ Исключение при отправке PDF админу: {e}")
