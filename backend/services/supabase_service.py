import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"],
)


def create_session(user_id: str, topic: str, subtopic: str, level: str) -> str:
    result = client.table("sessions").insert({
        "user_id": user_id,
        "topic": topic,
        "subtopic": subtopic,
        "level": level,
    }).execute()
    return result.data[0]["id"]


def create_investigation(session_id: str, subtopic: str, level: str, symptom: str, hidden: dict) -> str:
    result = client.table("investigations").insert({
        "session_id": session_id,
        "subtopic": subtopic,
        "level": level,
        "symptom": symptom,
        "hidden": hidden,
    }).execute()
    return result.data[0]["id"]


def session_belongs_to(session_id: str, user_id: str) -> bool:
    result = client.table("sessions").select("id").eq(
        "id", session_id
    ).eq("user_id", user_id).execute()
    return bool(result.data)


def get_topic_level(user_id: str, topic: str) -> str:
    result = client.table("topic_levels").select("level").eq(
        "user_id", user_id
    ).eq("topic", topic).execute()
    if result.data:
        return result.data[0]["level"]
    return "basis"


def save_answer(session_id: str, question: str, question_type: str,
                subtopic: str, user_answer: str, feedback: str, score: int,
                interview_answer: str, pi_commando: str,
                grammar_score: int | None, vocabulary_score: int | None,
                structure_score: int | None, fluency_score: int | None,
                english_tips: str):
    client.table("answers").insert({
        "session_id": session_id,
        "question": question,
        "question_type": question_type,
        "subtopic": subtopic,
        "user_answer": user_answer,
        "feedback": feedback,
        "score": score,
        "interview_taal": interview_answer,
        "pi_commando": pi_commando,
        "grammar_score": grammar_score,
        "vocabulary_score": vocabulary_score,
        "structure_score": structure_score,
        "fluency_score": fluency_score,
        "english_tips": english_tips,
    }).execute()

    session = client.table("sessions").select("user_id, topic").eq("id", session_id).execute()
    user_id = session.data[0]["user_id"]
    topic = session.data[0]["topic"]

    result = client.table("topic_scores").select("*").eq(
        "user_id", user_id
    ).eq("subtopic", subtopic).execute()

    if result.data:
        row = result.data[0]
        client.table("topic_scores").update({
            "correct_answers": row["correct_answers"] + (1 if score >= 7 else 0),
            "total_answers": row["total_answers"] + 1,
        }).eq("id", row["id"]).execute()
    else:
        client.table("topic_scores").insert({
            "user_id": user_id,
            "subtopic": subtopic,
            "correct_answers": 1 if score >= 7 else 0,
            "total_answers": 1,
        }).execute()

    _check_level_progression(user_id, topic)


def _check_level_progression(user_id: str, topic: str):
    # Haal de laatste 10 scores op voor dit topic
    recent = client.table("answers").select("score, sessions(topic, user_id)").eq(
        "sessions.user_id", user_id
    ).eq("sessions.topic", topic).order("created_at", desc=True).limit(10).execute()

    scores = [r["score"] for r in recent.data if r.get("score") is not None]
    if len(scores) < 10:
        return  # Nog niet genoeg data voor progressie

    avg = sum(scores) / len(scores)
    current_level = get_topic_level(user_id, topic)

    new_level = current_level
    if avg >= 8.0 and current_level == "basis":
        new_level = "gemiddeld"
    elif avg < 6.0 and current_level == "gemiddeld":
        new_level = "basis"

    if new_level != current_level:
        _set_topic_level(user_id, topic, new_level)


def _set_topic_level(user_id: str, topic: str, level: str):
    existing = client.table("topic_levels").select("id").eq(
        "user_id", user_id
    ).eq("topic", topic).execute()

    if existing.data:
        client.table("topic_levels").update({
            "level": level
        }).eq("id", existing.data[0]["id"]).execute()
    else:
        client.table("topic_levels").insert({
            "user_id": user_id,
            "topic": topic,
            "level": level,
        }).execute()


def get_weakest_subtopic(user_id: str, topic: str) -> str | None:
    from services.claude_service import SUBTOPICS
    result = client.table("topic_scores").select("*").eq(
        "user_id", user_id
    ).execute()

    scores = {row["subtopic"]: row["correct_answers"] / row["total_answers"]
              for row in result.data if row["total_answers"] > 0}

    topic_subtopics = SUBTOPICS.get(topic, [])
    weakest = None
    lowest = 1.0

    for subtopic in topic_subtopics:
        pct = scores.get(subtopic, 0.0)
        if pct < lowest:
            lowest = pct
            weakest = subtopic

    return weakest or (topic_subtopics[0] if topic_subtopics else None)


def get_weakest_topic(user_id: str) -> dict:
    """Geeft het topic + subtopic met de laagste score terug."""
    from services.claude_service import SUBTOPICS
    result = client.table("topic_scores").select("*").eq("user_id", user_id).execute()
    scores = {row["subtopic"]: row["correct_answers"] / row["total_answers"]
              for row in result.data if row["total_answers"] > 0}

    weakest_topic = "linux"
    weakest_subtopic = None
    lowest = 1.0

    for topic, subtopics in SUBTOPICS.items():
        for subtopic in subtopics:
            pct = scores.get(subtopic, 0.0)
            if pct < lowest:
                lowest = pct
                weakest_topic = topic
                weakest_subtopic = subtopic

    return {"topic": weakest_topic, "subtopic": weakest_subtopic}


def get_dashboard_data(user_id: str) -> dict:
    scores = client.table("topic_scores").select("*").eq(
        "user_id", user_id
    ).execute().data

    sessions = client.table("sessions").select("*").eq(
        "user_id", user_id
    ).order("created_at", desc=True).limit(5).execute().data

    levels = client.table("topic_levels").select("*").eq(
        "user_id", user_id
    ).execute().data

    level_map = {row["topic"]: row["level"] for row in levels}

    weak = [s for s in scores if s["total_answers"] > 0
            and s["correct_answers"] / s["total_answers"] < 0.7]

    return {
        "scores": scores,
        "recent_sessions": sessions,
        "weak_subtopics": weak,
        "levels": level_map,
    }


def get_english_coach_data(user_id: str) -> dict:
    from collections import defaultdict

    sessions = client.table("sessions").select("id").eq("user_id", user_id).execute()
    session_ids = [s["id"] for s in sessions.data]

    if not session_ids:
        return {
            "recent_answers": [],
            "trends": [],
            "weakest_category": None,
            "recommendation": "Complete a session to see your English progress.",
        }

    answers = client.table("answers").select(
        "id, session_id, question, user_answer, grammar_score, vocabulary_score, "
        "structure_score, fluency_score, english_tips, created_at"
    ).in_("session_id", session_ids).order("created_at", desc=True).limit(50).execute()

    rows = [r for r in answers.data if r.get("grammar_score") is not None]

    recent_answers = rows[:10]

    session_rows_map = defaultdict(list)
    session_date_map = {}
    for r in reversed(rows):
        session_rows_map[r["session_id"]].append(r)
        session_date_map[r["session_id"]] = r["created_at"]

    def avg(values):
        filtered = [v for v in values if v is not None]
        return round(sum(filtered) / len(filtered), 1) if filtered else None

    trends = []
    for sid in sorted(session_rows_map, key=lambda s: session_date_map[s]):
        sr = session_rows_map[sid]
        trends.append({
            "session_id": sid,
            "grammar_avg": avg([r["grammar_score"] for r in sr]),
            "vocabulary_avg": avg([r["vocabulary_score"] for r in sr]),
            "structure_avg": avg([r["structure_score"] for r in sr]),
            "fluency_avg": avg([r["fluency_score"] for r in sr]),
            "created_at": session_date_map[sid],
        })

    recent_ten = rows[:10]
    category_avgs = {
        "grammar": avg([r["grammar_score"] for r in recent_ten]),
        "vocabulary": avg([r["vocabulary_score"] for r in recent_ten]),
        "structure": avg([r["structure_score"] for r in recent_ten]),
        "fluency": avg([r["fluency_score"] for r in recent_ten]),
    }
    filled = {k: v for k, v in category_avgs.items() if v is not None}
    weakest_category = min(filled, key=filled.get) if filled else None

    recommendations = {
        "grammar": "Focus on verb tenses and sentence structure. Use complete sentences with clear subject-verb-object order.",
        "vocabulary": "Expand your technical vocabulary. Replace 'check' with 'inspect', 'monitor', or 'diagnose'. Use precise terms.",
        "structure": "Structure answers as: 1) Identify, 2) Investigate, 3) Fix, 4) Verify. Use 'First...', 'Then...', 'Finally...'",
        "fluency": "Vary sentence length and use linking words: 'therefore', 'however', 'as a result', 'consequently'.",
    }
    recommendation = (
        recommendations.get(weakest_category, "Keep practicing!")
        if weakest_category
        else "Complete more sessions to see personalised recommendations."
    )

    return {
        "recent_answers": recent_answers,
        "trends": trends,
        "weakest_category": weakest_category,
        "recommendation": recommendation,
    }
