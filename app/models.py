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
