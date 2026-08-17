const { chromium } = require('playwright');
const BASE = 'file:///home/user/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/product_ui/';
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  const R = []; const c = (n, ok, note) => R.push([ok ? 'PASS' : 'FAIL', n, note || '']);
  const ext = []; page.on('request', r => { if (!r.url().startsWith('file://')) ext.push(r.url()); });

  // Index → 五連結
  await page.goto(BASE + 'VIA_UI_Product_Index.html');
  c('Index 五系統連結', (await page.locator('.cardbox a').count()) === 5);

  // CGC:綁機流程+元指令隱藏
  await page.goto(BASE + 'VIA_UI_Product_CGC.html');
  await page.fill('#pn', 'VIA-A1B2-C3D4'); await page.click('button:has-text("綁定本機")');
  await page.waitForTimeout(100);
  c('商品號綁一機(格式閘+綁定)', (await page.locator('#bindst').textContent()).includes('已綁定 VIA-A1B2-C3D4'));
  await page.fill('#pn', 'BAD'); await page.click('button:has-text("綁定本機")'); await page.waitForTimeout(80);
  c('壞商品號被格式閘擋', (await page.locator('#bindst').textContent()).includes('格式'));
  const titles = await page.evaluate(() => [...document.querySelectorAll('[data-cmd]')].every(e => !e.title));
  c('元指令預設隱藏(title 空)', titles);
  await page.keyboard.press('Alt+m'); await page.waitForTimeout(80);
  const shown = await page.evaluate(() => [...document.querySelectorAll('[data-cmd]')].some(e => e.title.length > 0));
  c('Alt+M 揭示元指令(操作員道)', shown);

  // VRN:三卡+四 tab 切換
  await page.goto(BASE + 'VIA_UI_Product_VRN.html');
  c('VRN 首頁三卡', (await page.locator('#t0 .cardbox').count()) === 3);
  await page.click('.tab[data-pg="t2"]'); await page.waitForTimeout(80);
  c('VRN tab 切換→對照驗證', await page.locator('#t2').isVisible() && (await page.locator('#t2 tbody tr').count()) === 5);

  // VDF:77 勾選+清單產生
  await page.goto(BASE + 'VIA_UI_Product_VDF.html');
  c('VDF 77 勾選項', (await page.locator('.pick').count()) === 77);
  await page.locator('.pick').first().check(); await page.locator('.pick').nth(5).check();
  await page.click('button:has-text("產生執行清單")'); await page.waitForTimeout(80);
  const outp = await page.locator('#outp').inputValue();
  c('VDF 清單產生(長線模式)', outp.includes('長線維護') && outp.includes('via-forge'));

  // VAP:40 卡+輸出鈕
  await page.goto(BASE + 'VIA_UI_Product_VAP.html');
  c('VAP 40 型固定卡片', (await page.locator('#cards .cardbox').count()) === 40);
  c('PDF/HTML 輸出鈕在', (await page.locator('button:has-text("PDF")').count()) === 1 && (await page.locator('button:has-text("HTML")').count()) === 1);

  // FLOW:六 tab+主動 ETF 監控表
  await page.goto(BASE + 'VIA_UI_Product_FLOW.html');
  c('FLOW 六 tab', (await page.locator('.tabs .tab').count()) === 6);
  await page.click('.tab[data-pg="f5"]'); await page.waitForTimeout(80);
  c('主動 ETF 監控表(D 類 4 面)', (await page.locator('#f5 tbody tr').count()) === 4);
  await page.click('.tab[data-pg="f3"]'); await page.waitForTimeout(80);
  c('戰略回測 tab 含誠實界線', (await page.locator('#f3').textContent()).includes('勿以自證數字下單'));

  c('全門面零外連', ext.length === 0, ext.slice(0, 2).join(','));
  await browser.close();
  let f = 0; for (const [s, n, note] of R) { if (s === 'FAIL') f++; console.log(`  [${s}] ${n}${note ? ' · ' + note : ''}`); }
  console.log(`  [計] ${R.length - f}/${R.length} 產品門面 U/X 檢通過`); process.exit(f ? 1 : 0);
})();
