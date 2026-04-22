from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import session, dashboard
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://*.netlify.app", "https://leer-coach.nielsgroeneveld.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router, prefix="/session")
app.include_router(dashboard.router, prefix="/dashboard")

@app.get("/health")
def health():
    return {"status": "ok"}
