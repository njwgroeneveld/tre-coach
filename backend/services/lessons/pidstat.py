"""Lesson 5: pidstat 1 — which process uses the CPU (and with -d the disk, with -w context switches)."""

import random

from services.lessons.common import ampm, clock, host, sysstat_header

COMMAND = "pidstat 1"

CARD = {
    "title": "pidstat 1 — which process is responsible, every second",
    "summary": (
        "pidstat shows per-process statistics as a rolling summary, one report per second (unlike top, which "
        "clears the screen). By default it shows CPU use; -d shows disk I/O per process and -w shows context "
        "switches per process. %CPU is summed over all CPUs: 1591% means almost 16 CPUs."
    ),
    "example": (
        "07:41:03 PM   UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command\n"
        "07:41:03 PM     0      4214    5.66    5.66    0.00    0.00   11.32    15  mesos-slave\n"
        "07:41:03 PM     0      6521 1596.23    1.89    0.00    0.00 1598.11    27  java\n"
        "07:41:03 PM     0      6564 1571.70    7.55    0.00    0.00 1579.25    28  java"
    ),
    "fields": [
        {"name": "PID / Command", "meaning": "Which process the line is about.", "normal": "—", "alarming": "—"},
        {"name": "%usr / %system", "meaning": "% CPU in user space and in the kernel, for this process.",
         "normal": "—", "alarming": "high %system → the process makes many system calls"},
        {"name": "%CPU", "meaning": "Total CPU use, summed over all CPUs (100 = one full CPU).",
         "normal": "depends", "alarming": "1590 → the process uses almost 16 CPUs · exactly ~100 → one full core"},
        {"name": "%wait", "meaning": "% time the process waited for a CPU (runnable but not running).",
         "normal": "near 0", "alarming": "high → the process is starved of CPU"},
        {"name": "CPU", "meaning": "The CPU the process ran on last.", "normal": "—", "alarming": "—"},
        {"name": "kB_rd/s / kB_wr/s (-d)", "meaning": "KB read from and written to disk per second by the process.",
         "normal": "depends", "alarming": "one process writing hundreds of MB/s → it drives the disk load"},
        {"name": "iodelay (-d)", "meaning": "How long the process waited for block I/O, in clock ticks.",
         "normal": "0", "alarming": "high → the process is held up by the disk"},
        {"name": "cswch/s (-w)", "meaning": "Voluntary context switches: the process gave up the CPU itself (waiting for I/O, a lock, a sleep).",
         "normal": "depends", "alarming": "very high with low CPU → it keeps waiting (locks, I/O)"},
        {"name": "nvcswch/s (-w)", "meaning": "Involuntary context switches: the scheduler took the CPU away.",
         "normal": "low", "alarming": "high → the process is preempted: too much competition for its CPU"},
    ],
    "steps": [
        "Sort mentally by the column that matters: %CPU for CPU, kB_wr/s for disk, nvcswch/s for preemption.",
        "Find the process that stands out.",
        "Remember %CPU is summed over CPUs: divide by 100 for the number of CPUs it uses.",
    ],
    "next": "You know the process: look at what it does (its logs, its threads with pidstat -t) · "
            "disk writer → iostat -xz 1 for the device.",
}

PURPOSE_QUESTIONS = [
    {"question": "What does pidstat 1 show you?",
     "key_points": ["CPU use per process, every second"]},
    {"question": "How is pidstat different from top?",
     "key_points": ["it prints a rolling summary instead of clearing the screen"],
     "bonus": ["so you can see patterns over time and copy the output into your notes"]},
    {"question": "After vmstat and mpstat show the CPUs are busy, why run pidstat?",
     "key_points": ["to find which process uses the CPU"]},
    {"question": "What does pidstat -d show?",
     "key_points": ["disk reads and writes per process"]},
    {"question": "What does pidstat -w show?",
     "key_points": ["context switches per process (voluntary and involuntary)"]},
    {"question": "What does pidstat -t add?",
     "key_points": ["the same statistics per thread"]},
    {"question": "Why is %CPU in pidstat sometimes far above 100?",
     "key_points": ["it is summed over all CPUs; 100 is one full CPU"]},
    {"question": "Which question about the system does pidstat answer that vmstat cannot?",
     "key_points": ["which process is responsible"]},
]

COLUMN_QUESTIONS = [
    {"question": "A java process shows %CPU 1591. What does that mean?",
     "key_points": ["it uses almost 16 CPUs"]},
    {"question": "A process shows %CPU 99.8, and pidstat -t shows one thread at 99.8. What does that suggest?",
     "key_points": ["one thread uses a whole core: a single-threaded bottleneck"]},
    {"question": "What does %wait in pidstat measure?",
     "key_points": ["time the process was runnable but waiting for a CPU"]},
    {"question": "What does the CPU column in pidstat show?",
     "key_points": ["which CPU the process ran on last"]},
    {"question": "What do kB_rd/s and kB_wr/s show (pidstat -d)?",
     "key_points": ["KB read from and written to disk per second by each process"]},
    {"question": "What does iodelay show (pidstat -d)?",
     "key_points": ["how long the process waited for disk I/O"]},
    {"question": "What is the difference between cswch/s and nvcswch/s (pidstat -w)?",
     "key_points": ["cswch/s: the process gave up the CPU itself (voluntary)",
                    "nvcswch/s: the scheduler took the CPU away (involuntary)"]},
    {"question": "A trading process has a high nvcswch/s. What does that tell you?",
     "key_points": ["it is often preempted: other work competes for its CPU"],
     "bonus": ["that adds latency; pin it or move the other work"]},
    {"question": "A process has a very high cswch/s but low %CPU. What could it be doing?",
     "key_points": ["it keeps waiting: on locks, I/O or sleeps"]},
    {"question": "%system is high for one process. What does that suggest?",
     "key_points": ["it spends its time in the kernel: many system calls"]},
]

SITUATIONS = ["quiet", "cpu_hog", "single_thread", "disk_writer", "preempted"]

_CPU_HDR = "   UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command"
_DISK_HDR = "   UID       PID   kB_rd/s   kB_wr/s kB_ccwr/s iodelay  Command"
_CSW_HDR = "   UID       PID   cswch/s nvcswch/s  Command"


def _cpu(t, uid, pid, usr, sys_, wait, cpu, cmd) -> str:
    return f"{t} {uid:5d} {pid:9d} {usr:7.2f} {sys_:7.2f} {0:7.2f} {wait:7.2f} {usr + sys_:7.2f} {cpu:5d}  {cmd}"


def situation(rng: random.Random, kind: str) -> dict:
    cpus = rng.choice([8, 16, 32])
    hostname = host(rng)
    h, m, s = clock(rng)
    t = ampm(h, m, s + 1)
    command = "pidstat 1"
    lines = []

    background = [(0, 1187, "tuned"), (0, 842, "systemd-journal"), (1001, 3342, "ordergw"), (0, 4214, "node_exporter")]
    if kind in ("quiet", "cpu_hog", "single_thread"):
        lines.append(t + _CPU_HDR)
        for uid, pid, cmd in background:
            usr = rng.uniform(4, 20) if cmd == "ordergw" else rng.uniform(0, 2)
            lines.append(_cpu(t, uid, pid, usr, rng.uniform(0.2, 3), 0, rng.randrange(cpus), cmd))
        if kind == "cpu_hog":
            n = cpus * rng.uniform(0.75, 0.95)
            lines.append(_cpu(t, 1001, 6521, n * 100, rng.uniform(1, 9), rng.uniform(0, 4), rng.randrange(cpus), "java"))
        elif kind == "single_thread":
            lines.append(_cpu(t, 1001, 5120, rng.uniform(98, 99.5), rng.uniform(0.2, 1), 0, rng.randrange(cpus), "md-handler"))
        lines.append(_cpu(t, 1001, 60154, 0.99, 3.96, 0, rng.randrange(cpus), "pidstat"))
    elif kind == "disk_writer":
        command = "pidstat -d 1"
        lines.append(t + _DISK_HDR)
        lines.append(f"{t} {1001:5d} {3342:9d} {0.0:9.2f} {rng.uniform(800, 3000):9.2f} {0.0:9.2f} {rng.randint(90, 250):7d}  ordergw")
        lines.append(f"{t} {0:5d} {842:9d} {0.0:9.2f} {rng.uniform(4, 40):9.2f} {0.0:9.2f} {0:7d}  systemd-journal")
        lines.append(f"{t} {0:5d} {28431:9d} {rng.uniform(150_000, 260_000):9.2f} {rng.uniform(150_000, 240_000):9.2f} "
                     f"{0.0:9.2f} {rng.randint(400, 900):7d}  gzip")
    else:  # preempted
        command = "pidstat -w 1"
        lines.append(t + _CSW_HDR)
        lines.append(f"{t} {1001:5d} {3342:9d} {rng.uniform(800, 2500):9.2f} {rng.uniform(1500, 6000):9.2f}  ordergw")
        lines.append(f"{t} {1001:5d} {7712:9d} {rng.uniform(2, 20):9.2f} {rng.uniform(300, 900):9.2f}  batch-report")
        lines.append(f"{t} {0:5d} {842:9d} {rng.uniform(1, 10):9.2f} {0.0:9.2f}  systemd-journal")
        lines.append(f"{t} {0:5d} {12:9d} {rng.uniform(10, 80):9.2f} {0.0:9.2f}  ksoftirqd/1")

    output = "\n".join([sysstat_header(rng, hostname, cpus), ""] + lines)

    if kind == "quiet":
        key_points = ["no process stands out: CPU use is low everywhere"]
        bonus = ["ordergw uses a little CPU, the rest is near 0", "next: continue the checklist"]
    elif kind == "cpu_hog":
        key_points = ["java (PID 6521) uses most of the CPU"]
        bonus = ["its %CPU is summed over CPUs: divide by 100 for the number of CPUs it uses",
                 "next: find out what java is doing (its threads, its logs)"]
    elif kind == "single_thread":
        key_points = ["md-handler uses one full CPU (about 100%): probably a single-threaded bottleneck"]
        bonus = ["the host as a whole is not busy", "next: pidstat -t to confirm one thread, mpstat to see the hot CPU"]
    elif kind == "disk_writer":
        key_points = ["gzip (PID 28431) is responsible for almost all disk reads and writes"]
        bonus = ["ordergw has a high iodelay: it waits on the disk gzip is using",
                 "next: iostat -xz 1 for the device; move or throttle the gzip job"]
    else:
        key_points = ["ordergw is preempted a lot: its involuntary context switches (nvcswch/s) are high"]
        bonus = ["other work, such as batch-report, competes for its CPU", "this adds latency",
                 "next: mpstat and check CPU affinity / move the batch job"]

    return {
        "situation": kind,
        "prompt": f"The host has {cpus} CPUs. You run `{command}` (one report shown):",
        "output": output,
        "key_points": key_points,
        "bonus": bonus,
    }
