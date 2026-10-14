"""Build data/schematic.json: what the Retr_Cross carrier wires to each CM4 pin.

The source, Review/_data/chains.json, is a read-only snapshot of the EasyEDA
project. To refresh it: re-export the project in EasyEDA, run
Review/_tools/build_chains.py, then run this script.

Usage: extract_schematic.py [--check]
  --check  compare the would-be output with data/schematic.json; exit 1 on
           the first differing pin.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAINS = ROOT / "Review" / "_data" / "chains.json"
OUT = ROOT / "data" / "schematic.json"
SNAPSHOT = "2026-10-14 12:28–12:34"


def build():
    rows = json.loads(CHAINS.read_text(encoding="utf-8"))["cm4_map"]
    pins = {}
    for r in sorted(rows, key=lambda r: r["cm4_pin"]):
        to = (r.get("sch_destinations") or []) + (r.get("sch_destinations_via_series_part") or [])
        pins[str(r["cm4_pin"])] = {
            "net": r.get("sch_net") or "",
            "to": to[:6],
            "wired": r.get("wired_beyond_cm4"),
        }
    return {
        "source": {
            "project": "Retr_2026-09-26",
            "board": "Retr_Cross",
            "snapshot": SNAPSHOT,
            "chains": "Review/_data/chains.json",
        },
        "pins": pins,
    }


def render(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def main(argv):
    obj = build()
    text = render(obj)
    if "--check" in argv:
        have = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if have == text:
            return 0
        try:
            old = json.loads(have)
        except ValueError:
            old = {}
        if old.get("source") != obj["source"]:
            print("differs: source")
        else:
            for k, v in obj["pins"].items():
                if old.get("pins", {}).get(k) != v:
                    print(f"differs: pin {k}: have {old.get('pins', {}).get(k)} want {v}")
                    break
            else:
                print("differs: formatting")
        return 1
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote data/schematic.json ({len(obj['pins'])} pins)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
