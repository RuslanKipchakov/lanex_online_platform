"""
Создание базы данных PostgreSQL, если она не существует.

Этот модуль:
    - подключается к системной БД `postgres`;
    - проверяет, создана ли целевая БД;
    - создаёт её при необходимости.

Используется вручную при развертывании проекта.
"""

from sqlalchemy import create_engine, text
from config import settings


def create_database_if_not_exists() -> None:
    """
    Создаёт базу данных Postgres, если она отсутствует.

    Примечание:
        SQLAlchemy ORM не может создавать сами базы данных,
        поэтому здесь используется обычный синхронный драйвер psycopg2
        через create_engine().
    """
    default_url = (
        f"postgresql://{settings.db_username}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/postgres"
    )

    engine = create_engine(default_url, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": settings.db_name},
        )
        exists = result.scalar()

        if not exists:
            conn.execute(text(f"CREATE DATABASE {settings.db_name}"))
            print(f"База данных '{settings.db_name}' создана.")
        else:
            print(f"База данных '{settings.db_name}' уже существует.")


if __name__ == "__main__":
    create_database_if_not_exists()
