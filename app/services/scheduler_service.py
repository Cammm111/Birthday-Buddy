# app/services/scheduler_service.py

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select
from sqlalchemy import extract
from sqlalchemy.orm import selectinload
import logging

from app.core.db import engine
from app.models.birthday_model import Birthday
from app.services.slack_service import post_birthday_message

logger = logging.getLogger(__name__)

# Module-level scheduler instance
_sched: BackgroundScheduler | None = None

def birthday_job() -> None:
    logger.info("🎉 Running daily birthday job...")
    today = datetime.utcnow().date()
    month, day = today.month, today.day

    with Session(engine) as session:
        stmt = (
            select(Birthday)
            .options(selectinload(Birthday.workspace))
            .where(extract("month", Birthday.date_of_birth) == month)
            .where(extract("day", Birthday.date_of_birth) == day)
        )
        birthdays = session.exec(stmt).all()

        for b in birthdays:
            if b.workspace and b.workspace.slack_webhook:
                try:
                    post_birthday_message(
                        f"🎂 Happy Birthday, *{b.name}*! :tada:",
                        webhook_url=b.workspace.slack_webhook
                    )
                    logger.info(f"✅ Posted birthday for {b.name}")
                except Exception as e:
                    logger.exception(f"❌ Slack post failed for {b.name}")
            else:
                logger.warning(f"⚠️ Skipping {b.name}: No webhook configured")

    logger.info("✅ Birthday job complete.")

def start_scheduler() -> None:
    global _sched
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
