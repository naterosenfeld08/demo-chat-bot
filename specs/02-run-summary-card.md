# 02 - Run summary card

**Story:** As a researcher, I can see headline numbers for the loaded run without typing a question.
**Backlog item:** #2
**Status:** shipped

## What it does

After a usable run is loaded (a design log, a run summary, or both), the page
shows a card with four headline numbers: how many variants, how many of those
have a predicted structure, the best `physics.composite`, and the wall-clock
seconds. Each number names the artifact and field it came from. The user does
not type a question. The card is the thing they look at first.

If the session has a `run_summary.json`, every number on the card is the value
from that file. If the session has only a `log.jsonl`, the variant count, the
structure count, and the best composite are recomputed from the log and marked
`recomputed`. Wall-clock seconds cannot be recomputed from a log and display
`not recorded`.

A field that is absent, or whose value is not a usable number, displays
`not recorded`. A field that is present and equal to `0` displays `0` — zero
that was recorded is not the same as a field that was never written.

## What it does NOT do

- No questions and no AI model. That is feature #3.
- No charts (#6), no top-variants table (#7), no two-run comparison (#5).
- No converting a composite into Tm, activity, or ΔΔG. The card shows the
  composite and names it as `physics.composite`.
- No analysis of benchmark artifacts. They can sit in the session; they do not
  appear on this card.
- No new upload rules. Feature #1 still decides what is loaded.

## Where each number comes from

Four fields, always in this order. `source` is the string shown on the card.

| id | When a run summary is loaded | When only a design log is loaded |
|---|---|---|
| `n_variants` | `run_summary.json` → `counts.n_variants` | `log.jsonl` → parsed records, marked recomputed |
| `n_with_structure` | `run_summary.json` → `counts.n_with_structure` | Count of log records whose `structure_pdb` is a non-empty string, marked recomputed |
| `best_composite` | Maximum of `top_variants[].composite` in the summary, source `run_summary.json` → `top_variants[].composite (maximum)` | Maximum of `physics.composite` among parsed log records, source `log.jsonl` → `physics.composite (maximum)`, marked recomputed |
| `seconds_wall` | `run_summary.json` → `runtime.seconds_wall` | `not recorded` |

When both a summary and a log are loaded, the card still reads the four values
from the summary. If a recomputation from the log disagrees with a summary
value, the card keeps the summary value and adds a warning that names both
numbers and both sources. That is `AGENTS.md` rule 9, the same rule that
forced the count-disagreement criterion in feature #1.

A usable number is a finite `int` or `float` that is not a boolean. `0` and
`0.0` are usable. `null`, a string, a boolean, `NaN`, and a missing key are
not.

## HTTP contract

`GET /api/summary` returns the card for the current session.

When the session is not usable:

```json
{ "present": false, "fields": [], "warnings": [] }
```

When it is usable, `present` is true and `fields` has exactly those four ids,
each:

| key | meaning |
|---|---|
| `id` | One of the four ids above |
| `value` | The number, or `null` when not recorded |
| `display` | The number as a string, or `not recorded` |
| `source` | Artifact and field, or empty when not recorded |
| `recomputed` | `true` only when the value was computed from the log because no summary supplied it |

`warnings` lists summary-vs-log disagreements for these four fields.

The page paints `#run-summary-card` from this endpoint after upload, clear, and
reload, the same way the artifact list uses `GET /api/artifacts`.

## Acceptance criteria

- [x] With nothing loaded, `GET /api/summary` returns `present` false and no fields, and the page has an element `#run-summary-card` that does not show any of the four numbers.
- [x] Uploading the seed-42 `run_summary.json` makes the card present, with variant count `8` sourced from `run_summary.json` → `counts.n_variants`.
- [x] That same card shows structures `0` sourced from `run_summary.json` → `counts.n_with_structure`, and the display is `0`, not `not recorded`.
- [x] That same card shows best composite equal to the maximum `top_variants[].composite` in the file (`0.6085333333333334`) and names that source.
- [x] That same card shows wall-clock seconds `0.003` sourced from `run_summary.json` → `runtime.seconds_wall`.
- [x] Uploading the seed-42 summary and log together still shows those four summary values, none marked recomputed.
- [x] Uploading only the seed-42 `log.jsonl` makes the card present, with variant count `8` marked recomputed and sourced from the log.
- [x] That log-only card shows structures `0` marked recomputed (every `structure_pdb` in the fixture is null) and best composite equal to the maximum `physics.composite` in the log, marked recomputed.
- [x] That log-only card shows wall-clock seconds as `not recorded`, with `value` null.
- [x] Uploading only benchmark artifacts does not make the card present.
- [x] A summary whose `counts.n_variants` is missing or not a usable number shows `not recorded` for variants, not `0`.
- [x] A summary whose `runtime` object is missing shows `not recorded` for seconds.
- [x] A summary with no `top_variants`, or none with a usable `composite`, shows `not recorded` for best composite.
- [x] A summary that says `8` variants next to a log of `4` records keeps `8` on the card and warns, naming both numbers and both sources.
- [x] A summary whose best composite disagrees with the log's maximum keeps the summary value and warns, naming both numbers.
- [x] Clearing the session makes the card not present again.
- [x] Two sessions each see only their own card.

## Question round

Recorded 2026-10-03 by the spec writer, using the rules and fixtures from
feature #1 rather than a second model, so this feature can move in one sitting.
A second model can still object on the PR.

| # | Question | Answer |
|---|---|---|
| 1 | The sample summary records `n_with_structure: 0`. Is that "not recorded"? | No. Zero that was written is shown as `0`. `not recorded` is only for a missing or unusable value. |
| 2 | The summary has no `best_composite` field. Which field is "the value in the file"? | The maximum of `top_variants[].composite`. That is what the pipeline actually writes. |
| 3 | When both files are loaded, who wins? | The summary, always. A disagreement is a warning, not a substitute value. |
| 4 | Can wall-clock seconds be recomputed from a log? | No. `not recorded`. |
| 5 | Does a structure count of 0 from a log-only recompute display `0` or `not recorded`? | `0`, marked recomputed. We counted; the count was zero. |
| 6 | Do benchmark files affect the card? | No. |
| 7 | Should the card round the composite to three decimals? | No. Feature #3 will. This card equals the file value. |
| 8 | What is a usable number? | A finite int or float, including 0. Not a bool, string, null, or NaN. |

## Amendments

| Date | Change | Why |
|---|---|---|
|  |  |  |

## Notes

- Seed-42 best composite from the summary is `0.6085333333333334` (`gen00002`).
  The same maximum lives on the log as `physics.composite`. The two should
  agree on these fixtures; disagreement tests must alter one side.
- `n_with_structure: 0` on the sample summary is the common CLI case (ColabFold
  off). Treating it as missing would make every real CLI run look like the
  pipeline forgot to write the field.
