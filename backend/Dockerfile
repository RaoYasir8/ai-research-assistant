FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY . .
RUN chmod +x /app/docker-entrypoint.sh && chown -R app:app /app

FROM base AS test
RUN pip install --no-cache-dir '.[dev]'
USER app
CMD ["sh", "-c", "ruff check app tests && pytest"]

FROM base AS runtime
USER app
EXPOSE 8000
CMD ["/app/docker-entrypoint.sh"]
