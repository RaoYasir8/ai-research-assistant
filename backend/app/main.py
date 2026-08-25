import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, research, system
from app.config import settings
from app.middleware import RequestContextMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(
    title="AI Research Assistant API",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
)
app.include_router(system.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(research.router, prefix="/api/v1")
