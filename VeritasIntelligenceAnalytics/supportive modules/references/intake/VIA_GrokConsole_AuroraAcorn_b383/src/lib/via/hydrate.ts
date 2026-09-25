/** 開機即灌 VDF／VRN CACHE · 不 LIVE · 不同步 sleep。 */
import { pairAccels } from "./accel.ts";
import { FOLDER_SEEDS, PIPELINE_STEPS, REGISTERED_ENGINES, cacheFredRows } from "./catalog.ts";
import { completeVdf, cacheMetrics } from "./complete-vdf.ts";
import { packAea } from "./active-etf.ts";
import { runCnsSim } from "./consensus.ts";
import { runGffSim } from "./gff.ts";
import { motherIntakeFiles } from "./incoming-roster.ts";
import { buildMarketBook, crossValidate, etfFlowSum } from "./market-book.ts";
import { decideStep, statusFromSteps } from "./pipeline.ts";
import { runProcessPack } from "./processes.ts";
import { runRepairPack } from "./repair-pack.ts";
import { sealVrn } from "./seal.ts";
import { cacheRevRows, groupAnalysis, latestSnapshot, revContract } from "./tw-revenue.ts";
import { applySsot } from "./inventory.ts";
import type { BasicInfo, FinRow, IntakeFile, Light, SummaryRow } from "./types.ts";
import { packBasic, packFinance, packSummary, parseFilename } from "./vrn.ts";
import { runVdfToEnd } from "./vdf-end.ts";
import { runVrnToEnd } from "./vrn-end.ts";
import { buildProductionPlan, invokeVdfFetchStatus, invokeVdfStatus, sealFetch } from "./vdf-controller.ts";

export function hydrateVrn(seed: IntakeFile[] = [...FOLDER_SEEDS, ...motherIntakeFiles()]) {
  const files: IntakeFile[] = seed.map((f) => ({ ...f, steps: { ...f.steps } }));
  const basics: BasicInfo[] = [];
  const summaries: SummaryRow[] = [];
  const finances: FinRow[] = [];
  for (const file of files) {
    let skipRest = false;
    let aborted = false;
    const steps: Record<string, Light> = {};
    for (const step of PIPELINE_STEPS) {
      const d = decideStep(file, step.id, skipRest);
      skipRest = d.skipRest;
      aborted = d.aborted;
      steps[step.id] = d.light;
      if (d.stuck) {
        file.stuckStep = d.stuck;
        file.stuckDetail = d.detail;
      }
      if (aborted || skipRest) break;
    }
    file.steps = steps;
    file.status = statusFromSteps(steps, aborted, skipRest, false);
    if (file.skipDup && file.dupOf) file.status = "warn";
    if (file.status === "bad" || (file.skipDup && file.dupOf)) continue;
    const parsed = parseFilename(file.name);
    const light: Light = file.status === "warn" ? "warn" : "ok";
    file.status = light;
    basics.push(packBasic(file, parsed, light));
    if (parsed.ticker || file.ext === "xlsx" || file.ext === "csv") {
      summaries.push(...packSummary(file, parsed));
      finances.push(...packFinance(file, parsed, light));
    }
  }
  const pack = runRepairPack({ files, engines: applySsot(REGISTERED_ENGINES), finances });
  const seal = sealVrn(files, basics, summaries, pack.finances);
  const ended = runVrnToEnd({ files, basics, summaries, finances: pack.finances, confirmNlp: false });
  return {
    files,
    basics,
    summaries,
    finances: pack.finances,
    seal,
    ended,
    pass: files.filter((f) => f.status === "ok").length,
    fail: files.filter((f) => f.status === "bad").length,
  };
}

export function runVdfThenVrn() {
  const rows = cacheFredRows();
  const metrics = cacheMetrics(rows.length);
  const plan = pairAccels();
  const prod = buildProductionPlan({ confirmNet: false, apiKey: "", apiUrl: "", startYear: 2023 });
  const sealed = sealFetch(prod, { mode: "CACHE", note: "CACHE 開機", series: rows.length, metrics });
  const ended = runVdfToEnd({ confirmNet: false, mode: "CACHE", rows, metrics });
  const done = completeVdf({ testsPass: ended.fail === 0, confirmNet: false, rows, metrics });
  const book = buildMarketBook({ yfLive: false, akLive: false });
  const revPack = cacheRevRows();
  const revSnap = latestSnapshot(revPack);
  const aea = packAea(new Date(), "");
  const cns = runCnsSim({ mode: "GROUP", query: "2330", confirmNet: false });
  const gff = runGffSim();
  const vrn = hydrateVrn();
  const proc = runProcessPack({
    confirmNet: false,
    fredMode: "CACHE",
    vdfRows: rows.length,
    parquetOk: true,
    vrnPass: vrn.pass,
    vrnFail: vrn.fail,
    files: vrn.files,
    finances: vrn.finances,
  });
  return {
    order: ["VDF", "VRN"] as const,
    note: "先 VDF CACHE 再 VRN 實測 · LIVE 關 · DCT 不動",
    rows,
    metrics,
    pairPlan: plan,
    pairRows: plan.rows,
    lanes: prod.lanes,
    laneResults: sealed.lanes,
    manifest: sealed.manifest,
    ended,
    done,
    book,
    xval: crossValidate(),
    flow: etfFlowSum(book),
    revSnap,
    revGroups: groupAnalysis(revPack),
    revNote: `CACHE 分析 ${revSnap.length} 家 · 最新 ${revContract().latest} · 月檔 ${revContract().files} · LIVE 關`,
    aea,
    cns,
    gff,
    vrn,
    proc,
    gov: invokeVdfStatus(),
    fetchGov: invokeVdfFetchStatus(),
  };
}

export function hydrateVdf() {
  return runVdfThenVrn();
}
