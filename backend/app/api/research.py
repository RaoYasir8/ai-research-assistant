from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_csrf
from app.config import settings
from app.db import get_db
from app.models import ResearchRun, Source, User
from app.rate_limit import enforce_rate_limit
from app.schemas import ResearchCreate, ResearchListItem, ResearchRunOut, StatsOut

router = APIRouter(prefix="/research", tags=["research"])
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


def _owned_run(db: Session, run_id: str, user_id: str) -> ResearchRun:
    stmt = (
        select(ResearchRun)
        .options(selectinload(ResearchRun.sources), selectinload(ResearchRun.claims))
        .where(ResearchRun.id == run_id, ResearchRun.user_id == user_id)
    )
    run = db.scalar(stmt)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


@router.post(
    "",
    response_model=ResearchRunOut,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_csrf)],
)
def create_research(
    payload: ResearchCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    enforce_rate_limit(request, "research-create", limit=8, window_seconds=60)
    run = ResearchRun(user_id=user.id, question=payload.question, depth=payload.depth)
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        redis_client.xadd(
            settings.research_queue, {"run_id": run.id}, maxlen=10000, approximate=True
        )
    except Exception as exc:
        run.status = "failed"
        run.stage = "failed"
        run.error_message = "Queue service is unavailable"
        db.commit()
        raise HTTPException(status_code=503, detail="Research queue is unavailable") from exc
    return _owned_run(db, run.id, user.id)


@router.get("", response_model=list[ResearchListItem])
def list_research(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    stmt = (
        select(ResearchRun)
        .where(ResearchRun.user_id == user.id)
        .order_by(ResearchRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    base = ResearchRun.user_id == user.id
    total = db.scalar(select(func.count()).select_from(ResearchRun).where(base)) or 0
    completed = (
        db.scalar(
            select(func.count())
            .select_from(ResearchRun)
            .where(base, ResearchRun.status == "completed")
        )
        or 0
    )
    failed = (
        db.scalar(
            select(func.count())
            .select_from(ResearchRun)
            .where(base, ResearchRun.status == "failed")
        )
        or 0
    )
    total_sources = (
        db.scalar(
            select(func.count())
            .select_from(Source)
            .join(ResearchRun)
            .where(ResearchRun.user_id == user.id)
        )
        or 0
    )
    return StatsOut(
        total_runs=total, completed_runs=completed, failed_runs=failed, total_sources=total_sources
    )


@router.get("/{run_id}", response_model=ResearchRunOut)
def get_research(
    run_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return _owned_run(db, run_id, user.id)


@router.get("/{run_id}/report.md")
def download_report(
    run_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    run = _owned_run(db, run_id, user.id)
    if not run.report_markdown:
        raise HTTPException(status_code=409, detail="Report is not ready")
    safe_name = f"research-{run.id[:8]}.md"
    return Response(
        run.report_markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.delete(
    "/{run_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)]
)
def delete_research(
    run_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    run = _owned_run(db, run_id, user.id)
    if run.status in {"queued", "running"}:
        raise HTTPException(status_code=409, detail="A running research job cannot be deleted")
    db.delete(run)
    db.commit()
    return Response(status_code=204)
