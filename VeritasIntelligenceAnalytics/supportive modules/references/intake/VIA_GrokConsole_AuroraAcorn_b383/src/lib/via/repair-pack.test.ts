import assert from "node:assert/strict";
import { test } from "node:test";
import { auditFinRows, runRepairPack, versionGuard } from "./repair-pack.ts";
import type { FinRow } from "./types.ts";

test("v0110 beats v0100", () => {
  assert.equal(versionGuard("VIA_SameNameConsolidator_v0110.ps1", "VIA_SameNameConsolidator_v0100.ps1"), "VIA_SameNameConsolidator_v0110.ps1");
});

test("financial row auditor drops NaN and dups higher confidence", () => {
  const rows: FinRow[] = [
    { fileId: "a", fileName: "x", category: "IS", statement: "損益", item: "營收", dataName: "revenue", period: "2024", value: Number.NaN, unit: "TWD", confidence: 0.2, source: "x", status: "ok" },
    { fileId: "a", fileName: "x", category: "IS", statement: "損益", item: "營收", dataName: "revenue", period: "2024", value: 1, unit: "TWD", confidence: 0.4, source: "x", status: "ok" },
    { fileId: "a", fileName: "x", category: "IS", statement: "損益", item: "營收", dataName: "revenue", period: "2024", value: 2, unit: "TWD", confidence: 0.9, source: "x", status: "ok" },
  ];
  const r = auditFinRows(rows);
  assert.equal(r.rows.length, 1);
  assert.equal(r.rows[0]?.value, 2);
  assert.equal(r.dropped, 1);
  assert.equal(r.dups, 1);
});

test("repair pack drops unknown orphan stub and keeps 17 tools", () => {
  const p = runRepairPack({
    files: [],
    engines: [{ id: "ENG_ORPHAN", name: "orphan", kind: "ENG", path: "", hash: "", accel: false, net: false, nlp: false, ssot: false, status: "bad", note: "x" }],
    finances: [],
  });
  assert.equal(p.tools.length, 17);
  assert.equal(p.engines.length, 0);
});
