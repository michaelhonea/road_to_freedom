"""Shared access-code login with a small in-memory brute-force limiter."""
import secrets
import time

from fastapi import HTTPException, Request

from . import config

_failures: dict[str, list[float]] = {}


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def is_locked_out(ip: str) -> bool:
    cutoff = time.time() - config.LOCKOUT_SECONDS
    recent = [t for t in _failures.get(ip, []) if t > cutoff]
    _failures[ip] = recent
    return len(recent) >= config.MAX_FAILED_ATTEMPTS


def record_failure(ip: str) -> None:
    _failures.setdefault(ip, []).append(time.time())


def clear_failures(ip: str) -> None:
    _failures.pop(ip, None)


def code_is_valid(submitted: str) -> bool:
    return secrets.compare_digest(
        submitted.strip().encode("utf-8"), config.ACCESS_CODE.encode("utf-8")
    )


def require_login(request: Request) -> None:
    """Dependency: send anyone without a valid session to the login page."""
    if not request.session.get("authed"):
        raise HTTPException(status_code=303, headers={"Location": "/login"})
