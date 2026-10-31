# Design

## Why FastAPI
Same Python stack as your other tooling, small footprint, and the SMS webhook, scheduler, and AI calls are all plain Python. Pages are server-rendered with Jinja2 templates, so there is no separate front-end build.

## Layout
```
main.py                  entry point (run locally or via uvicorn)
render.yaml              Render blueprint
src/
  app.py                 app factory, starts DB + scheduler
  config.py              all settings from environment variables
  database.py, models.py SQLAlchemy tables
  security.py            admin login cookie, phone normalization
  web.py                 template rendering helper
  routers/
    public.py            home, join (opt-in), lessons, /api/ask
    admin.py             leader dashboard and tools
    webhook.py           Twilio inbound (STOP/START/HELP)
    tasks.py             /tasks/tick for sleeping hosts
  services/
    sms.py               Twilio sending, opt-in enforcement, dry-run
    lessons.py           loads Markdown lessons, keyword (BM25) search
    ai.py                Claude answers grounded in retrieved lessons + crisis screen
    scheduler.py         daily note + meeting reminders
  services/library.py    lesson/resource index and lesson page rendering
  tools/import_resources.py  imports the Celebrate Recovery downloads into the site
  tools/build_pdf.py     optional: builds a PDF from the Markdown lessons
  content/lessons/*.md   25 lessons (text) + any of your own
  content/reference/*.md 8 Principles, 12 Steps, Step Study (text for AI search)
  content/resources.json library index (lessons, ministry docs, pamphlets)
  static/resources/      the PDFs: lessons/, ministry/, pamphlets/, combined lesson notes
  templates/, static/    pages and styling
docs/                    these guides
```

## Data tables
members, groups, meetings, attendance, daily_notes, message_log, question_log.

## How the AI box works
1. Question arrives (rate limited per IP, stored without any identity).
2. Crisis words (suicide, self-harm, abuse...) skip the AI and return a 988/911/leader message, and the question is flagged on the admin dashboard.
3. Otherwise the 4 best-matching lesson sections are retrieved and sent to Claude with instructions to answer only from them, stay short, and defer to leaders for medical or counseling matters.
4. If nothing matches, it says so instead of guessing.

## Privacy choices
- Only name, phone, group, and an optional leader note are stored.
- Leader notes and the member list are behind the admin login only.
- Questions are logged without names or phone numbers.
- Recovery information is sensitive: use a strong admin password, keep the GitHub repo private, and share the leader login only with trusted leaders.

## Known limits / next steps
- Single shared admin login (add per-leader accounts later if needed).
- Retrieval is keyword-based; swap in embeddings if the lesson library gets large.
- Attendance table exists but has no screen yet.
- Optional: group-only access code for the whole site.
