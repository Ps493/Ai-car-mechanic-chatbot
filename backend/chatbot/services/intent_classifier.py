"""
Pure keyword/heuristic intent classification.

This deliberately does NOT call any AI model. The task explicitly rewards
minimizing AI usage, and "is this even a car-related question" is a cheap,
deterministic classification problem — a keyword/regex match is faster,
free, and more predictable than an LLM call for this step.
"""
import re

CAR_KEYWORDS = {
    "car", "vehicle", "engine", "brake", "brakes", "tyre", "tire", "tires", "tyres",
    "battery", "clutch", "gear", "gearbox", "transmission", "exhaust", "silencer",
    "coolant", "radiator", "oil", "spark", "plug", "alternator", "suspension",
    "steering", "wheel", "headlight", "taillight", "indicator", "wiper", "ac",
    "air conditioning", "horn", "dashboard", "check engine", "smoke", "noise",
    "vibration", "overheating", "overheat", "starter", "ignition", "fuel",
    "petrol", "diesel", "mileage", "sensor", "abs", "airbag", "bumper", "bonnet",
    "hood", "clunk", "rattle", "squeal", "squeak", "grinding", "stall", "stalling",
    "misfire", "idle", "idling", "jerk", "jerking", "pull", "pulling", "leak",
    "leaking", "smell", "burning", "gas", "diagnostic", "service", "mechanic",
    "workshop", "repair", "sedan", "suv", "hatchback", "truck", "bike",
    "motorcycle", "scooter", "odometer", "rpm", "gauge", "warning light",
}

GREETING_PATTERNS = re.compile(r"^\s*(hi|hello|hey|good\s(morning|afternoon|evening))[\s!.,]*$", re.I)

OFF_TOPIC_HINTS = {
    "recipe", "movie", "weather", "stock", "politics", "homework", "song",
    "joke", "relationship", "medicine", "doctor", "flight", "hotel booking",
}


def is_greeting(text: str) -> bool:
    return bool(GREETING_PATTERNS.match(text.strip()))


def is_car_related(text: str, has_media: bool = False) -> bool:
    """Returns True if the message is plausibly about a car/mechanical issue.

    Media (image/audio/video) uploads are always treated as car-related since
    the user is presumably showing/describing a vehicle problem.
    """
    if has_media:
        return True

    lowered = text.lower()

    if is_greeting(lowered):
        return True  # let the flow greet back and steer to cars

    if any(hint in lowered for hint in OFF_TOPIC_HINTS):
        return False

    # Very short generic replies (yes/no/numbers) during an active flow are fine —
    # the caller decides context; here we only judge the raw content.
    if any(word in lowered for word in CAR_KEYWORDS):
        return True

    # Short free-text answers to follow-up questions (e.g. "it's a 2018 Honda City",
    # "when I brake", "yesterday") won't always hit a keyword. Caller (question_flow)
    # handles those inside an active slot-filling session, so default to True only
    # when the message is very short (likely an answer, not a new unrelated topic).
    if len(lowered.split()) <= 4:
        return True

    return False
