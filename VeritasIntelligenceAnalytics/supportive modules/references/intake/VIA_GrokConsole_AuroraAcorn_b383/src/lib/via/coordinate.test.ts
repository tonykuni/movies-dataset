import assert from "node:assert/strict";
import { test } from "node:test";
import { coordinateLayers, lamp, tri, GITHUB_HEAD, GIT_ROOT, DATA_ROOT } from "./coordinate.ts";

test("lamp is traffic four-color; pending and idle are grey", () => {
  assert.equal(lamp("ok"), "ok");
  assert.equal(lamp("bad"), "bad");
  assert.equal(lamp("warn"), "warn");
  assert.equal(lamp("run"), "warn");
  assert.equal(lamp("pending"), "pending");
  assert.equal(lamp("idle"), "pending");
  assert.equal(tri("pending"), "pending");
});

test("coordinate layers cover github mother data via_core env engine module lib subsystem", () => {
  const layers = coordinateLayers({ engineOk: 3, engineBad: 1, engineWarn: 2, activated: false });
  assert.deepEqual(
    layers.map((l) => l.layer),
    ["GitHub", "Mother", "Data", "via_core", "via_env", "engine", "module", "lib", "subsystem"],
  );
  assert.equal(layers.find((l) => l.layer === "GitHub")?.light, "ok");
  assert.equal(layers.find((l) => l.layer === "Mother")?.light, "warn");
  assert.equal(layers.find((l) => l.layer === "engine")?.light, "bad");
  assert.equal(GITHUB_HEAD, "22a8bbe4");
  assert.match(layers.find((l) => l.layer === "GitHub")?.pc ?? "", /movies-dataset$/);
  assert.match(DATA_ROOT, /Downloads/);
  assert.equal(GIT_ROOT.endsWith("movies-dataset"), true);
});

test("activated coordinate is all green", () => {
  const layers = coordinateLayers({ engineOk: 20, engineBad: 0, engineWarn: 0, activated: true });
  assert.ok(layers.every((l) => l.light === "ok"));
});
