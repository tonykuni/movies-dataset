import type { Light } from "./types.ts";

/**
 * 母倉(tonykuni/movies-dataset · PR #30)批407–413 的現況鏡面。
 * 唯讀資料模組:不跑、不抓、不連線——數字全部來自母倉實跑與工作站實錄,
 * 在這裡只是被顯示。狀態一律誠實三態,沒跑成的就寫沒跑成。
 */
export type MotherStatusRow = {
  id: string;
  batch: string;
  area: "VDF" | "VRN" | "SSOT" | "NET" | "GOV";
  title: string;
  light: Light;
  metric: string;
  note: string;
};

export const MOTHER_STATUS_ROWS: MotherStatusRow[] = [
  {
    id: "ETF_LANE",
    batch: "批409",
    area: "VDF",
    title: "主動 ETF 持股 · 群益 PCF 車道驗真",
    light: "ok",
    metric: "26/26 檢 · 40 列真資料",
    note: "POST /CFWeb/api/etf/buyback {fundId,date};date 給過去日 pcf.date1 隨之改=真 DATED。00992A×2026-09-03 → 40 列",
  },
  {
    id: "ETF_COVER",
    batch: "批409",
    area: "VDF",
    title: "主動 ETF 覆蓋 · 誠實話",
    light: "warn",
    metric: "3 / 23 檔有源",
    note: "只通群益 00982A/00992A/00997A;其餘 13 家投信仍 PENDING_SOURCE。查法已定型可逐家照做,不臆造端點",
  },
  {
    id: "BACKFILL_RETRY",
    batch: "批411",
    area: "VDF",
    title: "回補重試律 · NO_SOURCE 不是終局",
    light: "ok",
    metric: "工作站 revived 23 · filled 1",
    note: "先前 tried 0 之真因=coverage 保留舊日格態而 backfill 只走 MISSING;車道驗真後日格復活重試",
  },
  {
    id: "NET_3LANE",
    batch: "批407",
    area: "NET",
    title: "三道升級取用 http → headers → scrape",
    light: "ok",
    metric: "22/22 檢",
    note: "headers 道用既有 curl_json/http_bytes 傳瀏覽器標頭,多數 UA 型 403 免瀏覽器即通",
  },
  {
    id: "GATE_NO_OVERWRITE",
    batch: "批408",
    area: "GOV",
    title: "同意閘不覆蓋律",
    light: "ok",
    metric: "6 令改為只在未設時補",
    note: "六個短令原本每呼必覆寫兩閘,操作員自設的正確 token 會被蓋掉=爬蟲道永遠不可達。永不代設同意閘",
  },
  {
    id: "VRN_FIXTURE",
    batch: "批410",
    area: "VRN",
    title: "自測污染修 · 收尾閘不再看到假報告",
    light: "ok",
    metric: "15/15 + 10/10 檢",
    note: "ENG072 自測曾把 fx_* fixture 寫進正式產出夾並被當真報告收進正本庫;工作站實查=從未被污染",
  },
  {
    id: "SSOT_NORM",
    batch: "批412",
    area: "SSOT",
    title: "券商／評等正典化",
    light: "ok",
    metric: "舊鍵覆蓋 15/16",
    note: "Buy/Outperform/Overweight/優於大盤 → BUY code2;NR → NOT_RATED code0。GF 是依裁決拒絕不是漏掉",
  },
  {
    id: "SSOT_ANALYST",
    batch: "批412",
    area: "VRN",
    title: "報告分析師姓名擷取(新能力)",
    light: "ok",
    metric: "落表 vrn_report_analyst",
    note: "email／電話錨點 → 鄰近行姓名 → local part 相似度 → 網域反查機構;matched 與 guess 分欄記來源",
  },
  {
    id: "SSOT_OVERLAY",
    batch: "批413",
    area: "SSOT",
    title: "操作員裁決疊加層(正典唯讀)",
    light: "ok",
    metric: "拒絕 20 · 別名 +82 · 機構 +5",
    note: "去摩通／陸券刪除／CLST·CLSA·里昂都可／增持=加碼=BUY;來源=Grok 倉昨天過關那份冊子",
  },
  {
    id: "VRN_INPUT",
    batch: "批410",
    area: "VRN",
    title: "VRN 走到 GREEN 還缺什麼",
    light: "pending",
    metric: "尚無真報告",
    note: "五段鏈可跑,卡的是沒有輸入。倉內 synthetic PDF 不是台股投資報告(抽不出代號與目標價),不能當示範件",
  },
];

/** 總燈:有 bad 即 bad;否則有 warn/pending 即 warn;全 ok 才 ok。不取巧、不四捨五入。 */
export function motherStatusLight(rows: MotherStatusRow[] = MOTHER_STATUS_ROWS): Light {
  if (rows.some((r) => r.light === "bad")) return "bad";
  if (rows.some((r) => r.light === "warn" || r.light === "pending")) return "warn";
  return "ok";
}

export function motherStatusSummary(rows: MotherStatusRow[] = MOTHER_STATUS_ROWS): {
  total: number;
  ok: number;
  open: number;
  areas: string[];
} {
  const ok = rows.filter((r) => r.light === "ok").length;
  return {
    total: rows.length,
    ok,
    open: rows.length - ok,
    areas: [...new Set(rows.map((r) => r.area))],
  };
}

/** 尚未了結的列(warn/pending/bad)——面板要先讓人看見還沒好的。 */
export function motherStatusOpen(rows: MotherStatusRow[] = MOTHER_STATUS_ROWS): MotherStatusRow[] {
  return rows.filter((r) => r.light !== "ok");
}
