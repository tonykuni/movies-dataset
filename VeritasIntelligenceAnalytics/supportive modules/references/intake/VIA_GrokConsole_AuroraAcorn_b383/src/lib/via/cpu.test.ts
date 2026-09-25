import assert from "node:assert/strict";
import { test } from "node:test";
import { alignUp, isaFromFlags, parseFlags, profileFromFlags, simdBoost } from "./cpu.ts";

test("flags pick avx512 over avx2", () => {
  assert.equal(isaFromFlags(parseFlags("sse4_1 avx avx2 avx512f avx512dq")), "avx512");
  assert.equal(isaFromFlags(parseFlags("avx avx2 fma")), "avx2");
  assert.equal(isaFromFlags(parseFlags("sse4_1")), "scalar");
});

test("avx512 profile is 8-wide and 64B aligned", () => {
  const p = profileFromFlags("avx2 avx512f", "AMD Ryzen 9 7950X");
  assert.equal(p.isa, "avx512");
  assert.equal(p.f64Width, 8);
  assert.equal(p.i32Width, 16);
  assert.equal(p.align, 64);
  assert.equal(p.vector, 2048);
  assert.equal(p.downclock, false);
  assert.equal(simdBoost(p.isa), 1.3);
});

test("old Xeon avx512 marks downclock risk", () => {
  const p = profileFromFlags("avx512f", "Intel Xeon Gold 6138");
  assert.equal(p.downclock, true);
});

test("alignUp pads to SIMD width", () => {
  assert.equal(alignUp(50, 8), 56);
  assert.equal(alignUp(16, 8), 16);
  assert.equal(alignUp(7, 1), 7);
});
