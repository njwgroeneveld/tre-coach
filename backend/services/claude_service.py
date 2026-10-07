import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Haiku is fast and cheap; set CLAUDE_MODEL (e.g. claude-sonnet-5-5) to switch without a code change.
MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")

SUBTOPICS = {
    "linux": [
        "processen_performance",
        "geheugen_analyse",
        "disk_problemen",
        "file_descriptors",
        "proc_filesystem",
        "logging_journalctl",
    ],
    "netwerk": [
        "tcp_fundamenten",
        "tcp_connection_states",
        "port_exhaustion",
        "dns_problemen",
        "tcpdump",
        "websocket",
    ],
    "kubernetes": [
        "pods_en_deployments",
        "crashloopbackoff",
        "resource_limits",
        "rolling_updates",
        "services_en_networking",
        "logs_en_debugging",
    ],
    "trading": [
        "slippage_en_latency",
        "order_types",
        "exchange_connectiviteit",
        "incident_response",
        "release_management",
        "monitoring_en_alerts",
    ],
    "performance": [
        "use_methode",
        "checklist_60s",
        "load_vs_cpu",
        "io_wait_en_dstate",
        "latency_en_context_switches",
        "netwerk_retransmits_drops",
    ],
}

# What a subtopic must cover — the name alone is too vague for good questions.
SUBTOPIC_FOCUS = {
    "use_methode": "Brendan Gregg's USE method: Utilization, Saturation and Errors for every resource (CPU, memory, disk, network).",
    "checklist_60s": "Brendan Gregg's 60-second checklist: uptime, dmesg | tail, vmstat 1, mpstat -P ALL 1, pidstat 1, iostat -xz 1, free -m, sar -n DEV 1, sar -n TCP,ETCP 1, top — what each shows and in which order.",
    "load_vs_cpu": "Load average vs CPU usage: run queue, load per core, high load with idle CPU, reading vmstat r/us/sy/id/wa.",
    "io_wait_en_dstate": "I/O wait and uninterruptible sleep (D state): %iowait, iostat await/%util, finding the process that waits on disk.",
    "latency_en_context_switches": "Latency on a low-latency trading host: voluntary vs involuntary context switches (pidstat -w), CPU pinning/isolation, noisy neighbours, tail latency.",
    "netwerk_retransmits_drops": "TCP retransmits and packet drops: sar -n ETCP, netstat -s, ip -s link, ethtool -S, ss -ti — and what they mean for order latency.",
}

TRADING_CONTEXT = {
    "websocket": "WebSocket connection to exchange lost — orders are not getting through.",
    "port_exhaustion": "Port exhaustion — the bot cannot open new connections to the exchange.",
    "dns_problemen": "DNS timeout — the bot cannot resolve the exchange hostname.",
    "crashloopbackoff": "Trading bot pod is crash-looping — orders are not being processed.",
    "rolling_updates": "Rolling out a new version while the market is open.",
    "resource_limits": "Bot killed by Kubernetes OOM during high volatility.",
    "slippage_en_latency": "Trader reports bad fills — orders are executing at worse prices than expected.",
    "incident_response": "Trading bot has been offline for 3 minutes — traders are complaining.",
    "release_management": "Deploying a new version while the market is open — what is your approach?",
    "checklist_60s": "A trader says the order gateway host 'feels slow'. You have just logged in and have 60 seconds.",
    "load_vs_cpu": "An alert fires: load average on the market-data host has tripled in ten minutes.",
    "io_wait_en_dstate": "The trading bot freezes for a few seconds at a time, a few times per hour.",
    "latency_en_context_switches": "Order round-trip latency is fine on average, but the 99th percentile has doubled since yesterday.",
    "netwerk_retransmits_drops": "Order acknowledgements from the exchange sometimes arrive tens of milliseconds late; the exchange says its side is fine.",
}

LEVEL_CONTEXT = {
    "basis": (
        "Foundation level — must be mastered perfectly for the interview. "
        "Ask recognisable questions about common situations with one clear approach. "
        "No edge cases. Suitable for someone with some Linux/K8s experience."
    ),
    "gemiddeld": (
        "Intermediate level — what IMC expects at 2+ years of experience. "
        "Ask practical questions with multiple possible root causes. "
        "Link to trading impact. The candidate must reason, not just list commands."
    ),
}


def generate_question(subtopic: str, question_type: str, level: str = "basis") -> str:
    trading_hint = ""
    if subtopic in TRADING_CONTEXT:
        trading_hint = f"\nTrading context: {TRADING_CONTEXT[subtopic]}"
    focus = ""
    if subtopic in SUBTOPIC_FOCUS:
        focus = f"\nFocus: {SUBTOPIC_FOCUS[subtopic]}"

    level_instruction = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT["basis"])

    if question_type == "scenario":
        prompt = f"""Generate one scenario question for a Trading Reliability Engineer (TRE) trainee about '{subtopic}'.
The question describes a concrete production problem. The candidate explains their approach step by step.
{trading_hint}{focus}
The focus is for you: do not name the commands or tools in the question — choosing them is part of the answer.
Describe only the symptom as a trader or an alert would report it: no metrics or measurements, never the cause or a hint towards it.
Do not list possible causes, layers or areas to check. The last sentence must be exactly: "How would you investigate?"

Level: {level.upper()} — {level_instruction}

Write only the question, no answer. Maximum 4 sentences. Write in English."""
    else:
        prompt = f"""Generate one command flash-card question for a TRE trainee about '{subtopic}'.
Ask about a specific command or what its output means.{focus}
If you show sample output, make the numbers realistic and consistent with each other.

Level: {level.upper()} — {level_instruction}

Write only the question. Maximum 2 sentences. Write in English."""

    message = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_hint(question: str, subtopic: str, hint_number: int, previous_answer: str = "") -> str:
    hint_instructions = {
        1: "Point in a direction without giving away the answer. One sentence.",
        2: "Name a specific command or concept that is relevant. Maximum 2 sentences.",
        3: "Explain what you would expect to see if you follow the right path. Maximum 3 sentences.",
    }
    instruction = hint_instructions.get(hint_number, hint_instructions[1])

    prompt = f"""You are a TRE mentor. A trainee is struggling with this question.

Question: {question}
Topic: {subtopic}
{f"Trainee's last answer: {previous_answer}" if previous_answer else ""}

Give hint {hint_number}/3: {instruction}
Write in English. Do NOT give the full answer."""

    message = client.messages.create(
        model=MODEL,
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_followup(question: str, subtopic: str, user_answer: str, feedback: str, followup_question: str, history: list) -> str:
    messages = [
        {
            "role": "user",
            "content": f"""You are a TRE mentor at a trading firm. A trainee has just answered a practice question and wants to ask follow-up questions.

Original question: {question}
Topic: {subtopic}
Trainee's answer: {user_answer}
Your feedback was: {feedback}

The trainee can now ask freely. Answer concisely and practically in English. Focus on understanding, give concrete examples or commands where relevant."""
        },
        {"role": "assistant", "content": "Of course, go ahead and ask."}
    ]

    for msg in history:
        messages.append({"role": "user" if msg["role"] == "user" else "assistant", "content": msg["text"]})

    messages.append({"role": "user", "content": followup_question})

    message = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=messages,
    )
    return message.content[0].text.strip()


SCENARIO_RUBRIC = """This is a scenario question: the symptom fits several root causes, and the topic above is only the cause the question writer had in mind.
Grade the approach, not whether the trainee guessed that cause:
- Hypotheses: does the trainee name several plausible causes, including the intended one?
- Elimination: for each cause, which command confirms or rules it out, and what output would they expect?
- Order: cheap, broad checks first, then narrow down.
- Trading impact: mitigate first, then fix the root cause.
A different but well-argued cause is not an error. Leaving the intended cause out of the hypotheses is.
In FEEDBACK, name the cause the question had in mind and how to tell it apart from the others."""


def evaluate_answer(question: str, user_answer: str, subtopic: str, level: str = "basis", question_type: str = "scenario") -> dict:
    level_instruction = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT["basis"])
    rubric = f"\n{SCENARIO_RUBRIC}\n" if question_type == "scenario" else ""
    # The subtopic id is Dutch-English ("io_wait_en_dstate"); the focus text says what it means.
    focus = f"\nTopic means: {SUBTOPIC_FOCUS[subtopic]}" if subtopic in SUBTOPIC_FOCUS else ""

    prompt = f"""You are a patient TRE mentor at a trading firm. Evaluate this answer.

Level: {level.upper()} — {level_instruction}
Topic: {subtopic}{focus}
Question: {question}
Trainee's answer: {user_answer}
{rubric}
Give your evaluation in this exact format:

FEEDBACK: <what was good + what the trainee missed + correct approach, maximum 150 words>
SCORE: <integer 0-10>
INTERVIEW: <how you would phrase this in an IMC interview, 2-3 sentences>
PI_COMMANDO: <one or two concrete Linux/kubectl commands the trainee can run on a Raspberry Pi to simulate this, with a short explanation>
GRAMMAR_SCORE: <integer 0-10, evaluate verb tenses, sentence construction, subject-verb agreement>
VOCABULARY_SCORE: <integer 0-10, evaluate technical term accuracy, word variety, appropriate register>
STRUCTURE_SCORE: <integer 0-10, evaluate logical flow, clear reasoning steps, answer completeness>
FLUENCY_SCORE: <integer 0-10, evaluate sentence variety, filler avoidance, use of linking words like therefore/however/as a result>
ENGLISH_TIP: <one concrete actionable tip to improve English, maximum 20 words, e.g. "Use 'therefore' instead of 'so' to sound more professional">"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )

    response = message.content[0].text.strip()
    result = {
        "feedback": "",
        "score": 5,
        "interview_answer": "",
        "pi_commando": "",
        "grammar_score": None,
        "vocabulary_score": None,
        "structure_score": None,
        "fluency_score": None,
        "english_tips": "",
    }

    sections = {
        "FEEDBACK": "", "SCORE": "", "INTERVIEW": "", "PI_COMMANDO": "",
        "GRAMMAR_SCORE": "", "VOCABULARY_SCORE": "", "STRUCTURE_SCORE": "",
        "FLUENCY_SCORE": "", "ENGLISH_TIP": "",
    }
    current = None
    for line in response.split("\n"):
        for key in sections:
            if line.startswith(f"{key}:"):
                current = key
                sections[key] = line.split(f"{key}:", 1)[1].strip()
                break
        else:
            if current and line.strip():
                sections[current] += " " + line.strip()

    result["feedback"] = sections["FEEDBACK"].strip()
    result["interview_answer"] = sections["INTERVIEW"].strip()
    result["pi_commando"] = sections["PI_COMMANDO"].strip()
    result["english_tips"] = sections["ENGLISH_TIP"].strip()

    for field, key in [
        ("score", "SCORE"),
        ("grammar_score", "GRAMMAR_SCORE"),
        ("vocabulary_score", "VOCABULARY_SCORE"),
        ("structure_score", "STRUCTURE_SCORE"),
        ("fluency_score", "FLUENCY_SCORE"),
    ]:
        try:
            result[field] = int(sections[key].strip().split()[0])
        except (ValueError, IndexError):
            result[field] = 5 if field == "score" else None

    return result
