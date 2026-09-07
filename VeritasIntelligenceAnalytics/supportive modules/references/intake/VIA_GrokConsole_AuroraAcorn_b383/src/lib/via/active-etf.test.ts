import assert from "node:assert/strict";
import { test } from "node:test";
import {
  AETF_LIVE_ENABLED,
  AETF_UNIVERSE,
  aetfByScope,
  aetfMeta,
  bookComplete,
  aeaMembersOk,
  aetfFlowSum,
  aumMktTwd,
  aumTwd,
  cacheNav,
  canFetchAetf,
  cashRows,
  dAumTwd,
  filterHolds,
  flowTwd,
  holdDeltas,
  inspectAetf,
  isActiveName,
  isActiveTicker,
  latestHoldingsDate,
  iPremiumFromF,
  navLogicRows,
  packAea,
  parseTwseEtfNavMsg,
  parseTwEtf,
  premiumOf,
  runAeaSim,
  settleNav,
  TWSE_ETF_NAV_FIELDS,
  TWSE_NAV_JSON_SAMPLE,
  twseHIsNavPrev,
  twseJsonMapRows,
  universeComplete,
  verifyAetf,
} from "./active-etf.ts";

const asof = new Date("2026-09-05T08:00:00Z");

test("LIVE off; trailing A means active ETF", () => {
  assert.equal(AETF_LIVE_ENABLED, false);
  assert.equal(canFetchAetf({ confirmNet: true }).ok, false);
  assert.equal(parseTwEtf("00980A.TW"), "00980A");
  assert.equal(parseTwEtf("2330"), "");
  assert.equal(isActiveTicker("00980A"), true);
  assert.equal(isActiveTicker("00980"), false);
  assert.equal(isActiveTicker("0050"), false);
  assert.equal(isActiveTicker("00982D"), false);
  assert.equal(isActiveName("主動野村臺灣優選"), true);
  assert.equal(aeaMembersOk(), true);
});

test("Saturday 5 Sep 2026 holdings date is Friday; cache sim runs", () => {
  assert.equal(latestHoldingsDate(asof), "2026-09-04");
  const g = inspectAetf(asof, false);
  assert.equal(g.live, false);
  assert.equal(g.funds.length, 3);
  assert.ok(g.holds.every((h) => h.source === "CACHE"));
  const sim = runAeaSim(asof);
  assert.equal(sim.rows.length, 7);
  assert.ok(sim.rows.some((r) => r.id === "AEA_AUM"));
  assert.match(sim.note, /CACHE/);
});

test("AUM is units×NAV; flow is Δunits×prev NAV; price-only is zero flow", () => {
  const n = cacheNav();
  const s = aetfFlowSum(n);
  assert.equal(s.aum, n.reduce((a, r) => a + aumTwd(r), 0));
  assert.ok(s.inFlow > 0);
  assert.ok(s.outFlow < 0);
  const row = n[0]!;
  assert.equal(flowTwd(row), row.dUnits * settleNav(row));
  assert.notEqual(settleNav(row), row.nav);
  const flat = { ...row, dUnits: 0, px: row.nav * 1.02 };
  assert.equal(flowTwd(flat), 0);
  assert.ok((premiumOf(row) ?? 0) === 0 || Math.abs(premiumOf({ nav: row.nav, px: row.nav * 1.02 })!) > 0);
  const prev = { units: row.units - row.dUnits, nav: row.navPrev ?? row.nav };
  assert.notEqual(Math.round(dAumTwd(prev, row)), Math.round(flowTwd(row)));
  const logic = navLogicRows();
  assert.equal(logic.find((r) => r.id === "N_DAUM")?.light, "ok");
  assert.equal(logic.find((r) => r.id === "N_PX")?.value, "0");
  assert.ok((aumMktTwd(row) ?? 0) > 0);
});
test("29-fund universe, cash ranks 00981A, holdings filter, update verify", () => {
  assert.equal(AETF_UNIVERSE.length, 29);
  assert.equal(universeComplete(), true);
  assert.equal(bookComplete(), true);
  assert.equal(aetfByScope("TW").length, 22);
  assert.equal(aetfByScope("GL").length, 7);
  assert.equal(aetfMeta("00400A").name, "主動國泰動能高息");
  assert.equal(aetfMeta("00983A").scope, "GL");
  const cash = cashRows();
  assert.equal(cash[0]?.ticker, "00981A");
  assert.equal(cash[0]?.name, "主動統一台股增長");
  assert.equal(cash.every((c) => c.name.length > 0), true);
  assert.ok((cash[0]?.aum ?? 0) > 2e11);
  assert.equal(cash.filter((c) => c.net != null).length, 29);
  assert.equal(cash.filter((c) => (c.net ?? 0) !== 0).length, 3);
  assert.equal(filterHolds("00980A").every((h) => h.fund === "00980A"), true);
  const d = holdDeltas("00980A");
  assert.ok(d.some((x) => x.stock === "2330" && x.dwgt != null && x.dwgt > 0));
  const asof = new Date("2026-09-05T08:00:00Z");
  const v = verifyAetf(asof);
  assert.equal(v.find((r) => r.id === "V_NAV")?.light, "ok");
  assert.equal(v.find((r) => r.id === "V_FLOW")?.light, "ok");
  assert.equal(v.find((r) => r.id === "V_LIVE")?.light, "ok");
  assert.equal(v.find((r) => r.id === "V_H")?.light, "ok");
  assert.equal(v.find((r) => r.id === "V_PX")?.light, "ok");
  assert.equal(v.find((r) => r.id === "V_STALE")?.light, "ok");
  assert.equal(v.filter((r) => r.light === "bad" || r.light === "warn").length, 0);
  const pack = packAea(asof, "00982A");
  assert.equal(pack.deltas.every((x) => x.fund === "00982A"), true);
  assert.match(pack.note, /29/);
});

test("TWSE ETF NAV JSON h is previous NAV, not MIS high", () => {
  const h = TWSE_ETF_NAV_FIELDS.find((x) => x.letter === "h");
  assert.equal(h?.key, "navPrev");
  assert.equal(h?.zh, "前一營業日淨值");
  const p = parseTwseEtfNavMsg({ ...TWSE_NAV_JSON_SAMPLE });
  assert.ok(p);
  assert.equal(p!.navPrev, 38.74);
  assert.equal(p!.units, 15000);
  assert.equal(p!.dUnits, 500);
  assert.equal(p!.px, 38.72);
  assert.ok(Math.abs(p!.iPremium - iPremiumFromF(p!.px, p!.iNav)) < 0.02);
  assert.equal(twseHIsNavPrev({ ...TWSE_NAV_JSON_SAMPLE }), true);
  assert.equal(p!.dUnits * p!.navPrev, 500 * 38.74);
  const rows = twseJsonMapRows();
  assert.equal(rows.find((r) => r.id === "H_MAP")?.light, "ok");
  assert.equal(rows.find((r) => r.id === "H_G")?.light, "ok");
  assert.equal(parseTwseEtfNavMsg({ ...TWSE_NAV_JSON_SAMPLE, h: "未結出" }), null);
});
