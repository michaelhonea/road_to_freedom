# Road to Freedom

Website for **Road to Freedom**, a Celebrate Recovery small group of New Covenant Church of God, Summerville, SC. The group meets Sundays at 6:00 PM at 304 S Pine St.

The site has a home page with navigation, all 25 lessons (read online or open the PDF notes), the 8 Principles and 12 Steps, free Celebrate Recovery resources, a meeting page with a map, an AI question box, optional text-message encouragement, and a leader admin area.

## Layout

- `main.py` is the entry point
- `src/` holds all code, templates, styles, and lesson content
- `docs/` has setup, design, and hosting notes. Start with `docs/SETUP.md`.

## Run locally

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit ADMIN_PASSWORD and SECRET_KEY
python main.py
```

Open http://localhost:8000

Meeting time and address are set in `src/services/reference.py`.
