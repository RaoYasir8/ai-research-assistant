from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import trafilatura

from app.config import settings

USER_AGENT = "AIResearchAssistant/1.0 (+local educational research tool)"


@dataclass(slots=True)
class FetchResult:
    text: str
    status: str


def _assert_public_host(hostname: str) -> None:
    if hostname.lower().endswith((".local", ".internal", ".localhost")) or hostname.lower() == "localhost":
        raise ValueError("local hostnames are blocked")
    infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    if not infos:
        raise ValueError("hostname did not resolve")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if any((ip.is_private, ip.is_loopback, ip.is_link_local, ip.is_multicast, ip.is_reserved, ip.is_unspecified)):
            raise ValueError("non-public address is blocked")


def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("only public http(s) URLs are allowed")
    _assert_public_host(parsed.hostname)


def _robots_allows(url: str, client: httpx.Client) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = client.get(robots_url, headers={"User-Agent": USER_AGENT})
        if response.status_code >= 400:
            return True
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(response.text.splitlines())
        return parser.can_fetch(USER_AGENT, url)
    except httpx.HTTPError:
        return True


def fetch_article(url: str) -> FetchResult:
    try:
        validate_public_url(url)
    except (ValueError, socket.gaierror):
        return FetchResult("", "blocked")

    timeout = httpx.Timeout(settings.source_fetch_timeout_seconds)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1"}
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            if not _robots_allows(url, client):
                return FetchResult("", "robots_denied")

            current = url
            for _ in range(4):
                validate_public_url(current)
                with client.stream("GET", current, headers=headers) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            return FetchResult("", "redirect_error")
                        current = urljoin(current, location)
                        continue
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "").lower()
                    if not any(kind in content_type for kind in ("text/html", "text/plain", "application/xhtml+xml")):
                        return FetchResult("", "unsupported_content")
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data) >= settings.max_fetch_bytes:
                            break
                    encoding = response.encoding or "utf-8"
                    html = bytes(data).decode(encoding, errors="replace")
                    extracted = trafilatura.extract(
                        html,
                        include_comments=False,
                        include_tables=False,
                        no_fallback=False,
                    ) or ""
                    clean = " ".join(extracted.split())[: settings.max_source_chars]
                    return FetchResult(clean, "fetched" if clean else "empty")
            return FetchResult("", "too_many_redirects")
    except (httpx.HTTPError, ValueError, socket.gaierror, UnicodeError):
        return FetchResult("", "fetch_failed")
