"""Import the free Celebrate Recovery resources into the website.

Re-run this whenever Celebrate Recovery posts updated files:

    python -m src.tools.import_resources \
        --leader   "path/to/Lessons-from-Leaders-Guide" \
        --inserts  "path/to/Bulletin-Inserts-2025" \
        --ministry "path/to/MinistryDocs" \
        --pamphlets "path/to/CR-Issue-Pamphlets-Rev-2025.07"

(Folders are the unzipped downloads from https://celebraterecovery.com/free-resources/ )

It will:
  * convert the Leader's Guide Word lessons to Markdown   -> src/content/lessons/
  * copy the PDFs (clean file names)                       -> src/static/resources/
  * pull text from the 8 Principles / 12 Steps PDFs for AI -> src/content/reference/
  * merge all 25 lesson-note PDFs into one full PDF
  * write the library index                                -> src/content/resources.json

Needs: pandoc (for .docx), pdftotext (poppler), and `pip install pypdf` (and reportlab for the cover).
The official files are copied unmodified. Keep the Celebrate Recovery credit on the pages.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
CONTENT = SRC / "content"
LESSONS_MD = CONTENT / "lessons"
REFERENCE_MD = CONTENT / "reference"
RES = SRC / "static" / "resources"

FULL_PDF_NAME = "Complete-Lesson-Notes-1-25.pdf"

MINISTRY_TITLES = [  # (filename keyword, nice title, slug)
    ("8 principles", "The 8 Principles", "8-principles"),
    ("12 steps", "The 12 Steps", "12-steps"),
    ("serenity", "The Serenity Prayer", "serenity-prayer"),
    ("dna group formats", "DNA Group Formats", "dna-group-formats"),
    ("dna updated", "Celebrate Recovery DNA Statement", "dna-statement"),
    ("guidelines", "Basic and Extended Group Guidelines", "group-guidelines"),
    ("step study", "Step Study Assignments", "step-study-assignments"),
    ("4th-step", "Inventory Sheets (Step 4)", "inventory-sheets"),
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def lesson_files(folder: Path, ext: str) -> dict[int, Path]:
    out = {}
    for p in folder.glob(f"*{ext}"):
        m = re.match(r"Lesson\s+(\d+)\s*-\s*(.+)$", p.stem, re.I)
        if m:
            out[int(m.group(1))] = p
    return out


def docx_to_markdown(path: Path, num: int, title: str) -> tuple[str, int | None]:
    md = subprocess.run(["pandoc", str(path), "-t", "gfm", "--wrap=none"],
                        capture_output=True, text=True, check=True).stdout
    lines = [ln.rstrip() for ln in md.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    # Drop the "Lesson N" / "Title" lines pandoc leaves at the top
    dropped = 0
    while lines and dropped < 2 and (re.match(r"^\s*Lesson\s+\d+\s*$", lines[0], re.I)
                                     or lines[0].strip().lower() == title.lower()
                                     or dropped == 1):
        lines.pop(0)
        dropped += 1
        while lines and not lines[0].strip():
            lines.pop(0)
    body = []
    for ln in lines:
        m = re.fullmatch(r"\*\*([^*]+)\*\*", ln.strip())
        body.append(f"## {m.group(1).strip()}" if m else ln)
    text = "\n".join(body)
    pm = re.search(r"Principle\s+(\d+)", text[:400])  # only trust it near the top of the lesson
    principle = int(pm.group(1)) if pm else None
    return f"# Lesson {num}: {title}\n\n{text}\n", principle


def pdf_text(pdf: Path) -> str:
    try:
        out = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    except Exception:  # noqa: BLE001
        return ""
    return re.sub(r"\n{3,}", "\n\n", out.replace("\f", "\n")).strip()


def build_full_pdf(lessons: list[dict]) -> bool:
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        print("pypdf not installed; skipping full PDF (pip install pypdf)")
        return False
    writer = PdfWriter()
    try:  # optional cover page
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        cover = RES / "_cover.pdf"
        c = canvas.Canvas(str(cover), pagesize=letter)
        w, h = letter
        c.setFont("Times-Bold", 34)
        c.drawCentredString(w / 2, h - 300, "Road to Freedom")
        c.setFont("Times-Roman", 16)
        c.drawCentredString(w / 2, h - 335, "Complete Lesson Notes, Lessons 1-25")
        c.setFont("Times-Italic", 11)
        c.drawCentredString(w / 2, 90, "Source: Celebrate Recovery free resources (celebraterecovery.com/free-resources)")
        c.save()
        writer.append(PdfReader(str(cover)))
        cover.unlink()
    except ImportError:
        print("reportlab not installed; full PDF will have no cover page")
    for lsn in lessons:
        start = len(writer.pages)
        writer.append(PdfReader(str(RES / lsn["pdf"])))
        writer.add_outline_item(f"Lesson {lsn['num']}: {lsn['title']}", start)
    with open(RES / FULL_PDF_NAME, "wb") as fh:
        writer.write(fh)
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leader", required=True, type=Path)
    ap.add_argument("--inserts", required=True, type=Path)
    ap.add_argument("--ministry", required=True, type=Path)
    ap.add_argument("--pamphlets", required=True, type=Path)
    a = ap.parse_args()

    for d in (LESSONS_MD, REFERENCE_MD, RES / "lessons", RES / "ministry", RES / "pamphlets"):
        d.mkdir(parents=True, exist_ok=True)
    for old in LESSONS_MD.glob("*.md"):
        old.unlink()  # clears sample lessons and previous imports

    docx = lesson_files(a.leader, ".docx")
    pdfs = lesson_files(a.inserts, ".pdf")
    lessons = []
    for num in sorted(set(docx) | set(pdfs)):
        src_name = (docx.get(num) or pdfs[num]).stem
        title = re.sub(r"^Lesson\s+\d+\s*-\s*", "", src_name, flags=re.I).strip().title()
        title = title.replace("(Part", "(Part")
        entry = {"num": num, "title": title, "slug": f"{num:02d}-{slugify(title)}",
                 "principle": None, "pdf": None, "has_text": False}
        if num in docx:
            md, principle = docx_to_markdown(docx[num], num, title)
            (LESSONS_MD / f"{entry['slug']}.md").write_text(md, encoding="utf-8")
            entry["principle"], entry["has_text"] = principle, True
        if num in pdfs:
            rel = f"lessons/lesson-{num:02d}-{slugify(title)}.pdf"
            shutil.copy2(pdfs[num], RES / rel)
            entry["pdf"] = rel
        lessons.append(entry)

    ministry = []
    for p in sorted(a.ministry.glob("*.pdf")):
        if p.name.startswith("._"):
            continue
        key = p.name.lower()
        match = next((m for m in MINISTRY_TITLES if m[0] in key), None)
        title, slug = (match[1], match[2]) if match else (p.stem, slugify(p.stem))
        rel = f"ministry/{slug}.pdf"
        shutil.copy2(p, RES / rel)
        ministry.append({"title": title, "slug": slug, "file": rel})
        if slug in ("8-principles", "12-steps", "step-study-assignments"):
            text = pdf_text(p)
            if text:
                (REFERENCE_MD / f"{slug}.md").write_text(f"# {title}\n\n{text}\n", encoding="utf-8")
    order = [m[2] for m in MINISTRY_TITLES]
    ministry.sort(key=lambda m: order.index(m["slug"]) if m["slug"] in order else 99)

    topics: dict[str, dict] = {}
    for p in sorted(a.pamphlets.glob("*.pdf")):
        m = re.match(r"^(.*?)\s*-\s*(Bi|Tri)-Fold\.pdf$", p.name, re.I)
        if not m:
            continue
        topic = re.sub(r"\s+", " ", m.group(1)).strip().title()
        for small in ("And", "Or", "Of", "For"):
            topic = re.sub(rf"\b{small}\b", small.lower(), topic)
        topic = topic.replace("and or", "and/or").replace("Abuse - for", "Abuse - For")
        topic = topic.replace("Physical Emotional and/or", "Physical, Emotional, and/or")
        topic = topic.replace("Sexual Addiction - for", "Sexual Addiction - For")
        topic = re.sub(r"\bThe 12 Steps\b", "The 12 Steps", topic)
        kind = "bifold" if m.group(2).lower() == "bi" else "trifold"
        rel = f"pamphlets/{slugify(topic)}-{kind}.pdf"
        shutil.copy2(p, RES / rel)
        topics.setdefault(topic, {"topic": topic, "slug": slugify(topic)})[kind] = rel
    pamphlets = sorted(topics.values(), key=lambda t: t["topic"])

    have_full = build_full_pdf([l for l in lessons if l["pdf"]])
    manifest = {"lessons": lessons, "ministry": ministry, "pamphlets": pamphlets,
                "full_pdf": f"{FULL_PDF_NAME}" if have_full else None}
    (CONTENT / "resources.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Imported {len(lessons)} lessons, {len(ministry)} ministry docs, {len(pamphlets)} pamphlet topics.")


if __name__ == "__main__":
    sys.exit(main())
