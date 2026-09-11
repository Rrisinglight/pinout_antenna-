import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync(new URL('../cm4_pinout.html', import.meta.url), 'utf8');
const grab = (a, b) => html.slice(html.indexOf(a) + a.length, html.indexOf(b));
const ctx = vm.createContext({});
vm.runInContext(grab('/*DATA-START*/', '/*DATA-END*/'), ctx);
vm.runInContext(grab('/*LIB-START*/', '/*LIB-END*/'), ctx);
const { LIB, DATA, PROJECT } = ctx;
const byN = Object.fromEntries(DATA.pins.map(p => [p.n, p]));
const ov = n => LIB.merge(byN[n], PROJECT);

test('данные вшиты', () => {
  assert.equal(DATA.pins.length, 200);
  assert.ok(PROJECT.pins['55']);
});

test('padXY: пин 1/2 справа, 99/100 слева, нечётный ряд верхний', () => {
  assert.deepEqual({ ...LIB.padXY(1) }, { x: 942, y: 52 });
  assert.deepEqual({ ...LIB.padXY(2) }, { x: 942, y: 72 });
  assert.deepEqual({ ...LIB.padXY(99) }, { x: 60, y: 52 });
  assert.deepEqual({ ...LIB.padXY(100) }, { x: 60, y: 72 });
  assert.deepEqual({ ...LIB.padXY(101) }, { x: 942, y: 340 });
  assert.deepEqual({ ...LIB.padXY(200) }, { x: 60, y: 360 });
  assert.deepEqual({ ...LIB.padXY(3) }, { x: 924, y: 52 });
});

test('merge: явная запись, default по группе, свободный', () => {
  assert.equal(ov(55).net, 'UART0_TXD');
  assert.equal(ov(55).status, 'used');
  assert.equal(ov(55).devName, 'Консоль UART0');
  assert.equal(ov(1).net, 'GND');
  assert.equal(ov(76).status, 'dnc');
  assert.equal(ov(24).net, 'FAN_TACH');
  assert.equal(LIB.merge({ n: 999, grp: 'ZZZ' }, PROJECT).status, 'free');
});

test('busOf', () => {
  assert.equal(LIB.busOf('ALT4 TXD3'), 'uart3');
  assert.equal(LIB.busOf('ALT4 RTS3'), 'uart3');
  assert.equal(LIB.busOf('ALT0 SDA1'), 'i2c1');
  assert.equal(LIB.busOf('ALT3 SPI6_MOSI'), 'spi6');
  assert.equal(LIB.busOf('ALT5 PWM0_0'), 'pwm0');
  assert.equal(LIB.busOf('GPIO'), '');
  assert.equal(LIB.busOf(''), '');
});

test('matches: номер, GPIO, сигнал, цепь, шина, устройство, пусто', () => {
  const m = (n, q) => LIB.matches(byN[n], ov(n), DATA.alt[byN[n].gpio], q);
  assert.equal(m(55, '55'), true);
  assert.equal(m(54, '55'), false);
  assert.equal(m(55, '14'), true);          // GPIO14
  assert.equal(m(55, 'gpio14'), true);
  assert.equal(m(55, 'txd0'), true);        // ALT-имя
  assert.equal(m(54, 'uart3'), true);
  assert.equal(m(34, 'UART3'), true);
  assert.equal(m(37, 'uart3'), true);
  assert.equal(m(55, 'uart3'), false);
  assert.equal(m(54, 'crsf'), true);
  assert.equal(m(54, 'консоль'), false);
  assert.equal(m(55, 'консоль'), true);
  assert.equal(m(116, 'pcie_rx'), true);
  assert.equal(m(1, ''), true);
  assert.equal(m(1, '   '), true);
});

test('colorOf и chipKey по слоям', () => {
  assert.equal(LIB.colorOf(byN[1], ov(1), 'ds', PROJECT), LIB.GROUPS.GND.c);
  assert.equal(LIB.colorOf(byN[55], ov(55), 'prj', PROJECT), PROJECT.devices.CONSOLE.c);
  assert.equal(LIB.colorOf(byN[76], ov(76), 'prj', PROJECT), '#B22222');
  assert.equal(LIB.colorOf(byN[146], ov(146), 'prj', PROJECT), '#9A9A9A');
  assert.equal(LIB.chipKey(byN[55], ov(55), 'ds'), 'GPIO');
  assert.equal(LIB.chipKey(byN[55], ov(55), 'prj'), 'CONSOLE');
  assert.equal(LIB.chipKey(byN[146], ov(146), 'prj'), 'NC');
  assert.equal(LIB.chipKey(byN[76], ov(76), 'prj'), 'NC');
});

test('csv: заголовок, 200 строк, экранирование', () => {
  const lines = LIB.csv(DATA.pins, PROJECT).split('\n');
  assert.equal(lines.length, 201);
  assert.equal(lines[0], 'pin;conn;row;signal;group;dir;net;device;mode;status;pair;note');
  assert.match(lines[55], /^55;J1;odd;GPIO14;GPIO;bidir;UART0_TXD;CONSOLE;ALT0 TXD0;used;;Сервисная консоль/);
  assert.match(lines[116], /^116;J2;even;PCIe_RX_P;PCIE;in;PCIE_RX_P;PCIE;;used;118;/);
  assert.equal(LIB.csv([{ n: 1, conn: 'J1', row: 'odd', sig: 'X', grp: 'ZZZ', dir: 'in' }], PROJECT).split('\n')[1], '1;J1;odd;X;ZZZ;in;;NC;;free;;');
  const esc = LIB.csv([{ n: 1, conn: 'J1', row: 'odd', sig: 'a;b', grp: 'ZZZ', dir: 'in' }], PROJECT).split('\n')[1];
  assert.equal(esc.split(';')[3], '"a');   // значение с ; взято в кавычки
});
