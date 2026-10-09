"""Lesson 11: ip -s link — interface state and its error and drop counters."""

import random

COMMAND = "ip -s link"

CARD = {
    "title": "ip -s link — is the interface up, and is it losing packets?",
    "summary": (
        "ip -s link shows each network interface with its state and counters: bytes and packets, plus errors, "
        "drops and missed packets. These are the error and saturation signals of the USE method for a network "
        "interface. The counters count since boot, so one snapshot says little: run it twice, a few seconds "
        "apart, and look at what increases."
    ),
    "example": (
        "3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000\n"
        "    link/ether 0c:42:a1:3b:5e:10 brd ff:ff:ff:ff:ff:ff\n"
        "    RX:  bytes  packets errors dropped  missed   mcast\n"
        "    982311234567 712321910      0       0       0 1022113\n"
        "    TX:  bytes  packets errors dropped carrier collsns\n"
        "    552100012345 410221130      0       0       0       0"
    ),
    "fields": [
        {"name": "<...UP,LOWER_UP>, state UP", "meaning": "UP: the interface is enabled. LOWER_UP: there is a physical link (cable, carrier).",
         "normal": "UP with LOWER_UP, state UP",
         "alarming": "NO-CARRIER or state DOWN → no link: cable, optic or switch port"},
        {"name": "mtu", "meaning": "The largest packet size the interface sends.", "normal": "1500 (or 9000 with jumbo frames)",
         "alarming": "different from the other side → large packets get lost"},
        {"name": "RX / TX bytes, packets", "meaning": "Totals received and sent since boot.", "normal": "—", "alarming": "—"},
        {"name": "RX errors", "meaning": "Received packets that were broken, for example bad checksums (CRC).",
         "normal": "0, or not increasing", "alarming": "increasing → a bad cable, optic or port"},
        {"name": "RX dropped", "meaning": "Packets the host dropped after the NIC received them (for example buffers full, or traffic nobody wants).",
         "normal": "small, or not increasing", "alarming": "increasing fast → the host cannot keep up"},
        {"name": "RX missed", "meaning": "Packets the NIC could not store because its receive ring was full.",
         "normal": "0, or not increasing", "alarming": "increasing → the ring overflows, typically during microbursts"},
        {"name": "RX mcast", "meaning": "Multicast packets received.", "normal": "high on a market-data interface", "alarming": "—"},
        {"name": "TX carrier, collsns", "meaning": "Link problems while sending; collisions (only on old half-duplex links).",
         "normal": "0", "alarming": "increasing carrier errors → the link drops"},
    ],
    "steps": [
        "Check the state: UP with LOWER_UP, or DOWN / NO-CARRIER?",
        "Take two snapshots a few seconds apart; which counters increase?",
        "errors → physical (cable, optic) · missed → the NIC's ring overflows · dropped → the host cannot keep up.",
    ],
    "next": "errors → the cable, optic or switch port · missed → a larger ring (ethtool -g / -G), spread interrupts · "
            "drops with retransmits → ss -ti for the affected connections.",
}

PURPOSE_QUESTIONS = [
    {"question": "What does ip -s link show you?",
     "key_points": ["each interface with its state and its counters: packets, errors, drops"]},
    {"question": "Why should you run ip -s link twice, a few seconds apart?",
     "key_points": ["the counters count since boot; only what increases now matters"]},
    {"question": "In USE terms, what does ip -s link show for a network interface?",
     "key_points": ["errors (errors, carrier) and saturation (dropped, missed)"]},
    {"question": "sar -n DEV shows a quiet link but there are retransmits. Why check ip -s link?",
     "key_points": ["to see whether the interface is dropping or corrupting packets"]},
    {"question": "What does the -s option do?",
     "key_points": ["show the statistics (counters)"]},
    {"question": "Which part of the output tells you the cable is connected?",
     "key_points": ["LOWER_UP in the flags (and not NO-CARRIER)"]},
    {"question": "Can ip -s link tell you which application loses packets?",
     "key_points": ["no; it shows the interface; netstat -s or ss show the protocol and socket level"]},
    {"question": "Why is ip -s link especially useful on a trading host?",
     "key_points": ["dropped or missed packets mean lost market data or delayed orders"]},
]

COLUMN_QUESTIONS = [
    {"question": "What is the difference between UP and LOWER_UP in the flags?",
     "key_points": ["UP: the interface is enabled", "LOWER_UP: there is a physical link"]},
    {"question": "The flags show NO-CARRIER and state DOWN. What does that mean?",
     "key_points": ["there is no physical link: the cable, optic or switch port is down"]},
    {"question": "What does RX errors count, and what causes it to rise?",
     "key_points": ["broken received packets (bad checksums)", "a bad cable, optic or port"]},
    {"question": "What does RX missed count?",
     "key_points": ["packets the NIC could not store because its receive ring was full"]},
    {"question": "RX missed rises in bursts at the market open. What is likely going on?",
     "key_points": ["microbursts overflow the NIC's receive ring"],
     "bonus": ["a larger ring (ethtool -G) or more queues/cores for interrupts"]},
    {"question": "What does RX dropped count?",
     "key_points": ["packets the host dropped after receiving them, for example because buffers were full"]},
    {"question": "RX errors is 1200, and five seconds later still 1200. Is there a problem now?",
     "key_points": ["no: the errors happened earlier; they are not increasing now"]},
    {"question": "What does mtu tell you, and why can a mismatch hurt?",
     "key_points": ["the largest packet size", "if the other side differs, large packets are lost"]},
    {"question": "What does RX mcast count?",
     "key_points": ["multicast packets received"]},
    {"question": "TX carrier errors are increasing. What does that suggest?",
     "key_points": ["the physical link keeps dropping"]},
]

SITUATIONS = ["clean", "missed", "crc_errors", "rx_dropped", "link_down"]


def _block(flags, state, rx, tx) -> str:
    return (f"3: eth1: <{flags}> mtu 1500 qdisc mq state {state} mode DEFAULT group default qlen 1000\n"
            "    link/ether 0c:42:a1:3b:5e:10 brd ff:ff:ff:ff:ff:ff\n"
            "    RX:  bytes  packets errors dropped  missed   mcast\n"
            f"    {rx[0]:>12} {rx[1]:>9} {rx[2]:>6} {rx[3]:>7} {rx[4]:>7} {rx[5]:>7}\n"
            "    TX:  bytes  packets errors dropped carrier collsns\n"
            f"    {tx[0]:>12} {tx[1]:>9} {tx[2]:>6} {tx[3]:>7} {tx[4]:>7} {tx[5]:>7}")


def situation(rng: random.Random, kind: str) -> dict:
    rx_b, rx_p = rng.randint(10**11, 10**12), rng.randint(10**8, 10**9)
    tx_b, tx_p = rng.randint(10**11, 10**12), rng.randint(10**8, 10**9)
    errors, dropped, missed, mcast = rng.choice([0, 0, 3]), rng.randint(0, 40), 0, rng.randint(10**5, 10**7)
    carrier = 0
    rx1 = [rx_b, rx_p, errors, dropped, missed, mcast]
    tx1 = [tx_b, tx_p, 0, 0, carrier, 0]
    pkts = rng.randint(80_000, 300_000)
    rx2 = [rx_b + pkts * 400, rx_p + pkts, errors, dropped, missed, mcast + pkts // 2]
    tx2 = [tx_b + pkts * 300, tx_p + pkts // 2, 0, 0, carrier, 0]
    flags, state = "BROADCAST,MULTICAST,UP,LOWER_UP", "UP"

    if kind == "missed":
        rx2[4] = missed + rng.randint(4_000, 30_000)
    elif kind == "crc_errors":
        rx1[2] = rng.randint(2_000, 50_000)
        rx2[2] = rx1[2] + rng.randint(300, 3_000)
    elif kind == "rx_dropped":
        rx2[3] = dropped + rng.randint(20_000, 90_000)
    elif kind == "link_down":
        flags, state = "NO-CARRIER,BROADCAST,MULTICAST,UP", "DOWN"
        rx2 = list(rx1)
        tx2 = list(tx1)
        tx1[4] = rng.randint(3, 20)
        tx2[4] = tx1[4] + 1

    output = (f"$ ip -s link show eth1\n{_block(flags, state, rx1, tx1)}\n\n"
              f"$ sleep 5; ip -s link show eth1\n{_block(flags, state, rx2, tx2)}")

    if kind == "clean":
        key_points = ["eth1 is healthy: up, and no errors, drops or missed packets are increasing"]
        bonus = ["the small old counts do not grow between the snapshots", "next: continue elsewhere"]
    elif kind == "missed":
        key_points = ["eth1's receive ring overflows: RX missed is increasing"]
        bonus = ["the NIC drops packets before the host sees them, typically during microbursts",
                 "next: check and enlarge the ring (ethtool -g / -G), spread the interrupts"]
    elif kind == "crc_errors":
        key_points = ["eth1 is receiving broken packets: RX errors are increasing"]
        bonus = ["a physical problem: cable, optic or switch port", "next: swap the cable or optic, check the switch port"]
    elif kind == "rx_dropped":
        key_points = ["the host is dropping received packets on eth1: RX dropped is increasing fast"]
        bonus = ["the NIC received them, but the host could not keep up (for example full buffers)",
                 "next: netstat -s for buffer errors, mpstat for %soft"]
    else:
        key_points = ["eth1 has no link: NO-CARRIER and state DOWN"]
        bonus = ["no traffic between the snapshots; carrier errors rose",
                 "next: the cable, the optic or the switch port"]

    return {
        "situation": kind,
        "prompt": "eth1 connects the order gateway to the exchange. You run `ip -s link show eth1` twice, five seconds apart:",
        "output": output,
        "key_points": key_points,
        "bonus": bonus,
    }
