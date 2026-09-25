import assert from "node:assert/strict";
import { test } from "node:test";
import { GOV_ACCEL, LKGC_UV, UV_CLASH_TOOLS, UV_MIRRORS } from "./gov-spec.ts";
import { runGovEnv } from "./gov-env.ts";
import { raceMirrors, runClashTools, uvRaceScript } from "./uv-clash.ts";
import { runProcessPack } from "./processes.ts";

test("three-mirror race keeps LKGC tsinghua winner", () => {
  const r = raceMirrors();
  assert.equal(r.rows.length, 3);
  assert.equal(r.winner, "tsinghua");
  assert.equal(r.lkgcHold, true);
  assert.equal(r.rows[0]!.role, "winner");
  assert.equal(r.rows[1]!.id, "aliyun");
  assert.equal(r.rows[2]!.id, "pypi");
  assert.ok(r.rows[0]!.ms < r.rows[1]!.ms && r.rows[1]!.ms < r.rows[2]!.ms);
  assert.match(r.note, /LKGC 2026-09-06 維持/);
  assert.equal(LKGC_UV.winner, "tsinghua");
  assert.equal(UV_MIRRORS.length, 3);
});

test("eight clash tools from LKGC: pin numpy isolated, never delete", () => {
  assert.equal(UV_CLASH_TOOLS.length, 8);
  assert.equal(GOV_ACCEL.length, 20);
  const ids = new Set(UV_CLASH_TOOLS.map((t) => t.id));
  assert.equal(ids.size, 8);
  const c = runClashTools();
  assert.equal(c.rows.length, 8);
  assert.equal(c.fail, 0);
  assert.ok(c.ok >= 6);
  const pin = c.rows.find((r) => r.id === "UVT-03")!;
  assert.equal(pin.light, "warn");
  assert.match(pin.note, /via_iso_numpy/);
  assert.doesNotMatch(pin.note, /remove|uninstall/i);
  const race = c.rows.find((r) => r.id === "UVT-05")!;
  assert.equal(race.light, "ok");
  const drift = c.rows.find((r) => r.id === "UVT-04")!;
  assert.match(drift.note, /2026-09-06/);
  const script = uvRaceScript();
  assert.match(script, /tuna.tsinghua/);
  assert.match(script, /aliyun/);
  assert.match(script, /pypi.org/);
  assert.doesNotMatch(script, /conda remove|pip uninstall/);
  assert.match(script, /未同意不切鏡/);
});

test("gov env and process pack expose race + eight tools", () => {
  const gov = runGovEnv({ apply: false });
  assert.equal(gov.race.winner, "tsinghua");
  assert.equal(gov.clash.rows.length, 8);
  assert.match(gov.seal.note, /八路/);
  assert.match(gov.seal.note, /競速 tsinghua/);
  assert.ok(gov.issues.some((i) => i.id === "UV_RACE"));
  assert.ok(gov.issues.some((i) => i.id === "UV_CLASH"));
  const pack = runProcessPack({
    confirmNet: false,
    fredMode: "CACHE",
    vdfRows: 53,
    parquetOk: true,
    vrnPass: 5,
    vrnFail: 1,
  });
  const uv = pack.find((r) => r.id === "P_UV");
  assert.ok(uv);
  assert.equal(uv?.result, "CACHE");
  assert.match(uv?.out ?? "", /八路/);
  assert.match(uv?.out ?? "", /via_iso_numpy/);
});
