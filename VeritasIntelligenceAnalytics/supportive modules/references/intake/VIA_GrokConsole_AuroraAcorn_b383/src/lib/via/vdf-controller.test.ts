import assert from "node:assert/strict";
import { test } from "node:test";
import { FRED_CATALOG } from "./catalog.ts";
import { DEFAULT_FRED_API } from "./fred-api.ts";
import { buildProductionPlan, invokeVdfFetchStatus, invokeVdfStatus, sealFetch } from "./vdf-controller.ts";
import type { FetchMetrics } from "./types.ts";
import { MACRO_PLUS } from "./vdf-mother.ts";

const metrics: FetchMetrics = {
  concurrency: 16,
  series: 53,
  lakeRows: 100,
  chunks: 4,
  skipped: 1,
  scanned: 3,
  cacheHits: 53,
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

test("Invoke-VDF status is reader-ready and does not claim dict files exist", () => {
  const rows = invokeVdfStatus();
  assert.equal(rows[0]?.value, "VDF_ACTIVE_READER_READY");
  assert.ok(rows.some((r) => r.key === "database" && r.status === "warn"));
});

test("Invoke-VDF-Fetch status is production controller ready", () => {
  const rows = invokeVdfFetchStatus();
  assert.equal(rows[0]?.value, "VDF_PRODUCTION_FETCH_CONTROLLER_READY");
});

test("plan disables network without dual gate", () => {
  const p = buildProductionPlan({ confirmNet: false, apiKey: "a".repeat(32), apiUrl: DEFAULT_FRED_API, startYear: 2024 });
  assert.equal(p.network, "DISABLED");
  assert.ok(p.lanes.filter((l) => l.intended !== "LOCAL").every((l) => l.intended === "SKIP"));
  assert.equal(p.lanes.find((l) => l.id === "PX")?.intended, "LOCAL");
});

test("plan enables only FRED when dual gate open", () => {
  const p = buildProductionPlan({ confirmNet: true, apiKey: "ab".repeat(16), apiUrl: DEFAULT_FRED_API, startYear: 2024 });
  assert.equal(p.network, "ENABLED");
  assert.equal(p.lanes.find((l) => l.id === "FRED")?.intended, "LIVE");
  assert.equal(p.lanes.find((l) => l.id === "PX")?.intended, "LOCAL");
  assert.ok(p.lanes.filter((l) => l.id !== "FRED" && l.intended !== "LOCAL").every((l) => l.intended === "SKIP"));
});

test("seal marks non-FRED lanes SKIP except local VIA_db", () => {
  const p = buildProductionPlan({ confirmNet: false, apiKey: "", apiUrl: DEFAULT_FRED_API, startYear: 2024 });
  const s = sealFetch(p, { mode: "CACHE", note: "cache", series: 53, metrics });
  assert.equal(s.manifest.skipLanes, s.lanes.filter((l) => l.result === "SKIP").length);
  assert.equal(s.lanes.find((l) => l.id === "FRED")?.result, "CACHE");
  assert.equal(s.lanes.find((l) => l.id === "PX")?.result, "LOCAL");
  assert.equal(s.lanes.find((l) => l.id === "CHIP")?.result, "LOCAL");
  assert.equal(s.lanes.find((l) => l.id === "REST")?.result, "LOCAL");
});

test("rates FX fiscal plus are in the FRED lake except Treasury MTS", () => {
  const ids = new Set(FRED_CATALOG.map((s) => s.seriesId));
  assert.ok(ids.has("DGS1MO") && ids.has("DEXUSEU") && ids.has("FGRECPT") && ids.has("FYFSD"));
  assert.ok(FRED_CATALOG.some((s) => s.category === "Fiscal"));
  assert.ok(MACRO_PLUS.some((s) => s.gate === "Treasury_FD"));
  assert.ok(!ids.has("MTS.ReceiptsBySource"));
});
