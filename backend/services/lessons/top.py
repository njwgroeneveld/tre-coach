"""Lesson 10: top — the whole picture on one screen, as a cross-check."""

import random

from services.lessons.common import split_percent

COMMAND = "top"

CARD = {
    "title": "top — load, CPU, memory and the busiest processes on one screen",
    "summary": (
        "top combines much of what the earlier commands showed: the uptime line, task states, the CPU "
        "breakdown, memory, and a list of processes sorted by CPU. Use it to check that nothing looks wildly "
        "different from what you already saw; if it does, the load is variable. Its downside: the screen clears, "
        "so patterns over time are harder to see (Ctrl-S pauses, Ctrl-Q continues)."
    ),
    "example": (
        "top - 00:15:40 up 21:56,  1 user,  load average: 31.09, 29.87, 29.92\n"
        "Tasks: 871 total,   1 running, 868 sleeping,   0 stopped,   2 zombie\n"
        "%Cpu(s): 96.8 us,  0.4 sy,  0.0 ni,  2.7 id,  0.1 wa,  0.0 hi,  0.0 si,  0.0 st\n"
        "\n"
        "    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND\n"
        "  20248 root      20   0  0.227t 0.012t  18748 S  3090   5.2  29812:58 java"
    ),
    "fields": [
        {"name": "top - ... load average", "meaning": "The same as uptime.", "normal": "—", "alarming": "see lesson 1"},
        {"name": "Tasks: running, sleeping, stopped, zombie", "meaning": "How many processes are in each state.",
         "normal": "most sleeping, few zombies",
         "alarming": "many zombies → a parent does not clean up its children"},
        {"name": "%Cpu(s): us sy ni id wa hi si st", "meaning": "The CPU breakdown, as in vmstat; hi = hardware interrupts, si = software interrupts.",
         "normal": "—", "alarming": "as in vmstat: us + sy near 100, high wa, high si"},
        {"name": "MiB Mem / Swap, avail Mem", "meaning": "Memory as in free -m; 'avail Mem' is free's 'available'.",
         "normal": "plenty available", "alarming": "low avail Mem, swap used"},
        {"name": "RES", "meaning": "Physical memory a process uses (resident).",
         "normal": "—", "alarming": "one process with most of the RAM → memory hog"},
        {"name": "VIRT", "meaning": "Virtual memory the process has reserved; often far larger than what it uses.",
         "normal": "large values are normal", "alarming": "rarely a signal on its own"},
        {"name": "S", "meaning": "Process state: R running, S sleeping, D uninterruptible (I/O), Z zombie.",
         "normal": "mostly S, a few R",
         "alarming": "several D → stuck on I/O"},
        {"name": "%CPU", "meaning": "CPU use of the process; 100 = one full CPU (3090 ≈ 31 CPUs).",
         "normal": "—", "alarming": "one process using most CPUs"},
        {"name": "TIME+", "meaning": "Total CPU time the process has used since it started.",
         "normal": "—", "alarming": "—"},
    ],
    "steps": [
        "Compare the summary lines with what uptime, vmstat and free showed: the same picture?",
        "Look at the top of the process list: who uses the CPU, and in which state are they?",
        "Look for D (I/O), Z (zombies) and very large RES.",
    ],
    "next": "A busy process → pidstat 1 to watch it over time · D-state processes → iostat -xz 1 · "
            "memory hog → free -m and its owner.",
}

PURPOSE_QUESTIONS = [
    {"question": "Why does the Netflix checklist end with top?",
     "key_points": ["to check whether anything looks different from the earlier commands"],
     "bonus": ["a different picture means the load is variable"]},
    {"question": "What does top show on one screen?",
     "key_points": ["the load, CPU breakdown, memory and the busiest processes"]},
    {"question": "What is the downside of top compared with vmstat or pidstat?",
     "key_points": ["the screen clears, so patterns over time are harder to see"],
     "bonus": ["an intermittent problem can scroll away before you notice"]},
    {"question": "How do you pause top's output, and why would you?",
     "key_points": ["Ctrl-S (Ctrl-Q continues), to keep evidence on screen"]},
    {"question": "Which line of top is the same as uptime?",
     "key_points": ["the first line"]},
    {"question": "Which line of top is like vmstat's cpu columns?",
     "key_points": ["the %Cpu(s) line"]},
    {"question": "top looks completely different from what vmstat showed a minute ago. What does that tell you?",
     "key_points": ["the load is changing (variable or intermittent)"]},
    {"question": "Which process state in top points to I/O problems?",
     "key_points": ["D (uninterruptible sleep)"]},
]

COLUMN_QUESTIONS = [
    {"question": "What does the S column show, and what do R, S, D and Z mean?",
     "key_points": ["the process state",
                    "R running, S sleeping, D uninterruptible (usually I/O), Z zombie"]},
    {"question": "What is the difference between RES and VIRT?",
     "key_points": ["RES is physical memory actually used; VIRT is virtual memory reserved, often much larger"]},
    {"question": "A java process shows %CPU 3090. What does that mean?",
     "key_points": ["it uses about 31 CPUs"]},
    {"question": "What does 'avail Mem' on the Swap line mean?",
     "key_points": ["memory available to applications, like free's 'available'"]},
    {"question": "What do hi and si in the %Cpu(s) line mean?",
     "key_points": ["time on hardware interrupts (hi) and software interrupts (si)"]},
    {"question": "Tasks shows 40 zombie. Is that a performance problem?",
     "key_points": ["usually not directly: zombies use no CPU or memory, but a parent is not cleaning up its children"],
     "bonus": ["very many could exhaust process IDs"]},
    {"question": "What does TIME+ show?",
     "key_points": ["the total CPU time the process has used since it started"]},
    {"question": "Several processes show S = D. What does that tell you?",
     "key_points": ["they are stuck waiting on I/O, usually disk"]},
    {"question": "What do PR and NI show?",
     "key_points": ["the scheduling priority and the nice value of the process"]},
    {"question": "A huge VIRT value (for example 0.227t). Should you worry?",
     "key_points": ["usually not: it is reserved address space, not memory in use; look at RES"]},
]

SITUATIONS = ["normal", "cpu_hog", "d_state", "memory_hog", "zombies"]

_COLS = "    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND"


def _proc(pid, user, virt, res, shr, state, cpu, mem, time_, cmd) -> str:
    return f"{pid:7d} {user:<9} 20   0 {virt:>7} {res:>6} {shr:>6} {state} {cpu:5.1f} {mem:5.1f} {time_:>9} {cmd}"


def situation(rng: random.Random, kind: str) -> dict:
    cpus = rng.choice([8, 16, 32])
    total = rng.choice([31_998.4, 64_221.4, 128_520.2])
    h, m, s = rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59)
    zombies, running = 0, rng.randint(1, 3)
    used, cache, swap_used = total * rng.uniform(0.15, 0.3), total * rng.uniform(0.3, 0.5), 0.0
    procs = [
        _proc(3342, "trading", "6.2g", "1.1g", "48212", "S", rng.uniform(5, 25), 1.8, "812:36.15", "ordergw"),
        _proc(4213, "root", "2.6g", "64640", "44232", "S", rng.uniform(0.3, 3), 0.1, "233:35.37", "node_exporter"),
        _proc(66128, "niels", "24344", "4332", "3172", "R", 1.0, 0.0, "0:00.07", "top"),
        _proc(1, "root", "167800", "12920", "8496", "S", 0.0, 0.0, "0:03.82", "systemd"),
    ]

    if kind == "normal":
        load = cpus * rng.uniform(0.1, 0.4)
        us, sy, wa = rng.uniform(5, 20), rng.uniform(1, 4), rng.uniform(0, 0.5)
    elif kind == "cpu_hog":
        load = cpus * rng.uniform(0.95, 1.4)
        us, sy, wa = rng.uniform(88, 97), rng.uniform(0.5, 3), 0
        running = rng.randint(2, 4)  # Tasks counts processes, not threads: one busy java is one task
        procs.insert(0, _proc(20248, "root", "38.2g", "12.1g", "18748", "R", cpus * 100 * rng.uniform(0.85, 0.96),
                              12.0, "29812:58", "java"))
    elif kind == "d_state":
        load = cpus * rng.uniform(1.2, 2.5)
        us, sy, wa = rng.uniform(3, 8), rng.uniform(2, 4), rng.uniform(45, 70)
        procs = [
            _proc(28431, "root", "12048", "1620", "1264", "D", 14.3, 0.0, "0:41.87", "gzip"),
            _proc(3342, "trading", "6.2g", "1.1g", "48212", "D", 3.2, 1.8, "812:36.15", "ordergw"),
            _proc(842, "root", "224316", "9876", "7120", "D", 0.7, 0.0, "3:12.77", "systemd-journal"),
            _proc(1187, "root", "412880", "18240", "10544", "D", 0.3, 0.0, "21:08.43", "rsyslogd"),
        ] + procs[1:]
    elif kind == "memory_hog":
        load = cpus * rng.uniform(0.3, 0.7)
        us, sy, wa = rng.uniform(10, 25), rng.uniform(4, 10), rng.uniform(5, 20)
        used, cache, swap_used = total * rng.uniform(0.93, 0.96), total * 0.015, rng.uniform(3000, 7000)
        res_gb = total / 1024 * rng.uniform(0.78, 0.86)
        procs.insert(0, _proc(5120, "trading", f"{res_gb * 1.1:.1f}g", f"{res_gb:.1f}g", "21344", "S", rng.uniform(20, 60),
                              res_gb * 1024 / total * 100, "142:11.02", "md-replay"))
    else:  # zombies
        load = cpus * rng.uniform(0.1, 0.4)
        us, sy, wa = rng.uniform(5, 20), rng.uniform(1, 4), 0
        zombies = rng.randint(30, 120)
        procs += [_proc(9100 + i, "trading", "0", "0", "0", "Z", 0.0, 0.0, "0:00.01", "healthcheck.sh <defunct>")
                  for i in range(3)]

    us_, sy_, id_, wa_, st_ = split_percent(rng, us, sy, wa)
    free = max(200.0, total - used - cache)
    avail = free + cache * 0.85
    total_tasks = rng.randint(300, 600) + zombies
    sleeping = total_tasks - running - zombies
    l1 = load
    lines = [
        f"top - {h:02d}:{m:02d}:{s:02d} up {rng.randint(3, 120)} days, {rng.randint(0, 23):2d}:{rng.randint(0, 59):02d},  "
        f"1 user,  load average: {l1:.2f}, {l1 * rng.uniform(0.9, 1.05):.2f}, {l1 * rng.uniform(0.85, 1.05):.2f}",
        f"Tasks: {total_tasks:3d} total, {running:3d} running, {sleeping:3d} sleeping,   0 stopped, {zombies:3d} zombie",
        f"%Cpu(s): {us_:4.1f} us, {sy_:4.1f} sy,  0.0 ni, {id_:4.1f} id, {wa_:4.1f} wa,  0.0 hi,  0.0 si,  0.0 st",
        f"MiB Mem : {total:8.1f} total, {free:8.1f} free, {used:8.1f} used, {cache:8.1f} buff/cache",
        f"MiB Swap:   8192.0 total, {8192 - swap_used:8.1f} free, {swap_used:8.1f} used. {avail:8.1f} avail Mem",
        "",
        _COLS,
    ] + procs

    if kind == "normal":
        key_points = ["nothing stands out: low load, CPUs mostly idle, plenty of memory"]
        bonus = ["consistent with the earlier commands: the load is stable"]
    elif kind == "cpu_hog":
        key_points = ["java (PID 20248) is using almost all CPUs"]
        bonus = ["us near 100%, load around the CPU count",
                 "next: pidstat 1 to watch it, and find out what java is doing"]
    elif kind == "d_state":
        key_points = ["several processes are in state D: they are stuck waiting on I/O"]
        bonus = ["wa is high and the CPUs are idle; the load is high because of the D tasks",
                 "gzip is busy while ordergw waits", "next: iostat -xz 1 and pidstat -d 1"]
    elif kind == "memory_hog":
        key_points = ["md-replay uses most of the memory; little is available and swap is in use"]
        bonus = ["its RES is most of the RAM", "next: free -m and vmstat si/so; restart or limit md-replay"]
    else:
        key_points = ["there are many zombie processes, but otherwise the host is fine"]
        bonus = ["zombies use no CPU or memory; healthcheck.sh's parent does not clean up its children",
                 "a problem only if there are so many that process IDs run out"]

    return {
        "situation": kind,
        "prompt": f"The host has {cpus} CPUs. You run `top` (first screen shown):",
        "output": "\n".join(lines),
        "key_points": key_points,
        "bonus": bonus,
    }
