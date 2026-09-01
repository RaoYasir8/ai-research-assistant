from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.models import Claim, ResearchRun, Source


def set_run_stage(run_id: str, stage: str, progress: int, status: str = "running") -> None:
    with SessionLocal() as db:
        run = db.get(ResearchRun, run_id)
        if run is None:
            return
        run.stage = stage
        run.progress = progress
        run.status = status
        if run.started_at is None:
            run.started_at = datetime.now(UTC)
        db.commit()


def save_plan(run_id: str, plan: list[str]) -> None:
    with SessionLocal() as db:
        run = db.get(ResearchRun, run_id)
        if run:
            run.plan = plan
            db.commit()


def replace_sources(run_id: str, items: list[dict]) -> None:
    with SessionLocal() as db:
        db.execute(delete(Source).where(Source.run_id == run_id))
        for item in items:
            db.add(Source(run_id=run_id, **item))
        db.commit()


def replace_claims(run_id: str, items: list[dict]) -> None:
    with SessionLocal() as db:
        db.execute(delete(Claim).where(Claim.run_id == run_id))
        for item in items:
            db.add(Claim(run_id=run_id, **item))
        db.commit()


def complete_run(
    run_id: str, summary: str, report: str, warnings: list[str], model_name: str
) -> None:
    with SessionLocal() as db:
        run = db.get(ResearchRun, run_id)
        if not run:
            return
        run.summary = summary
        run.report_markdown = report
        run.warnings = warnings
        run.model_name = model_name
        run.status = "completed"
        run.stage = "completed"
        run.progress = 100
        run.completed_at = datetime.now(UTC)
        db.commit()


def fail_run(run_id: str, message: str) -> None:
    with SessionLocal() as db:
        run = db.get(ResearchRun, run_id)
        if not run:
            return
        run.status = "failed"
        run.stage = "failed"
        run.error_message = message[:2000]
        run.completed_at = datetime.now(UTC)
        db.commit()


def get_run_question(run_id: str) -> tuple[str, str, str] | None:
    with SessionLocal() as db:
        run = db.scalar(select(ResearchRun).where(ResearchRun.id == run_id))
        if not run:
            return None
        return run.question, run.depth, run.status
