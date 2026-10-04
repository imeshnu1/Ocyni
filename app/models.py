"""SQLAlchemy models. All timestamps UTC. No PII beyond what the user writes."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    title = Column(String(200), nullable=True)
    body = Column(Text, nullable=False)
    mood_before = Column(Integer, nullable=True)  # 1-5, optional
    mood_after = Column(Integer, nullable=True)   # 1-5, optional
    tags = Column(String(500), nullable=True)     # comma-separated
    crisis_flag = Column(Integer, default=0)      # 1 if crisis language detected


class MoodCheckIn(Base):
    __tablename__ = "mood_checkins"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    score = Column(Integer, nullable=False)       # 1-5
    note = Column(String(500), nullable=True)


class WatchSchedule(Base):
    """Crew watchkeeping schedule. Up to two watch periods per 24h, HH:MM strings."""
    __tablename__ = "watch_schedules"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    name = Column(String(100), nullable=False)          # e.g. "4/8", "6/6", "custom"
    watch1_start = Column(String(5), nullable=False)    # "HH:MM"
    watch1_end = Column(String(5), nullable=False)
    watch2_start = Column(String(5), nullable=True)
    watch2_end = Column(String(5), nullable=True)
    active = Column(Integer, default=1)                 # 1 = current schedule


class SleepLog(Base):
    """One sleep session, logged in ship-local time."""
    __tablename__ = "sleep_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    sleep_date = Column(String(10), nullable=False)     # YYYY-MM-DD (ship local)
    bedtime = Column(String(5), nullable=False)         # "HH:MM"
    wake_time = Column(String(5), nullable=False)       # "HH:MM"
    quality = Column(Integer, nullable=True)            # 1-5, optional
    noise_level = Column(Integer, nullable=True)        # 1-5, optional (cabin noise)
    interruptions = Column(Integer, default=0)
    notes = Column(String(500), nullable=True)
    crisis_flag = Column(Integer, default=0)


class CopingSession(Base):
    """One guided coping-exercise session (Feature 3)."""
    __tablename__ = "coping_sessions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    exercise_id = Column(String(100), nullable=False)   # slug into coping_exercises
    mood_before = Column(Integer, nullable=False)        # 1-5
    mood_after = Column(Integer, nullable=True)          # 1-5, set on completion
    completed = Column(Integer, default=0)               # 1 when finished
    crisis_flag = Column(Integer, default=0)             # 1 if crisis language detected
