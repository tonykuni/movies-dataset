import assert from "node:assert/strict";
import { test } from "node:test";
import { parseFilename } from "./vrn.ts";
import {
  TW_CORE_RE,
  YEAR_BAND_REAL,
  disambiguateYear,
  expandTw,
  extractTwCore,
  resolveTwTicker,
  sameCompany,
  tickerFilenameQc,
  tokenizeFilename,
  triCodeCheck,
} from "./tw-ticker.ts";

test("three forms: native / yfinance / bloomberg stay first-digit-nonzero", () => {
  const a = resolveTwTicker("2330");
  const b = resolveTwTicker("2330.TW");
  const c = resolveTwTicker("2330 TT");
  assert.equal(a?.core, "2330");
  assert.equal(b?.yfinance, "2330.TW");
  assert.equal(c?.bloomberg, "2330 TT");
  assert.equal(expandTw("2330")?.yfinance, "2330.TW");
  assert.equal(resolveTwTicker("0330"), null);
  assert.equal(TW_CORE_RE.test("0050"), false);
});

test("year-band real tickers not killed; date filenames stay empty", () => {
  assert.equal(resolveTwTicker("大成鋼-2027-個股.pdf")?.core, "2027");
  assert.equal(expandTw("2027")?.yfinance, "2027.TW");
  assert.equal(YEAR_BAND_REAL["2027"], "大成鋼");
  assert.equal(resolveTwTicker("review_2024_notes.pdf"), null);
  assert.equal(parseFilename("review_2024_notes.pdf").ticker, "");
  assert.equal(parseFilename("大成鋼-2027-個股.pdf").ticker, "2027");
  assert.equal(triCodeCheck("2330", "2330", "2330.TW", "2330 TT").verdict, "PASS");
});

test("FY date cue keeps the equity ticker; year lookahead is not in regex", () => {
  assert.equal(resolveTwTicker("2454_FY2024_annual_report.pdf")?.core, "2454");
  assert.equal(extractTwCore("台積電_2024Q4_法人說明會.pdf"), "");
  assert.equal(parseFilename("台積電_2024Q4_法人說明會.pdf").ticker, "2330");
  assert.equal(/202\[1-9\]/.test(String(TW_CORE_RE)), false);
  assert.equal(disambiguateYear("2027", "大成鋼 個股").verdict, "TICKER");
  assert.equal(disambiguateYear("2024", "review notes").verdict, "AMBIGUOUS");
  assert.equal(disambiguateYear("2024", "FY2024 年報").verdict, "YEAR");
});

test("tokenizer splits CJK / latin / digits; tri-code fail on suffix mismatch", () => {
  const toks = tokenizeFilename("台積電2330_FY2024.pdf");
  assert.ok(toks.some((t) => t.kind === "CJK" && t.tok.includes("台積")));
  assert.ok(toks.some((t) => t.kind === "DIGIT" && t.tok === "2330"));
  assert.equal(sameCompany("2330.TW", "2330 TT"), true);
  assert.equal(triCodeCheck("2330", "2330", "2454.TW", "2330 TT").verdict, "FAIL");
  const qc = tickerFilenameQc();
  assert.equal(qc.filter((r) => r.light === "bad").length, 0);
});

test("wrong board suffix recovers from official list", () => {
  const hit = resolveTwTicker("2330.TWO");
  assert.equal(hit?.yfinance, "2330.TW");
  assert.equal(hit?.recovered, true);
  const tpex = resolveTwTicker("5347.TW");
  assert.equal(tpex?.yfinance, "5347.TWO");
  assert.equal(tpex?.recovered, true);
});
