/** 主動式台股 ETF 應有分析層。對兩份封存＋湖，缺則 LOCAL 補，LIVE 關。 */
import { inActiveEquityRange, isActiveDomesticEquityEtf } from "./tw-ticker-all.ts";
import { AETF_SEED, isActiveName, isActiveTicker } from "./active-etf.ts";
import type { Light } from "./types.ts";

export const AETF_SEAL_DIRS = [
  String.raw`C:\新增資料夾\新增資料夾\VETF_FINAL_SEAL_20260829_013330 (2)`,
  String.raw`C:\新增資料夾\新增資料夾\VIA_ActiveETF_FINAL (1)`,
] as const;

export const AETF_ANALYSIS: { id: string; layer: string; need: string; local: string }[] = [
  { id: "U", layer: "宇宙", need: "五條件全檔（A·Active·Domestic·日持股·00400A–00499A／00980A–00999A）", local: "etf_book 濾碼" },
  { id: "M", layer: "名冊", need: "發行人／類型／追蹤指數／is_active", local: "etf_book 欄" },
  { id: "H", layer: "日持股", need: "fund,as_of,stock,wgt 每日", local: "封存 DailyHoldings · 無則黃" },
  { id: "N", layer: "NAV/AUM", need: "units×NAV", local: "etf_stats_daily" },
  { id: "F", layer: "申贖流", need: "Δunits×NAV，價差不算流", local: "etf_stats_daily" },
  { id: "P", layer: "折溢價", need: "市價 vs NAV", local: "px ⋈ NAV" },
  { id: "R", layer: "績效", need: "報酬／波動 vs 0050", local: "px 日價" },
  { id: "C", layer: "集中", need: "前十大、2330 權重、HHI", local: "日持股" },
  { id: "A", layer: "主動度", need: "Active Share vs 0050", local: "日持股" },
  { id: "K", layer: "法人", need: "成分股三大法人", local: "chip ⋈ 持股" },
];

export type AetfGapRow = {
  id: string;
  layer: string;
  need: string;
  have: string;
  light: Light;
  fill: string;
};

export function cacheUniverseIncomplete(): boolean {
  return AETF_SEED.length < 4;
}

export function bookIsActiveEquity(code: string, name?: string, fundType?: string): boolean {
  const c = String(code).toUpperCase().replace(/\.TW|\.TWO/g, "");
  if (!isActiveTicker(c) && !inActiveEquityRange(c)) return false;
  if (name && !isActiveName(name) && fundType && !/active|主動/i.test(fundType)) return false;
  return isActiveDomesticEquityEtf(c);
}

export function inspectAetfGap(opts: {
  bookActive?: number;
  holdDays?: number;
  navRows?: number;
  pxActive?: number;
  sealHold?: boolean;
  sealEngine?: boolean;
} = {}): { rows: AetfGapRow[]; note: string } {
  const book = opts.bookActive ?? 0;
  const hold = opts.holdDays ?? 0;
  const nav = opts.navRows ?? 0;
  const px = opts.pxActive ?? 0;
  const rows: AetfGapRow[] = [
    {
      id: "U",
      layer: "宇宙",
      need: AETF_ANALYSIS[0]!.need,
      have: `CACHE ${AETF_SEED.length} 檔${book ? ` · book ${book}` : " · 湖 29"}`,
      light: book >= 4 || AETF_SEED.length >= 4 ? "ok" : "warn",
      fill: "etf_book 五條件濾碼 → aetf/year=roster",
    },
    {
      id: "H",
      layer: "日持股",
      need: AETF_ANALYSIS[2]!.need,
      have: hold > 0 ? `持股日 ${hold}` : opts.sealHold ? "封存有持股檔" : "CACHE 4 列種子",
      light: hold > 0 || opts.sealHold ? "ok" : "warn",
      fill: "從 VETF_SEAL / VIA_ActiveETF_FINAL COPY，不 LIVE",
    },
    {
      id: "N",
      layer: "NAV/流/折溢價",
      need: "AUM＋申贖＋市價",
      have: `nav列 ${nav} · px主動 ${px}`,
      light: nav > 0 || px > 0 ? "ok" : "warn",
      fill: "etf_stats_daily ⋈ px",
    },
    {
      id: "R",
      layer: "績效/集中/法人",
      need: "vs 0050 · HHI · chip",
      have: px > 0 ? "有價可算報酬" : "無",
      light: px > 0 ? "warn" : "bad",
      fill: "px 算報酬；持股齊才補集中／法人",
    },
    {
      id: "S",
      layer: "封存",
      need: "兩資料夾對帳",
      have: opts.sealEngine ? "引擎包在" : "本台未探",
      light: opts.sealEngine ? "ok" : "warn",
      fill: AETF_SEAL_DIRS.join(" · "),
    },
  ];
  const warn = rows.filter((r) => r.light !== "ok").length;
  return { rows, note: warn ? `缺 ${warn} 層 · LOCAL 補 · LIVE 關` : "十層齊 · LIVE 關" };
}

export function aetfFillPriority(): string[] {
  return ["U", "M", "N", "P", "R", "H", "C", "A", "K"];
}
