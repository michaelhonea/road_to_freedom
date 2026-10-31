"""Secured endpoint an external pinger (cron-job.org, UptimeRobot) calls to wake a sleeping
host and run any due texts. Not needed if your host stays running 24/7."""
import hmac

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..services import scheduler

router = APIRouter()


@router.get("/tasks/tick")
def tick(token: str = ""):
    if not settings.cron_token or not hmac.compare_digest(token, settings.cron_token):
        raise HTTPException(status_code=403, detail="forbidden")
    return scheduler.run_due()
