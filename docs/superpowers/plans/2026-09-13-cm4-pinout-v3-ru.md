# CM4 pinout v3 — leaders removed, Russian prose — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify the board drawing (no leader polygons, no frame around the drawing; the true-scale CM4 stays) and translate every explanatory text on the page into precise engineering Russian for the layout engineer, keeping identifiers, units of code strings, source tags and short UI labels in English; translation written under the PCB Hardware Engineer skill and checked under the PCB-and-Board-Level Design Review skill.

**Architecture:** Same single-file page and data pipeline. Prose lives in `data/routing.json` (bullets, section titles), `data/project.json` (`note` fields), a new `data/ds_ru.json` (Russian rendering of each unique datasheet pin description, keyed by the English string, injected as a fourth global `DS_RU`), and a handful of SVG/UI prose strings in `cm4_pinout.html`. English originals stay in git history (tag `v2-en` on 37a6895) and, for datasheet quotes, in small text under the Russian one.

**Tech Stack:** unchanged (HTML/CSS/JS single file; Python 3.13 + pdftotext; node --test; Playwright).

**Spec:** the "Specification" section below; Task 1 copies it to `docs/superpowers/specs/2026-09-13-cm4-pinout-v3-ru-design.md` and this plan to `docs/superpowers/plans/2026-09-13-cm4-pinout-v3-ru.md`.

## Global Constraints

- Russian only for prose; no EN/RU toggle. Stay English: signal, net, ALT and device names; pin numbers; part numbers; config.txt strings (`dtoverlay=…`, `force_eeprom_read=0`, `otg_mode=1`); connector/pin names (`PETp0`, `CLKREQ#`, `M.2`, `U.FL`, `GPIO_VREF`); source tags `[DS §2.3]`, `[DS Table 6]`, `[DS Fig. 4]`, `[BCM2711 §5.3]`, `[project]`, `[sdtv2csi]`; short UI labels (buttons, table headers, card titles "Routing notes"/"Layout notes", dl labels Net/Device/Mode/Status/Note/Group/Direction/Differential pair/Datasheet, legend names, `LIB.DIRS`/`LIB.STATUS` values).
- Units in Russian prose: Ом, кОм, мм, мА, мкА, А, В, мс, с, МГц, мкФ, пФ, °C, Мбит/с; decimal point (`0.15 мм`), en dash for ranges (`4.75–5.25 В`), `×` for dimensions (`6.5 × 11 мм`), non-breaking space before a unit is not required.
- Engineering register: imperative, one constraint per bullet, no anglicisms where a standard Russian term exists (see glossary in Task 2); where a Russian term is ambiguous give the English in parentheses once per bullet (`подтяжка к питанию (pull-up)`).
- Meaning must be preserved exactly: every number, direction (→/←), polarity, pin number and source tag identical to the English source. Bullet length ≤ 320 characters.
- Board: only the leader polygons and the frame around the drawing go; the CM4 outline drawing stays as is.
- Single file, file://, no external resources, themes, 400 px — unchanged. Do not touch `index.html`, nginx configs, iptables; merging to `master` updates the live page (expected).
- Do not touch other uncommitted files in the repo. `git add` only named files.

---

## Context

v2 (English, live at http://195.133.238.45:8088/) drew translucent leader polygons between the pad strips and the connector bodies and a bordered grey frame around the drawing; the user finds both unnecessary — the pads and the J1/J2 labels are enough — and wants the CM4 outline kept. The layout engineer reads little English, so all explanatory text must be Russian with engineering precision, checked by the hardware review skill; identifiers and short UI labels can stay English.

Decisions (2026-09-13): remove leaders + frame only; translate all explanatory prose incl. per-pin project notes and the datasheet quote (English original kept in small text); Russian only.

---

## Specification

### 1. Board drawing
- Delete the two `polygon.lead` elements, the `.lead` CSS rule and the `--lead` custom property (both themes).
- `.board-wrap` loses `border`, `border-radius` and `background`; keeps `overflow-x:auto`.
- Everything else in `#board` unchanged (outline, holes, connector bodies with "J1"/"J2", BCM2711, antenna hatch, U.FL, strip labels, caption) — but the prose SVG strings become Russian (§3).

### 2. Data
- `data/routing.json`: every bullet and every `general[].title` in Russian, tags unchanged. Section titles: «Механика и разъёмы», «Питание и последовательность включения», «Загрузка, сброс и сервис», «Высокоскоростные дифференциальные пары», «GPIO и низкоскоростные интерфейсы», «Wi-Fi и радиочасть», «Тепловой режим», «Видеодекодер ADV7280A-M (проект)».
- `data/project.json`: `pins[n].note` and `defaults[grp].note` in Russian; `meta.cm4` → «CM4 с eMMC и Wi-Fi»; everything else unchanged (device names stay English).
- `data/ds_ru.json` (new): `{"<English ds string>": "<Russian>"}` for all 115 unique `ds` strings of `data/cm4_datasheet.json` (English original text stays the key so regeneration of the datasheet JSON cannot break it).
- `tools/build.py` injects `var DS_RU = …;` as the fourth global.

### 3. Page prose (English → Russian)
- Strip labels: «J1 · пины 1–100 · нечётные номера в верхнем ряду», «J2 · пины 101–200 · нечётные номера в верхнем ряду»; end markers unchanged.
- Antenna label (3 lines): «Зона без меди 6.5 × 11 мм:», «под этой областью ни на одном», «слое baseboard нет меди; U.FL выше.»
- Caption: «CM4, вид сверху, в масштабе (Fig. 4 даташита). Разъёмы на нижней стороне; пин 1 — у правого края каждого разъёма.»
- Panel: «нечётный (верхний) ряд» / «чётный (нижний) ряд»; BCM2711 row: `GPIO14 · при загрузке pull-down`; pair row: `pin 118 PCIe_RX_N · 90 Ом · разбег дорожек на CM4 0.23 / 0.23 мм`; datasheet block: label **Datasheet:** then the Russian text from `DS_RU[p.ds]` (fallback: English), then the English original in a `.dsq-en` line (small, muted).
- Routing card placeholders: «Особых требований к трассировке для этого пина нет — см. Layout notes под схемой.», «Выберите пин или элемент легенды.»; panel placeholder «Нажмите на пин.»; filter summary «· N пинов».
- Counter: «Показано N из 200 пинов». CSV button/dialog texts stay English (UI chrome).

### 4. Tests
- `tests/test_routing.py`: every bullet contains Cyrillic; length 10–320; tag regex unchanged; SECTIONS = Russian titles; needles in Russian units (see Task 2 Step 1).
- `tests/test_project.py`: `test_english_only` → `test_notes_russian` (every explicit pin note and defaults note contains Cyrillic; `net`/`mode`/`dev` ASCII).
- `tests/test_ds_ru.py` (new): keys == set of unique `ds` strings (115); values non-empty, contain Cyrillic, ≤ 2× English length + 60.
- `tests/test_build.py`: four globals.
- `tests/test_lib.mjs`: `DS_RU` embedded; csv line-55 regex without the note prefix.
- `tests/test_browser.py`: `.lead` count 0; `.board-wrap` computed `border-style` = `none`; panel needles in Russian (`нечётный`, Cyrillic inside `.dsq`, English original present in `.dsq-en`); routing card for pin 1 contains Cyrillic and `GND`; pin 116 card contains `PERp0` and `90 Ом`; general h3 count == sections; the rest unchanged.

### 5. Out of scope
EN/RU toggle; translating UI chrome; translating v1/v2 docs.

---

## Tasks

### Task 1: Docs, tag, board cleanup

**Files:** Create `docs/superpowers/specs/2026-09-13-cm4-pinout-v3-ru-design.md`, `docs/superpowers/plans/2026-09-13-cm4-pinout-v3-ru.md`; Modify `cm4_pinout.html`, `tests/test_browser.py`.

- [ ] **Step 1:** `git tag v2-en 37a6895` (English state preserved for reference). Copy spec (Context + Specification of this plan) and this plan into docs.
- [ ] **Step 2 (test first):** in `tests/test_browser.py::test_board_geometry` replace `self.assertEqual(self.page.locator("#board .lead").count(), 2)` with:
```python
        self.assertEqual(self.page.locator("#board .lead").count(), 0)
        self.assertEqual(self.page.evaluate("getComputedStyle(document.querySelector('.board-wrap')).borderTopStyle"), "none")
```
Run `python3 -m unittest tests.test_browser.TestPage.test_board_geometry -v` → fails.
- [ ] **Step 3:** `cm4_pinout.html`: delete `--lead:#000000;` and `--lead:#ffffff;` from the two `:root` blocks; delete the line `.lead{fill:var(--lead);opacity:.08}`; change `.board-wrap{overflow-x:auto;border:1px solid var(--bd3);border-radius:var(--r);background:var(--bg2)}` to `.board-wrap{overflow-x:auto}`; in `buildBoard()` delete the comment line `// leaders: pad strip ↔ connector body on the outline` and the two `board.appendChild(svg('polygon', {class: 'lead', …}))` lines (keep the `cL/cR/j1/j2` variables — they are used by the connector bodies).
- [ ] **Step 4:** `python3 tools/build.py` (no-op for data, keeps the block current), full suite green, commit: `git add docs/… cm4_pinout.html tests/test_browser.py` → `chore: v3 docs; remove board leaders and frame`.

### Task 2: Russian translation of all prose (content agent under PCB-Hardware-Engineer skill)

**Files:** Modify `data/routing.json`, `data/project.json`, `tests/test_routing.py`, `tests/test_project.py`; Create `data/ds_ru.json`, `tests/test_ds_ru.py`; Modify `tools/build.py`, `tests/test_build.py`.

- [ ] **Step 1 (tests first, transcribe verbatim):**

`tests/test_routing.py` — replace the module-level constants and `check_item`/needles:
```python
CYR = re.compile(r"[Ѐ-ӿ]")
TAG = re.compile(r"\[(DS §[0-9.]+(?:, Table \d+)?|DS Table \d+|DS Fig\. \d+|BCM2711 §[0-9.]+|project|sdtv2csi|CM4IO)\]$")
SECTIONS = ["Механика и разъёмы", "Питание и последовательность включения", "Загрузка, сброс и сервис",
            "Высокоскоростные дифференциальные пары", "GPIO и низкоскоростные интерфейсы", "Wi-Fi и радиочасть",
            "Тепловой режим", "Видеодекодер ADV7280A-M (проект)"]

    def check_item(self, where, t):
        self.assertIsInstance(t, str, where)
        self.assertTrue(10 <= len(t) <= 320, f"{where}: length {len(t)}")
        self.assertIsNotNone(CYR.search(t), f"{where}: no Russian text")
        self.assertRegex(t, TAG, f"{where}: missing/invalid source tag: {t[-40:]}")
```
and in `test_key_numbers_present` the needle list becomes:
```python
        for needle in ("90 Ом", "100 Ом", "0.15 мм", "0.1 мм", "6.5 × 11 мм", "8 × 15 мм", "10 мм", "DF40C-100DS-0.4V", "DF40HC(3.0)-100DS-0.4V",
                       "4.75", "5.25", "600 мА", "300 мА", "50 мА", "2 мс", "220 Ом", "15 мкА", "PETp0", "PERp0", "CLKREQ#", "PERST#",
                       "1.8 кОм", "−20", "85 °C", "0x21", "28.63636 МГц"):
```
(everything else in the file unchanged: GROUPS, required pins, `test_groups` minimums).

`tests/test_project.py` — replace `test_english_only` with:
```python
    def test_notes_russian(self):
        for k, e in self.prj["pins"].items():
            self.assertIsNotNone(CYR.search(e.get("note", "")), f"pin {k} note is not Russian")
            for f in ("net", "mode", "dev"):
                self.assertTrue(e.get(f, "").isascii(), f"pin {k} {f} must stay ASCII")
        for g, e in self.prj["defaults"].items():
            self.assertIsNotNone(CYR.search(e.get("note", "")), f"defaults {g} note is not Russian")
        for k, d in self.prj["devices"].items():
            self.assertIsNone(CYR.search(d["name"]), f"device {k} name must stay English")
```
(`CYR` is already defined at module level. Device names contain "→" and "·", so an ASCII check would fail — hence the no-Cyrillic check.)

`tests/test_ds_ru.py` (new):
```python
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
```

`tools/build.py` — add `rt`-style loading of `data/ds_ru.json` as `dsru` and inject `";\nvar DS_RU = " + dumps(dsru)` after `ROUTING`. `tests/test_build.py` — regex gains `;\nvar DS_RU = (.*?)` before `;\n/\*DATA-END\*/` and asserts equality with `data/ds_ru.json`.

Run: `python3 -m unittest tests.test_routing tests.test_project tests.test_ds_ru tests.test_build -v` → red.

- [ ] **Step 2 (content):** the controller dispatches ONE subagent (most capable model) that first invokes `hardware-agency-agents__hardware-agency-agents-en__PCB-and-Board-Level-Implementation__PCB-Hardware-Engineer` and then translates, with this brief (verbatim):

```
Translate the explanatory text of the CM4 baseboard pinout into Russian for a PCB layout engineer who reads little English. Files: data/routing.json (every bullet, every general[].title), data/project.json (pins[n].note, defaults[grp].note, meta.cm4), and a new data/ds_ru.json mapping every unique `ds` string of data/cm4_datasheet.json (115 keys, exact English text as key) to its Russian rendering. Do not change anything else in these files (nets, modes, devices, tags, structure, order).

Rules:
- Meaning identical to the English: every number, unit value, direction arrow (→ / ←), polarity word, pin number, part number and source tag preserved. Source tags stay exactly as they are ([DS §2.3], [DS Table 6], [DS Fig. 4], [BCM2711 §5.3], [project], [sdtv2csi]).
- Stay English: signal/net/ALT names (GPIO_VREF, PCIe_RX_P, UART3_TXD, RTS3…), device and chip names, config.txt strings (dtoverlay=…, force_eeprom_read=0, otg_mode=1, dtparam=ant1), connector pin names (PETp0, PERp0, CLKREQ#, PERST#, M.2, U.FL, DF40C-100DS-0.4V), "baseboard", "CM4", "CM4IO", "Wi-Fi", "Bluetooth", "rpiboot", "usbboot", "FFC".
- Units in Russian: Ом, кОм, мм, мА, мкА, А, В, мс, с, МГц, мкФ, пФ, °C, Мбит/с; decimal point; en dash for ranges (4.75–5.25 В); × for dimensions (6.5 × 11 мм); "±" kept.
- Register: техническая инструкция — повелительное наклонение («Разведите…», «Подключите…», «Не подключайте…», «Оставьте неподключённым»), одно требование на пункт, ≤ 320 символов, без канцелярита и без воды.
- Glossary (use consistently): differential pair — дифференциальная пара; impedance 90 Ω differential — дифференциальное волновое сопротивление 90 Ом; intra-pair match/skew — разбег длин внутри пары; length matching — выравнивание длин; reference plane — опорный слой; AC-coupling capacitor — разделительный конденсатор; pull-up / pull-down — подтяжка к питанию (pull-up) / к земле (pull-down) [English in parentheses on first use in a bullet]; open-drain — открытый сток; keep-out / copper-free area — зона без меди; back-feed — обратное питание (питание через сигнальные линии); trace — дорожка; via — переходное отверстие; footprint — посадочное место; stack height — высота стека; receptacle — розетка (ответная часть); header — штыревой разъём; jumper — перемычка; mounting hole — крепёжное отверстие; power-up sequence — последовательность включения; monotonic rise — монотонный рост; sink current — втекающий ток; active low — активный низкий уровень; boot — загрузка; overlay — overlay (DT-оверлей); lane — линия (lane); clock — тактовая пара / тактовый сигнал; enclosure — корпус; heatsink — радиатор; throttling — снижение частоты (троттлинг); decoder — декодер; termination — терминирование (согласующий резистор).
- Datasheet descriptions (ds_ru.json): translate faithfully, keep signal names and "CM4_3.3V"-style tokens, keep every number; e.g. "Ground (0V)" → "Земля (0 В)"; "GPIO: typically a 3.3V signal, but can be a 1.8V signal by connecting GPIO_VREF to CM4_1.8V" → "GPIO: обычно сигнал 3.3 В; может быть 1.8 В, если GPIO_VREF подключён к CM4_1.8V".
- Section titles exactly: «Механика и разъёмы», «Питание и последовательность включения», «Загрузка, сброс и сервис», «Высокоскоростные дифференциальные пары», «GPIO и низкоскоростные интерфейсы», «Wi-Fi и радиочасть», «Тепловой режим», «Видеодекодер ADV7280A-M (проект)».
Process: translate → run `python3 tools/build.py` (do not commit) → `python3 -m unittest tests.test_routing tests.test_project tests.test_ds_ru tests.test_build -v` until green → self-review every string against the English (git show v2-en:data/routing.json etc.) → report: counts, the test output, and every place where you chose a term not in the glossary. Do not touch cm4_pinout.html prose (Task 3) or tests. Do not dispatch subagents.
```

- [ ] **Step 3 (review):** the controller dispatches ONE subagent (most capable model) that first invokes `hardware-agency-agents__hardware-design-review-validation__en__PCB-and-Board-Level-Design-Review-Engineer`, then compares every translated string with its English source (`git show v2-en:data/routing.json`, `git show v2-en:data/project.json`, `data/cm4_datasheet.json` `ds`) and reports, one line per problem: `location — WRONG MEANING | LOST NUMBER/DIRECTION | AMBIGUOUS | TERM (glossary) | STYLE | TOO LONG — <what> → <exact Russian replacement>`; plus a list of verified-correct locations. Controller sends findings to the content agent for one fix round, re-runs the tests, spot-checks 15 strings.

- [ ] **Step 4:** commit `data/routing.json data/project.json data/ds_ru.json tools/build.py tests/test_routing.py tests/test_project.py tests/test_ds_ru.py tests/test_build.py cm4_pinout.html` → `feat(content): Russian prose for routing/layout notes, project notes and datasheet descriptions; DS_RU global`.

### Task 3: Page prose in Russian + tests

**Files:** Modify `cm4_pinout.html` (UI block, SVG strings), `tests/test_browser.py`, `tests/test_lib.mjs`.

- [ ] **Step 1 (tests first):**
`tests/test_lib.mjs`: in `data embedded` add `assert.ok(DS_RU && Object.keys(DS_RU).length >= 100);`; csv test line-55 regex → `/^55;J1;odd;GPIO14;GPIO;bidir;UART0_TXD;CONSOLE;ALT0 TXD0;used;;/`.
`tests/test_browser.py`:
  - `test_pin_panel_english` → rename `test_pin_panel`; needles: `("GPIO14", "J1", "нечётный", "Group", "Direction", "bidirectional", "Datasheet", "при загрузке pull-down")`; add `self.assertRegex(self.page.locator("#panel .dsq").inner_text(), "[А-Яа-я]")` and `self.assertIn("GPIO: typically a 3.3V signal", self.page.locator("#panel .dsq-en").inner_text())`.
  - `test_project_layer_and_routing_card`: needles `("PCIE_RX_P", "PCIe → M.2 NVMe", "PERp0", "Differential pair", "118", "90 Ом")`; routing card: `assertIn("PERp0", rt); assertIn("90 Ом", rt)`; pin 76 → `assertIn("do not connect", …)` unchanged (STATUS label).
  - `test_routing_card_gnd_pin`: replace `assertIn("ground pin", rt)` with `self.assertIn("GND", rt); self.assertRegex(rt, "[А-Яа-я]")`.
  - `test_legend_filter_and_summary`: `"8 pins"` → `"8 пинов"`.
  - `test_table_and_csv`: unchanged.
  Run → red.
- [ ] **Step 2:** `cm4_pinout.html` UI block string replacements (exact):
  - strip labels: `'J1 · pins 1–100 · odd numbers in the top row'` → `'J1 · пины 1–100 · нечётные номера в верхнем ряду'`; J2 likewise `'J2 · пины 101–200 · нечётные номера в верхнем ряду'`.
  - antenna label lines → `'Зона без меди 6.5 × 11 мм:'`, `'под этой областью ни на одном'`, `'слое baseboard нет меди; U.FL выше.'`.
  - caption → `'CM4, вид сверху, в масштабе (Fig. 4 даташита). Разъёмы на нижней стороне; пин 1 — у правого края каждого разъёма.'`.
  - `renderRouting` default `empty` → `'Особых требований к трассировке для этого пина нет — см. Layout notes под схемой.'`; no-selection call → `'Выберите пин или элемент легенды.'`; panel placeholder `'Click a pin.'` → `'Нажмите на пин.'`; filter h2 `' pins'` → `' пинов'`.
  - panel: `'odd (top) row' : 'even (bottom) row'` → `'нечётный (верхний) ряд' : 'чётный (нижний) ряд'`; `' · boot pull-'` → `' · при загрузке pull-'`; pair text `' Ω · CM4 trace skew '` → `' Ом · разбег дорожек на CM4 '`, `' mm'` → `' мм'`; table Pair cell `' Ω'` → `' Ом'`.
  - datasheet block: replace `var dq = h('div', 'dsq'); dq.appendChild(h('b', null, 'Datasheet: ')); dq.appendChild(document.createTextNode(p.ds)); frag.appendChild(dq);` with
    ```js
    var dq = h('div', 'dsq'), ru = DS_RU[p.ds];
    dq.appendChild(h('b', null, 'Datasheet: ')); dq.appendChild(document.createTextNode(ru || p.ds));
    if (ru) dq.appendChild(h('div', 'dsq-en', p.ds));
    frag.appendChild(dq);
    ```
    and add CSS `.dsq-en{margin-top:4px;font-size:11px;opacity:.75}`.
  - counter: `'Showing ' + shown + ' of 200 pins'` → `'Показано ' + shown + ' из 200 пинов'`.
- [ ] **Step 3:** `python3 tools/build.py`; full suite green; screenshots 1280 light/dark + 400 (view: Russian labels fit inside the antenna area label lines and the strip labels; no overflow); commit `cm4_pinout.html tests/test_browser.py tests/test_lib.mjs` → `feat(page): Russian prose on the board, panel and routing card; datasheet quote with English original`.

### Task 4: Final verification
- [ ] `python3 tools/extract_datasheet.py && python3 tools/build.py && git diff --exit-code data/cm4_datasheet.json && node --test tests/test_lib.mjs && python3 -m unittest discover -s tests -v` → green (6 node; python 6 + 8 + 2 + 4 + 1 + 9).
- [ ] Playwright checks: pin 55 panel shows Russian datasheet text + English original; pin 116 routing card 7 bullets in Russian with `PERp0`/`90 Ом`; legend PCIe → 8 pins, «8 пинов»; Layout notes 8 Russian headings; no `.lead`; no frame; 400 px no page scroll.
- [ ] Whole-branch review (most capable model) incl. a language pass: any English prose left? any Russian ambiguity? then merge.

## Verification (end-to-end)
All tests green; page opened from disk shows the CM4 outline without leaders/frame, Russian notes everywhere, English identifiers; after merge http://195.133.238.45:8088/ shows v3.

## Execution
Subagent-driven: Task 1 (cheap model), Task 2 content agent + review agent (most capable), Task 3 (mid-tier), Task 4 verification; final whole-branch review; merge to master (approved by this plan; updates the live page).
