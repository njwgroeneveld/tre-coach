# TRE Coach — Learning Ladder Design

**Date:** 2026-10-09
**Goal:** Learn to read Linux performance and network output in small pieces, climbing step by step
to the investigation mode that already exists: there the trainee picks every command; on the ladder
they first learn what each command shows and what to conclude from it.

Sources the content follows:
- Netflix, *Linux Performance Analysis in 60,000 Milliseconds* — the ten commands and how to read them.
- Brendan Gregg, *The USE Method* and its Linux checklist — for every resource, check
  Utilization, Saturation and Errors.

The scenarios use trading hosts (order gateway, market-data handler, exchange sessions), because
that is where the trainee wants to work.

---

## The ladder

Each step is a set of short drills. A drill asks one question, often about a piece of output; the
trainee answers in a sentence or two and gets feedback at once.

Nothing is asked before it is taught:
- **Learn before practise.** Every command lesson opens with an explanation card that
  covers every column the drills use: what it measures, what is normal, what is alarming, what to
  run next. Drills only ask about what the card explains.
- **Unlocking follows what was learnt.** A lesson unlocks after 4 of the last 5 drills of the lesson
  before it are correct. Step 4 for a resource unlocks once the lessons for its commands are done
  (CPU: `uptime`, `vmstat`, `mpstat`, `pidstat`; storage: `vmstat`, `iostat`; and so on). Step 5
  unlocks only after all lessons.
- **Answers stay within what was taught.** Expected answers and "next command" suggestions use only
  commands from lessons the trainee has finished; a correct answer never needs a command they have
  not met.
- **The cards stay available.** A "Reference" panel with all finished cards is open during steps 4,
  5 and 6, the way an engineer would check a man page.

The trainee's six steps (agreed 2026-10-09). Steps 1–3 are done per command; steps 4–6 build on
all of them.

| Step | Name | What the trainee does | Example question |
|---|---|---|---|
| 1 | **What does it show?** | The purpose of the command: what it reports and when you run it | "What does `vmstat` show you, and when do you run it?" |
| 2 | **The columns** | What each column or field measures, and what an alarming value tells you | "What does `sy` measure, and what does a high value tell you?" |
| 3 | **Conclude** | One generated output, one conclusion | "8 CPUs, `vmstat 1` below. CPU, I/O, memory or fine? Which columns tell you, and what do you run next?" |
| 4 | **USE per resource** | Several outputs for one resource; fill in U, S and E and decide: problem or exonerated | "CPU: utilization? saturation? errors? Is the CPU the bottleneck?" |
| 5 | **First 60 seconds** | All ten Netflix outputs of one host at once; find the bottleneck | "Here is the first minute on the order gateway. What is wrong, and what is your evidence?" |
| 6 | **Investigation** | The existing investigation mode: only a symptom, the trainee runs commands | (exists) |

A short **Concepts** set (below) sits before step 1 of the first lesson.

### Concepts

- CPU versus I/O: runnable (R) versus uninterruptible (D); why load includes both.
- Memory: free versus available, page cache, swapping, the OOM killer.
- The USE method: resource, utilization, saturation, errors; why errors and saturation come first.
- Networking basics: TCP versus UDP (handshake, ordering, retransmits); why market data often comes
  over UDP multicast (no retransmit: a lost packet is a gap); TCP states (ESTABLISHED, TIME_WAIT).

### Steps 1–3 — one lesson per command

Every lesson opens with its **card** (see *How drills are made and graded*), then three drill parts
in this order, each mastered at 4 of the last 5 correct before the next opens:
1. **What does it show?** — the purpose: what the command reports, when you run it, and what it
   cannot tell you.
2. **The columns** — what each column or field measures, and what an alarming value tells you.
3. **Conclude** — a generated output and "what do you conclude?". The lesson is done when this
   part is mastered.

Lessons follow the Netflix order, then add the network commands the trading context needs:

| # | Command | Situations the drills cycle through |
|---|---|---|
| 1 | `uptime` | normal · overloaded (CPU or I/O still unknown) · rising · logged in too late |
| 2 | `dmesg \| tail` | quiet · OOM killer · disk I/O errors · TCP dropping requests |
| 3 | `vmstat 1` | normal · CPU saturated (r > CPUs) · I/O wait (b, wa) · swapping (si/so) · high system time · the first line is since boot |
| 4 | `mpstat -P ALL 1` | balanced · one hot CPU (single-threaded) · softirq on one core |
| 5 | `pidstat 1` (and `-d`, `-w`) | which process uses CPU · which writes to disk · context switches |
| 6 | `iostat -xz 1` | idle · busy but healthy · saturated (%util, await, avgqu-sz) · slow device |
| 7 | `free -m` | healthy cache · low available · swap in use |
| 8 | `sar -n DEV 1` | normal · interface at line rate |
| 9 | `sar -n TCP,ETCP 1` | normal · retransmits rising · connection storm |
| 10 | `top` | consistent with the earlier commands · a different picture (variable load) |
| 11 | `ip -s link` | clean · RX dropped / overruns · CRC errors |
| 12 | `ss -ti` | healthy session · retransmits and a large RTO on one connection |
| 13 | `netstat -s` | what retransmits, receive buffer errors and pruned packets mean |

### Step 4 — USE per resource

Resources from Gregg's Linux checklist, limited to what the commands above show: CPU, memory
capacity, storage device I/O, network interface, file descriptors.

### Step 5 — First 60 seconds

One host, ten outputs that all agree with one hidden situation, the way the Netflix article walks
through its example.

---

## How drills are made and graded

- **Output is generated in Python, not by Claude.** Each command has a generator that takes a
  situation and a CPU count and produces realistic, internally consistent output with random
  numbers within sensible ranges. Earlier, generated output by Claude (Haiku) contained impossible
  combinations; Python templates cannot. Drills also appear instantly and cost nothing.
- **Grading uses Claude (Haiku 4.5).** It gets the drill's true situation and the key points a
  correct answer contains (which columns, what conclusion, which next command), and returns
  correct / partly correct / wrong with a short explanation.
- Each lesson starts with a **short explanation card**: what the command shows, the columns that
  matter, what is normal and what is alarming, what to run next — following the sources above.

## Storage

Drill results go into `answers` with `question_type = 'drill'` and a subtopic per lesson
(`drill_uptime`, `drill_vmstat`, …), so `topic_scores` already tracks progress per lesson and the
unlock rule can read it. No new table.

## Frontend

A new **Learn** page reached from the dashboard: the ladder as a list of steps and lessons, with a
lock on what is not yet unlocked. A lesson shows its card, then drills one at a time.

---

## Decisions

- Everything is in English, the explanation cards included (decided 2026-10-09): it matches the
  rest of the app and trains interview English.

## Not in scope

- Steps 4 and 5 until a few lessons exist.
- Kubernetes drills (`kubectl top`, `describe` for OOMKilled, throttling) — a later lesson set.

---

## Build order

1. Drill engine, the `uptime` lesson (card, generator, grading) and a minimal Learn page.
2. `vmstat 1`.
3. The remaining Netflix commands, one per step.
4. Concepts, including TCP/UDP.
5. Network lessons 11–13.
6. Step 4 (USE per resource), then step 5 (first 60 seconds).
