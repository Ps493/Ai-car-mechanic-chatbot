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

### Backend → AWS free tier (Elastic Beanstalk, simplest path)
1. `pip install awsebcli`, then from `backend/`: `eb init -p python-3.11 instant-mechanic`.
2. `eb create instant-mechanic-env --single` (single-instance = free-tier eligible t2/t3.micro).
3. Set environment variables in the EB console (or `eb setenv`):
   `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=<your-eb-domain>`,
   `CORS_ALLOWED_ORIGINS=<your-vercel-url>`, `GEMINI_API_KEY`, `GEMINI_MODEL`.
4. `eb deploy`. Run `eb ssh` → `python manage.py migrate` once after first deploy
   (or add it as a `.ebextensions` container command — see below).
5. SQLite lives on the instance's local disk, which is fine for a graded demo
   but is **not persistent across redeploys/instance replacement** — see
   ARCHITECTURE.md for the production note on this.

A minimal `.ebextensions/django.config` for auto-migrate on deploy:
```yaml
container_commands:
  01_migrate:
    command: "source /var/app/venv/*/bin/activate && python manage.py migrate --noinput"
```

Alternative: any host that runs a standard WSGI app works (Render, Railway,
PythonAnywhere) if AWS setup is more time than you have — `gunicorn
mechanic_project.wsgi` is the entry point either way.

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
