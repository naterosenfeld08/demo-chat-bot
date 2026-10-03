<!-- Course: first required in Stage 1, graded again in Stage 2. Revised whenever
     you learn a rule the hard way. See docs/course/DELIVERABLES.md -->

# AGENTS.md

Rules for any AI assistant working in this repository. Read this file before
doing anything else. If a request conflicts with a rule below, stop and say so
rather than guessing.

---

## 1. What this project is

<!-- Fill this in. Two or three sentences. An assistant that knows what the app
     is for makes better guesses about everything you forgot to specify. -->

**Purpose:** A web app for interrogating the run artifacts produced by
[petase-thermostability-benchmark](https://github.com/naterosenfeld08/petase-thermostability-benchmark),
a protein thermostability pipeline. You upload a design run's `log.jsonl` and
`run_summary.json`, then ask questions in plain English; the server computes the
statistics and an AI model explains them with the project's interpretation
caveats attached. It replaces the throwaway pandas scripts that currently get
written, read once, and lost.

**Who uses it:** Primarily its author, a student maintaining that pipeline, who
has a growing pile of run directories and no way to ask comparative questions of
them. Secondarily anyone running an iterative in-silico design loop that emits
the same shape of structured run logs.

**What kind of app:** Server-side web app. A Python Flask server renders the
pages and makes every outside API call, so the API key stays off the browser.
See `docs/course/tracks.md`.

---

## 2. Rules that do not change

These are course requirements. Do not edit this section.

1. **Tests before code.** Write the automatic tests for a feature before
   writing any code that implements it. At that point every new test must fail.
   A test that passes before the feature exists proves nothing.

2. **Never modify an existing test to make it pass.** If you believe a test is
   wrong, say so out loud in the pull request and wait. Quietly editing a test
   so your code passes is the single most serious failure possible here.

3. **Stop and explain, then wait.** After writing the tests and before writing
   any implementation, describe each test to the human in plain English: what
   it tries, and why it matters. Use no code in these descriptions. Then stop.
   Do not write implementation code until the human replies `approved`.

4. **One feature at a time.** A pull request should cover one item from
   `docs/backlog.md` and be readable in one sitting. If a change is growing past
   that, stop and propose splitting it.

5. **Never write a secret into a file.** No API keys, tokens, or passwords in
   source, tests, config, or commit messages; not even fake-looking ones, not
   even temporarily. Secrets go in `.env`, which is git-ignored. If you need a
   key that doesn't exist yet, stop and ask.

6. **A static site cannot keep a secret.** If this project deploys as static
   files, there is no server, so any key in the page is public to every visitor.
   Never add one. Use a keyless API, or have the user supply their own key at
   runtime. See `docs/deploying.md`.

7. **Say when you are unsure.** "I don't know" and "this could go two ways" are
   correct answers. Confident invention is not.

---

## 3. How work happens here

The full routine is in [docs/course/routine.md](docs/course/routine.md). Short version:

```
backlog item  →  feature spec  →  question round  →  failing tests
              →  STOP: explain tests, wait for "approved"
              →  build until tests pass  →  review  →  reply to every comment  →  merge
```

Which role you are will be stated when you're asked to work. If it wasn't
stated, ask before starting. The roles have different rules.

| Role | Does | Must not |
|---|---|---|
| **Spec writer** | Expands a backlog item into `specs/NN-name.md` | Write code |
| **Questioner** | Finds what the spec forgot; max 10 questions, most important first | Answer its own questions, or write code |
| **Test writer** | Writes failing tests in `tests/`, then explains them in plain English and stops | Write implementation code |
| **Builder** | Writes code until tests pass | Touch any existing test |
| **Reviewer** | One concern only; max 5 comments, ranked most important first | Fix things itself |

---

## 4. Project rules

<!-- Mine. A rule gets added here every time an assistant does something I
     didn't want, so the same mistake cannot happen twice. -->

1. **The server computes every number. The model never does arithmetic.** Any
   statistic shown to the user is produced by Python in this repo and passed to
   the model as context. If a feature seems to need the model to add, average,
   compare, or rank, that is a signal the server is missing a function — write
   the function. See `docs/proposal.md` section 3 for why.

2. **Every number names its source.** A displayed value carries the artifact and
   field it came from, like "`run_summary.json` → `counts.n_variants`". A number
   with no provenance is not shippable.

3. **Never present a proxy as a measurement.** The physics composite, the ΔΔG
   output, and the Random Forest interval are proxies. They are not Tm, not
   activity, and not experimental error. Do not convert between them, do not
   phrase one as the other, and refuse requests that ask for the conversion.

4. **Caveats are data, not prose.** Interpretation caveats live in a file that is
   read at request time. Never hardcode caveat text into a prompt string or a
   template, because the whole point is that editing the file changes the output.

5. **Missing is not zero.** A field absent from an artifact displays "not
   recorded". Never `0`, never `null`, never an empty cell. Silently defaulting a
   missing metric to zero is how a run looks worse than it was.

6. **Parse defensively; real logs are messy.** Run logs are appended during long
   jobs and get truncated, interleaved, and half-written. A malformed line means
   skip it and report the count, never crash and never discard the whole file.

7. **This repo never writes to the pipeline repo.** `petase-thermostability-benchmark`
   is read-only input. Do not propose edits to it, do not import from it, and do
   not shell out to its scripts.

8. **Do not add a dependency without asking.** `requirements.txt` is already the
   thing a classmate has to install successfully in Stage 3. Prefer the standard
   library and what's already listed.

9. **Say when a number looks wrong.** If a computed statistic disagrees with what
   the artifact's own summary claims, surface the disagreement rather than picking
   a winner. A mismatch is a finding, not a bug to paper over.

---

## 5. Conventions

<!-- How this repo is laid out and named. Fill in as you go. -->

- **Source code:** `app.py` is the Flask entry point. Server modules go in `src/`.
- **Pages:** `templates/` (Jinja templates). Styles and scripts go in `static/`.
- **Tests:** `tests/`, one file per feature, named for the spec it tests
- **Feature specs:** `specs/NN-name.md`, numbered to match `docs/backlog.md`
- **Data files:** `data/`
- **Branches:** `feature/NN-short-name`
- **Commits:** present tense, one line, says what changed and why
- **Language / framework:** Python 3 with Flask; Jinja templates, plain CSS and
  JavaScript for the pages. Deployed on Render with `gunicorn`.
- **Run the app:** `source .venv/bin/activate && python app.py`, then open
  <http://127.0.0.1:5000>. Use `PORT=5050 python app.py` if 5000 is taken.
- **Run the tests:** `pytest`
