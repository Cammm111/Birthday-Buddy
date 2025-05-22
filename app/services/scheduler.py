# app/services/scheduler.py
from datetime import datetime
from sqlalchemy import extract
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import select
from app.db import Session, engine
from app.models import Birthday
from app.services.slack import post_birthday_message

def birthday_job():
    today = datetime.utcnow().date()
    month, day = today.month, today.day

    with Session(engine) as session:
        stmt = (
            select(Birthday)
            .where(extract("month", Birthday.date_of_birth) == month)  # 
            .where(extract("day",   Birthday.date_of_birth) == day)    # 
        )
        birthdays = session.exec(stmt).all()

    for b in birthdays:
        post_birthday_message(f"🎂 Happy Birthday, *{b.name}*! :tada:")

def start_scheduler():
    sched = BackgroundScheduler(timezone="America/New_York")
    # Every day at 09:00 local time
    sched.add_job(birthday_job, CronTrigger(hour=9, minute=0))
    sched.start()
