from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from utilities.check_function import check_test_results

router = APIRouter(prefix="/api")

class SubmissionModel(BaseModel):
    level: str
    answers: Dict[str, Dict[str, Any]]  # task -> { qnum: answer }

@router.post("/check_test")
async def check_test(submission: SubmissionModel):
    # convert to plain dict for the checker
    try:
        result = await check_test_results(submission.dict())
        return result
    except Exception as e:
        # don't leak internal details in production — this is for dev
        raise HTTPException(status_code=500, detail=str(e))
