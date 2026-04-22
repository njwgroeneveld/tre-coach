import random
from fastapi import APIRouter, Header, HTTPException
from models import StartSessionRequest, AnswerRequest, QuestionResponse, FeedbackResponse
from services.claude_service import generate_question, SUBTOPICS
from services.supabase_service import create_session, save_answer, get_weakest_subtopic

router = APIRouter()


def get_user_id(authorization: str) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    import jwt
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload["sub"]  # Supabase user UUID


@router.post("/start")
def start_session(body: StartSessionRequest, authorization: str = Header(...)):
    user_id = get_user_id(authorization)
    topic = body.topic or random.choice(["linux", "netwerk", "kubernetes"])
    subtopic = get_weakest_subtopic(user_id, topic) or random.choice(SUBTOPICS[topic])
    # Shuffle subtopics voor deze sessie zodat elke vraag een ander onderwerp heeft
    subtopics = SUBTOPICS[topic].copy()
    random.shuffle(subtopics)
    session_id = create_session(user_id, topic, subtopic)
    return {"session_id": session_id, "topic": topic, "subtopic": subtopic, "subtopics": subtopics}


@router.post("/question")
def get_question(session_id: str, subtopic: str):
    question_type = "scenario" if random.random() < 0.7 else "command"
    question = generate_question(subtopic, question_type)
    return QuestionResponse(question=question, question_type=question_type, subtopic=subtopic)


@router.post("/answer")
def submit_answer(body: AnswerRequest) -> FeedbackResponse:
    from services.claude_service import evaluate_answer
    feedback, score = evaluate_answer(body.question, body.user_answer, body.subtopic)
    save_answer(
        session_id=body.session_id,
        question=body.question,
        question_type=body.question_type,
        subtopic=body.subtopic,
        user_answer=body.user_answer,
        feedback=feedback,
        score=score,
    )
    return FeedbackResponse(feedback=feedback, score=score, session_id=body.session_id)
