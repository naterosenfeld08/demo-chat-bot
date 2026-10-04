# tests/

One file per feature, named for the spec it tests:

```
specs/01-load-a-run.md   →   tests/test_01_load_a_run.py
```

Every test traces back to a line in a spec's acceptance criteria. Each test's
docstring quotes the criterion it covers, so the trace is readable without
cross-referencing.

Two rules that matter more than anything else in this folder:

1. Tests get written **before** the code they test, and they must fail first.
2. Once a test exists, **it does not get edited to make code pass.** If a test is
   genuinely wrong, say so on the pull request and wait.

Run them with `pytest`.

---

## The HTTP contract these tests assume

The spec describes behavior, not an API. Writing tests first means the tests
have to pin down a contract, so here it is in one place. **The builder must
implement this contract rather than change these tests.** If any part of it is
wrong or awkward, say so on the pull request and wait for a decision.

### `POST /api/artifacts`

Multipart upload. Repeatable form field named `files`. Always returns `200` with
a JSON body, even when every file was refused — a refusal is a result, not an
HTTP error. Only a genuinely broken request returns a non-200.

```json
{
  "artifacts": [
    {
      "filename": "log.jsonl",
      "stored_name": "log.jsonl",
      "type": "design log",
      "count": 8,
      "count_display": "8",
      "count_source": "parsed JSONL records",
      "lines_read": 8,
      "skipped_lines": 0,
      "notes": [],
      "replaced": false
    }
  ],
  "refused": [{ "filename": "notes.txt", "reason": "I don't recognize this file type. ..." }],
  "warnings": [],
  "error": null,
  "usable": true
}
```

| Field | Meaning |
|---|---|
| `type` | One of `design log`, `benchmark results`, `run summary`, `benchmark summary` |
| `count` | The integer count, or `null` when the artifact's own value was unusable |
| `count_display` | `count` as a string, or `not recorded` when it is `null` |
| `count_source` | Where the count came from, e.g. `counts.n_variants`, `parsed JSONL records`, `CSV data rows` |
| `lines_read`, `skipped_lines` | JSONL only; `null` for other types |
| `notes` | Per-artifact remarks, e.g. `no feature uses this yet` |
| `replaced` | `true` when this upload replaced an earlier artifact with the same `stored_name` |
| `warnings` | Session-level messages, such as a summary and log disagreeing on variant count |
| `error` | A request-level refusal that rejects the whole upload, such as exceeding the file-count limit. `null` otherwise |
| `usable` | `true` when the session holds a design log or a run summary |

`refused` is per-file: other files in the same request still get processed.
`error` rejects the entire request, and then `artifacts` is empty.

### `GET /api/artifacts`

Current session state: `artifacts`, `warnings`, and `usable`, with the same
shapes. No `refused` key, since nothing was just uploaded.

### `POST /api/artifacts/clear`

Empties the session and deletes its temporary directory. Returns `200`.

### `GET /`

The page. With nothing loaded it names the files to look for and shows no
artifact list.

### Config keys

| Key | Default | Why it's config rather than a literal |
|---|---|---|
| `MAX_ARTIFACT_BYTES` | `50_000_000` | So boundary behavior can be tested without writing a 50 MB file to disk twice per run |
| `MAX_ARTIFACT_FILES` | `20` | Same reason, and it keeps the limit in one place |
| `ARTIFACT_ROOT` | a temp directory | Tests assert that nothing is written outside the session's own subdirectory |

One test asserts `MAX_ARTIFACT_BYTES` is exactly `50_000_000`, so the real limit
is still pinned. The inclusive-boundary tests then lower it, which is the only
way to test "a file of exactly the limit is accepted" without a 50 MB fixture.
