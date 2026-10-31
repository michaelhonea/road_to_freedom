"""SMS sending via Twilio, with opt-in checks and a dry-run mode for testing."""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Member, MessageLog

log = logging.getLogger(__name__)

STOP_WORDS = {"stop", "stopall", "unsubscribe", "cancel", "end", "quit"}
START_WORDS = {"start", "yes", "unstop"}
HELP_WORDS = {"help", "info"}

FOOTER = " Reply STOP to opt out."


def _client():
    from twilio.rest import Client

    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


def send_sms(db: Session, member: Member, body: str, kind: str) -> bool:
    """Send one text to one member. Returns True on success. Never texts non-opted-in members."""
    if not member.sms_opt_in or not member.active:
        return False

    status = "sent"
    try:
        if settings.sms_dry_run or not settings.twilio_account_sid:
            log.info("[DRY RUN] to %s: %s", member.phone, body)
            status = "dry_run"
        else:
            kwargs = {"to": member.phone, "body": body}
            if settings.twilio_messaging_service_sid:
                kwargs["messaging_service_sid"] = settings.twilio_messaging_service_sid
            else:
                kwargs["from_"] = settings.twilio_from_number
            _client().messages.create(**kwargs)
    except Exception as exc:  # noqa: BLE001
        log.exception("SMS failed for member %s", member.id)
        status = f"failed: {str(exc)[:60]}"

    db.add(MessageLog(member_id=member.id, kind=kind, body=body[:1000], status=status,
                      created_at=datetime.utcnow()))
    db.commit()
    return status in ("sent", "dry_run")


def send_welcome(db: Session, member: Member) -> None:
    send_sms(
        db, member,
        f"Welcome to {settings.app_name}! You'll get daily encouragement and meeting reminders. "
        "Msg & data rates may apply. Reply STOP to opt out, HELP for help.",
        "welcome",
    )


def handle_inbound(db: Session, phone: str, text: str) -> str:
    """Process an inbound text from Twilio. Returns the reply text (empty = no reply)."""
    word = (text or "").strip().lower()
    member = db.query(Member).filter(Member.phone == phone).first()

    if word in STOP_WORDS:
        if member:
            member.sms_opt_in = False
            member.opted_out_at = datetime.utcnow()
            db.commit()
        return f"You're unsubscribed from {settings.app_name}. Reply START to rejoin."
    if word in START_WORDS:
        if member:
            member.sms_opt_in = True
            member.opted_in_at = datetime.utcnow()
            db.commit()
            return f"Welcome back to {settings.app_name}!"
        return ""
    if word in HELP_WORDS:
        return (f"{settings.app_name} / {settings.church_name}. Daily notes & reminders. "
                "Reply STOP to opt out. Contact your group leader for help.")
    return ""
