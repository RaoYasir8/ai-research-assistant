# Acceptance checklist

Run these checks before calling a revision complete.

## Automated

```powershell
python scripts/check_no_paid_clients.py
docker build --target test -t ai-research-assistant-backend-test ./backend
docker run --rm ai-research-assistant-backend-test
docker build --target builder -t ai-research-assistant-frontend-check ./frontend
```

## Browser smoke test

1. Register a new user.
2. Sign out and sign back in.
3. Create a Standard research run.
4. Confirm the stage moves through planning, researching, fact checking and writing.
5. Confirm the completed run shows sources and a Markdown report.
6. Open at least two cited source links and confirm the report did not invent those URLs.
7. Download the Markdown report.
8. Refresh the browser and confirm the run remains in history.
9. Start a second run and confirm histories are independent.
10. Confirm `/api/v1/ready` reports database, Redis and Ollama ready.
