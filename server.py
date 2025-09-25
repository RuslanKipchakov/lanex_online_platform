from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from lanex_online_platform.api import check_api, application_api

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI()

# Статические страницы
app.mount(
    "/html_pages",
    StaticFiles(directory=BASE_DIR / "html_pages"),
    name="html_pages",
)

# Подключаем роуты
app.include_router(check_api.router)
app.include_router(application_api.router)  # 👈 добавили

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для отладки можно оставить *, потом лучше ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
