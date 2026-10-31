# Design

| Module | Job |
|---|---|
| `main.py` | Creates the app; runs uvicorn for local use |
| `src/app.py` | App factory, signed-cookie session middleware, docs endpoints disabled |
| `src/config.py` | Reads env vars; refuses to start without `ACCESS_CODE` and `SECRET_KEY` |
| `src/auth.py` | Constant-time code check, login dependency, 5-tries-per-5-minutes limiter |
| `src/routes.py` | `/login`, `/logout`, `/` (lesson page), `/files/...` (PDFs etc.), `/healthz` |
| `src/templates/login.html` | Login page |
| `src/content/` | Lesson HTML, PDFs, images. Served only after login |

Notes:
- Content is never mounted as public static files, so every page and PDF goes through the login check.
- File serving blocks path traversal.
- The login limiter is in memory per instance and resets on restart, which is fine for a small group.
- Pages are marked `noindex` so search engines skip them.
