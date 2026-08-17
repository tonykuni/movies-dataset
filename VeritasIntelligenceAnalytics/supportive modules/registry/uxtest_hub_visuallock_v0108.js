const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const R = []; const c = (n, ok, note) => R.push([ok ? 'PASS' : 'FAIL', n, note || '']);
  await page.goto('file:///home/user/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/VIA_Master_Hub.html');
  c('理印徽', (await page.locator('.seal').textContent().catch(() => '')).trim() === '理');
  const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  c('紙底鎖定', bg === 'rgb(242, 241, 236)', bg);
  const pb = await page.locator('.panel').boundingBox();
  const sb = await page.locator('.stage').boundingBox();
  c('左 panel 右 stage', pb && sb && pb.x < 10 && sb.x >= pb.x + pb.width - 2, pb && `pw=${pb.width}`);
  c('五系統板在 stage', (await page.locator('.stage .card').count()) >= 5);
  // 動詞過濾在 panel、作用於 stage 表
  const before = await page.locator('#verbBody tr:visible').count();
  await page.fill('.panel .filter', 'namereg'); await page.waitForTimeout(150);
  const after = await page.locator('#verbBody tr:visible').count();
  c('panel 過濾作用於動詞表', after < before && after >= 1, `${before}→${after}`);
  // 滾動隱現
  await page.evaluate(() => window.scrollTo(0, 700)); await page.waitForTimeout(400);
  const hid = await page.evaluate(() => document.getElementById('vmast').classList.contains('hide'));
  await page.evaluate(() => window.scrollTo(0, 50)); await page.waitForTimeout(400);
  const shw = await page.evaluate(() => !document.getElementById('vmast').classList.contains('hide'));
  c('標頭下滾隱上滾現', hid && shw);
  // 子頁殼
  await page.goto('file:///home/user/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/VIA_UI_VRN.html');
  c('子頁鎖定殼(理徽+紙底)', (await page.locator('.seal').textContent()).trim() === '理' &&
    (await page.evaluate(() => getComputedStyle(document.body).backgroundColor)) === 'rgb(242, 241, 236)');
  const ext = []; page.on('request', r => { if (!r.url().startsWith('file://')) ext.push(r.url()); });
  await page.reload(); await page.waitForTimeout(250);
  c('零外連', ext.length === 0);
  await browser.close();
  let f = 0; for (const [s, n, note] of R) { if (s === 'FAIL') f++; console.log(`  [${s}] ${n}${note ? ' · ' + note : ''}`); }
  console.log(`  [計] ${R.length - f}/${R.length} Hub 鎖定 U/X 檢通過`); process.exit(f ? 1 : 0);
})();
