"""Safety layer: crisis-language detection and resources.

This is a FIRST-PASS heuristic, not clinical detection. It exists so the app
never stays silent when someone may be in danger. Any match must surface
resources immediately; imminent danger must escalate to the proper authority
per vessel protocol — the app must not try to handle that alone.
"""

CRISIS_KEYWORDS = [
    "kill myself",
    "suicide",
    "suicidal",
    "end my life",
    "don't want to live",
    "dont want to live",
    "hurt myself",
    "self harm",
    "self-harm",
    "harm myself",
    "no reason to live",
]

SUPPORT_RESOURCES = [
    {
        "name": "US Suicide & Crisis Lifeline",
        "contact": "Call or text 988 (US)",
    },
    {
        "name": "ISWAN SeafarerHelp",
        "contact": "https://www.seafarerhelp.org — free, multilingual, confidential",
    },
    {
        "name": "Samaritans",
        "contact": "Call 116 123 (UK & Ireland)",
    },
]


def scan_for_crisis(text: str) -> bool:
    """Return True if crisis language is detected in the given text."""
    lowered = (text or "").lower()
    return any(keyword in lowered for keyword in CRISIS_KEYWORDS)


def crisis_response() -> dict:
    """Payload attached to any response where crisis language was detected."""
    return {
        "crisis_flag": True,
        "message": (
            "It sounds like you might be going through something really difficult. "
            "You don't have to face it alone — please reach out right now:"
        ),
        "resources": SUPPORT_RESOURCES,
    }
