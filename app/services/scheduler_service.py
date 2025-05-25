# app/services/scheduler_service.py

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select
from sqlalchemy import extract

from app.core.db import engine
from app.models.birthday_model import Birthday
from app.services.slack_service import post_birthday_message

# keep a module-level handle so we can check running state
_sched: BackgroundScheduler | None = None

def birthday_job() -> None:
    today = datetime.utcnow().date()
    month, day = today.month, today.day

    with Session(engine) as session:
        stmt = (
            select(Birthday)
            .where(extract("month", Birthday.date_of_birth) == month)
            .where(extract("day", Birthday.date_of_birth) == day)
        )
        birthdays = session.exec(stmt).all()

    for b in birthdays:
        post_birthday_message(f"🎂 Happy Birthday, *{b.name}*! :tada:")

def start_scheduler() -> None:
    global _sched
    # if it’s already running, do nothing
    if _sched and _sched.running:
        return

    _sched = BackgroundScheduler(timezone="America/New_York")
    _sched.add_job(
        birthday_job,
        CronTrigger(hour=9, minute=0),
        id="daily-birthday-job",
        replace_existing=True,
    )
    _sched.start()
