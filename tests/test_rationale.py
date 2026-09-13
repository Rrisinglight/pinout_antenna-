import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CYR = re.compile(r"[Ѐ-ӿ]")
TAG = re.compile(r"\[(ТЗ|project|sdtv2csi|DS §[0-9.]+(?:, Table \d+)?|DS Table \d+|DS Fig\. \d+|BCM2711 §[0-9.]+)\]$")
SKIP = {"GND", "NC"}


class TestRationale(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rat = json.loads((ROOT / "data" / "rationale.json").read_text(encoding="utf-8"))
        cls.prj = json.loads((ROOT / "data" / "project.json").read_text(encoding="utf-8"))
        cls.ds = json.loads((ROOT / "data" / "cm4_datasheet.json").read_text(encoding="utf-8"))
        cls.pins = {p["n"] for p in cls.ds["pins"]}

    def check(self, where, t):
        self.assertIsInstance(t, str, where)
        self.assertTrue(10 <= len(t) <= 320, f"{where}: length {len(t)}")
        self.assertIsNotNone(CYR.search(t), f"{where}: no Russian text")
        self.assertRegex(t, TAG, f"{where}: missing/invalid tag: {t[-40:]}")

    def test_overview(self):
        self.assertTrue(5 <= len(self.rat["overview"]) <= 7)
        for i, t in enumerate(self.rat["overview"]):
            self.check(f"overview#{i}", t)

    def test_devices(self):
        expected = {k for k in self.prj["devices"] if k not in SKIP}
        self.assertEqual(set(self.rat["devices"]), expected)
        for k, items in self.rat["devices"].items():
            self.assertTrue(1 <= len(items) <= 3, k)
            for i, t in enumerate(items):
                self.check(f"devices.{k}#{i}", t)

    def test_pins(self):
        for k, items in self.rat["pins"].items():
            self.assertIn(int(k), self.pins, k)
            self.assertIn(k, self.prj["pins"], f"pin {k} has no project entry")
            self.assertTrue(1 <= len(items) <= 2, k)
            for i, t in enumerate(items):
                self.check(f"pins.{k}#{i}", t)
        for k in ("36", "37", "38", "30", "44", "50", "26", "49", "27", "25", "46", "78", "80", "82", "55", "115", "121", "99", "93", "58"):
            self.assertIn(k, self.rat["pins"], f"pin {k} needs a rationale bullet")

    def test_i2c_rationale_present(self):
        blob = " ".join(self.rat["devices"]["I2C"]) + " " + " ".join(self.rat["overview"])
        for needle in ("I2C1", "ADS1115", "1.8 кОм"):
            self.assertIn(needle, blob, needle)


if __name__ == "__main__":
    unittest.main()
