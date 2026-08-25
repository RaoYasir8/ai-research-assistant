# API surface

Base path: `/api/v1`

## System

- `GET /health`
- `GET /ready`

## Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

## Research

- `POST /research` — create and queue a research run.
- `GET /research` — list the current user's runs.
- `GET /research/stats` — dashboard counters.
- `GET /research/{run_id}` — full run, including sources and claims.
- `GET /research/{run_id}/report.md` — download the completed report.
- `DELETE /research/{run_id}` — delete a completed or failed run.

The browser normally reaches these endpoints through `/api/backend/...` on the Next.js app so authentication cookies remain same-origin from the browser's perspective.
