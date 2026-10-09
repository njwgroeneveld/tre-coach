"""Lesson 9: sar -n TCP,ETCP 1 — new TCP connections and TCP errors, every second."""

import random

from services.lessons.common import ampm, clock, host, sysstat_header

COMMAND = "sar -n TCP,ETCP 1"

CARD = {
    "title": "sar -n TCP,ETCP 1 — TCP connections, segments and retransmits per second",
    "summary": (
        "TCP shows new connections and segments per second; ETCP shows TCP errors. Retransmits are the key "
        "signal: a sign of a network or server problem, such as an unreliable network or an overloaded host "
        "dropping packets. On a trading host every retransmit delays an order or its acknowledgement."
    ),
    "example": (
        "12:17:19 AM  active/s passive/s    iseg/s    oseg/s\n"
        "12:17:20 AM      1.00      0.00  10233.00  18846.00\n"
        "\n"
        "12:17:19 AM  atmptf/s  estres/s retrans/s isegerr/s   orsts/s\n"
        "12:17:20 AM      0.00      0.00      0.00      0.00      0.00"
    ),
    "fields": [
        {"name": "active/s", "meaning": "New connections this host started (outbound, connect()).",
         "normal": "low and steady", "alarming": "a sudden high number → reconnect storm"},
        {"name": "passive/s", "meaning": "New connections other hosts started to this host (inbound, accept()).",
         "normal": "low and steady", "alarming": "a sudden high number → many clients (re)connecting"},
        {"name": "iseg/s, oseg/s", "meaning": "TCP segments received and sent per second: the TCP workload.",
         "normal": "depends", "alarming": "—"},
        {"name": "retrans/s", "meaning": "Segments retransmitted per second.",
         "normal": "near 0",
         "alarming": "above 0 and steady → packets are lost: a network or server problem; each adds latency"},
        {"name": "atmptf/s", "meaning": "Connection attempts that failed.", "normal": "0",
         "alarming": "above 0 → the other side refuses or cannot be reached"},
        {"name": "estres/s", "meaning": "Established connections that were reset.", "normal": "0",
         "alarming": "above 0 → connections are being torn down"},
        {"name": "orsts/s", "meaning": "Resets sent by this host (RST).", "normal": "near 0",
         "alarming": "high → this host refuses connections (nothing listening, or the listen queue is full)"},
        {"name": "isegerr/s", "meaning": "Segments received with errors.", "normal": "0", "alarming": "above 0 → corrupt packets"},
    ],
    "steps": [
        "Look at retrans/s first: is the host retransmitting? Compare it with oseg/s for a rate.",
        "Look at active/s and passive/s: is there a burst of new connections?",
        "Look at the errors: failed attempts, resets.",
    ],
    "next": "Retransmits → ip -s link for drops and errors, ss -ti for the affected connection · "
            "resets or failed attempts → is the service listening, is its listen queue full (dmesg)?",
}

PURPOSE_QUESTIONS = [
    {"question": "What does sar -n TCP,ETCP 1 show you?",
     "key_points": ["new TCP connections and segments per second, and TCP errors such as retransmits"]},
    {"question": "What is the difference between the TCP and the ETCP report?",
     "key_points": ["TCP: connections and segments (the workload)", "ETCP: errors (retransmits, resets, failures)"]},
    {"question": "Why are retransmits so important on a trading host?",
     "key_points": ["each retransmit delays an order or its acknowledgement"],
     "bonus": ["a lost segment is resent only after a timeout or duplicate ACKs"]},
    {"question": "What can cause TCP retransmits?",
     "key_points": ["packets lost on the way: an unreliable or overloaded network, or a host dropping packets"]},
    {"question": "How do active/s and passive/s help you as a rough measure of load?",
     "key_points": ["they show how many new outbound (active) and inbound (passive) connections there are"]},
    {"question": "Can sar -n TCP,ETCP tell you which connection retransmits?",
     "key_points": ["no; ss -ti shows per connection"]},
    {"question": "When in the checklist do you run sar -n TCP,ETCP?",
     "key_points": ["after sar -n DEV, near the end, to check the TCP layer"]},
    {"question": "In USE terms, what do retransmits indicate?",
     "key_points": ["saturation or errors on the network path: packets are being lost"]},
]

COLUMN_QUESTIONS = [
    {"question": "What does active/s count?",
     "key_points": ["new connections this host starts (outbound)"]},
    {"question": "What does passive/s count?",
     "key_points": ["new connections other hosts start to this host (inbound)"]},
    {"question": "What do iseg/s and oseg/s count?",
     "key_points": ["TCP segments received and sent per second"]},
    {"question": "What does retrans/s count?",
     "key_points": ["TCP segments retransmitted per second"]},
    {"question": "retrans/s is 60 and oseg/s is 6000. How bad is that?",
     "key_points": ["about 1% of segments is retransmitted: clearly packet loss"]},
    {"question": "What does orsts/s count, and what does a high value suggest?",
     "key_points": ["resets sent by this host", "it refuses connections: nothing listening, or a full queue"]},
    {"question": "What does atmptf/s count?",
     "key_points": ["connection attempts that failed"]},
    {"question": "What does estres/s count?",
     "key_points": ["established connections that were reset"]},
    {"question": "active/s jumps from 1 to 900. What could be going on?",
     "key_points": ["a reconnect storm: this host keeps opening new connections"]},
    {"question": "Is 'active' always outbound and 'passive' always inbound?",
     "key_points": ["roughly, but not strictly (for example a connection from localhost to localhost is both)"]},
]

SITUATIONS = ["normal", "retransmits", "reconnect_storm", "refusing"]


def situation(rng: random.Random, kind: str) -> dict:
    hostname = host(rng)
    h, m, s = clock(rng)
    t0, t1 = ampm(h, m, s), ampm(h, m, s + 1)
    active, passive = rng.choice([0.0, 1.0, 2.0]), rng.choice([0.0, 1.0])
    iseg, oseg = rng.uniform(4_000, 15_000), rng.uniform(4_000, 20_000)
    atmptf = estres = retrans = isegerr = orsts = 0.0
    if kind == "retransmits":
        retrans = oseg * rng.uniform(0.006, 0.02)
    elif kind == "reconnect_storm":
        active = rng.uniform(400, 1200)
        atmptf = active * rng.uniform(0.6, 0.95)
        retrans = rng.uniform(0, 3)
    elif kind == "refusing":
        passive = rng.uniform(5, 40)
        orsts = rng.uniform(300, 1500)
    else:
        retrans = rng.choice([0.0, 0.0, 1.0])

    output = "\n".join([
        sysstat_header(rng, hostname, 16), "",
        f"{t0}  active/s passive/s    iseg/s    oseg/s",
        f"{t1} {active:9.2f} {passive:9.2f} {iseg:9.2f} {oseg:9.2f}",
        "",
        f"{t0}  atmptf/s  estres/s retrans/s isegerr/s   orsts/s",
        f"{t1} {atmptf:9.2f} {estres:9.2f} {retrans:9.2f} {isegerr:9.2f} {orsts:9.2f}",
    ])

    if kind == "normal":
        key_points = ["TCP looks healthy: few new connections and (almost) no retransmits or errors"]
        bonus = ["next: continue the checklist (top)"]
    elif kind == "retransmits":
        key_points = ["the host is retransmitting TCP segments: packets are being lost"]
        bonus = ["retrans/s against oseg/s is around 1%: far too high",
                 "every retransmit delays orders or acks", "next: ip -s link for drops, ss -ti per connection"]
    elif kind == "reconnect_storm":
        key_points = ["this host is opening very many new connections and most attempts fail: a reconnect storm"]
        bonus = ["active/s and atmptf/s are both very high",
                 "the service it connects to is down or refusing", "next: check that service and the client's retry settings"]
    else:
        key_points = ["this host is sending many resets: it is refusing connections"]
        bonus = ["orsts/s is very high while new inbound connections come in",
                 "nothing is listening on the port, or the listen queue is full",
                 "next: is the service running? dmesg for 'SYN flooding'"]

    return {
        "situation": kind,
        "prompt": "You run `sar -n TCP,ETCP 1` on the order gateway (one report shown):",
        "output": output,
        "key_points": key_points,
        "bonus": bonus,
    }
