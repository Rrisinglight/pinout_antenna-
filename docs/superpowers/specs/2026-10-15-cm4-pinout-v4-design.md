# CM4 pinout v4 — vertical CN1/CN2 drawing, schematic-checked allocation — design

## Context

The pinout page (`cm4_pinout.html`, data in `data/*.json`, rev 2 of `project.json` dated 2026-09-13) describes the **intended** CM4 allocation. Since then the EasyEDA project **Retr_2026-09-26** has grown real boards: the carrier **Retr_Cross** (CM4 on `CN1`/`CN2`), the power board **Retr_PWR**, the receiver boards **Retr_VRX1_2/3_5/5_8**, the one-wire CRSF block **CRSF_Mod** and the analog→CSI module **CVBS_Mod**. The folder `Review/` (2026-10-14) compares each of them with the site: `Review/_data/chains.json` holds the computed 200-row map «CM4 pin → site net → carrier net → where it goes», and the five `.md` files hold the discrepancies and the decisions still open.

The user (2026-10-15) wants a new version of the page that:

1. draws the CM4 **rotated vertically**, with the connectors called **CN1 / CN2** (the carrier's designators) instead of the datasheet's J1 / J2, and a **schematic-style pinout with direction arrows**, like the CM sheet in EasyEDA;
2. proposes the **new allocation** that connects the four finished blocks (CRSF_Mod, Retr_PWR, VRX boards, CVBS_Mod/ADV7280A-M) to the CM4 correctly, taking the real schematic into account; other devices of the old plan (GPS, fan, PCIe, USB hub, Ethernet switch, service pins) are **kept as planned** and only checked;
3. for every pin shows **status, concerns and a check against the schematic**, the way the review tables do, and keeps the page clean and usable.

Prose stays Russian (engineering register, v3 rules); identifiers, net names and short UI labels stay English.

Sources the implementer must read: `Review/README.md` («Главное», «Как читать»), `Review/power-board.md` §7, `Review/crsf-one-wire.md` §4–7, `Review/vrx-board.md` §4–7, `Review/analog-to-csi.md` §4–7, `Review/website.md` §2–6, `Review/_data/chains.json` (`cm4_map`), `Review/_data/retr_cross.sch.json`.

## Decisions and assumptions

| # | Decision | Why / source |
|---|---|---|
| D1 | **Power switches of Retr_PWR are driven by a TCA9534A (or PCA9534A) I2C expander on I2C1**, powered from CM4_3V3, one BSS138 + 100 kΩ gate pull-down per line on the carrier. Outputs P0–P7 = `PW_VRX`, `PW2`, `PW3`, `PW_RZ1`, `PW_RZ2`, `PW7`, `TX1_PWR_EN`, `TX2_PWR_EN`. P6/P7 are **reserved for TX switches that do not exist yet** on any board (`+V_TX1/+V_TX2` are unconnected, `Review/power-board.md` п. 6). This is option B of `Review/power-board.md` §7.2; **awaiting the user's confirmation** (question 2 there). **Sub-decision D1a (user, 2026-10-15):** `PWR_3V` (camera `FPC1`, ADV7280A-M `U1`, the 1.8 В regulator, the LEDs and the I2C0 slaves) is fed from the switched `+5V_VRX` (`Review/power-board.md` п. 4) and **stays that way** — no re-wiring. Linux must turn `PW_VRX` on at boot (a `gpio-hog` on the expander, or `gpio=` is not available for an expander line, so the hog is the mechanism); the camera/decoder are probed after that. Recorded as an informational issue on pins 97, 115, 128, 80/82. | all lines independent; the expander is unpowered when the CM4 is off, so every rail is off; I2C1 is empty today |
| D2 | Consequently **GPIO7, GPIO11, GPIO17, GPIO19 become spare** (`CRSF1_DIR`, `CRSF2_DIR`, `TX1_PWR_EN`, `TX2_PWR_EN` are dropped from the GPIO plan). If the user picks option A instead, pins 26, 37, 38, 50 change (`TX2_PWR_EN`/`TX1_PWR_EN` return as GPIO outputs, 37 → `PW_VRX`, 38 → `PW2`+`PW3`) plus the I2C device name and the rationale bullets. | CRSF_Mod switches direction itself (`Review/crsf-one-wire.md` п. 6); switches are on the expander (D1) |
| D3 | **CSI assignment follows the carrier**: ADV7280A-M (`U1`, and the external CVBS_Mod on `J2` in parallel) on **CSI0** (D0 + CLK), camera `FPC1` on **CSI1 with 4 lanes**. The site rev 2 had it the other way round. `J2` is treated as the CVBS_Mod port only (no camera on J2: its GPIO0/GPIO1 lines end at the open `R34`/`R35`). | `Review/analog-to-csi.md` п. 1–2, 8; the ТЗ does not fix the ports; a 4-lane camera port is the better use of CSI1 |
| D4 | **I2C split (user, 2026-10-15): the VRX board is tested and ordered and is not changed**, so its ADS1115 (and its 4K7 pull-ups to 5 В) stays on I2C0 with the camera and ADV7280A-M. Everything still on the carrier moves to I2C1: INA219 `U25`, the TCA9534A expander, the planned sensors. The ≈ 3.77 В bus level on I2C0 (`Review/vrx-board.md` п. 3) is reported as a **risk to measure on the bench**, not as a change request; the ADS1115/INA219 VIH figures are quoted from the review and not verified. | `Review/vrx-board.md` п. 3, 4, 9; `Review/analog-to-csi.md` п. 9; `Review/power-board.md` п. 8–9; DS §2.9 (I2C0 is the camera bus) |
| D5 | **Net naming rule (user, 2026-10-15: names must be clear first of all to the circuit designer working in EasyEDA)**: wherever the carrier has a label on a CM4 pin — wired **or dangling** — the site adopts the **carrier's net name** (`TD0+`, `VRX_SS1`, `SDA0`, `SDA1`/`SCL1`, `+5V_CM`, `+3V`, `CAM1_C_P`, `A_LED_G`, `NEXTRST`, `USB2_N`, `UART3_TXD`, …). Only where the carrier has nothing does the site keep its own descriptive name (`FAN_TACH`… are already identical). Two exceptions, both shown in the check column so the designer sees the mapping: the generic placeholders `IO16`/`IO27` on the INV lines are written `CRSF2_INV`/`CRSF1_INV` (function names; `IO7`/`IO11` are spare and get no net), and the carrier's `CAM0_DO_*`/`CAM1_DO_*` (letter O) are written `CAM0_D0_*`/`CAM1_D0_*` with the typo reported as an issue. | the engineer types the names in EasyEDA; the site should match what exists |
| D6 | The **check column compares the new plan with the snapshot** `Review/_data/chains.json` (2026-10-14 12:28–12:34). It is a snapshot, not live EasyEDA; the generated file records the snapshot time. | reproducible from the repo |
| D7 | CVBS mux (RS2255) is on the VRX module, so `CVBS_SEL0/1` join device **VRX**; the separate `CVBS` device disappears. | `Review/vrx-board.md` п. 10 |
| D8 | Servo bus: one CRSF_Mod block (`CBB3`) on UART5, `CBB4` is a spare; the servo rails `P_SRV1`/`P_SRV2` are switched by `PW2`/`PW3` through the expander. | `Review/crsf-one-wire.md` п. 12; `Review/power-board.md` §7.2 |
| D9 | The datasheet layer keeps the datasheet's `J1`/`J2` in `data/cm4_datasheet.json` (the extractor and its tests are untouched); the page maps them to **CN1 / CN2** everywhere it is displayed (`LIB.CONN`), and the panel says «CN1 (J1 в даташите)». | no churn in the extracted datasheet data |
| D10 | Deployment: the live page is the repo checkout via an nginx symlink, so **merging to `master` deploys**. Work on branch `pinout-v4`; merge only when the user says so. | `cm4-pinout-nginx.conf` |

---

## Specification

### 1. Board drawing (SVG `#board`, viewBox `0 0 1060 1000`, `min-width: 860px`, horizontal scroll below that; the board column is 876 px at the 1280 px breakpoint)

Coordinates are viewBox units. All geometry lives in `LIB` so it is unit-testable.

**Pads.** Pin `n` → row `i = floor(((n − 1) mod 100) / 2)`, `y = 60 + 18·i` (pad top). Pad size 16 × 16, radius 3, pin number inside (7 px mono, as now).

| Connector | Column | Pins | pad `x` | Label side |
|---|---|---|---|---|
| CN1 (= J1) | outer (left) | odd 1…99 | 152 | left |
| CN1 | inner | even 2…100 | 172 | right (towards the outline) |
| CN2 (= J2) | inner | odd 101…199 | 868 | left (towards the outline) |
| CN2 | outer (right) | even 102…200 | 888 | right |

So `LIB.padXY(1) = {x:152, y:60}`, `padXY(2) = {x:172, y:60}`, `padXY(3) = {x:152, y:78}`, `padXY(99) = {x:152, y:942}`, `padXY(100) = {x:172, y:942}`, `padXY(101) = {x:868, y:60}`, `padXY(102) = {x:888, y:60}`, `padXY(200) = {x:888, y:942}`. Label side: `LIB.sideOf(n)` = `'L'` for odd `n`, `'R'` for even `n`.

Why this is the correct rotation: datasheet Fig. 4 (top view) has J1 along the top edge with pin 1 at the right end and the odd row outermost, J2 along the bottom edge with pin 101 at the right end and the odd row innermost. Rotating the view 90° counter-clockwise puts J1 on the left edge and J2 on the right edge, both pin 1/101 ends at the top; the odd row of J1 stays outermost (left), the odd row of J2 stays innermost.

**Labels with arrows (the “Sheet CM” look).** Each pad has, on its label side:
- an arrow glyph `path.arr` in a 20 × 10 box: left side box `x = pad.x − 24 … pad.x − 4`, right side `x = pad.x + 20 … pad.x + 40`, vertically centred on the pad (`y = pad.y + 3 … pad.y + 13`);
- a text `text.netlbl` (mono, 11 px): left side `text-anchor="end"` at `x = pad.x − 28`; right side `text-anchor="start"` at `x = pad.x + 44`; baseline `pad.y + 12`.

Glyph shapes are path strings in local 20 × 10 coordinates, drawn for the **left** side (pad to the right of the glyph) and placed with `transform="translate(pad.x − 24, pad.y + 3)"`; on the right side they are mirrored with `transform="translate(pad.x + 40, pad.y + 3) scale(-1,1)"` (local x → `pad.x + 40 − x`, i.e. the box `pad.x + 20 … pad.x + 40`). A glyph element exists in the DOM **only** when the direction has a shape; `apply()` adds or removes `path.arr` (and `path.badge`) rather than hiding them, so element counts are meaningful:

| `dir` | class | shape (left side) | meaning |
|---|---|---|---|
| `in` | `arr in` | flag pointing **right** (towards the pad): `M0 0 H14 L20 5 L14 10 H0 Z` | signal into the CM4 |
| `out` | `arr out` | flag pointing **left** (away): `M6 0 H20 V10 H6 L0 5 Z` | signal out of the CM4 |
| `bidir` | `arr bidir` | both ends pointed: `M6 0 H14 L20 5 L14 10 H6 L0 5 Z` | bidirectional |
| `power_in` | `arr pwr in` | same as `in`, dashed stroke | power into the CM4 |
| `power_out` | `arr pwr out` | same as `out`, dashed stroke | power out of the CM4 |
| `gnd`, `nc`, `spare` | no glyph | — | ground / not connected / spare pin without a net |

Label text: Datasheet layer → `pin.sig`; Project layer → `ov.net`, or `—` (class `empty`) when the net is empty. GND pins show «GND» in muted colour on both layers. Colours: the pad rectangle keeps the layer colour (`LIB.colorOf`), the glyph is neutral (`fill: var(--bg3); stroke: var(--bd2)`), dimmed together with the pad under a filter.

**Direction per layer.** `LIB.dirOf(pin, ov, layer)`: Datasheet layer → `pin.dir` from the datasheet; Project layer → `status ∈ {nc, dnc, free}` → `'nc'`; otherwise an empty `ov.net` (spare GPIO) → `'spare'`; otherwise `ov.dir` when `project.json` sets one, else `pin.dir`. `LIB.DIRS` gains `spare: 'spare (no net)'`, so the table and the panel show it in words; `'nc'` and `'spare'` draw no glyph. Project `dir` is mandatory for every explicit entry of a `GPIO`-group pin and for pins 80/82 (§4.3); for spare pins it is `bidir` (what the pin can do) but is not displayed.

**Rotated outline (to scale, 8.4 px/mm)** between the connector symbols. `LIB.rot(x, y) = {x: y, y: 55 − x}` converts datasheet Fig. 4 millimetres (55 × 40 board, origin top-left, J1 at top) into the rotated frame (40 wide × 55 tall); `LIB.mm(x′, y′) = {x: 362 + 8.4·x′, y: 278 + 8.4·y′}`. Drawn elements (classes as today):
- `#outline`: `mm(0,0)` size 336 × 462, `rx = 16.8`;
- four `.hole` (r = 1.25 mm) at `rot` of (3.5,3.5), (51.5,3.5), (3.5,36.5), (51.5,36.5) → (3.5,51.5), (3.5,3.5), (36.5,51.5), (36.5,3.5) mm;
- two `.conn` bodies 3 × 22 mm (vertical) centred at `rot(25,3) = (3,30)` for CN1 and `rot(25,37) = (37,30)` for CN2, `data-conn="CN1"/"CN2"`, text «CN1» / «CN2» (`.lbl.s`) beside each body, and a `.pin1` dot (r = 2.2 px) at the **top** end of each body, inset 1.2 mm as today: `y′ = 20.2 mm` (= `rot(34.8, ·)`);
- `.soc` 15 × 15 mm centred at `rot(31.9875, 23.025) = (23.025, 23.0125)`, label «BCM2711»;
- `.ant` hatched keep-out `x′ 10.5…21.5, y′ 48.5…55` mm (bottom edge, left of centre), `.ufl` at `rot(2.567, 9) = (9, 52.433)` mm, three `.lbl.s` lines below the outline starting at `y = 760`: «Зона без меди 6.5 × 11 мм — внизу слева:», «под этой областью ни на одном слое», «baseboard нет меди; U.FL рядом с ней.»

**Headers and caption** (`.lbl`, `.lbl.b` for the two connector headers):
- `(162, 30, middle)` «CN1 (J1) · выводы 1–100 · нечётные — внешний ряд»;
- `(878, 30, middle)` «CN2 (J2) · выводы 101–200 · нечётные — внутренний ряд»;
- `(162, 50, middle)` «1 / 2», `(878, 50, middle)` «101 / 102»; `(162, 975, middle)` «99 / 100», `(878, 975, middle)` «199 / 200»;
- caption `(530, 992, middle)` «CM4, вид сверху, в масштабе, повёрнут на 90° против часовой стрелки: CN1 (J1 даташита) слева, CN2 (J2) справа, выводы 1 и 101 — вверху. Разъёмы на нижней стороне модуля.»

Nothing on the board says «J1 ·» or «J2 ·» any more; `#board .conn` count stays 2, `.hole` 4, `.ant` 1, `.lead` 0.

### 2. Check against the schematic

**New data file `data/schematic.json`**, generated by `tools/extract_schematic.py` from `Review/_data/chains.json`:

```json
{"source": {"project": "Retr_2026-09-26", "board": "Retr_Cross", "snapshot": "2026-10-14 12:28–12:34", "chains": "Review/_data/chains.json"},
 "pins": {"55": {"net": "UART0_TXD", "to": ["UART.2"], "wired": true}, "37": {"net": "IO7", "to": [], "wired": false}, "20": {"net": "", "to": [], "wired": null}, "...": {}}}
```

`net` = `sch_net`; `to` = `sch_destinations + sch_destinations_via_series_part` (first 6, strings as in chains.json, e.g. `"ETH_Y.1 (via R1)"`); `wired` = `wired_beyond_cm4` (`true`/`false`/`null`). All 200 keys present. `tools/build.py` injects it as the sixth global `var SCHEMATIC = …;`.

**Verdict** `LIB.checkOf(pin, ov, sch)` → `{code, text}` (Project layer only), with `s = sch.pins[String(pin.n)]`:

| code | condition (in this order) | symbol + text |
|---|---|---|
| `gnd_open` | `pin.grp === 'GND' && s.net !== 'GND'` | `✗ GND не на земле` + (`s.net ? ' (в схеме: ' + s.net + ')' : ' (без цепи)'`) |
| `ok` | `ov.net && s.net === ov.net && s.wired !== false` | `✓ совпадает со схемой` |
| `dead_end` | `ov.net && s.net === ov.net && s.wired === false` | `≈ метка на CN есть, дальше обрыв` |
| `renamed` | `ov.net && s.net && s.net !== ov.net` | `≈ в схеме: ` + s.net, plus ` · обрыв` when `s.wired === false` |
| `missing` | `ov.net && !s.net` | `✗ в схеме нет` |
| `extra` | `!ov.net && s.net` | `≈ в схеме метка ` + s.net + `, на сайте не используется` |
| `none` | otherwise | `— не используется` |

`LIB.hasIssue(pin, ov, check)` = `check.code ∈ {gnd_open, missing}` or `ov.issues.length > 0`.

The `Dir.` table column and the panel «Direction» row show `LIB.DIRS[LIB.dirOf(...)]`; for a spare pin that reads `spare (no net)`.

**Per-pin concerns** live in `project.json` as `pins[n].issues: [string]` (Russian, 10–320 chars, each ending with a source tag — see §4.4). They are shown in the panel («Замечания») and the table («Проверка» column shows the verdict symbol plus `· N замеч.`).

### 3. Page UI (Project layer additions; Datasheet layer unchanged except the drawing)

- **Legend row** gets a toggle button `#only-issues` («Только с замечаниями», `aria-pressed`) visible in the Project layer. When pressed, `visible(p)` also requires `LIB.hasIssue(...)`; it combines with the device filter; switching layer resets it.
- **Table**: columns `#, Conn., Signal, Group, Dir., Net*, Device*, Mode*, Status*, Схема*, Проверка*, Note*, Pair, Datasheet` (`*` = Project layer). `Conn.` shows `CN1`/`CN2`. `Схема` = `s.net || '—'` (mono). `Проверка` = verdict symbol + text, plus ` · N замеч.` when issues exist; cell class `c-check c-<code>`. `Dir.` shows the layer's direction (`LIB.DIRS[dirOf(...)]`).
- **Counter** (`#cnt`): «Показано N из 200 пинов»; in the Project layer append « · ✓ a · ≈ b · ✗ c · — d» counted over all 200 pins (`✓` = ok; `≈` = dead_end + renamed + extra; `✗` = gnd_open + missing; `—` = none).
- **Pad badge**: in the Project layer a pad with `hasIssue` gets class `warn` (small red triangle `path.badge` in the pad's top-right corner, 6 px).
- **Panel** (`#panel`) header: `CN1 (J1 в даташите) · нечётный ряд` / `CN2 (J2 в даташите) · чётный ряд`. Project layer `dl` adds rows **Direction** (project direction), **Схема** (`code(s.net)` + «→ dest1, dest2…» or «—»), **Проверка** (verdict text, class `chk-<code>`); after the datasheet quote a block `h3` «Замечания» with `ul` of `issues` rendered through `noteLi` (source tag styled `.src`), or the line «Замечаний нет.» when empty. Filter summary (device selected, no pin) lists pins as `pin N · sig — net` and appends the issue count.
- **CSV** columns: `pin;connector;row;signal;group;direction;net;device;mode;status;schematic_net;check;issues;pair;note;datasheet` where `connector` is `CN1`/`CN2`, `direction` is the Project direction, `check` is the verdict code, `issues` joined with ` | `.
- Subtitle `#sub`: `PROJECT.meta.cm4 + ' · rev. 3, 2026-10-15 · схема: Retr_2026-09-26 (снимок 2026-10-14)'` (date/rev from `meta`, snapshot from `SCHEMATIC.source`).

### 4. Data

#### 4.1 `data/project.json` — meta and devices

`meta`: `{"title": "CM4 baseboard — 2×100-pin pinout", "rev": "3", "date": "2026-10-15", "cm4": "CM4 с eMMC и Wi-Fi", "schematic": "Retr_2026-09-26 / Retr_Cross, снимок 2026-10-14"}`.

`devices` (keys fixed, names English, colours kept where the key exists):

| key | name | change |
|---|---|---|
| CONSOLE | `Service console · UART0` | — |
| GPS | `GPS · UART2` | — |
| CRSF1 | `CRSF TX1 (TBS) · UART3 · CRSF_Mod` | name |
| CRSF2 | `CRSF TX2 (ELRS) · UART4 · CRSF_Mod` | name |
| SERVO | `Servo bus ST3025 · UART5 · CRSF_Mod` | name |
| I2C | `I2C1 · TCA9534A switches, INA219, sensors` | name |
| VRX | `VRX module · SPI6, LE, CVBS mux` | absorbs CVBS |
| FAN | `Fan` | — |
| PCIE | `PCIe → M.2 NVMe` | — |
| CAM | `Camera FPC1 · CSI1 (4 lanes)` | **new**, colour `#3C9D8A` (old CSI0) |
| I2C0 | `I2C0 · camera, ADV7280A-M, VRX ADS1115` | **new**, colour `#5B8AC2` |
| VDEC | `ADV7280A-M video decoder · CSI0` | name |
| USB | `USB 2.0` | — |
| ETH | `Ethernet → ETH1 (2 pairs)` | name |
| CTRL | `Boot / reset / LEDs` | — |
| POWER | `Power · Retr_PWR` | name |
| SPARE | `Spare GPIO` | **new**, colour `#7A7A7A` |
| GND | `GND` | — |
| NC | `Not used` | — |
| ~~CVBS~~, ~~PWRKEY~~, ~~CSI0~~ | — | **removed** |

#### 4.2 `data/project.json` — defaults

`PWR5.net = "+5V_CM"`, note names the source (Retr_PWR U4 TPS5430 → `X_U8.2/4` → CN1 77–87) and the range 4.75–5.25 В. `PWR33.net = "+3V"` (the carrier's name, D5), note says it is the CM4's 3.3 В output (CM4_3.3V, 300 мА/вывод, 600 мА всего) and that on the carrier `+3V` reaches only GPIO_VREF so far. Other defaults unchanged (`GND`, `PWR18`, `SD`, `HDMI0/1`, `DSI0/1`, `RSV` dnc, `ANALOG`, `VDAC`).

#### 4.3 `data/project.json` — pins (rev 3 allocation)

Fields per explicit entry: `net`, `dev`, `mode` (GPIO pins), `dir` (mandatory for GPIO-group pins and 80/82; allowed elsewhere), `status` (default `used`), `note` (Russian), `issues` (list, may be empty; omitted = empty). Only the rows below change versus rev 2; **every other explicit rev 2 entry is kept** with its note (re-read for stale wording: `J1/J2`, `CSI1` for the decoder, `DIR`, `RTS3/RTS4`, `TX1_PWR_EN` as GPIO).

**CN1**

| pin | GPIO | rev 2 → rev 3 net | dev | mode | dir | status | note must say / issues (sources) |
|---|---|---|---|---|---|---|---|
| 3, 5, 9, 11 | — | `ETH_PAIR3_P/N`, `ETH_PAIR2_P/N` (keep) | ETH | — | bidir | **opt** | carrier is 100 Мбит on two pairs; these are dangling labels. Issue: решение по коммутатору на плате [Review/website.md п. 12] |
| 4, 6, 10, 12 | — | → `TD1+`, `TD1-`, `TD0-`, `TD0+` | ETH | — | bidir | used | → TVS1 → `LT1*` (ALANL100X1) → `ETH1` SM04B, 100 Мбит, пара 100 Ом |
| 15 | — | → `E_LED_Y` | ETH | — | out | opt | через R1 3K3 → `ETH_Y`. Issue: анод светодиода на `PWR_3V` (отключаемая шина) — перевести на CM4_3V3 [Review/power-board.md п. 10] |
| 17 | — | → `E_LED_G` | ETH | — | out | opt | через R2 → `ETH_G`; same issue |
| 19 | — | `ETH_nLED_SPD1` (keep) | ETH | — | out | opt | обрыв на CN1 |
| 21 | — | → `A_LED_G` | CTRL | — | out | used | через R10 → `ACT`; anode issue as 15 |
| 24 | 26 | `FAN_TACH` | FAN | GPIO | **in** | used | note unchanged; **no issues** (the dangling label is reported by the verdict «обрыв», not as an issue) |
| 25 | 21 | `VRX_CLK` | VRX | ALT3 SPI6_SCLK | out | used | → `VRX_1.4`. Issue: на платах 1.2/3.3 ГГц X1.2/X1.4 = SCK/DAT перепутаны [Review/vrx-board.md п. 1] |
| 26 | 19 | `TX2_PWR_EN` → `""` | **SPARE** | GPIO | bidir | opt | свободен: управление ключом TX2 — выход P7 TCA9534A (вариант B). Issues: при варианте A — вернуть `TX2_PWR_EN` [Review/power-board.md разд. 7.2]; ключей TX нет ни на носителе, ни на Retr_PWR, `+V_TX2` не подключена, напряжение (батарея или 12 В) не решено [Review/power-board.md п. 6] |
| 27 | 20 | `VRX_DATA` | VRX | ALT3 SPI6_MOSI | out | used | → `VRX_1.2`; same swap issue |
| 28 | 13 | `UART5_RXD` | SERVO | ALT4 RXD5 | in | used | от блока CBB3 (CRSF_Mod) RX. Issue: на PCB два блока CBB3/CBB4 на одной шине `SRV_1/2` — оставить один [Review/crsf-one-wire.md п. 12] |
| 29 | 16 | `CRSF2_INV` | CRSF2 | GPIO | out | used | → CBB2 INV; INV нельзя оставлять открытым (делитель R4/~R4) [Review/crsf-one-wire.md п. 9]. Check: carrier label `IO16`, обрыв |
| 30 | 6 | `CVBS_SEL0` | **VRX** | GPIO | out | used | → `VRX_1.18` = CH_A RS2255 на плате VRX; pull-up при загрузке [Review/vrx-board.md п. 10]. Issue (30 and 44): уровень 3.3 В на входах RS2255 и приёмников при их питании 5 В не проверен; таблица BA→канал по DS RS2255 не сверена [Review/website.md п. 10] |
| 31 | 12 | `UART5_TXD` | SERVO | ALT4 TXD5 | out | used | → CBB3 TX; направление — авто (RC на модуле), DIR не нужен |
| 34 | 5 | `UART3_RXD` | CRSF1 | ALT4 RXD3 | in | used | Issue: на PCB CN1.34 и CN1.37 в одной цепи RX3 — Import Changes [Review/crsf-one-wire.md п. 4] |
| 37 | 7 | `CRSF1_DIR` → `""` | **SPARE** | GPIO | bidir | opt | DIR не нужен (авто-направление CRSF_Mod); pull-up при загрузке; SPI0_CE1_N. Issue: вариант A использует его для `PW_VRX` [Review/power-board.md разд. 7.2] |
| 38 | 11 | `CRSF2_DIR` → `""` | **SPARE** | GPIO | bidir | opt | DIR не нужен (авто-направление CRSF_Mod); **pull-down при загрузке** (GPIO9–27); ALT0 = SPI0_SCLK. Issue: вариант A использует его для `PW2`+`PW3` [Review/power-board.md разд. 7.2] |
| 39 / 40 | 8 / 9 | `UART4_TXD` / `UART4_RXD` | CRSF2 | ALT4 TXD4 / RXD4 | out / in | used | → CBB2 TX/RX. Issue (39): V_IN блока на PCB = `+5V_CM`, нужно 3.3 В [Review/crsf-one-wire.md п. 3] |
| 41, 45, 46, 47 | 25, 24, 22, 23 | `VRX_LE4/3/1/2` → `VRX_SS4`, `VRX_SS3`, `VRX_SS1`, `VRX_SS2` | VRX | GPIO | out | used | → `VRX_1.12/10/6/8`, LE приёмника N (защёлка по фронту) |
| 44 | 10 | `CVBS_SEL1` | **VRX** | GPIO | out | used | → `VRX_1.20` = CH_B; pull-down при загрузке |
| 48 | 27 | `CRSF1_INV` | CRSF1 | GPIO | out | used | → CBB1 INV; as 29 |
| 49 | 18 | `FAN_PWM` | FAN | ALT5 PWM0_0 | out | used | — |
| 50 | 17 | `TX1_PWR_EN` → `""` | **SPARE** | GPIO | bidir | opt | as 26 (P6, `+V_TX1`, both issues) |
| 51 / 55 | 15 / 14 | `UART0_RXD` / `UART0_TXD` | CONSOLE | ALT0 RXD0 / TXD0 | in / out | used | → `UART.3` / `UART.2` (SM03B) ✓; **no issues** |
| 54 | 4 | `UART3_TXD` | CRSF1 | ALT4 TXD3 | out | used | → CBB1 TX; overlay `dtoverlay=uart3` без RTS; V_IN issue as 39 |
| 56 / 58 | 3 / 2 | `I2C1_SCL`/`I2C1_SDA` → `SCL1` / `SDA1` (carrier labels, D5) | I2C | ALT0 SCL1 / SDA1 | bidir | used | ведомые: TCA9534A (0x38–0x3F) → ключи `PW_VRX`, `PW2`, `PW3`, `PW_RZ1`, `PW_RZ2`, `PW7`, `TX1/TX2_PWR_EN`; INA219 `U25` (перенести с I2C0; A0/A1 задать [Review/power-board.md п. 8]); далее RM3100 (0x20–0x23), BMP390, Matek INA-BM. ADS1115 платы VRX остаётся на I2C0 (плата заказана). Подтяжки 1.8 кОм на CM4. Issues: на носителе `SDA1/SCL1` — обрыв [Review/website.md разд. 5]; INA219 сейчас на I2C0 [Review/power-board.md п. 9] |
| 57, 61, 62, 63, 67, 69, 75 | — | `""` (new explicit entries) | NC | — | nc | nc | eMMC: не подключать. Issue: на CN1 метки `SD_*` без цепей — для Lite-модуля? [Review/website.md п. 15] |
| 80 / 82 | 45 / 44 | `I2C0_SCL`/`I2C0_SDA` → `SCL0` / `SDA0` | **I2C0** | — | bidir | used | ведомые: камера `FPC1.3/2`, `U1` ADV7280A-M 0x21, `J2` внешний CVBS_Mod (тоже 0x21), ADS1115 платы VRX (`VRX_1.16/14`, ADDR не подключён — задать, 0x48 по DS ADS1115 не сверено [Review/vrx-board.md п. 4]). Issues: `U25` INA219 — перенести на I2C1 (D4) [Review/power-board.md п. 9]; подтяжки 4K7 к 5 В на платах VRX дают ≈ 3.77 В на линии — плата заказана, уровень проверить на стенде [Review/vrx-board.md п. 3]; два адреса 0x21 [Review/analog-to-csi.md п. 6]; до CN1.80/82 не разведено [Review/analog-to-csi.md п. 3]; ведомые питаются от `PWR_3V`, которую включает `PW_VRX` — включать при загрузке (D1a) [Review/power-board.md п. 4] |
| 92, 93, 99 | — | `RUN_PG`, `nRPIBOOT`, `GLOBAL_EN` (keep) | CTRL | — | (ds) | used | Issue: в схеме нет — добавить кнопку/перемычку (сервис по ТЗ) [Review/website.md разд. 5] |
| 20, 89, 91 | — | keep | CTRL | — | (ds) | opt | Issue: в схеме нет, подключение опционально (перемычка) [Review/website.md разд. 5] |
| 95 | — | `PWR_nLED` → `NPWR_LED` | CTRL | — | out | opt | через R9 → `PWR`. Issues: нужен буфер (DS); анод на `PWR_3V` [Review/power-board.md п. 10] |
| 97 | — | `CAM_GPIO` | **CAM** | — | out | used | → `FPC1.6`. Issue: камера питается от `PWR_3V` (`FPC1.1`), которую включает `PW_VRX` — включать при загрузке через gpio-hog (D1a) [Review/power-board.md п. 4] |
| 98 | — | `GND` (new explicit) | GND | — | gnd | used | Issue: CN1.98 без цепи — подключить к GND [Review/website.md п. 13] |
| 100 | — | `EXT_nRST` → `NEXTRST` | CTRL | — | out | opt | → `J_RST` 0R → `EXT_RST` (дальше никуда) |

**CN2**

| pin | rev 2 → rev 3 net | dev | dir | status | note must say / issues |
|---|---|---|---|---|---|
| 101 | `USB_OTG_ID` → `USBOTG_ID` | USB | in | used | → `R_OTG` 2K2 → GND (роль хоста) |
| 102, 109, 110, 112, 116, 118, 122, 124 | keep | PCIE | (ds) | used | Issue once per pin (no semicolons inside — the CSV test depends on it): «цепей PCIe на носителе нет, разъём M.2 не входит в текущий этап [Review/website.md разд. 5]» |
| 103 / 105 | `USB_DN`/`USB_DP` → `USB2_N` / `USB2_P` | USB | bidir | used | → `PWR_IN1` и `USB1` параллельно. Issue: два USB-C на одной паре, без хаба, VBUS/CC [Review/website.md п. 11] |
| 111 | `""` (new explicit) | NC | nc | nc | Issue: метка `TV_OUT` на CN2.11 без цепи [Review/analog-to-csi.md п. 12] |
| 115 / 117 | `CSI1_D0_N/P` → `CAM1_D0_N` / `CAM1_D0_P` | **CAM** | in | used | ← `FPC1.21/20`, пара 100 Ом. Issues: в схеме `CAM1_DO_N/P` (буква O) [Review/analog-to-csi.md п. 13]; разбег пары 0.219 мм [Review/analog-to-csi.md п. 11]; камера на `PWR_3V`, включается вместе с `PW_VRX` (D1a) [Review/power-board.md п. 4] |
| 121 / 123 | `""`(nc) → `CAM1_D1_N` / `CAM1_D1_P` | CAM | in | used | ← `FPC1.18/17` |
| 127 / 129 | `CSI1_CLK_N/P` → `CAM1_C_N` / `CAM1_C_P` | CAM | in | used | ← `FPC1.15/14` |
| 133 / 135 | → `CAM1_D2_N` / `CAM1_D2_P` | CAM | in | used | ← `FPC1.12/11` |
| 139 / 141 | → `CAM1_D3_N` / `CAM1_D3_P` | CAM | in | used | ← `FPC1.9/8` |
| 128 / 130 | `CSI0_D0_N/P` → `CAM0_D0_N` / `CAM0_D0_P` | **VDEC** | in | used | ← `U1.10/9` через R5/R6; параллельно `J2.14/13`. Issues: в схеме `CAM0_DO_*` (буква O) [Review/analog-to-csi.md п. 13]; тракт до CN2 не разведён [Review/analog-to-csi.md п. 3]; U1 и J2 параллельно — выбрать одно [Review/analog-to-csi.md п. 6]; U1 питается от `PWR_3V`, включается вместе с `PW_VRX` (D1a) [Review/power-board.md п. 4]; для ADV на CSI0 с I2C на 82/80 нужен свой overlay, не проверено [Review/analog-to-csi.md п. 2] |
| 134 / 136 | `CSI0_D1_N/P` → `CAM0_D1_N` / `CAM0_D1_P` | VDEC | in | **opt** | только `J2.11/10` — порт внешнего CVBS_Mod; ADV7280A-M использует одну линию, D1 на модуле не подключена. Issue: `R34`/`R35` (GPIO0/GPIO1 разъёма J2) висят — для камеры на J2 понадобилась бы линия включения, кандидат — резервный GPIO [Review/analog-to-csi.md п. 8] |
| 140 / 142 | `CSI0_CLK_N/P` → `CAM0_C_N` / `CAM0_C_P` | VDEC | in | used | ← `U1.12/11` через R13/R19; `J2.8/7` |
| 197, 198 | `GND` (new explicit) | GND | gnd | used | Issue: CN2.97/98 на цепи `RG_OE` вместо GND [Review/website.md п. 13] |

Invariants (tested): all 28 GPIO assigned exactly once; GPIO in use = 24, spare = 4 (7, 11, 17, 19); modes match DS ALT table; nets unique outside GND/PWR groups; `_P`/`_N` polarity matches the datasheet signal; every pin resolves (no `free`).

#### 4.4 Issues and notes — text rules

Russian, 10–320 characters, one fact per item, ends with a source tag matching
`\[(Review/(power-board|crsf-one-wire|vrx-board|analog-to-csi|website|README)\.md(?: (?:п\.|разд\.) [0-9][0-9., –-]*)?|DS §[0-9.]+(?:, Table \d+)?|DS Table \d+|DS Fig\. \d+|BCM2711 §[0-9.]+|ТЗ|project|sdtv2csi|CM4IO)\]$`
(the existing `[DS Fig. 4]`, `[sdtv2csi]` and `[CM4IO]` bullets stay valid). Issues used in the CSV test rows (PCIe pins) contain no `;`.
Notes keep the v3 glossary («подтяжка к питанию (pull-up)», units Ом/кОм/В/мА/мм). Nothing in `project.json`, `rationale.json`, `routing.json` may still describe the decoder on CSI1, the camera on CSI0, `CRSF*_DIR`/RTS3/RTS4 as the direction scheme, `TX*_PWR_EN` as GPIO outputs, `VRX_LE*`, `CSI1_D0_*`, `I2C0_SDA/SCL`, `I2C1_SDA/SCL`, `CM4_3V3` as a net name (prose may say «CM4_3.3V»), `CVBS switch` on the carrier, or J1/J2 as connector names (a grep test enforces the list).

#### 4.5 `data/rationale.json`

- `devices` keys = project devices minus GND/NC (test): add `CAM`, `I2C0`, `SPARE`; remove `CVBS`, `PWRKEY`, `CSI0`; rewrite `VDEC`, `VRX`, `I2C`, `CRSF1`, `CRSF2`, `SERVO`, `POWER`, `ETH` bullets for D1–D8.
- `overview`: bullet 1 (RTS rationale) → «UART3/UART4 остаются за CRSF: RTS3/RTS4 не нужны — CRSF_Mod переключает направление сам …»; bullet 4 → budget «24 из 28, резерв GPIO7, 11, 17, 19 …»; bullet 5 → the CSI assignment of D3; add one bullet on the TCA9534A (D1). 5–7 bullets total.
- `pins`: entries for 37, 38, 50, 26 explain the spare; 115/121/127 → the camera lanes; 128/140 → decoder on CSI0; 30/44 → mux on the VRX module; 58 → expander + sensor move; required keys list in the test = `36 35 37 38 30 44 50 26 49 27 25 46 78 80 82 55 115 128 99 93 58`.

#### 4.6 `data/routing.json`

- Section 8 «Видеодекодер ADV7280A-M (проект)»: decoder on **CSI0** (pins 128/130, 140/142), camera FPC1 on CSI1 four lanes; fix the 51 Ом wording (51 Ом after the series 24 Ом, before 0.1 мкФ) [Review/analog-to-csi.md п. 14]; overlay note: «штатный adv728x-m нацелен на CSI1 — для CSI0 нужен свой вариант overlay (не проверено)».
- New section 9 «Подключение готовых плат Retr_PWR, VRX, CRSF_Mod, CVBS_Mod (проект)», 10–14 bullets: the 5 В chain and its fixes (`V-IN`→`V_IN`, filter, R4 = 3K24, carrier copper); the expander + BSS138 drivers and the gate pull-down rule; P6/P7 reserved for TX switches that still have to be designed (`+V_TX1/+V_TX2` unconnected) [Review/power-board.md п. 6]; `PWR_3V` hangs on `PW_VRX` and stays so (D1a): enable `PW_VRX` at boot via a `gpio-hog` on the expander, camera/decoder probe after it [Review/power-board.md п. 4]; servo rails are not 12 В yet: MC34063 divider sets ≈ 27.95 В, fix before enabling `PW2`/`PW3` [Review/power-board.md п. 5]; CBB V_IN = 3.3 В; one servo block; `VRX_1` pin order and the DATA/CLK swap on two boards; I2C split (I2C0: camera, ADV, VRX ADS1115 as built; I2C1: expander, INA219, sensors), the 5 В pull-ups on the VRX boards as a bench-check item; GND 98/197/198; naming rule D5. Tags from §4.4 (`[Review/… п. N]`).
- `groups.GND` gets a **second** bullet «На носителе CN1.98 без цепи, а CN2.97/98 на цепи RG_OE — подключить все три к GND [Review/website.md п. 13]» (the browser test for pin 1 compares the routing-card count with `ROUTING.groups.GND.length`).
- The `SERVO` rationale/notes must not call the servo rail «12 В» as a fact; it is the ТЗ target, the board currently sets ≈ 27.95 В.
- Test `SECTIONS` list gains the new title; `TAG` regex gains the `Review/…` form.

### 5. Files

- Modify: `cm4_pinout.html` (CSS, `LIB`, UI), `tools/build.py`, `data/project.json`, `data/rationale.json`, `data/routing.json`, `tests/test_project.py`, `tests/test_rationale.py`, `tests/test_routing.py`, `tests/test_build.py`, `tests/test_lib.mjs`, `tests/test_browser.py`.
- Create: `tools/extract_schematic.py`, `data/schematic.json`, `tests/test_schematic.py`, `docs/superpowers/specs/2026-10-15-cm4-pinout-v4-design.md` (this file), `docs/superpowers/plans/2026-10-15-cm4-pinout-v4.md`.
- Untouched: `data/cm4_datasheet.json`, `data/ds_ru.json`, `tools/extract_datasheet.py`, `tests/test_datasheet.py`, `tests/test_ds_ru.py`, `index.html`, nginx configs, everything under `Review/` (read-only input) and EasyEDA.

### 6. Out of scope

Live EasyEDA sync; redesigning Ethernet/USB/PCIe/GPS/fan; an EN/RU toggle; deep links; redeploy steps (merge = deploy, D10); editing `Review/*.md`.
