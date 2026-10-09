"""Small helpers shared by the lesson generators: hosts, clocks and sysstat headers."""

import random

HOSTS = ["ogw-prd-01", "md-feed-02", "risk-prd-03", "exch-conn-02", "tradebot-01", "ogw-prd-04"]


def host(rng: random.Random) -> str:
    return rng.choice(HOSTS)


def clock(rng: random.Random) -> tuple[int, int, int]:
    return rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 50)


def hms(h: int, m: int, s: int) -> str:
    return f"{h:02d}:{m:02d}:{s:02d}"


def ampm(h: int, m: int, s: int) -> str:
    """sysstat-style 12-hour time: '07:38:49 PM'."""
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12:02d}:{m:02d}:{s:02d} {suffix}"


def sysstat_header(rng: random.Random, hostname: str, cpus: int) -> str:
    date = f"{rng.randint(1, 12):02d}/{rng.randint(1, 28):02d}/2026"
    return f"Linux 5.15.0-91-generic ({hostname}) \t{date} \t_x86_64_\t({cpus} CPU)"


def split_percent(rng: random.Random, us: float, sy: float, wa: float, st: float = 0.0) -> tuple:
    """Round CPU percentages and make idle the remainder, so the row adds up to 100."""
    us, sy, wa, st = (max(0, round(x)) for x in (us, sy, wa, st))
    idle = max(0, 100 - us - sy - wa - st)
    return us, sy, idle, wa, st
