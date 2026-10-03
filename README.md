<!-- Course: this file IS your setup instructions. First drafted in Stage 1,
     rewritten in Stage 3 when a classmate has to run your app from it without
     asking you anything. See docs/course/DELIVERABLES.md -->

# demo-chat-bot

A browser chat app that talks to an AI model, with selectable response tones.

## What it does

You type a message, the app sends your conversation to the TensorX AI service,
and the reply appears in the page. A tone menu (Helpful, Tutor, Concise) changes
how the AI answers. "Clear chat" discards the current conversation.

The API key lives on the server, in a file that is never committed, so it is
never exposed to the browser.

## Screenshot

<!-- TODO: add one once feature #1 is built. -->

---

## Setup

### You will need

- Python 3.11 or newer
- A TensorX API key. Create one at
  [app.tensorx.ai/dashboard/keys](https://app.tensorx.ai/dashboard/keys).

### Steps

```bash
# 1. Get the code
git clone https://github.com/naterosenfeld08/demo-chat-bot.git
cd demo-chat-bot

# 2. Install what it needs
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Add your API key
cp .env.example .env
# then edit .env and set TENSORX_API_KEY=sk-...

# 4. Run it
python app.py
```

Then open <http://127.0.0.1:5000> in your browser.

On macOS, port 5000 is often taken by AirPlay Receiver. If that happens, run
`PORT=5050 python app.py` and open <http://127.0.0.1:5050> instead.

### Running the tests

```bash
pytest
```

Every test should pass. If one fails, that is the app telling you something is
broken. Read what it says before changing anything.

---

## Deploying to Render

| Field | Value |
| --- | --- |
| Language | Python |
| Root directory | *(leave blank)* |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| Instance type | Free ($0) |

Set `TENSORX_API_KEY` in the service's Environment settings, then deploy. See
[docs/deploying.md](docs/deploying.md).

---

## Project status

**Current version:** pre-alpha
**Working:** a single-session chat page with three tones, running locally
**Not working yet:** see [docs/backlog.md](docs/backlog.md)

## How this project is organized

| Where | What's in it |
|---|---|
| [`docs/proposal.md`](docs/proposal.md) | The problem this solves and who it's for |
| [`docs/backlog.md`](docs/backlog.md) | Every feature, in build order, with its acceptance criteria |
| [`specs/`](specs/) | One page per feature: what it does, what it doesn't, what "done" means |
| [`AGENTS.md`](AGENTS.md) | The rules every AI assistant must follow in this repo |
| `app.py` | The Flask server |
| `templates/` | The HTML pages |
| `tests/` | The automatic tests |
| [`CHANGELOG.md`](CHANGELOG.md) | What changed between versions |

## License

MIT. See [LICENSE](LICENSE).
