import assert from "node:assert/strict";
import { test } from "node:test";
import { PS20, applyCpuToPlan, pairAccels } from "./accel.ts";
import { profileFromFlags } from "./cpu.ts";

test("all 20 pair when DAG is complete", () => {
  const plan = pairAccels();
  assert.equal(PS20.length, 20);
  assert.equal(plan.active, 20);
  assert.equal(plan.conflicts, 0);
  assert.equal(plan.concurrency, 16);
  assert.equal(plan.pipeline, true);
  assert.equal(plan.simd, true);
  assert.equal(plan.query, true);
  assert.ok(plan.planFactor > 8);
});

test("SIMD and DuckDB close if ChunkAlign missing", () => {
  const ids = PS20.map((a) => a.id).filter((id) => id !== "PS-10");
  const plan = pairAccels(ids);
  const simd = plan.rows.find((r) => r.id === "PS-17");
  const duck = plan.rows.find((r) => r.id === "PS-18");
  const pipe = plan.rows.find((r) => r.id === "PS-20");
  assert.equal(simd?.status, "warn");
  assert.equal(duck?.status, "warn");
  assert.equal(pipe?.status, "warn");
  assert.equal(plan.simd, false);
  assert.equal(plan.pipeline, false);
  assert.ok(plan.conflicts >= 3);
});

test("ConsentGate is root of fetch pool", () => {
  const ids = PS20.map((a) => a.id).filter((id) => id !== "PS-05");
  const plan = pairAccels(ids);
  assert.equal(plan.rows.find((r) => r.id === "PS-01")?.status, "warn");
  assert.ok(plan.concurrency <= 4);
});

test("scalar CPU demotes SIMDScan without breaking the DAG", () => {
  const tuned = applyCpuToPlan(pairAccels(), profileFromFlags("sse4_1", "virt"));
  const scan = tuned.rows.find((r) => r.id === "PS-17");
  assert.equal(scan?.status, "warn");
  assert.equal(tuned.simd, false);
  assert.equal(tuned.pipeline, true);
  assert.ok(tuned.active === 19);
});

test("avx2 CPU keeps SIMDScan with 1.15 boost", () => {
  const tuned = applyCpuToPlan(pairAccels(), profileFromFlags("avx avx2 fma", "Intel Core"));
  const scan = tuned.rows.find((r) => r.id === "PS-17");
  assert.equal(scan?.status, "ok");
  assert.equal(scan?.boost, 1.15);
  assert.equal(tuned.simd, true);
});

