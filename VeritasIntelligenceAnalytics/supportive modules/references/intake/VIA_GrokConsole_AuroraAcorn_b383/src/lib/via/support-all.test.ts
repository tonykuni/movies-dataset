import assert from "node:assert/strict";
import { test } from "node:test";
import { REGISTERED_ENGINES } from "./catalog.ts";
import { aliasOf, liveEngines, applySsot } from "./inventory.ts";
import { MDE, OFIE, SUPPORT_LIVE, USIP, ofieAccepts, supportStack } from "./support-all.ts";
import { guessType } from "./vrn.ts";

test("OFIE/MDE/USIP registered; pdf docx md ok; tmp rejected", () => {
  assert.equal(SUPPORT_LIVE, false);
  assert.equal(ofieAccepts("pdf"), true);
  assert.equal(ofieAccepts("docx"), true);
  assert.equal(ofieAccepts("pptx"), true);
  assert.equal(ofieAccepts("md"), true);
  assert.equal(ofieAccepts("tmp"), false);
  assert.equal(supportStack("docx").ofie, true);
  assert.equal(supportStack("md").mde, true);
  assert.equal(supportStack("docx").usip, true);
  assert.equal(guessType("華南-Memo.docx", "docx"), "MEMO");
  const ids = REGISTERED_ENGINES.map((e) => e.id);
  assert.ok(ids.includes(OFIE.id) && ids.includes(MDE.id) && ids.includes(USIP.id));
  const live = liveEngines(applySsot(REGISTERED_ENGINES));
  assert.ok(live.some((e) => e.id === OFIE.id));
  assert.equal(aliasOf(OFIE.id), null);
});
