# CM4 pinout v2 — design

## Context

v1 (`cm4_pinout.html`, merged and live on port 8088) is in Russian, draws the CM4 as a wide not-to-scale box with the pads on it, explains the Wi-Fi antenna as "вырез в земле" and shows a terse "Правило" line per group. The user's feedback (2026-09-13, with screenshots `BCM-wifi.png`, `GPIO.png`, `BCM-all.png`): the language is bad and ambiguous, the Wi-Fi block is unclear, the CM4 must be smaller and in its true 55×40 aspect ratio with the pins ("buttons") above and below it, search is unnecessary, routing facts must be more complete and understandable — pin-specific facts under the pin panel on the right, general facts below — written concisely through the PCB hardware skill. The user also added `sdtv2csi/` (ADV7280A-M SDTV→CSI-2 decoder, github rniwase/sdtv2csi) which will be traced onto the baseboard.

Decisions taken with the user: antenna keep-out drawn to scale at its real position; English for page, data and new docs; ADV7280A-M on CSI1 (D0 + CLK only), camera on CSI0; the CVBS switch + Haiwei K7 path stays, GPIO6/10 remain CVBS_SEL0/1, the decoder uses only its RC reset (as on sdtv2csi).

---

## Specification

### 1. Scope
- Same file, same layers ("Datasheet" default, "Project" toggle), same legend filter, keyboard navigation, table + CSV. Search removed.
- New: true-scale board drawing; "Routing notes" card per pin; "Layout notes" section (general); all text English; ADV7280A-M integration in the Project layer.

### 2. Board drawing (SVG, viewBox 0 0 1000 560; container scrolls horizontally, `min-width: 860px`)
- Pad strips as before (18 px pitch, 16 px pads, 50 columns, `X0 = 60`, pin 1/2 at the right end, odd row on top): J1 rows at y = 34 (odd) / 54 (even) above the outline; J2 rows at y = 484 / 504 below it. Labels: "J1 · pins 1–100 · odd numbers in the top row" above J1 (y = 24), "J2 · pins 101–200 · odd numbers in the top row" below J2 (y = 534); end markers "99 / 100" (left) and "1 / 2" (right), "199 / 200" and "101 / 102".
- Outline to scale, `S = 8.4 px/mm`, origin `OX = 269, OY = 118` (board 462 × 336 px). From datasheet Fig. 4 (CM4 viewed from the top): 55 × 40 mm; corner radius 2 mm; four M2.5 holes centred 3.5 mm from each edge (r = 1.25 mm); connector bodies 22 × 3 mm centred at x = 25 mm, J1 axis y = 3 mm, J2 axis y = 37 mm, pin 1/2 end on the right; BCM2711 15 × 15 mm centred at (31.99, 23.03) mm; antenna keep-out 6.5 × 11 mm at x = 0…6.5, y = 10.5…21.5 mm (hatched, label "Antenna keep-out"); U.FL at (2.57, 9.0) mm.
- Two translucent trapezoids link each pad strip to its connector body on the outline (J1: strip bottom edge y = 70 → connector top edge; J2: connector bottom edge → strip top edge y = 478).
- Caption (y = 552): "CM4 viewed from the top, to scale (datasheet Fig. 4). Connectors are on the underside; pin 1 is at the right end of each connector."

### 3. Right column (sticky on ≥1280 px; bottom sheet with ✕ below 1280 px when a pin or filter is active)
- Card 1 `#panel` — pin description: header (pin badge, signal, "J1 · odd (top) row"); Project layer: Net / Device / Mode / Status / Note; then Group / Direction / "BCM2711 GPIOn · boot pull-up|pull-down" / "Differential pair: pin N SIGNAL · 90 Ω · CM4 trace skew a / b mm"; quote block "Datasheet: …" (verbatim `ds`); ALT0–ALT5 table for GPIO with the project mode highlighted.
- Card 2 `#routing` — "Routing notes" for the selected pin: bullets = `ROUTING.groups[grp]` then `ROUTING.pins[n]`; if both empty: single line "No pin-specific routing constraint. See Layout notes below." Filter summary (no pin selected) shows the group's routing bullets in card 2.
- The old "Rule"/`ds_notes` line is removed.

### 4. General section `#general` — "Layout notes" (always visible, below the board, above the table)
- `ROUTING.general[]` sections, each `{title, items[]}`: Mechanical & connectors; Power & sequencing; Boot, reset & service; High-speed pairs; Wi-Fi & RF; Thermal; Video decoder ADV7280A-M (project). Rendered as h3 + bullet list.

### 5. Data
- `data/project.json` (v2, English). `meta.title = "CM4 baseboard — 2×100-pin pinout"`, `meta.cm4 = "CM4 with eMMC and Wi-Fi"`. `devices` names English. `pins` notes English, concise. Removed keys: `ds_notes`, `facts`. Changes for the decoder: pins 115/117 (CSI1 D0) and 127/129 (CSI1 clock) → `dev: "VDEC"`, `status: used`; 121/123, 133/135, 139/141 → `dev: "VDEC"`, `status: nc` ("CSI1 lanes D1–D3 unused by ADV7280A-M — leave unconnected"); device `VDEC` = "ADV7280A-M video decoder · CSI1"; pins 80/82 note lists both I2C0 clients; `CVBS` device stays.
- `data/routing.json` (new): `{"groups": {GRP: [str]}, "pins": {"n": [str]}, "general": [{"title": str, "items": [str]}]}`. Written by the content agent (Task 4), reviewed (Task 5).
- `data/cm4_datasheet.json` unchanged.

### 6. Files
- Modify: `cm4_pinout.html`, `data/project.json`, `tools/build.py`, `tests/test_lib.mjs`, `tests/test_project.py`, `tests/test_build.py`, `tests/test_browser.py`.
- Create: `data/routing.json`, `tests/test_routing.py`, `docs/superpowers/specs/2026-09-13-cm4-pinout-v2-design.md`, `docs/superpowers/plans/2026-09-13-cm4-pinout-v2.md`, `docs/adv7280a-m-integration.md` (fact sheet from sdtv2csi used by the content agent).

### 7. Tests
- Data: project.json shape (no `ds_notes`/`facts`), every pin resolves, GPIO uniqueness/modes/polarity as v1, approved nets incl. VDEC pins; routing.json: keys valid, all strings non-empty, ≤ 300 chars, end with a `[…]` source tag, contain no Cyrillic; every group has an entry (may be empty list); general has ≥ 6 sections.
- LIB (node): padXY new coordinates, csv English header, no `matches`.
- Browser: 200 pads at new coordinates; outline elements present (`#outline`, 4 `.hole`, 2 `.conn`, `.ant`, `.soc`); click → panel English; routing card content for 116 (PCIe) and 1 (GND); layer toggle; legend filter shows group routing bullets; keyboard; no `#q`; general section ≥ 6 h3; table + CSV; mobile bottom sheet; 1280 px no board overflow.

### 8. Out of scope
Search, deep links, PDF links, redeploy steps (live page updates via symlink on merge), translating v1 docs.
