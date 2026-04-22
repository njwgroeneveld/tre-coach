import random
from fastapi import APIRouter, Header, HTTPException
from models import StartSessionRequest, AnswerRequest, HintRequest, QuestionResponse, FeedbackResponse, HintResponse
from services.claude_service import generate_question, generate_hint, SUBTOPICS
from services.supabase_service import create_session, save_answer, get_weakest_subtopic, get_weakest_topic, get_topic_level

router = APIRouter()


def get_user_id(authorization: str) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    import jwt
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload["sub"]


@router.post("/start")
def start_session(body: StartSessionRequest, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    if body.topic:
        topic = body.topic
        subtopic = get_weakest_subtopic(user_id, topic) or random.choice(SUBTOPICS[topic])
    else:
        # App stelt voor: zwakste topic/subtopic over alle onderwerpen
        weakest = get_weakest_topic(user_id)
        topic = weakest["topic"]
        subtopic = weakest["subtopic"] or random.choice(SUBTOPICS[topic])

    level = body.level or get_topic_level(user_id, topic)

    # Shuffle subtopics voor rotatie binnen sessie
    subtopics = SUBTOPICS[topic].copy()
    random.shuffle(subtopics)

    session_id = create_session(user_id, topic, subtopic, level)
    return {
        "session_id": session_id,
        "topic": topic,
        "subtopic": subtopic,
        "level": level,
        "subtopics": subtopics,
    }


@router.post("/question")
def get_question(session_id: str, subtopic: str, level: str = "basis"):
    question_type = "scenario" if random.random() < 0.7 else "command"
    question = generate_question(subtopic, question_type, level)
    return QuestionResponse(question=question, question_type=question_type, subtopic=subtopic, level=level)


@router.post("/hint")
def get_hint(body: HintRequest) -> HintResponse:
    hint = generate_hint(body.question, body.subtopic, body.hint_number, body.previous_answer)
    return HintResponse(hint=hint, hint_number=body.hint_number)


@router.post("/answer")
def submit_answer(body: AnswerRequest) -> FeedbackResponse:
    from services.claude_service import evaluate_answer
    result = evaluate_answer(body.question, body.user_answer, body.subtopic, body.level)
    save_answer(
        session_id=body.session_id,
        question=body.question,
        question_type=body.question_type,
        subtopic=body.subtopic,
        user_answer=body.user_answer,
        feedback=result["feedback"],
        score=result["score"],
        interview_taal=result["interview_taal"],
        pi_commando=result["pi_commando"],
    )
    return FeedbackResponse(
        feedback=result["feedback"],
        interview_taal=result["interview_taal"],
        pi_commando=result["pi_commando"],
        session_id=body.session_id,
    )
