"""Lesson 8: sar -n DEV 1 — throughput per network interface."""

import random

from services.lessons.common import ampm, clock, host, sysstat_header

COMMAND = "sar -n DEV 1"

CARD = {
    "title": "sar -n DEV 1 — how much traffic each network interface carries",
    "summary": (
        "sar -n DEV shows throughput per network interface, every second. Use it to see the workload "
        "(how much is received and sent) and whether an interface is at its limit. To compare with the link "
        "speed, convert: kB/s × 8 / 1000 = Mbit/s. A 1 Gbit link tops out around 120,000 kB/s; 10 Gbit "
        "around 1,200,000 kB/s."
    ),
    "example": (
        "12:16:48 AM     IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil\n"
        "12:16:49 AM      eth0  18763.00   5032.00  20686.42    478.30      0.00      0.00      0.00      0.00\n"
        "12:16:49 AM        lo     14.00     14.00      1.36      1.36      0.00      0.00      0.00      0.00"
    ),
    "fields": [
        {"name": "IFACE", "meaning": "The interface: eth0, eth1, bond0, lo (loopback, local traffic only).",
         "normal": "—", "alarming": "—"},
        {"name": "rxpck/s, txpck/s", "meaning": "Packets received and sent per second.",
         "normal": "depends", "alarming": "a sudden jump → a burst or a flood"},
        {"name": "rxkB/s, txkB/s", "meaning": "KB received and sent per second: the throughput.",
         "normal": "well below the link speed",
         "alarming": "near the link speed (1 Gbit ≈ 120,000 kB/s) → the link is full; packets queue and drop"},
        {"name": "rxmcst/s", "meaning": "Multicast packets received per second.",
         "normal": "high on a market-data interface (feeds are often multicast)", "alarming": "—"},
        {"name": "%ifutil", "meaning": "Utilization of the interface: the busier direction against the link speed.",
         "normal": "below about 70%",
         "alarming": "near 100% → saturated (it can read 0.00 when the speed is unknown)"},
    ],
    "steps": [
        "Find the interfaces that carry traffic.",
        "Convert their kB/s to Mbit/s and compare with the link speed.",
        "Ask whether the traffic is on the interface you expect (exchange traffic on the exchange NIC?).",
    ],
    "next": "A full link → find what sends or receives (who is the client?) · drops or retransmits → "
            "sar -n TCP,ETCP 1 and ip -s link.",
}

PURPOSE_QUESTIONS = [
    {"question": "What does sar -n DEV 1 show you?",
     "key_points": ["how much traffic each network interface receives and sends, every second"]},
    {"question": "What are the two things you use sar -n DEV for?",
     "key_points": ["see the network workload", "check whether an interface is at its limit"]},
    {"question": "Why do you need to know the link speed to read sar -n DEV?",
     "key_points": ["to tell whether the throughput is near the maximum of the link"]},
    {"question": "How do you convert rxkB/s to Mbit/s?",
     "key_points": ["multiply by 8 and divide by 1000"]},
    {"question": "In USE terms, what does sar -n DEV show for a network interface?",
     "key_points": ["utilization: throughput against the link speed"],
     "bonus": ["errors and drops are in ip -s link; retransmits in sar -n TCP,ETCP"]},
    {"question": "Can sar -n DEV show packet loss?",
     "key_points": ["no; it shows throughput; drops and errors need ip -s link (or sar -n EDEV)"]},
    {"question": "Why is the 'lo' interface usually not interesting?",
     "key_points": ["it is local traffic on the host itself, not real network traffic"]},
    {"question": "On a trading host, why look at which interface the traffic is on, not only how much?",
     "key_points": ["traffic on the wrong interface (for example the management link) means a routing or config problem"]},
]

COLUMN_QUESTIONS = [
    {"question": "What do rxkB/s and txkB/s show?",
     "key_points": ["KB received and sent per second on that interface"]},
    {"question": "What do rxpck/s and txpck/s show?",
     "key_points": ["packets received and sent per second"]},
    {"question": "What does rxmcst/s show, and where is it high?",
     "key_points": ["multicast packets received per second", "high on market-data interfaces"]},
    {"question": "What does %ifutil show?",
     "key_points": ["the utilization of the interface against its link speed"]},
    {"question": "eth0 is a 1 Gbit link and shows rxkB/s 117,000. Is it full?",
     "key_points": ["yes: about 940 Mbit/s, near the 1 Gbit maximum"]},
    {"question": "eth1 is a 10 Gbit link and shows rxkB/s 22,000. Is it full?",
     "key_points": ["no: about 176 Mbit/s, far below 10 Gbit"]},
    {"question": "%ifutil shows 0.00 while rxkB/s is high. What is going on?",
     "key_points": ["sar does not know the link speed, so it cannot compute utilization; convert kB/s yourself"]},
    {"question": "About how many kB/s does a full 10 Gbit link carry?",
     "key_points": ["about 1,200,000 kB/s (roughly 1.2 GB/s)"]},
    {"question": "rxpck/s is high but rxkB/s is low. What kind of traffic is that?",
     "key_points": ["many small packets"],
     "bonus": ["typical for market data or order messages; packets per second can be a limit too"]},
]

SITUATIONS = ["normal", "rx_line_rate", "tx_saturated", "multicast_feed"]

_HDR = "     IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s   rxcmp/s   txcmp/s  rxmcst/s   %ifutil"


def _row(t, iface, rxp, txp, rxk, txk, mc, speed_mbit) -> str:
    util = max(rxk, txk) * 8 / 1000 / speed_mbit * 100 if speed_mbit else 0.0
    return f"{t} {iface:>9} {rxp:9.2f} {txp:9.2f} {rxk:9.2f} {txk:9.2f} {0:9.2f} {0:9.2f} {mc:9.2f} {util:9.2f}"


def situation(rng: random.Random, kind: str) -> dict:
    hostname = host(rng)
    h, m, s = clock(rng)
    t = ampm(h, m, s + 1)
    # eth0: 1 Gbit management; eth1: 10 Gbit to the exchange.
    eth0 = dict(rxp=rng.uniform(20, 300), txp=rng.uniform(20, 300), rxk=rng.uniform(5, 80), txk=rng.uniform(5, 80), mc=0)
    eth1 = dict(rxp=rng.uniform(8_000, 25_000), txp=rng.uniform(6_000, 20_000), rxk=rng.uniform(4_000, 30_000),
                txk=rng.uniform(3_000, 20_000), mc=0)
    if kind == "rx_line_rate":
        eth0.update(rxp=rng.uniform(78_000, 82_000), rxk=rng.uniform(116_000, 118_500))
    elif kind == "tx_saturated":
        eth1.update(txp=rng.uniform(780_000, 820_000), txk=rng.uniform(1_150_000, 1_190_000))
    elif kind == "multicast_feed":
        mc = rng.uniform(150_000, 400_000)
        eth1.update(rxp=mc + rng.uniform(5_000, 20_000), rxk=mc * rng.uniform(0.15, 0.3), mc=mc)

    lines = [sysstat_header(rng, hostname, 16), "", t + _HDR,
             _row(t, "eth0", eth0["rxp"], eth0["txp"], eth0["rxk"], eth0["txk"], eth0["mc"], 1000),
             _row(t, "eth1", eth1["rxp"], eth1["txp"], eth1["rxk"], eth1["txk"], eth1["mc"], 10_000),
             _row(t, "lo", 14.0, 14.0, 1.36, 1.36, 0, 0)]

    if kind == "normal":
        key_points = ["the network is fine: both interfaces are far below their link speed"]
        bonus = ["eth1 carries the exchange traffic as expected", "next: continue the checklist"]
    elif kind == "rx_line_rate":
        key_points = ["eth0, the 1 Gbit management link, is receiving at line rate: it is full"]
        bonus = ["about 117,000 kB/s ≈ 940 Mbit/s", "eth1 to the exchange is quiet",
                 "something floods eth0, or traffic goes over the wrong interface; expect drops"]
    elif kind == "tx_saturated":
        key_points = ["eth1, the 10 Gbit exchange link, is sending at line rate: it is full"]
        bonus = ["about 1,170,000 kB/s ≈ 9.4 Gbit/s; %ifutil near 100",
                 "orders share the link with something big (a backup?); expect queueing and latency",
                 "next: find what sends; sar -n TCP,ETCP 1 for retransmits"]
    else:
        key_points = ["eth1 receives a lot of multicast market data, but it is well below its link speed: normal"]
        bonus = ["many small packets: high rxpck/s and rxmcst/s, modest kB/s",
                 "packets per second can still be a limit for the NIC and the CPU handling it"]

    return {
        "situation": kind,
        "prompt": "The order gateway has eth0 (1 Gbit, management) and eth1 (10 Gbit, to the exchange). "
                  "You run `sar -n DEV 1` (one report shown):",
        "output": "\n".join(lines),
        "key_points": key_points,
        "bonus": bonus,
    }
