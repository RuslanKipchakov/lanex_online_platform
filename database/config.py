import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DB
    db_username: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str

    # Admin & Dropbox
    telegram_bot_token: str
    super_admin_id: int
    admin_telegram_id: int
    admin_name: str
    dropbox_access_token: str
    dropbox_folder_path: str

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def sync_db_url(self) -> str:
        return (
            f"postgresql://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = SettingsConfigDict(
        env_file=os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", ".env")
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix=""
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
