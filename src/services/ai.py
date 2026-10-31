"""AI question answering grounded in the lesson content, with a safety screen."""
import logging
import re

from ..config import settings
from . import lessons

log = logging.getLogger(__name__)

CRISIS_PATTERN = re.compile(
    r"\b(suicid\w*|kill myself|end my life|want to die|self[- ]harm|hurt myself|overdos\w*|"
    r"abus\w+ me|being abused)\b",
    re.I,
)

CRISIS_REPLY = (
    "I'm really glad you reached out, and you matter. This is something to talk through with a real "
    "person right now. If you are in danger or thinking about harming yourself, call or text 988 "
    "(Suicide & Crisis Lifeline, free, 24/7) or call 911. You can also contact your group leader or "
    "pastor today. You do not have to carry this alone."
)

SYSTEM_PROMPT = """You are a gentle, encouraging guide for the "{app}" faith-based recovery \
curriculum at {church}. Answer using ONLY the lesson excerpts provided. Keep answers short \
(under 180 words), warm, and practical, and point to the lesson name when helpful.

Rules:
- If the excerpts do not answer the question, say so kindly and suggest asking a group leader. Do not invent teaching.
- You are not a counselor, doctor, or lawyer. Never give medical, medication, or legal advice; suggest a professional or leader.
- If the person seems to be in crisis or danger, urge them to call or text 988 or 911 and contact a leader.
- Be gracious and non-judgmental. Do not shame."""


def is_crisis(question: str) -> bool:
    return bool(CRISIS_PATTERN.search(question))


def answer_question(question: str) -> dict:
    """Returns {"answer": str, "sources": [str], "crisis": bool}."""
    if is_crisis(question):
        return {"answer": CRISIS_REPLY, "sources": [], "crisis": True}

    hits = lessons.search(question, k=4)
    sources = sorted({f"{p.lesson}: {p.heading}" for p in hits})

    if not settings.anthropic_api_key:
        if not hits:
            return {"answer": "I couldn't find that in the lessons. Please ask a group leader.",
                    "sources": [], "crisis": False}
        snippet = hits[0].text[:500]
        return {"answer": f"(AI is not configured yet. Closest lesson section:)\n\n{snippet}",
                "sources": sources, "crisis": False}

    if not hits:
        return {"answer": "I couldn't find that in the lessons. Please ask a group leader or pastor "
                          "- they'd be glad to help.", "sources": [], "crisis": False}

    context = "\n\n".join(f"[{p.lesson} - {p.heading}]\n{p.text[:1500]}" for p in hits)
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=500,
            system=SYSTEM_PROMPT.format(app=settings.app_name, church=settings.church_name),
            messages=[{
                "role": "user",
                "content": f"Lesson excerpts:\n{context}\n\nQuestion: {question}",
            }],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        return {"answer": text or "Sorry, I couldn't put an answer together.",
                "sources": sources, "crisis": False}
    except Exception:  # noqa: BLE001
        log.exception("Claude API call failed")
        return {"answer": "Sorry, the question helper is unavailable right now. Please try again "
                          "later or ask a group leader.", "sources": [], "crisis": False}
