"""Seeded coping-exercise library for Feature 3.

Template-driven (no LLM) so everything works fully offline and
deterministically. Each exercise is short (max 20 minutes) and carries a
maritime_note tying it to ship life.

Step format: {"title": ..., "instruction": ...}
"""

EXERCISES = {
    "box-breathing": {
        "id": "box-breathing",
        "title": "Box Breathing",
        "category": "breathing",
        "duration_minutes": 5,
        "maritime_note": "Used by divers and bridge crews to steady nerves before a tricky maneuver.",
        "steps": [
            {
                "title": "Get settled",
                "instruction": "Sit upright with both feet flat, hands resting in your lap. Let your shoulders drop.",
            },
            {
                "title": "Breathe in — 4 counts",
                "instruction": "Inhale slowly through your nose for 4 counts. Feel your belly expand, not your chest.",
            },
            {
                "title": "Hold — 4 counts",
                "instruction": "Hold the breath for 4 counts. Keep your face and jaw relaxed.",
            },
            {
                "title": "Breathe out — 4 counts",
                "instruction": "Exhale slowly through your mouth for 4 counts, like fogging a mirror.",
            },
            {
                "title": "Hold empty — 4 counts",
                "instruction": "Rest with empty lungs for 4 counts before the next inhale.",
            },
            {
                "title": "Repeat the box",
                "instruction": "Run the full box 4 more times. Notice your heart rate settling with each round.",
            },
        ],
    },
    "4-7-8-breathing": {
        "id": "4-7-8-breathing",
        "title": "4-7-8 Calming Breath",
        "category": "breathing",
        "duration_minutes": 6,
        "maritime_note": "A fast way to downshift after a tense watch handover or a rough call home.",
        "steps": [
            {
                "title": "Settle and exhale",
                "instruction": "Sit comfortably. Exhale completely through your mouth with a soft whoosh.",
            },
            {
                "title": "Inhale — 4 counts",
                "instruction": "Close your mouth and inhale quietly through your nose for 4 counts.",
            },
            {
                "title": "Hold — 7 counts",
                "instruction": "Hold your breath for 7 counts. This is where the calm builds — stay with it.",
            },
            {
                "title": "Exhale — 8 counts",
                "instruction": "Exhale fully through your mouth for 8 counts, slow and controlled.",
            },
            {
                "title": "Three full cycles",
                "instruction": "Repeat the 4-7-8 cycle three more times. If you feel lightheaded, breathe normally for a minute first.",
            },
            {
                "title": "Notice the shift",
                "instruction": "Sit quietly for 30 seconds. Rate your tension 1–10 now versus when you started.",
            },
        ],
    },
    "five-senses-grounding": {
        "id": "five-senses-grounding",
        "title": "5-4-3-2-1 Grounding",
        "category": "grounding",
        "duration_minutes": 5,
        "maritime_note": "Anchors you when your mind races during a long night watch or in a rolling sea.",
        "steps": [
            {
                "title": "5 — See",
                "instruction": "Name 5 things you can see right now. Say each one slowly, out loud if you can.",
            },
            {
                "title": "4 — Touch",
                "instruction": "Notice 4 things you can feel: the rail under your hand, your boots on deck, the fabric of your sleeve.",
            },
            {
                "title": "3 — Hear",
                "instruction": "Pick out 3 sounds: the engine hum, wind, water against the hull. Just listen, don't judge.",
            },
            {
                "title": "2 — Smell",
                "instruction": "Notice 2 smells around you — salt air, coffee, oil, rain. Breathe them in.",
            },
            {
                "title": "1 — Taste",
                "instruction": "Notice 1 taste in your mouth right now. Take a sip of water and feel it fully.",
            },
            {
                "title": "Arrive",
                "instruction": "You are here, on this ship, in this moment — not in the worry. Notice that your breathing has slowed.",
            },
        ],
    },
    "progressive-muscle-relaxation": {
        "id": "progressive-muscle-relaxation",
        "title": "Progressive Muscle Relaxation",
        "category": "muscle-relaxation",
        "duration_minutes": 12,
        "maritime_note": "Releases the tension that builds in shoulders, neck, and back over long watches.",
        "steps": [
            {
                "title": "Prepare",
                "instruction": "Sit or lie down somewhere you won't be disturbed for 12 minutes. Unclench your jaw.",
            },
            {
                "title": "Hands and forearms",
                "instruction": "Clench both fists hard for 5 seconds, then release. Notice the warmth spreading through your hands.",
            },
            {
                "title": "Shoulders",
                "instruction": "Shrug your shoulders up to your ears and hold 5 seconds. Drop them and feel the release.",
            },
            {
                "title": "Face",
                "instruction": "Scrunch your whole face tight for 5 seconds, then let it go slack. Let your tongue drop from the roof of your mouth.",
            },
            {
                "title": "Chest and belly",
                "instruction": "Take a deep breath and tighten your chest and stomach for 5 seconds, then exhale and soften completely.",
            },
            {
                "title": "Legs and feet",
                "instruction": "Tense your thighs, calves, and curl your toes for 5 seconds, then release. Feel the weight of your legs.",
            },
            {
                "title": "Full-body scan",
                "instruction": "Slowly scan from head to toe. Wherever you find leftover tension, breathe into it and let it soften on the exhale.",
            },
        ],
    },
    "cabin-wind-down": {
        "id": "cabin-wind-down",
        "title": "Cabin Wind-Down",
        "category": "wind-down",
        "duration_minutes": 10,
        "maritime_note": "Built for thin cabin walls and engine hum — helps you fall asleep while off-watch.",
        "steps": [
            {
                "title": "Dim and quiet",
                "instruction": "Turn off the overhead light; use only a dim lamp or your phone at lowest brightness. Put in earplugs if engine noise bothers you.",
            },
            {
                "title": "Slow the breath",
                "instruction": "Breathe in for 4, out for 6, for two minutes. Longer exhales tell your body the watch is over.",
            },
            {
                "title": "Body scan",
                "instruction": "Starting at your feet, move attention slowly upward, softening each area. Don't rush — give each part one full breath.",
            },
            {
                "title": "Park tomorrow",
                "instruction": "Write down anything on your mind for tomorrow — duties, worries, messages. The list holds it so you don't have to.",
            },
            {
                "title": "Lights out",
                "instruction": "Lights off. If thoughts come, label them 'thinking' and return to the breath. No screens from here.",
            },
        ],
    },
    "anger-cool-down": {
        "id": "anger-cool-down",
        "title": "Cool Down After Conflict",
        "category": "anger-cooling",
        "duration_minutes": 8,
        "maritime_note": "For the flare-ups that happen in close quarters — cool it before it festers for the rest of the voyage.",
        "steps": [
            {
                "title": "Pause",
                "instruction": "Step away if you safely can — the passageway, the deck, anywhere with air. Do not reply or react yet.",
            },
            {
                "title": "Slow exhale",
                "instruction": "Exhale longer than you inhale for one minute: in 4, out 8. Anger lives in a fast body; slow the body first.",
            },
            {
                "title": "Name it precisely",
                "instruction": "Say exactly what you're feeling: 'I feel disrespected because…' Vague anger grows; named anger shrinks.",
            },
            {
                "title": "The 10-10-10 test",
                "instruction": "Ask: will this matter in 10 minutes? 10 days? 10 months? Most shipboard clashes fail the 10-day test.",
            },
            {
                "title": "Plan the repair",
                "instruction": "Decide one concrete, calm thing you'll say or do next — an apology, a clarification, or simply letting it go. Write it down.",
            },
        ],
    },
    "letter-home-unsent": {
        "id": "letter-home-unsent",
        "title": "Unsent Letter Home",
        "category": "loneliness",
        "duration_minutes": 10,
        "maritime_note": "For contract loneliness — say it on paper now, say it in person when you're home.",
        "steps": [
            {
                "title": "Choose who",
                "instruction": "Pick the person you're missing most right now. Picture their face clearly.",
            },
            {
                "title": "Three honest lines",
                "instruction": "Write three lines you'd say if they were sitting across from you. No editing, no performing.",
            },
            {
                "title": "One good memory",
                "instruction": "Write down one specific good memory with them — where you were, what you laughed about, what it smelled like.",
            },
            {
                "title": "One thing ahead",
                "instruction": "Write one thing you'll do together when the contract ends. Make it concrete: a meal, a walk, a place.",
            },
            {
                "title": "Seal it",
                "instruction": "Fold it away or save it in the app. You've said it — the feeling has somewhere to live now, not just in your chest.",
            },
        ],
    },
    "shipmate-micro-connection": {
        "id": "shipmate-micro-connection",
        "title": "Shipmate Micro-Connection",
        "category": "loneliness",
        "duration_minutes": 5,
        "maritime_note": "Small bridges beat big loneliness — one real moment with someone on board today.",
        "steps": [
            {
                "title": "Pick a person",
                "instruction": "Think of one crew member you haven't really talked to lately — messmate, watch partner, anyone.",
            },
            {
                "title": "One genuine question",
                "instruction": "Ask them one real question today: where they're from, what they miss, what they did before sea. Not small talk — one real question.",
            },
            {
                "title": "Listen fully",
                "instruction": "Give them your full attention for two minutes. No phone, no glancing away. People can tell.",
            },
            {
                "title": "Follow up once",
                "instruction": "Tomorrow, reference one thing they said. That's it — a thread of connection started.",
            },
        ],
    },
}

CATEGORIES = sorted({e["category"] for e in EXERCISES.values()})


def list_exercises(category: str | None = None) -> list[dict]:
    """Lightweight summaries for listing. Full detail via get_exercise()."""
    items = EXERCISES.values()
    if category is not None:
        items = [e for e in items if e["category"] == category]
    return [
        {
            "id": e["id"],
            "title": e["title"],
            "category": e["category"],
            "duration_minutes": e["duration_minutes"],
        }
        for e in items
    ]


def get_exercise(exercise_id: str) -> dict | None:
    return EXERCISES.get(exercise_id)


def valid_category(category: str) -> bool:
    return category in CATEGORIES
