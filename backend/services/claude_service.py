import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SUBTOPICS = {
    "linux": [
        "processen_performance",
        "geheugen_analyse",
        "disk_problemen",
        "file_descriptors",
        "kernel_parameters",
        "proc_filesystem",
        "logging_journalctl",
    ],
    "netwerk": [
        "tcp_fundamenten",
        "verbindingsproblemen",
        "port_exhaustion",
        "dns_problemen",
        "tcpdump",
        "iptables",
        "latency",
        "packet_loss",
        "websocket",
        "tcp_keepalive",
    ],
}

TRADING_SCENARIOS = {
    "websocket": "WebSocket verbinding met exchange verloren — orders komen niet door.",
    "port_exhaustion": "Port exhaustion door te veel korte verbindingen — bot kan geen nieuwe orders plaatsen.",
    "dns_problemen": "DNS timeout — bot kan exchange niet vinden.",
}


def generate_question(subtopic: str, question_type: str) -> str:
    trading_hint = ""
    if subtopic in TRADING_SCENARIOS:
        trading_hint = f"\nGeef de vraag een trading context: {TRADING_SCENARIOS[subtopic]}"

    if question_type == "scenario":
        prompt = f"""Genereer één scenario-vraag voor een Trading Reliability Engineer (TRE) over het onderwerp '{subtopic}'.
De vraag beschrijft een productieprobleem. De kandidaat moet zijn aanpak stap voor stap uitleggen.
{trading_hint}
Schrijf alleen de vraag, geen antwoord. Maximaal 4 zinnen. Schrijf in het Nederlands."""
    else:
        prompt = f"""Genereer één commando-flitsvraag voor een Trading Reliability Engineer (TRE) over '{subtopic}'.
Vraag naar een specifiek Linux/netwerk commando of wat de output ervan betekent.
Schrijf alleen de vraag. Maximaal 2 zinnen. Schrijf in het Nederlands."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def evaluate_answer(question: str, user_answer: str, subtopic: str) -> tuple[str, int]:
    prompt = f"""Je bent een senior TRE bij een trading firm. Evalueer dit antwoord van een junior kandidaat.

Onderwerp: {subtopic}
Vraag: {question}
Antwoord van de kandidaat: {user_answer}

Geef:
1. Concrete feedback: wat was goed, wat miste de kandidaat, wat is het juiste antwoord.
2. Een score van 0-10.

Formaat (gebruik exact dit formaat):
FEEDBACK: <jouw feedback in het Nederlands, maximaal 150 woorden>
SCORE: <getal 0-10>"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    response = message.content[0].text.strip()
    lines = response.split("\n")
    feedback = ""
    score = 5

    for line in lines:
        if line.startswith("FEEDBACK:"):
            feedback = line.replace("FEEDBACK:", "").strip()
        elif line.startswith("SCORE:"):
            try:
                score = int(line.replace("SCORE:", "").strip())
            except ValueError:
                score = 5

    return feedback, score
