/** 持股 × Consensus：單檔或全勾。目標價＝FS Median 與 YF Median，各帶 +-%。 */
import { AETF_UNIVERSE, SEAL_HOLD_FUNDS, aetfMeta, cacheHolds, cashRows, type AetfHold } from "./active-etf.ts";
import { CNS_SEED } from "./consensus.ts";

export { SEAL_HOLD_FUNDS };
export const SEAL_HOLD_ASOF = "2026-08-29";

export type HoldAction = "超額配置" | "強勢重壓" | "順勢加碼" | "逢低承接" | "單檔持有";

export type HoldAggRow = {
  stock: string;
  name: string;
  group: string;
  wgt: number;
  holdN: number;
  selN: number;
  action: HoldAction;
  cost: number | null;
  adj: number | null;
  fsLow: number | null;
  fsMean: number | null;
  fsMedian: number | null;
  yfMedian: number | null;
  yfPx: number | null;
};

export type FundPick = { ticker: string; name: string; issuer: string; scope: "TW" | "GL"; hasHold: boolean; aum: number };

/** 封存 Standalone「總持股聚合」6 列（全勾 9 檔）。估均價＝成本預估。 */
const SEAL_AGG: HoldAggRow[] = [
  { stock: "2330", name: "台積電", group: "半導體", wgt: 25.8, holdN: 9, selN: 9, action: "超額配置", cost: 519.5, adj: 560.0, fsLow: 590.0, fsMean: 696.2, fsMedian: 611.9, yfMedian: null, yfPx: null },
  { stock: "2317", name: "鴻海", group: "AI伺服器", wgt: 4.8, holdN: 6, selN: 9, action: "強勢重壓", cost: 485.8, adj: 547.0, fsLow: 560.0, fsMean: 627.4, fsMedian: 636.2, yfMedian: null, yfPx: null },
  { stock: "2454", name: "聯發科", group: "半導體", wgt: 4.6, holdN: 6, selN: 9, action: "順勢加碼", cost: 652.7, adj: 684.0, fsLow: 720.0, fsMean: 794.3, fsMedian: 839.5, yfMedian: null, yfPx: null },
  { stock: "2382", name: "廣達", group: "AI伺服器", wgt: 2.8, holdN: 6, selN: 9, action: "順勢加碼", cost: 564.6, adj: 612.0, fsLow: 650.0, fsMean: 751.6, fsMedian: 753.0, yfMedian: null, yfPx: null },
  { stock: "6669", name: "緯穎", group: "AI伺服器", wgt: 2.3, holdN: 5, selN: 9, action: "強勢重壓", cost: 358.2, adj: 399.0, fsLow: 408.0, fsMean: 465.2, fsMedian: 418.9, yfMedian: null, yfPx: null },
  { stock: "2308", name: "台達電", group: "電源管理", wgt: 1.8, holdN: 8, selN: 9, action: "逢低承接", cost: 516.3, adj: 538.0, fsLow: 560.0, fsMean: 581.2, fsMedian: 626.0, yfMedian: null, yfPx: null },
];

const COST: Record<string, Pick<HoldAggRow, "cost" | "adj" | "fsLow" | "fsMean" | "fsMedian" | "group" | "name">> = Object.fromEntries(
  SEAL_AGG.map((r) => [r.stock, r]),
);

export function fundNameOf(ticker: string): string {
  return aetfMeta(ticker).name;
}

export function fundPickList(): FundPick[] {
  const aum = new Map(cashRows().map((c) => [c.ticker, c.aum]));
  const hold = new Set<string>([...SEAL_HOLD_FUNDS, ...cacheHolds().map((h) => h.fund)]);
  return AETF_UNIVERSE.map((ticker) => {
    const m = aetfMeta(ticker);
    return { ticker, name: m.name, issuer: m.issuer, scope: m.scope, hasHold: hold.has(ticker), aum: aum.get(ticker) ?? 0 };
  });
}

export function costPnl(cost: number | null, adj: number | null): number | null {
  if (cost == null || adj == null || cost <= 0) return null;
  return adj / cost - 1;
}

export function yfTargetOf(stock: string): { median: number | null; px: number | null } {
  const s = CNS_SEED.find((x) => x.code === stock);
  if (!s || s.medianYf == null || s.priceYf == null) return { median: null, px: null };
  return { median: s.medianYf, px: s.priceYf };
}

export function attachTargets(r: HoldAggRow): HoldAggRow {
  const y = yfTargetOf(r.stock);
  return { ...r, yfMedian: y.median, yfPx: y.px };
}

export function fsUpside(adj: number | null, target: number | null): number | null {
  if (adj == null || target == null || adj <= 0) return null;
  return target / adj - 1;
}

export function yfUpside(px: number | null, target: number | null): number | null {
  return fsUpside(px, target);
}

function actionOf(wgt: number, pnl: number | null, up: number | null): HoldAction {
  if (wgt >= 15) return "超額配置";
  if ((up ?? 0) > 0.12 && (pnl ?? 0) < 0.04) return "逢低承接";
  if ((up ?? 0) > 0.12 && (pnl ?? 0) >= 0.04) return "順勢加碼";
  if (wgt >= 4) return "強勢重壓";
  return "單檔持有";
}

function aumOf(ticker: string): number {
  return cashRows().find((c) => c.ticker === ticker)?.aum ?? 1;
}

/** 單檔：CACHE 日持股 × 封存估均價。全勾 9 檔：封存聚合。其餘選集：AUM 加權三檔種子。 */
export function aggregateHolds(picked: string[]): HoldAggRow[] {
  const uni = new Set<string>(AETF_UNIVERSE);
  const sel = [...new Set(picked.map((t) => t.toUpperCase()))].filter((t) => uni.has(t));
  if (sel.length === 0) return [];
  const sealSet = new Set<string>(SEAL_HOLD_FUNDS);
  const allSeal = sel.length >= 8 && sel.every((t) => sealSet.has(t)) && SEAL_HOLD_FUNDS.filter((t) => sel.includes(t)).length >= 8;
  if (allSeal) {
    return SEAL_AGG.map((r) => attachTargets({ ...r, selN: sel.length, holdN: Math.min(r.holdN, sel.length) }));
  }
  const holds: AetfHold[] = cacheHolds().filter((h) => sel.includes(h.fund));
  if (holds.length === 0) return [];
  const byStock = new Map<string, { w: number; funds: Set<string>; name: string }>();
  const aumSel = sel.reduce((s, t) => s + aumOf(t), 0) || 1;
  for (const h of holds) {
    const rec = byStock.get(h.stock) ?? { w: 0, funds: new Set<string>(), name: h.name };
    rec.w += h.wgt * (aumOf(h.fund) / aumSel);
    rec.funds.add(h.fund);
    rec.name = h.name;
    byStock.set(h.stock, rec);
  }
  return [...byStock.entries()]
    .map(([stock, rec]) => {
      const c = COST[stock];
      const wgt = Number(rec.w.toFixed(2));
      const pnl = costPnl(c?.cost ?? null, c?.adj ?? null);
      const up = fsUpside(c?.adj ?? null, c?.fsMedian ?? null);
      const y = yfTargetOf(stock);
      return attachTargets({
        stock,
        name: c?.name ?? rec.name,
        group: c?.group ?? "",
        wgt,
        holdN: rec.funds.size,
        selN: sel.length,
        action: sel.length === 1 ? ("單檔持有" as const) : actionOf(wgt, pnl, up),
        cost: c?.cost ?? null,
        adj: c?.adj ?? null,
        fsLow: c?.fsLow ?? null,
        fsMean: c?.fsMean ?? null,
        fsMedian: c?.fsMedian ?? null,
        yfMedian: y.median,
        yfPx: y.px,
      });
    })
    .sort((a, b) => b.wgt - a.wgt);
}

export function holdKpis(rows: HoldAggRow[]): { pe: string; wgtUp: string; review: number } {
  const w = rows.reduce((s, r) => s + r.wgt, 0) || 1;
  const up = rows.reduce((s, r) => s + r.wgt * (costPnl(r.cost, r.adj) ?? 0), 0) / w;
  const review = rows.filter((r) => (fsUpside(r.adj, r.fsMedian) ?? 0) < 0.08).length;
  return { pe: "15.6x", wgtUp: `${(up * 100).toFixed(1)}%`, review };
}

export function defaultPicked(): string[] {
  return [...SEAL_HOLD_FUNDS];
}
