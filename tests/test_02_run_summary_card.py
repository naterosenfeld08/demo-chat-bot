"""Tests for specs/02-run-summary-card.md.

One test per acceptance criterion, in the spec's own order. Each docstring
quotes the criterion it covers. GET /api/summary is the contract in that spec.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from conftest import (
    as_jsonl,
    benchmark_results_csv,
    design_log,
    design_log_records,
    payload,
    run_summary,
    summary_with_count,
    upload,
)
from conftest import BENCHMARK, SEED42

BEST_FROM_SUMMARY = max(v["composite"] for v in run_summary()["top_variants"])
BEST_FROM_LOG = max(r["physics"]["composite"] for r in design_log_records())
SECONDS_WALL = run_summary()["runtime"]["seconds_wall"]


def body(path: Path) -> bytes:
    return path.read_bytes()


def card(client):
    return payload(client.get("/api/summary"))


def field(client, field_id: str) -> dict:
    fields = {item["id"]: item for item in card(client)["fields"]}
    assert field_id in fields, f"missing {field_id} in {sorted(fields)}"
    return fields[field_id]


def summary_bytes(**patches) -> bytes:
    doc = copy.deepcopy(run_summary())
    for key, value in patches.items():
        if key == "counts":
            doc["counts"].update(value)
        elif key == "runtime":
            if value is None:
                doc.pop("runtime", None)
            else:
                doc.setdefault("runtime", {}).update(value)
        else:
            doc[key] = value
    return json.dumps(doc).encode("utf-8")


def test_empty_session_has_no_card_numbers(client):
    """With nothing loaded, GET /api/summary returns present false and no fields,
    and the page has an element #run-summary-card that does not show any of the
    four numbers."""
    data = card(client)
    assert data["present"] is False
    assert data["fields"] == []
    page = client.get("/").get_data(as_text=True)
    assert 'id="run-summary-card"' in page
    for number in ("0.6085333333333334", "0.003"):
        assert number not in page


def test_summary_card_shows_variant_count_from_the_file(client):
    """Uploading the seed-42 run_summary.json makes the card present, with
    variant count 8 sourced from run_summary.json → counts.n_variants."""
    upload(client, ("run_summary.json", body(SEED42 / "run_summary.json")))
    data = card(client)
    assert data["present"] is True
    row = field(client, "n_variants")
    assert row["value"] == 8
    assert row["display"] == "8"
    assert row["source"] == "run_summary.json → counts.n_variants"
    assert row["recomputed"] is False


def test_recorded_zero_structures_display_as_zero(client):
    """That same card shows structures 0 sourced from run_summary.json →
    counts.n_with_structure, and the display is 0, not not recorded."""
    upload(client, ("run_summary.json", body(SEED42 / "run_summary.json")))
    row = field(client, "n_with_structure")
    assert row["value"] == 0
    assert row["display"] == "0"
    assert row["source"] == "run_summary.json → counts.n_with_structure"
    assert row["recomputed"] is False


def test_best_composite_equals_the_summary_maximum(client):
    """That same card shows best composite equal to the maximum
    top_variants[].composite in the file and names that source."""
    upload(client, ("run_summary.json", body(SEED42 / "run_summary.json")))
    row = field(client, "best_composite")
    assert row["value"] == BEST_FROM_SUMMARY
    assert row["display"] == str(BEST_FROM_SUMMARY)
    assert row["source"] == "run_summary.json → top_variants[].composite (maximum)"
    assert row["recomputed"] is False


def test_wall_clock_seconds_come_from_the_summary(client):
    """That same card shows wall-clock seconds 0.003 sourced from
    run_summary.json → runtime.seconds_wall."""
    upload(client, ("run_summary.json", body(SEED42 / "run_summary.json")))
    row = field(client, "seconds_wall")
    assert row["value"] == SECONDS_WALL
    assert row["display"] == str(SECONDS_WALL)
    assert row["source"] == "run_summary.json → runtime.seconds_wall"
    assert row["recomputed"] is False


def test_summary_plus_log_still_uses_the_summary_values(client):
    """Uploading the seed-42 summary and log together still shows those four
    summary values, none marked recomputed."""
    upload(
        client,
        ("run_summary.json", body(SEED42 / "run_summary.json")),
        ("log.jsonl", body(SEED42 / "log.jsonl")),
    )
    assert card(client)["present"] is True
    for field_id in ("n_variants", "n_with_structure", "best_composite", "seconds_wall"):
        assert field(client, field_id)["recomputed"] is False
    assert field(client, "n_variants")["value"] == 8
    assert field(client, "n_with_structure")["value"] == 0
    assert field(client, "best_composite")["value"] == BEST_FROM_SUMMARY
    assert field(client, "seconds_wall")["value"] == SECONDS_WALL


def test_log_only_recomputes_the_variant_count(client):
    """Uploading only the seed-42 log.jsonl makes the card present, with variant
    count 8 marked recomputed and sourced from the log."""
    upload(client, ("log.jsonl", body(SEED42 / "log.jsonl")))
    row = field(client, "n_variants")
    assert card(client)["present"] is True
    assert row["value"] == 8
    assert row["recomputed"] is True
    assert "log.jsonl" in row["source"]


def test_log_only_recomputes_structures_and_best_composite(client):
    """That log-only card shows structures 0 marked recomputed and best composite
    equal to the maximum physics.composite in the log, marked recomputed."""
    upload(client, ("log.jsonl", body(SEED42 / "log.jsonl")))
    structures = field(client, "n_with_structure")
    assert structures["value"] == 0
    assert structures["display"] == "0"
    assert structures["recomputed"] is True
    best = field(client, "best_composite")
    assert best["value"] == BEST_FROM_LOG
    assert best["recomputed"] is True
    assert "physics.composite" in best["source"]


def test_log_only_seconds_are_not_recorded(client):
    """That log-only card shows wall-clock seconds as not recorded, with value
    null."""
    upload(client, ("log.jsonl", body(SEED42 / "log.jsonl")))
    row = field(client, "seconds_wall")
    assert row["value"] is None
    assert row["display"] == "not recorded"
    assert row["recomputed"] is False


def test_benchmark_only_does_not_present_a_card(client):
    """Uploading only benchmark artifacts does not make the card present."""
    upload(
        client,
        ("benchmark_results.csv", benchmark_results_csv()),
        ("benchmark_summary.json", body(BENCHMARK / "benchmark_summary.json")),
    )
    data = card(client)
    assert data["present"] is False
    assert data["fields"] == []


def test_unusable_variant_count_is_not_recorded(client):
    """A summary whose counts.n_variants is missing or not a usable number shows
    not recorded for variants, not 0."""
    doc = copy.deepcopy(run_summary())
    del doc["counts"]["n_variants"]
    # Keep the file recognizable: counts still has n_variants? Wait, identification
    # requires n_variants to be present. Use an unusable value instead.
    upload(client, ("run_summary.json", summary_with_count(None)))
    row = field(client, "n_variants")
    assert row["value"] is None
    assert row["display"] == "not recorded"


def test_missing_runtime_is_not_recorded(client):
    """A summary whose runtime object is missing shows not recorded for seconds."""
    upload(client, ("run_summary.json", summary_bytes(runtime=None)))
    row = field(client, "seconds_wall")
    assert row["value"] is None
    assert row["display"] == "not recorded"


def test_missing_composites_are_not_recorded(client):
    """A summary with no top_variants, or none with a usable composite, shows
    not recorded for best composite."""
    upload(client, ("run_summary.json", summary_bytes(top_variants=[])))
    row = field(client, "best_composite")
    assert row["value"] is None
    assert row["display"] == "not recorded"


def test_variant_count_disagreement_keeps_the_summary_and_warns(client):
    """A summary that says 8 variants next to a log of 4 records keeps 8 on the
    card and warns, naming both numbers and both sources."""
    upload(
        client,
        ("run_summary.json", body(SEED42 / "run_summary.json")),
        ("log.jsonl", design_log(4)),
    )
    assert field(client, "n_variants")["value"] == 8
    warnings = " ".join(card(client)["warnings"])
    assert "8" in warnings and "4" in warnings
    assert "counts.n_variants" in warnings
    assert "disagree" in warnings.lower()


def test_composite_disagreement_keeps_the_summary_and_warns(client):
    """A summary whose best composite disagrees with the log's maximum keeps the
    summary value and warns, naming both numbers."""
    records = design_log_records()
    records[0]["physics"]["composite"] = 9.5
    upload(
        client,
        ("run_summary.json", body(SEED42 / "run_summary.json")),
        ("log.jsonl", as_jsonl(records)),
    )
    assert field(client, "best_composite")["value"] == BEST_FROM_SUMMARY
    warnings = " ".join(card(client)["warnings"])
    assert "9.5" in warnings
    assert str(BEST_FROM_SUMMARY) in warnings
    assert "disagree" in warnings.lower()


def test_clearing_hides_the_card(client):
    """Clearing the session makes the card not present again."""
    upload(client, ("run_summary.json", body(SEED42 / "run_summary.json")))
    assert card(client)["present"] is True
    assert client.post("/api/artifacts/clear").status_code == 200
    data = card(client)
    assert data["present"] is False
    assert data["fields"] == []


def test_two_sessions_see_their_own_cards(client, second_client):
    """Two sessions each see only their own card."""
    upload(client, ("run_summary.json", body(SEED42 / "run_summary.json")))
    upload(second_client, ("log.jsonl", design_log(4)))
    assert field(client, "n_variants")["value"] == 8
    assert field(client, "n_variants")["recomputed"] is False
    assert field(second_client, "n_variants")["value"] == 4
    assert field(second_client, "n_variants")["recomputed"] is True
