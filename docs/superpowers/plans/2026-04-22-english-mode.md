# English Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert TRE Coach fully to English, add optional voice input via Web Speech API, and add a `/coach` page showing English language progress over time.

**Architecture:** All Claude prompts in `claude_service.py` are rewritten in English; `evaluate_answer()` is extended to return English scores (grammar, vocabulary, structure, fluency) in the same Claude call. Five new columns are added to the `answers` table. A new `/coach` backend route aggregates those scores per session. A new `Coach.jsx` frontend page renders trend lines using recharts.

**Tech Stack:** React 19 + Vite + Tailwind + react-router-dom, FastAPI, Supabase (postgres), Claude Sonnet 4-6, Web Speech API (browser-native), recharts

---

## File Map

| File | Action | What changes |
|---|---|---|
| `supabase/schema.sql` | Modify | Add 5 new column definitions |
| `backend/services/claude_service.py` | Modify | All prompts → English; `evaluate_answer()` returns English scores |
| `backend/models.py` | Modify | `FeedbackResponse` adds English score fields; rename `interview_taal` → `interview_answer` |
| `backend/services/supabase_service.py` | Modify | `save_answer()` stores English scores; add `get_english_coach_data()` |
| `backend/routers/coach.py` | Create | `GET /coach/` route |
| `backend/main.py` | Modify | Register coach router |
| `frontend/src/pages/Dashboard.jsx` | Modify | UI text → English |
| `frontend/src/pages/Results.jsx` | Modify | UI text → English |
| `frontend/src/pages/Session.jsx` | Modify | Voice input button; English feedback block; rename `interview_taal` → `interview_answer`; UI text → English |
| `frontend/src/components/ChatBubble.jsx` | Modify | Add `english` role; translate label strings |
| `frontend/src/pages/Coach.jsx` | Create | Coach dashboard with trend charts |
| `frontend/src/App.jsx` | Modify | Add `/coach` route |

---

## Task 1: Database — add English score columns

**Files:**
- Modify: `supabase/schema.sql`

- [ ] **Step 1: Run migration in Supabase SQL editor**

Open the Supabase dashboard → SQL Editor → run:

```sql
alter table answers
  add column if not exists grammar_score    integer,
  add column if not exists vocabulary_score integer,
  add column if not exists structure_score  integer,
  add column if not exists fluency_score    integer,
  add column if not exists english_tips     text default '';
```

- [ ] **Step 2: Verify columns exist**

In the Supabase Table Editor open the `answers` table and confirm the 5 new columns appear.

- [ ] **Step 3: Update schema.sql to reflect the new columns**

Add the following lines inside the `answers` table definition in `supabase/schema.sql`, after the `pi_commando` line:

```sql
  grammar_score    integer,
  vocabulary_score integer,
  structure_score  integer,
  fluency_score    integer,
  english_tips     text default '',
```

- [ ] **Step 4: Commit**

```bash
cd tre-coach
git add supabase/schema.sql
git commit -m "feat: add English score columns to answers table"
```

---

## Task 2: Backend — convert all Claude prompts to English and add English analysis

**Files:**
- Modify: `backend/services/claude_service.py`

- [ ] **Step 1: Replace the entire file contents**

Replace `backend/services/claude_service.py` with:

```python
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SUBTOPICS = {
    "linux": [
        "processen_performance",
        "geheugen_analyse",
        "disk_problemen",
        "file_descriptors",
        "proc_filesystem",
        "logging_journalctl",
    ],
    "netwerk": [
        "tcp_fundamenten",
        "tcp_connection_states",
        "port_exhaustion",
        "dns_problemen",
        "tcpdump",
        "websocket",
    ],
    "kubernetes": [
        "pods_en_deployments",
        "crashloopbackoff",
        "resource_limits",
        "rolling_updates",
        "services_en_networking",
        "logs_en_debugging",
    ],
    "trading": [
        "slippage_en_latency",
        "order_types",
        "exchange_connectiviteit",
        "incident_response",
        "release_management",
        "monitoring_en_alerts",
    ],
}

TRADING_CONTEXT = {
    "websocket": "WebSocket connection to exchange lost — orders are not getting through.",
    "port_exhaustion": "Port exhaustion — the bot cannot open new connections to the exchange.",
    "dns_problemen": "DNS timeout — the bot cannot resolve the exchange hostname.",
    "crashloopbackoff": "Trading bot pod is crash-looping — orders are not being processed.",
    "rolling_updates": "Rolling out a new version while the market is open.",
    "resource_limits": "Bot killed by Kubernetes OOM during high volatility.",
    "slippage_en_latency": "Trader reports bad fills — orders are executing at worse prices than expected.",
    "incident_response": "Trading bot has been offline for 3 minutes — traders are complaining.",
    "release_management": "Deploying a new version while the market is open — what is your approach?",
}

LEVEL_CONTEXT = {
    "basis": (
        "Foundation level — must be mastered perfectly for the interview. "
        "Ask recognisable questions about common situations with one clear approach. "
        "No edge cases. Suitable for someone with some Linux/K8s experience."
    ),
    "gemiddeld": (
        "Intermediate level — what a trading firm expects from an engineer with 2+ years of experience. "
        "Ask practical questions with multiple possible root causes. "
        "Link to trading impact. The candidate must reason, not just list commands."
    ),
}


def generate_question(subtopic: str, question_type: str, level: str = "basis") -> str:
    trading_hint = ""
    if subtopic in TRADING_CONTEXT:
        trading_hint = f"\nTrading context: {TRADING_CONTEXT[subtopic]}"

    level_instruction = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT["basis"])

    if question_type == "scenario":
        prompt = f"""Generate one scenario question for a Trading Reliability Engineer (TRE) trainee about '{subtopic}'.
The question describes a concrete production problem. The candidate explains their approach step by step.
{trading_hint}

Level: {level.upper()} — {level_instruction}

Write only the question, no answer. Maximum 4 sentences. Write in English."""
    else:
        prompt = f"""Generate one command flash-card question for a TRE trainee about '{subtopic}'.
Ask about a specific command or what its output means.

Level: {level.upper()} — {level_instruction}

Write only the question. Maximum 2 sentences. Write in English."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_hint(question: str, subtopic: str, hint_number: int, previous_answer: str = "") -> str:
    hint_instructions = {
        1: "Point in a direction without giving away the answer. One sentence.",
        2: "Name a specific command or concept that is relevant. Maximum 2 sentences.",
        3: "Explain what you would expect to see if you follow the right path. Maximum 3 sentences.",
    }
    instruction = hint_instructions.get(hint_number, hint_instructions[1])

    prompt = f"""You are a TRE mentor. A trainee is struggling with this question.

Question: {question}
Topic: {subtopic}
{f"Trainee's last answer: {previous_answer}" if previous_answer else ""}

Give hint {hint_number}/3: {instruction}
Write in English. Do NOT give the full answer."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_followup(question: str, subtopic: str, user_answer: str, feedback: str, followup_question: str, history: list) -> str:
    messages = [
        {
            "role": "user",
            "content": f"""You are a TRE mentor at a trading firm. A trainee has just answered a practice question and wants to ask follow-up questions.

Original question: {question}
Topic: {subtopic}
Trainee's answer: {user_answer}
Your feedback was: {feedback}

The trainee can now ask freely. Answer concisely and practically in English. Focus on understanding, give concrete examples or commands where relevant."""
        },
        {"role": "assistant", "content": "Of course, go ahead and ask."}
    ]

    for msg in history:
        messages.append({"role": "user" if msg["role"] == "user" else "assistant", "content": msg["text"]})

    messages.append({"role": "user", "content": followup_question})

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=messages,
    )
    return message.content[0].text.strip()


def evaluate_answer(question: str, user_answer: str, subtopic: str, level: str = "basis") -> dict:
    level_instruction = LEVEL_CONTEXT.get(level, LEVEL_CONTEXT["basis"])

    prompt = f"""You are a patient TRE mentor at a trading firm. Evaluate this answer.

Level: {level.upper()} — {level_instruction}
Topic: {subtopic}
Question: {question}
Trainee's answer: {user_answer}

Give your evaluation in this exact format:

FEEDBACK: <what was good + what the trainee missed + correct approach, maximum 150 words>
SCORE: <integer 0-10>
INTERVIEW: <how you would phrase this in a trading-firm interview, 2-3 sentences>
PI_COMMANDO: <one or two concrete Linux/kubectl commands the trainee can run on a Raspberry Pi to simulate this, with a short explanation>
GRAMMAR_SCORE: <integer 0-10, evaluate verb tenses, sentence construction, subject-verb agreement>
VOCABULARY_SCORE: <integer 0-10, evaluate technical term accuracy, word variety, appropriate register>
STRUCTURE_SCORE: <integer 0-10, evaluate logical flow, clear reasoning steps, answer completeness>
FLUENCY_SCORE: <integer 0-10, evaluate sentence variety, filler avoidance, use of linking words like therefore/however/as a result>
ENGLISH_TIP: <one concrete actionable tip to improve English, maximum 20 words, e.g. "Use 'therefore' instead of 'so' to sound more professional">"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )

    response = message.content[0].text.strip()
    result = {
        "feedback": "",
        "score": 5,
        "interview_answer": "",
        "pi_commando": "",
        "grammar_score": None,
        "vocabulary_score": None,
        "structure_score": None,
        "fluency_score": None,
        "english_tips": "",
    }

    sections = {
        "FEEDBACK": "", "SCORE": "", "INTERVIEW": "", "PI_COMMANDO": "",
        "GRAMMAR_SCORE": "", "VOCABULARY_SCORE": "", "STRUCTURE_SCORE": "",
        "FLUENCY_SCORE": "", "ENGLISH_TIP": "",
    }
    current = None
    for line in response.split("\n"):
        for key in sections:
            if line.startswith(f"{key}:"):
                current = key
                sections[key] = line.split(f"{key}:", 1)[1].strip()
                break
        else:
            if current and line.strip():
                sections[current] += " " + line.strip()

    result["feedback"] = sections["FEEDBACK"].strip()
    result["interview_answer"] = sections["INTERVIEW"].strip()
    result["pi_commando"] = sections["PI_COMMANDO"].strip()
    result["english_tips"] = sections["ENGLISH_TIP"].strip()

    for field, key in [
        ("score", "SCORE"),
        ("grammar_score", "GRAMMAR_SCORE"),
        ("vocabulary_score", "VOCABULARY_SCORE"),
        ("structure_score", "STRUCTURE_SCORE"),
        ("fluency_score", "FLUENCY_SCORE"),
    ]:
        try:
            result[field] = int(sections[key].strip().split()[0])
        except (ValueError, IndexError):
            result[field] = 5 if field == "score" else None

    return result
```

- [ ] **Step 2: Manual verification**

Start the backend and call evaluate_answer via a quick test in the Python REPL (inside the venv):

```bash
cd tre-coach/backend
source venv/Scripts/activate  # Windows: venv\Scripts\activate
python -c "
from services.claude_service import evaluate_answer
r = evaluate_answer('What happens when a pod enters CrashLoopBackOff?', 'I would check the logs using kubectl logs', 'crashloopbackoff', 'basis')
print(r.keys())
print('grammar_score:', r['grammar_score'])
print('english_tips:', r['english_tips'])
"
```

Expected: all keys present, `grammar_score` is an integer 0-10, `english_tips` is a non-empty string.

- [ ] **Step 3: Commit**

```bash
git add backend/services/claude_service.py
git commit -m "feat: convert all Claude prompts to English and add English language analysis"
```

---

## Task 3: Backend — update models.py

**Files:**
- Modify: `backend/models.py`

- [ ] **Step 1: Replace models.py**

Replace `backend/models.py` with:

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/models.py
git commit -m "feat: add English score fields to FeedbackResponse, rename interview_taal to interview_answer"
```

---

## Task 4: Backend — update supabase_service.py

**Files:**
- Modify: `backend/services/supabase_service.py`

- [ ] **Step 1: Update save_answer() signature and body**

In `save_answer()`, add 5 new parameters and include them in the insert. Replace the function:

```python
def save_answer(session_id: str, question: str, question_type: str,
                subtopic: str, user_answer: str, feedback: str, score: int,
                interview_answer: str, pi_commando: str,
                grammar_score: int | None, vocabulary_score: int | None,
                structure_score: int | None, fluency_score: int | None,
                english_tips: str):
    client.table("answers").insert({
        "session_id": session_id,
        "question": question,
        "question_type": question_type,
        "subtopic": subtopic,
        "user_answer": user_answer,
        "feedback": feedback,
        "score": score,
        "interview_taal": interview_answer,
        "pi_commando": pi_commando,
        "grammar_score": grammar_score,
        "vocabulary_score": vocabulary_score,
        "structure_score": structure_score,
        "fluency_score": fluency_score,
        "english_tips": english_tips,
    }).execute()

    session = client.table("sessions").select("user_id, topic").eq("id", session_id).execute()
    user_id = session.data[0]["user_id"]
    topic = session.data[0]["topic"]

    result = client.table("topic_scores").select("*").eq(
        "user_id", user_id
    ).eq("subtopic", subtopic).execute()

    if result.data:
        row = result.data[0]
        client.table("topic_scores").update({
            "correct_answers": row["correct_answers"] + (1 if score >= 7 else 0),
            "total_answers": row["total_answers"] + 1,
        }).eq("id", row["id"]).execute()
    else:
        client.table("topic_scores").insert({
            "user_id": user_id,
            "subtopic": subtopic,
            "correct_answers": 1 if score >= 7 else 0,
            "total_answers": 1,
        }).execute()

    _check_level_progression(user_id, topic)
```

- [ ] **Step 2: Add get_english_coach_data() at the end of the file**

```python
def get_english_coach_data(user_id: str) -> dict:
    from collections import defaultdict

    sessions = client.table("sessions").select("id").eq("user_id", user_id).execute()
    session_ids = [s["id"] for s in sessions.data]

    if not session_ids:
        return {
            "recent_answers": [],
            "trends": [],
            "weakest_category": None,
            "recommendation": "Complete a session to see your English progress.",
        }

    answers = client.table("answers").select(
        "id, session_id, question, user_answer, grammar_score, vocabulary_score, "
        "structure_score, fluency_score, english_tips, created_at"
    ).in_("session_id", session_ids).order("created_at", desc=True).limit(50).execute()

    rows = [r for r in answers.data if r.get("grammar_score") is not None]

    recent_answers = rows[:10]

    session_rows_map = defaultdict(list)
    session_date_map = {}
    for r in reversed(rows):
        session_rows_map[r["session_id"]].append(r)
        session_date_map[r["session_id"]] = r["created_at"]

    def avg(values):
        filtered = [v for v in values if v is not None]
        return round(sum(filtered) / len(filtered), 1) if filtered else None

    trends = []
    for sid in sorted(session_rows_map, key=lambda s: session_date_map[s]):
        sr = session_rows_map[sid]
        trends.append({
            "session_id": sid,
            "grammar_avg": avg([r["grammar_score"] for r in sr]),
            "vocabulary_avg": avg([r["vocabulary_score"] for r in sr]),
            "structure_avg": avg([r["structure_score"] for r in sr]),
            "fluency_avg": avg([r["fluency_score"] for r in sr]),
            "created_at": session_date_map[sid],
        })

    recent_ten = rows[:10]
    category_avgs = {
        "grammar": avg([r["grammar_score"] for r in recent_ten]),
        "vocabulary": avg([r["vocabulary_score"] for r in recent_ten]),
        "structure": avg([r["structure_score"] for r in recent_ten]),
        "fluency": avg([r["fluency_score"] for r in recent_ten]),
    }
    filled = {k: v for k, v in category_avgs.items() if v is not None}
    weakest_category = min(filled, key=filled.get) if filled else None

    recommendations = {
        "grammar": "Focus on verb tenses and sentence structure. Use complete sentences with clear subject-verb-object order.",
        "vocabulary": "Expand your technical vocabulary. Replace 'check' with 'inspect', 'monitor', or 'diagnose'. Use precise terms.",
        "structure": "Structure answers as: 1) Identify, 2) Investigate, 3) Fix, 4) Verify. Use 'First...', 'Then...', 'Finally...'",
        "fluency": "Vary sentence length and use linking words: 'therefore', 'however', 'as a result', 'consequently'.",
    }
    recommendation = (
        recommendations.get(weakest_category, "Keep practicing!")
        if weakest_category
        else "Complete more sessions to see personalised recommendations."
    )

    return {
        "recent_answers": recent_answers,
        "trends": trends,
        "weakest_category": weakest_category,
        "recommendation": recommendation,
    }
```

- [ ] **Step 3: Commit**

```bash
git add backend/services/supabase_service.py
git commit -m "feat: save English scores in answers, add get_english_coach_data()"
```

---

## Task 5: Backend — update session router and add coach router

**Files:**
- Modify: `backend/routers/session.py`
- Create: `backend/routers/coach.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Update routers/session.py — rename interview_taal → interview_answer, pass English scores to save_answer**

Replace the `submit_answer` function in `backend/routers/session.py`:

```python
@router.post("/answer")
def submit_answer(body: AnswerRequest) -> FeedbackResponse:
    from services.claude_service import evaluate_answer
    result = evaluate_answer(body.question, body.user_answer, body.subtopic, body.level)
    save_answer(
        session_id=body.session_id,
        question=body.question,
        question_type=body.question_type,
        subtopic=body.subtopic,
        user_answer=body.user_answer,
        feedback=result["feedback"],
        score=result["score"],
        interview_answer=result["interview_answer"],
        pi_commando=result["pi_commando"],
        grammar_score=result["grammar_score"],
        vocabulary_score=result["vocabulary_score"],
        structure_score=result["structure_score"],
        fluency_score=result["fluency_score"],
        english_tips=result["english_tips"],
    )
    return FeedbackResponse(
        feedback=result["feedback"],
        interview_answer=result["interview_answer"],
        pi_commando=result["pi_commando"],
        session_id=body.session_id,
        grammar_score=result["grammar_score"],
        vocabulary_score=result["vocabulary_score"],
        structure_score=result["structure_score"],
        fluency_score=result["fluency_score"],
        english_tips=result["english_tips"],
    )
```

- [ ] **Step 2: Create backend/routers/coach.py**

```python
from fastapi import APIRouter, Header
from services.supabase_service import get_english_coach_data
import jwt

router = APIRouter()


@router.get("/")
def get_coach(authorization: str = Header(...)):
    token = authorization.split(" ")[1]
    user_id = jwt.decode(token, options={"verify_signature": False})["sub"]
    return get_english_coach_data(user_id)
```

- [ ] **Step 3: Register the coach router in backend/main.py**

Change:
```python
from routers import session, dashboard
```
to:
```python
from routers import session, dashboard, coach
```

And add after `app.include_router(dashboard.router, prefix="/dashboard")`:
```python
app.include_router(coach.router, prefix="/coach")
```

- [ ] **Step 4: Manual verification**

Start the backend:
```bash
cd tre-coach/backend
uvicorn main:app --reload
```

Open `http://localhost:8000/docs` and confirm the `/coach/` GET endpoint appears. The `/session/answer` POST should still work.

- [ ] **Step 5: Commit**

```bash
git add backend/routers/session.py backend/routers/coach.py backend/main.py
git commit -m "feat: add coach router and wire English scores through session answer endpoint"
```

---

## Task 6: Frontend — install recharts

**Files:**
- Modify: `frontend/package.json` (via npm)

- [ ] **Step 1: Install recharts**

```bash
cd tre-coach/frontend
npm install recharts
```

- [ ] **Step 2: Verify install**

```bash
grep recharts package.json
```

Expected output: `"recharts": "^2.x.x"` in dependencies.

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: install recharts for English coach dashboard"
```

---

## Task 7: Frontend — translate Dashboard.jsx and Results.jsx to English

**Files:**
- Modify: `frontend/src/pages/Dashboard.jsx`
- Modify: `frontend/src/pages/Results.jsx`

- [ ] **Step 1: Replace Dashboard.jsx**

Replace `frontend/src/pages/Dashboard.jsx` with:

```jsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import TopicCard from '../components/TopicCard'

const API = import.meta.env.VITE_API_URL

const TOPICS = [
  { key: 'linux', label: 'Linux', emoji: '🐧', color: 'bg-blue-600 hover:bg-blue-700' },
  { key: 'netwerk', label: 'TCP/IP Network', emoji: '🌐', color: 'bg-purple-600 hover:bg-purple-700' },
  { key: 'kubernetes', label: 'Kubernetes', emoji: '☸️', color: 'bg-green-700 hover:bg-green-800' },
  { key: 'trading', label: 'Trading Context', emoji: '📈', color: 'bg-orange-600 hover:bg-orange-700' },
]

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => { load() }, [])

  async function load() {
    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/dashboard/`, {
      headers: { Authorization: `Bearer ${session.access_token}` }
    })
    setData(await res.json())
    setLoading(false)
  }

  async function startSession(topic, level) {
    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
      body: JSON.stringify({ topic: topic || null, level: level || null })
    })
    const sessionData = await res.json()
    navigate('/session', { state: sessionData })
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-400">Loading...</p>
    </div>
  )

  const levels = data?.levels || {}
  const weak = data?.weak_subtopics || []

  return (
    <div className="min-h-screen bg-gray-950 p-6 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-white text-2xl font-bold">TRE Coach</h1>
          <p className="text-gray-400 text-sm">Troubleshooting practice for trading systems</p>
        </div>
        <div className="flex gap-4 items-center">
          <button onClick={() => navigate('/coach')} className="text-blue-400 hover:text-blue-300 text-sm">
            English Coach
          </button>
          <button onClick={() => supabase.auth.signOut()} className="text-gray-400 hover:text-white text-sm">
            Sign out
          </button>
        </div>
      </div>

      <div className="bg-gray-900 rounded-xl p-4 mb-6">
        <h2 className="text-white font-semibold mb-3">Your level</h2>
        <div className="grid grid-cols-2 gap-2">
          {TOPICS.map(t => (
            <div key={t.key} className="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2">
              <span className="text-gray-300 text-sm">{t.emoji} {t.label}</span>
              <span className={`text-xs font-bold px-2 py-1 rounded ${
                levels[t.key] === 'gemiddeld' ? 'bg-green-800 text-green-300' : 'bg-gray-700 text-gray-400'
              }`}>
                {levels[t.key] === 'gemiddeld' ? 'Intermediate' : 'Foundation'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {weak.length > 0 && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 mb-6">
          <p className="text-red-400 font-medium mb-1">Weak areas (&lt;70%)</p>
          <p className="text-gray-300 text-sm">{weak.map(w => w.subtopic.replace(/_/g, ' ')).join(', ')}</p>
        </div>
      )}

      <div className="mb-6">
        <h2 className="text-white font-semibold mb-3">Recommended</h2>
        <button
          onClick={() => startSession(null, null)}
          className="w-full bg-gray-700 hover:bg-gray-600 text-white p-4 rounded-xl font-medium text-left"
        >
          <span className="block text-white">🎯 Start recommended session</span>
          <span className="text-gray-400 text-sm">Weakest topic at your current level</span>
        </button>
      </div>

      <div className="mb-8">
        <h2 className="text-white font-semibold mb-3">Choose topic</h2>
        <div className="grid grid-cols-2 gap-3">
          {TOPICS.map(t => (
            <button
              key={t.key}
              onClick={() => startSession(t.key, levels[t.key] || 'basis')}
              className={`${t.color} text-white p-4 rounded-xl font-medium text-left`}
            >
              <span className="block">{t.emoji} {t.label}</span>
              <span className="text-white/70 text-xs">
                {levels[t.key] === 'gemiddeld' ? 'Intermediate' : 'Foundation'}
              </span>
            </button>
          ))}
        </div>
      </div>

      <h2 className="text-white font-semibold mb-3">Progress per topic</h2>
      <div className="space-y-3">
        {(data?.scores || []).map(s => (
          <TopicCard key={s.subtopic} subtopic={s.subtopic} correct={s.correct_answers} total={s.total_answers} />
        ))}
        {(!data?.scores || data.scores.length === 0) && (
          <p className="text-gray-500 text-sm">No sessions yet. Start your first session above!</p>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Replace Results.jsx**

Replace `frontend/src/pages/Results.jsx` with:

```jsx
import { useLocation, useNavigate } from 'react-router-dom'

export default function Results() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const { sessionData } = state || {}

  const topicLabel = sessionData?.topic
    ? sessionData.topic.charAt(0).toUpperCase() + sessionData.topic.slice(1)
    : 'Session'

  const levelLabel = sessionData?.level === 'gemiddeld' ? 'Intermediate' : 'Foundation'

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
      <div className="bg-gray-900 rounded-2xl p-8 max-w-sm w-full text-center space-y-6">
        <div className="text-4xl">✅</div>
        <h1 className="text-white text-2xl font-bold">Session complete!</h1>

        <div className="bg-gray-800 rounded-xl p-4 text-left space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Topic</span>
            <span className="text-white">{topicLabel}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Level</span>
            <span className={`font-medium ${sessionData?.level === 'gemiddeld' ? 'text-green-400' : 'text-gray-300'}`}>
              {levelLabel}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Questions answered</span>
            <span className="text-white">3</span>
          </div>
        </div>

        <p className="text-gray-400 text-sm">
          Your progress has been saved. Weak topics will come back automatically in future sessions.
        </p>

        <div className="space-y-3">
          <button
            onClick={() => navigate('/session', { state: sessionData })}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-xl font-medium"
          >
            Another round
          </button>
          <button
            onClick={() => navigate('/')}
            className="w-full bg-gray-700 hover:bg-gray-600 text-white p-3 rounded-xl"
          >
            Back to dashboard
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Update TopicCard.jsx — translate the one Dutch string**

In `frontend/src/components/TopicCard.jsx`, replace:

```jsx
<p className="text-gray-400 text-xs mt-1">{correct}/{total} goed</p>
```

with:

```jsx
<p className="text-gray-400 text-xs mt-1">{correct}/{total} correct</p>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Dashboard.jsx frontend/src/pages/Results.jsx frontend/src/components/TopicCard.jsx
git commit -m "feat: translate Dashboard, Results, and TopicCard UI to English"
```

---

## Task 8: Frontend — update ChatBubble.jsx

**Files:**
- Modify: `frontend/src/components/ChatBubble.jsx`

- [ ] **Step 1: Replace ChatBubble.jsx**

Replace `frontend/src/components/ChatBubble.jsx` with:

```jsx
export default function ChatBubble({ role, text, subtopic }) {
  if (role === 'question') {
    return (
      <div className="bg-gray-800 rounded-2xl p-4">
        {subtopic && (
          <span className="text-xs text-gray-500 uppercase tracking-wide mb-2 block">
            {subtopic.replace(/_/g, ' ')}
          </span>
        )}
        <p className="text-gray-100 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-blue-600 rounded-2xl p-4">
          <p className="text-white text-sm whitespace-pre-wrap">{text}</p>
        </div>
      </div>
    )
  }

  if (role === 'hint') {
    return (
      <div className="bg-yellow-900/30 border border-yellow-800/50 rounded-2xl p-4">
        <p className="text-yellow-300 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'feedback') {
    return (
      <div className="bg-gray-800 rounded-2xl p-4">
        <span className="text-xs text-gray-500 uppercase tracking-wide mb-2 block">Technical Feedback</span>
        <p className="text-gray-100 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'english') {
    const { grammar_score, vocabulary_score, structure_score, fluency_score, english_tips } = text
    return (
      <div className="bg-indigo-900/30 border border-indigo-700/50 rounded-2xl p-4 space-y-3">
        <span className="text-xs text-indigo-400 uppercase tracking-wide block">English Feedback</span>
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: 'Grammar', score: grammar_score },
            { label: 'Vocabulary', score: vocabulary_score },
            { label: 'Structure', score: structure_score },
            { label: 'Fluency', score: fluency_score },
          ].map(({ label, score }) => (
            <div key={label} className="flex items-center justify-between bg-indigo-900/30 rounded-lg px-3 py-2">
              <span className="text-indigo-300 text-xs">{label}</span>
              <span className={`text-xs font-bold ${score >= 7 ? 'text-green-400' : score >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>
                {score ?? '–'}/10
              </span>
            </div>
          ))}
        </div>
        {english_tips && (
          <p className="text-indigo-200 text-sm">💡 {english_tips}</p>
        )}
      </div>
    )
  }

  if (role === 'interview') {
    return (
      <div className="bg-green-900/30 border border-green-800/50 rounded-2xl p-4">
        <p className="text-green-300 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'followup') {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-2xl p-4">
        <span className="text-xs text-blue-400 uppercase tracking-wide mb-2 block">Coach</span>
        <p className="text-gray-100 text-sm whitespace-pre-wrap">{text}</p>
      </div>
    )
  }

  if (role === 'pi') {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-4">
        <p className="text-pink-300 text-sm whitespace-pre-wrap font-mono">{text}</p>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="bg-gray-700 rounded-2xl p-4">
        <p className="text-gray-300 text-sm">{text}</p>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ChatBubble.jsx
git commit -m "feat: add English feedback bubble to ChatBubble"
```

---

## Task 9: Frontend — update Session.jsx (voice input + English feedback + UI translation)

**Files:**
- Modify: `frontend/src/pages/Session.jsx`

- [ ] **Step 1: Replace Session.jsx**

Replace `frontend/src/pages/Session.jsx` with:

```jsx
import { useState, useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import ChatBubble from '../components/ChatBubble'

const API = import.meta.env.VITE_API_URL
const QUESTIONS_PER_SESSION = 3

function useVoiceInput(onTranscript) {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef(null)

  function startListening() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) {
      alert('Speech recognition is not supported in this browser. Please use Chrome.')
      return
    }
    const recognition = new SR()
    recognition.lang = 'en-US'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onresult = (e) => onTranscript(e.results[0][0].transcript)
    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)
    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }

  function stopListening() {
    recognitionRef.current?.stop()
    setListening(false)
  }

  return { listening, startListening, stopListening }
}

export default function Session() {
  const { state: sessionData } = useLocation()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [questionCount, setQuestionCount] = useState(0)
  const [hintsUsed, setHintsUsed] = useState(0)
  const [showHintBtn, setShowHintBtn] = useState(false)
  const [followUpMode, setFollowUpMode] = useState(false)
  const [followUpHistory, setFollowUpHistory] = useState([])
  const [currentFeedback, setCurrentFeedback] = useState('')
  const [currentAnswer, setCurrentAnswer] = useState('')
  const subtopicsRef = useRef(sessionData?.subtopics || [sessionData?.subtopic])
  const subtopicIndexRef = useRef(0)
  const bottomRef = useRef(null)

  const { listening, startListening, stopListening } = useVoiceInput((transcript) => {
    setInput(prev => prev ? prev + ' ' + transcript : transcript)
  })

  useEffect(() => { fetchQuestion() }, [])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function fetchQuestion() {
    setLoading(true)
    setHintsUsed(0)
    setShowHintBtn(false)
    setFollowUpMode(false)
    setFollowUpHistory([])
    setCurrentFeedback('')
    setCurrentAnswer('')

    const subtopics = subtopicsRef.current
    const subtopic = subtopics[subtopicIndexRef.current % subtopics.length]
    subtopicIndexRef.current += 1

    const res = await fetch(
      `${API}/session/question?session_id=${sessionData.session_id}&subtopic=${subtopic}&level=${sessionData.level}`,
      { method: 'POST' }
    )
    const q = await res.json()
    setCurrentQuestion(q)
    setMessages(prev => [...prev, { role: 'question', text: q.question, subtopic: q.subtopic }])
    setShowHintBtn(true)
    setLoading(false)
  }

  async function handleHint() {
    if (hintsUsed >= 3 || loading) return
    const nextHint = hintsUsed + 1
    setLoading(true)

    const res = await fetch(`${API}/session/hint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: currentQuestion.question,
        subtopic: currentQuestion.subtopic,
        hint_number: nextHint,
        previous_answer: input,
      })
    })
    const data = await res.json()
    setHintsUsed(nextHint)
    setMessages(prev => [...prev, { role: 'hint', text: `💡 Hint ${nextHint}/3: ${data.hint}` }])
    setLoading(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!input.trim() || loading) return

    if (followUpMode) {
      await handleFollowUp()
      return
    }

    const userAnswer = input.trim()
    setInput('')
    setShowHintBtn(false)
    setMessages(prev => [...prev, { role: 'user', text: userAnswer }])
    setLoading(true)

    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/session/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
      body: JSON.stringify({
        session_id: sessionData.session_id,
        question: currentQuestion.question,
        question_type: currentQuestion.question_type,
        subtopic: currentQuestion.subtopic,
        user_answer: userAnswer,
        level: sessionData.level,
      })
    })
    const result = await res.json()

    setCurrentFeedback(result.feedback)
    setCurrentAnswer(userAnswer)

    setMessages(prev => [...prev,
      { role: 'feedback', text: result.feedback },
      ...(result.grammar_score != null ? [{ role: 'english', text: result }] : []),
      ...(result.interview_answer ? [{ role: 'interview', text: `🎤 Interview: ${result.interview_answer}` }] : []),
      ...(result.pi_commando ? [{ role: 'pi', text: `🍓 Pi simulation:\n${result.pi_commando}` }] : []),
    ])

    setFollowUpMode(true)
    setLoading(false)
  }

  async function handleFollowUp() {
    const question = input.trim()
    if (!question) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: question }])
    setLoading(true)

    const res = await fetch(`${API}/session/followup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: currentQuestion.question,
        subtopic: currentQuestion.subtopic,
        user_answer: currentAnswer,
        feedback: currentFeedback,
        followup_question: question,
        history: followUpHistory,
      })
    })
    const data = await res.json()

    const newHistory = [
      ...followUpHistory,
      { role: 'user', text: question },
      { role: 'coach', text: data.answer },
    ]
    setFollowUpHistory(newHistory)
    setMessages(prev => [...prev, { role: 'followup', text: data.answer }])
    setLoading(false)
  }

  function handleNextQuestion() {
    const newCount = questionCount + 1
    setQuestionCount(newCount)
    if (newCount >= QUESTIONS_PER_SESSION) {
      navigate('/results', { state: { sessionData } })
    } else {
      fetchQuestion()
    }
  }

  const levelLabel = sessionData?.level === 'gemiddeld' ? 'Intermediate' : 'Foundation'

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col max-w-2xl mx-auto">
      <div className="p-4 border-b border-gray-800 flex justify-between items-center">
        <div>
          <h2 className="text-white font-semibold">
            {sessionData?.topic} — {currentQuestion?.subtopic?.replace(/_/g, ' ') || sessionData?.subtopic?.replace(/_/g, ' ')}
          </h2>
          <p className="text-gray-400 text-xs">{levelLabel} · {questionCount}/{QUESTIONS_PER_SESSION} questions</p>
        </div>
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white text-sm">Stop</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => <ChatBubble key={i} role={m.role} text={m.text} subtopic={m.subtopic} />)}
        {loading && <ChatBubble role="system" text="..." />}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-gray-800">
        {followUpMode ? (
          <div className="px-4 pt-3 pb-1 flex items-center justify-between">
            <p className="text-gray-500 text-xs">💬 Ask follow-up questions about this topic</p>
            <button
              onClick={handleNextQuestion}
              disabled={loading}
              className="text-blue-400 hover:text-blue-300 text-sm font-medium disabled:opacity-50"
            >
              Next question →
            </button>
          </div>
        ) : (
          showHintBtn && hintsUsed < 3 && (
            <div className="px-4 pt-3">
              <button
                onClick={handleHint}
                disabled={loading}
                className="text-yellow-400 hover:text-yellow-300 text-sm disabled:opacity-50"
              >
                💡 Hint {hintsUsed + 1}/3 — I need a nudge
              </button>
            </div>
          )
        )}
        <form onSubmit={handleSubmit} className="p-4 flex gap-3">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSubmit(e)}
            placeholder={followUpMode ? 'Ask a follow-up question...' : 'Type your answer... (Shift+Enter for new line)'}
            rows={3}
            disabled={loading}
            className="flex-1 bg-gray-800 text-white p-3 rounded-xl resize-none text-sm disabled:opacity-50"
          />
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={listening ? stopListening : startListening}
              disabled={loading}
              title={listening ? 'Stop recording' : 'Speak your answer'}
              className={`p-3 rounded-xl text-white disabled:opacity-50 ${
                listening ? 'bg-red-600 hover:bg-red-700 animate-pulse' : 'bg-gray-700 hover:bg-gray-600'
              }`}
            >
              {listening ? '⏹' : '🎤'}
            </button>
            <button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white px-5 rounded-xl disabled:opacity-50 flex-1">
              {followUpMode ? 'Ask' : 'Send'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Session.jsx
git commit -m "feat: add voice input and English feedback block to Session"
```

---

## Task 10: Frontend — create Coach.jsx

**Files:**
- Create: `frontend/src/pages/Coach.jsx`

- [ ] **Step 1: Create frontend/src/pages/Coach.jsx**

```jsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const API = import.meta.env.VITE_API_URL

const CATEGORY_COLORS = {
  Grammar: '#818cf8',
  Vocabulary: '#34d399',
  Structure: '#fb923c',
  Fluency: '#f472b6',
}

export default function Coach() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => { load() }, [])

  async function load() {
    const { data: { session } } = await supabase.auth.getSession()
    const res = await fetch(`${API}/coach/`, {
      headers: { Authorization: `Bearer ${session.access_token}` }
    })
    setData(await res.json())
    setLoading(false)
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <p className="text-gray-400">Loading...</p>
    </div>
  )

  const trendData = (data?.trends || []).map((t, i) => ({
    session: `S${i + 1}`,
    Grammar: t.grammar_avg,
    Vocabulary: t.vocabulary_avg,
    Structure: t.structure_avg,
    Fluency: t.fluency_avg,
  }))

  const weakest = data?.weakest_category
  const weakestLabel = weakest ? weakest.charAt(0).toUpperCase() + weakest.slice(1) : null

  return (
    <div className="min-h-screen bg-gray-950 p-6 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-white text-2xl font-bold">English Coach</h1>
          <p className="text-gray-400 text-sm">Your language progress over time</p>
        </div>
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white text-sm">
          ← Dashboard
        </button>
      </div>

      {trendData.length < 2 ? (
        <div className="bg-gray-900 rounded-xl p-6 mb-6 text-center">
          <p className="text-gray-400">Complete at least 2 sessions to see your trend lines.</p>
        </div>
      ) : (
        <div className="bg-gray-900 rounded-xl p-4 mb-6">
          <h2 className="text-white font-semibold mb-4">Score trends</h2>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trendData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <XAxis dataKey="session" stroke="#6b7280" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 10]} stroke="#6b7280" tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                labelStyle={{ color: '#d1d5db' }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {Object.entries(CATEGORY_COLORS).map(([key, color]) => (
                <Line key={key} type="monotone" dataKey={key} stroke={color} strokeWidth={2} dot={{ r: 3 }} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {weakestLabel && (
        <div className="bg-indigo-900/20 border border-indigo-700/50 rounded-xl p-4 mb-6">
          <p className="text-indigo-300 font-medium mb-1">
            Focus area: <span style={{ color: CATEGORY_COLORS[weakestLabel] }}>{weakestLabel}</span>
          </p>
          <p className="text-gray-300 text-sm">{data.recommendation}</p>
        </div>
      )}

      {(data?.recent_answers || []).length === 0 ? (
        <div className="bg-gray-900 rounded-xl p-6 text-center">
          <p className="text-gray-400">No English answers recorded yet. Complete a session to get started.</p>
        </div>
      ) : (
        <div>
          <h2 className="text-white font-semibold mb-3">Recent answers</h2>
          <div className="space-y-3">
            {(data.recent_answers || []).map((a) => (
              <div key={a.id} className="bg-gray-900 rounded-xl p-4 space-y-2">
                <p className="text-gray-400 text-xs uppercase tracking-wide">
                  {new Date(a.created_at).toLocaleDateString('en-GB')}
                </p>
                <p className="text-gray-300 text-sm font-medium">{a.question}</p>
                <p className="text-gray-500 text-xs italic">"{a.user_answer}"</p>
                <div className="flex gap-3">
                  {[
                    { label: 'Grammar', score: a.grammar_score },
                    { label: 'Vocab', score: a.vocabulary_score },
                    { label: 'Structure', score: a.structure_score },
                    { label: 'Fluency', score: a.fluency_score },
                  ].map(({ label, score }) => (
                    <span key={label} className={`text-xs px-2 py-1 rounded-full ${
                      score >= 7 ? 'bg-green-900/40 text-green-300' :
                      score >= 5 ? 'bg-yellow-900/40 text-yellow-300' :
                      'bg-red-900/40 text-red-300'
                    }`}>
                      {label} {score ?? '–'}
                    </span>
                  ))}
                </div>
                {a.english_tips && (
                  <p className="text-indigo-300 text-xs">💡 {a.english_tips}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/Coach.jsx
git commit -m "feat: create English Coach dashboard with trend charts and recent answers"
```

---

## Task 11: Frontend — register /coach route in App.jsx

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Add Coach import and route**

In `frontend/src/App.jsx`, add the import:

```jsx
import Coach from './pages/Coach'
```

And add the route inside `<Routes>`:

```jsx
<Route path="/coach" element={session ? <Coach /> : <Navigate to="/login" />} />
```

The full updated file:

```jsx
import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { supabase } from './lib/supabase'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Session from './pages/Session'
import Results from './pages/Results'
import Coach from './pages/Coach'

export default function App() {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setLoading(false)
    })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })
    return () => subscription.unsubscribe()
  }, [])

  if (loading) return <div className="min-h-screen bg-gray-950" />

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={!session ? <Login /> : <Navigate to="/" />} />
        <Route path="/" element={session ? <Dashboard /> : <Navigate to="/login" />} />
        <Route path="/session" element={session ? <Session /> : <Navigate to="/login" />} />
        <Route path="/results" element={session ? <Results /> : <Navigate to="/login" />} />
        <Route path="/coach" element={session ? <Coach /> : <Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 2: Smoke test the full app**

Start both backend and frontend:

```bash
# Terminal 1 — backend
cd tre-coach/backend
uvicorn main:app --reload

# Terminal 2 — frontend
cd tre-coach/frontend
npm run dev
```

Open `http://localhost:5173` and verify:
1. Dashboard loads in English with "English Coach" link
2. Starting a session shows English questions
3. Submitting a typed answer shows Technical Feedback + English Feedback bubbles (indigo)
4. The 🎤 button appears next to the text area; clicking it in Chrome starts listening
5. After completing 3 questions, Results page is in English
6. Navigating to `/coach` shows the coach page (empty state if no English answers yet, or trends if answers exist)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: register /coach route in App"
```
