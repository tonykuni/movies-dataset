import assert from "node:assert/strict";
import { test } from "node:test";
import {
  aggregateLanes,
  analyzeTopo,
  authorized,
  AST_LAYERS,
  blocksDownstream,
  DCT_CATALOG,
  dispatchDryRun,
  downwardGates,
  mintToken,
  planDigest,
  unboundLocal,
} from "./govern.ts";
import type { Capability } from "./mother-ops.ts";

test("dual-gate token needs format AND commit AND plan digest", () => {
  const tok = mintToken(new Date("2026-09-05T04:30:00"));
  assert.equal(authorized(tok, true), true);
  assert.equal(authorized(tok, false), false);
  assert.equal(authorized("==VEM-APPROVE==20260905_103000-abcdef", true), false);
  assert.ok(tok.endsWith(planDigest()));
});

test("hard fail blocks; soft RED does not unless strict", () => {
  assert.equal(blocksDownstream("FAILED", "RED", false), true);
  assert.equal(blocksDownstream("OK", "RED", false), false);
  assert.equal(blocksDownstream("OK", "RED", true), true);
});

test("default topo has no cycle; unresolved self-dep is reported", () => {
  const a = analyzeTopo();
  assert.equal(a.cycles.length, 0);
  assert.equal(a.unresolved.length, 0);
  const caps: Capability[] = [
    { urn: "A", name: "A", kind: "X", mutating: false, dependsOn: ["A", "Z"], script: "a.py" },
  ];
  const b = analyzeTopo(caps);
  assert.ok(b.selfLoops.includes("A"));
  assert.ok(b.unresolved.some((u) => u.includes("Z")));
});

test("D01–D08: APPLY skipped, D06 warn honest, no FAIL", () => {
  const g = downwardGates();
  assert.equal(g.length, 8);
  assert.equal(g.find((x) => x.code === "D03")?.status, "PASS");
  assert.equal(g.find((x) => x.code === "D06")?.status, "WARN");
  assert.equal(g.find((x) => x.code === "D08")?.status, "WARN");
  assert.equal(g.filter((x) => x.status === "FAIL").length, 0);
});

test("DCT catalog all twenty FIXED", () => {
  assert.equal(DCT_CATALOG.length, 20);
  assert.ok(DCT_CATALOG.every((d) => d.status === "FIXED"));
});

test("analysis RED does not hijack overall to RED", () => {
  const a = aggregateLanes([
    { kind: "ENV", state: "OK", verdict: "GREEN" },
    { kind: "ANALYSIS", state: "OK", verdict: "RED" },
  ]);
  assert.equal(a.overall, "AMBER");
  const b = aggregateLanes([{ kind: "REPAIR", state: "TIMEOUT", verdict: "TIMEOUT" }]);
  assert.equal(b.overall, "RED");
});

test("dry-run APPLY stays SKIPPED until token+commit", () => {
  const closed = dispatchDryRun();
  assert.ok(closed.some((r) => r.urn.includes("APPLY") && r.state === "SKIPPED"));
  const open = dispatchDryRun({ token: mintToken(), commit: true });
  assert.ok(open.some((r) => r.urn.includes("APPLY") && r.state === "APPLY"));
  assert.ok(open.every((r) => r.state !== "BLOCKED"));
});

test("AST four layers present", () => {
  assert.deepEqual(AST_LAYERS.map((l) => l.id), ["L0", "L1", "L2", "L3"]);
});

test("Name body Load before Store is UnboundLocal; defaults ignored", () => {
  const hits = unboundLocal(
    [
      { id: "x", ctx: "Load", line: 7, where: "defaults" },
      { id: "x", ctx: "Load", line: 10, where: "body" },
      { id: "x", ctx: "Store", line: 11, where: "body" },
      { id: "p", ctx: "Load", line: 9, where: "body" },
    ],
    ["p"],
    [],
  );
  assert.deepEqual(hits, [{ id: "x", load: 10, store: 11 }]);
});
