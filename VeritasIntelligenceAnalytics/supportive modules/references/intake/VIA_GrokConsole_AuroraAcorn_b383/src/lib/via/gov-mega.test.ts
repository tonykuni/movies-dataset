import assert from "node:assert/strict";
import { test } from "node:test";
import { DCT_SEALED } from "./ast-anchor.ts";
import { GOV_ACCEL, GOV_INVARIANTS, GOV_PIPELINES, GOV_ZONES } from "./gov-spec.ts";
import { govPrompt } from "./gov-prompt.ts";
import {
  GOV_MEGA_BIND,
  GOV_MEGA_PIPES,
  GOV_MEGA_PROMPT_ZH,
  GOV_MEGA_SEALED,
  GOV_MEGA_TITLE,
  GOV_MEGA_TITLE_EN,
  megaAccelOk,
  megaAstOk,
  megaBoundText,
  megaHydraOk,
  megaSeal,
} from "./gov-mega.ts";

test("mega-prompt is sealed as future-action SSOT", () => {
  assert.equal(GOV_MEGA_SEALED, true);
  assert.match(GOV_MEGA_TITLE, /終極旗艦整合版/);
  assert.match(GOV_MEGA_TITLE_EN, /SSOT Registry/);
  assert.match(GOV_MEGA_PROMPT_ZH, /全景式分析/);
  assert.match(GOV_MEGA_PROMPT_ZH, /AST 雙模錨點/);
  assert.match(GOV_MEGA_PROMPT_ZH, /六個獨立流程/);
  assert.match(GOV_MEGA_PROMPT_ZH, /20 個加速器/);
  assert.match(GOV_MEGA_PROMPT_ZH, /三輪精準修正/);
  assert.match(GOV_MEGA_PROMPT_ZH, /MODULE \/ ENGINE \/ FUNCTION-LIB \/ OTHERS/);
  assert.match(GOV_MEGA_PROMPT_ZH, /via_lib_plotly_v5/);
  assert.match(GOV_MEGA_PROMPT_ZH, /via_engine_cuda12/);
  assert.match(GOV_MEGA_PROMPT_ZH, /Tsinghua/);
  assert.match(GOV_MEGA_PROMPT_ZH, /launch\.ps1/);
  assert.match(GOV_MEGA_PROMPT_ZH, /Parallel-Fixable/);
  assert.ok(GOV_INVARIANTS.some((x) => /Mega-Prompt 已封/.test(x)));
});

test("future actions bind 拔除 to via_iso isolate-not-delete", () => {
  const pull = GOV_MEGA_BIND.find((b) => b.id === "B_PULL");
  assert.ok(pull);
  assert.match(pull!.to, /via_iso_\*/);
  assert.match(pull!.to, /不刪/);
  assert.match(pull!.note, /禁止 conda remove/);
  assert.doesNotMatch(pull!.to, /conda remove|刪 base/);
  const plot = GOV_MEGA_BIND.find((b) => b.id === "B_PLOTLY");
  assert.equal(plot?.to, "via_iso_plotly");
  const cuda = GOV_MEGA_BIND.find((b) => b.id === "B_CUDA");
  assert.equal(cuda?.light, "warn");
  assert.match(cuda!.to, /via_iso_cuda/);
  const bound = megaBoundText();
  assert.match(bound, /拔除＝隔離不刪/);
  assert.doesNotMatch(bound, /conda remove -n|pip uninstall /);
  assert.equal(DCT_SEALED, true);
  assert.equal(GOV_MEGA_BIND.length >= 10, true);
  const dead = GOV_MEGA_BIND.find((b) => b.id === "B_DEAD");
  assert.match(dead!.to, /不刪檔/);
  assert.match(megaSeal().note, /DCT 不動/);
  assert.equal(megaSeal().light, "ok");
});

test("mega six pipelines match G1–G6 hydra writes and 20 GA", () => {
  assert.equal(megaHydraOk(), true);
  assert.equal(megaAccelOk(), true);
  assert.equal(megaAstOk(), true);
  assert.equal(GOV_MEGA_PIPES.length, 6);
  assert.equal(GOV_ACCEL.length, 20);
  assert.deepEqual(
    GOV_MEGA_PIPES.map((p) => p.write),
    GOV_PIPELINES.map((p) => p.write),
  );
  assert.deepEqual(GOV_ZONES, ["MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS"]);
  assert.match(govPrompt("zh"), /未來動作規範/);
  assert.match(govPrompt("en"), /isolate not delete/i);
});
