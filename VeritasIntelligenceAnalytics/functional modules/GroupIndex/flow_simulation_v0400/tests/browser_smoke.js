const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function main() {
  const root = path.resolve(__dirname, '..');
  const dashboard = path.join(root, 'data', 'output', 'VIA_TW_Group_Flow_Simulation_System_v0400.html');
  const executablePath = chromium.executablePath();
  if (!fs.existsSync(executablePath)) {
    console.log('BROWSER_SMOKE_SKIP_NO_CHROMIUM');
    return;
  }
  const browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  await page.goto('file://' + dashboard, { waitUntil: 'load' });
  if (!(await page.locator('#rotationPanel').isVisible())) throw new Error('rotation panel not visible by default');
  if (await page.locator('#rotationTable tbody tr').count() !== 18) throw new Error('rotation snapshot must render 18 rows');
  if (await page.locator('.rotation-state').count() !== 5) throw new Error('five-state cards are missing');
  await page.locator('#viewPipeline').click();
  await page.locator('#pipelineChain .stage-card').first().waitFor();
  if (await page.locator('#candidateTable tbody tr').count() !== 49) throw new Error('candidate group table must render 49 rows');
  await page.waitForTimeout(500);

  await page.locator('#viewClassification').click();
  if (!(await page.locator('#classificationPanel').isVisible())) throw new Error('classification panel not visible');
  if (await page.locator('.class-card').count() !== 31) throw new Error('classification group card count mismatch');
  if (await page.locator('.member-row').count() !== 149) throw new Error('classification member row count mismatch');
  if (await page.locator('.review-x').count() < 1) throw new Error('C review actions are missing');

  page.once('dialog', dialog => dialog.accept('browser smoke test proposal'));
  await page.locator('.review-x').first().click();
  const decisions = await page.evaluate(() => JSON.parse(localStorage.getItem('VIA_CLASSIFICATION_REVIEW_V0400') || '[]'));
  if (decisions.length !== 1 || decisions[0].Decision !== 'EXCLUDE_PROPOSED' || decisions[0].CanonicalMutation !== 0) {
    throw new Error('append-only human review decision failed');
  }

  await page.locator('#viewBacktest').click();
  if (!(await page.locator('#backtestPanel').isVisible())) throw new Error('backtest panel not visible');
  if (!(await page.locator('#backtestMetrics').innerText()).includes('t+1')) throw new Error('backtest alignment label missing');
  await page.locator('#viewParameters').click();
  if (!(await page.locator('#parametersPanel').isVisible())) throw new Error('parameters panel not visible');
  if (await page.locator('.parameter').count() < 8) throw new Error('dynamic parameter cards missing');
  await page.locator('#viewFlow').click();
  if (!(await page.locator('#flowPanel').isVisible())) throw new Error('flow panel not visible');
  await page.screenshot({ path: path.join(root, 'evidence', 'dashboard_desktop.png'), fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator('#viewClassification').click();
  await page.waitForTimeout(150);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  if (overflow > 2) throw new Error('mobile horizontal overflow=' + overflow);
  await page.screenshot({ path: path.join(root, 'evidence', 'dashboard_mobile.png'), fullPage: false });
  if (errors.length) throw new Error('browser errors: ' + errors.join(' | '));
  await browser.close();
  console.log('BROWSER_SMOKE_PASS');
  console.log('GROUP_CARDS=31');
  console.log('ROTATION_ROWS=18');
  console.log('ROTATION_STATES=5');
  console.log('MEMBER_ROWS=149');
  console.log('HUMAN_X_APPEND_ONLY_PASS');
  console.log('RESPONSIVE_390PX_PASS');
}

main().catch(error => {
  console.error(error.stack || String(error));
  process.exit(1);
});
