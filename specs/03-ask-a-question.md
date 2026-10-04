# 03 - Ask a question and get a computed answer

**Story:** As a researcher, I can ask a question in English and get an answer whose numbers came from the artifacts.
**Backlog item:** #3
**Status:** shipped

## What it does

With a usable run loaded, the user types a question. The **server** decides
which statistic answers it, pulls that number from the same functions as the
summary card, and builds a short answer that includes the number and its
source. A language model may be given that precomputed block as context; it
never adds, averages, or ranks.

If nothing usable is loaded, the app says to upload `log.jsonl` or
`run_summary.json` first and returns no statistic.

If the question is about something the loaded artifacts do not record, the
answer is `the loaded run doesn't record that`, names the artifact that would
be needed, and contains no statistic.

## What it does NOT do

- The model does not compute. If a new question needs a new number, write a
  Python function.
- No caveats file yet. That is feature #4. This feature does not refuse Tm
  conversions; #4 will.
- No charts, no two-run compare, no question history (#10).
- No free-form pandas. Only the intents listed below.

## Intents the server recognizes

| Intent | Example question | Number | Source |
|---|---|---|---|
| `n_variants` | how many variants were in this run | Same integer as the summary card | card field `n_variants` |
| `best_composite` | what was the best composite score | Maximum `physics.composite`, **three decimal places**, plus the `job_id` | log `physics.composite` / summary `top_variants[].composite`; `job_id` from the winning row |
| `seconds_wall` | how long did the run take | Card seconds, or unanswerable if not recorded | `runtime.seconds_wall` |
| `unanswerable` | what was the GDT-TS / what Tm will it have | none | names the artifact that would be needed |

Three decimal places means rounded half-up, so the seed-42 best of
`0.6085333333333334` displays as `0.609`. The card (feature #2) still shows
the exact file value.

## HTTP contract

`POST /api/ask` with JSON `{"question": "..."}`. Always `200`.

```json
{
  "answer": "This run has 8 variants (run_summary.json → counts.n_variants).",
  "intent": "n_variants",
  "facts": {"n_variants": 8, "source": "run_summary.json → counts.n_variants"},
  "echo": null
}
```

`app.config["LLM_MODE"]` is `live` or `echo`. In `echo`, `echo` is the JSON
string of the stats block that would have been sent to the model, and that
block contains every computed fact. Tests set `LLM_MODE` to `echo`.

Unanswerable: `facts` is `{}`, `answer` contains `the loaded run doesn't record that` and an artifact name, and no computed statistic.

Nothing loaded: `intent` is `need_upload`, answer tells the user to upload
`log.jsonl` or `run_summary.json`.

## Acceptance criteria

- [x] Asking "how many variants were in this run" after loading the seed-42 summary returns the same integer the summary card shows, and names `run_summary.json` → `counts.n_variants`.
- [x] Asking "what was the best composite score" after loading the seed-42 log returns `0.609` and the `job_id` of that variant (`gen00002`).
- [x] That best-composite answer names the artifact and field the number came from.
- [x] Asking "what was the GDT-TS" after loading only a design run returns `the loaded run doesn't record that`, names `benchmark_results.csv` (or equivalent), and `facts` is empty.
- [x] Asking "how long did the run take" with only a log loaded returns `the loaded run doesn't record that`, names `run_summary.json`, and `facts` is empty.
- [x] With `LLM_MODE=echo`, asking the variant-count question puts `8` in the echoed context.
- [x] Asking any question with nothing loaded says to upload `log.jsonl` or `run_summary.json` first and returns no fact.

## Question round

| # | Question | Answer |
|---|---|---|
| 1 | Does the model write the answer? | No. The server writes `answer`. The model, when live, sees the same stats block the stub echoes. |
| 2 | Three decimals — round or truncate? | Round half-up. Seed-42 best displays `0.609`. |
| 3 | Where does `job_id` come from if only a summary is loaded? | `top_variants` row that holds the maximum composite. |
| 4 | Is "what Tm will this have" unanswerable here? | Yes, same as any question we do not have a fact for. Feature #4 adds the proxy refusal text. |
| 5 | New endpoint or `/api/chat`? | `POST /api/ask`, so the demo chat stays untouched. |

## Amendments

| Date | Change | Why |
|---|---|---|
|  |  |  |
