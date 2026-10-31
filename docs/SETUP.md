# Setup

## Deploy on Render (free)

1. Push this repo to GitHub. Make it **private** (Settings > General > Danger Zone > Change visibility), since the lessons live in the repo.
2. In Render: **New > Web Service**, connect the repo.
3. Language: Python. Instance Type: **Free**.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Environment tab, add:
   - `ACCESS_CODE` = the code you give your group
   - `SECRET_KEY` = a long random string (for example, run `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
7. Advanced > Health Check Path: `/healthz`
8. Deploy.

The free tier sleeps after about 15 minutes idle. The first visit afterward takes 30 to 60 seconds. The $7 Starter plan removes that.

## Weekly update

1. Replace `src/content/road_to_freedom.html` (and any PDFs in `src/content/`).
2. Commit and push. Render redeploys automatically.

If a lesson links to a PDF, use `files/yourfile.pdf` (relative, no leading slash issues) so the login check applies.

## Run locally

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ACCESS_CODE=test SECRET_KEY=devkey HTTPS_ONLY=false   # Windows: use set
python main.py
```

Open http://localhost:8000

## Changing the access code

Change `ACCESS_CODE` in Render's Environment tab. Anyone already logged in stays logged in for 30 days. To log everyone out, also change `SECRET_KEY`.
