# demo-chat-bot

A small Python web chat app for the CSCI-2521 demo. It talks to [TensorX](https://api.tensorx.ai/v1) and is set up to deploy on Render.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your key in `.env`:

```
TENSORX_API_KEY=sk-...
```

Create a key at [app.tensorx.ai/dashboard/keys](https://app.tensorx.ai/dashboard/keys), then start the app:

```bash
python app.py
```

Open http://127.0.0.1:5000

On macOS, port 5000 is often taken by AirPlay Receiver. If that happens, start with `PORT=5050 python app.py` and open http://127.0.0.1:5050.

The tone menu (Helpful, Tutor, Concise) changes the system prompt. Clear chat drops the current conversation.

## Render

| Field | Value |
| --- | --- |
| Language | Python |
| Root directory | *(leave blank)* |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Instance type | Free ($0) |

Add a secret file named `.env` with the same `TENSORX_API_KEY=...` line, then deploy.
