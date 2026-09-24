# Instant Mechanic — AI Car Mechanic Chatbot

A full-stack chatbot where a car owner describes a vehicle problem, gets guided
through a technician-style intake interview, receives an AI-assisted diagnosis
(with photo analysis support), and can book a mechanic — all in one flow.

**Stack:** Next.js (React) frontend · Django REST Framework backend · SQLite ·
Gemini API (used sparingly — see [ARCHITECTURE.md](./ARCHITECTURE.md)).

```
instant-mechanic-chatbot/
├── backend/     Django + DRF API
├── frontend/    Next.js chat UI
├── ARCHITECTURE.md
└── API_DOCS.md
```

## 1. Backend setup (local)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set GEMINI_API_KEY (free key: https://aistudio.google.com/app/apikey)

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000`. Admin at `/admin/` (view conversations,
diagnoses, bookings). Without a Gemini key set, `/api/diagnosis/` and image
analysis still work — they return a safe fallback response instead of erroring,
so the app never breaks a demo.

## 2. Frontend setup (local)

```bash
cd frontend
npm install
cp .env.local.example .env.local
# set NEXT_PUBLIC_API_BASE_URL to your backend URL (http://127.0.0.1:8000/api for local)
npm run dev
```

Frontend runs at `http://localhost:3000`.

## 3. Deployment

### Frontend → Vercel (free tier)
1. Push this repo to GitHub.
2. Import the `frontend/` directory as a new Vercel project (set **Root Directory** to `frontend`).
3. Add env var `NEXT_PUBLIC_API_BASE_URL` = your live backend URL + `/api`.
4. Deploy. Vercel auto-detects Next.js.

### Backend → Render (free tier, no credit card required)
1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → sign up with GitHub → **New +** → **Web Service**.
3. Select this repo. Set:
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn mechanic_project.wsgi:application`
   - **Instance Type**: Free
4. Add environment variables (Render dashboard → Environment):
   `SECRET_KEY` (any long random string), `DEBUG=False`,
   `CORS_ALLOWED_ORIGINS=<your-vercel-url>`, `GEMINI_API_KEY`,
   `GEMINI_MODEL=gemini-3.6-flash`.
5. Click **Create Web Service**. Render runs `build.sh` (installs deps,
   collects static files, runs migrations) automatically on every deploy —
   you don't need to SSH in or run anything manually.
6. Your API will be live at `https://<your-service-name>.onrender.com`.

**Free-tier notes:**
- The service spins down after ~15 minutes of inactivity; the first request
  after that takes ~30–60 seconds to wake up. Fine for a graded demo — just
  give it a moment on the first request.
- SQLite lives on Render's local disk, which persists while the instance is
  running but resets on redeploy — acceptable for this assignment's scope
  (see ARCHITECTURE.md for the production note on this).
- No credit card is required for the free web service tier.

Alternative if you outgrow the free tier or want a persistent DB: swap in
Render's free PostgreSQL (90 days) — just add `dj-database-url` and point
`DATABASES` at the `DATABASE_URL` env var Render provides.

## 4. Trying it out

1. Open the frontend. Say something like *"my car makes a grinding noise when I brake"*.
2. Answer the follow-up questions (vehicle, symptom, when it occurs, duration, warning signs).
3. Optionally attach a photo (📷) — Gemini vision will describe what it sees.
4. Click **Get Diagnosis** once prompted.
5. Click **Book Mechanic** on the diagnosis card and fill in your details.
6. Check `/admin/` on the backend to see the booking, or call
   `GET /api/booking/{id}/`.

See [API_DOCS.md](./API_DOCS.md) for the full endpoint reference and
[ARCHITECTURE.md](./ARCHITECTURE.md) for design decisions, especially around
**where and why AI is used**.
