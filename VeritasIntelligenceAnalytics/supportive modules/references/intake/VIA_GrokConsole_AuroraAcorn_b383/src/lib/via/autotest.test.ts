import assert from "node:assert/strict";
import { test } from "node:test";
import { REGISTERED_ENGINES } from "./catalog.ts";
import { autoTestAll, buildHandover, handoverPanorama, handoverReport, nextDayIso } from "./autotest.ts";

const base = {
  engines: REGISTERED_ENGINES,
  activated: { vdf: false, vrn: false, engine: true, var: false },
  confirmNet: false,
  confirmNlp: false,
  vdfRan: false,
  vdfLive: false,
  vrnRan: false,
  vrnPass: 0,
  vrnFail: 0,
  varRan: false,
};

test("unknown orphan stub is dropped from roster", () => {
  const rows = autoTestAll(base);
  assert.equal(rows.find((r) => r.id === "ENG_ORPHAN"), undefined);
  const inject = rows.find((r) => r.id === "VDF_ENG039");
  assert.equal(inject?.light, "ok");
  assert.equal(inject?.github, "contract");
  const vap = rows.find((r) => r.id === "VAP_MDL001");
  assert.equal(vap?.light, "ok");
});

test("handover has VIA VDF VRN GOV ENG for next day", () => {
  const day = nextDayIso(new Date("2026-09-05T03:00:00Z"));
  const h = buildHandover(autoTestAll(base), day);
  assert.deepEqual(
    h.map((r) => r.system),
    ["VIA", "VDF", "VRN", "GOV", "ENG"],
  );
  assert.ok(h.every((r) => r.tomorrow.includes(day)));
});

test("panorama handover names AEA git splat and tomorrow day", () => {
  const day = "2026-09-08";
  const p = handoverPanorama(day);
  assert.ok(p.some((r) => r.id === "H_AEA" && /00981A/.test(r.tonight)));
  assert.ok(p.some((r) => r.id === "H_REV" && /ENG075/.test(r.tonight)));
  const text = handoverReport(day, []);
  assert.match(text, /foreach \(\$p in \$add\)/);
  assert.match(text, /2026-09-08/);
  assert.match(text, /流=0/);
});

test("dual gate closed is fail-closed green", () => {
  const rows = autoTestAll(base);
  assert.equal(rows.find((r) => r.id === "VIA_GATE")?.light, "ok");
});

test("sealed ctx is all green after dropping unknown orphan", () => {
  const rows = autoTestAll({
    ...base,
    activated: { vdf: true, vrn: true, engine: true, var: true },
    vdfRan: true,
    vrnRan: true,
    vrnPass: 5,
    vrnFail: 1,
    varRan: true,
  });
  assert.equal(rows.filter((r) => r.light === "bad").length, 0);
  assert.equal(rows.find((r) => r.id === "ENG_ORPHAN"), undefined);
  assert.ok(rows.every((r) => r.light === "ok"));
});
