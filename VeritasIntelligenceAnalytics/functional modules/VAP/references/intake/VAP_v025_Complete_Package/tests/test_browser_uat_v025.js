'use strict';
const assert = require('assert');
const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('playwright');

// def 01 PARAMETERS
const PACKAGE_ROOT = path.resolve(__dirname, '..');
const HOST = '127.0.0.1';
const PORT = Number(process.env.VAP_UAT_PORT || 18765);
const BROWSER_EXECUTABLE = process.env.VAP_BROWSER_EXECUTABLE || '';

// def 02 STATIC SERVER
function def_content_type(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  return ({ '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8', '.css': 'text/css; charset=utf-8' })[extension] || 'application/octet-stream';
}
function def_start_server() {
  const server = http.createServer((request, response) => {
    const urlPath = decodeURIComponent(String(request.url || '/').split('?')[0]);
    const relative = urlPath === '/' ? 'ui/VAP_Workbench_v025.html' : urlPath.replace(/^\/+/, '');
    const filePath = path.resolve(PACKAGE_ROOT, relative);
    if (!filePath.startsWith(PACKAGE_ROOT + path.sep) || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
      response.writeHead(404); response.end('Not Found'); return;
    }
    response.writeHead(200, { 'Content-Type': def_content_type(filePath), 'Cache-Control': 'no-store' });
    fs.createReadStream(filePath).pipe(response);
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(PORT, HOST, () => resolve(server));
  });
}

// def 03 USER JOURNEY
async function def_run_browser_uat() {
  if (!BROWSER_EXECUTABLE || !fs.existsSync(BROWSER_EXECUTABLE)) throw new Error('VAP_BROWSER_EXECUTABLE_REQUIRED');
  const server = await def_start_server();
  let browser;
  try {
    browser = await chromium.launch({ headless: true, executablePath: BROWSER_EXECUTABLE });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
    const errors = [];
    page.on('pageerror', error => errors.push(String(error && error.stack || error)));
    await page.goto(`http://${HOST}:${PORT}/ui/VAP_Workbench_v025.html`, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForFunction(() => Boolean(window.VeritasAutoPlot && document.querySelector('#pairChart svg')), null, { timeout: 60000 });

    const observation = await page.evaluate(() => {
      document.getElementById('pairObservationMode').value = 'rebase_100';
      document.getElementById('pairObservationFrequency').value = 'monthly';
      applyObservationWindow('ALL');
      const allPoints = Number(document.querySelector('#pairChart svg').closest('#pairChart') && document.getElementById('pairVisiblePoints').textContent.match(/(\d+) Pts/i)?.[1] || 0);
      applyObservationWindow('1Y');
      const svg = document.querySelector('#pairChart svg');
      const oneYearPoints = Number(document.getElementById('pairVisiblePoints').textContent.match(/(\d+) Pts/i)?.[1] || 0);
      togglePairParameters(true);
      const collapsed = document.querySelector('#page-pair>.panel:first-child').classList.contains('pairParametersCollapsed');
      togglePairParameters(false);
      return {
        allPoints, oneYearPoints, collapsed,
        mode: svg.dataset.observationMode,
        frequency: svg.dataset.observationFrequency,
        range: svg.dataset.observationRange,
        latest: document.getElementById('pairLatestLeft').textContent,
        evidence: document.getElementById('pairEvidenceBadge').textContent
      };
    });
    assert.equal(observation.mode, 'rebase_100');
    assert.equal(observation.frequency, 'monthly');
    assert.equal(observation.range, '1Y');
    assert.ok(observation.oneYearPoints >= 3 && observation.oneYearPoints < observation.allPoints);
    assert.ok(observation.collapsed && observation.latest !== '—' && observation.evidence.includes('As Of'));

    const gate = await page.evaluate(async () => {
      document.getElementById('pairObservationMode').value = 'level';
      document.getElementById('pairObservationFrequency').value = 'native';
      applyObservationWindow('ALL');
      const completed = await runTestDebugActivate();
      return { completed, summary: window.VeritasAutoPlot.diagnosticSummary(), runtimeErrors: [...VAP_RUNTIME_ERRORS] };
    });
    assert.equal(gate.completed, true);
    assert.equal(gate.summary.fullCounts.FAIL, 0);
    assert.equal(gate.summary.userCounts.FAIL, 0);
    assert.ok(gate.summary.fullCounts.PASS >= 136);
    assert.ok(gate.summary.userCounts.PASS >= 72);
    assert.equal(gate.runtimeErrors.length, 0);
    assert.deepEqual(errors, []);
    return { schema: 'VIA-VAP-BROWSER-UAT/1.0', version: 'v025', status: 'PASS', observation, gate: gate.summary };
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}

// def 04 ENTRYPOINT
def_run_browser_uat().then(result => {
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
}).catch(error => {
  process.stderr.write(String(error && error.stack || error) + '\n');
  process.exitCode = 1;
});
