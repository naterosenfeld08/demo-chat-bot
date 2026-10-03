"""Identify and store uploaded PETase run artifacts.

Recognition uses content signatures from specs/01-load-a-run.md. Every count
names its source. Missing or unusable values display "not recorded".
"""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ACCEPTED_EXTENSIONS = (".json", ".jsonl", ".csv")
BENCHMARK_NOTE = "no feature uses this yet"
UNUSABLE_NOTE = "the artifact's own value was unusable"
DESIGN_LOG = "design log"
BENCHMARK_RESULTS = "benchmark results"
RUN_SUMMARY = "run summary"
BENCHMARK_SUMMARY = "benchmark summary"
SOURCE_N_VARIANTS = "counts.n_variants"
SOURCE_PAIRS_TOTAL = "counts.pairs_total"
SOURCE_JSONL = "parsed JSONL records"
SOURCE_CSV = "CSV data rows"


@dataclass
class Artifact:
    filename: str
    stored_name: str
    type: str
    count: int | None
    count_source: str | None
    lines_read: int | None = None
    skipped_lines: int | None = None
    notes: list[str] = field(default_factory=list)
    replaced: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "stored_name": self.stored_name,
            "type": self.type,
            "count": self.count,
            "count_display": "not recorded" if self.count is None else str(self.count),
            "count_source": self.count_source,
            "lines_read": self.lines_read,
            "skipped_lines": self.skipped_lines,
            "notes": list(self.notes),
            "replaced": self.replaced,
        }


@dataclass
class Refusal:
    filename: str
    reason: str
    count: None = None

    def as_dict(self) -> dict[str, Any]:
        return {"filename": self.filename, "reason": self.reason, "count": self.count}


class IdentifyError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def sanitize_filename(name: str) -> str:
    """Keep only the final path component so `../log.jsonl` stores as `log.jsonl`."""
    cleaned = name.replace("\\", "/")
    base = cleaned.split("/")[-1]
    base = base.replace("..", "")
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    return base or "upload"


def extension_of(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".jsonl"):
        return ".jsonl"
    if lower.endswith(".json"):
        return ".json"
    if lower.endswith(".csv"):
        return ".csv"
    suffix = Path(name).suffix.lower()
    return suffix


def usable_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 0:
        return None
    return value


def _first_parseable_object(lines: list[str]) -> dict[str, Any] | None:
    for line in lines:
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _jsonl_counts(lines: list[str], type_key: str) -> tuple[int, int]:
    records = 0
    skipped = 0
    for line in lines:
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if isinstance(parsed, dict) and type_key in parsed:
            records += 1
        else:
            skipped += 1
    return records, skipped


def identify(filename: str, raw: bytes) -> Artifact:
    ext = extension_of(filename)
    if ext not in ACCEPTED_EXTENSIONS:
        accepted = ", ".join(ACCEPTED_EXTENSIONS)
        raise IdentifyError(
            f"I don't recognize this file type. Accepted extensions are {accepted}."
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IdentifyError("This file is not valid UTF-8 text.") from exc

    stored_name = sanitize_filename(filename)
    if ext == ".jsonl":
        return _identify_jsonl(filename, stored_name, text)
    if ext == ".csv":
        return _identify_csv(filename, stored_name, text)
    return _identify_json(filename, stored_name, text)


def _identify_jsonl(filename: str, stored_name: str, text: str) -> Artifact:
    lines = text.splitlines()
    first = _first_parseable_object(lines)
    if first is None:
        raise IdentifyError("No readable records were found.")
    if "physics" in first:
        artifact_type = DESIGN_LOG
        type_key = "physics"
    elif "metrics" in first:
        artifact_type = BENCHMARK_RESULTS
        type_key = "metrics"
    else:
        raise IdentifyError("This looks like JSONL but not a design log.")
    records, skipped = _jsonl_counts(lines, type_key)
    notes = [BENCHMARK_NOTE] if artifact_type == BENCHMARK_RESULTS else []
    return Artifact(
        filename=filename,
        stored_name=stored_name,
        type=artifact_type,
        count=records,
        count_source=SOURCE_JSONL,
        lines_read=len(lines),
        skipped_lines=skipped,
        notes=notes,
    )


def _identify_csv(filename: str, stored_name: str, text: str) -> Artifact:
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise IdentifyError(
            "Header is missing job_id, mutation_code, and seq_identity."
        ) from exc
    required = ("job_id", "mutation_code", "seq_identity")
    missing = [name for name in required if name not in header]
    if missing:
        raise IdentifyError(
            "Header is missing " + ", ".join(missing) + "."
        )
    rows = list(reader)
    return Artifact(
        filename=filename,
        stored_name=stored_name,
        type=BENCHMARK_RESULTS,
        count=len(rows),
        count_source=SOURCE_CSV,
        notes=[BENCHMARK_NOTE],
    )


def _identify_json(filename: str, stored_name: str, text: str) -> Artifact:
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise IdentifyError("This file is not valid JSON.") from exc
    if not isinstance(doc, dict):
        raise IdentifyError("Top level must be a JSON object.")
    counts = doc.get("counts")
    if not isinstance(counts, dict) or (
        "n_variants" not in counts and "pairs_total" not in counts
    ):
        raise IdentifyError(
            "Looked for counts.n_variants or counts.pairs_total and found neither."
        )
    if "n_variants" in counts:
        artifact_type = RUN_SUMMARY
        source = SOURCE_N_VARIANTS
        value = usable_int(counts.get("n_variants"))
    else:
        artifact_type = BENCHMARK_SUMMARY
        source = SOURCE_PAIRS_TOTAL
        value = usable_int(counts.get("pairs_total"))
    notes: list[str] = []
    if artifact_type == BENCHMARK_SUMMARY:
        notes.append(BENCHMARK_NOTE)
    if value is None:
        notes.append(UNUSABLE_NOTE)
    return Artifact(
        filename=filename,
        stored_name=stored_name,
        type=artifact_type,
        count=value,
        count_source=source,
        notes=notes,
    )


class ArtifactStore:
    """In-memory session metadata plus files under ARTIFACT_ROOT / session_id."""

    def __init__(self) -> None:
        self._sessions: dict[str, list[Artifact]] = {}

    def list(self, session_id: str) -> list[Artifact]:
        return [self._copy(item) for item in self._sessions.get(session_id, [])]

    def usable(self, session_id: str) -> bool:
        return any(
            item.type in (DESIGN_LOG, RUN_SUMMARY)
            for item in self._sessions.get(session_id, [])
        )

    def warnings(self, session_id: str) -> list[str]:
        items = self._sessions.get(session_id, [])
        summary = next((item for item in items if item.type == RUN_SUMMARY), None)
        log = next((item for item in items if item.type == DESIGN_LOG), None)
        if summary is None or log is None:
            return []
        if summary.count is None or log.count is None:
            return []
        if summary.count == log.count:
            return []
        return [
            (
                f"The run summary and design log disagree on the variant count: "
                f"{summary.count} ({SOURCE_N_VARIANTS}) vs {log.count} ({SOURCE_JSONL})."
            )
        ]

    def has_design_log(self, session_id: str, stored_name: str) -> bool:
        return any(
            item.type == DESIGN_LOG and item.stored_name != stored_name
            for item in self._sessions.get(session_id, [])
        )

    def has_stored_name(self, session_id: str, stored_name: str) -> bool:
        return any(
            item.stored_name == stored_name
            for item in self._sessions.get(session_id, [])
        )

    def put(
        self,
        session_id: str,
        artifact: Artifact,
        raw: bytes,
        root: Path,
    ) -> Artifact:
        directory = root / session_id
        directory.mkdir(parents=True, exist_ok=True)
        (directory / artifact.stored_name).write_bytes(raw)
        items = self._sessions.setdefault(session_id, [])
        replaced = False
        kept: list[Artifact] = []
        for item in items:
            if item.stored_name == artifact.stored_name:
                replaced = True
            else:
                kept.append(item)
        artifact.replaced = replaced
        kept.append(artifact)
        self._sessions[session_id] = kept
        return self._copy(artifact)

    def clear(self, session_id: str, root: Path) -> None:
        self._sessions.pop(session_id, None)
        directory = root / session_id
        if directory.exists():
            shutil.rmtree(directory)

    def _copy(self, artifact: Artifact) -> Artifact:
        return Artifact(
            filename=artifact.filename,
            stored_name=artifact.stored_name,
            type=artifact.type,
            count=artifact.count,
            count_source=artifact.count_source,
            lines_read=artifact.lines_read,
            skipped_lines=artifact.skipped_lines,
            notes=list(artifact.notes),
            replaced=artifact.replaced,
        )


store = ArtifactStore()
