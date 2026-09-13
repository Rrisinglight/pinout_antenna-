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
        self.assertIn("Зона без меди", self.page.locator("#board").text_content())
        self.assertNotEqual(self.page.evaluate("getComputedStyle(document.querySelector('#outline')).fill"), self.page.evaluate("getComputedStyle(document.body).backgroundColor"))
        self.assertEqual(self.page.locator("#q").count(), 0)
        w = self.page.evaluate("(e=>[e.scrollWidth,e.clientWidth])(document.querySelector('.board-wrap'))")
        self.assertLessEqual(w[0], w[1])

    def test_pin_panel(self):
        self.page.click('g.pad[data-n="55"]')
        text = self.page.locator("#panel").inner_text()
        for s in ("GPIO14", "J1", "нечётный", "Group", "Direction", "bidirectional", "Datasheet", "при загрузке pull-down"):
            self.assertIn(s, text)
        self.assertRegex(self.page.locator("#panel .dsq").inner_text(), "[А-Яа-я]")
        self.assertIn("GPIO: typically a 3.3V signal", self.page.locator("#panel .dsq-en").inner_text())
        self.assertNotIn("UART0_TXD", text)
        self.assertIn("TXD0", self.page.locator("#panel table.alt").inner_text())
        self.assertTrue(self.page.evaluate("document.body.classList.contains('has-sel')"))

    def test_project_layer_and_routing_card(self):
        self.page.click('.seg button[data-layer="prj"]')
        self.page.click('g.pad[data-n="116"]')
        text = self.page.locator("#panel").inner_text()
        for s in ("PCIE_RX_P", "PCIe → M.2 NVMe", "PERp0", "Differential pair", "118", "90 Ом"):
            self.assertIn(s, text)
        self.assertTrue(self.page.evaluate("document.querySelector('g.pad[data-n=\"118\"]').classList.contains('mate')"))
        rt = self.page.locator("#routing").inner_text()
        self.assertIn("Routing notes · pin 116", rt)
        self.assertGreaterEqual(self.page.locator("#routing li").count(), 7)
        self.assertIn("PERp0", rt); self.assertIn("90 Ом", rt)
        self.page.click('g.pad[data-n="76"]')
        self.assertTrue(self.page.evaluate("document.querySelector('g.pad[data-n=\"76\"]').classList.contains('dnc')"))
        self.assertIn("do not connect", self.page.locator("#panel").inner_text())

    def test_routing_card_gnd_pin(self):
        self.page.click('g.pad[data-n="1"]')
        rt = self.page.locator("#routing").inner_text()
        self.assertIn("Routing notes · pin 1", rt)
        self.assertEqual(self.page.locator("#routing li").count(), 1)
        self.assertIn("GND", rt); self.assertRegex(rt, "[А-Яа-я]")
        self.page.click('.seg button[data-layer="prj"]')   # pin 1 stays selected across the layer switch
        self.assertIn("Земля — обоснование не требуется", self.page.locator("#design").inner_text())
        self.page.click('g.pad[data-n="104"]')   # Reserved → device NC
        self.assertIn("Вывод не используется — обоснование не требуется", self.page.locator("#design").inner_text())

    def test_legend_filter_and_summary(self):
        self.page.click('#leg .lg[data-k="VDAC"]')
        self.assertIn("1 пин", self.page.locator("#panel h2").inner_text())
        self.page.click('#leg .lg[data-k="VDAC"]')
        self.page.click('#leg .lg[data-k="PCIE"]')
        self.assertEqual(self.visible_pads(), 8)
        self.assertIn("8 пинов", self.page.locator("#panel").inner_text())
        self.assertIn("Routing notes", self.page.locator("#routing").inner_text())
        self.assertEqual(self.page.locator("#routing li").count(), self.page.evaluate("ROUTING.groups.PCIE.length"))
        self.page.click('#leg .lg[data-k="PCIE"]')
        self.assertEqual(self.visible_pads(), 200)
        self.page.click('.seg button[data-layer="prj"]')
        self.page.click('#leg .lg[data-k="VDEC"]')
        self.assertEqual(self.visible_pads(), 4)   # 115/117/127/129; the six unused CSI1 lanes are status nc → "Not used"
        self.assertIn("4 пина", self.page.locator("#panel h2").inner_text())
        self.assertGreaterEqual(self.page.locator("#routing li").count(), 1)

    def test_filter_clears_selection(self):
        self.page.click('g.pad[data-n="77"]')
        self.page.click('.seg button[data-layer="prj"]')
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 77)
        self.page.click('#leg .lg[data-k="I2C"]')
        self.assertIsNone(self.page.evaluate("PINOUT.state.sel"))
        self.assertEqual(self.page.evaluate("PINOUT.state.filter"), "I2C")
        self.assertFalse(self.page.evaluate("document.querySelector('g.pad[data-n=\"77\"]').classList.contains('sel')"))
        self.assertIn("2 пина", self.page.locator("#panel h2").inner_text())

    def test_select_clears_filter_and_toggle(self):
        self.page.click('#leg .lg[data-k="PCIE"]')
        self.page.click('g.pad[data-n="55"]')
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 55)
        self.assertIsNone(self.page.evaluate("PINOUT.state.filter"))
        self.assertEqual(self.visible_pads(), 200)
        self.page.click('g.pad[data-n="55"]')
        self.assertIsNone(self.page.evaluate("PINOUT.state.sel"))
        self.assertFalse(self.page.evaluate("document.body.classList.contains('has-sel')"))

    def test_no_keyboard(self):
        self.assertEqual(self.page.locator("g.pad[tabindex]").count(), 0)
        self.page.click('g.pad[data-n="55"]')
        self.page.keyboard.press("ArrowRight")
        self.page.keyboard.press("Escape")
        self.assertEqual(self.page.evaluate("PINOUT.state.sel"), 55)
        self.assertEqual(self.page.evaluate("[...document.querySelectorAll('g.pad.sel')].length"), 1)

    def test_design_card(self):
        self.assertFalse(self.page.locator("#design").is_visible())
        self.page.click('.seg button[data-layer="prj"]')
        self.assertTrue(self.page.locator("#design").is_visible())
        self.assertIn("Design notes", self.page.locator("#design h3").inner_text())
        self.page.click('g.pad[data-n="58"]')
        self.assertIn("Design notes · pin 58", self.page.locator("#design").inner_text())
        n = self.page.evaluate("(RATIONALE.devices.I2C || []).length + (RATIONALE.pins['58'] || []).length")
        self.assertEqual(self.page.locator("#design li").count(), n)
        self.page.click('#leg .lg[data-k="I2C"]')
        self.assertIn("Design notes · I2C1", self.page.locator("#design h3").inner_text())
        self.assertEqual(self.page.locator("#design li").count(), self.page.evaluate("(RATIONALE.devices.I2C || []).length"))
        self.page.click('#leg .lg[data-k="I2C"]')
        self.assertEqual(self.page.locator("#design li").count(), self.page.evaluate("RATIONALE.overview.length"))

    def test_table_no_inner_scroll_and_thin_scrollbars(self):
        self.assertEqual(self.page.evaluate("getComputedStyle(document.querySelector('.tbl-wrap')).maxHeight"), "none")
        # overflow-x:auto stays (narrow screens), which makes a "visible" overflow-y compute to "auto" (CSS Overflow 3);
        # assert the behaviour instead: the wrapper grows with its 200 rows, so it never scrolls vertically on its own
        self.assertTrue(self.page.evaluate("(e => e.scrollHeight <= e.clientHeight)(document.querySelector('.tbl-wrap'))"))
        css = self.page.evaluate("[...document.styleSheets[0].cssRules].map(r => r.cssText).join('\\n')")
        self.assertIn("scrollbar-width: thin", css)

    def test_sticky_table_header(self):
        # ≥1280 px: .tbl-wrap must not be a scroll container, so the header sticks to the viewport
        self.page.evaluate("document.querySelector('.tbl-wrap').scrollIntoView(); window.scrollBy(0, 3000)")
        wrap_top = self.page.evaluate("document.querySelector('.tbl-wrap').getBoundingClientRect().top")
        self.assertLess(wrap_top, -2500)
        top = self.page.evaluate("document.querySelector('#tbl thead th').getBoundingClientRect().top")
        self.assertTrue(-1 <= top <= 1, f"sticky header top = {top}")

    def test_general_section(self):
        n = self.page.evaluate("ROUTING.general.length")
        self.assertEqual(self.page.locator("#general h3").count(), n)
        self.assertIn("Layout notes", self.page.locator("#general").inner_text())

    def test_table_and_csv(self):
        self.assertEqual(self.page.locator("#tbl tbody tr.row").count(), 200)
        heads = self.page.locator("#tbl thead th").all_inner_texts()
        self.assertEqual(heads[:5], ["#", "Conn.", "Signal", "Group", "Dir."])
        self.assertRegex(self.page.locator('#tbl tbody tr.row[data-n="116"] td.txt').last.inner_text(), "[А-Яа-я]")
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
