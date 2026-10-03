# 01 - Load a run and see what was recognized

**Story:** As a researcher, I can upload run artifacts and see exactly which ones the app understood.
**Backlog item:** #1
**Status:** draft

## What it does

The page opens with a file-picker and a short line saying which files to look
for. The user selects one or more files from a run directory produced by the
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
- **No checking that an uploaded summary and log came from the same run.** A
  `run_summary.json` records the log path it describes in its `out_jsonl` field,
  so this is checkable, but it is not checked here. See Notes.
- No persistence across a server restart. The loaded run lives in server memory
  and a temporary directory. Durable storage arrives with feature #10.
- No accounts, no login, no sharing a loaded run between two browsers.
- No writing to, editing, or renaming the uploaded files. They are read-only input.
- No `.zip` or archive upload. One file at a time, or several at once, but not
  bundled.

## How a file is identified

By content signature, in this order. The first match wins.

| Type shown to the user | Extension | Signature |
|---|---|---|
| `design log` | `.jsonl` | First line that parses as a JSON object has a `physics` key |
| `benchmark results` | `.jsonl` | First line that parses as a JSON object has a `metrics` key |
| `benchmark results` | `.csv` | Header row contains all of `job_id`, `mutation_code`, `seq_identity` |
| `run summary` | `.json` | Top level is an object whose `counts` value is an object containing `n_variants` |
| `benchmark summary` | `.json` | Top level is an object whose `counts` value is an object containing `pairs_total` |

Two notes on why the signatures are shaped this way:

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

Identification uses the **first line that parses as a JSON object**, not
literally the first line, because run logs are appended during long jobs and a
half-written first line is a thing that happens.

## Acceptance criteria

Happy path:

- [ ] Uploading a design run's `run_summary.json` lists it as recognized, labeled `run summary`.
- [ ] Uploading a `log.jsonl` lists it as recognized, labeled `design log`, showing the number of variant records it contains.
- [ ] Uploading a `benchmark_results.csv` lists it as recognized, labeled `benchmark results`, showing the number of data rows excluding the header.
- [ ] Uploading a `benchmark_summary.json` lists it as recognized, labeled `benchmark summary`.
- [ ] Every recognized benchmark artifact is listed with the note `no feature uses this yet`, and no design-log or run-summary row carries that note.
- [ ] Uploading a `run_summary.json` and a `log.jsonl` together lists both, each with its own type, in one response.

Identification edge cases:

- [ ] Uploading a `benchmark_results.jsonl`, whose records have `metrics` but no `physics`, is labeled `benchmark results` and is never labeled `design log`.
- [ ] A `log.jsonl` whose first line is truncated mid-object but whose remaining lines are valid is still labeled `design log`, and the response reports that 1 line was skipped.
- [ ] A `log.jsonl` with one malformed line among valid ones loads every valid record, reports the count of records loaded, and separately reports how many lines were skipped.
- [ ] A `.json` file whose `counts` object contains `pairs_total` is labeled `benchmark summary`, and the same file with `n_variants` instead is labeled `run summary`.
- [ ] Blank lines in a `.jsonl` are not counted as records and are not counted as skipped lines.

Refusals, each with its own message and none of them added to the session:

- [ ] Uploading a `.txt`, `.pdb`, or `.fasta` file shows `I don't recognize this file type` and names the three extensions that are accepted.
- [ ] Uploading a file of 51 MB is refused with a message naming the 50 MB limit, and no record count is reported for it.
- [ ] Uploading a 0-byte file is refused with a message saying the file is empty.
- [ ] A `.jsonl` whose first parseable object has neither a `physics` nor a `metrics` key is refused with `This looks like JSONL but not a design log`.
- [ ] A `.jsonl` in which no line at all parses as a JSON object is refused with a message saying no readable records were found.
- [ ] A `.json` file that is not valid JSON is refused with a message saying so, and the app does not return a 500.
- [ ] A `.json` file that parses but whose top level is an array or a number rather than an object is refused.
- [ ] A `.json` object with no `counts` key, or whose `counts` holds neither `n_variants` nor `pairs_total`, is refused with a message naming both keys it looked for.
- [ ] A `.csv` whose header lacks any of `job_id`, `mutation_code`, or `seq_identity` is refused with a message naming the missing columns.

Session and safety:

- [ ] A file whose name contains `../` is stored under a sanitized name inside the session's own directory, and no file is created anywhere outside that directory.
- [ ] Uploading a file whose name matches one already loaded replaces it, and the row says it replaced an earlier upload.
- [ ] Before anything is uploaded, the page names the files to look for and shows no artifact list.
- [ ] Clearing the session empties the artifact list and deletes the session's temporary directory from disk.
- [ ] Two browser sessions uploading different runs each see only their own artifacts.

## Question round

Pending. This spec has not been through the question round yet. Agent 2 should
be a different model, must not write code, and should ask at most 10 questions
about what this spec fails to specify, most important first.

| # | Question | Answer |
|---|---|---|
|  |  |  |

## Amendments

<!-- Append only. Never rewrite the sections above. -->

| Date | Change | Why |
|---|---|---|
|  |  |  |

## Notes

- **The backlog needs a correction.** Item #1's acceptance criteria in
  `docs/backlog.md` still say a `.jsonl` qualifies as a design log if its records
  have "neither a `physics` nor a `job_id` key". As argued above, `job_id` does
  not discriminate, because benchmark result records carry it too. The backlog
  should be updated to match the signature table in this spec. Flagging it here
  rather than editing it silently.

- **Tests need real fixture files.** Every criterion above refers to a genuine
  artifact shape, and hand-written fakes will drift from what the pipeline
  actually emits. Before the tests are written, a small real run should be
  captured into `data/` — a short `log.jsonl` with a handful of variants, its
  `run_summary.json`, and one `benchmark_results.csv`. Backlog #12 also needs a
  bundled sample run for a classmate to upload, so this serves both.

- **Things I expect the questioner to raise**, recorded so the answers land in
  the table rather than in a chat window: what happens when two design logs are
  uploaded at once; whether a run summary is usable with no log beside it;
  whether the record count should come from parsing every line of a large log or
  only a prefix; what the limit is on the number of files in one upload; and
  whether the `out_jsonl` mismatch check deferred above should actually be part
  of this feature instead of #5.

- The 50 MB limit is a guess that needs a real number behind it. A 50-cycle
  design run's `log.jsonl` carries a full variant sequence per record, so the
  size should be measured against an actual long run before this is treated as
  settled.
