import json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestSchematic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = json.loads((ROOT / "data" / "schematic.json").read_text(encoding="utf-8"))

    def test_shape(self):
        self.assertEqual(set(self.s), {"source", "pins"})
        self.assertEqual(self.s["source"]["project"], "Retr_2026-09-26")
        self.assertEqual(self.s["source"]["board"], "Retr_Cross")
        self.assertIn("2026-10-14", self.s["source"]["snapshot"])
        self.assertEqual(sorted(map(int, self.s["pins"])), list(range(1, 201)))
        for k, p in self.s["pins"].items():
            self.assertEqual(set(p), {"net", "to", "wired"}, k)
            self.assertIsInstance(p["net"], str); self.assertIsInstance(p["to"], list)
            self.assertIn(p["wired"], (True, False, None), k)
            self.assertLessEqual(len(p["to"]), 6)

    def test_spot_checks(self):
        p = self.s["pins"]
        self.assertEqual(p["55"], {"net": "UART0_TXD", "to": ["UART.2"], "wired": True})
        self.assertEqual(p["37"], {"net": "IO7", "to": [], "wired": False})
        self.assertEqual(p["20"], {"net": "", "to": [], "wired": None})
        self.assertEqual(p["98"]["net"], ""); self.assertEqual(p["197"]["net"], "RG_OE")
        self.assertEqual(p["25"]["net"], "VRX_CLK"); self.assertEqual(p["25"]["to"], ["VRX_1.4"])
        self.assertEqual(p["15"]["to"], ["R1.2", "ETH_Y.1 (via R1)"])
        self.assertEqual(p["128"]["net"], "CAM0_DO_N")
        self.assertEqual(p["77"]["net"], "+5V_CM"); self.assertEqual(p["78"]["net"], "+3V")
        self.assertEqual(sum(1 for x in p.values() if x["net"]), 131)   # 200 − 51 unused − 14 site-only − CN1.98 − 3 more empty labels (verified against chains.json)

    @unittest.skipUnless((ROOT / "Review" / "_data" / "chains.json").exists(), "review snapshot not present")
    def test_regenerates_identically(self):
        import subprocess, sys
        out = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "extract_schematic.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
