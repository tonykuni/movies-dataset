import assert from "node:assert/strict";
import { test } from "node:test";
import { GOV_TOOLS, NLP_TOOLS, REGISTERED_ENGINES } from "./catalog.ts";
import { CEL_REG, AEG_REG } from "./cel-aeg.ts";
import { accelToolOf, autoRegOf, engineMountQc, engineMountRows, netToolOf, nlpToolOf, NLP_MAP } from "./engine-mount.ts";
import { aliasOf } from "./inventory.ts";

test("every live engine shows auto-reg and CEL/AEG/NLP mount; GOV stays 10", () => {
  assert.equal(GOV_TOOLS.length, 10);
  assert.equal(CEL_REG, "VIS-SA-CEL-000001");
  assert.equal(AEG_REG, "無");
  const cel = REGISTERED_ENGINES.find((e) => e.id === "ACC-CEL")!;
  assert.equal(autoRegOf(cel).auto, true);
  assert.equal(nlpToolOf(cel), "—");
  assert.equal(nlpToolOf(REGISTERED_ENGINES.find((e) => e.id === "VRN_MDL004")!), "NLP-OCR");
  assert.equal(nlpToolOf(REGISTERED_ENGINES.find((e) => e.id === "VRN_MDL001")!), "NLP-063");
  assert.equal(nlpToolOf(REGISTERED_ENGINES.find((e) => e.id === "VRN_MDL005")!), "NLP-064");
  assert.equal(nlpToolOf(REGISTERED_ENGINES.find((e) => e.id === "VRN_ENG063")!), "NLP-063");
  assert.equal(nlpToolOf(REGISTERED_ENGINES.find((e) => e.id === "VRN_SYN")!), "NLP-063");
  assert.equal(aliasOf("VRN_SYN"), null);
  const yf = REGISTERED_ENGINES.find((e) => e.id === "VDF_MDL002")!;
  assert.equal(accelToolOf(yf), "ACC-CEL");
  assert.equal(netToolOf(yf), "NET-AEG");
  const rows = engineMountRows();
  assert.equal(rows.length, REGISTERED_ENGINES.length);
  const nlpIds = new Set(Object.values(NLP_MAP));
  for (const t of NLP_TOOLS) {
    assert.ok(nlpIds.has(t.id), `missing engine map for ${t.id}`);
  }
  const liveNlp = rows.filter((r) => !r.aliased && r.nlp !== "—");
  assert.ok(liveNlp.every((r) => NLP_TOOLS.some((t) => t.id === r.nlp)));
  const qc = engineMountQc();
  assert.ok(Number(qc.find((r) => r.id === "EM_ACC")?.value.split("/")[0]) > 20);
});
