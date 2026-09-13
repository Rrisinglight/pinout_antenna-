import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CYR = re.compile(r"[Ѐ-ӿ]")
TAG = re.compile(r"\[(DS §[0-9.]+(?:, Table \d+)?|DS Table \d+|DS Fig\. \d+|BCM2711 §[0-9.]+|project|sdtv2csi|CM4IO)\]$")
GROUPS = {"GND", "PWR5", "PWR33", "PWR18", "GPIO", "ETH", "SD", "USB", "PCIE", "CSI0", "CSI1",
          "HDMI0", "HDMI1", "DSI0", "DSI1", "I2C0", "CTRL", "RSV", "VDAC", "ANALOG"}
SECTIONS = ["Механика и разъёмы", "Питание и последовательность включения", "Загрузка, сброс и сервис",
            "Высокоскоростные дифференциальные пары", "GPIO и низкоскоростные интерфейсы", "Wi-Fi и радиочасть",
            "Тепловой режим", "Видеодекодер ADV7280A-M (проект)"]


class TestRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rt = json.loads((ROOT / "data" / "routing.json").read_text(encoding="utf-8"))
        cls.ds = json.loads((ROOT / "data" / "cm4_datasheet.json").read_text(encoding="utf-8"))
        cls.pins = {p["n"]: p for p in cls.ds["pins"]}

    def check_item(self, where, t):
        self.assertIsInstance(t, str, where)
        self.assertTrue(10 <= len(t) <= 320, f"{where}: length {len(t)}")
        self.assertIsNotNone(CYR.search(t), f"{where}: no Russian text")
        self.assertRegex(t, TAG, f"{where}: missing/invalid source tag: {t[-40:]}")

    def test_groups(self):
        self.assertEqual(set(self.rt["groups"]), GROUPS)
        for g, items in self.rt["groups"].items():
            self.assertIsInstance(items, list, g)
            for t in items:
                self.check_item(f"groups.{g}", t)
        for g in ("PCIE", "USB", "ETH", "CSI0", "CSI1", "GPIO", "PWR5", "PWR33", "GND"):
            self.assertGreaterEqual(len(self.rt["groups"][g]), 1, g)

    def test_pins(self):
        for k, items in self.rt["pins"].items():
            self.assertIn(int(k), self.pins, k)
            self.assertIsInstance(items, list, k)
            self.assertGreaterEqual(len(items), 1, k)
            for t in items:
                self.check_item(f"pins.{k}", t)
        for k in ("78", "99", "93", "92", "102", "109", "116", "122", "101"):
            self.assertIn(k, self.rt["pins"], f"pin {k} needs a pin-specific note")

    def test_general(self):
        self.assertEqual([s["title"] for s in self.rt["general"]], SECTIONS)
        for s in self.rt["general"]:
            self.assertGreaterEqual(len(s["items"]), 2, s["title"])
            for t in s["items"]:
                self.check_item(s["title"], t)

    def test_key_numbers_present(self):
        blob = "\n".join(t for s in self.rt["general"] for t in s["items"]) + "\n" + \
               "\n".join(t for items in self.rt["groups"].values() for t in items) + "\n" + \
               "\n".join(t for items in self.rt["pins"].values() for t in items)
        for needle in ("90 Ом", "100 Ом", "0.15 мм", "0.1 мм", "6.5 × 11 мм", "8 × 15 мм", "10 мм", "DF40C-100DS-0.4V", "DF40HC(3.0)-100DS-0.4V",
                       "4.75", "5.25", "600 мА", "300 мА", "50 мА", "2 мс", "220 Ом", "15 мкА", "PETp0", "PERp0", "CLKREQ#", "PERST#",
                       "1.8 кОм", "−20", "85 °C", "0x21", "28.63636 МГц"):
            self.assertIn(needle, blob, needle)


if __name__ == "__main__":
    unittest.main()
