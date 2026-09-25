/** Method SSOT def01–21 compact. Broker raw never overwritten. Official = actuals. */
import type { Light } from "./types.ts";
import { VRN_FIELDS, VRN_FIELD_N } from "./vrn-field-cache.ts";
import { VRN_FIN_MAP, VRN_FIN_N } from "./vrn-fin-map-cache.ts";
import { VRN_RATING_ALIASES } from "./vrn-rating-cache.ts";
import { vrnRxNote } from "./vrn-rx.ts";
import { VRN_EBIT_ZH_CANDIDATE, VRN_LEX_FILLS, VRN_LEX_MERGE, lexFillOk } from "./vrn-lexicon.ts";

export const VRN_PILLARS = ["五區抽取", "雙層保存", "官方對照", "算術勾稽", "證據仲裁"] as const;

export function vrnUpside(target: number, current: number): number | null {
  if (!current) return null;
  return (target - current) / current;
}

export function vrnYoy(cur: number, base: number): { state: string; value: number | null } {
  if (base === 0) return { state: "NOT_COMPUTABLE_ZERO_BASE", value: null };
  if (!Number.isFinite(base) || !Number.isFinite(cur)) return { state: "NOT_COMPUTABLE_NULL_BASE", value: null };
  const v = (cur - base) / Math.abs(base);
  if (base < 0 && cur > 0) return { state: "TURNAROUND_TO_PROFIT", value: v };
  if (base > 0 && cur < 0) return { state: "TURNAROUND_TO_LOSS", value: v };
  if (base < 0 && cur < 0) return { state: "NEG_TO_NEG_ANNOTATED", value: v };
  return { state: "NORMAL", value: v };
}

export function vrnGross(rev: number, cogs: number): number {
  return rev - cogs;
}

export function vrnBsGap(assets: number, liab: number, eq: number): number {
  return assets - (liab + eq);
}

export function vrnMapLookup(id: string) {
  return VRN_FIN_MAP.find((r) => r.id === id) ?? null;
}

export function vrnFieldLookup(id: string) {
  return VRN_FIELDS.find((r) => r.id === id) ?? null;
}

export function vrnQuickRatioNote(): string {
  return "方法：(流動資產-存貨-預付)/流動負債 · 對照表略預付 · 以方法為準";
}

export function vrnRate(text: string): { lvl: string; w: string } | null {
  const t = text.trim().toLowerCase();
  if (!t) return null;
  const hit = VRN_RATING_ALIASES.find((a) => a.w.toLowerCase() === t);
  if (hit) return hit;
  const part = VRN_RATING_ALIASES.find((a) => a.w.length >= 2 && t.includes(a.w.toLowerCase()));
  return part ?? null;
}

export function vrnMethodQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const ebit = vrnMapLookup("ebit");
  const ebitZh = ebit?.zh ? ebit.zh : VRN_EBIT_ZH_CANDIDATE.zh;
  const up = vrnUpside(1450, 1200);
  return [
    { id: "M_POL", metric: "政策", value: "雙層", light: "ok", note: "券商原貌保留 · 官方實績不覆寫" },
    { id: "M_PIL", metric: "五柱", value: `${VRN_PILLARS.length}`, light: "ok", note: VRN_PILLARS.join("／") },
    { id: "M_FIN", metric: "三語欄", value: `${VRN_FIN_N}`, light: VRN_FIN_N === 195 ? "ok" : "bad", note: "非空原源不覆寫 · 不灌 144k regex" },
    { id: "M_57", metric: "三源欄", value: `${VRN_FIELD_N}`, light: VRN_FIELD_N === 57 ? "ok" : "bad", note: `營收 YF ${vrnFieldLookup("revenue")?.yf ?? "—"}` },
    { id: "M_QR", metric: "速動比", value: "含預付", light: "warn", note: vrnQuickRatioNote() },
    { id: "M_RX", metric: "TW regex", value: "LOCKED", light: "ok", note: vrnRxNote() },
    { id: "M_EBIT", metric: "EBIT 中", value: ebitZh, light: ebit?.zh ? "ok" : "warn", note: ebit?.zh ? "源有值" : "候審填空 · 不改 id" },
    { id: "M_LEX", metric: "K6 英欄", value: `${VRN_LEX_FILLS.length}/14`, light: lexFillOk() ? "ok" : "bad", note: VRN_LEX_MERGE ? "已 merge" : "候審 · 待 --merge" },
    { id: "M_UP", metric: "上漲空間", value: up === null ? "—" : `${(up * 100).toFixed(4)}%`, light: up && Math.abs(up - 0.208333) < 1e-5 ? "ok" : "bad", note: "(1450-1200)/1200 · 21% 合理四捨五入" },
    { id: "M_0", metric: "零基成長", value: vrnYoy(10, 0).state, light: vrnYoy(10, 0).state === "NOT_COMPUTABLE_ZERO_BASE" ? "ok" : "bad", note: "分母零不造無限大" },
  ];
}

export function vrnMethodNote(): string {
  return `VRN 方法 · 三語 ${VRN_FIN_N} · 三源 ${VRN_FIELD_N} · K6 ${VRN_LEX_FILLS.length} 候審 · 不覆寫官方`;
}
