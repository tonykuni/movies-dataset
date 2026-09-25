import assert from "node:assert/strict";
import { test } from "node:test";
import { cacheFredRows } from "./catalog.ts";
import { runVdfToEnd } from "./vdf-end.ts";
import type { FetchMetrics } from "./types.ts";

const metrics: FetchMetrics = {
  concurrency: 8,
  series: 98,
  lakeRows: 200,
  chunks: 4,
  skipped: 1,
  scanned: 3,
  cacheHits: 98,
  encodeMs: 1,
  queryMs: 1,
  fetchMs: 0,
  wallMs: 12,
  planFactor: 4,
  active: 20,
  conflicts: 0,
  pipeline: true,
  skipRatio: 0.25,
  isa: "avx2",
  f64Width: 4,
  i32Width: 8,
  align: 32,
  kernel: "avx2",
  downclock: false,
  phys: 8,
  width: 4,
  compactBytes: 400,
  rowBytes: 4000,
  storeRatio: 0.1,
  partitions: 2,
  parquetBytes: 80,
  parquetPages: 2,
  parquetTokenRatio: 0.2,
  parquetReadPages: 2,
  parquetSkipPages: 0,
  parquetRoundtrip: true,
};

test("VDF run-to-end finishes at E15 close-out", () => {
  const rows = cacheFredRows();
  const out = runVdfToEnd({ confirmNet: false, mode: "CACHE", rows, metrics });
  assert.equal(out.fail, 0);
  assert.equal(out.steps.at(-1)?.id, "E15");
  assert.equal(out.steps.find((s) => s.id === "E12")?.light, "ok");
  assert.equal(out.steps.find((s) => s.id === "E13")?.light, "ok");
  assert.equal(out.steps.find((s) => s.id === "E14")?.light, "ok");
  assert.equal(out.steps.find((s) => s.id === "E15")?.light, "ok");
  assert.equal(out.steps.find((s) => s.id === "E16")?.result, "CACHE");
  assert.equal(out.steps.find((s) => s.id === "E16")?.light, "ok");
  assert.match(out.steps.find((s) => s.id === "E16")?.out ?? "", /原件不刪/);
  assert.equal(out.modules.find((m) => m.id === "VDF_MDL_PX")?.result, "CACHE");
  assert.equal(out.steps.find((s) => s.id === "E06")?.light, "ok");
  assert.equal(out.steps.find((s) => s.id === "E08X")?.light, "ok");
  assert.match(out.steps.find((s) => s.id === "E08X")?.out ?? "", /轉碼 10\/10/);
  assert.match(out.steps.find((s) => s.id === "E06")?.out ?? "", /21\/21/);
  assert.equal(out.modules.find((m) => m.id === "VDF_MDL002")?.result, "SKIP");
  assert.equal(out.modules.find((m) => m.id === "VDF_MDL001")?.result, "RAN");
  assert.equal(out.modules.find((m) => m.id === "VDF_ENG075")?.result, "CACHE");
  assert.equal(out.modules.find((m) => m.id === "VDF_ENG076")?.result, "CACHE");
  assert.equal(out.modules.find((m) => m.id === "VDF_ENG077")?.result, "CACHE");
  assert.equal(out.seal.light, "ok");
});
