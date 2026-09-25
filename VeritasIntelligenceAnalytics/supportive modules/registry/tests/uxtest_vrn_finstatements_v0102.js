#!/usr/bin/env node
"use strict";

/**
 * VRN 交易所財報模板頁 · 瀏覽器使用者實測(側線 2026-09-24 第十五段;主線批號由併線的手指定 L25)
 * v0100→v0101(第十五段(續),併 main 批735 時):引擎 LL334 讓號為 VRN_ENG090;+⑱⑲⑳ 跟批735 VRN 模板共存——
 *   同一份 SYNCHRONIZER 狀態裡有批735 掛的 vrn-report-template(你在 SYNCHRONIZER 關掉了)和你自建的模組,
 *   交接只增不減(ENG090 v0101):兩個原樣留著;你關掉的本頁模組,自動更新之後還是關的;中央 UI 側欄照啟用與否畫。
 *
 * 真開三支頁(全部 file://,零伺服器、零網路):
 *   VRN 頁   supportive modules/ui_support/VIA_UI_VRNFinStatements_v0100.html(VRN_ENG090 run 產)
 *   SYNCHRONIZER / 中央 UI   VIA_HTML_UI/ui/(正本,只讀不改)
 * 驗:開頁零錯誤 · 燈與矩陣畫出來 · 交接到 SYNCHRONIZER → 中央 UI 收到 · 重開不重寫 · 檢視跟著 SYNCHRONIZER ·
 *     「手動」規則擋交接 · 只往新的方向自動更新(舊 → 更新;新 → 不蓋回去)· 別的範本要確認 · 下載信封 ·
 *     SYNCHRONIZER 匯入信封 / 歷史 CSV · 手機寬度不橫捲 · 跟批735 VRN 模板共存(只增不減)。
 * 用法:先 `python "functional modules/VRN/VRN_ENG090_FinStatementsTemplate_v*.py" run`,再
 *       `node uxtest_vrn_finstatements_v0101.js`(需要 Playwright 與它的 Chromium;缺 = 丟錯講明,不假綠)。
 * 環境:VIA_UX_ARTIFACT_DIR(截圖與報告)· VIA_VRN_FINSTAT_PAGE / VIA_VRN_FINSTAT_OUT(換頁或信封夾)。
 * 產出:uxtest_vrn_finstatements_report.json + uxtest_vrn_finstatements_report.html(單檔 HTML 結果報告:截圖內嵌、零外連,file:// 直開)。
 */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {chromium} = require("playwright");

const VIA_ROOT = path.resolve(__dirname, "..", "..", "..");
const PAGE = process.env.VIA_VRN_FINSTAT_PAGE ||
  path.join(VIA_ROOT, "supportive modules", "ui_support", "VIA_UI_VRNFinStatements_v0100.html");
const OUT = process.env.VIA_VRN_FINSTAT_OUT || path.join(VIA_ROOT, "VIA_Reports", "vrn", "finstat");
const ENVELOPE = path.join(OUT, "VRN_FINSTAT_SYNC_latest.json");
const HISTORY_CSV = path.join(OUT, "VRN_FINSTAT_HISTORY_latest.csv");
const SYNC = path.join(VIA_ROOT, "VIA_HTML_UI", "ui", "VIA-SYNCHRONIZER-Standalone.html");
const UI = path.join(VIA_ROOT, "VIA_HTML_UI", "ui", "VIA-UI-Standalone-NoServer.html");
const ARTIFACT_DIR = process.env.VIA_UX_ARTIFACT_DIR ||
  path.join(VIA_ROOT, "VIA_Reports", "ui_vrn_finstat_test_artifacts");
const KEY = "via.sync.state.v2";
const TID = "vrn-exchange-finstatements";
const SYSTEM_IDS = ["overview", "topology", "endpoints", "events", "governance"];
// 套件正本(VIA_HTML_UI)已知缺陷:中央 UI 同步段在另一個 <script> 作用域呼叫 toast(),解析到 window.toast(id="toast" 的元素)
// → 每收到一次遠端狀態拋一次 TypeError。基線實量:不經本頁、只用 SYNCHRONIZER 套範本 + 套檢視,一樣拋 2 次;狀態照套用(寫入在前)。
// 套件是正本(sha256 冊 · CGC_MDL160 閘)不能改,所以只放行這一句、別的錯照紅;本頁自己必須零錯誤。
const KNOWN_PACKAGE_ERRORS = []; // authorized canonical template repair: all errors fail

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
let browserVersion = "";
const SHOTS = [["vrn_desktop.png", "VRN 模板頁(桌機 1440)"], ["synchronizer_after_handover.png", "SYNCHRONIZER 交接後"],
  ["central_ui_after_handover.png", "中央 UI 交接後(自定義模組側欄)"], ["vrn_mobile.png", "VRN 模板頁(手機 390)"],
  ["synchronizer_coexist.png", "跟批735 VRN 模板共存:SYNCHRONIZER 模組清單(只增不減)"], ["central_ui_coexist.png", "共存:中央 UI 自定義模組側欄"]];
// 批735 VRN 模板(VRN_ENG089_TemplateView)預置段掛進同一份狀態的模組(照它的 MODULE 常數;只增不減)
const B735_MODULE = {id: "vrn-report-template", name: "VRN 研報自測成果", type: "dashboard", enabled: true, pinned: true, system: false,
  note: "VRN_ENG089 制式模板外掛(上游:自測迴圈報告)"};

function esc(v) {
  return String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
}

function htmlReport(meta, summary, rows) {
  // 單檔 HTML 結果報告:VIA 制式淺色配色、截圖內嵌(data URI)、零外連,file:// 直開
  const ok = summary.failed === 0;
  const shots = SHOTS.map(([f, cap]) => {
    const p = path.join(ARTIFACT_DIR, f);
    if (!fs.existsSync(p)) return "";
    return `<figure><img alt="${esc(cap)}" src="data:image/png;base64,${fs.readFileSync(p).toString("base64")}"><figcaption>${esc(cap)}</figcaption></figure>`;
  }).join("");
  const trs = rows.map((r) => `<tr class="${r.passed ? "ok" : "bad"}"><td><span class="chip">${r.passed ? "OK" : "FAIL"}</span></td><td>${esc(r.name)}</td>` +
    `<td class="num">${r.ms}</td><td><code>${esc(r.passed ? JSON.stringify(r.detail) : r.error).slice(0, 400)}</code></td></tr>`).join("");
  return `<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>VRN 財報模板 · 使用者實測結果</title><style>
:root{--bg:#f3f5f2;--surface:#fff;--ink:#17201d;--muted:#778680;--line:#dce5e0;--teal:#177066;--teal-soft:#e4f2ef;--danger:#b33e3e;--accent-soft:#f8e9e6;--gold:#b5822c}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 'Segoe UI','Noto Sans TC',system-ui,sans-serif}
main{max-width:1200px;margin:0 auto;padding:18px}h1{font-size:1.4em;margin:4px 0}.sub{color:var(--muted)}
.eyebrow{color:var(--gold);font-size:.78em;letter-spacing:.14em;font-weight:600}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:12px 0}
.big{font-size:2em;font-weight:700;color:${ok ? "var(--teal)" : "var(--danger)"}}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
td.num{text-align:right;font-variant-numeric:tabular-nums}code{font-size:.85em;word-break:break-all;white-space:pre-wrap}
tr.ok .chip{background:var(--teal-soft);color:var(--teal)}tr.bad .chip{background:var(--accent-soft);color:var(--danger)}
.chip{display:inline-block;padding:2px 10px;border-radius:999px;font-weight:600;font-size:.85em}
.shots{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}figure{margin:0}figure img{width:100%;border:1px solid var(--line);border-radius:10px}
figcaption{color:var(--muted);font-size:.85em;margin-top:4px}.scroll{overflow-x:auto}
</style></head><body><main>
<div class="eyebrow">VRN · EXCHANGE MOPS · SYNCHRONIZER · USER TEST</div><h1>VRN 交易所財報模板 · 瀏覽器使用者實測</h1>
<p class="sub">${esc(meta.ran)} · Chromium ${esc(meta.chromium)} · 範本 ${esc(meta.template)}</p>
<section class="panel"><div class="big">${summary.passed} / ${summary.total} OK</div><p class="sub">FAIL ${summary.failed}。三支頁全部 file:// 真開(零伺服器、零網路)。
已知套件缺陷(不是本頁):${esc(meta.known_package_defect)}</p></section>
<section class="panel"><h2>逐檢</h2><div class="scroll"><table><thead><tr><th>結果</th><th>檢</th><th>ms</th><th>細節</th></tr></thead><tbody>${trs}</tbody></table></div></section>
<section class="panel"><h2>截圖</h2><div class="shots">${shots}</div></section>
<p class="sub">頁 ${esc(meta.page)} · 信封 ${esc(meta.envelope)}</p></main></body></html>
`;
}

async function check(name, fn) {
  const t0 = Date.now();
  try {
    const detail = (await fn()) || {};
    results.push({name, passed: true, ms: Date.now() - t0, detail});
    console.log(`  [OK] ${name} ${JSON.stringify(detail).slice(0, 180)}`);
  } catch (err) {
    results.push({name, passed: false, ms: Date.now() - t0, error: String(err && err.message || err)});
    console.log(`  [FAIL] ${name} :: ${String(err && err.message || err).slice(0, 300)}`);
  }
}

async function waitFor(fn, ms = 4000, step = 60) {
  const t0 = Date.now();
  let last;
  while (Date.now() - t0 < ms) {
    last = await fn();
    if (last) return last;
    await sleep(step);
  }
  return last;
}

const storage = (page) => page.evaluate((k) => JSON.parse(localStorage.getItem(k) || "null"), KEY);
const lamp = (page) => page.evaluate(() => {
  const el = document.getElementById("handoverLamp");
  return {state: el.dataset.state, text: el.textContent};
});

function watchErrors(page, tag, bag) {
  page.on("console", (m) => { if (m.type() === "error") bag.push(`${tag} console: ${m.text()}`); });
  page.on("pageerror", (e) => bag.push(`${tag} pageerror: ${e.message}`));
}

function launchOptions() {
  const exe = chromium.executablePath();
  if (!fs.existsSync(exe)) {
    throw new Error(`Playwright 的 Chromium 不在:${exe}(npx playwright install chromium)`);
  }
  return {headless: true};
}

async function main() {
  for (const p of [PAGE, ENVELOPE, HISTORY_CSV, SYNC, UI]) {
    if (!fs.existsSync(p)) throw new Error(`缺件:${p}(先跑 VRN_ENG090 run;套件在 VIA_HTML_UI/ui)`);
  }
  fs.mkdirSync(ARTIFACT_DIR, {recursive: true});
  const envFile = JSON.parse(fs.readFileSync(ENVELOPE, "utf-8"));
  const csvRows = fs.readFileSync(HISTORY_CSV, "utf-8").replace(/^﻿/, "").trim().split(/\r?\n/).length - 1;
  const pageUrl = pathToFileURL(PAGE).href;
  const syncUrl = pathToFileURL(SYNC).href;
  const uiUrl = pathToFileURL(UI).href;
  const browser = await chromium.launch(launchOptions());
  browserVersion = browser.version();
  const errors = {vrn: [], sync: [], ui: []};

  // ── 桌機:交接主流程 ────────────────────────────────────────────
  const ctx = await browser.newContext({viewport: {width: 1440, height: 900}, locale: "zh-TW", acceptDownloads: true});
  const vrn = await ctx.newPage();
  watchErrors(vrn, "vrn", errors.vrn);
  await vrn.goto(pageUrl, {waitUntil: "load"});
  const stamp = await vrn.evaluate(() => window.VRN_FINSTAT.envelope().analytics.templateName);
  const hasDataStamp = /資料 \d{4}-\d{2}-\d{2}/.test(stamp);

  await check("① 開頁零錯誤(console / pageerror 0)· 頁內信封 == 信封檔", async () => {
    await sleep(200);
    assert.equal(errors.vrn.length, 0, errors.vrn.join(" | "));
    const env = await vrn.evaluate(() => window.VRN_FINSTAT.envelope());
    assert.deepEqual(env, envFile, "頁內信封跟信封檔不同");
    return {title: await vrn.title(), templateName: env.analytics.templateName};
  });

  await check("② 燈、KPI、端點矩陣、圖都畫出來", async () => {
    const d = await vrn.evaluate(() => ({
      up: document.querySelectorAll(".lamps section:first-child li").length,
      down: document.querySelectorAll(".lamps section:nth-child(2) li").length,
      chips: [...document.querySelectorAll(".lamps .chip")].every((c) => /lamp-(GREEN|NODATA|STALE|GATED|ABSENT|RED)/.test(c.className)),
      kpi: document.querySelectorAll(".kpi").length,
      rows: document.querySelectorAll("#endpointMatrix tbody tr").length,
      bars: document.querySelectorAll("#chart rect").length,
      noData: !!document.querySelector("main p.sub") && !document.getElementById("chart"),
    }));
    assert.ok(d.up >= 2 && d.down >= 5 && d.chips, `燈 上 ${d.up} 下 ${d.down}`);
    assert.ok(d.kpi >= 1 && d.rows >= 12, `KPI ${d.kpi} · 矩陣列 ${d.rows}`);
    assert.ok(d.bars > 0 || d.noData, "圖沒畫、也沒寫「尚無資料列」");
    return d;
  });

  await check("③ 空的 SYNCHRONIZER 狀態 → 交接燈 缺料「還沒有狀態」", async () => {
    const l = await lamp(vrn);
    assert.equal(l.state, "NODATA", l.text);
    return l;
  });

  const sync = await ctx.newPage();
  watchErrors(sync, "sync", errors.sync);
  await sync.goto(syncUrl, {waitUntil: "load"});
  await sync.locator("#templateSelect").waitFor({state: "visible"});
  const ui = await ctx.newPage();
  watchErrors(ui, "ui", errors.ui);
  await ui.goto(uiUrl, {waitUntil: "load"});
  await ui.locator("#investmentDesk").waitFor({state: "visible"});
  await sleep(200);

  await check("④ 三頁同源(file://)· VRN 頁與 SYNCHRONIZER 共用 localStorage", async () => {
    const o = [await vrn.evaluate(() => location.origin), await sync.evaluate(() => location.origin), await ui.evaluate(() => location.origin)];
    assert.ok(o[0] === o[1] && o[1] === o[2], JSON.stringify(o));
    return {origin: o[0]};
  });

  await check("⑤ 按「交接到 SYNCHRONIZER」→ 狀態寫進同一把鍵:範本 id 對、系統模組照留排最前、VRN 模組跟上;同時在頻道上廣播(別頁聽得到)", async () => {
    await sync.evaluate((ch) => { window.__vrnHeard = null; const b = new BroadcastChannel(ch); b.onmessage = (e) => { if (e.data && e.data.type === "via-state-v2" && String(e.data.originId || "").startsWith("vrn-finstat-")) window.__vrnHeard = e.data.state.analytics.templateId; }; window.__vrnBc = b; }, "via.sync.v2");
    await vrn.bringToFront();
    await vrn.click("#handoverBtn");
    if (await vrn.locator("#confirmBar").isVisible()) await vrn.click("#confirmBtn");
    const st = await waitFor(async () => { const s = await storage(vrn); return s && s.analytics && s.analytics.templateId === TID ? s : null; });
    assert.ok(st, "localStorage 沒有 VRN 範本");
    assert.deepEqual(st.modules.slice(0, 5).map((m) => m.id), SYSTEM_IDS);
    const own = st.modules.filter((m) => !m.system).map((m) => m.id);
    assert.deepEqual(own, envFile.modules.filter((m) => !m.system).map((m) => m.id));
    const heard = await waitFor(async () => sync.evaluate(() => window.__vrnHeard));
    assert.equal(heard, TID, "頻道上沒聽到 VRN 頁的廣播");
    return {revision: st.sync.revision, modules: st.modules.length, history: st.analytics.history.length, heard};
  });

  await check("⑥ SYNCHRONIZER 收到(範本名 · 模組清單有「上櫃財報」)", async () => {
    const ok = await waitFor(async () => {
      const t = await sync.evaluate(() => ({name: document.getElementById("templateName").textContent, list: document.getElementById("moduleList").textContent}));
      return t.name.includes("VRN 交易所財報") && t.list.includes("財報總覽") ? t : null;
    });
    assert.ok(ok, "SYNCHRONIZER 沒有畫出 VRN 範本");
    return {templateName: ok.name};
  });

  await check("⑦ 中央 UI 收到(同一份狀態 · 自定義模組側欄出現 VRN 模組、名稱帶燈)", async () => {
    const ok = await waitFor(async () => {
      const s = await ui.evaluate(() => window.VIA_ENGINE_HUB && window.VIA_ENGINE_HUB.state && window.VIA_ENGINE_HUB.state.snapshot());
      const nav = await ui.evaluate(() => (document.getElementById("customModuleNav") || {}).textContent || "");
      return s && s.analytics && s.analytics.templateId === TID && nav.includes("VRN 財報總覽") ? {nav} : null;
    });
    assert.ok(ok, "中央 UI 沒收到 VRN 範本");
    return {nav: ok.nav.slice(0, 80)};
  });

  await check("⑧ VRN 頁交接燈轉綠;重開頁不重寫(revision 不動)", async () => {
    const l1 = await lamp(vrn);
    assert.equal(l1.state, "GREEN", l1.text);
    const rev = (await storage(vrn)).sync.revision;
    await vrn.reload({waitUntil: "load"});
    await sleep(300);
    const l2 = await lamp(vrn);
    assert.equal(l2.state, "GREEN", l2.text);
    assert.ok(l2.text.includes("已是本頁資料"), l2.text);
    assert.equal((await storage(vrn)).sync.revision, rev);
    return {revision: rev, lamp: l2.text};
  });

  await check("⑨ 檢視跟著 SYNCHRONIZER(密度改「緊湊」→ VRN 頁 --density = 中央 UI 同一個值)", async () => {
    await sync.bringToFront();
    await sync.selectOption("#density", "compact");
    await sync.click("#applyView");
    const d = await waitFor(async () => {
      const v = await vrn.evaluate(() => document.documentElement.style.getPropertyValue("--density").trim());
      return v === ".86" ? v : null;
    });
    assert.equal(d, ".86");
    return {density: d};
  });

  await check("⑩ SYNCHRONIZER 規則「手動」·「只同步檢視」· 衝突「本機優先」→ VRN 頁都不寫(燈=閘、revision 不動);改回「全部 / 最新優先」", async () => {
    const seen = [];
    for (const [scope, conflict] of [["manual", "latest"], ["view-only", "latest"], ["all", "local"]]) {
      await sync.bringToFront();
      await sync.selectOption("#syncScope", scope);
      await sync.selectOption("#conflictRule", conflict);
      await sync.click("#applyRules");
      await sleep(500);
      const rev = (await storage(vrn)).sync.revision;
      await vrn.bringToFront();
      await vrn.click("#handoverBtn");
      await sleep(300);
      const l = await lamp(vrn);
      const after = (await storage(vrn)).sync.revision;
      assert.equal(l.state, "GATED", `${scope}/${conflict}:${l.text}`);
      assert.equal(after, rev, `${scope}/${conflict} 還是寫了`);
      seen.push(`${scope}/${conflict}`);
    }
    await sync.bringToFront();
    await sync.selectOption("#syncScope", "all");
    await sync.selectOption("#conflictRule", "latest");
    await sync.click("#applyRules");
    await sleep(500);
    return {blocked: seen};
  });

  await check("⑪ 自動更新只往新的方向:SYNCHRONIZER 是本範本的舊資料 → VRN 頁自己更新;是更新的資料 → 不蓋回去", async () => {
    const setStamp = (s) => sync.evaluate(([k, st]) => {
      const cur = JSON.parse(localStorage.getItem(k));
      cur.analytics.templateName = cur.analytics.templateName.replace(/資料 (?:[0-9: -]+|—)/, "資料 " + st);
      cur.updatedAt = new Date(Date.now() + 1000).toISOString();
      localStorage.setItem(k, JSON.stringify(cur));
    }, [KEY, s]);
    const rev0 = (await storage(vrn)).sync.revision;
    if (!hasDataStamp) {
      await setStamp("2099-01-01 00:00:00");
      await sleep(900);
      const kept = await storage(vrn);
      assert.ok(kept.analytics.templateName.includes("2099-01-01"), "NODATA overwrote dated data");
      assert.equal(kept.sync.revision, rev0, "NODATA silently wrote shared state");
      assert.equal((await lamp(vrn)).state, "STALE");
      return {scenario: "NODATA preserves dated state", datedUpdate: "covered by populated-fixture run"};
    }
    await setStamp("2020-01-01 00:00:00");
    const up = await waitFor(async () => { const s = await storage(vrn); return s.analytics.templateName === stamp && s.sync.revision > rev0 ? s : null; });
    const l1 = await lamp(vrn);
    assert.ok(up, "舊資料沒被自動更新(範本名沒換回本頁資料時點,或 revision 沒往上)");
    assert.equal(l1.state, "GREEN", l1.text);          // 自動更新後 SYNCHRONIZER 回寫同一份,燈停在「已是本頁資料」
    await setStamp("2099-01-01 00:00:00");
    await sleep(900);
    const s2 = await storage(vrn);
    const l2 = await lamp(vrn);
    assert.ok(s2.analytics.templateName.includes("2099-01-01"), "更新的資料被蓋回去了");
    assert.equal(l2.state, "STALE", l2.text);
    return {older: `rev ${rev0} → ${up.sync.revision} · ${l1.text.slice(0, 30)}`, newer: l2.text.slice(0, 50)};
  });

  await check("⑫ SYNCHRONIZER 換成別的範本(投資研究)→ VRN 頁先問、確認才換", async () => {
    await sync.bringToFront();
    await sync.selectOption("#templateSelect", "investment-research");
    await sync.selectOption("#templateMode", "replace");
    await sync.click("#applyTemplate");
    await waitFor(async () => ((await storage(sync)).analytics || {}).templateId === "investment-research");
    await vrn.bringToFront();
    const l = await waitFor(async () => { const x = await lamp(vrn); return x.text.includes("投資研究") ? x : null; });
    assert.ok(l, "VRN 頁沒發現範本換了");
    await vrn.click("#handoverBtn");
    assert.ok(await vrn.locator("#confirmBar").isVisible(), "沒先問就換");
    assert.equal((await storage(vrn)).analytics.templateId, "investment-research");
    await vrn.click("#confirmBtn");
    const s = await waitFor(async () => { const x = await storage(vrn); return x.analytics.templateId === TID ? x : null; });
    assert.ok(s, "確認後沒換成 VRN 範本");
    return {lamp: (await lamp(vrn)).text.slice(0, 40)};
  });

  await check("⑬ 下載信封 = 信封檔(SYNCHRONIZER 匯入用)", async () => {
    const [dl] = await Promise.all([vrn.waitForEvent("download"), vrn.click("#downloadBtn")]);
    const p = path.join(ARTIFACT_DIR, dl.suggestedFilename());
    await dl.saveAs(p);
    assert.deepEqual(JSON.parse(fs.readFileSync(p, "utf-8")), envFile);
    return {file: dl.suggestedFilename()};
  });

  await vrn.screenshot({path: path.join(ARTIFACT_DIR, "vrn_desktop.png"), fullPage: true});
  await sync.screenshot({path: path.join(ARTIFACT_DIR, "synchronizer_after_handover.png"), fullPage: false});
  await ui.screenshot({path: path.join(ARTIFACT_DIR, "central_ui_after_handover.png"), fullPage: false});
  await check("⑭ 全程:VRN 頁零錯誤 · SYNCHRONIZER 零錯誤 · 中央 UI 零錯誤", async () => {
    assert.equal(errors.vrn.length, 0, errors.vrn.join(" | "));
    assert.equal(errors.sync.length, 0, errors.sync.join(" | "));
    const other = errors.ui.filter((e) => !KNOWN_PACKAGE_ERRORS.some((rx) => rx.test(e)));
    assert.equal(other.length, 0, other.join(" | "));
    return {vrn: 0, sync: 0, ui_known_package_defect: errors.ui.length - other.length};
  });
  await ctx.close();

  // ── 另一個乾淨瀏覽器:SYNCHRONIZER 匯入信封 / 歷史 CSV ─────────────────
  const ctx2 = await browser.newContext({viewport: {width: 1280, height: 860}, locale: "zh-TW"});
  const s2 = await ctx2.newPage();
  const e2 = [];
  watchErrors(s2, "sync2", e2);
  await s2.goto(syncUrl, {waitUntil: "load"});
  await s2.locator("#templateSelect").waitFor({state: "visible"});
  await check("⑮ SYNCHRONIZER「匯入」信封檔 → 狀態 = 信封(模組 / 歷史列 / 範本名一樣)", async () => {
    await s2.setInputFiles("#importData", ENVELOPE);
    const st = await waitFor(async () => { const s = await storage(s2); return s && s.analytics && s.analytics.templateId === TID ? s : null; });
    assert.ok(st, "匯入後沒有 VRN 範本");
    assert.deepEqual(st.modules.map((m) => m.id), envFile.modules.map((m) => m.id));
    assert.equal(st.analytics.history.length, envFile.analytics.history.length);
    assert.equal(st.analytics.templateName, envFile.analytics.templateName);
    return {modules: st.modules.length, history: st.analytics.history.length};
  });
  await check("⑯ SYNCHRONIZER「匯入」歷史 CSV → 歷史列數 = CSV 列數", async () => {
    await s2.setInputFiles("#importData", HISTORY_CSV);
    const st = await waitFor(async () => { const s = await storage(s2); return s && s.analytics.history.length === csvRows ? s : null; });
    assert.ok(st, `歷史列數不是 ${csvRows}`);
    assert.equal(e2.length, 0, e2.join(" | "));
    return {rows: csvRows};
  });
  await ctx2.close();

  // ── 手機寬度 ──────────────────────────────────────────────────
  const ctx3 = await browser.newContext({viewport: {width: 390, height: 844}, locale: "zh-TW", isMobile: true, hasTouch: true});
  const m = await ctx3.newPage();
  const e3 = [];
  watchErrors(m, "mobile", e3);
  await m.goto(pageUrl, {waitUntil: "load"});
  await check("⑰ 手機 390 寬:頁身不橫捲(表格自己捲)· 交接鍵看得到 · 零錯誤", async () => {
    const d = await m.evaluate(() => ({sw: document.documentElement.scrollWidth, iw: window.innerWidth,
      btn: document.getElementById("handoverBtn").getBoundingClientRect().right}));
    assert.ok(d.sw <= 391 && d.iw <= 391, `頁身橫捲 ${d.sw} > ${d.iw}`);
    assert.ok(d.btn <= d.iw + 1, `交接鍵出界 ${d.btn}`);
    assert.equal(e3.length, 0, e3.join(" | "));
    return d;
  });
  await m.screenshot({path: path.join(ARTIFACT_DIR, "vrn_mobile.png"), fullPage: true});
  await ctx3.close();

  // ── 另一個乾淨瀏覽器:跟批735 VRN 模板共存(ENG090 v0101 交接只增不減)──────────────
  const ctx4 = await browser.newContext({viewport: {width: 1440, height: 900}, locale: "zh-TW"});
  const e4 = {vrn: [], sync: [], ui: []};
  const s4 = await ctx4.newPage();
  watchErrors(s4, "sync", e4.sync);
  await s4.goto(syncUrl, {waitUntil: "load"});
  await s4.locator("#templateSelect").waitFor({state: "visible"});
  const rowToggle = (pg, id) => pg.locator(".module-row", {has: pg.locator("small", {hasText: id})}).locator("input.module-toggle");
  await check("⑱ 跟批735 VRN 模板共存:狀態裡有它的 vrn-report-template(你關掉了)和你自建的「我的筆記」→ 交接後兩個原樣留著(啟用 / 釘選 / 順序),VRN 模組接在後面", async () => {
    // 使用者在 SYNCHRONIZER 自建一個模組(走頁上的表單)
    await s4.fill("#moduleId", "my-notes");
    await s4.fill("#moduleName", "我的筆記");
    await s4.click("#addModule");
    await waitFor(async () => ((await storage(s4)) || {modules: []}).modules.some((x) => x.id === "my-notes"));
    // 批735 的模板頁預置段:只增不減加一個 vrn-report-template(同它的 MODULE);SYNCHRONIZER 重新讀本機狀態
    await s4.evaluate(([k, mod]) => { const s = JSON.parse(localStorage.getItem(k)); s.modules.push({...mod, order: s.modules.length + 1});
      localStorage.setItem(k, JSON.stringify(s)); }, [KEY, B735_MODULE]);
    await s4.click("#loadState");
    // 使用者在 SYNCHRONIZER 把它關掉(停用,不是刪)
    await rowToggle(s4, "vrn-report-template").uncheck();
    const before = await waitFor(async () => { const s = await storage(s4); const b = s && s.modules.find((x) => x.id === "vrn-report-template");
      return b && b.enabled === false ? s : null; });
    assert.ok(before, "SYNCHRONIZER 沒記下「停用 vrn-report-template」");
    const keep = before.modules.map((x) => ({...x}));
    const v4 = await ctx4.newPage();
    watchErrors(v4, "vrn", e4.vrn);
    await v4.goto(pageUrl, {waitUntil: "load"});
    await v4.click("#handoverBtn");
    if (await v4.locator("#confirmBar").isVisible()) await v4.click("#confirmBtn");
    const st = await waitFor(async () => { const s = await storage(v4); return s && s.analytics.templateId === TID ? s : null; });
    assert.ok(st, "交接沒寫進去");
    const strip = (x) => { const {order, ...rest} = x; return rest; };
    const ids = st.modules.map((x) => x.id);
    assert.deepEqual(ids.slice(0, keep.length), keep.map((x) => x.id), "原有模組的順序被動了");
    for (const x of keep) assert.deepEqual(strip(st.modules.find((y) => y.id === x.id)), strip(x), `「${x.name}」被改了或被刪了`);
    assert.deepEqual(ids.slice(keep.length), envFile.modules.filter((x) => !x.system).map((x) => x.id), "VRN 模組沒接在後面");
    const row = await waitFor(async () => { const on = await rowToggle(s4, "vrn-report-template").isChecked().catch(() => null);
      const list = await s4.evaluate(() => document.getElementById("moduleList").textContent);
      return on === false && list.includes("財報總覽") && list.includes("我的筆記") ? {on, list} : null; });
    assert.ok(row, "SYNCHRONIZER 模組清單沒畫出三方並存(或 vrn-report-template 的勾被打回來)");
    await s4.screenshot({path: path.join(ARTIFACT_DIR, "synchronizer_coexist.png"), fullPage: false});
    return {kept: keep.length, vrn: ids.length - keep.length, b735: "停用照留", revision: st.sync.revision};
  });
  await check("⑲ 你在 SYNCHRONIZER 關掉的 VRN 模組(上下連結),自動更新(SYNCHRONIZER 是本範本的舊資料)之後還是關的;名稱換新、別人的照舊", async () => {
    const v4 = ctx4.pages().find((p) => p.url() === pageUrl);
    await s4.bringToFront();
    await rowToggle(s4, "vrn-finstat-links").uncheck();
    await waitFor(async () => { const s = await storage(s4); const l = s.modules.find((x) => x.id === "vrn-finstat-links"); return l && l.enabled === false; });
    const rev0 = (await storage(s4)).sync.revision;
    await s4.evaluate(([k]) => { const cur = JSON.parse(localStorage.getItem(k));
      cur.analytics.templateName = cur.analytics.templateName.replace(/資料 (?:[0-9: -]+|—)/, "資料 2020-01-01 00:00:00");
      cur.modules.forEach((x) => { if (x.id === "vrn-finstat-links") x.name = "上下連結(舊名)"; });
      cur.updatedAt = new Date(Date.now() + 1000).toISOString(); localStorage.setItem(k, JSON.stringify(cur)); }, [KEY]);
    if (!hasDataStamp) {
      await sleep(900);
      const kept = await storage(v4);
      const by = Object.fromEntries(kept.modules.map(x => [x.id, x]));
      assert.equal(kept.sync.revision, rev0, "NODATA rewrote dated modules");
      assert.equal(by["vrn-finstat-links"].enabled, false);
      assert.equal(by["vrn-finstat-links"].name, "上下連結(舊名)");
      assert.equal(by["vrn-report-template"].enabled, false);
      assert.ok(by["my-notes"]);
      assert.equal((await lamp(v4)).state, "STALE");
      return {scenario: "NODATA preserves disabled modules and dated state"};
    }
    const up = await waitFor(async () => { const s = await storage(v4); return s.analytics.templateName === stamp && s.sync.revision > rev0 ? s : null; }, 6000);
    assert.ok(up, "舊資料沒被自動更新");
    const by = Object.fromEntries(up.modules.map((x) => [x.id, x]));
    const envLinks = envFile.modules.find((x) => x.id === "vrn-finstat-links");
    assert.equal(by["vrn-finstat-links"].enabled, false, "你關掉的 VRN 模組被自動更新打開了");
    assert.equal(by["vrn-finstat-links"].name, envLinks.name, "VRN 模組名稱(帶燈)沒換新");
    assert.equal(by["vrn-report-template"].enabled, false, "批735 的模組被打開了");
    assert.ok(by["my-notes"], "自建模組不見了");
    return {revision: `${rev0} → ${up.sync.revision}`, links: "停用照留 · 名稱換新", b735: "停用照留"};
  });
  await check("⑳ 中央 UI 從同一份狀態照啟用與否畫側欄:VRN 財報總覽與「我的筆記」在,停用的 vrn-report-template 與「上下連結」不在;全程三頁零錯誤(中央 UI 不放行任何錯誤)", async () => {
    const u4 = await ctx4.newPage();
    watchErrors(u4, "ui", e4.ui);
    await u4.goto(uiUrl, {waitUntil: "load"});
    const nav = await waitFor(async () => { const t = await u4.evaluate(() => (document.getElementById("customModuleNav") || {}).textContent || "");
      return t.includes("VRN 財報總覽") && t.includes("我的筆記") ? t : null; });
    assert.ok(nav, "中央 UI 側欄沒畫出 VRN 模組與自建模組");
    const envLinks = envFile.modules.find((x) => x.id === "vrn-finstat-links");
    assert.ok(!nav.includes("VRN 研報自測成果"), "停用的批735 模組還畫在側欄");
    assert.ok(!nav.includes(envLinks.name), "停用的「上下連結」還畫在側欄");
    await u4.screenshot({path: path.join(ARTIFACT_DIR, "central_ui_coexist.png"), fullPage: false});
    assert.equal(e4.vrn.length, 0, e4.vrn.join(" | "));
    assert.equal(e4.sync.length, 0, e4.sync.join(" | "));
    const other = e4.ui.filter((e) => !KNOWN_PACKAGE_ERRORS.some((rx) => rx.test(e)));
    assert.equal(other.length, 0, other.join(" | "));
    return {nav: nav.replace(/\s+/g, " ").slice(0, 90)};
  });
  await ctx4.close();
  await browser.close();

  const summary = {total: results.length, passed: results.filter((r) => r.passed).length, failed: results.filter((r) => !r.passed).length};
  const meta = {page: PAGE, envelope: ENVELOPE, template: envFile.analytics.templateName, ran: new Date().toISOString(),
    chromium: browserVersion, known_package_defect: "無放行項目；空資料與有資料情境分別驗證"};
  fs.writeFileSync(path.join(ARTIFACT_DIR, "uxtest_vrn_finstatements_report.json"),
    JSON.stringify({...meta, summary, results}, null, 2) + "\n", "utf-8");
  fs.writeFileSync(path.join(ARTIFACT_DIR, "uxtest_vrn_finstatements_report.html"), htmlReport(meta, summary, results), "utf-8");
  console.log(`  [計] ${summary.total} 檢 OK ${summary.passed} · FAIL ${summary.failed} · 截圖與報告 ${ARTIFACT_DIR}`);
  return summary.failed === 0 ? 0 : 1;
}

main().then((rc) => process.exit(rc)).catch((err) => {
  console.error(`[FAIL] ${err && err.stack || err}`);
  process.exit(1);
});
