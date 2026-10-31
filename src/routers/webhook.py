"""Twilio inbound SMS webhook: handles STOP / START / HELP."""
from fastapi import APIRouter, Depends, Form, Request, Response
from sqlalchemy.orm import Session
from xml.sax.saxutils import escape

from ..database import get_db
from ..services import sms

router = APIRouter()


@router.post("/sms/inbound")
def inbound(From: str = Form(...), Body: str = Form(""), db: Session = Depends(get_db)):
    reply = sms.handle_inbound(db, From, Body)
    twiml = "<Response>" + (f"<Message>{escape(reply)}</Message>" if reply else "") + "</Response>"
    return Response(content=twiml, media_type="application/xml")
