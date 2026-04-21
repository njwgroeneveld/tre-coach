from pydantic import BaseModel

class StartSessionRequest(BaseModel):
    topic: str | None = None  # None = app kiest zwakste subtopic

class AnswerRequest(BaseModel):
    session_id: str
    question: str
    question_type: str
    subtopic: str
    user_answer: str

class QuestionResponse(BaseModel):
    question: str
    question_type: str
    subtopic: str

class FeedbackResponse(BaseModel):
    feedback: str
    score: int
    session_id: str
