"""FastAPI application factory."""
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from . import config
from .routes import router


def create_app() -> FastAPI:
    # No public API docs: this is a private group site.
    app = FastAPI(title="Road to Freedom", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(
        SessionMiddleware,
        secret_key=config.SECRET_KEY,
        session_cookie="rtf_session",
        max_age=config.SESSION_MAX_AGE,
        same_site="lax",
        https_only=config.HTTPS_ONLY,
    )
    app.include_router(router)
    return app
