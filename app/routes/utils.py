# app/routers/utils.py

from fastapi import APIRouter, Depends
from app.auth import current_superuser
from app.services.scheduler import birthday_job
from app.services.slack import post_birthday_message

router = APIRouter(
    prefix="/utils",
    tags=["utils"],
    dependencies=[Depends(current_superuser)],  # superuser only
)

@router.post("/run-birthday-job", status_code=204)
def run_birthday_job():
    """
    Manually trigger the daily birthday job.
    """
    birthday_job()
    return

@router.post("/ping-slack")
def ping_slack(webhook_url: str, message: str = "Test message"):
    """
    Send a test message to a Slack webhook.
    """
    post_birthday_message(message, webhook_url)
    return {"status": "sent"}
