"""Loads lesson/reference Markdown and does keyword (BM25-style) retrieval for the AI search box.

Sources: src/content/lessons/*.md and src/content/reference/*.md (8 Principles, 12 Steps...).
Each file is split by `##` headings, and long sections are split further so the AI is given
only the most relevant passages.
"""
import math
import re
from dataclasses import dataclass
from functools import lru_cache

from ..config import settings

STOPWORDS = set(
    "a an and are as at be but by for from has have how i in is it its my of on or so "
    "that the this to was what when where which who why will with you your do does can".split()
)
MAX_CHUNK = 1400


@dataclass
class Passage:
    lesson: str
    heading: str
    text: str
    tokens: list[str]


def _stem(w: str) -> str:
    """Very light stemming so 'forgive', 'forgiving' and 'forgiveness' match each other."""
    for suf in ("ness", "ing", "ed", "es", "s", "ly"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            w = w[: -len(suf)]
            break
    if w.endswith("e") and len(w) > 4:
        w = w[:-1]
    return w


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return [_stem(w) for w in words if w not in STOPWORDS and (len(w) > 1 or w.isdigit())]


def _chunks(text: str) -> list[str]:
    """Split long text on paragraph boundaries into pieces of roughly MAX_CHUNK characters."""
    out, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        if cur and len(cur) + len(para) > MAX_CHUNK:
            out.append(cur.strip())
            cur = ""
        cur += para + "\n\n"
    if cur.strip():
        out.append(cur.strip())
    return out


def _clean(text: str) -> str:
    text = re.sub(r"</?sup>", "", text)
    return re.sub(r"[>*_`]+", "", text)


@lru_cache(maxsize=1)
def load_passages() -> list[Passage]:
    passages: list[Passage] = []
    for folder in (settings.lessons_dir, settings.reference_dir):
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            title_match = re.search(r"^#\s+(.+)$", raw, re.M)
            lesson = title_match.group(1).strip() if title_match else path.stem
            raw_body = re.sub(r"^#\s+.+$", "", raw, count=1, flags=re.M)
            parts = re.split(r"^##\s+", raw_body, flags=re.M)
            sections = [("Overview", parts[0])] + [
                (p.split("\n", 1)[0].strip(), p.split("\n", 1)[1] if "\n" in p else "") for p in parts[1:]
            ]
            for heading, body in sections:
                body = _clean(body).strip()
                if len(body) < 40:
                    continue
                for i, chunk in enumerate(_chunks(body)):
                    h = heading if i == 0 else f"{heading} (cont.)"
                    passages.append(Passage(lesson, h, chunk, _tokens(f"{lesson} {lesson} {h} {chunk}")))
    return passages


def reload() -> int:
    load_passages.cache_clear()
    return len(load_passages())


def search(query: str, k: int = 4) -> list[Passage]:
    passages = load_passages()
    q = _tokens(query)
    if not passages or not q:
        return []
    n = len(passages)
    avg_len = sum(len(p.tokens) for p in passages) / n
    df: dict[str, int] = {}
    for p in passages:
        for t in set(p.tokens):
            df[t] = df.get(t, 0) + 1

    k1, b = 1.5, 0.75
    scored = []
    for p in passages:
        score = 0.0
        length = len(p.tokens) or 1
        for t in q:
            tf = p.tokens.count(t)
            if not tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * length / avg_len))
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:k]]
