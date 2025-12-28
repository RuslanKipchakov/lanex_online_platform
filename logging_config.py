"""Конфигурация логирования проекта.

Логгер:
    logger (logging.Logger): Основной логгер проекта.

Особенности:
    - Уровень логирования: WARNING и выше.
    - Логи пишутся только в файл.
    - Ротация: 5 МБ, 3 резервных файла.
    - Формат: [YYYY-MM-DD HH:MM:SS] LEVEL in NAME: message
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Настройка директории и файла логов
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "error.log")

# Формат логов
LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Создание обработчика с ротацией
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

# Основной логгер
logger = logging.getLogger("lanex_backend")
logger.setLevel(logging.WARNING)
logger.handlers.clear()
logger.addHandler(file_handler)
logger.propagate = False
