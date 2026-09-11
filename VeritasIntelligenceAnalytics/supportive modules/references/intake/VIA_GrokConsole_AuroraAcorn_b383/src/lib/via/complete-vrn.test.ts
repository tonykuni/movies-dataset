import assert from "node:assert/strict";
import { test } from "node:test";
import { completeVrn, vrnReady } from "./complete-vrn.ts";
import { hydraRiskVrn } from "./processes.ts";

test("no seal until tests pass", () => {
  const blocked = completeVrn({ testsPass: false });
  assert.equal(blocked.seal.light, "warn");
  assert.match(blocked.seal.note, /不封印/);
});

test("VRN seals only after ready + tests pass", () => {
  const h = hydraRiskVrn();
  assert.equal(h.ok, true);
  const ready = vrnReady(false);
  assert.equal(ready.ok, true, ready.r11);
  const out = completeVrn({ confirmNlp: false, testsPass: true });
  assert.equal(out.fail, 0, out.seal.note);
  assert.equal(out.seal.light, "ok");
  assert.match(out.seal.note, /測試已過/);
});
