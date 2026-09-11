/** 起始年 2023。右邊啟動：查湖缺年／缺序列，從新往舊補。LIVE 仍雙閘。不把 2026 期末抄進 2023。 */
import { FRED_CATALOG } from "./catalog.ts";
import { incrCopySql, PARQUET_LAKES } from "./duck-catalog.ts";
import { LIVE_YEAR_SEEDS } from "./fred-year-seeds.ts";
import { applyYearDone, emptyCkpt, incrPlan, resumeSeries, LAKE_START_YEAR, type LakeCkpt, type YearJob } from "./lake-incr.ts";
import type { Light } from "./types.ts";

export { LAKE_START_YEAR };

export function lakeEndYear(now = new Date()): number {
  return now.getUTCFullYear();
}

export function liveSeedCounts(): Record<number, number> {
  return { ...LIVE_YEAR_SEEDS };
}

export function seedCountByYear(dates?: string[]): Record<number, number> {
  if (!dates) return liveSeedCounts();
  const m: Record<number, number> = {};
  for (const d of dates) {
    const y = Number(String(d).slice(0, 4));
    if (Number.isFinite(y) && y >= 1900) m[y] = (m[y] ?? 0) + 1;
  }
  return m;
}

export type GapRow = {
  year: number;
  action: YearJob["action"] | "SEED";
  light: Light;
  seed: number;
  note: string;
};

export type GapReport = {
  start: number;
  end: number;
  jobs: YearJob[];
  rows: GapRow[];
  seriesLeft: string[];
  catalog: number;
  complete: boolean;
  copyPlan: string;
  note: string;
};

export function inspectGap(
  ckpt: LakeCkpt | null,
  opts: { start?: number; end?: number; seriesIds?: string[]; now?: Date; live?: boolean; seedDates?: string[] } = {},
): GapReport {
  const start = opts.start ?? LAKE_START_YEAR;
  const end = opts.end ?? lakeEndYear(opts.now ?? new Date());
  const seriesIds = opts.seriesIds ?? FRED_CATALOG.map((s) => s.seriesId);
  const ck = ckpt ?? emptyCkpt(start);
  const jobs = incrPlan(start, end, ck);
  const seeds = seedCountByYear(opts.seedDates);
  const seriesLeft = resumeSeries(
    seriesIds.map((seriesId) => ({ seriesId })),
    ck.doneSeries,
  ).map((s) => s.seriesId);
  const rows: GapRow[] = jobs.map((j) => {
    const seed = seeds[j.year] ?? 0;
    const skip = j.action === "SKIP";
    return {
      year: j.year,
      action: skip ? "SKIP" : opts.live ? j.action : "SEED",
      light: skip ? "ok" : opts.live ? "run" : seed > 0 ? "ok" : "warn",
      seed,
      note: skip
        ? "年檔已在湖"
        : opts.live
          ? `LIVE 補年檔 · 種子 ${seed}/${seriesIds.length}`
          : seed > 0
            ? `CACHE 期末齊 ${seed}/${seriesIds.length} · 年檔槽保留待 LIVE`
            : `該年無期末種子 · 年檔槽保留 · 不抄新值`,
    };
  });
  const need = rows.filter((r) => r.action !== "SKIP");
  const complete = need.length === 0 && seriesLeft.length === 0;
  const fred = PARQUET_LAKES[0]!;
  const copyPlan = need.map((r) => incrCopySql(fred, r.year, 0)).join("\n");
  return {
    start,
    end,
    jobs,
    rows,
    seriesLeft,
    catalog: seriesIds.length,
    complete,
    copyPlan,
    note: complete
      ? `${start}–${end} 年檔齊 · ${seriesIds.length} 序列`
      : `缺年 ${need.map((r) => r.year).join("/")} · 種子僅 ${Object.entries(seeds)
          .map(([y, n]) => `${y}:${n}`)
          .join(",") || "無"} · ${opts.live ? "LIVE 補" : "不抄值"}`,
  };
}

export function nextRoundNeeded(gap: GapReport | null): boolean {
  return Boolean(gap && !gap.complete);
}

export function afterCacheCoverage(ckpt: LakeCkpt, endYear: number, haveSeries: number, catalog: number): LakeCkpt {
  if (haveSeries < catalog) return ckpt;
  return applyYearDone(ckpt, endYear);
}

/** 雙閘：閘1 NET × 閘2 下一輪同意。LIVE 另要 32 hex KEY。YES 只開閘2，不開網。 */
export type DualGate = {
  gate1Net: boolean;
  gate2Round: boolean;
  keyOk: boolean;
  live: boolean;
  cacheRound: boolean;
  note: string;
};

export function dualGateNext(input: { confirmNet: boolean; roundConsent: boolean; apiKey: string }): DualGate {
  const gate1Net = Boolean(input.confirmNet);
  const gate2Round = Boolean(input.roundConsent);
  const keyOk = /^[a-f0-9]{32}$/i.test(input.apiKey.trim());
  const live = gate1Net && gate2Round && keyOk;
  const cacheRound = gate2Round && !live;
  let note = "閘2 未同意 · 不補年檔";
  if (live) note = "雙閘+KEY · LIVE 補 2023 年起年檔";
  else if (cacheRound && gate1Net) note = "閘2 同意 · KEY 缺 · CACHE 期末 · 年檔仍待 LIVE";
  else if (cacheRound) note = "閘2 同意 · 閘1 關 · CACHE 期末 · 零外呼";
  return { gate1Net, gate2Round, keyOk, live, cacheRound, note };
}