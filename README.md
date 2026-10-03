<!-- Course: this file IS your setup instructions. First drafted in Stage 1,
     rewritten in Stage 3 when a classmate has to run your app from it without
     asking you anything. See docs/course/DELIVERABLES.md -->

# PETase Run Analyst

Ask questions in plain English about the run logs from a protein thermostability
pipeline, and get answers computed from the data with the right scientific
caveats attached.

## What it does

The [petase-thermostability-benchmark](https://github.com/naterosenfeld08/petase-thermostability-benchmark)
pipeline runs an in-silico design loop over PETase variants and writes a
`log.jsonl` with one record per variant plus a `run_summary.json` beside it.
Those files hold the real results, but asking anything of them means writing a
throwaway pandas script that gets closed with the terminal window.

This app takes those artifacts and lets you ask instead. Upload a run, and you
get headline numbers, a comparison against another run, and answers to typed
questions like "what was the best composite score." **Every number is computed by
the server in Python, never by the AI model** — the model's only job is choosing
which statistic answers your question and explaining it in prose. Answers carry
the interpretation caveats from the pipeline's own
[limitations doc](https://github.com/naterosenfeld08/petase-thermostability-benchmark/blob/main/docs/LIMITATIONS_AND_PRIORS.md),
so a proxy score never gets quoted as if it were a measured melting temperature.

See [docs/proposal.md](docs/proposal.md) for the problem this solves and
[docs/backlog.md](docs/backlog.md) for the features in build order.

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
**Working:** the chat page and server this is built on — you can type a message
and get an AI reply, with three selectable tones
**Not working yet:** everything that reads a run artifact. Feature #1 is upload
and recognition; see [docs/backlog.md](docs/backlog.md)

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
