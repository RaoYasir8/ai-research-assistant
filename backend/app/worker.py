from __future__ import annotations

import logging
import os
import signal
import socket
import sys
import time

from redis import Redis
from redis.exceptions import ResponseError

from app.config import settings
from app.services.repository import fail_run, get_run_question
from app.services.research_graph import run_research

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("research.worker")
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
RUNNING = True
CONSUMER = f"{socket.gethostname()}-{os.getpid()}"


def stop_worker(*_args) -> None:
    global RUNNING
    RUNNING = False


def ensure_group() -> None:
    try:
        redis_client.xgroup_create(
            settings.research_queue, settings.worker_group, id="0", mkstream=True
        )
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def _process(message_id: str, run_id: str) -> None:
    record = get_run_question(run_id)
    if record is None:
        logger.warning("run_missing id=%s", run_id)
        redis_client.xack(settings.research_queue, settings.worker_group, message_id)
        return
    question, depth, status = record
    if status in {"completed", "failed"}:
        redis_client.xack(settings.research_queue, settings.worker_group, message_id)
        return
    try:
        logger.info("run_started id=%s message=%s", run_id, message_id)
        run_research(run_id, question, depth)
        redis_client.xack(settings.research_queue, settings.worker_group, message_id)
        logger.info("run_completed id=%s", run_id)
    except Exception as exc:
        logger.exception("run_failed id=%s", run_id)
        fail_run(run_id, str(exc))
        redis_client.xack(settings.research_queue, settings.worker_group, message_id)


def reclaim_stale() -> None:
    try:
        result = redis_client.xautoclaim(
            settings.research_queue,
            settings.worker_group,
            CONSUMER,
            min_idle_time=300_000,
            start_id="0-0",
            count=5,
        )
    except (ResponseError, TypeError):
        return
    messages = result[1] if len(result) > 1 else []
    for message_id, fields in messages:
        run_id = fields.get("run_id")
        if run_id:
            logger.info("reclaimed_stale_job id=%s", run_id)
            _process(message_id, run_id)


def main() -> int:
    signal.signal(signal.SIGTERM, stop_worker)
    signal.signal(signal.SIGINT, stop_worker)
    while RUNNING:
        try:
            ensure_group()
            reclaim_stale()
            batches = redis_client.xreadgroup(
                settings.worker_group,
                CONSUMER,
                {settings.research_queue: ">"},
                count=1,
                block=3000,
            )
        except Exception as exc:
            logger.warning("queue_unavailable error=%s", exc)
            time.sleep(3)
            continue
        for _, messages in batches:
            for message_id, fields in messages:
                run_id = fields.get("run_id")
                if not run_id:
                    redis_client.xack(settings.research_queue, settings.worker_group, message_id)
                    continue
                _process(message_id, run_id)
    logger.info("worker_stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
