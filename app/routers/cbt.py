"""CBT endpoints: prompt library + guided thought-reframing session."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..cbt_prompts import get_prompts, list_categories
from ..safety import crisis_response, scan_for_crisis

router = APIRouter(prefix="/cbt", tags=["cbt"])


@router.get("/prompts")
def prompts():
    return {"categories": list_categories()}


@router.get("/prompts/{category}")
def prompts_for_category(category: str):
    result = get_prompts(category)
    if not result:
        raise HTTPException(status_code=404, detail="Unknown prompt category")
    return result


class ReframeRequest(BaseModel):
    situation: str = Field(min_length=1, description="What happened, in plain facts")
    automatic_thought: str = Field(min_length=1, description="The thought that followed")
    emotion: str = Field(min_length=1, description="What you feel, e.g. anger, sadness")
    emotion_intensity: int = Field(ge=1, le=10, description="How strong, 1-10")


@router.post("/reframe")
def guided_reframe(payload: ReframeRequest):
    """Walk the user through a structured thought-reframing exercise.

    Template-driven (no LLM) so it works fully offline and deterministically.
    """
    flagged = any(
        scan_for_crisis(text)
        for text in (payload.situation, payload.automatic_thought, payload.emotion)
    )
    steps = [
        {
            "step": 1,
            "title": "Separate fact from story",
            "instruction": f"You wrote: '{payload.situation}'. Now strip it to just observable facts — what a camera would record.",
        },
        {
            "step": 2,
            "title": "Name the thought",
            "instruction": f"Your automatic thought was: '{payload.automatic_thought}'. Label it: is it catastrophizing, mind-reading, all-or-nothing thinking, or something else?",
        },
        {
            "step": 3,
            "title": "Examine the evidence",
            "instruction": "List two pieces of evidence FOR this thought, and two pieces AGAINST it. Be specific.",
        },
        {
            "step": 4,
            "title": "The shipmate test",
            "instruction": "If a shipmate came to you with this exact thought, what would you honestly tell them?",
        },
        {
            "step": 5,
            "title": "Write the balanced thought",
            "instruction": "Now rewrite the original thought in a more balanced, fair way — not forced positive, just honest.",
        },
        {
            "step": 6,
            "title": "Re-rate",
            "instruction": f"You rated '{payload.emotion}' at {payload.emotion_intensity}/10. After the exercise, rate it again and notice any shift.",
        },
    ]
    response: dict = {"steps": steps, "crisis_flag": flagged, "support": None}
    if flagged:
        response["support"] = crisis_response()
    return response
