import os

import jwt
from dotenv import load_dotenv
from fastapi import Header, HTTPException
from services.supabase_service import session_belongs_to

load_dotenv()

# Supabase signs access tokens with an asymmetric key (ES256); the public half is published here.
_jwks = jwt.PyJWKClient(f"{os.environ['SUPABASE_URL']}/auth/v1/.well-known/jwks.json")


def current_user(authorization: str | None = Header(None)) -> str:
    """FastAPI dependency: verify the Supabase access token and return the user id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    try:
        key = _jwks.get_signing_key_from_jwt(token)
        payload = jwt.decode(token, key, algorithms=["ES256"], audience="authenticated")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return payload["sub"]


def require_own_session(session_id: str, user_id: str):
    if not session_belongs_to(session_id, user_id):
        raise HTTPException(status_code=404, detail="Session not found")
