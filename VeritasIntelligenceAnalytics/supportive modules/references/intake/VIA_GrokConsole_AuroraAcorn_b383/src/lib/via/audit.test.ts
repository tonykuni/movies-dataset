import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { applyAuditPatch, auditEngine, repairHash } from "./audit.ts";
import type { EngineRec } from "./types.ts";

const base: EngineRec = {
  id: "VRN_ENG064",
  name: "KnowledgeStack",
  kind: "NLP",
  path: "functional modules/VRN/",
  hash: "a91c2e",
  accel: true,
  net: false,
  nlp: true,
  ssot: true,
  status: "ok",
  note: "ok",
};

describe("auditEngine", () => {
  it("passes a healthy engine with NONE", () => {
    const r = auditEngine(base, { confirmNet: false, confirmNlp: false });
    assert.equal(r.repair, "NONE");
    assert.equal(r.status, "ok");
    assert.equal(r.steps.A10, "ok");
  });

  it("repairs missing accel and ssot additively", () => {
    const r = auditEngine(
      { ...base, id: "VAP_MDL001", name: "VAP Router", kind: "GOV", accel: false, ssot: false, hash: "" },
      { confirmNet: false, confirmNlp: false },
    );
    assert.equal(r.repair, "REPAIRED");
    assert.equal(r.patch.accel, true);
    assert.equal(r.patch.ssot, true);
    assert.equal(r.patch.hash, repairHash("VAP_MDL001"));
    const next = applyAuditPatch({ ...base, accel: false, ssot: false, hash: "" }, r);
    assert.equal(next.accel, true);
    assert.equal(next.ssot, true);
  });

  it("keeps unrepairable orphan in details", () => {
    const r = auditEngine(
      { ...base, id: "ENG_ORPHAN", name: "orphan_stub", path: "", hash: "", accel: false, ssot: false },
      { confirmNet: false, confirmNlp: false },
    );
    assert.equal(r.repair, "UNREPAIRABLE");
    assert.equal(r.steps.A02, "bad");
    assert.equal(r.steps.A04, "bad");
    assert.ok(r.findings.some((f) => f.includes("DETAILS") || f.includes("無法")));
  });

  it("does not auto-open NET without consent", () => {
    const r = auditEngine(
      { ...base, id: "NET_X", kind: "NET", net: false, nlp: false },
      { confirmNet: false, confirmNlp: false },
    );
    assert.equal(r.repair, "UNREPAIRABLE");
    assert.equal(r.patch.net, undefined);
  });

  it("repairs NET when consent is on", () => {
    const r = auditEngine(
      { ...base, id: "NET_X", kind: "NET", net: false, nlp: false },
      { confirmNet: true, confirmNlp: false },
    );
    assert.equal(r.repair, "REPAIRED");
    assert.equal(r.patch.net, true);
  });
});
