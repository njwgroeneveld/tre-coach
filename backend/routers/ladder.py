from fastapi import APIRouter, Depends, HTTPException
from auth import current_user
from models import DrillAnswerRequest, DrillAnswerResponse, DrillRequest, DrillResponse
from services.claude_service import grade_drill
from services.ladder import (
    LESSONS, PARTS, VERDICT_SCORES, all_drill_subtopics, build_drill, drill_subtopic, ladder_progress, new_drill_id,
)
from services.supabase_service import get_ladder_session, recent_drill_questions, recent_drill_scores, save_answer

router = APIRouter()


def progress_for(user_id: str) -> list[dict]:
    return ladder_progress(recent_drill_scores(user_id, all_drill_subtopics()))


@router.get("/lessons")
def lessons(user_id: str = Depends(current_user)) -> list[dict]:
    return progress_for(user_id)


@router.get("/lessons/{lesson}")
def lesson_card(lesson: str, user_id: str = Depends(current_user)) -> dict:
    if lesson not in LESSONS:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return LESSONS[lesson]["card"]


@router.post("/drill")
def drill(body: DrillRequest, user_id: str = Depends(current_user)) -> DrillResponse:
    if body.lesson not in LESSONS or body.kind not in PARTS:
        raise HTTPException(status_code=404, detail="Lesson not found")
    progress = next(p for p in progress_for(user_id) if p["lesson"] == body.lesson)
    if not progress[body.kind]["unlocked"]:
        raise HTTPException(status_code=403, detail="Not unlocked yet")
    asked = recent_drill_questions(user_id, drill_subtopic(body.lesson, body.kind))
    d = build_drill(new_drill_id(body.lesson, body.kind, asked, body.previous_drill_id))
    # key_points and the situation stay on the server: they are the answer.
    return DrillResponse(drill_id=d["drill_id"], lesson=d["lesson"], kind=d["kind"],
                         context=d["context"], output=d["output"], question=d["question"])


@router.post("/answer")
def answer(body: DrillAnswerRequest, user_id: str = Depends(current_user)) -> DrillAnswerResponse:
    try:
        d = build_drill(body.drill_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown drill")
    text = body.answer.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Empty answer")

    grade = grade_drill(d, text)
    save_answer(
        session_id=get_ladder_session(user_id),
        question="\n".join(part for part in [d["context"], d["output"], d["question"]] if part),
        question_type="drill",
        subtopic=drill_subtopic(d["lesson"], d["kind"]),
        user_answer=text,
        feedback=grade.feedback,
        score=VERDICT_SCORES[grade.verdict],
        interview_answer="",
        pi_commando="",
        grammar_score=None,
        vocabulary_score=None,
        structure_score=None,
        fluency_score=None,
        english_tips="",
    )
    return DrillAnswerResponse(verdict=grade.verdict, feedback=grade.feedback,
                               key_points=d["key_points"], bonus_points=d.get("bonus", []),
                               progress=progress_for(user_id))
