"""Lesson 3: vmstat 1 — a one-line summary of the whole system, every second."""

import random

from services.lessons.common import split_percent

COMMAND = "vmstat 1"

CARD = {
    "title": "vmstat 1 — a summary of the whole system, one line per second",
    "summary": (
        "vmstat prints CPU, memory, swap and I/O activity for the whole system, one line every second. "
        "It answers three questions fast: is the CPU saturated, are tasks waiting on I/O, is the host swapping? "
        "Skip the first line: it shows averages since boot, not the last second."
    ),
    "example": (
        "procs ---------memory---------- ---swap-- -----io---- -system-- ------cpu-----\n"
        " r  b swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st\n"
        "34  0    0 200889792  73708 591828    0    0     0     5    6   10 96  1  3  0  0\n"
        "32  0    0 200889920  73708 591860    0    0     0   592 13284 4282 98  1  1  0  0\n"
        "32  0    0 200890112  73708 591860    0    0     0     0 9501 2154 99  1  0  0  0"
    ),
    "fields": [
        {"name": "r", "meaning": "Tasks running on a CPU or waiting for one.",
         "normal": "below the CPU count",
         "alarming": "above the CPU count → CPU saturation (a better signal than load: it excludes I/O)"},
        {"name": "b", "meaning": "Tasks blocked in uninterruptible I/O (state D).",
         "normal": "0",
         "alarming": "above 0 for several seconds → tasks waiting on disk (or network storage)"},
        {"name": "swpd", "meaning": "Swap space in use, in KB.",
         "normal": "0, or a constant amount",
         "alarming": "growing → memory is being pushed to swap"},
        {"name": "free", "meaning": "Free memory in KB.",
         "normal": "\"too many digits to count\"",
         "alarming": "small → look at free -m: available memory matters more"},
        {"name": "buff / cache", "meaning": "Memory used for disk buffers and the page cache.",
         "normal": "large: Linux uses spare memory for cache",
         "alarming": "near zero → more disk I/O"},
        {"name": "si / so", "meaning": "Swap-ins and swap-outs per second.",
         "normal": "0",
         "alarming": "not 0 → out of memory: the host is swapping"},
        {"name": "bi / bo", "meaning": "Blocks read from (bi) and written to (bo) disk per second.",
         "normal": "depends on the workload",
         "alarming": "very high together with b and wa → heavy disk load"},
        {"name": "in / cs", "meaning": "Interrupts and context switches per second.",
         "normal": "depends on the workload",
         "alarming": "very high cs with high sy → the kernel is busy switching tasks"},
        {"name": "us", "meaning": "% CPU time in user space: applications.",
         "normal": "depends on the load",
         "alarming": "us + sy near 100 → the CPUs are busy"},
        {"name": "sy", "meaning": "% CPU time in the kernel (system).",
         "normal": "low",
         "alarming": "above 20% → the kernel works hard (I/O, interrupts, context switches)"},
        {"name": "id", "meaning": "% CPU idle.", "normal": "—", "alarming": "—"},
        {"name": "wa", "meaning": "% CPU idle while tasks wait for disk I/O.",
         "normal": "0",
         "alarming": "steady wa → disk bottleneck (\"another form of idle, with a clue why\")"},
        {"name": "st", "meaning": "% CPU stolen by other virtual machines on the same hypervisor.",
         "normal": "0",
         "alarming": "above 0 → a noisy neighbour takes CPU from this VM"},
    ],
    "steps": [
        "Skip the first line (averages since boot).",
        "r against the CPU count → is the CPU saturated?",
        "b and wa → are tasks waiting on I/O?",
        "si / so → is the host swapping?",
        "us + sy → how busy are the CPUs, and is sy unusually high?",
    ],
    "next": "CPU busy → mpstat -P ALL 1 and pidstat 1 · I/O wait → iostat -xz 1 · swapping → free -m.",
}

PURPOSE_QUESTIONS = [
    {"question": "What does vmstat 1 show you?",
     "key_points": ["a one-line summary of the whole system every second: CPU, memory, swap and I/O"]},
    {"question": "Why do you skip the first line of vmstat output?",
     "key_points": ["it shows averages since boot, not the last second"]},
    {"question": "What does the 1 in 'vmstat 1' mean?",
     "key_points": ["print a new line every second"]},
    {"question": "What can vmstat tell you that uptime cannot?",
     "key_points": ["whether the load is CPU (r) or I/O (b, wa)"],
     "bonus": ["also whether the host is swapping (si/so)"]},
    {"question": "Which three questions does vmstat answer quickly?",
     "key_points": ["is the CPU saturated", "are tasks waiting on I/O", "is the host swapping"]},
    {"question": "Does vmstat show one process or the whole system?",
     "key_points": ["the whole system"],
     "bonus": ["pidstat or top show individual processes"]},
    {"question": "Why is vmstat's r column a better signal for CPU saturation than the load average?",
     "key_points": ["r counts only tasks wanting a CPU, not tasks blocked in I/O"]},
    {"question": "Name one thing vmstat cannot show you.",
     "key_points": ["one of: per-CPU usage, per-process usage, per-disk usage, which process is responsible"]},
    {"question": "You see high wa in vmstat. Which command do you run next, and why?",
     "key_points": ["iostat -xz 1, to see which disk is busy"]},
]

COLUMN_QUESTIONS = [
    {"question": "What does the r column mean, and when is it alarming?",
     "key_points": ["tasks running or waiting for a CPU", "alarming when it is above the CPU count"]},
    {"question": "What does the b column mean?",
     "key_points": ["tasks blocked in uninterruptible I/O (waiting on disk)"]},
    {"question": "What do si and so mean, and what does a non-zero value tell you?",
     "key_points": ["swap-ins and swap-outs per second", "non-zero means the host is out of memory and swapping"]},
    {"question": "What does us measure?",
     "key_points": ["% CPU time spent in user space: applications"]},
    {"question": "What does sy measure, and what does a high value tell you?",
     "key_points": ["% CPU time spent in the kernel", "above about 20% the kernel works hard, for example on I/O or interrupts"]},
    {"question": "What is the difference between id and wa?",
     "key_points": ["both are idle CPU time; wa is idle while tasks wait for disk I/O"]},
    {"question": "What does st mean, and where does it matter?",
     "key_points": ["CPU time stolen by other virtual machines", "it matters on virtual machines (cloud)"]},
    {"question": "What do bi and bo measure?",
     "key_points": ["blocks read from disk (bi) and written to disk (bo) per second"]},
    {"question": "What does cs measure?",
     "key_points": ["context switches per second"]},
    {"question": "free shows only a few hundred MB. Is the host out of memory?",
     "key_points": ["not necessarily: Linux uses spare memory for cache; check free -m and its available column"]},
    {"question": "r is 32 on a host with 32 CPUs. What does that mean?",
     "key_points": ["the CPUs are fully used, but there is no queue yet"]},
    {"question": "us + sy is 99 and r is low. Is the CPU saturated?",
     "key_points": ["the CPUs are busy (utilized) but not saturated: there is no queue (r below the CPU count)"]},
    {"question": "wa is steadily 40. What does that tell you?",
     "key_points": ["a disk bottleneck: the CPUs are idle because tasks wait for disk I/O"]},
    {"question": "buff and cache are near zero. Why can that be a problem?",
     "key_points": ["almost nothing is cached, so more reads have to go to disk"]},
]

SITUATIONS = ["normal", "cpu_saturated", "io_wait", "swapping", "high_sys", "first_line"]

_HEADER = ("procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----\n"
           " r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st")


def _row(r, b, swpd, free, buff, cache, si, so, bi, bo, inn, cs, us, sy, idle, wa, st) -> str:
    return (f"{r:2d} {b:2d} {swpd:6d} {free:6d} {buff:6d} {cache:6d} {si:4d} {so:4d} "
            f"{bi:5d} {bo:5d} {inn:4d} {cs:4d} {us:2d} {sy:2d} {idle:2d} {wa:2d} {st:2d}")


def situation(rng: random.Random, kind: str) -> dict:
    cpus = rng.choice([4, 8, 16, 32])
    mem_kb = cpus * rng.choice([4, 8]) * 1024 * 1024
    swpd, buff = 0, rng.randint(40_000, 400_000)
    cache = int(mem_kb * rng.uniform(0.3, 0.6))
    free = int(mem_kb * rng.uniform(0.15, 0.4))
    if kind == "swapping":
        swpd = rng.randint(2_000_000, 5_000_000)
        free, cache = rng.randint(60_000, 180_000), rng.randint(200_000, 600_000)
    elif kind == "first_line":
        swpd = rng.randint(300_000, 900_000)  # swapped out at some point in the past; constant now
    rows = []

    # First line: the rate columns (si/so, bi/bo, in/cs, cpu %) are averages since boot; the memory
    # columns (swpd, free, buff, cache) are current values, like in every other line.
    first = dict(r=1, b=0, swpd=swpd, free=free, buff=buff, cache=cache, si=0, so=0,
                 bi=rng.randint(2, 40), bo=rng.randint(10, 120), inn=rng.randint(5, 80), cs=rng.randint(10, 300))
    us0, sy0, id0, wa0, st0 = split_percent(rng, rng.uniform(3, 12), rng.uniform(1, 3), rng.uniform(0, 1))

    for _ in range(4):
        if kind in ("normal", "first_line"):
            r, b = rng.randint(0, max(1, cpus // 4)), 0
            us, sy, wa = rng.uniform(5, 20), rng.uniform(1, 5), rng.uniform(0, 1)
            si = so = 0
            bi, bo = rng.randint(0, 50), rng.randint(0, 300)
            inn, cs = rng.randint(800, 3000), rng.randint(1500, 6000)
        elif kind == "cpu_saturated":
            r, b = int(cpus * rng.uniform(1.6, 3.0)), 0
            us, sy, wa = rng.uniform(88, 96), rng.uniform(2, 6), 0
            si = so = 0
            bi, bo = rng.randint(0, 20), rng.randint(0, 600)
            inn, cs = rng.randint(9000, 16000), rng.randint(2000, 5000)
        elif kind == "io_wait":
            r, b = rng.randint(0, 2), rng.randint(max(3, cpus // 2), cpus + 6)
            us, sy, wa = rng.uniform(3, 8), rng.uniform(2, 5), rng.uniform(45, 70)
            si = so = 0
            bi, bo = rng.randint(100, 400), rng.randint(30_000, 60_000)
            inn, cs = rng.randint(8000, 10000), rng.randint(14000, 17000)
        elif kind == "swapping":
            r, b = rng.randint(1, max(2, cpus // 2)), rng.randint(1, 4)
            us, sy, wa = rng.uniform(10, 25), rng.uniform(5, 12), rng.uniform(8, 25)
            si, so = rng.randint(400, 3000), rng.randint(800, 6000)
            swpd += so - si  # si/so are KB per second, so swap use moves by their difference
            bi, bo = si * 4 + rng.randint(0, 200), so * 4 + rng.randint(0, 200)
            inn, cs = rng.randint(3000, 7000), rng.randint(5000, 12000)
        else:  # high_sys
            r, b = rng.randint(max(1, cpus // 3), max(2, cpus - 1)), 0
            us, sy, wa = rng.uniform(15, 25), rng.uniform(32, 50), 0
            si = so = 0
            bi, bo = rng.randint(0, 30), rng.randint(0, 400)
            inn, cs = rng.randint(80_000, 160_000), rng.randint(200_000, 450_000)
        us_, sy_, id_, wa_, st_ = split_percent(rng, us, sy, wa)
        rows.append(_row(r, b, swpd, free + rng.randint(-2000, 2000), buff, cache, si, so, bi, bo, inn, cs,
                         us_, sy_, id_, wa_, st_))

    if kind == "first_line":
        # Since boot: the host had heavy I/O and swapping in the past, but the live lines are calm.
        first.update(b=2, si=rng.randint(20, 90), so=rng.randint(40, 160))
        us0, sy0, id0, wa0, st0 = split_percent(rng, rng.uniform(20, 35), rng.uniform(6, 10), rng.uniform(12, 25))
    first_row = _row(first["r"], first["b"], first["swpd"], first["free"], first["buff"], first["cache"],
                     first["si"], first["so"], first["bi"], first["bo"], first["inn"], first["cs"],
                     us0, sy0, id0, wa0, st0)

    if kind == "normal":
        key_points = ["nothing wrong: the CPU is not saturated, no tasks wait on I/O, no swapping"]
        bonus = ["evidence: r below the CPU count, b and wa 0, si/so 0", "next: continue the checklist"]
    elif kind == "cpu_saturated":
        key_points = ["the CPU is saturated: r is well above the CPU count"]
        bonus = ["us is near 100: the work is in applications (user space)", "no I/O wait and no swapping",
                 "next: mpstat -P ALL 1 and pidstat 1 to find the process"]
    elif kind == "io_wait":
        key_points = ["tasks are waiting on disk I/O, not on the CPU"]
        bonus = ["evidence: b and wa are high while us + sy is low and r is small", "bo is high: heavy writing",
                 "next: iostat -xz 1 to find the busy disk"]
    elif kind == "swapping":
        key_points = ["the host is swapping: it is out of memory"]
        bonus = ["evidence: si and so are not 0, free is small and swpd is large",
                 "next: free -m, then find the process that uses the memory"]
    elif kind == "high_sys":
        key_points = ["system (kernel) CPU time is high, well above 20%"]
        bonus = ["very many context switches and interrupts (cs, in)",
                 "next: mpstat -P ALL 1 (%sys, %soft) and pidstat -w to see who switches"]
    else:  # first_line
        key_points = ["nothing wrong now: the live lines are calm; the first line is the average since boot"]
        bonus = ["the swapping and I/O wait in the first line happened in the past",
                 "swpd is not 0, but it stays the same and si/so are 0: nothing is swapping now",
                 "next: continue the checklist"]

    return {
        "situation": kind,
        "prompt": f"The host has {cpus} CPUs and {mem_kb // (1024 * 1024)} GB of RAM. You run `vmstat 1`:",
        "output": "\n".join([_HEADER, first_row] + rows),
        "key_points": key_points,
        "bonus": bonus,
    }
