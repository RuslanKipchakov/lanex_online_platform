"""
Утилиты для работы с Dropbox.

Функции:
    - get_dropbox_client: инициализация Dropbox клиента с проверкой доступа.
    - upload_to_dropbox: загрузка файлов в структурированные папки Dropbox.
    - ensure_user_dropbox_folder: проверка/создание личной папки пользователя.
    - get_folder_path_by_id: получение пути по Dropbox folder ID.
    - get_or_create_user_dropbox_folder: асинхронное получение/создание
      папки и сохранение ID в БД.
"""

import os
from datetime import datetime

import dropbox
from dropbox.exceptions import ApiError, AuthError, HttpError
from dropbox.files import FileMetadata, FolderMetadata, WriteMode

from config import settings
from database.base import AsyncSessionLocal
from database.crud.user_session import read_user_session, update_dropbox_folder_id
from logging_config import logger


def get_dropbox_client() -> dropbox.Dropbox:
    """Инициализирует Dropbox клиент через refresh_token.

    Returns:
        dropbox.Dropbox: Клиент Dropbox.

    Raises:
        AuthError, HttpError, Exception
    """
    try:
        dbx = dropbox.Dropbox(
            oauth2_refresh_token=settings.dropbox_refresh_token,
            app_key=settings.dropbox_app_key,
            app_secret=settings.dropbox_app_secret,
        )
        dbx.users_get_current_account()
        return dbx
    except AuthError as e:
        logger.error("Dropbox auth error: %s", e)
        raise
    except HttpError as e:
        logger.error("Dropbox network error: %s", e)
        raise
    except Exception as e:
        logger.error("Unknown Dropbox init error: %s", e)
        raise


def upload_to_dropbox(
    local_path: str,
    file_type: str,
    username: str | None = None,
    level: str | None = None,
    user_folder_path: str | None = None,
) -> dict:
    """
    Загружает файл в Dropbox и возвращает словарь с dropbox_path,
    dropbox_file_id и file_name.

    Args:
        local_path: Путь к локальному файлу.
        file_type: Тип файла ("application", "UPDATED_APPLICATION", "test-report").
        username: Имя пользователя, используется для формирования имени файла.
        level: Уровень теста, для отчётов о тестах.
        user_folder_path: Путь к папке пользователя в Dropbox.

    Returns:
        dict: Словарь с ключами:
            - dropbox_path: путь к файлу в Dropbox,
            - dropbox_file_id: уникальный ID файла в Dropbox,
            - file_name: имя файла.

    Raises:
        FileNotFoundError: если файл не найден локально.
        ValueError: если не указан путь к папке пользователя или некорректный file_type.
        ApiError, HttpError: при ошибках работы с Dropbox API.
    """

    dbx = get_dropbox_client()

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Файл не найден: {local_path}")

    if not user_folder_path:
        raise ValueError("Не указан путь к папке пользователя (user_folder_path)")

    date_str = datetime.now().strftime("%d-%m-%Y")
    safe_username = (username or "unknown").replace(" ", "_")

    if file_type == "application":
        subfolder = "applications"
        filename = f"NEW_APPLICATION_{safe_username}_{date_str}.pdf"
    elif file_type == "UPDATED_APPLICATION":
        subfolder = "applications"
        filename = f"UPDATED_APPLICATION_{safe_username}_{date_str}.pdf"
    elif file_type == "test-report":
        subfolder = "test-reports"
        filename = f"TEST_REPORT_{safe_username}_{date_str}_{level or 'Unknown'}.pdf"
    else:
        raise ValueError(f"Некорректный тип файла: {file_type}")

    subfolder_path = f"{user_folder_path.rstrip('/')}/{subfolder}"

    try:
        dbx.files_get_metadata(subfolder_path)
    except ApiError as e:
        if (
            hasattr(e, "error")
            and e.error.is_path()
            and e.error.get_path().is_not_found()
        ):
            dbx.files_create_folder_v2(subfolder_path)
        else:
            logger.error("Dropbox folder check error: %s", e)
            raise

    dropbox_path = f"{subfolder_path}/{filename}"

    try:
        with open(local_path, "rb") as f:
            dbx.files_upload(
                f.read(),
                dropbox_path,
                mode=WriteMode.overwrite,
            )  # type: ignore

        metadata = dbx.files_get_metadata(dropbox_path)
        if isinstance(metadata, FileMetadata):
            dropbox_file_id = metadata.id
        else:
            raise ValueError(
                f"Не удалось получить dropbox_file_id, "
                f"метаданные не являются файлом: {metadata}"
            )
        return {
            "dropbox_path": dropbox_path,
            "dropbox_file_id": dropbox_file_id,
            "file_name": filename,
        }

    except (ApiError, HttpError) as e:
        logger.error("Dropbox upload error: %s", e)
        raise


def ensure_user_dropbox_folder(
    dbx: dropbox.Dropbox, telegram_id: int
) -> tuple[str, str]:
    """Создаёт папку пользователя, если не существует.

    Returns:
        folder_id, folder_path
    """
    base_folder = settings.dropbox_folder_path or "/Lanex/users"
    user_folder_path = f"{base_folder.rstrip('/')}/{telegram_id}"

    try:
        metadata = dbx.files_get_metadata(user_folder_path)
        if isinstance(metadata, FolderMetadata):
            return metadata.id, user_folder_path
        raise RuntimeError("Unexpected metadata type for user folder")

    except ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            res = dbx.files_create_folder_v2(user_folder_path)
            if res is None:
                raise RuntimeError("Dropbox did not return folder metadata") from e
            return res.metadata.id, user_folder_path
        logger.error("Dropbox folder creation/check error: %s", e)
        raise


def get_folder_path_by_id(dbx: dropbox.Dropbox, folder_id: str) -> str:
    """Возвращает путь к папке по ID."""
    try:
        metadata = dbx.files_get_metadata(folder_id)

        if metadata is None or not hasattr(metadata, "path_display"):
            raise RuntimeError(f"Invalid metadata for folder_id={folder_id}")

        return metadata.path_display
    except ApiError as e:
        logger.error("Dropbox get path by ID error (%s): %s", folder_id, e)
        raise


async def get_or_create_user_dropbox_folder(
    dbx: dropbox.Dropbox, telegram_id: int
) -> str:
    """Асинхронно получает или создаёт папку пользователя и сохраняет ID в БД."""
    async with AsyncSessionLocal() as session:
        user_session = await read_user_session(session, telegram_id)

        if user_session and user_session.dropbox_folder_id:
            folder_id: str = user_session.dropbox_folder_id  # type: ignore
            try:
                return get_folder_path_by_id(dbx, folder_id)
            except Exception:
                pass

        folder_id, folder_path = ensure_user_dropbox_folder(dbx, telegram_id)
        await update_dropbox_folder_id(session, telegram_id, folder_id)
        return folder_path
