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
    {"question": "You have just logged in to a slow server. Why is uptime a good first command?",
     "key_points": ["it gives a quick overview of how much load there is and whether it is rising or falling"],
     "bonus": ["it also shows whether the host rebooted recently"]},
    {"question": "uptime gives three load numbers instead of one. Why is that useful?",
     "key_points": ["comparing them shows the trend: whether the load is rising, falling or steady"]},
    {"question": "After uptime, which command do you run to find out whether the load is CPU or I/O?",
     "key_points": ["vmstat 1"],
     "bonus": ["compare its r column (waiting for CPU) with its b column (blocked in I/O)"]},
    {"question": "Is uptime enough to conclude that a server is healthy? Why or why not?",
     "key_points": ["no",
                    "it only shows the overall load; problems such as errors, one busy CPU, a slow disk or "
                    "network trouble do not show in it"]},
    {"question": "What does the load average tell you that a CPU-usage percentage does not?",
     "key_points": ["the load counts tasks waiting to run, not only how busy the CPUs are"],
     "bonus": ["it also counts tasks blocked in I/O, which use no CPU at all"]},
    {"question": "In one sentence: what is the 'load' that uptime reports?",
     "key_points": ["the number of tasks running or wanting to run"],
     "bonus": ["on Linux it includes tasks blocked in uninterruptible I/O"]},
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
    {"question": "What does 'up 63 days,  2:40' mean in the uptime output?",
     "key_points": ["the host has been running for 63 days, 2 hours and 40 minutes since its last boot"]},
    {"question": "The load average is 4.0 on a host with 4 CPUs. What does that mean?",
     "key_points": ["there is about as much work as there are CPUs: they are fully used, with little or no queue"]},
    {"question": "The load average is 0.5 on a host with 8 CPUs. Is the host busy?",
     "key_points": ["no, it is mostly idle: the load is far below the CPU count"]},
    {"question": "Why can the load average be high while the CPUs are mostly idle?",
     "key_points": ["tasks blocked in I/O (state D) count in the load but use no CPU"],
     "bonus": ["for example many tasks waiting on a slow or saturated disk"]},
    {"question": "The load averages are 8.0, 8.1, 7.9 on a host with 8 CPUs. What do they tell you?",
     "key_points": ["the load has been steady for 15 minutes", "it is at about the CPU count: fully used"]},
    {"question": "How do you find the number of CPUs to compare the load with?",
     "key_points": ["nproc"],
     "bonus": ["or lscpu, or counting the processors in /proc/cpuinfo"]},
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


UPTIME_SITUATIONS = ["normal", "overloaded", "rising", "too_late", "rebooted"]


def _uptime_situation(rng: random.Random, kind: str) -> dict:
    cpus = rng.choice([4, 8, 16, 32])
    j = lambda: rng.uniform(0.9, 1.1)  # small jitter between the three averages

    # key_points: the conclusion itself (required). bonus: the evidence and the next step (tips).
    if kind == "normal":
        base = rng.uniform(0.1, 0.6) * cpus
        loads = (base * j(), base * j(), base * j())
        key_points = ["the load is fine: healthy, not a problem"]
        bonus = ["evidence: it is below the CPU count and steady",
                 "next: continue the checklist (dmesg | tail, vmstat 1)"]
    elif kind == "overloaded":
        base = rng.uniform(1.6, 3.0) * cpus
        loads = (base * j(), base * j(), base * rng.uniform(0.85, 1.0))
        key_points = ["the load is too high: well above the CPU count"]
        bonus = ["it has been like this for at least 15 minutes (all three values are high)",
                 "uptime cannot tell whether it is CPU or I/O",
                 "next: vmstat 1, r against b"]
    elif kind == "rising":
        l15 = rng.uniform(0.2, 0.5) * cpus
        l1 = rng.uniform(1.5, 3.0) * cpus
        loads = (l1, (l1 + l15) / 2 * j(), l15)
        key_points = ["the load is rising, or the problem started recently"]
        bonus = ["evidence: the 1-minute value is far above the 15-minute value",
                 "it is now above the CPU count",
                 "CPU or I/O is still unknown: next vmstat 1"]
    elif kind == "too_late":
        l15 = rng.uniform(1.2, 2.5) * cpus
        l1 = rng.uniform(0.1, 0.4) * cpus
        loads = (l1, (l1 + l15) / 2 * j(), l15)
        key_points = ["the load is falling: the problem was earlier and is mostly over"]
        bonus = ["evidence: the 1-minute value is far below the 15-minute value",
                 "you may have logged in too late",
                 "next: look for traces, for example dmesg | tail"]
    else:  # rebooted
        base = rng.uniform(0.2, 0.8) * cpus
        loads = (base * j(), base * 0.6 * j(), base * 0.25 * j())
        key_points = ["the host rebooted or crashed a few minutes ago"]
        bonus = ["evidence: 'up' shows only minutes",
                 "the load says little yet",
                 "next: find out why it rebooted (dmesg, system logs)"]

    boot_minutes = rng.randint(2, 9) if kind == "rebooted" else None
    output = _uptime_line(rng, *loads, boot_minutes=boot_minutes)
    return {
        "situation": kind,
        "prompt": f"The host has {cpus} CPUs. You run `uptime`:",
        "output": output,
        "key_points": key_points,
        "bonus": bonus,
    }


LESSONS = {
    "uptime": {
        "number": 1,
        "card": UPTIME_CARD,
        "purpose_questions": UPTIME_PURPOSE_QUESTIONS,
        "column_questions": UPTIME_COLUMN_QUESTIONS,
        "situations": UPTIME_SITUATIONS,
        "situation": _uptime_situation,
    },
}

LESSON_ORDER = ["uptime"]


# --- drills ---------------------------------------------------------------------------------------

def _questions(lesson: str, kind: str) -> list[dict]:
    return LESSONS[lesson]["purpose_questions" if kind == "purpose" else "column_questions"]


def new_drill_id(lesson: str, kind: str, asked: list[str], previous_drill_id: str | None = None) -> str:
    """Pick the next drill without repeats.

    Ids: '<lesson>.<purpose|columns>.<question index>' and '<lesson>.read.<situation>.<seed>'.
    asked: question texts the trainee already answered for this part, newest first.
    """
    if kind in ("purpose", "columns"):
        questions = _questions(lesson, kind)
        # The drill just shown counts as asked, even if it was not answered.
        if previous_drill_id and previous_drill_id.startswith(f"{lesson}.{kind}."):
            try:
                asked = [questions[int(previous_drill_id.split(".")[2])]["question"]] + asked
            except (ValueError, IndexError):
                pass
        never = [i for i, q in enumerate(questions) if q["question"] not in asked]
        if never:
            index = random.choice(never)
        else:
            # All seen: take the one seen longest ago.
            last_seen = {q: pos for pos, q in reversed(list(enumerate(asked)))}
            index = max(range(len(questions)), key=lambda i: last_seen.get(questions[i]["question"], -1))
        return f"{lesson}.{kind}.{index}"

    # Read drills get new numbers every time; only avoid the same situation twice in a row.
    situations = list(LESSONS[lesson]["situations"])
    previous = previous_drill_id.split(".")[2] if previous_drill_id and previous_drill_id.count(".") == 3 else None
    choices = [s for s in situations if s != previous] or situations
    return f"{lesson}.read.{random.choice(choices)}.{random.randrange(1, 2**31)}"


def build_drill(drill_id: str) -> dict:
    """Rebuild a drill from its id (see new_drill_id). Raises ValueError on a bad id."""
    parts = drill_id.split(".")
    try:
        lesson, kind = parts[0], parts[1]
        lesson_data = LESSONS[lesson]
        # A drill is shown as: context, then output (if any), then the question.
        if kind in ("purpose", "columns") and len(parts) == 3:
            q = _questions(lesson, kind)[int(parts[2])]
            return {"drill_id": drill_id, "lesson": lesson, "kind": kind,
                    "context": None, "output": None, "question": q["question"],
                    "key_points": q["key_points"], "bonus": q.get("bonus", [])}
        if kind == "read" and len(parts) == 4 and parts[2] in lesson_data["situations"]:
            s = lesson_data["situation"](random.Random(int(parts[3])), parts[2])
            return {"drill_id": drill_id, "lesson": lesson, "kind": kind,
                    "context": s["prompt"], "output": s["output"], "question": "What do you conclude?",
                    "key_points": s["key_points"], "bonus": s.get("bonus", []), "situation": s["situation"]}
    except (ValueError, KeyError, IndexError) as e:
        raise ValueError(f"Unknown drill: {drill_id}") from e
    raise ValueError(f"Unknown drill: {drill_id}")


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
