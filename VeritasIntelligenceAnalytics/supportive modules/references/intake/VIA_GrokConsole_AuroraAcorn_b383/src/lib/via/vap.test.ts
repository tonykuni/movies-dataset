import assert from "node:assert/strict";
import { test } from "node:test";
import { COMPLETE_LANES, SIX_LANES, VRN_LANES } from "./processes.ts";
import { auditEngine } from "./audit.ts";
import { REGISTERED_ENGINES } from "./catalog.ts";
import { aliasOf } from "./inventory.ts";
import { runViaToEnd } from "./via-end.ts";
import { VAP_WRITE, vapHydraOk, vapReady, sealVap } from "./vap.ts";

test("VAP SSOT live, hydra-safe, VAR green", () => {
  const rec = REGISTERED_ENGINES.find((e) => e.id === "VAP_MDL001");
  assert.equal(rec?.ssot, true);
  assert.equal(rec?.status, "ok");
  assert.ok((rec?.hash.length ?? 0) >= 4);
  const a = auditEngine(rec!, { confirmNet: false, confirmNlp: false });
  assert.equal(a.repair, "NONE");
  const r = vapReady();
  assert.equal(r.ok, true, r.note);
  assert.equal(sealVap().light, "ok");
  const writes = [...SIX_LANES, ...COMPLETE_LANES, ...VRN_LANES].map((l) => l.write);
  assert.equal(vapHydraOk(writes), true);
  assert.equal(writes.includes(VAP_WRITE), false);
  assert.equal(aliasOf("VDF_ENG039"), "VDF_MDL007");
  assert.equal(aliasOf("VDF_ENG040"), "VDF_MDL001");
});

test("VIA close-out includes VAP", () => {
  const out = runViaToEnd({ engines: REGISTERED_ENGINES, confirmNet: false, confirmNlp: false });
  assert.equal(out.fail, 0);
  assert.match(out.steps.find((s) => s.id === "V10")?.out ?? "", /VAP true/);
});
