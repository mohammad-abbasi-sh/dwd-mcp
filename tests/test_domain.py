"""Offline tests — parse real captured DWD / Open-Meteo responses, no network."""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from dwd_mcp import domain as dom
from dwd_mcp import server as srv

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _read(name):
    return (FIX / name).read_text(encoding="utf-8")


class TestForecastFixture(unittest.TestCase):
    def test_forecast_shape(self):
        out = dom.parse_forecast(_read("forecast-berlin.json"))
        self.assertAlmostEqual(out["latitude"], 52.52, places=1)
        self.assertEqual(out["timezone"], "Europe/Berlin")
        self.assertEqual(out["hourly_count"], 48)
        self.assertEqual(len(out["daily"]), 2)
        self.assertIsNotNone(out["current"])
        self.assertEqual(out["current"]["weather"], "Overcast")

    def test_forecast_hourly_rows_complete(self):
        rows = dom.parse_forecast(_read("forecast-berlin.json"))["hourly"]
        self.assertTrue(all(r["time"] and r["temperature_2m"] is not None for r in rows))
        self.assertTrue(all(r["weather"] for r in rows))

    def test_forecast_daily_rows(self):
        daily = dom.parse_forecast(_read("forecast-berlin.json"))["daily"]
        self.assertTrue(all(d["temperature_2m_max"] is not None for d in daily))
        self.assertTrue(all(d["sunrise"] and d["sunset"] for d in daily))

    def test_current_fixture(self):
        out = dom.parse_current(_read("current-berlin.json"))
        self.assertEqual(out["temperature_2m"], 3.5)
        self.assertEqual(out["relative_humidity_2m"], 92)
        self.assertEqual(out["weather"], "Overcast")

    def test_weather_codes(self):
        self.assertEqual(dom.weather_desc(0), "Clear sky")
        self.assertEqual(dom.weather_desc(95), "Thunderstorm")
        self.assertEqual(dom.weather_desc(999), "Weather code 999")


class TestGeocodeFixture(unittest.TestCase):
    def test_geocode_berlin_first(self):
        out = dom.parse_geocode(_read("geocode-berlin.json"))
        self.assertGreaterEqual(len(out), 1)
        self.assertEqual(out[0]["name"], "Berlin")
        self.assertEqual(out[0]["country"], "Deutschland")
        self.assertAlmostEqual(out[0]["latitude"], 52.52437, places=3)

    def test_resolve_place(self):
        loc = dom.resolve_place(_read("geocode-berlin.json"), "Berlin")
        self.assertEqual(loc["name"], "Berlin")

    def test_resolve_place_empty(self):
        with self.assertRaises(ValueError):
            dom.resolve_place('{"results": []}', "Nowhere")


class TestWarningsFixture(unittest.TestCase):
    def test_warnings_parse(self):
        out = dom.parse_warnings_jsonp(_read("warnings.jsonp"))
        self.assertGreater(out["count"], 50)
        self.assertEqual(len(out["warnings"]), out["count"])
        self.assertTrue(out["issued_at"].startswith("2026-11-10"))
        first = out["warnings"][0]
        self.assertTrue(first["state"] and first["region"] and first["headline"])
        self.assertIn(first["level"], (1, 2, 3, 4))

    def test_warnings_sorted_by_level(self):
        warns = dom.parse_warnings_jsonp(_read("warnings.jsonp"))["warnings"]
        levels = [w["level"] for w in warns]
        self.assertEqual(levels, sorted(levels, reverse=True))

    def test_warnings_filter_state(self):
        warns = dom.parse_warnings_jsonp(_read("warnings.jsonp"))["warnings"]
        th = dom.filter_warnings(warns, "Thüringen")
        self.assertGreater(len(th), 0)
        self.assertTrue(all(w["state"] == "Thüringen" for w in th))
        by = dom.filter_warnings(warns, "BY")
        self.assertTrue(all(w["state_short"] == "BY" for w in by))

    def test_warnings_filter_level(self):
        warns = dom.parse_warnings_jsonp(_read("warnings.jsonp"))["warnings"]
        high = dom.filter_warnings(warns, min_level=3)
        self.assertTrue(all(w["level"] >= 3 for w in high))
        self.assertLessEqual(len(high), len(warns))

    def test_warnings_bad_input(self):
        with self.assertRaises(ValueError):
            dom.parse_warnings_jsonp("<html>not jsonp</html>")


class TestPollenFixture(unittest.TestCase):
    def test_pollen_shape(self):
        out = dom.parse_pollen(_read("pollen-berlin.json"))
        self.assertEqual(out["hourly_count"], 48)
        self.assertEqual(len(out["daily_max"]), 2)
        row = out["hourly"][0]
        for t in dom.POLLEN_TYPES:
            self.assertIn(t, row)
        self.assertIn("CAMS", out["source"])

    def test_server_envelope(self):
        out = json.loads(srv._ok({"x": 1}))
        self.assertIn("fetched_at", out)
        self.assertIn("source", out)
        self.assertEqual(out["x"], 1)


if __name__ == "__main__":
    unittest.main()
