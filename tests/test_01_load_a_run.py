"""Tests for specs/01-load-a-run.md.

One test per acceptance criterion, in the spec's own order. Each docstring
quotes the criterion it covers. The HTTP contract these tests assume is written
down in tests/README.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import (
    as_jsonl,
    benchmark_results_csv,
    benchmark_results_jsonl,
    design_log,
    design_log_records,
    payload,
    refusal_for,
    refusals,
    row_for,
    rows,
    summary_with_count,
    upload,
)
from conftest import BENCHMARK, SEED42, SEED43


def body(path: Path) -> bytes:
    return path.read_bytes()


RUN_SUMMARY = SEED42 / "run_summary.json"
LOG = SEED42 / "log.jsonl"
BENCH_SUMMARY = BENCHMARK / "benchmark_summary.json"


# =============================================================================
# Happy path
# =============================================================================


def test_run_summary_is_recognized(client):
    """Uploading a design run's run_summary.json lists it as recognized,
    labeled `run summary`."""
    r = upload(client, ("run_summary.json", body(RUN_SUMMARY)))
    assert row_for(r, "run_summary.json")["type"] == "run summary"


def test_design_log_is_recognized_with_its_record_count(client):
    """Uploading a log.jsonl lists it as recognized, labeled `design log`,
    showing the number of variant records it contains."""
    r = upload(client, ("log.jsonl", body(LOG)))
    row = row_for(r, "log.jsonl")
    assert row["type"] == "design log"
    assert row["count"] == 8


def test_benchmark_csv_is_recognized_with_its_data_row_count(client):
    """Uploading a benchmark_results.csv lists it as recognized, labeled
    `benchmark results`, showing the number of data rows excluding the header."""
    r = upload(client, ("benchmark_results.csv", benchmark_results_csv()))
    row = row_for(r, "benchmark_results.csv")
    assert row["type"] == "benchmark results"
    assert row["count"] == 3


def test_benchmark_summary_is_recognized(client):
    """Uploading a benchmark_summary.json lists it as recognized, labeled
    `benchmark summary`."""
    r = upload(client, ("benchmark_summary.json", body(BENCH_SUMMARY)))
    assert row_for(r, "benchmark_summary.json")["type"] == "benchmark summary"


def test_only_benchmark_artifacts_are_noted_as_unused(client):
    """Every recognized benchmark artifact is listed with the note `no feature
    uses this yet`, and no design-log or run-summary row carries that note."""
    r = upload(
        client,
        ("benchmark_results.csv", benchmark_results_csv()),
        ("benchmark_summary.json", body(BENCH_SUMMARY)),
        ("log.jsonl", body(LOG)),
        ("run_summary.json", body(RUN_SUMMARY)),
    )
    note = "no feature uses this yet"
    for name in ("benchmark_results.csv", "benchmark_summary.json"):
        assert note in row_for(r, name)["notes"]
    for name in ("log.jsonl", "run_summary.json"):
        assert note not in row_for(r, name)["notes"]


def test_summary_and_log_uploaded_together_are_both_listed(client):
    """Uploading a run_summary.json and a log.jsonl together lists both, each
    with its own type, in one response."""
    r = upload(
        client,
        ("run_summary.json", body(RUN_SUMMARY)),
        ("log.jsonl", body(LOG)),
    )
    assert row_for(r, "run_summary.json")["type"] == "run summary"
    assert row_for(r, "log.jsonl")["type"] == "design log"


def test_every_displayed_count_names_its_source(client):
    """Every row that shows a count also names the source of that count."""
    r = upload(
        client,
        ("run_summary.json", body(RUN_SUMMARY)),
        ("log.jsonl", body(LOG)),
        ("benchmark_results.csv", benchmark_results_csv()),
        ("benchmark_summary.json", body(BENCH_SUMMARY)),
    )
    assert rows(r), "nothing was accepted"
    for row in rows(r):
        if row["count"] is not None:
            assert row["count_source"], f"{row['filename']} shows a count with no source"
    assert row_for(r, "run_summary.json")["count_source"] == "counts.n_variants"
    assert row_for(r, "benchmark_summary.json")["count_source"] == "counts.pairs_total"


def test_a_run_summary_alone_is_a_usable_session(client):
    """Uploading only a run_summary.json, with no design log, leaves the session
    in a usable state rather than warning that something is missing."""
    r = upload(client, ("run_summary.json", body(RUN_SUMMARY)))
    assert payload(r)["usable"] is True


# =============================================================================
# Identification edge cases
# =============================================================================


def test_benchmark_jsonl_is_never_mistaken_for_a_design_log(client):
    """Uploading a benchmark_results.jsonl, whose records have `metrics` but no
    `physics`, is labeled `benchmark results` and is never labeled `design log`."""
    r = upload(client, ("benchmark_results.jsonl", benchmark_results_jsonl()))
    assert row_for(r, "benchmark_results.jsonl")["type"] == "benchmark results"


def test_truncated_first_line_still_identifies_a_design_log(client):
    """A log.jsonl whose first line is truncated mid-object but whose remaining
    lines are valid is still labeled `design log`, and the response reports that
    1 line was skipped."""
    valid = design_log(8)
    truncated = b'{"job_id": "petase-0000", "physi\n' + valid
    r = upload(client, ("log.jsonl", truncated))
    row = row_for(r, "log.jsonl")
    assert row["type"] == "design log"
    assert row["skipped_lines"] == 1
    assert row["count"] == 8


def test_malformed_line_is_skipped_and_counted_separately(client):
    """A log.jsonl with one malformed line among valid ones loads every valid
    record, reports the count of records loaded, and separately reports how many
    lines were skipped."""
    records = design_log_records()
    broken = as_jsonl(records[:4]) + b"{not json at all\n" + as_jsonl(records[4:])
    r = upload(client, ("log.jsonl", broken))
    row = row_for(r, "log.jsonl")
    assert row["count"] == 8
    assert row["skipped_lines"] == 1


def test_opposite_type_record_counts_as_skipped(client):
    """A log.jsonl containing one line that is a valid JSON object but carries
    `metrics` instead of `physics` loads the `physics` records and counts that
    line as skipped."""
    records = design_log_records()
    mixed = records[:4] + [{"job_id": "x", "metrics": {}}] + records[4:]
    r = upload(client, ("log.jsonl", as_jsonl(mixed)))
    row = row_for(r, "log.jsonl")
    assert row["count"] == 8
    assert row["skipped_lines"] == 1


def test_array_and_scalar_lines_are_skipped_not_counted(client):
    """A log.jsonl containing a line that is a valid JSON array and another that
    is a bare number counts both as skipped and neither as a record."""
    records = design_log_records()
    mixed = records[:4] + [[1, 2, 3], 42] + records[4:]
    r = upload(client, ("log.jsonl", as_jsonl(mixed)))
    row = row_for(r, "log.jsonl")
    assert row["count"] == 8
    assert row["skipped_lines"] == 2


def test_summaries_are_told_apart_by_which_count_key_they_hold(client):
    """A .json file whose `counts` object contains `pairs_total` is labeled
    `benchmark summary`, and the same file with `n_variants` instead is labeled
    `run summary`."""
    pairs = json.dumps({"counts": {"pairs_total": 3}}).encode()
    variants = json.dumps({"counts": {"n_variants": 8}}).encode()
    assert row_for(upload(client, ("a.json", pairs)), "a.json")["type"] == "benchmark summary"
    assert row_for(upload(client, ("b.json", variants)), "b.json")["type"] == "run summary"


@pytest.mark.parametrize("bad_value", ["eight", -3, True, None])
def test_unusable_count_value_still_recognizes_the_summary(client, bad_value):
    """A run_summary.json whose counts.n_variants is a string, a negative number,
    a boolean, or null is still recognized as `run summary`, displays
    `not recorded` for the count, and says the artifact's own value was unusable."""
    r = upload(client, ("run_summary.json", summary_with_count(bad_value)))
    row = row_for(r, "run_summary.json")
    assert row["type"] == "run summary"
    assert row["count"] is None
    assert row["count_display"] == "not recorded"
    assert any("unusable" in note.lower() for note in row["notes"])


def test_blank_lines_are_neither_records_nor_skips(client):
    """Blank lines in a .jsonl are not counted as records and are not counted as
    skipped lines."""
    records = design_log_records()
    padded = as_jsonl(records[:4]) + b"\n   \n" + as_jsonl(records[4:])
    r = upload(client, ("log.jsonl", padded))
    row = row_for(r, "log.jsonl")
    assert row["count"] == 8
    assert row["skipped_lines"] == 0


# =============================================================================
# Disagreement between artifacts
# =============================================================================


def test_count_disagreement_is_surfaced_with_both_numbers_and_sources(client):
    """When a run_summary.json and a log.jsonl are both loaded and the summary's
    counts.n_variants differs from the number of records in the log, both numbers
    are shown with their sources and the disagreement is stated."""
    r = upload(
        client,
        ("run_summary.json", summary_with_count(99)),
        ("log.jsonl", design_log(8)),
    )
    warnings = " ".join(payload(r)["warnings"])
    assert "99" in warnings and "8" in warnings
    assert "counts.n_variants" in warnings
    assert "disagree" in warnings.lower()


def test_agreeing_counts_produce_no_disagreement_warning(client):
    """When those two numbers agree, no disagreement is reported."""
    r = upload(
        client,
        ("run_summary.json", body(RUN_SUMMARY)),
        ("log.jsonl", design_log(8)),
    )
    warnings = " ".join(payload(r)["warnings"])
    assert "disagree" not in warnings.lower()


# =============================================================================
# Refusals
# =============================================================================


@pytest.mark.parametrize("name", ["notes.txt", "petase.pdb", "wt.fasta"])
def test_unrecognized_extension_is_refused_and_names_what_is_accepted(client, name):
    """Uploading a .txt, .pdb, or .fasta file shows `I don't recognize this file
    type` and names the three extensions that are accepted."""
    r = upload(client, (name, b"anything at all"))
    reason = refusal_for(r, name)["reason"]
    assert "I don't recognize this file type" in reason
    for ext in (".json", ".jsonl", ".csv"):
        assert ext in reason


def test_the_byte_limit_is_fifty_million_decimal(app):
    """The 50 MB boundary is decimal: 50,000,000 bytes."""
    assert app.config.get("MAX_ARTIFACT_BYTES") == 50_000_000


def test_file_one_byte_over_the_limit_is_refused_naming_the_limit(client, app):
    """Uploading a file over the limit is refused with a message naming the
    limit, and no record count is reported for it."""
    content = design_log(8)
    app.config["MAX_ARTIFACT_BYTES"] = len(content) - 1
    r = upload(client, ("log.jsonl", content))
    refusal = refusal_for(r, "log.jsonl")
    assert str(len(content) - 1) in refusal["reason"]
    assert refusal.get("count") is None


def test_file_exactly_at_the_limit_is_accepted(client, app):
    """Uploading a file of exactly the limit is accepted, because the limit is
    inclusive."""
    content = design_log(8)
    app.config["MAX_ARTIFACT_BYTES"] = len(content)
    r = upload(client, ("log.jsonl", content))
    assert row_for(r, "log.jsonl")["type"] == "design log"


def test_the_file_count_limit_is_twenty(app):
    """At most 20 files may be uploaded in one request."""
    assert app.config.get("MAX_ARTIFACT_FILES") == 20


def test_too_many_files_refuses_the_whole_request(client, app):
    """Uploading 21 files in one request is refused with a message naming the
    20-file limit, and none of the 21 is added."""
    app.config["MAX_ARTIFACT_FILES"] = 20
    files = [(f"log{i}.jsonl", design_log(1)) for i in range(21)]
    r = upload(client, *files)
    data = payload(r)
    assert data["artifacts"] == []
    assert data["error"] and "20" in data["error"]


def test_empty_file_is_refused_as_empty(client):
    """Uploading a 0-byte file is refused with a message saying the file is
    empty."""
    r = upload(client, ("log.jsonl", b""))
    assert "empty" in refusal_for(r, "log.jsonl")["reason"].lower()


def test_second_design_log_is_refused_and_the_first_survives(client):
    """A second design log is refused with a message saying one is already loaded
    and the session must be cleared first, and the first design log remains
    loaded."""
    upload(client, ("log.jsonl", design_log(8)))
    r = upload(client, ("other.jsonl", body(SEED43 / "log.jsonl")))
    reason = refusal_for(r, "other.jsonl")["reason"].lower()
    assert "already loaded" in reason
    assert "clear" in reason
    current = payload(client.get("/api/artifacts"))["artifacts"]
    assert [a["stored_name"] for a in current] == ["log.jsonl"]


def test_jsonl_without_physics_or_metrics_is_refused(client):
    """A .jsonl whose first parseable object has neither a `physics` nor a
    `metrics` key is refused with `This looks like JSONL but not a design log`."""
    r = upload(client, ("mystery.jsonl", as_jsonl([{"job_id": "x", "note": "hi"}])))
    assert "This looks like JSONL but not a design log" in refusal_for(r, "mystery.jsonl")["reason"]


def test_jsonl_with_no_parseable_object_is_refused(client):
    """A .jsonl in which no line at all parses as a JSON object is refused with a
    message saying no readable records were found."""
    r = upload(client, ("broken.jsonl", b"{oops\n[1,2]\nnope\n"))
    assert "no readable records" in refusal_for(r, "broken.jsonl")["reason"].lower()


def test_invalid_json_is_refused_without_a_500(client):
    """A .json file that is not valid JSON is refused with a message saying so,
    and the app does not return a 500."""
    r = upload(client, ("run_summary.json", b'{"counts": '))
    assert r.status_code == 200
    assert "json" in refusal_for(r, "run_summary.json")["reason"].lower()


@pytest.mark.parametrize("payload", [b"[1, 2, 3]", b"42"])
def test_json_that_is_not_an_object_is_refused(client, payload):
    """A .json file that parses but whose top level is an array or a number
    rather than an object is refused."""
    r = upload(client, ("summary.json", payload))
    assert refusal_for(r, "summary.json")["reason"]


@pytest.mark.parametrize(
    "payload",
    [b'{"generated_at": "now"}', b'{"counts": {"something_else": 3}}'],
)
def test_json_object_without_a_usable_counts_key_is_refused(client, payload):
    """A .json object with no `counts` key, or whose `counts` holds neither
    `n_variants` nor `pairs_total`, is refused with a message naming both keys it
    looked for."""
    r = upload(client, ("summary.json", payload))
    reason = refusal_for(r, "summary.json")["reason"]
    assert "n_variants" in reason and "pairs_total" in reason


@pytest.mark.parametrize("missing", ["job_id", "mutation_code", "seq_identity"])
def test_csv_missing_a_signature_column_is_refused_naming_it(client, missing):
    """A .csv whose header lacks any of `job_id`, `mutation_code`, or
    `seq_identity` is refused with a message naming the missing columns."""
    header = [c for c in ("job_id", "mutation_code", "seq_identity", "status") if c != missing]
    csv_bytes = (",".join(header) + "\n" + ",".join("x" for _ in header) + "\n").encode()
    r = upload(client, ("benchmark_results.csv", csv_bytes))
    assert missing in refusal_for(r, "benchmark_results.csv")["reason"]


def test_undecodable_bytes_are_refused_without_a_500(client):
    """A file with an accepted extension whose bytes are not valid UTF-8 is
    refused with a message saying it is not valid UTF-8 text, and the app does
    not return a 500."""
    r = upload(client, ("log.jsonl", b"\xff\xfe\x00\x81 not text at all"))
    assert r.status_code == 200
    assert "utf-8" in refusal_for(r, "log.jsonl")["reason"].lower()


# =============================================================================
# Session and safety
# =============================================================================


def test_traversal_filename_is_sanitized_into_the_session_directory(client, app):
    """A file whose name contains `../` is stored under a sanitized name inside
    the session's own directory, and no file is created anywhere outside that
    directory."""
    r = upload(client, ("../log.jsonl", design_log(8)))
    row = row_for(r, "../log.jsonl")
    assert ".." not in row["stored_name"]

    root = Path(app.config["ARTIFACT_ROOT"])
    stored = [p for p in root.rglob("*") if p.is_file()]
    assert stored, "nothing was written inside the session directory"
    outside = [p for p in root.parent.glob("*.jsonl") if p.is_file()]
    assert outside == [], f"files written outside the session directory: {outside}"


def test_same_sanitized_name_replaces_and_says_so(client):
    """Uploading a file whose sanitized name matches one already loaded replaces
    it, the row says it replaced an earlier upload, and the row shows the
    sanitized name."""
    upload(client, ("log.jsonl", design_log(8)))
    r = upload(client, ("log.jsonl", design_log(4)))
    row = row_for(r, "log.jsonl")
    assert row["replaced"] is True
    assert row["stored_name"] == "log.jsonl"
    assert row["count"] == 4


def test_traversal_name_collides_with_its_sanitized_twin(client):
    """Uploading ../log.jsonl when log.jsonl is already loaded is treated as a
    replacement, because the two sanitize to the same name."""
    upload(client, ("log.jsonl", design_log(8)))
    r = upload(client, ("../log.jsonl", design_log(4)))
    assert row_for(r, "../log.jsonl")["replaced"] is True
    current = payload(client.get("/api/artifacts"))["artifacts"]
    assert len(current) == 1


def test_a_refused_upload_keeps_the_existing_artifact(client):
    """An upload that is refused leaves any previously loaded artifact of the
    same name in place, and the row says the existing artifact was kept."""
    upload(client, ("log.jsonl", design_log(8)))
    r = upload(client, ("log.jsonl", b"{not json\n"))
    assert "kept" in refusal_for(r, "log.jsonl")["reason"].lower()
    current = payload(client.get("/api/artifacts"))["artifacts"]
    assert current[0]["count"] == 8


def test_the_empty_page_says_what_to_upload(client):
    """Before anything is uploaded, the page names the files to look for and
    shows no artifact list."""
    page = client.get("/").get_data(as_text=True)
    for name in ("log.jsonl", "run_summary.json"):
        assert name in page
    assert payload(client.get("/api/artifacts"))["artifacts"] == []


def test_clearing_empties_the_list_and_deletes_the_directory(client, app):
    """Clearing the session empties the artifact list and deletes the session's
    temporary directory from disk."""
    upload(client, ("log.jsonl", design_log(8)))
    root = Path(app.config["ARTIFACT_ROOT"])
    assert [p for p in root.rglob("*") if p.is_file()]

    assert client.post("/api/artifacts/clear").status_code == 200
    assert payload(client.get("/api/artifacts"))["artifacts"] == []
    assert [p for p in root.rglob("*") if p.is_file()] == []


def test_two_sessions_do_not_see_each_other(client, second_client):
    """Two browser sessions uploading different runs each see only their own
    artifacts."""
    upload(client, ("log.jsonl", design_log(8)))
    assert second_payload(client.get("/api/artifacts"))["artifacts"] == []

    upload(second_client, ("run_summary.json", body(RUN_SUMMARY)))
    mine = [a["type"] for a in payload(client.get("/api/artifacts"))["artifacts"]]
    theirs = [a["type"] for a in second_payload(client.get("/api/artifacts"))["artifacts"]]
    assert mine == ["design log"]
    assert theirs == ["run summary"]
