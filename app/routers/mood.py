"""Mood check-in endpoints. 1-5 scale, optional note."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MoodCheckIn

router = APIRouter(prefix="/mood", tags=["mood"])


class CheckInCreate(BaseModel):
    score: int = Field(ge=1, le=5)
    note: str | None = Field(default=None, max_length=500)


@router.post("/checkin", status_code=201)
def checkin(payload: CheckInCreate, db: Session = Depends(get_db)):
    entry = MoodCheckIn(score=payload.score, note=payload.note)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {
        "id": entry.id,
        "created_at": entry.created_at.isoformat(),
        "score": entry.score,
        "note": entry.note,
    }


@router.get("/history")
def history(limit: int = 90, db: Session = Depends(get_db)):
    rows = (
        db.query(MoodCheckIn)
        .order_by(MoodCheckIn.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "score": r.score,
            "note": r.note,
        }
        for r in rows
    ]
