import os
import logging
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
        dbx.users_get_current_account()  # Проверим токен
        logger.info("✅ Dropbox клиент успешно инициализирован.")
        return dbx
    except AuthError:
        logger.error("❌ Ошибка авторизации Dropbox. Проверь токен.")
        raise


def upload_to_dropbox(local_path: str, dropbox_folder: str | None = None) -> str:
    """
    Загружает файл в Dropbox и возвращает путь в облаке.
    """
    dbx = get_dropbox_client()

    if not os.path.exists(local_path):
        logger.error(f"❌ Файл не найден: {local_path}")
        raise FileNotFoundError(f"Файл не найден: {local_path}")

    dropbox_folder = dropbox_folder or settings.dropbox_folder_path or "/Lanex"
    file_name = os.path.basename(local_path)
    dropbox_path = f"{dropbox_folder.rstrip('/')}/{file_name}"

    try:
        with open(local_path, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        logger.info(f"✅ Файл успешно загружен в Dropbox: {dropbox_path}")
        return dropbox_path
    except ApiError as e:
        logger.error(f"❌ Ошибка при загрузке в Dropbox: {e}")
        raise
