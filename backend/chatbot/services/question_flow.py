"""
Deterministic slot-filling state machine for the "senior technician" persona.

Instead of asking an LLM "what should I ask next", we track a small set of
required slots per conversation and walk through them in order. This is the
"traditional backend logic wherever possible" requirement in action — the
follow-up questioning costs zero AI tokens.

Once all required slots are filled, the caller (views.py) triggers the single
Gemini call needed to synthesize an actual diagnosis.
"""

# Ordered so the "senior technician" interview feels natural.
REQUIRED_SLOTS = [
    ("vehicle_info", "What car do you drive (make, model, and approximate year)?"),
    ("symptom", "What exactly is happening — please describe the problem in your own words."),
    ("when_occurs", "When does it happen? For example: at startup, while braking, at high speed, or all the time."),
    ("duration", "How long has this been going on — just started, a few days, or longer?"),
    ("warning_signs", "Have you noticed any warning lights on the dashboard, unusual smells, or noises?"),
]

OPTIONAL_MEDIA_PROMPT = (
    "If you have a photo of the issue (e.g. a warning light, leak, or damaged part), "
    "or a short audio/video clip of the noise, feel free to upload it — it helps a lot. "
    "Otherwise, just reply 'no' and we'll continue."
)


def next_missing_slot(collected_slots: dict):
    for key, question in REQUIRED_SLOTS:
        if not collected_slots.get(key):
            return key, question
    return None, None


def is_ready_for_diagnosis(collected_slots: dict) -> bool:
    return all(collected_slots.get(key) for key, _ in REQUIRED_SLOTS)


def record_answer(collected_slots: dict, pending_slot: str, answer_text: str) -> dict:
    """Traditional logic: store the raw answer text against the slot that was
    being asked. No AI call needed to do this bookkeeping."""
    if pending_slot:
        collected_slots[pending_slot] = answer_text.strip()
    return collected_slots


def build_progress_summary(collected_slots: dict) -> str:
    lines = []
    labels = {
        "vehicle_info": "Vehicle",
        "symptom": "Symptom",
        "when_occurs": "Occurs",
        "duration": "Duration",
        "warning_signs": "Warning signs",
    }
    for key, label in labels.items():
        if collected_slots.get(key):
            lines.append(f"- {label}: {collected_slots[key]}")
    return "\n".join(lines)
