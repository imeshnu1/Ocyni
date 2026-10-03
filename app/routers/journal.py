"""Journal endpoints. Every write is scanned for crisis language."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import JournalEntry
from ..safety import crisis_response, scan_for_crisis

router = APIRouter(prefix="/journal", tags=["journal"])


class JournalCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    body: str = Field(min_length=1)
    mood_before: int | None = Field(default=None, ge=1, le=5)
    mood_after: int | None = Field(default=None, ge=1, le=5)
    tags: str | None = None


class JournalOut(BaseModel):
    id: int
    created_at: str
    title: str | None
    body: str
    mood_before: int | None
    mood_after: int | None
    tags: str | None
    crisis_flag: bool
    support: dict | None = None

    class Config:
        from_attributes = True


def _to_out(entry: JournalEntry) -> dict:
    data = {
        "id": entry.id,
        "created_at": entry.created_at.isoformat(),
        "title": entry.title,
        "body": entry.body,
        "mood_before": entry.mood_before,
        "mood_after": entry.mood_after,
        "tags": entry.tags,
        "crisis_flag": bool(entry.crisis_flag),
        "support": None,
    }
    if entry.crisis_flag:
        data["support"] = crisis_response()
    return data


@router.post("/entries", response_model=JournalOut, status_code=201)
def create_entry(payload: JournalCreate, db: Session = Depends(get_db)):
    flagged = scan_for_crisis(payload.title) or scan_for_crisis(payload.body)
    entry = JournalEntry(
        title=payload.title,
        body=payload.body,
        mood_before=payload.mood_before,
        mood_after=payload.mood_after,
        tags=payload.tags,
        crisis_flag=1 if flagged else 0,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _to_out(entry)


@router.get("/entries", response_model=list[JournalOut])
def list_entries(limit: int = 50, db: Session = Depends(get_db)):
    entries = (
        db.query(JournalEntry)
        .order_by(JournalEntry.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_to_out(e) for e in entries]


@router.get("/entries/{entry_id}", response_model=JournalOut)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return _to_out(entry)
