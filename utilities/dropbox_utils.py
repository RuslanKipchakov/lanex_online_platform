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
    dropbox_folder: str | None = None,
    telegram_id: int | None = None,
    username: str | None = None
) -> str:
    """
    Загружает файл в Dropbox и возвращает путь в облаке.
    Имя файла формируется как:
    'Ruslan_16-10-2025_112454227.pdf'
    """
    dbx = get_dropbox_client()

    if not os.path.exists(local_path):
        logger.error(f"❌ Файл не найден: {local_path}")
        raise FileNotFoundError(f"Файл не найден: {local_path}")

    # Формируем читаемое имя файла
    date_str = datetime.now().strftime("%d-%m-%Y_%H-%M")
    username_part = (username or "UnknownUser").replace(" ", "_")
    id_part = str(telegram_id) if telegram_id else "no_id"
    file_name = f"{username_part}_{date_str}_{id_part}.pdf"

    # Определяем папку для загрузки
    dropbox_folder = dropbox_folder or settings.dropbox_folder_path or "/Lanex"
    dropbox_path = f"{dropbox_folder.rstrip('/')}/users/{file_name}"

    try:
        with open(local_path, "rb") as f:
            dbx.files_upload(
                f.read(),
                dropbox_path,
                mode=dropbox.files.WriteMode("overwrite")
            )
        logger.info(f"✅ Файл успешно загружен в Dropbox: {dropbox_path}")
        return dropbox_path
    except ApiError as e:
        logger.error(f"❌ Ошибка при загрузке в Dropbox: {e}")
        raise
