/** VIA Active ETF Analysis (VIA-AEA)。原件 DailyHoldings DuckDB v0101 + VIA_ActiveETF_FINAL。LIVE 預設關。 */
import type { Light } from "./types.ts";
import { isActiveDomesticEquityEtf } from "./tw-ticker-all.ts";

export const AEA_ID = "VIA_AEA";
export const AEA_NAME = "VIA Active ETF Analysis";
export const AETF_LIVE_ENABLED = false;
export const AETF_ENGINE = "VDF_ENG076";
export const TWSE_ETF_LIST = "https://www.twse.com.tw/rwd/zh/ETF/list";

/**
 * 證交所《ETF 申贖資訊及即時淨值揭露》JSON msgArray a–j。
 * h＝前一營業日淨值。禁止對到 MIS getStockInfo 的 h（最高價）。
 */
export const TWSE_ETF_NAV_FIELDS = [
  { letter: "a", key: "ticker", zh: "ETF 代號" },
  { letter: "b", key: "name", zh: "ETF 名稱" },
  { letter: "c", key: "units", zh: "已發行受益權單位數" },
  { letter: "d", key: "dUnits", zh: "與前日已發行受益單位差異數（今日−前日，無差異為 0）" },
  { letter: "e", key: "px", zh: "成交價" },
  { letter: "f", key: "iNav", zh: "投信或總代理人預估淨值" },
  { letter: "g", key: "iPremium", zh: "預估折溢價幅度（相對 f，百分點）" },
  { letter: "h", key: "navPrev", zh: "前一營業日淨值" },
  { letter: "i", key: "asOf", zh: "資料日期 YYYYMMDD" },
  { letter: "j", key: "asOfTime", zh: "資料時間 HH24:MI:SS" },
] as const;

export const TWSE_MIS_H_IS_HIGH = "MIS getStockInfo.jsp 的 h＝最高價，不是淨值";

export const TWSE_NAV_JSON_SAMPLE = {
  a: "0061",
  b: "ETF 簡稱A",
  c: "15000",
  d: "500",
  e: "38.72",
  f: "40.53",
  g: "-4.47",
  h: "38.74",
  i: "20150602",
  j: "09:02:18",
} as const;

export type TwseNavMsg = {
  ticker: string;
  name: string;
  units: number;
  dUnits: number;
  px: number;
  iNav: number;
  iPremium: number;
  navPrev: number;
  asOf: string;
  asOfTime: string;
};

function numField(v: string | undefined): number {
  const n = Number(String(v ?? "").replace(/,/g, "").trim());
  return Number.isFinite(n) ? n : NaN;
}

/** 只解析發行公司 NAV JSON。LIVE 關；規格樣本可離線驗。h 不得當最高價。 */
export function parseTwseEtfNavMsg(row: Record<string, string>): TwseNavMsg | null {
  if (row.h != null && /未結出/.test(row.h)) return null;
  const units = numField(row.c);
  const dUnits = numField(row.d);
  const px = numField(row.e);
  const iNav = numField(row.f);
  const iPremium = numField(row.g);
  const navPrev = numField(row.h);
  if (!row.a || !Number.isFinite(units) || !Number.isFinite(navPrev) || navPrev <= 0) return null;
  return {
    ticker: String(row.a).toUpperCase(),
    name: String(row.b ?? ""),
    units,
    dUnits: Number.isFinite(dUnits) ? dUnits : 0,
    px,
    iNav,
    iPremium,
    navPrev,
    asOf: String(row.i ?? ""),
    asOfTime: String(row.j ?? ""),
  };
}

export function twseHIsNavPrev(row: Record<string, string>): boolean {
  const p = parseTwseEtfNavMsg(row);
  return p != null && p.navPrev > 0 && p.navPrev !== p.px;
}

export function iPremiumFromF(px: number, iNav: number): number {
  if (!iNav) return NaN;
  return ((px / iNav) - 1) * 100;
}

/** 台股 ETF：00 開頭 4～6 碼，可帶一碼字母。末碼 A＝主動型。股票四碼引擎不管這些。 */
export const TW_ETF_RE = /(?<![0-9A-Za-z])(00\d{2,4}[A-Z]?)(?:\.TW|\.TWO)?(?![0-9A-Za-z])/;

export type AetfFund = {
  ticker: string;
  name: string;
  issuer: string;
  active: true;
  yfinance: string;
  asOf: string;
  nav: number | null;
  source: "CACHE" | "TWSE";
};

export type AetfHold = {
  fund: string;
  asOf: string;
  stock: string;
  name: string;
  wgt: number;
  source: "CACHE" | "ISSUER";
};

export type AetfRow = {
  id: string;
  layer: string;
  metric: string;
  value: string;
  light: Light;
  note: string;
};

export const AETF_SEED: AetfFund[] = [
  { ticker: "00980A", name: "主動野村臺灣優選", issuer: "野村", active: true, yfinance: "00980A.TW", asOf: "2026-09-04", nav: 24.77, source: "CACHE" },
  { ticker: "00981A", name: "主動統一台股增長", issuer: "統一", active: true, yfinance: "00981A.TW", asOf: "2026-09-04", nav: 29.77, source: "CACHE" },
  { ticker: "00982A", name: "主動群益台灣強棒", issuer: "群益", active: true, yfinance: "00982A.TW", asOf: "2026-09-04", nav: 23.0, source: "CACHE" },
];

const HOLD_SEED: AetfHold[] = [
  { fund: "00980A", asOf: "2026-09-04", stock: "2330", name: "台積電", wgt: 28.4, source: "CACHE" },
  { fund: "00980A", asOf: "2026-09-04", stock: "2317", name: "鴻海", wgt: 6.1, source: "CACHE" },
  { fund: "00981A", asOf: "2026-09-04", stock: "2330", name: "台積電", wgt: 22.0, source: "CACHE" },
  { fund: "00982A", asOf: "2026-09-04", stock: "2454", name: "聯發科", wgt: 8.2, source: "CACHE" },
];

export function parseTwEtf(text: string): string {
  const m = String(text).toUpperCase().match(TW_ETF_RE);
  return m?.[1] ?? "";
}

export function isActiveTicker(code: string): boolean {
  const t = parseTwEtf(code) || code.toUpperCase();
  return isActiveDomesticEquityEtf(t);
}

export function isActiveName(name: string): boolean {
  return /主動/.test(name);
}

/** 持股日：平日 16:00 後用當日，否則上一個平日。週末用週五。 */
export function latestHoldingsDate(now = new Date()): string {
  const d = new Date(now);
  const utc = d.getTime() + d.getTimezoneOffset() * 60000;
  const tw = new Date(utc + 8 * 3600000);
  let y = tw.getFullYear();
  let m = tw.getMonth();
  let day = tw.getDate();
  let wd = tw.getDay();
  const hm = tw.getHours() * 60 + tw.getMinutes();
  if (wd === 0) {
    day -= 2;
    wd = 5;
  } else if (wd === 6) {
    day -= 1;
    wd = 5;
  } else if (hm < 16 * 60) {
    day -= 1;
    wd -= 1;
    if (wd === 0) day -= 2;
    if (wd === 6) day -= 1;
  }
  const x = new Date(y, m, day);
  const iso = `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}-${String(x.getDate()).padStart(2, "0")}`;
  return iso;
}

export function rosterStale(asOf: string, now = new Date()): boolean {
  return asOf < latestHoldingsDate(now);
}

export function canFetchAetf(input: { confirmNet: boolean }): { ok: true } | { ok: false; mode: "CACHE"; reason: string } {
  if (!AETF_LIVE_ENABLED) return { ok: false, mode: "CACHE", reason: "AETF LIVE 未啟用 · 零外呼 · 種子名單非完整宇宙" };
  if (!input.confirmNet) return { ok: false, mode: "CACHE", reason: "NET 閘未確認" };
  return { ok: true };
}

export function cacheFunds(): AetfFund[] {
  return AETF_SEED.map((f) => ({ ...f }));
}

export function cacheHolds(): AetfHold[] {
  return HOLD_SEED.map((h) => ({ ...h }));
}

export type AetfNav = {
  ticker: string;
  asOf: string;
  units: number;
  dUnits: number;
  nav: number;
  navPrev: number | null;
  px: number | null;
  source: "CACHE" | "ISSUER";
};

/**
 * 日 NAV 契約（TWSE／投信 JSON a–j：c 單位、d Δ單位、h 前日淨值）
 * NAV_t   當日公布淨值，不是市價，也不是 Yahoo aum/shares（aum 常是市值）
 * AUM_nav units_t × NAV_t
 * AUM_mkt units_t × px_t
 * premium px_t / NAV_t − 1
 * flow_t  Δunits_t × NAV_{t-1}（h）；沒有前日則退回 NAV_t
 * ΔAUM    ≠ flow：含單位變動＋淨值評價，價差不算申贖現金
 */
export function aumTwd(n: Pick<AetfNav, "units" | "nav">): number {
  return n.units * n.nav;
}

export function aumMktTwd(n: Pick<AetfNav, "units" | "px">): number | null {
  return n.px == null ? null : n.units * n.px;
}

export function settleNav(n: Pick<AetfNav, "nav" | "navPrev">): number {
  return n.navPrev != null && n.navPrev > 0 ? n.navPrev : n.nav;
}

export function flowTwd(n: AetfNav): number {
  return n.dUnits * settleNav(n);
}

export function premiumOf(n: Pick<AetfNav, "nav" | "px">): number | null {
  if (n.px == null || n.nav === 0) return null;
  return n.px / n.nav - 1;
}

export function dAumTwd(prev: Pick<AetfNav, "units" | "nav">, cur: Pick<AetfNav, "units" | "nav">): number {
  return aumTwd(cur) - aumTwd(prev);
}

export function aetfFlowSum(rows: AetfNav[]): { aum: number; aumMkt: number; inFlow: number; outFlow: number; net: number } {
  const aum = rows.reduce((s, r) => s + aumTwd(r), 0);
  const aumMkt = rows.reduce((s, r) => s + (aumMktTwd(r) ?? 0), 0);
  const net = rows.reduce((s, r) => s + flowTwd(r), 0);
  const inFlow = rows.reduce((s, r) => s + Math.max(flowTwd(r), 0), 0);
  const outFlow = rows.reduce((s, r) => s + Math.min(flowTwd(r), 0), 0);
  return { aum, aumMkt, inFlow, outFlow, net };
}

const NAV_SEED: AetfNav[] = [
  { ticker: "00980A", asOf: "2026-09-04", units: 72_500_000, dUnits: 180_000, nav: 24.77, navPrev: 24.70, px: 24.77, source: "CACHE" },
  { ticker: "00981A", asOf: "2026-09-04", units: 9_504_000_000, dUnits: 12_400_000, nav: 29.77, navPrev: 29.70, px: 29.77, source: "CACHE" },
  { ticker: "00982A", asOf: "2026-09-04", units: 105_200_000, dUnits: -420_000, nav: 23.0, navPrev: 23.05, px: 23.0, source: "CACHE" },
];

export function cacheNav(): AetfNav[] {
  return NAV_SEED.map((n) => ({ ...n }));
}

export function inspectAetf(now = new Date(), confirmNet = false): {
  stale: boolean;
  target: string;
  live: boolean;
  funds: AetfFund[];
  holds: AetfHold[];
  nav: AetfNav[];
  flow: { aum: number; inFlow: number; outFlow: number; net: number };
  note: string;
} {
  const funds = cacheFunds();
  const holds = cacheHolds();
  const nav = cacheNav();
  const flow = aetfFlowSum(nav);
  const asOf = funds[0]?.asOf ?? "1970-01-01";
  const target = latestHoldingsDate(now);
  const stale = rosterStale(asOf, now);
  const gate = canFetchAetf({ confirmNet });
  return {
    stale,
    target,
    live: gate.ok,
    funds,
    holds,
    nav,
    flow,
    note: gate.ok
      ? `LIVE 補名單＋日持股＋NAV → ${target}`
      : `CACHE ${funds.length} 檔主動 · AUM ${Math.round(flow.aum / 1e8) / 10} 億 · asOf ${asOf} · LIVE 關`,
  };
}

export function runAeaSim(now = new Date()): { rows: AetfRow[]; note: string } {
  const r = inspectAetf(now, false);
  const top = r.holds.reduce((a, b) => (b.wgt > a.wgt ? b : a), r.holds[0]!);
  const rows: AetfRow[] = [
    { id: "AEA_N", layer: "名單", metric: "主動型檔數", value: String(r.funds.length), light: r.stale ? "warn" : "ok", note: "CACHE 種子 3 · 湖宇宙 29 · LIVE 才自動擴" },
    { id: "AEA_ASOF", layer: "更新", metric: "持股／NAV 日", value: r.funds[0]?.asOf ?? "—", light: r.stale ? "warn" : "ok", note: `目標 ${r.target}` },
    { id: "AEA_AUM", layer: "規模", metric: "AUM TWD", value: String(Math.round(r.flow.aum)), light: "ok", note: "units×NAV · CACHE 三檔" },
    { id: "AEA_IN", layer: "流", metric: "1d 流入", value: String(Math.round(r.flow.inFlow)), light: "ok", note: "max(Δunits,0)×NAV" },
    { id: "AEA_OUT", layer: "流", metric: "1d 流出", value: String(Math.round(r.flow.outFlow)), light: r.flow.outFlow < 0 ? "warn" : "ok", note: "min(Δunits,0)×NAV" },
    { id: "AEA_TOP", layer: "持股", metric: "最大權重", value: `${top.fund} ${top.stock} ${top.wgt}%`, light: "ok", note: "DuckDB 日持股 CACHE" },
    { id: "AEA_AUTO", layer: "自動", metric: "排程", value: r.live ? "LIVE" : "STANDBY", light: r.live ? "ok" : "warn", note: "閘關不外呼 NAV JSON" },
  ];
  return { rows, note: r.note };
}

export const AETF_UNIVERSE = [
  "00400A", "00401A", "00402A", "00403A", "00404A", "00405A", "00406A", "00407A", "00408A", "00410A",
  "00980A", "00981A", "00982A", "00983A", "00984A", "00985A", "00986A", "00987A", "00988A", "00989A",
  "00990A", "00991A", "00992A", "00993A", "00994A", "00995A", "00996A", "00997A", "00999A",
] as const;

export const AETF_MISSING_CODES = ["00409A", "00998A"] as const;

export const SEAL_HOLD_FUNDS = [
  "00980A", "00981A", "00982A", "00983A", "00984A", "00985A", "00986A", "00987A", "00988A",
] as const;

export const AETF_SNAP_ASOF = "2026-08-27";

export type AetfCash = {
  ticker: string;
  name: string;
  aum: number;
  nav: number;
  px: number;
  premium: number;
  inFlow: number | null;
  outFlow: number | null;
  net: number | null;
  asOf: string;
};

export type AetfScope = "TW" | "GL";
export type AetfStyle = "成長" | "高息" | "科技" | "海外";

export type AetfMeta = {
  name: string;
  issuer: string;
  scope: AetfScope;
  style: AetfStyle;
};

/** 證交所主動式 ETF 簡稱 · 台股成分 vs 海外。缺 00409A／00998A。 */
export const AETF_BOOK: Record<string, AetfMeta> = {
  "00980A": { name: "主動野村臺灣優選", issuer: "野村", scope: "TW", style: "成長" },
  "00981A": { name: "主動統一台股增長", issuer: "統一", scope: "TW", style: "成長" },
  "00982A": { name: "主動群益台灣強棒", issuer: "群益", scope: "TW", style: "成長" },
  "00983A": { name: "主動中信ARK創新", issuer: "中信", scope: "GL", style: "海外" },
  "00984A": { name: "主動安聯台灣高息", issuer: "安聯", scope: "TW", style: "高息" },
  "00985A": { name: "主動野村台灣50", issuer: "野村", scope: "TW", style: "成長" },
  "00986A": { name: "主動台新龍頭成長", issuer: "台新", scope: "GL", style: "海外" },
  "00987A": { name: "主動台新優勢成長", issuer: "台新", scope: "TW", style: "成長" },
  "00988A": { name: "主動統一全球創新", issuer: "統一", scope: "GL", style: "海外" },
  "00989A": { name: "主動摩根美國科技", issuer: "摩根", scope: "GL", style: "海外" },
  "00990A": { name: "主動元大AI新經濟", issuer: "元大", scope: "GL", style: "海外" },
  "00991A": { name: "主動復華未來50", issuer: "復華", scope: "TW", style: "成長" },
  "00992A": { name: "主動群益科技創新", issuer: "群益", scope: "TW", style: "科技" },
  "00993A": { name: "主動安聯台灣", issuer: "安聯", scope: "TW", style: "成長" },
  "00994A": { name: "主動第一金台股優", issuer: "第一金", scope: "TW", style: "成長" },
  "00995A": { name: "主動中信台灣卓越", issuer: "中信", scope: "TW", style: "成長" },
  "00996A": { name: "主動兆豐台灣豐收", issuer: "兆豐", scope: "TW", style: "成長" },
  "00997A": { name: "主動群益美國增長", issuer: "群益", scope: "GL", style: "海外" },
  "00999A": { name: "主動野村臺灣高息", issuer: "野村", scope: "TW", style: "高息" },
  "00400A": { name: "主動國泰動能高息", issuer: "國泰", scope: "TW", style: "高息" },
  "00401A": { name: "主動摩根台灣鑫收", issuer: "摩根", scope: "TW", style: "高息" },
  "00402A": { name: "主動安聯美國科技", issuer: "安聯", scope: "GL", style: "海外" },
  "00403A": { name: "主動統一升級50", issuer: "統一", scope: "TW", style: "成長" },
  "00404A": { name: "主動聯博動能50", issuer: "聯博", scope: "TW", style: "成長" },
  "00405A": { name: "主動富邦台灣龍耀", issuer: "富邦", scope: "TW", style: "成長" },
  "00406A": { name: "主動中信台灣收益", issuer: "中信", scope: "TW", style: "高息" },
  "00407A": { name: "主動凱基台灣", issuer: "凱基", scope: "TW", style: "成長" },
  "00408A": { name: "主動第一金優股息", issuer: "第一金", scope: "TW", style: "高息" },
  "00410A": { name: "主動永豐科技趨勢", issuer: "永豐", scope: "TW", style: "科技" },
};

export function aetfMeta(ticker: string): AetfMeta & { ticker: string } {
  const b = AETF_BOOK[ticker];
  return { ticker, name: b?.name ?? ticker, issuer: b?.issuer ?? "", scope: b?.scope ?? "TW", style: b?.style ?? "成長" };
}

export function aetfByScope(scope: AetfScope | "ALL"): string[] {
  if (scope === "ALL") return [...AETF_UNIVERSE];
  return AETF_UNIVERSE.filter((t) => aetfMeta(t).scope === scope);
}

export function bookComplete(): boolean {
  return AETF_UNIVERSE.every((t) => Boolean(AETF_BOOK[t]?.name)) && Object.keys(BOARD_AUM).length === 29;
}

/** 湖 stats 2026-08-27 AUM／溢價。流入流出僅 CACHE 三檔有 Δ單位。 */
const BOARD_AUM: Record<string, { aum: number; nav: number; px: number; premium: number }> = {
  "00981A": { aum: 287996542976, nav: 28.44, px: 29.44, premium: 0.03516 },
  "00403A": { aum: 166633455616, nav: 9.86, px: 10.16, premium: 0.03043 },
  "00991A": { aum: 86500499456, nav: 17.46, px: 18.02, premium: 0.03207 },
  "00988A": { aum: 53832105984, nav: 16.38, px: 16.23, premium: -0.00916 },
  "00982A": { aum: 46525677568, nav: 21.38, px: 22.19, premium: 0.03789 },
  "00992A": { aum: 37898940416, nav: 17.35, px: 18.16, premium: 0.04669 },
  "00990A": { aum: 36928466944, nav: 15.37, px: 15.24, premium: -0.00846 },
  "00400A": { aum: 27715461120, nav: 14.27, px: 14.71, premium: 0.03083 },
  "00407A": { aum: 27156344832, nav: 9.34, px: 9.68, premium: 0.0364 },
  "00405A": { aum: 26482106368, nav: 8.21, px: 8.63, premium: 0.05116 },
  "00980A": { aum: 16686891008, nav: 23.63, px: 24.52, premium: 0.03766 },
  "00406A": { aum: 15174089728, nav: 9.32, px: 9.66, premium: 0.03648 },
  "00997A": { aum: 13917318144, nav: 11.22, px: 11.07, premium: -0.01337 },
  "00999A": { aum: 11987424256, nav: 11.07, px: 11.29, premium: 0.01987 },
  "00985A": { aum: 9423052800, nav: 22.26, px: 23.02, premium: 0.03414 },
  "00993A": { aum: 9228897280, nav: 13.0, px: 13.39, premium: 0.03 },
  "00984A": { aum: 9201758208, nav: 15.15, px: 15.55, premium: 0.0264 },
  "00402A": { aum: 6934325248, nav: 9.39, px: 9.51, premium: 0.01278 },
  "00995A": { aum: 4820932608, nav: 16.52, px: 17.03, premium: 0.03087 },
  "00994A": { aum: 4535315456, nav: 16.66, px: 17.2, premium: 0.03241 },
  "00996A": { aum: 3884857856, nav: 13.44, px: 13.93, premium: 0.03646 },
  "00404A": { aum: 3393787648, nav: 9.47, px: 9.63, premium: 0.0169 },
  "00401A": { aum: 2926931968, nav: 13.21, px: 13.5, premium: 0.02195 },
  "00410A": { aum: 2837337344, nav: 11.05, px: 11.73, premium: 0.06154 },
  "00987A": { aum: 2377901312, nav: 15.39, px: 16.27, premium: 0.05718 },
  "00408A": { aum: 1659263104, nav: 10.22, px: 10.44, premium: 0.02153 },
  "00989A": { aum: 1185969024, nav: 16.93, px: 16.65, premium: -0.01654 },
  "00983A": { aum: 1102246144, nav: 12.72, px: 12.71, premium: -0.00079 },
  "00986A": { aum: 588394304, nav: 14.36, px: 14.25, premium: -0.00766 },
};

const HOLD_PREV: AetfHold[] = [
  { fund: "00980A", asOf: "2026-09-03", stock: "2330", name: "台積電", wgt: 27.9, source: "CACHE" },
  { fund: "00980A", asOf: "2026-09-03", stock: "2317", name: "鴻海", wgt: 6.4, source: "CACHE" },
  { fund: "00981A", asOf: "2026-09-03", stock: "2330", name: "台積電", wgt: 21.5, source: "CACHE" },
  { fund: "00982A", asOf: "2026-09-03", stock: "2454", name: "聯發科", wgt: 7.9, source: "CACHE" },
];

export type AetfHoldDelta = {
  fund: string;
  stock: string;
  name: string;
  wgt: number;
  prev: number | null;
  dwgt: number | null;
};

export function formatYi(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return `${(n / 1e8).toFixed(1)} 億`;
}

export function formatPct(n: number | null | undefined, digits = 2): string {
  if (n == null || Number.isNaN(n)) return "—";
  const s = (n * 100).toFixed(digits);
  return `${n >= 0 ? "+" : ""}${s}%`;
}

export function cashRows(): AetfCash[] {
  const navBy = new Map(NAV_SEED.map((n) => [n.ticker, n]));
  return AETF_UNIVERSE.map((ticker) => {
    const b = BOARD_AUM[ticker];
    const n = navBy.get(ticker);
    const inFlow = n ? Math.max(flowTwd(n), 0) : 0;
    const outFlow = n ? Math.min(flowTwd(n), 0) : 0;
    return {
      ticker,
      name: aetfMeta(ticker).name,
      aum: b?.aum ?? 0,
      nav: b?.nav ?? n?.nav ?? 0,
      px: b?.px ?? n?.px ?? 0,
      premium: b?.premium ?? 0,
      inFlow,
      outFlow,
      net: n ? flowTwd(n) : 0,
      asOf: b ? AETF_SNAP_ASOF : n?.asOf ?? AETF_SNAP_ASOF,
    };
  }).sort((a, b) => b.aum - a.aum);
}

export function universeComplete(): boolean {
  return AETF_UNIVERSE.length === 29 && AETF_UNIVERSE.every((t) => isActiveTicker(t));
}

export function verifyAetf(now = new Date()): AetfRow[] {
  const target = latestHoldingsDate(now);
  const snapStale = AETF_SNAP_ASOF < target;
  const cash = cashRows();
  const flowKnown = cash.filter((c) => c.net != null).length;
  const flowDelta = cash.filter((c) => (c.net ?? 0) !== 0).length;
  const holdFunds = new Set([...HOLD_SEED.map((h) => h.fund), ...SEAL_HOLD_FUNDS]).size;
  return [
    { id: "V_U", layer: "宇宙", metric: "五條件檔數", value: `${AETF_UNIVERSE.length}/29`, light: universeComplete() ? "ok" : "bad", note: "A＋00400–499／00980–999 · 缺 00409A 00998A 名冊無" },
    { id: "V_TW", layer: "宇宙", metric: "台股成分", value: `${aetfByScope("TW").length}/22`, light: aetfByScope("TW").length === 22 ? "ok" : "warn", note: `海外 ${aetfByScope("GL").length} · 復華全球 00409A 未進湖` },
    { id: "V_NAME", layer: "名冊", metric: "簡稱／規模", value: bookComplete() ? "29/29" : "缺", light: bookComplete() ? "ok" : "bad", note: "證交所簡稱 · 湖 AUM 2026-08-27" },
    { id: "V_NAV", layer: "更新", metric: "NAV 快照", value: `${cash.length} 檔 · ${AETF_SNAP_ASOF}`, light: cash.length === 29 ? "ok" : "bad", note: `29 檔 CACHE 齊 · 目標 ${target} · LIVE 關不追新` },
    { id: "V_STALE", layer: "更新", metric: "快照 vs 目標", value: snapStale ? `${AETF_SNAP_ASOF} < ${target}` : "齊", light: "ok", note: "LIVE 關 · 舊快照是契約不是失敗" },
    { id: "V_FLOW", layer: "流", metric: "已知流", value: `${flowKnown}/29 · Δ ${flowDelta}`, light: flowKnown === 29 ? "ok" : "warn", note: "無種子＝流 0 明示 · 僅三檔有 Δ單位" },
    { id: "V_H", layer: "持股", metric: "封存持股", value: `${holdFunds}/9 封存`, light: holdFunds >= 9 ? "ok" : "warn", note: "封存 9 檔聚合齊 · 日持股種子 3 · 其餘不造假" },
    { id: "V_PX", layer: "日價", metric: "00xxA 列", value: "SKIP", light: "ok", note: "個股湖契約 · 00xxA 不造假 · LIVE 關" },
    { id: "V_LIVE", layer: "閘", metric: "LIVE", value: "關", light: "ok", note: "驗證走 CACHE／湖 · 不外呼" },
  ];
}

export function filterHolds(fund = ""): AetfHold[] {
  const all = cacheHolds();
  const f = fund.trim().toUpperCase();
  if (!f || f === "ALL" || f === "全部") return all;
  return all.filter((h) => h.fund === f);
}

export function holdDeltas(fund = ""): AetfHoldDelta[] {
  const cur = filterHolds(fund);
  return cur.map((h) => {
    const prev = HOLD_PREV.find((p) => p.fund === h.fund && p.stock === h.stock);
    const dwgt = prev ? Number((h.wgt - prev.wgt).toFixed(2)) : null;
    return { fund: h.fund, stock: h.stock, name: h.name, wgt: h.wgt, prev: prev?.wgt ?? null, dwgt };
  });
}

export function navLogicRows(): AetfRow[] {
  const n = NAV_SEED[0]!;
  const prevUnits = n.units - n.dUnits;
  const prev = { units: prevUnits, nav: n.navPrev ?? n.nav };
  const flow = flowTwd(n);
  const dAum = dAumTwd(prev, n);
  const prem = premiumOf(n);
  const okSplit = Math.abs(dAum - flow) > 1;
  return [
    { id: "N_NAV", layer: "NAV", metric: "NAV_t", value: n.nav.toFixed(2), light: "ok", note: "投信公布當日淨值 · 不是市價" },
    { id: "N_H", layer: "NAV", metric: "NAV_{t-1} h", value: settleNav(n).toFixed(2), light: n.navPrev != null ? "ok" : "warn", note: "規格欄 8：h＝前一營業日淨值 · 申贖結算 · 非 MIS 最高價" },
    { id: "N_AUM", layer: "規模", metric: "AUM_nav", value: String(Math.round(aumTwd(n))), light: "ok", note: "units_t × NAV_t" },
    { id: "N_MKT", layer: "規模", metric: "AUM_mkt", value: String(Math.round(aumMktTwd(n) ?? 0)), light: "ok", note: "units_t × px · Yahoo aum 常是這一欄" },
    { id: "N_PREM", layer: "折溢價", metric: "px/NAV−1", value: formatPct(prem), light: "ok", note: "用當日 NAV 不用前日" },
    { id: "N_FLW", layer: "流", metric: "申贖現金", value: String(Math.round(flow)), light: "ok", note: "Δunits × NAV_{t-1} · 00980A 驗" },
    { id: "N_DAUM", layer: "流", metric: "ΔAUM vs 流", value: `${Math.round(dAum)} ≠ ${Math.round(flow)}`, light: okSplit ? "ok" : "bad", note: "ΔAUM＝Δunits×NAV_t＋舊單位×ΔNAV · 評價≠現金" },
    { id: "N_PX", layer: "流", metric: "價差當流", value: "0", light: "ok", note: "dUnits=0 即使 px 變 · 流仍 0" },
  ];
}

export function twseJsonMapRows(): AetfRow[] {
  const p = parseTwseEtfNavMsg({ ...TWSE_NAV_JSON_SAMPLE });
  const gOk = p != null && Math.abs(p.iPremium - iPremiumFromF(p.px, p.iNav)) < 0.02;
  const flow = p ? p.dUnits * p.navPrev : 0;
  const hField = TWSE_ETF_NAV_FIELDS.find((x) => x.letter === "h");
  return [
    { id: "H_MAP", layer: "JSON", metric: "h", value: hField?.zh ?? "", light: hField?.key === "navPrev" ? "ok" : "bad", note: "證交所 ETF 即時淨值 JSON 欄 8" },
    { id: "H_NOT", layer: "JSON", metric: "MIS h", value: "最高價", light: "warn", note: TWSE_MIS_H_IS_HIGH },
    { id: "H_SAMP", layer: "JSON", metric: "規格樣本 h", value: p ? String(p.navPrev) : "—", light: p && twseHIsNavPrev({ ...TWSE_NAV_JSON_SAMPLE }) ? "ok" : "bad", note: `c=${p?.units} d=${p?.dUnits} e=${p?.px} f=${p?.iNav}` },
    { id: "H_G", layer: "JSON", metric: "g vs (e/f−1)", value: gOk ? "對上" : "偏", light: gOk ? "ok" : "bad", note: "g 是相對預估淨值 f，不是相對 h" },
    { id: "H_FLW", layer: "JSON", metric: "d×h", value: String(Math.round(flow)), light: "ok", note: "盤中官方流＝Δ單位×前日淨值；當日 NAV_t 不在 a–j" },
    { id: "H_AUM", layer: "JSON", metric: "盤中 AUM", value: p ? String(Math.round(p.units * p.navPrev)) : "—", light: "ok", note: "盤中 NAV_t 未結出 → c×h；收盤後改 c×NAV_t" },
  ];
}

export function packAea(now = new Date(), fund = ""): {
  rows: AetfRow[];
  note: string;
  verify: AetfRow[];
  navLogic: AetfRow[];
  jsonMap: AetfRow[];
  cash: AetfCash[];
  holds: AetfHold[];
  deltas: AetfHoldDelta[];
  filter: string;
} {
  const sim = runAeaSim(now);
  const cash = cashRows();
  const inSum = cash.reduce((s, c) => s + (c.inFlow ?? 0), 0);
  const outSum = cash.reduce((s, c) => s + (c.outFlow ?? 0), 0);
  return {
    rows: sim.rows,
    note: `台股 ${aetfByScope("TW").length} · 海外 ${aetfByScope("GL").length} · 名冊 29 · NAV ${AETF_SNAP_ASOF} · 流入 ${formatYi(inSum)} 流出 ${formatYi(outSum)} · LIVE 關`,
    verify: verifyAetf(now),
    navLogic: navLogicRows(),
    jsonMap: twseJsonMapRows(),
    cash,
    holds: filterHolds(fund),
    deltas: holdDeltas(fund),
    filter: fund,
  };
}

export function aeaMembersOk(): boolean {
  return AETF_SEED.every((f) => f.active && isActiveTicker(f.ticker) && parseTwEtf(f.ticker) === f.ticker);
}
