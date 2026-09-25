/** VDF_ENG075 TWMopsMonthlyRevenue · MOPS 月檔（sii/otc），非 ticker 迴圈。LIVE 預設關。 */
import type { Light } from "./types.ts";
import { TW_LEADERS, TW_UNIVERSE, TW_UNIVERSE_COUNTS } from "./vdf-mother.ts";

export const REV_LIVE_ENABLED = false;
export const REV_START_YM = "2023-01";
export const MOPS_ORIGIN = "https://mops.twse.com.tw";

export type RevMarket = "sii" | "otc";

export type RevFile = {
  year: number;
  month: number;
  market: RevMarket;
  url: string;
};

export type RevRow = {
  ticker: string;
  name: string;
  market: "TWSE" | "TPEX";
  group: string;
  year: number;
  month: number;
  rev: number;
  yoy: number | null;
  mom: number | null;
  streak: number;
  light: Light;
  source: "CACHE" | "MOPS";
};

export type RevGroup = {
  group: string;
  n: number;
  yoyMed: number | null;
  light: Light;
};

/** 上市櫃約每月 10 日前公告上月。9/5 → 最新完整月為 7 月。 */
export function latestCompleteMonth(now = new Date()): { year: number; month: number } {
  const y = now.getUTCFullYear();
  const m = now.getUTCMonth() + 1;
  const d = now.getUTCDate();
  let yy = y;
  let mm = m - (d >= 11 ? 1 : 2);
  if (mm <= 0) {
    mm += 12;
    yy -= 1;
  }
  return { year: yy, month: mm };
}

export function ymKey(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, "0")}`;
}

export function parseYm(ym: string): { year: number; month: number } {
  const [y, m] = ym.split("-").map(Number);
  return { year: y, month: m };
}

export function monthRange(startYm: string, end: { year: number; month: number }): Array<{ year: number; month: number }> {
  const s = parseYm(startYm);
  const out: Array<{ year: number; month: number }> = [];
  let y = s.year;
  let m = s.month;
  while (y < end.year || (y === end.year && m <= end.month)) {
    out.push({ year: y, month: m });
    m += 1;
    if (m > 12) {
      m = 1;
      y += 1;
    }
  }
  return out;
}

/** 官方月彙總 HTML。一檔＝該月該市場全部公告公司。 */
export function mopsMonthUrl(year: number, month: number, market: RevMarket): string {
  return `${MOPS_ORIGIN}/nas/t21/${market}/t21sc03_${year}_${month}_0.html`;
}

export function planMonthFiles(startYm = REV_START_YM, now = new Date()): RevFile[] {
  const end = latestCompleteMonth(now);
  const months = monthRange(startYm, end);
  const files: RevFile[] = [];
  for (const p of months) {
    for (const market of ["sii", "otc"] as RevMarket[]) {
      files.push({ year: p.year, month: p.month, market, url: mopsMonthUrl(p.year, p.month, market) });
    }
  }
  return files;
}

export function canFetchRev(input: { confirmNet: boolean }): { ok: true } | { ok: false; mode: "CACHE"; reason: string } {
  if (!REV_LIVE_ENABLED) {
    return { ok: false, mode: "CACHE", reason: "月營收 LIVE 未啟用 · 月檔契約已留 · CACHE 分析可跑" };
  }
  if (!input.confirmNet) return { ok: false, mode: "CACHE", reason: "NET 閘未確認 · 月營收零外呼" };
  return { ok: true };
}

function fixtureRev(ticker: string, year: number, month: number): number {
  const n = Number(ticker) || 1;
  const wave = 1 + ((month - 6) / 100) * 4;
  const base = 20 + (n % 900) + ((year - 2024) * 8);
  return Math.round(base * wave * 10) / 10;
}

function gradeYoy(yoy: number | null): Light {
  if (yoy == null) return "warn";
  if (yoy >= 0) return "ok";
  if (yoy >= -0.1) return "warn";
  return "bad";
}

export function cacheRevRows(now = new Date()): RevRow[] {
  const end = latestCompleteMonth(now);
  const months = monthRange(REV_START_YM, end);
  const raw: Array<Omit<RevRow, "yoy" | "mom" | "streak" | "light">> = [];
  for (const m of TW_LEADERS) {
    for (const p of months) {
      raw.push({
        ticker: m.ticker,
        name: m.name,
        market: m.market,
        group: m.group,
        year: p.year,
        month: p.month,
        rev: fixtureRev(m.ticker, p.year, p.month),
        source: "CACHE",
      });
    }
  }
  const idx = new Map<string, number>();
  for (const r of raw) idx.set(`${r.ticker}:${r.year}-${r.month}`, r.rev);

  return raw.map((r) => {
    const py = idx.get(`${r.ticker}:${r.year - 1}-${r.month}`);
    const pm = r.month === 1 ? idx.get(`${r.ticker}:${r.year - 1}-12`) : idx.get(`${r.ticker}:${r.year}-${r.month - 1}`);
    const yoy = py ? (r.rev - py) / py : null;
    const mom = pm ? (r.rev - pm) / pm : null;
    let streak = 0;
    if (yoy != null && yoy >= 0) {
      streak = 1;
      for (let back = 1; back < 12; back++) {
        let yy = r.year;
        let mm = r.month - back;
        while (mm <= 0) {
          mm += 12;
          yy -= 1;
        }
        const cur = idx.get(`${r.ticker}:${yy}-${mm}`);
        const prev = idx.get(`${r.ticker}:${yy - 1}-${mm}`);
        if (cur == null || prev == null || (cur - prev) / prev < 0) break;
        streak += 1;
      }
    }
    return { ...r, yoy, mom, streak, light: gradeYoy(yoy) };
  });
}

export function latestSnapshot(rows: RevRow[], now = new Date()): RevRow[] {
  const { year, month } = latestCompleteMonth(now);
  return rows.filter((r) => r.year === year && r.month === month);
}

export function groupAnalysis(rows: RevRow[], now = new Date()): RevGroup[] {
  const snap = latestSnapshot(rows, now);
  const by = new Map<string, number[]>();
  for (const r of snap) {
    if (r.yoy == null) continue;
    const a = by.get(r.group) ?? [];
    a.push(r.yoy);
    by.set(r.group, a);
  }
  return [...by.entries()]
    .map(([group, ys]) => {
      const sorted = [...ys].sort((a, b) => a - b);
      const yoyMed = sorted[Math.floor(sorted.length / 2)] ?? null;
      return { group, n: ys.length, yoyMed, light: gradeYoy(yoyMed) };
    })
    .sort((a, b) => a.group.localeCompare(b.group, "zh-Hant"));
}

export function revContract(now = new Date()): {
  files: number;
  months: number;
  latest: string;
  focus: number;
  leaders: number;
  listedNote: string;
} {
  const files = planMonthFiles(REV_START_YM, now);
  const months = files.length / 2;
  const end = latestCompleteMonth(now);
  return {
    files: files.length,
    months,
    latest: ymKey(end.year, end.month),
    focus: TW_UNIVERSE_COUNTS.members,
    leaders: TW_LEADERS.length,
    listedNote: `全部上市櫃＝每月 sii+otc 兩檔（${files.length} 檔自 ${REV_START_YM}）· 非 ${TW_UNIVERSE.length}×月 次請求 · 焦點宇宙 ${TW_UNIVERSE_COUNTS.members} 僅分析層`,
  };
}
