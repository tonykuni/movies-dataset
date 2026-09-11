import type { Light } from "./types.ts";

/**
 * 整合輸入台 / 整合結果台的純邏輯層(批417)。
 *
 * 為什麼要有:VDF、ETF、VRN 三族的**輸入**原本散在三個分頁
 * (VDF 的起始年與金鑰在 01、ETF 的挑檔在 01 內層、VRN 的檔案拖放在 02),
 * **結果**也散在各自的分頁與四個 tab。操作員要「跑一輪看結果」得走三處。
 * 這一層把三族的「可不可以跑」與「跑完是什麼」收成同一個模型,
 * 由 run-deck 一頁呈現;**引擎一支都不新造**,跑的仍是既有 runVdf/runIntake。
 *
 * 誠實三態鐵律(與母倉同律):
 *   · 沒有輸入 = pending,絕不當成 ok
 *   · 跑出零列 = warn(「跑完了但什麼都沒有」跟「成功」是兩件事)
 *   · 總燈取最壞:bad > run > warn > pending > ok
 */

export type RunFamily = "VDF" | "ETF" | "VRN";

export type RunInput = {
  startYear: number;
  confirmNet: boolean;
  fredKey: string;
  etfPicked: string[];
  vrnFiles: number;
};

export type RunReady = {
  family: RunFamily;
  ready: boolean;
  why: string;
};

export type RunResultRow = {
  family: RunFamily;
  key: string;
  value: string;
  light: Light;
  note: string;
};

export type RunCounts = {
  fredRows: number;
  laneResults: number;
  laneLive: number;
  etfRows: number;
  etfPicked: number;
  vrnFiles: number;
  vrnBasics: number;
  vrnSummaries: number;
  vrnFinances: number;
  vrnBad: number;
};

const ORDER: Light[] = ["bad", "run", "warn", "pending", "ok"];

/** 取最壞燈;空陣列=pending(沒有東西可判就不准說 ok)。 */
export function worstLight(lights: Light[]): Light {
  if (!lights.length) return "pending";
  for (const l of ORDER) {
    if (l === "ok") continue;
    if (lights.some((x) => x === l || (l === "pending" && x === "idle"))) return l;
  }
  return "ok";
}

/**
 * 跑之前先講清楚每一族能不能跑、不能跑是差什麼。
 * VDF/ETF 一定跑得動(離線快取湖就在包內),VRN 沒檔案就是不能跑——
 * 這點不含糊:母倉那邊 VRN 卡的也正是「沒有真報告」。
 */
export function readiness(input: RunInput): RunReady[] {
  const rows: RunReady[] = [];
  rows.push({
    family: "VDF",
    ready: true,
    why: input.confirmNet
      ? input.fredKey
        ? `雙閘 AND 已足 · FRED 車道可 LIVE · 起始 ${input.startYear}`
        : `閘 1 開但 KEY 空 · 走離線列式湖 · 起始 ${input.startYear}`
      : `NET 閘未確認 · 零外呼 · 走離線列式湖 · 起始 ${input.startYear}`,
  });
  rows.push({
    family: "ETF",
    ready: true,
    why: input.etfPicked.length
      ? `已挑 ${input.etfPicked.length} 檔主動 ETF`
      : "未挑檔=跑全部主動 ETF(挑了就只跑挑的)",
  });
  rows.push({
    family: "VRN",
    ready: input.vrnFiles > 0,
    why: input.vrnFiles > 0
      ? `待驗 ${input.vrnFiles} 件`
      : "尚無報告檔——拖 PDF 進左欄或按選擇檔案;沒有輸入就不會有結果",
  });
  return rows;
}

/** 三族都能跑才算「可整合跑」;VRN 缺檔就誠實擋下,不假裝跑得動。 */
export function canRunAll(input: RunInput): boolean {
  return readiness(input).every((r) => r.ready);
}

/**
 * 把三族跑完的實際數字收成同一張結果表。
 * busy 中一律 run;沒跑過(全零且沒 busy)一律 pending;
 * 跑完但零列=warn,不當成功。
 */
export function resultRows(c: RunCounts, busy: { vdf: boolean; vrn: boolean }): RunResultRow[] {
  const rows: RunResultRow[] = [];
  const zero = (n: number, ran: boolean): Light => (ran ? (n > 0 ? "ok" : "warn") : "pending");

  const vdfRan = c.fredRows > 0 || c.laneResults > 0;
  rows.push({
    family: "VDF",
    key: "巨觀序列",
    value: `${c.fredRows} 列`,
    light: busy.vdf ? "run" : zero(c.fredRows, vdfRan),
    note: vdfRan ? "FRED/列式湖車道回列" : "尚未跑",
  });
  rows.push({
    family: "VDF",
    key: "擷取車道",
    value: `${c.laneLive}/${c.laneResults} 有料`,
    light: busy.vdf ? "run" : c.laneResults === 0 ? "pending" : c.laneLive > 0 ? "ok" : "warn",
    note: c.laneResults ? "LIVE/CACHE/LOCAL 皆算有料;SKIP/DENIED 不算" : "尚未跑",
  });

  const etfRan = c.etfRows > 0;
  rows.push({
    family: "ETF",
    key: "主動 ETF 檢核列",
    value: `${c.etfRows} 列`,
    light: busy.vdf ? "run" : zero(c.etfRows, etfRan),
    note: c.etfPicked ? `已挑 ${c.etfPicked} 檔` : "全部主動 ETF",
  });

  const vrnRan = c.vrnBasics > 0 || c.vrnSummaries > 0 || c.vrnFinances > 0;
  rows.push({
    family: "VRN",
    key: "報告基本資料",
    value: `${c.vrnBasics}/${c.vrnFiles} 件`,
    light: busy.vrn ? "run" : c.vrnFiles === 0 ? "pending" : zero(c.vrnBasics, vrnRan),
    note: c.vrnFiles ? "檔名×首頁交互驗證後入庫" : "尚無報告檔",
  });
  rows.push({
    family: "VRN",
    key: "一題四點文摘",
    value: `${c.vrnSummaries} 列`,
    light: busy.vrn ? "run" : c.vrnFiles === 0 ? "pending" : zero(c.vrnSummaries, vrnRan),
    note: c.vrnFiles ? "quote-or-abstain:抽不到就不寫" : "尚無報告檔",
  });
  rows.push({
    family: "VRN",
    key: "財報頁表格",
    value: `${c.vrnFinances} 列`,
    light: busy.vrn ? "run" : c.vrnFiles === 0 ? "pending" : zero(c.vrnFinances, vrnRan),
    note: c.vrnFiles ? "三方對照(檔名×首頁×財報頁)" : "尚無報告檔",
  });
  if (c.vrnBad > 0) {
    rows.push({
      family: "VRN",
      key: "卡住的件",
      value: `${c.vrnBad} 件`,
      light: "bad",
      note: "逐件卡點在 02 VRN 分頁列得出來——不掃到地毯下",
    });
  }
  return rows;
}

/** 某一族的燈 = 該族各列取最壞。 */
export function familyLight(rows: RunResultRow[], family: RunFamily): Light {
  return worstLight(rows.filter((r) => r.family === family).map((r) => r.light));
}

/** 總燈 = 全部列取最壞。 */
export function overallLight(rows: RunResultRow[]): Light {
  return worstLight(rows.map((r) => r.light));
}

/** 一句話結論;給頁首用。 */
export function verdictText(rows: RunResultRow[]): string {
  const l = overallLight(rows);
  const n = rows.length;
  const bad = rows.filter((r) => r.light === "bad").length;
  const warn = rows.filter((r) => r.light === "warn").length;
  const pend = rows.filter((r) => r.light === "pending").length;
  if (l === "run") return "跑動中";
  if (l === "bad") return `有 ${bad} 項卡住 · 共 ${n} 項`;
  if (l === "warn") return `跑完但 ${warn} 項零列 · 共 ${n} 項`;
  if (l === "pending") return `${pend} 項尚未跑 · 共 ${n} 項`;
  return `三族 ${n} 項全數有料`;
}
