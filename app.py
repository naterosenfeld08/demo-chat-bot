import os
import secrets
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from werkzeug.datastructures import FileStorage

from src.artifacts import (
    DESIGN_LOG,
    IdentifyError,
    identify,
    read_capped,
    sanitize_filename,
    store,
)

load_dotenv()

MULTIPART_OVERHEAD_BYTES = 1_000_000

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["MAX_ARTIFACT_BYTES"] = 50_000_000
app.config["MAX_ARTIFACT_FILES"] = 20
app.config["MAX_CONTENT_LENGTH"] = (
    app.config["MAX_ARTIFACT_BYTES"] * app.config["MAX_ARTIFACT_FILES"]
    + MULTIPART_OVERHEAD_BYTES
)
app.config["ARTIFACT_ROOT"] = tempfile.mkdtemp(prefix="petase-artifacts-")

API_URL = "https://api.tensorx.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("TENSORX_MODEL", "z-ai/glm-5.2")

TONES = {
    "helpful": "You are a helpful assistant.",
    "tutor": "You are a patient tutor. Explain ideas step by step, use a short example, and end by checking whether the explanation made sense.",
    "concise": "You are a concise assistant. Answer in a few short sentences and skip extra background.",
}


def api_key():
    key = os.environ.get("TENSORX_API_KEY", "").strip()
    if not key or key.startswith("paste-"):
        return ""
    return key


def session_id() -> str:
    if "sid" not in session:
        session["sid"] = secrets.token_hex(16)
    return session["sid"]


def session_payload(*, include_refused: bool, refused=None, error=None, accepted=None):
    sid = session_id()
    body = {
        "artifacts": [item.as_dict() for item in (accepted if accepted is not None else store.list(sid))],
        "warnings": store.warnings(sid),
        "usable": store.usable(sid),
    }
    if include_refused:
        body["refused"] = [item.as_dict() for item in (refused or [])]
        body["error"] = error
    return body


def _refuse(filename: str, reason: str, existing: bool) -> dict:
    if existing:
        reason = f"{reason} The existing artifact was kept."
    return {"filename": filename, "reason": reason, "count": None}


@app.errorhandler(413)
def request_too_large(_error):
    sid = session.get("sid")
    return jsonify(
        {
            "artifacts": [],
            "refused": [],
            "warnings": store.warnings(sid) if sid else [],
            "error": (
                "This request exceeds the upload size limit "
                f"({app.config['MAX_CONTENT_LENGTH']} bytes)."
            ),
            "usable": store.usable(sid) if sid else False,
        }
    )


@app.get("/")
def index():
    return render_template(
        "index.html",
        model=DEFAULT_MODEL,
        key_ready=bool(api_key()),
    )


@app.get("/api/artifacts")
def list_artifacts():
    return jsonify(session_payload(include_refused=False))


@app.post("/api/artifacts/clear")
def clear_artifacts():
    store.clear(session_id(), Path(app.config["ARTIFACT_ROOT"]))
    return jsonify(session_payload(include_refused=False))


@app.post("/api/artifacts")
def upload_artifacts():
    files: list[FileStorage] = request.files.getlist("files")
    max_files = int(app.config["MAX_ARTIFACT_FILES"])
    if len(files) > max_files:
        return jsonify(
            {
                "artifacts": [],
                "refused": [],
                "warnings": store.warnings(session_id()),
                "error": (
                    f"Too many files. This request has {len(files)}; "
                    f"the limit is {max_files}."
                ),
                "usable": store.usable(session_id()),
            }
        )

    sid = session_id()
    root = Path(app.config["ARTIFACT_ROOT"])
    limit = int(app.config["MAX_ARTIFACT_BYTES"])
    accepted = []
    refused = []

    for uploaded in files:
        original_name = uploaded.filename or "upload"
        stored_name = sanitize_filename(original_name)
        existed = store.has_stored_name(sid, stored_name)
        raw, oversize = read_capped(uploaded, limit)
        if oversize:
            refused.append(
                _refuse(
                    original_name,
                    f"File exceeds the {limit}-byte limit.",
                    existed,
                )
            )
            continue
        if raw == b"":
            refused.append(_refuse(original_name, "The file is empty.", existed))
            continue
        try:
            artifact = identify(original_name, raw)
        except IdentifyError as exc:
            refused.append(_refuse(original_name, exc.reason, existed))
            continue
        if artifact.type == DESIGN_LOG and store.has_design_log(sid, artifact.stored_name):
            refused.append(
                _refuse(
                    original_name,
                    "A design log is already loaded. Clear the session first.",
                    existed,
                )
            )
            continue
        accepted.append(store.put(sid, artifact, raw, root).as_dict())

    return jsonify(
        {
            "artifacts": accepted,
            "refused": refused,
            "warnings": store.warnings(sid),
            "error": None,
            "usable": store.usable(sid),
        }
    )


@app.post("/api/chat")
def chat():
    key = api_key()
    if not key:
        return jsonify(
            {
                "error": "Add your TensorX API key to the .env file as TENSORX_API_KEY, then restart the app."
            }
        ), 400

    data = request.get_json(silent=True) or {}
    messages = data.get("messages") or []
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "Send at least one message."}), 400

    cleaned = []
    for message in messages[-20:]:
        role = message.get("role")
        content = (message.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        cleaned.append({"role": role, "content": content[:8000]})
    if not cleaned or cleaned[-1]["role"] != "user":
        return jsonify({"error": "The last message must be from you."}), 400

    tone = data.get("tone") or "helpful"
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [{"role": "system", "content": TONES.get(tone, TONES["helpful"])}, *cleaned],
        "temperature": 0.7,
        "max_tokens": 1000,
    }
    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
    except requests.RequestException as exc:
        return jsonify({"error": f"Could not reach TensorX: {exc}"}), 502

    if not response.ok:
        detail = response.text.strip() or response.reason
        return jsonify({"error": f"TensorX returned {response.status_code}: {detail}"}), 502

    body = response.json()
    try:
        reply = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return jsonify({"error": "TensorX returned an unexpected response."}), 502

    return jsonify({"reply": reply, "model": body.get("model", DEFAULT_MODEL)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
