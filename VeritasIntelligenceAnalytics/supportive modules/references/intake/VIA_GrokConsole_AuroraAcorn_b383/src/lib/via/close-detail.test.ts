import assert from "node:assert/strict";
import { test } from "node:test";
import { inspectAetf } from "./active-etf.ts";
import { cacheFredRows } from "./catalog.ts";
import {
  aumYi,
  cacheClosePack,
  isolateRows,
  simulateVrnClose,
  vdfCloseSnap,
  vrnCloseSnap,
} from "./close-detail.ts";
import { REGISTERED_ENGINES } from "./catalog.ts";

test("CACHE VDF close snap is 98 series / 10 cats / PAR1 2p / AEA 3 AUM 287.1", () => {
  const pack = cacheClosePack();
  const rows = cacheFredRows();
  assert.equal(rows.length, 98);
  assert.equal(new Set(rows.map((r) => r.category)).size, 10);
  const fred = pack.vdf.find((r) => r.id === "VDF_FRED");
  assert.equal(fred?.value, "98 · 10 類");
  assert.equal(fred?.light, "ok");
  const par1 = pack.vdf.find((r) => r.id === "VDF_PAR1");
  assert.match(par1?.value ?? "", /PAR1 2p 跳過 0/);
  assert.equal(par1?.light, "ok");
  const aea = inspectAetf(new Date("2026-09-06T10:00:00+08:00"), false);
  assert.equal(aea.funds.length, 3);
  assert.equal(aea.funds[0]?.asOf, "2026-09-04");
  assert.equal(aumYi(aea.flow.aum), "287.1");
  const aeaRow = pack.vdf.find((r) => r.id === "VDF_AEA");
  assert.match(aeaRow?.value ?? "", /CACHE 3 檔主動/);
  assert.match(aeaRow?.value ?? "", /287\.1 億/);
  assert.match(aeaRow?.value ?? "", /2026-09-04/);
  assert.match(aeaRow?.value ?? "", /LIVE 關/);
  const g1 = pack.vdf.find((r) => r.id === "VDF_G1");
  assert.equal(g1?.value, "關");
  const xf = pack.vdf.find((r) => r.id === "VDF_X");
  assert.match(xf?.value ?? "", /^×/);
  assert.ok(pack.metrics.planFactor > 8);
  assert.equal(pack.vdf.find((r) => r.id === "VDF_PX")?.value, "VIA_db_part1_prices");
  assert.equal(pack.vdf.find((r) => r.id === "VDF_CHIP")?.light, "ok");
  assert.equal(pack.vdf.find((r) => r.id === "VDF_REST")?.value, "VIA_db_part3_rest");
});

test("CACHE VRN close snap is TAB2 71 · TAB4 27 · v0110 · NLP 黃", () => {
  const sim = simulateVrnClose();
  assert.equal(sim.basics.length, 71, `TAB2 ${sim.basics.length}`);
  assert.equal(sim.finances.length, 27, `TAB4 ${sim.finances.length}`);
  const snap = vrnCloseSnap({
    files: sim.files,
    basics: sim.basics,
    finances: sim.finances,
    summaries: sim.summaries,
    confirmNlp: false,
    repairNote: sim.note,
  });
  assert.equal(snap.find((r) => r.id === "VRN_TAB2")?.value, "71");
  assert.equal(snap.find((r) => r.id === "VRN_TAB4")?.value, "27");
  assert.equal(snap.find((r) => r.id === "VRN_NLP")?.value, "黃");
  assert.match(snap.find((r) => r.id === "VRN_V0110")?.value ?? "", /v0110/);
  assert.ok(sim.files.some((f) => f.status === "bad" && f.stuckStep === "S04"));
});

test("unknown orphan dropped; aliases idle; packages not deleted", () => {
  const iso = isolateRows(REGISTERED_ENGINES);
  assert.equal(iso.find((r) => r.id === "ENG_ORPHAN"), undefined);
  const aliases = iso.filter((r) => r.value === "ALIAS");
  assert.ok(aliases.length >= 4);
  assert.ok(aliases.every((r) => r.light === "idle"));
  assert.ok(aliases.some((r) => r.id === "VRN_XVAL"));
  assert.ok(aliases.some((r) => r.id === "VRN_PDF"));
});

test("vdfCloseSnap stays fail-closed when NET off", () => {
  const pack = cacheClosePack();
  const rows = vdfCloseSnap({
    rows: pack.rows,
    metrics: pack.metrics,
    aetfNote: pack.vdf.find((r) => r.id === "VDF_AEA")?.value ?? "",
    cnsNote: pack.vdf.find((r) => r.id === "VDF_CNS")?.value ?? "",
    cnsN: 1,
    revNote: pack.vdf.find((r) => r.id === "VDF_REV")?.value ?? "",
    revN: 1,
    confirmNet: false,
  });
  assert.equal(rows.find((r) => r.id === "VDF_G1")?.value, "關");
  assert.equal(rows.find((r) => r.id === "VDF_G1")?.light, "ok");
});
