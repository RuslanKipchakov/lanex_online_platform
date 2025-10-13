import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Определяем базовую директорию
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "error.log")

# Формат логов
LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"

# Основной логгер
logger = logging.getLogger("lanex_backend")
logger.setLevel(logging.INFO)  # INFO — чтобы не пропускать важные записи

# --- Файловый логгер (для локальной отладки) ---
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5_000_000,
    backupCount=3,
    encoding="utf-8"
)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# --- Консольный логгер (для Railway) ---
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# --- Определяем среду ---
# Railway автоматически задаёт переменную RAILWAY_ENVIRONMENT
is_railway = "RAILWAY_ENVIRONMENT" in os.environ

# --- Добавляем обработчики ---
logger.handlers.clear()
if is_railway:
    # На Railway выводим в консоль (stdout)
    logger.addHandler(console_handler)
else:
    # Локально — в файл
    logger.addHandler(file_handler)

logger.propagate = False
