# Hosting guide

## Read this first: what the free tier can and can't do

Checked against Render's docs ([render.com/docs/free](https://render.com/docs/free)):

- A free web service **spins down after 15 minutes** with no visitors; the next visit takes about a minute to wake it.
- **Local files are wiped** on redeploy, restart, or spin-down, so the SQLite file would lose all members.
- **Free Postgres expires 30 days after creation**, then is deleted after a 14-day grace period.

Your site needs to send texts at set times and must never lose member data, so there are two good paths.

## Option A (recommended): always-on paid, about the cost of a coffee a month

Render **Starter** web service plus a paid Render Postgres (`render.yaml` is already set up for this). Confirm current prices on [render.com/pricing](https://render.com/pricing). Nothing sleeps, so the built-in scheduler sends the daily note and reminders on its own, and the database is backed by a real plan.

## Option B: free web + free outside database + a free pinger

1. Web service on Render **free**.
2. Free Postgres from **Neon** or **Supabase** (not Render's, which expires). Put its connection string in `DATABASE_URL`.
3. A free pinger (cron-job.org or UptimeRobot) that requests this URL every 10-15 minutes:
   `https://YOUR-APP.onrender.com/tasks/tick?token=YOUR_CRON_TOKEN`
   This wakes the site and sends anything due. Set `CRON_TOKEN` to a long random string in Render.

Tradeoff: texts may be a few minutes late, and the first visitor after idle waits about a minute.

## Deploy steps (either option)

1. **GitHub:** unzip the project, create a repo (you planned `michaelhonea/Road-too-Freedom`), and push. `.gitignore` already excludes `.env` and the database.
   ```
   git init && git add . && git commit -m "Initial site"
   git branch -M main
   git remote add origin https://github.com/michaelhonea/Road-too-Freedom.git
   git push -u origin main
   ```
2. **Render:** New > Blueprint (Option A) pointing at the repo, or New > Web Service (Option B) with build `pip install -r requirements.txt` and start `uvicorn main:app --host 0.0.0.0 --port $PORT`.
3. **Environment variables** (Render > Environment): `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SECRET_KEY`, `DATABASE_URL`, `ANTHROPIC_API_KEY`, and later the `TWILIO_*` values. Keep `SMS_DRY_RUN=true` until Twilio is approved.
4. **Test:** open `/health`, then `/admin/login`.
5. **Updates:** push to GitHub and Render redeploys automatically. Group members never need a GitHub account.

## Custom domain

Render > Settings > Custom Domains, then add the CNAME record at your registrar. HTTPS is automatic.

## Twilio texting setup

1. Create a Twilio account and buy a local number (or a toll-free number).
2. US carriers require registration before group texting. For a church that is **A2P 10DLC (Sole Proprietor or Standard Brand)**, or **toll-free verification**. Approval takes days to weeks, so start now. Use the signup page text as your proof of opt-in.
3. In Twilio, set the number's (or Messaging Service's) incoming-message webhook to `https://YOUR-APP.onrender.com/sms/inbound` (HTTP POST). This is how STOP/START/HELP work.
4. Put the SID, token, and number into Render, then set `SMS_DRY_RUN=false`.
5. Send yourself a test from **Admin > Send Text** before texting the group.

Rules this site already follows: texts only go to people who opted in, every message includes "Reply STOP to opt out", and STOP is honored immediately.

## Is it private?

The lessons pages and the question box are public. If you want group-only access, put the whole site behind a shared access code. That is a small addition; ask and it can be added.
