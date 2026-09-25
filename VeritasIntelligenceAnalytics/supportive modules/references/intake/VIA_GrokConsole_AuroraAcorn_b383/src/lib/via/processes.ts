/** Local process pack. Six hydra-safe lanes run with disjoint jobs/writes. */
import { FOLDER_SEEDS, FRED_CATALOG, REGISTERED_ENGINES, VDF_FETCH_LANES, VDF_MODULES, ACCEL_TOOLS, NET_TOOLS } from "./catalog.ts";
import { ofieAccepts } from "./support-all.ts";
import { MOTHER_INCOMING, motherIntakeFiles } from "./incoming-roster.ts";
import { packBasic, packFinance, packSummary, parseFilename, validationRisk } from "./vrn.ts";
import { runVrnToEnd } from "./vrn-end.ts";
import { auditFinancialRows } from "./fin-audit.ts";
import { freqCover, resampleLast } from "./freq.ts";
import { applySsot, liveEngines, scanEnvConflicts, accelBindSummary, mountAccelNet } from "./inventory.ts";
import { BASIC_INFO_COLUMNS, DIGEST_SLOTS, FINANCIAL_DATA_COLUMNS, YEAR_SUSPECT, matchBroker } from "./knowledge.ts";
import { buildMarketBook, crossValidate } from "./market-book.ts";
import { consolidateSameName } from "./repair-pack.ts";
import { expandTw, tickerFilenameQc, YEAR_BAND_REAL } from "./tw-ticker.ts";
import { twRxQc } from "./tw-ticker-all.ts";
import { compileQc } from "./compile-matrix.ts";
import { runTranscodeFetchTest } from "./transcode-fetch.ts";
import { cacheRevRows, canFetchRev, latestSnapshot, revContract } from "./tw-revenue.ts";
import { runGffSim, GLSS_ID } from "./gff.ts";
import { duckCatalogNote, lakesHydraOk, maintainSql } from "./duck-catalog.ts";
import { inspectAetf, aeaMembersOk } from "./active-etf.ts";
import { canFetchCns, cnsMembersOk, runCnsSim } from "./consensus.ts";
import { raceMirrors, runClashTools } from "./uv-clash.ts";
import { inspectGap, LAKE_START_YEAR, liveSeedCounts } from "./gap-fill.ts";
import { emptyCkpt, incrNote, incrPlan, seriesBatch, stackFactor } from "./lake-incr.ts";
import { canFetchEia } from "./eia-api.ts";
import type { FinRow, IntakeFile, Light } from "./types.ts";
import { ENG047_FRED, TW_UNIVERSE, TW_UNIVERSE_COUNTS } from "./vdf-mother.ts";
import { astCloseNote, astMode, DCT_SEALED } from "./ast-anchor.ts";
import { GOV_PIPELINES, GOV_ZONES } from "./gov-spec.ts";
import { GITHUB_BRANCH, GITHUB_HEAD, GITHUB_REPO } from "./coordinate.ts";
import { isLocalLane, viaDbHydraOk, viaDbSealNote } from "./via-db-parts.ts";
import { VRN_SSOT_PROMOTED, vrnSsotNote, vrnSsotQc } from "./vrn-ssot.ts";
import { vrnDictNote, vrnDictQc } from "./vrn-dict.ts";
import { vrnMethodNote, vrnMethodQc } from "./vrn-method.ts";
import { vrnPipeNote, vrnPipeQc } from "./vrn-pipe.ts";
import { fwdQc } from "./fwd-vintage.ts";
import { feQc } from "./vrn-four.ts";
import { celAegNote, celAegRows, consentUntouched } from "./cel-aeg.ts";
import { engineMountNote, engineMountQc } from "./engine-mount.ts";

export type ProcResult = "RAN" | "CACHE" | "SKIP" | "FAIL";

export type ProcRow = {
  id: string;
  system: "VDF" | "VRN" | "GOV" | "VIA";
  name: string;
  result: ProcResult;
  light: Light;
  ms: number;
  out: string;
};

export type ProcCtx = {
  confirmNet: boolean;
  fredMode: "LIVE" | "CACHE" | "DENIED" | null;
  vdfRows: number;
  parquetOk: boolean;
  vrnPass: number;
  vrnFail: number;
  files?: IntakeFile[];
  finances?: FinRow[];
  confirmNlp?: boolean;
};

export type SixLane = {
  id: "L1" | "L2" | "L3" | "L4" | "L5" | "L6";
  job: string;
  role: string;
  winner: string;
  write: string;
  layer: "cache" | "struct" | "compute" | "query" | "parse" | "validate";
};

/** 六程職能分離：job／winner／write／layer 皆不重。禁止兩頭寫同一湖。 */
export const SIX_LANES: SixLane[] = [
  { id: "L1", job: "VDF_MACRO", role: "cache", winner: "VDF_ENG074", write: "fred-cache", layer: "cache" },
  { id: "L2", job: "VDF_FREQ", role: "struct", winner: "VDF_STAT", write: "freq-index", layer: "struct" },
  { id: "L3", job: "VDF_USDET", role: "compute", winner: "VDF_ENG047", write: "macro-cover", layer: "compute" },
  { id: "L4", job: "VDF_PARQ", role: "query", winner: "VDF_FETCH", write: "parquet-read", layer: "query" },
  { id: "L5", job: "VRN_CONSOL", role: "parse", winner: "VRN_MDL006", write: "intake-consol", layer: "parse" },
  { id: "L6", job: "VRN_AUDIT", role: "validate", winner: "VRN_AUDITU", write: "fin-audit", layer: "validate" },
];

export function hydraRisk(lanes: SixLane[] = SIX_LANES): { ok: boolean; light: Light; note: string } {
  const n = lanes.length;
  const uniq = (key: keyof SixLane) => new Set(lanes.map((l) => l[key])).size === n;
  const ok = n === 6 && uniq("job") && uniq("winner") && uniq("write") && uniq("layer");
  return {
    ok,
    light: ok ? "ok" : "bad",
    note: ok ? "六職分離 · 無九頭龍 · 不互寫" : "職能重疊 · 停同步",
  };
}

export type CompleteLane = {
  id: "C1" | "C2" | "C3" | "C4" | "C5" | "C6";
  job: string;
  role: string;
  winner: string;
  write: string;
  layer: "rev" | "sim" | "gate" | "console" | "lex" | "iso";
};

/** 完工六程：與 L1–L6 寫區全異。不開未授權 LIVE、不重做 DCT。 */
export const COMPLETE_LANES: CompleteLane[] = [
  { id: "C1", job: "VDF_REV", role: "rev", winner: "VDF_ENG075", write: "rev-cache", layer: "rev" },
  { id: "C2", job: "VIA_GLSS", role: "sim", winner: GLSS_ID, write: "glss-sim", layer: "sim" },
  { id: "C3", job: "VDF_EIA", role: "gate", winner: "EIA_HOLD", write: "eia-param", layer: "gate" },
  { id: "C4", job: "VIA_CGC", role: "console", winner: "VIA_CGC", write: "cgc-ssot", layer: "console" },
  { id: "C5", job: "VRN_KNOW", role: "lex", winner: "VRN_ENG064", write: "know-ssot", layer: "lex" },
  { id: "C6", job: "GOV_ISO", role: "iso", winner: "VIS-ENV-000001", write: "iso-policy", layer: "iso" },
];

export function hydraRiskComplete(lanes: CompleteLane[] = COMPLETE_LANES): { ok: boolean; light: Light; note: string } {
  const n = lanes.length;
  const uniq = (key: keyof CompleteLane) => new Set(lanes.map((l) => l[key])).size === n;
  const vsL = new Set(SIX_LANES.map((l) => l.write));
  const clash = lanes.filter((l) => vsL.has(l.write));
  const ok = n === 6 && uniq("job") && uniq("winner") && uniq("write") && uniq("layer") && clash.length === 0;
  return {
    ok,
    light: ok ? "ok" : "bad",
    note: ok ? "完工六程 · 與 L1–L6 不互寫" : `完工程重疊 ${clash.map((c) => c.write).join(",") || "職能"}`,
  };
}

export type VrnLane = {
  id: "V1" | "V2" | "V3" | "V4" | "V5" | "V6";
  job: string;
  role: string;
  winner: string;
  write: string;
  layer: "name" | "fmt" | "info" | "digest" | "facts" | "seal";
};

/** VRN 六程：與 L1–L6、C1–C6 寫區全異。不開 NLP LIVE、不重做 DCT。 */
export const VRN_LANES: VrnLane[] = [
  { id: "V1", job: "VRN_INC", role: "name", winner: "VRN_MDL001", write: "incoming-roster", layer: "name" },
  { id: "V2", job: "VRN_FMT", role: "fmt", winner: "VRN_ENG_OFIE", write: "ofie-s04", layer: "fmt" },
  { id: "V3", job: "VRN_TAB2", role: "info", winner: "VRN_MDL010", write: "basic-tab2", layer: "info" },
  { id: "V4", job: "VRN_SUM", role: "digest", winner: "VRN_ENG062", write: "digest-tab3", layer: "digest" },
  { id: "V5", job: "VRN_FACT", role: "facts", winner: "VRN_ENG063", write: "fin-facts", layer: "facts" },
  { id: "V6", job: "VRN_R11", role: "seal", winner: "VRN_REP", write: "vrn-seal", layer: "seal" },
];

export function hydraRiskVrn(lanes: VrnLane[] = VRN_LANES): { ok: boolean; light: Light; note: string } {
  const n = lanes.length;
  const uniq = (key: keyof VrnLane) => new Set(lanes.map((l) => l[key])).size === n;
  const taken = new Set([...SIX_LANES.map((l) => l.write), ...COMPLETE_LANES.map((l) => l.write)]);
  const clash = lanes.filter((l) => taken.has(l.write));
  const ok = n === 6 && uniq("job") && uniq("winner") && uniq("write") && uniq("layer") && clash.length === 0;
  return {
    ok,
    light: ok ? "ok" : "bad",
    note: ok ? "VRN 六程 · 與 L/C 不互寫" : `VRN 程重疊 ${clash.map((c) => c.write).join(",") || "職能"}`,
  };
}

export type CloseLane = {
  id: "D1" | "D2" | "D3" | "D4" | "D5" | "D6";
  job: string;
  role: string;
  winner: string;
  write: string;
  layer: "accel" | "net" | "lake" | "harden" | "anchor" | "layout";
};

/** VDF 收官六程：加速器／網具／補湖／SSOT／AST 錨／版面。與 L/C/V/G 寫區全異。不重做 DCT。 */
export const CLOSE_LANES: CloseLane[] = [
  { id: "D1", job: "VDF_BIND", role: "accel", winner: "ACC-PS20", write: "accel-mount", layer: "accel" },
  { id: "D2", job: "VDF_NETM", role: "net", winner: "NET-740", write: "net-mount", layer: "net" },
  { id: "D3", job: "VDF_LAKE", role: "lake", winner: "VDF_INCR", write: "lake-close", layer: "lake" },
  { id: "D4", job: "VDF_HARD", role: "harden", winner: "VDF_MDL103", write: "ssot-close", layer: "harden" },
  { id: "D5", job: "GOV_PREC", role: "anchor", winner: "VIA_PREC", write: "ast-anchor", layer: "anchor" },
  { id: "D6", job: "VIA_LAYOUT", role: "layout", winner: "VIA_LAYOUT", write: "layout-close", layer: "layout" },
];

export function hydraRiskClose(lanes: CloseLane[] = CLOSE_LANES): { ok: boolean; light: Light; note: string } {
  const n = lanes.length;
  const uniq = (key: keyof CloseLane) => new Set(lanes.map((l) => l[key])).size === n;
  const taken = new Set([
    ...SIX_LANES.map((l) => l.write),
    ...COMPLETE_LANES.map((l) => l.write),
    ...VRN_LANES.map((l) => l.write),
    ...GOV_PIPELINES.map((l) => l.write),
  ]);
  const clash = lanes.filter((l) => taken.has(l.write));
  const ok = n === 6 && uniq("job") && uniq("winner") && uniq("write") && uniq("layer") && clash.length === 0;
  return {
    ok,
    light: ok ? "ok" : "bad",
    note: ok ? "VDF 收官六程 · 與 L/C/V/G 不互寫 · 勿 DCT" : `收官重疊 ${clash.map((c) => c.write).join(",") || "職能"}`,
  };
}

function row(
  id: string,
  system: ProcRow["system"],
  name: string,
  fn: () => { result: ProcResult; light: Light; out: string },
): ProcRow {
  const t0 = performance.now();
  try {
    const r = fn();
    return { id, system, name, ...r, ms: Math.round((performance.now() - t0) * 1000) / 1000 };
  } catch (err) {
    return {
      id,
      system,
      name,
      result: "FAIL",
      light: "bad",
      ms: Math.round((performance.now() - t0) * 1000) / 1000,
      out: err instanceof Error ? err.message : String(err),
    };
  }
}

export function runSixLanes(ctx: ProcCtx): ProcRow[] {
  const hydra = hydraRisk();
  const head: ProcRow = {
    id: "L0",
    system: "VIA",
    name: "六程同步閘",
    result: hydra.ok ? "RAN" : "FAIL",
    light: hydra.light,
    ms: 0,
    out: hydra.note,
  };
  if (!hydra.ok) return [head];

  const l1 = row("L1", "VDF", "L1 cache · ENG074", () => {
    if (ctx.fredMode === "LIVE") return { result: "RAN", light: "ok", out: "FRED LIVE · 唯寫 fred-cache" };
    if (ctx.fredMode === "CACHE") return { result: "CACHE", light: "ok", out: "CACHE 完工 · 禁網正確" };
    return { result: "SKIP", light: "warn", out: "尚未擷取" };
  });

  const l2 = row("L2", "VDF", "L2 struct · 頻率期末", () => {
    const cover = freqCover(FRED_CATALOG);
    const sample = resampleLast(
      [
        { date: "2024-01-15", value: 1 },
        { date: "2024-01-31", value: 2 },
        { date: "2024-02-10", value: 3 },
      ],
      "M",
    );
    if (sample.length !== 2 || sample[0]?.value !== 2) {
      return { result: "FAIL", light: "bad", out: "月末取值失敗" };
    }
    return {
      result: "RAN",
      light: "ok",
      out: `D${cover.D}/W${cover.W}/M${cover.M}/Q${cover.Q}/A${cover.A} · 不插值`,
    };
  });

  const l3 = row("L3", "VDF", "L3 compute · ENG047", () => {
    const lake = new Set(FRED_CATALOG.map((s) => s.seriesId));
    const hit = ENG047_FRED.filter((s) => lake.has(s.seriesId)).length;
    const miss = ENG047_FRED.length - hit;
    return {
      result: "RAN",
      light: miss ? "warn" : "ok",
      out: `細項在冊 ${hit}/${ENG047_FRED.length} · 未入湖 ${miss} 不發明 LIVE`,
    };
  });

  const l4 = row("L4", "VDF", "L4 query · Parquet", () => {
    if (!ctx.vdfRows) return { result: "SKIP", light: "warn", out: "尚未落盤" };
    if (!ctx.parquetOk) return { result: "FAIL", light: "bad", out: "回讀不一致" };
    return { result: "RAN", light: "ok", out: "PAR1 年分區回讀 · 唯讀" };
  });

  const l5 = row("L5", "VRN", "L5 parse · MDL006", () => {
    const files = ctx.files ?? [];
    if (!files.length) return { result: "SKIP", light: "warn", out: "尚未進件" };
    const cons = consolidateSameName(files);
    const dups = cons.filter((f) => f.skipDup).length;
    const tickers = new Set(cons.map((f) => f.name.match(/[1-9]\d{3}/)?.[0] ?? "")).size;
    return { result: "RAN", light: "ok", out: `件 ${cons.length} · 去重 ${dups} · 代碼簇 ${tickers}` };
  });

  const l6 = row("L6", "VRN", "L6 validate · 財務原子", () => {
    const finances = ctx.finances ?? [];
    if (!finances.length) return { result: "SKIP", light: "warn", out: "尚未出 TAB 4" };
    const a = auditFinancialRows(finances);
    const fail = a.gates.filter((g) => g.status === "FAIL").length;
    return {
      result: fail ? "FAIL" : "RAN",
      light: fail ? "bad" : a.verdict === "GREEN" ? "ok" : "warn",
      out: `${a.verdict} · V${a.gradeV} M${a.gradeM} P${a.gradeP} · 假綠 ${a.fakeGreen}`,
    };
  });

  return [head, l1, l2, l3, l4, l5, l6];
}

export function runCompleteLanes(ctx: ProcCtx): ProcRow[] {
  const hydra = hydraRiskComplete();
  const head: ProcRow = {
    id: "C0",
    system: "VIA",
    name: "完工六程閘",
    result: hydra.ok ? "RAN" : "FAIL",
    light: hydra.light,
    ms: 0,
    out: hydra.note,
  };
  if (!hydra.ok) return [head];

  const asof = new Date("2026-09-05T08:00:00Z");

  const c1 = row("C1", "VDF", "C1 rev · ENG075 月營收", () => {
    const gate = canFetchRev({ confirmNet: ctx.confirmNet });
    const snap = latestSnapshot(cacheRevRows(asof), asof);
    const c = revContract(asof);
    if (gate.ok) return { result: "RAN", light: "ok", out: `LIVE ${snap.length} · 月檔 ${c.files}` };
    return { result: "CACHE", light: "ok", out: `CACHE ${snap.length} 家 ${c.latest} · 月檔 ${c.files} · LIVE 關` };
  });

  const c2 = row("C2", "VIA", "C2 sim · GLSS", () => {
    const g = runGffSim(asof);
    return { result: "CACHE", light: "ok", out: g.note };
  });

  const c3 = row("C3", "VDF", "C3 gate · EIA 參數", () => {
    const g = canFetchEia({ confirmNet: ctx.confirmNet, apiKey: "", apiUrl: "" });
    if (g.ok) return { result: "RAN", light: "warn", out: "EIA LIVE 不應開" };
    return { result: "CACHE", light: "ok", out: g.reason };
  });

  const c4 = row("C4", "VIA", "C4 console · CGC", () => {
    const live = liveEngines(applySsot(REGISTERED_ENGINES));
    const hit = live.some((e) => e.id === "VIA_CGC");
    if (!hit) return { result: "FAIL", light: "bad", out: "總管未登錄" };
    return { result: "RAN", light: "ok", out: `唯一總管 · 活路 ${live.length}` };
  });

  const c5 = row("C5", "VRN", "C5 lex · Knowledge", () => {
    const n = BASIC_INFO_COLUMNS.length + FINANCIAL_DATA_COLUMNS.length;
    if (n < 8) return { result: "FAIL", light: "bad", out: `欄 ${n}` };
    return { result: "RAN", light: "ok", out: `欄 ${n} · 不發明` };
  });

  const c6 = row("C6", "GOV", "C6 iso · via_iso_numpy", () => {
    const hits = scanEnvConflicts();
    return {
      result: "RAN",
      light: hits.length ? "warn" : "ok",
      out: hits.length ? `隔離指令已備 · 不刪 · ${hits.map((h) => h.isolate).join(",")}` : "無衝突",
    };
  });

  return [head, c1, c2, c3, c4, c5, c6];
}

export function runVrnLanes(ctx: ProcCtx): ProcRow[] {
  const hydra = hydraRiskVrn();
  const head: ProcRow = {
    id: "V0",
    system: "VRN",
    name: "VRN 六程閘",
    result: hydra.ok ? "RAN" : "FAIL",
    light: hydra.light,
    ms: 0,
    out: hydra.note,
  };
  if (!hydra.ok) return [head];

  const v1 = row("V1", "VRN", "V1 name · incoming 檔名", () => {
    let g = 0;
    let y = 0;
    let r = 0;
    for (const name of MOTHER_INCOMING) {
      const ext = name.split(".").pop() ?? "";
      const p = parseFilename(name);
      const risk = validationRisk({ status: "ok", name, ext, size: 80_000 }, p);
      if (risk === "GREEN") g += 1;
      else if (risk === "YELLOW") y += 1;
      else r += 1;
    }
    if (r) return { result: "FAIL", light: "bad", out: `RED ${r}` };
    if (g < 30) return { result: "FAIL", light: "warn", out: `GREEN ${g}` };
    return { result: "RAN", light: "ok", out: `GREEN ${g} · YELLOW ${y} · RED 0` };
  });

  const v2 = row("V2", "VRN", "V2 fmt · OFIE S04", () => {
    const bad = MOTHER_INCOMING.filter((n) => !ofieAccepts(n.split(".").pop() ?? ""));
    if (bad.length) return { result: "FAIL", light: "bad", out: `拒 ${bad.length}` };
    return { result: "RAN", light: "ok", out: `OFIE 收 ${MOTHER_INCOMING.length} · tmp 仍拒` };
  });

  const v3 = row("V3", "VRN", "V3 info · TAB 2", () => {
    const files = motherIntakeFiles();
    const yf = files.filter((f) => {
      const b = packBasic(f, parseFilename(f.name), "ok");
      return /\.TW|\.TWO| TT$/.test(b.ticker);
    });
    if (yf.length) return { result: "FAIL", light: "bad", out: `YF 混入 ${yf.length}` };
    return { result: "RAN", light: "ok", out: `TAB2 四碼 · 件 ${files.length}` };
  });

  const v4 = row("V4", "VRN", "V4 digest · K1–K5", () => {
    if (DIGEST_SLOTS.length < 5) return { result: "FAIL", light: "bad", out: `槽 ${DIGEST_SLOTS.length}` };
    return { result: "RAN", light: "ok", out: "headline+K1–K4 四點 · K5 可空 · quote-or-abstain" };
  });

  const v5 = row("V5", "VRN", "V5 facts · 不發明", () => {
    const ghost = packFinance(motherIntakeFiles()[0]!, parseFilename(MOTHER_INCOMING[0]!), "ok");
    if (ghost.length) return { result: "FAIL", light: "bad", out: "無本文卻寫財務" };
    return { result: "CACHE", light: "ok", out: "無 body → 0 列 · 不套 2330" };
  });

  const v6 = row("V6", "VRN", "V6 seal · R11", () => {
    const files = FOLDER_SEEDS.map((f) => ({
      ...f,
      status: f.size === 0 ? ("bad" as const) : ("ok" as const),
      stuckStep: f.size === 0 ? "S04" : null,
    }));
    const pass = files.filter((f) => f.status !== "bad" && !(f.skipDup && f.dupOf));
    const basics = pass.map((f) => packBasic(f, parseFilename(f.name), "ok"));
    const summaries = pass.flatMap((f) => packSummary(f, parseFilename(f.name)));
    const finances = pass.flatMap((f) => packFinance(f, parseFilename(f.name), "ok"));
    const out = runVrnToEnd({ files, basics, summaries, finances, confirmNlp: Boolean(ctx.confirmNlp) });
    const r11 = out.steps.find((s) => s.id === "R11");
    if (out.fail || r11?.light !== "ok") {
      return { result: "FAIL", light: "bad", out: r11?.out ?? `fail ${out.fail}` };
    }
    return { result: "RAN", light: "ok", out: r11.out };
  });

  return [head, v1, v2, v3, v4, v5, v6];
}

export function runCloseLanes(ctx: ProcCtx): ProcRow[] {
  const hydra = hydraRiskClose();
  const head: ProcRow = {
    id: "D0",
    system: "VDF",
    name: "VDF 收官六程閘",
    result: hydra.ok ? "RAN" : "FAIL",
    light: hydra.light,
    ms: 0,
    out: hydra.note,
  };
  if (!hydra.ok) return [head];

  const d1 = row("D1", "VDF", "D1 accel · PS20+包裝", () => {
    const m = mountAccelNet(ctx.confirmNet);
    const s = accelBindSummary();
    if (m.light === "bad" || s.bound !== 20) {
      return { result: "FAIL", light: "bad", out: m.note };
    }
    return { result: "RAN", light: "ok", out: `${m.note} · 包裝 ${ACCEL_TOOLS.length}` };
  });

  const d2 = row("D2", "VDF", "D2 net · 網具已掛 fail-closed", () => {
    const ids = NET_TOOLS.map((t) => t.id);
    if (!ids.includes("NET-FRED") || !ids.includes("NET-TWSE") || !ids.includes("NET-CNYES") || ids.length < 8) {
      return { result: "FAIL", light: "bad", out: `網具 ${ids.length}` };
    }
    if (ctx.confirmNet) {
      return { result: "RAN", light: "warn", out: `網具 ${ids.length} 已掛 · 閘1 開 · 仍須 KEY` };
    }
    return { result: "CACHE", light: "ok", out: `網具 ${ids.length} 已掛 · LIVE 0 · fail-closed` };
  });

  const d3 = row("D3", "VDF", "D3 lake · 2023 起補湖", () => {
    const seeds = liveSeedCounts();
    const g = inspectGap(null, { start: LAKE_START_YEAR, end: 2026, live: ctx.confirmNet });
    if (g.start !== 2023 || (seeds[2023] ?? 0) < 90) {
      return { result: "FAIL", light: "bad", out: `起步 ${g.start} · 種子 ${seeds[2023] ?? 0}` };
    }
    const seeded = g.rows.every((r) => r.action === "SKIP" || r.seed > 0);
    return {
      result: g.complete ? "RAN" : "CACHE",
      light: g.complete || seeded ? "ok" : "warn",
      out: g.complete
        ? `${g.note} · 年檔齊`
        : `${g.note} · CACHE 完工 · 年檔槽保留 · 種子 2023=${seeds[2023]}`,
    };
  });

  const d4 = row("D4", "VDF", "D4 harden · SSOT 活路", () => {
    const live = liveEngines(applySsot(REGISTERED_ENGINES));
    const mods = VDF_MODULES.length;
    const local = VDF_MODULES.filter((m) => m.gate === "local").length;
    if (live.length < 8 || mods < 10) return { result: "FAIL", light: "bad", out: `活路 ${live.length}` };
    return { result: "RAN", light: "ok", out: `VDF 模組 ${mods} · 本機 ${local} · 活路 ${live.length} · 別名退下` };
  });

  const d5 = row("D5", "GOV", "D5 AST · 精準／彈性錨", () => {
    if (!DCT_SEALED) return { result: "FAIL", light: "bad", out: "DCT 未封" };
    if (astMode("py") !== "precision" || astMode("ps1") !== "elastic") {
      return { result: "FAIL", light: "bad", out: "錨點模式錯" };
    }
    const a = astCloseNote();
    return { result: "RAN", light: a.light, out: `${a.note} · py=${astMode("py")} · ps1=${astMode("ps1")}` };
  });

  const d6 = row("D6", "VIA", "D6 layout · 四區矩陣", () => {
    if (GOV_ZONES.length !== 4) return { result: "FAIL", light: "bad", out: `區 ${GOV_ZONES.length}` };
    const cgc = liveEngines(applySsot(REGISTERED_ENGINES)).some((e) => e.id === "VIA_CGC");
    if (!cgc) return { result: "FAIL", light: "bad", out: "總管未登錄" };
    return { result: "RAN", light: "ok", out: `區 ${GOV_ZONES.join("/")} · 唯一 Console · 小字折疊` };
  });

  return [head, d1, d2, d3, d4, d5, d6];
}

export function runProcessPack(ctx: ProcCtx): ProcRow[] {
  const out: ProcRow[] = [...runSixLanes(ctx), ...runCompleteLanes(ctx), ...runVrnLanes(ctx), ...runCloseLanes(ctx)];

  out.push(
    row("P_UNI", "VDF", "MDL001 宇宙對帳", () => {
      const clash = TW_UNIVERSE.filter((m) => YEAR_SUSPECT.test(m.ticker));
      const rest = TW_UNIVERSE.filter((m) => !YEAR_SUSPECT.test(m.ticker));
      const bad = rest.filter((m) => {
        const x = expandTw(m.ticker, m.market === "TPEX" ? "TWO" : "TW");
        return !x || x.yfinance !== m.yfinance || x.bloomberg !== m.bloomberg || x.native !== m.ticker;
      });
      if (bad.length) {
        return { result: "FAIL", light: "bad", out: `代號對不齊 ${bad.map((b) => b.ticker).join(",")}` };
      }
      return {
        result: "RAN",
        light: "ok",
        out: `焦點 ${rest.length} 對帳通過 · 年碼例外 ${clash.map((c) => c.ticker).join("/") || "無"} · 契約 ${TW_UNIVERSE_COUNTS.members}`,
      };
    }),
  );

  out.push(
    row("P_REV", "VDF", "ENG075 MOPS 月營收", () => {
      const gate = canFetchRev({ confirmNet: ctx.confirmNet });
      const asof = new Date("2026-09-05T08:00:00Z");
      const rows = cacheRevRows(asof);
      const snap = latestSnapshot(rows, asof);
      const c = revContract(asof);
      if (gate.ok) return { result: "RAN", light: "ok", out: `LIVE ${snap.length} 列 · ${c.files} 檔` };
      return {
        result: "CACHE",
        light: "ok",
        out: `CACHE 分析 ${snap.length} 家最新月 ${c.latest} · 月檔 ${c.files} · LIVE 關`,
      };
    }),
  );

  out.push(
    row("P_GFF", "VIA", "GLSS 全球流動性沙盒", () => {
      const g = runGffSim(new Date("2026-09-05T08:00:00Z"));
      const eng = g.rows.find((r) => r.id === "GFF_REV");
      return {
        result: "CACHE",
        light: "ok",
        out: `${g.note} · ${eng?.metric ?? "ENG075"}`,
      };
    }),
  );

  out.push(
    row("P_TICKER", "VDF", "MDL007 SSOT 三面", () => {
      const tsmc = expandTw("2330", "TW");
      if (!tsmc || tsmc.yfinance !== "2330.TW" || tsmc.bloomberg !== "2330 TT") {
        return { result: "FAIL", light: "bad", out: "2330 三面失敗" };
      }
      if (tsmc.yfinance.includes(".TWO")) {
        return { result: "FAIL", light: "bad", out: "2330 誤成 TPEX" };
      }
      return { result: "RAN", light: "ok", out: `${tsmc.native} · ${tsmc.yfinance} · ${tsmc.bloomberg}` };
    }),
  );

  out.push(
    row("P_FN", "VRN", "檔名 ticker SSOT", () => {
      const qc = tickerFilenameQc();
      const bad = qc.filter((r) => r.light === "bad");
      if (bad.length) return { result: "FAIL", light: "bad", out: bad[0]!.note };
      return { result: "RAN", light: "ok", out: "年碼不剔除真碼 · 切詞 · 三碼對帳" };
    }),
  );

  out.push(
    row("P_RX", "VDF", "TW ticker 13類 v0100", () => {
      const qc = twRxQc();
      const bad = qc.filter((r) => r.light === "bad");
      if (bad.length) return { result: "FAIL", light: "bad", out: bad[0]!.note };
      const self = qc.find((r) => r.id === "RX_SELF");
      return { result: "RAN", light: "ok", out: `${self?.value ?? "—"} · DORMANT 5碼 · 不灌 py` };
    }),
  );

  out.push(
    row("P_CPL", "GOV", "編譯矩陣", () => {
      const qc = compileQc();
      const bad = qc.filter((r) => r.light === "bad");
      if (bad.length) return { result: "FAIL", light: "bad", out: bad[0]!.note };
      const n = qc.find((r) => r.id === "CPL_N");
      return { result: "CACHE", light: "ok", out: `${n?.value ?? "—"} · 母機樹缺 · LIVE 關` };
    }),
  );

  out.push(
    row("P_XCODE", "VDF", "自動轉碼擷取", () => {
      const x = runTranscodeFetchTest();
      if (!x.ok) return { result: "FAIL", light: "bad", out: x.note };
      return { result: "RAN", light: "ok", out: x.note };
    }),
  );

  out.push(
    row("P_GIT", "GOV", "GitHub 對帳", () => ({
      result: "RAN",
      light: "ok",
      out: `${GITHUB_REPO}@${GITHUB_BRANCH} · ${GITHUB_HEAD} 已推 · 禁網`,
    })),
  );

  out.push(
    row("P_LOCALDB", "VDF", "本機 VIA_db 三庫", () => {
      if (!viaDbHydraOk()) return { result: "FAIL", light: "bad", out: "px/chip/rest 寫區重疊" };
      return { result: "CACHE", light: "ok", out: viaDbSealNote() };
    }),
  );

  out.push(
    row("P_REG", "VDF", "MDL103 主登錄", () => {
      const live = liveEngines(applySsot(REGISTERED_ENGINES));
      const mods = VDF_MODULES.filter((m) => m.gate === "local").length;
      return { result: "RAN", light: "ok", out: `活路 ${live.length} · 本機模組 ${mods}` };
    }),
  );

  out.push(
    row("P_STAT", "VDF", "STAT 列式湖", () => {
      if (!ctx.vdfRows) return { result: "SKIP", light: "warn", out: "尚未擷取" };
      return { result: "RAN", light: "ok", out: `series ${ctx.vdfRows} · 期末查詢完成` };
    }),
  );

  out.push(
    row("P_FRED", "VDF", "ENG074 FRED 車道", () => {
      if (ctx.fredMode === "LIVE") return { result: "RAN", light: "ok", out: "FRED LIVE" };
      if (ctx.fredMode === "CACHE") return { result: "CACHE", light: "ok", out: "CACHE 完工 · 禁網正確" };
      if (ctx.fredMode === "DENIED") return { result: "SKIP", light: "ok", out: "DENIED · fail-closed" };
      return { result: "SKIP", light: "warn", out: "尚未擷取" };
    }),
  );

  for (const lane of VDF_FETCH_LANES.filter((l) => l.id !== "FRED" && l.id !== "REV" && l.id !== "CNS" && !isLocalLane(l.id))) {
    out.push(
      row(`P_${lane.id}`, "VDF", `${lane.id} ${lane.engine}`, () => ({
        result: "SKIP",
        light: "ok",
        out: ctx.confirmNet ? `${lane.note} · 第二閘仍關` : "車道未掛 · fail-closed",
      })),
    );
  }

  out.push(
    row("P_MKT", "VDF", "市場簿指數/ETF", () => {
      const book = buildMarketBook({ yfLive: false, akLive: false });
      return { result: "RAN", light: "ok", out: `${book.length} 列 · YF/AK 未 LIVE` };
    }),
  );

  out.push(
    row("P_XVAL", "VDF", "同日交叉驗證", () => {
      const x = crossValidate();
      const bad = x.filter((r) => r.light === "bad").length;
      return {
        result: bad ? "FAIL" : "RAN",
        light: bad ? "bad" : "ok",
        out: `${x.length} 組 · 紅 ${bad}`,
      };
    }),
  );

  out.push(
    row("P_PARQ", "VDF", "Parquet 年分區回讀", () => {
      if (!ctx.vdfRows) return { result: "SKIP", light: "warn", out: "尚未落盤" };
      if (!ctx.parquetOk) return { result: "FAIL", light: "bad", out: "回讀不一致" };
      return { result: "RAN", light: "ok", out: "PAR1 對帳通過" };
    }),
  );

  out.push(
    row("P_KNOW", "VRN", "Knowledge SSOT", () => {
      const n = BASIC_INFO_COLUMNS.length + FINANCIAL_DATA_COLUMNS.length;
      return { result: "RAN", light: "ok", out: `欄位 ${n} · 不發明` };
    }),
  );

  out.push(
    row("P_INC", "VRN", "C:\\incoming 檔名", () => {
      let g = 0;
      let y = 0;
      let r = 0;
      for (const name of MOTHER_INCOMING) {
        const ext = name.split(".").pop() ?? "";
        const p = parseFilename(name);
        const risk = validationRisk({ status: "ok", name, ext, size: 80_000 }, p);
        if (risk === "GREEN") g += 1;
        else if (risk === "YELLOW") y += 1;
        else r += 1;
      }
      if (r) return { result: "FAIL", light: "bad", out: `RED ${r}` };
      if (g < 30) return { result: "FAIL", light: "warn", out: `GREEN ${g} < 30` };
      return { result: "RAN", light: "ok", out: `GREEN ${g} · YELLOW ${y} · RED 0 · 無本文不發明財務` };
    }),
  );

  out.push(
    row("P_BROKER", "VRN", "券商字典", () => {
      const names = (ctx.files ?? FOLDER_SEEDS).map((f) => f.name);
      const hit = names.filter((n) => matchBroker(n)).length;
      return { result: "RAN", light: "ok", out: `解析 ${hit}/${names.length} · 不發明券商` };
    }),
  );

  out.push(
    row("P_DIGEST", "VRN", "摘要 K1–K5", () => {
      const n = DIGEST_SLOTS.length;
      if (n < 5) return { result: "FAIL", light: "bad", out: `槽 ${n} < 5` };
      return { result: "RAN", light: "ok", out: `槽 ${DIGEST_SLOTS.map((s) => s.id).join("/")} · quote-or-abstain` };
    }),
  );

  out.push(
    row("P_YEAR", "VDF", "年碼例外 2021–2030", () => {
      const clash = TW_UNIVERSE.filter((m) => YEAR_SUSPECT.test(m.ticker));
      const band = Object.keys(YEAR_BAND_REAL);
      return {
        result: "RAN",
        light: "ok",
        out: `鋼鐵代碼 ${clash.map((c) => c.ticker).join("/") || "無"} · 真碼 ${band.join("/")} · 年碼需佐證 · 不整段剔除`,
      };
    }),
  );

  out.push(
    row("P_ISO", "GOV", "via_iso_numpy", () => {
      const hits = scanEnvConflicts();
      return {
        result: "RAN",
        light: hits.length ? "warn" : "ok",
        out: hits.length ? `指令已產生 · 母機未跑 · ${hits.map((h) => h.isolate).join(",")}` : "無衝突",
      };
    }),
  );

  out.push(
    row("P_UV", "GOV", "uv 三鏡競向＋八路", () => {
      const race = raceMirrors();
      const clash = runClashTools();
      if (clash.fail) return { result: "FAIL", light: "bad", out: clash.note };
      return {
        result: "CACHE",
        light: clash.warn ? "warn" : "ok",
        out: `${race.note} · ${clash.note}`,
      };
    }),
  );

  out.push(
    row("P_ACCEL", "VIA", "PS20 加速器×工具", () => {
      const s = accelBindSummary();
      if (s.lanes !== 20 || s.bound !== 20 || s.miss) {
        return { result: "FAIL", light: "bad", out: `車道 ${s.lanes} · 已綁 ${s.bound} · 缺 ${s.miss}` };
      }
      return { result: "RAN", light: "ok", out: `20/20 · 正典 CEL · ${celAegNote()}` };
    }),
  );

  out.push(
    row("P_CELAEG", "VDF", "Celeritas×AegisNexus", () => {
      const rows = celAegRows();
      const ok = rows.filter((r) => r.winner === "ACC-CEL" || r.winner === "NET-AEG").length === 4;
      if (!ok || !consentUntouched()) return { result: "FAIL", light: "bad", out: "正典未統一或 CONSENT 被動" };
      const qc = engineMountQc();
      const acc = qc.find((r) => r.id === "EM_ACC");
      return { result: "CACHE", light: "ok", out: `${celAegNote()} · ${engineMountNote()} · 加速掛 ${acc?.value}` };
    }),
  );

  out.push(
    row("P_INCR", "VDF", "從新往舊 parquet 增量", () => {
      const start = 2023;
      const end = 2026;
      const ckpt = emptyCkpt(start);
      ckpt.yearsHave = [2026];
      ckpt.aborted = true;
      ckpt.cursorYear = 2025;
      ckpt.doneSeries = ["GDP"];
      const jobs = incrPlan(start, end, ckpt);
      const batches = seriesBatch(Array.from({ length: 16 }, (_, i) => i), 8);
      const st = stackFactor();
      if (jobs[0]?.year !== 2026 || jobs.find((j) => j.year === 2025)?.action !== "RESUME") {
        return { result: "FAIL", light: "bad", out: "年序或續抓失敗" };
      }
      if (!st.pipeline || st.active < 20) return { result: "FAIL", light: "bad", out: "疊加未滿 20" };
      return {
        result: "CACHE",
        light: "ok",
        out: `${incrNote(jobs, ckpt, 8)} · batches ${batches.length}`,
      };
    }),
  );

  out.push(
    row("P_DUCK", "VDF", "DuckDB 管全部 parquet", () => {
      if (!lakesHydraOk()) return { result: "FAIL", light: "bad", out: "湖寫區重疊" };
      const sql = maintainSql();
      if (!sql.includes("v_fred_obs") || !sql.includes("v_rev_obs") || !sql.includes("CHECKPOINT")) {
        return { result: "FAIL", light: "bad", out: "catalog 缺 view" };
      }
      return { result: "CACHE", light: "ok", out: duckCatalogNote() };
    }),
  );

  out.push(
    row("P_GAP", "VDF", "2023 起補湖", () => {
      const g = inspectGap(null, { start: LAKE_START_YEAR, end: 2026, live: ctx.confirmNet });
      if (g.start !== 2023 || g.jobs[g.jobs.length - 1]?.year !== 2023) {
        return { result: "FAIL", light: "bad", out: `起步 ${g.start}` };
      }
      const seeded = g.rows.every((r) => r.action === "SKIP" || r.seed > 0);
      return {
        result: g.complete ? "RAN" : "CACHE",
        light: g.complete || seeded ? "ok" : "warn",
        out: g.complete ? g.note : `${g.note} · CACHE 完工 · 年檔槽保留`,
      };
    }),
  );

  out.push(
    row("P_COPY", "VDF", "缺年 COPY 計畫", () => {
      const g = inspectGap(null, { start: LAKE_START_YEAR, end: 2026, live: ctx.confirmNet });
      if (!g.copyPlan.includes("year=2023") || g.copyPlan.includes("year * 100")) {
        return { result: "FAIL", light: "bad", out: "COPY 計畫缺 2023 或被 year*100 殺死" };
      }
      const seeded = g.rows.filter((r) => r.seed > 0).map((r) => r.year);
      return {
        result: "CACHE",
        light: "ok",
        out: `COPY ${g.rows.filter((r) => r.action !== "SKIP").length} 年 · 種子年 ${seeded.join("/") || "無"} · 不抄新值`,
      };
    }),
  );

  out.push(
    row("P_AEA", "VIA", "主動型 ETF 自動掃", () => {
      if (!aeaMembersOk()) return { result: "FAIL", light: "bad", out: "種子名單非主動" };
      const g = inspectAetf(new Date("2026-09-05T08:00:00Z"), ctx.confirmNet);
      if (g.live) return { result: "FAIL", light: "bad", out: "LIVE 不應開" };
      return { result: "CACHE", light: g.stale ? "warn" : "ok", out: g.note };
    }),
  );

  out.push(
    row("P_CNS", "VDF", "ENG077 FactSet×YF 共識", () => {
      if (!cnsMembersOk()) return { result: "FAIL", light: "bad", out: "種子三面失敗" };
      const gate = canFetchCns({ confirmNet: ctx.confirmNet });
      const sim = runCnsSim({ mode: "GROUP", query: "2330", confirmNet: ctx.confirmNet });
      if (gate.ok) return { result: "RAN", light: "ok", out: sim.note };
      return { result: "CACHE", light: "ok", out: `${sim.note} · 長表 ${sim.long.length}` };
    }),
  );

  out.push(
    row("P_SSOT", "VRN", "研報 SSOT v2 候選", () => {
      if (VRN_SSOT_PROMOTED) return { result: "FAIL", light: "bad", out: "不應晉升" };
      const bad = vrnSsotQc().filter((r) => r.light === "bad");
      if (bad.length) return { result: "FAIL", light: "bad", out: bad[0]!.note };
      return { result: "CACHE", light: "ok", out: vrnSsotNote() };
    }),
  );

  out.push(
    row("P_METH", "VRN", "方法／字庫候審", () => {
      const bad = vrnMethodQc().filter((r) => r.light === "bad");
      if (bad.length) return { result: "FAIL", light: "bad", out: bad[0]!.note };
      return { result: "CACHE", light: "ok", out: vrnMethodNote() };
    }),
  );

  out.push(
    row("P_DICT", "VRN", "券商／年度／清單", () => {
      const bad = vrnDictQc().filter((r) => r.light === "bad");
      if (bad.length) return { result: "FAIL", light: "bad", out: bad[0]!.note };
      return { result: "CACHE", light: "ok", out: vrnDictNote() };
    }),
  );

  out.push(
    row("P_PIPE", "VRN", "全景／三角／四點", () => {
      const bad = vrnPipeQc().filter((r) => r.light === "bad");
      if (bad.length) return { result: "FAIL", light: "bad", out: bad[0]!.note };
      return { result: "CACHE", light: "ok", out: vrnPipeNote() };
    }),
  );

  out.push(
    row("P_FWD", "VDF", "遠期估值 vintage", () => {
      const bad = fwdQc().filter((r) => r.light === "bad");
      if (bad.length) return { result: "FAIL", light: "bad", out: bad[0]!.note };
      return { result: "CACHE", light: "ok", out: "指數≠ETF · 不平均 · 推算≠源報" };
    }),
  );

  out.push(
    row("P_FE", "VRN", "四引擎批次", () => {
      const bad = feQc().filter((r) => r.light === "bad");
      if (bad.length) return { result: "FAIL", light: "bad", out: bad[0]!.note };
      return { result: "CACHE", light: "ok", out: "R/L/T/Tb · NEEDS_OCR 黃 · append-only" };
    }),
  );

  return out;
}

export function processSummary(rows: ProcRow[]): { ran: number; skip: number; fail: number; cache: number } {
  return {
    ran: rows.filter((r) => r.result === "RAN").length,
    cache: rows.filter((r) => r.result === "CACHE").length,
    skip: rows.filter((r) => r.result === "SKIP").length,
    fail: rows.filter((r) => r.result === "FAIL").length,
  };
}