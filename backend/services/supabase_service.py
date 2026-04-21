import os
from supabase import create_client

client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"],
)


def create_session(user_id: str, topic: str, subtopic: str) -> str:
    result = client.table("sessions").insert({
        "user_id": user_id,
        "topic": topic,
        "subtopic": subtopic,
    }).execute()
    return result.data[0]["id"]


def save_answer(session_id: str, question: str, question_type: str,
                subtopic: str, user_answer: str, feedback: str, score: int):
    client.table("answers").insert({
        "session_id": session_id,
        "question": question,
        "question_type": question_type,
        "subtopic": subtopic,
        "user_answer": user_answer,
        "feedback": feedback,
        "score": score,
    }).execute()

    result = client.table("topic_scores").select("*").eq(
        "subtopic", subtopic
    ).execute()

    if result.data:
        row = result.data[0]
        client.table("topic_scores").update({
            "correct_answers": row["correct_answers"] + (1 if score >= 7 else 0),
            "total_answers": row["total_answers"] + 1,
        }).eq("id", row["id"]).execute()
    else:
        session = client.table("sessions").select("user_id").eq(
            "id", session_id
        ).execute()
        user_id = session.data[0]["user_id"]
        client.table("topic_scores").insert({
            "user_id": user_id,
            "subtopic": subtopic,
            "correct_answers": 1 if score >= 7 else 0,
            "total_answers": 1,
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


def get_dashboard_data(user_id: str) -> dict:
    scores = client.table("topic_scores").select("*").eq(
        "user_id", user_id
    ).execute().data

    sessions = client.table("sessions").select("*").eq(
        "user_id", user_id
    ).order("created_at", desc=True).limit(10).execute().data

    weak = [s for s in scores if s["total_answers"] > 0
            and s["correct_answers"] / s["total_answers"] < 0.7]

    return {"scores": scores, "recent_sessions": sessions, "weak_subtopics": weak}
