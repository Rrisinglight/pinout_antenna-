import json, re, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "cm4_pinout.html"


class TestBuild(unittest.TestCase):
    def test_build_embeds_data_and_is_idempotent(self):
        subprocess.run([sys.executable, str(ROOT / "tools" / "build.py")], check=True, capture_output=True)
        first = HTML.read_text(encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "tools" / "build.py")], check=True, capture_output=True)
        self.assertEqual(first, HTML.read_text(encoding="utf-8"))
        m = re.search(r"/\*DATA-START\*/\nvar DATA = (.*?);\nvar PROJECT = (.*?);\nvar ROUTING = (.*?);\nvar DS_RU = (.*?);\nvar RATIONALE = (.*?);\n/\*DATA-END\*/", first, re.S)
        self.assertIsNotNone(m)
        data = json.loads(m.group(1).replace("<\\/", "</"))
        prj = json.loads(m.group(2).replace("<\\/", "</"))
        self.assertEqual(data, json.loads((ROOT / "data" / "cm4_datasheet.json").read_text(encoding="utf-8")))
        self.assertEqual(prj, json.loads((ROOT / "data" / "project.json").read_text(encoding="utf-8")))
        self.assertEqual(json.loads(m.group(3).replace("<\\/", "</")), json.loads((ROOT / "data" / "routing.json").read_text(encoding="utf-8")))
        self.assertEqual(json.loads(m.group(4).replace("<\\/", "</")), json.loads((ROOT / "data" / "ds_ru.json").read_text(encoding="utf-8")))
        self.assertEqual(json.loads(m.group(5).replace("<\\/", "</")), json.loads((ROOT / "data" / "rationale.json").read_text(encoding="utf-8")))
        self.assertEqual(first.count("/*DATA-START*/"), 1)

    def test_self_contained(self):
        src = HTML.read_text(encoding="utf-8")
        self.assertNotIn("fetch(", src)
        self.assertNotIn("<script src=", src)
        self.assertNotIn("<link ", src)
        self.assertNotIn("http://", src.split("/*DATA-START*/")[0])
        self.assertLess(len(src.encode("utf-8")), 1_000_000)


if __name__ == "__main__":
    unittest.main()
