/** Forward valuation vintage v2 緊湊。指數與 ETF 錨分開。不平均來源。不把推算叫「源報」。 */
import type { Light } from "./types.ts";

export const FWD_VER = "forward_valuation_vintage_v2";
export const FWD_PE_INC = 0.1;
export const FWD_EPS_TOL = 0.005;
export const FWD_SRC_ALIGN = 0.02;
export const FWD_STALE_MULT = 1.5;
export const FWD_STALE_MIN = 7;
export const FWD_STALE_MAX = 62;

export type FwdOrigin = "reported_forward_eps" | "calculated_not_original" | "etf_source_reported_forward_pe" | "index_mapped_proxy";
export type FwdReady = "research_grade" | "screen_grade" | "quarantine";
export type FwdConflict = "single_source" | "aligned_not_blended" | "material_definition_or_timing_conflict";

export function roundingInterval(level: number, pe: number, increment = FWD_PE_INC, approximate = false): {
  peLo: number;
  peHi: number;
  eps: number;
  epsLo: number;
  epsHi: number;
} {
  if (level <= 0 || pe <= 0 || increment <= 0) throw new Error("pe_interval");
  const half = increment * (approximate ? 1 : 0.5);
  const peLo = pe - half;
  const peHi = pe + half;
  if (peLo <= 0) throw new Error("pe_cross_zero");
  return { peLo, peHi, eps: level / pe, epsLo: level / peHi, epsHi: level / peLo };
}

export function epsGap(reported: number, implied: number): number {
  return Math.abs(reported - implied) / reported;
}

export function originLabel(hasReportedEps: boolean): { origin: FwdOrigin; evidence: "fact_source_reported" | "derived_calculation" } {
  return hasReportedEps
    ? { origin: "reported_forward_eps", evidence: "fact_source_reported" }
    : { origin: "calculated_not_original", evidence: "derived_calculation" };
}

export function readiness(input: {
  origin: FwdOrigin;
  quality: "pass" | "warning" | "quarantine";
  cutoff: "exact" | "external_same_close" | "date_only" | "mismatch";
  approximate?: boolean;
  mapping?: "exact" | "near_exact" | "proxy" | null;
}): { score: number; ready: FwdReady; blockers: string[] } {
  let score = 100;
  const blockers: string[] = [];
  if (input.origin === "calculated_not_original") score -= 12;
  if (input.origin === "index_mapped_proxy") score -= 25;
  if (input.approximate) score -= 8;
  if (input.cutoff === "external_same_close") score -= 5;
  else if (input.cutoff === "date_only") score -= 12;
  else if (input.cutoff === "mismatch") {
    score -= 40;
    blockers.push("price_cutoff_mismatch");
  }
  if (input.mapping === "near_exact") score -= 15;
  else if (input.mapping === "proxy") {
    score -= 30;
    blockers.push("proxy_benchmark_mismatch");
  }
  if (input.quality === "warning") score -= 10;
  else if (input.quality === "quarantine") {
    score = Math.min(score, 39);
    blockers.push("quality_quarantine");
  }
  score = Math.max(0, Math.min(100, score));
  const ready: FwdReady = blockers.length || score < 60 ? "quarantine" : score < 80 ? "screen_grade" : "research_grade";
  return { score, ready, blockers };
}

export function etfEpsFromNav(nav: number, pe: number): number {
  if (nav <= 0 || pe <= 0) throw new Error("etf_eps");
  return nav / pe;
}

export function capWeightedPe(rows: { mv: number; earn: number }[]): number {
  const mv = rows.reduce((s, r) => s + r.mv, 0);
  const earn = rows.reduce((s, r) => s + r.earn, 0);
  if (earn <= 0) throw new Error("cap_pe");
  return mv / earn;
}

export function compareSources(a: number, b: number): { spread: number; status: FwdConflict } {
  const lo = Math.min(a, b);
  const hi = Math.max(a, b);
  if (lo <= 0) return { spread: Infinity, status: "material_definition_or_timing_conflict" };
  const spread = hi / lo - 1;
  return { spread, status: spread <= FWD_SRC_ALIGN ? "aligned_not_blended" : "material_definition_or_timing_conflict" };
}

export function estimateStaleDays(dates: string[]): number {
  const ts = dates.map((d) => Date.parse(d)).filter((n) => Number.isFinite(n)).sort((a, b) => a - b);
  const gaps: number[] = [];
  for (let i = 1; i < ts.length; i++) gaps.push((ts[i]! - ts[i - 1]!) / 86400000);
  if (!gaps.length) return FWD_STALE_MIN;
  gaps.sort((a, b) => a - b);
  const mid = gaps[Math.floor((gaps.length - 1) / 2)]!;
  const d = Math.round(mid * FWD_STALE_MULT);
  return Math.max(FWD_STALE_MIN, Math.min(FWD_STALE_MAX, d));
}

/** SP500 自測錨 · 非 LIVE。implied 不得標源報。 */
export const FWD_INDEX_SEED = {
  index: "SP500",
  level: 6890.59,
  pe: 23.1,
  epsReported: 298.56,
  asOf: "2025-10-29",
} as const;

export function fwdQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const iv = roundingInterval(FWD_INDEX_SEED.level, FWD_INDEX_SEED.pe);
  const gap = epsGap(FWD_INDEX_SEED.epsReported, iv.eps);
  const src = compareSources(23.1, 24.0);
  const stale = estimateStaleDays(["2026-01-02", "2026-01-09", "2026-01-16", "2026-01-23"]);
  const cap = capWeightedPe([
    { mv: 100, earn: 5 },
    { mv: 200, earn: 10 },
    { mv: 700, earn: 35 },
  ]);
  const org = originLabel(true);
  return [
    { id: "F_GAP", metric: "EPS 間隙", value: `${(gap * 100).toFixed(3)}%`, light: gap <= FWD_EPS_TOL ? "ok" : "bad", note: "reported vs implied · 0.5%" },
    { id: "F_RND", metric: "捨入區間", value: iv.epsLo < iv.eps && iv.eps < iv.epsHi ? "含 implied" : "破", light: iv.epsLo < iv.eps && iv.eps < iv.epsHi ? "ok" : "bad", note: `±${FWD_PE_INC / 2} PE` },
    { id: "F_SRC", metric: "雙源", value: src.status, light: src.status !== "aligned_not_blended" ? "ok" : "warn", note: "不平均 · 23.1 vs 24.0" },
    { id: "F_STALE", metric: "動態過期", value: `${stale}d`, light: stale === 11 ? "ok" : "bad", note: "週頻 ×1.5" },
    { id: "F_CAP", metric: "市值加權 PE", value: cap.toFixed(1), light: cap === 20 ? "ok" : "bad", note: "指數≠ETF" },
    { id: "F_ORG", metric: "源標", value: org.origin, light: org.evidence === "fact_source_reported" ? "ok" : "bad", note: "推算不得叫源報" },
  ];
}
