"""Pure logic for the Sleep & Circadian Optimizer.

SAFETY INVARIANT: recommended sleep windows are ALWAYS strictly inside
off-duty periods. Watch hours are NEVER suggested for sleep. This protects
both the crew member's rest and the vessel's safe operation.
"""
import re
from datetime import date, timedelta

HHMM = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

TARGET_SLEEP_HOURS = 7.0
CAFFEINE_CUTOFF_HOURS_BEFORE_BED = 6
WIND_DOWN_MINUTES = 30   # buffer after watch ends before sleep starts
WAKE_BUFFER_MINUTES = 30  # buffer to be up before next watch starts


def to_minutes(hhmm: str) -> int:
    m = HHMM.match(hhmm or "")
    if not m:
        raise ValueError(f"Bad time format: {hhmm!r} (expected HH:MM, 24h)")
    return int(m.group(1)) * 60 + int(m.group(2))


def to_hhmm(minutes: int) -> str:
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _expand(start: int, end: int) -> set:
    """Minutes covered by [start, end); handles overnight wrap."""
    mins = set()
    cur = start
    while cur != end:
        mins.add(cur)
        cur = (cur + 1) % 1440
        if len(mins) > 1440:
            break
    return mins


def intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return bool(_expand(a_start, a_end) & _expand(b_start, b_end))


def off_duty_windows(watches: list) -> list:
    """Complement of watch intervals over the 24h clock.

    Returns (start_min, end_min) pairs; end may exceed 1440 for windows
    crossing midnight. Windows tile the full day.
    """
    on_watch = set()
    for s, e in watches:
        on_watch |= _expand(s, e)
    windows = []
    cur = None
    for m in range(0, 2880):
        minute = m % 1440
        if minute not in on_watch:
            if cur is None:
                cur = m
        elif cur is not None:
            windows.append((cur, m))
            cur = None
    if cur is not None:
        windows.append((cur, 2880))
    return [(s, e) for s, e in windows if s < 1440]


def sleep_duration_hours(bedtime: str, wake_time: str) -> float:
    b, w = to_minutes(bedtime), to_minutes(wake_time)
    return round(((w - b) % 1440) / 60, 2)


def last_n_dates(n: int = 7) -> list:
    today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(n)]


WIND_DOWN_ROUTINE = [
    "Dim the cabin lights (or put on an eye mask) 30 minutes before bed.",
    "4-7-8 breathing: inhale 4s, hold 7s, exhale 8s — repeat 4 rounds.",
    "Unclench jaw, drop shoulders, relax each muscle group head to toe.",
    "If thoughts race, name 3 things you can hear in the cabin right now.",
    "No screens once you're in the bunk — the phone stays face-down.",
]


def generate_plan(watches: list, avg_noise: float | None) -> dict:
    """Build a sleep hygiene plan. Sleep is only ever placed off-watch."""
    windows = off_duty_windows(watches)
    no_sleep_zones = [f"{to_hhmm(s)}–{to_hhmm(e)} — ON WATCH, do not sleep" for s, e in watches]

    if not windows:
        return {
            "sleep_window": None,
            "note": "Your watches cover the full 24 hours — no consolidated sleep window exists. "
                    "Talk to your chief officer about rest-hour compliance (MLC 2006).",
            "no_sleep_zones": no_sleep_zones,
            "safety_notice": "Never sleep on watch. This plan only uses off-duty hours.",
        }

    # Primary window = longest off-duty stretch
    p_start, p_end = max(windows, key=lambda w: w[1] - w[0])
    p_len = p_end - p_start
    sleep_start = p_start + WIND_DOWN_MINUTES
    max_sleep_min = p_len - WIND_DOWN_MINUTES - WAKE_BUFFER_MINUTES

    secondary = [
        {"start": to_hhmm(s), "end": to_hhmm(e), "hours": round((e - s) / 60, 1)}
        for s, e in sorted(windows, key=lambda w: w[1] - w[0])[1:3]
    ]

    if max_sleep_min < 60:
        strategy = (
            "Your off-duty gaps are short — use strategic naps of 20–30 minutes "
            "inside these gaps. Set an alarm; never nap into your next watch."
        )
        sleep_window = None
    else:
        sleep_hours = min(TARGET_SLEEP_HOURS, max_sleep_min / 60)
        sleep_end = sleep_start + int(sleep_hours * 60)
        strategy = None
        sleep_window = {
            "start": to_hhmm(sleep_start),
            "end": to_hhmm(sleep_end),
            "hours": round(sleep_hours, 1),
        }

    anchor = sleep_window["start"] if sleep_window else to_hhmm(p_start + WIND_DOWN_MINUTES)
    wake = sleep_window["end"] if sleep_window else to_hhmm(p_end - WAKE_BUFFER_MINUTES)
    caffeine_cutoff = to_hhmm(to_minutes(anchor) - CAFFEINE_CUTOFF_HOURS_BEFORE_BED * 60)

    noise_tip = None
    if avg_noise is not None and avg_noise >= 4:
        noise_tip = ("Your cabin noise scores are high — earplugs or a steady fan/white-noise "
                     "sound can mask intermittent ship noise. Keep the mask/earplugs by your bunk.")

    return {
        "sleep_window": sleep_window,
        "strategy": strategy,
        "secondary_nap_gaps": secondary,
        "caffeine_cutoff": f"No caffeine after {caffeine_cutoff} (6h before your sleep window).",
        "light_guidance": (
            f"Get bright light (daylight or bright indoor light) within an hour after waking "
            f"({wake}). Dim lights and avoid screens for the last hour before {anchor}."
        ),
        "wind_down_routine": WIND_DOWN_ROUTINE,
        "noise_tip": noise_tip,
        "no_sleep_zones": no_sleep_zones,
        "safety_notice": "Never sleep on watch. This plan only uses your off-duty hours.",
    }


def fatigue_summary(durations: list, qualities: list) -> dict:
    """Wellness estimate only — not medical advice."""
    avg_dur = round(sum(durations) / len(durations), 1) if durations else 0.0
    avg_q = round(sum(qualities) / len(qualities), 1) if qualities else None
    debt = round(max(0.0, TARGET_SLEEP_HOURS - avg_dur), 1)
    if debt >= 2 or (avg_q is not None and avg_q <= 2):
        band = "high"
    elif debt >= 1 or (avg_q is not None and avg_q <= 3):
        band = "moderate"
    else:
        band = "low"
    return {
        "days_logged": len(durations),
        "avg_sleep_hours": avg_dur,
        "avg_quality": avg_q,
        "sleep_debt_hours_per_night": debt,
        "fatigue_band": band,
        "disclaimer": "Wellness estimate only — not medical advice. If fatigue affects your watch, tell your officer.",
    }
