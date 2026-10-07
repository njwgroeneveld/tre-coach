import os
import random
import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel
from services.causes import CAUSES, pick_cause

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Haiku 4.5: no thinking, no effort setting. To move to Sonnet 5.5, see commit d4d3e37 — it adds
# effort (low, medium for grading) and server-side fallback to _ask.
MODEL = "claude-haiku-4-5"


class ClaudeRefusal(Exception):
    """Claude declined the request (stop_reason "refusal")."""


def _ask(messages: list, max_tokens: int) -> str:
    # The prompts themselves cap the length of the answer; max_tokens is only a ceiling.
    message = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=messages,
    )
    if message.stop_reason == "refusal":
        raise ClaudeRefusal()
    # Read by block type rather than content[0], so a thinking model works too.
    return "".join(b.text for b in message.content if b.type == "text").strip()

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
    cause = pick_cause(subtopic, level, [])
    if cause:
        trading_hint += f"\nWrite the symptom of this root cause (never reveal it): {cause['cause']}"
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

    return _ask([{"role": "user", "content": prompt}], max_tokens=4000)


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

    return _ask([{"role": "user", "content": prompt}], max_tokens=4000)


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

    return _ask(messages, max_tokens=4000)


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
    # Which cause the question was built on never reaches the browser, so grading gets the options.
    if question_type == "scenario" and subtopic in CAUSES:
        options = "; ".join(c["cause"] for c in CAUSES[subtopic])
        focus += f"\nThe question was written around one of these root causes; infer which from the symptom: {options}"

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

    response = _ask([{"role": "user", "content": prompt}], max_tokens=8000)
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


# --- Investigation mode -------------------------------------------------------------------------

# The scenario is the ground truth for the simulated host and the grading, so it gets the stronger
# model: Haiku produced technically wrong causes and facts that contradicted each other.
INVESTIGATION_MODEL = "claude-sonnet-5-5"

# Varying the host keeps scenarios from all landing on the same machine.
INVESTIGATION_HOSTS = [
    "a bare-metal order gateway (Linux, 16 cores)",
    "a market-data feed handler running as a Kubernetes pod",
    "a risk engine on a Linux VM",
    "a trading bot running under systemd on a single Linux server",
    "a co-located exchange connectivity host with two NICs",
]


class InvestigationScenario(BaseModel):
    symptom: str
    cause: str
    facts: list[str]
    fix: str
    fastest_path: list[str]


def generate_investigation(subtopic: str, level: str = "basis", cause: dict | None = None) -> InvestigationScenario:
    level_instruction = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT["basis"])
    # The cause is chosen in code, so scenarios vary; Claude builds the host and facts around it.
    given_cause = (
        f"\nRoot cause to build the scenario around (make it concrete for this host): {cause['cause']}"
        if cause else ""
    )
    focus = SUBTOPIC_FOCUS.get(subtopic, subtopic)
    host = random.choice(INVESTIGATION_HOSTS)
    red_herring = (
        "Add one plausible red herring among the facts: something that looks suspicious but is not the cause."
        if level == "gemiddeld" else "No red herrings: one clear cause."
    )

    prompt = f"""You design a hands-on troubleshooting exercise for a Trading Reliability Engineer trainee.
A simulator will later play the host and answer the trainee's commands, so the scenario must be concrete.

Topic: {subtopic} — {focus}
Host: {host}
Level: {level.upper()} — {level_instruction}{given_cause}

Fields:
- symptom: what a trader or an alert reports, 2-3 sentences. No metrics, no cause, no hint, no tool names.
  The last sentence must be exactly: "How would you investigate?"
- cause: the single root cause, one sentence, specific (which process, which resource, why).
- facts: 10-15 concrete facts the simulator must stay consistent with: hostname, CPU count, RAM,
  disks or NICs with device names, the relevant processes with PIDs, how often and how long the
  problem occurs, and the numbers the key commands would show during the incident versus normal.
  {red_herring}
- fix: mitigation first, then the root-cause fix, 2-3 sentences.
- fastest_path: 3-5 commands an experienced engineer would run in order, each with what it reveals."""

    message = client.beta.messages.parse(
        model=INVESTIGATION_MODEL,
        # Sonnet 5.5 thinks by default and thinking counts toward max_tokens.
        max_tokens=16000,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": prompt}],
        output_format=InvestigationScenario,
        # On a policy decline the API retries on a fallback model within the same call.
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
    )
    if message.stop_reason == "refusal":
        raise ClaudeRefusal()
    return message.parsed_output


def format_steps(steps: list) -> str:
    """The investigation so far as a transcript; a wrong diagnosis and its consequence are part of it."""
    lines = []
    for s in steps:
        if s.get("kind") == "diagnosis":
            lines.append(f"[diagnosis] {s['input']}\n{s['output']}")
        else:
            lines.append(f"$ {s['input']}\n{s['output']}")
    return "\n\n".join(lines)


class SimulatedOutput(BaseModel):
    output: str
    risky_action: bool


def simulate_step(hidden: dict, steps: list, user_input: str) -> SimulatedOutput:
    facts = "\n".join(f"- {f}" for f in hidden["facts"])
    history = format_steps(steps) or "(none yet)"

    system = f"""You simulate a Linux host during an incident, for a troubleshooting exercise. The trainee
types commands or actions; you answer exactly as the host (or the people around it) would.

Hidden root cause (never reveal it): {hidden['cause']}
Facts you must stay consistent with:
{facts}

Rules:
- output: only what the command prints, in its real format. No explanations, no comments, no hints.
- Stay consistent with the facts and with every earlier output below: same hostname, PIDs, devices,
  core count and numbers. Values may move a little between samples, as real output does.
- The trainee runs commands while the problem is happening, unless they say otherwise.
- Keep output to at most 25 lines; trim long listings the way head would.
- A command that does not exist or is mistyped gives the shell's real error.
- If the input is an action or question rather than a command (for example "check the GC log" or
  "ask the trader when it started"), answer briefly as that log or person would.
- If the input is destructive or disruptive (kill, restart, reboot, stopping a service, deleting
  files), set risky_action to true and describe the consequence in square brackets, including the
  trading impact. A wrong action does not fix the problem: it comes back. The consequence must not
  name or hint at the root cause, the culprit process or why it returns; only say that and when the
  symptom comes back.
- Otherwise risky_action is false."""

    message = client.beta.messages.parse(
        model=INVESTIGATION_MODEL,
        max_tokens=16000,
        output_config={"effort": "low"},
        system=system,
        messages=[{"role": "user", "content": f"Earlier steps:\n{history}\n\nNew input:\n$ {user_input}"}],
        output_format=SimulatedOutput,
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
    )
    if message.stop_reason == "refusal":
        raise ClaudeRefusal()
    return message.parsed_output


class DiagnosisJudgement(BaseModel):
    correct: bool
    consequence: str


def judge_diagnosis(hidden: dict, steps: list, diagnosis: str) -> DiagnosisJudgement:
    prompt = f"""A trainee in a troubleshooting exercise states their diagnosis. Judge it against the hidden root cause.

Hidden root cause: {hidden['cause']}
Facts: {'; '.join(hidden['facts'])}

Investigation so far:
{format_steps(steps) or '(no commands run)'}

Trainee's diagnosis: {diagnosis}

- correct: true only if the diagnosis names the culprit (the process, job or component) and the
  mechanism (how it causes the symptom). Restating the symptom ("the disk is slow") or naming the
  resource without the culprit is not enough. Wording does not matter, substance does.
- consequence: if not correct, 2-3 sentences in square brackets describing what happens when the
  trainee acts on their diagnosis: their fix is applied, the symptom comes back (say when), and the
  trading impact. Do not name or hint at the real cause. If correct, an empty string."""

    message = client.beta.messages.parse(
        model=INVESTIGATION_MODEL,
        max_tokens=16000,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": prompt}],
        output_format=DiagnosisJudgement,
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
    )
    if message.stop_reason == "refusal":
        raise ClaudeRefusal()
    return message.parsed_output


class InvestigationEvaluation(BaseModel):
    feedback: str
    score: int
    interview_answer: str
    pi_commando: str
    grammar_score: int
    vocabulary_score: int
    structure_score: int
    fluency_score: int
    english_tip: str


def evaluate_investigation(investigation: dict, solved: bool) -> InvestigationEvaluation:
    hidden = investigation["hidden"]
    commands = sum(1 for s in investigation["steps"] if s.get("kind") != "diagnosis")
    level_instruction = LEVEL_CONTEXT.get(investigation["level"], LEVEL_CONTEXT["basis"])
    outcome = (
        f"Solved after {investigation['wrong_diagnoses']} wrong diagnosis(es)." if solved
        else "Not solved: two wrong diagnoses, the cause was revealed."
    )

    prompt = f"""You are a patient TRE mentor at a trading firm. Evaluate a hands-on troubleshooting exercise.

Level: {investigation['level'].upper()} — {level_instruction}
Symptom given: {investigation['symptom']}
Hidden root cause: {hidden['cause']}
Fix: {hidden['fix']}
Fastest path an experienced engineer would take: {' | '.join(hidden['fastest_path'])}

The trainee's investigation ({commands} commands, {investigation['risky_actions']} risky actions):
{format_steps(investigation['steps'])}

Outcome: {outcome}

Score 0-10, weighing:
- Cause: found or not, and at which attempt.
- Efficiency: commands used compared with the fastest path ({len(hidden['fastest_path'])} steps).
- Order: broad, cheap checks first (the 60-second checklist), then narrowing down.
- Interpretation: did each next command follow from what the previous output showed?
- Trading impact: risky actions lower the score; a diagnosis that includes mitigation raises it.

Fields:
- feedback: what went well, where the trainee lost time or went off track, and the fastest path
  with what each command would have shown. Maximum 150 words.
- interview_answer: how to tell this investigation in an IMC interview, 2-3 sentences.
- pi_commando: one or two commands to reproduce this situation on a Raspberry Pi, with a short explanation.
- grammar_score, vocabulary_score, structure_score, fluency_score: 0-10, judged on the trainee's
  diagnoses (the English text they wrote, not the commands).
- english_tip: one concrete tip to improve their English, maximum 20 words."""

    message = client.beta.messages.parse(
        model=INVESTIGATION_MODEL,
        max_tokens=16000,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": prompt}],
        output_format=InvestigationEvaluation,
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
    )
    if message.stop_reason == "refusal":
        raise ClaudeRefusal()
    return message.parsed_output
