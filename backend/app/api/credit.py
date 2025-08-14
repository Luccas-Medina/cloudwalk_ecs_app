from fastapi import APIRouter, HTTPException
from app.tasks.credit import evaluate_credit
from celery.result import AsyncResult
from fastapi import APIRouter

router = APIRouter(prefix="/credit", tags=["credit"])

@router.post("/evaluate/{user_id}")
def evaluate_credit_endpoint(user_id: int):
    """
    Trigger asynchronous credit evaluation for a given user.
    Returns Celery task ID.
    """
    task = evaluate_credit.delay(user_id)
    return {"task_id": task.id, "status": "pending"}

status_router = APIRouter(prefix="/credit/status", tags=["credit"])

@status_router.get("/{task_id}")
def credit_status(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.state == "PENDING":
        return {"task_id": task_id, "status": "pending"}
    elif task_result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(task_result.info)}
    else:
        return {"task_id": task_id, "status": task_result.state.lower(), "result": task_result.result}
