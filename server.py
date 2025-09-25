# from pathlib import Path
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
#
# from api import check_api, application_api
#
# BASE_DIR = Path(__file__).resolve().parent
# app = FastAPI()
#
# # Статические страницы
# app.mount(
#     "/html_pages",
#     StaticFiles(directory=BASE_DIR / "html_pages"),
#     name="html_pages",
# )
#
# # Подключаем роуты
# app.include_router(check_api.router)
# app.include_router(application_api.router)  # 👈 добавили
#
# # CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

import os
import logging
from fastapi import FastAPI

# Логи в консоль для диагностики
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("🔥 Запуск минимального FastAPI сервера...")

app = FastAPI()

# Тестовый эндпоинт для проверки
@app.get("/ping")
async def ping():
    logger.info("Ping endpoint вызван!")
    return {"status": "ok", "message": "FastAPI сервер работает!"}

# Информация о хосте и порте при старте
port = int(os.environ.get("PORT", 8000))
host = "0.0.0.0"
logger.info(f"Сервер будет слушать на {host}:{port}")
