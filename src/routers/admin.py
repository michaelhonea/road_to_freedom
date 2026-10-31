"""Leader admin: members, groups, meetings, daily notes, broadcast, message log."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DailyNote, Group, Meeting, Member, MessageLog, QuestionLog
from ..security import (COOKIE_NAME, check_credentials, is_admin, make_session_token,
                        normalize_phone, require_admin)
from ..services import lessons, library, sms
from ..web import render

router = APIRouter(prefix="/admin")


def _guard(request: Request):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    return None


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return render(request, "admin/login.html", {"error": None})


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not check_credentials(username, password):
        return render(request, "admin/login.html", {"error": "Wrong username or password."})
    resp = RedirectResponse("/admin", status_code=303)
    resp.set_cookie(COOKIE_NAME, make_session_token(), httponly=True, samesite="lax",
                    secure=request.url.scheme == "https", max_age=60 * 60 * 12)
    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie(COOKIE_NAME)
    return resp


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    stats = {
        "members": db.query(func.count(Member.id)).filter(Member.active.is_(True)).scalar(),
        "opted_in": db.query(func.count(Member.id)).filter(Member.sms_opt_in.is_(True)).scalar(),
        "upcoming": db.query(func.count(Meeting.id)).filter(Meeting.starts_at > datetime.now()).scalar(),
        "questions": db.query(func.count(QuestionLog.id)).scalar(),
    }
    recent_q = db.query(QuestionLog).order_by(QuestionLog.id.desc()).limit(10).all()
    return render(request, "admin/dashboard.html", {"stats": stats, "recent_q": recent_q})


# ---------- Members ----------
@router.get("/members", response_class=HTMLResponse)
def members(request: Request, db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    return render(request, "admin/members.html", {
        "members": db.query(Member).order_by(Member.first_name).all(),
        "groups": db.query(Group).order_by(Group.name).all(),
        "error": request.query_params.get("error"),
    })


@router.post("/members/add")
def member_add(request: Request, first_name: str = Form(...), last_name: str = Form(""),
               phone: str = Form(...), group_id: str = Form(""),
               consented: str = Form(""), db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    p = normalize_phone(phone)
    if not p:
        return RedirectResponse("/admin/members?error=Invalid+phone", status_code=303)
    if db.query(Member).filter(Member.phone == p).first():
        return RedirectResponse("/admin/members?error=Phone+already+exists", status_code=303)
    m = Member(first_name=first_name.strip(), last_name=last_name.strip(), phone=p,
               group_id=int(group_id) if group_id.isdigit() else None)
    # Only mark opted in if the leader confirms the person gave consent.
    if consented:
        m.sms_opt_in = True
        m.opted_in_at = datetime.utcnow()
    db.add(m)
    db.commit()
    return RedirectResponse("/admin/members", status_code=303)


@router.post("/members/{member_id}/update")
def member_update(member_id: int, request: Request, group_id: str = Form(""),
                  private_note: str = Form(""), active: str = Form(""),
                  db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    m = db.get(Member, member_id)
    if m:
        m.group_id = int(group_id) if group_id.isdigit() else None
        m.private_note = private_note[:2000]
        m.active = bool(active)
        db.commit()
    return RedirectResponse("/admin/members", status_code=303)


@router.post("/members/{member_id}/delete")
def member_delete(member_id: int, request: Request, db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    m = db.get(Member, member_id)
    if m:
        db.query(MessageLog).filter(MessageLog.member_id == m.id).delete()
        db.delete(m)
        db.commit()
    return RedirectResponse("/admin/members", status_code=303)


@router.post("/groups/add")
def group_add(request: Request, name: str = Form(...), description: str = Form(""),
              db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    if name.strip() and not db.query(Group).filter(Group.name == name.strip()).first():
        db.add(Group(name=name.strip(), description=description.strip()))
        db.commit()
    return RedirectResponse("/admin/members", status_code=303)


# ---------- Meetings ----------
@router.get("/meetings", response_class=HTMLResponse)
def meetings(request: Request, db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    return render(request, "admin/meetings.html", {
        "meetings": db.query(Meeting).order_by(Meeting.starts_at.desc()).limit(50).all(),
        "groups": db.query(Group).order_by(Group.name).all(),
    })


@router.post("/meetings/add")
def meeting_add(request: Request, title: str = Form(...), starts_at: str = Form(...),
                location: str = Form(""), group_id: str = Form(""),
                reminder_hours_before: int = Form(24), custom_message: str = Form(""),
                db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    db.add(Meeting(title=title.strip(), starts_at=datetime.fromisoformat(starts_at),
                   location=location.strip(), group_id=int(group_id) if group_id.isdigit() else None,
                   reminder_hours_before=reminder_hours_before, custom_message=custom_message[:300]))
    db.commit()
    return RedirectResponse("/admin/meetings", status_code=303)


@router.post("/meetings/{meeting_id}/delete")
def meeting_delete(meeting_id: int, request: Request, db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    m = db.get(Meeting, meeting_id)
    if m:
        db.delete(m)
        db.commit()
    return RedirectResponse("/admin/meetings", status_code=303)


# ---------- Daily notes ----------
@router.get("/notes", response_class=HTMLResponse)
def notes(request: Request, db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    return render(request, "admin/notes.html", {
        "notes": db.query(DailyNote).filter(DailyNote.send_date >= date.today())
                   .order_by(DailyNote.send_date).limit(60).all(),
        "today": date.today().isoformat(),
    })


@router.post("/notes/add")
def note_add(request: Request, send_date: str = Form(...), body: str = Form(...),
             db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    d = date.fromisoformat(send_date)
    existing = db.query(DailyNote).filter(DailyNote.send_date == d).first()
    if existing:
        existing.body, existing.sent = body[:600], False
    else:
        db.add(DailyNote(send_date=d, body=body[:600]))
    db.commit()
    return RedirectResponse("/admin/notes", status_code=303)


@router.post("/notes/{note_id}/delete")
def note_delete(note_id: int, request: Request, db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    n = db.get(DailyNote, note_id)
    if n:
        db.delete(n)
        db.commit()
    return RedirectResponse("/admin/notes", status_code=303)


# ---------- Broadcast + log ----------
@router.get("/broadcast", response_class=HTMLResponse)
def broadcast_form(request: Request, db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    return render(request, "admin/broadcast.html", {
        "groups": db.query(Group).order_by(Group.name).all(),
        "sent": request.query_params.get("sent"),
    })


@router.post("/broadcast")
def broadcast(request: Request, body: str = Form(...), group_id: str = Form(""),
              db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    q = db.query(Member).filter(Member.sms_opt_in.is_(True), Member.active.is_(True))
    if group_id.isdigit():
        q = q.filter(Member.group_id == int(group_id))
    count = 0
    for m in q.all():
        if sms.send_sms(db, m, body.strip()[:300] + sms.FOOTER, "broadcast"):
            count += 1
    return RedirectResponse(f"/admin/broadcast?sent={count}", status_code=303)


@router.get("/log", response_class=HTMLResponse)
def log_view(request: Request, db: Session = Depends(get_db)):
    if (r := _guard(request)):
        return r
    rows = (db.query(MessageLog, Member).outerjoin(Member, MessageLog.member_id == Member.id)
              .order_by(MessageLog.id.desc()).limit(200).all())
    return render(request, "admin/log.html", {"rows": rows})


@router.post("/lessons/reload")
def reload_lessons(request: Request):
    if (r := _guard(request)):
        return r
    lessons.reload()
    library.reload()
    return RedirectResponse("/admin", status_code=303)
