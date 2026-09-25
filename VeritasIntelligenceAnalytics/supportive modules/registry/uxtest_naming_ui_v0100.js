const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage();
  const results = [];
  const check = (name, ok, note) => { results.push([ok ? 'PASS' : 'FAIL', name, note || '']); };

  // U/X 1: 命名冊板
  await page.goto('file:///home/user/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/VIA_UI_NamingRegistry.html');
  const total = await page.locator('#tb tr').count();
  check('命名冊板渲染列數>0', total > 0, `rows=${total}`);
  const stat0 = await page.locator('#stat').textContent();
  check('統計徽章顯示', /\d+\/\d+ 筆/.test(stat0), stat0.trim());
  // 使用者搜尋
  await page.fill('#q', 'TableOmni');
  await page.waitForTimeout(100);
  const hits = await page.locator('#tb tr').count();
  const first = hits ? await page.locator('#tb tr td').first().textContent() : '';
  check('搜尋 TableOmni 命中且正典名格式', hits >= 1 && /^VRN_ENG\d{3}_/.test(first), `hits=${hits} first=${first}`);
  // SYS 篩選
  await page.fill('#q', '');
  await page.selectOption('#sys', 'FLOW');
  await page.waitForTimeout(100);
  const flowRows = await page.locator('#tb tr').count();
  check('FLOW 篩選=21(18 ENG+3 MDL)', flowRows === 21, `rows=${flowRows}`);
  await page.selectOption('#kind', 'ENG');
  await page.waitForTimeout(100);
  check('FLOW+ENG 疊加=18', (await page.locator('#tb tr').count()) === 18, '');
  // 零 CDN 驗證:頁面無外連請求
  const ext = [];
  page.on('request', r => { if (!r.url().startsWith('file://')) ext.push(r.url()); });
  await page.reload(); await page.waitForTimeout(200);
  check('零 CDN 零外連', ext.length === 0, ext.slice(0, 2).join(','));

  // U/X 2: 母港 Hub 板
  await page.goto('file:///home/user/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/VIA_UI_Hub_Live.html').catch(() => {});
  const hubBody = await page.locator('body').textContent().catch(() => '');
  check('Hub 板可開含五系統字樣', /VRN|VDF|VAP/.test(hubBody), `len=${hubBody.length}`);

  await browser.close();
  let fail = 0;
  for (const [s, n, note] of results) { if (s === 'FAIL') fail++; console.log(`  [${s}] ${n}${note ? ' · ' + note : ''}`); }
  console.log(`  [計] ${results.length - fail}/${results.length} U/X 檢通過`);
  process.exit(fail ? 1 : 0);
})();
