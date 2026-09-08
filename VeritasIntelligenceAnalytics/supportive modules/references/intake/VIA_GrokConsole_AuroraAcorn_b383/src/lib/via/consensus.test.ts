import assert from "node:assert/strict";
import { test } from "node:test";
import {
  CNS_ENGINE,
  CNS_ID,
  CNS_LIVE_ENABLED,
  CNS_SCHEMA,
  CNS_SEED,
  MAX_CODES_PER_RUN,
  batchCodes,
  canFetchCns,
  cnsMembersOk,
  cnyesPage,
  cnyesPath,
  CNYES_TARGET,
  comparePair,
  comparesOf,
  gradePct,
  longFromSeed,
  planFetch,
  recordKey,
  runCnsSim,
  validateCode,
  validateCodes,
} from "./consensus.ts";

test("codes reject ETF prefix-zero and keep TWSE/TPEX yf", () => {
  assert.equal(validateCode("2330.TW"), "2330");
  assert.throws(() => validateCode("00980A"));
  assert.throws(() => validateCode("0050"));
  assert.deepEqual(validateCodes(["2330", "2330.TW", "2317"]), ["2330", "2317"]);
  assert.throws(() => validateCodes(Array.from({ length: MAX_CODES_PER_RUN + 1 }, (_, i) => String(1000 + i))));
});

test("CNYES paths stay public marketinfo", () => {
  assert.equal(cnyesPage("2330"), "https://www.cnyes.com/twstock/2330/summary/overview");
  assert.match(cnyesPath(CNYES_TARGET, "TWS:2330:STOCK"), /marketinfo\.api\.cnyes\.com/);
});

test("quality grades match Python thresholds", () => {
  assert.equal(gradePct(0.04, 0.05, 0.15), "MATCH");
  assert.equal(gradePct(0.05, 0.05, 0.15), "MATCH");
  assert.equal(gradePct(0.12, 0.05, 0.15), "REVIEW");
  assert.equal(gradePct(0.2, 0.05, 0.15), "CONFLICT");
  assert.equal(gradePct(null, 0.05, 0.15), "INCOMPLETE");
  assert.equal(comparePair("3711", "TARGET_MEAN", 180, 5.6, "target", false).grade, "CURRENCY_MISMATCH");
  assert.equal(comparePair("2454", "RATING", "POSITIVE", "NEUTRAL", "rating").grade, "CONFLICT");
});

test("long table keys are idempotent and dual-source", () => {
  const a = longFromSeed(CNS_SEED[0]!);
  const b = longFromSeed(CNS_SEED[0]!);
  assert.equal(a.length, b.length);
  assert.equal(a[0]?.recordKey, b[0]?.recordKey);
  assert.equal(new Set(a.map((r) => r.recordKey)).size, a.length);
  assert.ok(a.every((r) => r.recordKey === recordKey(r)));
  assert.ok(a.some((r) => r.source === "FactSet"));
  assert.ok(a.some((r) => r.source === "YFinance"));
  assert.equal(a[0]?.sourceMode, "CACHE");
});

test("2330 MATCH · 2317 REVIEW · 2454 CONFLICT · 2303 INCOMPLETE · 3711 FX", () => {
  const g = (code: string, metric: string) => comparesOf(CNS_SEED.find((s) => s.code === code)!).find((c) => c.metric === metric)!;
  assert.equal(g("2330", "TARGET_MEAN").grade, "MATCH");
  assert.equal(g("2317", "TARGET_MEAN").grade, "REVIEW");
  assert.equal(g("2454", "TARGET_MEAN").grade, "CONFLICT");
  assert.equal(g("2303", "TARGET_MEAN").grade, "INCOMPLETE");
  assert.equal(g("3711", "TARGET_MEAN").grade, "CURRENCY_MISMATCH");
});

test("GROUP vs ALL plan · LIVE closed · seeds SSOT", () => {
  assert.equal(CNS_LIVE_ENABLED, false);
  assert.equal(canFetchCns({ confirmNet: false }).ok, false);
  assert.equal(canFetchCns({ confirmNet: true }).ok, false);
  const one = planFetch("GROUP", "2330");
  assert.deepEqual(one.codes, ["2330"]);
  assert.equal(one.cached, 1);
  const semi = planFetch("GROUP", "半導體");
  assert.ok(semi.codes.includes("2330") && semi.codes.includes("2454"));
  const all = planFetch("ALL", "");
  assert.ok(all.codes.length >= 40);
  assert.equal(all.batches.length, batchCodes(all.codes).length);
  assert.ok(all.batches.every((b) => b.length <= MAX_CODES_PER_RUN));
  assert.equal(cnsMembersOk(), true);
  const sim = runCnsSim({ mode: "GROUP", query: "2330" });
  assert.equal(sim.seeds[0]?.code, "2330");
  assert.match(sim.note, /CACHE/);
  assert.equal(sim.long[0]?.recordKey.startsWith("2330|"), true);
  assert.equal(CNS_ENGINE, "VDF_ENG077");
  assert.equal(CNS_ID, "VIA_CNS");
  assert.equal(CNS_SCHEMA, "VIA-CONSENSUS-LONG/2.0");
});
