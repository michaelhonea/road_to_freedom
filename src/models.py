"""Database tables."""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(300), default="")

    members: Mapped[list["Member"]] = relationship(back_populates="group")


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80), default="")
    phone: Mapped[str] = mapped_column(String(20), unique=True)  # E.164, e.g. +18435551234
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)

    # Consent: we only text people who opted in. STOP flips this to False.
    sms_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    opted_in_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opted_out_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    wants_daily_note: Mapped[bool] = mapped_column(Boolean, default=True)
    wants_reminders: Mapped[bool] = mapped_column(Boolean, default=True)

    private_note: Mapped[str] = mapped_column(Text, default="")  # leader-only notes
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    group: Mapped[Group | None] = relationship(back_populates="members")
    attendance: Mapped[list["Attendance"]] = relationship(back_populates="member")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Meeting(Base):
    """A scheduled meeting/event that triggers reminders."""

    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    starts_at: Mapped[datetime] = mapped_column(DateTime)  # stored as local time
    location: Mapped[str] = mapped_column(String(200), default="")
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    reminder_hours_before: Mapped[int] = mapped_column(Integer, default=24)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    custom_message: Mapped[str] = mapped_column(String(300), default="")

    attendance: Mapped[list["Attendance"]] = relationship(back_populates="meeting")


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"))
    present: Mapped[bool] = mapped_column(Boolean, default=True)

    member: Mapped[Member] = relationship(back_populates="attendance")
    meeting: Mapped[Meeting] = relationship(back_populates="attendance")


class DailyNote(Base):
    """One note per date. Leaders write them ahead; the scheduler sends them."""

    __tablename__ = "daily_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    send_date: Mapped[date] = mapped_column(Date, unique=True)
    body: Mapped[str] = mapped_column(String(600))
    sent: Mapped[bool] = mapped_column(Boolean, default=False)


class MessageLog(Base):
    __tablename__ = "message_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int | None] = mapped_column(ForeignKey("members.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(30))  # daily_note | reminder | broadcast | reply
    body: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class QuestionLog(Base):
    """Questions asked through the AI search box (no personal identifiers stored)."""

    __tablename__ = "question_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(String(500))
    flagged_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
