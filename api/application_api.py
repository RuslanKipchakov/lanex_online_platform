import os
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime

from database.base import get_db
from database.crud.application import create_application, read_application_by_user_id, read_application_by_id, update_application_by_id
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


@router.post("/applications")
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
            file_type="application",
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


# === 1. Получить все заявки пользователя ===
@router.get("/applications/user/{telegram_id}")
async def get_applications_by_user(
    telegram_id: int = Path(..., description="Telegram ID пользователя"),
    session: AsyncSession = Depends(get_db)
):
    apps = await read_application_by_user_id(session, telegram_id)
    result = [
        {
            "id": app.id,
            "name": app.applicant_name,
            "date": app.created_at.strftime("%Y-%m-%d") if hasattr(app, "created_at") else "—",
        }
        for app in apps
    ]
    return result


# === 2. Получить данные конкретной заявки ===
@router.get("/applications/{id}")
async def get_application_by_id(id: int, session: AsyncSession = Depends(get_db)):
    app = await read_application_by_id(session, id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return {
        "id": app.id,
        "applicant_name": app.applicant_name,
        "phone_number": app.phone_number,
        "applicant_age": app.applicant_age,
        "preferred_class_format": app.preferred_class_format,
        "preferred_study_mode": app.preferred_study_mode,
        "level": app.level.value if app.level else None,
        "possible_scheduling": app.possible_scheduling,
        "reference_source": app.reference_source.value if app.reference_source else None,
        "need_ielts": app.need_ielts,
        "studied_at_lanex": app.studied_at_lanex,
        "previous_experience": [v.value for v in app.previous_experience] if app.previous_experience else None,
        "telegram_id": app.user_id,
    }


# === 3. Обновить заявку ===
@router.put("/applications/{id}")
async def update_application_endpoint(
    id: int,
    payload: ApplicationSchema,
    session: AsyncSession = Depends(get_db)
):
    """
    Обновляет заявку:
    - проверяет, есть ли изменения;
    - генерирует новый PDF с пометкой UPDATED_APPLICATION;
    - загружает файл в Dropbox;
    - обновляет запись в базе;
    - отправляет PDF админу.
    """
    try:
        # 1️⃣ Проверим, существует ли заявка
        existing_app = await read_application_by_id(session, id)
        if not existing_app:
            raise HTTPException(status_code=404, detail="Application not found")

        # 2️⃣ Генерация PDF
        local_dir = "generated_applications"
        timestamp = datetime.now().strftime("%d-%m-%Y_%H%M%S")
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
            username=payload.applicant_name,
            output_dir=local_dir,
        )

        # Корректно формируем новое имя — явно задаём префикс UPDATED_APPLICATION
        dir_name = os.path.dirname(pdf_path) or local_dir
        new_name = os.path.join(dir_name, f"UPDATED_APPLICATION_{timestamp}.pdf")
        os.replace(pdf_path, new_name)  # os.replace безопаснее: перезапишет при необходимости
        pdf_path = new_name

        # 3️⃣ Загрузка PDF в Dropbox
        dropbox_path = upload_to_dropbox(
            local_path=pdf_path,
            telegram_id=payload.telegram_id,
            username=payload.applicant_name,
            file_type="UPDATED_APPLICATION",
        )

        # 4️⃣ Обновляем запись в БД
        updated_app = await update_application_by_id(
            session=session,
            id=id,
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

        # 5️⃣ Отправляем админу обновлённый PDF
        await send_pdf_to_admin(
            file_path=pdf_path,
            caption=f"🔄 Обновлена заявка от {payload.applicant_name}"
        )

        return {"message": "Application updated successfully", "dropbox_path": dropbox_path}

    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении заявки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


