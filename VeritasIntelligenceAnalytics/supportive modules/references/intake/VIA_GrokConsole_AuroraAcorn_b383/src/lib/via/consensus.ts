/** VDF_ENG077 + VIA_CNS · CNYES FactSet × YFinance 台股共識融合。LIVE 預設關。 */
import type { Light } from "./types.ts";
import { expandTw } from "./tw-ticker.ts";
import { TW_UNIVERSE, type TwMember } from "./vdf-mother.ts";

export const CNS_ID = "VIA_CNS";
export const CNS_ENGINE = "VDF_ENG077";
export const CNS_NAME = "VIA CNYES FactSet × YFinance Consensus";
export const CNS_LIVE_ENABLED = false;
export const CNS_SCHEMA = "VIA-CONSENSUS-LONG/2.0";
export const CNS_VERSION = "2.0.0";
export const MAX_CODES_PER_RUN = 50;
export const CNYES_PAGE = "https://www.cnyes.com/twstock/{code}/summary/overview";
export const CNYES_API = "https://marketinfo.api.cnyes.com";
export const CNYES_TARGET = "/mi/api/v1/financialIndicator/targetPrice/{symbol}";
export const CNYES_RATING = "/mi/api/v1/financialIndicator/factSetEstimate/{symbol}";
export const CNYES_PROFIT = "/mi/api/v1/financialIndicator/estimateProfit/{symbol}";

export const MATCH_TARGET = 0.05;
export const REVIEW_TARGET = 0.15;
export const MATCH_PRICE = 0.02;
export const REVIEW_PRICE = 0.05;
export const MATCH_ANALYST = 0.1;
export const REVIEW_ANALYST = 0.25;
export const MATCH_EST = 0.1;

export type CnsMode = "GROUP" | "ALL";
export type CnsGrade = "MATCH" | "REVIEW" | "CONFLICT" | "INCOMPLETE" | "CURRENCY_MISMATCH";
export type CnsSection =
  | "TARGET"
  | "RATING"
  | "EPS_ESTIMATE"
  | "SALES_ESTIMATE"
  | "YFINANCE_PRICE_TARGETS"
  | "COMPARE";

export type CnsSeed = {
  code: string;
  name: string;
  group: string;
  market: "TWSE" | "TPEX";
  symbol: string;
  yfinance: string;
  bloomberg: string;
  currencyFs: string;
  currencyYf: string;
  priceFs: number | null;
  priceYf: number | null;
  lowFs: number | null;
  lowYf: number | null;
  meanFs: number | null;
  meanYf: number | null;
  medianFs: number | null;
  medianYf: number | null;
  highFs: number | null;
  highYf: number | null;
  analystsFs: number | null;
  analystsYf: number | null;
  ratingFs: "POSITIVE" | "NEUTRAL" | "NEGATIVE" | "MIXED" | null;
  ratingYf: "POSITIVE" | "NEUTRAL" | "NEGATIVE" | null;
  epsFs: number | null;
  epsYf: number | null;
  salesFs: number | null;
  salesYf: number | null;
  asOf: string;
};

export type CnsLong = {
  recordKey: string;
  code: string;
  yfinance: string;
  group: string;
  section: CnsSection;
  period: string;
  metric: string;
  value: number | string | null;
  currency: string | null;
  source: "FactSet" | "YFinance" | "COMPARE";
  sourceMode: "CACHE" | "API_PRIMARY" | "YFINANCE_INFO_LIVE";
  asOf: string;
};

export type CnsCompare = {
  code: string;
  metric: string;
  fs: number | string | null;
  yf: number | string | null;
  pct: number | null;
  grade: CnsGrade;
  light: Light;
};

export type CnsRow = {
  id: string;
  layer: string;
  metric: string;
  value: string;
  light: Light;
  note: string;
};

export type CnsPlan = {
  mode: CnsMode;
  query: string;
  codes: string[];
  batches: string[][];
  cached: number;
  missing: number;
  groups: string[];
};

export type CnsStruct = {
  id: string;
  strategy: string;
  gain: string;
  applies: string;
  note: string;
};

/** 離線回歸樣本 · 非 LIVE。涵蓋 MATCH／REVIEW／CONFLICT／INCOMPLETE／幣別。 */
export const CNS_SEED: CnsSeed[] = [
  {
    code: "2330", name: "台積電", group: "半導體", market: "TWSE",
    symbol: "TWS:2330:STOCK", yfinance: "2330.TW", bloomberg: "2330 TT",
    currencyFs: "TWD", currencyYf: "TWD",
    priceFs: 920, priceYf: 918,
    lowFs: 900, lowYf: 890, meanFs: 1200, meanYf: 1185, medianFs: 1180, medianYf: 1170, highFs: 1500, highYf: 1480,
    analystsFs: 32, analystsYf: 30, ratingFs: "POSITIVE", ratingYf: "POSITIVE",
    epsFs: 58, epsYf: 56, salesFs: 3.2e12, salesYf: 3.1e12, asOf: "2026-08-27",
  },
  {
    code: "2317", name: "鴻海", group: "AI 伺服器", market: "TWSE",
    symbol: "TWS:2317:STOCK", yfinance: "2317.TW", bloomberg: "2317 TT",
    currencyFs: "TWD", currencyYf: "TWD",
    priceFs: 180, priceYf: 182,
    lowFs: 160, lowYf: 155, meanFs: 210, meanYf: 240, medianFs: 205, medianYf: 230, highFs: 260, highYf: 280,
    analystsFs: 18, analystsYf: 16, ratingFs: "POSITIVE", ratingYf: "POSITIVE",
    epsFs: 12.4, epsYf: 12.1, salesFs: 6.8e12, salesYf: 6.6e12, asOf: "2026-08-27",
  },
  {
    code: "2454", name: "聯發科", group: "半導體", market: "TWSE",
    symbol: "TWS:2454:STOCK", yfinance: "2454.TW", bloomberg: "2454 TT",
    currencyFs: "TWD", currencyYf: "TWD",
    priceFs: 1280, priceYf: 1290,
    lowFs: 1100, lowYf: 1080, meanFs: 1400, meanYf: 1800, medianFs: 1380, medianYf: 1720, highFs: 1700, highYf: 2100,
    analystsFs: 22, analystsYf: 20, ratingFs: "POSITIVE", ratingYf: "NEUTRAL",
    epsFs: 92, epsYf: 88, salesFs: 6.1e11, salesYf: 5.9e11, asOf: "2026-08-27",
  },
  {
    code: "2303", name: "聯電", group: "半導體", market: "TWSE",
    symbol: "TWS:2303:STOCK", yfinance: "2303.TW", bloomberg: "2303 TT",
    currencyFs: "TWD", currencyYf: "TWD",
    priceFs: 48, priceYf: null,
    lowFs: 42, lowYf: null, meanFs: 52, meanYf: null, medianFs: 51, medianYf: null, highFs: 60, highYf: null,
    analystsFs: 14, analystsYf: null, ratingFs: "NEUTRAL", ratingYf: null,
    epsFs: 3.2, epsYf: null, salesFs: 2.2e11, salesYf: null, asOf: "2026-08-27",
  },
  {
    code: "3711", name: "日月光投控", group: "半導體", market: "TWSE",
    symbol: "TWS:3711:STOCK", yfinance: "3711.TW", bloomberg: "3711 TT",
    currencyFs: "TWD", currencyYf: "USD",
    priceFs: 165, priceYf: 5.2,
    lowFs: 150, lowYf: 4.8, meanFs: 180, meanYf: 5.6, medianFs: 176, medianYf: 5.5, highFs: 210, highYf: 6.4,
    analystsFs: 16, analystsYf: 15, ratingFs: "POSITIVE", ratingYf: "POSITIVE",
    epsFs: 11, epsYf: 0.35, salesFs: 6.4e11, salesYf: 2.0e10, asOf: "2026-08-27",
  },
];

export const CNS_STRUCT: CnsStruct[] = [
  { id: "A1", strategy: "長表 consensus_long", gain: "5×", applies: "Polars / DuckDB", note: "寬表禁止 · 一列一原子" },
  { id: "A2", strategy: "字典編碼 section/metric/source", gain: "2–6×", applies: "Arrow / DuckDB", note: "GROUP BY 與壓縮" },
  { id: "A3", strategy: "hive year+group 分區", gain: "4–10×", applies: "DuckDB prune", note: "data/vdf/cns/year=*/group=* " },
  { id: "A4", strategy: "排序 code+section+period+metric", gain: "3–8×", applies: "SIMD 批次", note: "向量化友善" },
  { id: "A5", strategy: "record_key 冪等", gain: "I/O", applies: "DuckDB UPSERT", note: "不含 run_id · 斷點續傳" },
  { id: "A6", strategy: "批次 50 碼", gain: "2×", applies: "Async fetch", note: "MAX_CODES_PER_RUN · checkpoint 一碼一檔" },
  { id: "A7", strategy: "角色分工", gain: "乘", applies: "20 加速器", note: "抓取 Async · 流 Arrow · 算 Polars · 查 DuckDB · 存 Parquet" },
];

export function cnyesPage(code: string): string {
  return CNYES_PAGE.replace("{code}", code);
}

export function cnyesPath(path: string, symbol: string): string {
  return `${CNYES_API}${path.replace("{symbol}", encodeURIComponent(symbol))}`;
}

export function validateCode(raw: string): string {
  const t = String(raw).trim().toUpperCase().replace(/\.(TW|TWO)$/, "");
  if (!/^[1-9]\d{3}$/.test(t)) throw new Error(`INVALID_TW_STOCK_CODE: ${raw}`);
  return t;
}

export function validateCodes(codes: string[]): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const c of codes) {
    const x = validateCode(c);
    if (!seen.has(x)) {
      seen.add(x);
      out.push(x);
    }
  }
  if (!out.length) throw new Error("NO_VALID_CODE");
  if (out.length > MAX_CODES_PER_RUN) throw new Error(`TOO_MANY_CODES: count=${out.length} max=${MAX_CODES_PER_RUN}`);
  return out;
}

export function yfFromMember(m: TwMember): string {
  return m.yfinance;
}

export function recordKey(row: Pick<CnsLong, "code" | "section" | "period" | "metric" | "source">): string {
  return `${row.code}|${row.section}|${row.period}|${row.metric}|${row.source}`;
}

export function gradePct(pct: number | null, matchMax: number, reviewMax: number): CnsGrade {
  if (pct == null || !Number.isFinite(pct)) return "INCOMPLETE";
  const a = Math.abs(pct);
  if (a <= matchMax) return "MATCH";
  if (a <= reviewMax) return "REVIEW";
  return "CONFLICT";
}

export function lightOf(grade: CnsGrade): Light {
  if (grade === "MATCH") return "ok";
  if (grade === "REVIEW" || grade === "INCOMPLETE") return "warn";
  return "bad";
}

export function ratioDiff(a: number | null, b: number | null): number | null {
  if (a == null || b == null || a === 0) return null;
  return (b - a) / a;
}

export function comparePair(
  code: string,
  metric: string,
  fs: number | string | null,
  yf: number | string | null,
  kind: "target" | "price" | "analyst" | "est" | "rating" | "fx",
  currencyOk = true,
): CnsCompare {
  if (!currencyOk && kind !== "rating") {
    return { code, metric, fs, yf, pct: null, grade: "CURRENCY_MISMATCH", light: "bad" };
  }
  if (kind === "rating") {
    const grade: CnsGrade = !fs || !yf ? "INCOMPLETE" : fs === yf ? "MATCH" : "CONFLICT";
    return { code, metric, fs, yf, pct: null, grade, light: lightOf(grade) };
  }
  const fa = typeof fs === "number" ? fs : null;
  const fb = typeof yf === "number" ? yf : null;
  const pct = ratioDiff(fa, fb);
  const cap =
    kind === "price" ? [MATCH_PRICE, REVIEW_PRICE] :
    kind === "analyst" ? [MATCH_ANALYST, REVIEW_ANALYST] :
    kind === "est" ? [MATCH_EST, MATCH_EST] :
    [MATCH_TARGET, REVIEW_TARGET];
  const grade = gradePct(pct, cap[0], cap[1]);
  return { code, metric, fs, yf, pct, grade, light: lightOf(grade) };
}

export function seedByCode(): Map<string, CnsSeed> {
  return new Map(CNS_SEED.map((s) => [s.code, s]));
}

export function universeGroups(): string[] {
  return [...new Set(TW_UNIVERSE.map((m) => m.group))].sort();
}

export function membersOfGroup(group: string): TwMember[] {
  return TW_UNIVERSE.filter((m) => m.group === group);
}

export function parseQuery(query: string): { group: string | null; codes: string[] } {
  const q = String(query || "").trim();
  if (!q) return { group: null, codes: ["2330"] };
  const hit = universeGroups().find((g) => g === q);
  if (hit) return { group: hit, codes: membersOfGroup(hit).map((m) => m.ticker) };
  const tokens = q.split(/[,;\s]+/).map((t) => t.trim()).filter(Boolean);
  const codes: string[] = [];
  for (const t of tokens) {
    try {
      codes.push(validateCode(t));
    } catch {
      /* skip invalid */
    }
  }
  return { group: null, codes: codes.length ? [...new Set(codes)] : ["2330"] };
}

export function batchCodes(codes: string[], size = MAX_CODES_PER_RUN): string[][] {
  const out: string[][] = [];
  for (let i = 0; i < codes.length; i += size) out.push(codes.slice(i, i + size));
  return out.length ? out : [[]];
}

export function planFetch(mode: CnsMode, query: string): CnsPlan {
  const seeds = seedByCode();
  if (mode === "ALL") {
    const codes = TW_UNIVERSE.map((m) => m.ticker);
    const cached = codes.filter((c) => seeds.has(c)).length;
    return {
      mode,
      query: "ALL",
      codes,
      batches: batchCodes(codes),
      cached,
      missing: codes.length - cached,
      groups: universeGroups(),
    };
  }
  const parsed = parseQuery(query);
  const codes = parsed.codes;
  const cached = codes.filter((c) => seeds.has(c)).length;
  return {
    mode: "GROUP",
    query: parsed.group ?? codes.join(","),
    codes,
    batches: batchCodes(codes),
    cached,
    missing: codes.length - cached,
    groups: parsed.group ? [parsed.group] : [...new Set(codes.map((c) => seeds.get(c)?.group).filter(Boolean) as string[])],
  };
}

export function canFetchCns(input: { confirmNet: boolean }): { ok: true } | { ok: false; mode: "CACHE"; reason: string } {
  if (!CNS_LIVE_ENABLED) return { ok: false, mode: "CACHE", reason: "CNS LIVE 未啟用 · 零外呼 · CACHE 長表可跑" };
  if (!input.confirmNet) return { ok: false, mode: "CACHE", reason: "NET 閘未確認 · FactSet/YF 雙源 fail-closed" };
  return { ok: true };
}

function pushLong(out: CnsLong[], seed: CnsSeed, section: CnsSection, period: string, metric: string, value: number | string | null, source: CnsLong["source"], currency: string | null): void {
  const row: CnsLong = {
    recordKey: "",
    code: seed.code,
    yfinance: seed.yfinance,
    group: seed.group,
    section,
    period,
    metric,
    value,
    currency,
    source,
    sourceMode: "CACHE",
    asOf: seed.asOf,
  };
  row.recordKey = recordKey(row);
  out.push(row);
}

export function longFromSeed(seed: CnsSeed): CnsLong[] {
  const out: CnsLong[] = [];
  pushLong(out, seed, "TARGET", "SPOT", "CURRENT_PRICE", seed.priceFs, "FactSet", seed.currencyFs);
  pushLong(out, seed, "YFINANCE_PRICE_TARGETS", "SPOT", "CURRENT_PRICE", seed.priceYf, "YFinance", seed.currencyYf);
  pushLong(out, seed, "TARGET", "SPOT", "TARGET_LOW", seed.lowFs, "FactSet", seed.currencyFs);
  pushLong(out, seed, "YFINANCE_PRICE_TARGETS", "SPOT", "TARGET_LOW", seed.lowYf, "YFinance", seed.currencyYf);
  pushLong(out, seed, "TARGET", "SPOT", "TARGET_MEAN", seed.meanFs, "FactSet", seed.currencyFs);
  pushLong(out, seed, "YFINANCE_PRICE_TARGETS", "SPOT", "TARGET_MEAN", seed.meanYf, "YFinance", seed.currencyYf);
  pushLong(out, seed, "TARGET", "SPOT", "TARGET_MEDIAN", seed.medianFs, "FactSet", seed.currencyFs);
  pushLong(out, seed, "YFINANCE_PRICE_TARGETS", "SPOT", "TARGET_MEDIAN", seed.medianYf, "YFinance", seed.currencyYf);
  pushLong(out, seed, "TARGET", "SPOT", "TARGET_HIGH", seed.highFs, "FactSet", seed.currencyFs);
  pushLong(out, seed, "YFINANCE_PRICE_TARGETS", "SPOT", "TARGET_HIGH", seed.highYf, "YFinance", seed.currencyYf);
  pushLong(out, seed, "TARGET", "SPOT", "ANALYST_COUNT", seed.analystsFs, "FactSet", null);
  pushLong(out, seed, "YFINANCE_PRICE_TARGETS", "SPOT", "ANALYST_COUNT", seed.analystsYf, "YFinance", null);
  pushLong(out, seed, "RATING", "SPOT", "RATING", seed.ratingFs, "FactSet", null);
  pushLong(out, seed, "YFINANCE_PRICE_TARGETS", "SPOT", "RATING", seed.ratingYf, "YFinance", null);
  pushLong(out, seed, "EPS_ESTIMATE", "2026", "estimate_median", seed.epsFs, "FactSet", seed.currencyFs);
  pushLong(out, seed, "EPS_ESTIMATE", "2026", "estimate_median", seed.epsYf, "YFinance", seed.currencyYf);
  pushLong(out, seed, "SALES_ESTIMATE", "2026", "estimate_median", seed.salesFs, "FactSet", seed.currencyFs);
  pushLong(out, seed, "SALES_ESTIMATE", "2026", "estimate_median", seed.salesYf, "YFinance", seed.currencyYf);
  return out;
}

export function comparesOf(seed: CnsSeed): CnsCompare[] {
  const fx = seed.currencyFs === seed.currencyYf;
  return [
    comparePair(seed.code, "CURRENT_PRICE", seed.priceFs, seed.priceYf, "price", fx),
    comparePair(seed.code, "TARGET_MEDIAN", seed.medianFs, seed.medianYf, "target", fx),
    comparePair(seed.code, "TARGET_LOW", seed.lowFs, seed.lowYf, "target", fx),
    comparePair(seed.code, "TARGET_MEAN", seed.meanFs, seed.meanYf, "target", fx),
    comparePair(seed.code, "TARGET_HIGH", seed.highFs, seed.highYf, "target", fx),
    comparePair(seed.code, "ANALYST_COUNT", seed.analystsFs, seed.analystsYf, "analyst", true),
    comparePair(seed.code, "RATING", seed.ratingFs, seed.ratingYf, "rating", true),
    comparePair(seed.code, "EPS_2026", seed.epsFs, seed.epsYf, "est", fx),
    comparePair(seed.code, "SALES_2026", seed.salesFs, seed.salesYf, "est", fx),
  ];
}

export function cacheSeeds(codes: string[]): CnsSeed[] {
  const map = seedByCode();
  return codes.map((c) => map.get(c)).filter((s): s is CnsSeed => Boolean(s));
}

export function cnsMembersOk(): boolean {
  if (CNS_SEED.length < 5) return false;
  return CNS_SEED.every((s) => {
    const x = expandTw(s.code, s.market === "TPEX" ? "TWO" : "TW");
    return Boolean(x && x.yfinance === s.yfinance && x.bloomberg === s.bloomberg);
  });
}

export function runCnsSim(input: { mode: CnsMode; query: string; confirmNet?: boolean } = { mode: "GROUP", query: "2330" }): {
  plan: CnsPlan;
  seeds: CnsSeed[];
  long: CnsLong[];
  compare: CnsCompare[];
  rows: CnsRow[];
  note: string;
} {
  const plan = planFetch(input.mode, input.query);
  const gate = canFetchCns({ confirmNet: Boolean(input.confirmNet) });
  const seeds = cacheSeeds(plan.codes);
  const long = seeds.flatMap(longFromSeed);
  const compare = seeds.flatMap(comparesOf);
  const keys = new Set(long.map((r) => r.recordKey));
  const grades = {
    match: compare.filter((c) => c.grade === "MATCH").length,
    review: compare.filter((c) => c.grade === "REVIEW").length,
    conflict: compare.filter((c) => c.grade === "CONFLICT").length,
    incomplete: compare.filter((c) => c.grade === "INCOMPLETE").length,
    fx: compare.filter((c) => c.grade === "CURRENCY_MISMATCH").length,
  };
  const rows: CnsRow[] = [
    { id: "CNS_MODE", layer: "擷取", metric: "模式", value: plan.mode === "ALL" ? "全部台股" : "族群／個股", light: "ok", note: plan.query },
    { id: "CNS_PLAN", layer: "擷取", metric: "計畫碼", value: String(plan.codes.length), light: plan.missing ? "warn" : "ok", note: `批次 ${plan.batches.length} ×≤${MAX_CODES_PER_RUN} · CACHE ${plan.cached} · 缺 ${plan.missing}` },
    { id: "CNS_GATE", layer: "閘", metric: "LIVE", value: gate.ok ? "開" : "關", light: gate.ok ? "warn" : "ok", note: gate.ok ? "雙源外呼" : gate.reason },
    { id: "CNS_N", layer: "長表", metric: "列", value: String(long.length), light: long.length ? "ok" : "warn", note: `${CNS_SCHEMA} · key ${keys.size}` },
    { id: "CNS_MATCH", layer: "對帳", metric: "MATCH", value: String(grades.match), light: "ok", note: `目標≤${MATCH_TARGET * 100}% · 價≤${MATCH_PRICE * 100}%` },
    { id: "CNS_REVIEW", layer: "對帳", metric: "REVIEW", value: String(grades.review), light: grades.review ? "warn" : "ok", note: `目標≤${REVIEW_TARGET * 100}%` },
    { id: "CNS_CONFLICT", layer: "對帳", metric: "CONFLICT", value: String(grades.conflict), light: grades.conflict ? "bad" : "ok", note: "雙源方向或幅度衝突" },
    { id: "CNS_INC", layer: "對帳", metric: "INCOMPLETE", value: String(grades.incomplete), light: grades.incomplete ? "warn" : "ok", note: "單源缺值 · 不發明" },
    { id: "CNS_FX", layer: "對帳", metric: "CURRENCY", value: String(grades.fx), light: grades.fx ? "bad" : "ok", note: "幣別不一致不換算" },
    { id: "CNS_NET", layer: "工具", metric: "網具", value: "NET-CNYES+NET-YF", light: "ok", note: "marketinfo 公開端點 · 不登入" },
    { id: "CNS_ACC", layer: "工具", metric: "加速", value: "PS20+Arrow+Polars+DuckDB", light: "ok", note: "長表＋分區＋字典＋批次50" },
  ];
  const note = gate.ok
    ? `LIVE ${plan.codes.length} 碼 · ${plan.batches.length} 批`
    : `CACHE ${seeds.length} 檔 · 計畫 ${plan.codes.length} · ${plan.mode} · LIVE 關`;
  return { plan, seeds, long, compare, rows, note };
}

export function cnsLakeRel(): string {
  return "data/vdf/cns";
}
