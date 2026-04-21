from fastapi import APIRouter, Header
from services.supabase_service import get_dashboard_data
import jwt

router = APIRouter()


@router.get("/")
def dashboard(authorization: str = Header(...)):
    token = authorization.split(" ")[1]
    user_id = jwt.decode(token, options={"verify_signature": False})["sub"]
    return get_dashboard_data(user_id)
