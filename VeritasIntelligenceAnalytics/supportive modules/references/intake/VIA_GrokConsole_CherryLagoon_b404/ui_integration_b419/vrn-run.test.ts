import assert from "node:assert/strict";
import test from "node:test";
import {
  ASOF, RUN_CLOSEOUT, RUN_DIGESTS, STALE_DAYS, auditDigest, auditLight, auditTally,
  basisAge, basisState, digestLight, tpSanity,
} from "./vrn-run.ts";

test("目標價合理性:1/50–1/200 的 TP 是抽錯的數,不是預測", () => {
  assert.equal(tpSanity(37.8, 1850.0).state, "TP_SUSPECT");   // MS-2308
  assert.equal(tpSanity(17.81, 937.0).state, "TP_SUSPECT");   // MS-8210
  assert.equal(tpSanity(25.84, 5655.0).state, "TP_SUSPECT");  // JP-3653
  assert.equal(tpSanity(2577.41, 2070.0).state, "OK");        // 凱基 3665 +24.5%
  assert.equal(tpSanity(200.31, 68.6).state, "OK");           // 泓德 +192% 仍在帶內,不亂殺
  assert.equal(tpSanity(null, 100).state, "NA");
  assert.equal(tpSanity(10, 0).state, "NA");
});

test("基準日:37 份全部拿 2026-09-07 比,最舊的報告距今 1062 天", () => {
  assert.equal(ASOF, "2026-09-07");
  assert.equal(basisAge("2023-10-11"), 1062);
  assert.equal(basisState(1062), "STALE_BASIS");
  assert.equal(basisState(basisAge("2026-05-19")), "CURRENT");
  assert.equal(basisState(STALE_DAYS), "CURRENT");
  assert.equal(basisState(STALE_DAYS + 1), "STALE_BASIS");
  assert.equal(basisAge(""), null);
  assert.equal(basisState(null), "UNKNOWN");
});

test("判讀次序:TP 疑誤壓過非當期(連數字都可疑就別談基準日)", () => {
  const a = auditDigest({ file: "MS-8210", ticker: "8210", reportDate: "2025-10-07", tpAdj: 17.81, price: 937 });
  assert.equal(a.verdict, "TP 疑誤");
  assert.equal(basisState(a.days), "STALE_BASIS");   // 它同時也是非當期,但先報 TP 疑誤
  assert.match(a.why, /合理帶/);
});

test("這一跑的 37 份:可信 7 · 非當期 18 · TP 疑誤 3 · 未算 9", () => {
  assert.equal(RUN_DIGESTS.length, 37);
  const t = auditTally();
  assert.deepEqual(t, { 可信: 7, 非當期: 18, "TP 疑誤": 3, 未算: 9 });
  assert.equal(t.可信 + t.非當期 + t["TP 疑誤"] + t.未算, RUN_DIGESTS.length);
});

test("總燈不取巧:有 TP 疑誤就是紅", () => {
  assert.equal(auditLight(), "bad");
  // 只留當期且比值正常的那幾份才會是綠——3665 有兩份,其中 MS-3665(279 天)是非當期,
  // 所以整組取最壞會是黃,這正是判準該有的行為
  assert.equal(auditLight(RUN_DIGESTS.filter((r) => r.file.startsWith("凱基投顧_3665"))), "ok");
  assert.equal(auditLight(RUN_DIGESTS.filter((r) => r.ticker === "3665")), "warn");
  assert.equal(auditLight([]), "pending");
  assert.equal(digestLight("可信"), "ok");
  assert.equal(digestLight("TP 疑誤"), "bad");
  assert.equal(digestLight("非當期"), "warn");
  assert.equal(digestLight("未算"), "pending");
});

test("收尾閘鏡面:三態加總=報告數,段直方圖加總=段數", () => {
  const c = RUN_CLOSEOUT;
  assert.equal(c.done + c.fail + c.pending, c.reports);
  assert.equal(Object.values(c.stages).reduce((a, b) => a + b, 0), c.reports);
  assert.ok(c.cross.checked <= c.cross.of);
  assert.equal(c.ui.pages, c.ui.fresh);
  assert.equal(c.digest.reports, RUN_DIGESTS.length);
});
