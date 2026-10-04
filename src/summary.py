"""Headline numbers for a loaded run. The server computes every value."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from src.artifacts import DESIGN_LOG, RUN_SUMMARY, store

EMPTY = {"present": False, "fields": [], "warnings": []}


def usable_number(value: Any) -> int | float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    return None


def _field(field_id: str, value: int | float | None, source: str, recomputed: bool) -> dict[str, Any]:
    return {
        "id": field_id,
        "value": value,
        "display": "not recorded" if value is None else str(value),
        "source": source if value is not None else "",
        "recomputed": recomputed,
    }


def _parse_log(raw: bytes) -> list[dict[str, Any]]:
    records = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "physics" in parsed:
            records.append(parsed)
    return records


def _from_log(records: list[dict[str, Any]]) -> dict[str, int | float | None]:
    composites = []
    structures = 0
    for record in records:
        physics = record.get("physics")
        if isinstance(physics, dict):
            composite = usable_number(physics.get("composite"))
            if composite is not None:
                composites.append(composite)
        pdb = record.get("structure_pdb")
        if isinstance(pdb, str) and pdb.strip():
            structures += 1
    return {
        "n_variants": len(records),
        "n_with_structure": structures,
        "best_composite": max(composites) if composites else None,
        "seconds_wall": None,
    }


def _from_summary(raw: bytes) -> dict[str, int | float | None]:
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "n_variants": None,
            "n_with_structure": None,
            "best_composite": None,
            "seconds_wall": None,
        }
    if not isinstance(doc, dict):
        return {
            "n_variants": None,
            "n_with_structure": None,
            "best_composite": None,
            "seconds_wall": None,
        }
    counts = doc.get("counts") if isinstance(doc.get("counts"), dict) else {}
    runtime = doc.get("runtime") if isinstance(doc.get("runtime"), dict) else {}
    top = doc.get("top_variants")
    composites = []
    if isinstance(top, list):
        for row in top:
            if isinstance(row, dict):
                value = usable_number(row.get("composite"))
                if value is not None:
                    composites.append(value)
    return {
        "n_variants": usable_number(counts.get("n_variants")),
        "n_with_structure": usable_number(counts.get("n_with_structure")),
        "best_composite": max(composites) if composites else None,
        "seconds_wall": usable_number(runtime.get("seconds_wall")),
    }


def build_summary(session_id: str, root: Path) -> dict[str, Any]:
    if not store.usable(session_id):
        return dict(EMPTY)

    summary_meta = store.find(session_id, RUN_SUMMARY)
    log_meta = store.find(session_id, DESIGN_LOG)
    summary_raw = (
        store.read_bytes(session_id, summary_meta.stored_name, root)
        if summary_meta
        else None
    )
    log_raw = (
        store.read_bytes(session_id, log_meta.stored_name, root) if log_meta else None
    )
    log_values = _from_log(_parse_log(log_raw)) if log_raw is not None else None
    summary_values = _from_summary(summary_raw) if summary_raw is not None else None

    sources = {
        "n_variants": (
            "run_summary.json → counts.n_variants",
            "log.jsonl → parsed records",
        ),
        "n_with_structure": (
            "run_summary.json → counts.n_with_structure",
            "log.jsonl → structure_pdb",
        ),
        "best_composite": (
            "run_summary.json → top_variants[].composite (maximum)",
            "log.jsonl → physics.composite (maximum)",
        ),
        "seconds_wall": (
            "run_summary.json → runtime.seconds_wall",
            "",
        ),
    }

    fields = []
    warnings: list[str] = []
    for field_id in ("n_variants", "n_with_structure", "best_composite", "seconds_wall"):
        if summary_values is not None:
            value = summary_values[field_id]
            recomputed = False
            source = sources[field_id][0]
            if log_values is not None:
                other = log_values[field_id]
                if value is not None and other is not None and value != other:
                    warnings.append(
                        f"The run summary and design log disagree on {field_id}: "
                        f"{value} ({sources[field_id][0]}) vs {other} ({sources[field_id][1]})."
                    )
        else:
            value = log_values[field_id] if log_values else None
            recomputed = value is not None
            source = sources[field_id][1]
        fields.append(_field(field_id, value, source, recomputed))

    return {"present": True, "fields": fields, "warnings": warnings}
