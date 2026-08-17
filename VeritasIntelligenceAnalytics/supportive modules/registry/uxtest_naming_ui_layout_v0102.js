const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } }); // 橫向螢幕基準
  const R = []; const c = (n, ok, note) => R.push([ok ? 'PASS' : 'FAIL', n, note || '']);
  await page.goto('file:///home/user/movies-dataset/VeritasIntelligenceAnalytics/VIA_Reports/VIA_UI_NamingRegistry.html');
  // 幾何:panel 在左、stage 在右
  const pb = await page.locator('#panel').boundingBox();
  const sb = await page.locator('.stage').boundingBox();
  c('左功能 panel 存在且靠左', pb && pb.x < 10 && pb.width > 200 && pb.width < 300, pb && `x=${pb.x} w=${pb.width}`);
  c('右視覺 stage 在 panel 右側', sb && sb.x >= pb.x + pb.width - 2, sb && `x=${sb.x}`);
  // 視覺鎖定沿用
  const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  c('紙底鎖定沿用', bg === 'rgb(242, 241, 236)', bg);
  c('理印徽沿用', (await page.locator('.seal').textContent()).trim() === '理');
  // SYS 即點即濾
  const total = await page.locator('#tb tr').count();
  await page.locator('.syslist li', { hasText: 'FLOW' }).first().click();
  await page.waitForTimeout(120);
  const flowRows = await page.locator('#tb tr').count();
  c('SYS panel 即點即濾 FLOW=21', flowRows === 21, `all=${total} flow=${flowRows}`);
  // 滾動隱藏標頭:下滾隱、上滾現
  await page.locator('.syslist li').first().click(); await page.waitForTimeout(120); // 回全部,行多可滾
  await page.evaluate(() => window.scrollTo(0, 600)); await page.waitForTimeout(400);
  const hidden = await page.evaluate(() => document.getElementById('mast').classList.contains('hide'));
  await page.evaluate(() => window.scrollTo(0, 100)); await page.waitForTimeout(400);
  const shown = await page.evaluate(() => !document.getElementById('mast').classList.contains('hide'));
  c('下滾標頭自動隱', hidden === true);
  c('上滾標頭復現', shown === true);
  // 窄幅(直向)回退:panel 收頂單欄
  await page.setViewportSize({ width: 700, height: 1000 }); await page.waitForTimeout(250);
  const pb2 = await page.locator('#panel').boundingBox();
  const sb2 = await page.locator('.stage').boundingBox();
  c('窄幅單欄 panel 收頂', pb2 && sb2 && sb2.y > pb2.y + pb2.height - 5, `panelY=${pb2 && pb2.y} stageY=${sb2 && sb2.y}`);
  // 零外連
  const ext = []; page.on('request', r => { if (!r.url().startsWith('file://')) ext.push(r.url()); });
  await page.reload(); await page.waitForTimeout(300);
  c('零 CDN 零外連', ext.length === 0);
  await browser.close();
  let f = 0; for (const [s, n, note] of R) { if (s === 'FAIL') f++; console.log(`  [${s}] ${n}${note ? ' · ' + note : ''}`); }
  console.log(`  [計] ${R.length - f}/${R.length} 佈局 U/X 檢通過`); process.exit(f ? 1 : 0);
})();
