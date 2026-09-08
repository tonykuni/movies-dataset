import assert from "node:assert/strict";
import { test } from "node:test";
import { hydraRisk, hydraRiskComplete, hydraRiskVrn, hydraRiskClose, processSummary, runProcessPack, runSixLanes, runVrnLanes, runCloseLanes, SIX_LANES, COMPLETE_LANES, VRN_LANES, CLOSE_LANES } from "./processes.ts";

test("local processes run; net lanes stay SKIP", () => {
  const rows = runProcessPack({
    confirmNet: false,
    fredMode: "CACHE",
    vdfRows: 53,
    parquetOk: true,
    vrnPass: 5,
    vrnFail: 1,
  });
  const sum = processSummary(rows);
  assert.equal(sum.fail, 0);
  assert.ok(sum.ran >= 6);
  assert.equal(rows.find((r) => r.id === "P_YF")?.result, "SKIP");
  assert.equal(rows.find((r) => r.id === "P_AK")?.result, "SKIP");
  assert.equal(rows.find((r) => r.id === "P_UNI")?.result, "RAN");
  assert.equal(rows.find((r) => r.id === "P_REV")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_GFF")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_ACCEL")?.result, "RAN");
  assert.equal(rows.find((r) => r.id === "P_CELAEG")?.result, "CACHE");
  assert.match(rows.find((r) => r.id === "P_CELAEG")?.out ?? "", /VIS-SA-CEL-000001/);
  assert.equal(rows.find((r) => r.id === "P_INCR")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_DUCK")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_GAP")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_COPY")?.result, "CACHE");
  assert.match(rows.find((r) => r.id === "P_COPY")?.out ?? "", /不抄新值/);
  assert.equal(rows.find((r) => r.id === "P_AETF")?.result, "SKIP");
  assert.equal(rows.find((r) => r.id === "P_AEA")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_CNS")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_SSOT")?.result, "CACHE");
  assert.match(rows.find((r) => r.id === "P_SSOT")?.out ?? "", /未晉升/);
  assert.equal(rows.find((r) => r.id === "P_METH")?.result, "CACHE");
  assert.match(rows.find((r) => r.id === "P_METH")?.out ?? "", /候審/);
  assert.equal(rows.find((r) => r.id === "P_DICT")?.result, "CACHE");
  assert.match(rows.find((r) => r.id === "P_DICT")?.out ?? "", /券商/);
  assert.equal(rows.find((r) => r.id === "P_PIPE")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_FWD")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_FE")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_TICKER")?.out.includes("2330.TWO"), false);
  assert.match(rows.find((r) => r.id === "P_TICKER")?.out ?? "", /2330\.TW/);
  assert.equal(rows.find((r) => r.id === "P_FN")?.result, "RAN");
  assert.equal(rows.find((r) => r.id === "P_RX")?.result, "RAN");
  assert.match(rows.find((r) => r.id === "P_RX")?.out ?? "", /75\/75/);
  assert.equal(rows.find((r) => r.id === "P_CPL")?.result, "CACHE");
  assert.match(rows.find((r) => r.id === "P_CPL")?.out ?? "", /母機樹缺/);
  assert.equal(rows.find((r) => r.id === "P_XCODE")?.result, "RAN");
  assert.match(rows.find((r) => r.id === "P_XCODE")?.out ?? "", /轉碼 10\/10/);
  assert.match(rows.find((r) => r.id === "P_GIT")?.out ?? "", /tonykuni\/movies-dataset/);
  assert.equal(rows.find((r) => r.id === "P_LOCALDB")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_LOCALDB")?.light, "ok");
  assert.match(rows.find((r) => r.id === "P_LOCALDB")?.out ?? "", /不刪/);
  assert.equal(rows.find((r) => r.id === "P_FRED")?.result, "CACHE");
  assert.equal(rows.find((r) => r.id === "P_PARQ")?.result, "RAN");
  assert.equal(rows.find((r) => r.id === "L3")?.light, "ok");
  assert.match(rows.find((r) => r.id === "L3")?.out ?? "", /21\/21/);
  assert.equal(rows.find((r) => r.id === "P_DIGEST")?.result, "RAN");
});

test("parquet mismatch fails only that process", () => {
  const rows = runProcessPack({
    confirmNet: false,
    fredMode: "CACHE",
    vdfRows: 10,
    parquetOk: false,
    vrnPass: 1,
    vrnFail: 1,
  });
  assert.equal(rows.find((r) => r.id === "P_PARQ")?.result, "FAIL");
  assert.equal(rows.find((r) => r.id === "P_UNI")?.result, "RAN");
});

test("six lanes are hydra-safe and run disjoint jobs", () => {
  const h = hydraRisk();
  assert.equal(h.ok, true);
  assert.equal(SIX_LANES.length, 6);
  assert.equal(new Set(SIX_LANES.map((l) => l.job)).size, 6);
  assert.equal(new Set(SIX_LANES.map((l) => l.write)).size, 6);
  const six = runSixLanes({
    confirmNet: false,
    fredMode: "CACHE",
    vdfRows: 53,
    parquetOk: true,
    vrnPass: 5,
    vrnFail: 1,
    files: [
      {
        id: "a",
        name: "GS-2330.pdf",
        ext: "pdf",
        size: 10,
        lastModified: 1,
        origin: "folder",
        skipDup: false,
        fingerprint: "aa",
        status: "ok",
        stuckStep: null,
        stuckDetail: null,
        steps: {},
      },
    ],
    finances: [
      {
        fileId: "a",
        fileName: "GS-2330.pdf",
        category: "IS",
        statement: "損益",
        item: "營業收入合計",
        dataName: "revenue",
        period: "2024",
        value: 1,
        unit: "十億 TWD",
        confidence: 0.9,
        source: "phase1",
        status: "ok",
      },
    ],
  });
  assert.equal(six.find((r) => r.id === "L0")?.out.includes("無九頭龍"), true);
  assert.equal(six.find((r) => r.id === "L2")?.result, "RAN");
  assert.equal(six.find((r) => r.id === "L5")?.result, "RAN");
  assert.notEqual(six.find((r) => r.id === "L6")?.result, "FAIL");
});

test("complete six lanes are hydra-safe and disjoint from L1–L6", () => {
  const h = hydraRiskComplete();
  assert.equal(h.ok, true);
  assert.equal(COMPLETE_LANES.length, 6);
  const writes = [...SIX_LANES, ...COMPLETE_LANES].map((l) => l.write);
  assert.equal(new Set(writes).size, writes.length);
  const pack = runProcessPack({
    confirmNet: false,
    fredMode: "CACHE",
    vdfRows: 53,
    parquetOk: true,
    vrnPass: 5,
    vrnFail: 1,
  });
  assert.equal(pack.find((r) => r.id === "C0")?.result, "RAN");
  assert.equal(pack.find((r) => r.id === "C1")?.result, "CACHE");
  assert.equal(pack.find((r) => r.id === "C2")?.result, "CACHE");
  assert.equal(pack.find((r) => r.id === "C3")?.result, "CACHE");
  assert.equal(pack.find((r) => r.id === "C4")?.result, "RAN");
  assert.equal(pack.find((r) => r.id === "C5")?.result, "RAN");
  assert.equal(pack.find((r) => r.id === "C4")?.out.includes("唯一總管"), true);
});

test("VRN six lanes are hydra-safe and disjoint from L and C", () => {
  const h = hydraRiskVrn();
  assert.equal(h.ok, true);
  const writes = [...SIX_LANES, ...COMPLETE_LANES, ...VRN_LANES].map((l) => l.write);
  assert.equal(new Set(writes).size, 18);
  const vrn = runVrnLanes({
    confirmNet: false,
    fredMode: "CACHE",
    vdfRows: 53,
    parquetOk: true,
    vrnPass: 5,
    vrnFail: 1,
  });
  assert.equal(vrn.find((r) => r.id === "V0")?.result, "RAN");
  assert.equal(vrn.find((r) => r.id === "V1")?.result, "RAN");
  assert.equal(vrn.find((r) => r.id === "V2")?.result, "RAN");
  assert.equal(vrn.find((r) => r.id === "V3")?.result, "RAN");
  assert.equal(vrn.find((r) => r.id === "V5")?.result, "CACHE");
  assert.equal(vrn.find((r) => r.id === "V6")?.light, "ok");
});

test("VDF close six lanes hydra-safe vs L/C/V and mount accel/net", () => {
  const h = hydraRiskClose();
  assert.equal(h.ok, true);
  const writes = [...SIX_LANES, ...COMPLETE_LANES, ...VRN_LANES, ...CLOSE_LANES].map((l) => l.write);
  assert.equal(new Set(writes).size, 24);
  const d = runCloseLanes({
    confirmNet: false,
    fredMode: "CACHE",
    vdfRows: 53,
    parquetOk: true,
    vrnPass: 5,
    vrnFail: 0,
  });
  assert.equal(d.find((r) => r.id === "D0")?.result, "RAN");
  assert.equal(d.find((r) => r.id === "D1")?.result, "RAN");
  assert.equal(d.find((r) => r.id === "D2")?.result, "CACHE");
  assert.match(d.find((r) => r.id === "D2")?.out ?? "", /fail-closed/);
  assert.equal(d.find((r) => r.id === "D3")?.light, "ok");
  assert.equal(d.find((r) => r.id === "D3")?.result, "CACHE");
  assert.equal(d.find((r) => r.id === "D4")?.result, "RAN");
  assert.equal(d.find((r) => r.id === "D5")?.result, "RAN");
  assert.match(d.find((r) => r.id === "D5")?.out ?? "", /封印/);
  assert.equal(d.find((r) => r.id === "D6")?.result, "RAN");
  const live = runCloseLanes({
    confirmNet: true,
    fredMode: "CACHE",
    vdfRows: 53,
    parquetOk: true,
    vrnPass: 5,
    vrnFail: 0,
  });
  assert.equal(live.find((r) => r.id === "D2")?.result, "RAN");
});

