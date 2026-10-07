# TRE Coach — English Mode Design

**Date:** 2026-04-22
**Goal:** Convert the existing Dutch TRE Coach app fully to English, add optional voice input, and add an English coaching dashboard to help Niels improve his technical English for a trading-firm interview.

---

## Overview

The existing app (Dutch questions, Dutch answers, typed input) is converted entirely to English. No Dutch mode remains. A microphone button is added as an optional input method alongside the existing text field. An AI English coach analyzes every answer and tracks progress over time on a new `/coach` page.

---

## Architecture

### What changes

**Frontend:**
- All UI text translated to English
- `Session.jsx` — English questions, optional microphone button next to text field, English feedback block added
- `Dashboard.jsx` — UI translated to English
- New page `/coach` — English coaching dashboard

**Backend:**
- All prompts in `claude_service.py` converted from Dutch to English (`generate_question`, `evaluate_answer`, `generate_hint`, `generate_followup`)
- `evaluate_answer()` extended: single Claude call returns both technical feedback and English language analysis
- New route `GET /english/coach` returns aggregated coaching data per user

**Database:**
- Five new columns added to existing `answers` table:
  - `grammar_score INT` — 0-10
  - `vocabulary_score INT` — 0-10
  - `structure_score INT` — 0-10
  - `fluency_score INT` — 0-10
  - `english_tips TEXT` — one concrete actionable tip per answer

---

## Session Flow

1. User starts a session from the dashboard (same flow as now, but in English)
2. English question is shown in the chat
3. User either:
   - Types their answer in the text field, or
   - Presses the microphone button → browser requests permission once → recording starts → button turns red with "Listening..." → recording stops automatically when user stops talking → transcribed text appears in the text field → user can edit before submitting
4. User submits answer
5. Backend receives answer text (same regardless of voice or typed)
6. Claude returns in a single call:
   - Technical feedback (was the answer correct, what was missing)
   - English analysis (grammar, vocabulary, structure, fluency, connectors, register)
7. Two feedback blocks are shown in the chat:
   - Technical block (same as now)
   - English block: scores + one concrete tip (e.g. "You used 'so' 4 times — vary with 'therefore' or 'as a result'")

---

## English Analysis

Claude analyzes each answer on these dimensions, targeting B2 level English:

| Category | What is evaluated |
|---|---|
| Grammar | Verb tenses, sentence construction, subject-verb agreement |
| Vocabulary | Technical term accuracy, word variety, appropriate register |
| Structure | Logical flow, clear reasoning steps, answer completeness |
| Fluency | Sentence variety, filler avoidance, natural phrasing |
| Connectors | Use of linking words (therefore, however, as a result, consequently) |
| Register | Professional/interview-appropriate tone vs. casual |

Each answer gets scores 0-10 per category and one actionable tip. Feedback is on the full answer, not per sentence.

---

## Coach Dashboard (`/coach`)

Shows English progress over time across all sessions.

**Sections:**
- **Trend lines** — one line per category (grammar, vocabulary, structure, fluency) over the last N sessions
- **Current weakest area** — the category with the lowest recent average, highlighted with advice
- **Concrete recommendations** — e.g. "Your structure is improving well, but you use few linking words. Practice: therefore, however, as a result"
- **Recent answers** — scrollable list of past answers with their English tip, so Niels can review what he said

The dashboard is a coaching view, not a report card — it always points to the next concrete improvement step.

---

## Voice Input

- Uses browser Web Speech API (no API key, no cost, works in Chrome)
- Accuracy is sufficient because answers are conversational explanations, not exact command syntax
- Microphone button is optional — user can always type instead
- Transcribed text is editable before submission
- No audio is stored — transcribed text is treated identically to typed text and stored as `user_answer`

---

## Token Cost

Single Claude call per answer handles both technical evaluation and English analysis. Estimated ~100-150 additional output tokens per answer vs. current. Cost impact: ~$0.003 extra per session. Negligible.

---

## What Is Not In Scope

- Per-sentence feedback
- Dutch fallback mode
- Audio storage or playback
- Pronunciation scoring (Web Speech API does not provide this)
- Multi-user comparison or leaderboards
