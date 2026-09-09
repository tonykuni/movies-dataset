import type { Light } from "./types.ts";

/**
 * VRN 真跑實況(批419)——工作站 2026-09-08 21:55 那一跑的**唯讀鏡面**。
 * 不跑、不抓、不連線:數字全部來自 `via-console run` / `via-vrn4` / `via-closeout vrn`
 * 的實際輸出,在這裡只是被顯示與被判讀。
 *
 * 這一頁存在的理由:那一跑「成功了」——65 份真報告全走完鏈、37 份四點文摘、
 * VRN 三頁再生 GREEN。但輸出裡有兩件事會讓人讀錯:
 *   ① 三份的目標價/現價比是 0.020 / 0.019 / 0.005——目標價只有股價的 1/50 到 1/200。
 *      那不是預測,是抽錯的數;印成「潛在上漲空間 -98.0%」比不印更糟。
 *   ② 37 份**全部**拿 2026-09-07 的價去比,但其中 18 份的報告日超過 180 天前
 *      (最舊的 Daiwa-1319 是 2023-10-11,距今 1062 天)。拿三年後的價算三年前報告的
 *      「潛在上漲空間」,算出來的不是上漲空間,是事後看圖。
 * 所以這裡不只顯示數字,還把每一份標成「可信 / 非當期 / TP 疑誤 / 未算」。
 */

export const TP_SANITY_LO = 0.2;
export const TP_SANITY_HI = 5.0;
export const STALE_DAYS = 180;
/** 這一跑的價格基準日(ENG080 取 VDF 價表最新 adj close 日)。 */
export const ASOF = "2026-09-07";

export type TpState = "OK" | "TP_SUSPECT" | "NA";
export type BasisState = "CURRENT" | "STALE_BASIS" | "UNKNOWN";
export type DigestVerdict = "可信" | "非當期" | "TP 疑誤" | "未算";

export type DigestRow = {
  file: string;
  ticker: string;
  reportDate: string;   // "" = 檔名無日期
  tpAdj: number | null; // 除權息調整後目標價;null = 報告沒抽到目標價
  price: number;        // 基準日 adj close
};

/** 目標價合理性(與母倉 ENG080 v0101 tp_sanity 同律)。只 flag 不丟棄。 */
export function tpSanity(tpAdj: number | null, price: number): { state: TpState; ratio: number | null } {
  if (tpAdj === null || !price) return { state: "NA", ratio: null };
  const r = tpAdj / price;
  return { state: r >= TP_SANITY_LO && r <= TP_SANITY_HI ? "OK" : "TP_SUSPECT", ratio: r };
}

/** 報告日到基準日的天數;算不出=null(不猜)。 */
export function basisAge(reportDate: string, asof: string = ASOF): number | null {
  if (!reportDate) return null;
  const a = Date.parse(`${reportDate}T00:00:00Z`);
  const b = Date.parse(`${asof}T00:00:00Z`);
  if (Number.isNaN(a) || Number.isNaN(b)) return null;
  return Math.round((b - a) / 86400000);
}

export function basisState(days: number | null): BasisState {
  if (days === null) return "UNKNOWN";
  return days <= STALE_DAYS ? "CURRENT" : "STALE_BASIS";
}

/** 一份文摘的判讀。次序刻意:TP 疑誤壓過非當期——連數字都可疑就別談基準日。 */
export function auditDigest(r: DigestRow): {
  verdict: DigestVerdict; ratio: number | null; days: number | null; upside: number | null; why: string;
} {
  const { state, ratio } = tpSanity(r.tpAdj, r.price);
  const days = basisAge(r.reportDate);
  const upside = r.tpAdj !== null && r.price ? r.tpAdj / r.price - 1 : null;
  if (state === "NA") return { verdict: "未算", ratio, days, upside, why: "報告沒抽到目標價,或價表無 adj close" };
  if (state === "TP_SUSPECT") {
    return { verdict: "TP 疑誤", ratio, days, upside, why: `目標價/現價 ${ratio!.toFixed(3)} 落在合理帶 ${TP_SANITY_LO}–${TP_SANITY_HI} 外=疑為擷取誤判` };
  }
  if (basisState(days) === "STALE_BASIS") {
    return { verdict: "非當期", ratio, days, upside, why: `報告距基準日 ${days} 天(>${STALE_DAYS});今日比值僅供參考,不作潛在上漲空間` };
  }
  return { verdict: "可信", ratio, days, upside, why: `當期(${days} 天)且比值在合理帶內` };
}

export function digestLight(v: DigestVerdict): Light {
  return v === "可信" ? "ok" : v === "TP 疑誤" ? "bad" : v === "非當期" ? "warn" : "pending";
}

/** 這一跑 37 份文摘(照 via-vrn4 實際輸出逐列抄錄)。 */
export const RUN_DIGESTS: DigestRow[] = [
  { file: "Daiwa-6278 20260521", ticker: "6278", reportDate: "2026-05-21", tpAdj: null, price: 195.0 },
  { file: "20260519兆豐個股報告-望隼(4771)", ticker: "4771", reportDate: "2026-05-19", tpAdj: 229.47, price: 206.0 },
  { file: "GS-2383 20260519", ticker: "2383", reportDate: "2026-05-19", tpAdj: 5972.73, price: 5495.0 },
  { file: "凱基投顧_1476 儒鴻_劉昃恩_20260519", ticker: "1476", reportDate: "2026-05-19", tpAdj: 350.97, price: 306.0 },
  { file: "凱基投顧_2891 中信金_施志鴻_20260519", ticker: "2891", reportDate: "2026-05-19", tpAdj: 56.89, price: 67.4 },
  { file: "凱基投顧_3665 貿聯-KY_李承泰_20260519", ticker: "3665", reportDate: "2026-05-19", tpAdj: 2577.41, price: 2070.0 },
  { file: "凱基投顧_6147 頎邦_劉宇程_20260519", ticker: "6147", reportDate: "2026-05-19", tpAdj: 276.55, price: 191.0 },
  { file: "GS-6415 20260517", ticker: "6415", reportDate: "2026-05-17", tpAdj: 650.0, price: 418.0 },
  { file: "晶心科(6533,N,中立)-CTBC251208", ticker: "6533", reportDate: "2025-12-08", tpAdj: 300.0, price: 257.0 },
  { file: "瑞基(4171,NR_未評等)-CTBC251208", ticker: "4171", reportDate: "2025-12-08", tpAdj: null, price: 16.8 },
  { file: "GS-2317 20251205", ticker: "2317", reportDate: "2025-12-05", tpAdj: null, price: 256.0 },
  { file: "20251204兆豐個股報告-志強-KY(6768)", ticker: "6768", reportDate: "2025-12-04", tpAdj: 117.51, price: 63.8 },
  { file: "GS-1590 20251203", ticker: "1590", reportDate: "2025-12-03", tpAdj: null, price: 1370.0 },
  { file: "MS-3661 20251203", ticker: "3661", reportDate: "2025-12-03", tpAdj: 4388.0, price: 4040.0 },
  { file: "MS-1590 20251202", ticker: "1590", reportDate: "2025-12-02", tpAdj: 1106.28, price: 1370.0 },
  { file: "MS-3665 20251202", ticker: "3665", reportDate: "2025-12-02", tpAdj: 1883.5, price: 2070.0 },
  { file: "華南投顧-2606-裕民-1141202", ticker: "2606", reportDate: "2025-12-02", tpAdj: 67.08, price: 78.6 },
  { file: "華南投顧-2637-慧洋-KY-1141202", ticker: "2637", reportDate: "2025-12-02", tpAdj: 74.63, price: 99.2 },
  { file: "華南投顧-3017-奇鋐-1141202", ticker: "3017", reportDate: "2025-12-02", tpAdj: 1769.5, price: 3420.0 },
  { file: "GS-3706 20251130", ticker: "3706", reportDate: "2025-11-30", tpAdj: null, price: 92.6 },
  { file: "20251128兆豐訪談速報-神達(3706)", ticker: "3706", reportDate: "2025-11-28", tpAdj: 78.0, price: 92.6 },
  { file: "MS-2308 20251128", ticker: "2308", reportDate: "2025-11-28", tpAdj: 37.8, price: 1850.0 },
  { file: "華南投顧-6143-振曜-1141128", ticker: "6143", reportDate: "2025-11-28", tpAdj: 137.23, price: 86.5 },
  { file: "MS-6669 20251007", ticker: "6669", reportDate: "2025-10-07", tpAdj: 3401.49, price: 2490.0 },
  { file: "MS-8210 20251007", ticker: "8210", reportDate: "2025-10-07", tpAdj: 17.81, price: 937.0 },
  { file: "JP-3653 20251003", ticker: "3653", reportDate: "2025-10-03", tpAdj: 25.84, price: 5655.0 },
  { file: "Daiwa-3653 20251002", ticker: "3653", reportDate: "2025-10-02", tpAdj: null, price: 5655.0 },
  { file: "CLST-6669 20251001", ticker: "6669", reportDate: "2025-10-01", tpAdj: 4081.78, price: 2490.0 },
  { file: "【國泰證期研究部】神達(3706 TT)", ticker: "3706", reportDate: "2025-08-22", tpAdj: 118.69, price: 92.6 },
  { file: "20250819兆豐個股報告-泓德能源(6873)", ticker: "6873", reportDate: "2025-08-19", tpAdj: 200.31, price: 68.6 },
  { file: "JP-2330 20250718", ticker: "2330", reportDate: "2025-07-18", tpAdj: 1258.23, price: 2460.0 },
  { file: "Citi-3231 20250604", ticker: "3231", reportDate: "2025-06-04", tpAdj: 159.16, price: 197.0 },
  { file: "GS-1590 20231012", ticker: "1590", reportDate: "2023-10-12", tpAdj: null, price: 1370.0 },
  { file: "GS-2382 20231012", ticker: "2382", reportDate: "2023-10-12", tpAdj: null, price: 347.5 },
  { file: "Daiwa-1319 20231011", ticker: "1319", reportDate: "2023-10-11", tpAdj: 87.39, price: 81.7 },
  { file: "3014TT-20231005", ticker: "3014", reportDate: "2023-10-05", tpAdj: 157.58, price: 132.0 },
  { file: "6933_AMAX-KY_個股介紹報告", ticker: "6933", reportDate: "", tpAdj: null, price: 313.0 },
];

/** 這一跑的收尾閘與各段實況(照 via-closeout / via-famui 實際輸出)。 */
export const RUN_CLOSEOUT = {
  ranAt: "2026-09-08 21:55",
  reports: 65, done: 25, fail: 34, pending: 6,
  stages: { 收件: 5, 首頁: 1, 入庫: 21, 財報頁: 4, 四點: 34 } as Record<string, number>,
  cross: { checked: 61, of: 65, agree: 0, diverge: 6, onlyTable: 468 },
  ui: { pages: 3, fresh: 3, light: "ok" as Light },
  digest: { reports: 37, withBody: 37, k1Grounded: 28, upsideCalc: 28, exAdj: 30, qcRed: 0 },
};

export type AuditTally = { 可信: number; 非當期: number; "TP 疑誤": number; 未算: number };

export function auditTally(rows: DigestRow[] = RUN_DIGESTS): AuditTally {
  const t: AuditTally = { 可信: 0, 非當期: 0, "TP 疑誤": 0, 未算: 0 };
  for (const r of rows) t[auditDigest(r).verdict] += 1;
  return t;
}

/** 總燈:有 TP 疑誤即 bad;有非當期即 warn;全可信才 ok。 */
export function auditLight(rows: DigestRow[] = RUN_DIGESTS): Light {
  const t = auditTally(rows);
  if (t["TP 疑誤"] > 0) return "bad";
  if (t.非當期 > 0 || t.未算 > 0) return "warn";
  return t.可信 > 0 ? "ok" : "pending";
}
