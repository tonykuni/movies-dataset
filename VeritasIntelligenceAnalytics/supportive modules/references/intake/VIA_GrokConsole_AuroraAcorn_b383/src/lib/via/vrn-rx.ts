/** Ticker/date regex 冊。TW LOCKED 用 tw-ticker lookaround，不用附件 \\b 寬鬆式。ETF 13 類在 tw-ticker-all。 */
import { TW_BB_RE, TW_CORE_RE, TW_YF_RE } from "./tw-ticker.ts";

export const VRN_RX = {
  twCore: TW_CORE_RE,
  twYf: TW_YF_RE,
  twBb: TW_BB_RE,
  rocYear: /(?:民國)?\s*(\d{2,3})\s*年/,
  fy: /\b(?:FY|財年|會計年度)\s*-?\s*(\d{2,4})\b/i,
  qZh: /第?([一二三四1-4])\s*季/,
  yq: /\b(?:([1-4])Q(\d{2,4})|(\d{2,4})Q([1-4]))\b/i,
} as const;

export function rocToGregorian(roc: number): number {
  return roc + 1911;
}

export function vrnRxNote(): string {
  return "TW ticker LOCKED lookaround · 附件 LOOSE \\b 不入圈 · ETF 13類 v0100 · 民國+1911";
}
