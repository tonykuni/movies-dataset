import assert from "node:assert/strict";
import { test } from "node:test";
import { GOV_MEGA_BIND, megaBoundText } from "./gov-mega.ts";
import { GOV_LESSONS, runEnvManager } from "./env-manager.ts";

test("EnvManager plans from LKGC, no spawn, isolate numpy", () => {
  const idle = runEnvManager({ consent: false });
  assert.equal(idle.id, "VIA_EnvManager");
  assert.equal(idle.consent, false);
  assert.equal(idle.apply, false);
  assert.equal(idle.gov.race.winner, "tsinghua");
  assert.equal(idle.gov.clash.rows.length, 8);
  assert.ok(idle.envs.some((e) => e.id === "via_core"));
  assert.ok(idle.envs.some((e) => e.id === "via_iso_*"));
  assert.equal(GOV_LESSONS.length, 10);
  assert.match(idle.plan, /待使用者同意/);
  assert.doesNotMatch(idle.plan, /conda remove|pip uninstall/);
  assert.ok(idle.log.some((l) => /CONSENT NO/.test(l)));
  const go = runEnvManager({ consent: true });
  assert.equal(go.apply, true);
  assert.match(go.plan, /同意已錄/);
  assert.match(go.note, /via_iso_numpy|無新槽/);
  assert.ok(go.iso.some((s) => /via_iso_numpy/.test(s.title + s.cmd)));
});

test("mega overlay binds dead-code and EnvManager.py to isolate-not-delete", () => {
  const ids = GOV_MEGA_BIND.map((b) => b.id);
  for (const id of ["B_DEAD", "B_SLOT", "B_UV8", "B_LOG", "B_ENVPY"]) {
    assert.ok(ids.includes(id), id);
  }
  const dead = GOV_MEGA_BIND.find((b) => b.id === "B_DEAD")!;
  assert.match(dead.to, /不刪檔/);
  const slot = GOV_MEGA_BIND.find((b) => b.id === "B_SLOT")!;
  assert.equal(slot.to, "via_iso_*");
  const txt = megaBoundText();
  assert.match(txt, /R3 不刪死碼/);
  assert.match(txt, /日誌當教訓/);
});
