<!-- Course: Stage 2 (graded) and Stage 4 (feeds your final report). Several of
     the Friday lab milestones get recorded here. See docs/course/DELIVERABLES.md -->

# Development log

A running record of how this project got built and how AI was used to build it.

---

## Entries

### 2026-10-03 - Feature 03 shipped: ask a computed question

**What happened:** After a usable run is loaded, typed questions go to
`POST /api/ask`. The server classifies a small set of intents, writes the
answer, and (in `LLM_MODE=echo`) echoes the same stats block a live model
would see. Seed-42's best composite answers as `0.609` for `gen00002`.
**AI tools used, and for what:** Cursor (Claude / Grok) wrote the spec, seven
failing tests, the implementation, and merged PR #3. No second-model question
round or review, same thinner process as feature 02.
**What surprised me:** The page composer still talked to `/api/chat` until this
feature. Leaving that in place would have looked like the product worked while
every number came from the model. Switching the form to `/api/ask` was the
thing that made the rule visible.

### 2026-10-03 - Feature 02 shipped: the run summary card

**What happened:** After a run is loaded, four headline numbers appear without a
typed question. A recorded `n_with_structure: 0` displays as `0`, which is the
common CLI case (ColabFold off). Missing fields display `not recorded`.
**AI tools used, and for what:** Cursor (Claude) wrote the spec, 17 failing
tests, then the `GET /api/summary` implementation. The question round was
folded into the spec from `AGENTS.md` and the fixtures instead of a second
model, to keep the feature in one sitting.
**What surprised me:** The sample summary already stores a written zero for
structures. Treating zero as missing would have made every real CLI run look
like the pipeline forgot a field.

### 2026-10-03 - Feature 01 shipped: load a run

**What happened:** Upload recognizes design logs, run summaries, and benchmark
files by content signature. The page lists what was understood or why a file
was refused. Two sessions cannot see each other.
**AI tools used, and for what:** Cursor (Claude) drafted the spec; GPT-5.6 Sol
ran the question round (10 questions) and later the code review; Claude
implemented against 49 tests written first. Fixtures came from a real
`petase_design.run` (8 cycles, seeds 42 and 43) plus the pipeline's own CSV
writer over committed benchmark metrics.
**What surprised me:** Three things I would not have caught from the backlog
alone. (1) `job_id` cannot identify a design log — benchmark rows carry it too.
(2) Question 6 found the spec contradicting `AGENTS.md` rule 9: deferring
same-run checks would have hidden a count mismatch. (3) A code review caught
the page replacing the whole list with the last request's accepted files, so a
second upload or a reload hid the loaded run.

### 2026-10-03 - Course template merged into the chat demo

**What happened:** `naterosenfeld08/demo-chat-bot` was a Flask + TensorX demo
with none of the course files. The template has unrelated git history, so
`git merge upstream/main` needed `--allow-unrelated-histories`. The repo was
made public. Flask was kept instead of the track's FastAPI example; that
deviation is recorded in the proposal.
**AI tools used, and for what:** Cursor (Claude) fetched
`CSCI-2521/project-template`, resolved the four add/add conflicts, and filled
`docs/proposal.md`, `docs/backlog.md`, and `AGENTS.md` around the PETase
pipeline.
**What surprised me:** `gh pr create` first targeted the template remote
because `upstream` looks like a fork parent. `gh repo set-default` was
required before PRs would open on this repo.

---

## How AI was used, in one place

| Role | Model | What it did |
|---|---|---|
| Spec writer / test writer / builder | Claude / Grok (Cursor) | Specs, failing tests, implementation, merges |
| Questioner and reviewer for feature 01 | GPT-5.6 Sol | Ten spec questions; later a two-item code review of the page and the upload size cap |
| Human | Nate | Chose the project (Run Analyst over a notebook or auditor), answered the question round, authorized the `second_payload` typo fix, approved tests, merged |

The standing rule that mattered most: **the server computes every number; the
model never does arithmetic.** Feature 02 is entirely Python. Feature 03 passes
a precomputed stats block as context and proves that with an echo stub.

Process that is thinner than the routine describes: features 02 and 03 did not
get a second-model question round or code review. That is recorded here so
Stage 4 does not invent a fuller process than happened.
