from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from database.base import get_db
from database.crud.application import create_application
from database.crud.user_session import append_application_id
from utilities.pdf_generation import generate_application_pdf
from utilities.dropbox_utils import upload_to_dropbox
from utilities.telegram_notifications import send_pdf_to_admin  # 👈 добавили импорт
from logging_config import logger

router = APIRouter(prefix="/api")


class ApplicationSchema(BaseModel):
    applicant_name: str
    phone_number: str
    applicant_age: int
    preferred_class_format: List[str]
    preferred_study_mode: List[str]
    level: Optional[str]
    possible_scheduling: List[Dict[str, Any]]
    reference_source: Optional[str] = None
    need_ielts: Optional[bool] = False
    studied_at_lanex: bool = False
    previous_experience: Optional[List[str]] = None
    telegram_id: int  # 👈 основной идентификатор

    class Config:
        use_enum_values = True


@router.post("/application")
async def create_application_endpoint(payload: ApplicationSchema, session: AsyncSession = Depends(get_db)):
    """
    Создаёт заявку:
    1) принимает данные из формы;
    2) генерирует PDF-файл;
    3) загружает PDF в Dropbox;
    4) сохраняет запись в базе данных;
    5) отправляет PDF админу в Telegram.
    """

    try:
        # === 1. Генерация PDF-заявки ===
        local_dir = "generated_applications"
        pdf_path = generate_application_pdf(
            applicant_name=payload.applicant_name,
            phone_number=payload.phone_number,
            applicant_age=payload.applicant_age,
            preferred_class_format=payload.preferred_class_format,
            preferred_study_mode=payload.preferred_study_mode,
            level=payload.level,
            possible_scheduling=payload.possible_scheduling,
            reference_source=payload.reference_source,
            need_ielts=payload.need_ielts,
            studied_at_lanex=payload.studied_at_lanex,
            previous_experience=payload.previous_experience,
            telegram_id=payload.telegram_id,
            username=payload.applicant_name,  # пока используем имя как username
            output_dir=local_dir,
        )

        logger.info(f"📄 PDF заявка успешно создана: {pdf_path}")

        # === 2. Загрузка PDF в Dropbox ===
        dropbox_path = upload_to_dropbox(
            local_path=pdf_path,
            telegram_id=payload.telegram_id,
            username=payload.applicant_name,
        )
        logger.info(f"☁️ Файл успешно загружен в Dropbox: {dropbox_path}")

        # === 3. Сохранение записи в БД ===
        new_app = await create_application(
            session=session,
            user_id=payload.telegram_id,
            applicant_name=payload.applicant_name,
            phone_number=payload.phone_number,
            applicant_age=payload.applicant_age,
            preferred_class_format=payload.preferred_class_format,
            preferred_study_mode=payload.preferred_study_mode,
            level=payload.level,
            possible_scheduling=payload.possible_scheduling,
            reference_source=payload.reference_source,
            need_ielts=payload.need_ielts,
            studied_at_lanex=payload.studied_at_lanex,
            previous_experience=payload.previous_experience,
            pdf_path=dropbox_path,
        )
        logger.info(f"✅ Заявка успешно сохранена в БД: ID={new_app.id}")

        # === 4. Добавляем id заявки в объект UserSession ===
        await append_application_id(session, payload.telegram_id, new_app.id)

        # === 5. Отправляем PDF админу в Telegram ===
        caption = (
            f"📩 Новая заявка от {payload.applicant_name}\n"
            f"📞 {payload.phone_number}\n"
            f"🧩 Уровень: {payload.level or 'Не указан'}\n"
            f"👤 Telegram ID: {payload.telegram_id}"
        )
        await send_pdf_to_admin(file_path=pdf_path, caption=caption)
        logger.info("📨 PDF отправлен админу в Telegram")

        # === 6. Успешный ответ ===
        return {
            "status": "success",
            "application_id": new_app.id,
            "dropbox_path": dropbox_path,
        }

    except Exception as e:
        logger.error(f"❌ Ошибка при создании заявки: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке заявки: {e}")

# @router.post("/applications/update", status_code=200)
# async def update_application_endpoint(
#     data: ApplicationSchema,
#     telegram_id: int,
#     session: AsyncSession = Depends(get_db)
# ):
#     from utilities.creating_paths import create_application_path
#
#     # создаём новый путь
#     pdf_path = create_application_path(data.name, telegram_id).replace(".pdf", f"_updated.pdf")
#
#     # сохраняем обновлённую заявку в БД
#     updated_app = await update_application_by_user_id(session, telegram_id, data, pdf_path)
#
#     # (TODO) генерим PDF, грузим в Dropbox, отправляем админу в Telegram
#
#     return {"status": "ok", "application_id": updated_app.id}

