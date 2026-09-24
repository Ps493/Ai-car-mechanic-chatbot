"""
The ONLY module in this codebase that calls the Gemini API.

By design, AI is used in exactly two places, both of which genuinely require
reasoning that hand-written rules can't reliably do:
  1. Synthesizing a diagnosis from structured symptom data (analyze_symptoms)
  2. Reading an uploaded photo of a car problem (analyze_image)

Everything else (intent filtering, follow-up questions, booking, persistence)
is handled with traditional Python/Django logic in the rest of the app.
"""
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PERSONA = (
    "You are a senior automobile technician with 20+ years of hands-on experience "
    "diagnosing cars, SUVs, and motorcycles. You are precise, safety-conscious, and "
    "avoid unnecessary alarm. You only ever discuss vehicle mechanical/electrical issues."
)


def _get_client():
    import google.generativeai as genai

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured on the server.")
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai


def analyze_symptoms(collected_slots: dict, image_analyses: list[str]) -> dict:
    """Single AI call: turn structured symptom slots (+ any image analysis notes)
    into a diagnosis. Returns a dict matching the Diagnosis model fields.

    Falls back to a safe, generic response if the API key isn't configured or
    the call fails, so the API never hard-crashes a demo because of a missing key.
    """
    prompt = f"""{SYSTEM_PERSONA}

A customer described the following car problem. Based ONLY on this information,
give a professional preliminary diagnosis. Respond with STRICT JSON only, no markdown
fences, matching exactly this schema:

{{
  "summary": "2-4 sentence plain-English explanation of what is likely wrong",
  "likely_causes": ["cause 1", "cause 2", "cause 3"],
  "recommended_service": "short name of the repair/service needed, e.g. 'Brake pad replacement'",
  "urgency": "low | medium | high | urgent",
  "confidence": 0.0
}}

Customer-reported details:
- Vehicle: {collected_slots.get('vehicle_info', 'unknown')}
- Symptom: {collected_slots.get('symptom', 'unknown')}
- When it occurs: {collected_slots.get('when_occurs', 'unknown')}
- Duration: {collected_slots.get('duration', 'unknown')}
- Warning signs: {collected_slots.get('warning_signs', 'unknown')}

Notes from any uploaded photos/clips (if empty, none were provided):
{chr(10).join(f"- {a}" for a in image_analyses) if image_analyses else "- (none)"}

If the information is insufficient for a confident diagnosis, say so honestly in
"summary" and set "confidence" low, but still suggest the most likely 1-2 causes.
Remember: "urgent" means the customer should stop driving immediately (e.g. brake
failure, smoke, overheating). Do not exaggerate urgency for minor issues.
"""
    try:
        genai = _get_client()
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        # Strip accidental markdown fences defensively
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            raw_text = raw_text.split("json", 1)[-1] if raw_text.lower().startswith("json") else raw_text
        data = json.loads(raw_text)
        data["raw_ai_response"] = response.text
        return data
    except Exception as exc:  # noqa: BLE001 - we want a graceful fallback in a demo/eval context
        logger.exception("Gemini diagnosis call failed, using fallback")
        return {
            "summary": (
                "We collected your symptom details, but our AI diagnosis service is "
                "temporarily unavailable. Based on the description alone, a technician "
                "should inspect the vehicle in person to confirm the exact cause."
            ),
            "likely_causes": ["Unable to determine automatically — needs in-person inspection"],
            "recommended_service": "General diagnostic inspection",
            "urgency": "medium",
            "confidence": 0.0,
            "raw_ai_response": f"ERROR: {exc}",
        }


def analyze_image(image_bytes: bytes, mime_type: str) -> str:
    """Single AI call per image: ask Gemini vision to describe anything relevant
    to a car problem (dashboard lights, leaks, damage, worn parts, etc.)."""
    try:
        genai = _get_client()
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(
            [
                {"mime_type": mime_type, "data": image_bytes},
                (
                    "You are a senior automobile technician. In 1-3 concise sentences, "
                    "describe anything relevant to a mechanical/electrical car problem "
                    "visible in this image (e.g. warning lights, fluid leaks, worn parts, "
                    "damage, rust, tyre condition). If nothing car-related is visible, say so."
                ),
            ]
        )
        return response.text.strip()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini image analysis failed")
        return f"(Image analysis unavailable right now: {exc})"
