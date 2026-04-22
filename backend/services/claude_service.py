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
}

TRADING_CONTEXT = {
    "websocket": "WebSocket verbinding met exchange verloren — orders komen niet door.",
    "port_exhaustion": "Port exhaustion — bot kan geen nieuwe verbindingen openen naar de exchange.",
    "dns_problemen": "DNS timeout — bot kan exchange niet vinden.",
    "crashloopbackoff": "Trading bot pod crasht steeds — orders worden niet verwerkt.",
    "rolling_updates": "Nieuwe versie uitrollen terwijl markt open is.",
    "resource_limits": "Bot gestopt door Kubernetes wegens te veel geheugen tijdens hoge volatiliteit.",
    "slippage_en_latency": "Trader meldt slechte fills — orders worden op slechtere prijs uitgevoerd dan verwacht.",
    "incident_response": "Trading bot is 3 minuten offline — traders klagen.",
    "release_management": "Nieuwe versie deployen terwijl markt open is — wat is je aanpak?",
}

LEVEL_CONTEXT = {
    "basis": (
        "Basis niveau — feilloos te beheersen voor de sollicitatie. "
        "Stel herkenbare vragen over veelvoorkomende situaties met één duidelijke aanpak. "
        "Geen edge cases. Geschikt voor iemand met enige Linux/K8s ervaring."
    ),
    "gemiddeld": (
        "Gemiddeld niveau — wat IMC verwacht bij 2+ jaar ervaring. "
        "Stel praktische vragen met meerdere mogelijke oorzaken. "
        "Koppel aan trading impact. Kandidaat moet kunnen redeneren, niet alleen commando's opnoemen."
    ),
}


def generate_question(subtopic: str, question_type: str, level: str = "basis") -> str:
    trading_hint = ""
    if subtopic in TRADING_CONTEXT:
        trading_hint = f"\nTrading context: {TRADING_CONTEXT[subtopic]}"

    level_instruction = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT["basis"])

    if question_type == "scenario":
        prompt = f"""Genereer één scenario-vraag voor een Trading Reliability Engineer (TRE) trainee over '{subtopic}'.
De vraag beschrijft een concreet productieprobleem. De kandidaat legt stap voor stap zijn aanpak uit.
{trading_hint}

Niveau: {level.upper()} — {level_instruction}

Schrijf alleen de vraag, geen antwoord. Maximaal 4 zinnen. Schrijf in het Nederlands."""
    else:
        prompt = f"""Genereer één commando-flitsvraag voor een TRE trainee over '{subtopic}'.
Vraag naar een specifiek commando of wat de output ervan betekent.

Niveau: {level.upper()} — {level_instruction}

Schrijf alleen de vraag. Maximaal 2 zinnen. Schrijf in het Nederlands."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_hint(question: str, subtopic: str, hint_number: int, previous_answer: str = "") -> str:
    hint_instructions = {
        1: "Wijs een richting aan zonder het antwoord te geven. Één zin.",
        2: "Noem een specifiek commando of concept dat relevant is. Maximaal 2 zinnen.",
        3: "Leg uit wat je zou zien als je het juiste pad volgt. Maximaal 3 zinnen.",
    }
    instruction = hint_instructions.get(hint_number, hint_instructions[1])

    prompt = f"""Je bent een TRE-mentor. Een trainee heeft moeite met deze vraag.

Vraag: {question}
Onderwerp: {subtopic}
{f"Laatste antwoord van trainee: {previous_answer}" if previous_answer else ""}

Geef hint {hint_number}/3: {instruction}
Schrijf in het Nederlands. Geef NIET het volledige antwoord."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def evaluate_answer(question: str, user_answer: str, subtopic: str, level: str = "basis") -> dict:
    level_instruction = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT["basis"])

    prompt = f"""Je bent een geduldige TRE-mentor bij een trading firm. Evalueer dit antwoord.

Niveau: {level.upper()} — {level_instruction}
Onderwerp: {subtopic}
Vraag: {question}
Antwoord van de trainee: {user_answer}

Geef je evaluatie in dit exacte formaat:

FEEDBACK: <wat goed was + wat miste de trainee + juiste aanpak, maximaal 150 woorden, in het Nederlands>
SCORE: <getal 0-10>
INTERVIEW: <hoe zou je dit in een sollicitatiegesprek bij IMC formuleren, 2-3 zinnen, in het Nederlands>
PI_COMMANDO: <één of twee concrete Linux/kubectl commando's die de trainee op zijn Raspberry Pi kan uitvoeren om dit te simuleren, met korte uitleg>"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )

    response = message.content[0].text.strip()
    result = {"feedback": "", "score": 5, "interview_taal": "", "pi_commando": ""}

    sections = {"FEEDBACK": "", "SCORE": "", "INTERVIEW": "", "PI_COMMANDO": ""}
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
    result["interview_taal"] = sections["INTERVIEW"].strip()
    result["pi_commando"] = sections["PI_COMMANDO"].strip()
    try:
        result["score"] = int(sections["SCORE"].strip().split()[0])
    except (ValueError, IndexError):
        result["score"] = 5

    return result
