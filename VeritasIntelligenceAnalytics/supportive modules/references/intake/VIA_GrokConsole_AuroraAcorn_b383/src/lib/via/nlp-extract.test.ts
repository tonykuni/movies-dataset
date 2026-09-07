import assert from "node:assert/strict";
import { test } from "node:test";
import { FOLDER_SEEDS } from "./catalog.ts";
import { incomingText } from "./incoming.ts";
import { extractFacts, parseNum } from "./nlp-extract.ts";
import { packFinance, packSummary, parseFilename } from "./vrn.ts";
import { sealVrn } from "./seal.ts";

test("parseNum takes one number only; two numbers abstain", () => {
  assert.equal(parseNum("2,894.3"), 2894.3);
  assert.equal(parseNum("營業收入 2894.3"), 2894.3);
  assert.equal(parseNum("100 110"), null);
  assert.equal(parseNum("—"), null);
});

test("NLP 1.5 extracts IS/BS/CF from GS-2330 incoming fixture", () => {
  const name = "GS-2330 台積電_20251130.pdf";
  const facts = extractFacts(incomingText(name));
  assert.ok(facts.some((f) => f.stmt === "IS" && f.zh.includes("營業收入")));
  assert.ok(facts.some((f) => f.stmt === "BS"));
  assert.ok(facts.some((f) => f.stmt === "CF"));
});

test("incoming folder seeds seal green with NLP facts", () => {
  const files = FOLDER_SEEDS.map((f) => ({
    ...f,
    status: f.size === 0 ? ("bad" as const) : ("ok" as const),
    stuckStep: f.size === 0 ? "S04" : null,
  }));
  const pass = files.filter((f) => f.status !== "bad" && !(f.skipDup && f.dupOf));
  const basics = pass.map((f) => {
    const p = parseFilename(f.name);
    return {
      fileId: f.id,
      fileName: f.name,
      reportType: "x",
      ticker: p.ticker || "—",
      market: p.market,
      yfinanceTicker: p.yfinance,
      yfinanceTwo: p.yfinanceTwo,
      bloombergTicker: p.bloomberg,
      tickerKind: p.tickerKind,
      companyName: p.company,
      broker: p.broker,
      brokerAbbr: p.brokerAbbr,
      reportDate: p.reportDate,
      reportCode: "x",
      language: "zh-Hant",
      period: "2024",
      pages: 1,
      issuer: "x",
      rating: "—",
      ratingCat: "—",
      validationStatus: p.ticker && p.reportDate ? "PHASE2_OK" : "BASICINFO_TEMP_PREVIEW",
      validationRisk: (p.ticker && p.reportDate ? "GREEN" : "YELLOW") as "GREEN" | "YELLOW",
      status: "ok" as const,
    };
  });
  const summaries = pass.flatMap((f) => packSummary(f, parseFilename(f.name)));
  const finances = pass.flatMap((f) => packFinance(f, parseFilename(f.name), "ok"));
  const seal = sealVrn(files, basics, summaries, finances);
  assert.equal(seal.light, "ok", seal.note);
});
