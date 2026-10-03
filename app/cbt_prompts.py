"""Seeded CBT prompt library. Served offline — no network calls, ever."""

PROMPTS = {
    "thought_reframing": {
        "title": "Thought Reframing",
        "description": "Catch an unhelpful thought, examine the evidence, find balance.",
        "prompts": [
            "What happened, in plain facts? Separate what occurred from what it means.",
            "What thought went through your mind right then? Write it exactly.",
            "What evidence supports this thought? What evidence goes against it?",
            "What would you say to a shipmate who had this same thought?",
            "Write a more balanced version of the original thought.",
        ],
    },
    "emotional_grounding": {
        "title": "Emotional Grounding",
        "description": "Come back to the present moment when feelings surge.",
        "prompts": [
            "Name 5 things you can see right now, 4 you can hear, 3 you can touch.",
            "Slow your breathing: in for 4, hold for 4, out for 6. Repeat 4 times.",
            "Where do you feel this emotion in your body? Describe it without judging it.",
            "What is one small thing within your control in the next hour?",
        ],
    },
    "contract_loneliness": {
        "title": "Contract Loneliness",
        "description": "For the ache of being far from home for months.",
        "prompts": [
            "Who are you missing most right now? Write them a few unsent lines.",
            "What is one good memory with them you can hold onto today?",
            "What is one small connection you can make on board today — even a nod?",
            "Your contract has an end date. What is the first thing you'll do home?",
        ],
    },
    "gratitude": {
        "title": "Gratitude Reset",
        "description": "A short reset when the days blur together.",
        "prompts": [
            "Name three things that went right today, however small.",
            "Who on board made your day even slightly better? (No need to tell them.)",
            "What is one thing about this voyage you will actually miss?",
        ],
    },
}


def list_categories() -> list[dict]:
    return [
        {"key": key, "title": value["title"], "description": value["description"]}
        for key, value in PROMPTS.items()
    ]


def get_prompts(category: str) -> dict | None:
    entry = PROMPTS.get(category)
    if not entry:
        return None
    return {
        "key": category,
        "title": entry["title"],
        "description": entry["description"],
        "prompts": entry["prompts"],
    }
