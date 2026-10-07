from fastapi import APIRouter, Depends, HTTPException
from auth import current_user
from models import InvestigationStartRequest, InvestigationStartResponse, InvestigationStepRequest, InvestigationStepResponse
from routers.session import require_own_session
from services.claude_service import generate_investigation, simulate_step
from services.supabase_service import create_investigation, get_investigation, add_investigation_step

router = APIRouter()

MAX_STEPS = 10


def load_own_investigation(investigation_id: str, user_id: str) -> dict:
    investigation = get_investigation(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    # Same 404 for someone else's investigation, so ids cannot be probed.
    require_own_session(investigation["session_id"], user_id)
    return investigation


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
    if investigation["status"] != "open":
        raise HTTPException(status_code=409, detail="This investigation is closed")
    steps = investigation["steps"]
    if len(steps) >= MAX_STEPS:
        raise HTTPException(status_code=409, detail="No steps left: make your diagnosis")
    user_input = body.input.strip()
    if not user_input:
        raise HTTPException(status_code=422, detail="Empty command")

    result = simulate_step(investigation["hidden"], steps, user_input)
    steps = steps + [{"input": user_input, "output": result.output}]
    risky_actions = investigation["risky_actions"] + (1 if result.risky_action else 0)
    add_investigation_step(body.investigation_id, steps, risky_actions)
    return InvestigationStepResponse(output=result.output, steps_left=MAX_STEPS - len(steps))
