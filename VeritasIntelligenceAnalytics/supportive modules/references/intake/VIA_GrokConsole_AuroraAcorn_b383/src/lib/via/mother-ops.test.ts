import assert from "node:assert/strict";
import { test } from "node:test";
import { auditFinancialRows, gradeRow } from "./fin-audit.ts";
import { CAPABILITIES, filePriority, LAUNCH_ACCELS, topoLevels } from "./mother-ops.ts";
import { normalizeTemporal } from "./temporal.ts";
import { resolveTwTicker } from "./tw-ticker.ts";
import type { FinRow } from "./types.ts";

test("C9 民國與季別正規化", () => {
  assert.equal(normalizeTemporal("民國113年8月1日")?.normalized, "2024-08-01");
  assert.equal(normalizeTemporal("1Q24")?.normalized, "2024-Q1");
  assert.equal(normalizeTemporal("4Q26F")?.normalized, "2026-Q4F");
  assert.equal(normalizeTemporal("1130801")?.normalized, "2024-08-01");
  assert.equal(normalizeTemporal("FY24")?.normalized, "FY2024");
  assert.equal(normalizeTemporal("隨便") , null);
});

test("F08 禁止假綠燈：無期間不得 ok", () => {
  const row: FinRow = { fileId: "a", fileName: "x", category: "IS", statement: "損益", item: "營收", dataName: "revenue", period: "", value: 1, unit: "TWD", confidence: 1, source: "x", status: "ok" };
  const g = gradeRow(row);
  assert.equal(g.grade, "P");
  assert.notEqual(g.status, "ok");
});

test("原子列 2024 + 單值 = V", () => {
  const row: FinRow = { fileId: "a", fileName: "x", category: "IS", statement: "損益", item: "營收", dataName: "revenue", period: "2024", value: 1, unit: "TWD", confidence: 1, source: "x", status: "ok" };
  assert.equal(gradeRow(row).grade, "V");
  const a = auditFinancialRows([row]);
  assert.equal(a.verdict, "GREEN");
  assert.equal(a.fakeGreen, 0);
});

test("CJK 後綴仍能抽 2330.TW", () => {
  const hit = resolveTwTicker("2330.TW今日收盤");
  assert.equal(hit?.core, "2330");
  assert.equal(hit?.yfinance, "2330.TW");
});

test("啟動器不安裝：ABSENT 外加 BUILTIN 20 支", () => {
  assert.equal(LAUNCH_ACCELS.length, 20);
  assert.equal(LAUNCH_ACCELS.filter((a) => a.state === "ABSENT").length, 11);
  assert.equal(LAUNCH_ACCELS.filter((a) => a.state === "BUILTIN").length, 9);
});

test("下行拓撲變更類 SKIPPED 且無循環", () => {
  const rows = topoLevels();
  assert.equal(rows.length, CAPABILITIES.length);
  assert.ok(rows.some((r) => r.state === "SKIPPED" && r.urn.includes("APPLY")));
  assert.equal(filePriority("id_rsa", "key", 12).priority, "SKIP");
  assert.equal(filePriority("urn_registry.json", "json", 99).priority, "P0-GOVERNANCE");
});
