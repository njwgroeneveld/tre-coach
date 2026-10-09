"""Lesson 6: iostat -xz 1 — how busy each disk is, and how long I/O takes."""

import random

from services.lessons.common import host, sysstat_header

COMMAND = "iostat -xz 1"

CARD = {
    "title": "iostat -xz 1 — per disk: the work it gets and how long that work takes",
    "summary": (
        "iostat shows block devices (disks): the workload applied and the resulting performance. -x gives the "
        "extended columns, -z hides idle devices, 1 prints a report every second. Like vmstat, the first report "
        "is since boot. Older versions name some columns differently: avgqu-sz (now aqu-sz) and await "
        "(now r_await / w_await)."
    ),
    "example": (
        "Device            r/s     w/s     rkB/s     wkB/s   rrqm/s   wrqm/s  %rrqm  %wrqm r_await w_await aqu-sz rareq-sz wareq-sz  svctm  %util\n"
        "nvme0n1          1.02    8.94    127.97    598.53     0.01     0.00   0.97   0.00    1.78    0.28   0.00   125.46    66.95   0.25   0.25\n"
        "sdb            180.40  150.20 231040.00 224380.00     0.00    12.00   0.00   7.40   85.20  118.90  30.12  1280.70  1493.88   3.02 100.00"
    ),
    "fields": [
        {"name": "r/s, w/s", "meaning": "Reads and writes completed per second.",
         "normal": "depends on the workload", "alarming": "much higher than usual → too much work sent to the disk"},
        {"name": "rkB/s, wkB/s", "meaning": "KB read and written per second: the throughput.",
         "normal": "depends", "alarming": "near what the device can do → it is at its limit"},
        {"name": "r_await, w_await", "meaning": "Average time per read / write in ms, including time in the queue: what the application feels.",
         "normal": "SSD below about 1–2 ms; spinning disk below about 10–20 ms",
         "alarming": "tens or hundreds of ms → saturation, or a device problem"},
        {"name": "aqu-sz (avgqu-sz)", "meaning": "Average number of requests queued or in service.",
         "normal": "below 1", "alarming": "above 1 and rising → requests are queueing: saturation"},
        {"name": "%util", "meaning": "% of time the device was busy.",
         "normal": "below about 60%",
         "alarming": "above 60% usually hurts; near 100% → saturated (less certain for SSD/RAID that work in parallel)"},
        {"name": "avg-cpu %iowait", "meaning": "The CPU summary on top: % idle while waiting for I/O.",
         "normal": "0", "alarming": "high → the system as a whole waits on disks"},
    ],
    "steps": [
        "Look at %util and aqu-sz: is a device saturated?",
        "Look at await: how long does each I/O take, compared with what the device should do?",
        "Look at r/s, w/s, kB/s: is it simply too much work, or slow on little work (a device problem)?",
    ],
    "next": "Find who sends the I/O: pidstat -d 1 · a slow device on little work → dmesg for disk errors.",
}

PURPOSE_QUESTIONS = [
    {"question": "What does iostat -xz 1 show you?",
     "key_points": ["per disk: how much I/O it gets and how long that I/O takes"]},
    {"question": "What do the options -x and -z do?",
     "key_points": ["-x: extended statistics", "-z: hide devices with no activity"]},
    {"question": "vmstat shows high wa. Why is iostat the next command?",
     "key_points": ["it shows which disk is busy or slow"]},
    {"question": "Why should you ignore the first report of iostat 1?",
     "key_points": ["it shows averages since boot, not the current second"]},
    {"question": "Which two things does iostat let you tell apart for a slow disk?",
     "key_points": ["too much work sent to it (high r/s, w/s, kB/s)",
                    "a device that is slow on little work (high await with low throughput)"]},
    {"question": "Can iostat tell you which process causes the disk load?",
     "key_points": ["no; pidstat -d or iotop show processes"]},
    {"question": "Why does slow disk I/O not always slow down the application?",
     "key_points": ["much I/O is asynchronous: writes are buffered and reads use read-ahead, so the application does not wait"]},
    {"question": "In USE terms, which iostat columns show utilization and which show saturation?",
     "key_points": ["utilization: %util", "saturation: aqu-sz (queue length) or a high await"]},
]

COLUMN_QUESTIONS = [
    {"question": "What do r/s and w/s show?",
     "key_points": ["reads and writes completed per second"]},
    {"question": "What do rkB/s and wkB/s show?",
     "key_points": ["KB read and written per second: the throughput"]},
    {"question": "What does w_await show, and why does it matter?",
     "key_points": ["the average time per write in ms, queue time included", "it is the time the application waits"]},
    {"question": "What does aqu-sz (avgqu-sz) show, and when is it a warning?",
     "key_points": ["the average number of requests waiting or in service", "above 1 can mean saturation"]},
    {"question": "What does %util show?",
     "key_points": ["the % of time the device was busy"]},
    {"question": "%util is 100 on a RAID array with many disks. Is it certainly saturated?",
     "key_points": ["no: it means some I/O was in progress all the time; the disks behind it can work in parallel"]},
    {"question": "w_await is 350 ms on an SSD. Is that normal?",
     "key_points": ["no: an SSD should take about a millisecond; this is saturation or a device problem"]},
    {"question": "A disk does 30 writes per second with w_await 900 ms and %util 100. What does that suggest?",
     "key_points": ["a slow or failing device: it is slow even on very little work"]},
    {"question": "A disk does 9000 writes per second with w_await 0.4 ms and %util 45. Healthy?",
     "key_points": ["yes: a lot of work, but fast and not saturated"]},
    {"question": "What does %iowait in the avg-cpu line show?",
     "key_points": ["% of CPU time idle while waiting for I/O"]},
    {"question": "Older iostat shows 'avgqu-sz' and 'await'. What are they called now?",
     "key_points": ["aqu-sz", "r_await and w_await"]},
]

SITUATIONS = ["idle", "busy_healthy", "saturated", "slow_device"]

_DEV_HDR = ("Device            r/s     w/s     rkB/s     wkB/s   rrqm/s   wrqm/s  %rrqm  %wrqm "
            "r_await w_await aqu-sz rareq-sz wareq-sz  svctm  %util")


def _dev(name, rs, ws, rkb, wkb, r_await, w_await, util) -> str:
    aqu = rs * r_await / 1000 + ws * w_await / 1000
    rareq = rkb / rs if rs else 0.0
    wareq = wkb / ws if ws else 0.0
    svctm = util * 10 / (rs + ws) if (rs + ws) else 0.0
    return (f"{name:<12}{rs:8.2f}{ws:8.2f}{rkb:10.2f}{wkb:10.2f}{0.0:9.2f}{ws * 0.05:9.2f}{0.0:7.2f}{4.76:7.2f}"
            f"{r_await:8.2f}{w_await:8.2f}{aqu:7.2f}{rareq:9.2f}{wareq:9.2f}{svctm:7.2f}{util:7.2f}")


def situation(rng: random.Random, kind: str) -> dict:
    cpus = rng.choice([8, 16])
    hostname = host(rng)
    os_disk = _dev("nvme0n1", rng.uniform(0, 3), rng.uniform(2, 15), rng.uniform(0, 60), rng.uniform(20, 300),
                   rng.uniform(0.1, 0.4), rng.uniform(0.02, 0.2), rng.uniform(0.1, 1.5))
    if kind == "idle":
        data = _dev("sdb", rng.uniform(0, 5), rng.uniform(1, 20), rng.uniform(0, 80), rng.uniform(10, 400),
                    rng.uniform(0.2, 1), rng.uniform(0.1, 0.8), rng.uniform(0.2, 3))
        cpu = (rng.uniform(4, 10), rng.uniform(1, 2), rng.uniform(0, 0.5))
    elif kind == "busy_healthy":
        ws = rng.uniform(6000, 12000)
        # aqu-sz ≈ IOPS × await: keep it below 1 for a healthy device.
        data = _dev("sdb", rng.uniform(200, 900), ws, rng.uniform(5_000, 40_000), ws * rng.uniform(12, 30),
                    rng.uniform(0.05, 0.2), rng.uniform(0.02, 0.06), rng.uniform(30, 55))
        cpu = (rng.uniform(15, 30), rng.uniform(4, 8), rng.uniform(0.5, 2))
    elif kind == "saturated":
        ws = rng.uniform(900, 1600)
        data = _dev("sdb", rng.uniform(50, 200), ws, rng.uniform(20_000, 90_000), ws * rng.uniform(120, 250),
                    rng.uniform(20, 70), rng.uniform(40, 110), rng.uniform(99.5, 100))
        cpu = (rng.uniform(3, 8), rng.uniform(2, 4), rng.uniform(40, 65))
    else:  # slow_device
        ws = rng.uniform(15, 45)
        data = _dev("sdb", rng.uniform(1, 8), ws, rng.uniform(4, 60), ws * rng.uniform(4, 16),
                    rng.uniform(400, 900), rng.uniform(700, 1600), rng.uniform(99, 100))
        cpu = (rng.uniform(3, 8), rng.uniform(1, 3), rng.uniform(15, 35))

    us, sy, wa = cpu
    idle = 100 - us - sy - wa
    avg_cpu = ("avg-cpu:  %user   %nice %system %iowait  %steal   %idle\n"
               f"         {us:6.2f}    0.00  {sy:6.2f}  {wa:6.2f}    0.00  {idle:6.2f}")
    output = "\n".join([sysstat_header(rng, hostname, cpus), "", avg_cpu, "", _DEV_HDR, os_disk, data])

    if kind == "idle":
        key_points = ["the disks are nearly idle: no disk problem"]
        bonus = ["%util low, await low, no queue", "next: continue the checklist"]
    elif kind == "busy_healthy":
        key_points = ["sdb is busy but healthy: lots of I/O, but it is fast and not saturated"]
        bonus = ["await well below a millisecond, %util about half, no queue to speak of",
                 "the disk is not the bottleneck; look elsewhere"]
    elif kind == "saturated":
        key_points = ["sdb is saturated: %util about 100, a deep queue and high await"]
        bonus = ["it gets a lot of work: very high w/s and wkB/s",
                 "the CPUs wait on it (%iowait high)", "next: pidstat -d 1 to find who writes"]
    else:
        key_points = ["sdb is slow on very little work: a slow or failing device"]
        bonus = ["evidence: await of hundreds of ms and %util 100 while r/s and w/s are tiny",
                 "next: dmesg | tail for disk errors; smartctl"]

    return {
        "situation": kind,
        "prompt": f"The order gateway has an NVMe system disk and a data SSD (sdb). You run `iostat -xz 1` (a live report):",
        "output": output,
        "key_points": key_points,
        "bonus": bonus,
    }
