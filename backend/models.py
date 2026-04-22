from pydantic import BaseModel

class StartSessionRequest(BaseModel):
    topic: str | None = None
    level: str | None = None

class AnswerRequest(BaseModel):
    session_id: str
    question: str
    question_type: str
    subtopic: str
    user_answer: str
    level: str = "basis"

class HintRequest(BaseModel):
    question: str
    subtopic: str
    hint_number: int
    previous_answer: str = ""

class QuestionResponse(BaseModel):
    question: str
    question_type: str
    subtopic: str
    level: str

class FeedbackResponse(BaseModel):
    feedback: str
    interview_answer: str
    pi_commando: str
    session_id: str
    grammar_score: int | None = None
    vocabulary_score: int | None = None
    structure_score: int | None = None
    fluency_score: int | None = None
    english_tips: str = ""

class HintResponse(BaseModel):
    hint: str
    hint_number: int

class FollowupMessage(BaseModel):
    role: str  # 'user' or 'coach'
    text: str

class FollowupRequest(BaseModel):
    question: str
    subtopic: str
    user_answer: str
    feedback: str
    followup_question: str
    history: list[FollowupMessage] = []

class FollowupResponse(BaseModel):
    answer: str
