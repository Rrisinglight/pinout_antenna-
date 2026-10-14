import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync(new URL('../cm4_pinout.html', import.meta.url), 'utf8');
const grab = (a, b) => html.slice(html.indexOf(a) + a.length, html.indexOf(b));
const ctx = vm.createContext({});
vm.runInContext(grab('/*DATA-START*/', '/*DATA-END*/'), ctx);
vm.runInContext(grab('/*LIB-START*/', '/*LIB-END*/'), ctx);
const { LIB, DATA, PROJECT, ROUTING, DS_RU, RATIONALE, SCHEMATIC } = ctx;
const byN = Object.fromEntries(DATA.pins.map(p => [p.n, p]));
const ov = n => LIB.merge(byN[n], PROJECT);

test('data embedded incl. SCHEMATIC', () => {
  assert.equal(Object.keys(SCHEMATIC.pins).length, 200);
  assert.equal(PROJECT.meta.rev, '3');
});

test('padXY: CN1 columns at x 152/172, CN2 at 868/888, pin 1/101 top, 18 px rows', () => {
  assert.deepEqual({ ...LIB.padXY(1) }, { x: 152, y: 60 });
  assert.deepEqual({ ...LIB.padXY(2) }, { x: 172, y: 60 });
  assert.deepEqual({ ...LIB.padXY(3) }, { x: 152, y: 78 });
  assert.deepEqual({ ...LIB.padXY(99) }, { x: 152, y: 942 });
  assert.deepEqual({ ...LIB.padXY(100) }, { x: 172, y: 942 });
  assert.deepEqual({ ...LIB.padXY(101) }, { x: 868, y: 60 });
  assert.deepEqual({ ...LIB.padXY(102) }, { x: 888, y: 60 });
  assert.deepEqual({ ...LIB.padXY(200) }, { x: 888, y: 942 });
  assert.equal(LIB.sideOf(1), 'L'); assert.equal(LIB.sideOf(2), 'R'); assert.equal(LIB.sideOf(101), 'L'); assert.equal(LIB.sideOf(200), 'R');
  assert.equal(LIB.connOf(byN[1]), 'CN1'); assert.equal(LIB.connOf(byN[101]), 'CN2');
});

test('rotated outline: rot + mm', () => {
  assert.deepEqual({ ...LIB.rot(55, 0) }, { x: 0, y: 0 });
  assert.deepEqual({ ...LIB.rot(0, 0) }, { x: 0, y: 55 });
  assert.deepEqual({ ...LIB.rot(25, 3) }, { x: 3, y: 30 });
  assert.deepEqual({ ...LIB.rot(25, 37) }, { x: 37, y: 30 });
  assert.deepEqual({ ...LIB.mm(0, 0) }, { x: 362, y: 278 });
  assert.deepEqual({ ...LIB.mm(40, 55) }, { x: 362 + 40 * 8.4, y: 278 + 55 * 8.4 });
});

test('dirOf: datasheet vs project', () => {
  assert.equal(LIB.dirOf(byN[55], ov(55), 'ds'), 'bidir');
  assert.equal(LIB.dirOf(byN[55], ov(55), 'prj'), 'out');
  assert.equal(LIB.dirOf(byN[34], ov(34), 'prj'), 'in');
  assert.equal(LIB.dirOf(byN[37], ov(37), 'prj'), 'spare');   // spare: status opt, empty net → no glyph, shown as 'spare (no net)'
  assert.equal(LIB.DIRS.spare, 'spare (no net)');
  assert.equal(LIB.dirOf(byN[1], ov(1), 'prj'), 'gnd');
  assert.equal(LIB.dirOf(byN[57], ov(57), 'prj'), 'nc');
  assert.equal(LIB.dirOf(byN[116], ov(116), 'prj'), 'in');    // no project dir → datasheet dir
});

test('checkOf verdicts', () => {
  const c = n => ({ ...LIB.checkOf(byN[n], ov(n), SCHEMATIC) });   // spread: vm-realm object → this realm, as for padXY
  assert.deepEqual(c(55), { code: 'ok', text: '✓ совпадает со схемой' });
  assert.deepEqual(c(24), { code: 'dead_end', text: '≈ метка на CN есть, дальше обрыв' });
  assert.deepEqual(c(37), { code: 'extra', text: '≈ в схеме метка IO7, на сайте не используется' });   // empty project net → extra, not renamed
  assert.deepEqual(c(78), { code: 'dead_end', text: '≈ метка на CN есть, дальше обрыв' });   // +3V adopted (D5), label reaches only CN1
  assert.deepEqual(c(29), { code: 'renamed', text: '≈ в схеме: IO16 · обрыв' });
  assert.deepEqual(c(128), { code: 'renamed', text: '≈ в схеме: CAM0_DO_N' });
  assert.deepEqual(c(92), { code: 'missing', text: '✗ в схеме нет' });
  assert.deepEqual(c(57), { code: 'extra', text: '≈ в схеме метка SD_CLK, на сайте не используется' });
  assert.deepEqual(c(98), { code: 'gnd_open', text: '✗ GND не на земле (без цепи)' });
  assert.deepEqual(c(197), { code: 'gnd_open', text: '✗ GND не на земле (в схеме: RG_OE)' });
  assert.deepEqual(c(1), { code: 'ok', text: '✓ совпадает со схемой' });
  assert.deepEqual(c(146), { code: 'none', text: '— не используется' });
  assert.equal(LIB.hasIssue(byN[24], ov(24), c(24)), false);
  assert.equal(LIB.hasIssue(byN[98], ov(98), c(98)), true);
  assert.equal(LIB.hasIssue(byN[82], ov(82), c(82)), true);
});

test('merge and labels are English', () => {
  assert.equal(ov(55).net, 'UART0_TXD');
  assert.equal(ov(55).devName, 'Service console · UART0');
  assert.equal(ov(76).status, 'dnc');
  assert.equal(LIB.STATUS.dnc, 'do not connect');
  assert.equal(LIB.DIRS.bidir, 'bidirectional');
  assert.equal(LIB.GROUPS.CTRL.n, 'Control');
  assert.equal(LIB.matches, undefined);
});

test('routingFor merges group and pin notes', () => {
  const r = LIB.routingFor(byN[116], { groups: { PCIE: ['g1 [DS]'] }, pins: { '116': ['p1 [DS]'] } });
  assert.deepEqual([...r], ['g1 [DS]', 'p1 [DS]']);
  assert.deepEqual([...LIB.routingFor(byN[1], { groups: {}, pins: {} })], []);
});

test('csv: new header, CN names, 200 rows', () => {
  const lines = LIB.csv(DATA.pins, PROJECT, SCHEMATIC).split('\n');
  assert.equal(lines.length, 201);
  assert.equal(lines[0], 'pin;connector;row;signal;group;direction;net;device;mode;status;schematic_net;check;issues;pair;note;datasheet');
  assert.match(lines[55], /^55;CN1;odd;GPIO14;GPIO;out;UART0_TXD;CONSOLE;ALT0 TXD0;used;UART0_TXD;ok;;;/);
  assert.match(lines[116], /^116;CN2;even;PCIe_RX_P;PCIE;in;PCIE_RX_P;PCIE;;used;;missing;[^;]+;118;/);
});
