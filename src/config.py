"""Central configuration, loaded from environment variables (.env locally)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Settings:
    app_name: str = os.getenv("APP_NAME", "Road to Freedom")
    church_name: str = os.getenv("CHURCH_NAME", "New Covenant Church of God")
    timezone: str = os.getenv("TIMEZONE", "America/New_York")

    # Database: SQLite by default; set DATABASE_URL to a Postgres URL in production
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

    # Admin login (leaders). CHANGE THESE.
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "change-me-now")
    secret_key: str = os.getenv("SECRET_KEY", "dev-only-change-me")

    # Twilio (SMS)
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_from_number: str = os.getenv("TWILIO_FROM_NUMBER", "")
    twilio_messaging_service_sid: str = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "")
    sms_dry_run: bool = os.getenv("SMS_DRY_RUN", "true").lower() == "true"

    # Anthropic (AI Q&A)
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

    # Daily note send time (local, 24h)
    daily_note_hour: int = int(os.getenv("DAILY_NOTE_HOUR", "7"))
    daily_note_minute: int = int(os.getenv("DAILY_NOTE_MINUTE", "30"))

    # Secret for /tasks/tick (only needed on hosts that sleep)
    cron_token: str = os.getenv("CRON_TOKEN", "")

    # Rate limit for public AI endpoint (questions per IP per hour)
    ask_limit_per_hour: int = int(os.getenv("ASK_LIMIT_PER_HOUR", "20"))

    content_dir: Path = BASE_DIR / "content"
    lessons_dir: Path = BASE_DIR / "content" / "lessons"
    reference_dir: Path = BASE_DIR / "content" / "reference"
    templates_dir: Path = BASE_DIR / "templates"
    static_dir: Path = BASE_DIR / "static"


settings = Settings()
