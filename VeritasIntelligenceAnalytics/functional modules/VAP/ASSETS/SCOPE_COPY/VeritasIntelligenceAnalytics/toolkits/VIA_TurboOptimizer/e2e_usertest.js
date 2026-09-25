'use strict';
// REAL end-to-end user-test:
//  1) reproduce the PS .Replace() to get the EXACT served HTML
//  2) stand up a real HTTP backend implementing the API contract
//  3) load the page in jsdom with a real fetch + simulate user clicks
const fs = require('fs');
const http = require('http');
const { JSDOM } = require('jsdom');

const PS = process.argv[2] || 'VIA_TurboOptimizer_v3.ps1';
const ps = fs.readFileSync(PS, 'utf8');

// ---- extract the HTML here-string and apply the SAME token substitution ----
const tm = ps.match(/\$htmlTpl = @'\n([\s\S]*?)\n'@/);
if (!tm) { console.error('html template not found'); process.exit(2); }
const PORT = 8899, AGE = 3, LOG = 'C:\\Users\\tonyk\\AppData\\Local\\OptimizeTool\\logs\\OptimizeLog.txt';
let html = tm[1]
  .split('__PORT__').join(String(PORT))
  .split('__AGE__').join(String(AGE))
  .split('__LOGPATH__').join(LOG);

// ---- real backend (mirrors the PS API contract) ----------------------------
const scan = (freed) => ({
  GenTime: '2026-06-08 10:00:00', IsAdmin: false, AgeDays: 3,
  Mem: freed ? { TotalGB: 15.7, UsedGB: 7.1, FreeGB: 8.6, UsedPct: 45.2 } : { TotalGB: 15.7, UsedGB: 9.96, FreeGB: 5.74, UsedPct: 63.44 },
  Cpu: freed ? 22 : 9,
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
});
const runResp = {
  Execute: true, GenTime: '2026-06-08 10:01:00',
  Cleaned: [{ Key: 'UserTemp', DeletedFiles: 120, DeletedDirs: 4, Skipped: 30, Errors: 0, FreedMB: 1500.25, Notes: '' },
            { Key: 'LocalTemp', DeletedFiles: 40, DeletedDirs: 1, Skipped: 5, Errors: 0, FreedMB: 88.0, Notes: '' }],
  Optimized: [{ Opt: 'gc', Ok: true, Detail: 'GC' }, { Opt: 'trimall', Ok: true, Detail: 'Trimmed 240 process(es)' }, { Opt: 'flushdns', Ok: true, Detail: 'DNS flushed' }],
  TotalFreedMB: 1588.25, MemBefore: { UsedGB: 9.96, UsedPct: 63.44, FreeGB: 5.74, TotalGB: 15.7 },
  MemAfter: { UsedGB: 7.10, UsedPct: 45.2, FreeGB: 8.6, TotalGB: 15.7 }, MemReclaimedGB: 2.86
};
const state = { ran: false, failRun: false, lastRun: null };
function send(res, code, obj, type) {
  const body = type === 'html' ? obj : JSON.stringify(obj);
  res.writeHead(code, { 'Content-Type': type === 'html' ? 'text/html; charset=utf-8' : 'application/json; charset=utf-8' });
  res.end(body);
}
const server = http.createServer((req, res) => {
  const u = req.url;
  if (u === '/') return send(res, 200, html, 'html');
  if (u === '/api/scan') return send(res, 200, scan(state.ran));
  if (u === '/api/metrics') return send(res, 200, { Mem: scan(state.ran).Mem, Cpu: scan(state.ran).Cpu });
  if (u === '/api/psutil') return send(res, 200, { Ok: true, Detail: 'psutil 7.0.0 installed' });
  if (u === '/api/run') {
    let body = ''; req.on('data', c => body += c); req.on('end', () => {
      state.lastRun = JSON.parse(body || '{}');
      if (state.failRun) return send(res, 500, { error: 'boom' });
      state.ran = true; return send(res, 200, runResp);
    });
    return;
  }
  return send(res, 404, { error: 'not found' });
});

// ---- assertions -------------------------------------------------------------
let pass = 0, fail = 0;
const ok = (n, c) => { c ? (pass++, console.log('  [PASS]', n)) : (fail++, console.log('  [FAIL]', n)); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function until(fn, ms = 4000) { const t = Date.now(); while (Date.now() - t < ms) { try { if (fn()) return true; } catch (e) {} await sleep(40); } return false; }

server.listen(PORT, async () => {
  const origin = 'http://127.0.0.1:' + PORT;
  const realFetch = globalThis.fetch;
  const dom = new JSDOM(html, {
    runScripts: 'dangerously', pretendToBeVisual: true, url: origin + '/',
    beforeParse(window) {
      window.confirm = () => window.__confirmVal !== false;
      window.fetch = (url, opts) => realFetch(url.startsWith('http') ? url : origin + url, opts);
    }
  });
  const w = dom.window, d = w.document;
  const $ = s => d.querySelector(s);

  try {
    // ---- initial load (user opens the page) --------------------------------
    ok('page parsed, title present', /VIA Turbo Optimizer/.test(d.title) || /VIA Turbo Optimizer/.test(d.body.textContent));
    const loaded = await until(() => $('#targets').querySelectorAll('input.tgt').length === 8);
    ok('scan auto-loaded 8 target rows', loaded);
    ok('admin target rendered as disabled checkbox', !!$('#targets').querySelector('input.tgt[value="WinTemp"][disabled]'));
    ok('env badge shows python 3.11.9', /3\.11\.9/.test($('#env').innerHTML));
    ok('proc table filled (10 rows)', $('#proc tbody').querySelectorAll('tr').length === 10);

    // gauges animate to initial state
    await until(() => $('#vMem').textContent === '63.44%');
    ok('memory gauge text reached 63.44%', $('#vMem').textContent === '63.44%');
    ok('cpu gauge text reached 9%', await until(() => $('#vCpu').textContent === '9%'));
    const offset = parseFloat($('#gMem').style.strokeDashoffset);
    ok('memory ring offset reflects 63.44%', Math.abs(offset - (2 * Math.PI * 40) * (1 - 0.6344)) < 1.5);

    // ---- user toggles to "實際刪除" then clicks Turbo ----------------------
    w.__confirmVal = true;
    $('#mExec').click();                       // real click → setExec(true)
    ok('toggle: run button now says 刪除', /刪除/.test($('#btnRun').textContent));
    ok('toggle: mExec marked active', $('#mExec').classList.contains('act') && !$('#mScan').classList.contains('act'));

    $('#btnRun').click();                       // real click → turbo()
    const done = await until(() => /\[EXECUTE\]/.test($('#out').textContent));
    ok('turbo ran, result shows EXECUTE', done);
    ok('backend received execute=true', state.lastRun && state.lastRun.execute === true);
    ok('backend received auto-checked targets', Array.isArray(state.lastRun.targets) && state.lastRun.targets.includes('UserTemp'));
    ok('result lists both cleaned targets', /UserTemp/.test($('#out').textContent) && /LocalTemp/.test($('#out').textContent));
    ok('result shows reclaimed 2.86GB', /回收 2\.86GB/.test($('#out').textContent));
    ok('result shows total freed 1588.25 MB', /1588\.25 MB/.test($('#out').textContent));
    ok('progress bar reached 100%', await until(() => $('#progBar').style.width === '100%'));
    ok('success toast shown', await until(() => $('#toast').classList.contains('show')));
    ok('toast text mentions freed MB', /1588\.25MB/.test($('#toast').textContent));
    ok('targets refreshed after run (memory now 45.2%)', await until(() => $('#vMem').textContent === '45.2%', 3000));

    // ---- error path: backend 500 on next run -------------------------------
    state.failRun = true;
    $('#out').textContent = '';                 // clear to detect fresh write
    $('#btnRun').click();
    const errShown = await until(() => /執行失敗/.test($('#out').textContent));
    ok('500 from backend surfaces "執行失敗" gracefully', errShown);
    ok('no uncaught crash (window still responsive)', typeof w.turbo === 'function');

    // ---- 404 path ----------------------------------------------------------
    const r404 = await realFetch(origin + '/nope'); 
    ok('unknown route returns 404', r404.status === 404);

  } catch (e) {
    fail++; console.log('  [FAIL] uncaught exception:', e.message);
  } finally {
    try { dom.window.close(); } catch (e) {}
    server.close();
    console.log(`-- ${pass}/${pass + fail} PASS --`);
    process.exit(fail ? 1 : 0);
  }
});
