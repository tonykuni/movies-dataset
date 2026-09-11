import assert from "node:assert/strict";
import { test } from "node:test";
import { GOV_TOOLS } from "./catalog.ts";
import { JOBS, aliasOf, accelBindSummary } from "./inventory.ts";
import {
  AEG_FILE,
  AEG_REL,
  CEL_FILE,
  CEL_HOST,
  CEL_REL,
  celAegNote,
  celAegRows,
  consentUntouched,
  vdfAccelWinner,
  vdfNetWinner,
} from "./cel-aeg.ts";

test("VDF accel/net SSOT is Celeritas + AegisNexus; bridges alias; GOV stays 10", () => {
  assert.equal(GOV_TOOLS.length, 10);
  assert.equal(vdfAccelWinner(), "ACC-CEL");
  assert.equal(vdfNetWinner(), "NET-AEG");
  assert.equal(CEL_FILE, "VeritasCeleritas.py");
  assert.equal(AEG_FILE, "VeritasAegisNexus.py");
  assert.match(CEL_REL, /supportive modules/);
  assert.match(AEG_REL, /supportive modules/);
  assert.match(CEL_HOST, /OneDrive/);
  assert.equal(aliasOf("VDF_MDL000"), "ACC-CEL");
  assert.equal(aliasOf("SUP_MDL740"), "NET-AEG");
  assert.equal(aliasOf("SUP_MDL737"), null);
  assert.equal(consentUntouched(), true);
  assert.match(celAegNote(), /VIS-SA-CEL-000001/);
  const rows = celAegRows();
  assert.equal(rows.length, 4);
  assert.ok(rows.every((r) => r.winner === "ACC-CEL" || r.winner === "NET-AEG"));
  assert.ok(JOBS.some((j) => j.job === "VDF_ACCEL" && j.winner === "ACC-CEL"));
  assert.ok(JOBS.some((j) => j.job === "VDF_NET" && j.winner === "NET-AEG"));
  const s = accelBindSummary();
  assert.equal(s.bound, 20);
  assert.equal(s.miss, 0);
});
