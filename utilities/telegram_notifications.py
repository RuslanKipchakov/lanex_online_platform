import aiohttp
import os
from logging_config import logger
from database.config import settings


async def send_pdf_to_admin(file_path: str, caption: str = ""):
    """
    Отправляет PDF-файл админу в Telegram.
    """
    bot_token = settings.telegram_bot_token
    admin_id = settings.admin_telegram_id

    if not bot_token or not admin_id:
        logger.error("❌ TELEGRAM_BOT_TOKEN или ADMIN_TELEGRAM_ID не указаны в настройках.")
        return

    send_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("chat_id", str(admin_id))
                form.add_field("document", f, filename=os.path.basename(file_path))
                form.add_field("caption", caption or "Новая заявка получена 📄")

                async with session.post(send_url, data=form) as response:
                    if response.status == 200:
                        logger.info(f"📨 PDF успешно отправлен админу ({admin_id}).")
                    else:
                        text = await response.text()
                        logger.error(f"⚠️ Ошибка при отправке PDF админу: {response.status} — {text}")
    except Exception as e:
        logger.error(f"❌ Исключение при отправке PDF админу: {e}")
