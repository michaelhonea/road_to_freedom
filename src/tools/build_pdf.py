"""Builds one combined PDF from the Markdown lessons in src/content/lessons/.

Usage:  python -m src.tools.build_pdf            (writes build/Road_to_Freedom_Workbook.pdf)
Requires: pip install markdown weasyprint   (weasyprint needs system pango; see docs/SETUP.md)
"""
import sys
from pathlib import Path

import markdown

from ..config import BASE_DIR, settings

CSS = """
@page { size: Letter; margin: 0.9in; @bottom-center { content: counter(page); font-size: 10pt; color:#777 } }
body { font-family: Georgia, serif; font-size: 12pt; line-height: 1.5; color:#222 }
h1 { color:#1f3a5f; page-break-before: always; border-bottom: 3px solid #c8963e; padding-bottom:6pt }
h2 { color:#1f3a5f; margin-top: 18pt } blockquote { color:#666; font-style: italic }
.cover { text-align:center; margin-top: 3in; page-break-after: always } .cover h1 { page-break-before: avoid; border:0; font-size: 34pt }
"""


def main() -> None:
    try:
        from weasyprint import HTML
    except ImportError:
        sys.exit("Install weasyprint first:  pip install weasyprint")

    files = sorted(settings.lessons_dir.glob("*.md"))
    if not files:
        sys.exit("No lesson files found.")
    body = [f'<div class="cover"><h1>{settings.app_name}</h1><p>{settings.church_name}</p></div>']
    for f in files:
        body.append(markdown.markdown(f.read_text(encoding="utf-8"), extensions=["extra"]))
    html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(body)}</body></html>"

    out_dir = Path(BASE_DIR).parent / "build"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "Road_to_Freedom_Workbook.pdf"
    HTML(string=html).write_pdf(str(out))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
