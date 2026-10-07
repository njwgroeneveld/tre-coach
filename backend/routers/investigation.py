from fastapi import APIRouter, Depends
from auth import current_user
from models import InvestigationStartRequest, InvestigationStartResponse
from routers.session import require_own_session
from services.claude_service import generate_investigation
from services.supabase_service import create_investigation

router = APIRouter()


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
