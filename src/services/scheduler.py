"""Background jobs: daily note at a set time, meeting reminders every 15 minutes."""
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from ..config import settings
from ..database import SessionLocal
from ..models import DailyNote, Meeting, Member
from . import sms

log = logging.getLogger(__name__)
TZ = ZoneInfo(settings.timezone)
scheduler = BackgroundScheduler(timezone=TZ)


def now_local() -> datetime:
    return datetime.now(TZ).replace(tzinfo=None)


def send_daily_note() -> None:
    db = SessionLocal()
    try:
        today = now_local().date()
        note = db.query(DailyNote).filter(DailyNote.send_date == today, DailyNote.sent.is_(False)).first()
        if not note:
            log.info("No unsent daily note for %s", today)
            return
        members = db.query(Member).filter(
            Member.sms_opt_in.is_(True), Member.active.is_(True), Member.wants_daily_note.is_(True)
        ).all()
        body = f"{settings.app_name}: {note.body}{sms.FOOTER}"
        for m in members:
            sms.send_sms(db, m, body, "daily_note")
        note.sent = True
        db.commit()
        log.info("Daily note sent to %d members", len(members))
    finally:
        db.close()


def send_meeting_reminders() -> None:
    db = SessionLocal()
    try:
        now = now_local()
        due = db.query(Meeting).filter(Meeting.reminder_sent.is_(False), Meeting.starts_at > now).all()
        for meeting in due:
            send_at = meeting.starts_at - timedelta(hours=meeting.reminder_hours_before)
            if now < send_at:
                continue
            q = db.query(Member).filter(
                Member.sms_opt_in.is_(True), Member.active.is_(True), Member.wants_reminders.is_(True)
            )
            if meeting.group_id:
                q = q.filter(Member.group_id == meeting.group_id)
            when = meeting.starts_at.strftime("%a %b %d at %I:%M %p").replace(" 0", " ")
            where = f" at {meeting.location}" if meeting.location else ""
            extra = f" {meeting.custom_message}" if meeting.custom_message else ""
            body = f"Reminder: {meeting.title} - {when}{where}.{extra}{sms.FOOTER}"
            for m in q.all():
                sms.send_sms(db, m, body, "reminder")
            meeting.reminder_sent = True
            db.commit()
    finally:
        db.close()


def run_due() -> dict:
    """Catch-up tick for hosts that sleep. An outside pinger calls /tasks/tick every ~15 min.
    Safe to call repeatedly: notes and reminders are flagged as sent so nothing double-sends."""
    now = now_local()
    ran = {"daily_note": False, "reminders": True}
    if (now.hour, now.minute) >= (settings.daily_note_hour, settings.daily_note_minute):
        send_daily_note()
        ran["daily_note"] = True
    send_meeting_reminders()
    return ran


def start() -> None:
    if scheduler.running:
        return
    scheduler.add_job(send_daily_note, "cron", hour=settings.daily_note_hour,
                      minute=settings.daily_note_minute, id="daily_note", replace_existing=True)
    scheduler.add_job(send_meeting_reminders, "interval", minutes=15, id="reminders",
                      replace_existing=True)
    scheduler.start()
    log.info("Scheduler started (daily note %02d:%02d %s)", settings.daily_note_hour,
             settings.daily_note_minute, settings.timezone)


def stop() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
