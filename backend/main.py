from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import session, dashboard, coach, investigation
from services.claude_service import ClaudeRefusal
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://*.netlify.app", "https://leer-coach.nielsgroeneveld.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(ClaudeRefusal)
def claude_refusal(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Claude declined this request. Try the next question."})


app.include_router(session.router, prefix="/session")
app.include_router(dashboard.router, prefix="/dashboard")
app.include_router(coach.router, prefix="/coach")
app.include_router(investigation.router, prefix="/investigation")

@app.get("/health")
def health():
    return {"status": "ok"}
