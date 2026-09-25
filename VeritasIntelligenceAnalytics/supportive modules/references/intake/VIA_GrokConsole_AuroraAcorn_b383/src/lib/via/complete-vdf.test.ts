import assert from "node:assert/strict";
import { test } from "node:test";
import { cacheFredRows } from "./catalog.ts";
import { completeVdf, vdfReady } from "./complete-vdf.ts";

test("VDF CACHE path is complete and sealed", () => {
  const rows = cacheFredRows();
  const done = completeVdf({ testsPass: true, confirmNet: false, rows });
  assert.equal(done.fail, 0);
  assert.equal(done.seal.light, "ok");
  assert.match(done.seal.note, /完工/);
  assert.match(done.seal.note, /年檔槽保留/);
  const ready = vdfReady({ confirmNet: false, rows, metrics: null });
  assert.equal(ready.ok, true);
});

test("VDF will not seal if tests fail", () => {
  const done = completeVdf({ testsPass: false });
  assert.equal(done.seal.light, "warn");
  assert.equal(done.fail, 1);
});
