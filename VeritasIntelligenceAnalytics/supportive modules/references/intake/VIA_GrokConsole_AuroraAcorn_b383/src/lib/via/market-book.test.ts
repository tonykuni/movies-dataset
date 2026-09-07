import assert from "node:assert/strict";
import { test } from "node:test";
import { buildMarketBook, crossValidate, etfFlowSum, gradeDiff } from "./market-book.ts";

test("seven regions and ETF flow signs", () => {
  const book = buildMarketBook({ yfLive: false, akLive: false });
  const regs = new Set(book.filter((r) => r.kind === "index").map((r) => r.region));
  assert.ok(["US", "EU", "JP", "TW", "CN", "IN", "AU"].every((r) => regs.has(r)));
  assert.ok(book.some((r) => r.ticker === "SPY" && (r.aumUsd ?? 0) > 0));
  assert.ok(book.some((r) => r.ticker === "IBIT"));
  assert.ok(book.some((r) => r.ticker === "BDI"));
  assert.ok(book.some((r) => r.id === "TW_10Y"));
  const f = etfFlowSum(book);
  assert.ok(f.aum > 0 && f.inFlow > 0 && f.outFlow < 0);
});

test("same-day cross source within 2% is green", () => {
  const rows = crossValidate();
  assert.ok(rows.length >= 6);
  assert.ok(rows.every((r) => r.light === "ok"));
  assert.equal(gradeDiff(0.03).light, "warn");
  assert.equal(gradeDiff(0.08).light, "bad");
});
