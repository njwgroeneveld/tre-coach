"""Lesson 7: free -m — memory in MB, and how much is really available."""

import random

COMMAND = "free -m"

CARD = {
    "title": "free -m — memory in MB, and how much is really available",
    "summary": (
        "free shows memory and swap in megabytes (-m). Linux uses spare memory for the page cache and gives it "
        "back quickly when applications need it, so a small 'free' value is normal. The column to read is "
        "'available': memory applications can still get without swapping."
    ),
    "example": (
        "               total        used        free      shared  buff/cache   available\n"
        "Mem:          245998       24545      221453          83         600      222053\n"
        "Swap:              0           0           0"
    ),
    "fields": [
        {"name": "total", "meaning": "All installed memory.", "normal": "—", "alarming": "—"},
        {"name": "used", "meaning": "Memory used by processes and the kernel (not counting cache).",
         "normal": "depends", "alarming": "close to total → little left"},
        {"name": "free", "meaning": "Memory not used for anything, not even cache.",
         "normal": "often small: Linux fills spare memory with cache",
         "alarming": "small on its own is not a problem → read 'available'"},
        {"name": "shared", "meaning": "Shared memory (tmpfs and shared segments).", "normal": "small", "alarming": "—"},
        {"name": "buff/cache", "meaning": "Memory used for disk buffers and the page cache; mostly reclaimable.",
         "normal": "large", "alarming": "near zero → more reads go to disk (check iostat)"},
        {"name": "available", "meaning": "Estimate of memory applications can still get without swapping (free + reclaimable cache).",
         "normal": "a good share of total",
         "alarming": "a few % of total → memory pressure; swapping or the OOM killer may follow"},
        {"name": "Swap used", "meaning": "How much is pushed out to swap.",
         "normal": "0, or a constant amount",
         "alarming": "large and growing → out of memory; confirm with vmstat si/so"},
    ],
    "steps": [
        "Read 'available', not 'free': is there memory left for applications?",
        "Check buff/cache: a large cache is good, not a problem.",
        "Check Swap used: is anything swapped out? vmstat si/so tells whether it happens now.",
    ],
    "next": "Low available → find the process with the most memory (top, sort by RES) · "
            "swap used → vmstat 1 si/so to see whether it swaps now · OOM suspicion → dmesg | tail.",
}

PURPOSE_QUESTIONS = [
    {"question": "What does free -m show you?",
     "key_points": ["how much memory and swap is used, free and available, in MB"]},
    {"question": "What does the -m option do?",
     "key_points": ["show the values in megabytes"]},
    {"question": "Which column of free tells you whether the host is short of memory?",
     "key_points": ["available"]},
    {"question": "Why is a small 'free' value usually not a problem on Linux?",
     "key_points": ["Linux uses spare memory for cache and gives it back when applications need it"]},
    {"question": "What is the website 'linuxatemyram' about?",
     "key_points": ["the confusion that Linux seems to use all memory, while it is only cache that is available"]},
    {"question": "Can free tell you which process uses the memory?",
     "key_points": ["no; top or ps (sorted by RES) show that"]},
    {"question": "free shows swap in use. Does that mean the host is swapping right now?",
     "key_points": ["not necessarily: it may have swapped earlier; vmstat si/so shows whether it happens now"]},
    {"question": "In USE terms, what does free show for memory?",
     "key_points": ["utilization: how much memory is used or still available"],
     "bonus": ["saturation is swapping (vmstat si/so) or OOM kills (dmesg)"]},
]

COLUMN_QUESTIONS = [
    {"question": "What is the difference between 'free' and 'available'?",
     "key_points": ["free is memory used for nothing at all",
                    "available also counts cache that can be given back to applications"]},
    {"question": "What is buff/cache?",
     "key_points": ["memory used for disk buffers and the page cache, which can mostly be reclaimed"]},
    {"question": "buff/cache is near zero. Why can that hurt performance?",
     "key_points": ["almost nothing is cached, so more reads must go to disk"]},
    {"question": "total 64000, free 900, buff/cache 48000, available 51000. Is the host short of memory?",
     "key_points": ["no: 51000 MB is available; the low free is just cache"]},
    {"question": "total 64000, buff/cache 600, available 1200. Is the host short of memory?",
     "key_points": ["yes: under 2% is available; swapping or the OOM killer is likely"]},
    {"question": "What does 'used' count?",
     "key_points": ["memory used by processes and the kernel, not counting cache"]},
    {"question": "What does the Swap line show?",
     "key_points": ["how much swap space exists, is used and is free"]},
    {"question": "Swap used is 2000 MB, but available is 40000 MB and vmstat si/so are 0. What happened?",
     "key_points": ["the host swapped some memory out earlier; it is not swapping now"]},
    {"question": "What does 'shared' usually contain?",
     "key_points": ["shared memory: tmpfs files and shared memory segments"]},
    {"question": "Which value would you put on a memory alert: free or available? Why?",
     "key_points": ["available, because free is low on any healthy host that uses cache"]},
]

SITUATIONS = ["plenty", "healthy_cache", "low_available", "swapping", "old_swap"]


def _free(total, used, free_, shared, cache, available, swap_total, swap_used) -> str:
    return ("               total        used        free      shared  buff/cache   available\n"
            f"Mem:    {total:12d}{used:12d}{free_:12d}{shared:12d}{cache:12d}{available:12d}\n"
            f"Swap:   {swap_total:12d}{swap_used:12d}{swap_total - swap_used:12d}")


def situation(rng: random.Random, kind: str) -> dict:
    total = rng.choice([31_998, 64_221, 128_520, 257_604])
    shared = rng.randint(20, 600)
    swap_total = rng.choice([0, 8_191]) if kind in ("plenty", "healthy_cache") else 8_191

    if kind == "plenty":
        used = int(total * rng.uniform(0.1, 0.3))
        cache = int(total * rng.uniform(0.05, 0.15))
        swap_used = 0
    elif kind == "healthy_cache":
        used = int(total * rng.uniform(0.1, 0.2))
        cache = int(total * rng.uniform(0.75, 0.86))  # leaves free at only a few %
        swap_used = 0
    elif kind == "low_available":
        used = int(total * rng.uniform(0.94, 0.97))
        cache = int(total * rng.uniform(0.01, 0.02))
        swap_used = rng.randint(0, 300)
    elif kind == "swapping":
        used = int(total * rng.uniform(0.95, 0.975))
        cache = int(total * rng.uniform(0.005, 0.015))
        swap_used = rng.randint(4_000, 7_800)
    else:  # old_swap
        used = int(total * rng.uniform(0.2, 0.35))
        cache = int(total * rng.uniform(0.3, 0.5))
        swap_used = rng.randint(800, 2_500)
    free_ = max(100, total - used - cache)
    available = int(free_ + cache * rng.uniform(0.8, 0.95))

    if kind == "plenty":
        key_points = ["plenty of memory is free and available: no memory problem"]
        bonus = ["no swap in use", "next: continue the checklist"]
    elif kind == "healthy_cache":
        key_points = ["memory is fine: most of it is cache, and plenty is available"]
        bonus = ["free is small, but that is only because Linux uses spare memory as cache",
                 "read available, not free"]
    elif kind == "low_available":
        key_points = ["the host is short of memory: very little is available"]
        bonus = ["buff/cache is nearly gone, so disk reads rise too",
                 "swapping or the OOM killer may follow", "next: find the process using the memory (top, sort by RES)"]
    elif kind == "swapping":
        key_points = ["the host is out of memory and has pushed a lot to swap"]
        bonus = ["available is tiny, swap used is large",
                 "next: vmstat 1 si/so to see the swapping now; find the process using the memory"]
    else:
        key_points = ["memory is fine now: plenty available; the swap in use was pushed out earlier"]
        bonus = ["check vmstat si/so: if 0, nothing is swapping now"]

    return {
        "situation": kind,
        "prompt": "You run `free -m` on the risk engine:",
        "output": _free(total, used, free_, shared, cache, available, swap_total, swap_used if swap_total else 0),
        "key_points": key_points,
        "bonus": bonus,
    }
