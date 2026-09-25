import assert from "node:assert/strict";
import { test } from "node:test";
import { COMPLETE_LANES, SIX_LANES, VRN_LANES } from "./processes.ts";
import { GOV_ACCEL, GOV_PIPELINES, GOV_REQUIRED_LIBS, UV_CLASH_TOOLS } from "./gov-spec.ts";
import { govPrompt } from "./gov-prompt.ts";
import { hydraRiskGov, libCompleteness, motherPathScript, runGovEnv } from "./gov-env.ts";
import { ENV_PINS } from "./inventory.ts";

test("gov spec: 20 GA, 6 hydra-safe pipelines, libs pinned", () => {
  assert.equal(GOV_ACCEL.length, 20);
  assert.equal(UV_CLASH_TOOLS.length, 8);
  assert.equal(GOV_PIPELINES.length, 6);
  const h = hydraRiskGov();
  assert.equal(h.ok, true, h.note);
  const taken = [...SIX_LANES, ...COMPLETE_LANES, ...VRN_LANES].map((l) => l.write);
  assert.equal(GOV_PIPELINES.some((p) => taken.includes(p.write)), false);
  const libs = libCompleteness(ENV_PINS);
  assert.equal(libs.ok, true, libs.miss.join(","));
  assert.ok(GOV_REQUIRED_LIBS.every((x) => libs.pinned.includes(x)));
});

test("gov prompt is generated from spec and stays editable", () => {
  const zh = govPrompt("zh");
  assert.match(zh, /零九頭龍/);
  assert.match(zh, /via_vap/);
  assert.match(zh, /GA-20/);
  assert.match(zh, /不 spawn/);
  assert.match(govPrompt("en"), /Zero-Hydra|zero cascading|isolate not delete/i);
});

test("runGovEnv: no delete, isolate numpy, three rounds, no apply on host", () => {
  const out = runGovEnv({ apply: false });
  assert.equal(out.rounds.length, 3);
  assert.equal(/conda remove|pip uninstall/i.test(out.script), false);
  assert.match(out.script, /via_iso_numpy/);
  assert.match(out.lockVdf, /polars=1\.9\.0/);
  assert.match(out.lockVdf, /fredapi=/);
  assert.equal(out.seal.light === "bad", false, out.seal.note);
  assert.match(out.uv, /tuna.tsinghua/);
  assert.equal(out.race.winner, "tsinghua");
  assert.equal(out.clash.rows.length, 8);
  assert.match(out.raceScript, /RACE/);
  assert.doesNotMatch(out.raceScript, /conda remove/);
  const apply = runGovEnv({ apply: true });
  assert.match(apply.rounds[1]!.did, /不 spawn/);
  const path = motherPathScript();
  assert.match(path, /VIA_LKGC/);
  assert.match(path, /via_iso_\*/);
  assert.match(path, /venv-via_vdf/);
  assert.match(path, /不進 PATH/);
  assert.match(path, /禁止刪槽/);
  assert.doesNotMatch(path, /conda remove -n|pip uninstall /);
});
