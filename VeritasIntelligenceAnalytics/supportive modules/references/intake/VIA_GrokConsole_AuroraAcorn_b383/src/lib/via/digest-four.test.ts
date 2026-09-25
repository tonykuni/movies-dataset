import assert from "node:assert/strict";
import { test } from "node:test";
import { incomingText } from "./incoming.ts";
import { ADJ_CLOSE_CACHE, buildFourPoints, extractEpsYears, extractTargetPrice } from "./digest-four.ts";
import { vrnUpside } from "./vrn-method.ts";

test("P1 upside uses report TP and CACHE adj close", () => {
  const text = incomingText("GS-2330 台積電_20251130.pdf");
  assert.equal(extractTargetPrice(text), 1450);
  const u = vrnUpside(1450, ADJ_CLOSE_CACHE["2330"]!.adj);
  assert.ok(u !== null && Math.abs(u - 0.2083333333) < 1e-6);
  const four = buildFourPoints(text, "2330");
  const k1 = four.points.find((p) => p.id === "K1")!;
  assert.equal(k1.grounded, true);
  assert.match(k1.text, /20\.8%/);
  assert.match(k1.text, /PE/);
  assert.match(k1.text, /VDF_CACHE/);
});

test("P2 n..n+3 EPS yoy; P3/P4 remainder; K5 empty", () => {
  const text = incomingText("GS-2330 台積電_20251130.pdf");
  const yrs = extractEpsYears(text);
  assert.equal(yrs.length, 4);
  const four = buildFourPoints(text, "2330");
  const k2 = four.points.find((p) => p.id === "K2")!;
  assert.match(k2.text, /YoY/);
  assert.match(k2.text, /主要原因/);
  assert.equal(four.points.find((p) => p.id === "K3")?.grounded, true);
  assert.equal(four.points.find((p) => p.id === "K4")?.grounded, true);
  assert.equal(four.points.find((p) => p.id === "K5")?.grounded, false);
});

test("SSOT tp after VDF adj: 2637 +7.7%, no average", () => {
  const four = buildFourPoints("", "2637", { fileName: "華南投顧-2637-慧洋-KY-1141202.pdf" });
  const k1 = four.points.find((p) => p.id === "K1")!;
  assert.equal(k1.grounded, true);
  assert.match(k1.text, /7\.7%/);
  assert.match(k1.text, /VRN_SSOT/);
  assert.match(k1.text, /72\.4/);
});

test("no TP → no invented upside even if adj exists", () => {
  const four = buildFourPoints("標題: 測試\n沒有目標價", "2330");
  const k1 = four.points.find((p) => p.id === "K1")!;
  assert.equal(k1.grounded, false);
  assert.equal(k1.text, "未提及");
});
