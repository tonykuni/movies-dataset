import "@tanstack/react-start/server-only";
import { buildDesk } from "@/lib/desk/load";
import { deductedTurnover } from "@/lib/desk/parse";
import { computeAll, marketSeries, type CalcBar, type Reading } from "./engine";
import { LIBRARIES, TOPICS, VQG } from "./registry";
import { SIGNALS } from "./signals";
import { resolveLibraries } from "./libs.server";
import { runTopics } from "./topics";
import { PARQUET, readBars, readIndicators, readSignals, readTests, saveBars, saveIndicators, saveReadings, saveSignals, saveTests, themeCounts } from "./store";
import { runTests } from "./test-engine";
import type { VqgPayload } from "./types";

const UA = "Mozilla/5.0 (compatible; MorningPulse/1.0)";
let flight: Promise<VqgPayload> | null = null;

function taipeiDate(sec: number): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Taipei",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(sec * 1000));
}

async function fetchAdj(symbol: string, range: string): Promise<Array<{ date: string; adj: number; high: number | null; low: number | null }>> {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=${range}&includeAdjustedClose=true`;
  const res = await fetch(url, {
    headers: { "user-agent": UA, accept: "application/json" },
    signal: AbortSignal.timeout(12000),
  });
  if (!res.ok) throw new Error(`${res.status} ${symbol}`);
  const json = (await res.json()) as {
    chart?: {
      result?: Array<{
        timestamp?: number[];
        indicators?: {
          quote?: Array<{ close?: Array<number | null>; high?: Array<number | null>; low?: Array<number | null> }>;
          adjclose?: Array<{ adjclose?: Array<number | null> }>;
        };
      }>;
    };
  };
  const result = json.chart?.result?.[0];
  const ts = result?.timestamp ?? [];
  const adj = result?.indicators?.adjclose?.[0]?.adjclose ?? [];
  const quote = result?.indicators?.quote?.[0];
  const close = quote?.close ?? [];
  const high = quote?.high ?? [];
  const low = quote?.low ?? [];
  const rows: Array<{ date: string; adj: number; high: number | null; low: number | null }> = [];
  for (let i = 0; i < ts.length; i++) {
    const stamp = ts[i];
    const price = adj[i] ?? close[i];
    if (stamp == null || price == null || price <= 0) continue;
    const basis = close[i];
    const factor = basis != null && basis > 0 ? price / basis : 1;
    rows.push({
      date: taipeiDate(stamp),
      adj: price,
      high: high[i] == null ? null : high[i]! * factor,
      low: low[i] == null ? null : low[i]! * factor,
    });
  }
  return rows;
}

function themeSummary(theme: string, readings: Reading[]): string {
  const picked = new Map<string, Reading>();
  for (const row of readings) {
    if (row.theme !== theme) continue;
    const current = picked.get(row.id);
    const prefer = row.window === 20 || row.window === 14 || row.label.includes("柱");
    if (!current || prefer) picked.set(row.id, row);
  }
  const lines = [...picked.values()].slice(0, 3).map((row) => row.signal);
  return lines.join("") || "這個主題目前沒有算完的數字。";
}

export function buildVqg(): Promise<VqgPayload> {
  if (!flight) {
    flight = buildVqgOnce().finally(() => {
      flight = null;
    });
  }
  return flight;
}

async function buildVqgOnce(): Promise<VqgPayload> {
  const [prices, desk] = await Promise.all([fetchAdj("^TWII", "2y"), buildDesk()]);
  const byDate = new Map(desk.rows.map((row) => [row.date, row]));
  const bars: CalcBar[] = prices.map((price) => {
    const row = byDate.get(price.date);
    return {
      date: price.date,
      adj: price.adj,
      high: price.high,
      low: price.low,
      deducted: row ? deductedTurnover(row) : null,
      turnover: row?.turnover ?? null,
      daytrade: row?.daytradeAmt ?? null,
      activeEtf: row?.activeEtf ?? null,
      foreign: row?.foreign ?? null,
      trust: row?.trust ?? null,
      dealer: row?.dealer ?? null,
    };
  });
  for (const row of desk.rows) {
    if (bars.some((bar) => bar.date === row.date) || !(row.adj > 0)) continue;
    const factor = row.close != null && row.close > 0 ? row.adj / row.close : 1;
    bars.push({
      date: row.date,
      adj: row.adj,
      high: row.high == null ? null : row.high * factor,
      low: row.low == null ? null : row.low * factor,
      deducted: deductedTurnover(row),
      turnover: row.turnover,
      daytrade: row.daytradeAmt,
      activeEtf: row.activeEtf,
      foreign: row.foreign,
      trust: row.trust,
      dealer: row.dealer,
    });
  }
  bars.sort((a, b) => a.date.localeCompare(b.date));

  const versions = await saveIndicators(VQG);
  await saveBars(bars);
  await saveSignals(SIGNALS);
  const registry = await readIndicators();
  const stored = await readBars();
  const signalBook = await readSignals();
  const readings = computeAll(registry, stored);
  const asOf = stored.at(-1)?.date ?? "";
  await saveReadings(readings, asOf);
  await saveTests(runTests(signalBook, marketSeries(stored)), asOf);
  const counts = await themeCounts();
  const tests = await readTests();

  return {
    asOf,
    barCount: stored.length,
    flowDays: stored.filter((bar) => bar.deducted != null).length,
    policy: [
      "三個引擎分開。這是演算法候選，不是 QuantGuard 本體，也不用同名套件代替。",
      "窗口必須連續。缺值不刪掉再拿較早的資料補滿。布林 ddof=0。MACD 柱倍率是 1。RSI 漲跌都是 0 時記 50。最高等於最低時 KD 留空。",
      "測試只問到目前這一筆，跡象是否成立。回放只計看得到、看不到、樣本不足，以及噪音和鈍化的次數。",
      "不用淨利、勝率、獲利因子或盈虧比。那些是交易結果，不是跡象驗證。",
      "價格只用調整後收盤。要比就比漲跌幅，不比點數。金額先除以扣掉當沖的成交值，變成占比，才能跨日比。占比和漲跌再看自己過去的位置，才能跨群比強弱。",
      "當沖和台積電都會把成交灌大。分母拿掉它們，其餘變化才不會被蓋住。融資融券、櫃買、台積電扣當沖、指數對自己的去連動，目前留空，不估。成交股數、利率、同市場基準和台積電序列沒接上時，能量潮、乾淨資金流動比、滾動夏普、相對強度的對應解也留空。",
      "高低位置用指標自身近 120 筆的分位。這只說明目前位置，不表示之後會怎樣。",
      "QuantGuard SSOT 0.3.0 裡還沒有編號的指標邏輯，補進同一份庫、同一個計算入口。已有編號的公式、參數、天數不改。沒有成交股數或第二條價格的項目留空，不拿成交值或這條價格自己代替。",
      "指標、專題、跡象回放、本機免費函式庫各加 20 項。專題只讀已經算出的讀數，不另算價格。回放仍只計看得到、看不到、樣本不足、噪音和鈍化，不計淨利、勝率、獲利因子或盈虧比。函式庫只登記已經安裝的免費套件和版本，價格不交給套件重算。",
      "編號不變。只有公式、參數或天數改變才把版本加一。說明文字改變不加版本。舊版本留著，不覆蓋。",
    ],
    files: PARQUET,
    themes: counts.map((row) => ({ ...row, summary: themeSummary(row.theme, readings) })),
    registry,
    readings,
    counts,
    signals: signalBook,
    tests,
    versions,
    topics: runTopics(TOPICS, readings),
    libraries: resolveLibraries(LIBRARIES),
  };
}
