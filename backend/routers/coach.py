from fastapi import APIRouter, Header
from services.supabase_service import get_english_coach_data
import jwt

router = APIRouter()


@router.get("/")
def get_coach(authorization: str = Header(...)):
    token = authorization.split(" ")[1]
    user_id = jwt.decode(token, options={"verify_signature": False})["sub"]
    return get_english_coach_data(user_id)
