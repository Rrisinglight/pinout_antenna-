import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync(new URL('../cm4_pinout.html', import.meta.url), 'utf8');
const grab = (a, b) => html.slice(html.indexOf(a) + a.length, html.indexOf(b));
const ctx = vm.createContext({});
vm.runInContext(grab('/*DATA-START*/', '/*DATA-END*/'), ctx);
vm.runInContext(grab('/*LIB-START*/', '/*LIB-END*/'), ctx);
const { LIB, DATA, PROJECT, ROUTING } = ctx;
const byN = Object.fromEntries(DATA.pins.map(p => [p.n, p]));
const ov = n => LIB.merge(byN[n], PROJECT);

test('data embedded', () => {
  assert.equal(DATA.pins.length, 200);
  assert.ok(PROJECT.pins['55']);
  assert.ok(ROUTING.groups && ROUTING.pins && Array.isArray(ROUTING.general));
});

test('padXY: J1 strip above, J2 strip below, pin 1/2 at the right end, odd row on top', () => {
  assert.deepEqual({ ...LIB.padXY(1) }, { x: 942, y: 34 });
  assert.deepEqual({ ...LIB.padXY(2) }, { x: 942, y: 54 });
  assert.deepEqual({ ...LIB.padXY(99) }, { x: 60, y: 34 });
  assert.deepEqual({ ...LIB.padXY(100) }, { x: 60, y: 54 });
  assert.deepEqual({ ...LIB.padXY(101) }, { x: 942, y: 484 });
  assert.deepEqual({ ...LIB.padXY(200) }, { x: 60, y: 504 });
  assert.deepEqual({ ...LIB.padXY(3) }, { x: 924, y: 34 });
});

test('outline geometry in mm → px', () => {
  assert.equal(LIB.MM, 8.4);
  assert.deepEqual({ ...LIB.mm(0, 0) }, { x: 269, y: 118 });
  assert.deepEqual({ ...LIB.mm(55, 40) }, { x: 269 + 55 * 8.4, y: 118 + 40 * 8.4 });
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

test('csv: English header with ds column, 200 rows', () => {
  const lines = LIB.csv(DATA.pins, PROJECT).split('\n');
  assert.equal(lines.length, 201);
  assert.equal(lines[0], 'pin;connector;row;signal;group;direction;net;device;mode;status;pair;note;datasheet');
  assert.match(lines[55], /^55;J1;odd;GPIO14;GPIO;bidir;UART0_TXD;CONSOLE;ALT0 TXD0;used;;"Service console/);
  assert.match(lines[116], /^116;J2;even;PCIe_RX_P;PCIE;in;PCIE_RX_P;PCIE;;used;118;/);
});
