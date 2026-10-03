"""Sleep & Circadian Optimizer endpoints.

Hard safety rule: the plan generator only ever recommends sleep inside
off-duty hours. Watch periods are always labeled no-sleep zones.
All guidance is non-pharmaceutical. Data stays on-device (SQLite).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import sleep_logic as sl
from ..database import get_db
from ..models import SleepLog, WatchSchedule
from ..safety import crisis_response, scan_for_crisis

router = APIRouter(prefix="/sleep", tags=["sleep"])


# ---------- schemas ----------

class WatchScheduleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)  # e.g. "4/8", "6/6", "custom"
    watch1_start: str = Field(examples=["04:00"])
    watch1_end: str = Field(examples=["08:00"])
    watch2_start: str | None = Field(default=None, examples=["16:00"])
    watch2_end: str | None = Field(default=None, examples=["20:00"])


class WatchScheduleOut(BaseModel):
    id: int
    name: str
    watch1_start: str
    watch1_end: str
    watch2_start: str | None
    watch2_end: str | None

    class Config:
        from_attributes = True


class SleepLogCreate(BaseModel):
    sleep_date: str = Field(examples=["2026-10-03"])  # YYYY-MM-DD, ship local
    bedtime: str = Field(examples=["21:30"])
    wake_time: str = Field(examples=["05:00"])
    quality: int | None = Field(default=None, ge=1, le=5)
    noise_level: int | None = Field(default=None, ge=1, le=5)
    interruptions: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=500)


class SleepLogOut(BaseModel):
    id: int
    sleep_date: str
    bedtime: str
    wake_time: str
    duration_hours: float
    quality: int | None
    noise_level: int | None
    interruptions: int
    notes: str | None
    watch_overlap_warning: bool
    crisis_flag: bool
    support: dict | None = None

    class Config:
        from_attributes = True


# ---------- helpers ----------

def _watches(schedule: WatchSchedule) -> list:
    watches = [(sl.to_minutes(schedule.watch1_start), sl.to_minutes(schedule.watch1_end))]
    if schedule.watch2_start and schedule.watch2_end:
        watches.append((sl.to_minutes(schedule.watch2_start), sl.to_minutes(schedule.watch2_end)))
    return watches


def _validate_schedule(payload: WatchScheduleCreate) -> None:
    try:
        w1 = (sl.to_minutes(payload.watch1_start), sl.to_minutes(payload.watch1_end))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if w1[0] == w1[1]:
        raise HTTPException(status_code=422, detail="Watch 1 has zero length.")
    watches = [w1]
    if (payload.watch2_start is None) != (payload.watch2_end is None):
        raise HTTPException(status_code=422, detail="Watch 2 needs both start and end, or neither.")
    if payload.watch2_start and payload.watch2_end:
        try:
            w2 = (sl.to_minutes(payload.watch2_start), sl.to_minutes(payload.watch2_end))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        if w2[0] == w2[1]:
            raise HTTPException(status_code=422, detail="Watch 2 has zero length.")
        if sl.intervals_overlap(w1[0], w1[1], w2[0], w2[1]):
            raise HTTPException(status_code=422, detail="Watch 1 and Watch 2 overlap.")
        watches.append(w2)
    if len(sl.off_duty_windows(watches)) == 0:
        raise HTTPException(status_code=422, detail="Watches cover the full 24h — no rest possible.")


def _active_schedule(db: Session) -> WatchSchedule:
    sched = db.query(WatchSchedule).filter(WatchSchedule.active == 1).first()
    if not sched:
        raise HTTPException(
            status_code=404,
            detail="No active watch schedule. Set one via POST /sleep/watch-schedule first.",
        )
    return sched


def _log_to_out(log: SleepLog, watches: list | None) -> dict:
    overlap = False
    if watches:
        b, w = sl.to_minutes(log.bedtime), sl.to_minutes(log.wake_time)
        overlap = any(sl.intervals_overlap(b, w, ws, we) for ws, we in watches)
    data = {
        "id": log.id,
        "sleep_date": log.sleep_date,
        "bedtime": log.bedtime,
        "wake_time": log.wake_time,
        "duration_hours": sl.sleep_duration_hours(log.bedtime, log.wake_time),
        "quality": log.quality,
        "noise_level": log.noise_level,
        "interruptions": log.interruptions,
        "notes": log.notes,
        "watch_overlap_warning": overlap,
        "crisis_flag": bool(log.crisis_flag),
        "support": crisis_response() if log.crisis_flag else None,
    }
    return data


# ---------- endpoints ----------

@router.post("/watch-schedule", response_model=WatchScheduleOut, status_code=201)
def set_watch_schedule(payload: WatchScheduleCreate, db: Session = Depends(get_db)):
    _validate_schedule(payload)
    db.query(WatchSchedule).filter(WatchSchedule.active == 1).update({"active": 0})
    sched = WatchSchedule(
        name=payload.name,
        watch1_start=payload.watch1_start,
        watch1_end=payload.watch1_end,
        watch2_start=payload.watch2_start,
        watch2_end=payload.watch2_end,
        active=1,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


@router.get("/watch-schedule", response_model=WatchScheduleOut)
def get_watch_schedule(db: Session = Depends(get_db)):
    return _active_schedule(db)


@router.post("/logs", response_model=SleepLogOut, status_code=201)
def log_sleep(payload: SleepLogCreate, db: Session = Depends(get_db)):
    try:
        sl.to_minutes(payload.bedtime)
        sl.to_minutes(payload.wake_time)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    sched = db.query(WatchSchedule).filter(WatchSchedule.active == 1).first()
    watches = _watches(sched) if sched else None
    flagged = scan_for_crisis(payload.notes)
    log = SleepLog(
        sleep_date=payload.sleep_date,
        bedtime=payload.bedtime,
        wake_time=payload.wake_time,
        quality=payload.quality,
        noise_level=payload.noise_level,
        interruptions=payload.interruptions,
        notes=payload.notes,
        crisis_flag=1 if flagged else 0,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return _log_to_out(log, watches)


@router.get("/logs", response_model=list[SleepLogOut])
def list_sleep_logs(limit: int = 50, db: Session = Depends(get_db)):
    sched = db.query(WatchSchedule).filter(WatchSchedule.active == 1).first()
    watches = _watches(sched) if sched else None
    logs = db.query(SleepLog).order_by(SleepLog.sleep_date.desc()).limit(limit).all()
    return [_log_to_out(l, watches) for l in logs]


@router.get("/plan")
def get_sleep_plan(db: Session = Depends(get_db)):
    """Personalized, non-pharmaceutical sleep plan — off-duty hours only."""
    sched = _active_schedule(db)
    watches = _watches(sched)
    recent = db.query(SleepLog).order_by(SleepLog.sleep_date.desc()).limit(14).all()
    noises = [l.noise_level for l in recent if l.noise_level]
    avg_noise = sum(noises) / len(noises) if noises else None
    plan = sl.generate_plan(watches, avg_noise)
    plan["watch_schedule"] = sched.name
    return plan


@router.get("/debt")
def get_sleep_debt(db: Session = Depends(get_db)):
    """7-day sleep debt & fatigue estimate. Wellness estimate, not medical advice."""
    dates = set(sl.last_n_dates(7))
    logs = db.query(SleepLog).filter(SleepLog.sleep_date.in_(dates)).all()
    durations = [sl.sleep_duration_hours(l.bedtime, l.wake_time) for l in logs]
    qualities = [l.quality for l in logs if l.quality]
    return sl.fatigue_summary(durations, qualities)
