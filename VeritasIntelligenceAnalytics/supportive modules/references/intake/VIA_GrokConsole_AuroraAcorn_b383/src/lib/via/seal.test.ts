import assert from "node:assert/strict";
import { test } from "node:test";
import { FOLDER_SEEDS, cacheFredRows } from "./catalog.ts";
import { sealGoLive, sealParquet, sealVdf, sealVrn, sealConsole, sealEng075, sealGlss } from "./seal.ts";
import { packFinance, packSummary, parseFilename } from "./vrn.ts";

test("VDF cache seals complete with 8+ categories and no missing values", () => {
  const s = sealVdf(cacheFredRows());
  assert.equal(s.light, "ok");
  assert.match(s.note, /完工/);
});

test("ENG047 labor/CPI detail is in the cache lake", () => {
  const rows = cacheFredRows();
  const u6 = rows.find((r) => r.seriesId === "U6RATE");
  assert.equal(u6?.lastValue != null, true);
  assert.equal(u6?.source, "VDF_CACHE");
  const ids = new Set(rows.map((r) => r.seriesId));
  for (const id of ["U6RATE", "CCSA", "UEMPMEAN", "CPIENGSL", "CORESTICKM159SFRBATL"]) {
    assert.equal(ids.has(id), true, id);
    assert.equal(rows.find((r) => r.seriesId === id)?.lastValue != null, true, id);
  }
});

test("xlsx routes income to IS and cashflow to CF", () => {
  const inc = FOLDER_SEEDS.find((f) => f.name.startsWith("income_"))!;
  const cf = FOLDER_SEEDS.find((f) => f.name.startsWith("cashflow_"))!;
  const incRows = packFinance(inc, parseFilename(inc.name), "ok");
  const cfRows = packFinance(cf, parseFilename(cf.name), "ok");
  assert.ok(incRows.every((r) => r.category === "IS" || r.category === "RATIO"));
  assert.ok(cfRows.every((r) => r.category === "CF"));
  assert.ok(cfRows.some((r) => r.dataName === "fcf"));
});

test("annual report FY date and full IS/BS/CF", () => {
  const f = FOLDER_SEEDS.find((x) => x.name.includes("annual"))!;
  const p = parseFilename(f.name);
  assert.equal(p.reportDate, "2024-12-31");
  const fin = packFinance(f, p, "ok");
  assert.ok(fin.some((r) => r.category === "IS"));
  assert.ok(fin.some((r) => r.category === "BS"));
  assert.ok(fin.some((r) => r.category === "CF"));
});

test("VRN seal green when S04 fail stays out of TAB2 and statements present", () => {
  const files = FOLDER_SEEDS.map((f) => ({ ...f, status: f.size === 0 ? ("bad" as const) : ("ok" as const), stuckStep: f.size === 0 ? "S04" : null }));
  const pass = files.filter((f) => f.status !== "bad" && !(f.skipDup && f.dupOf));
  const basics = pass.map((f) => ({
    fileId: f.id,
    fileName: f.name,
    reportType: "x",
    ticker: parseFilename(f.name).ticker,
    market: parseFilename(f.name).market,
    yfinanceTicker: parseFilename(f.name).yfinance,
    yfinanceTwo: parseFilename(f.name).yfinanceTwo,
    bloombergTicker: parseFilename(f.name).bloomberg,
    tickerKind: parseFilename(f.name).tickerKind,
    companyName: "x",
    broker: "x",
    brokerAbbr: "x",
    reportDate: parseFilename(f.name).reportDate || "—",
    reportCode: "x",
    language: "zh-Hant",
    period: "2024",
    pages: 1,
    issuer: "x",
    rating: "—",
    ratingCat: "—",
    validationStatus: parseFilename(f.name).ticker && parseFilename(f.name).reportDate ? "PHASE2_OK" : "BASICINFO_TEMP_PREVIEW",
    validationRisk: (parseFilename(f.name).ticker && parseFilename(f.name).reportDate ? "GREEN" : "YELLOW") as "GREEN" | "YELLOW",
    status: "ok" as const,
  }));
  const summaries = pass.flatMap((f) => packSummary(f, parseFilename(f.name)));
  const finances = pass.flatMap((f) => packFinance(f, parseFilename(f.name), "ok"));
  const s = sealVrn(files, basics, summaries, finances);
  assert.equal(s.light, "ok", s.note);
});

test("parquet mismatch fails VDF seal; go-live needs VDF+VRN+PARQ", () => {
  const rows = cacheFredRows();
  const parqIn = {
    parquetPages: 2,
    parquetRoundtrip: false,
    parquetReadPages: 0,
    parquetSkipPages: 0,
    parquetTokenRatio: 0.2,
  };
  assert.equal(sealVdf(rows, parqIn).light, "bad");
  const okParq = { ...parqIn, parquetRoundtrip: true, parquetReadPages: 2 };
  assert.equal(sealVdf(rows, okParq).light, "ok");
  const live = sealGoLive([
    sealVdf(rows, okParq),
    { id: "VRN", name: "VRN", light: "ok", note: "完工" },
    sealParquet(okParq),
  ]);
  assert.equal(live.light, "ok");
  assert.match(live.note, /實測通過/);
  assert.match(live.note, /DCT01–20 不動/);
});

test("console ENG075 GLSS seal as complete cache contracts", () => {
  const cgc = sealConsole(40);
  assert.equal(cgc.light, "ok");
  const e075 = sealEng075(41, "2026-07");
  assert.equal(e075.light, "ok");
  const glss = sealGlss(7);
  assert.equal(glss.light, "ok");
  const live = sealGoLive([
    { id: "VDF", name: "VDF", light: "ok", note: "完工" },
    { id: "VRN", name: "VRN", light: "ok", note: "完工" },
    { id: "PARQ", name: "PARQ", light: "ok", note: "PAR1" },
    cgc,
  ]);
  assert.equal(live.light, "ok");
  assert.match(live.note, /Console/);
});
