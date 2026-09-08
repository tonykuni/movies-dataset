/** VRN 研報 SSOT v2 候選。activation_allowed=false · 不晉升 · 不造假日期。 */
import type { Light } from "./types.ts";
import { VRN_SSOT_CHAIN_OK, VRN_SSOT_N, VRN_SSOT_PROMOTED, VRN_SSOT_RECS, type VrnSsotRec } from "./vrn-ssot-cache.ts";

export { VRN_SSOT_CHAIN_OK, VRN_SSOT_N, VRN_SSOT_PROMOTED, VRN_SSOT_RECS };
export type { VrnSsotRec };

export type VrnQcRow = { id: string; metric: string; value: string; light: Light; note: string };
export type VrnTpRow = { ticker: string; broker: string; prices: number[]; median: number; doc: string };

function nums(tp: string): number[] {
  return tp
    .split(/[;,\s]+/)
    .map((s) => Number(s))
    .filter((n) => Number.isFinite(n) && n > 0 && n < 1e6);
}

function median(xs: number[]): number {
  const a = [...xs].sort((x, y) => x - y);
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m]! : (a[m - 1]! + a[m]!) / 2;
}

export function vrnSsotQc(): VrnQcRow[] {
  const recs = VRN_SSOT_RECS;
  const unresolved = recs.filter((r) => r.dateState === "UNRESOLVED_EVIDENCE_INSUFFICIENT");
  const brokerC = recs.filter((r) => r.conflictB).length;
  const typeC = recs.filter((r) => r.conflictT).length;
  const absent = recs.filter((r) => r.primary === "ABSENT").length;
  const sparse = recs.filter((r) => r.sparse).length;
  const tp = recs.filter((r) => r.tp).length;
  return [
    { id: "SSOT_N", metric: "列", value: `${recs.length}`, light: recs.length === VRN_SSOT_N ? "ok" : "bad", note: "v0155 64 列候選" },
    { id: "SSOT_CHAIN", metric: "雜湊鏈", value: VRN_SSOT_CHAIN_OK ? "齊" : "斷", light: VRN_SSOT_CHAIN_OK ? "ok" : "bad", note: "previous_record_hash 銜接" },
    { id: "SSOT_PROMO", metric: "晉升", value: VRN_SSOT_PROMOTED ? "已升" : "未升", light: VRN_SSOT_PROMOTED ? "warn" : "ok", note: "activation_allowed=false · v1 指標不動" },
    { id: "SSOT_DATE", metric: "日期未決", value: `${unresolved.length}`, light: unresolved.length ? "warn" : "ok", note: unresolved[0]?.doc || "無造假" },
    { id: "SSOT_BRK", metric: "券商衝突", value: `${brokerC}`, light: brokerC ? "warn" : "ok", note: "FILENAME vs 內文 · 審查" },
    { id: "SSOT_TYP", metric: "文類衝突", value: `${typeC}`, light: typeC ? "warn" : "ok", note: "FILENAME_RULE vs NATIVE_TEXT" },
    { id: "SSOT_PRI", metric: "主代碼缺", value: `${absent}`, light: absent ? "warn" : "ok", note: "產業／晨會可缺 · 不發明" },
    { id: "SSOT_DOCX", metric: "稀疏 docx", value: `${sparse}`, light: sparse ? "warn" : "ok", note: "v0154B 草稿 · 僅日期欄" },
    { id: "SSOT_TP", metric: "目標價列", value: `${tp}`, light: "ok", note: "review-ready · 未晉升共識" },
  ];
}

/** 單檔公司報告、主代碼在、1–2 個價 → MEDIAN。晨會多價不進。 */
export function vrnCompanyTp(): VrnTpRow[] {
  const out: VrnTpRow[] = [];
  for (const r of VRN_SSOT_RECS) {
    if (!r.ticker || !/^\d{4}$/.test(r.ticker)) continue;
    if (!/COMPANY/.test(r.type)) continue;
    const prices = nums(r.tp);
    if (prices.length < 1 || prices.length > 2) continue;
    out.push({ ticker: r.ticker, broker: r.broker, prices, median: median(prices), doc: r.doc });
  }
  return out;
}

export function vrnSsotNote(): string {
  const q = vrnSsotQc();
  const u = q.find((r) => r.id === "SSOT_DATE");
  return `VRN SSOT v2 候選 ${VRN_SSOT_N} · 未晉升 · 鏈${VRN_SSOT_CHAIN_OK ? "齊" : "斷"} · 未決 ${u?.value ?? "?"} · 不造假`;
}

export function vrnSsotLight(): Light {
  const q = vrnSsotQc();
  if (q.some((r) => r.light === "bad")) return "bad";
  if (q.some((r) => r.light === "warn")) return "ok";
  return "ok";
}
