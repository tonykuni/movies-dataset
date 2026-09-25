import assert from "node:assert/strict";
import { test } from "node:test";
import { hydrateVdf, hydrateVrn, runVdfThenVrn } from "./hydrate.ts";

test("VDF CACHE hydrate fills lake, AEA, revenue, no LIVE", () => {
  const h = hydrateVdf();
  assert.ok(h.rows.length > 20, "fred cache");
  assert.equal(h.rows.every((r) => r.source !== "FRED_LIVE"), true);
  assert.equal(h.done.fail, 0, h.done.seal.note);
  assert.equal(h.done.seal.light, "ok");
  assert.ok(h.aea.rows.length >= 6, "aea kpi");
  assert.ok(h.aea.note.includes("29"));
  assert.ok(h.revSnap.length > 0, "rev");
  assert.ok(h.ended.fail === 0, h.ended.seal.note);
  assert.ok(h.proc.some((p) => p.id.startsWith("D")));
  assert.match(h.revNote, /LIVE 關/);
});

test("VRN CACHE hydrate fills TAB2–4, stub fails TAB1", () => {
  const v = hydrateVrn();
  assert.ok(v.pass >= 6, `pass ${v.pass}`);
  assert.ok(v.fail >= 1, "empty stub");
  assert.ok(v.basics.length >= 6);
  assert.ok(v.basics.some((b) => b.ticker === "2330"));
  assert.ok(v.summaries.length > 0);
  assert.ok(v.finances.length > 0);
  assert.ok(v.files.some((f) => f.status === "bad" && f.name.includes("empty_stub")));
  assert.equal(v.ended.fail, 0, v.ended.steps.map((s) => s.id + s.light).join(","));
});

test("seq VDF then VRN: VDF seal first, 2330 K1 body, 2637 K1 SSOT", () => {
  const s = runVdfThenVrn();
  assert.deepEqual([...s.order], ["VDF", "VRN"]);
  assert.equal(s.done.fail, 0, s.done.seal.note);
  assert.ok(s.rows.length > 20);
  assert.ok(s.vrn.pass >= 6);
  const k2330 = s.vrn.summaries.find((r) => r.fileName.startsWith("GS-2330") && r.slot === "K1");
  assert.match(k2330?.bullet ?? "", /20\.8%/);
  assert.match(k2330?.bullet ?? "", /報告正文/);
  const k2637 = s.vrn.summaries.find((r) => r.fileName.includes("2637") && r.slot === "K1");
  assert.equal(k2637?.grounded, true);
  assert.match(k2637?.bullet ?? "", /VRN_SSOT/);
});
