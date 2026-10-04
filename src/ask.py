"""Route a typed question to a server-computed statistic.

The language model never adds, averages, or ranks. It only sees a JSON block
this module already filled in.
"""

from __future__ import annotations

import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from src.artifacts import DESIGN_LOG, RUN_SUMMARY, store
from src.summary import _parse_log, build_summary, usable_number

UNANSWERABLE_PHRASE = "the loaded run doesn't record that"
NEED_UPLOAD = (
    "Upload a log.jsonl or run_summary.json first, then ask about that run."
)


def _round_three(value: float) -> str:
    quantized = Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return format(quantized, "f")


def _classify(question: str) -> str:
    text = question.lower()
    if "gdt" in text:
        return "unanswerable_gdt"
    if "how long" in text or "seconds" in text or "wall" in text:
        return "seconds_wall"
    if "composite" in text:
        return "best_composite"
    if "variant" in text:
        return "n_variants"
    return "unanswerable"


def _field_map(card: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in card.get("fields", [])}


def _best_from_log(records: list[dict[str, Any]]) -> tuple[float | None, str | None]:
    best: float | None = None
    job_id: str | None = None
    for record in records:
        physics = record.get("physics")
        if not isinstance(physics, dict):
            continue
        composite = usable_number(physics.get("composite"))
        if composite is None:
            continue
        if best is None or composite > best:
            best = composite
            raw_id = record.get("job_id")
            job_id = raw_id if isinstance(raw_id, str) and raw_id else None
    return best, job_id


def _best_from_summary(raw: bytes) -> tuple[float | None, str | None]:
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, None
    if not isinstance(doc, dict):
        return None, None
    top = doc.get("top_variants")
    if not isinstance(top, list):
        return None, None
    best: float | None = None
    job_id: str | None = None
    for row in top:
        if not isinstance(row, dict):
            continue
        composite = usable_number(row.get("composite"))
        if composite is None:
            continue
        if best is None or composite > best:
            best = composite
            raw_id = row.get("job_id")
            job_id = raw_id if isinstance(raw_id, str) and raw_id else None
    return best, job_id


def _best_composite_detail(
    session_id: str, root: Path
) -> tuple[float | None, str | None, str]:
    # Same winner as the summary card: the run summary, when it has a value.
    summary_meta = store.find(session_id, RUN_SUMMARY)
    if summary_meta:
        raw = store.read_bytes(session_id, summary_meta.stored_name, root)
        if raw is not None:
            value, job_id = _best_from_summary(raw)
            if value is not None:
                return value, job_id, "run_summary.json → top_variants[].composite"
    log_meta = store.find(session_id, DESIGN_LOG)
    if log_meta:
        raw = store.read_bytes(session_id, log_meta.stored_name, root)
        if raw is not None:
            value, job_id = _best_from_log(_parse_log(raw))
            if value is not None:
                return value, job_id, "log.jsonl → physics.composite"
    return None, None, ""


def _unanswerable(needed: str) -> dict[str, Any]:
    return {
        "answer": (
            f"{UNANSWERABLE_PHRASE}. "
            f"A {needed} would be needed to answer that."
        ),
        "intent": "unanswerable",
        "facts": {},
    }


def _stats_block(intent: str, facts: dict[str, Any]) -> dict[str, Any]:
    return {"intent": intent, "facts": facts}


def answer_question(
    session_id: str, root: Path, question: str, *, llm_mode: str
) -> dict[str, Any]:
    card = build_summary(session_id, root)
    if not card.get("present"):
        body = {
            "answer": NEED_UPLOAD,
            "intent": "need_upload",
            "facts": {},
        }
        return _with_echo(body, llm_mode)

    intent = _classify(question)
    fields = _field_map(card)

    if intent == "unanswerable_gdt":
        return _with_echo(_unanswerable("benchmark_results.csv"), llm_mode)
    if intent == "unanswerable":
        return _with_echo(_unanswerable("benchmark_results.csv"), llm_mode)

    if intent == "n_variants":
        field = fields.get("n_variants") or {}
        value = field.get("value")
        source = field.get("source") or "run_summary.json → counts.n_variants"
        if value is None:
            return _with_echo(_unanswerable("run_summary.json"), llm_mode)
        facts = {"n_variants": value, "source": source}
        body = {
            "answer": f"This run has {value} variants ({source}).",
            "intent": "n_variants",
            "facts": facts,
        }
        return _with_echo(body, llm_mode)

    if intent == "seconds_wall":
        field = fields.get("seconds_wall") or {}
        value = field.get("value")
        source = field.get("source") or "run_summary.json → runtime.seconds_wall"
        if value is None:
            return _with_echo(_unanswerable("run_summary.json"), llm_mode)
        facts = {"seconds_wall": value, "source": source}
        body = {
            "answer": f"The run took {value} seconds ({source}).",
            "intent": "seconds_wall",
            "facts": facts,
        }
        return _with_echo(body, llm_mode)

    value, job_id, source = _best_composite_detail(session_id, root)
    if value is None:
        return _with_echo(_unanswerable("log.jsonl"), llm_mode)
    display = _round_three(value)
    facts = {
        "best_composite": value,
        "best_composite_display": display,
        "job_id": job_id,
        "source": source,
    }
    job_bit = f" (job_id {job_id})" if job_id else ""
    body = {
        "answer": (
            f"The best physics.composite is {display}{job_bit} ({source})."
        ),
        "intent": "best_composite",
        "facts": facts,
    }
    return _with_echo(body, llm_mode)


def _with_echo(body: dict[str, Any], llm_mode: str) -> dict[str, Any]:
    if llm_mode == "echo":
        body["echo"] = json.dumps(_stats_block(body["intent"], body["facts"]))
    else:
        body["echo"] = None
    return body
