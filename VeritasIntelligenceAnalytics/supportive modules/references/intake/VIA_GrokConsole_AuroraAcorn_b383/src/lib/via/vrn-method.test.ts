import assert from "node:assert/strict";
import { test } from "node:test";
import { VRN_FIELD_N } from "./vrn-field-cache.ts";
import { VRN_FIN_MAP, VRN_FIN_N } from "./vrn-fin-map-cache.ts";
import { VRN_EBIT_ZH_CANDIDATE, VRN_LEX_FILLS, VRN_LEX_MERGE, lexFillOk } from "./vrn-lexicon.ts";
import { rocToGregorian } from "./vrn-rx.ts";
import { vrnFieldLookup, vrnMapLookup, vrnMethodNote, vrnMethodQc, vrnRate, vrnUpside, vrnYoy } from "./vrn-method.ts";

test("lexicon K6 14 empty-en fills, not merged", () => {
  assert.equal(VRN_LEX_FILLS.length, 14);
  assert.equal(lexFillOk(), true);
  assert.equal(VRN_LEX_MERGE, false);
  assert.equal(VRN_LEX_FILLS.find((r) => r.node === "K6.2")?.en, "Co-Packaged Optics");
  assert.equal(VRN_LEX_FILLS.every((r) => r.zh.length > 0), true);
});

test("trilingual 195, ebit zh empty so candidate only", () => {
  assert.equal(VRN_FIN_N, 195);
  assert.equal(VRN_FIN_MAP.length, 195);
  const ebit = vrnMapLookup("ebit");
  assert.equal(ebit?.en, "EBIT");
  assert.equal(ebit?.zh, "");
  assert.equal(VRN_EBIT_ZH_CANDIDATE.zh, "稅前息前盈餘");
  assert.equal(vrnMapLookup("revenue")?.zh, "營業收入");
});

test("upside example and zero-base growth", () => {
  const u = vrnUpside(1450, 1200);
  assert.ok(u !== null && Math.abs(u - 0.2083333333) < 1e-6);
  assert.equal(vrnYoy(10, 0).state, "NOT_COMPUTABLE_ZERO_BASE");
  assert.equal(vrnYoy(10, 0).value, null);
});

test("rating dict Neutral=HOLD, 強力買進=BUY, NR", () => {
  assert.equal(vrnRate("中立")?.lvl, "HOLD");
  assert.equal(vrnRate("Neutral")?.lvl, "HOLD");
  assert.equal(vrnRate("強力買進")?.lvl, "BUY");
  assert.equal(vrnRate("Not Rated")?.lvl, "NOT_RATED");
  const q = vrnMethodQc();
  assert.equal(q.filter((r) => r.light === "bad").length, 0);
  assert.match(vrnMethodNote(), /候審/);
});

test("57-field map TWSE/YF; ROC 115=2026; QR warn prepaid", () => {
  assert.equal(VRN_FIELD_N, 57);
  assert.equal(vrnFieldLookup("revenue")?.yf, "totalRevenue");
  assert.equal(vrnFieldLookup("cash")?.twse, "現金及約當現金");
  assert.equal(rocToGregorian(115), 2026);
  const q = vrnMethodQc();
  assert.equal(q.find((r) => r.id === "M_57")?.light, "ok");
  assert.equal(q.find((r) => r.id === "M_QR")?.light, "warn");
  assert.equal(q.find((r) => r.id === "M_RX")?.light, "ok");
});
