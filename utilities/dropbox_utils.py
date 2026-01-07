"""
Утилиты для работы с Dropbox.

Функции:
    - get_dropbox_client: инициализация Dropbox клиента с проверкой доступа.
    - upload_to_dropbox: загрузка файлов в структурированные папки Dropbox.
    - ensure_user_dropbox_folder: проверка/создание личной папки пользователя.
    - get_folder_path_by_id: получение пути по Dropbox folder ID.
    - get_or_create_user_dropbox_folder: асинхронное получение/создание
      папки и сохранение ID в БД.

Особенности:
    - реализован retry с экспоненциальной задержкой для сетевых ошибок
    - отсутствие папки в Dropbox считается нормальным сценарием
    - временные ошибки сети не валят бизнес-логику с первой попытки
"""

import os
import random
import time
from datetime import datetime
from http.client import RemoteDisconnected

import dropbox
from dropbox.exceptions import ApiError, AuthError, HttpError
from dropbox.files import FileMetadata, FolderMetadata, WriteMode
from requests.exceptions import ConnectionError

from config import settings
from database.base import AsyncSessionLocal
from database.crud.user_session import read_user_session, update_dropbox_folder_id
from logging_config import logger

# ---------------------------------------------------------------------------
# Retry utilities
# ---------------------------------------------------------------------------


def dropbox_retry(retries: int = 3, base_delay: float = 0.5):
    """
    Декоратор для повторных попыток вызовов Dropbox API
    при временных сетевых ошибках.

    Args:
        retries: максимальное количество попыток.
        base_delay: базовая задержка (сек), увеличивается экспоненциально.

    Raises:
        Исключение последней попытки при исчерпании retries.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None

            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except (HttpError, ConnectionError, RemoteDisconnected) as e:
                    last_exc = e
                    if attempt == retries:
                        logger.error(
                            "Dropbox network error after %s attempts: %s",
                            retries,
                            e,
                        )
                        break

                    delay = base_delay * (2 ** (attempt - 1)) + random.random()
                    logger.warning(
                        "Dropbox temporary error (attempt %s/%s), retry in %.2fs",
                        attempt,
                        retries,
                        delay,
                    )
                    time.sleep(delay)

            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Dropbox client
# ---------------------------------------------------------------------------


def get_dropbox_client() -> dropbox.Dropbox:
    """
    Инициализирует Dropbox клиент через refresh_token
    и проверяет валидность авторизации.

    Returns:
        dropbox.Dropbox: Инициализированный клиент Dropbox.

    Raises:
        AuthError: при ошибке авторизации.
        HttpError: при сетевых ошибках.
        Exception: при иных ошибках инициализации.
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


# ---------------------------------------------------------------------------
# Internal Dropbox helpers (with retry)
# ---------------------------------------------------------------------------


@dropbox_retry()
def _get_metadata(dbx: dropbox.Dropbox, path: str):
    """Безопасно получает метаданные Dropbox-объекта."""
    return dbx.files_get_metadata(path)


@dropbox_retry()
def _create_folder(dbx: dropbox.Dropbox, path: str):
    """Безопасно создаёт папку в Dropbox."""
    return dbx.files_create_folder_v2(path)


@dropbox_retry()
def _upload_file(dbx: dropbox.Dropbox, data: bytes, path: str):
    """Безопасно загружает файл в Dropbox."""
    return dbx.files_upload(data, path, mode=WriteMode.overwrite)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def upload_to_dropbox(
    local_path: str,
    file_type: str,
    username: str | None = None,
    level: str | None = None,
    user_folder_path: str | None = None,
) -> dict:
    """
    Загружает файл в Dropbox и возвращает информацию о нём.

    Args:
        local_path: путь к локальному файлу.
        file_type: тип файла ("application", "UPDATED_APPLICATION", "test-report").
        username: имя пользователя (используется в имени файла).
        level: уровень теста (для отчётов).
        user_folder_path: путь к пользовательской папке в Dropbox.

    Returns:
        dict с ключами:
            - dropbox_path
            - dropbox_file_id
            - file_name

    Raises:
        FileNotFoundError: если файл не найден локально.
        ValueError: при некорректных аргументах.
        ApiError, HttpError: при ошибках Dropbox API.
    """
    dbx = get_dropbox_client()

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Файл не найден: {local_path}")

    if not user_folder_path:
        raise ValueError("Не указан путь к папке пользователя (user_folder_path)")

    date_str = datetime.now().strftime("%d-%m-%Y")
    safe_username = (username or "unknown").replace(" ", "_")

    if file_type in {"application", "UPDATED_APPLICATION"}:
        subfolder = "applications"
        prefix = "NEW" if file_type == "application" else "UPDATED"
        filename = f"{prefix}_APPLICATION_{safe_username}_{date_str}.pdf"
    elif file_type == "test-report":
        subfolder = "test-reports"
        filename = f"TEST_REPORT_{safe_username}_{date_str}_{level or 'Unknown'}.pdf"
    else:
        raise ValueError(f"Некорректный тип файла: {file_type}")

    subfolder_path = f"{user_folder_path.rstrip('/')}/{subfolder}"

    try:
        _get_metadata(dbx, subfolder_path)
    except ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            logger.info("Dropbox subfolder not found, creating: %s", subfolder_path)
            _create_folder(dbx, subfolder_path)
        else:
            logger.error("Dropbox folder check error: %s", e)
            raise

    dropbox_path = f"{subfolder_path}/{filename}"

    with open(local_path, "rb") as f:
        _upload_file(dbx, f.read(), dropbox_path)

    metadata = _get_metadata(dbx, dropbox_path)
    if not isinstance(metadata, FileMetadata):
        raise RuntimeError("Не удалось получить метаданные загруженного файла")

    return {
        "dropbox_path": dropbox_path,
        "dropbox_file_id": metadata.id,
        "file_name": filename,
    }


def ensure_user_dropbox_folder(
    dbx: dropbox.Dropbox, telegram_id: int
) -> tuple[str, str]:
    """
    Проверяет существование папки пользователя в Dropbox
    и создаёт её при отсутствии.

    Args:
        dbx: Инициализированный клиент Dropbox.
        telegram_id: Telegram ID пользователя.

    Returns:
        (folder_id, folder_path)
    """
    base_folder = settings.dropbox_folder_path or "/Lanex/users"
    user_folder_path = f"{base_folder.rstrip('/')}/{telegram_id}"

    try:
        metadata = _get_metadata(dbx, user_folder_path)
        if isinstance(metadata, FolderMetadata):
            return metadata.id, user_folder_path
        raise RuntimeError("Unexpected metadata type for user folder")

    except ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            logger.info("Creating Dropbox folder for user %s", telegram_id)
            res = _create_folder(dbx, user_folder_path)
            if res is None:
                raise RuntimeError(
                    "Dropbox did not return folder creation result"
                ) from None
            return res.metadata.id, user_folder_path

        logger.error("Dropbox folder creation/check error: %s", e)
        raise


def get_folder_path_by_id(dbx: dropbox.Dropbox, folder_id: str) -> str:
    """
    Получает путь к папке Dropbox по её ID.

    Args:
        dbx: Инициализированный клиент Dropbox.
        folder_id: Dropbox folder ID.

    Returns:
        Строковый путь к папке.
    """
    try:
        metadata = _get_metadata(dbx, folder_id)
        if metadata is None or not hasattr(metadata, "path_display"):
            raise RuntimeError(f"Invalid metadata for folder_id={folder_id}")

        return metadata.path_display
    except ApiError as e:
        logger.error("Dropbox get path by ID error (%s): %s", folder_id, e)
        raise


async def get_or_create_user_dropbox_folder(
    dbx: dropbox.Dropbox, telegram_id: int
) -> str:
    """
    Асинхронно получает путь к пользовательской папке Dropbox.
    При отсутствии папки создаёт её и сохраняет ID в БД.

    Args:
        dbx: Инициализированный клиент Dropbox.
        telegram_id: Telegram ID пользователя.

    Returns:
        Путь к папке пользователя в Dropbox.
    """
    async with AsyncSessionLocal() as session:
        user_session = await read_user_session(session, telegram_id)

        if user_session and user_session.dropbox_folder_id:
            try:
                return get_folder_path_by_id(dbx, user_session.dropbox_folder_id)
            except Exception as e:
                logger.warning(
                    "Stored Dropbox folder_id invalid for user %s: %s",
                    telegram_id,
                    e,
                )

        folder_id, folder_path = ensure_user_dropbox_folder(dbx, telegram_id)
        await update_dropbox_folder_id(session, telegram_id, folder_id)
        return folder_path
