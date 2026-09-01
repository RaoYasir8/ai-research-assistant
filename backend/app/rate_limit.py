from __future__ import annotations

import time

from fastapi import HTTPException, Request, status
from redis import Redis

from app.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


def enforce_rate_limit(request: Request, bucket: str, limit: int, window_seconds: int) -> None:
    host = request.client.host if request.client else "unknown"
    key = f"ratelimit:{bucket}:{host}:{int(time.time() // window_seconds)}"
    try:
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, window_seconds + 1)
        if current > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests"
            )
    except HTTPException:
        raise
    except Exception:
        return
