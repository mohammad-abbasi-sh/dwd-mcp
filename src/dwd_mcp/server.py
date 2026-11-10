"""MCP server: unofficial read-only access to DWD weather — the
Deutscher Wetterdienst (Germany's national weather service) — via the
DWD ICON model (Open-Meteo) and the official DWD warning feed. No key,
no login."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for DWD weather — the Deutscher \
Wetterdienst, Germany's national weather service. ICON-model forecasts \
and current conditions (DWD's own numerical model, via Open-Meteo, no \
key), the official DWD severe-weather warnings (warnapp feed, no key), \
and pollen counts (CAMS data via the Open-Meteo air-quality API — not \
DWD data, the tool says so). Place names are geocoded for German \
places. Built by Mohammad Abbasi (mohammad-abbasi-sh) — \
https://almanibama.ir · https://mabbasi.ir — Germany MCP factory.\
"""

_SOURCE = "DWD (opendata.dwd.de + api.open-meteo.com)"
_DISCLAIMER = "Unofficial read-only data from DWD / Open-Meteo; verify on the DWD site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("dwd-mcp", instructions=INSTRUCTIONS)


def _resolve(place: str) -> dict:
    """Geocode a place name to the best German hit."""
    if not (place or "").strip():
        raise ValueError("place must not be empty")
    return _dom.resolve_place(_http.fetch_text(_dom.geocode_url(place.strip())), place.strip())


@mcp.tool()
def dwd_forecast(place: str = "Berlin", days: int = 3) -> str:
    """DWD ICON-model forecast for a German place: current conditions,
    hourly (temperature, precipitation probability, wind, weather) and
    daily (min/max, precipitation probability, sunrise/sunset).
    place: e.g. "Berlin" or "München". days: 1..7 (default 3)."""
    try:
        d = _dom.validate_days(days)
        loc = _resolve(place)
        out = _dom.parse_forecast(_http.fetch_text(
            _dom.forecast_url(loc["latitude"], loc["longitude"], d)))
    except (_http.DwdMcpError, ValueError) as e:
        return _err(e)
    return _ok({"place": loc["name"], "latitude": loc["latitude"],
                "longitude": loc["longitude"], **out})


@mcp.tool()
def dwd_current_weather(place: str = "Berlin") -> str:
    """Current DWD ICON conditions for a German place: temperature,
    humidity, apparent temperature, wind speed/direction, weather.
    place: e.g. "Berlin" or "Hamburg"."""
    try:
        loc = _resolve(place)
        out = _dom.parse_current(_http.fetch_text(
            _dom.current_url(loc["latitude"], loc["longitude"])))
    except (_http.DwdMcpError, ValueError) as e:
        return _err(e)
    return _ok({"place": loc["name"], "latitude": loc["latitude"],
                "longitude": loc["longitude"], **out})


@mcp.tool()
def dwd_warnings(state: str | None = None, min_level: int = 1) -> str:
    """Official DWD severe-weather warnings, newest/highest level first.
    state: filter by Bundesland — German name ("Bayern"), short code
    ("BY") or region substring ("Kassel"); empty = all of Germany.
    min_level: 1..4 (default 1)."""
    try:
        if not 1 <= min_level <= 4:
            raise ValueError(f"min_level out of range: {min_level} (expected 1..4)")
        parsed = _dom.parse_warnings_jsonp(_http.fetch_text(_dom.WARNINGS_URL))
        found = _dom.filter_warnings(parsed["warnings"], state, min_level)
    except (_http.DwdMcpError, ValueError) as e:
        return _err(e)
    return _ok({"issued_at": parsed["issued_at"], "total_results": parsed["count"],
                "state": state, "min_level": min_level,
                "count": len(found), "warnings": found})


@mcp.tool()
def dwd_pollen(place: str = "Berlin", days: int = 2) -> str:
    """Pollen counts for a German place, by type (alder, birch, grass,
    mugwort, ragweed, olive) — hourly plus per-day maximum.
    NOTE: pollen data comes from CAMS via the Open-Meteo air-quality
    API, not from DWD. place: e.g. "Berlin". days: 1..7 (default 2)."""
    try:
        d = _dom.validate_days(days)
        loc = _resolve(place)
        out = _dom.parse_pollen(_http.fetch_text(
            _dom.pollen_url(loc["latitude"], loc["longitude"], d)))
    except (_http.DwdMcpError, ValueError) as e:
        return _err(e)
    return _ok({"place": loc["name"], "latitude": loc["latitude"],
                "longitude": loc["longitude"], **out})


@mcp.tool()
def dwd_find_place(query: str) -> str:
    """Find German places by name and return coordinates.
    query: e.g. "München" or "Freiburg". German hits first."""
    try:
        if not (query or "").strip():
            return _ok({"error": "query must not be empty"})
        out = _dom.parse_geocode(_http.fetch_text(_dom.geocode_url(query.strip())))
    except (_http.DwdMcpError, ValueError) as e:
        return _err(e)
    return _ok({"query": query.strip(), "count": len(out), "places": out})


@mcp.tool()
def dwd_health() -> str:
    """Check whether the DWD weather sources are reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
