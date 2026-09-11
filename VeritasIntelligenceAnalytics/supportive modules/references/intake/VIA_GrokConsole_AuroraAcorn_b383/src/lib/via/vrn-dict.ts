/** Broker + annual extract + VRN manifest snapshot. 不發明、不假設本機有檔。 */
import type { Light } from "./types.ts";
import { VRN_ANN_FORMULAS, VRN_ANN_ITEMS, VRN_ANN_N, VRN_ANN_NOTE } from "./vrn-annual-cache.ts";
import {
  VRN_BROKERS,
  VRN_BROKERS_EXT,
  VRN_BROKER_EXT_N,
  VRN_BROKER_N,
  VRN_DROP_KEYS,
} from "./vrn-broker-cache.ts";

export { VRN_ANN_FORMULAS, VRN_ANN_ITEMS, VRN_ANN_N, VRN_ANN_NOTE, VRN_BROKER_EXT_N, VRN_BROKER_N, VRN_DROP_KEYS };

export const VRN_MANIFEST = {
  prodFound: 94,
  prodMissing: 14,
  prodExtra: 76,
  core: 8,
  ssot: 7,
  promotion: "OPERATOR_REVIEW",
  tree: "functional modules/VRN · 他樹快照 2026-08-11 · 本沙盒不宣稱存在",
};

export type BrokerHit = { zh: string; abbr: string; n: number; collide: boolean };

export function vrnDropped(q: string): boolean {
  const t = q.trim().toLowerCase();
  return (VRN_DROP_KEYS as readonly string[]).some((k) => k.toLowerCase() === t);
}

export function vrnBrokerLookup(q: string): BrokerHit | null {
  const t = q.trim();
  if (!t || vrnDropped(t)) return null;
  const tl = t.toLowerCase();
  const hits = VRN_BROKERS.filter(
    (b) => b.zh === t || b.abbr.toLowerCase() === tl || b.al.some((a) => a.toLowerCase() === tl),
  );
  if (hits.length) {
    return { zh: hits[0]!.zh, abbr: hits[0]!.abbr, n: hits.length, collide: hits.length > 1 };
  }
  const ext = VRN_BROKERS_EXT.filter(
    (b) => b.c.toLowerCase() === tl || b.zh === t || b.en.toLowerCase() === tl,
  );
  if (!ext.length) return null;
  return { zh: ext[0]!.zh, abbr: ext[0]!.c, n: ext.length, collide: ext.length > 1 };
}

export function vrnAbbrCollisions(): { abbr: string; names: string[] }[] {
  const m = new Map<string, string[]>();
  for (const b of VRN_BROKERS) {
    const cur = m.get(b.abbr) ?? [];
    cur.push(b.zh);
    m.set(b.abbr, cur);
  }
  return [...m.entries()].filter(([, n]) => n.length > 1).map(([abbr, names]) => ({ abbr, names }));
}

export function vrnAnnByBlock(): Record<string, number> {
  const o: Record<string, number> = {};
  for (const i of VRN_ANN_ITEMS) o[i.b] = (o[i.b] ?? 0) + 1;
  return o;
}

export function vrnFcfNote(): string {
  return VRN_ANN_FORMULAS.fcf;
}

export function vrnBvpsNote(): string {
  return VRN_ANN_FORMULAS.bvps;
}

export function vrnDictQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const coll = vrnAbbrCollisions();
  const yuanta = vrnBrokerLookup("元大");
  const gs = vrnBrokerLookup("GS");
  const dh = vrnBrokerLookup("大華");
  const ms = vrnBrokerLookup("大摩");
  const jpm = vrnBrokerLookup("小摩");
  const dropped = vrnBrokerLookup("摩根");
  const ctbc = vrnBrokerLookup("中信");
  const citic = vrnBrokerLookup("中信證券");
  const gj = vrnBrokerLookup("國泰君安");
  const gf = vrnBrokerLookup("廣發");
  const cathay = vrnBrokerLookup("國泰");
  const blocks = vrnAnnByBlock();
  const cnGone = citic === null && gj === null && gf === null;
  return [
    { id: "D_BRK", metric: "券商", value: `${VRN_BROKER_N}+${VRN_BROKER_EXT_N}`, light: VRN_BROKER_N === 29 && VRN_BROKER_EXT_N === 28 ? "ok" : "bad", note: "延伸無陸券 · 刪摩根" },
    { id: "D_YT", metric: "元大", value: yuanta?.abbr ?? "—", light: yuanta?.abbr === "YT" ? "ok" : "bad", note: "Yuanta" },
    { id: "D_GS", metric: "GS", value: gs?.zh ?? "—", light: gs?.zh === "高盛" && dh?.abbr === "DH" && !coll.length ? "ok" : "bad", note: `高盛 · 大華 ${dh?.abbr}` },
    { id: "D_MS", metric: "MS", value: ms?.zh ?? "—", light: ms?.abbr === "MS" ? "ok" : "bad", note: "摩根士丹利／大摩" },
    { id: "D_JPM", metric: "JPM", value: jpm?.zh ?? "—", light: jpm?.abbr === "JPM" && dropped === null ? "ok" : "bad", note: "摩根大通／小摩 · 「摩根」已刪" },
    { id: "D_CTBC", metric: "中信", value: ctbc?.abbr ?? "—", light: ctbc?.abbr === "CTBC" && cnGone ? "ok" : "bad", note: "臺 CTBC · 陸券已刪" },
    { id: "D_CN", metric: "陸券", value: cnGone ? "已刪" : "殘留", light: cnGone ? "ok" : "bad", note: "CITIC／君安／中金／海通／廣發" },
    { id: "D_CT", metric: "國泰", value: cathay?.abbr ?? "—", light: cathay?.abbr === "CT" && gj === null ? "ok" : "bad", note: "不併君安" },
    { id: "D_ANN", metric: "年度欄", value: `${VRN_ANN_N}`, light: VRN_ANN_N === 79 ? "ok" : "bad", note: Object.entries(blocks).map(([k, v]) => `${k}${v}`).join(" ") },
    { id: "D_FCF", metric: "FCF", value: "CFO+CapEx", light: /CFO/.test(vrnFcfNote()) ? "ok" : "bad", note: vrnFcfNote() },
    { id: "D_BV", metric: "BVPS", value: "歸母權益", light: /母公司/.test(vrnBvpsNote()) ? "ok" : "bad", note: vrnBvpsNote() },
    { id: "D_MAN", metric: "清單", value: `缺${VRN_MANIFEST.prodMissing} 多${VRN_MANIFEST.prodExtra}`, light: "warn", note: `核心 ${VRN_MANIFEST.core} · 晉升 ${VRN_MANIFEST.promotion} · ${VRN_MANIFEST.tree}` },
  ];
}

export function vrnDictNote(): string {
  return `券商 ${VRN_BROKER_N} · 延伸 ${VRN_BROKER_EXT_N} 無陸券 · 摩根已刪 · 年度 ${VRN_ANN_N}`;
}

export function vrnExtTw(): string[] {
  return VRN_BROKERS_EXT.filter((x) => x.cc === "TW").map((x) => x.zh);
}
