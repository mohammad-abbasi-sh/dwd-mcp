# dwd-mcp 🌤️

mcp-name: io.github.mohammad-abbasi-sh/dwd-mcp

Inoffizieller **nur lesender** MCP-Server für **[DWD (Deutscher Wetterdienst)](https://www.dwd.de)** — Deutsches Wetter vom Deutschen Wetterdienst (DWD): ICON-Vorhersagen und aktuelles Wetter über Open-Meteo, amtliche Unwetterwarnungen und Pollenflug. Kein Schlüssel, keine Anmeldung.

> Gebaut von Mohammad Abbasi als Teil der "Germany MCP factory". Nicht mit DWD (Deutscher Wetterdienst) verbunden.

## Für KI-Agenten

Zur MCP-Client-Konfiguration hinzufügen (stdio):

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

Oder lokal starten: `python -m dwd_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|-------------|
| `dwd_forecast` | ICON-Vorhersage für einen deutschen Ort (stündlich + täglich) |
| `dwd_current_weather` | Aktuelles Wetter für einen deutschen Ort |
| `dwd_warnings` | Amtliche Unwetterwarnungen des DWD, filterbar nach Bundesland |
| `dwd_pollen` | Pollenflug für einen deutschen Ort (CAMS über Open-Meteo) |
| `dwd_find_place` | Deutsche Orte finden (Name → Koordinaten) |
| `dwd_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## Lizenz

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
