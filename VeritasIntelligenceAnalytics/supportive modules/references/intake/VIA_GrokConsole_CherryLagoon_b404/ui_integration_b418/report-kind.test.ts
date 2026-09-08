import assert from "node:assert/strict";
import test from "node:test";
import { classifyKind, kindExpectsTicker, kindHistogram, tickerFromStem, yearReject } from "./report-kind.ts";

// fixture 全部取自操作員給的 63 份真報告檔名
const CONF = "第三場 AI潮流下展望2026半導體產業趨勢 - 陳子昂";
const CONF2 = "第一場 2026年投資大趨勢 - 華南投顧 -1141201";
const STOCK = "凱基投顧_3665 貿聯-KY_李承泰_20260519";
const IND = "MS-Thermal Solutions 20251007";
const MORN = "20251205兆豐晨會報告(一)-當日新聞與重要訊息評論";
const OS = "凱基日股分析20251205-軍工股及機器人股上漲推升日股收漲";
const DATED = "GS-2382 20231012";
// 2026 是**真實上市代號**(聚亨),名冊逐驗擋不住——必須靠年份守衛
const ROSTER = new Set(["2026", "3665", "2382", "2023"]);

test("年份守衛:展望2026 的 2026 是年份不是代號(名冊有它也一樣)", () => {
  assert.equal(tickerFromStem(CONF, ROSTER).ticker, "");
  assert.equal(tickerFromStem(CONF2, ROSTER).ticker, "");
  assert.ok(tickerFromStem(CONF, ROSTER).rejected.some((r) => r.startsWith("2026")));
});

test("年份守衛不得誤殺真個股與日期件", () => {
  assert.equal(tickerFromStem(STOCK, ROSTER).ticker, "3665");
  assert.equal(tickerFromStem(DATED, ROSTER).ticker, "2382");   // 20231012 裡的 2023 不得被當代號
});

test("年份守衛三道各自講得出理由", () => {
  assert.match(yearReject("GS-2382 20231012", 8, "2023"), /日期字串/);
  assert.match(yearReject("2026年投資大趨勢", 0, "2026"), /後接年份詞/);
  assert.match(yearReject(CONF, CONF.indexOf("2026"), "2026"), /展望/);
  assert.equal(yearReject("MS-3665 20251202", 3, "3665"), "");
});

test("報告型別:五型分得出來,理由印得出來", () => {
  const k = (s: string) => classifyKind(s, tickerFromStem(s, ROSTER).ticker);
  assert.equal(k(STOCK).kind, "個股");
  assert.equal(k(IND).kind, "產業");
  assert.equal(k(MORN).kind, "大盤晨報");
  assert.equal(k(OS).kind, "海外");
  assert.equal(k(CONF).kind, "研討會");
  for (const s of [STOCK, IND, MORN, OS, CONF]) assert.ok(k(s).why.length > 0);
});

test("認不出型別=誠實「其他」,不硬塞個股", () => {
  const r = classifyKind("某某不明檔案", "");
  assert.equal(r.kind, "其他");
  assert.match(r.why, /誠實留白/);
});

test("只有個股型才該有代號(非個股沒代號不是失敗)", () => {
  assert.equal(kindExpectsTicker("個股"), true);
  for (const k of ["產業", "大盤晨報", "海外", "研討會", "其他"] as const) {
    assert.equal(kindExpectsTicker(k), false);
  }
});

test("型別分佈:五型加總=件數", () => {
  const h = kindHistogram([STOCK, IND, MORN, OS, CONF, CONF2], ROSTER);
  assert.equal(h.個股, 1);
  assert.equal(h.研討會, 2);
  assert.equal(Object.values(h).reduce((a, b) => a + b, 0), 6);
});
