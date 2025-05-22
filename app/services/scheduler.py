# app/services/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
from sqlmodel import Session, select
from app.db import engine
from app.models import Workspace, Birthday
from app.services.slack import post_birthday_message

sched = BackgroundScheduler(timezone="America/New_York")

def birthday_job():
    with Session(engine) as session:
        for ws in session.exec(select(Workspace)):
            tz = pytz.timezone(ws.timezone)
            today = datetime.now(tz).date()
            month, day = today.month, today.day
            bdays = session.exec(
                select(Birthday)
                .where(Birthday.workspace_id==ws.id)
                .where(extract("month", Birthday.date_of_birth)==month)
                .where(extract("day",   Birthday.date_of_birth)==day)
            ).all()
            for b in bdays:
                msg = f"🎂 Happy Birthday, *{b.name}*! :tada:"
                post_birthday_message(msg, ws.slack_webhook)

def start_scheduler():
    sched.add_job(birthday_job, CronTrigger(hour=9, minute=0))
    sched.start()
