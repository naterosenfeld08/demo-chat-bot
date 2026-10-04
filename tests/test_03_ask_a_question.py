"""Tests for specs/03-ask-a-question.md."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import design_log, payload, upload
from conftest import SEED42


def body(path: Path) -> bytes:
    return path.read_bytes()


def ask(client, question: str):
    return payload(
        client.post(
            "/api/ask",
            json={"question": question},
            content_type="application/json",
        )
    )


def test_variant_count_matches_the_summary_card(client):
    """Asking how many variants were in this run after loading the seed-42
    summary returns the same integer the summary card shows, and names
    run_summary.json → counts.n_variants."""
    upload(client, ("run_summary.json", body(SEED42 / "run_summary.json")))
    card = payload(client.get("/api/summary"))
    expected = next(f["value"] for f in card["fields"] if f["id"] == "n_variants")
    data = ask(client, "how many variants were in this run")
    assert str(expected) in data["answer"]
    assert expected == 8
    assert "run_summary.json" in data["answer"]
    assert "counts.n_variants" in data["answer"]
    assert data["facts"]["n_variants"] == expected


def test_best_composite_is_three_decimals_and_names_the_job(client):
    """Asking what was the best composite score after loading the seed-42 log
    returns 0.609 and the job_id of that variant (gen00002)."""
    upload(client, ("log.jsonl", body(SEED42 / "log.jsonl")))
    data = ask(client, "what was the best composite score")
    assert "0.609" in data["answer"]
    assert "gen00002" in data["answer"]
    assert data["facts"]["best_composite_display"] == "0.609"
    assert data["facts"]["job_id"] == "gen00002"


def test_best_composite_names_its_source(client):
    """That best-composite answer names the artifact and field the number came
    from."""
    upload(client, ("log.jsonl", body(SEED42 / "log.jsonl")))
    data = ask(client, "what was the best composite score")
    assert "log.jsonl" in data["answer"]
    assert "physics.composite" in data["answer"]


def test_gdt_question_is_unanswerable_without_a_benchmark_reader(client):
    """Asking what was the GDT-TS after loading only a design run returns
    the loaded run doesn't record that, names benchmark_results.csv, and facts
    is empty."""
    upload(client, ("log.jsonl", body(SEED42 / "log.jsonl")))
    data = ask(client, "what was the GDT-TS")
    assert "the loaded run doesn't record that" in data["answer"]
    assert "benchmark_results.csv" in data["answer"]
    assert data["facts"] == {}


def test_seconds_without_a_summary_is_unanswerable(client):
    """Asking how long did the run take with only a log loaded returns
    the loaded run doesn't record that, names run_summary.json, and facts is
    empty."""
    upload(client, ("log.jsonl", design_log(8)))
    data = ask(client, "how long did the run take")
    assert "the loaded run doesn't record that" in data["answer"]
    assert "run_summary.json" in data["answer"]
    assert data["facts"] == {}


def test_echo_stub_receives_the_computed_variant_count(client, app):
    """With LLM_MODE=echo, asking the variant-count question puts 8 in the
    echoed context."""
    app.config["LLM_MODE"] = "echo"
    upload(client, ("run_summary.json", body(SEED42 / "run_summary.json")))
    data = ask(client, "how many variants were in this run")
    assert data["echo"]
    echoed = json.loads(data["echo"])
    blob = json.dumps(echoed)
    assert "8" in blob


def test_question_before_upload_says_what_to_load(client):
    """Asking any question with nothing loaded says to upload log.jsonl or
    run_summary.json first and returns no fact."""
    data = ask(client, "how many variants were in this run")
    assert "log.jsonl" in data["answer"]
    assert "run_summary.json" in data["answer"]
    assert data["facts"] == {}
    assert data["intent"] == "need_upload"
