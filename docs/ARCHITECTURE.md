# Architecture

The application is split into six runtime services:

1. **Next.js web app** — user interface and a same-origin proxy for browser requests.
2. **FastAPI API** — authentication, research CRUD, validation and queue submission.
3. **Worker** — consumes Redis queue entries and runs the LangGraph workflow.
4. **PostgreSQL** — users, runs, sources, claims and final reports.
5. **Ollama** — local model runtime. The default model is `qwen3:1.7b`.
6. **SearXNG** — self-hosted metasearch endpoint used for keyless web discovery.

## Research graph

```text
Question
  |
  v
Planner
  |  search queries
  v
Researcher ----> SearXNG ----> public web pages
  |                  |
  |                  +---- snippets
  +---- safe fetch + article extraction
  |
  v
Fact checker
  |  claim/source links + deterministic lexical grounding check
  v
Writer
  |  validated [Sx] citations
  v
Saved Markdown report
```

LangGraph owns stage ordering and shared state. Database writes are explicit around each stage so the UI can show progress even while the worker is busy.

## Reliability choices

- The API does not run long research work inside an HTTP request.
- Redis queue entries contain only the run ID; durable state stays in PostgreSQL.
- A run can fail without losing its question or stage history.
- Planner and writer have deterministic/extractive fallbacks when the local model is unavailable.
- Search results are deduplicated by canonical URL, and fetched content is deduplicated by SHA-256 hash.
- Generated citations are rejected if they reference source IDs that were not collected.

## Browser security

The browser talks to the Next.js same-origin proxy. Access and refresh JWTs are HttpOnly cookies. Mutations additionally require a double-submit CSRF token. The backend does not expose auth tokens to browser JavaScript.
