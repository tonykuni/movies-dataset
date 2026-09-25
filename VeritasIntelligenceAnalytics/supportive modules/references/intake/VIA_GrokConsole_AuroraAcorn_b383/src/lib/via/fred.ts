import { createServerFn } from "@tanstack/react-start";
import { readFileSync } from "node:fs";
import { applyCpuToPlan, pairAccels } from "./accel.ts";
import { cacheFredRows, FRED_CATALOG } from "./catalog.ts";
import { encodeLake, lakeStats, queryLatest, type Obs } from "./columnar.ts";
import { encodeParquet, readParquetPayload, writeParquetPayload } from "./parquet.ts";
import { profileFromFlags } from "./cpu.ts";
import { buildFredObsUrl, canFetchFred } from "./fred-api.ts";
import type { FetchMetrics, FredRow } from "./types.ts";

type PullInput = { apiKey: string; startYear: number; apiUrl: string; confirmNet: boolean };

type CachedObs = { exp: number; points: Array<{ date: string; value: number | null }>; live: boolean };

const OBS_CACHE = new Map<string, CachedObs>();
const CACHE_TTL_MS = 5 * 60 * 1000;

async function mapPool<T, R>(items: T[], limit: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length);
  let cursor = 0;
  async function worker() {
    while (cursor < items.length) {
      const i = cursor;
      cursor += 1;
      out[i] = await fn(items[i]);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, () => worker()));
  return out;
}

function cacheKey(seriesId: string, start: string, live: boolean, host: string) {
  return `${live ? "L" : "C"}:${host}:${start}:${seriesId}`;
}

function detectCpu() {
  try {
    const txt = readFileSync("/proc/cpuinfo", "utf8");
    const flags = /flags\s*:\s*(.+)/.exec(txt)?.[1] ?? "";
    const model = /model name\s*:\s*(.+)/.exec(txt)?.[1] ?? "";
    return profileFromFlags(flags, model);
  } catch {
    return profileFromFlags("", "unknown");
  }
}

async function fetchSeries(
  seriesId: string,
  key: string,
  start: string,
  apiUrl: string,
  limit = 8,
): Promise<{ date: string; value: number | null }[]> {
  const url = buildFredObsUrl(apiUrl, seriesId, key, start, limit);
  const run = async () => {
    const res = await fetch(url, { signal: AbortSignal.timeout(7000) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = (await res.json()) as { observations?: Array<{ date: string; value: string }> };
    return (json.observations ?? [])
      .filter((o) => o.value !== ".")
      .map((o) => {
        const v = Number(o.value);
        return { date: o.date, value: Number.isFinite(v) ? v : null };
      });
  };
  try {
    return await run();
  } catch {
    return await run();
  }
}

function pointsFromCacheRow(row: FredRow): Array<{ date: string; value: number | null }> {
  const last = { date: row.lastDate, value: row.lastValue };
  if (row.lastValue == null || row.change == null) return [last];
  const prevDate = row.lastDate.slice(0, 8) + "01";
  return [last, { date: prevDate, value: row.lastValue - row.change }];
}

export const pullFred = createServerFn({ method: "POST" })
  .validator((data: unknown): PullInput => {
    if (typeof data !== "object" || data === null) throw new Error("invalid");
    const rec = data as Record<string, unknown>;
    const apiKey = typeof rec.apiKey === "string" ? rec.apiKey.trim() : "";
    const startYear = Number(rec.startYear) || 2023;
    const apiUrl = typeof rec.apiUrl === "string" ? rec.apiUrl : "";
    const confirmNet = Boolean(rec.confirmNet);
    return { apiKey, startYear, apiUrl, confirmNet };
  })
  .handler(
    async ({
      data,
    }): Promise<{ mode: "LIVE" | "CACHE" | "DENIED"; rows: FredRow[]; note: string; metrics: FetchMetrics }> => {
      const wall0 = performance.now();
      const cpu = detectCpu();
      const plan = applyCpuToPlan(pairAccels(), cpu);
      const key = data.apiKey || (typeof process !== "undefined" ? String(process.env.FRED_API_KEY ?? "").trim() : "");
      const start = `${data.startYear}-01-01`;
      const cachedRows = cacheFredRows();
      const emptyMetrics = (over: Partial<FetchMetrics> = {}): FetchMetrics => ({
        concurrency: plan.concurrency,
        series: FRED_CATALOG.length,
        lakeRows: 0,
        chunks: 0,
        skipped: 0,
        scanned: 0,
        cacheHits: 0,
        encodeMs: 0,
        queryMs: 0,
        fetchMs: 0,
        wallMs: 0,
        planFactor: plan.planFactor,
        active: plan.active,
        conflicts: plan.conflicts,
        pipeline: plan.pipeline,
        skipRatio: 0,
        isa: cpu.isa,
        f64Width: cpu.f64Width,
        i32Width: cpu.i32Width,
        align: cpu.align,
        kernel: cpu.kernel,
        downclock: cpu.downclock,
        phys: 0,
        width: cpu.f64Width,
        compactBytes: 0,
        rowBytes: 0,
        storeRatio: 0,
        partitions: 0,
        parquetBytes: 0,
        parquetPages: 0,
        parquetTokenRatio: 0,
        parquetReadPages: 0,
        parquetSkipPages: 0,
        parquetRoundtrip: false,
        ...over,
      });

      const build = (obs: Obs[], fetchMs: number, cacheHits: number, mode: "LIVE" | "CACHE" | "DENIED", note: string) => {
        const t1 = performance.now();
        const lake = encodeLake(obs, cpu);
        const encodeMs = performance.now() - t1;
        const since = Math.floor(Date.UTC(data.startYear, 0, 1) / 86400000);
        const t2 = performance.now();
        const q = queryLatest(lake, plan.predPush ? since : 0);
        const queryMs = performance.now() - t2;
        const stats = lakeStats(lake);
        const parq = encodeParquet(lake);
        const bin = writeParquetPayload(lake);
        const back = readParquetPayload(bin, data.startYear);
        const q2 = queryLatest(back.lake, plan.predPush ? since : 0);
        const metrics = emptyMetrics({
          lakeRows: stats.rows,
          phys: stats.phys,
          width: stats.width,
          chunks: stats.chunks,
          skipped: q.skipped,
          scanned: q.scanned,
          cacheHits,
          encodeMs: Math.round(encodeMs * 1000) / 1000,
          queryMs: Math.round(queryMs * 1000) / 1000,
          fetchMs: Math.round(fetchMs),
          wallMs: Math.round(performance.now() - wall0),
          skipRatio: stats.chunks ? Math.round((q.skipped / stats.chunks) * 100) / 100 : 0,
          compactBytes: stats.compactBytes,
          rowBytes: stats.rowBytes,
          storeRatio: stats.storeRatio,
          partitions: stats.partitions,
          parquetBytes: parq.bytes,
          parquetPages: parq.pages.length,
          parquetTokenRatio: parq.tokenRatio,
          parquetReadPages: back.pagesRead,
          parquetSkipPages: back.pagesSkipped,
          parquetRoundtrip: q2.rows.length === q.rows.length,
        });
        return { mode, rows: q.rows.length ? q.rows : cachedRows, note: `${note} · CPU ${cpu.isa} ${cpu.kernel}`, metrics };
      };

      const gate = canFetchFred({ confirmNet: data.confirmNet, apiKey: key, apiUrl: data.apiUrl });
      if (!gate.ok) {
        const denied = gate.mode === "DENIED";
        const obs: Obs[] = cachedRows.flatMap((r) =>
          pointsFromCacheRow(r).map((p) => ({
            seriesId: r.seriesId,
            title: r.title,
            category: r.category,
            frequency: r.frequency,
            units: r.units,
            date: p.date,
            value: p.value,
            source: denied ? ("DENIED" as const) : "VDF_CACHE",
            status: denied ? "warn" : "ok",
          })),
        );
        return build(obs, 0, denied ? 0 : FRED_CATALOG.length, gate.mode, gate.reason);
      }
      const apiHost = new URL(gate.url).host;

      const tFetch = performance.now();
      let cacheHits = 0;
      const packed = await mapPool(FRED_CATALOG, plan.concurrency, async (spec) => {
        const ck = cacheKey(spec.seriesId, start, true, apiHost);
        const hit = OBS_CACHE.get(ck);
        if (hit && hit.exp > Date.now()) {
          cacheHits += 1;
          return { spec, points: hit.points, live: hit.live };
        }
        try {
          const span = Math.max(1, new Date().getUTCFullYear() - data.startYear + 1);
          const limit = Math.min(100000, span * 400);
          const points = await fetchSeries(spec.seriesId, key, start, gate.url, limit);
          OBS_CACHE.set(ck, { exp: Date.now() + CACHE_TTL_MS, points, live: true });
          return { spec, points, live: true };
        } catch {
          const row = cachedRows.find((r) => r.seriesId === spec.seriesId);
          const points = row ? pointsFromCacheRow(row) : [];
          return { spec, points, live: false };
        }
      });
      const fetchMs = performance.now() - tFetch;

      const obs: Obs[] = packed.flatMap(({ spec, points, live }) =>
        points.map((p) => ({
          seriesId: spec.seriesId,
          title: spec.title,
          category: spec.category,
          frequency: spec.frequency,
          units: spec.units,
          date: p.date,
          value: p.value,
          source: live ? "FRED_LIVE" : "VDF_CACHE",
          status: live && p.value != null ? "ok" : "warn",
        })),
      );

      const liveOk = packed.filter((p) => p.live && p.points.some((x) => x.value != null)).length;
      if (liveOk === 0) {
        const fallback: Obs[] = cachedRows.flatMap((r) =>
          pointsFromCacheRow(r).map((p) => ({
            seriesId: r.seriesId,
            title: r.title,
            category: r.category,
            frequency: r.frequency,
            units: r.units,
            date: p.date,
            value: p.value,
            source: "VDF_CACHE",
            status: "warn",
          })),
        );
        return build(fallback, fetchMs, cacheHits, "DENIED", "FRED 全數失敗 · 回退 VDF 快取");
      }
      return build(
        obs,
        fetchMs,
        cacheHits,
        "LIVE",
        `FRED LIVE ${liveOk}/${FRED_CATALOG.length} · API ${apiHost} · 池 ${plan.concurrency} · 湖 ${obs.length} 列 · ${start}→最新`,
      );
    },
  );
