const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const R = []; const c = (n, ok, note) => R.push([ok ? 'PASS' : 'FAIL', n, note || '']);
  await page.goto('file:///home/user/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/product_ui/VIA_UI_Product_CGC.html');
  c('CGC 四 tab', (await page.locator('.tabs .tab').count()) === 4);
  await page.click('.tab[data-pg="g1"]'); await page.waitForTimeout(80);
  const libRows = await page.locator('#g1 tbody tr').count();
  const firstLib = await page.locator('#g1 tbody td').first().textContent();
  c('LIB 冊表渲染(120 顯示)', libRows === 120 && firstLib === 'LIB001', `rows=${libRows} first=${firstLib}`);
  await page.click('.tab[data-pg="g2"]'); await page.waitForTimeout(80);
  c('虛擬環境 tab', (await page.locator('#g2').textContent()).includes('via_operation_optimizer_2026'));
  await page.click('.tab[data-pg="g3"]'); await page.waitForTimeout(80);
  c('架構 WorkFlow 五段鏈', (await page.locator('#g3 tbody tr').count()) === 5);
  await browser.close();
  let f = 0; for (const [s, n, note] of R) { if (s === 'FAIL') f++; console.log(`  [${s}] ${n}${note ? ' · ' + note : ''}`); }
  console.log(`  [計] ${R.length - f}/${R.length} CGC 擴充 U/X 檢通過`); process.exit(f ? 1 : 0);
})();
