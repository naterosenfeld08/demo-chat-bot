<!-- Course: Stage 1. Revise it whenever your thinking changes. A proposal that
     still says what you believed in September is not evidence of learning.
     See docs/course/DELIVERABLES.md -->

# Project proposal

**Project name:** PETase Run Analyst
**Author:** Nate Rosenfeld
**Last updated:** 2026-10-03

---

## 1. The problem

I maintain a protein thermostability pipeline at
[petase-thermostability-benchmark](https://github.com/naterosenfeld08/petase-thermostability-benchmark).
It predicts ΔΔG from protein language model embeddings, and it runs an in-silico
design loop over IsPETase-like variants that scores each one with a physics
composite and, optionally, a predicted structure.

Every run of that loop writes a `log.jsonl` with one JSON record per variant, a
`run_summary.json` next to it, and — for the structural benchmark — a
`benchmark_results.csv` and `benchmark_summary.json`. Those files are the actual
scientific output of the project. They are also where the project's results go
to die.

The problem is not that the data is missing. It is that **asking a question of
it costs more than the answer is worth**, so the questions stop getting asked.

Here is the loop I actually run. I finish a 50-cycle design run. I want to know
whether the adaptive generator policy produced better top variants than plain
random mutagenesis, or whether the difference is just the seed. There is no way
to ask that. So I open a Python REPL, write ten lines of pandas to read the
JSONL, group by `generator_policy`, and take the max `physics.composite` per
group. I get two numbers. I eyeball them, decide they look close, and move on.
The ten lines get closed with the terminal window. The reasoning exists nowhere.

Three weeks later I need the same comparison for a different pair of runs and I
write the same ten lines again, slightly differently, and I cannot tell whether
this month's number disagrees with last month's because the pipeline changed or
because I grouped differently.

This has already cost me something concrete. The figures in
`expo_presentation/03_figure_pack/` are generated from a `figure_data.json` that
I populated by hand from runs I can no longer identify. When a mentor asks
"which run is the 54.76% GDT-TS from," I can answer only because I happened to
paste the job ID into a notes file. There are a dozen other numbers in that
presentation for which I could not do the same.

There is a second, worse failure. My own
[`docs/LIMITATIONS_AND_PRIORS.md`](https://github.com/naterosenfeld08/petase-thermostability-benchmark/blob/main/docs/LIMITATIONS_AND_PRIORS.md)
documents that the ΔΔG head is a **generic FireProt-scale prior**, trained on
single substitutions across many unrelated proteins, and is *not* a PETase-specific
predictor of Tm or activity. It also documents that the Random Forest's
inter-tree variance is **model disagreement, not experimental error**. I wrote
those caveats down because I had already caught myself forgetting them. A raw
number in a terminal carries none of that context. The moment a composite score
of 0.87 gets copied into a slide, it starts looking like a measurement.

So: the results are structured, the questions are answerable, and the caveats
are already written. What is missing is anything that connects the three.

## 2. Who uses this

**Primary user:** Me. I am the person with ~90 tracked files of pipeline code, a
growing pile of run directories, and no way to interrogate my own output without
writing throwaway scripts.

That is a legitimate user and a convenient one, because I can answer my own
questions about what the tool should do without guessing. But I am not unusual.
Anyone running an iterative in-silico design loop — protein, molecule, or
materials — ends up with the same shape of problem: a directory of structured
run logs, a handful of metrics that matter, and a set of interpretation caveats
that live in a README nobody rereads. What I share with them is the specific
failure of writing the same analysis script repeatedly and losing the reasoning
each time.

**What they do today instead:** Ad-hoc pandas in a REPL, or scrolling
`run_summary.json` in an editor. For the Streamlit GUI already in the PETase
repo, clicking through the JSONL Run Browser tab, which shows sortable tables
but cannot answer a comparative question or carry a caveat.

**Why they'd switch:** Because the cost of asking drops to typing a sentence,
and because the answer arrives with its provenance (which file, which field) and
its caveat attached, so it is safe to paste into an email.

## 3. Tools and services

| What | Choice | Why this one |
|---|---|---|
| Track | Web app (server-side) | The TensorX API key must never reach the browser, and a server is the only way to keep it secret. |
| Language / framework | Python 3 with Flask | The pipeline whose artifacts this reads is already Python, so the parsing code can be shared rather than reimplemented. |
| Where it's hosted | Render | Class default, free tier, and it already runs this app's `gunicorn` start command. |
| Data storage | Neon (Postgres) | Question history has to survive a page reload (backlog #10), which rules out in-memory session state. |
| Outside services (APIs) | [TensorX](https://api.tensorx.ai/v1) chat completions | Already wired into `app.py`, and an OpenAI-compatible endpoint means swapping providers later is a URL change. |
| Testing | `pytest` plus `pytest-playwright` | Class default; Playwright drives a real browser so the upload flow is tested the way a user hits it. |

**A note on Flask vs FastAPI.** `docs/course/tracks.md` describes the web-app
track as FastAPI on uvicorn with `main.py` as the entry point. This project uses
Flask with `app.py`, because the working chat app it builds on was already Flask.
Both satisfy everything the track requires — one command to run the app, one
command to run the tests, tests that fail out loud, and a URL a peer can try —
and the choice is recorded in `AGENTS.md` section 5. Confirming the deviation
with the instructor is still open; the app meets the track's runnable-app
requirements either way.

### The one design decision everything else follows from

**The server computes every number in Python. The language model never does
arithmetic.**

When I ask a question, the Flask server parses the run artifacts and computes a
compact block of statistics deterministically. The model receives that block as
context, and its only two jobs are choosing which statistic answers my question
and explaining it in prose with the right caveat attached.

I am making this choice for two reasons. The scientific one: floating-point
aggregation over thousands of JSONL records is precisely what language models
are worst at, and a plausible-looking wrong mean is more dangerous than no
answer. The practical one, which matters for this course: it makes the
acceptance criteria verifiable. I can assert an exact float against `pandas`,
and test the model layer for routing and refusal rather than for math. Backlog
item #3 encodes this directly as a test — stubbing out the AI service entirely
must still produce the correct number in the stub's input.

## 4. Development timeline

Each numbered feature is a backlog item from [`backlog.md`](backlog.md) and gets
its own pull request through the full routine in
[`docs/course/routine.md`](course/routine.md).

| Week | Dates | Features | Milestone |
|---|---|---|---|
| 1 | Oct 6–12 | #1 load a run and see what was recognized | First full routine end to end |
| 2 | Oct 13–19 | #2 run summary card | |
| 3 | Oct 20–26 | #3 ask a question, get a computed answer | The core of the app works |
| 4 | Oct 27–30 | Write `docs/dev-log.md`; tidy PR evidence | **Stage 2 due 10/30** (needs 2 features; will have 3) |
| 5 | Nov 3–9 | #4 caveats travel with the numbers, #5 compare two runs | |
| 6 | Nov 10–16 | #6 objective drift chart, #7 top variants table | |
| 7 | Nov 17–20 | #12 deploy to Render; rewrite README; three classmates test it | **Stage 3 due 11/20**, `CHANGELOG.md` 0.1.0 alpha |
| 8 | Nov 24–30 | Feedback fixes from `docs/feedback-log.md`, then #8 multi-seed stability | Revised acceptance criteria and changed tests |
| 9 | Dec 1–7 | #9 export a mentor-ready summary, #10 question history | |
| 10 | Dec 8–16 | #11 repo structure audit if time allows; `docs/final-report.md`; rehearse the sabotage round | **Stage 4 due 12/16** |

Weeks 1–3 are deliberately one feature each. The routine has eight steps and a
mandatory stop where I have to understand the tests before any code gets
written, and I would rather discover how long that actually takes on feature #1
than on feature #6. Week 8 is reserved for acting on feedback rather than for
new features, because Stage 4 puts 40% of its grade on the chain from a user
comment through a revised acceptance criterion to a changed test.

Items #8 through #11 are the ones I will drop first if the schedule slips. #11
is a stretch goal and is written that way in the backlog.
