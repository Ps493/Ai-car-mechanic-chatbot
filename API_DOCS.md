# API Documentation

Base URL (local): `http://127.0.0.1:8000/api`

All request/response bodies are JSON unless noted (upload is multipart).

---

## POST /api/chat/

Drives the conversation. Creates a new conversation if `conversation_id` is omitted.

**Request**
```json
{ "conversation_id": "uuid | null", "message": "my car makes a grinding noise when braking" }
```

**Response `200`**
```json
{
  "conversation_id": "24067aab-ff31-49ac-8fe3-b0aca375fa44",
  "reply": "What exactly is happening — please describe the problem in your own words.",
  "status": "collecting_info",
  "ready_for_diagnosis": false,
  "collected_slots": { "vehicle_info": "..." }
}
```

`status` progresses: `collecting_info` → `ready_for_diagnosis` → `diagnosed` → `booked`.
Non-car-related messages get a polite rejection reply instead of advancing the flow.

---

## POST /api/upload/  (multipart/form-data)

**Fields:** `conversation_id`, `file`, `media_type` (`image` | `audio` | `video`)

**Response `201`**
```json
{
  "upload": {
    "id": 3, "file": "/media/uploads/2026/09/23/leak.jpg", "media_type": "image",
    "analysis_result": "Visible reddish fluid pooling under the engine, consistent with a coolant or transmission fluid leak.",
    "analyzed": true, "uploaded_at": "2026-09-23T10:00:00Z"
  },
  "reply": "Got your image. Here's what I can see: ...",
  "conversation_id": "24067aab-..."
}
```

Images are analyzed by Gemini vision automatically. Audio/video are stored and
attached to the case for the technician to review (no AI call — kept minimal
per the assignment's "minimize AI usage" requirement).

---

## POST /api/diagnosis/

Triggers the single AI call that synthesizes a diagnosis from the collected
symptom slots (+ any image analysis notes). Idempotent — calling again returns
the existing diagnosis rather than generating a new one.

**Request**
```json
{ "conversation_id": "24067aab-..." }
```

**Response `201`**
```json
{
  "diagnosis": {
    "id": 1,
    "summary": "This is consistent with worn brake pads or a warped rotor...",
    "likely_causes": ["Worn brake pads", "Warped brake rotor", "Low-quality/contaminated brake fluid"],
    "recommended_service": "Brake pad and rotor inspection/replacement",
    "urgency": "high",
    "confidence": 0.8,
    "created_at": "2026-09-23T10:05:00Z"
  },
  "reply": "Here's my assessment: ..."
}
```

**GET /api/diagnosis/?conversation_id=<uuid>** retrieves an existing diagnosis (`404` if none yet).

---

## POST /api/booking/

Pure CRUD, no AI. Creates a mechanic booking tied to a conversation (and
diagnosis, if one exists).

**Request**
```json
{
  "conversation_id": "24067aab-...",
  "customer_name": "Rahul Sharma",
  "phone_number": "9876543210",
  "preferred_date": "2026-09-30",
  "preferred_time_slot": "Morning / 10-12 PM",
  "address": "MP Nagar, Bhopal",
  "notes": "Prefer weekday"
}
```

**Response `201`**
```json
{
  "id": 1, "conversation": "24067aab-...", "diagnosis": 1,
  "customer_name": "Rahul Sharma", "phone_number": "9876543210",
  "vehicle_info": "2018 Honda City", "preferred_date": "2026-09-30",
  "preferred_time_slot": "Morning / 10-12 PM", "address": "MP Nagar, Bhopal",
  "notes": "Prefer weekday", "status": "pending", "created_at": "2026-09-23T10:06:00Z"
}
```

---

## GET /api/booking/{id}/

**Response `200`** — same shape as the booking creation response.
`404` if the booking doesn't exist.

---

## GET /api/conversation/{id}/  (bonus, used internally by the frontend if needed)

Returns the full conversation: all messages, uploads, collected slots, and
diagnosis (if any). Useful for reloading a session or building an admin view.

---

## Error format

Validation and not-found errors return:
```json
{ "error": "human readable message" }
```
or, for serializer field errors, DRF's standard `{ "field_name": ["message"] }` shape.

## Rate limiting

Anonymous requests are throttled to 60/minute per client (DRF `AnonRateThrottle`)
to keep the free-tier deployment inexpensive and abuse-resistant.
