# QA report

## Package status

The source package passed the static and dependency-free checks that can be executed in this workspace.

### Passed here

- Python syntax compilation for `backend/app` and backend tests.
- Pure evidence-domain Pytest suite: 3 tests passed.
- Canonical URL cleanup, lexical grounding and citation validation smoke checks.
- TypeScript/TSX syntax transpilation across the frontend.
- Frontend local import resolution audit.
- Backend local import resolution audit.
- `docker-compose.yml`, GitHub Actions YAML and SearXNG settings YAML parsing.
- Frontend JSON configuration parsing.
- Paid-provider runtime-client scan.
- Required project file inventory.

## Environment boundary

The current build environment does not provide a Docker daemon and cannot resolve public package registries, so the following gates could not be executed here:

- Docker image builds.
- Python dependency installation from PyPI.
- Full backend Ruff + Pytest suite inside the container image.
- `npm install`.
- Next.js typecheck/lint/production build with project dependencies.
- Live PostgreSQL, Redis, SearXNG and Ollama integration.
- Browser end-to-end research run.

Those checks are intentionally included in the repository's Docker targets, README runbook and GitHub Actions workflow. Treat them as mandatory before portfolio publication.

## Mandatory local acceptance

Run:

```powershell
docker compose up --build
```

Then complete the browser smoke test in `docs/QA_CHECKLIST.md` and run:

```powershell
docker build --target test -t ai-research-assistant-backend-test .\backend
docker run --rm ai-research-assistant-backend-test
docker build --target builder -t ai-research-assistant-frontend-check .\frontend
```

Only push the portfolio revision after those commands are green.
