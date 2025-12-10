import os
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import get_db
from database.crud.application import (
    create_application,
    read_application_by_user_id,
    read_application_by_id,
    update_application_by_id,
)
from database.crud.user_session import append_application_id
from utilities.pdf_generation import generate_application_pdf
from utilities.dropbox_utils import (
    upload_to_dropbox,
    get_dropbox_client,
    get_or_create_user_dropbox_folder
)
from utilities.telegram_notifications import send_pdf_to_admin
from utilities.phone_utils import normalize_phone
from logging_config import logger


router = APIRouter(prefix="/api")


class ApplicationSchema(BaseModel):
    """
    Схема данных заявки от пользователя.

    Attributes:
        applicant_name: Имя заявителя.
        phone_number: Телефон.
        applicant_age: Возраст.
        preferred_class_format: Список предпочтительных форматов занятий.
        preferred_study_mode: Список предпочтительных режимов обучения.
        level: Уровень английского.
        possible_scheduling: Список доступных дней/времени.
        reference_source: Источник информации о школе.
        need_ielts: Требуется ли IELTS.
        studied_at_lanex: Учился ли ранее в Lanex.
        previous_experience: Предыдущий опыт.
        telegram_id: Telegram ID пользователя.
    """
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
    telegram_id: int

    class Config:
        use_enum_values = True


@router.post("/applications")
async def create_application_endpoint(
    payload: ApplicationSchema,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """
    Создаёт новую заявку: PDF на сервере, загрузка в Dropbox, уведомление админа и сохранение в БД.

    Args:
        payload: Данные заявки.
        session: Асинхронная сессия БД.

    Returns:
        dict: Статус создания, ID заявки и путь в Dropbox.
    """
    normalized_phone = normalize_phone(payload.phone_number)

    try:
        # === 1. Генерация PDF на сервере ===
        pdf_path = generate_application_pdf(
            applicant_name=payload.applicant_name,
            phone_number=normalized_phone,
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
            output_dir="generated_applications",
            is_update=False,
        )

        # === 2. Получение/создание папки пользователя в Dropbox ===
        dbx = get_dropbox_client()
        user_folder_path = await get_or_create_user_dropbox_folder(dbx, payload.telegram_id)

        # === 3. Загрузка PDF в Dropbox ===
        upload_result = upload_to_dropbox(
            local_path=pdf_path,
            username=payload.applicant_name,
            file_type="application",
            user_folder_path=user_folder_path
        )

        # === 4. Уведомление админа ===
        caption = (
            f"📩 Новая заявка от {payload.applicant_name}\n"
            f"📞 {payload.phone_number}\n"
            f"🧩 Уровень: {payload.level or 'Не указан'}\n"
            f"👤 Telegram ID: {payload.telegram_id}"
        )
        await send_pdf_to_admin(file_path=pdf_path, caption=caption)

        # === 5. Удаление PDF с сервера ===
        try:
            os.remove(pdf_path)
        except Exception as e:
            logger.warning(f"Не удалось удалить временный PDF: {e}")

        # === 6. Сохранение заявки в БД ===
        new_app = await create_application(
            session=session,
            user_id=payload.telegram_id,
            applicant_name=payload.applicant_name,
            phone_number=normalized_phone,
            applicant_age=payload.applicant_age,
            preferred_class_format=payload.preferred_class_format,
            preferred_study_mode=payload.preferred_study_mode,
            level=payload.level,
            possible_scheduling=payload.possible_scheduling,
            reference_source=payload.reference_source,
            need_ielts=payload.need_ielts,
            studied_at_lanex=payload.studied_at_lanex,
            previous_experience=payload.previous_experience,
            dropbox_file_id=upload_result["dropbox_file_id"],
            file_name=upload_result["file_name"],
        )

        await append_application_id(session, payload.telegram_id, new_app.id)

        return {
            "status": "success",
            "application_id": new_app.id,
            "dropbox_path": upload_result["dropbox_path"],
        }

    except Exception as e:
        logger.exception(f"❌ Ошибка при создании заявки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/user/{telegram_id}")
async def get_applications_by_user(
    telegram_id: int = Path(..., description="Telegram ID пользователя"),
    session: AsyncSession = Depends(get_db)
) -> list[dict]:
    """
    Возвращает все заявки пользователя.

    Args:
        telegram_id: Telegram ID пользователя.
        session: Асинхронная сессия БД.

    Returns:
        list[dict]: Список заявок с ID, именем и датой создания.
    """
    apps = await read_application_by_user_id(session, telegram_id)
    return [
        {
            "id": app.id,
            "name": app.applicant_name,
            "date": app.created_at.strftime("%Y-%m-%d") if hasattr(app, "created_at") else "—",
        }
        for app in apps
    ]


@router.get("/applications/{id}")
async def get_application_by_id(
    id: int,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """
    Возвращает заявку по её ID.

    Args:
        id: ID заявки.
        session: Асинхронная сессия БД.

    Returns:
        dict: Данные заявки.

    Raises:
        HTTPException: Если заявка не найдена.
    """
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


@router.put("/applications/{id}")
async def update_application_endpoint(
    id: int,
    payload: ApplicationSchema,
    session: AsyncSession = Depends(get_db)
) -> dict:
    """
    Обновляет существующую заявку: генерация PDF, Dropbox, уведомление админа и БД.

    Args:
        id: ID заявки.
        payload: Данные для обновления.
        session: Асинхронная сессия БД.

    Returns:
        dict: Сообщение об успехе и путь в Dropbox.

    Raises:
        HTTPException: Если заявка не найдена.
    """

    normalized_phone = normalize_phone(payload.phone_number)

    try:
        existing_app = await read_application_by_id(session, id)
        if not existing_app:
            raise HTTPException(status_code=404, detail="Application not found")

        # === 1. Генерация PDF ===
        pdf_path = generate_application_pdf(
            applicant_name=payload.applicant_name,
            phone_number=normalized_phone,
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
            output_dir="generated_applications",
            is_update=True,
        )

        # === 2. Dropbox ===
        dbx = get_dropbox_client()
        user_folder_path = await get_or_create_user_dropbox_folder(dbx, payload.telegram_id)

        upload_result = upload_to_dropbox(
            local_path=pdf_path,
            username=payload.applicant_name,
            file_type="UPDATED_APPLICATION",
            user_folder_path=user_folder_path,
        )

        # === 3. Уведомление админа ===
        await send_pdf_to_admin(
            file_path=pdf_path,
            caption=f"🔄 Обновлена заявка от {payload.applicant_name}",
        )

        # === 4. Удаление PDF с сервера ===
        try:
            os.remove(pdf_path)
        except Exception as e:
            logger.warning(f"Не удалось удалить временный PDF: {e}")

        # === 5. Обновление заявки в БД ===
        await update_application_by_id(
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
            dropbox_file_id=upload_result["dropbox_file_id"],
            file_name=upload_result["file_name"],
        )

        return {"message": "Application updated successfully", "dropbox_path": upload_result["dropbox_path"]}

    except Exception as e:
        logger.exception(f"❌ Ошибка при обновлении заявки: {e}")
        raise HTTPException(status_code=500, detail=str(e))
