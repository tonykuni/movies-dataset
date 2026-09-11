import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { test } from "node:test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const testRoot = path.dirname(fileURLToPath(import.meta.url));
const engineRoot = path.dirname(testRoot);
const worker = path.join(engineRoot, "node", "ast_reorganizer.mjs");
const fixture = path.join(testRoot, "fixtures", "broken.md");

test("AST signature preserves code and links", () => {
  const output = execFileSync(process.execPath, [worker, "signature", fixture], { encoding: "utf8" });
  const signature = JSON.parse(output);
  assert.equal(signature.codeBlocks[0].lang, "python");
  assert.equal(signature.links[0].url, "missing.md");
  assert.match(signature.parser, /remark-gfm/);
});

test("AST validate returns ok", () => {
  const output = execFileSync(process.execPath, [worker, "validate", fixture], { encoding: "utf8" });
  assert.equal(JSON.parse(output).ok, true);
});
