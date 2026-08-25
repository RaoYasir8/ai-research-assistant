from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.services.ollama import ollama

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "ai-research-assistant-api"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    checks = {"database": False, "redis": False, "ollama": False}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    try:
        checks["redis"] = bool(Redis.from_url(settings.redis_url).ping())
    except Exception:
        pass
    checks["ollama"] = ollama.is_ready()
    if not all(checks.values()):
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks, "model": settings.ollama_model}
