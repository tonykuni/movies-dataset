import assert from "node:assert/strict";
import { test } from "node:test";
import { extractTicker, packBasic, parseFilename, reportCode, validationRisk } from "./vrn.ts";

test("MDL001 filename parse GS-2330", () => {
  const p = parseFilename("GS-2330 台積電_20251130.pdf");
  assert.equal(p.ticker, "2330");
  assert.equal(p.yfinance, "2330.TW");
  assert.equal(p.bloomberg, "2330 TT");
  assert.equal(p.reportDate, "2025-11-30");
  assert.equal(p.broker, "Goldman Sachs");
  assert.equal(p.company, "台積電");
  assert.ok(reportCode(p).startsWith("GS-2330-"));
});

test("does not treat year as ticker", () => {
  assert.equal(extractTicker("review_2024_notes.pdf"), "");
  assert.equal(extractTicker("台積電_2024Q4_法人說明會.pdf"), "2330");
});

test("Q4 maps to year-end date", () => {
  assert.equal(parseFilename("台積電_2024Q4_法人說明會.pdf").reportDate, "2024-12-31");
});

test("FY2024 maps to year-end", () => {
  assert.equal(parseFilename("2330_FY2024_annual_report.pdf").reportDate, "2024-12-31");
});

test("validation risk lights", () => {
  const p = parseFilename("GS-2330 台積電_20251130.pdf");
  assert.equal(validationRisk({ status: "ok", name: p.ticker, ext: "pdf", size: 10 }, p), "GREEN");
  assert.equal(validationRisk({ status: "ok", name: "scan.pdf", ext: "pdf", size: 10 }, parseFilename("scan.pdf")), "YELLOW");
  assert.equal(validationRisk({ status: "bad", name: "empty_stub.tmp", ext: "tmp", size: 0 }, parseFilename("empty_stub.tmp")), "RED");
});

test("BASIC INFO ticker is 4-digit not yfinance", () => {
  const p = parseFilename("GS-2330 台積電_20251130.pdf");
  const b = packBasic(
    {
      id: "1",
      name: "GS-2330 台積電_20251130.pdf",
      ext: "pdf",
      size: 100,
      origin: "folder",
      skipDup: false,
      status: "ok",
      lastModified: 0,
      fingerprint: "pdf:100",
      steps: {},
      stuckStep: null,
      stuckDetail: null,
    },
    p,
    "ok",
  );
  assert.equal(b.ticker, "2330");
  assert.equal(b.market, "TWSE");
  assert.equal(b.yfinanceTicker, "2330.TW");
  assert.equal(b.yfinanceTwo, "—");
});
