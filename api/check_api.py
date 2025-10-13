from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from utilities.check_function import check_test_results
from database.base import AsyncSessionLocal
from database.crud.user_session import read_user_session
from database.crud.test_result import create_test_result
from database.models import LevelEnum
import re

router = APIRouter(prefix="/api")


class SubmissionModel(BaseModel):
    level: str
    username: str | None = None
    telegram_id: int
    answers: Dict[str, Dict[str, Any]]


@router.post("/check_test")
async def check_test(submission: SubmissionModel, request: Request):
    data = submission.dict()
    username = (data.get("username") or "").strip()
    level_str = data.get("level")
    answers = data.get("answers") or {}
    telegram_id = data.get("telegram_id")

    # 1️⃣ Проверяем, что хотя бы один ответ есть
    has_any_answer = any(
        (isinstance(v, list) and v) or (isinstance(v, str) and v.strip())
        for task in answers.values()
        for v in task.values()
    )
    if not has_any_answer:
        return {"status": "empty_form"}

    # 2️⃣ Проверяем имя
    #    - очищаем от лишних символов
    #    - если пусто → берём из user_session.username или fallback user_{id}
    safe_name = re.sub(r"[^a-zA-Zа-яА-Я0-9_\-\s]", "", username)

    if not safe_name.strip():
        async with AsyncSessionLocal() as session:
            user_session = await read_user_session(session, telegram_id)

        if user_session and user_session.telegram_username:
            safe_name = user_session.telegram_username
        else:
            safe_name = f"user_{telegram_id}"

    # 3️⃣ Приводим уровень к Enum
    try:
        level = LevelEnum(level_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid level: {level_str}")

    # 4️⃣ Проверяем тест
    try:
        check_result = await check_test_results({**data, "username": safe_name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal check error: {e}")

    # 5️⃣ Формируем результат
    closed_answers = {}
    open_answers = {}
    score = {}

    for task, content in answers.items():
        task_key = f"task_{task[-1]}" if not task.startswith("task_") else task
        task_result = check_result.get(task, {})

        if task_result == "open":
            open_answers[task_key] = content
            continue

        closed_answers[task_key] = {}
        for q_num, user_answer in content.items():
            status = task_result.get(q_num, "unchecked")
            closed_answers[task_key][f"Q{q_num}"] = {
                "answer": user_answer,
                "status": status
            }

        score_str = task_result.get("score")
        if score_str:
            try:
                score_val = int(score_str.split("/")[0])
                score[task_key] = score_val
            except Exception:
                pass

    # 6️⃣ Сохраняем в БД
    async with AsyncSessionLocal() as session:
        try:
            await create_test_result(
                session=session,
                user_id=telegram_id,
                level=level,
                closed_answers=closed_answers,
                open_answers=open_answers or None,
                score=score,
                pdf_path="pending",  # обновится позже
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB error: {e}")

    # 7️⃣ Возвращаем ответ фронтенду
    return {
        "status": "ok",
        "username_used": safe_name,
        "result": check_result
    }
