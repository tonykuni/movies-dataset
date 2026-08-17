const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage();
  const R = []; const c = (n, ok, note) => R.push([ok ? 'PASS' : 'FAIL', n, note || '']);
  await page.goto('file:///home/user/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/VIA_UI_NamingRegistry.html');
  c('渲染列數>0', (await page.locator('#tb tr').count()) > 0);
  const seal = await page.locator('.seal').textContent().catch(() => '');
  c('理印徽存在', seal.trim() === '理', seal.trim());
  const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  c('紙底 #f2f1ec 鎖定', bg === 'rgb(242, 241, 236)', bg);
  const sealBg = await page.evaluate(() => getComputedStyle(document.querySelector('.seal')).backgroundColor);
  c('印紅 #9e2b25 鎖定', sealBg === 'rgb(158, 43, 37)', sealBg);
  const thb = await page.evaluate(() => getComputedStyle(document.querySelector('th')).borderBottomColor);
  c('表頭青線 #3c6660', thb === 'rgb(60, 102, 96)', thb);
  await page.fill('#q', 'TableOmni'); await page.waitForTimeout(100);
  c('搜尋仍命中', (await page.locator('#tb tr').count()) >= 1);
  const ext = []; page.on('request', r => { if (!r.url().startsWith('file://')) ext.push(r.url()); });
  await page.reload(); await page.waitForTimeout(300);
  c('零 CDN 零外連', ext.length === 0, ext.slice(0, 2).join(','));
  await browser.close();
  let f = 0; for (const [s, n, note] of R) { if (s === 'FAIL') f++; console.log(`  [${s}] ${n}${note ? ' · ' + note : ''}`); }
  console.log(`  [計] ${R.length - f}/${R.length} 視覺鎖定 U/X 檢通過`); process.exit(f ? 1 : 0);
})();
