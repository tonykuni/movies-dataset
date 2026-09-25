#!/usr/bin/env node
"use strict";
// Real browser delivery: repeated state must not erase a pending local checkbox edit.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {chromium} = require("playwright");
const VIA = path.resolve(__dirname, "..", "..", "..");
const PAGE = process.env.VIA_SYNC_TEST_PAGE || path.join(VIA, "VIA_HTML_UI/ui/VIA-SYNCHRONIZER-Standalone.html");
const OUT = process.env.VIA_UX_ARTIFACT_DIR || path.join(VIA, "VIA_Reports/sync_pending_test");
const KEY = "via.sync.state.v2";
const CHANNEL = "via.sync.v2";
const CASES = ["storage duplicate", "broadcast duplicate", "same timestamp higher revision", "newer timestamp"];

async function exercise(browser, name) {
  const context = await browser.newContext();
  try {
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(pathToFileURL(PAGE).href);
    await page.click(".module-toggle >> nth=0");
    await page.waitForFunction(key => localStorage.getItem(key) !== null, KEY);
    const prior = await page.evaluate(key => JSON.parse(localStorage.getItem(key)), KEY);
    const wanted = !prior.modules[0].enabled;
    const incoming = structuredClone(prior);
    const peer = name.startsWith("broadcast") ? await context.newPage() : null;
    if (peer) await peer.goto(pathToFileURL(PAGE).href);
    if (name.endsWith("duplicate")) {
      await page.click(".module-toggle >> nth=0");
    } else {
      incoming.modules[0].enabled = wanted;
      if (name === "same timestamp higher revision") incoming.sync.revision += 1;
      else incoming.updatedAt = new Date(Date.parse(prior.updatedAt) + 1000).toISOString();
    }
    if (name.startsWith("broadcast")) {
      // Independent same-origin tab delivers a real BroadcastChannel notification.
      await peer.evaluate(({channel, state}) => {
        const bc = new BroadcastChannel(channel);
        bc.postMessage({type: "via-state-v2", originId: "independent-test-peer", state});
        bc.close();
      }, {channel: CHANNEL, state: incoming});
    } else {
      await page.evaluate(({key, state}) => {
        window.dispatchEvent(new StorageEvent("storage", {key, newValue: JSON.stringify(state)}));
      }, {key: KEY, state: incoming});
    }
    if (name.endsWith("duplicate")) {
      await page.waitForFunction(({key, rev}) => JSON.parse(localStorage.getItem(key)).sync.revision > rev,
                                 {key: KEY, rev: prior.sync.revision});
      const saved = await page.evaluate(key => JSON.parse(localStorage.getItem(key)), KEY);
      assert.equal(saved.modules[0].enabled, wanted, "duplicate delivery erased pending local edit");
    }
    assert.equal(await page.isChecked(".module-toggle >> nth=0"), wanted);
    assert.deepEqual(errors, []);
    return {name, passed: true};
  } finally {
    await context.close();
  }
}

(async () => {
  const browser = await chromium.launch({headless: true});
  const results = [];
  try {
    for (const name of CASES) {
      try { results.push(await exercise(browser, name)); }
      catch (error) { results.push({name, passed: false, error: String(error)}); }
    }
    const report = {browser: browser.version(), total: results.length,
                    passed: results.filter(row => row.passed).length, results};
    fs.mkdirSync(OUT, {recursive: true});
    fs.writeFileSync(path.join(OUT, "sync_pending_report.json"), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report));
    process.exitCode = report.passed === report.total ? 0 : 1;
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
