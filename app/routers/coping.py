"""Coping exercises & guided bot endpoints (Feature 3).

Template-driven (no LLM) so everything works fully offline and
deterministically. Safety rules enforced here:
- Watchkeeping non-interference: exercises never start while on watch.
- No addiction design: a daily session cap encourages real-world connection.
- Harm response matched to risk: crisis language always surfaces resources.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..coping_exercises import get_exercise, list_exercises, valid_category
from ..database import get_db
from ..models import CopingSession
from ..safety import crisis_response, scan_for_crisis

router = APIRouter(prefix="/coping", tags=["coping"])

DAILY_SESSION_CAP = 10

DISCLAIMER = (
    "Ocyni is a wellness support tool, not a medical device "
    "or a replacement for professional help."
)


# ---------- schemas ----------

class SessionStart(BaseModel):
    exercise_id: str = Field(min_length=1)
    mood_before: int = Field(ge=1, le=5)
    on_watch: bool = Field(default=False, description="True if currently on watch duty")
    note: str | None = Field(default=None, max_length=500)


class SessionComplete(BaseModel):
    mood_after: int = Field(ge=1, le=5)


class SessionOut(BaseModel):
    id: int
    created_at: str
    exercise_id: str
    exercise_title: str
    mood_before: int
    mood_after: int | None
    mood_shift: int | None
    completed: bool
    crisis_flag: bool
    support: dict | None = None

    class Config:
        from_attributes = True


class TalkRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


# ---------- keyword matching (deterministic, offline) ----------

_KEYWORD_RULES: list[tuple[tuple[str, ...], tuple[str, ...], str]] = [
    (
        ("sleep", "tired", "insomnia", "can't sleep", "cannot sleep", "awake",
         "restless", "fatigue", "exhausted"),
        ("cabin-wind-down", "progressive-muscle-relaxation"),
        "Rest is hard to come by at sea, and tiredness makes everything heavier. "
        "A short wind-down routine can help your body switch off when your watch ends.",
    ),
    (
        ("angry", "anger", "furious", "argument", "fight", "fighting",
         "shouted", "conflict", "annoyed", "irritated", "rage"),
        ("anger-cool-down", "box-breathing"),
        "Close quarters make tempers flare — that's human, not a failing. "
        "Cooling down now keeps a small clash from poisoning the rest of the voyage.",
    ),
    (
        ("lonely", "loneliness", "homesick", "family", "alone",
         "isolated", "miss home", "missing home"),
        ("letter-home-unsent", "shipmate-micro-connection"),
        "Being far from home for months is one of the hardest parts of this life. "
        "Putting words to it — on paper or with a shipmate — genuinely helps.",
    ),
    (
        ("panic", "anxious", "anxiety", "worried", "worry", "scared",
         "fear", "overwhelm", "racing", "nervous"),
        ("five-senses-grounding", "4-7-8-breathing"),
        "When everything speeds up inside, the way back is through the body — "
        "slow breath, present senses. Let's bring you back to right here, right now.",
    ),
    (
        ("tense", "tension", "shoulders", "neck", "headache", "tight",
         "stress", "stressed"),
        ("progressive-muscle-relaxation", "box-breathing"),
        "Your body keeps the score of every long watch. Releasing that held "
        "tension on purpose works better than waiting for it to fade.",
    ),
    (
        ("breath", "breathing", "calm", "relax", "unwind"),
        ("box-breathing", "4-7-8-breathing"),
        "Good instinct — the breath is the fastest lever you have. "
        "A few slow rounds can shift your whole state.",
    ),
]

_DEFAULT_REPLY = (
    "Thanks for telling me that — it takes something to put it into words. "
    "Here's a short exercise that helps a lot of crew in moments like this. "
    "And remember: I'm a tool, not a person. If there's a shipmate you trust, "
    "talking to them matters more than anything I can offer."
)
_DEFAULT_SUGGESTIONS = ("box-breathing", "five-senses-grounding")


def _match_exercises(message: str) -> tuple[str, tuple[str, ...]]:
    lowered = message.lower()
    for keywords, exercise_ids, reply in _KEYWORD_RULES:
        if any(k in lowered for k in keywords):
            return reply, exercise_ids
    return _DEFAULT_REPLY, _DEFAULT_SUGGESTIONS


# ---------- helpers ----------

def _session_to_out(session: CopingSession) -> dict:
    exercise = get_exercise(session.exercise_id) or {}
    mood_shift = (
        session.mood_after - session.mood_before
        if session.mood_after is not None
        else None
    )
    data = {
        "id": session.id,
        "created_at": session.created_at.isoformat(),
        "exercise_id": session.exercise_id,
        "exercise_title": exercise.get("title", session.exercise_id),
        "mood_before": session.mood_before,
        "mood_after": session.mood_after,
        "mood_shift": mood_shift,
        "completed": bool(session.completed),
        "crisis_flag": bool(session.crisis_flag),
        "support": None,
    }
    if session.crisis_flag:
        data["support"] = crisis_response()
    return data


def _sessions_today(db: Session) -> int:
    start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return (
        db.query(CopingSession)
        .filter(CopingSession.created_at >= start.replace(tzinfo=None))
        .count()
    )


# ---------- endpoints ----------

@router.get("/exercises")
def list_all_exercises(category: str | None = None):
    if category is not None and not valid_category(category):
        raise HTTPException(status_code=404, detail="Unknown exercise category")
    return {"exercises": list_exercises(category)}


@router.get("/exercises/{exercise_id}")
def exercise_detail(exercise_id: str):
    exercise = get_exercise(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise


@router.post("/sessions/start")
def start_session(payload: SessionStart, db: Session = Depends(get_db)):
    exercise = get_exercise(payload.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    # Watchkeeping non-interference: never start an exercise on watch.
    if payload.on_watch:
        return JSONResponse(
            status_code=200,
            content={
                "status": "deferred",
                "message": (
                    "You're on watch — this can wait. Ocyni never interrupts "
                    "watchkeeping duties. Come back when you're off duty and we'll "
                    "do this together. If it's urgent, hand over duties per vessel "
                    "protocol first."
                ),
            },
        )

    # No-addiction design: daily cap encourages real-world connection.
    if _sessions_today(db) >= DAILY_SESSION_CAP:
        raise HTTPException(
            status_code=429,
            detail=(
                f"You've done {DAILY_SESSION_CAP} coping sessions today — that's "
                "plenty. Ocyni helps and lets go: try a real-world connection "
                "instead — check in with a shipmate, step out for some air, or "
                "write home. The exercises will be here tomorrow."
            ),
        )

    flagged = scan_for_crisis(payload.note)
    session = CopingSession(
        exercise_id=payload.exercise_id,
        mood_before=payload.mood_before,
        crisis_flag=1 if flagged else 0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    out = _session_to_out(session)
    out["exercise"] = exercise
    return JSONResponse(status_code=201, content=out)


@router.post("/sessions/{session_id}/complete")
def complete_session(
    session_id: int, payload: SessionComplete, db: Session = Depends(get_db)
):
    session = db.query(CopingSession).filter(CopingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.completed = 1
    session.mood_after = payload.mood_after
    db.commit()
    db.refresh(session)
    return _session_to_out(session)


@router.post("/talk")
def talk(payload: TalkRequest):
    """Template-driven supportive reply + matched exercises. Offline, deterministic."""
    if scan_for_crisis(payload.message):
        support = crisis_response()
        return {
            "crisis_flag": True,
            "reply": support["message"],
            "suggested_exercises": [],
            "support": support,
            "disclaimer": DISCLAIMER,
        }
    reply, exercise_ids = _match_exercises(payload.message)
    suggestions = [
        summary
        for summary in list_exercises()
        if summary["id"] in exercise_ids
    ]
    return {
        "crisis_flag": False,
        "reply": reply,
        "suggested_exercises": suggestions,
        "support": None,
        "disclaimer": DISCLAIMER,
    }
