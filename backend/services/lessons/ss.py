"""Lesson 12: ss -ti — TCP details per connection: queues, round-trip time, retransmits."""

import random

COMMAND = "ss -ti"

CARD = {
    "title": "ss -ti — per TCP connection: queues, round-trip time and retransmits",
    "summary": (
        "ss lists sockets; -t limits it to TCP and -i adds internal TCP details per connection. Where "
        "sar -n TCP,ETCP tells you the host retransmits, ss -ti tells you which connection: its queues, its "
        "round-trip time (rtt), its retransmit timeout (rto) and its retransmits. Add a filter such as "
        "'dst 10.99.4.20' to see one exchange session."
    ),
    "example": (
        "State  Recv-Q Send-Q   Local Address:Port   Peer Address:Port\n"
        "ESTAB  0      0          10.20.1.15:41872     10.99.4.20:9001\n"
        "\t cubic wscale:7,7 rto:204 rtt:0.352/0.051 mss:1448 pmtu:1500 cwnd:10 bytes_acked:812344112 "
        "segs_out:1201123 segs_in:988122 send 329.1Mbps minrtt:0.31"
    ),
    "fields": [
        {"name": "State", "meaning": "The TCP state; ESTAB is an open connection.", "normal": "ESTAB", "alarming": "—"},
        {"name": "Recv-Q", "meaning": "Bytes received but not yet read by the application.",
         "normal": "0 or near 0", "alarming": "large and staying → the application reads too slowly"},
        {"name": "Send-Q", "meaning": "Bytes sent but not yet acknowledged by the other side (or still waiting to be sent).",
         "normal": "0 or near 0", "alarming": "large and staying → the network or the other side does not keep up"},
        {"name": "rtt:avg/var", "meaning": "Smoothed round-trip time and its variation, in ms.",
         "normal": "steady and low (sub-millisecond in a co-location)", "alarming": "much higher than minrtt → queueing or loss on the path"},
        {"name": "minrtt", "meaning": "The lowest round-trip time seen: the path's baseline.", "normal": "—", "alarming": "—"},
        {"name": "rto", "meaning": "Retransmit timeout in ms: how long TCP waits before resending a lost segment.",
         "normal": "about 200 ms (the minimum)", "alarming": "higher → it has had to back off after losses"},
        {"name": "cwnd", "meaning": "Congestion window: how many segments may be in flight.",
         "normal": "10 or more", "alarming": "very small (1–2) → TCP slowed itself down after loss"},
        {"name": "retrans:a/b", "meaning": "Segments being retransmitted now / in total on this connection. Only shown when not zero.",
         "normal": "absent", "alarming": "a growing total → this connection loses packets"},
        {"name": "lost, unacked", "meaning": "Segments considered lost; segments not yet acknowledged.",
         "normal": "absent or small", "alarming": "present → loss on this connection"},
    ],
    "steps": [
        "Find the connection (Peer Address:Port tells you which exchange or service).",
        "Queues: is Recv-Q or Send-Q building up?",
        "Health: rtt against minrtt, rto, cwnd, and whether retrans appears.",
    ],
    "next": "Retransmits on one connection → ip -s link on its interface, then the path to that peer · "
            "Recv-Q building → the application is too slow (pidstat) · Send-Q building → the path or the peer.",
}

PURPOSE_QUESTIONS = [
    {"question": "What does ss -ti show you?",
     "key_points": ["TCP connections with internal details per connection: queues, round-trip time, retransmits"]},
    {"question": "What do the options -t and -i do?",
     "key_points": ["-t: only TCP sockets", "-i: show internal TCP information"]},
    {"question": "sar -n TCP,ETCP shows retransmits. Why run ss -ti next?",
     "key_points": ["to find which connection is retransmitting"]},
    {"question": "How do you limit ss -ti to the connection with one exchange?",
     "key_points": ["add a filter such as 'dst <exchange IP>' (or a port)"]},
    {"question": "What is ss the modern replacement of?",
     "key_points": ["netstat (for listing sockets)"]},
    {"question": "Which two queue columns does ss show, and what do they tell you in general?",
     "key_points": ["Recv-Q and Send-Q: data waiting to be read by the application and data waiting to be acknowledged"]},
    {"question": "Why is rtt from ss useful for a trading engineer?",
     "key_points": ["it shows the network delay to the exchange on that connection"]},
    {"question": "Can ss -ti show packet drops on the NIC?",
     "key_points": ["no; ip -s link shows interface drops; ss shows the effect on one connection"]},
]

COLUMN_QUESTIONS = [
    {"question": "What does Recv-Q mean on an established connection?",
     "key_points": ["bytes received but not yet read by the application"]},
    {"question": "What does Send-Q mean on an established connection?",
     "key_points": ["bytes sent but not yet acknowledged by the other side"]},
    {"question": "Recv-Q stays at 2 MB on the market-data connection. What does that tell you?",
     "key_points": ["the application reads too slowly: it falls behind"]},
    {"question": "What do the two numbers in rtt:0.352/0.051 mean?",
     "key_points": ["the smoothed round-trip time and its variation, in ms"]},
    {"question": "What does rto mean, and what does rto:412 tell you?",
     "key_points": ["the retransmit timeout", "above the 200 ms minimum: TCP has backed off after losses"]},
    {"question": "What does cwnd mean, and why is cwnd:2 a warning?",
     "key_points": ["the congestion window: how much may be in flight", "2 is tiny: TCP slowed down after loss"]},
    {"question": "What does retrans:0/341 mean?",
     "key_points": ["nothing is being retransmitted right now, but 341 segments were retransmitted in total"]},
    {"question": "What does minrtt tell you?",
     "key_points": ["the lowest round-trip time seen: the baseline of the path"]},
    {"question": "rtt is 8.4 ms while minrtt is 0.31 ms. What does that suggest?",
     "key_points": ["delay far above the baseline: queueing or loss on the path"]},
    {"question": "What does a connection without any 'retrans' field tell you?",
     "key_points": ["it has had no retransmits"]},
]

SITUATIONS = ["healthy", "retransmits", "recv_q", "send_q"]

_HDR = "State  Recv-Q  Send-Q    Local Address:Port    Peer Address:Port"


def _conn(recv_q, send_q, lport, peer, info) -> str:
    return f"ESTAB  {recv_q:<7} {send_q:<7} 10.20.1.15:{lport:<9} {peer}\n\t {info}"


def _info(rng, rto=204, rtt=None, var=None, cwnd=10, retrans=None, extra="") -> str:
    minrtt = rng.uniform(0.28, 0.36)
    rtt = rtt if rtt is not None else minrtt * rng.uniform(1.05, 1.2)
    var = var if var is not None else rng.uniform(0.02, 0.06)
    acked = rng.randint(10**8, 10**10)
    parts = [f"cubic wscale:7,7 rto:{rto} rtt:{rtt:.3f}/{var:.3f} ato:40 mss:1448 pmtu:1500 cwnd:{cwnd}"]
    if extra:
        parts.append(extra)
    parts.append(f"bytes_acked:{acked} segs_out:{acked // 700} segs_in:{acked // 900}")
    if retrans:
        parts.append(f"retrans:{retrans}")
    parts.append(f"minrtt:{minrtt:.2f}")
    return " ".join(parts)


def situation(rng: random.Random, kind: str) -> dict:
    a = _conn(0, 0, rng.randint(30000, 60000), "10.99.4.20:9001", _info(rng))
    if kind == "healthy":
        b = _conn(0, 0, rng.randint(30000, 60000), "10.99.7.31:9001", _info(rng))
    elif kind == "retransmits":
        rtt = rng.uniform(6, 15)
        b = _conn(0, rng.randint(2_000, 9_000), rng.randint(30000, 60000), "10.99.7.31:9001",
                  _info(rng, rto=rng.choice([412, 616, 824]), rtt=rtt, var=rtt * rng.uniform(0.8, 1.5),
                        cwnd=rng.choice([1, 2, 3]), retrans=f"{rng.choice([0, 1])}/{rng.randint(150, 900)}",
                        extra=f"ssthresh:2 unacked:{rng.randint(2, 6)} lost:{rng.randint(1, 3)}"))
    elif kind == "recv_q":
        # A TCP market-data feed whose handler does not keep up.
        b = _conn(rng.randint(1_500_000, 4_000_000), 0, rng.randint(30000, 60000), "10.99.9.5:7000", _info(rng))
    else:  # send_q
        b = _conn(0, rng.randint(400_000, 2_000_000), rng.randint(30000, 60000), "10.99.7.31:9001",
                  _info(rng, rtt=rng.uniform(2, 5), cwnd=rng.randint(10, 40), extra=f"unacked:{rng.randint(80, 300)}"))

    output = "\n".join([_HDR, a, b])
    peer_b = "10.99.9.5:7000" if kind == "recv_q" else "10.99.7.31:9001"

    if kind == "healthy":
        key_points = ["both connections are healthy: empty queues, low steady rtt, no retransmits"]
        bonus = ["rtt close to minrtt, rto at the 200 ms minimum, no retrans field"]
    elif kind == "retransmits":
        key_points = [f"the connection to {peer_b} is losing packets: it has many retransmits"]
        bonus = ["rto is backed off, cwnd is tiny, rtt far above minrtt, lost and unacked are present",
                 "the other connection is fine, so the problem is on the path to this peer",
                 "next: ip -s link on its interface, then the network path to that exchange"]
    elif kind == "recv_q":
        key_points = [f"the application reads the connection from {peer_b} too slowly: Recv-Q is large"]
        bonus = ["data arrives but waits in the socket: the market-data handler falls behind",
                 "next: pidstat for the handler process (CPU, preemption)"]
    else:
        key_points = [f"data to {peer_b} is piling up unacknowledged: Send-Q is large"]
        bonus = ["the network path or the exchange side does not keep up; rtt is up",
                 "no retransmits yet, so it is slow rather than lossy", "next: the path and the peer"]

    return {
        "situation": kind,
        "prompt": "You run `ss -ti` on the order gateway for its two busiest TCP connections:",
        "output": output,
        "key_points": key_points,
        "bonus": bonus,
    }
