import assert from "node:assert/strict";
import { test } from "node:test";
import {
  REV_LIVE_ENABLED,
  cacheRevRows,
  canFetchRev,
  groupAnalysis,
  latestCompleteMonth,
  latestSnapshot,
  mopsMonthUrl,
  planMonthFiles,
  revContract,
} from "./tw-revenue.ts";

const asof = new Date("2026-09-05T08:00:00Z");

test("LIVE stays off; NET does not fetch", () => {
  assert.equal(REV_LIVE_ENABLED, false);
  const g = canFetchRev({ confirmNet: true });
  assert.equal(g.ok, false);
  if (!g.ok) assert.equal(g.mode, "CACHE");
});

test("Sep 5 2026 latest complete month is 2026-07", () => {
  const e = latestCompleteMonth(asof);
  assert.equal(e.year, 2026);
  assert.equal(e.month, 7);
});

test("month files are sii+otc not ticker loops", () => {
  const files = planMonthFiles("2024-01", asof);
  assert.equal(files.length % 2, 0);
  assert.ok(files.length >= 24);
  assert.ok(files.every((f) => f.url.startsWith("https://mops.twse.com.tw/nas/t21/")));
  assert.equal(mopsMonthUrl(2024, 1, "sii"), "https://mops.twse.com.tw/nas/t21/sii/t21sc03_2024_1_0.html");
  assert.ok(files.some((f) => f.market === "otc"));
});

test("CACHE analysis covers leaders from 2024 with YoY after 12 months", () => {
  const rows = cacheRevRows(asof);
  const snap = latestSnapshot(rows, asof);
  assert.ok(snap.length >= 30);
  assert.ok(snap.every((r) => r.year === 2026 && r.month === 7 && r.source === "CACHE"));
  assert.ok(snap.every((r) => r.yoy != null));
  const tsmc = snap.find((r) => r.ticker === "2330");
  assert.ok(tsmc);
  const groups = groupAnalysis(rows, asof);
  assert.ok(groups.some((g) => g.group === "半導體"));
  const c = revContract(asof);
  assert.equal(c.latest, "2026-07");
  assert.match(c.listedNote, /sii\+otc/);
});
