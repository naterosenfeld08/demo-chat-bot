import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

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


@app.get("/")
def index():
    return render_template(
        "index.html",
        model=DEFAULT_MODEL,
        key_ready=bool(api_key()),
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
