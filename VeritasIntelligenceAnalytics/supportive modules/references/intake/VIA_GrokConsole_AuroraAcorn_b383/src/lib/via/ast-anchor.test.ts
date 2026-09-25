import assert from "node:assert/strict";
import { test } from "node:test";
import { AST_ANCHORS, DCT_SEALED, astCloseNote, astMode, classifyFix } from "./ast-anchor.ts";

test("py/ts precision; ps1/html elastic; DCT sealed", () => {
  assert.equal(astMode("py"), "precision");
  assert.equal(astMode("ts"), "precision");
  assert.equal(astMode("ps1"), "elastic");
  assert.equal(astMode("html"), "elastic");
  assert.equal(DCT_SEALED, true);
  assert.equal(classifyFix([]), "parallel");
  assert.equal(classifyFix(["L1"]), "sequence");
  assert.equal(AST_ANCHORS.length, 2);
  assert.equal(astCloseNote().light, "ok");
});
