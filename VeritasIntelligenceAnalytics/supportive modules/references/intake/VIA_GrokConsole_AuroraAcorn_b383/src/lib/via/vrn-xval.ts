/** MDL008 緊湊：單位／容差／同義字 fallback／信心。API LIVE 關 → NO_API 合法。 */
import type { Light } from "./types.ts";

export const XVAL_UNIT: Record<string, number> = {
  thousand: 0.001,
  million: 1,
  billion: 1000,
  hundred_million: 100,
};

export const XVAL_TOL = { large: 0.001, medium: 0.005, small: 0.01 } as const;
export const XVAL_CONF = { base: 0.8, match: 0.15, unresolved: 0.2 } as const;

export const XVAL_SYN: Record<string, string[]> = {
  revenue: ["gross_revenue", "net_sales", "sales"],
  gross_profit: ["gross_income", "gross"],
  operating_income: ["ebit", "operating_profit"],
  net_income: ["pat", "net_profit"],
  eps: ["basic_eps", "diluted_eps"],
};

export const HG_PLUGIN_ORDER = [
  "ssot",
  "registry",
  "runtime_bridge",
  "env_manager",
  "ast_planner",
  "celeritas",
  "aegis",
] as const;

export function isHistorical(period: string): boolean {
  const s = String(period).trim();
  if (/^(20\d{2})[EeFfPp]$/.test(s)) return false;
  return /^(20\d{2})[AaHh]?$/.test(s) || /^20\d{2}$/.test(s);
}

export function toMillion(value: string | number, unit = "million"): number | null {
  const n = Number(String(value).replace(/[,，]/g, ""));
  if (!Number.isFinite(n)) return null;
  return n * (XVAL_UNIT[unit] ?? 1);
}

export function precision1(v: number): number {
  return Math.floor(Math.round(v * 10) ) / 10;
}

export function stdVal(value: string | number, unit = "million"): number | null {
  const v = toMillion(value, unit);
  return v == null ? null : precision1(v);
}

export function tolerance(v: number | null): number {
  if (v == null) return XVAL_TOL.small;
  const a = Math.abs(v);
  if (a >= 1000) return XVAL_TOL.large;
  if (a >= 100) return XVAL_TOL.medium;
  return XVAL_TOL.small;
}

export function classifyMismatch(report: number, api: number): string {
  if (api === 0) return "zero_denominator";
  const ratio = report / api;
  if ((ratio >= 990 && ratio <= 1010) || (ratio >= 0.00099 && ratio <= 0.00101)) return "unit_error_thousand";
  if ((ratio >= 99 && ratio <= 101) || (ratio >= 0.0099 && ratio <= 0.0101)) return "unit_error_hundred";
  if (ratio >= -1.05 && ratio <= -0.95) return "sign_opposite";
  return "unknown";
}

export function compareOne(report: number, api: number): {
  status: "MATCH" | "MISMATCH";
  diffPct: number;
  final: number;
  reason: string;
  conf: number;
} {
  const diff = Math.abs(report - api) / Math.max(Math.abs(api), 0.01);
  const tol = tolerance(api);
  if (diff <= tol) {
    return { status: "MATCH", diffPct: diff * 100, final: api, reason: "", conf: XVAL_CONF.base + XVAL_CONF.match };
  }
  return {
    status: "MISMATCH",
    diffPct: diff * 100,
    final: report,
    reason: classifyMismatch(report, api),
    conf: XVAL_CONF.base - XVAL_CONF.unresolved,
  };
}

export function xvalQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const a = compareOne(1000, 1000.5);
  const u = classifyMismatch(1_000_000, 1000);
  return [
    { id: "X_TOL", metric: "大數容差", value: a.status, light: a.status === "MATCH" ? "ok" : "bad", note: "≥1000m 0.1%" },
    { id: "X_UNIT", metric: "千倍誤", value: u, light: u === "unit_error_thousand" ? "ok" : "bad", note: "fallback 換單位" },
    { id: "X_HG", metric: "插件序", value: String(HG_PLUGIN_ORDER.length), light: HG_PLUGIN_ORDER.length === 7 ? "ok" : "bad", note: HG_PLUGIN_ORDER.join("→") },
    { id: "X_API", metric: "API", value: "NO_API", light: "ok", note: "MDL007 LIVE 關 · 官方列後補" },
  ];
}
