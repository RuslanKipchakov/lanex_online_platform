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

# server.py
import os
import logging
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.get("/ping")
async def ping():
    logging.info("🔥 /ping endpoint called")
    return {"status": "ok", "message": "Server is running!"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Railway задаёт этот порт автоматически
    logging.info(f"🚀 Starting FastAPI server on 0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
