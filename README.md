# AI Research Assistant

A full-stack multi-agent research workspace built around a local model and self-hosted search. It plans a research question, gathers web evidence, checks claims against collected sources and produces a Markdown report with source IDs.

The project deliberately has **no paid AI or search API dependency**. Ollama runs the model locally and SearXNG supplies web discovery through a container in the same Docker network.

## What is included

- Next.js 16 App Router frontend
- FastAPI backend
- PostgreSQL persistence
- Redis-backed job queue
- LangGraph research workflow
- Ollama local inference (`qwen3:1.7b` by default)
- Self-hosted SearXNG search
- Safe article fetching + Trafilatura extraction
- Planner, researcher, fact-checker and writer stages
- URL/content deduplication
- Citation validation
- User accounts, research history and Markdown download
- Docker Compose
- Alembic migrations
- Backend tests, linting and GitHub Actions CI

## Repository layout

```text
ai-research-assistant/
├── backend/              FastAPI, worker, LangGraph and tests
├── frontend/             Next.js web app
├── infra/searxng/        search configuration
├── docs/                 architecture, API and security notes
├── scripts/              local project checks
├── .github/workflows/    CI
├── docker-compose.yml
└── .env.example
```

## Hardware guidance

The default `qwen3:1.7b` model is a compact local model. Ollama currently lists the quantized model at roughly 1.4 GB. A machine with **8 GB RAM can run the project for development**, while 16 GB or more is more comfortable when Docker, the browser and local inference are all active.

If your machine struggles, set `OLLAMA_MODEL=gemma3:1b` in `.env`, then pull that model instead.

---

# Run locally on Windows — step 1 to final

The cleanest path is Docker Desktop. You do not need to install Python, PostgreSQL, Redis or Ollama separately when using this route.

## Step 1 — install prerequisites

Install:

- Git
- Docker Desktop with Docker Compose

Then restart Windows if Docker asks you to.

## Step 2 — verify the tools

Open PowerShell and run:

```powershell
git --version
docker --version
docker compose version
```

All three commands must print versions.

## Step 3 — extract the project

Extract the ZIP to a simple path, for example:

```text
C:\Projects\ai-research-assistant
```

Open PowerShell in that folder:

```powershell
cd C:\Projects\ai-research-assistant
```

## Step 4 — create `.env`

```powershell
Copy-Item .env.example .env
```

## Step 5 — generate the application secret

If Python is available on your computer:

```powershell
python scripts\generate_secret.py
```

If Python is not installed, use PowerShell instead:

```powershell
$bytes = New-Object byte[] 64
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
[Convert]::ToBase64String($bytes)
```

Copy the generated value.

## Step 6 — edit `.env`

```powershell
notepad .env
```

Replace:

```env
SECRET_KEY=replace-with-a-long-random-secret
```

with your generated secret.

Also replace `SEARXNG_SECRET` with another random value. For a local-only first run, the default database credentials can remain unchanged.

Save and close Notepad.

## Step 7 — run the no-paid-client policy check

If Python is installed:

```powershell
python scripts\check_no_paid_clients.py
```

Expected:

```text
No paid-provider runtime client references found.
```

This check is also run in GitHub Actions.

## Step 8 — build the complete stack

Make sure Docker Desktop is running, then execute:

```powershell
docker compose up --build
```

The first build downloads container images, Python/Node dependencies and the local model. It is much heavier than later starts.

The stack starts:

```text
PostgreSQL
Redis
Ollama
qwen3:1.7b model pull
SearXNG
FastAPI backend
Research worker
Next.js frontend
```

Do not close this PowerShell window while you are testing the app.

## Step 9 — confirm containers are healthy

Open a second PowerShell window in the project folder:

```powershell
docker compose ps
```

`db`, `redis`, `ollama`, `backend`, `worker`, `frontend` and `searxng` should be running. `model-pull` is expected to exit successfully after the model download finishes.

## Step 10 — check backend health

Open:

```text
http://localhost:8000/api/v1/health
```

Expected:

```json
{"status":"ok","service":"ai-research-assistant-api"}
```

Then open:

```text
http://localhost:8000/api/v1/ready
```

When the model is ready, the response should show database, Redis and Ollama as ready.

## Step 11 — open the web app

Open:

```text
http://localhost:3000
```

Create an account.

## Step 12 — create your first research run

Go to **New research** and try a focused question such as:

```text
How has small-scale solar adoption affected electricity demand in Pakistan since 2022, and what evidence supports the trend?
```

Choose **Standard** depth and start the run.

## Step 13 — watch the agent pipeline

The run should move through:

```text
queued
planning
researching
fact checking
writing
completed
```

The page polls the backend while the worker is running.

## Step 14 — verify the report

On a completed run, check that you can see:

- the final Markdown report
- `[S1]`, `[S2]` style citations
- the source list and original URLs
- fact-check notes
- grounding scores
- any fallback warnings

Open two or three source links manually and make sure the cited URLs are real and relevant.

## Step 15 — download the report

Click **Download Markdown** on a completed run. The browser should download a `.md` file.

## Step 16 — persistence test

Refresh the page, then visit **Research history**. The completed run must still be present because it is stored in PostgreSQL.

## Step 17 — run backend QA

From the project root:

```powershell
docker build --target test -t ai-research-assistant-backend-test .\backend
docker run --rm ai-research-assistant-backend-test
```

This runs Ruff and Pytest.

## Step 18 — run the frontend production gate

```powershell
docker build --target builder -t ai-research-assistant-frontend-check .\frontend
```

This runs TypeScript type checking, ESLint and `next build`. Do not push the repo until this command passes.

## Step 19 — inspect logs if a research run fails

```powershell
docker compose logs --tail=200 backend
docker compose logs --tail=200 worker
docker compose logs --tail=200 ollama
docker compose logs --tail=200 searxng
```

The worker log is usually the most useful for agent-pipeline failures.

## Step 20 — stop the app safely

In the original terminal press `Ctrl + C`, then:

```powershell
docker compose down
```

This keeps database and model volumes.

Do **not** use `docker compose down -v` unless you intentionally want to delete saved research, Redis data and downloaded model files.

---

# Push to GitHub

Do this only after the browser smoke test and both QA builds pass.

## Step 21 — initialize Git

```powershell
git init
git branch -M main
git status
```

Confirm `.env` is not listed as a tracked file.

## Step 22 — create the first commit

```powershell
git add .
git status
git commit -m "feat: build AI Research Assistant"
```

Review `git status` before the commit. Never commit `.env`.

## Step 23 — create an empty GitHub repository

Create a repository named:

```text
ai-research-assistant
```

Do not initialize it with a README, `.gitignore` or license because this project already contains them.

## Step 24 — connect the remote

Replace `YOUR_USERNAME`:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/ai-research-assistant.git
git remote -v
```

## Step 25 — push

```powershell
git push -u origin main
```

## Step 26 — check GitHub Actions

Open the repository's **Actions** tab. The CI workflow checks:

- backend dependencies
- Ruff
- Pytest
- Python compilation
- frontend TypeScript
- ESLint
- Next.js production build
- no-paid-provider client policy

The project is ready for portfolio use when local smoke tests and CI are green.

---

# Deployment notes

This application is deployable as containers, but the local model needs real CPU/RAM. "No paid API" does not mean cloud compute is guaranteed to be free. The zero-cost path is to run the full stack on your own machine or a machine you already control.

For a public deployment, use HTTPS, `APP_ENV=production`, `COOKIE_SECURE=true`, unique production secrets and a reverse proxy. Do not expose Redis, PostgreSQL, Ollama or SearXNG directly.

See `docs/SECURITY.md`, `docs/ARCHITECTURE.md` and `docs/QA_CHECKLIST.md` before public exposure.
