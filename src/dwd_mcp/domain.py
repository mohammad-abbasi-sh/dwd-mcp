"""Domain logic: shape DWD / Open-Meteo weather data into compact dicts
(stdlib only).

Data sources (all free, no key, no login):
- Forecasts + current conditions: Open-Meteo DWD ICON model
  (api.open-meteo.com/v1/dwd-icon) — the DWD's own numerical model.
- Official severe-weather warnings: DWD warnapp JSONP
  (www.dwd.de/DWD/warnungen/warnapp/json/warnings.json) — a
  `warnWetter.loadWarnings({...});` wrapper, stripped here.
- Pollen counts: CAMS pollen via Open-Meteo air-quality API
  (air-quality-api.open-meteo.com) — NOT DWD data; the tool and the
  README say so.
- Place search: Open-Meteo geocoding (country=DE preferred).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/dwd-icon"
POLLEN_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WARNINGS_URL = "https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json"

# WMO weather codes (Open-Meteo) → short English description.
WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

POLLEN_TYPES = ["alder_pollen", "birch_pollen", "grass_pollen",
                "mugwort_pollen", "ragweed_pollen", "olive_pollen"]


def weather_desc(code) -> str:
    """Short English description for a WMO weather code."""
    try:
        return WEATHER_CODES.get(int(code), f"Weather code {code}")
    except (TypeError, ValueError):
        return f"Weather code {code}"


def _ms_iso(ms) -> str | None:
    if not ms:
        return None
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def validate_days(days: int) -> int:
    if not 1 <= days <= 7:
        raise ValueError(f"days out of range: {days} (expected 1..7)")
    return days


def forecast_url(lat: float, lon: float, days: int) -> str:
    return (
        f"{FORECAST_URL}?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        "wind_speed_10m,wind_direction_10m,weather_code"
        "&hourly=temperature_2m,precipitation_probability,precipitation,"
        "wind_speed_10m,weather_code"
        "&daily=temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max,sunrise,sunset"
        f"&forecast_days={days}&timezone=Europe%2FBerlin"
    )


def current_url(lat: float, lon: float) -> str:
    return (
        f"{FORECAST_URL}?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        "wind_speed_10m,wind_direction_10m,weather_code&forecast_days=1"
    )


def pollen_url(lat: float, lon: float, days: int) -> str:
    return (
        f"{POLLEN_URL}?latitude={lat}&longitude={lon}"
        f"&hourly={','.join(POLLEN_TYPES)}"
        f"&forecast_days={days}&timezone=Europe%2FBerlin"
    )


def geocode_url(query: str) -> str:
    from urllib.parse import quote_plus
    return f"{GEOCODE_URL}?name={quote_plus(query)}&count=5&language=de&country=DE"


def parse_geocode(text: str) -> list:
    """Geocoding results: German places first, then the rest."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid geocoding response: {e}") from e
    out = []
    for r in data.get("results") or []:
        out.append({
            "name": r.get("name") or "",
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "country": r.get("country") or "",
            "admin1": r.get("admin1") or "",
            "population": r.get("population"),
        })
    out.sort(key=lambda p: 0 if p["country"] in ("Deutschland", "Germany") else 1)
    return out


def resolve_place(geocode_text: str, query: str) -> dict:
    """Best geocoding hit for a place query; raises when nothing found."""
    results = parse_geocode(geocode_text)
    if not results:
        raise ValueError(f"no place found for {query!r} (try a German city name)")
    return results[0]


def _zip_hourly(hourly: dict, fields: list) -> list:
    times = hourly.get("time") or []
    rows = []
    for i, t in enumerate(times):
        row = {"time": t}
        for f in fields:
            vals = hourly.get(f) or []
            row[f] = vals[i] if i < len(vals) else None
        rows.append(row)
    return rows


def parse_forecast(text: str) -> dict:
    """DWD ICON forecast: current + hourly rows + daily rows."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid forecast response: {e}") from e
    if "hourly" not in data and "daily" not in data:
        raise ValueError("unexpected forecast shape: no hourly/daily data")
    hourly = _zip_hourly(data.get("hourly") or {}, [
        "temperature_2m", "precipitation_probability", "precipitation",
        "wind_speed_10m", "weather_code",
    ])
    for row in hourly:
        row["weather"] = weather_desc(row.get("weather_code"))
    daily = []
    d = data.get("daily") or {}
    for i, date in enumerate(d.get("time") or []):
        daily.append({
            "date": date,
            "temperature_2m_max": (d.get("temperature_2m_max") or [None])[i] if i < len(d.get("temperature_2m_max") or []) else None,
            "temperature_2m_min": (d.get("temperature_2m_min") or [None])[i] if i < len(d.get("temperature_2m_min") or []) else None,
            "precipitation_probability_max": (d.get("precipitation_probability_max") or [None])[i] if i < len(d.get("precipitation_probability_max") or []) else None,
            "sunrise": (d.get("sunrise") or [None])[i] if i < len(d.get("sunrise") or []) else None,
            "sunset": (d.get("sunset") or [None])[i] if i < len(d.get("sunset") or []) else None,
        })
    current = None
    c = data.get("current")
    if c:
        current = _current_block(c)
    return {
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone"),
        "current": current,
        "hourly_count": len(hourly),
        "hourly": hourly,
        "daily": daily,
    }


def _current_block(c: dict) -> dict:
    return {
        "time": c.get("time"),
        "temperature_2m": c.get("temperature_2m"),
        "relative_humidity_2m": c.get("relative_humidity_2m"),
        "apparent_temperature": c.get("apparent_temperature"),
        "wind_speed_10m": c.get("wind_speed_10m"),
        "wind_direction_10m": c.get("wind_direction_10m"),
        "weather_code": c.get("weather_code"),
        "weather": weather_desc(c.get("weather_code")),
    }


def parse_current(text: str) -> dict:
    """Current conditions only (current-only API response)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid current-conditions response: {e}") from e
    c = data.get("current")
    if not c:
        raise ValueError("unexpected current-conditions shape: no current block")
    return _current_block(c)


_JSONP_RE = re.compile(r"^\s*warnWetter\.loadWarnings\((.*)\);\s*$", re.S)


def parse_warnings_jsonp(text: str) -> dict:
    """Strip the DWD JSONP wrapper and flatten warnings by region.

    Returns {"issued_at", "count", "warnings": [...]} sorted by level
    (highest first), then start time.
    """
    m = _JSONP_RE.match(text)
    if not m:
        raise ValueError("unexpected warnings shape: not warnWetter.loadWarnings JSONP")
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid warnings JSON: {e}") from e
    flat = []
    for _region_id, items in (data.get("warnings") or {}).items():
        for w in items or []:
            flat.append({
                "state": w.get("state") or "",
                "state_short": w.get("stateShort") or "",
                "region": w.get("regionName") or "",
                "event": w.get("event") or "",
                "headline": w.get("headline") or "",
                "level": w.get("level"),
                "start": _ms_iso(w.get("start")),
                "end": _ms_iso(w.get("end")),
                "description": (w.get("description") or "").strip(),
            })
    flat.sort(key=lambda w: (-(w["level"] or 0), w["start"] or ""))
    return {
        "issued_at": _ms_iso(data.get("time")),
        "count": len(flat),
        "warnings": flat,
    }


def filter_warnings(warnings: list, state: str | None = None,
                    min_level: int = 1) -> list:
    """Filter by state (German name, short code like "BY", or region
    substring) and minimum warning level (1..4)."""
    key = (state or "").strip().casefold()
    out = []
    for w in warnings:
        if (w["level"] or 0) < min_level:
            continue
        if key:
            hay = f"{w['state']} {w['state_short']} {w['region']}".casefold()
            if key not in hay:
                continue
        out.append(w)
    return out


def parse_pollen(text: str) -> dict:
    """CAMS pollen counts: hourly rows + per-day max per pollen type."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid pollen response: {e}") from e
    hourly = _zip_hourly(data.get("hourly") or {}, POLLEN_TYPES)
    daily_max: dict[str, dict] = {}
    for row in hourly:
        day = (row["time"] or "")[:10]
        slot = daily_max.setdefault(day, {})
        for t in POLLEN_TYPES:
            v = row.get(t)
            if v is not None:
                slot[t] = max(v, slot.get(t, 0))
    return {
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": data.get("timezone"),
        "source": "CAMS pollen via Open-Meteo air-quality API (not DWD data)",
        "hourly_count": len(hourly),
        "hourly": hourly,
        "daily_max": [{"date": d, **vals} for d, vals in sorted(daily_max.items())],
    }
