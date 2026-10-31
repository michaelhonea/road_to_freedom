"""The resource library: lessons, ministry documents, and pamphlets (see tools/import_resources.py)."""
import json
import re
from functools import lru_cache

import markdown

from ..config import settings


@lru_cache(maxsize=1)
def manifest() -> dict:
    path = settings.content_dir / "resources.json"
    if not path.exists():
        return {"lessons": [], "ministry": [], "pamphlets": [], "full_pdf": None}
    return json.loads(path.read_text(encoding="utf-8"))


def reload() -> None:
    manifest.cache_clear()


def lessons() -> list[dict]:
    return manifest()["lessons"]


def lessons_by_principle() -> list[tuple[str, list[dict]]]:
    groups: dict[str, list[dict]] = {}
    for lsn in lessons():
        key = f"Principle {lsn['principle']}" if lsn.get("principle") else "Extra lessons"
        groups.setdefault(key, []).append(lsn)
    return list(groups.items())


def get_lesson(num: int) -> dict | None:
    for lsn in lessons():
        if lsn["num"] == num:
            return lsn
    return None


def neighbors(num: int) -> tuple[dict | None, dict | None]:
    items = lessons()
    for i, lsn in enumerate(items):
        if lsn["num"] == num:
            return (items[i - 1] if i > 0 else None, items[i + 1] if i + 1 < len(items) else None)
    return None, None


def lesson_html(lsn: dict) -> str:
    if not lsn.get("has_text"):
        return ""
    path = settings.lessons_dir / f"{lsn['slug']}.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^#\s+.+\n", "", text, count=1)  # page already shows the title
    return markdown.markdown(text, extensions=["extra", "sane_lists"])
