"""AI question answering grounded in the lesson content, with a safety screen."""
import logging
import random
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

# Crude language only. Words that also appear in Scripture or recovery talk (hell, damn, ass, sex)
# are deliberately NOT listed, so honest questions about them are never blocked.
INAPPROPRIATE_PATTERN = re.compile(
    r"(f+u+c+k\w*|sh[i1]+t\w*|b[i1]tch\w*|cunt\w*|d[i1]ckhead\w*|asshole\w*|dumbass\w*|"
    r"motherf\w*|\bwtf\b|\bstfu\b|\bpussy\b|\bwhore\w*|\bslut\w*|\bporn\w*)",
    re.I,
)

# Playful, never cruel. Rotated so repeat offenders get fresh lines.
JESUS_REPLIES = [
    "Would you ask Jesus that? Go ahead, picture it. I'll wait. This box happily answers honest "
    "questions about God, Jesus, the Bible, the church, or the Road to Freedom class and website, "
    "so try it again in words you'd say to Him.",
    "Bold choice of words. Now, would you ask Jesus that to His face? He's heard everything, but "
    "He'd probably love the real question underneath it. Ask me that one, and I'll gladly help.",
    "Interesting. Next question: would you ask Jesus that? I answer questions about God, Jesus, "
    "the Bible, the church, or the Road to Freedom class and website, and I'm happy to help once "
    "it's rephrased.",
    "Hmm, that one might make the angels clutch their pearls. Would you ask Jesus that? Reword it "
    "and I'll do my best with anything about the Bible, church, or your walk with God.",
    "I'm fairly sure that's not how you'd start a chat with Jesus. Would you ask Him that? Try "
    "again with the honest version. I can answer questions like that, just not in that tone.",
]

OFFTOPIC_REPLIES = [
    "Nice try, but I'm not the Googling kind. Please keep your questions about God, Jesus, the "
    "Bible, the church, or the Road to Freedom class and website.",
    "That's a fascinating question for someone else. I stay in my lane: God, Jesus, the Bible, the "
    "church, or the Road to Freedom class and website. Ask me something from there!",
]

SYSTEM_PROMPT = """You are a gentle, encouraging guide for the "{app}" faith-based recovery \
curriculum at {church}. Answer using ONLY the lesson excerpts provided. Keep answers short \
(under 180 words), warm, and practical, and point to the lesson name when helpful.

Rules:
- Stay in scope: God, Jesus, the Bible, prayer, the church, and the Road to Freedom class and website. If the \
question is unrelated to those (sports, coding, recipes, celebrities, politics, trivia, etc.), do NOT \
answer it. Reply with ONE short, dry, playfully sarcastic line (never mean) that tells them to keep \
questions about God, Jesus, the Bible, the church, or the Road to Freedom class and website, then stop. Vary your wording each time.
- If the question is crude, mocking, or inappropriate, reply playfully with a fresh version of \
"Would you ask Jesus that?", and explain you are glad to answer honest questions like that if reworded. \
Never repeat the same phrasing twice.
- Sarcasm is only for off-topic or inappropriate questions. If the person sounds sincere, hurting, or \
struggling, be gentle with NO sarcasm.
- If a Bible/church/recovery question is not covered by the excerpts, say so kindly and suggest asking a \
group leader. Do not invent teaching.
- You are not a counselor, doctor, or lawyer. Never give medical, medication, or legal advice; suggest a professional or leader.
- If the person seems to be in crisis or danger, urge them to call or text 988 or 911 and contact a leader.
- Be gracious. Do not shame anyone who is sincerely seeking help."""


def is_crisis(question: str) -> bool:
    return bool(CRISIS_PATTERN.search(question))


def is_inappropriate(question: str) -> bool:
    return bool(INAPPROPRIATE_PATTERN.search(question))


def answer_question(question: str) -> dict:
    """Returns {"answer": str, "sources": [str], "crisis": bool}."""
    if is_crisis(question):
        return {"answer": CRISIS_REPLY, "sources": [], "crisis": True}

    if is_inappropriate(question):
        return {"answer": random.choice(JESUS_REPLIES), "sources": [], "crisis": False}

    hits = lessons.search(question, k=4)
    sources = sorted({f"{p.lesson}: {p.heading}" for p in hits})

    if not settings.anthropic_api_key:
        if not hits:
            return {"answer": "I couldn't find that in the lessons. Please ask a group leader.",
                    "sources": [], "crisis": False}
        snippet = hits[0].text[:500]
        return {"answer": f"(AI is not configured yet. Closest lesson section:)\n\n{snippet}",
                "sources": sources, "crisis": False}

    # No excerpt match: still let the model judge scope (off-topic gets a sarcastic redirect).
    context = ("\n\n".join(f"[{p.lesson} - {p.heading}]\n{p.text[:1500]}" for p in hits)
               or "(no matching lesson excerpts)")
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
