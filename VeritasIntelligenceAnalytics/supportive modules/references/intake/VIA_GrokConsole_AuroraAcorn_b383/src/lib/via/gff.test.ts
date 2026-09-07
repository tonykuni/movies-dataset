import assert from "node:assert/strict";
import { test } from "node:test";
import { GFF_MEMBERS, gffMembersOk, runGffSim } from "./gff.ts";

test("ENG075 is a GFF member and GFF writes only gff-sim", () => {
  assert.equal(gffMembersOk(), true);
  assert.ok(GFF_MEMBERS.some((m) => m.id === "VDF_ENG075" && m.write === "rev-cache"));
  assert.equal(GFF_MEMBERS.filter((m) => m.write === "glss-sim").length, 1);
  assert.equal(new Set(GFF_MEMBERS.map((m) => m.write)).size, GFF_MEMBERS.length);
});

test("GFF sim is CACHE and does not claim causality", () => {
  const { rows, note } = runGffSim(new Date("2026-09-05T08:00:00Z"));
  assert.match(note, /VIA-GLSS/);
  assert.match(note, /ENG075 在籍/);
  assert.ok(rows.find((r) => r.id === "GFF_REV"));
  assert.equal(rows.find((r) => r.id === "GFF_LINK")?.value, "未因果");
  assert.equal(rows.find((r) => r.id === "GFF_AUM")?.light, "warn");
});
