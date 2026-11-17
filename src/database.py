"""Database engine and session helpers (SQLAlchemy 2.x)."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

_url = settings.database_url
if _url.startswith("postgres://"):  # some hosts still hand out the old scheme
    _url = _url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if _url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    Path("data").mkdir(exist_ok=True)

engine = create_engine(_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401  (register tables)

    Base.metadata.create_all(bind=engine)
    _add_missing_columns()


def _add_missing_columns() -> None:
    """create_all won't add columns to existing tables; add the email columns if missing."""
    from sqlalchemy import inspect, text

    cols = {c["name"] for c in inspect(engine).get_columns("members")}
    stmts = []
    if "email" not in cols:
        stmts.append("ALTER TABLE members ADD COLUMN email VARCHAR(200)")
    if "email_opt_in" not in cols:
        default = "0" if _url.startswith("sqlite") else "FALSE"
        stmts.append(f"ALTER TABLE members ADD COLUMN email_opt_in BOOLEAN DEFAULT {default}")
    with engine.begin() as conn:
        for st in stmts:
            conn.execute(text(st))
