import re
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
        self.assertEqual(self.page.get_attribute("#board", "viewBox"), "0 0 1060 1000")
        self.assertEqual(self.page.evaluate("document.querySelector('g.pad[data-n=\"1\"] rect').getAttribute('x')"), "152")
        self.assertEqual(self.page.evaluate("document.querySelector('g.pad[data-n=\"1\"] rect').getAttribute('y')"), "60")
        self.assertEqual(self.page.evaluate("document.querySelector('g.pad[data-n=\"101\"] rect').getAttribute('x')"), "868")
        self.assertEqual(self.page.evaluate("document.querySelector('g.pad[data-n=\"200\"] rect').getAttribute('y')"), "942")
        self.assertEqual(self.page.locator("#outline").count(), 1)
        self.assertAlmostEqual(float(self.page.get_attribute("#outline", "width")), 336.0, places=6)
        self.assertAlmostEqual(float(self.page.get_attribute("#outline", "height")), 462.0, places=6)
        self.assertAlmostEqual(float(self.page.get_attribute("#outline", "x")), 362.0, places=6)
        self.assertEqual(self.page.locator("#board .hole").count(), 4)
        self.assertEqual(self.page.locator("#board .conn").count(), 2)
        self.assertEqual(self.page.locator("#board .pin1").count(), 2)
        self.assertEqual(self.page.locator("#board .ant").count(), 1)
        self.assertEqual(self.page.locator("#board .lead").count(), 0)
        txt = self.page.locator("#board").text_content()
        for s in ("CN1 (J1)", "CN2 (J2)", "Зона без меди", "против часовой", "1 / 2", "101 / 102", "199 / 200"):
            self.assertIn(s, txt)
        self.assertNotIn("J1 ·", txt); self.assertNotIn("J2 ·", txt)
        self.assertEqual(self.page.locator("#q").count(), 0)
        w = self.page.evaluate("(e=>[e.scrollWidth,e.clientWidth])(document.querySelector('.board-wrap'))")
        self.assertLessEqual(w[0], w[1])      # 1280 px viewport → board column 876 px ≥ min-width 860 px

    def test_labels_and_arrows(self):
        self.assertEqual(self.page.locator("g.pad text.netlbl").count(), 200)
        self.assertEqual(self.page.locator('g.pad[data-n="55"] text.netlbl').text_content(), "GPIO14")
        self.assertEqual(self.page.get_attribute('g.pad[data-n="55"] text.netlbl', "text-anchor"), "end")
        self.assertEqual(self.page.get_attribute('g.pad[data-n="56"] text.netlbl', "text-anchor"), "start")
        self.assertEqual(self.page.locator("g.pad path.arr").count(), 146)      # 200 − 51 GND − 3 Reserved(nc)
        self.assertEqual(self.page.get_attribute('g.pad[data-n="55"] path.arr', "class"), "arr bidir")
        self.assertEqual(self.page.locator('g.pad[data-n="1"] path.arr').count(), 0)
        self.page.click('.seg button[data-layer="prj"]')
        self.assertEqual(self.page.locator('g.pad[data-n="55"] text.netlbl').text_content(), "UART0_TXD")
        self.assertEqual(self.page.get_attribute('g.pad[data-n="55"] path.arr', "class"), "arr out")
        self.assertEqual(self.page.get_attribute('g.pad[data-n="34"] path.arr', "class"), "arr in")
        self.assertEqual(self.page.get_attribute('g.pad[data-n="77"] path.arr', "class"), "arr pwr in")
        self.assertEqual(self.page.locator('g.pad[data-n="37"] text.netlbl').text_content(), "—")
        self.assertEqual(self.page.locator('g.pad[data-n="37"] path.arr').count(), 0)
        self.assertTrue(self.page.evaluate("document.querySelector('g.pad[data-n=\"98\"]').classList.contains('warn')"))
        self.assertFalse(self.page.evaluate("document.querySelector('g.pad[data-n=\"24\"]').classList.contains('warn')"))
        self.assertEqual(self.page.locator('g.pad[data-n="98"] path.badge').count(), 1)

    def test_pin_panel(self):
        self.page.click('g.pad[data-n="55"]')
        text = self.page.locator("#panel").inner_text()
        for s in ("GPIO14", "CN1 (J1 в даташите)", "нечётный", "Group", "Direction", "bidirectional", "Datasheet", "при загрузке pull-down"):
            self.assertIn(s, text)
        self.assertNotIn("J1 ·", text)
        self.assertNotIn("UART0_TXD", text)                    # Datasheet layer: no project data
        self.assertRegex(self.page.locator("#panel .dsq").inner_text(), "[А-Яа-я]")
        self.assertIn("TXD0", self.page.locator("#panel table.alt").inner_text())
        self.assertEqual(self.page.locator("#panel .issues").count(), 0)      # Datasheet layer: no check block

    def test_project_panel_check_and_issues(self):
        self.page.click('.seg button[data-layer="prj"]')
        self.page.click('g.pad[data-n="82"]')
        text = self.page.locator("#panel").inner_text()
        for s in ("SDA0", "I2C0 · camera, ADV7280A-M, VRX ADS1115", "Схема", "U1.30", "Проверка", "✓ совпадает", "Замечания", "3.77"):
            self.assertIn(s, text)
        self.assertIn("Direction (DS)", text)                  # datasheet Direction row, distinct from the project one
        self.assertGreaterEqual(self.page.locator("#panel ul.issues li").count(), 2)
        self.page.click('g.pad[data-n="98"]')
        self.assertIn("✗ GND не на земле (без цепи)", self.page.locator("#panel").inner_text())
        self.page.click('g.pad[data-n="55"]')
        self.assertIn("Замечаний нет.", self.page.locator("#panel").inner_text())
        self.assertIn("output", self.page.locator("#panel").inner_text())   # project Direction row
        self.page.click('g.pad[data-n="37"]')
        self.assertIn("spare (no net)", self.page.locator("#panel").inner_text())

    def test_spare_pin(self):
        self.page.click('.seg button[data-layer="prj"]')
        self.page.click('g.pad[data-n="37"]')
        text = self.page.locator("#panel").inner_text()
        # brief lists "вариант A"; the pin-37 issue text in data/project.json starts with a capital «Вариант A»
        for s in ("Spare GPIO", "≈ в схеме метка IO7, на сайте не используется", "GPIO7", "Вариант A"):
            self.assertIn(s, text)
        self.assertTrue(re.fullmatch(r"≈( · \d+)?", self.page.locator('#tbl tbody tr.row[data-n="37"] td.c-check').inner_text()))
        self.assertEqual(self.page.locator('g.pad[data-n="37"] path.arr').count(), 0)

    def test_project_layer_and_routing_card(self):
        self.page.click('.seg button[data-layer="prj"]')
        self.page.click('g.pad[data-n="116"]')
        text = self.page.locator("#panel").inner_text()
        for s in ("PCIE_RX_P", "PCIe → M.2 NVMe", "PERp0", "Differential pair", "118", "90 Ом", "✗ в схеме нет"):
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
        self.assertEqual(self.page.locator("#routing li").count(), self.page.evaluate("ROUTING.groups.GND.length"))
        self.assertIn("GND", rt); self.assertRegex(rt, "[А-Яа-я]")
        self.page.click('.seg button[data-layer="prj"]')   # pin 1 stays selected across the layer switch
        self.assertIn("✓ совпадает со схемой", self.page.locator("#panel").inner_text())
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
        self.assertEqual(self.visible_pads(), 6)   # 128/130/140/142 used + 134/136 opt (CSI0 D1, external CVBS_Mod only)
        self.assertIn("6 пинов", self.page.locator("#panel h2").inner_text())
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
        # the 200-pin table comes first, Layout notes last (DOCUMENT_POSITION_FOLLOWING = 4)
        self.assertTrue(self.page.evaluate("!!(document.querySelector('.tbl-sec').compareDocumentPosition(document.querySelector('#general')) & 4)"))

    def test_table_and_csv(self):
        self.assertEqual(self.page.locator("#tbl tbody tr.row").count(), 200)
        heads = self.page.locator("#tbl thead th").all_inner_texts()
        self.assertEqual(heads[:5], ["#", "Conn.", "Signal", "Group", "Dir."])
        self.assertIn("Схема", heads); self.assertIn("Проверка", heads)
        self.assertEqual(self.page.locator('#tbl tbody tr.row[data-n="1"] td').nth(1).inner_text(), "CN1")
        self.assertEqual(self.page.locator('#tbl tbody tr.row[data-n="101"] td').nth(1).inner_text(), "CN2")
        self.page.click('.seg button[data-layer="prj"]')
        self.assertEqual(self.page.locator('#tbl tbody tr.row[data-n="55"] .c-net').inner_text(), "UART0_TXD")
        self.assertEqual(self.page.locator('#tbl tbody tr.row[data-n="55"] .c-sch').inner_text(), "UART0_TXD")
        self.assertTrue(self.page.evaluate("document.querySelector('#tbl tbody tr.row[data-n=\"92\"] td.c-check').classList.contains('c-missing')"))
        self.assertRegex(self.page.locator('#tbl tbody tr.row[data-n="82"] td.c-check').inner_text(), r"^✓ · \d+$")
        self.assertIn("✗ в схеме нет", self.page.get_attribute('#tbl tbody tr.row[data-n="92"] td.c-check', "title"))
        self.page.click('#tbl tbody tr.row[data-n="92"]')
        self.assertIn("RUN_PG", self.page.locator("#panel h2").inner_text())
        self.page.click("#csv")
        self.page.wait_for_function("document.querySelector('#csv').textContent.includes('Copied') || document.querySelector('#csvdlg').open")
        text = self.page.evaluate("LIB.csv(DATA.pins, PROJECT, SCHEMATIC)")
        self.assertTrue(text.startswith("pin;connector;row;signal") and ";schematic_net;check;issues;" in text.split("\n")[0])

    def test_project_table_fits_1280(self):
        def th(page, name):
            return page.locator("#tbl thead th").filter(has_text=re.compile("^" + re.escape(name) + "$"))
        def width(page):
            return page.evaluate("(e=>[e.scrollWidth,e.clientWidth])(document.querySelector('.tbl-wrap'))")
        hidden_in_prj = ("Group", "Dir.", "Pair", "Datasheet")
        for name in hidden_in_prj:                              # Datasheet layer keeps the datasheet columns
            self.assertTrue(th(self.page, name).is_visible(), name)
        self.page.click('.seg button[data-layer="prj"]')
        for name in hidden_in_prj + ("Mode",):                  # 1280–1599 px: Mode is in the panel's ALT table
            self.assertFalse(th(self.page, name).is_visible(), name)
        for name in ("Схема", "Проверка", "Note"):
            self.assertTrue(th(self.page, name).is_visible(), name)
        w = width(self.page)
        self.assertLessEqual(w[0], w[1], f"Project-layer table {w[0]} px in a {w[1]} px wrapper at 1280")
        page = self.browser.new_page(viewport={"width": 1600, "height": 900})
        page.on("pageerror", lambda e: self.errors.append(str(e)))
        page.goto(URL)
        page.click('.seg button[data-layer="prj"]')
        self.assertTrue(th(page, "Mode").is_visible())
        w = width(page)
        self.assertLessEqual(w[0], w[1], f"Project-layer table {w[0]} px in a {w[1]} px wrapper at 1600")
        page.close()

    def test_counter_tally(self):
        self.assertEqual(self.page.locator("#cnt").inner_text(), "Показано 200 из 200 пинов")
        self.page.click('.seg button[data-layer="prj"]')
        t = self.page.locator("#cnt").inner_text()
        self.assertRegex(t, r"^Показано 200 из 200 пинов · ✓ \d+ · ≈ \d+ · ✗ \d+ · — \d+$")
        nums = [int(x) for x in __import__("re").findall(r"\d+", t)[2:]]
        self.assertEqual(sum(nums), 200)
        tally = self.page.evaluate("(()=>{const c={};DATA.pins.forEach(p=>{const k=LIB.checkOf(p,PINOUT.ov(p),SCHEMATIC).code;c[k]=(c[k]||0)+1});return c})()")
        self.assertEqual(nums[0], tally.get("ok", 0))
        self.assertEqual(nums[2], tally.get("gnd_open", 0) + tally.get("missing", 0))

    def test_only_issues_filter(self):
        self.assertFalse(self.page.locator("#only-issues").is_visible())
        self.page.click('.seg button[data-layer="prj"]')
        self.assertTrue(self.page.locator("#only-issues").is_visible())
        self.page.click("#only-issues")
        n = self.page.evaluate("DATA.pins.filter(p=>LIB.hasIssue(p,PINOUT.ov(p),LIB.checkOf(p,PINOUT.ov(p),SCHEMATIC))).length")
        self.assertGreater(n, 20); self.assertLess(n, 120)
        self.assertEqual(self.visible_pads(), n)
        self.assertEqual(self.page.locator("#cnt").inner_text().split(" ·")[0], f"Показано {n} из 200 пинов")
        self.page.click('#leg .lg[data-k="VRX"]')          # combines with the device filter
        m = self.page.evaluate("DATA.pins.filter(p=>PINOUT.ov(p).dev==='VRX'&&LIB.hasIssue(p,PINOUT.ov(p),LIB.checkOf(p,PINOUT.ov(p),SCHEMATIC))).length")
        self.assertEqual(self.visible_pads(), m); self.assertGreater(m, 0)
        self.assertEqual(self.page.locator("#panel ul.plain li").count(), self.visible_pads())   # panel list honours the toggle
        self.page.click('.seg button[data-layer="ds"]')    # layer switch resets it
        self.assertEqual(self.visible_pads(), 200)
        self.assertEqual(self.page.get_attribute("#only-issues", "aria-pressed"), "false")

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
