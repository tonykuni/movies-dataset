import assert from "node:assert/strict";
import { test } from "node:test";
import { NPY_MEALS, npyPlanNote, npySlotOf } from "./numpy-matrix.ts";

test("six numpy meals; 1.6 museum never; iso 1.26 not on PATH", () => {
  assert.equal(NPY_MEALS.length, 6);
  const mus = NPY_MEALS.find((m) => m.id === "NPY_MUSEUM")!;
  assert.equal(mus.spawn, "NEVER");
  assert.match(mus.tools, /ArcGIS|LabVIEW|SciPy 0\.9/);
  const iso = NPY_MEALS.find((m) => m.id === "NPY_ISO")!;
  assert.equal(iso.numpy, "1.26.4");
  assert.equal(iso.slot, "via_iso_numpy");
  assert.equal(iso.spawn, "ISO");
  const vdf = npySlotOf("3.13", false);
  assert.equal(vdf.numpy, "2.1.1");
  const old = NPY_MEALS.find((m) => m.id === "NPY_LEGACY")!;
  assert.equal(old.spawn, "PLAN");
  assert.match(npyPlanNote(), /via_iso_numpy/);
  assert.match(npyPlanNote(), /NEVER/);
});
