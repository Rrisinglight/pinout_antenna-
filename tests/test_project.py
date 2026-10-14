import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUSES = {"used", "opt", "free", "nc", "dnc"}
DIRS = {"gnd", "power_in", "power_out", "in", "out", "bidir", "nc"}
CYR = re.compile(r"[Ѐ-ӿ]")
TAG = re.compile(r"\[(Review/(power-board|crsf-one-wire|vrx-board|analog-to-csi|website|README)\.md(?: (?:п\.|разд\.) [0-9][0-9., –-]*)?|DS §[0-9.]+(?:, Table \d+)?|DS Table \d+|DS Fig\. \d+|BCM2711 §[0-9.]+|ТЗ|project|sdtv2csi|CM4IO)\]$")
DEVICES = {"CONSOLE", "GPS", "CRSF1", "CRSF2", "SERVO", "I2C", "VRX", "FAN", "PCIE", "CAM", "I2C0", "VDEC",
           "USB", "ETH", "CTRL", "POWER", "SPARE", "GND", "NC"}
CAM_LANES = (115, 117, 121, 123, 127, 129, 133, 135, 139, 141)
VDEC_USED = (128, 130, 140, 142)
# spec §4.4: names of the old plan that must not survive as identifiers
STALE = ["VRX_LE", "CSI1_D0_", "CSI1_CLK_", "CSI0_D0_", "CSI0_D1_", "CSI0_CLK_", "CRSF1_DIR", "CRSF2_DIR", "RTS3", "RTS4",
         "I2C0_SDA", "I2C0_SCL", "I2C1_SDA", "I2C1_SCL", "CM4_3V3", "TX1_PWR_EN", "TX2_PWR_EN", "CVBS switch"]
CONN_J = re.compile(r"\bJ[12]\b")


class TestProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = json.loads((ROOT / "data" / "cm4_datasheet.json").read_text(encoding="utf-8"))
        cls.prj = json.loads((ROOT / "data" / "project.json").read_text(encoding="utf-8"))
        cls.pins = {p["n"]: p for p in cls.ds["pins"]}

    def entry(self, n):
        p = self.pins[n]
        e = self.prj["pins"].get(str(n)) or self.prj["defaults"].get(p["grp"]) or {}
        return {"net": e.get("net", ""), "dev": e.get("dev", "NC"), "mode": e.get("mode", ""), "dir": e.get("dir", ""),
                "status": e.get("status", "used" if str(n) in self.prj["pins"] else "free"), "note": e.get("note", ""),
                "issues": e.get("issues", [])}

    def test_shape_v3(self):
        for key in ("meta", "devices", "defaults", "pins"):
            self.assertIn(key, self.prj)
        for key in ("ds_notes", "facts"):
            self.assertNotIn(key, self.prj)
        self.assertEqual(set(self.prj["devices"]), DEVICES)
        for k, d in self.prj["devices"].items():
            self.assertTrue(d["name"] and re.fullmatch(r"#[0-9A-Fa-f]{6}", d["c"]), k)
        meta = self.prj["meta"]
        self.assertEqual(meta["rev"], "3")
        self.assertEqual(meta["date"], "2026-10-15")
        self.assertIn("schematic", meta)

    def test_notes_russian(self):
        for k, e in self.prj["pins"].items():
            self.assertIsNotNone(CYR.search(e.get("note", "")), f"pin {k} note is not Russian")
            for f in ("net", "mode", "dev"):
                self.assertTrue(e.get(f, "").isascii(), f"pin {k} {f} must stay ASCII")
            self.assertIsInstance(e.get("issues", []), list, f"pin {k} issues must be a list")
            for t in e.get("issues", []):
                self.assertIsNotNone(CYR.search(t), f"pin {k} issue is not Russian: {t[:40]}")
                self.assertTrue(10 <= len(t) <= 320, f"pin {k} issue length {len(t)}: {t[:40]}")
                self.assertRegex(t, TAG, f"pin {k}: missing/invalid source tag: {t[-40:]}")
            if "dir" in e:
                self.assertIn(e["dir"], DIRS, f"pin {k} dir")
        for g, e in self.prj["defaults"].items():
            self.assertIsNotNone(CYR.search(e.get("note", "")), f"defaults {g} note is not Russian")
        for k, d in self.prj["devices"].items():
            self.assertIsNone(CYR.search(d["name"]), f"device {k} name must stay English")

    def test_dir_required(self):
        for k, e in self.prj["pins"].items():
            if self.pins[int(k)]["grp"] == "GPIO" or int(k) in (80, 82):
                self.assertIn("dir", e, f"pin {k} has no dir")

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
        spare = sorted(gpio for gpio, n in seen.items() if self.prj["pins"][str(n)]["dev"] == "SPARE")
        self.assertEqual(spare, [7, 11, 17, 19])

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
                 39: "ALT4 TXD4", 40: "ALT4 RXD4", 31: "ALT4 TXD5", 28: "ALT4 RXD5", 30: "GPIO", 44: "GPIO",
                 55: "ALT0 TXD0", 51: "ALT0 RXD0", 49: "ALT5 PWM0_0", 27: "ALT3 SPI6_MOSI", 25: "ALT3 SPI6_SCLK"}
        for n, mode in modes.items():
            self.assertEqual(self.prj["pins"][str(n)]["mode"], mode, f"pin {n}")

    def test_approved_allocation(self):
        expect = {36: "UART2_TXD", 35: "UART2_RXD", 58: "SDA1", 56: "SCL1", 54: "UART3_TXD", 34: "UART3_RXD",
                  30: "CVBS_SEL0", 44: "CVBS_SEL1", 39: "UART4_TXD", 40: "UART4_RXD", 31: "UART5_TXD", 28: "UART5_RXD",
                  55: "UART0_TXD", 51: "UART0_RXD", 29: "CRSF2_INV", 48: "CRSF1_INV", 49: "FAN_PWM", 24: "FAN_TACH",
                  27: "VRX_DATA", 25: "VRX_CLK", 46: "VRX_SS1", 47: "VRX_SS2", 45: "VRX_SS3", 41: "VRX_SS4",
                  37: "", 38: "", 50: "", 26: "",
                  99: "GLOBAL_EN", 92: "RUN_PG", 93: "nRPIBOOT", 78: "+3V", 77: "+5V_CM", 84: "+3V",
                  80: "SCL0", 82: "SDA0", 97: "CAM_GPIO", 21: "A_LED_G", 15: "E_LED_Y", 17: "E_LED_G", 95: "NPWR_LED", 100: "NEXTRST",
                  4: "TD1+", 6: "TD1-", 10: "TD0-", 12: "TD0+", 101: "USBOTG_ID", 103: "USB2_N", 105: "USB2_P",
                  102: "PCIE_CLKREQ_N", 116: "PCIE_RX_P",
                  115: "CAM1_D0_N", 117: "CAM1_D0_P", 121: "CAM1_D1_N", 123: "CAM1_D1_P", 127: "CAM1_C_N", 129: "CAM1_C_P",
                  133: "CAM1_D2_N", 135: "CAM1_D2_P", 139: "CAM1_D3_N", 141: "CAM1_D3_P",
                  128: "CAM0_D0_N", 130: "CAM0_D0_P", 134: "CAM0_D1_N", 136: "CAM0_D1_P", 140: "CAM0_C_N", 142: "CAM0_C_P"}
        for n, net in expect.items():
            self.assertEqual(self.entry(n)["net"], net, f"pin {n}")
        for n in CAM_LANES:
            self.assertEqual(self.entry(n)["dev"], "CAM", f"pin {n}"); self.assertEqual(self.entry(n)["status"], "used", f"pin {n}")
        for n in VDEC_USED:
            self.assertEqual(self.entry(n)["dev"], "VDEC", f"pin {n}"); self.assertEqual(self.entry(n)["status"], "used", f"pin {n}")
        for n in (134, 136):
            self.assertEqual(self.entry(n)["dev"], "VDEC", f"pin {n}"); self.assertEqual(self.entry(n)["status"], "opt", f"pin {n}")
        for n in (30, 44):
            self.assertEqual(self.entry(n)["dev"], "VRX", f"pin {n}")
        for n in (80, 82):
            self.assertEqual(self.entry(n)["dev"], "I2C0", f"pin {n}")
        for n in (37, 38, 50, 26):
            e = self.entry(n)
            self.assertEqual((e["dev"], e["status"], e["mode"]), ("SPARE", "opt", "GPIO"), f"pin {n}")
        for n in (3, 5, 9, 11):
            self.assertEqual(self.entry(n)["status"], "opt", f"pin {n}")
        for n in (57, 61, 62, 63, 67, 69, 75, 111):
            self.assertIn(str(n), self.prj["pins"], f"pin {n} must be explicit")
            self.assertEqual(self.entry(n)["status"], "nc", f"pin {n}")
            self.assertGreaterEqual(len(self.entry(n)["issues"]), 1, f"pin {n}")
        for n in (98, 197, 198):
            self.assertIn(str(n), self.prj["pins"], f"pin {n} must be explicit")
            e = self.entry(n)
            self.assertEqual((e["net"], e["dev"]), ("GND", "GND"), f"pin {n}")
            self.assertGreaterEqual(len(e["issues"]), 1, f"pin {n}")
        self.assertEqual(self.entry(76)["status"], "dnc")
        self.assertEqual(self.entry(1)["net"], "GND")
        self.assertEqual(self.entry(146)["status"], "nc")
        notes = {n: self.prj["pins"][str(n)]["note"] for n in (116, 118, 122, 124)}
        self.assertIn("PERp0", notes[116]); self.assertIn("PERn0", notes[118])
        self.assertIn("PETp0", notes[122]); self.assertIn("PETn0", notes[124])
        p82, p58, p97 = self.prj["pins"]["82"], self.prj["pins"]["58"], self.prj["pins"]["97"]
        self.assertGreaterEqual(len(p82["issues"]), 2)
        self.assertIn("0x21", p82["note"]); self.assertIn("ADS1115", p82["note"])
        self.assertIn("TCA9534A", p58["note"]); self.assertIn("INA219", p58["note"])
        self.assertIn("PWR_3V", p97["note"] + " " + " ".join(p97.get("issues", [])))

    def test_no_stale_wording(self):
        idents = [(f"pin {k} {f}", e.get(f, "")) for k, e in self.prj["pins"].items() for f in ("net", "mode", "dev")]
        idents += [(f"defaults {g} {f}", e.get(f, "")) for g, e in self.prj["defaults"].items() for f in ("net", "mode", "dev")]
        idents += [(f"device {k} name", d["name"]) for k, d in self.prj["devices"].items()]
        for where, text in idents:
            for bad in STALE:
                self.assertNotIn(bad, text, f"{where}: stale {bad!r}")
            self.assertIsNone(CONN_J.search(text), f"{where}: J1/J2 as a connector name")
        for n in VDEC_USED:
            self.assertNotIn("CSI1", self.prj["pins"][str(n)]["note"], f"pin {n}: decoder note mentions CSI1")
        for n in range(115, 142):
            if str(n) in self.prj["pins"]:
                self.assertNotIn("CSI0", self.prj["pins"][str(n)]["note"], f"pin {n}: note in 115–141 mentions CSI0")


if __name__ == "__main__":
    unittest.main()
