# Базовый образ
FROM python:3.10-slim

# Переменные окружения Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Рабочая директория внутри контейнера
WORKDIR /app

# Установка системных зависимостей
# (gcc и libpq нужны для psycopg / asyncpg)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

# Копируем только зависимости (для кеша)
COPY pyproject.toml poetry.lock ./

# Отключаем virtualenv внутри контейнера
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Копируем весь проект
COPY . .

# Открываем порт FastAPI
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
