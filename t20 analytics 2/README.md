# t20-analytics — Deployment Guide

This repo contains a Flask-based cricket analytics app. This document shows simple, copy-paste steps to host the app publicly. I added a `Procfile`, `Dockerfile`, and `vercel.json` to this repo to make common hosting options easier.

Important files already added:
- `Procfile` — `web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app` (for Render / Heroku)
- `Dockerfile` — containerized app using Gunicorn (uses `$PORT` env var)
- `vercel.json` — instruct Vercel to use the Dockerfile (if your plan allows Docker builds)
- `requirements.txt` — includes `gunicorn`

Before deploying
- Ensure the `data/` folder is present (it is in this repo) and that your `templates/` and `static/` folders are in the project root.
- Confirm `requirements.txt` is up to date. Install locally to test:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
# open http://localhost:5050 (or PORT env var if set)
```

Option A — Render (recommended, easy)
1. Push the repository to GitHub.
2. Create a new Web Service on Render (or a similar host like Railway/Heroku).
   - Connect your GitHub repo.
   - Build Command: `pip install -r requirements.txt`
   - Start Command (Render / Heroku style): `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
3. Render will set `$PORT` automatically. The `Procfile` is already present, so many hosts auto-detect and use it.

Option B — Railway / Heroku (also easy)
- Railway: create a new service, choose GitHub repo. Railway will run `pip install -r requirements.txt` and you can set the Start command to the same Gunicorn command above.
- Heroku: `git push heroku main` (Heroku will use `Procfile` if present).

Option C — Vercel (Docker) — only if your Vercel plan supports Docker
1. Ensure Dockerfile and `vercel.json` are in repo root (already added).
2. Push and deploy. Vercel will run Docker builds if your account/plan allows it.
3. If Vercel does not support Docker for your account, you will get a build error — see next section.

Option D — Local Docker (test container locally before pushing)

```bash
# build
docker build -t t20-app .

# run (map host port 8000 to container PORT)
docker run --rm -e PORT=8000 -p 8000:8000 t20-app

# test
curl -i http://localhost:8000/
curl -i http://localhost:8000/health
```

If you get 404 on Vercel
- Check the Vercel Build Logs first. If Docker build didn't run or failed, paste the lines here and I will fix the Dockerfile / requirements.
- If Docker build succeeded but there's no runtime logs, the container might have crashed. Check Runtime Logs.
- If Vercel plan doesn't allow Docker, deploy to Render/Railway instead — it's straightforward and reliable for WSGI apps.

Environment variables and tips
- The app reads `$PORT` and `$HOST` if you run `python app.py` directly. Gunicorn uses `$PORT` in the `Procfile` and Dockerfile.
- If you use browser-facing analytics or API keys, store them in the host's environment variables.

Want me to deploy for you?
- I can: (a) prepare a GitHub repo and push these changes (you must give repo access), or (b) walk you through connecting the existing repo to Render (very quick).

Tell me which host you prefer and I will: create any remaining small files, give exact step-by-step commands for your OS, and/or test a local Docker run and paste results here.