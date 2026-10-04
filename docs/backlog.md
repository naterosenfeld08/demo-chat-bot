<!-- Course: Stage 1, then revised all semester. Graded again in Stage 3 and
     Stage 4: how it CHANGED is the evidence, not whether it stayed the same.
     See docs/course/DELIVERABLES.md -->

# Backlog

Every feature, in the order it gets built. **#1 is what gets built first.**

Each item is one user story plus acceptance criteria that someone else could test
without asking you anything.

> **If you can't say how you'd test it, it isn't ready to be on this list yet.**
> Move it to *Not ready* at the bottom and come back to it.

## How to read this

| Column | Means |
|---|---|
| **#** | Build order. Also the spec filename and the branch name. |
| **Story** | As a [user], I can [do X]. |
| **Acceptance criteria** | Something observable. A stranger could confirm it. Written as "It's done when ___". |
| **Status** | not started / spec written / tests written / built / shipped |

Acceptance criteria are written out in full below the table, because they do not
fit in a table cell and shortening them is how they stop being testable.

Throughout, "a run" means a directory produced by the
[petase-thermostability-benchmark](https://github.com/naterosenfeld08/petase-thermostability-benchmark)
pipeline: a `log.jsonl` of one record per variant, usually a `run_summary.json`
beside it, and for structural benchmarks a `benchmark_results.csv` and
`benchmark_summary.json`.

---

## To build

| # | Story | Status | Week |
|---|---|---|---|
| 1 | As a researcher, I can upload run artifacts and see which ones the app understood | shipped | 1 |
| 2 | As a researcher, I can see headline numbers for a loaded run without typing a question | not started | 2 |
| 3 | As a researcher, I can ask a question in English and get an answer computed from the artifacts | not started | 3 |
| 4 | As a researcher, I can't accidentally read more into a score than it supports | not started | 5 |
| 5 | As a researcher, I can compare two runs side by side | not started | 5 |
| 6 | As a researcher, I can see whether the design loop actually improved over generations | not started | 6 |
| 7 | As a researcher, I can see the top-ranked variants with their mutations spelled out | not started | 6 |
| 8 | As a researcher, I can tell whether a result is real or just the seed | not started | 8 |
| 9 | As a researcher, I can export a summary that's safe to send to a mentor | not started | 9 |
| 10 | As a researcher, I can see what I already asked about a run | not started | 9 |
| 11 | As a maintainer, I can find modules that shadow each other in the pipeline repo | not started | 10 (stretch) |
| 12 | As a classmate, I can try the app from a URL with no setup | not started | 7 |

Item #12 is built in week 7 rather than last. It is listed near the end because
it depends on #1–#3 existing, but Stage 3 needs it before the later features.

---

## Acceptance criteria

### 1. Load a run and see what was recognized

*As a researcher, I can upload one or more run artifacts and see exactly which
ones the app understood.*

- It's done when uploading a `run_summary.json` lists it as recognized, labeled
  "run summary".
- It's done when uploading a `log.jsonl` lists it as recognized, labeled "design
  log", showing the number of variant records it contains.
- It's done when uploading a file that is not `.json`, `.jsonl`, or `.csv` shows
  the message "I don't recognize this file type" and the file is not added to
  the session.
- It's done when uploading a `.jsonl` whose first parseable object has neither a
  `physics` nor a `metrics` key shows "This looks like JSONL but not a design
  log" instead of a stack trace.
- It's done when uploading a file over 50,000,000 bytes is refused with a
  message that names the limit.
- It's done when a `log.jsonl` containing one malformed line among valid ones
  loads the valid records and reports how many lines it skipped.
- It's done when a `run_summary.json` and a `log.jsonl` are both loaded, their
  variant counts disagree, and both numbers are shown with their sources
  alongside a statement of the disagreement.

> **Corrected 2026-10-03.** This item originally said a `.jsonl` qualifies as a
> design log if its records carry `physics` **or `job_id`**. That was wrong:
> records in `benchmark_results.jsonl` also carry `job_id`, so the rule would
> have filed a structural benchmark as a design log. Only `physics` discriminates.
> The disagreement criterion was added after the question round found that the
> spec's deferral of same-run checking contradicted `AGENTS.md` rule 9.
> [`specs/01-load-a-run.md`](../specs/01-load-a-run.md) holds the full set of
> criteria and the reasoning.

### 2. Run summary card

*As a researcher, I can see headline numbers for the loaded run without typing a
question.*

- It's done when the card shows the variant count, the number of variants with a
  predicted structure, the best `physics.composite`, and the wall-clock seconds.
- It's done when each of those four values is labeled with the artifact and field
  it was read from, for example "`run_summary.json` → `counts.n_variants`".
- It's done when, for a run that has a `run_summary.json`, every value on the
  card equals the value in that file.
- It's done when a run with only a `log.jsonl` still shows a card, with the
  variant count and best composite recomputed from the log and each marked
  "recomputed".
- It's done when a field absent from the artifact displays "not recorded" rather
  than `0`, `null`, or a blank.

### 3. Ask a question and get a computed answer

*As a researcher, I can ask a question in plain English and get an answer whose
numbers came from the artifacts.*

- It's done when asking "how many variants were in this run" returns the same
  integer the summary card shows.
- It's done when asking "what was the best composite score" returns the maximum
  `physics.composite` in the log to three decimal places and names the `job_id`
  it belongs to.
- It's done when every numeric answer states which artifact and which field the
  number came from.
- It's done when asking something the loaded artifacts cannot answer returns
  "the loaded run doesn't record that", names what artifact would be needed, and
  gives no number.
- It's done when the AI service is replaced with a stub that echoes the context
  it was given, and the correct number is present in that echoed context — proving
  the server computed it rather than the model.
- It's done when no question can be answered before at least one artifact is
  loaded; the app says what to upload first.

### 4. Caveats travel with the numbers

*As a researcher, I can't accidentally read more into a score than it supports.*

- It's done when any answer citing a ΔΔG value appends the FireProt-scale caveat
  text, stating that the value is a generic prior and not a PETase-specific
  measurement.
- It's done when asking "what Tm will this variant have" returns a refusal
  stating that the composite is a proxy and does not predict Tm, and returns no
  number.
- It's done when asking "is this variant more stable than wild type" returns the
  composite comparison followed by the sentence that these scores are proxies,
  not measured Tm.
- It's done when any answer citing a Random Forest uncertainty interval states
  that the interval is model disagreement, not experimental error.
- It's done when the caveat text is read at request time from a file in this
  repo, so that editing that file changes the next answer without a code change
  or restart.

### 5. Compare two runs

*As a researcher, I can load two runs and see them side by side.*

- It's done when two loaded runs show one table with the same metrics for both
  and a delta column.
- It's done when the two runs used different seeds and the table shows a warning
  naming both seeds and saying the difference may be noise.
- It's done when the two runs used different `mutations_per_variant` and the
  warning names that config difference and its two values.
- It's done when a metric is present in one run and absent in the other, that
  cell reads "not recorded" and no delta is computed for that row.
- It's done when a third run is loaded and the app asks which two to compare
  rather than silently picking.

### 6. Objective drift chart

*As a researcher, I can see whether the design loop actually improved over
generations.*

- It's done when a run with an `objective_drift` block renders a chart with one
  point per generation for both `objective_mean` and `objective_best`.
- It's done when every plotted y-value equals the corresponding number in
  `run_summary.json`.
- It's done when a run where no record has an `objective_scalar` shows "this run
  didn't record an objective per generation" and no empty chart.
- It's done when `objective_best` is unchanged from some generation onward, the
  app states that the loop stopped improving after that generation and names it.

### 7. Top variants table

*As a researcher, I can see the top-ranked variants with their mutations spelled
out.*

- It's done when the table lists the top ten variants by `rank_score`, each with
  its rank, composite, and mutations rendered as codes like "M51A, S121E".
- It's done when a listed variant has no `structure_pdb_basename` and its row is
  flagged "no structure".
- It's done when clicking a column heading re-sorts the table by that column.
- It's done when the run has fewer than ten variants, every one is shown and no
  blank or padded rows appear.
- It's done when two variants tie on `rank_score` and both appear, with the tie
  visible rather than one silently dropped.

### 8. Multi-seed stability

*As a researcher, I can tell whether a result is real or just the seed.*

- It's done when three runs from seeds 42, 43, and 44 load together and the app
  reports the best composite for each seed plus the spread across them.
- It's done when the spread across seeds exceeds the gap between the best and
  tenth-best variant within a single seed, and the app states that the ranking is
  seed-dependent.
- It's done when two of the loaded runs share the same seed, the app says so and
  declines to treat them as independent samples.
- It's done when only one run is loaded, the app says multi-seed analysis needs
  at least two runs with different seeds.

### 9. Export a mentor-ready summary

*As a researcher, I can export a summary that's safe to send to a mentor.*

- It's done when a copy button produces Markdown whose first section is the
  caveats, positioned before any numeric result.
- It's done when every number in the export also appears somewhere in the app's
  own cards or answers.
- It's done when the export names the source run and the date its artifacts were
  generated.
- It's done when the export contains no API key, no file path outside the run
  directory, and no content from a run that is not currently loaded.

### 10. Question history per run

*As a researcher, I can see what I already asked about a run.*

- It's done when a question asked earlier in the session appears in a list with
  its answer and a timestamp.
- It's done when the page is reloaded and the history for the still-loaded run is
  still there.
- It's done when clearing a run also clears its history, and the app warns before
  doing it.
- It's done when two different runs are loaded and each question is listed under
  the run it was asked about.

### 11. Shadowed-module audit (stretch)

*As a maintainer, I can find modules that shadow each other in the pipeline
repo.*

- It's done when pointing the audit at a checkout lists every root-level module
  whose name matches a module in `core/`, reporting both line counts.
- It's done when a root module only re-exports from its `core/` counterpart, it's
  labeled "shim" rather than "duplicate".
- It's done when a root module and its `core/` counterpart both contain
  definitions, it's labeled "duplicate" and both line counts are shown.
- It's done when no shadowed modules exist, the audit says so rather than showing
  an empty list.

### 12. Deployed and testable by someone else

*As a classmate, I can try the app from a URL with no setup.*

- It's done when a classmate opens the Render URL, uploads the sample run bundled
  in `data/`, and sees a summary card without installing anything.
- It's done when no API key appears in the page source, in any network response,
  or in any client-side script.
- It's done when the server has no API key configured and the page explains how
  to set one instead of returning a 500.
- It's done when a classmate follows only `README.md` to run it locally and
  reaches a working summary card without asking me a question.

---

## Added later

<!-- Things that came out of user testing in Stage 3 and got the answer
     "yes, but later." Put them in position, with a note saying where they came
     from, so the reason survives. Nothing here yet; Stage 3 fills it. -->

---

## Not ready

Ideas I can't yet write testable acceptance criteria for.

- **Free-form query over arbitrary columns.** Letting the model generate a pandas
  expression against any field in the JSONL. I can't yet say how I'd test that a
  generated query is both correct and safe, and an unsafe one executes arbitrary
  code on my machine. Needs a fixed, enumerated set of query shapes first.
- **"Is this improvement statistically significant?"** I'd have to decide which
  test is appropriate for comparing composite distributions across seeds before I
  can write a criterion. Picking the test is the real work, not the coding.
- **Reading structural benchmark CSVs alongside design logs.** The GDT-TS metrics
  in `benchmark_results.csv` describe WT/mutant structure pairs, not design
  variants, so it isn't yet clear what a combined view would even assert.
- **Suggesting which mutation to try next.** Tempting and the most scientifically
  interesting thing here, but any criterion I write would be unfalsifiable without
  lab data, and the limitations doc is explicit that these scores don't support it.

## Decided against

| Idea | Why not |
|---|---|
| Let the model compute the statistics itself | Float aggregation over thousands of records is what language models are worst at, and a plausible wrong mean is more dangerous than no answer. It would also make every numeric acceptance criterion unverifiable. |
| Retrain or fine-tune the ΔΔG model inside this app | That's the pipeline repo's job. This app reads results; it doesn't produce them. Mixing the two would make a failed training run look like a broken web app. |
| Embed a 3D structure viewer | The pipeline's Streamlit GUI already does this with py3Dmol, and reimplementing it adds a CDN dependency for no new insight. |
| Host as a static site | The TensorX key would be visible to every visitor. `AGENTS.md` rule 6 forbids it and so does physics. |
| Read run directories straight off my local disk in the deployed app | Convenient for me, but then a classmate can't test it in Stage 3, which is a graded requirement. Upload instead. |
