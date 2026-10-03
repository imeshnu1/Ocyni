"""Ocyni backend — Feature 1: CBT & Mind-Journaling Hub."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import init_db
from .routers import cbt, journal, mood


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Ocyni API",
    description="Seafarer mental health companion — Feature 1: CBT & Mind-Journaling Hub",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(journal.router)
app.include_router(cbt.router)
app.include_router(mood.router)


@app.get("/", tags=["meta"])
def root():
    return {
        "app": "Ocyni",
        "feature": "1 — Offline Interactive CBT & Mind-Journaling Hub",
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
