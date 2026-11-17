"""Email sending via SMTP (Gmail App Password), with opt-in checks and a dry-run mode."""
import logging
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Member, MessageLog

log = logging.getLogger(__name__)

FOOTER = "\n\nTo stop these emails, reply STOP or contact your group leader."


def configured() -> bool:
    return bool(settings.smtp_user and settings.smtp_password)


def _deliver(to_addr: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = f"{settings.app_name} <{settings.email_from or settings.smtp_user}>"
    msg["To"] = to_addr
    msg["Subject"] = subject
    if settings.email_reply_to:
        msg["Reply-To"] = settings.email_reply_to
    msg.set_content(body)
    ctx = ssl.create_default_context()
    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_host, 465, context=ctx, timeout=20) as s:
            s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as s:
            s.starttls(context=ctx)
            s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)


def send_email(db: Session, member: Member, subject: str, body: str, kind: str) -> bool:
    """Send one email to one member. Never emails people who did not opt in."""
    if not member.email or not member.email_opt_in or not member.active:
        return False
    status = "sent"
    try:
        if settings.email_dry_run or not configured():
            log.info("[EMAIL DRY RUN] to %s: %s | %s", member.email, subject, body)
            status = "dry_run"
        else:
            _deliver(member.email, subject, body + FOOTER)
    except Exception as exc:  # noqa: BLE001
        log.exception("Email failed for member %s", member.id)
        status = f"failed: {str(exc)[:60]}"
    db.add(MessageLog(member_id=member.id, kind=f"email_{kind}", body=body[:1000], status=status,
                      created_at=datetime.utcnow()))
    db.commit()
    return status in ("sent", "dry_run")


def send_welcome(db: Session, member: Member) -> None:
    send_email(db, member, f"Welcome to {settings.app_name}",
               f"Hi {member.first_name},\n\nWelcome to {settings.app_name} at {settings.church_name}. "
               "You'll get daily encouragement and meeting reminders by email.", "welcome")
