"""Lesson 2: dmesg | tail — the last kernel messages."""

import random

COMMAND = "dmesg | tail"

CARD = {
    "title": "dmesg | tail — the last kernel messages",
    "summary": (
        "dmesg prints the kernel's message buffer; | tail keeps the last 10 lines. Look for errors that "
        "explain a performance problem: the OOM killer, disk I/O errors, dropped connections, a network "
        "link going down, tasks stuck on I/O. Netflix: \"Don't miss this step! dmesg is always worth checking.\""
    ),
    "example": (
        "[1880957.563150] perl invoked oom-killer: gfp_mask=0x280da, order=0, oom_score_adj=0\n"
        "[1880957.563400] Out of memory: Kill process 18694 (perl) score 246 or sacrifice child\n"
        "[1880957.563408] Killed process 18694 (perl) total-vm:1972392kB, anon-rss:1953348kB, file-rss:0kB\n"
        "[2320864.954447] TCP: Possible SYN flooding on port 7001. Dropping request.  Check SNMP counters."
    ),
    "fields": [
        {"name": "[1880957.563150]", "meaning": "When it happened: seconds since boot (dmesg -T shows the clock time).",
         "normal": "old messages from long ago",
         "alarming": "messages from around the time of the incident"},
        {"name": "invoked oom-killer / Out of memory: Killed process",
         "meaning": "Memory ran out; the kernel killed a process to free memory, and names it.",
         "normal": "not there",
         "alarming": "there → a process was killed; memory is exhausted → check free -m"},
        {"name": "I/O error, dev sdb",
         "meaning": "Reads or writes to a disk failed.",
         "normal": "not there",
         "alarming": "there → failing disk or controller; I/O becomes slow → check iostat"},
        {"name": "Possible SYN flooding on port N",
         "meaning": "The queue of new connections on that port is full; new connection requests are dropped "
                    "(or answered with SYN cookies).",
         "normal": "not there",
         "alarming": "there → clients cannot connect; the application accepts too slowly or there is a flood"},
        {"name": "task X blocked for more than 120 seconds",
         "meaning": "A task has been stuck in uninterruptible sleep (state D) for over 2 minutes, usually waiting on I/O.",
         "normal": "not there",
         "alarming": "there → the process hangs on disk or network storage"},
        {"name": "eth1: Link down / Link up",
         "meaning": "The network link of an interface went down or came back.",
         "normal": "only at boot",
         "alarming": "repeating → a flapping link: cable, optic or switch port"},
        {"name": "nf_conntrack: table full, dropping packet",
         "meaning": "The connection-tracking table is full; packets of new connections are dropped.",
         "normal": "not there",
         "alarming": "there → new connections fail"},
    ],
    "steps": [
        "Check the timestamps: do the messages match the time of the incident?",
        "Look for the keywords: oom, Killed process, I/O error, SYN flooding, blocked for more than, Link down, dropping.",
        "Nothing relevant? Then the kernel saw no errors: exonerate that and move on.",
    ],
    "next": "OOM → free -m · disk errors or blocked tasks → iostat -xz 1 · TCP drops → sar -n TCP,ETCP 1 · "
            "link down → ip -s link.",
}

PURPOSE_QUESTIONS = [
    {"question": "What does dmesg | tail show you?",
     "key_points": ["the most recent kernel messages"],
     "bonus": ["the last 10 lines of the kernel's message buffer", "errors such as OOM kills, disk errors or dropped connections"]},
    {"question": "Why does Netflix say about dmesg: \"Don't miss this step!\"?",
     "key_points": ["it can show an error that explains the problem directly, in seconds"],
     "bonus": ["for example the OOM killer or disk I/O errors"]},
    {"question": "Why do you add | tail to dmesg?",
     "key_points": ["to see only the last, most recent lines"],
     "bonus": ["the full dmesg output is long and mostly old boot messages"]},
    {"question": "What does dmesg -T change?",
     "key_points": ["it shows readable clock times instead of seconds since boot"]},
    {"question": "Who writes the messages that dmesg shows?",
     "key_points": ["the kernel"],
     "bonus": ["its drivers and subsystems: memory, disks, network"]},
    {"question": "Name two kinds of problems dmesg can reveal.",
     "key_points": ["a first one, for example: OOM kills, disk I/O errors, dropped connections (SYN flooding), "
                    "a network link going down, tasks stuck on I/O",
                    "a second, different one from that same kind of list"]},
    {"question": "A process has suddenly disappeared. Why is dmesg one of the first places to look?",
     "key_points": ["the OOM killer logs there which process it killed"]},
    {"question": "dmesg | tail shows nothing unusual. What do you conclude?",
     "key_points": ["the kernel logged no recent errors, so continue with the next command"],
     "bonus": ["it does not prove there is no problem, only that the kernel saw none"]},
    {"question": "Can dmesg tell you which application is slow? Why or why not?",
     "key_points": ["no: it only shows kernel events, not how fast applications are"],
     "bonus": ["other tools such as pidstat or top show the processes"]},
]

COLUMN_QUESTIONS = [
    {"question": "What does the number in [1880957.563150] mean?",
     "key_points": ["the time of the message in seconds since boot"]},
    {"question": "What does 'invoked oom-killer' mean?",
     "key_points": ["the system ran out of memory and the kernel started killing a process to free it"]},
    {"question": "'Out of memory: Killed process 4412 (riskcalc)'. What happened?",
     "key_points": ["the kernel killed process riskcalc (PID 4412) because memory ran out"]},
    {"question": "What does 'I/O error, dev sdb, sector 88212480' tell you?",
     "key_points": ["reads or writes to disk sdb are failing"],
     "bonus": ["a failing disk or controller; I/O on it becomes slow"]},
    {"question": "'TCP: Possible SYN flooding on port 9001. Dropping request.' What does that mean?",
     "key_points": ["the queue of new connections on port 9001 is full, so new connection requests are dropped"],
     "bonus": ["a real flood, or an application that accepts connections too slowly"]},
    {"question": "'INFO: task ordergw:3342 blocked for more than 120 seconds.' What does that mean?",
     "key_points": ["the task has been stuck for over 2 minutes, usually waiting on I/O"],
     "bonus": ["it is in uninterruptible sleep, state D"]},
    {"question": "'eth1: Link down' followed a few seconds later by 'eth1: Link up', several times. What is going on?",
     "key_points": ["the network link of eth1 keeps going down and up: it is flapping"],
     "bonus": ["a bad cable, optic or switch port"]},
    {"question": "What does 'nf_conntrack: table full, dropping packet' mean?",
     "key_points": ["the connection-tracking table is full, so packets of new connections are dropped"]},
    {"question": "How do you tell whether a dmesg message has anything to do with the incident?",
     "key_points": ["compare its time with the time of the incident"],
     "bonus": ["dmesg -T makes the times readable"]},
    {"question": "The same error repeats in every line of dmesg | tail. What does that tell you?",
     "key_points": ["the problem is ongoing, not a one-off"]},
    {"question": "Which messages in dmesg are usually harmless?",
     "key_points": ["informational ones, such as boot messages or a device being detected"],
     "bonus": ["for example 'perf: interrupt took too long' or a docker interface changing state"]},
]

SITUATIONS = ["quiet", "oom", "disk_error", "syn_flood", "hung_task", "link_flap"]

_BENIGN = [
    "perf: interrupt took too long (2504 > 2500), lowering kernel.perf_event_max_sample_rate to 79750",
    "systemd-journald[412]: Received client request to flush runtime journal.",
    "IPv6: ADDRCONF(NETDEV_CHANGE): veth3a1f2b0: link becomes ready",
    "docker0: port 2(veth3a1f2b0) entered forwarding state",
    "audit: type=1400 audit(1760000000.123:42): apparmor=\"STATUS\" operation=\"profile_replace\" name=\"docker-default\"",
    "EXT4-fs (nvme0n1p2): re-mounted. Opts: errors=remount-ro. Quota mode: none.",
    "device veth9c71d0e entered promiscuous mode",
]


def _stamp(t: float) -> str:
    return f"[{t:13.6f}]"


def situation(rng: random.Random, kind: str) -> dict:
    t = rng.uniform(300_000, 9_000_000)
    lines = []
    # Older harmless lines first, then whatever matters for this situation.
    n_benign = len(_BENIGN) if kind == "quiet" else rng.randint(3, 5)
    for msg in rng.sample(_BENIGN, n_benign):
        t += rng.uniform(50, 40_000)
        lines.append(f"{_stamp(t)} {msg}")
    t += rng.uniform(100, 5_000)

    if kind == "quiet":
        key_points = ["nothing alarming: the kernel logged no errors"]
        bonus = ["only harmless informational messages", "next: continue the checklist (vmstat 1)"]
    elif kind == "oom":
        pid = rng.randint(2000, 40000)
        proc = rng.choice(["riskcalc", "java", "md-replay", "python3"])
        rss = rng.randint(5_000_000, 30_000_000)
        lines += [
            f"{_stamp(t)} ordergw invoked oom-killer: gfp_mask=0x100cca(GFP_HIGHUSER_MOVABLE), order=0, oom_score_adj=0",
            f"{_stamp(t + 0.000210)} Out of memory: Killed process {pid} ({proc}) total-vm:{rss + 812344}kB, "
            f"anon-rss:{rss}kB, file-rss:0kB, shmem-rss:0kB, UID:1001 pgtables:{rss // 500}kB oom_score_adj:0",
            f"{_stamp(t + 0.231004)} oom_reaper: reaped process {pid} ({proc}), now anon-rss:0kB, file-rss:0kB, shmem-rss:0kB",
        ]
        key_points = [f"memory ran out and the kernel (OOM killer) killed process {proc}"]
        bonus = [f"the killed process is {proc}, PID {pid}", "next: free -m, and find out why memory grew"]
    elif kind == "disk_error":
        sector = rng.randint(10_000_000, 900_000_000)
        lines += [
            f"{_stamp(t)} sd 2:0:0:0: [sdb] tag#12 FAILED Result: hostbyte=DID_OK driverbyte=DRIVER_OK cmd_age=31s",
            f"{_stamp(t + 0.000040)} blk_update_request: I/O error, dev sdb, sector {sector} op 0x1:(WRITE) flags 0x800 phys_seg 1 prio class 0",
            f"{_stamp(t + 0.000310)} Buffer I/O error on dev sdb1, logical block {sector // 8}, lost async page write",
            f"{_stamp(t + 4.120011)} blk_update_request: I/O error, dev sdb, sector {sector + 2048} op 0x1:(WRITE) flags 0x800 phys_seg 1 prio class 0",
        ]
        key_points = ["disk sdb has I/O errors: writes to it are failing"]
        bonus = ["a failing disk or controller", "next: iostat -xz 1 for sdb (await, %util)"]
    elif kind == "syn_flood":
        port = rng.choice([9001, 7001, 8443, 5001])
        lines += [
            f"{_stamp(t)} TCP: request_sock_TCP: Possible SYN flooding on port {port}. Sending cookies.  Check SNMP counters.",
            f"{_stamp(t + rng.uniform(30, 90))} TCP: request_sock_TCP: Possible SYN flooding on port {port}. Sending cookies.  Check SNMP counters.",
        ]
        key_points = [f"the queue of new connections on port {port} is overflowing: new connections are dropped or delayed"]
        bonus = ["the application accepts connections too slowly, or clients reconnect in a storm",
                 "next: sar -n TCP,ETCP 1"]
    elif kind == "hung_task":
        lines += [
            f"{_stamp(t)} INFO: task ordergw:3342 blocked for more than 120 seconds.",
            f"{_stamp(t + 0.000012)}       Not tainted 5.15.0-91-generic #101-Ubuntu",
            f"{_stamp(t + 0.000020)} \"echo 0 > /proc/sys/kernel/hung_task_timeout_secs\" disables this message.",
            f"{_stamp(t + 0.000031)} task:ordergw         state:D stack:    0 pid: 3342 ppid:     1 flags:0x00004000",
            f"{_stamp(t + 0.000040)} Call Trace:",
            f"{_stamp(t + 0.000044)}  <TASK>",
            f"{_stamp(t + 0.000051)}  __schedule+0x2cd/0x890",
            f"{_stamp(t + 0.000058)}  io_schedule+0x46/0x70",
        ]
        key_points = ["process ordergw has been stuck for over 2 minutes, waiting on I/O"]
        bonus = ["it is in state D (uninterruptible sleep)", "next: vmstat 1 (b, wa) and iostat -xz 1"]
    else:  # link_flap
        for _ in range(2):
            lines += [
                f"{_stamp(t)} mlx5_core 0000:3b:00.1 eth1: Link down",
                f"{_stamp(t + 0.004)} bond0: (slave eth1): link status definitely down, disabling slave",
                f"{_stamp(t + rng.uniform(2, 6))} mlx5_core 0000:3b:00.1 eth1: Link up",
            ]
            t += rng.uniform(40, 200)
        key_points = ["the network link of eth1 keeps going down and coming back up: it is flapping"]
        bonus = ["a bad cable, optic or switch port", "next: ip -s link for errors on eth1"]

    lines = lines[-10:]  # what | tail shows
    return {
        "situation": kind,
        "prompt": "Traders report problems on the order gateway. You run `dmesg | tail`:",
        "output": "\n".join(lines),
        "key_points": key_points,
        "bonus": bonus,
    }
