/** VIA Global Liquidity Sandbox Simulation (VIA-GLSS)。ENG075 為成員。舊名 VIA_GFF 為別名。 */
import { buildMarketBook, etfFlowSum } from "./market-book.ts";
import type { Light } from "./types.ts";
import { cacheRevRows, groupAnalysis, latestSnapshot, revContract } from "./tw-revenue.ts";

export const GLSS_ID = "VIA_GLSS";
export const GLSS_NAME = "Global Liquidity Sandbox Simulation";
export const GFF_ID = "VIA_GFF";
export const GFF_NAME = GLSS_NAME;

export type GffMember = {
  id: string;
  role: string;
  write: string;
  live: boolean;
};

export const GLSS_MEMBERS: GffMember[] = [
  { id: "VDF_ENG075", role: "台股月營收 · 實質營運流", write: "rev-cache", live: false },
  { id: "VDF_ENG074", role: "美利率／風險胃納", write: "fred-cache", live: true },
  { id: "VDF_ENG047", role: "美宏觀細項", write: "macro-cover", live: true },
  { id: "VDF_MDL002", role: "YF 價／ETF NAV", write: "yf-book", live: false },
  { id: GLSS_ID, role: "全球流動性沙盒模擬（本專案）", write: "glss-sim", live: false },
];

export const GFF_MEMBERS = GLSS_MEMBERS;

export function gffMembersOk(): boolean {
  return GLSS_MEMBERS.some((m) => m.id === "VDF_ENG075") && GLSS_MEMBERS.filter((m) => m.id === GLSS_ID).length === 1;
}

export type GffRow = {
  id: string;
  layer: string;
  metric: string;
  value: string;
  light: Light;
  note: string;
};

export function runGffSim(now = new Date()): { rows: GffRow[]; note: string } {
  const book = buildMarketBook({ yfLive: false, akLive: false });
  const flow = etfFlowSum(book);
  const rev = cacheRevRows(now);
  const snap = latestSnapshot(rev, now);
  const groups = groupAnalysis(rev, now);
  const c = revContract(now);
  const yoyMed =
    groups.length === 0
      ? null
      : [...groups].sort((a, b) => (b.n ?? 0) - (a.n ?? 0))[0]?.yoyMed ?? null;
  const twEtf = book.filter((r) => r.region === "TW" && (r.kind === "etf" || r.kind === "index"));
  const twFlow = twEtf.reduce((s, r) => s + (r.flow1d ?? 0), 0);

  const rows: GffRow[] = [
    {
      id: "GFF_AUM",
      layer: "ETF",
      metric: "AUM mn",
      value: String(Math.round(flow.aum)),
      light: "warn",
      note: "CACHE 市場簿 · YF 未 LIVE",
    },
    {
      id: "GFF_IN",
      layer: "ETF",
      metric: "1d 流入",
      value: String(Math.round(flow.inFlow)),
      light: "warn",
      note: "創贖≈Δunits×NAV · 種子",
    },
    {
      id: "GFF_OUT",
      layer: "ETF",
      metric: "1d 流出",
      value: String(Math.round(flow.outFlow)),
      light: "warn",
      note: "負值加總",
    },
    {
      id: "GFF_TWETF",
      layer: "TW ETF",
      metric: "0050/EWT 等 1d 流",
      value: String(Math.round(twFlow)),
      light: "warn",
      note: `${twEtf.length} 列 · 非 ENG075`,
    },
    {
      id: "GFF_REV",
      layer: "ENG075",
      metric: `月營收家數 ${c.latest}`,
      value: String(snap.length),
      light: "ok",
      note: `CACHE · 月檔契約 ${c.files} · LIVE 關`,
    },
    {
      id: "GFF_YOY",
      layer: "ENG075",
      metric: "龍頭族群 YoY 中位",
      value: yoyMed == null ? "—" : `${(yoyMed * 100).toFixed(1)}%`,
      light: yoyMed == null ? "warn" : yoyMed >= 0 ? "ok" : "warn",
      note: "實質營收 · 不可當成 ETF 流",
    },
    {
      id: "GFF_LINK",
      layer: "SIM",
      metric: "營收 vs 資金流",
      value: "未因果",
      light: "warn",
      note: "沙盒並列 · 不合併、不回歸、不發明 alpha",
    },
  ];

  return {
    rows,
    note: `VIA-GLSS · 成員 ${GLSS_MEMBERS.length} · ENG075 在籍 · ETF CACHE · 月營收 CACHE ${c.latest}`,
  };
}
