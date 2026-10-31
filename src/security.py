"""Admin authentication (signed session cookie) and phone normalization."""
import hmac
import re

from fastapi import HTTPException, Request
from itsdangerous import BadSignature, URLSafeSerializer

from .config import settings

_serializer = URLSafeSerializer(settings.secret_key, salt="admin-session")
COOKIE_NAME = "rtf_admin"


def check_credentials(username: str, password: str) -> bool:
    ok_user = hmac.compare_digest(username, settings.admin_username)
    ok_pass = hmac.compare_digest(password, settings.admin_password)
    return ok_user and ok_pass


def make_session_token() -> str:
    return _serializer.dumps({"admin": True})


def is_admin(request: Request) -> bool:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return False
    try:
        return bool(_serializer.loads(token).get("admin"))
    except BadSignature:
        return False


def require_admin(request: Request) -> None:
    if not is_admin(request):
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})


def normalize_phone(raw: str) -> str | None:
    """Return +1XXXXXXXXXX for US numbers, or None if it doesn't look valid."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return None
