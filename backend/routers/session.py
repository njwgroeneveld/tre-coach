import os
import random
from fastapi import APIRouter, Depends, HTTPException
from auth import current_user, require_own_session
from models import StartSessionRequest, AnswerRequest, HintRequest, QuestionResponse, FeedbackResponse, HintResponse, FollowupRequest, FollowupResponse
from services.claude_service import generate_question, generate_hint, generate_followup, SUBTOPICS
from services.supabase_service import create_session, save_answer, get_weakest_subtopic, get_weakest_topic, get_topic_level
from services.causes import CAUSES
from routers.investigation import start_investigation

router = APIRouter()



@router.post("/start")
def start_session(body: StartSessionRequest, user_id: str = Depends(current_user)):
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
def get_question(session_id: str, subtopic: str, level: str = "basis", user_id: str = Depends(current_user)):
    require_own_session(session_id, user_id)
    roll = random.random()
    if subtopic in CAUSES:
        # Performance subtopics: 50% investigation, 30% scenario, 20% command.
        question_type = "investigation" if roll < 0.5 else "scenario" if roll < 0.8 else "command"
    else:
        question_type = "scenario" if roll < 0.7 else "command"
    # Local testing only: FORCE_QUESTION_TYPE=investigation|scenario|command (never set in production).
    forced = os.environ.get("FORCE_QUESTION_TYPE")
    if forced in ("scenario", "command") or (forced == "investigation" and subtopic in CAUSES):
        question_type = forced

    if question_type == "investigation":
        investigation_id, symptom = start_investigation(session_id, subtopic, level, user_id)
        return QuestionResponse(question=symptom, question_type=question_type, subtopic=subtopic, level=level,
                                investigation_id=investigation_id)
    question = generate_question(subtopic, question_type, level)
    return QuestionResponse(question=question, question_type=question_type, subtopic=subtopic, level=level)


@router.post("/hint")
def get_hint(body: HintRequest, user_id: str = Depends(current_user)) -> HintResponse:
    hint = generate_hint(body.question, body.subtopic, body.hint_number, body.previous_answer)
    return HintResponse(hint=hint, hint_number=body.hint_number)


@router.post("/followup")
def followup(body: FollowupRequest, user_id: str = Depends(current_user)) -> FollowupResponse:
    answer = generate_followup(
        question=body.question,
        subtopic=body.subtopic,
        user_answer=body.user_answer,
        feedback=body.feedback,
        followup_question=body.followup_question,
        history=[m.model_dump() for m in body.history],
    )
    return FollowupResponse(answer=answer)


@router.post("/answer")
def submit_answer(body: AnswerRequest, user_id: str = Depends(current_user)) -> FeedbackResponse:
    require_own_session(body.session_id, user_id)
    from services.claude_service import evaluate_answer
    result = evaluate_answer(body.question, body.user_answer, body.subtopic, body.level, body.question_type)
    save_answer(
        session_id=body.session_id,
        question=body.question,
        question_type=body.question_type,
        subtopic=body.subtopic,
        user_answer=body.user_answer,
        feedback=result["feedback"],
        score=result["score"],
        interview_answer=result["interview_answer"],
        pi_commando=result["pi_commando"],
        grammar_score=result["grammar_score"],
        vocabulary_score=result["vocabulary_score"],
        structure_score=result["structure_score"],
        fluency_score=result["fluency_score"],
        english_tips=result["english_tips"],
    )
    return FeedbackResponse(
        feedback=result["feedback"],
        interview_answer=result["interview_answer"],
        pi_commando=result["pi_commando"],
        session_id=body.session_id,
        grammar_score=result["grammar_score"],
        vocabulary_score=result["vocabulary_score"],
        structure_score=result["structure_score"],
        fluency_score=result["fluency_score"],
        english_tips=result["english_tips"],
    )
