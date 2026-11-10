"""HTTP layer for dwd_mcp — plain httpx GETs against DWD (Deutscher Wetterdienst).

No key, no login. One retry on 429/5xx; error taxonomy (403/429/other).
"""
from __future__ import annotations

import os
import ssl
import time

import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
TIMEOUT = 25.0
PROBE_URL = "https://api.open-meteo.com/v1/dwd-icon?latitude=52.52&longitude=13.41&current=temperature_2m&forecast_days=1"
SOURCE = "DWD (Deutscher Wetterdienst)"


class DwdMcpError(RuntimeError):
    pass


def _verify():
    """TLS trust store: the OS bundle when present, else httpx/certifi."""
    for path in (
        "/etc/ssl/certs/ca-certificates.crt",
        ssl.get_default_verify_paths().openssl_cafile,
    ):
        if path and os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return True


def _client() -> httpx.Client:
    # NOTE: we read the proxy URL from the environment but never log it.
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    return httpx.Client(
        headers={"User-Agent": UA, "Accept": "application/json, application/xml, text/html, */*"},
        timeout=TIMEOUT,
        proxy=proxy or None,
        trust_env=False,
        verify=_verify(),
    )


def fetch_text(url: str) -> str:
    """GET one URL and return its text. One retry on 429/5xx."""
    last_exc: Exception | None = None
    r: httpx.Response | None = None
    for attempt in range(2):
        try:
            with _client() as c:
                r = c.get(url)
        except httpx.HTTPError as e:
            last_exc = e
            if attempt == 0:
                time.sleep(1.0)
                continue
            raise DwdMcpError(f"network error fetching {url}: {e}") from e
        if r.status_code in (429, 500, 502, 503):
            if attempt == 0:
                time.sleep(1.0)
                continue
        break
    assert r is not None  # loop always assigns r or raises
    if r.status_code == 403:
        raise DwdMcpError(
            f"{SOURCE} returned HTTP 403 for {url} (bot wall) — try again later"
        )
    if r.status_code == 429:
        raise DwdMcpError(
            f"{SOURCE} rate-limited the request (HTTP 429) — try again later"
        )
    if r.status_code != 200:
        raise DwdMcpError(f"{SOURCE} returned HTTP {r.status_code} for {url}")
    return r.text


def health_check() -> dict:
    """One polite probe of the source site.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `<prefix>_health` tool
    and the daily smoke CI.
    """
    url = PROBE_URL
    try:
        fetch_text(url)
    except DwdMcpError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
