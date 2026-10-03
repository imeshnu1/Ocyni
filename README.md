# Ocyni — Seafarer Mental Health Companion

Backend API for the Ocyni MVP. Built offline-first for life at sea.

## Feature 1 (this scaffold): Offline Interactive CBT & Mind-Journaling Hub

A private journaling API with structured Cognitive Behavioral Therapy prompts —
thought reframing, emotional grounding — plus mood check-ins. All data stays
on-device by default (SQLite); sync is opt-in.

### Safety rules (apply to every feature)

1. **No addiction design** — the API supports session limits; clients must not
   build endless-engagement loops.
2. **A tool, not a replacement** — the API encourages real human connection;
   it never substitutes for buddies, family, or counselors.
3. **Harm response matched to risk** — journal/reframe inputs are scanned for
   crisis language. On a match, the response includes crisis resources
   (988, ISWAN SeafarerHelp) and a `crisis_flag`. This is a first-pass
   heuristic, NOT clinical detection. Imminent danger must always escalate
   to the proper authority per vessel protocol.

## Quickstart (Mac mini)

```bash
cd ~/ocyni-backend   # or wherever you cloned this repo
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## API overview

| Method | Path | Description |
|---|---|---|
| POST | /journal/entries | Create a journal entry (crisis scan applied) |
| GET | /journal/entries | List entries, newest first |
| GET | /journal/entries/{id} | Get one entry |
| GET | /cbt/prompts | List CBT prompt categories |
| GET | /cbt/prompts/{category} | Prompts for a category |
| POST | /cbt/reframe | Guided thought-reframing session |
| POST | /mood/checkin | Log a 1–5 mood check-in |
| GET | /mood/history | Check-in history |

## Roadmap (the 10-feature MVP)

1. ✅ CBT & Mind-Journaling Hub (this scaffold)
2. Sleep & Circadian Optimizer
3. Offline AI Coping Bot
4. Panic / Grounding SOS Mode
5. Shipmate Buddy Check-In
6. Async Text Counselor Line
7. Offline Family Messaging Queue
8. Anonymous Ombudsperson Hub
9. Corporate Wellness Dashboard
10. Leadership Micro-Learning Prompts

See `../ocyni-white-paper.md` (goal workspace) for the full product spec.
