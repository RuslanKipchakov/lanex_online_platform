from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from lanex_online_platform.database.async_db_connection import get_db
from lanex_online_platform.database.models import (
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
    session: AsyncSession = Depends(get_db)
):
    # Пока — печатаем и возвращаем (позже заменим на вызов CRUD-функции)
    print("📩 Получена заявка:", data.dict())
    return {"status": "ok", "received": data.dict()}
