# Security notes

This repository includes a practical baseline for a portfolio deployment, not a claim of formal security certification.

## Included controls

- Argon2 password hashing through `pwdlib`.
- Short-lived access JWT and rotated refresh sessions stored server-side.
- HttpOnly authentication cookies plus double-submit CSRF protection.
- Rate limiting for registration, login and research creation using Redis.
- Security response headers and request IDs.
- Per-user ownership checks for every research run.
- Source fetcher rejects loopback, private, link-local, reserved and local hostnames.
- Redirect targets are revalidated to reduce SSRF risk.
- Page fetch size and timeout limits.
- Basic robots.txt respect before article fetching.
- HTML is converted to plain extracted text before it enters model context.
- Source text is explicitly framed as untrusted data in fact-checking and writing prompts to reduce prompt-injection risk.
- Overview and Key Findings blocks are rejected if substantive generated text lacks source citations.
- Final report citations must match collected source IDs.

## Before public internet exposure

- Set `APP_ENV=production` and `COOKIE_SECURE=true` behind HTTPS.
- Use unique high-entropy values for `SECRET_KEY`, database password and `SEARXNG_SECRET`.
- Put the app behind a reverse proxy with request/body limits and IP-level throttling.
- Do not expose PostgreSQL, Redis, Ollama or SearXNG directly to the internet.
- Review SearXNG engines for your jurisdiction and acceptable-use requirements.
- Patch base images and Python/Node dependencies on a regular schedule.
- Add backups for PostgreSQL if reports matter beyond a demo environment.
