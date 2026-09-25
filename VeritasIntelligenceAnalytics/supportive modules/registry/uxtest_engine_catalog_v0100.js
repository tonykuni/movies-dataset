const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.PW_CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const R = []; const c = (n, ok, note) => R.push([ok ? 'PASS' : 'FAIL', n, note || '']);
  await page.goto('file:///home/user/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/VIA_UI_EngineCatalog.html');
  c('352 支載入', (await page.locator('#st').textContent()).includes('352'));
  await page.locator('details').first().click();
  c('詳目展開含功能說明', (await page.locator('details .d').first().textContent()).length > 20);
  await page.fill('#q', 'TableOmni'); await page.waitForTimeout(120);
  c('搜尋命中', (await page.locator('details:visible').count()) >= 1 && (await page.locator('#st').textContent()).startsWith('1/'));
  const ext = []; page.on('request', r => { if (!r.url().startsWith('file://')) ext.push(r.url()); });
  await page.reload(); await page.waitForTimeout(200);
  c('零外連', ext.length === 0);
  await browser.close();
  let f = 0; for (const [s, n] of R) { if (s === 'FAIL') f++; console.log(`  [${s}] ${n}`); }
  console.log(`  [計] ${R.length - f}/${R.length} 目錄板 U/X 過`); process.exit(f ? 1 : 0);
})();
