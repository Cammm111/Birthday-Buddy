# app/services/scheduler_service.py

import logging
import zoneinfo
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select
from sqlalchemy import extract
from sqlalchemy.orm import selectinload
from app.core.db import engine
from app.models.birthday_model import Birthday
from app.services.slack_service import post_birthday_message

logger = logging.getLogger(__name__)

# ───────────────────────────── Module-level scheduler instance ─────────────────────────────
_sched: BackgroundScheduler | None = None

# ───────────────────────────── Birthday job ─────────────────────────────
def birthday_job() -> None: # Query today’s birthdays and post Slack messages at 9 AM ET daily. Uses try/except wrapper so scheduler doesn't crash
    logger.info("Running daily birthday job...")
    try:
        tz = zoneinfo.ZoneInfo("America/New_York")
        today = datetime.now(tz).date()
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
                            f":partying_face: Happy Birthday, *{b.name}*! :tada:",
                            webhook_url=b.workspace.slack_webhook
                        )
                        logger.info(f"Posted birthday for {b.name}")
                    except Exception:
                        logger.exception(f"Slack post failed for {b.name}")
                else:
                    logger.warning(f"Skipping {b.name}: No webhook configured")

        logger.info("Birthday job complete.")
    except Exception:
        logger.exception("Unhandled error in birthday_job")

# ───────────────────────────── Start Scheduler ─────────────────────────────
def start_scheduler() -> None: # Initialize and start the background scheduler
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
    logger.info("Scheduler started, job scheduled at 09:00 ET daily.")


# ───────────────────────────── Stop Scheduler ─────────────────────────────
def stop_scheduler() -> None: # Stop the background scheduler, if running
    global _sched
    if _sched:
        _sched.shutdown(wait=False)
        logger.info("Scheduler stopped.")