#!/usr/bin/env python3
"""Embeds data/cm4_datasheet.json, data/project.json, data/routing.json, data/ds_ru.json and data/rationale.json into cm4_pinout.html between /*DATA-START*/ and /*DATA-END*/.
Run from the repo root: python3 tools/build.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "cm4_pinout.html"
MARK = re.compile(r"/\*DATA-START\*/.*?/\*DATA-END\*/", re.S)


def dumps(obj):
    # "</" must not appear inside <script>; escape it just in case
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def build():
    ds = json.loads((ROOT / "data" / "cm4_datasheet.json").read_text(encoding="utf-8"))
    prj = json.loads((ROOT / "data" / "project.json").read_text(encoding="utf-8"))
    rt = json.loads((ROOT / "data" / "routing.json").read_text(encoding="utf-8"))
    dsru = json.loads((ROOT / "data" / "ds_ru.json").read_text(encoding="utf-8"))
    rat = json.loads((ROOT / "data" / "rationale.json").read_text(encoding="utf-8"))
    block = ("/*DATA-START*/\nvar DATA = " + dumps(ds) + ";\nvar PROJECT = " + dumps(prj) +
             ";\nvar ROUTING = " + dumps(rt) + ";\nvar DS_RU = " + dumps(dsru) +
             ";\nvar RATIONALE = " + dumps(rat) + ";\n/*DATA-END*/")
    src = HTML.read_text(encoding="utf-8")
    if len(MARK.findall(src)) != 1:
        raise SystemExit("cm4_pinout.html must contain exactly one DATA-START…DATA-END block")
    new = MARK.sub(lambda m: block, src, count=1)
    HTML.write_text(new, encoding="utf-8")
    return len(new)


if __name__ == "__main__":
    print(f"ok {build()} bytes -> {HTML}")
