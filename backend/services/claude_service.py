import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

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
    "kubernetes": [
        "pods_en_deployments",
        "services_en_networking",
        "resource_limits",
        "crashloopbackoff",
        "rolling_updates",
        "configmaps_en_secrets",
        "logs_en_debugging",
    ],
}

TRADING_SCENARIOS = {
    "websocket": "WebSocket verbinding met exchange verloren — orders komen niet door.",
    "port_exhaustion": "Port exhaustion door te veel korte verbindingen — bot kan geen nieuwe orders plaatsen.",
    "dns_problemen": "DNS timeout — bot kan exchange niet vinden.",
    "crashloopbackoff": "De trading bot pod crasht steeds opnieuw op — orders worden niet verwerkt.",
    "rolling_updates": "Een nieuwe versie van de trading service wordt uitgerold maar connecties met de exchange vallen weg.",
    "resource_limits": "De trading bot wordt door Kubernetes gestopt wegens te veel geheugengebruik tijdens hoge marktvolatiliteit.",
}


DIFFICULTY_CONTEXT = {
    1: "De kandidaat is een absolute beginner. Stel alleen basisvragen: wat is X, waarvoor gebruik je Y. Geen edge cases, geen productiedruk.",
    2: "De kandidaat heeft basiskennis. Stel vragen over herkenbare situaties met één duidelijke aanpak. Licht niveau voor iemand met ~1 jaar ervaring.",
    3: "De kandidaat heeft ~2 jaar ervaring. Stel praktische vragen over veelvoorkomende problemen. Dit is het niveau voor een junior TRE sollicitatie bij IMC.",
    4: "De kandidaat is medior. Stel complexere vragen met meerdere mogelijke oorzaken en trade-offs.",
    5: "De kandidaat is senior. Stel diepgaande vragen over edge cases, performance optimalisatie en systeemontwerp.",
}

# Huidige moeilijkheidsgraad — begin makkelijk, schaal op naarmate kennis groeit
DIFFICULTY = 2


def generate_question(subtopic: str, question_type: str) -> str:
    trading_hint = ""
    if subtopic in TRADING_SCENARIOS:
        trading_hint = f"\nGeef de vraag een trading context: {TRADING_SCENARIOS[subtopic]}"

    difficulty_instruction = DIFFICULTY_CONTEXT[DIFFICULTY]

    if question_type == "scenario":
        prompt = f"""Genereer één scenario-vraag voor een Trading Reliability Engineer (TRE) over het onderwerp '{subtopic}'.
De vraag beschrijft een productieprobleem. De kandidaat moet zijn aanpak stap voor stap uitleggen.
{trading_hint}

Moeilijkheidsgraad {DIFFICULTY}/5: {difficulty_instruction}

Schrijf alleen de vraag, geen antwoord. Maximaal 4 zinnen. Schrijf in het Nederlands."""
    else:
        prompt = f"""Genereer één commando-flitsvraag voor een Trading Reliability Engineer (TRE) over '{subtopic}'.
Vraag naar een specifiek Linux/netwerk commando of wat de output ervan betekent.

Moeilijkheidsgraad {DIFFICULTY}/5: {difficulty_instruction}

Schrijf alleen de vraag. Maximaal 2 zinnen. Schrijf in het Nederlands."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def evaluate_answer(question: str, user_answer: str, subtopic: str) -> tuple[str, int]:
    prompt = f"""Je bent een geduldige TRE-mentor bij een trading firm. Evalueer dit antwoord op moeilijkheidsgraad {DIFFICULTY}/5.

Moeilijkheidsgraad context: {DIFFICULTY_CONTEXT[DIFFICULTY]}

Onderwerp: {subtopic}
Vraag: {question}
Antwoord van de kandidaat: {user_answer}

Geef:
1. Wat goed was aan het antwoord.
2. Wat de kandidaat miste of beter had kunnen zeggen — leg het uit alsof je het uitlegt aan iemand die het nog aan het leren is.
3. Een score van 0-10, waarbij je rekening houdt met het verwachte niveau (moeilijkheidsgraad {DIFFICULTY}).

Formaat (gebruik exact dit formaat):
FEEDBACK: <jouw feedback in het Nederlands, maximaal 150 woorden>
SCORE: <getal 0-10>"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    response = message.content[0].text.strip()
    feedback = ""
    score = 5

    if "SCORE:" in response:
        parts = response.split("SCORE:")
        score_str = parts[-1].strip().split()[0]
        try:
            score = int(score_str)
        except ValueError:
            score = 5
        feedback_part = parts[0]
    else:
        feedback_part = response

    if "FEEDBACK:" in feedback_part:
        feedback = feedback_part.split("FEEDBACK:", 1)[1].strip()
    else:
        feedback = feedback_part.strip()

    return feedback, score
