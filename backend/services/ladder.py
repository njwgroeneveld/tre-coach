"""Learning ladder, rung 1: one command per lesson.

A lesson has a card (the explanation), column questions and read-the-output situations. Drills are
rebuilt from a seed, so the server never stores a pending drill: the drill id carries the lesson,
the kind and the seed, and grading rebuilds the same drill to know the right answer.

Card content follows Netflix, "Linux Performance Analysis in 60,000 Milliseconds" (2015), and
Brendan Gregg's USE method.
"""

import random

# --- uptime ---------------------------------------------------------------------------------------

UPTIME_CARD = {
    "title": "uptime — how long the host has been up, and its load averages",
    "summary": (
        "The load average is the number of tasks wanting to run. On Linux that includes tasks running "
        "or waiting for a CPU and tasks blocked in uninterruptible I/O (usually disk). It shows how much "
        "demand there is, not where it comes from: worth a quick look only."
    ),
    "example": "23:51:26 up 21:31,  1 user,  load average: 30.02, 26.43, 19.02",
    "fields": [
        {"name": "23:51:26", "meaning": "The current time.", "normal": "—", "alarming": "—"},
        {"name": "up 21:31", "meaning": "Time since the last boot (days, hours:minutes).",
         "normal": "days or weeks",
         "alarming": "a few minutes during an incident → the host rebooted or crashed; find out why"},
        {"name": "1 user", "meaning": "Number of logged-in sessions.", "normal": "—", "alarming": "—"},
        {"name": "load average: 1, 5, 15",
         "meaning": "Average number of tasks running or waiting for a CPU, plus tasks blocked in I/O, "
                    "over the last 1, 5 and 15 minutes.",
         "normal": "below the number of CPUs",
         "alarming": "above the number of CPUs → more demand than the host can serve right now"},
        {"name": "trend (1 min vs 15 min)",
         "meaning": "Compare the 1-minute value with the 15-minute value.",
         "normal": "about equal → steady",
         "alarming": "1 min ≫ 15 min → load is rising, the problem is recent · "
                     "1 min ≪ 15 min → load is falling, you may have logged in too late"},
    ],
    "steps": [
        "Compare the load with the number of CPUs (nproc).",
        "Read the trend: 1-minute against 15-minute.",
        "Remember what uptime cannot tell you: whether the load is CPU or I/O.",
    ],
    "next": "vmstat 1 — its r column (waiting for CPU) and b column (blocked in I/O) tell CPU from I/O. "
            "Also dmesg | tail for anything the kernel logged.",
}

# key_points: what a correct answer must contain. bonus: worth mentioning, never required.
UPTIME_PURPOSE_QUESTIONS = [
    {"question": "What does uptime show you, in one or two sentences?",
     "key_points": ["the load average (over 1, 5 and 15 minutes, or its trend)"],
     "bonus": ["load means how much work wants to run",
               "how long the host has been running since its last boot"]},
    {"question": "When do you run uptime, and why is it only a quick look?",
     "key_points": ["it shows only the overall load or its trend, not what causes it"],
     "bonus": ["you run it first, right after logging in (the first command of the 60-second checklist)",
               "other tools (vmstat) must follow to see whether it is CPU or I/O"]},
    {"question": "Name two things uptime cannot tell you.",
     "key_points": ["a first limitation, for example: whether the load is CPU or I/O, which process causes it, "
                    "which CPU or disk is busy, whether there are errors, what the actual cause is",
                    "a second, different limitation from that same kind of list"]},
]

UPTIME_COLUMN_QUESTIONS = [
    {"question": "What do the three load average numbers represent?",
     "key_points": ["moving averages of load over the last 1, 5 and 15 minutes"]},
    {"question": "On Linux, which two kinds of tasks are counted in the load average?",
     "key_points": ["tasks running or waiting for a CPU (runnable, state R)",
                    "tasks blocked in uninterruptible I/O, usually disk (state D)"]},
    {"question": "How do you decide whether a load average is high?",
     "key_points": ["compare it with the number of CPUs (nproc)",
                    "above the CPU count means more demand than the host can serve"]},
    {"question": "The 1-minute load is much higher than the 15-minute load. What does that tell you?",
     "key_points": ["load is rising", "the problem started recently or is getting worse"]},
    {"question": "The 1-minute load is much lower than the 15-minute load. What does that tell you?",
     "key_points": ["load is falling", "the problem was earlier and is fading; you may have logged in too late"]},
    {"question": "During an incident uptime shows 'up 4 min'. Why does that matter?",
     "key_points": ["the host rebooted or crashed a few minutes ago",
                    "find out why (for example dmesg or the system logs)"]},
    {"question": "The load is three times the CPU count. Can uptime tell you whether the CPU is the "
                 "bottleneck? What do you run next?",
     "key_points": ["no: the load also counts tasks blocked in I/O",
                    "run vmstat 1 and compare r (waiting for CPU) with b (blocked in I/O)"]},
]


def _fmt_load(x: float) -> str:
    return f"{max(x, 0.0):.2f}"


def _uptime_line(rng: random.Random, l1: float, l5: float, l15: float, boot_minutes: int | None = None) -> str:
    clock = f"{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}"
    if boot_minutes is not None:
        up = f"up {boot_minutes} min"
    else:
        up = f"up {rng.randint(2, 180)} days, {rng.randint(0, 23):2d}:{rng.randint(0, 59):02d}"
    users = rng.randint(1, 4)
    user_word = "user" if users == 1 else "users"
    return f" {clock} {up},  {users} {user_word},  load average: {_fmt_load(l1)}, {_fmt_load(l5)}, {_fmt_load(l15)}"


def _uptime_situation(rng: random.Random) -> dict:
    cpus = rng.choice([4, 8, 16, 32])
    kind = rng.choice(["normal", "overloaded", "rising", "too_late", "rebooted"])
    j = lambda: rng.uniform(0.9, 1.1)  # small jitter between the three averages

    if kind == "normal":
        base = rng.uniform(0.1, 0.6) * cpus
        loads = (base * j(), base * j(), base * j())
        key_points = ["the load is below the CPU count and steady",
                      "load is not a problem here; continue the checklist (dmesg, vmstat)"]
    elif kind == "overloaded":
        base = rng.uniform(1.6, 3.0) * cpus
        loads = (base * j(), base * j(), base * rng.uniform(0.85, 1.0))
        key_points = ["the load is well above the CPU count, and has been for at least 15 minutes",
                      "uptime cannot tell whether it is CPU or I/O",
                      "next: vmstat 1, r against b"]
    elif kind == "rising":
        l15 = rng.uniform(0.2, 0.5) * cpus
        l1 = rng.uniform(1.5, 3.0) * cpus
        loads = (l1, (l1 + l15) / 2 * j(), l15)
        key_points = ["the load is rising fast: 1-minute far above 15-minute",
                      "the problem started in the last minutes and the load is now above the CPU count",
                      "CPU or I/O is still unknown: next vmstat 1"]
    elif kind == "too_late":
        l15 = rng.uniform(1.2, 2.5) * cpus
        l1 = rng.uniform(0.1, 0.4) * cpus
        loads = (l1, (l1 + l15) / 2 * j(), l15)
        key_points = ["the load is falling: 1-minute far below 15-minute",
                      "something heavy happened in the last 15 minutes and is now mostly over; "
                      "you may have logged in too late",
                      "look for traces of it, for example dmesg | tail"]
    else:  # rebooted
        base = rng.uniform(0.2, 0.8) * cpus
        loads = (base * j(), base * 0.6 * j(), base * 0.25 * j())
        key_points = ["the host was booted only minutes ago: it rebooted or crashed",
                      "the load says little yet; find out why it rebooted (dmesg, system logs)"]

    boot_minutes = rng.randint(2, 9) if kind == "rebooted" else None
    output = _uptime_line(rng, *loads, boot_minutes=boot_minutes)
    return {
        "situation": kind,
        "prompt": f"The host has {cpus} CPUs. You run `uptime`:",
        "output": output,
        "key_points": key_points,
    }


LESSONS = {
    "uptime": {
        "number": 1,
        "card": UPTIME_CARD,
        "purpose_questions": UPTIME_PURPOSE_QUESTIONS,
        "column_questions": UPTIME_COLUMN_QUESTIONS,
        "situation": _uptime_situation,
    },
}

LESSON_ORDER = ["uptime"]


# --- drills ---------------------------------------------------------------------------------------

def new_drill_id(lesson: str, kind: str) -> str:
    return f"{lesson}.{kind}.{random.randrange(1, 2**31)}"


def build_drill(drill_id: str) -> dict:
    """Rebuild a drill from its id: '<lesson>.<purpose|columns|read>.<seed>'. Raises ValueError on a bad id."""
    try:
        lesson, kind, seed = drill_id.split(".")
        lesson_data = LESSONS[lesson]
        rng = random.Random(int(seed))
    except (ValueError, KeyError) as e:
        raise ValueError(f"Unknown drill: {drill_id}") from e

    # A drill is shown as: context, then output (if any), then the question.
    if kind in ("purpose", "columns"):
        questions = lesson_data["purpose_questions" if kind == "purpose" else "column_questions"]
        q = rng.choice(questions)
        return {"drill_id": drill_id, "lesson": lesson, "kind": kind,
                "context": None, "output": None, "question": q["question"],
                "key_points": q["key_points"], "bonus": q.get("bonus", [])}
    if kind == "read":
        s = lesson_data["situation"](rng)
        return {"drill_id": drill_id, "lesson": lesson, "kind": kind,
                "context": s["prompt"], "output": s["output"], "question": "What do you conclude?",
                "key_points": s["key_points"], "bonus": s.get("bonus", []), "situation": s["situation"]}
    raise ValueError(f"Unknown drill kind: {kind}")


# --- progress -------------------------------------------------------------------------------------

# The three parts of a lesson, in the order the trainee takes them (steps 1-3 of the ladder).
PARTS = ["purpose", "columns", "read"]

MASTERY_NEEDED = 4   # correct answers ...
MASTERY_WINDOW = 5   # ... out of the last this many
CORRECT_SCORE = 7    # a drill with a score of at least this counts as correct

VERDICT_SCORES = {"correct": 10, "partial": 6, "wrong": 2}


def drill_subtopic(lesson: str, kind: str) -> str:
    return f"drill_{lesson}_{kind}"


def all_drill_subtopics() -> list[str]:
    return [drill_subtopic(lesson, kind) for lesson in LESSON_ORDER for kind in PARTS]


def ladder_progress(scores: dict[str, list[int]]) -> list[dict]:
    """Per lesson and part: how far the trainee is and what is unlocked. scores: newest first."""
    lessons = []
    open_ = True  # the first part of the first lesson is always open
    for lesson in LESSON_ORDER:
        lesson_unlocked = open_
        parts = {}
        for kind in PARTS:
            recent = scores.get(drill_subtopic(lesson, kind), [])[:MASTERY_WINDOW]
            correct = sum(1 for s in recent if s >= CORRECT_SCORE)
            mastered = correct >= MASTERY_NEEDED
            parts[kind] = {"correct": correct, "attempts": len(recent), "mastered": mastered, "unlocked": open_}
            # A part opens the next one only once it is mastered.
            open_ = open_ and mastered
        lessons.append({
            "lesson": lesson,
            "number": LESSONS[lesson]["number"],
            "title": LESSONS[lesson]["card"]["title"],
            "unlocked": lesson_unlocked,
            "done": parts["read"]["mastered"],
            **parts,
        })
    return lessons
