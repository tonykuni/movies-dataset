#!/usr/bin/env node
'use strict';
// Exercise the actual canonical template with the engine's escaped fixture.
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');

(async () => {
  const root = process.argv[2];
  if (!root) throw new Error('Expected ETF activity report directory');
  const browser = await chromium.launch({headless: true});
  const checks = [];
  try {
    for (const width of [1440, 390]) {
      const page = await browser.newPage({viewport: {width, height: 1000}});
      const errors = [], external = [];
      page.on('pageerror', e => errors.push(String(e)));
      page.on('request', r => {if (/^https?:/.test(r.url())) external.push(r.url());});
      await page.goto(pathToFileURL(path.join(root, 'ui', 'VIA-UI-Standalone-NoServer.html')).href);
      await page.waitForSelector('[data-addon-id="vdf-etf-activity"] table', {timeout: 10000});
      const state = await page.evaluate(() => ({
        registered: window.VIA_ADDON_API.list().filter(a => a.id === 'vdf-etf-activity').length,
        injection: !!window.badETF,
        text: document.querySelector('[data-addon-id="vdf-etf-activity"]').textContent,
        documentWidth: document.documentElement.scrollWidth,
        viewport: innerWidth,
      }));
      const assertions = {
        registeredOnce: state.registered === 1,
        sourceTextInert: !state.injection && state.text.includes('</script><script>window.badETF=true</script>'),
        estimateVisible: state.text.includes('ESTIMATE') && state.text.includes('淨增持推估均價') && state.text.includes('淨申贖金額估計') && state.text.includes('AUM (TWD)'),
        noPageErrors: errors.length === 0,
        noExternalRequests: external.length === 0,
        noHorizontalPageScroll: state.documentWidth <= state.viewport,
      };
      checks.push({width, assertions, errors, external, documentWidth: state.documentWidth});
      await page.locator('[data-addon-id="vdf-etf-activity"]').scrollIntoViewIfNeeded();
      await page.screenshot({path: path.join(root, `etf-activity-${width}.png`), fullPage: true});
      await page.close();
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(root, 'ETF_ACTIVITY_UAT.json'), JSON.stringify(checks, null, 2));
  console.log(JSON.stringify(checks, null, 2));
  if (checks.some(c => Object.values(c.assertions).some(v => !v))) process.exitCode = 1;
})().catch(e => {console.error(e); process.exitCode = 1;});
