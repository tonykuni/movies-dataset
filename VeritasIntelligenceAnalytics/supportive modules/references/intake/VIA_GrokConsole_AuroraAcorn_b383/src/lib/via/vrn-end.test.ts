import assert from "node:assert/strict";
import { test } from "node:test";
import { FOLDER_SEEDS } from "./catalog.ts";
import { packFinance, packSummary, parseFilename } from "./vrn.ts";
import { runVrnToEnd } from "./vrn-end.ts";

test("VRN run-to-end finishes at R11 close-out", () => {
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
      ticker: p.ticker,
      market: p.market,
      yfinanceTicker: p.yfinance,
      yfinanceTwo: p.yfinanceTwo,
      bloombergTicker: p.bloomberg,
      tickerKind: p.tickerKind,
      companyName: "x",
      broker: "x",
      brokerAbbr: "x",
      reportDate: p.reportDate || "—",
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
  const out = runVrnToEnd({ files, basics, summaries, finances, confirmNlp: false });
  assert.equal(out.fail, 0);
  assert.equal(out.steps.at(-1)?.id, "R11");
  assert.equal(out.steps.find((s) => s.id === "R11")?.light, "ok");
  assert.equal(out.steps.find((s) => s.id === "R04")?.light, "ok");
  assert.equal(out.steps.find((s) => s.id === "R09")?.result, "SKIP");
  assert.equal(out.seal.light, "ok");
});
