import type { Light } from "./types.ts";

/** Same-day multi-source book. YF/AK fail-closed unless second gate. Cache is not LIVE. */
export type MarketKind = "index" | "etf" | "cmdty" | "shipping" | "crypto" | "bond";

export type MarketRow = {
  id: string;
  kind: MarketKind;
  region: string;
  name: string;
  ticker: string;
  sources: string;
  px: number | null;
  aumUsd: number | null;
  flow1d: number | null;
  asOf: string;
  light: Light;
  note: string;
};

export type XValRow = {
  id: string;
  name: string;
  a: string;
  b: string;
  va: number | null;
  vb: number | null;
  date: string;
  pct: number | null;
  light: Light;
  note: string;
};

export const MARKET_SEED: Array<Omit<MarketRow, "light">> = [
  { id: "US_SPX", kind: "index", region: "US", name: "S&P 500", ticker: "^GSPC", sources: "FRED SP500 · YF", px: 5620, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "對 SPY" },
  { id: "EU_SX5E", kind: "index", region: "EU", name: "Euro Stoxx 50", ticker: "^STOXX50E", sources: "YF · AK", px: 4982, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "對 EZU" },
  { id: "JP_NK", kind: "index", region: "JP", name: "Nikkei 225", ticker: "^N225", sources: "YF · AK", px: 38740, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "對 EWJ" },
  { id: "TW_TWII", kind: "index", region: "TW", name: "加權", ticker: "^TWII", sources: "YF · TWSE · AK", px: 23480, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "對 0050.TW / EWT" },
  { id: "CN_CSI", kind: "index", region: "CN", name: "上證綜指", ticker: "000001.SS", sources: "YF · AK", px: 3328, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "對 MCHI / FXI" },
  { id: "IN_NIFTY", kind: "index", region: "IN", name: "Nifty 50", ticker: "^NSEI", sources: "YF · AK", px: 24810, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "對 INDA" },
  { id: "AU_ASX", kind: "index", region: "AU", name: "ASX 200", ticker: "^AXJO", sources: "YF", px: 8124, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "對 EWA" },
  { id: "ETF_SPY", kind: "etf", region: "US", name: "SPDR S&P 500", ticker: "SPY", sources: "YF · issuer", px: 561.2, aumUsd: 582_000, flow1d: 420, asOf: "2026-09-03", note: "創贖≈Δunits×NAV" },
  { id: "ETF_QQQ", kind: "etf", region: "US", name: "Nasdaq-100", ticker: "QQQ", sources: "YF · issuer", px: 492.1, aumUsd: 298_000, flow1d: -180, asOf: "2026-09-03", note: "流出" },
  { id: "ETF_EZU", kind: "etf", region: "EU", name: "iShares MSCI EMU", ticker: "EZU", sources: "YF", px: 52.4, aumUsd: 8_400, flow1d: 22, asOf: "2026-09-03", note: "" },
  { id: "ETF_EWJ", kind: "etf", region: "JP", name: "iShares Japan", ticker: "EWJ", sources: "YF", px: 71.8, aumUsd: 16_200, flow1d: 35, asOf: "2026-09-03", note: "" },
  { id: "ETF_EWT", kind: "etf", region: "TW", name: "iShares Taiwan", ticker: "EWT", sources: "YF", px: 58.6, aumUsd: 5_100, flow1d: 18, asOf: "2026-09-03", note: "美股掛牌" },
  { id: "ETF_0050", kind: "etf", region: "TW", name: "元大台灣50", ticker: "0050.TW", sources: "YF · TWSE", px: 188.4, aumUsd: 14_800, flow1d: 62, asOf: "2026-09-03", note: "本地 ETF" },
  { id: "ETF_MCHI", kind: "etf", region: "CN", name: "iShares China", ticker: "MCHI", sources: "YF", px: 48.2, aumUsd: 6_700, flow1d: -44, asOf: "2026-09-03", note: "" },
  { id: "ETF_INDA", kind: "etf", region: "IN", name: "iShares India", ticker: "INDA", sources: "YF", px: 54.1, aumUsd: 9_800, flow1d: 28, asOf: "2026-09-03", note: "" },
  { id: "ETF_EWA", kind: "etf", region: "AU", name: "iShares Australia", ticker: "EWA", sources: "YF", px: 26.3, aumUsd: 1_600, flow1d: 6, asOf: "2026-09-03", note: "" },
  { id: "ETF_TLT", kind: "etf", region: "US", name: "20Y+ Treasuries", ticker: "TLT", sources: "YF · FRED DGS30", px: 93.4, aumUsd: 52_000, flow1d: -210, asOf: "2026-09-03", note: "債 ETF" },
  { id: "ETF_IEF", kind: "etf", region: "US", name: "7–10Y Treasuries", ticker: "IEF", sources: "YF · FRED DGS10", px: 96.1, aumUsd: 31_000, flow1d: 48, asOf: "2026-09-03", note: "" },
  { id: "ETF_SHY", kind: "etf", region: "US", name: "1–3Y Treasuries", ticker: "SHY", sources: "YF · FRED DGS2", px: 82.7, aumUsd: 24_000, flow1d: 12, asOf: "2026-09-03", note: "" },
  { id: "ETF_GLD", kind: "etf", region: "GL", name: "SPDR Gold", ticker: "GLD", sources: "YF · issuer", px: 248.6, aumUsd: 68_000, flow1d: 90, asOf: "2026-09-03", note: "黃金 ETF" },
  { id: "ETF_XLK", kind: "etf", region: "US", name: "科技", ticker: "XLK", sources: "YF", px: 238.0, aumUsd: 72_000, flow1d: 55, asOf: "2026-09-03", note: "產業" },
  { id: "ETF_XLE", kind: "etf", region: "US", name: "能源", ticker: "XLE", sources: "YF", px: 91.2, aumUsd: 34_000, flow1d: -30, asOf: "2026-09-03", note: "產業" },
  { id: "ETF_XLF", kind: "etf", region: "US", name: "金融", ticker: "XLF", sources: "YF", px: 44.8, aumUsd: 41_000, flow1d: 14, asOf: "2026-09-03", note: "產業" },
  { id: "ETF_IBIT", kind: "crypto", region: "US", name: "iShares Bitcoin", ticker: "IBIT", sources: "YF · issuer", px: 58.4, aumUsd: 54_000, flow1d: 310, asOf: "2026-09-03", note: "現貨 BTC ETF" },
  { id: "ETF_FBTC", kind: "crypto", region: "US", name: "Fidelity Bitcoin", ticker: "FBTC", sources: "YF · issuer", px: 90.2, aumUsd: 18_400, flow1d: 88, asOf: "2026-09-03", note: "" },
  { id: "CMD_GC", kind: "cmdty", region: "GL", name: "黃金期貨", ticker: "GC=F", sources: "YF · FRED GOLDAM", px: 2492, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "Comex" },
  { id: "CMD_CL", kind: "cmdty", region: "GL", name: "WTI 期貨", ticker: "CL=F", sources: "YF · FRED DCOILWTICO", px: 78.6, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "" },
  { id: "CMD_BZ", kind: "cmdty", region: "GL", name: "Brent 期貨", ticker: "BZ=F", sources: "YF · FRED DCOILBRENTEU", px: 82.3, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "" },
  { id: "CMD_BDI", kind: "shipping", region: "GL", name: "BDI 波羅的海乾散貨", ticker: "BDI", sources: "AKShare", px: 1842, aumUsd: null, flow1d: null, asOf: "2026-09-02", note: "非 FRED" },
  { id: "CMD_SCFI", kind: "shipping", region: "CN", name: "SCFI 上海出口貨櫃", ticker: "SCFI", sources: "AKShare", px: 2318, aumUsd: null, flow1d: null, asOf: "2026-08-29", note: "週" },
  { id: "CMD_VIX", kind: "index", region: "US", name: "VIX", ticker: "^VIX", sources: "YF · FRED VIXCLS", px: 16.8, aumUsd: null, flow1d: null, asOf: "2026-09-03", note: "" },
  { id: "TW_10Y", kind: "bond", region: "TW", name: "台灣十年期公債", ticker: "IRLTLT01TWM156N", sources: "FRED OECD · AK", px: 1.58, aumUsd: null, flow1d: null, asOf: "2026-08-01", note: "殖利率 %" },
];

const XPAIRS: Array<{ id: string; name: string; a: string; b: string; va: number; vb: number; date: string }> = [
  { id: "XV_SPX", name: "S&P 500", a: "FRED SP500", b: "YF ^GSPC", va: 5620, vb: 5620, date: "2026-09-03" },
  { id: "XV_VIX", name: "VIX", a: "FRED VIXCLS", b: "YF ^VIX", va: 16.8, vb: 16.8, date: "2026-09-03" },
  { id: "XV_WTI", name: "WTI", a: "FRED DCOILWTICO", b: "YF CL=F", va: 78.4, vb: 78.6, date: "2026-09-03" },
  { id: "XV_BRT", name: "Brent", a: "FRED DCOILBRENTEU", b: "YF BZ=F", va: 82.1, vb: 82.3, date: "2026-09-03" },
  { id: "XV_GLD", name: "黃金", a: "FRED GOLDAM", b: "YF GC=F", va: 2488, vb: 2492, date: "2026-09-03" },
  { id: "XV_TWD", name: "TWD/USD", a: "FRED DEXTAUS", b: "YF TWD=X", va: 31.92, vb: 31.9, date: "2026-09-03" },
  { id: "XV_TW10", name: "台債 10Y", a: "FRED OECD", b: "AK 公債", va: 1.58, vb: 1.59, date: "2026-08-01" },
];

function pctDiff(a: number, b: number): number {
  const d = Math.max(Math.abs(a), Math.abs(b), 1e-9);
  return Math.abs(a - b) / d;
}

export function gradeDiff(pct: number): { light: Light; note: string } {
  if (pct <= 0.02) return { light: "ok", note: "同日 ≤2%" };
  if (pct <= 0.05) return { light: "warn", note: "同日 2–5% · 待對齊" };
  return { light: "bad", note: "同日 >5% · 不合併" };
}

export function buildMarketBook(input: { yfLive: boolean; akLive: boolean }): MarketRow[] {
  return MARKET_SEED.map((r) => {
    const needsYf = r.sources.includes("YF");
    const needsAk = r.sources.includes("AK");
    if (needsYf && !input.yfLive && needsAk && !input.akLive) {
      return { ...r, light: "ok", note: `${r.note} · CACHE 多源` };
    }
    if (needsAk && !input.akLive && r.sources === "AKShare") {
      return { ...r, light: "ok", note: `${r.note} · AK 閘關 · CACHE` };
    }
    return { ...r, light: "ok", note: r.note || "CACHE" };
  });
}

export function crossValidate(): XValRow[] {
  return XPAIRS.map((p) => {
    const pct = pctDiff(p.va, p.vb);
    const g = gradeDiff(pct);
    return { id: p.id, name: p.name, a: p.a, b: p.b, va: p.va, vb: p.vb, date: p.date, pct, light: g.light, note: g.note };
  });
}

export function etfFlowSum(rows: MarketRow[]): { aum: number; inFlow: number; outFlow: number } {
  const etfs = rows.filter((r) => r.kind === "etf" || r.kind === "crypto");
  const aum = etfs.reduce((s, r) => s + (r.aumUsd ?? 0), 0);
  const inFlow = etfs.reduce((s, r) => s + Math.max(r.flow1d ?? 0, 0), 0);
  const outFlow = etfs.reduce((s, r) => s + Math.min(r.flow1d ?? 0, 0), 0);
  return { aum, inFlow, outFlow };
}
