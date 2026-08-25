# Version notes

The initial package was assembled against current upstream interfaces checked in August 2026.

- FastAPI: `0.141.1`
- SQLAlchemy: `2.0.52`
- LangGraph: `1.2.11`
- redis-py: `8.1.0`
- Next.js: `16.3.0`
- Ollama container: `0.32.13`
- Default local model: `qwen3:1.7b`
- SearXNG container: `2026.8.20-8d3dd0cd4`

Before a long-lived public deployment, update dependencies deliberately and re-run the full acceptance suite instead of changing versions ad hoc.
