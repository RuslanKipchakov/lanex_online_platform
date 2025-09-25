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

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI()

# 🚀 Тестовый корневой роут
@app.get("/")
async def root():
    return {"status": "ok", "message": "FastAPI is running on Railway!"}

# Статические страницы
app.mount(
    "/html_pages",
    StaticFiles(directory=BASE_DIR / "html_pages"),
    name="html_pages",
)

# --- Мини API для теста ---
router = APIRouter(prefix="/api")

class DummySubmission(BaseModel):
    level: str
    answers: Dict[str, Dict[str, Any]]

@router.post("/check_test")
async def check_test(submission: DummySubmission):
    # просто возвращаем данные, чтобы проверить эндпоинт
    return {"status": "ok", "received": submission.dict()}

class DummyApplication(BaseModel):
    applicant_name: str
    phone_number: str
    applicant_age: int

@router.post("/applications")
async def create_application(app_data: DummyApplication):
    return {"status": "ok", "received": app_data.dict()}

app.include_router(router)

# CORS (для фронта)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
