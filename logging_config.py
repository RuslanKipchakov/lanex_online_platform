import logging
import os
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "error.log")

handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
handler.setLevel(logging.WARNING)

formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger("microblog_backend")
logger.setLevel(logging.WARNING)
logger.addHandler(handler)
logger.propagate = False