# dwd-mcp 🌤️

mcp-name: io.github.mohammad-abbasi-sh/dwd-mcp

Unofficial **read-only** MCP server for **[DWD (Deutscher Wetterdienst)](https://www.dwd.de)** — German weather from the Deutscher Wetterdienst (DWD): ICON-model forecasts and current conditions via Open-Meteo, official DWD severe-weather warnings, and pollen counts. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory". Not affiliated with DWD (Deutscher Wetterdienst).

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "dwd": {
      "command": "uvx",
      "args": ["dwd-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m dwd_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `dwd_forecast` | ICON-model forecast (hourly + daily) — `place` (e.g. "Berlin"), `days` 1..7 |
| `dwd_current_weather` | Current conditions — `place` (e.g. "München") |
| `dwd_warnings` | Official DWD warnings — `state` (e.g. "Bayern" or "BY"), `min_level` 1..4 |
| `dwd_pollen` | Pollen counts by type — `place` (e.g. "Berlin"), `days` 1..7 |
| `dwd_find_place` | Geocode German places — `query` (e.g. "München") |
| `dwd_health` | Reachability probe (ok / blocked / error) — one polite request |

## Notes

- Forecasts and current conditions come from the **DWD ICON model** via Open-Meteo (api.open-meteo.com) — the DWD's own numerical model, free, no key.
- `dwd_warnings` reads the **official DWD warnapp feed** (www.dwd.de/DWD/warnungen/warnapp/json/warnings.json) — a `warnWetter.loadWarnings({...});` JSONP wrapper, stripped here. Warnings are sorted by level (highest first).
- `dwd_pollen` is **CAMS pollen data via the Open-Meteo air-quality API, not DWD data** — the tool output says so. DWD publishes no public pollen JSON (verified 2026-11-10: the warnapp pollen path is a 404).
- Daily station observations (CDC) are intentionally out of scope — pipeworx-io/mcp-dwd-climate already covers them in the official registry.

Tests: 22/22 green (15 offline + 7 live, 2026-11-10).

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
