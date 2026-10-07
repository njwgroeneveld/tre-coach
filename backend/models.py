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
    score: int | None = None
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

class InvestigationStartRequest(BaseModel):
    session_id: str
    subtopic: str
    level: str = "basis"

class InvestigationStartResponse(BaseModel):
    investigation_id: str
    symptom: str

class InvestigationStepRequest(BaseModel):
    investigation_id: str
    input: str

class InvestigationStepResponse(BaseModel):
    output: str
    steps_left: int

class InvestigationDiagnoseRequest(BaseModel):
    investigation_id: str
    diagnosis: str

class InvestigationReveal(BaseModel):
    cause: str
    fix: str
    fastest_path: list[str]

class InvestigationDiagnoseResponse(BaseModel):
    correct: bool
    status: str                                 # open, solved or revealed
    attempts_left: int
    consequence: str | None = None              # only after a wrong diagnosis that leaves the case open
    reveal: InvestigationReveal | None = None   # once the investigation is closed
    evaluation: FeedbackResponse | None = None  # once the investigation is closed
