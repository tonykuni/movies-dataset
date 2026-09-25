/** Newest-first incremental parquet lake. DuckDB read · checkpoint resume · GitHub/mother path. */
import { pairAccels, type AccelLayer } from "./accel.ts";
import { GITHUB_REPO, MOTHER_ROOTS } from "./coordinate.ts";

export const LAKE_REL = "data/vdf/fred";
export const LAKE_FILE = "part-000.parquet";
export const LAKE_GLOB = "part-*.parquet";
export const LAKE_START_YEAR = 2023;
export const PART_ROWS = 250_000;
export const PART_BYTES = 128 * 1024 * 1024;

export type PartitionPolicy = {
  keys: ["year"];
  skipKeys: string[];
  layout: "year|series|date";
  hive: true;
  maxFilesPerYear: number;
  rowGroup: string;
  note: string;
};

/** 只切 year。FRED 2024–2026 三檔；切 series 會變成上百小檔，DuckDB 開檔成本高過掃描。 */
export function partitionPolicy(): PartitionPolicy {
  return {
    keys: ["year"],
    skipKeys: ["series_id", "month", "category"],
    layout: "year|series|date",
    hive: true,
    maxFilesPerYear: 8,
    rowGroup: "year page · sorted series,date · min/max+bloom",
    note: "hive year 謂詞下推 · 年內增量 part-NNN · 不切代號",
  };
}

export type LakeCkpt = {
  startYear: number;
  yearsHave: number[];
  cursorYear: number | null;
  doneSeries: string[];
  aborted: boolean;
  batchesDone: number;
};

export type YearJob = { year: number; action: "SKIP" | "FETCH" | "RESUME" };

export function yearsNewestFirst(startYear: number, endYear: number): number[] {
  const out: number[] = [];
  for (let y = endYear; y >= startYear; y--) out.push(y);
  return out;
}

export function lakeGithubPath(): string {
  return `${GITHUB_REPO}/${LAKE_REL}/year=*/${LAKE_GLOB}`;
}

export function lakeMotherPath(): string {
  return `${MOTHER_ROOTS[0]}\\${LAKE_REL.replace(/\//g, "\\")}\\year=*\\${LAKE_GLOB.replace(/\//g, "\\")}`;
}

export function parquetYearPath(year: number, part = 0, root = LAKE_REL): string {
  const n = String(Math.max(0, part | 0)).padStart(3, "0");
  return `${root}/year=${year}/part-${n}.parquet`;
}

export function nextPartIndex(existing: number[]): number {
  if (!existing.length) return 0;
  return Math.max(...existing) + 1;
}

export function shouldSplitPart(rows: number, bytes: number): boolean {
  return rows >= PART_ROWS || bytes >= PART_BYTES;
}

/** DuckDB hive prune：查詢區間外的 year= 目錄整區不開檔。 */
export function pruneYears(haveYears: number[], sinceYear: number, untilYear: number): { read: number[]; skip: number[] } {
  const read: number[] = [];
  const skip: number[] = [];
  for (const y of [...haveYears].sort((a, b) => b - a)) {
    if (y >= sinceYear && y <= untilYear) read.push(y);
    else skip.push(y);
  }
  return { read, skip };
}

export function duckPruneSql(sinceYear: number, untilYear: number, root = LAKE_REL): string {
  const glob = `${root}/year=*/${LAKE_GLOB}`;
  return [
    "SET parquet_metadata_cache=true",
    `SELECT series_id, max(obs_date) AS last_date, arg_max(value, obs_date) AS last_value FROM read_parquet('${glob}', hive_partitioning=true, union_by_name=false, hive_types={'year': INTEGER}) WHERE year BETWEEN ${sinceYear} AND ${untilYear} GROUP BY series_id`,
  ].join("; ");
}

/** 已有年整區跳過；從最新缺年往舊抓。中斷年 RESUME 該年未完成序列。 */
export function incrPlan(startYear: number, endYear: number, ckpt: LakeCkpt | null): YearJob[] {
  const years = yearsNewestFirst(startYear, endYear);
  const have = new Set(ckpt?.yearsHave ?? []);
  return years.map((year) => {
    if (ckpt?.aborted && ckpt.cursorYear === year) return { year, action: "RESUME" as const };
    if (have.has(year)) return { year, action: "SKIP" as const };
    return { year, action: "FETCH" as const };
  });
}

export function applyYearDone(ckpt: LakeCkpt, year: number): LakeCkpt {
  const yearsHave = ckpt.yearsHave.includes(year) ? ckpt.yearsHave : [...ckpt.yearsHave, year].sort((a, b) => b - a);
  return { ...ckpt, yearsHave, cursorYear: null, doneSeries: [], aborted: false };
}

export function applyAbort(ckpt: LakeCkpt, year: number, doneSeries: string[]): LakeCkpt {
  return { ...ckpt, cursorYear: year, doneSeries: [...doneSeries], aborted: true };
}

export function seriesBatch<T>(items: T[], size: number): T[][] {
  const n = Math.max(1, size | 0);
  const out: T[][] = [];
  for (let i = 0; i < items.length; i += n) out.push(items.slice(i, i + n));
  return out;
}

export function resumeSeries<T extends { seriesId: string }>(all: T[], done: string[]): T[] {
  const have = new Set(done);
  return all.filter((s) => !have.has(s.seriesId));
}

export function duckScanSql(sinceYear: number, root = LAKE_REL): string {
  const glob = `${root}/year=*/${LAKE_GLOB}`;
  return `SELECT series_id, max(obs_date) AS last_date, arg_max(value, obs_date) AS last_value FROM read_parquet('${glob}', hive_partitioning=true, union_by_name=false, hive_types={'year': INTEGER}) WHERE year >= ${sinceYear} GROUP BY series_id`;
}

export function stackLayers(): AccelLayer[] {
  return ["fetch", "cache", "struct", "compute", "query"];
}

export function stackFactor(): { active: number; planFactor: number; pipeline: boolean; layers: AccelLayer[] } {
  const plan = pairAccels();
  return {
    active: plan.active,
    planFactor: plan.planFactor,
    pipeline: plan.pipeline,
    layers: stackLayers(),
  };
}

export function emptyCkpt(startYear: number): LakeCkpt {
  return { startYear, yearsHave: [], cursorYear: null, doneSeries: [], aborted: false, batchesDone: 0 };
}

export function incrNote(jobs: YearJob[], ckpt: LakeCkpt, batchSize: number): string {
  const fetch = jobs.filter((j) => j.action === "FETCH").map((j) => j.year);
  const skip = jobs.filter((j) => j.action === "SKIP").map((j) => j.year);
  const resume = jobs.filter((j) => j.action === "RESUME").map((j) => j.year);
  const st = stackFactor();
  return `從新往舊 ${jobs.map((j) => j.year).join("→")} · 抓 ${fetch.join("/") || "無"} · 跳過 ${skip.join("/") || "無"} · 續 ${resume.join("/") || "無"} · batch ${batchSize} · 疊加 ×${st.planFactor} · ${lakeGithubPath()}`;
}
