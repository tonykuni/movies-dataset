import type { CpuProfile } from "./cpu.ts";
import { simdBoost } from "./cpu.ts";
import type { Light } from "./types.ts";

export type AccelLayer = "fetch" | "cache" | "struct" | "compute" | "query";

export type AccelLane = {
  id: string;
  name: string;
  layer: AccelLayer;
  needs: string[];
  boost: number;
  note: string;
};

export type PairRow = {
  id: string;
  name: string;
  layer: AccelLayer;
  status: Light;
  pairedWith: string;
  reason: string;
  boost: number;
};

export type PairPlan = {
  rows: PairRow[];
  concurrency: number;
  encode: boolean;
  query: boolean;
  pipeline: boolean;
  simd: boolean;
  predPush: boolean;
  planFactor: number;
  active: number;
  conflicts: number;
};

export type StructRule = {
  id: string;
  strategy: string;
  field: string;
  applies: string;
  note: string;
};

/** PS Accel 20 · 角色分工，禁止全開互踩。boost 為單車道計畫係數，加乘見 pairAccels。 */
export const PS20: AccelLane[] = [
  { id: "PS-01", name: "AsyncPool", layer: "fetch", needs: ["PS-05"], boost: 1.35, note: "工作者池 8→16" },
  { id: "PS-02", name: "HttpReuse", layer: "fetch", needs: ["PS-01"], boost: 1.12, note: "連線重用" },
  { id: "PS-03", name: "TimeoutBudget", layer: "fetch", needs: ["PS-01"], boost: 1.08, note: "單序列 7s 截止" },
  { id: "PS-04", name: "RetryOnce", layer: "fetch", needs: ["PS-03"], boost: 1.06, note: "僅一輪、fail-closed" },
  { id: "PS-05", name: "ConsentGate", layer: "fetch", needs: [], boost: 1.0, note: "無 KEY 不外呼" },
  { id: "PS-06", name: "SeriesCache", layer: "cache", needs: [], boost: 1.4, note: "序列觀測記憶快取" },
  { id: "PS-07", name: "ParquetYearPart", layer: "cache", needs: ["PS-08"], boost: 1.18, note: "parquet year 分區落盤" },
  { id: "PS-08", name: "SortDateId", layer: "struct", needs: [], boost: 1.2, note: "date, series_id 排序" },
  { id: "PS-09", name: "DictEncode", layer: "struct", needs: [], boost: 1.16, note: "類別欄字典編碼" },
  { id: "PS-10", name: "ChunkAlign", layer: "struct", needs: [], boost: 1.14, note: "chunk 起點對齊 32/64B，SIMD 前提" },
  { id: "PS-11", name: "MinMaxIndex", layer: "struct", needs: ["PS-08", "PS-10"], boost: 1.25, note: "RowGroup 跳過" },
  { id: "PS-12", name: "BloomProbe", layer: "struct", needs: ["PS-09"], boost: 1.1, note: "series_id 成員探針" },
  { id: "PS-13", name: "Batch64k", layer: "struct", needs: ["PS-10"], boost: 1.08, note: "Arrow batch 政策 65536" },
  { id: "PS-14", name: "HotColumns", layer: "struct", needs: [], boost: 1.1, note: "date, series_id, value 靠前" },
  { id: "PS-15", name: "TypedCols", layer: "struct", needs: ["PS-14"], boost: 1.22, note: "int32 / float64，禁 object" },
  { id: "PS-16", name: "PolarsLazy", layer: "compute", needs: ["PS-15", "PS-10"], boost: 1.28, note: "select / unique / 列裁剪" },
  { id: "PS-17", name: "SIMDScan", layer: "compute", needs: ["PS-10", "PS-15"], boost: 1.3, note: "AVX2/AVX-512 形狀核 · 執行期探測" },
  { id: "PS-18", name: "DuckDBScan", layer: "query", needs: ["PS-11", "PS-15"], boost: 1.32, note: "謂詞下推 + 期末列" },
  { id: "PS-19", name: "PredPush", layer: "query", needs: ["PS-11", "PS-18"], boost: 1.2, note: "WHERE date/series 先裁" },
  { id: "PS-20", name: "PipeParallel", layer: "query", needs: ["PS-01", "PS-06", "PS-16", "PS-18"], boost: 1.35, note: "抓取∥編碼∥查詢" },
];

export const STRUCT_RULES: StructRule[] = [
  { id: "D1", strategy: "Columnar Arrow-native", field: "typed columns", applies: "PS-14/15/16/18", note: "零拷貝契約：date i32 執行核、落盤 u16 相對 epoch、value f64" },
  { id: "D2", strategy: "Partition year", field: "year parts", applies: "PS-07", note: "謂詞下推：since 之前的年整區跳過" },
  { id: "D3", strategy: "Sorted (year, series, date)", field: "series run", applies: "PS-08/11", note: "序列主序：期末=run 尾 O(序列) 非全表 hash" },
  { id: "D4", strategy: "Dictionary encoding", field: "u8/u16 auto", applies: "PS-09/12", note: "基數≤256 用 u8；padding 不進字典" },
  { id: "D5", strategy: "Chunk alignment", field: "32B AVX2 / 64B AVX-512", applies: "PS-10/13/17", note: "phys 為 f64 寬度倍數；valid=0 為 pad" },
  { id: "D6", strategy: "Min/Max index", field: "per-chunk date/series", applies: "PS-11/18/19", note: "跳過不可能 RowGroup" },
  { id: "D7", strategy: "Hot columns first", field: "date, series_id, value", applies: "PS-14", note: "減少掃描寬度" },
  { id: "D8", strategy: "No Python object", field: "float64 / int32", applies: "PS-15", note: "object 欄會讓 Polars 退回 scalar" },
  { id: "D9", strategy: "RLE via series-major", field: "run tail", applies: "PS-08/11", note: "同序列連續，從尾取 latest+prev" },
  { id: "D10", strategy: "Bloom+range", field: "chunk bloom/minSeries", applies: "PS-12/19", note: "WHERE IN 與序列區間跳過" },
  { id: "D11", strategy: "Compact parquet shape", field: "compactBytes", applies: "PS-09/16", note: "落盤不含 SIMD pad；比 row object 小一個數量級" },
  { id: "D12", strategy: "Parquet year pages", field: "PAR1 row-groups", applies: "PS-07", note: "年分區 page · JSON 對 parquet 降 token" },
];

export function pairAccels(enabledIds?: string[]): PairPlan {
  const want = new Set(enabledIds ?? PS20.map((a) => a.id));
  const on = new Set<string>();
  const rows: PairRow[] = [];

  const order = [...PS20].sort((a, b) => a.needs.length - b.needs.length);
  for (const a of order) {
    if (!want.has(a.id)) {
      rows.push({
        id: a.id,
        name: a.name,
        layer: a.layer,
        status: "idle",
        pairedWith: "—",
        reason: "未啟用",
        boost: 1,
      });
      continue;
    }
    const missing = a.needs.filter((n) => !want.has(n) || !on.has(n));
    if (missing.length) {
      rows.push({
        id: a.id,
        name: a.name,
        layer: a.layer,
        status: "warn",
        pairedWith: missing.join(", "),
        reason: `缺前置 ${missing.join("+")} · 關閉以免互踩`,
        boost: 1,
      });
      continue;
    }
    on.add(a.id);
    rows.push({
      id: a.id,
      name: a.name,
      layer: a.layer,
      status: "ok",
      pairedWith: a.needs.length ? a.needs.join(" + ") : "root",
      reason: a.note,
      boost: a.boost,
    });
  }

  rows.sort((a, b) => a.id.localeCompare(b.id));
  const activeRows = rows.filter((r) => r.status === "ok");
  const planFactor = activeRows.reduce((p, r) => p * r.boost, 1);
  const pipeline = on.has("PS-20");
  const simd = on.has("PS-17");
  const predPush = on.has("PS-19");
  const concurrency = on.has("PS-01") ? (pipeline ? 16 : 12) : 4;

  return {
    rows,
    concurrency,
    encode: on.has("PS-15") && on.has("PS-10"),
    query: on.has("PS-18"),
    pipeline,
    simd,
    predPush,
    planFactor: Math.round(planFactor * 100) / 100,
    active: activeRows.length,
    conflicts: rows.filter((r) => r.status === "warn").length,
  };
}

export function applyCpuToPlan(plan: PairPlan, cpu: CpuProfile): PairPlan {
  const rows = plan.rows.map((r) => {
    if (r.id !== "PS-17") return r;
    if (r.status !== "ok" && r.status !== "warn") return r;
    if (cpu.isa === "scalar") {
      return {
        ...r,
        status: "warn" as const,
        boost: 1,
        pairedWith: r.pairedWith,
        reason: `無 AVX · remainder ×1 · 契約對齊 ${cpu.align}B`,
      };
    }
    if (r.status === "warn") return r;
    const boost = simdBoost(cpu.isa);
    return {
      ...r,
      boost,
      reason: cpu.downclock
        ? `SIMDScan · ${cpu.isa} · f64×${cpu.f64Width} · 可能降頻`
        : `SIMDScan · ${cpu.isa} · f64×${cpu.f64Width} · align ${cpu.align}B`,
    };
  });
  const activeRows = rows.filter((r) => r.status === "ok");
  return {
    ...plan,
    rows,
    simd: cpu.isa !== "scalar" && activeRows.some((r) => r.id === "PS-17"),
    planFactor: Math.round(activeRows.reduce((p, r) => p * r.boost, 1) * 100) / 100,
    active: activeRows.length,
    conflicts: rows.filter((r) => r.status === "warn").length,
  };
}
