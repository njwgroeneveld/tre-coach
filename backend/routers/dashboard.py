from fastapi import APIRouter, Depends
from auth import current_user
from services.supabase_service import get_dashboard_data

router = APIRouter()


@router.get("/")
def dashboard(user_id: str = Depends(current_user)):
    return get_dashboard_data(user_id)
