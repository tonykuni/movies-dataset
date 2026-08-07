'use strict';
// REAL end-to-end user-test for the ALL-IN-ONE PowerShell system:
//  1) spawn the actual pwsh HttpListener backend (-NoBrowser)
//  2) verify the served HTML got the EXACT .Replace() token substitution
//  3) exercise the full API contract over real HTTP
//  4) drive a real sandbox tree through dry-run (x3 engines) and live-delete
// Zero npm dependencies: node:http fetch + node:fs only (Node v18+).
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const APP_DIR = path.resolve(__dirname, '..');
const PS1 = path.join(APP_DIR, 'VeritasStorageOptimizer_AllInOne.ps1');
const PWSH = process.env.PWSH || 'pwsh';
const PORT = 8872;
const ORIGIN = 'http://127.0.0.1:' + PORT;

let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  [PASS]', n)) : (fail++, console.log('  [FAIL]', n)); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function until(fn, ms = 20000) {
  const t = Date.now();
  while (Date.now() - t < ms) {
    try { if (await fn()) return true; } catch (e) {}
    await sleep(200);
  }
  return false;
}

async function api(route, body) {
  const opts = body
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
    : {};
  const r = await fetch(ORIGIN + route, opts);
  return { status: r.status, json: await r.json().catch(() => null) };
}

function buildSandbox(root) {
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
  return sand;
}

(async () => {
  const server = spawn(PWSH, ['-NoProfile', '-File', PS1, '-Port', String(PORT), '-NoBrowser'], { cwd: APP_DIR });
  let serverLog = '';
  server.stdout.on('data', d => serverLog += d);
  server.stderr.on('data', d => serverLog += d);
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'veritas_ps_e2e_'));

  try {
    // ---- server boots and serves the exact substituted front-end ------------
    const up = await until(async () => (await fetch(ORIGIN + '/')).status === 200);
    ok('pwsh backend boots and serves /', up);
    if (!up) throw new Error('server did not start:\n' + serverLog);

    const html = await (await fetch(ORIGIN + '/')).text();
    ok('page title present', /Veritas Storage Optimizer/.test(html));
    ok('__PORT__ token substituted', !html.includes('__PORT__') && html.includes(String(PORT)));
    ok('__MAXMB__ token substituted', !html.includes('__MAXMB__'));
    ok('__LOGPATH__ token substituted', !html.includes('__LOGPATH__'));
    ok('three-engine switch rendered', /engPs/.test(html) && /engPy/.test(html) && /engJs/.test(html));
    ok('dry-run is the default mode', /僅掃描 Dry-Run/.test(html));
    ok('front-end confirms before live delete', /confirm\(/.test(html) && /無法復原/.test(html));

    // ---- env contract --------------------------------------------------------
    const env = await api('/api/env');
    ok('/api/env returns PS version', env.status === 200 && /^7\./.test(env.json.PSVer));
    ok('/api/env detects python + node', !!env.json.Python && !!env.json.Node);
    ok('/api/env locates sub-engine scripts', env.json.PyEngine === true && env.json.JsEngine === true);

    // ---- dry-run across ALL THREE engines ------------------------------------
    for (const engine of ['ps', 'python', 'node']) {
      const sand = buildSandbox(fs.mkdtempSync(path.join(root, engine + '_')));
      const d = await api('/api/run', { dir: sand, maxMB: 2, engine, execute: false });
      ok(`[${engine}] dry-run ok`, d.status === 200 && d.json.ok === true && d.json.execute === false);
      const items = Array.isArray(d.json.items) ? d.json.items : [];
      const reasons = items.map(i => i.reason).join('|');
      ok(`[${engine}] marks temp file`, /Temp File/.test(reasons));
      ok(`[${engine}] marks oversize file`, /Over/.test(reasons));
      ok(`[${engine}] marks duplicate`, /Duplicate of/.test(reasons));
      ok(`[${engine}] tiny 1-byte twins not marked`, !items.some(i => /stub_[ab]\.txt/.test(i.path)));
      ok(`[${engine}] skips protected .git`, !items.some(i => i.path.includes('.git')));
      ok(`[${engine}] skips python venv (pyvenv.cfg)`, !items.some(i => i.path.includes('fake_env')));
      ok(`[${engine}] skips .veritas_protect zone`, !items.some(i => i.path.includes('keepzone')));
      ok(`[${engine}] reports freed size`, /MB/.test(d.json.freedHuman));
      ok(`[${engine}] audit log written`, d.json.logPath && fs.existsSync(d.json.logPath));
      ok(`[${engine}] dry-run deletes nothing`,
        fs.existsSync(path.join(sand, 'junk.tmp')) && fs.existsSync(path.join(sand, 'bigfile.bin')));
    }

    // ---- system protection guard ---------------------------------------------
    const guardRoot = await api('/api/run', { dir: '/', maxMB: 200, engine: 'ps', execute: true });
    ok('guard refuses filesystem root', guardRoot.json.ok === false && /拒絕/.test(guardRoot.json.error));
    const guardHome = await api('/api/run', { dir: os.homedir(), maxMB: 200, engine: 'ps', execute: true });
    ok('guard refuses home directory', guardHome.json.ok === false);
    const guardMissing = await api('/api/run', { dir: path.join(root, 'no_such_dir'), maxMB: 200, engine: 'ps', execute: false });
    ok('guard refuses missing directory', guardMissing.json.ok === false);

    // ---- live delete with the native PS engine ---------------------------------
    const sandLive = buildSandbox(fs.mkdtempSync(path.join(root, 'live_')));
    const live = await api('/api/run', { dir: sandLive, maxMB: 2, engine: 'ps', execute: true });
    ok('live run ok', live.status === 200 && live.json.ok === true && live.json.execute === true);
    ok('live run removed temp file', !fs.existsSync(path.join(sandLive, 'junk.tmp')));
    ok('live run removed oversize file', !fs.existsSync(path.join(sandLive, 'bigfile.bin')));
    const dupSurvivors = ['orig.dat', path.join('sub', 'copy.dat')].filter(f => fs.existsSync(path.join(sandLive, f)));
    ok('live run kept exactly one duplicate copy', dupSurvivors.length === 1);
    ok('live run kept normal file', fs.existsSync(path.join(sandLive, 'keep.txt')));
    ok('live run kept tiny twin stubs', fs.existsSync(path.join(sandLive, 'stub_a.txt')) && fs.existsSync(path.join(sandLive, 'stub_b.txt')));
    ok('live run kept protected .git content', fs.existsSync(path.join(sandLive, '.git', 'protected.tmp')));
    ok('live run kept venv content', fs.existsSync(path.join(sandLive, 'fake_env', 'venvjunk.tmp')));
    ok('live run kept .veritas_protect zone', fs.existsSync(path.join(sandLive, 'keepzone', 'zonejunk.tmp')));
    const guardMarker = await api('/api/run', { dir: path.join(sandLive, 'keepzone'), maxMB: 200, engine: 'ps', execute: true });
    ok('guard refuses protect-marked target', guardMarker.json.ok === false && /veritas_protect/.test(guardMarker.json.error));
    ok('live run removed empty dir', !fs.existsSync(path.join(sandLive, 'sub', 'empty_dir')));

    // ---- hardening: invalid threshold rejected server-side ----------------------
    const sandZero = buildSandbox(fs.mkdtempSync(path.join(root, 'zero_')));
    const zero = await api('/api/run', { dir: sandZero, maxMB: 0, engine: 'ps', execute: true });
    ok('maxMB=0 rejected server-side', zero.json.ok === false);
    ok('maxMB=0 deleted nothing', fs.existsSync(path.join(sandZero, 'keep.txt')) && fs.existsSync(path.join(sandZero, 'junk.tmp')));

    // ---- hardening: unicode + spaces in file names --------------------------------
    const uniRoot = fs.mkdtempSync(path.join(root, 'uni_'));
    const uniSand = path.join(uniRoot, 'sand');
    fs.mkdirSync(uniSand, { recursive: true });
    fs.writeFileSync(path.join(uniSand, '暫存 檔案.tmp'), '中文暫存');
    fs.writeFileSync(path.join(uniSand, "quote'name.txt"), 'keep');
    const uni = await api('/api/run', { dir: uniSand, maxMB: 200, engine: 'ps', execute: false });
    ok('unicode temp file marked', uni.json.ok === true && uni.json.items.some(i => i.path.includes('暫存 檔案.tmp')));
    ok('unicode run leaves files intact', fs.existsSync(path.join(uniSand, '暫存 檔案.tmp')));

    // ---- hardening: single-item result keeps JSON array shape ---------------------
    ok('single-item items is a JSON array', Array.isArray(uni.json.items) && uni.json.items.length === 1);
    ok('empty emptyDirs is a JSON array', Array.isArray(uni.json.emptyDirs) && uni.json.emptyDirs.length === 0);

    // ---- hardening: symlink cycle + escape containment -----------------------------
    let symlinksOk = true;
    const symRoot = fs.mkdtempSync(path.join(root, 'sym_'));
    const symTarget = path.join(symRoot, 'target');
    const outside = path.join(symRoot, 'outside');
    fs.mkdirSync(path.join(symTarget, 'sub'), { recursive: true });
    fs.mkdirSync(outside, { recursive: true });
    fs.writeFileSync(path.join(outside, 'victim.tmp'), 'outside data');
    fs.writeFileSync(path.join(symTarget, 'inside.tmp'), 'inside data');
    try {
      fs.symlinkSync(outside, path.join(symTarget, 'link_out'), 'dir');
      fs.symlinkSync(symTarget, path.join(symTarget, 'sub', 'loop'), 'dir');
    } catch (e) { symlinksOk = false; }
    if (symlinksOk) {
      const sym = await api('/api/run', { dir: symTarget, maxMB: 200, engine: 'ps', execute: false });
      ok('symlink tree scan completes (no cycle hang)', sym.json && sym.json.ok === true);
      ok('symlink scan never escapes target', !sym.json.items.some(i => i.path.includes('outside') || i.path.includes('link_out') || i.path.includes('loop')));
      const symLive = await api('/api/run', { dir: symTarget, maxMB: 200, engine: 'ps', execute: true });
      ok('symlink live run ok', symLive.json.ok === true);
      ok('outside file untouched after live run', fs.existsSync(path.join(outside, 'victim.tmp')));
      ok('inside temp file removed', !fs.existsSync(path.join(symTarget, 'inside.tmp')));
    } else {
      console.log('  [SKIP] symlink tests (no symlink privilege on this OS)');
    }

    // ---- hardening: scale correctness (many files, exact duplicate count) ----------
    const bigRoot = fs.mkdtempSync(path.join(root, 'big_'));
    const bigSand = path.join(bigRoot, 'sand');
    fs.mkdirSync(bigSand, { recursive: true });
    for (let i = 0; i < 100; i++) {
      const payload = Buffer.alloc(2048 + i, i % 251);   // unique size per pair
      fs.writeFileSync(path.join(bigSand, `file_${i}_a.dat`), payload);
      fs.writeFileSync(path.join(bigSand, `file_${i}_b.dat`), payload);
      fs.writeFileSync(path.join(bigSand, `noise_${i}.txt`), Buffer.alloc(2048 + i, (i + 1) % 251));
    }
    const big = await api('/api/run', { dir: bigSand, maxMB: 200, engine: 'ps', execute: false });
    const dupCount = big.json.items.filter(i => /Duplicate of/.test(i.reason)).length;
    ok('scale: exactly 100 duplicates detected in 300 files', big.json.ok === true && dupCount === 100 && big.json.totalFiles === 100);

    // ---- 404 + graceful shutdown ------------------------------------------------
    const r404 = await fetch(ORIGIN + '/nope');
    ok('unknown route returns 404', r404.status === 404);
    const down = await api('/api/shutdown');
    ok('shutdown endpoint acknowledges', down.status === 200 && down.json.ok === true);

  } catch (e) {
    fail++; console.log('  [FAIL] uncaught exception:', e.message);
  } finally {
    server.kill();
    fs.rmSync(root, { recursive: true, force: true });
    console.log(`-- ${pass}/${pass + fail} PASS --`);
    process.exit(fail ? 1 : 0);
  }
})();
