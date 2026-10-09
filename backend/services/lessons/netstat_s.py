"""Lesson 13: netstat -s — protocol counters: retransmits, buffer errors, listen-queue overflows."""

import random

COMMAND = "netstat -s"

CARD = {
    "title": "netstat -s — protocol counters since boot: what TCP and UDP lost, and why",
    "summary": (
        "netstat -s prints counters per protocol (Ip, Tcp, Udp, TcpExt, ...). They explain why packets were "
        "lost at the socket level: retransmits, receive buffer errors, packets pruned because a socket buffer "
        "overran, listen-queue overflows. Like ip -s link, the counters count since boot: compare two "
        "snapshots and look at what grows. It is long, so filter it with grep."
    ),
    "example": (
        "Tcp:\n"
        "    11023122 segments sent out\n"
        "    48211 segments retransmitted\n"
        "Udp:\n"
        "    4211 packet receive errors\n"
        "    4211 receive buffer errors\n"
        "TcpExt:\n"
        "    312 packets pruned from receive queue because of socket buffer overrun\n"
        "    1201 times the listen queue of a socket overflowed\n"
        "    1201 SYNs to LISTEN sockets dropped"
    ),
    "fields": [
        {"name": "segments retransmitted (Tcp)", "meaning": "TCP segments sent again since boot.",
         "normal": "grows slowly, a tiny share of segments sent out",
         "alarming": "growing fast → packet loss on TCP connections"},
        {"name": "receive buffer errors (Udp)", "meaning": "UDP packets dropped because the socket's receive buffer was full.",
         "normal": "0, or not growing",
         "alarming": "growing → the application reads too slowly or the buffer is too small; for market data: gaps"},
        {"name": "packet receive errors (Udp)", "meaning": "UDP packets that could not be delivered (includes buffer errors).",
         "normal": "not growing", "alarming": "growing → see receive buffer errors"},
        {"name": "packets pruned ... socket buffer overrun (TcpExt)", "meaning": "TCP data thrown away because a socket buffer overran.",
         "normal": "0, or not growing", "alarming": "growing → an application cannot keep up with incoming TCP data"},
        {"name": "times the listen queue of a socket overflowed / SYNs to LISTEN sockets dropped (TcpExt)",
         "meaning": "New connections dropped because a listening socket's accept queue was full.",
         "normal": "0, or not growing", "alarming": "growing → the server accepts connections too slowly"},
        {"name": "failed connection attempts, resets", "meaning": "Connections that could not be made, or were reset.",
         "normal": "grows slowly", "alarming": "growing fast → connection trouble"},
    ],
    "steps": [
        "Filter for the counters that matter (retrans, errors, pruned, overflow).",
        "Take two snapshots a few seconds apart.",
        "Read what grows: retransmits (the network), buffer errors and pruning (the application keeps up too slowly), "
        "listen overflows (the server accepts too slowly).",
    ],
    "next": "Retransmits → ss -ti for the connection · UDP buffer errors → a bigger socket buffer and a faster reader · "
            "listen overflows → the accepting process (and its backlog).",
}

PURPOSE_QUESTIONS = [
    {"question": "What does netstat -s show you?",
     "key_points": ["counters per network protocol (TCP, UDP, IP) since boot"]},
    {"question": "Why compare two snapshots of netstat -s instead of reading one?",
     "key_points": ["the counters count since boot; only what grows now matters"]},
    {"question": "Why do you usually pipe netstat -s through grep?",
     "key_points": ["the output is very long; grep keeps the counters you care about"]},
    {"question": "What can netstat -s explain that ip -s link cannot?",
     "key_points": ["losses at the socket and protocol level, such as full socket buffers or listen queues"]},
    {"question": "Why does netstat -s matter for market data received over UDP?",
     "key_points": ["it shows UDP packets dropped because the receive buffer was full, which means gaps in the feed"]},
    {"question": "Which netstat -s counter matches sar's retrans/s?",
     "key_points": ["segments retransmitted"]},
    {"question": "Can netstat -s tell you which socket is affected?",
     "key_points": ["no; it is host-wide; ss shows per socket"]},
    {"question": "In USE terms, what do netstat -s's drop counters show?",
     "key_points": ["saturation and errors at the protocol level (for example buffers or queues that overflow)"]},
]

COLUMN_QUESTIONS = [
    {"question": "What does 'segments retransmitted' count?",
     "key_points": ["TCP segments sent again since boot"]},
    {"question": "What does 'receive buffer errors' under Udp count?",
     "key_points": ["UDP packets dropped because the socket's receive buffer was full"]},
    {"question": "UDP receive buffer errors grow by 4000 in five seconds on the market-data host. What does that mean?",
     "key_points": ["market-data packets are being dropped: the handler reads too slowly or its buffer is too small"],
     "bonus": ["the feed has gaps"]},
    {"question": "What does 'packets pruned from receive queue because of socket buffer overrun' mean?",
     "key_points": ["TCP data thrown away because a socket buffer was full: the application did not keep up"]},
    {"question": "What does 'times the listen queue of a socket overflowed' mean?",
     "key_points": ["new connections were dropped because a server's accept queue was full"]},
    {"question": "What does 'SYNs to LISTEN sockets dropped' mean?",
     "key_points": ["connection requests dropped at a listening socket"]},
    {"question": "segments retransmitted is 48211 in both snapshots, five seconds apart. Is there a problem now?",
     "key_points": ["no: the retransmits happened earlier; none now"]},
    {"question": "segments retransmitted grows by 300 in five seconds while 60000 segments are sent. How bad is that?",
     "key_points": ["about 0.5%: real packet loss"]},
    {"question": "What does 'failed connection attempts' count?",
     "key_points": ["connections this host tried to open that did not succeed"]},
    {"question": "What is the difference between 'packet receive errors' and 'receive buffer errors' under Udp?",
     "key_points": ["receive errors count every undelivered packet; buffer errors are the ones dropped because the buffer was full"]},
]

SITUATIONS = ["steady", "tcp_retrans", "udp_buffers", "listen_overflow"]


def _snapshot(c: dict) -> str:
    return (f"    {c['sent']} segments sent out\n"
            f"    {c['retrans']} segments retransmitted\n"
            f"    {c['rcv_err']} packet receive errors\n"
            f"    {c['buf_err']} receive buffer errors\n"
            f"    {c['pruned']} packets pruned from receive queue because of socket buffer overrun\n"
            f"    {c['overflow']} times the listen queue of a socket overflowed\n"
            f"    {c['overflow']} SYNs to LISTEN sockets dropped")


def situation(rng: random.Random, kind: str) -> dict:
    sent = rng.randint(10**8, 10**9)
    c1 = dict(sent=sent, retrans=sent // rng.randint(4000, 20000), rcv_err=rng.randint(0, 300),
              pruned=rng.randint(0, 50), overflow=rng.randint(0, 20))
    c1["buf_err"] = c1["rcv_err"]
    c2 = dict(c1)
    delta = rng.randint(40_000, 90_000)
    c2["sent"] = c1["sent"] + delta
    c2["retrans"] = c1["retrans"] + rng.choice([0, 0, 1])
    if kind == "tcp_retrans":
        c2["retrans"] = c1["retrans"] + int(delta * rng.uniform(0.006, 0.02))
    elif kind == "udp_buffers":
        grow = rng.randint(2_000, 9_000)
        c2["rcv_err"] = c1["rcv_err"] + grow
        c2["buf_err"] = c1["buf_err"] + grow
    elif kind == "listen_overflow":
        c2["overflow"] = c1["overflow"] + rng.randint(200, 1500)

    grep = "netstat -s | grep -E 'segments (sent|retrans)|receive (buffer )?errors|pruned|listen queue|SYNs to LISTEN'"
    output = f"$ {grep}\n{_snapshot(c1)}\n\n$ sleep 5; {grep}\n{_snapshot(c2)}"

    if kind == "steady":
        key_points = ["nothing is being lost now: none of the counters grows (meaningfully) between the snapshots"]
        bonus = ["the old values happened earlier", "next: continue elsewhere"]
    elif kind == "tcp_retrans":
        key_points = ["TCP is retransmitting a lot right now: packets are being lost"]
        bonus = ["segments retransmitted grows by about 1% of the segments sent",
                 "next: ss -ti to find the connection, ip -s link for interface drops"]
    elif kind == "udp_buffers":
        key_points = ["UDP packets are dropped because a socket's receive buffer is full"]
        bonus = ["on a market-data host that means gaps in the feed",
                 "the handler reads too slowly or its buffer is too small",
                 "next: the handler's CPU (pidstat), and a larger receive buffer"]
    else:
        key_points = ["new connections are dropped: a listening socket's queue keeps overflowing"]
        bonus = ["the server accepts connections too slowly, or there is a connection storm",
                 "next: the accepting process; dmesg may show 'SYN flooding'"]

    return {
        "situation": kind,
        "prompt": "You check the protocol counters on the market-data host twice, five seconds apart:",
        "output": output,
        "key_points": key_points,
        "bonus": bonus,
    }
