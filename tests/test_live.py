"""Live tests — hit the real DWD / Open-Meteo APIs. Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set DWD_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from dwd_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("DWD_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="DWD_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_forecast_live(self):
        out = json.loads(srv.dwd_forecast("Berlin", days=2))
        self.assertNotIn("error", out)
        self.assertEqual(out["place"], "Berlin")
        self.assertGreaterEqual(out["hourly_count"], 24)
        self.assertTrue(all(r["temperature_2m"] is not None for r in out["hourly"]))
        print(f"\nLIVE forecast Berlin: {out['hourly_count']} hours, now {out['current']['temperature_2m']}°C")

    def test_current_live(self):
        out = json.loads(srv.dwd_current_weather("München"))
        self.assertNotIn("error", out)
        self.assertEqual(out["place"], "München")
        self.assertIsNotNone(out["temperature_2m"])
        print(f"\nLIVE current München: {out['temperature_2m']}°C, {out['weather']}")

    def test_warnings_live(self):
        out = json.loads(srv.dwd_warnings())
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 0)
        print(f"\nLIVE warnings: {out['count']} active in Germany")

    def test_warnings_state_live(self):
        out = json.loads(srv.dwd_warnings(state="Bayern"))
        self.assertNotIn("error", out)
        self.assertTrue(all(w["state"] == "Bayern" for w in out["warnings"]))
        print(f"\nLIVE warnings Bayern: {out['count']}")

    def test_pollen_live(self):
        out = json.loads(srv.dwd_pollen("Berlin", days=1))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["hourly_count"], 12)
        print(f"\nLIVE pollen Berlin: {out['hourly_count']} hours")

    def test_find_place_live(self):
        out = json.loads(srv.dwd_find_place("Hamburg"))
        self.assertNotIn("error", out)
        self.assertGreaterEqual(out["count"], 1)
        self.assertEqual(out["places"][0]["name"], "Hamburg")
        print(f"\nLIVE find Hamburg: {out['places'][0]['latitude']}, {out['places'][0]['longitude']}")

    def test_health_live(self):
        out = json.loads(srv.dwd_health())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["http_status"], 200)
