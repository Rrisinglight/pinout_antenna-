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
        self.page.goto(URL)
        self.errors = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))

    def tearDown(self):
        self.assertEqual(self.errors, [])
        self.page.close()

    def visible_pads(self):
        return self.page.evaluate("[...document.querySelectorAll('g.pad')].filter(g => !g.classList.contains('dim')).length")

    def test_board_has_200_pads(self):
        self.assertEqual(self.page.locator("g.pad").count(), 200)
        self.assertEqual(self.page.evaluate("document.querySelector('g.pad[data-n=\"1\"] rect').getAttribute('x')"), "942")
        self.assertEqual(self.page.evaluate("document.querySelector('g.pad[data-n=\"100\"] rect').getAttribute('x')"), "60")

    def test_click_pin_shows_datasheet_panel(self):
        self.page.click('g.pad[data-n="55"]')
        panel = self.page.locator("#panel")
        self.assertIn("GPIO14", panel.inner_text())
        self.assertIn("J1", panel.inner_text())
        self.assertIn("нечётный", panel.inner_text())
        self.assertIn("TXD0", panel.locator("table.alt").inner_text())
        self.assertNotIn("UART0_TXD", panel.inner_text())
        self.assertTrue(self.page.evaluate("document.querySelector('g.pad[data-n=\"55\"]').classList.contains('sel')"))
        self.assertTrue(self.page.evaluate("document.body.classList.contains('has-sel')"))

    def test_project_layer(self):
        self.page.click('g.pad[data-n="55"]')
        self.page.click('.seg button[data-layer="prj"]')
        text = self.page.locator("#panel").inner_text()
        self.assertIn("UART0_TXD", text)
        self.assertIn("Консоль UART0", text)
        self.assertIn("ALT0 TXD0", text)
        self.assertTrue(self.page.evaluate("document.body.classList.contains('layer-prj')"))
        self.assertEqual(self.page.evaluate("document.querySelector('#panel table.alt td.on').textContent"), "TXD0")
        self.assertEqual(self.page.evaluate("document.querySelector('g.pad[data-n=\"55\"] rect').getAttribute('fill')"), "#8E6C3A")
        self.page.click('g.pad[data-n="76"]')
        self.assertTrue(self.page.evaluate("document.querySelector('g.pad[data-n=\"76\"]').classList.contains('dnc')"))
        self.assertIn("не подключать", self.page.locator("#panel").inner_text())

    def test_diff_pair_partner(self):
        self.page.click('g.pad[data-n="116"]')
        text = self.page.locator("#panel").inner_text()
        self.assertIn("PCIe_RX_N", text)
        self.assertIn("90 Ω", text)
        self.assertIn("0.23", text)
        self.assertTrue(self.page.evaluate("document.querySelector('g.pad[data-n=\"118\"]').classList.contains('mate')"))
        self.page.click("#panel button.pinbtn")
        self.assertIn("PCIe_RX_N", self.page.locator("#panel h2").inner_text())
        self.assertTrue(self.page.evaluate("document.querySelector('g.pad[data-n=\"118\"]').classList.contains('sel')"))

    def test_legend_filter(self):
        self.page.click('#leg .lg[data-k="PCIE"]')
        self.assertEqual(self.visible_pads(), 8)
        self.assertIn("8 пин", self.page.locator("#panel").inner_text())
        self.page.click('#leg .lg[data-k="PCIE"]')
        self.assertEqual(self.visible_pads(), 200)
        self.page.click('.seg button[data-layer="prj"]')
        self.page.click('#leg .lg[data-k="CRSF1"]')
        self.assertEqual(self.visible_pads(), 4)
        self.page.click('#leg .lg[data-k="NC"]')
        self.assertGreater(self.visible_pads(), 50)

    def test_search(self):
        self.page.click('.seg button[data-layer="prj"]')
        self.page.fill("#q", "uart3")
        self.assertEqual(self.visible_pads(), 4)   # 54, 34, 37 + CRSF1_INV (48): имя устройства содержит UART3
        self.page.fill("#q", "116")
        self.assertEqual(self.visible_pads(), 1)
        self.page.fill("#q", "")
        self.assertEqual(self.visible_pads(), 200)

    def test_keyboard(self):
        self.page.click('g.pad[data-n="55"]')
        self.page.keyboard.press("ArrowRight")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 53)
        self.page.keyboard.press("ArrowLeft")
        self.page.keyboard.press("ArrowLeft")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 57)
        self.page.keyboard.press("ArrowDown")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 58)
        self.page.keyboard.press("ArrowUp")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 57)
        self.page.click('#leg .lg[data-k="GPIO"]')
        self.page.keyboard.press("Escape")
        self.assertIsNone(self.page.evaluate("PINOUT.state.sel"))
        self.assertIsNone(self.page.evaluate("PINOUT.state.filter"))
        self.assertEqual(self.visible_pads(), 200)
        self.page.focus('g.pad[data-n="3"]')
        self.page.keyboard.press("Enter")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 3)

    def test_mobile_no_horizontal_scroll_and_bottom_sheet(self):
        page = self.browser.new_page(viewport={"width": 400, "height": 800})
        page.goto(URL)
        self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"))
        page.evaluate("PINOUT.select(92)")
        box = page.locator("#panel").bounding_box()
        self.assertLessEqual(box["y"] + box["height"], 801)
        self.assertIn("RUN_PG", page.locator("#panel").inner_text())
        page.click("#panel .close")
        self.assertIsNone(page.evaluate("PINOUT.state.sel"))
        page.close()

    def test_table_rows_and_click(self):
        self.assertEqual(self.page.locator("#tbl tbody tr.row").count(), 200)
        self.assertEqual(self.page.locator("#tbl thead th").count(), 12)
        self.assertFalse(self.page.locator('#tbl tbody tr.row[data-n="55"] .c-net').is_visible())
        self.page.click('.seg button[data-layer="prj"]')
        self.assertEqual(self.page.locator('#tbl tbody tr.row[data-n="55"] .c-net').inner_text(), "UART0_TXD")
        self.page.click('#tbl tbody tr.row[data-n="92"]')
        self.assertIn("RUN_PG", self.page.locator("#panel h2").inner_text())
        self.assertTrue(self.page.evaluate("document.querySelector('#tbl tbody tr.row[data-n=\"92\"]').classList.contains('sel')"))
        self.page.fill("#q", "pcie")
        self.assertEqual(self.page.evaluate("[...document.querySelectorAll('#tbl tbody tr.row')].filter(r => !r.hidden).length"), 8)
        self.assertEqual(self.page.locator("#cnt").inner_text(), "Показано 8 из 200")

    def test_csv_button(self):
        self.page.click("#csv")
        self.page.wait_for_function("document.querySelector('#csv').textContent.includes('Скопировано') || document.querySelector('#csvdlg').open")
        if self.page.evaluate("document.querySelector('#csvdlg').open"):
            text = self.page.locator("#csvdlg textarea").input_value()
        else:
            text = self.page.evaluate("LIB.csv(DATA.pins, PROJECT)")
        self.assertEqual(len(text.split("\n")), 201)
        self.assertTrue(text.startswith("pin;conn;row;signal"))

    def test_facts(self):
        n = self.page.evaluate("PROJECT.facts.length")
        self.assertEqual(self.page.locator("#facts li").count(), n)
        self.assertGreaterEqual(n, 12)


if __name__ == "__main__":
    unittest.main()
