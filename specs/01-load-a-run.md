# 01 - Load a run and see what was recognized

**Story:** As a researcher, I can upload run artifacts and see exactly which ones the app understood.
**Backlog item:** #1
**Status:** shipped

## What it does

The page opens with a file-picker and a short line saying which files to look
for. The user selects up to 20 files from a run directory produced by the
[petase-thermostability-benchmark](https://github.com/naterosenfeld08/petase-thermostability-benchmark)
pipeline and uploads them.

For each file the server decides what it is by looking at its contents, not its
name, and then shows one row per file: the filename, the artifact type it was
recognized as, and one line of fact about it (how many records it holds, or why
it was refused). Refused files are listed with their reason and are not added to
the session. Recognized files become "the loaded run" that every later feature
reads from.

That is the whole feature. Nothing is analyzed, summarized, charted, or asked
about. The user's takeaway is a confident answer to one question: *did the app
understand my files, or not?*

## What it does NOT do

- **No statistics of any kind.** No counts beyond "how many records are in this
  file", no best score, no averages. The summary card is feature #2.
- **No questions and no AI model.** This feature does not call TensorX at all.
  Typed questions are feature #3.
- No charts (#6), no top-variants table (#7), no run comparison (#5).
- **No analysis of benchmark artifacts.** `benchmark_results.csv`,
  `benchmark_results.jsonl`, and `benchmark_summary.json` are recognized and
  listed, but no feature reads them yet, and each is labeled to say so. Doing
  something useful with them is parked in the backlog's *Not ready* section.
- No recognition of other files from the pipeline: `discovery_manifest.json`,
  `figure_data.json`, `training_metadata.json`, `data_splits.npz`, `.pdb`,
  `.fasta`. These are refused like any other unrecognized file.
- No reading a directory path off the local disk. The backlog decided against
  it: a classmate has to be able to test this in Stage 3.
- **No more than one design log per session.** A second design log is refused.
  Holding two runs at once is feature #5's job, and lifting this restriction
  will be a recorded amendment to this spec rather than a silent change.
- **No proving that a summary and a log came from the same run.** A
  `run_summary.json` records the log path it describes in its `out_jsonl` field;
  matching that path is deferred to feature #5. This feature does still report
  when their variant counts disagree — see the question log, question 6.
- No persistence across a server restart. The loaded run lives in server memory
  and a temporary directory. Durable storage arrives with feature #10.
- No accounts, no login, no sharing a loaded run between two browsers.
- No writing to, editing, or renaming the uploaded files. They are read-only input.
- No `.zip` or archive upload. Several files at once, but not bundled.

## How a file is identified

By content signature, in this order. The first match wins.

| Type shown to the user | Extension | Signature |
|---|---|---|
| `design log` | `.jsonl` | First line that parses as a JSON object has a `physics` key |
| `benchmark results` | `.jsonl` | First line that parses as a JSON object has a `metrics` key |
| `benchmark results` | `.csv` | Header row contains all of `job_id`, `mutation_code`, `seq_identity` |
| `run summary` | `.json` | Top level is an object whose `counts` value is an object containing `n_variants` |
| `benchmark summary` | `.json` | Top level is an object whose `counts` value is an object containing `pairs_total` |

Three notes on why the signatures are shaped this way.

**`job_id` cannot be part of the design-log signature.** The backlog's first
draft of this item said a `.jsonl` qualifies if its records have "a `physics` or
a `job_id` key". That is wrong. Records in `benchmark_results.jsonl` also carry
`job_id`, so that rule would file a structural benchmark under `design log` and
every later feature would then look for a `physics.composite` that isn't there.
Only `physics` distinguishes a design log; only `metrics` distinguishes benchmark
results.

**`schema_version` is not usable as a signature.** A design `run_summary.json`
sets it to the integer `1`, while `benchmark_summary.json` sets it to the string
`"2026-04-10.struct-benchmark.run.v1"`. The two summaries are told apart by
which key sits inside `counts` instead.

**Signatures test for a key's presence, never its value.** A file whose
`counts.n_variants` is `null`, `-3`, `"eight"`, or `true` is still recognized as
a `run summary`; what changes is that no count is displayed for it. Recognition
and validation are separate steps, so that a summary with one bad field is still
usable for its other fields.

Identification uses the **first line that parses as a JSON object**, not
literally the first line, because run logs are appended during long jobs and a
half-written first line is a thing that happens.

### What counts as a record

Once the first parseable object has established the type, a **record** is any
later line that parses as a JSON object *and* carries that type's key. Every
other non-blank line — malformed JSON, a valid JSON array, a bare number or
string, or a record of the opposite type — counts as **skipped**, under a single
skipped count. Blank lines are neither.

### The one line of fact

Every displayed count names where it came from, per `AGENTS.md` rule 2.

| Type | The fact shown |
|---|---|
| `run summary` | Variant count, attributed to `counts.n_variants` |
| `design log` | Record count, attributed to parsed JSONL records, with how many lines were read |
| `benchmark summary` | Pair count, attributed to `counts.pairs_total` |
| `benchmark results` (`.jsonl`) | Pair count, attributed to parsed JSONL records |
| `benchmark results` (`.csv`) | Data-row count, excluding the header |

## Acceptance criteria

Happy path:

- [x] Uploading a design run's `run_summary.json` lists it as recognized, labeled `run summary`.
- [x] Uploading a `log.jsonl` lists it as recognized, labeled `design log`, showing the number of variant records it contains.
- [x] Uploading a `benchmark_results.csv` lists it as recognized, labeled `benchmark results`, showing the number of data rows excluding the header.
- [x] Uploading a `benchmark_summary.json` lists it as recognized, labeled `benchmark summary`.
- [x] Every recognized benchmark artifact is listed with the note `no feature uses this yet`, and no design-log or run-summary row carries that note.
- [x] Uploading a `run_summary.json` and a `log.jsonl` together lists both, each with its own type, in one response.
- [x] Every row that shows a count also names the source of that count: `counts.n_variants`, `counts.pairs_total`, parsed JSONL records, or CSV data rows.
- [x] Uploading only a `run_summary.json`, with no design log, leaves the session in a usable state rather than warning that something is missing.

Identification edge cases:

- [x] Uploading a `benchmark_results.jsonl`, whose records have `metrics` but no `physics`, is labeled `benchmark results` and is never labeled `design log`.
- [x] A `log.jsonl` whose first line is truncated mid-object but whose remaining lines are valid is still labeled `design log`, and the response reports that 1 line was skipped.
- [x] A `log.jsonl` with one malformed line among valid ones loads every valid record, reports the count of records loaded, and separately reports how many lines were skipped.
- [x] A `log.jsonl` containing one line that is a valid JSON object but carries `metrics` instead of `physics` loads the `physics` records and counts that line as skipped.
- [x] A `log.jsonl` containing a line that is a valid JSON array and another that is a bare number counts both as skipped and neither as a record.
- [x] A `.json` file whose `counts` object contains `pairs_total` is labeled `benchmark summary`, and the same file with `n_variants` instead is labeled `run summary`.
- [x] A `run_summary.json` whose `counts.n_variants` is a string, a negative number, a boolean, or `null` is still recognized as `run summary`, displays `not recorded` for the count, and says the artifact's own value was unusable.
- [x] Blank lines in a `.jsonl` are not counted as records and are not counted as skipped lines.

Disagreement between artifacts:

- [x] When a `run_summary.json` and a `log.jsonl` are both loaded and the summary's `counts.n_variants` differs from the number of records in the log, both numbers are shown with their sources and the disagreement is stated.
- [x] When those two numbers agree, no disagreement is reported.

Refusals, each with its own message and none of them added to the session:

- [x] Uploading a `.txt`, `.pdb`, or `.fasta` file shows `I don't recognize this file type` and names the three extensions that are accepted.
- [x] Uploading a file of 50,000,001 bytes is refused with a message naming the 50,000,000-byte limit, and no record count is reported for it.
- [x] Uploading a file of exactly 50,000,000 bytes is accepted, because the limit is inclusive.
- [x] Uploading 21 files in one request is refused with a message naming the 20-file limit, and none of the 21 is added.
- [x] Uploading a 0-byte file is refused with a message saying the file is empty.
- [x] A second `design log` is refused with a message saying one is already loaded and the session must be cleared first, and the first design log remains loaded.
- [x] A `.jsonl` whose first parseable object has neither a `physics` nor a `metrics` key is refused with `This looks like JSONL but not a design log`.
- [x] A `.jsonl` in which no line at all parses as a JSON object is refused with a message saying no readable records were found.
- [x] A `.json` file that is not valid JSON is refused with a message saying so, and the app does not return a 500.
- [x] A `.json` file that parses but whose top level is an array or a number rather than an object is refused.
- [x] A `.json` object with no `counts` key, or whose `counts` holds neither `n_variants` nor `pairs_total`, is refused with a message naming both keys it looked for.
- [x] A `.csv` whose header lacks any of `job_id`, `mutation_code`, or `seq_identity` is refused with a message naming the missing columns.
- [x] A file with an accepted extension whose bytes are not valid UTF-8 is refused with a message saying it is not valid UTF-8 text, and the app does not return a 500.

Session and safety:

- [x] A file whose name contains `../` is stored under a sanitized name inside the session's own directory, and no file is created anywhere outside that directory.
- [x] Uploading a file whose **sanitized** name matches one already loaded replaces it, the row says it replaced an earlier upload, and the row shows the sanitized name.
- [x] Uploading `../log.jsonl` when `log.jsonl` is already loaded is treated as a replacement, because the two sanitize to the same name.
- [x] An upload that is refused leaves any previously loaded artifact of the same name in place, and the row says the existing artifact was kept.
- [x] Before anything is uploaded, the page names the files to look for and shows no artifact list.
- [x] Clearing the session empties the artifact list and deletes the session's temporary directory from disk.
- [x] Two browser sessions uploading different runs each see only their own artifacts.

## Question round

Questioner: GPT-5.6 Sol, a different model from the one that drafted this spec.
Ten questions, answered 2026-10-03. Posted on pull request #1.

Question 6 found a genuine contradiction rather than an omission: the "What it
does NOT do" section conflicted with `AGENTS.md` rule 9, which requires that a
disagreement between a computed statistic and an artifact's own claim be
surfaced. Questions 1 and 3 resolved ambiguity that would have blocked a test
writer. The remaining answers tightened boundaries that were merely vague.

| # | Question | Answer |
|---|---|---|
| 1 | If two design logs with different filenames are uploaded into one session, are both part of "the loaded run," or must the second replace or be refused? | Refuse the second, saying one is already loaded and the session must be cleared. Holding two runs is feature #5's job; lifting this will be a recorded amendment. Keeps this feature small, and removes the ambiguity about what "the loaded run" means for #2 and #3. |
| 2 | If an existing artifact is re-uploaded under the same filename but the new file is refused, should the previously loaded artifact remain or be removed? | It remains, untouched. A refused upload must never destroy loaded state. The row reports the refusal and says the existing artifact was kept. |
| 3 | After the first JSONL object establishes the type, which later lines count as loaded records: every JSON object, or only objects carrying the expected `physics` or `metrics` key? How should valid arrays, scalars, or opposite-type records be reported? | Only objects carrying the type's key. Malformed lines, valid arrays, bare scalars, and opposite-type records all count as skipped, under one skipped count. Blank lines stay neither, as already specified. |
| 4 | What exact "one line of fact" should appear for `run_summary.json`, `benchmark_results.jsonl`, and `benchmark_summary.json`? Must displayed counts cite sources under `AGENTS.md` rule 2? | Yes, rule 2 applies and every count names its source. See the "one line of fact" table above for all five types. |
| 5 | Should summary signatures validate the values of `counts.n_variants` and `counts.pairs_total`, or does mere key presence recognize values that are strings, negative numbers, booleans, or null? | Key presence only, which keeps detection robust. A value that is not a non-negative integer still identifies the file, but the count displays "not recorded" per rule 5 and the row says the artifact's own value was unusable per rule 9. |
| 6 | When an uploaded `run_summary.json` and design log report different variant counts, should this feature surface the disagreement as required by `AGENTS.md` rule 9, despite deferring same-run validation? | Yes. The spec was contradicting its own rules. Proving same-run origin via `out_jsonl` stays deferred to #5, but when both are loaded and the counts disagree, both numbers are shown with their sources and the disagreement is stated. Two new acceptance criteria. |
| 7 | Is a recognized `run_summary.json` without a design log considered a usable loaded run, and likewise is a benchmark artifact by itself loaded despite the note `no feature uses this yet`? | A run summary alone is usable; feature #2's card can be built entirely from it. A benchmark artifact alone is recognized but not usable by any feature, which the existing note conveys. A session is usable when it holds either a design log or a run summary. |
| 8 | How should invalid UTF-8 or other undecodable content with an accepted extension be refused, and must it be guaranteed not to produce a 500? | Refused with a message saying the file is not valid UTF-8 text, and yes, guaranteed not to 500. New acceptance criterion. |
| 9 | Does "name matches one already loaded" compare original filenames or sanitized storage names? Do `../log.jsonl` and `log.jsonl` collide and trigger replacement? | Sanitized names, because that is what actually collides in storage. So yes, they collide and the second replaces the first. The row shows the sanitized name so the reason is visible. |
| 10 | Is the 50 MB boundary decimal or binary, and is a file exactly at the limit accepted? What maximum number of files may one request upload? | Decimal, 50,000,000 bytes, inclusive — exactly at the limit is accepted, larger is refused. Maximum 20 files per request, generous for a run directory while still bounding it. |

### Already settled before the question round

Recorded so these are not re-asked by an AI with no memory of this conversation.
Content signatures and their first-match order; why `job_id` and
`schema_version` are excluded as discriminators; blank lines counting as
neither record nor skip; malformed lines being skipped while valid records load;
refusals for unsupported extensions, empty files, invalid JSON, wrong JSON
top-level types, and incomplete CSV headers; benchmark artifacts being
recognized but not analyzed; the exclusion of archives, local directory paths,
cross-restart persistence, accounts, and `out_jsonl` matching; and session
clearing, traversal-safe filenames, same-name replacement, and browser-session
isolation.

## Amendments

<!-- Append only. Never rewrite the sections above. -->

| Date | Change | Why |
|---|---|---|
|  |  |  |

## Notes

- **The backlog has been corrected.** Item #1 in `docs/backlog.md` originally
  said a `.jsonl` qualifies as a design log if its records have `physics` or
  `job_id`. As argued above, `job_id` does not discriminate, because benchmark
  result records carry it too. The backlog now matches the signature table here
  and carries a dated note saying what changed and why, so the correction is
  visible rather than silent.

- **Fixtures are in `data/`, and they are real pipeline output.** Two 8-variant
  design runs at seeds 42 and 43, plus a three-pair structural benchmark. See
  [`data/README.md`](../data/README.md) for exactly how they were produced and
  what to know before asserting against them. All five signatures in the table
  above were verified against these files: a design-log record has `physics` and
  not `metrics`, a benchmark record has `metrics` and not `physics`, and the two
  summaries are separated by `n_variants` against `pairs_total`.

- **`metrics` is always present on a benchmark row, even when scoring failed.**
  `_score_pair` in `petase_design/benchmark_run.py` assigns `row["metrics"] = {}`
  *before* its `try` block, so an errored pair still carries the key with an
  empty object. This is what makes the `metrics` signature safe, and it is why
  detection must test for the key's **presence** rather than its truthiness. A
  truthiness check would refuse a benchmark file whose first pair failed.

- **The 50 MB limit has a measured number behind it.** An 8-variant `log.jsonl`
  is 8,856 bytes, so a record with a full ~290-residue sequence costs about
  1.1 KB. A 1,000-variant run lands near 1.1 MB and 50,000,000 bytes allows
  roughly 45,000 variants, which is far beyond any run this pipeline produces.
  The limit is generous rather than tight, and it exists to stop an accidental
  upload of something huge, not to bound a real run.

- **A finding for backlog #6, recorded here so it isn't rediscovered.** Neither
  fixture's `run_summary.json` contains an `objective_drift` block. The pipeline
  only emits one when records carry an `objective_scalar`, and the plain
  `python -m petase_design.run` path never sets that field — it comes from the
  Pareto-archive and policy-mixing path the Streamlit GUI worker uses. So for
  feature #6, "this run didn't record an objective per generation" is the
  **common** case for CLI runs, not the rare edge case its acceptance criteria
  currently imply. Feature #6 should be re-read in that light when its turn
  comes.

## User test log

2026-10-03, against `http://127.0.0.1:5051`, using the bundled files in `data/`
via curl (one cookie jar per browser session). Sent here from routine step 5.

| Tried | Expected | Happened | Sent back to |
|---|---|---|---|
| Open the page with nothing loaded | Names `log.jsonl` and `run_summary.json`; session list empty | Both names present; `GET /api/artifacts` was `[]` | — |
| Upload seed 42 `log.jsonl` and `run_summary.json` together | Both recognized; 8 variants each; session usable | Design log 8 (`parsed JSONL records`), run summary 8 (`counts.n_variants`), `usable: true`, no warning | — |
| `GET /api/artifacts` after that upload | Same two files still listed | Same two files | — |
| Upload seed 43 `log.jsonl` as `other.jsonl` | Refused; seed 42 log kept | Refused: "A design log is already loaded. Clear the session first." Session still usable | — |
| Upload `petase.pdb` | Refused; names accepted extensions | "I don't recognize this file type. Accepted extensions are .json, .jsonl, .csv." | — |
| Upload the sample benchmark CSV and summary | Recognized, counted 3, noted unused | Both labeled with `no feature uses this yet`; CSV 3 data rows; summary `counts.pairs_total` 3 | — |
| Replace `log.jsonl` with the seed 43 log | Replaced; still one design log | `replaced: true`, count still 8 | — |
| Upload a summary claiming 99 variants next to the 8-record log | Disagreement named with both sources | Warning: `99 (counts.n_variants) vs 8 (parsed JSONL records)` | — |
| Re-upload an empty `log.jsonl` | Refused; existing log kept | "The file is empty. The existing artifact was kept." GET still showed count 8 | — |
| Second cookie jar uploads only a summary | Sees only its own file; first session unchanged | Session 2: `[run summary]`. Session 1 kept its own list | — |
| Clear session 1 | Session 1 empty; session 2 untouched | Session 1 `[]`; session 2 still `[run summary]` | — |

No bug found. Did not send back to spec, tests, or design. Ready for merge once backlog status and a changelog line are written.
