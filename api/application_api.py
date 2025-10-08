from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import get_db
from database.models import (
    PreferredClassFormatEnum,
    PreferredStudyModeEnum,
    LevelEnum,
    ReferenceSourceEnum,
    PreviousExperienceEnum,
)

router = APIRouter(prefix="/api")

class ApplicationSchema(BaseModel):
    applicant_name: str
    phone_number: str
    applicant_age: int
    preferred_class_format: List[PreferredClassFormatEnum]
    preferred_study_mode: List[PreferredStudyModeEnum]
    level: Optional[LevelEnum]
    possible_scheduling: List[Dict[str, Any]]   # [{"day": "Tuesday", "times":["08:00"]}, ...]
    reference_source: Optional[ReferenceSourceEnum] = None
    need_ielts: Optional[bool] = False
    studied_at_lanex: bool = False
    previous_experience: Optional[List[PreviousExperienceEnum]] = None

    class Config:
        use_enum_values = True  # позволяет принимать строковые значения enum'ов из фронта

@router.post("/applications", status_code=201)
async def create_application_endpoint(
    data: ApplicationSchema,
    telegram_id: int,
    session: AsyncSession = Depends(get_db)
):
    # 1. создаём путь для хранения PDF
    from utilities.creating_paths import create_application_path
    pdf_path = create_application_path(data.name, telegram_id)

    # 2. сохраняем заявку в БД
    new_app = await create_application(session, data, telegram_id, pdf_path)

    # 3. (TODO) генерим PDF, грузим в Dropbox, отправляем админу в Telegram

    return {"status": "ok", "application_id": new_app.id}


@router.post("/applications/update", status_code=200)
async def update_application_endpoint(
    data: ApplicationSchema,
    telegram_id: int,
    session: AsyncSession = Depends(get_db)
):
    from utilities.creating_paths import create_application_path

    # создаём новый путь
    pdf_path = create_application_path(data.name, telegram_id).replace(".pdf", f"_updated.pdf")

    # сохраняем обновлённую заявку в БД
    updated_app = await update_application_by_user_id(session, telegram_id, data, pdf_path)

    # (TODO) генерим PDF, грузим в Dropbox, отправляем админу в Telegram

    return {"status": "ok", "application_id": updated_app.id}

