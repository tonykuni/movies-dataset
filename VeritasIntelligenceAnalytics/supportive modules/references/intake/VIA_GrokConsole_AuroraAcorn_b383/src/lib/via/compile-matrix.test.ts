import assert from "node:assert/strict";
import { test } from "node:test";
import { COMPILE_SNAP, UPLOAD_NEED, compileNote, compileQc, compileRows, uploadGapQc } from "./compile-matrix.ts";

test("tsc/vite snapshot green; host tree honestly missing", () => {
  assert.equal(COMPILE_SNAP.tsc, true);
  assert.equal(COMPILE_SNAP.vite, true);
  assert.equal(COMPILE_SNAP.winEngineTree, false);
  assert.equal(COMPILE_SNAP.live, false);
  assert.equal(COMPILE_SNAP.pwsh, false);
  const rows = compileRows();
  assert.equal(rows.length, 12);
  assert.equal(rows.find((r) => r.id === "CPL_VIA")?.can, true);
  assert.equal(rows.find((r) => r.id === "CPL_VDF_PY")?.can, false);
  assert.equal(rows.find((r) => r.id === "CPL_PS")?.can, false);
  assert.equal(rows.find((r) => r.id === "CPL_LIVE")?.tier, "sealed");
  const qc = compileQc();
  assert.equal(qc.filter((r) => r.light === "bad").length, 0);
  assert.match(compileNote(), /LIVE 關/);
});

test("upload gap: P1 names TrustScore and engine folder; skip sha/gate chain", () => {
  assert.ok(UPLOAD_NEED.some((r) => r.file.includes("VRN_MDL009_TrustScore") && r.listed === false && r.staged === false));
  assert.ok(UPLOAD_NEED.some((r) => r.file.includes("ENG047") && r.staged === false));
  assert.ok(UPLOAD_NEED.some((r) => r.file.includes("engine") && r.staged === true));
  assert.ok(UPLOAD_NEED.every((r) => !/_sha/.test(r.file)));
  const qc = uploadGapQc();
  assert.ok(Number(qc.find((r) => r.id === "UP_P1")?.value) >= 5);
  assert.ok(Number(qc.find((r) => r.id === "UP_STAGED")?.value) >= 10);
  assert.equal(qc.find((r) => r.id === "UP_SKIP")?.light, "ok");
});
