from fastapi import APIRouter, Depends, HTTPException
from auth import current_user
from models import (
    FeedbackResponse,
    InvestigationDiagnoseRequest,
    InvestigationDiagnoseResponse,
    InvestigationReveal,
    InvestigationStartRequest,
    InvestigationStartResponse,
    InvestigationStepRequest,
    InvestigationStepResponse,
)
from routers.session import require_own_session
from services.claude_service import evaluate_investigation, format_steps, generate_investigation, judge_diagnosis, simulate_step
from services.supabase_service import add_investigation_step, create_investigation, get_investigation, save_answer, update_investigation

router = APIRouter()

MAX_STEPS = 10
MAX_WRONG_DIAGNOSES = 2


def load_own_investigation(investigation_id: str, user_id: str) -> dict:
    investigation = get_investigation(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    # Same 404 for someone else's investigation, so ids cannot be probed.
    require_own_session(investigation["session_id"], user_id)
    return investigation


def require_open(investigation: dict):
    if investigation["status"] != "open":
        raise HTTPException(status_code=409, detail="This investigation is closed")


def count_commands(steps: list) -> int:
    # Diagnoses are stored in steps too, but only commands count toward the limit.
    return sum(1 for s in steps if s.get("kind") != "diagnosis")


@router.post("/start")
def start(body: InvestigationStartRequest, user_id: str = Depends(current_user)) -> InvestigationStartResponse:
    require_own_session(body.session_id, user_id)
    scenario = generate_investigation(body.subtopic, body.level)
    # Everything except the symptom stays in the database; the trainee only sees the symptom.
    hidden = {
        "cause": scenario.cause,
        "facts": scenario.facts,
        "fix": scenario.fix,
        "fastest_path": scenario.fastest_path,
    }
    investigation_id = create_investigation(body.session_id, body.subtopic, body.level, scenario.symptom, hidden)
    return InvestigationStartResponse(investigation_id=investigation_id, symptom=scenario.symptom)


@router.post("/step")
def step(body: InvestigationStepRequest, user_id: str = Depends(current_user)) -> InvestigationStepResponse:
    investigation = load_own_investigation(body.investigation_id, user_id)
    require_open(investigation)
    steps = investigation["steps"]
    if count_commands(steps) >= MAX_STEPS:
        raise HTTPException(status_code=409, detail="No steps left: make your diagnosis")
    user_input = body.input.strip()
    if not user_input:
        raise HTTPException(status_code=422, detail="Empty command")

    result = simulate_step(investigation["hidden"], steps, user_input)
    steps = steps + [{"kind": "command", "input": user_input, "output": result.output}]
    risky_actions = investigation["risky_actions"] + (1 if result.risky_action else 0)
    add_investigation_step(body.investigation_id, steps, risky_actions)
    return InvestigationStepResponse(output=result.output, steps_left=MAX_STEPS - count_commands(steps))


@router.post("/diagnose")
def diagnose(body: InvestigationDiagnoseRequest, user_id: str = Depends(current_user)) -> InvestigationDiagnoseResponse:
    investigation = load_own_investigation(body.investigation_id, user_id)
    require_open(investigation)
    diagnosis = body.diagnosis.strip()
    if not diagnosis:
        raise HTTPException(status_code=422, detail="Empty diagnosis")

    judgement = judge_diagnosis(investigation["hidden"], investigation["steps"], diagnosis)
    wrong = investigation["wrong_diagnoses"] + (0 if judgement.correct else 1)
    if judgement.correct:
        status = "solved"
    elif wrong >= MAX_WRONG_DIAGNOSES:
        status = "revealed"
    else:
        status = "open"
    steps = investigation["steps"] + [{
        "kind": "diagnosis",
        "input": diagnosis,
        "output": "[correct]" if judgement.correct else judgement.consequence,
    }]
    update_investigation(body.investigation_id, {"steps": steps, "wrong_diagnoses": wrong, "status": status})

    if status == "open":
        return InvestigationDiagnoseResponse(
            correct=False, status=status, attempts_left=MAX_WRONG_DIAGNOSES - wrong,
            consequence=judgement.consequence,
        )

    # Closed: grade the whole investigation and store it as an answer, so the dashboard counts it.
    investigation.update(steps=steps, wrong_diagnoses=wrong, status=status)
    result = evaluate_investigation(investigation, solved=judgement.correct)
    hidden = investigation["hidden"]
    save_answer(
        session_id=investigation["session_id"],
        question=investigation["symptom"],
        question_type="investigation",
        subtopic=investigation["subtopic"],
        user_answer=format_steps(steps),
        feedback=result.feedback,
        score=result.score,
        interview_answer=result.interview_answer,
        pi_commando=result.pi_commando,
        grammar_score=result.grammar_score,
        vocabulary_score=result.vocabulary_score,
        structure_score=result.structure_score,
        fluency_score=result.fluency_score,
        english_tips=result.english_tip,
    )
    return InvestigationDiagnoseResponse(
        correct=judgement.correct,
        status=status,
        attempts_left=MAX_WRONG_DIAGNOSES - wrong,
        consequence=None if judgement.correct else judgement.consequence,
        reveal=InvestigationReveal(cause=hidden["cause"], fix=hidden["fix"], fastest_path=hidden["fastest_path"]),
        evaluation=FeedbackResponse(
            feedback=result.feedback,
            score=result.score,
            interview_answer=result.interview_answer,
            pi_commando=result.pi_commando,
            session_id=investigation["session_id"],
            grammar_score=result.grammar_score,
            vocabulary_score=result.vocabulary_score,
            structure_score=result.structure_score,
            fluency_score=result.fluency_score,
            english_tips=result.english_tip,
        ),
    )
