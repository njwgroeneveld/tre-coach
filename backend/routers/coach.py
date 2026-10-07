from fastapi import APIRouter, Depends
from auth import current_user
from services.supabase_service import get_english_coach_data

router = APIRouter()


@router.get("/")
def get_coach(user_id: str = Depends(current_user)):
    return get_english_coach_data(user_id)
