import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CYR = re.compile(r"[Ѐ-ӿ]")
TAG = re.compile(r"\[(Review/(power-board|crsf-one-wire|vrx-board|analog-to-csi|website|README)\.md(?: (?:п\.|разд\.) [0-9][0-9., –-]*)?|DS §[0-9.]+(?:, Table \d+)?|DS Table \d+|DS Fig\. \d+|BCM2711 §[0-9.]+|ТЗ|project|sdtv2csi|CM4IO)\]$")
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
        for k in ("36", "35", "37", "38", "30", "44", "50", "26", "49", "27", "25", "46", "78", "80", "82", "55", "115", "128", "99", "93", "58"):
            self.assertIn(k, self.rat["pins"], f"pin {k} needs a rationale bullet")

    def test_v3_claims(self):
        bullets = list(self.rat["overview"])
        for grp in ("devices", "pins"):
            for items in self.rat[grp].values():
                bullets += items
        blob = "\n".join(bullets)
        self.assertIn("TCA9534A", blob)
        self.assertIn("CSI0", " ".join(self.rat["devices"]["VDEC"]), "decoder must be on CSI0")
        self.assertIn("CSI1", " ".join(self.rat["devices"]["CAM"]), "camera must be on CSI1")
        spare = " ".join(self.rat["devices"]["SPARE"])
        for needle in ("GPIO7", "GPIO11"):
            self.assertIn(needle, spare, needle)
        for t in bullets:
            if "RTS3 = GPIO7" in t:
                self.assertIn("не нужн", t, f"RTS3 as the direction scheme: {t[:60]}")

    def test_i2c_rationale_present(self):
        blob = " ".join(self.rat["devices"]["I2C"]) + " " + " ".join(self.rat["overview"])
        for needle in ("I2C1", "ADS1115", "1.8 кОм"):
            self.assertIn(needle, blob, needle)

    def test_alt_claims_match_datasheet(self):
        # "GPIO7 = RTS3 (ALT4)", "GPIO18 = аппаратный PWM0_0 (ALT5)" and the grouped
        # "(ALT5: GPIO18 = PWM0_0, GPIO19 = PWM0_1)" must all agree with DS Table 1.
        single = re.compile(r"GPIO(\d+)\s*=\s*(?:[а-яё]+\s+)?([A-Za-z0-9_]+)\s*\(ALT(\d)\)")
        grouped = re.compile(r"\(ALT(\d):\s*((?:GPIO\d+\s*=\s*[A-Za-z0-9_]+(?:,\s*)?)+)\)")
        pair = re.compile(r"GPIO(\d+)\s*=\s*([A-Za-z0-9_]+)")
        bullets = [("overview", t) for t in self.rat["overview"]]
        for grp in ("devices", "pins"):
            for k, items in self.rat[grp].items():
                bullets += [(f"{grp}.{k}", t) for t in items]
        claims = []
        for where, t in bullets:
            for m in single.finditer(t):
                claims.append((where, m.group(1), m.group(2), int(m.group(3))))
            for m in grouped.finditer(t):
                for g, fn in pair.findall(m.group(2)):
                    claims.append((where, g, fn, int(m.group(1))))
        self.assertGreaterEqual(len(claims), 5, "regex no longer matches the bullet phrasing")
        for where, gpio, fn, alt in claims:
            self.assertIn(gpio, self.ds["alt"], f"{where}: GPIO{gpio} not in ALT table")
            self.assertEqual(self.ds["alt"][gpio]["alt"][alt], fn, f"{where}: GPIO{gpio} ALT{alt}")


if __name__ == "__main__":
    unittest.main()
