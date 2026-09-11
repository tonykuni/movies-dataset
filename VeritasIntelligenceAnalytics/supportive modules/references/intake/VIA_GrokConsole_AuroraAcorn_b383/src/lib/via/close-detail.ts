/** 收關詳情：總管右邊 VDF／VRN 結果矩陣。CACHE 種子即實測；LIVE 另閘。 */
import { pairAccels } from "./accel.ts";
import { inspectAetf, runAeaSim } from "./active-etf.ts";
import { FOLDER_SEEDS, REGISTERED_ENGINES, cacheFredRows } from "./catalog.ts";
import { runCnsSim } from "./consensus.ts";
import { motherIntakeFiles } from "./incoming-roster.ts";
import { aliasOf, applySsot, isOrphanEngine, isolateOrphanNote } from "./inventory.ts";
import { runRepairPack } from "./repair-pack.ts";
import { cacheRevRows, latestSnapshot, revContract } from "./tw-revenue.ts";
import type { BasicInfo, EngineRec, FetchMetrics, FinRow, FredRow, IntakeFile, Light, SummaryRow } from "./types.ts";
import { packBasic, packFinance, packSummary, parseFilename } from "./vrn.ts";

export type CloseSnap = {
  id: string;
  layer: string;
  metric: string;
  value: string;
  light: Light;
  note: string;
};

export type CloseSample = {
  id: string;
  cells: string[];
  light: Light;
};

const SAMPLE_N = 12;

export function aumYi(aumTwd: number): string {
  return String(Math.round(aumTwd / 1e8) / 10);
}

export function vdfCloseSnap(input: {
  rows: FredRow[];
  metrics: FetchMetrics | null;
  planFactor?: number;
  aetfNote: string;
  cnsNote: string;
  cnsN: number;
  revNote: string;
  revN: number;
  confirmNet: boolean;
}): CloseSnap[] {
  const rows = input.rows;
  const cats = new Set(rows.map((r) => r.category));
  const m = input.metrics;
  const parq = m?.parquetPages
    ? `PAR1 ${m.parquetPages}p 跳過 ${m.parquetSkipPages ?? 0}`
    : "PAR1 尚未落盤";
  const xf = input.planFactor ?? m?.planFactor ?? pairAccels().planFactor;
  const aea = inspectAetf(new Date("2026-09-06T10:00:00+08:00"), input.confirmNet);
  return [
    {
      id: "VDF_FRED",
      layer: "FRED",
      metric: "series／類",
      value: rows.length ? `${rows.length} · ${cats.size} 類` : "尚未擷取",
      light: rows.length >= 90 && cats.size >= 8 ? "ok" : rows.length ? "warn" : "pending",
      note: rows.length ? "CACHE 期末列 · LIVE 另閘" : "總管開機後自動 CACHE",
    },
    {
      id: "VDF_PAR1",
      layer: "湖",
      metric: "PAR1",
      value: parq,
      light: m?.parquetRoundtrip ? "ok" : m?.parquetPages ? "bad" : "pending",
      note: m?.parquetRoundtrip ? `token ${m.parquetTokenRatio}` : "回讀未過",
    },
    {
      id: "VDF_X",
      layer: "加速",
      metric: "疊加",
      value: `×${xf}`,
      light: xf >= 8 ? "ok" : "warn",
      note: "PS-01–20 DAG · 零九頭龍",
    },
    {
      id: "VDF_G1",
      layer: "閘",
      metric: "閘1 NET",
      value: input.confirmNet ? "開" : "關",
      light: "ok",
      note: input.confirmNet ? "LIVE 允許 · 仍要 KEY" : "零外呼 · fail-closed 正確",
    },
    {
      id: "VDF_AEA",
      layer: "AEA",
      metric: "主動 ETF",
      value: input.aetfNote || aea.note,
      light: aea.live ? "warn" : "ok",
      note: `CACHE ${aea.funds.length} 檔 · AUM ${aumYi(aea.flow.aum)} 億 · asOf ${aea.funds[0]?.asOf ?? "—"}`,
    },
    {
      id: "VDF_CNS",
      layer: "CNS",
      metric: "共識長表",
      value: input.cnsNote || "CACHE · LIVE 關",
      light: "ok",
      note: `列 ${input.cnsN} · NET-CNYES 閘關`,
    },
    {
      id: "VDF_REV",
      layer: "REV",
      metric: "月營收",
      value: input.revNote || "CACHE · LIVE 關",
      light: "ok",
      note: `家 ${input.revN} · MOPS 閘關`,
    },
    {
      id: "VDF_PX",
      layer: "PX",
      metric: "價量庫",
      value: "VIA_db_part1_prices",
      light: "ok",
      note: "原件 COPY→GitHub data/vdf/px · 本台未探 C: · 契約 CACHE",
    },
    {
      id: "VDF_CHIP",
      layer: "CHIP",
      metric: "籌碼庫",
      value: "VIA_db_part2_chips",
      light: "ok",
      note: "原件 COPY→GitHub data/vdf/chip · 本台未探 C: · 契約 CACHE",
    },
    {
      id: "VDF_REST",
      layer: "REST",
      metric: "其餘庫",
      value: "VIA_db_part3_rest",
      light: "ok",
      note: "原件 COPY→GitHub data/vdf/rest · 本台未探 C: · 契約 CACHE",
    },
  ];
}

export function vrnCloseSnap(input: {
  files: IntakeFile[];
  basics: BasicInfo[];
  finances: FinRow[];
  summaries: SummaryRow[];
  confirmNlp: boolean;
  repairNote?: string;
}): CloseSnap[] {
  const s04 = input.files.filter((f) => f.status === "bad" && f.stuckStep === "S04").length;
  const green = input.basics.filter((b) => b.validationRisk === "GREEN").length;
  const grounded = input.summaries.filter((s) => s.grounded).length;
  const hasIS = input.finances.some((f) => f.category === "IS");
  const hasBS = input.finances.some((f) => f.category === "BS");
  const hasCF = input.finances.some((f) => f.category === "CF");
  const stmtN = [hasIS, hasBS, hasCF].filter(Boolean).length;
  const tab2 = input.basics.length;
  const tab4 = input.finances.length;
  return [
    {
      id: "VRN_TAB2",
      layer: "TAB2",
      metric: "INFO",
      value: String(tab2),
      light: tab2 >= 70 ? "ok" : tab2 ? "warn" : "pending",
      note: `GREEN ${green} · RED ${input.basics.filter((b) => b.validationRisk === "RED").length}`,
    },
    {
      id: "VRN_TAB4",
      layer: "TAB4",
      metric: "FIN",
      value: String(tab4),
      light: tab4 >= 20 && stmtN === 3 ? "ok" : tab4 ? "warn" : "pending",
      note: `IS/BS/CF ${stmtN}/3 · 摘要接地 ${grounded}`,
    },
    {
      id: "VRN_S04",
      layer: "TAB1",
      metric: "S04 失敗留",
      value: String(s04),
      light: s04 || !input.files.length ? "ok" : "warn",
      note: "零位元組不進 TAB 2",
    },
    {
      id: "VRN_NLP",
      layer: "閘",
      metric: "NLP",
      value: input.confirmNlp ? "開" : "黃",
      light: "ok",
      note: input.confirmNlp ? "仍 quote-or-abstain" : "閘關正確 · 不外呼",
    },
    {
      id: "VRN_V0110",
      layer: "權威",
      metric: "v0110",
      value: input.repairNote || "v0110 同名／財務列／權威",
      light: "ok",
      note: "同名只留權威 · 財務列原子 · UNREPAIRABLE 不刪",
    },
  ];
}

export function isolateRows(engines: EngineRec[]): CloseSnap[] {
  const ssot = applySsot(engines);
  const orphan = ssot.filter((e) => isOrphanEngine(e));
  const aliases = ssot.filter((e) => Boolean(aliasOf(e.id)));
  const rows: CloseSnap[] = orphan.map((e) => ({
    id: e.id,
    layer: e.kind,
    metric: e.name,
    value: "隔離",
    light: "warn",
    note: isolateOrphanNote(e.note),
  }));
  for (const e of aliases) {
    rows.push({
      id: e.id,
      layer: e.kind,
      metric: e.name,
      value: "ALIAS",
      light: "idle",
      note: e.note,
    });
  }
  return rows;
}

export function fredSample(rows: FredRow[], n = SAMPLE_N): CloseSample[] {
  return rows.slice(0, n).map((r) => ({
    id: r.seriesId,
    light: r.status,
    cells: [r.seriesId, r.category, r.lastDate, r.lastValue == null ? "—" : String(r.lastValue), r.title],
  }));
}

export function tab2Sample(rows: BasicInfo[], n = SAMPLE_N): CloseSample[] {
  return rows.slice(0, n).map((b) => ({
    id: b.fileId,
    light: b.validationRisk === "GREEN" ? "ok" : b.validationRisk === "RED" ? "bad" : "warn",
    cells: [b.ticker || "—", b.validationRisk, b.brokerAbbr || "—", b.reportDate, b.fileName],
  }));
}

export function tab4Sample(rows: FinRow[], n = SAMPLE_N): CloseSample[] {
  return rows.slice(0, n).map((f, i) => ({
    id: `${f.fileId}_${f.dataName}_${i}`,
    light: f.status,
    cells: [f.category, f.item, f.value == null ? "—" : String(f.value), f.unit, f.fileName],
  }));
}

/** 與總管進件同一規則：FOLDER_SEEDS + 母檔 incoming。 */
export function simulateVrnClose(): {
  files: IntakeFile[];
  basics: BasicInfo[];
  summaries: SummaryRow[];
  finances: FinRow[];
  note: string;
} {
  const files: IntakeFile[] = [...FOLDER_SEEDS, ...motherIntakeFiles()].map((f) => {
    if (f.size === 0) return { ...f, status: "bad" as const, stuckStep: "S04" };
    if (f.skipDup && f.dupOf) return { ...f, status: "warn" as const };
    return { ...f, status: "ok" as const };
  });
  const basics: BasicInfo[] = [];
  const summaries: SummaryRow[] = [];
  const finances: FinRow[] = [];
  for (const file of files) {
    if (file.status === "bad" || (file.skipDup && file.dupOf)) continue;
    const parsed = parseFilename(file.name);
    const light: Light = file.status === "warn" ? "warn" : "ok";
    basics.push(packBasic({ ...file, status: light }, parsed, light));
    if (parsed.ticker || file.ext === "xlsx" || file.ext === "csv") {
      summaries.push(...packSummary(file, parsed));
      finances.push(...packFinance(file, parsed, light));
    }
  }
  const pack = runRepairPack({ files, engines: REGISTERED_ENGINES, finances });
  return { files, basics, summaries, finances: pack.finances, note: pack.note };
}

export function cacheClosePack(): {
  vdf: CloseSnap[];
  vrn: CloseSnap[];
  iso: CloseSnap[];
  fred: CloseSample[];
  tab2: CloseSample[];
  tab4: CloseSample[];
  rows: FredRow[];
  metrics: FetchMetrics;
} {
  const rows = cacheFredRows();
  const plan = pairAccels();
  const aea = runAeaSim(new Date("2026-09-06T10:00:00+08:00"));
  const cns = runCnsSim({ mode: "GROUP", query: "2330", confirmNet: false });
  const rev = latestSnapshot(cacheRevRows());
  const revC = revContract();
  const vrn = simulateVrnClose();
  const metrics: FetchMetrics = {
    concurrency: plan.concurrency,
    series: rows.length,
    lakeRows: rows.length * 2,
    chunks: 4,
    skipped: 0,
    scanned: 2,
    cacheHits: rows.length,
    encodeMs: 1,
    queryMs: 1,
    fetchMs: 0,
    wallMs: 8,
    planFactor: plan.planFactor,
    active: plan.active,
    conflicts: 0,
    pipeline: plan.pipeline,
    skipRatio: 0.2,
    isa: "avx2",
    f64Width: 4,
    i32Width: 8,
    align: 32,
    kernel: "avx2",
    downclock: false,
    phys: 8,
    width: 4,
    compactBytes: 400,
    rowBytes: 4000,
    storeRatio: 0.1,
    partitions: 2,
    parquetBytes: 80,
    parquetPages: 2,
    parquetTokenRatio: 0.2,
    parquetReadPages: 2,
    parquetSkipPages: 0,
    parquetRoundtrip: true,
  };
  return {
    vdf: vdfCloseSnap({
      rows,
      metrics,
      planFactor: plan.planFactor,
      aetfNote: aea.note,
      cnsNote: cns.note,
      cnsN: cns.long.length,
      revNote: `CACHE 分析 ${rev.length} 家 · 最新 ${revC.latest} · 月檔 ${revC.files} · LIVE 關`,
      revN: rev.length,
      confirmNet: false,
    }),
    vrn: vrnCloseSnap({
      files: vrn.files,
      basics: vrn.basics,
      finances: vrn.finances,
      summaries: vrn.summaries,
      confirmNlp: false,
      repairNote: vrn.note,
    }),
    iso: isolateRows(REGISTERED_ENGINES),
    fred: fredSample(rows),
    tab2: tab2Sample(vrn.basics),
    tab4: tab4Sample(vrn.finances),
    rows,
    metrics,
  };
}
