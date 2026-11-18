import type { MarketSeries } from "./engine";
import type { SignalDef } from "./signals";

export type TestStatus = "看得到" | "看不到" | "樣本不足";

export type TestRow = {
  id: string;
  name: string;
  indicatorId: string;
  meaning: string;
  testQuestion: string;
  evidenceRule: string;
  noiseRule: string;
  saturationRule: string;
  checks: number;
  present: number;
  absent: number;
  insufficient: number;
  noiseCount: number;
  saturationCount: number;
  latestStatus: TestStatus;
  latestDetail: string;
  noiseNow: string;
  saturationNow: string;
};

type Flag = boolean | null;
type Side = "高檔" | "低檔" | null;

function pctAt(series: (number | null)[], index: number): number | null {
  const current = series[index];
  if (current == null) return null;
  const start = Math.max(0, index + 1 - 120);
  const slice: number[] = [];
  for (let i = start; i <= index; i++) {
    const value = series[i];
    if (value != null) slice.push(value);
  }
  if (slice.length < 20) return null;
  return (slice.filter((value) => value <= current).length / slice.length) * 100;
}

function stuck(series: (number | null)[], adj: number[], index: number): Side {
  if (index < 4 || adj[index - 4] === 0) return null;
  const slice: number[] = [];
  for (let i = index - 4; i <= index; i++) {
    const value = series[i];
    if (value == null) return null;
    slice.push(value);
  }
  const span = Math.max(...slice) - Math.min(...slice);
  const move = adj[index]! / adj[index - 4]! - 1;
  if (slice.every((value) => value >= 70) && span < 8 && move > 0) return "高檔";
  if (slice.every((value) => value <= 30) && span < 8 && move < 0) return "低檔";
  return null;
}

function gap(left: (number | null)[], right: (number | null)[]): (number | null)[] {
  return left.map((value, i) => (value == null || right[i] == null || right[i] === 0 ? null : value / right[i]! - 1));
}

function num(value: number | null, digits = 2): string {
  return value == null ? "—" : value.toFixed(digits);
}

type Frame = {
  flag: Flag;
  drive: (number | null)[];
  detail: string;
  sat: Side;
  skipNoise: boolean;
};

function lineFrame(price: number | null, adj: number[], line: (number | null)[], index: number, label: string): Frame {
  const value = line[index] ?? null;
  return {
    flag: price == null || value == null ? null : price > value,
    drive: gap(adj, line),
    detail: `收盤 ${num(price, 1)}，${label} ${num(value, 1)}。`,
    sat: null,
    skipNoise: false,
  };
}

function signFrame(line: (number | null)[], index: number, label: string, digits = 2): Frame {
  const value = line[index] ?? null;
  return {
    flag: value == null ? null : value > 0,
    drive: line,
    detail: `${label} ${num(value, digits)}。`,
    sat: null,
    skipNoise: false,
  };
}

function rankFrame(line: (number | null)[], index: number, label: string, side: "高" | "低", digits = 2): Frame {
  const rank = pctAt(line, index);
  const value = line[index] ?? null;
  return {
    flag: rank == null ? null : side === "高" ? rank >= 80 : rank <= 20,
    drive: line,
    detail: `${label} ${num(value, digits)}，分位 ${rank == null ? "—" : rank.toFixed(0)}。`,
    sat: null,
    skipNoise: false,
  };
}

function extraFrame(id: string, series: MarketSeries, index: number): Frame | null {
  const price = series.adj[index] ?? null;
  if (id === "VIA-VQG-SG-TRD007") return lineFrame(price, series.adj, series.dema, index, "20 日雙重指數均線");
  if (id === "VIA-VQG-SG-TRD008") return lineFrame(price, series.adj, series.tema, index, "20 日三重指數均線");
  if (id === "VIA-VQG-SG-TRD009") return lineFrame(price, series.adj, series.hma, index, "16 日赫爾均線");
  if (id === "VIA-VQG-SG-TRD010") {
    const up = series.aroonUp[index] ?? null;
    const down = series.aroonDown[index] ?? null;
    return {
      flag: up == null || down == null ? null : up > down,
      drive: series.aroonUp.map((value, i) => (value == null || series.aroonDown[i] == null ? null : value - series.aroonDown[i]!)),
      detail: `Aroon Up ${num(up, 1)}，Aroon Down ${num(down, 1)}。`,
      sat: stuck(series.aroonUp, series.adj, index),
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-TRD011") return signFrame(series.slope, index, "20 日迴歸斜率", 4);
  if (id === "VIA-VQG-SG-MOM008") return signFrame(series.momentum, index, "10 日動量", 1);
  if (id === "VIA-VQG-SG-MOM009") return signFrame(series.ppoHist, index, "PPO 柱");
  if (id === "VIA-VQG-SG-MOM010") {
    const row = signFrame(series.tsi, index, "TSI", 1);
    return { ...row, sat: stuck(series.tsi, series.adj, index) };
  }
  if (id === "VIA-VQG-SG-MOM011") {
    const row = rankFrame(series.ultimate, index, "Ultimate Oscillator", "高", 1);
    return { ...row, sat: stuck(series.ultimate, series.adj, index) };
  }
  if (id === "VIA-VQG-SG-MOM012") return signFrame(series.awesome, index, "Awesome Oscillator", 1);
  if (id === "VIA-VQG-SG-VOL005") return rankFrame(series.parkinson, index, "Parkinson 波動", "高", 4);
  if (id === "VIA-VQG-SG-VOL006") return rankFrame(series.ulcer, index, "Ulcer Index", "高", 2);
  if (id === "VIA-VQG-SG-VOL007") return signFrame(series.chaikin, index, "Chaikin Volatility");
  if (id === "VIA-VQG-SG-VOL008") return rankFrame(series.closeStd, index, "收盤標準差", "高", 1);
  if (id === "VIA-VQG-SG-RSK004") return rankFrame(series.downside, index, "下跌偏差", "高", 4);
  if (id === "VIA-VQG-SG-RSK005") return rankFrame(series.pain, index, "Pain Index", "低", 4);
  if (id === "VIA-VQG-SG-RSK006") return rankFrame(series.burke, index, "Burke Ratio", "低", 2);
  if (id === "VIA-VQG-SG-STA001") return rankFrame(series.zscore, index, "Z-Score", "高", 2);
  if (id === "VIA-VQG-SG-STA002") return lineFrame(price, series.adj, series.median, index, "20 日中位數");
  if (id === "VIA-VQG-SG-STA003") return rankFrame(series.returnMad, index, "報酬平均絕對離差", "高", 4);
  return null;
}

function frameAt(id: string, series: MarketSeries, index: number, drives: Record<string, (number | null)[]>): Frame | null {
  const price = series.adj[index] ?? null;
  if (id === "VIA-VQG-SG-TRD001") {
    const line = series.sma20[index] ?? null;
    return {
      flag: price == null || line == null ? null : price > line,
      drive: drives.smaGap!,
      detail: `收盤 ${num(price, 1)}，20 日均線 ${num(line, 1)}。`,
      sat: null,
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-TRD002") {
    const fast = series.sma10[index] ?? null;
    const slow = series.sma60[index] ?? null;
    return {
      flag: fast == null || slow == null ? null : fast > slow,
      drive: drives.maGap!,
      detail: `10 日均線 ${num(fast, 1)}，60 日均線 ${num(slow, 1)}。`,
      sat: null,
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-TRD003") {
    const line = series.ema20[index] ?? null;
    return {
      flag: price == null || line == null ? null : price > line,
      drive: drives.emaGap!,
      detail: `收盤 ${num(price, 1)}，20 日指數均線 ${num(line, 1)}。`,
      sat: null,
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-VOL001") {
    const rank = pctAt(series.bandwidth, index);
    return {
      flag: rank == null ? null : rank <= 20,
      drive: series.bandwidth,
      detail: `帶寬分位 ${rank == null ? "—" : rank.toFixed(0)}。`,
      sat: null,
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-TRD004" || id === "VIA-VQG-SG-TRD005") {
    const upper = series.bollUpper[index] ?? null;
    const lower = series.bollLower[index] ?? null;
    const outside = id.endsWith("004");
    return {
      flag: price == null || (outside ? upper == null : lower == null) ? null : outside ? price > upper! : price < lower!,
      drive: outside ? drives.upGap! : drives.downGap!,
      detail: `收盤 ${num(price, 1)}，上軌 ${num(upper, 1)}，下軌 ${num(lower, 1)}。`,
      sat: null,
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-MOM007") {
    const change = series.roc20[index] ?? null;
    return {
      flag: change == null ? null : change > 0,
      drive: series.roc20,
      detail: `20 日漲跌 ${change == null ? "—" : (change * 100).toFixed(2)}%。`,
      sat: null,
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-TRD006") {
    const line = series.sma20[index] ?? null;
    const dev = price == null || line == null || line === 0 ? null : price / line - 1;
    const rank = pctAt(drives.dev20!, index);
    return {
      flag: rank == null ? null : rank >= 80,
      drive: drives.dev20!,
      detail: `20 日乖離 ${dev == null ? "—" : (dev * 100).toFixed(2)}%，分位 ${rank == null ? "—" : rank.toFixed(0)}。`,
      sat: null,
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-VOL004") {
    const rank = pctAt(series.atrS3, index);
    const value = series.atrS3[index] ?? null;
    return {
      flag: rank == null ? null : rank >= 80,
      drive: series.atrS3,
      detail: `真實波幅占收盤 ${value == null ? "—" : value.toFixed(4)}，分位 ${rank == null ? "—" : rank.toFixed(0)}。`,
      sat: null,
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-RSK003") {
    const rank = pctAt(series.sharpe60, index);
    const value = series.sharpe60[index] ?? null;
    return {
      flag: rank == null ? null : rank <= 20,
      drive: series.sharpe60,
      detail: `滾動夏普 S2 ${value == null ? "—" : value.toFixed(4)}，分位 ${rank == null ? "—" : rank.toFixed(0)}。`,
      sat: null,
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-MOM001" || id === "VIA-VQG-SG-MOM002") {
    const rank = pctAt(series.rsi14, index);
    const high = id.endsWith("001");
    return {
      flag: rank == null ? null : high ? rank >= 80 : rank <= 20,
      drive: series.rsi14,
      detail: `RSI ${num(series.rsi14[index] ?? null, 1)}，分位 ${rank == null ? "—" : rank.toFixed(0)}。`,
      sat: stuck(series.rsi14, series.adj, index),
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-MOM003") {
    const side = stuck(series.rsi14, series.adj, index);
    return {
      flag: series.rsi14[index] == null ? null : side != null,
      drive: series.rsi14,
      detail: side == null ? `RSI ${num(series.rsi14[index] ?? null, 1)}，沒有停在極端區。` : `RSI 出現${side}鈍化。`,
      sat: side,
      skipNoise: true,
    };
  }
  if (id === "VIA-VQG-SG-MOM004") {
    const hist = series.macdHist[index] ?? null;
    return {
      flag: hist == null ? null : hist > 0,
      drive: series.macdHist,
      detail: `柱 ${num(hist, 1)}。`,
      sat: null,
      skipNoise: false,
    };
  }
  if (id === "VIA-VQG-SG-MOM005" || id === "VIA-VQG-SG-MOM006") {
    const k = series.k[index] ?? null;
    const d = series.d[index] ?? null;
    const side = stuck(series.k, series.adj, index);
    return {
      flag: id.endsWith("005") ? (k == null || d == null ? null : k > d) : k == null ? null : side != null,
      drive: drives.kdGap!,
      detail: id.endsWith("005") ? `K ${num(k, 1)}，D ${num(d, 1)}。` : side == null ? `K ${num(k, 1)}，沒有停在極端區。` : `K 出現${side}鈍化。`,
      sat: side,
      skipNoise: id.endsWith("006"),
    };
  }
  const extra = extraFrame(id, series, index);
  if (extra) return extra;
  return null;
}

function noiseText(now: Flag, prev: Flag, rank: number | null, skip: boolean): string {
  if (skip) return "這個跡象不使用中間區翻轉來記噪音。";
  if (now == null || prev == null) return "樣本不足，不記噪音。";
  if (now !== prev && rank != null && rank > 20 && rank < 80) return "潛在噪音：這一筆和前一筆不同，驅動數字仍在中間區。";
  if (now !== prev) return "這一筆和前一筆不同，但不在中間區，不記成這類噪音。";
  return "沒有看到這類噪音。";
}

function saturationText(side: Side, applies: boolean): string {
  if (!applies) return "不適用。";
  if (side == null) return "沒有看到鈍化。";
  return `${side}鈍化：指標停在極端區，價格仍往同一邊走。這不表示價格會轉彎。`;
}

export function runTests(defs: SignalDef[], series: MarketSeries): TestRow[] {
  const drives = {
    smaGap: gap(series.adj, series.sma20),
    maGap: gap(series.sma10, series.sma60),
    emaGap: gap(series.adj, series.ema20),
    kdGap: series.k.map((value, i) => (value == null || series.d[i] == null ? null : value - series.d[i]!)),
    upGap: gap(series.adj, series.bollUpper),
    downGap: gap(series.bollLower, series.adj),
    dev20: series.adj.map((price, i) => {
      const line = series.sma20[i];
      return price == null || line == null || line === 0 ? null : price / line - 1;
    }),
  };
  const last = series.adj.length - 1;
  return defs.map((def) => {
    const counts = { checks: 0, present: 0, absent: 0, insufficient: 0, noiseCount: 0, saturationCount: 0 };
    let prev: Flag = null;
    let prior: Flag = null;
    let latest: Frame | null = null;
    const applies = !def.saturationRule.startsWith("不適用");
    for (let i = 0; i < series.adj.length; i++) {
      const row = frameAt(def.id, series, i, drives);
      if (!row) continue;
      if (row.flag == null) counts.insufficient += 1;
      else {
        counts.checks += 1;
        if (row.flag) counts.present += 1;
        else counts.absent += 1;
      }
      const rank = pctAt(row.drive, i);
      if (!row.skipNoise && row.flag != null && prev != null && row.flag !== prev && rank != null && rank > 20 && rank < 80) {
        counts.noiseCount += 1;
      }
      if (row.sat) counts.saturationCount += 1;
      prior = prev;
      prev = row.flag;
      if (i === last) latest = row;
    }
    const status: TestStatus = latest == null || latest.flag == null ? "樣本不足" : latest.flag ? "看得到" : "看不到";
    const rank = latest ? pctAt(latest.drive, last) : null;
    return {
      id: def.id,
      name: def.name,
      indicatorId: def.indicatorId,
      meaning: def.meaning,
      testQuestion: def.testQuestion,
      evidenceRule: def.evidenceRule,
      noiseRule: def.noiseRule,
      saturationRule: def.saturationRule,
      ...counts,
      latestStatus: status,
      latestDetail: latest?.detail ?? "沒有可核對的數列。",
      noiseNow: noiseText(latest?.flag ?? null, prior, rank, latest?.skipNoise ?? false),
      saturationNow: saturationText(latest?.sat ?? null, applies),
    };
  });
}

export type CatalogCheck = {
  id: string;
  name: string;
  question: string;
  status: TestStatus;
  detail: string;
};

export function runCatalogTests(input: {
  rows: { name: string; source: string; frequency: string; evidence: string; code: string }[];
  groups: { code: string; members: { symbol: string }[] }[];
  historyOffRoster: number;
  quotedSymbols: string[];
}): CatalogCheck[] {
  const keys = input.rows.map((row) => `${row.name}|${row.source}|${row.frequency}`);
  const duplicateKeys = keys.length - new Set(keys).size;
  const codes = [...input.rows.map((row) => row.code), ...input.groups.map((group) => group.code)];
  const duplicateCodes = codes.filter(Boolean).length - new Set(codes.filter(Boolean)).size;
  const blank = input.rows.filter((row) => !row.code || !row.evidence).length;
  const waiting = input.rows.filter((row) => row.evidence !== "T1" && row.evidence !== "SSOT").length;
  const members = input.groups.flatMap((group) => group.members);
  const quoted = new Set(input.quotedSymbols);
  const hit = members.filter((member) => quoted.has(member.symbol)).length;
  return [
    {
      id: "VIA-TST-EXT-001",
      name: "擷取列是否重複",
      question: "同一小項目、同一來源、同一頻率，有沒有登錄兩次？",
      status: duplicateKeys === 0 ? "看得到" : "看不到",
      detail: duplicateKeys === 0 ? `${keys.length} 列，沒有重複。` : `${duplicateKeys} 個重複。重複的要留下，但不能當成兩筆新資料。`,
    },
    {
      id: "VIA-TST-EXT-002",
      name: "編碼是否撞號",
      question: "擷取列和族群有沒有用到同一個編碼？",
      status: duplicateCodes === 0 && blank === 0 ? "看得到" : "看不到",
      detail: `${codes.filter(Boolean).length} 個編碼。${duplicateCodes === 0 && blank === 0 ? "沒有撞號，也沒有空號。" : `撞號 ${duplicateCodes}，空號 ${blank}。`}`,
    },
    {
      id: "VIA-TST-EXT-003",
      name: "證據層有沒有標明",
      question: "每一列是否寫明現在能不能接到真值？",
      status: blank === 0 ? "看得到" : "看不到",
      detail: `${input.rows.length - waiting} 列標成可接真值或骨架。${waiting} 列是待接或推算，不補數字。`,
    },
    {
      id: "VIA-TST-EXT-004",
      name: "名冊對到今天報價",
      question: "族群名冊裡，今天有幾檔對到報價？對不到的留空。",
      status: hit === 0 ? "樣本不足" : "看得到",
      detail: `${hit} / ${members.length} 檔有報價。沒有報價不算失敗，也不補上。`,
    },
    {
      id: "VIA-TST-EXT-005",
      name: "舊快照有沒有混進今天",
      question: "2026-07-18 的五態，有沒有被當成今天的計算結果？",
      status: "看得到",
      detail: `分開存放。其中 ${input.historyOffRoster} 個名稱不在目前名冊，不能拿來排今天。`,
    },
  ];
}
