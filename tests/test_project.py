import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUSES = {"used", "opt", "free", "nc", "dnc"}
CYR = re.compile(r"[Ѐ-ӿ]")


class TestProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = json.loads((ROOT / "data" / "cm4_datasheet.json").read_text(encoding="utf-8"))
        cls.prj = json.loads((ROOT / "data" / "project.json").read_text(encoding="utf-8"))
        cls.pins = {p["n"]: p for p in cls.ds["pins"]}

    def entry(self, n):
        p = self.pins[n]
        e = self.prj["pins"].get(str(n)) or self.prj["defaults"].get(p["grp"]) or {}
        return {"net": e.get("net", ""), "dev": e.get("dev", "NC"), "mode": e.get("mode", ""),
                "status": e.get("status", "used" if str(n) in self.prj["pins"] else "free"), "note": e.get("note", "")}

    def test_shape_v2(self):
        for key in ("meta", "devices", "defaults", "pins"):
            self.assertIn(key, self.prj)
        for key in ("ds_notes", "facts"):
            self.assertNotIn(key, self.prj)
        for k, d in self.prj["devices"].items():
            self.assertTrue(d["name"] and re.fullmatch(r"#[0-9A-Fa-f]{6}", d["c"]), k)
        self.assertIn("NC", self.prj["devices"])
        self.assertIn("VDEC", self.prj["devices"])

    def test_notes_russian(self):
        for k, e in self.prj["pins"].items():
            self.assertIsNotNone(CYR.search(e.get("note", "")), f"pin {k} note is not Russian")
            for f in ("net", "mode", "dev"):
                self.assertTrue(e.get(f, "").isascii(), f"pin {k} {f} must stay ASCII")
        for g, e in self.prj["defaults"].items():
            self.assertIsNotNone(CYR.search(e.get("note", "")), f"defaults {g} note is not Russian")
        for k, d in self.prj["devices"].items():
            self.assertIsNone(CYR.search(d["name"]), f"device {k} name must stay English")

    def test_pins_reference_existing(self):
        for k, e in self.prj["pins"].items():
            self.assertIn(int(k), self.pins, k)
            self.assertIn(e["dev"], self.prj["devices"], k)
            self.assertIn(e.get("status", "used"), STATUSES, k)
            self.assertTrue(e.get("note"), f"pin {k} has no note")
        for grp, e in self.prj["defaults"].items():
            self.assertIn(e["dev"], self.prj["devices"], grp)
            self.assertIn(e["status"], STATUSES, grp)

    def test_every_pin_resolves(self):
        for n in range(1, 201):
            self.assertNotEqual(self.entry(n)["status"], "free", f"pin {n} ({self.pins[n]['sig']}) not described")

    def test_gpio_used_once_and_modes_match_alt(self):
        seen = {}
        for n, p in self.pins.items():
            if p["grp"] != "GPIO":
                continue
            e = self.prj["pins"].get(str(n))
            self.assertIsNotNone(e, f"GPIO{p['gpio']} (pin {n}) unassigned")
            self.assertNotIn(p["gpio"], seen)
            seen[p["gpio"]] = n
            m = re.fullmatch(r"ALT(\d) (.+)", e["mode"])
            if m:
                self.assertEqual(self.ds["alt"][str(p["gpio"])]["alt"][int(m.group(1))], m.group(2), f"pin {n}")
            else:
                self.assertEqual(e["mode"], "GPIO", f"pin {n}")
        self.assertEqual(sorted(seen), list(range(28)))

    def test_nets_unique_outside_power(self):
        nets = {}
        for n in range(1, 201):
            e = self.entry(n)
            if not e["net"] or self.pins[n]["grp"] in ("GND", "PWR5", "PWR33"):
                continue
            self.assertNotIn(e["net"], nets, f"net {e['net']}: pins {nets.get(e['net'])} and {n}")
            nets[e["net"]] = n

    def test_diff_pair_polarity_and_modes(self):
        for n, e in self.prj["pins"].items():
            p = self.pins[int(n)]
            m = re.search(r"_([PN])$", e.get("net", ""))
            if m and "pair" in p:
                self.assertTrue(p["sig"].endswith("_" + m.group(1)), f"pin {n}: {e['net']} vs {p['sig']}")
        modes = {36: "ALT4 TXD2", 35: "ALT4 RXD2", 58: "ALT0 SDA1", 56: "ALT0 SCL1", 54: "ALT4 TXD3", 34: "ALT4 RXD3",
                 37: "ALT4 RTS3", 39: "ALT4 TXD4", 40: "ALT4 RXD4", 38: "ALT4 RTS4", 31: "ALT4 TXD5", 28: "ALT4 RXD5",
                 55: "ALT0 TXD0", 51: "ALT0 RXD0", 49: "ALT5 PWM0_0", 27: "ALT3 SPI6_MOSI", 25: "ALT3 SPI6_SCLK"}
        for n, mode in modes.items():
            self.assertEqual(self.prj["pins"][str(n)]["mode"], mode, f"pin {n}")

    def test_approved_allocation(self):
        expect = {36: "UART2_TXD", 35: "UART2_RXD", 58: "I2C1_SDA", 56: "I2C1_SCL", 54: "UART3_TXD", 34: "UART3_RXD",
                  30: "CVBS_SEL0", 37: "CRSF1_DIR", 39: "UART4_TXD", 40: "UART4_RXD", 44: "CVBS_SEL1", 38: "CRSF2_DIR",
                  31: "UART5_TXD", 28: "UART5_RXD", 55: "UART0_TXD", 51: "UART0_RXD", 29: "CRSF2_INV", 50: "TX1_PWR_EN",
                  49: "FAN_PWM", 26: "TX2_PWR_EN", 27: "VRX_DATA", 25: "VRX_CLK", 46: "VRX_LE1", 47: "VRX_LE2",
                  45: "VRX_LE3", 41: "VRX_LE4", 24: "FAN_TACH", 48: "CRSF1_INV",
                  99: "GLOBAL_EN", 92: "RUN_PG", 93: "nRPIBOOT", 78: "CM4_3V3", 102: "PCIE_CLKREQ_N", 116: "PCIE_RX_P",
                  115: "CSI1_D0_N", 117: "CSI1_D0_P", 127: "CSI1_CLK_N", 129: "CSI1_CLK_P"}
        for n, net in expect.items():
            self.assertEqual(self.entry(n)["net"], net, f"pin {n}")
        for n in (115, 117, 127, 129):
            self.assertEqual(self.entry(n)["dev"], "VDEC"); self.assertEqual(self.entry(n)["status"], "used")
        for n in (121, 123, 133, 135, 139, 141):
            self.assertEqual(self.entry(n)["dev"], "VDEC"); self.assertEqual(self.entry(n)["status"], "nc")
        self.assertEqual(self.entry(76)["status"], "dnc")
        self.assertEqual(self.entry(1)["net"], "GND")
        self.assertEqual(self.entry(146)["status"], "nc")
        notes = {n: self.prj["pins"][str(n)]["note"] for n in (116, 118, 122, 124)}
        self.assertIn("PERp0", notes[116]); self.assertIn("PERn0", notes[118])
        self.assertIn("PETp0", notes[122]); self.assertIn("PETn0", notes[124])
        self.assertIn("0x21", self.prj["pins"]["82"]["note"])


if __name__ == "__main__":
    unittest.main()
