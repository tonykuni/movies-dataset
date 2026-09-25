import assert from "node:assert/strict";
import { test } from "node:test";
import { VRN_FAIL_N } from "./vrn-fail-cache.ts";
import {
  VRN_CV_SNAP,
  VRN_HG,
  vrnCoverageOnly,
  vrnNovelNumbers,
  vrnPhaseDiff,
  vrnPipeNote,
  vrnPipeQc,
  vrnTickerNotYear,
  vrnYfFromMaster,
} from "./vrn-pipe.ts";
import { GLE_N, gleProbe } from "./vrn-layout.ts";
import { classifyMismatch, compareOne, HG_PLUGIN_ORDER } from "./vrn-xval.ts";
import { FOUR_POINT_SLOTS, summarizeTitleFour } from "./nlp-extract.ts";
import { isTwEquityReport, parseFilename } from "./vrn.ts";
import { capWeightedPe, compareSources, estimateStaleDays, originLabel, roundingInterval } from "./fwd-vintage.ts";
import { feRecon, feRoute, feStageLight, FE_STAGES } from "./vrn-four.ts";
import { VRN_CORE_N, vrnLayoutZone, vrnNlpMounted, vrnTrust } from "./vrn-core.ts";
import { runProcessPack } from "./processes.ts";

test("HardGate PARTIAL 3/7, no activate", () => {
  assert.equal(VRN_HG.seal, "PARTIAL");
  assert.equal(VRN_HG.capable, 3);
  assert.match(VRN_HG.policy, /NO_NETWORK/);
});

test("CV snapshot 22 pass; OCR 0.45% match; missing = p1_only", () => {
  assert.equal(VRN_CV_SNAP.pass, 22);
  assert.equal(vrnPhaseDiff(220, 221), "MATCH");
  assert.equal(vrnPhaseDiff(220, 300), "MISMATCH");
  assert.deepEqual(vrnCoverageOnly(["rev", "ni"], ["rev"]), ["ni"]);
});

test("YF from master not filename; year not ticker; no invented numbers", () => {
  assert.equal(vrnYfFromMaster("2317"), "2317.TW");
  assert.equal(vrnTickerNotYear("2026"), true);
  assert.deepEqual(vrnNovelNumbers("目標價 9999", "目標價 850"), ["9999"]);
  assert.equal(vrnNovelNumbers("850元", "目標價850元").length, 0);
});

test("playbook 15 and P_PIPE cache", () => {
  assert.equal(VRN_FAIL_N, 15);
  const q = vrnPipeQc();
  assert.equal(q.filter((r) => r.light === "bad").length, 0);
  assert.equal(q.find((r) => r.id === "P_HG")?.light, "warn");
  assert.equal(q.find((r) => r.id === "P_RX")?.light, "ok");
  assert.match(q.find((r) => r.id === "P_RX")?.value ?? "", /75\/75/);
  const rows = runProcessPack({ confirmNet: false, fredMode: "CACHE", vdfRows: 0, parquetOk: true, vrnPass: 5, vrnFail: 1 });
  assert.equal(rows.find((r) => r.id === "P_PIPE")?.result, "CACHE");
  assert.match(vrnPipeNote(), /LIVE 關/);
});

test("core 10, NLP 8 CACHE, layout zones, fail-closed trust", () => {
  assert.equal(VRN_CORE_N, 10);
  assert.equal(vrnNlpMounted().ok, 8);
  assert.equal(vrnLayoutZone(0, 10, 1000), "header");
  assert.equal(vrnLayoutZone(950, 990, 1000), "footer");
  assert.equal(vrnLayoutZone(200, 400, 1000), "body");
  assert.equal(vrnTrust({ entityOk: false, periodOk: true, arithOk: true, officialOk: true }).status, "FAIL_CLOSED");
});

test("GLE 31 skipped, title+4, TW-only, unit mismatch, plugin order 7", () => {
  assert.equal(GLE_N, 31);
  assert.equal(gleProbe().filter((p) => p.status === "SKIPPED_UNAVAILABLE").length, 31);
  assert.equal(gleProbe().find((p) => p.name === "adobe_extract_api")?.status, "SKIPPED_POLICY");
  assert.equal(FOUR_POINT_SLOTS.map((s) => s.digest).join("/"), "K1/K2/K3/K4");
  const four = summarizeTitleFour("標題：甲\n目標價：1450元\n評價方式：PE\n基於：產能\n2024 稀釋每股盈餘 10\n2025 稀釋每股盈餘 12\n2026 稀釋每股盈餘 14\n2027 稀釋每股盈餘 16\n主要原因：需求\n其餘甲句。\n其餘乙句。", "2330");
  assert.equal(four.title, "甲");
  assert.equal(four.points.length, 4);
  assert.equal(four.points[0]?.digest, "K1");
  assert.equal(four.points[3]?.digest, "K4");
  assert.equal(isTwEquityReport(parseFilename("GS-2330 台積電_20251130.pdf"), "GS-2330 台積電_20251130.pdf"), true);
  assert.equal(isTwEquityReport(parseFilename("凱基美股分析20251205.pdf"), "凱基美股分析20251205.pdf"), false);
  assert.equal(isTwEquityReport(parseFilename("00981A 主動統一台股增長.pdf"), "00981A 主動統一台股增長.pdf"), false);
  assert.equal(isTwEquityReport(parseFilename("0050 元大台灣50.pdf"), "0050 元大台灣50.pdf"), false);
  assert.equal(classifyMismatch(1_000_000, 1000), "unit_error_thousand");
  assert.equal(compareOne(1000, 1000.5).status, "MATCH");
  assert.deepEqual([...HG_PLUGIN_ORDER], ["ssot", "registry", "runtime_bridge", "env_manager", "ast_planner", "celeritas", "aegis"]);
});

test("vintage: no blend, rounding contains implied, ETF≠index, four-engine routes", () => {
  const iv = roundingInterval(6890.59, 23.1);
  assert.equal(iv.epsLo < iv.eps && iv.eps < iv.epsHi, true);
  assert.equal(compareSources(23.1, 24.0).status, "material_definition_or_timing_conflict");
  assert.equal(compareSources(23.1, 23.2).status, "aligned_not_blended");
  assert.equal(originLabel(false).evidence, "derived_calculation");
  assert.equal(originLabel(true).origin, "reported_forward_eps");
  assert.equal(capWeightedPe([{ mv: 100, earn: 5 }, { mv: 200, earn: 10 }, { mv: 700, earn: 35 }]), 20);
  assert.equal(estimateStaleDays(["2026-01-02", "2026-01-09", "2026-01-16", "2026-01-23"]), 11);
  assert.deepEqual([...FE_STAGES], ["repair", "layout", "text", "table"]);
  assert.equal(feRoute("pdf"), "NATIVE_DOC");
  assert.equal(feRoute("docx"), "MARKITDOWN_BRIDGE");
  assert.equal(feRoute("exe"), "SKIP");
  assert.equal(feStageLight("NEEDS_OCR"), "warn");
  assert.equal(feRecon([220], [221]), "MISMATCH");
  assert.equal(feRecon([220], [220]), "MATCH");
});
