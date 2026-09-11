import assert from "node:assert/strict";
import { test } from "node:test";
import { REGISTERED_ENGINES } from "./catalog.ts";
import { runViaToEnd } from "./via-end.ts";

test("VIA right-side close-out seals what console can master", () => {
  const out = runViaToEnd({ engines: REGISTERED_ENGINES, confirmNet: false, confirmNlp: false });
  assert.equal(out.fail, 0, out.steps.filter((s) => s.result === "FAIL").map((s) => `${s.id} ${s.out}`).join(" | "));
  assert.equal(out.steps.at(-1)?.id, "V12");
  assert.equal(out.steps.find((s) => s.id === "V12")?.light, "ok");
  assert.equal(out.steps.find((s) => s.id === "V09")?.light, "warn");
  assert.equal(out.steps.find((s) => s.id === "V07")?.result, "SKIP");
  assert.equal(out.seal.light, "ok");
});
