import json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "cm4_datasheet.json"
GROUPS = {"GND", "PWR5", "PWR33", "PWR18", "GPIO", "ETH", "SD", "USB", "PCIE", "CSI0", "CSI1",
          "HDMI0", "HDMI1", "DSI0", "DSI1", "I2C0", "CTRL", "RSV", "VDAC", "ANALOG"}
DIRS = {"gnd", "power_in", "power_out", "in", "out", "bidir", "nc"}


class TestDatasheet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(PATH.read_text(encoding="utf-8"))
        cls.pins = {p["n"]: p for p in cls.data["pins"]}

    def test_200_pins_sequential(self):
        self.assertEqual([p["n"] for p in self.data["pins"]], list(range(1, 201)))

    def test_spot_checks(self):
        p = self.pins
        self.assertEqual(p[1]["sig"], "GND")
        self.assertEqual(p[55]["sig"], "GPIO14")
        self.assertEqual(p[99]["sig"], "GLOBAL_EN")
        self.assertEqual(p[200]["sig"], "HDMI0_SCL")
        self.assertEqual(p[36]["gpio"], 0)
        self.assertEqual(p[35]["gpio"], 1)
        self.assertEqual(p[80]["gpio"], 45)
        self.assertEqual(p[82]["gpio"], 44)
        self.assertNotIn("gpio", p[97])
        self.assertEqual(p[92]["ds"], "Bidirectional pin. Can be driven low (via a 220Ω resistor) to reset the CM4 CPU. "
                         "As an output, a high signals that power is good and CPU is running. Internally pulled up to +3.3V via 10kΩ")

    def test_fields_and_counts(self):
        cnt = {}
        for p in self.data["pins"]:
            self.assertIn(p["grp"], GROUPS, p)
            self.assertIn(p["dir"], DIRS, p)
            self.assertTrue(p["sig"] and p["ds"], p)
            self.assertEqual(p["conn"], "J1" if p["n"] <= 100 else "J2")
            self.assertEqual(p["row"], "odd" if p["n"] % 2 else "even")
            cnt[p["grp"]] = cnt.get(p["grp"], 0) + 1
        self.assertEqual(cnt, {"GND": 51, "PWR5": 6, "PWR33": 3, "PWR18": 2, "GPIO": 28, "ETH": 13, "SD": 12,
                               "USB": 3, "PCIE": 8, "CSI0": 6, "CSI1": 10, "HDMI0": 12, "HDMI1": 12,
                               "DSI0": 6, "DSI1": 10, "I2C0": 2, "CTRL": 10, "RSV": 3, "VDAC": 1, "ANALOG": 2})

    def test_directions(self):
        p = self.pins
        self.assertEqual(p[1]["dir"], "gnd")
        self.assertEqual(p[77]["dir"], "power_in")
        self.assertEqual(p[84]["dir"], "power_out")
        self.assertEqual(p[78]["dir"], "power_in")
        self.assertEqual(p[15]["dir"], "out")
        self.assertEqual(p[3]["dir"], "bidir")
        self.assertEqual(p[99]["dir"], "in")
        self.assertEqual(p[100]["dir"], "out")
        self.assertEqual(p[110]["dir"], "out")
        self.assertEqual(p[116]["dir"], "in")
        self.assertEqual(p[76]["dir"], "nc")
        self.assertEqual(p[128]["dir"], "in")
        self.assertEqual(p[157]["dir"], "out")

    def test_pairs(self):
        paired = [p for p in self.data["pins"] if "pair" in p]
        self.assertEqual(len(paired), 64)
        for p in paired:
            q = self.pins[p["pair"]["partner"]]
            self.assertEqual(q["pair"]["partner"], p["n"])
            self.assertEqual(q["pair"]["z"], p["pair"]["z"])
            self.assertIn(p["pair"]["z"], (90, 100))
        self.assertEqual(self.pins[116]["pair"], {"partner": 118, "z": 90, "skew": 0.23})
        self.assertEqual(self.pins[3]["pair"], {"partner": 5, "z": 100, "skew": 4.29})
        self.assertEqual(self.pins[103]["pair"], {"partner": 105, "z": 90, "skew": 0.0})
        self.assertEqual(self.pins[157]["pair"]["partner"], 159)

    def test_alt(self):
        alt = self.data["alt"]
        self.assertEqual(sorted(map(int, alt)), list(range(28)))
        for a in alt.values():
            self.assertIn(a["pull"], ("High", "Low"))
            self.assertEqual(len(a["alt"]), 6)
        self.assertEqual(alt["0"]["alt"], ["SDA0", "SA5", "PCLK", "SPI3_CE0_N", "TXD2", "SDA6"])
        self.assertEqual(alt["7"]["alt"], ["SPI0_CE1_N", "SWE_N / SRW_N", "DPI_D3", "SPI4_SCLK", "RTS3", "SCL4"])
        self.assertEqual(alt["10"]["alt"][3], "BSCSL SDA / MOSI")
        self.assertEqual(alt["18"]["alt"][5], "PWM0_0")
        self.assertEqual(alt["20"]["alt"][3], "SPI6_MOSI")
        self.assertEqual(alt["27"]["pull"], "Low")


if __name__ == "__main__":
    unittest.main()
