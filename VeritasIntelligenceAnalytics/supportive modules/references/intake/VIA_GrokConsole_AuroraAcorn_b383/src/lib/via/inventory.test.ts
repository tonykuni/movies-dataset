import assert from "node:assert/strict";
import { test } from "node:test";
import { ACCEL_TOOLS, GOV_TOOLS, NET_TOOLS, REGISTERED_ENGINES } from "./catalog.ts";
import { PS20 } from "./accel.ts";
import {
  JOBS,
  accelBindSummary,
  aliasOf,
  applySsot,
  isolationScript,
  isolationSteps,
  liveEngines,
  mountAccelNet,
  parquetAccelPresent,
} from "./inventory.ts";

test("jobs unique; aliases step down; GOV stays 10", () => {
  assert.equal(GOV_TOOLS.length, 10);
  assert.equal(new Set(JOBS.map((j) => j.job)).size, JOBS.length);
  assert.equal(aliasOf("VIA_AETF"), "VIA_AEA");
  assert.equal(aliasOf("VIA_CNYES"), "VIA_CNS");
  assert.equal(aliasOf("VDF_ENG075"), null);
  assert.equal(aliasOf("VDF_MDL000"), "ACC-CEL");
  assert.equal(aliasOf("SUP_MDL740"), "NET-AEG");
  const live = liveEngines(applySsot(REGISTERED_ENGINES));
  assert.ok(live.some((e) => e.id === "VIA_CGC"));
  assert.equal(live.some((e) => e.id === "VIA_AETF"), false);
});

test("PS20 bound 20/20; parquet present; LIVE net stays 0", () => {
  const s = accelBindSummary();
  assert.equal(PS20.length, 20);
  assert.equal(s.lanes, 20);
  assert.equal(s.bound, 20);
  assert.equal(s.miss, 0);
  assert.equal(parquetAccelPresent(), true);
  const m = mountAccelNet(false);
  assert.equal(m.live, 0);
  assert.equal(m.light, "ok");
  assert.ok(ACCEL_TOOLS.length >= 4);
  assert.ok(NET_TOOLS.length >= 8);
});

test("ISO99 isolation does not remove conda packages", () => {
  const steps = isolationSteps();
  assert.ok(steps.some((s) => s.id === "ISO99"));
  assert.doesNotMatch(isolationScript(), /conda remove|pip uninstall/);
  assert.match(isolationScript(), /via_iso_/);
});

test("python engines mount accel; fetchers mount net", () => {
  const py = REGISTERED_ENGINES.filter((e) => /\.py(\b|$)/i.test(e.path) || e.path.endsWith(".py"));
  assert.ok(py.length >= 8);
  assert.equal(py.filter((e) => !e.accel).length, 0);
  const fetchers = REGISTERED_ENGINES.filter((e) =>
    /YFinance|FredMacro|MOPS|CNYES|TWSE OpenAPI|APIDataFetcher|Invoke-VDF-Fetch|FactSet/i.test(`${e.name} ${e.id}`),
  );
  assert.ok(fetchers.length >= 6);
  assert.ok(fetchers.every((e) => e.net || /ALIAS/.test(e.note)));
});
