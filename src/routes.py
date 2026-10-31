"""HTTP routes. Everything except /login and /healthz needs the access code."""
import html

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from . import auth, config

router = APIRouter()


def _login_page(error: str = "", status_code: int = 200) -> HTMLResponse:
    template = (config.TEMPLATES_DIR / "login.html").read_text(encoding="utf-8")
    return HTMLResponse(template.replace("{{error}}", html.escape(error)), status_code)


@router.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_form(request: Request):
    if request.session.get("authed"):
        return RedirectResponse("/", status_code=303)
    return _login_page()


@router.post("/login", include_in_schema=False)
def login_submit(request: Request, code: str = Form(...)):
    ip = auth.client_ip(request)
    if auth.is_locked_out(ip):
        return _login_page("Too many tries. Please wait a few minutes.", 429)
    if auth.code_is_valid(code):
        auth.clear_failures(ip)
        request.session["authed"] = True
        return RedirectResponse("/", status_code=303)
    auth.record_failure(ip)
    return _login_page("That code is not correct.", 401)


@router.get("/logout", include_in_schema=False)
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/", include_in_schema=False, dependencies=[Depends(auth.require_login)])
def home():
    page = config.CONTENT_DIR / config.MAIN_PAGE
    if not page.is_file():
        page = config.CONTENT_DIR / config.FALLBACK_PAGE
    return FileResponse(page, media_type="text/html")


@router.get(
    "/files/{path:path}",
    include_in_schema=False,
    dependencies=[Depends(auth.require_login)],
)
def content_file(path: str):
    """Serve PDFs, images, etc. from src/content/ (login required)."""
    root = config.CONTENT_DIR.resolve()
    target = (root / path).resolve()
    if root not in target.parents or not target.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(target)
