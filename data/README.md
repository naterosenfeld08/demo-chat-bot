# data/

Sample run artifacts from the
[petase-thermostability-benchmark](https://github.com/naterosenfeld08/petase-thermostability-benchmark)
pipeline. They serve two purposes: fixtures for the test suite, and something a
classmate can upload in Stage 3 without having to run the pipeline themselves.

**These are real pipeline output, not hand-written mock-ups.** Everything here
was emitted by the pipeline's own code, because a fixture that drifts from what
the pipeline actually writes is worse than no fixture.

## What's here

| Path | What it is |
|---|---|
| `sample-run-seed42/log.jsonl` | 8 design-loop variants, one JSON object per line |
| `sample-run-seed42/run_summary.json` | The summary the pipeline writes beside that log |
| `sample-run-seed43/` | The same run with a different seed, for comparison and multi-seed features |
| `sample-benchmark/benchmark_results.csv` | 3 structural benchmark pairs, 32 columns |
| `sample-benchmark/benchmark_results.jsonl` | The same 3 pairs, unflattened |
| `sample-benchmark/benchmark_summary.json` | The summary for that benchmark run |

The two seeds disagree slightly on the best composite score — 0.6085 for seed 42
against 0.6106 for seed 43. That near-tie is useful rather than inconvenient: it
is exactly the "is this real or is this the seed" situation backlog item #8 has
to handle, and it comes for free in the fixtures.

## How they were generated

The design runs came from the pipeline CLI, at 8 cycles so the files stay small
enough to read by eye:

```bash
python -m petase_design.run --cycles 8 --mutations 3 --seed 42 \
  --out sample-run-seed42/log.jsonl
```

No structure prediction was enabled, so no variant has a `structure_pdb` and
`counts.n_with_structure` is 0. That is a realistic state — ColabFold is opt-in
and slow — and it means the "no structure" paths get exercised by default.

The benchmark files were built by calling the pipeline's own
`_flatten_row_for_csv` and the summary shape from `_write_results` in
`petase_design/benchmark_run.py`, over the real measured metrics committed in
that repo under `reports/structural_design_integration_summary/data/`. The one
`status: "ok"` row is the genuine amicyanin M51A case (2OV0 to 2QDV) with its
real 54.76% GDT-TS. The two `status: "error"` rows are real discovered pairs that
were never scored, which is the shape a partially completed campaign leaves
behind.

The generator script is not committed here on purpose. `AGENTS.md` rule 7 says
this repo never imports from the pipeline repo, and the generator has to import
it to guarantee the CSV header matches. Regenerating is a one-time job done from
a checkout of the pipeline.

## Things to know before writing tests against these

- **Absolute paths are baked in.** `run_summary.json` records `out_jsonl` and
  `run.wt_fasta` as absolute paths from the machine that generated it. That is
  what the pipeline writes, so it is left alone. No test should assume those
  paths exist.
- **`objective_drift` is absent** from both `run_summary.json` files. The
  pipeline only emits it when records carry an `objective_scalar`, which the
  plain CLI path does not produce. See the note in `specs/01-load-a-run.md`.
- **`metrics` is always present** on a benchmark row, even when scoring failed,
  because `_score_pair` assigns it before its `try` block. On the two error rows
  it is an empty object, so artifact detection must test for the key's presence
  rather than its truthiness.
- `runtime.seconds_wall` is about 0.005 for these runs. Any test asserting a
  formatted duration needs to cope with a sub-second value.
- These files contain no personal data and no secrets.
