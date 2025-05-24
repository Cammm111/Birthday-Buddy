# app/routes/utils_route.py

from fastapi import APIRouter, Depends, status

from app.services.auth_service import current_superuser
from app.services.scheduler_service import birthday_job
from app.services.slack_service import post_birthday_message

router = APIRouter(
    prefix="/utils",
    tags=["utils"],
    dependencies=[Depends(current_superuser)],  # superuser only
)

@router.post("/run-birthday-job", status_code=status.HTTP_204_NO_CONTENT)
def run_birthday_job_endpoint():
    """
    Manually trigger the daily birthday job.
    """
    birthday_job()
    return

@router.post("/ping-slack", status_code=status.HTTP_200_OK)
def ping_slack_endpoint(message: str = "Test message"):
    """
    Send a test message to Slack via the configured webhook.
    """
    post_birthday_message(message)
    return {"status": "sent"}
