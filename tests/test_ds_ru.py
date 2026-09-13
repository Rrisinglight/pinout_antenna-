import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CYR = re.compile(r"[Ѐ-ӿ]")


class TestDsRu(unittest.TestCase):
    def test_covers_every_datasheet_string(self):
        ds = json.loads((ROOT / "data" / "cm4_datasheet.json").read_text(encoding="utf-8"))
        ru = json.loads((ROOT / "data" / "ds_ru.json").read_text(encoding="utf-8"))
        uniq = {p["ds"] for p in ds["pins"]}
        self.assertEqual(set(ru), uniq, "ds_ru.json keys must equal the set of unique datasheet strings")
        for en, tr in ru.items():
            self.assertIsInstance(tr, str)
            self.assertTrue(tr.strip(), en)
            self.assertIsNotNone(CYR.search(tr), f"not Russian: {en[:40]}")
            self.assertLessEqual(len(tr), 2 * len(en) + 60, f"too long: {en[:40]}")
            for token in re.findall(r"\b\d+(?:\.\d+)?\b", en):   # every number of the original must survive
                self.assertIn(token, tr, f"number {token} lost in: {en[:50]}")


if __name__ == "__main__":
    unittest.main()
