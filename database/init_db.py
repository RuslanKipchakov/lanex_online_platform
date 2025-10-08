from sqlalchemy import create_engine, text

from .config import settings


def create_database_if_not_exists() -> None:
    """Создаёт базу данных Postgres, если она не существует"""
    default_url = (
        f"postgresql://{settings.db_username}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/postgres"
    )
    initial_engine = create_engine(default_url, isolation_level="AUTOCOMMIT")
    with initial_engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{settings.db_name}'")
        )
        exists = result.scalar()
        if not exists:
            conn.execute(text(f"CREATE DATABASE {settings.db_name}"))
            print(f"База данных '{settings.db_name}' создана.")
        else:
            print(f"База данных '{settings.db_name}' уже существует.")


if __name__ == "__main__":
    create_database_if_not_exists()
