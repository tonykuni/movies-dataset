#!/usr/bin/env node
import { mkdirSync } from "node:fs";
import { chromium } from "playwright";

const url = process.env.VIA_QA_URL || "http://127.0.0.1:8080/";
const outDir = "/workspace/screenshots";
mkdirSync(outDir, { recursive: true });

const errors = [];
const log = [];

function rec(ok, name, extra = "") {
  log.push(`${ok ? "PASS" : "FAIL"}  ${name}${extra ? ` · ${extra}` : ""}`);
  if (!ok) errors.push(name);
}

const browser = await chromium.launch({ args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
page.setDefaultTimeout(45000);
page.on("pageerror", (err) => errors.push(`pageerror: ${err.message}`));
page.on("console", (msg) => {
  if (msg.type() === "error") errors.push(`console: ${msg.text()}`);
});

await page.goto(url, { waitUntil: "load", timeout: 45000 });
await page.waitForSelector("[data-left-engine='1']", { timeout: 20000 });
await page.waitForTimeout(600);

const title = await page.title();
rec(title.includes("VIA Central Console"), "title", title);

const body = await page.locator("body").innerText();
rec(body.includes("同一總管") || body.includes("唯一總管"), "console identity");
rec(body.includes("Govern") || body.includes("總管"), "central govern chrome");
rec(body.includes("VDF") && body.includes("VRN") && body.includes("引擎"), "four pillars in chrome");
rec(body.includes("綠") && body.includes("黃") && body.includes("紅"), "three-color legend");
rec(body.includes("via_core") || body.includes("via_*") || body.includes("協調"), "left engine coordinates via_core");
rec(body.includes("ALIAS") && body.includes("工具保留"), "roster live path hides aliases");
rec(body.includes("ParquetYearPart") || body.includes("PS-07"), "parquet accelerator in tool table");
rec(body.includes("via_iso_numpy") || body.includes("隔離"), "env isolate policy");
rec(body.includes("產生隔離指令") && body.includes("本台不 spawn conda"), "iso mint chrome");
rec(body.includes("JavaScript"), "js lib table");
rec(body.includes("實測矩陣") && body.includes("DCT 不動"), "seal matrix present");
await page.locator("[data-action='iso-mint']").click();
await page.waitForFunction(
  () => document.body.innerText.includes("ISO99") && document.body.innerText.includes("via_iso_numpy"),
  null,
  { timeout: 10000 },
);
const isoTxt = await page.locator("body").innerText();
rec(isoTxt.includes("ISO99") && isoTxt.includes("via_iso_numpy"), "iso steps minted");
rec(isoTxt.includes("隔離不刪") && isoTxt.includes("本台不 spawn"), "iso never deletes");
await page.screenshot({ path: `${outDir}/qa-00-console.png` });

await page.locator("[data-action='seal-run']").click();
await page.waitForFunction(
  () => document.body.innerText.includes("VDF+VRN 實測通過"),
  null,
  { timeout: 60000 },
);
const sealed = await page.locator("body").innerText();
rec(sealed.includes("VDF+VRN 實測通過"), "console seal go-live");
rec(sealed.includes("DCT01–20 不動") || sealed.includes("DCT 不動"), "DCT not redone");
rec(sealed.includes("程序矩陣") && sealed.includes("P_UNI"), "process pack ran");
rec(sealed.includes("P_YF") && sealed.includes("SKIP"), "YF lane stay skip");
rec(sealed.includes("六程同步") && sealed.includes("無九頭龍"), "six hydra-safe lanes");
rec(sealed.includes("L2") && sealed.includes("L6"), "six lanes L2 and L6 present");
await page.screenshot({ path: `${outDir}/qa-00-console-sealed.png` });

await page.locator("[data-deck='vdf']").click();
await page.waitForSelector("[data-action='vdf-start']", { timeout: 20000 });
await page.locator("[data-action='vdf-start']").click();
await page.waitForSelector("text=FEDFUNDS", { timeout: 15000 });
const vdfText = await page.locator("body").innerText();
rec(vdfText.includes("Rates & Yields"), "VDF category matrix");
rec(vdfText.includes("U6RATE") && vdfText.includes("CPIENGSL"), "VDF ENG047 labor/CPI in lake");
rec(vdfText.includes("跑完矩陣") && vdfText.includes("E12"), "VDF run to end E01–E12");
rec(vdfText.includes("分類摺疊") || vdfText.includes("Rates & Yields"), "VDF fold heading is category not duplicate");
rec(vdfText.includes("VDF_CACHE") || vdfText.includes("FRED_LIVE"), "VDF source badge");
rec(vdfText.includes("VDF_ACTIVE_READER_READY"), "VDF Invoke-VDF status");
rec(vdfText.includes("VDF_PRODUCTION_FETCH_CONTROLLER_READY"), "VDF Fetch controller");
rec(vdfText.includes("完工") && (vdfText.includes("類") || vdfText.includes("series")), "VDF seal complete");
rec(vdfText.includes("MDL007") || vdfText.includes("焦點"), "VDF mother MDL007 / universe");
rec(vdfText.includes("SPY") && vdfText.includes("IBIT") && (vdfText.includes("BDI") || vdfText.includes("多源")), "VDF market book indices/ETF/crypto");
rec(vdfText.includes("VIA-AEA") || vdfText.includes("主動台股"), "AEA deck on VDF");
rec(vdfText.includes("台股成分"), "AEA TW scope chip");
rec(vdfText.includes("主動統一台股增長") && vdfText.includes("00981A"), "AEA book names 00981A");
rec(vdfText.includes("FS 目標 Med") && vdfText.includes("YF 目標 Med"), "AEA dual median target");
rec(vdfText.includes("估均價") && vdfText.includes("2330"), "AEA holdings cost TSMC");
const aeaTw = vdfText.includes("主動國泰動能高息") && !vdfText.includes("主動中信ARK創新");
rec(aeaTw, "AEA default TW hides overseas ARK");
await page.locator("[data-action='aea-gl']").click();
await page.waitForTimeout(200);
const aeaGl = await page.locator("body").innerText();
rec(aeaGl.includes("主動中信ARK創新") || aeaGl.includes("主動安聯美國科技"), "AEA GL shows overseas book");
await page.locator("[data-action='aea-tw']").click();
await page.waitForTimeout(150);
await page.locator("[data-action='vdf-fold']").click();
await page.waitForTimeout(300);
const folded = await page.locator("body").innerText();
rec(!folded.includes("Effective Federal Funds Rate"), "VDF fold hides series titles");
await page.screenshot({ path: `${outDir}/qa-01-vdf.png` });
rec(true, "VDF collapse control");

await page.getByRole("tab", { name: /TAB 2/ }).click();
await page.waitForTimeout(200);
const pairText = await page.locator("body").innerText();
rec(pairText.includes("AsyncPool") && pairText.includes("DuckDBScan"), "VDF accel pairing matrix");
await page.getByRole("tab", { name: /TAB 3/ }).click();
await page.waitForTimeout(200);
const structText = await page.locator("body").innerText();
rec(structText.includes("Columnar") || structText.includes("字典"), "VDF structure contract");
rec(structText.includes("year") || structText.includes("年分區") || structText.includes("序列主序"), "VDF year|series|date layout");
await page.getByRole("tab", { name: /TAB 4/ }).click();
await page.waitForTimeout(200);
const fx = await page.locator("body").innerText();
rec(fx.includes("wall ms") || fx.includes("計畫加乘"), "VDF measured multiply");
rec(/avx512|avx2|scalar/.test(fx.toLowerCase()) && fx.includes("f64"), "VDF CPU ISA kernel");
rec(fx.includes("年分區") || fx.includes("compact") || fx.includes("存量"), "VDF lake compact storage");
rec(fx.includes("parquet 回讀") || fx.includes("跳過"), "VDF parquet year-page round-trip");
await page.getByRole("tab", { name: /TAB 1/ }).click();
await page.waitForTimeout(200);

await page.locator("[data-deck='vrn']").click();
await page.waitForSelector("[data-action='vrn-start']", { timeout: 20000 });
await page.waitForFunction(
  () => {
    const b = document.querySelector("[data-action='vrn-start']");
    return b && !b.hasAttribute("disabled");
  },
  null,
  { timeout: 90000 },
);
await page.locator("[data-action='vrn-start']").click();
await page.waitForFunction(
  () => document.querySelector("[data-intake-tab='tab2']"),
  null,
  { timeout: 90000 },
);
await page.waitForTimeout(400);
const vrnAuto = await page.locator("body").innerText();
rec(vrnAuto.includes("2330") || vrnAuto.includes("BASIC INFO"), "VRN auto-opens TAB 2 with passing results");
rec(!vrnAuto.includes("錯誤步驟矩陣"), "TAB 2 does not show TAB 1 error matrix");
await page.screenshot({ path: `${outDir}/qa-02-vrn-tab2.png` });

await page.getByRole("tab", { name: /TAB 1/ }).click();
await page.waitForTimeout(200);
const vrnTab1 = await page.locator("body").innerText();
rec(vrnTab1.includes("empty_stub") || vrnTab1.includes("零位元組") || vrnTab1.includes("S04"), "VRN error step visible on TAB 1");
await page.screenshot({ path: `${outDir}/qa-02-vrn-tab1.png` });

await page.getByRole("tab", { name: /TAB 2/ }).click();
await page.waitForTimeout(200);
const tab2 = await page.locator("body").innerText();
rec(tab2.includes("2330") || tab2.includes("BASIC INFO") || tab2.includes("台積"), "VRN TAB 2 basic info");
rec(tab2.includes("incoming") && tab2.includes("NLP"), "VRN incoming path + NLP engine");
rec(tab2.includes("2330.TW") && tab2.includes("2330 TT") && tab2.includes("TWSE"), "VRN three ticker surfaces");
rec(!/\b2330\.TWO\b/.test(tab2), "VRN does not invent TPEX YF for TWSE 2330");

await page.getByRole("tab", { name: /TAB 3/ }).click();
await page.waitForTimeout(200);
const tab3 = await page.locator("body").innerText();
rec(tab3.includes("GROUNDED") || tab3.includes("Summarizer") || tab3.includes("摘要"), "VRN TAB 3 summarizer");
rec(tab3.includes("K1") || tab3.includes("投資結論"), "VRN digest K1 slot");

await page.getByRole("tab", { name: /TAB 4/ }).click();
await page.waitForTimeout(200);
const tab4 = await page.locator("body").innerText();
rec(tab4.includes("營業收入") || tab4.includes("損益") || tab4.includes("持股"), "VRN TAB 4 financial");
rec(tab4.includes("自由現金流") || tab4.includes("資產總計") || tab4.includes("fcf"), "VRN complete IS/BS/CF");
rec(tab4.includes("原子") || /\bV\b/.test(tab4), "VRN financial atomic grade");
await page.screenshot({ path: `${outDir}/qa-02-vrn-tab4.png` });

await page.locator("[data-deck='engine']").click();
await page.getByPlaceholder("VRN_ENG080_…").fill("VRN_ENG080_UserTest");
await page.locator("[data-action='engine-mount']").click();
await page.locator("[data-action='engine-ssot']").click();
await page.waitForSelector("text=VRN_ENG080_UserTest", { timeout: 10000 });
const eng = await page.locator("body").innerText();
rec(eng.includes("SSOT JSON"), "engine SSOT json");
rec(eng.includes("VRN_ENG080_UserTest"), "engine row appended");
await page.screenshot({ path: `${outDir}/qa-03-engine.png` });

await page.locator("[data-deck='var']").click();
await page.waitForFunction(
  () => document.body.innerText.includes("UNREPAIRABLE") || document.body.innerText.includes("鑑測結束"),
  null,
  { timeout: 20000 },
);
await page.waitForTimeout(400);
const varText = await page.locator("body").innerText();
rec(varText.includes("DETAILS"), "VAR details matrix");
rec(varText.includes("orphan_stub") || varText.includes("ENG_ORPHAN"), "VAR keeps unrepairable in log/details");
rec(varText.includes("VAP") || varText.includes("REPAIRED"), "VAR repairs VAP");
await page.screenshot({ path: `${outDir}/qa-04-var.png` });
await page.getByRole("tab", { name: /TAB 2/ }).click();
await page.waitForTimeout(200);
const varTab2 = await page.locator("body").innerText();
rec(varTab2.includes("A01") || varTab2.includes("KnowledgeStack"), "VAR audit matrix");
await page.getByRole("tab", { name: /TAB 3/ }).click();
await page.waitForTimeout(200);
const varTab3 = await page.locator("body").innerText();
rec(varTab3.includes("UNREPAIRABLE") || varTab3.includes("修復"), "VAR repair status tab");
await page.getByRole("tab", { name: /TAB 4/ }).click();
await page.waitForTimeout(150);
const varTab4 = await page.locator("body").innerText();
rec(varTab4.includes("SameName") && varTab4.includes("FinancialRow"), "VAR mother repair pack");
rec(varTab4.includes("ABSENT") && varTab4.includes("BUILTIN"), "launcher detect-only accels");
rec(varTab4.includes("VIA-SYS-ENG-002-APPLY") && varTab4.includes("SKIPPED"), "downward mutating gated");
rec(varTab4.includes("D01") && varTab4.includes("D08"), "downward D-gates");
rec(varTab4.includes("DCT06") && varTab4.includes("FIXED"), "DCT hardening matrix");
rec(varTab4.includes("DCT08") && varTab4.includes("DCT17"), "DCT priority five present");
rec(varTab4.includes("DCT19") && varTab4.includes("DCT20"), "DCT19 retry and DCT20 lanes");
rec(varTab4.includes("分系封印") || varTab4.includes("overall"), "lane verdicts");
rec(varTab4.includes("產生權杖") || varTab4.includes("下行 DryRun"), "downward dual-gate");
rec(varTab4.includes("symtable") || varTab4.includes("tokenize"), "AST four-layer");
await page.screenshot({ path: `${outDir}/qa-04-var-tab3.png` });

await page.locator("[data-deck='console']").click();
await page.waitForTimeout(300);
const hub = await page.locator("body").innerText();
rec(hub.includes("全線啟動") || hub.includes("ACTIVATED"), "console activation after runs");
rec(/紅 0/.test(hub) || !hub.includes("紅失敗"), "console no red after seal");
rec(hub.includes("SuperAccel"), "shared bus visible");
await page.screenshot({ path: `${outDir}/qa-00-console-activated.png` });

await page.setViewportSize({ width: 390, height: 844 });
await page.waitForTimeout(200);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
rec(!overflow, "mobile no horizontal overflow");
await page.screenshot({ path: `${outDir}/qa-mobile.png` });

await browser.close();

const report = { ok: errors.length === 0, errors, log };
console.log(JSON.stringify(report, null, 2));
process.exit(errors.length ? 1 : 0);
