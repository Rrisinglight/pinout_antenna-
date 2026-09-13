# CM4 pinout v3 — design

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

