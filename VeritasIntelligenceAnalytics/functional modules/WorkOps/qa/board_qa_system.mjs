// board_qa_system.mjs v0100 — 指揮板 system 層(真瀏覽器旅程;需 playwright,缺=呼叫端誠實 SKIP)
// 用法:node board_qa_system.mjs <sample_html> [chromium_path]
import { pathToFileURL } from 'node:url';

const [, , htmlPath, chromePath] = process.argv;
let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  if (process.env.PW_MODULE) {
    try {
      ({ chromium } = await import(pathToFileURL(process.env.PW_MODULE).href));
    } catch { /* 落到下方誠實 SKIP */ }
  }
  if (!chromium) {
    console.log('SKIP system tier: playwright 未安裝(npm i playwright 後重跑;或設 PW_MODULE 指向模組)');
    process.exit(3);
  }
}
const browser = await chromium.launch(chromePath ? { executablePath: chromePath } : {});
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errs = [];
page.on('pageerror', e => errs.push(String(e)));
let nOK = 0, nFAIL = 0;
function A(cond, msg) {
  if (cond) { nOK++; console.log('ok  SYS - ' + msg); }
  else { nFAIL++; console.error('FAIL SYS - ' + msg); }
}
await page.goto(pathToFileURL(htmlPath).href);
A((await page.locator('.pfstrip').count()) === 11, '流程帶 11 頁');
for (const p of ['pO', 'p1', 'p2', 'p6']) {
  await page.click(`.tab[data-p='${p}']`);
  A(await page.locator(`#${p}.on`).count() === 1, `分頁切換 ${p}`);
}
await page.fill('#gsq', '艾克米');
await page.waitForTimeout(150);
A((await page.locator('#gsd .gsi').count()) >= 1, '搜尋命中');
await page.keyboard.press('Enter');
await page.waitForTimeout(150);
A((await page.locator('#mback.on').count()) === 1, 'Enter 開專案詳情窗');
await page.keyboard.press('Escape');
await page.click('#mclose').catch(() => {});
await page.click("[data-l='en']");
await page.waitForTimeout(150);
A((await page.locator('#p2 .pfstrip').first().textContent()).indexOf('Page flow') >= 0, 'EN 語言切換(流程帶隨切;textContent 不受隱藏頁影響)');
A(errs.length === 0, `零 pageerror(實得 ${errs.length})`);
await browser.close();
console.log('----------------------------------------');
console.log(`SYSTEM result: ${nOK} ok / ${nFAIL} fail`);
process.exit(nFAIL ? 1 : 0);
