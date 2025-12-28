import os
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import get_db
from database.crud.test_result import create_test_result
from database.crud.user_session import read_user_session
from logging_config import logger
from utilities.check_function import FrontendTestPayload, check_test_results
from utilities.dropbox_utils import (
    get_dropbox_client,
    get_or_create_user_dropbox_folder,
    upload_to_dropbox,
)
from utilities.pdf_generation import generate_test_report

router = APIRouter(prefix="/api")


class TestSubmissionSchema(BaseModel):
    """
    Схема данных для отправки результатов теста пользователем.

    Attributes:
        level: Уровень теста.
        username: Имя пользователя (необязательно).
        telegram_id: Telegram ID пользователя.
        answers: Словарь с ответами по задачам и вопросам.
    """

    level: str
    username: Optional[str] = None
    telegram_id: int
    answers: Dict[str, Dict[str, str]]


@router.post("/check_test")
async def check_test_endpoint(
    payload: TestSubmissionSchema, session: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """
    Проверяет ответы пользователя на тест, формирует PDF отчёт, загружает его в Dropbox
    и сохраняет результат в базе данных.

    Args:
        payload: Валидированные данные отправки теста.
        session: Асинхронная сессия БД.

    Returns:
        dict:
            status (str): Статус обработки.
            username_used (str): Имя, использованное в отчёте.
            dropbox_path (str): Путь к файлу в Dropbox.
            result (dict): Детальные результаты проверки.

    Raises:
        HTTPException: При ошибках обработки или сохранения данных.
    """
    telegram_id = payload.telegram_id
    level = payload.level
    username = (payload.username or "").strip()
    answers = payload.answers or {}

    try:
        # === 1. Проверка, что есть ответы ===
        if not any(v.strip() for task in answers.values() for v in task.values()):
            logger.warning(f"Пустая форма от пользователя {telegram_id}")
            return {"status": "empty_form"}

        # === 2. Безопасное имя пользователя ===
        safe_name = re.sub(r"[^a-zA-Zа-яА-Я0-9_\-\s]", "", username).strip()
        if not safe_name:
            user_session = await read_user_session(session, telegram_id)
            safe_name = (
                user_session.telegram_username
                if user_session and user_session.telegram_username
                else f"user_{telegram_id}"
            )

        # === 3. Проверка теста и вычисление результатов ===
        check_result = await check_test_results(
            FrontendTestPayload(
                level=level,
                username=safe_name,
                answers=answers,
            )
        )

        # === 4. Формирование структуры закрытых/открытых ответов и баллов ===
        closed_answers, open_answers, score = {}, {}, {}
        for task, content in answers.items():
            task_key = task if task.startswith("task") else f"task_{task}"
            task_result = check_result.get(task, {})

            if task_result == "open":
                open_answers[task_key] = content
                continue

            closed_answers[task_key] = {
                f"Q{q_num}": {
                    "answer": user_answer,
                    "status": task_result.get(q_num, "unchecked"),
                }
                for q_num, user_answer in content.items()
            }

            if isinstance(task_result, dict):
                score_str = task_result.get("score")
                if score_str:
                    try:
                        score[task_key] = int(score_str.split("/")[0])
                    except Exception:
                        logger.warning(
                            f"Невозможно преобразовать балл в int для {task_key}"
                        )

        if "total" in check_result:
            try:
                score["total"] = float(check_result["total"].strip("%"))
            except Exception:
                logger.warning("Невозможно преобразовать общий балл в float")

        # === 5. Генерация PDF отчёта ===
        pdf_path = generate_test_report(
            test_taker=safe_name,
            level=level,
            closed_answers=closed_answers,
            open_answers=open_answers or None,
            score=score,
            output_dir="test-reports",
        )

        # === 6. Работа с Dropbox ===
        dbx = get_dropbox_client()
        user_folder_path = await get_or_create_user_dropbox_folder(dbx, telegram_id)

        upload_result = upload_to_dropbox(
            local_path=pdf_path,
            username=safe_name,
            file_type="test-report",
            level=level,
            user_folder_path=user_folder_path,
        )

        # === 7. Удаление временного PDF с сервера ===
        try:
            os.remove(pdf_path)
        except Exception as e:
            logger.warning(f"Не удалось удалить временный PDF: {e}")

        # === 8. Сохранение результата в БД ===
        await create_test_result(
            session=session,
            user_id=telegram_id,
            test_taker=safe_name,
            level=level,
            closed_answers=closed_answers,
            open_answers=open_answers or None,
            score=score,
            dropbox_file_id=upload_result["dropbox_file_id"],
            file_name=upload_result["file_name"],
        )

        # === 9. Ответ клиенту ===
        return {
            "status": "ok",
            "username_used": safe_name,
            "dropbox_path": upload_result["dropbox_path"],
            "result": check_result,
        }

    except Exception as e:
        logger.exception(
            f"❌ Ошибка при обработке теста пользователя {telegram_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e)) from e
