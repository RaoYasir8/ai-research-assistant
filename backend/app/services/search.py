from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.domain.evidence import canonicalize_url


@dataclass(slots=True)
class SearchHit:
    title: str
    url: str
    snippet: str
    domain: str


class SearchError(RuntimeError):
    pass


def search_web(query: str, limit: int | None = None) -> list[SearchHit]:
    take = limit or settings.max_search_results_per_query
    params = {
        "q": query,
        "format": "json",
        "safesearch": 1,
        "language": "all",
    }
    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(f"{settings.searxng_url.rstrip('/')}/search", params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise SearchError(f"Search service unavailable: {exc}") from exc

    hits: list[SearchHit] = []
    seen: set[str] = set()
    for item in payload.get("results", []):
        raw_url = str(item.get("url", "")).strip()
        title = str(item.get("title", "")).strip()
        if not raw_url or not title:
            continue
        try:
            clean_url = canonicalize_url(raw_url)
            parsed = urlparse(clean_url)
        except ValueError:
            continue
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            continue
        if clean_url in seen:
            continue
        seen.add(clean_url)
        hits.append(
            SearchHit(
                title=title[:500],
                url=clean_url,
                snippet=str(item.get("content", "")).strip()[:1500],
                domain=parsed.hostname.lower(),
            )
        )
        if len(hits) >= take:
            break
    return hits
