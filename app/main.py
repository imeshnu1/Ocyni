"""Ocyni backend — Feature 1: CBT & Mind-Journaling Hub. Feature 2: Sleep & Circadian Optimizer. Feature 3: Coping Exercises & Guided Bot. Home: Calm Check-In Router."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import init_db
from .routers import cbt, coping, home, journal, mood, sleep


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Ocyni API",
    description=(
        "Seafarer mental health companion — "
        "Feature 1: CBT & Mind-Journaling Hub; "
        "Feature 2: Low-Bandwidth Sleep & Circadian Optimizer; "
        "Feature 3: Coping Exercises & Guided Bot (template-driven, offline); "
        "Home: Calm Check-In Router (conversational routing to the right feature)"
    ),
    version="0.4.0",
    lifespan=lifespan,
)

app.include_router(journal.router)
app.include_router(cbt.router)
app.include_router(mood.router)
app.include_router(sleep.router)
app.include_router(coping.router)
app.include_router(home.router)


@app.get("/", tags=["meta"])
def root():
    return {
        "app": "Ocyni",
        "features": [
            "1 — Offline Interactive CBT & Mind-Journaling Hub",
            "2 — Low-Bandwidth Sleep & Circadian Optimizer",
            "3 — Coping Exercises & Guided Bot (template-driven, offline)",
            "Home — Calm Check-In Router (conversational routing)",
        ],
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
