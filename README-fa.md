# dwd-mcp 🌤️

mcp-name: io.github.mohammad-abbasi-sh/dwd-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **[DWD (Deutscher Wetterdienst)](https://www.dwd.de)** — هواشناسی آلمان از سرویس ملی هواشناسی آلمان (DWD): پیش‌بینی و وضعیت فعلی با مدل ICON از طریق Open-Meteo، هشدارهای رسمی آب‌وهوای DWD و شمارش گرده. بدون کلید، بدون ورود.

> ساختهٔ محمد عباسی، بخشی از «کارخانهٔ MCP آلمان». وابسته به DWD (Deutscher Wetterdienst) نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP کلاینت اضافه کنید (stdio):

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

یا به‌صورت محلی اجرا کنید: `python -m dwd_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `dwd_forecast` | پیش‌بینی مدل ICON برای یک شهر آلمان (ساعتی + روزانه) |
| `dwd_current_weather` | وضعیت فعلی هوا برای یک شهر آلمان |
| `dwd_warnings` | هشدارهای رسمی آب‌وهوای DWD، قابل فیلتر بر اساس ایالت |
| `dwd_pollen` | شمارش گرده برای یک شهر آلمان (CAMS از طریق Open-Meteo) |
| `dwd_find_place` | یافتن شهرهای آلمان (نام → مختصات) |
| `dwd_health` | بررسی دسترس‌پذیری (ok / blocked / error) — یک درخواست مؤدبانه |

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## لایسنس

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
