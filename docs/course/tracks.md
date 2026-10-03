# Pick a track

This decides your language, how your tests run, and where your app is hosted.
Pick in week 3 and write it into `AGENTS.md` section 1 and `docs/proposal.md` section 3.

There is one main track, **web-app**, and one escape hatch, **other**. Almost
every project takes web-app. The specs, backlog, routine, and every graded
document are identical either way; only `src/`, `tests/`, and hosting differ.

---

## Web app: the default project type

**A real web application. A Python server, a hosted database, and pages people
open in a browser.**

Choose this for anything a person opens and uses: a tracker, a tool, a game, a
visualizer, a quiz, a calculator, a dashboard. It works on a phone, it can
remember data between visits, and it can keep a secret, so it is the right home
for an API key or for logins.

| | |
|---|---|
| Language | Python 3 (FastAPI on uvicorn) for the server; HTML, CSS, JavaScript for the pages |
| Entry point | `main.py` (the FastAPI app object) |
| Code | `src/*.py` for the server; `src/static/` for pages, styles, and scripts |
| Tests | `pytest` and [Playwright](https://playwright.dev/python/), driving a real browser against your running server |
| Run the app | `uvicorn main:app --reload`, then visit `localhost:8000` |
| Run the tests | `pytest` |
| Hosting | [Render](https://render.com) as a web service; GitHub Actions runs the tests |
| Database | [Neon](https://neon.com) hosted Postgres, reached through a `DATABASE_URL` connection string |
| Storage | The Neon database for anything that must persist; files in `data/` for the rest |
| Secrets | `.env` locally (git-ignored); environment variables on Render |

Setup:

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install fastapi "uvicorn[standard]" "psycopg[binary]" pytest pytest-playwright
playwright install chromium
```

Note: `requirements.txt` is the full list of all external python packages/tools that need to be installed. AI agents know to maintain this, but if you ever get a "package not found" or similar error, the package might be missing from this file.

**How this web app works.** The browser asks your FastAPI server for a web page.
The server does the real work: it reads and writes the Neon database, and it holds
any secret. The browser never sees a key. The visible web pages will mostly live in
HTML, CSS, and JavaScript files, while the server code that does the backend work like handling the database, secrets, and API calls, will be written in python.

**Why no "frontend framework".** More advanced projects will have more complicated
code to build and display the actual web pages. One of the most common tools for this is "React'. 
You might end up using this for your project, but it adds a little bit of complexity, 
so we're not starting out with it.

**A server can keep a secret.** Unlike a static web page, your own server can
hold an API key or a database password out of sight. Put it in `.env` for local
work and in Render's environment settings once deployed. A safety reminder: Never commit `.env` to your github project, and
never paste an API key into a page. See [`../deploying.md`](../deploying.md).

**Tests drive a real browser.** The "Playwright" tool that your package will use
allows coding agents to actually start your server, open the pages that a 
user would, and click through them to make sure they are working right.
The `pytest` package mentioned above manages directly testing the Python code behind
the web pages.

---

## Other project types

Anything else: a desktop app, a browser extension, a phone app, a different
language, or a project with no screen at all. Talk to the instructor first, not
for permission, but so you don't discover a wall in week 11.

Whatever you choose must supply four things, because the grading depends on them:

| | Why |
|---|---|
| **One command that runs the app** | Goes in your README. A stranger types it. |
| **One command that runs every test** | The routine and the sabotage demo both need it. |
| **Tests that can fail out loud** | If a break can't turn something red, it isn't a test. |
| **A way a peer can try it in Stage 3** | A URL, or setup steps they follow alone. |

Write all four into `AGENTS.md` section 5 so every assistant knows them.

---

## Not sure?

| If your project... | Track |
|---|---|
| is something people open in a browser | **web-app** |
| needs to work on a phone | **web-app** |
| crunches a spreadsheet or dataset | **web-app** |
| calls an API that needs a secret key | **web-app** |
| must remember data between visits | **web-app** (use Neon) |
| has no screen at all | **other**: talk to the instructor |
| is none of the above | **other**: talk to the instructor |
