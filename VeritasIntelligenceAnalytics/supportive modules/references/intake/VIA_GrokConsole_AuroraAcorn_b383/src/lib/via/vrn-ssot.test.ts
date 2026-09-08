import assert from "node:assert/strict";
import { test } from "node:test";
import { VRN_SSOT_N, VRN_SSOT_PROMOTED, VRN_SSOT_RECS } from "./vrn-ssot-cache.ts";
import { vrnCompanyTp, vrnSsotLight, vrnSsotNote, vrnSsotQc } from "./vrn-ssot.ts";

test("v2 candidate 64 rows, not promoted, hash chain, unresolved 陳子昂 kept", () => {
  assert.equal(VRN_SSOT_N, 64);
  assert.equal(VRN_SSOT_RECS.length, 64);
  assert.equal(VRN_SSOT_PROMOTED, false);
  const ids = new Set(VRN_SSOT_RECS.map((r) => r.id));
  assert.equal(ids.size, 64);
  const q = vrnSsotQc();
  assert.equal(q.find((r) => r.id === "SSOT_PROMO")?.value, "未升");
  assert.equal(q.find((r) => r.id === "SSOT_CHAIN")?.light, "ok");
  assert.equal(q.find((r) => r.id === "SSOT_DATE")?.value, "1");
  assert.match(q.find((r) => r.id === "SSOT_DATE")?.note ?? "", /陳子昂/);
  assert.equal(vrnSsotLight(), "ok");
  assert.match(vrnSsotNote(), /未晉升/);
  assert.equal(q.filter((r) => r.light === "bad").length, 0);
});

test("company TP uses median of 1–2 prices; CTBC 6533 315; mega morning dump skipped", () => {
  const tp = vrnCompanyTp();
  const a = tp.find((r) => r.ticker === "6533");
  assert.equal(a?.median, 315);
  assert.deepEqual(a?.prices, [300, 330]);
  const hynix = tp.find((r) => r.ticker === "6873");
  assert.equal(hynix?.median, (345 + 208) / 2);
  assert.equal(tp.some((r) => r.prices.length > 2), false);
  assert.ok(tp.every((r) => /^\d{4}$/.test(r.ticker)));
});
