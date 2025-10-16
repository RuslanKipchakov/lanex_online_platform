import os
import logging
from datetime import datetime
import dropbox
from dropbox.exceptions import AuthError, ApiError
from database.config import settings

logger = logging.getLogger("lanex_backend")


def get_dropbox_client():
    """Инициализация клиента Dropbox с проверкой токена"""
    access_token = settings.dropbox_access_token

    if not access_token:
        logger.error("❌ DROPBOX_ACCESS_TOKEN не найден в переменных окружения.")
        raise ValueError("DROPBOX_ACCESS_TOKEN отсутствует.")

    try:
        dbx = dropbox.Dropbox(access_token)
        dbx.users_get_current_account()  # Проверка валидности токена
        logger.info("✅ Dropbox клиент успешно инициализирован.")
        return dbx
    except AuthError:
        logger.error("❌ Ошибка авторизации Dropbox. Проверь токен.")
        raise


def upload_to_dropbox(
    local_path: str,
    telegram_id: int,
    username: str,
    file_type: str,  # "application" или "test-report"
    level: str | None = None,
    dropbox_folder: str | None = None,
) -> str:
    """
    Загружает файл в Dropbox в структуре:
    /Lanex/users/{date_telegramid}/{applications|test-reports}/ФАЙЛ.pdf
    """
    dbx = get_dropbox_client()

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Файл не найден: {local_path}")

    # === 1️⃣ Определяем базовые значения ===
    dropbox_folder = dropbox_folder or settings.dropbox_folder_path or "/Lanex"
    date_str = datetime.now().strftime("%d-%m-%Y")
    folder_name = f"{date_str}_{telegram_id}"
    safe_username = username.replace(" ", "_")

    # === 2️⃣ Определяем подтип (application / test-report) ===
    if file_type == "application":
        subfolder = "applications"
        filename = f"NEW_APPLICATION_{safe_username}_{date_str}.pdf"
    elif file_type == "test-report":
        subfolder = "test-reports"
        filename = f"TEST_REPORT_{safe_username}_{date_str}_{level or 'Unknown'}.pdf"
    else:
        raise ValueError(f"Некорректный тип файла: {file_type}")

    # === 3️⃣ Формируем итоговый путь в Dropbox ===
    dropbox_path = (
        f"{dropbox_folder.rstrip('/')}/users/{folder_name}/{subfolder}/{filename}"
    )

    # === 4️⃣ Создаём путь и загружаем ===
    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

    logger.info(f"✅ Файл загружен в Dropbox: {dropbox_path}")
    return dropbox_path

