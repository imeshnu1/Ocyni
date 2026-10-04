"""Calm home check-in router — the conversational brain of the home screen.

The app opens with a greeting and one question ("how has your day been?").
This router reads the answer — free text, a mood tap, or both — and routes
the seafarer to the right feature: journal, sleep, or a guided coping exercise.

Template-driven (no LLM) so everything works fully offline and
deterministically. Safety rules enforced here:
- Crisis language always takes priority and surfaces resources immediately.
- Mood 1/5 always routes to soothing first, whatever the words say.
"""
import hashlib

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..coping_exercises import get_exercise
from ..safety import crisis_response, scan_for_crisis

router = APIRouter(prefix="/home", tags=["home"])


# ---------- schemas ----------

class RecommendRequest(BaseModel):
    message: str | None = Field(default=None, max_length=2000)
    mood: int | None = Field(default=None, ge=1, le=5)
    name: str | None = Field(default=None, max_length=100)


# ---------- keyword rules (deterministic, offline) ----------

SLEEP_KEYWORDS = (
    "sleep", "tired", "exhausted", "insomnia", "can't sleep",
    "cannot sleep", "couldn't sleep", "awake all night", "restless",
)

# (keywords, exercise slug) — checked in order, first match wins.
COPING_RULES: list[tuple[tuple[str, ...], str]] = [
    (("panic", "panicking", "anxiety", "anxious"), "4-7-8-breathing"),
    (("overwhelm", "overwhelmed"), "five-senses-grounding"),
    (("angry", "anger", "furious"), "anger-cool-down"),
    (("stress", "stressed", "tense", "tension"), "progressive-muscle-relaxation"),
]

JOURNAL_KEYWORDS = (
    "sad", "lonely", "loneliness", "miss home", "homesick",
    "vent", "confused", "think",
)

CRISIS_EXERCISE = "five-senses-grounding"
DEFAULT_COPING_EXERCISE = "box-breathing"


# ---------- reply templates (2-4 sentences, human-sounding) ----------

_SLEEP_REPLIES = [
    "{greet} Sleep is the first thing to break at sea, and everything feels "
    "harder without it. Let's sort out your rest — I'll open the sleep "
    "optimizer so you can log your watch and get a plan that fits around it.",
    "{greet} Being exhausted makes every watch feel twice as long. The good "
    "news: small changes to light, caffeine, and wind-down can make a real "
    "difference. Let's open your sleep plan.",
    "{greet} Tiredness is your body asking for help, not a weakness. I'll "
    "take you to the sleep optimizer — log your schedule and it'll build "
    "rest around your watches.",
]

_COPING_REPLIES = [
    "{greet} That sounds like a lot to carry right now. Let's slow things "
    "down together — I'll open a short guided exercise made for exactly "
    "this feeling.",
    "{greet} I hear you — when it gets like this, the fastest way back is "
    "through the body, not the mind. There's a {duration}-minute exercise "
    "ready for you; we'll do it step by step.",
    "{greet} Rough stretches happen out here. You don't have to push through "
    "on willpower alone — let me open a quick exercise to help you reset.",
]

_JOURNAL_REPLIES = [
    "{greet} Some things need to be said out loud — or at least written "
    "down. I'll open your journal; getting it out of your head and onto "
    "the page really does lighten it.",
    "{greet} Writing it out is one of the most reliable ways to untangle a "
    "knotted-up feeling. Your journal is open and private — take your time.",
    "{greet} When thoughts keep looping, putting them into words breaks the "
    "loop. Let's open the journal and get them somewhere they can't chase you.",
]

_CALM_REPLIES = [
    "{greet} Good — hold onto this. Days like this are worth noticing. If "
    "you want, jot a quick line in your journal so future-you remembers "
    "what a good day at sea feels like.",
    "{greet} Love to hear it. Keep doing whatever's working. A one-line "
    "journal note is a nice way to bank the feeling.",
    "{greet} That's the good stuff. Nothing to fix today — but if anything "
    "is on your mind, the journal is always there.",
]

_CRISIS_REPLY = (
    "{greet} I'm really glad you told me — that took courage. Right now the "
    "most important thing is you don't sit with this alone: I've listed "
    "people you can reach right now below. Let's also do a short grounding "
    "exercise together, one step at a time."
)

_TITLES = {
    "sleep": "Sleep & Circadian Optimizer",
    "coping": "Guided Coping Exercise",
    "journal": "Journal & CBT Reframe",
    "none": "All good",
}

_REASONS = {
    "sleep": "Fatigue is the signal — rest first, everything else gets easier after sleep.",
    "coping": "Your body is asking for relief right now — a short guided exercise is the fastest way there.",
    "journal": "Some feelings untangle best in writing — your private journal is the right place.",
    "none": "You're in a good place — no intervention needed, just an optional note to self.",
    "crisis": "Grounding first — steady the body, then reach out.",
}


# ---------- helpers ----------

def _greet(name: str | None) -> str:
    return f"Hey {name.strip()}," if name and name.strip() else "Hey,"


def _pick(variants: list[str], key: str) -> str:
    """Deterministic variant pick — same input always yields the same reply."""
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    return variants[int(digest, 16) % len(variants)]


def _duration(exercise_id: str) -> int:
    exercise = get_exercise(exercise_id)
    return exercise["duration_minutes"] if exercise else 5


def _match_coping_exercise(message: str) -> str | None:
    lowered = message.lower()
    for keywords, exercise_id in COPING_RULES:
        if any(k in lowered for k in keywords):
            return exercise_id
    return None


def _build_reply(template: str, name: str | None, exercise_id: str | None = None) -> str:
    return template.format(
        greet=_greet(name),
        duration=_duration(exercise_id) if exercise_id else 5,
    )


# ---------- endpoint ----------

@router.post("/recommend")
def recommend(payload: RecommendRequest):
    """Route a home-screen check-in to the right feature.

    Accepts free text, a 1-5 mood tap, or both. At least one is required.
    """
    message = (payload.message or "").strip()
    mood = payload.mood
    name = payload.name.strip() if payload.name and payload.name.strip() else None

    if not message and mood is None:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one of: message, mood",
        )

    key = f"{message}|{mood}"

    # 1. Crisis always comes first.
    if message and scan_for_crisis(message):
        return {
            "reply": _build_reply(_CRISIS_REPLY, name),
            "recommendation": {
                "feature": "coping",
                "title": _TITLES["coping"],
                "reason": _REASONS["crisis"],
                "exercise_id": CRISIS_EXERCISE,
            },
            "crisis_flag": True,
            "support": crisis_response(),
        }

    lowered = message.lower()

    # 2. Mood 1/5 overrides everything — soothe first.
    if mood == 1:
        exercise_id = _match_coping_exercise(message) or DEFAULT_COPING_EXERCISE
        return {
            "reply": _build_reply(_pick(_COPING_REPLIES, key), name, exercise_id),
            "recommendation": {
                "feature": "coping",
                "title": _TITLES["coping"],
                "reason": _REASONS["coping"],
                "exercise_id": exercise_id,
            },
            "crisis_flag": False,
            "support": None,
        }

    # 3. Keyword routing on the message (message beats mood, except mood 1).
    if message:
        if any(k in lowered for k in SLEEP_KEYWORDS):
            return {
                "reply": _build_reply(_pick(_SLEEP_REPLIES, key), name),
                "recommendation": {
                    "feature": "sleep",
                    "title": _TITLES["sleep"],
                    "reason": _REASONS["sleep"],
                    "exercise_id": None,
                },
                "crisis_flag": False,
                "support": None,
            }
        exercise_id = _match_coping_exercise(message)
        if exercise_id:
            return {
                "reply": _build_reply(_pick(_COPING_REPLIES, key), name, exercise_id),
                "recommendation": {
                    "feature": "coping",
                    "title": _TITLES["coping"],
                    "reason": _REASONS["coping"],
                    "exercise_id": exercise_id,
                },
                "crisis_flag": False,
                "support": None,
            }
        if any(k in lowered for k in JOURNAL_KEYWORDS):
            return {
                "reply": _build_reply(_pick(_JOURNAL_REPLIES, key), name),
                "recommendation": {
                    "feature": "journal",
                    "title": _TITLES["journal"],
                    "reason": _REASONS["journal"],
                    "exercise_id": None,
                },
                "crisis_flag": False,
                "support": None,
            }
        # Message present but no keyword hit — writing it out is the safe default.
        return {
            "reply": _build_reply(_pick(_JOURNAL_REPLIES, key), name),
            "recommendation": {
                "feature": "journal",
                "title": _TITLES["journal"],
                "reason": _REASONS["journal"],
                "exercise_id": None,
            },
            "crisis_flag": False,
            "support": None,
        }

    # 4. Mood-only fallback.
    if mood is not None and mood <= 2:
        return {
            "reply": _build_reply(
                _pick(_COPING_REPLIES, key), name, DEFAULT_COPING_EXERCISE
            ),
            "recommendation": {
                "feature": "coping",
                "title": _TITLES["coping"],
                "reason": _REASONS["coping"],
                "exercise_id": DEFAULT_COPING_EXERCISE,
            },
            "crisis_flag": False,
            "support": None,
        }
    if mood == 3:
        return {
            "reply": _build_reply(_pick(_JOURNAL_REPLIES, key), name),
            "recommendation": {
                "feature": "journal",
                "title": _TITLES["journal"],
                "reason": _REASONS["journal"],
                "exercise_id": None,
            },
            "crisis_flag": False,
            "support": None,
        }
    # mood 4-5: warm affirmation, nothing to fix.
    return {
        "reply": _build_reply(_pick(_CALM_REPLIES, key), name),
        "recommendation": {
            "feature": "none",
            "title": _TITLES["none"],
            "reason": _REASONS["none"],
            "exercise_id": None,
        },
        "crisis_flag": False,
        "support": None,
    }
