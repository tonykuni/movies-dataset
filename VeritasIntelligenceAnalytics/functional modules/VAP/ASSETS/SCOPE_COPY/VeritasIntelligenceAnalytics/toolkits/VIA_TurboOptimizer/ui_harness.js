'use strict';
// Extract the embedded <script> JS from the PS here-string and exercise it
// under a DOM/fetch shim against mock backend payloads.
const fs = require('fs');
const vm = require('vm');

const ps = fs.readFileSync(process.argv[2] || 'VIA_TurboOptimizer_v2.ps1', 'utf8');
const m = ps.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('No <script> block found'); process.exit(2); }
let js = m[1];

// ---- assertion plumbing ----------------------------------------------------
let pass = 0, fail = 0;
function ok(name, cond) { if (cond) { pass++; console.log('  [PASS]', name); } else { fail++; console.log('  [FAIL]', name); } }

// ---- DOM shim --------------------------------------------------------------
function makeEl(id) {
  const classes = new Set();
  return {
    id, _text: '', _html: '',
    style: {}, _attrs: {},
    clientWidth: 80, clientHeight: 36,
    get textContent() { return this._text; }, set textContent(v) { this._text = String(v); },
    get innerHTML() { return this._html; }, set innerHTML(v) { this._html = String(v); },
    get className() { return [...classes].join(' '); },
    set className(v) { classes.clear(); String(v).split(/\s+/).filter(Boolean).forEach(c => classes.add(c)); },
    classList: { toggle(c, on) { if (on === undefined) { classes.has(c) ? classes.delete(c) : classes.add(c); } else { on ? classes.add(c) : classes.delete(c); } }, add(c) { classes.add(c); }, remove(c) { classes.delete(c); }, contains(c) { return classes.has(c); } },
    setAttribute(k, v) { this._attrs[k] = v; }, getAttribute(k) { return this._attrs[k]; },
    insertAdjacentHTML(pos, h) { this._html += h; },
    appendChild() {}, remove() {}, closest() { return null; }
  };
}
const els = {};
function el(id) { if (!els[id]) els[id] = makeEl(id); return els[id]; }

// checkbox sets for querySelectorAll
let tgtBoxes = [];
let optBoxes = [];

const document = {
  querySelector(sel) {
    if (sel === '#proc tbody') return el('proc-tbody');
    if (sel[0] === '#') return el(sel.slice(1));
    return el(sel);
  },
  querySelectorAll(sel) {
    if (sel === '.tgt') return tgtBoxes;
    if (sel === '.opt') return optBoxes;
    return [];
  },
  createElement() { return makeEl('tmp'); },
  addEventListener() {}
};

// ---- fetch shim ------------------------------------------------------------
const scanPayload = {
  GenTime: '2026-06-08 10:00:00', IsAdmin: false, AgeDays: 3,
  Mem: { TotalGB: 15.7, UsedGB: 9.96, FreeGB: 5.74, UsedPct: 63.44 },
  Cpu: 9,
  Drives: [{ Name: 'C', Root: 'C:\\', UsedGB: 347.5, FreeGB: 128.11 }],
  Env: { EnvMgr: 'C:\\...\\VIA_EnvManager.py', EnvMgrOk: true, Python: 'C:\\py\\python.exe', PythonVer: '3.11.9', PsutilVer: '', PsutilOk: false },
  Targets: [
    { Key: 'UserTemp', Desc: '使用者 TEMP', Path: 'C:\\Temp', Admin: false, Exists: true, SizeMB: 1750.52, Blocked: false },
    { Key: 'LocalTemp', Desc: 'LOCALAPPDATA Temp', Path: 'C:\\LT', Admin: false, Exists: true, SizeMB: 1750.52, Blocked: false },
    { Key: 'INetCache', Desc: 'INetCache', Path: 'C:\\IN', Admin: false, Exists: true, SizeMB: 12.3, Blocked: false },
    { Key: 'CrashDumps', Desc: 'CrashDumps', Path: 'C:\\CD', Admin: false, Exists: false, SizeMB: 0, Blocked: false },
    { Key: 'ThumbCache', Desc: '縮圖快取', Path: 'C:\\TC', Admin: false, Exists: true, SizeMB: 45.25, Blocked: false },
    { Key: 'WinTemp', Desc: 'Windows Temp', Path: 'C:\\WT', Admin: true, Exists: true, SizeMB: 0, Blocked: true },
    { Key: 'WER', Desc: 'WER', Path: 'C:\\WER', Admin: true, Exists: true, SizeMB: 3.56, Blocked: true },
    { Key: 'WUCache', Desc: 'WU', Path: 'C:\\WU', Admin: true, Exists: true, SizeMB: 500, Blocked: true }
  ],
  Proc: { Mem: Array.from({ length: 10 }, (_, i) => ({ Id: 1000 + i, Name: 'proc' + i, WorkingSetMB: 100 - i, Responding: true })) }
};
const metricsPayload = { Mem: { TotalGB: 15.7, UsedGB: 8.5, FreeGB: 7.2, UsedPct: 54.1 }, Cpu: 22 };
const runPayload = {
  Execute: true, GenTime: '2026-06-08 10:01:00',
  Cleaned: [{ Key: 'UserTemp', DeletedFiles: 120, DeletedDirs: 4, Skipped: 30, Errors: 0, FreedMB: 1500.25, Notes: '' }],
  Optimized: [{ Opt: 'gc', Ok: true, Detail: 'GC' }, { Opt: 'trimall', Ok: true, Detail: 'Trimmed 240' }],
  TotalFreedMB: 1500.25, MemBefore: { UsedGB: 9.96, UsedPct: 63.44, FreeGB: 5.74, TotalGB: 15.7 },
  MemAfter: { UsedGB: 7.10, UsedPct: 45.2, FreeGB: 8.6, TotalGB: 15.7 }, MemReclaimedGB: 2.86
};
let lastRunBody = null;
let ran = false;
function fetch(url, opts) {
  let data;
  if (url === '/api/scan') data = ran ? Object.assign({}, scanPayload, { Mem: runPayload.MemAfter, Cpu: 22 }) : scanPayload;
  else if (url === '/api/metrics') data = metricsPayload;
  else if (url === '/api/run') { lastRunBody = JSON.parse(opts.body); ran = true; data = runPayload; }
  else if (url === '/api/psutil') data = { Ok: true, Detail: 'psutil 7.0.0 installed' };
  else data = {};
  return Promise.resolve({ json: () => Promise.resolve(data) });
}

// ---- fake-clock requestAnimationFrame (lets animNum converge in <=2 steps) -
let clock = 1000;
function requestAnimationFrame(cb) { clock += 1000; cb(clock); return 1; }

// timers: real setTimeout (deferred macrotask) so awaited delays resolve;
// setInterval no-op so the pollMetrics interval doesn't keep us alive.
const setTimeoutShim = (cb, ms) => setTimeout(cb, ms);
const setIntervalShim = () => 0;

let threw = null;
const ctx = {
  document, fetch, requestAnimationFrame,
  setTimeout: setTimeoutShim, setInterval: setIntervalShim,
  confirm: () => true, console, Math, JSON, Date, Promise,
  alert: () => {}
};
vm.createContext(ctx);
try { vm.runInContext(js, ctx, { filename: 'embedded_ui.js' }); }
catch (e) { threw = e; }

(async () => {
  ok('JS evaluates without throwing', !threw);
  if (threw) { console.log('   ', threw.message); }

  // loadScan() auto-ran at eval; await a tick for the promise chain
  await new Promise(r => setImmediate(r));
  await ctx.loadScan();

  ok('env panel rendered EnvManager badge', /EnvManager/.test(el('env').innerHTML));
  ok('env panel shows python version', /3\.11\.9/.test(el('env').innerHTML));
  ok('targets rendered all 8 keys', scanPayload.Targets.every(t => el('targets').innerHTML.includes('value="' + t.Key + '"')));
  ok('blocked admin target is disabled', /value="WinTemp"[^>]*disabled/.test(el('targets').innerHTML));
  ok('target size formatted (1,750.52 MB)', /1,750\.52 MB/.test(el('targets').innerHTML));
  ok('proc table has 10 rows', (el('proc-tbody').innerHTML.match(/<tr>/g) || []).length === 10);

  // metrics gauges
  ok('CPU value shows percent', /%$/.test(el('vCpu').textContent));
  ok('Mem value shows percent', /%$/.test(el('vMem').textContent));
  const off = parseFloat(el('gMem').style.strokeDashoffset);
  const circ = 2 * Math.PI * 40;
  ok('Mem gauge offset matches 63.44%', Math.abs(off - circ * (1 - 0.6344)) < 1.0);
  ok('high-mem gauge would turn warn/red color', (() => { ctx.setGauge('gMem', 90); return el('gMem').getAttribute('stroke') === '#C44E52'; })());

  // pollMetrics live update
  await ctx.pollMetrics();
  ok('pollMetrics updated CPU to 22%', el('vCpu').textContent === '22%');

  // picked(): two checked tgts, one unchecked, one disabled+checked
  tgtBoxes = [
    { checked: true, disabled: false, value: 'UserTemp' },
    { checked: true, disabled: false, value: 'LocalTemp' },
    { checked: false, disabled: false, value: 'INetCache' },
    { checked: true, disabled: true, value: 'WinTemp' }
  ];
  optBoxes = [{ checked: true, disabled: false, value: 'gc' }, { checked: true, disabled: false, value: 'trimall' }, { checked: false, disabled: false, value: 'highperf' }];
  const pk = ctx.picked('.tgt');
  ok('picked() excludes unchecked + disabled', JSON.stringify(pk) === JSON.stringify(['UserTemp', 'LocalTemp']));

  // setExec toggles label
  ctx.setExec(true);
  ok('setExec(true) sets delete label', /刪除/.test(el('btnRun').textContent));
  ok('setExec(true) marks mExec active', el('mExec').classList.contains('act') && !el('mScan').classList.contains('act'));

  // turbo(): posts correct body, renders result, reaches 100%
  await ctx.turbo();
  ok('turbo POST body carries execute=true', lastRunBody && lastRunBody.execute === true);
  ok('turbo POST body carries picked targets', JSON.stringify(lastRunBody.targets) === JSON.stringify(['UserTemp', 'LocalTemp']));
  ok('turbo POST body carries picked opts', JSON.stringify(lastRunBody.opts) === JSON.stringify(['gc', 'trimall']));
  ok('result shows EXECUTE header', /\[EXECUTE\]/.test(el('out').textContent));
  ok('result shows cleanup section', /\[清理\]/.test(el('out').textContent));
  ok('result shows accel section', /\[加速\]/.test(el('out').textContent));
  ok('result shows reclaimed GB', /回收 2\.86GB/.test(el('out').textContent));
  ok('progress reached 100%', el('progBar').style.width === '100%');
  ok('toast shown on success', el('toast').classList.contains('show'));
  ok('mem gauge updated to after-state (45.2%)', el('vMem').textContent === '45.2%');

  // installPsutil + restoreBalanced
  await ctx.installPsutil();
  ok('installPsutil renders detail', /psutil 7\.0\.0/.test(el('out').textContent));
  await ctx.restoreBalanced();

  console.log(`-- ${pass}/${pass + fail} PASS --`);
  process.exit(fail ? 1 : 0);
})();
