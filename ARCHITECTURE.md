# Architecture

## Overview

```
┌─────────────────┐        HTTPS/JSON         ┌──────────────────────────┐
│  Next.js (React) │ ───────────────────────▶ │  Django + DRF             │
│  Vercel (free)    │ ◀─────────────────────── │  Render (free)             │
└─────────────────┘                            │  SQLite                   │
                                                │                            │
                                                │  ┌──────────────────────┐  │
                                                │  │ Traditional logic     │  │
                                                │  │ - intent filter       │  │
                                                │  │ - slot-filling FSM    │  │
                                                │  │ - booking CRUD        │  │
                                                │  └──────────────────────┘  │
                                                │  ┌──────────────────────┐  │
                                                │  │ Gemini (AI, 2 calls   │  │
                                                │  │ only): diagnosis      │  │
                                                │  │ synthesis + image     │  │
                                                │  │ analysis              │  │
                                                │  └──────────────────────┘  │
                                                └──────────────────────────┘
```

## Why this design minimizes AI usage (the core evaluation criterion)

The brief is explicit: *"Use traditional backend logic wherever possible and
minimize AI/API usage."* Most chatbot demos reach for an LLM for every turn of
conversation. This one doesn't. AI is called in exactly **two** places:

1. **`gemini_service.analyze_symptoms()`** — one call, only after all intake
   slots are filled, to turn structured symptom data into a diagnosis. This is
   the one step that genuinely requires reasoning/domain knowledge a rule
   engine can't approximate well.
2. **`gemini_service.analyze_image()`** — one call per uploaded photo, because
   "what's visible in this image" is a vision task no traditional code can do.

Everything else is deterministic Python:

- **Intent filtering** (`intent_classifier.py`): keyword/heuristic matching
  decides whether a message is car-related, a greeting, or off-topic — no API
  call, instant response, zero cost, and fully predictable/testable.
- **Follow-up questioning** (`question_flow.py`): a fixed ordered slot list
  (vehicle, symptom, when it occurs, duration, warning signs) with a simple
  "what's the next unfilled slot" function. This is what lets the bot "ask
  relevant follow-up questions before diagnosis" per the brief, entirely
  without AI.
- **Media storage, conversation state, booking CRUD**: standard Django ORM/DRF,
  no AI involved at all.
- **Audio/video uploads** are stored and attached to the case for a human
  technician to review, rather than run through a speech/video model — a
  deliberate scope cut that keeps AI usage to only where it clearly adds
  diagnostic value within a 48-hour window.

## Data model

- `Conversation` — one diagnosis session; holds `collected_slots` (JSON) so
  the slot-filling state survives across requests without needing a session
  store or re-deriving state from message history each time.
- `Message` — full chat transcript (user + bot), typed (`text|image|audio|video`).
- `MediaUpload` — file + type + (for images) the AI analysis text.
- `Diagnosis` — one-to-one with a conversation; stores the AI's structured
  output plus `raw_ai_response` for auditability/debugging.
- `Booking` — FK to conversation and (optionally) diagnosis; independent
  lifecycle (`pending → confirmed → completed/cancelled`) so it can be managed
  from `/admin/` even without further chatbot involvement.

## API design choices

- Conversation-centric: every endpoint after the first takes a
  `conversation_id`, so the frontend never has to resend the whole chat
  history — the backend is the source of truth for state (important once a
  slot-filling FSM is involved).
- `/api/diagnosis/` is idempotent (POST again returns the existing diagnosis)
  to avoid burning API quota if the frontend retries.
- Graceful AI degradation: if `GEMINI_API_KEY` is missing or the call fails,
  `gemini_service` returns a safe fallback (`confidence: 0`, asks for an
  in-person inspection) instead of a 500 — the rest of the product (booking,
  history, etc.) keeps working even if the AI provider has an outage.

## Frontend

- Single chat page (Next.js App Router) that renders the transcript, an
  intake progress state, a diagnosis "report" card once ready, and a booking
  modal — matching the required UX: text/image/audio/video upload, diagnosis
  history, and a "Book Mechanic" CTA that only appears post-diagnosis.
- All state is component state in `page.js`; no client-side session storage
  needed since the backend owns conversation state via `conversation_id`.

## Known trade-offs given the 48-hour scope

- SQLite on Render's free tier persists while the instance is running but
  resets on redeploy — fine for a graded demo, but a production version
  would move to a managed Postgres (Render's free tier includes one for 90
  days, or Supabase/Neon long-term) and object storage (S3/Cloudflare R2)
  for uploaded media.
- Audio/video are stored, not transcribed/analyzed — flagged above as an
  intentional AI-usage-minimization + time trade-off, not an oversight.
- No auth/user accounts — out of scope per the brief; each conversation is
  anonymous and identified only by its UUID.
