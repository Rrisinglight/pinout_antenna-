#!/usr/bin/env python3
"""Слой «Даташит»: PDF → data/cm4_datasheet.json.

Источники: RP-008168-DS-4-cm4-datasheet.pdf (табл. 6 — пины, табл. 7/8 — дифф-пары),
RP-008248-DS-1-bcm2711-peripherals.pdf (табл. 94 — ALT-функции GPIO0–27).
Запуск из корня репо: python3 tools/extract_datasheet.py   (нужен pdftotext, poppler-utils)
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CM4_PDF = ROOT / "RP-008168-DS-4-cm4-datasheet.pdf"
BCM_PDF = ROOT / "RP-008248-DS-1-bcm2711-peripherals.pdf"
OUT = ROOT / "data" / "cm4_datasheet.json"

SKIP = re.compile(r"^\s*(Pinout\s+\d+|Raspberry Pi Compute Module 4|Pin\s+Signal\s+Description)\s*$")
ROW = re.compile(r"^\s{1,4}(\d{1,3})\s{2,}(\S.*?)\s{2,}(\S.*)$")
GROUP_PREFIX = [("Ethernet_", "ETH"), ("SD_", "SD"), ("USB_", "USB"), ("PCIe_", "PCIE"),
                ("CAM0_", "CSI0"), ("CAM1_", "CSI1"), ("HDMI0_", "HDMI0"), ("HDMI1_", "HDMI1"),
                ("DSI0_", "DSI0"), ("DSI1_", "DSI1"), ("AnalogIP", "ANALOG")]
DIR_BY_SIG = {
    "EEPROM_nWP": "in", "Pi_nLED_Activity": "out", "SD_VDD_OVERRIDE": "in", "SD_PWR_ON": "out",
    "GPIO_VREF": "power_in", "SCL0": "bidir", "SDA0": "bidir", "WL_nDisable": "bidir",
    "BT_nDisable": "bidir", "RUN_PG": "bidir", "nRPIBOOT": "in", "PI_LED_nPWR": "out",
    "Camera_GPIO": "out", "GLOBAL_EN": "in", "nEXTRST": "out", "USB_OTG_ID": "in",
    "PCIe_CLK_nREQ": "in", "PCIe_nRST": "out", "VDAC_COMP": "out", "Reserved": "nc",
    "Ethernet_SYNC_IN": "in", "Ethernet_SYNC_OUT": "out",
}


def pdftext(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                          capture_output=True, text=True).stdout.splitlines()


def parse_pins(lines):
    start = next(i for i, l in enumerate(lines) if l.startswith("Pinout for the Raspberry Pi Compute Module 4"))
    end = next(i for i, l in enumerate(lines) if l.startswith("All ground pins should be connected"))
    pins, cur = [], None
    for l in lines[start + 1:end]:
        if not l.strip() or SKIP.match(l):
            continue
        m = ROW.match(l)
        if m and (cur is None or int(m.group(1)) == cur["n"] + 1):
            cur = {"n": int(m.group(1)), "sig": m.group(2).strip(), "ds": m.group(3).strip()}
            pins.append(cur)
        elif cur is not None:
            cur["ds"] += " " + l.strip()
    for p in pins:
        p["ds"] = re.sub(r"\s+", " ", p["ds"]).replace("( ", "(").replace(" .", ".")
    return pins, end


def parse_pair_lengths(lines):
    """Табл. 7 (100 Ω) и 8 (90 Ω): имя сигнала -> {z, skew}. lines — текст ПОСЛЕ таблицы пинов."""
    out, z = {}, None
    for l in lines:
        if "100Ω differential pair signal lengths" in l:
            z = 100
        elif "90Ω differential pair signal lengths" in l:
            z = 90
        elif l.startswith("5. Power"):
            break
        elif z:
            m = re.match(r"^\s+([A-Za-z0-9_]+_[PN])\s+([\d.]+)\s*$", l)
            if m:
                out[m.group(1)] = {"z": z, "skew": float(m.group(2))}
    return out


def parse_alt(lines):
    """Табл. 94 BCM2711: GPIO0..27 -> {pull, alt[6]}."""
    i = next(i for i, l in enumerate(lines) if "Table 94. GPIO Pins" in l)
    j = next(i for i, l in enumerate(lines) if "Table 95. GPIO Pins" in l)
    rows, alt, k = lines[i:j], {}, 0
    while k < len(rows):
        m = re.match(r"^\s+GPIO(\d+)\s+(High|Low|-)\s+(.*)$", rows[k])
        if m and int(m.group(1)) <= 27:
            cells = re.split(r"\s{2,}", m.group(3).strip())
            nxt = rows[k + 1] if k + 1 < len(rows) else ""
            if nxt.strip() and not re.match(r"^\s+GPIO\d+", nxt):
                # строка-продолжение ("SRW_N", "MOSI", "SCLK") клеится к ячейке по позиции колонки
                pos = len(nxt) - len(nxt.lstrip())
                best = None
                for c in cells:
                    if rows[k].find(c) <= pos + 1:
                        best = c
                cells[cells.index(best)] = best + " " + nxt.strip()
                k += 1
            while len(cells) < 6:
                cells.append("")
            alt[str(int(m.group(1)))] = {"pull": m.group(2), "alt": cells[:6]}
        k += 1
    return alt


def classify(sig):
    if sig == "GND":
        return "GND"
    if sig.startswith("+5V"):
        return "PWR5"
    if sig.startswith("CM4_3.3V") or sig == "GPIO_VREF":
        return "PWR33"
    if sig.startswith("CM4_1.8V"):
        return "PWR18"
    if re.fullmatch(r"GPIO\d+", sig) or sig in ("ID_SD", "ID_SC"):
        return "GPIO"
    if sig in ("SCL0", "SDA0"):
        return "I2C0"
    if sig == "Reserved":
        return "RSV"
    if sig == "VDAC_COMP":
        return "VDAC"
    for pre, grp in GROUP_PREFIX:
        if sig.startswith(pre):
            return grp
    return "CTRL"


def direction(sig, grp, ds):
    if sig in DIR_BY_SIG:
        return DIR_BY_SIG[sig]
    if grp == "GND":
        return "gnd"
    if grp == "PWR5":
        return "power_in"
    if grp in ("PWR33", "PWR18"):
        return "power_out"
    if grp in ("GPIO", "SD", "USB", "I2C0"):
        return "bidir"
    if grp == "ETH":
        return "out" if "_nLED" in sig else "bidir"
    if grp == "ANALOG":
        return "in"
    if sig.startswith("PCIe_CLK_"):
        return "out"
    for word, d in (("Input", "in"), ("Output", "out"), ("Bidirectional", "bidir")):
        if ds.startswith(word):
            return d
    raise ValueError(f"нет правила направления для {sig}: {ds[:50]}")


def gpio_num(sig, ds):
    m = re.fullmatch(r"GPIO(\d+)", sig)
    if m:
        return int(m.group(1))
    m = re.search(r"BCM2711 GPIO ?(\d+)", ds)
    return int(m.group(1)) if m else None


def attach_pairs(pins, lengths):
    by_sig = {p["sig"]: p for p in pins}
    for p in pins:
        m = re.fullmatch(r"(.+)_([PN])", p["sig"])
        if not m:
            continue
        partner = by_sig.get(f"{m.group(1)}_{'N' if m.group(2) == 'P' else 'P'}")
        if partner is None:
            continue
        info = lengths[p["sig"].replace("USB_", "USB2_")]  # табл. 8 зовёт пару USB2_P/N
        p["pair"] = {"partner": partner["n"], "z": info["z"], "skew": info["skew"]}


def main():
    cm4 = pdftext(CM4_PDF)
    pins, end = parse_pins(cm4)
    for p in pins:
        p["conn"] = "J1" if p["n"] <= 100 else "J2"
        p["row"] = "odd" if p["n"] % 2 else "even"
        p["grp"] = classify(p["sig"])
        p["dir"] = direction(p["sig"], p["grp"], p["ds"])
        g = gpio_num(p["sig"], p["ds"])
        if g is not None:
            p["gpio"] = g
    attach_pairs(pins, parse_pair_lengths(cm4[end:]))
    data = {"source": {"cm4": CM4_PDF.name, "bcm2711": BCM_PDF.name},
            "pins": pins, "alt": parse_alt(pdftext(BCM_PDF))}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"pins={len(pins)} pairs={sum('pair' in p for p in pins)} alt={len(data['alt'])} -> {OUT}")


if __name__ == "__main__":
    main()
