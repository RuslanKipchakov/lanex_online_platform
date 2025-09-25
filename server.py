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

from fastapi import FastAPI
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("🔥 FastAPI сервер стартует...")

@app.get("/ping")
async def ping():
    logger.info("⚡ Ping получен!")
    return {"status": "ok", "message": "FastAPI сервер работает!"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Сервер будет слушать на 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
