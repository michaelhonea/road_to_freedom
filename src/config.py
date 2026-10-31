"""Settings, read once from environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "content"
TEMPLATES_DIR = BASE_DIR / "templates"

# Drop your real lesson page into src/content/ with this name and it is served at "/".
MAIN_PAGE = "road_to_freedom.html"
FALLBACK_PAGE = "index.html"


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Environment variable {name} is required. Set it in Render "
            "(Environment tab) or in your shell for local runs."
        )
    return value


ACCESS_CODE = _required("ACCESS_CODE")  # shared group code
SECRET_KEY = _required("SECRET_KEY")  # signs the login cookie

# Set HTTPS_ONLY=false for local http testing. Keep true on Render.
HTTPS_ONLY = os.environ.get("HTTPS_ONLY", "true").lower() != "false"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # stay logged in 30 days

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 300
