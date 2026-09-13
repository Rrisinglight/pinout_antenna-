import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = (Path(__file__).resolve().parent.parent / "cm4_pinout.html").as_uri()


class TestPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        self.errors = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.goto(URL)

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.page.close()

    def visible_pads(self):
        return self.page.evaluate("[...document.querySelectorAll('g.pad')].filter(g => !g.classList.contains('dim')).length")

    def test_board_geometry(self):
        self.assertEqual(self.page.locator("g.pad").count(), 200)
        self.assertEqual(self.page.evaluate("document.querySelector('g.pad[data-n=\"1\"] rect').getAttribute('y')"), "34")
        self.assertEqual(self.page.evaluate("document.querySelector('g.pad[data-n=\"101\"] rect').getAttribute('y')"), "484")
        self.assertEqual(self.page.locator("#outline").count(), 1)
        self.assertEqual(self.page.locator("#board .hole").count(), 4)
        self.assertEqual(self.page.locator("#board .conn").count(), 2)
        self.assertEqual(self.page.locator("#board .ant").count(), 1)
        self.assertEqual(self.page.locator("#board .lead").count(), 0)
        self.assertEqual(self.page.evaluate("getComputedStyle(document.querySelector('.board-wrap')).borderTopStyle"), "none")
        self.assertIn("Antenna keep-out", self.page.locator("#board").text_content())
        self.assertEqual(self.page.locator("#q").count(), 0)
        w = self.page.evaluate("(e=>[e.scrollWidth,e.clientWidth])(document.querySelector('.board-wrap'))")
        self.assertLessEqual(w[0], w[1])

    def test_pin_panel_english(self):
        self.page.click('g.pad[data-n="55"]')
        text = self.page.locator("#panel").inner_text()
        for s in ("GPIO14", "J1", "odd (top) row", "Group", "Direction", "bidirectional", "Datasheet", "boot pull-down"):
            self.assertIn(s, text)
        self.assertNotIn("UART0_TXD", text)
        self.assertIn("TXD0", self.page.locator("#panel table.alt").inner_text())
        self.assertTrue(self.page.evaluate("document.body.classList.contains('has-sel')"))

    def test_project_layer_and_routing_card(self):
        self.page.click('.seg button[data-layer="prj"]')
        self.page.click('g.pad[data-n="116"]')
        text = self.page.locator("#panel").inner_text()
        for s in ("PCIE_RX_P", "PCIe → M.2 NVMe", "PERp0", "Differential pair", "118", "90 Ω"):
            self.assertIn(s, text)
        self.assertTrue(self.page.evaluate("document.querySelector('g.pad[data-n=\"118\"]').classList.contains('mate')"))
        rt = self.page.locator("#routing").inner_text()
        self.assertIn("Routing notes · pin 116", rt)
        self.assertGreaterEqual(self.page.locator("#routing li").count(), 7)
        self.assertIn("PERp0", rt); self.assertIn("90 Ω", rt)
        self.page.click('g.pad[data-n="76"]')
        self.assertTrue(self.page.evaluate("document.querySelector('g.pad[data-n=\"76\"]').classList.contains('dnc')"))
        self.assertIn("do not connect", self.page.locator("#panel").inner_text())

    def test_routing_card_gnd_pin(self):
        self.page.click('g.pad[data-n="1"]')
        rt = self.page.locator("#routing").inner_text()
        self.assertIn("Routing notes · pin 1", rt)
        self.assertEqual(self.page.locator("#routing li").count(), 1)
        self.assertIn("ground pin", rt)

    def test_legend_filter_and_summary(self):
        self.page.click('#leg .lg[data-k="PCIE"]')
        self.assertEqual(self.visible_pads(), 8)
        self.assertIn("8 pins", self.page.locator("#panel").inner_text())
        self.assertIn("Routing notes", self.page.locator("#routing").inner_text())
        self.assertEqual(self.page.locator("#routing li").count(), self.page.evaluate("ROUTING.groups.PCIE.length"))
        self.page.click('#leg .lg[data-k="PCIE"]')
        self.assertEqual(self.visible_pads(), 200)
        self.page.click('.seg button[data-layer="prj"]')
        self.page.click('#leg .lg[data-k="VDEC"]')
        self.assertEqual(self.visible_pads(), 4)   # 115/117/127/129; the six unused CSI1 lanes are status nc → "Not used"
        self.assertGreaterEqual(self.page.locator("#routing li").count(), 1)

    def test_keyboard(self):
        self.page.click('g.pad[data-n="55"]')
        self.page.keyboard.press("ArrowRight")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 53)
        self.page.keyboard.press("ArrowLeft"); self.page.keyboard.press("ArrowLeft")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 57)
        self.page.keyboard.press("ArrowDown")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 58)
        self.page.keyboard.press("ArrowUp")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 57)
        self.page.keyboard.press("Escape")
        self.assertIsNone(self.page.evaluate("PINOUT.state.sel"))
        self.page.focus('g.pad[data-n="3"]'); self.page.keyboard.press("Enter")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 3)

    def test_general_section(self):
        n = self.page.evaluate("ROUTING.general.length")
        self.assertEqual(self.page.locator("#general h3").count(), n)
        self.assertIn("Layout notes", self.page.locator("#general").inner_text())

    def test_table_and_csv(self):
        self.assertEqual(self.page.locator("#tbl tbody tr.row").count(), 200)
        heads = self.page.locator("#tbl thead th").all_inner_texts()
        self.assertEqual(heads[:5], ["#", "Conn.", "Signal", "Group", "Dir."])
        self.page.click('.seg button[data-layer="prj"]')
        self.assertEqual(self.page.locator('#tbl tbody tr.row[data-n="55"] .c-net').inner_text(), "UART0_TXD")
        self.page.click('#tbl tbody tr.row[data-n="92"]')
        self.assertIn("RUN_PG", self.page.locator("#panel h2").inner_text())
        self.page.click("#csv")
        self.page.wait_for_function("document.querySelector('#csv').textContent.includes('Copied') || document.querySelector('#csvdlg').open")
        text = self.page.evaluate("LIB.csv(DATA.pins, PROJECT)")
        self.assertTrue(text.startswith("pin;connector;row;signal") and text.split("\n")[0].endswith(";datasheet"))

    def test_mobile(self):
        page = self.browser.new_page(viewport={"width": 400, "height": 800})
        page.goto(URL)
        self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"))
        page.evaluate("PINOUT.select(92)")
        box = page.locator(".side").bounding_box()
        self.assertLessEqual(box["y"] + box["height"], 801)
        self.assertIn("RUN_PG", page.locator("#panel").inner_text())
        page.click("#panel .close")
        self.assertIsNone(page.evaluate("PINOUT.state.sel"))
        page.close()


if __name__ == "__main__":
    unittest.main()
