"""Public pages: home, join (opt-in signup), lessons, and the AI question box."""
import time
from collections import defaultdict, deque
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Group, Member, QuestionLog
from ..security import normalize_phone
from ..services import ai, lessons, library, reference, sms
from ..web import render

router = APIRouter()

_hits: dict[str, deque] = defaultdict(deque)


def _rate_ok(ip: str) -> bool:
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > 3600:
        q.popleft()
    if len(q) >= settings.ask_limit_per_hour:
        return False
    q.append(now)
    return True


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    m = library.manifest()
    return render(request, "index.html", {
        "lesson_count": len(library.lessons()),
        "principles": reference.principles_with_lessons(),
        "extra_lessons": reference.extra_lessons(),
        "steps": reference.STEP_TEXT,
        "full_pdf": m.get("full_pdf"),
        "resource_count": len(m.get("ministry", [])) + len(m.get("pamphlets", [])),
    })


@router.get("/principles", response_class=HTMLResponse)
def principles_page(request: Request):
    return render(request, "principles.html", {
        "principles": reference.principles_with_lessons(),
        "steps": reference.STEP_TEXT,
    })


@router.get("/meetings", response_class=HTMLResponse)
def meetings_page(request: Request):
    return render(request, "meetings.html", {})


@router.get("/join", response_class=HTMLResponse)
def join_form(request: Request, db: Session = Depends(get_db)):
    groups = db.query(Group).order_by(Group.name).all()
    return render(request, "join.html", {"groups": groups, "error": None})


@router.post("/join", response_class=HTMLResponse)
def join_submit(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(""),
    phone: str = Form(...),
    group_id: str = Form(""),
    consent: str = Form(""),
    db: Session = Depends(get_db),
):
    groups = db.query(Group).order_by(Group.name).all()
    phone_n = normalize_phone(phone)
    if not phone_n:
        return render(request, "join.html", {"groups": groups, "error": "Please enter a valid 10-digit US phone number."})
    if not consent:
        return render(request, "join.html", {"groups": groups, "error": "Please check the box to agree to receive texts."})

    member = db.query(Member).filter(Member.phone == phone_n).first()
    if not member:
        member = Member(first_name=first_name.strip()[:80], last_name=last_name.strip()[:80], phone=phone_n)
        db.add(member)
    member.group_id = int(group_id) if group_id.isdigit() else member.group_id
    member.sms_opt_in = True
    member.opted_in_at = datetime.utcnow()
    member.active = True
    db.commit()
    sms.send_welcome(db, member)
    return render(request, "join_done.html", {"name": member.first_name})


@router.get("/ask", response_class=HTMLResponse)
def ask_page(request: Request):
    return render(request, "ask.html", {})


@router.post("/api/ask")
def ask_api(request: Request, question: str = Form(...), db: Session = Depends(get_db)):
    question = question.strip()[:500]
    if len(question) < 3:
        return JSONResponse({"answer": "Please type a question.", "sources": []})
    ip = request.client.host if request.client else "unknown"
    if not _rate_ok(ip):
        return JSONResponse({"answer": "You've asked a lot of questions this hour. Please try again later.",
                             "sources": []}, status_code=429)
    result = ai.answer_question(question)
    db.add(QuestionLog(question=question, flagged_sensitive=result["crisis"]))
    db.commit()
    return JSONResponse(result)


@router.get("/lessons", response_class=HTMLResponse)
def lesson_list(request: Request):
    return render(request, "lessons.html", {"groups": library.lessons_by_principle(),
                                            "full_pdf": library.manifest().get("full_pdf")})


@router.get("/lessons/search", response_class=HTMLResponse)
def lesson_search(request: Request, q: str = ""):
    hits = lessons.search(q, k=8) if q else []
    return render(request, "search.html", {"q": q, "hits": hits})


@router.get("/lessons/{num}", response_class=HTMLResponse)
def lesson_page(request: Request, num: int):
    lsn = library.get_lesson(num)
    if not lsn:
        raise HTTPException(status_code=404, detail="Lesson not found")
    prev_l, next_l = library.neighbors(num)
    return render(request, "lesson.html", {"lsn": lsn, "html": library.lesson_html(lsn),
                                           "prev_l": prev_l, "next_l": next_l})


@router.get("/resources", response_class=HTMLResponse)
def resources(request: Request):
    m = library.manifest()
    return render(request, "resources.html", {"ministry": m["ministry"], "pamphlets": m["pamphlets"],
                                              "full_pdf": m.get("full_pdf"), "lesson_count": len(m["lessons"])})


@router.get("/health")
def health():
    return {"status": "ok"}
