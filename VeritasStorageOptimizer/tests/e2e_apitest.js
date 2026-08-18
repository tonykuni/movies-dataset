'use strict';
// REAL end-to-end test for the Veritas GUI backend:
//  1) spawn the actual Python GUI server (--no-browser)
//  2) exercise the served HTML + full API contract over real HTTP
//  3) drive a real sandbox tree through dry-run and live-delete
// Zero npm dependencies: node:http + node:fs only (Node v18+).
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const APP_DIR = path.resolve(__dirname, '..');
const GUI = path.join(APP_DIR, 'veritas_gui.py');

// Windows ships the interpreter as `python` / `py`, Unix as `python3`;
// probe with --version so Store alias stubs (which fail it) are skipped.
function findPython() {
  if (process.env.PYTHON) return process.env.PYTHON;
  const candidates = os.platform() === 'win32'
    ? ['python', 'py', 'python3']
    : ['python3', 'python'];
  for (const c of candidates) {
    try {
      if (spawnSync(c, ['--version'], { stdio: 'ignore' }).status === 0) return c;
    } catch (e) {}
  }
  return null;
}
const PY = findPython();
if (!PY) {
  console.log('  [FAIL] no working Python interpreter found (tried python/py/python3; set PYTHON env var)');
  console.log('-- 0/1 PASS --');
  process.exit(1);
}
const PORT = 8871;
const ORIGIN = 'http://127.0.0.1:' + PORT;

let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  [PASS]', n)) : (fail++, console.log('  [FAIL]', n)); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function until(fn, ms = 8000) {
  const t = Date.now();
  while (Date.now() - t < ms) {
    try { if (await fn()) return true; } catch (e) {}
    await sleep(120);
  }
  return false;
}

async function api(route, body) {
  const opts = body
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
    : {};
  const r = await fetch(ORIGIN + route, opts);
  return { status: r.status, json: await r.json().catch(() => null), };
}

function buildSandbox() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'veritas_e2e_'));
  const sand = path.join(root, 'sand');
  fs.mkdirSync(path.join(sand, 'sub', 'empty_dir'), { recursive: true });
  fs.mkdirSync(path.join(sand, '.git'), { recursive: true });
  fs.writeFileSync(path.join(sand, 'junk.tmp'), 'temp data');
  fs.writeFileSync(path.join(sand, 'bigfile.bin'), Buffer.alloc(3 * 1024 * 1024, 7));
  fs.writeFileSync(path.join(sand, 'orig.dat'), Buffer.alloc(51200, 1));
  fs.writeFileSync(path.join(sand, 'sub', 'copy.dat'), Buffer.alloc(51200, 1));
  fs.writeFileSync(path.join(sand, 'keep.txt'), 'keep me');
  fs.writeFileSync(path.join(sand, 'stub_a.txt'), '\n');
  fs.writeFileSync(path.join(sand, 'stub_b.txt'), '\n');
  fs.writeFileSync(path.join(sand, '.git', 'protected.tmp'), 'protected');
  fs.mkdirSync(path.join(sand, 'fake_env'), { recursive: true });
  fs.writeFileSync(path.join(sand, 'fake_env', 'pyvenv.cfg'), 'home = /usr');
  fs.writeFileSync(path.join(sand, 'fake_env', 'venvjunk.tmp'), 'venv temp');
  fs.mkdirSync(path.join(sand, 'keepzone'), { recursive: true });
  fs.writeFileSync(path.join(sand, 'keepzone', '.veritas_protect'), '');
  fs.writeFileSync(path.join(sand, 'keepzone', 'zonejunk.tmp'), 'zone temp');
  fs.mkdirSync(path.join(sand, '__pycache__'), { recursive: true });
  fs.writeFileSync(path.join(sand, '__pycache__', 'mod.cpython-311.pyc'), 'bytecode');
  fs.writeFileSync(path.join(sand, 'legacy.pyc'), 'old bytecode');
  const pair = Buffer.alloc(2048, 9);
  fs.writeFileSync(path.join(sand, 'pair_a.dat'), pair);
  fs.writeFileSync(path.join(sand, 'pair_b.txt'), pair);
  return { root, sand };
}

(async () => {
  const server = spawn(PY, [GUI, '--port', String(PORT), '--no-browser'], { cwd: APP_DIR });
  let serverLog = '';
  server.on('error', e => { serverLog += 'spawn failed: ' + e.message + '\n'; });
  server.stdout.on('data', d => serverLog += d);
  server.stderr.on('data', d => serverLog += d);
  const { root, sand } = buildSandbox();

  try {
    // ---- server boots and serves the front-end -----------------------------
    const up = await until(async () => (await fetch(ORIGIN + '/')).status === 200);
    ok('server boots and serves /', up);
    if (!up) throw new Error('server did not start:\n' + serverLog);

    const html = await (await fetch(ORIGIN + '/')).text();
    ok('page title present', /Veritas Storage Optimizer/.test(html));
    ok('__PORT__ token substituted', !html.includes('__PORT__') && html.includes(String(PORT)));
    ok('__LOGPATH__ token substituted', !html.includes('__LOGPATH__'));
    ok('dry-run is the default mode', /僅掃描 Dry-Run/.test(html));
    ok('front-end confirms before live delete', /confirm\(/.test(html) && /無法復原/.test(html));

    // ---- env contract -------------------------------------------------------
    const env = await api('/api/env');
    ok('/api/env returns python version', env.status === 200 && /^\d+\.\d+\.\d+$/.test(env.json.PythonVer));
    ok('/api/env locates both engines', env.json.PyEngine === true && env.json.JsEngine === true);

    // ---- dry-run over both engines ------------------------------------------
    for (const engine of ['python', 'node']) {
      if (engine === 'node' && !env.json.Node) { console.log('  [SKIP] node engine (no node)'); continue; }
      const d = await api('/api/run', { dir: sand, maxMB: 2, engine, execute: false });
      ok(`[${engine}] dry-run ok`, d.status === 200 && d.json.ok === true && d.json.execute === false);
      const reasons = (d.json.items || []).map(i => i.reason).join('|');
      ok(`[${engine}] marks temp file`, /Temp File/.test(reasons));
      ok(`[${engine}] marks oversize file`, /Over/.test(reasons));
      ok(`[${engine}] marks duplicate`, /Duplicate of/.test(reasons));
      ok(`[${engine}] tiny 1-byte twins not marked`, !(d.json.items || []).some(i => /stub_[ab]\.txt/.test(i.path)));
      ok(`[${engine}] skips protected .git`, !(d.json.items || []).some(i => i.path.includes('.git')));
      ok(`[${engine}] skips python venv (pyvenv.cfg)`, !(d.json.items || []).some(i => i.path.includes('fake_env')));
      ok(`[${engine}] skips .veritas_protect zone`, !(d.json.items || []).some(i => i.path.includes('keepzone')));
      ok(`[${engine}] marks coding junk`, (d.json.items || []).some(i => i.reason === 'Coding Junk' && i.path.includes('__pycache__')) && (d.json.items || []).some(i => i.reason === 'Coding Junk' && i.path.includes('legacy.pyc')));
      ok(`[${engine}] cross-ext same-size twins not marked`, !(d.json.items || []).some(i => /pair_[ab]\./.test(i.path)));
      ok(`[${engine}] reports freed size`, /MB/.test(d.json.freedHuman));
      ok(`[${engine}] audit log written`, d.json.logPath && fs.existsSync(d.json.logPath));
      ok(`[${engine}] dry-run deletes nothing`, fs.existsSync(path.join(sand, 'junk.tmp')) && fs.existsSync(path.join(sand, 'bigfile.bin')));
    }

    // ---- system protection guard --------------------------------------------
    const guardRoot = await api('/api/run', { dir: '/', maxMB: 200, engine: 'python', execute: true });
    ok('guard refuses filesystem root', guardRoot.json.ok === false && /拒絕/.test(guardRoot.json.error));
    const guardHome = await api('/api/run', { dir: os.homedir(), maxMB: 200, engine: 'python', execute: true });
    ok('guard refuses home directory', guardHome.json.ok === false);
    const guardMissing = await api('/api/run', { dir: path.join(root, 'no_such_dir'), maxMB: 200, engine: 'python', execute: false });
    ok('guard refuses missing directory', guardMissing.json.ok === false);

    // ---- live delete ---------------------------------------------------------
    const live = await api('/api/run', { dir: sand, maxMB: 2, engine: 'python', execute: true });
    ok('live run ok', live.status === 200 && live.json.ok === true && live.json.execute === true);
    ok('live run removed temp file', !fs.existsSync(path.join(sand, 'junk.tmp')));
    ok('live run removed oversize file', !fs.existsSync(path.join(sand, 'bigfile.bin')));
    const dupSurvivors = ['orig.dat', path.join('sub', 'copy.dat')].filter(f => fs.existsSync(path.join(sand, f)));
    ok('live run kept exactly one duplicate copy', dupSurvivors.length === 1);
    ok('live run kept normal file', fs.existsSync(path.join(sand, 'keep.txt')));
    ok('live run kept tiny twin stubs', fs.existsSync(path.join(sand, 'stub_a.txt')) && fs.existsSync(path.join(sand, 'stub_b.txt')));
    ok('live run kept protected .git content', fs.existsSync(path.join(sand, '.git', 'protected.tmp')));
    ok('live run kept venv content', fs.existsSync(path.join(sand, 'fake_env', 'venvjunk.tmp')));
    ok('live run kept .veritas_protect zone', fs.existsSync(path.join(sand, 'keepzone', 'zonejunk.tmp')));
    ok('live run removed coding junk', !fs.existsSync(path.join(sand, 'legacy.pyc')) && !fs.existsSync(path.join(sand, '__pycache__', 'mod.cpython-311.pyc')));
    ok('live run kept cross-ext twins', fs.existsSync(path.join(sand, 'pair_a.dat')) && fs.existsSync(path.join(sand, 'pair_b.txt')));
    ok('live run removed empty dir', !fs.existsSync(path.join(sand, 'sub', 'empty_dir')));

    // ---- hardening: invalid threshold rejected server-side ---------------------
    const zeroDir = fs.mkdtempSync(path.join(root, 'zero_'));
    fs.writeFileSync(path.join(zeroDir, 'keep.txt'), 'x');
    const zero = await api('/api/run', { dir: zeroDir, maxMB: 0, engine: 'python', execute: true });
    ok('maxMB=0 rejected server-side', zero.json.ok === false);
    ok('maxMB=0 deleted nothing', fs.existsSync(path.join(zeroDir, 'keep.txt')));

    // ---- hardening: unicode + spaces in file names -------------------------------
    const uniDir = fs.mkdtempSync(path.join(root, 'uni_'));
    fs.writeFileSync(path.join(uniDir, '暫存 檔案.tmp'), '中文暫存');
    const uni = await api('/api/run', { dir: uniDir, maxMB: 200, engine: 'python', execute: false });
    ok('unicode temp file marked', uni.json.ok === true && uni.json.items.some(i => i.path.includes('暫存 檔案.tmp')));

    // ---- hardening: symlinked dirs are never followed ------------------------------
    let symlinksOk = true;
    const symRoot = fs.mkdtempSync(path.join(root, 'sym_'));
    const symTarget = path.join(symRoot, 'target');
    const outside = path.join(symRoot, 'outside');
    fs.mkdirSync(path.join(symTarget, 'sub'), { recursive: true });
    fs.mkdirSync(outside, { recursive: true });
    fs.writeFileSync(path.join(outside, 'victim.tmp'), 'outside data');
    try {
      fs.symlinkSync(outside, path.join(symTarget, 'link_out'), 'dir');
      fs.symlinkSync(symTarget, path.join(symTarget, 'sub', 'loop'), 'dir');
    } catch (e) { symlinksOk = false; }
    if (symlinksOk) {
      for (const engine of ['python', 'node']) {
        if (engine === 'node' && !env.json.Node) continue;
        const sym = await api('/api/run', { dir: symTarget, maxMB: 200, engine, execute: true });
        ok(`[${engine}] symlink scan completes without escaping`,
          sym.json.ok === true && !sym.json.items.some(i => i.path.includes('outside') || i.path.includes('link_out')));
        ok(`[${engine}] outside file untouched after live run`, fs.existsSync(path.join(outside, 'victim.tmp')));
      }
    } else {
      console.log('  [SKIP] symlink tests (no symlink privilege on this OS)');
    }

    // ---- 404 path -------------------------------------------------------------
    const r404 = await fetch(ORIGIN + '/nope');
    ok('unknown route returns 404', r404.status === 404);

  } catch (e) {
    fail++; console.log('  [FAIL] uncaught exception:', e.message);
  } finally {
    server.kill();
    fs.rmSync(root, { recursive: true, force: true });
    console.log(`-- ${pass}/${pass + fail} PASS --`);
    process.exit(fail ? 1 : 0);
  }
})();
