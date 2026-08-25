from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PREFIXES = ("utm_", "mc_", "pk_")
TRACKING_KEYS = {"gclid", "fbclid", "ref", "source"}
TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_+.-]{1,}")
CITATION_RE = re.compile(r"\[(S\d{1,3})\]")


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query_pairs = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        low = key.lower()
        if low in TRACKING_KEYS or low.startswith(TRACKING_PREFIXES):
            continue
        query_pairs.append((key, value))
    clean_path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), clean_path, urlencode(query_pairs), ""))


def content_hash(text: str) -> str:
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text) if len(token) > 2}


def grounding_score(claim: str, evidence: str) -> float:
    claim_tokens = tokens(claim)
    if not claim_tokens:
        return 0.0
    evidence_tokens = tokens(evidence)
    overlap = claim_tokens & evidence_tokens
    return round(len(overlap) / len(claim_tokens), 4)


def citation_keys(markdown: str) -> list[str]:
    return CITATION_RE.findall(markdown)


def invalid_citations(markdown: str, allowed: set[str]) -> set[str]:
    return {key for key in citation_keys(markdown) if key not in allowed}



def uncited_key_blocks(markdown: str) -> list[str]:
    """Return substantive lines in key report sections that lack a source citation."""
    active = False
    missing: list[str] = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            active = heading in {"overview", "key findings"}
            continue
        if not active or not line or line.startswith("#"):
            continue
        if len(line) >= 50 and not CITATION_RE.search(line):
            missing.append(line)
    return missing
