# TRE Coach — Investigation Mode Design

**Date:** 2026-10-07
**Goal:** Practise troubleshooting the way a trading-firm interviewer runs it: a vague symptom, a hidden root
cause, and the trainee gathers evidence command by command until they can name the cause.

---

## Why

Scenario questions give a symptom and ask "how would you investigate?". A symptom fits several root
causes, so the trainee has to describe an approach in the abstract and never reads real output. Since
2026-10-07 scenario answers are graded on approach (hypotheses, elimination, order, trading impact),
which makes them fair — but reading output and ruling causes out is the actual skill, and the
60-second checklist (Brendan Gregg) is only learnt by doing it.

Investigation mode adds that: the coach plays the host.

---

## Session Flow

1. The trainee gets an investigation in the Performance topic (see *Where it appears*).
2. The coach shows only the symptom, as a trader or alert reports it.
3. The trainee types a command (`vmstat 1`) or an action (`check the GC log`).
4. The coach answers with realistic output that is consistent with the hidden cause — including for
   commands that lead nowhere. Output rules out wrong hypotheses; it never says what the cause is.
5. Repeat, up to **10 steps**.
6. The trainee presses **Diagnose** and states cause + fix.
   - **Correct** → evaluation (see *Scoring*), the investigation is closed.
   - **Wrong, attempt 1** → a realistic consequence ("you restart the bot, traders lose 40 s of
     quoting; 23 minutes later it freezes again") and the trainee continues.
   - **Wrong, attempt 2** → the cause is revealed with the fastest path and where the trainee went
     off track, then evaluation.
7. After evaluation the existing follow-up chat works as for other questions.

Destructive actions (`kill -9`, `reboot`, `systemctl restart`) are allowed and produce consequences;
they count as *risky actions* in the score.

Hints: the existing hint button (1–3) works, but through a new endpoint, because a useful hint needs
the hidden cause.

---

## Example

```text
COACH:  The bot freezes for a few seconds, a few times per hour.
TRAINEE: vmstat 1 during a freeze
COACH:   r  b  us sy id wa
         1  0  12  3 84  1
         0  6   4  2 21 73
TRAINEE: iostat -xz 1
COACH:  Device  r/s   w/s   await  %util
        sda     2.0   890   412.3  100.0
TRAINEE: pidstat -d 1
COACH:  PID   kB_wr/s  Command
        4412  98312    gzip
TRAINEE: [Diagnose] logrotate compresses on the bot's disk → move logs / ionice the job
COACH:  ✅ Correct in 3 steps. …
```

---

## Architecture

### Where it appears

Only in the **performance** topic at first. Question type split for that topic:
investigation 50%, scenario 30%, command 20%. Other topics keep 70% scenario / 30% command.
Extending to `linux`, `netwerk` and `kubernetes` is a later step.

### Database

New table `investigations`:

| column | type | meaning |
|---|---|---|
| `id` | uuid pk | |
| `session_id` | uuid → sessions | |
| `subtopic`, `level` | text | as for questions |
| `symptom` | text | shown to the trainee |
| `hidden` | jsonb | `{cause, facts, fix, fastest_path}` — **never sent to the frontend** |
| `steps` | jsonb | `[{input, output}]` |
| `wrong_diagnoses` | int | 0–2 |
| `risky_actions` | int | |
| `status` | text | `open` / `solved` / `revealed` |
| `created_at` | timestamptz | |

RLS is enabled with **no policy**: only the backend (service role key) can read the table. The
frontend uses the anon key, so without a policy the trainee cannot read `hidden` through Supabase.
The final result is also written to `answers` (`question_type = 'investigation'`) so dashboard,
weak-subtopic logic and the English coach keep working unchanged.

### Backend

New router `routers/investigation.py`:

- `POST /investigation/start {session_id, subtopic, level}` → `{investigation_id, symptom}`.
  One Claude call generates symptom + hidden cause + a set of concrete *facts* (process names,
  device, numbers) that all later output must agree with.
- `POST /investigation/step {investigation_id, input}` → `{output, steps_left}`.
  Claude plays the host. The prompt gets the hidden facts and **all previous steps**, so output
  stays consistent. Rules: raw output only, max ~25 lines, never name the cause, never comment.
- `POST /investigation/diagnose {investigation_id, diagnosis}` →
  `{correct, consequence?, revealed?, evaluation?}`. One Claude call judges correctness against
  `hidden.cause`; on correct or on the second wrong attempt it runs the evaluation and saves to
  `answers`.
- `POST /investigation/hint {investigation_id, hint_number}` → `{hint}`.

The `hidden` field is read only inside these endpoints and never appears in a response until the
cause is revealed.

### Frontend

`Session.jsx`, when `question_type === 'investigation'`:

- The input field becomes a command prompt (`$`), outputs render in a monospace terminal bubble.
- A **Diagnose** button opens a text field for cause + fix.
- A small status line: `step 3/10 · attempt 1/2`.
- The subtopic label is hidden until the investigation closes (it would give the cause away).

---

## Scoring

Evaluation (0–10) weighs:

- **Cause** — correct, and at which attempt.
- **Efficiency** — steps used versus the fastest path.
- **Order** — broad and cheap first (the 60 s checklist), then narrow.
- **Reasoning** — did the trainee's notes between commands interpret the output?
- **Trading impact** — mitigation before root cause; risky actions lower the score.

The English scores and tip are produced as for other answers, over the trainee's text inputs.

---

## Token Cost

Per investigation roughly: 1 call to start, 1 per step (≤ 10), 1–2 to diagnose and evaluate.
Same model as the rest of the app (`claude-sonnet-4-6`). Step prompts grow with history; at 10
steps of ≤ 25 lines this stays well below 10k input tokens per call.

---

## Risks

- **Inconsistent output** across steps (e.g. `top` shows 4 cores, `mpstat` 8). Mitigated by fixed
  facts generated at start plus full history in every step prompt.
- **Leaking the cause** in output ("note: logrotate is running"). Mitigated by the raw-output rule;
  verify while building with a few runs per subtopic.
- **Existing auth weakness, not introduced here:** `get_user_id` decodes the JWT without verifying
  its signature, and `/session/question` and `/session/answer` take no auth. The new endpoints follow
  the existing pattern; fixing auth is a separate piece of work.

---

## What Is Not In Scope

- Investigation mode in topics other than `performance`. Starting points for the `trading` topic,
  noted 2026-10-07 because they are typical for trading hosts but not performance problems: clock
  drift (PTP/NTP) breaking timestamps and latency measurement, a FIX session out of sequence after a
  restart, and exchange rate limits rejecting orders while the host is healthy.
- Running real commands on a real host (the Pi simulation stays a separate suggestion).
- Voice input for commands.
- Fixing the JWT verification.

---

## Build Order

Each step is small enough to build and explain on its own:

1. Table `investigations` + RLS (`supabase/schema.sql`).
2. `/investigation/start`: generate symptom + hidden facts; check a few by hand.
3. `/investigation/step`: the host simulation; test consistency over 5–6 commands.
4. `/investigation/diagnose`: judge, consequence, reveal, evaluation, save to `answers`.
5. Frontend: terminal bubbles and command input.
6. Frontend: Diagnose button, status line, hidden subtopic label.
7. `/investigation/hint` and the 50/30/20 question split for `performance`.
