"""Lesson 4: mpstat -P ALL 1 — CPU time per CPU."""

import random

from services.lessons.common import ampm, clock, host, sysstat_header

COMMAND = "mpstat -P ALL 1"

CARD = {
    "title": "mpstat -P ALL 1 — how busy each CPU is, every second",
    "summary": (
        "mpstat breaks CPU time down per CPU (-P ALL), one report per second. The 'all' row is the average "
        "over all CPUs; the numbered rows are each CPU. Use it to spot an imbalance: a single hot CPU can be a "
        "single-threaded application, or interrupt work landing on one core."
    ),
    "example": (
        "07:38:49 PM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle\n"
        "07:38:50 PM  all   98.47    0.00    0.75    0.00    0.00    0.00    0.00    0.00    0.00    0.78\n"
        "07:38:50 PM    0   96.04    0.00    2.97    0.00    0.00    0.00    0.00    0.00    0.00    0.99\n"
        "07:38:50 PM    1   97.00    0.00    1.00    0.00    0.00    0.00    0.00    0.00    0.00    2.00"
    ),
    "fields": [
        {"name": "CPU", "meaning": "'all' is the average over every CPU; a number is one CPU (core or hardware thread).",
         "normal": "—", "alarming": "—"},
        {"name": "%usr", "meaning": "% time running applications (user space).",
         "normal": "depends on the load",
         "alarming": "one CPU near 100 while the rest is idle → a single-threaded bottleneck"},
        {"name": "%sys", "meaning": "% time in the kernel.", "normal": "low",
         "alarming": "high → kernel work: system calls, I/O"},
        {"name": "%iowait", "meaning": "% idle while waiting for disk I/O.", "normal": "0",
         "alarming": "high → a disk bottleneck"},
        {"name": "%irq", "meaning": "% time handling hardware interrupts.", "normal": "near 0",
         "alarming": "high on one CPU → interrupts all land on that core"},
        {"name": "%soft", "meaning": "% time handling software interrupts, mostly network packet processing.",
         "normal": "low",
         "alarming": "high on one CPU → network traffic processed on one core; anything else on that core suffers"},
        {"name": "%steal", "meaning": "% time stolen by other virtual machines.", "normal": "0",
         "alarming": "above 0 → a noisy neighbour on the hypervisor"},
        {"name": "%idle", "meaning": "% time idle.", "normal": "—",
         "alarming": "near 0 on every CPU → all CPUs busy (check vmstat r for saturation)"},
    ],
    "steps": [
        "Read the 'all' row: how busy is the host on average?",
        "Compare the CPUs with each other: balanced, or is one CPU very different?",
        "For the busy CPUs, see where the time goes: %usr, %sys, %iowait or %soft.",
    ],
    "next": "A hot CPU in %usr → pidstat 1 to find the process · %soft on one CPU → network interrupts "
            "(sar -n DEV 1) · %iowait → iostat -xz 1.",
}

PURPOSE_QUESTIONS = [
    {"question": "What does mpstat -P ALL 1 show you?",
     "key_points": ["how CPU time is spent per CPU, every second"],
     "bonus": ["plus an 'all' row with the average"]},
    {"question": "What does mpstat show that vmstat does not?",
     "key_points": ["the breakdown per CPU instead of only the average over all CPUs"]},
    {"question": "What does -P ALL mean?",
     "key_points": ["show every CPU separately (and the average)"]},
    {"question": "Why is a per-CPU view useful when total CPU usage looks low?",
     "key_points": ["one CPU can be at 100% while the average looks low"],
     "bonus": ["for example a single-threaded application"]},
    {"question": "What is a 'single hot CPU' evidence of?",
     "key_points": ["a single-threaded application (or work that can only run on one core)"]},
    {"question": "When in the checklist do you run mpstat?",
     "key_points": ["after vmstat, to see how the CPU load is spread over the CPUs"]},
    {"question": "Can mpstat tell you which process is busy?",
     "key_points": ["no; pidstat or top show processes"]},
    {"question": "Why does a trading host care about %soft on one CPU?",
     "key_points": ["network packet processing on that core takes time away from what else runs there, adding latency"]},
]

COLUMN_QUESTIONS = [
    {"question": "What does the 'all' row in mpstat mean?",
     "key_points": ["the average over all CPUs"]},
    {"question": "What does %usr measure?",
     "key_points": ["% time spent running applications (user space)"]},
    {"question": "What does %sys measure?",
     "key_points": ["% time spent in the kernel"]},
    {"question": "What does %iowait measure?",
     "key_points": ["% time the CPU is idle while waiting for disk I/O"]},
    {"question": "What does %soft measure?",
     "key_points": ["% time handling software interrupts, mostly network packet processing"]},
    {"question": "What does %irq measure?",
     "key_points": ["% time handling hardware interrupts"]},
    {"question": "What does %steal measure?",
     "key_points": ["% time stolen by other virtual machines on the same hypervisor"]},
    {"question": "CPU 3 shows %usr 99 and the other CPUs about 10. What does that suggest?",
     "key_points": ["a single-threaded process is using all of CPU 3: a single-thread bottleneck"]},
    {"question": "CPU 0 shows %soft 85 while the others are near 0. What does that suggest?",
     "key_points": ["network interrupt work all lands on CPU 0"]},
    {"question": "Every CPU shows %idle near 0. Is the host saturated?",
     "key_points": ["all CPUs are busy, but saturation means a queue: check vmstat's r against the CPU count"]},
    {"question": "The 'all' row shows %usr 12. Can a CPU still be at 100%?",
     "key_points": ["yes: the average hides one busy CPU among many idle ones"]},
]

SITUATIONS = ["balanced_idle", "balanced_busy", "hot_cpu", "soft_irq", "iowait"]


def _row(t: str, cpu: str, usr, sys_, iowait, irq, soft) -> str:
    idle = max(0.0, 100 - usr - sys_ - iowait - irq - soft)
    vals = [usr, 0.0, sys_, iowait, irq, soft, 0.0, 0.0, 0.0, idle]
    return f"{t}  {cpu:>3} " + " ".join(f"{v:7.2f}" for v in vals)


def situation(rng: random.Random, kind: str) -> dict:
    cpus = rng.choice([4, 8])
    hostname = host(rng)
    h, m, s = clock(rng)
    t = ampm(h, m, s + 1)
    hot = rng.randrange(cpus)
    per_cpu = []
    for c in range(cpus):
        if kind == "balanced_idle":
            v = (rng.uniform(2, 12), rng.uniform(0.5, 3), rng.uniform(0, 0.5), 0, rng.uniform(0, 0.5))
        elif kind == "balanced_busy":
            v = (rng.uniform(90, 97), rng.uniform(1, 4), 0, 0, rng.uniform(0, 0.5))
        elif kind == "hot_cpu":
            v = (rng.uniform(97, 99.5), rng.uniform(0.3, 1.5), 0, 0, 0) if c == hot else \
                (rng.uniform(4, 15), rng.uniform(1, 3), 0, 0, rng.uniform(0, 0.5))
        elif kind == "soft_irq":
            v = (rng.uniform(5, 12), rng.uniform(2, 5), 0, rng.uniform(0.5, 2), rng.uniform(70, 88)) if c == hot else \
                (rng.uniform(5, 15), rng.uniform(1, 3), 0, 0, rng.uniform(0, 1))
        else:  # iowait
            v = (rng.uniform(2, 6), rng.uniform(1, 4), rng.uniform(40, 70), 0, rng.uniform(0, 0.5))
        per_cpu.append(v)
    avg = tuple(sum(v[i] for v in per_cpu) / cpus for i in range(5))
    header = f"{t}  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle"
    rows = [_row(t, "all", *avg)] + [_row(t, str(c), *v) for c, v in enumerate(per_cpu)]
    output = "\n".join([sysstat_header(rng, hostname, cpus), "", header] + rows)

    if kind == "balanced_idle":
        key_points = ["the CPUs are mostly idle and evenly loaded: no CPU problem"]
        bonus = ["no single hot CPU, no %iowait, no %soft", "next: continue the checklist"]
    elif kind == "balanced_busy":
        key_points = ["all CPUs are busy, evenly, almost all in %usr (applications)"]
        bonus = ["the load is spread well: no single-thread bottleneck",
                 "whether it is saturated: check vmstat's r", "next: pidstat 1 to find the process"]
    elif kind == "hot_cpu":
        key_points = [f"one CPU (CPU {hot}) is at about 100% %usr while the others are mostly idle"]
        bonus = ["a single-threaded process is the bottleneck", "the 'all' average hides it",
                 "next: pidstat 1 (or pidstat -t) to find the thread on that CPU"]
    elif kind == "soft_irq":
        key_points = [f"CPU {hot} spends most of its time in %soft: network interrupt work lands on one core"]
        bonus = ["anything else running on that core gets less CPU and more latency",
                 "next: sar -n DEV 1 for the traffic; spread the interrupts over cores"]
    else:
        key_points = ["the CPUs are mostly waiting for disk I/O (%iowait high on every CPU)"]
        bonus = ["the CPUs themselves are not busy", "next: iostat -xz 1 to find the disk"]

    return {
        "situation": kind,
        "prompt": f"The host has {cpus} CPUs. You run `mpstat -P ALL 1` (one report shown):",
        "output": output,
        "key_points": key_points,
        "bonus": bonus,
    }
