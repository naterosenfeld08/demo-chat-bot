"""Shared fixtures and builders for the test suite.

Artifact bodies are derived from the real pipeline output committed in `data/`
rather than hand-written, so a test can never pass against a shape the pipeline
does not actually emit. See `data/README.md` for how those files were produced.
"""

from __future__ import annotations

import copy
import io
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data"

SEED42 = DATA / "sample-run-seed42"
SEED43 = DATA / "sample-run-seed43"
BENCHMARK = DATA / "sample-benchmark"


# --- Reading the real fixtures -------------------------------------------------


def design_log_records() -> list[dict]:
    """The 8 real design-loop variant records from the seed 42 run."""
    lines = (SEED42 / "log.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def benchmark_records() -> list[dict]:
    """The 3 real structural benchmark pair records."""
    lines = (BENCHMARK / "benchmark_results.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def run_summary() -> dict:
    return json.loads((SEED42 / "run_summary.json").read_text(encoding="utf-8"))


def benchmark_summary() -> dict:
    return json.loads((BENCHMARK / "benchmark_summary.json").read_text(encoding="utf-8"))


# --- Building derived artifact bodies -----------------------------------------


def as_jsonl(records: list) -> bytes:
    """Serialize records one-per-line. Non-dict entries are written as-is, so a
    test can place a bare array or number on a line on purpose."""
    return ("".join(json.dumps(r) + "\n" for r in records)).encode("utf-8")


def design_log(n: int = 8) -> bytes:
    return as_jsonl(design_log_records()[:n])


def benchmark_results_jsonl() -> bytes:
    return (BENCHMARK / "benchmark_results.jsonl").read_bytes()


def benchmark_results_csv() -> bytes:
    return (BENCHMARK / "benchmark_results.csv").read_bytes()


def summary_with_count(value) -> bytes:
    """A real run_summary.json whose counts.n_variants is replaced."""
    doc = copy.deepcopy(run_summary())
    doc["counts"]["n_variants"] = value
    return json.dumps(doc).encode("utf-8")


# --- The app and its client ---------------------------------------------------


@pytest.fixture
def app(tmp_path):
    from app import app as flask_app

    flask_app.config.update(TESTING=True, ARTIFACT_ROOT=str(tmp_path / "artifacts"))
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def second_client(app):
    """A second, independent browser session against the same app."""
    return app.test_client()


# --- Uploading ----------------------------------------------------------------


def upload(client, *files: tuple[str, bytes]):
    """POST one or more (filename, body) pairs as a multipart upload."""
    payload = [(io.BytesIO(body), name) for name, body in files]
    return client.post(
        "/api/artifacts",
        data={"files": payload},
        content_type="multipart/form-data",
    )


def payload(response) -> dict:
    """The JSON body, with a readable failure when the endpoint isn't there yet."""
    assert response.status_code == 200, (
        f"expected 200 with a JSON body, got {response.status_code}. "
        "An unimplemented endpoint shows up here as a 404 or 405."
    )
    data = response.get_json(silent=True)
    assert isinstance(data, dict), f"expected a JSON object body, got {data!r}"
    return data


def rows(response) -> list[dict]:
    data = payload(response)
    assert "artifacts" in data, f"response has no 'artifacts' key: {sorted(data)}"
    return data["artifacts"]


def refusals(response) -> list[dict]:
    data = payload(response)
    assert "refused" in data, f"response has no 'refused' key: {sorted(data)}"
    return data["refused"]


def row_for(response, filename: str) -> dict:
    """The accepted artifact row for a given uploaded filename."""
    matches = [r for r in rows(response) if r["filename"] == filename]
    assert matches, f"{filename!r} was not accepted; refused: {refusals(response)}"
    return matches[0]


def refusal_for(response, filename: str) -> dict:
    matches = [r for r in refusals(response) if r["filename"] == filename]
    assert matches, f"{filename!r} was not refused; accepted: {rows(response)}"
    return matches[0]
