"""Конфигурация приложения Lanex Online Platform.

Загружает переменные окружения из файла .env и предоставляет централизованные
настройки для всех компонентов:
    - База данных (PostgreSQL)
    - Telegram-бот
    - Dropbox-интеграция
    - Параметры CORS
"""

from functools import lru_cache
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения или файла .env."""

    # Database
    db_username: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str

    # Telegram
    telegram_bot_token: str
    admin_telegram_id: int
    admin_name: str

    # Dropbox
    dropbox_folder_path: str
    dropbox_refresh_token: str
    dropbox_app_key: str
    dropbox_app_secret: str

    # CORS and Base URL
    cors_origins: Union[List[str], str]
    base_url: str

    @property
    def db_url(self) -> str:
        """URL для asyncpg."""
        return (
            f"postgresql+asyncpg://{self.db_username}:"
            f"{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def sync_db_url(self) -> str:
        """URL для sync SQLAlchemy."""
        return (
            f"postgresql://{self.db_username}:"
            f"{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )


@lru_cache()
def get_settings() -> Settings:
    """Возвращает кэшированный экземпляр Settings."""
    return Settings()


settings = get_settings()

# ---- НОРМАЛИЗАЦИЯ CORS ----
if isinstance(settings.cors_origins, str):
    settings.cors_origins = [
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ]
