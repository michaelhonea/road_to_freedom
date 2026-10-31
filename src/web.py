"""Template helper and app factory live here to avoid circular imports."""
from fastapi import Request
from fastapi.templating import Jinja2Templates

from .config import settings
from .security import is_admin
from .services import library, reference

templates = Jinja2Templates(directory=str(settings.templates_dir))


def render(request: Request, name: str, ctx: dict | None = None, status: int = 200):
    base = {"app_name": settings.app_name, "church_name": settings.church_name,
            "is_admin": is_admin(request), "meeting": reference.MEETING,
            "nav_groups": library.lessons_by_principle(),
            "current_path": request.url.path}
    base.update(ctx or {})
    return templates.TemplateResponse(request, name, base, status_code=status)
