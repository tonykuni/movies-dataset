export type CalcBar = {
  date: string;
  adj: number;
  high: number | null;
  low: number | null;
  turnover: number | null;
  daytrade: number | null;
  activeEtf: number | null;
  deducted: number | null;
  foreign: number | null;
  trust: number | null;
  dealer: number | null;
};

export type CalcDef = {
  id: string;
  theme: string;
  name: string;
  params: Record<string, number>;
  windows: number[];
};

export type Reading = {
  id: string;
  theme: string;
  name: string;
  window: number | null;
  label: string;
  value: number | null;
  unit: string;
  percentile: number | null;
  signal: string;
};

const TAIL = "只說明目前位置，不表示之後會怎樣。";

function round(n: number, digits: number): number {
  const p = 10 ** digits;
  return Math.round(n * p) / p;
}

export function sma(values: number[], period: number): (number | null)[] {
  return values.map((_, i) => {
    if (i + 1 < period) return null;
    let sum = 0;
    for (let k = i + 1 - period; k <= i; k++) sum += values[k]!;
    return sum / period;
  });
}

export function ema(values: number[], period: number): (number | null)[] {
  const out: (number | null)[] = values.map(() => null);
  if (values.length < period) return out;
  const alpha = 2 / (period + 1);
  let seed = 0;
  for (let i = 0; i < period; i++) seed += values[i]!;
  let prev = seed / period;
  out[period - 1] = prev;
  for (let i = period; i < values.length; i++) {
    prev = values[i]! * alpha + prev * (1 - alpha);
    out[i] = prev;
  }
  return out;
}

function lastOf(series: (number | null)[]): number | null {
  for (let i = series.length - 1; i >= 0; i--) if (series[i] != null) return series[i]!;
  return null;
}

function percentileOf(series: (number | null)[], lookback = 120): number | null {
  let idx = -1;
  for (let i = series.length - 1; i >= 0; i--) {
    if (series[i] != null) {
      idx = i;
      break;
    }
  }
  if (idx < 0) return null;
  const start = Math.max(0, idx + 1 - lookback);
  const slice = series.slice(start, idx + 1).filter((value): value is number => value != null);
  if (slice.length < 20) return null;
  const current = series[idx]!;
  return round((slice.filter((value) => value <= current).length / slice.length) * 100, 1);
}

function place(name: string, pct: number | null, fact: string): string {
  const where =
    pct == null
      ? "樣本不足，不判定高低"
      : pct >= 80
        ? `落在自身近 120 筆的高位（${pct.toFixed(0)} 分位）`
        : pct <= 20
          ? `落在自身近 120 筆的低位（${pct.toFixed(0)} 分位）`
          : `落在自身近 120 筆的中間（${pct.toFixed(0)} 分位）`;
  return `${name}：${fact}${where}。${TAIL}`;
}

function reading(
  def: CalcDef,
  window: number | null,
  label: string,
  value: number | null,
  unit: string,
  series: (number | null)[],
  fact: string,
): Reading {
  const percentile = percentileOf(series);
  return {
    id: def.id,
    theme: def.theme,
    name: def.name,
    window,
    label,
    value: value == null ? null : round(value, 4),
    unit,
    percentile,
    signal: place(`${def.name}${label}`, percentile, fact),
  };
}

function returns(adj: number[]): (number | null)[] {
  return adj.map((price, i) => (i === 0 || adj[i - 1] === 0 ? null : price / adj[i - 1]! - 1));
}

function stdev(values: number[]): number | null {
  if (values.length < 2) return null;
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  const ss = values.reduce((sum, value) => sum + (value - mean) ** 2, 0);
  return Math.sqrt(ss / values.length);
}

function rsi(adj: number[], period: number): (number | null)[] {
  const out: (number | null)[] = adj.map(() => null);
  if (adj.length <= period) return out;
  let gain = 0;
  let loss = 0;
  for (let i = 1; i <= period; i++) {
    const diff = adj[i]! - adj[i - 1]!;
    if (diff >= 0) gain += diff;
    else loss -= diff;
  }
  let avgGain = gain / period;
  let avgLoss = loss / period;
  const score = () => {
    if (avgGain === 0 && avgLoss === 0) return 50;
    if (avgLoss === 0 && avgGain > 0) return 100;
    if (avgGain === 0) return 0;
    return (100 * avgGain) / (avgGain + avgLoss);
  };
  out[period] = score();
  for (let i = period + 1; i < adj.length; i++) {
    const diff = adj[i]! - adj[i - 1]!;
    avgGain = (avgGain * (period - 1) + Math.max(diff, 0)) / period;
    avgLoss = (avgLoss * (period - 1) + Math.max(-diff, 0)) / period;
    out[i] = score();
  }
  return out;
}

function macd(adj: number[], fast: number, slow: number, signal: number) {
  const fastLine = ema(adj, fast);
  const slowLine = ema(adj, slow);
  const line = fastLine.map((value, i) => {
    const slowValue = slowLine[i];
    return value == null || slowValue == null ? null : value - slowValue;
  });
  const signalLine = emaNullable(line, signal);
  const hist = line.map((value, i) => (value == null || signalLine[i] == null ? null : value - signalLine[i]!));
  return { line, signalLine, hist };
}

function emaNullable(values: (number | null)[], period: number): (number | null)[] {
  const out: (number | null)[] = values.map(() => null);
  const alpha = 2 / (period + 1);
  let bucket: number[] = [];
  let prev: number | null = null;
  for (let i = 0; i < values.length; i++) {
    const value = values[i];
    if (value == null) {
      bucket = [];
      prev = null;
      continue;
    }
    if (prev == null) {
      bucket.push(value);
      if (bucket.length === period) {
        prev = bucket.reduce((sum, item) => sum + item, 0) / period;
        out[i] = prev;
        bucket = [];
      }
      continue;
    }
    prev = value * alpha + prev * (1 - alpha);
    out[i] = prev;
  }
  return out;
}

function kdj(bars: CalcBar[], period: number) {
  const k: (number | null)[] = bars.map(() => null);
  const d: (number | null)[] = bars.map(() => null);
  const j: (number | null)[] = bars.map(() => null);
  const kW = 3;
  const dW = 3;
  const seed = 50;
  let prevK = seed;
  let prevD = seed;
  let ready = false;
  for (let i = period - 1; i < bars.length; i++) {
    let high = -Infinity;
    let low = Infinity;
    let complete = true;
    for (let n = i + 1 - period; n <= i; n++) {
      const barHigh = bars[n]!.high;
      const barLow = bars[n]!.low;
      if (barHigh == null || barLow == null) {
        complete = false;
        break;
      }
      high = Math.max(high, barHigh);
      low = Math.min(low, barLow);
    }
    if (!complete || high === low) {
      prevK = seed;
      prevD = seed;
      ready = false;
      continue;
    }
    const rsv = ((bars[i]!.adj - low) / (high - low)) * 100;
    prevK = ready ? ((kW - 1) / kW) * prevK + rsv / kW : ((kW - 1) / kW) * seed + rsv / kW;
    prevD = ready ? ((dW - 1) / dW) * prevD + prevK / dW : ((dW - 1) / dW) * seed + prevK / dW;
    ready = true;
    k[i] = prevK;
    d[i] = prevD;
    j[i] = 3 * prevK - 2 * prevD;
  }
  return { k, d, j };
}

function sharpeSeries(adj: number[], period: number): (number | null)[] {
  const ret = returns(adj);
  return ret.map((_, i) => {
    if (i < period) return null;
    const slice: number[] = [];
    for (let k = i + 1 - period; k <= i; k++) {
      const value = ret[k];
      if (value == null) return null;
      slice.push(value);
    }
    const sd = stdev(slice);
    if (sd == null || sd === 0) return null;
    const mean = slice.reduce((sum, value) => sum + value, 0) / slice.length;
    return (mean / sd) * Math.sqrt(252);
  });
}

function sortinoSeries(adj: number[], period: number): (number | null)[] {
  const ret = returns(adj);
  return ret.map((_, i) => {
    if (i < period) return null;
    const slice: number[] = [];
    for (let k = i + 1 - period; k <= i; k++) {
      const value = ret[k];
      if (value == null) return null;
      slice.push(value);
    }
    const downside = Math.sqrt(slice.reduce((sum, value) => sum + Math.min(value, 0) ** 2, 0) / slice.length);
    if (downside === 0) return null;
    const mean = slice.reduce((sum, value) => sum + value, 0) / slice.length;
    return (mean / downside) * Math.sqrt(252);
  });
}

function strictWindow(values: (number | null)[], period: number, reduce: (slice: number[]) => number): (number | null)[] {
  return values.map((_, i) => {
    if (i + 1 < period) return null;
    const slice: number[] = [];
    for (let k = i + 1 - period; k <= i; k++) {
      const value = values[k];
      if (value == null) return null;
      slice.push(value);
    }
    return reduce(slice);
  });
}

function obv(bars: CalcBar[]): (number | null)[] {
  const out: (number | null)[] = bars.map(() => null);
  let level = 0;
  let started = false;
  for (let i = 1; i < bars.length; i++) {
    const amount = bars[i]!.deducted;
    if (amount == null) continue;
    started = true;
    if (bars[i]!.adj > bars[i - 1]!.adj) level += amount;
    else if (bars[i]!.adj < bars[i - 1]!.adj) level -= amount;
    out[i] = level;
  }
  if (!started) return out;
  return out;
}

function unavailable(def: CalcDef, text: string): Reading[] {
  return [
    {
      id: def.id,
      theme: def.theme,
      name: def.name,
      window: null,
      label: "",
      value: null,
      unit: "",
      percentile: null,
      signal: text,
    },
  ];
}

function windowed(def: CalcDef, series: (number | null)[], unit: string, fact: string, mode: "avg" | "sum"): Reading[] {
  return def.windows.map((period) => {
    const rolled =
      period <= 1
        ? series
        : strictWindow(series, period, (slice) => {
            const total = slice.reduce((sum, item) => sum + item, 0);
            return mode === "avg" ? total / slice.length : total;
          });
    return reading(def, period, period <= 1 ? " 當天" : ` ${period}日`, lastOf(rolled), unit, rolled, fact);
  });
}

function comparable(def: CalcDef, bars: CalcBar[]): Reading[] {
  if (def.id.endsWith("CMP001")) {
    const last = bars.at(-1)?.adj ?? null;
    return [
      {
        id: def.id,
        theme: def.theme,
        name: def.name,
        window: 1,
        label: " 當天",
        value: last == null ? null : round(last, 2),
        unit: "點",
        percentile: null,
        signal: "調整後收盤只是價格。點數不能跟過去或別的商品比，要比就用漲跌幅。",
      },
    ];
  }
  if (def.id.endsWith("CMP008")) return unavailable(def, "融資融券餘額還沒接上。留空，不用成交量或法人數字代替。");
  if (def.id.endsWith("CMP009")) return unavailable(def, "這頁只有上市成交。櫃買沒接上之前，不把上市單獨當成上市加櫃買。");
  if (def.id.endsWith("CMP010")) return unavailable(def, "台積電扣過當沖的成交值還沒接上。先留空，避免用總成交硬減。");
  if (def.id.endsWith("CMP011")) return unavailable(def, "這張表是加權指數。指數對自己沒有剩餘漲跌。這個指標留給個股，跨群比較時才算。");
  if (def.id.endsWith("CMP002")) {
    const changes = bars.map((bar, i) => (i === 0 || bars[i - 1]!.adj === 0 ? null : (bar.adj / bars[i - 1]!.adj - 1) * 100));
    return windowed(def, changes, "%", "這是漲跌幅，用來跨日、跨群比較。", "avg");
  }
  const nets = bars.map((bar) => (bar.foreign == null || bar.trust == null || bar.dealer == null ? null : bar.foreign + bar.trust + bar.dealer));
  if (def.id.endsWith("CMP003")) return windowed(def, nets, "億元", "這是金額。跨日比較請改看占比。", "sum");
  if (def.id.endsWith("CMP004")) {
    const ratios = bars.map((bar, i) => {
      const net = nets[i];
      if (net == null || bar.deducted == null || bar.deducted === 0) return null;
      return ((net * 1e8) / bar.deducted) * 100;
    });
    return windowed(def, ratios, "%", "這是淨額占扣當沖成交的比例。", "avg");
  }
  if (def.id.endsWith("CMP005")) {
    const ratios = bars.map((bar) => (bar.daytrade == null || bar.turnover == null || bar.turnover === 0 ? null : (bar.daytrade / bar.turnover) * 100));
    return windowed(def, ratios, "%", "占比高，表示成交比較多是當天來回去。", "avg");
  }
  if (def.id.endsWith("CMP006")) {
    const amounts = bars.map((bar) => (bar.deducted == null ? null : bar.deducted / 1e8));
    return windowed(def, amounts, "億元", "這是扣掉當沖後的成交金額。", "sum");
  }
  if (def.id.endsWith("CMP007")) {
    if (bars.every((bar) => bar.activeEtf == null)) {
      return unavailable(def, "投信合計裡已經含主動式台股 ETF，但沒有拆開。沒有拆開就不另算。");
    }
    return windowed(def, bars.map((bar) => bar.activeEtf), "億元", "這一段才是主動式台股 ETF，不是全部投信。", "sum");
  }
  return unavailable(def, "這個編號還沒有接上計算式。");
}

export function computeIndicator(def: CalcDef, bars: CalcBar[]): Reading[] {
  if (def.id.includes("-CMP")) return comparable(def, bars);
  const adj = bars.map((bar) => bar.adj);
  const lastAdj = adj.at(-1) ?? null;
  const windows = def.windows.length ? def.windows : [0];
  if (def.id === "VIA-VQG-TA-TRD001" || def.id === "VIA-VQG-TA-TRD002") {
    return windows.map((period) => {
      const series = def.id.endsWith("001") ? sma(adj, period) : ema(adj, period);
      const value = lastOf(series);
      const gap = lastAdj != null && value ? lastAdj / value - 1 : null;
      return reading(
        def,
        period,
        ` ${period}日`,
        value,
        "點",
        series,
        gap == null ? "" : `收盤較均線 ${gap >= 0 ? "高" : "低"} ${Math.abs(gap * 100).toFixed(2)}%。`,
      );
    });
  }
  if (def.id === "VIA-VQG-TA-TRD003") {
    const period = def.windows[0] ?? 20;
    const mult = def.params.mult ?? 2;
    const ddof = def.params.ddof ?? 0;
    const band = bands(adj, period, mult, ddof);
    return [reading(def, period, ` ${period}日`, lastOf(band.width), "比值", band.width, "")];
  }
  if (def.id === "VIA-VQG-TA-TRD004" || def.id === "VIA-VQG-TA-MOM004") {
    return windows.map((period) => {
      const series =
        def.id === "VIA-VQG-TA-TRD004"
          ? adj.map((price, i) => {
              const base = sma(adj, period)[i];
              return base == null || base === 0 ? null : (price / base - 1) * 100;
            })
          : adj.map((price, i) => (i < period || adj[i - period] === 0 ? null : (price / adj[i - period]! - 1) * 100));
      return reading(def, period, ` ${period}日`, lastOf(series), "%", series, "");
    });
  }
  if (def.id === "VIA-VQG-TA-MOM001") {
    return windows.map((period) => {
      const series = rsi(adj, period);
      return reading(def, period, ` ${period}日`, lastOf(series), "點", series, "");
    });
  }
  if (def.id === "VIA-VQG-TA-MOM002") {
    const fast = def.params.fast ?? 12;
    const slow = def.params.slow ?? 26;
    const signal = def.params.signal ?? 9;
    const scale = def.params.histogram_scale ?? 1;
    const result = macd(adj, fast, slow, signal);
    const hist = result.hist.map((value) => (value == null ? null : value * scale));
    return [
      reading(def, null, " DIF", lastOf(result.line), "點", result.line, ""),
      reading(def, null, " DEA", lastOf(result.signalLine), "點", result.signalLine, ""),
      reading(def, null, " 柱", lastOf(hist), "點", hist, "柱的倍率是 1，不是 2。"),
    ];
  }
  if (def.id === "VIA-VQG-TA-MOM003") {
    const period = def.windows[0] ?? 9;
    const result = kdj(bars, period);
    return [
      reading(def, period, " K", lastOf(result.k), "點", result.k, ""),
      reading(def, period, " D", lastOf(result.d), "點", result.d, ""),
      reading(def, period, " J", lastOf(result.j), "點", result.j, ""),
    ];
  }
  if (def.id === "VIA-VQG-TA-VOL001") {
    const ret = returns(adj);
    return windows.map((period) => {
      const vol = ret.map((_, i) => {
        if (i < period) return null;
        const slice: number[] = [];
        for (let k = i + 1 - period; k <= i; k++) {
          const value = ret[k];
          if (value == null) return null;
          slice.push(value);
        }
        const sd = stdev(slice);
        return sd == null ? null : sd * Math.sqrt(252) * 100;
      });
      return reading(def, period, ` ${period}日`, lastOf(vol), "%", vol, "");
    });
  }
  if (def.id === "VIA-VQG-TA-VOL002") {
    const ret = returns(adj);
    return windows.map((period) => {
      const series = ret.map((value, i) => {
        if (value == null || i + 1 < period) return null;
        const slice: number[] = [];
        for (let k = i + 1 - period; k <= i; k++) {
          const item = ret[k];
          if (item == null) return null;
          slice.push(item);
        }
        return (slice.filter((item) => item <= value).length / slice.length) * 100;
      });
      return reading(def, period, ` ${period}日`, lastOf(series), "分位", series, "");
    });
  }
  if (def.id === "VIA-VQG-TA-FLW001") {
    const amounts = bars.map((bar) => bar.deducted);
    return windows.map((period) => {
      const series = strictWindow(amounts, period, (slice) => slice.reduce((sum, item) => sum + item, 0) / slice.length).map((value) =>
        value == null ? null : value / 1e8,
      );
      return reading(def, period, ` ${period}日`, lastOf(series), "億元", series, "只用扣當沖後的成交值。");
    });
  }
  if (def.id === "VIA-VQG-TA-FLW002") {
    const series = obv(bars).map((value) => (value == null ? null : value / 1e8));
    return [reading(def, null, "", lastOf(series), "億元", series, "累計只用扣當沖後的成交值。")];
  }
  if (def.id === "VIA-VQG-TA-FLW003" || def.id === "VIA-VQG-TA-FLW004") {
    const source = bars.map((bar) => (def.id.endsWith("003") ? bar.foreign : bar.trust));
    return windows.map((period) => {
      const summed = strictWindow(source, period, (slice) => slice.reduce((sum, item) => sum + item, 0));
      return reading(def, period, ` ${period}日`, lastOf(summed), "億元", summed, "窗口裡缺一天，這一段就不加總。");
    });
  }
  if (def.id === "VIA-VQG-TA-RSK001") {
    return windows.map((period) => {
      const series = sharpeSeries(adj, period);
      return reading(def, period, ` ${period}日`, lastOf(series), "倍", series, "無風險利率以 0 計算。");
    });
  }
  if (def.id === "VIA-VQG-TA-RSK002") {
    return windows.map((period) => {
      const series = sortinoSeries(adj, period);
      return reading(def, period, ` ${period}日`, lastOf(series), "倍", series, "無風險利率以 0 計算。");
    });
  }
  return [
    reading(def, null, "", null, "", [], "這個編號還沒有接上計算式。"),
  ];
}

export function computeAll(defs: CalcDef[], bars: CalcBar[]): Reading[] {
  return defs.flatMap((def) => computeIndicator(def, bars));
}

export type MarketSeries = {
  adj: number[];
  sma10: (number | null)[];
  sma20: (number | null)[];
  sma60: (number | null)[];
  ema20: (number | null)[];
  rsi14: (number | null)[];
  macdHist: (number | null)[];
  k: (number | null)[];
  d: (number | null)[];
  bandwidth: (number | null)[];
  bollUpper: (number | null)[];
  bollLower: (number | null)[];
  roc20: (number | null)[];
};

export function marketSeries(bars: CalcBar[]): MarketSeries {
  const adj = bars.map((bar) => bar.adj);
  const band = bands(adj, 20, 2, 0);
  const osc = macd(adj, 12, 26, 9);
  const kd = kdj(bars, 9);
  return {
    adj,
    sma10: sma(adj, 10),
    sma20: band.mid,
    sma60: sma(adj, 60),
    ema20: ema(adj, 20),
    rsi14: rsi(adj, 14),
    macdHist: osc.hist,
    k: kd.k,
    d: kd.d,
    bandwidth: band.width,
    bollUpper: band.upper,
    bollLower: band.lower,
    roc20: adj.map((price, i) => (i < 20 || adj[i - 20] === 0 ? null : price / adj[i - 20]! - 1)),
  };
}

function bands(values: number[], period: number, mult: number, ddof: number) {
  const mid = sma(values, period);
  const denom = period - ddof;
  const upper: (number | null)[] = values.map(() => null);
  const lower: (number | null)[] = values.map(() => null);
  const width: (number | null)[] = values.map(() => null);
  mid.forEach((value, i) => {
    if (value == null || value === 0 || denom <= 0) return;
    let ss = 0;
    for (let k = i + 1 - period; k <= i; k++) ss += (values[k]! - value) ** 2;
    const sd = Math.sqrt(ss / denom);
    upper[i] = value + mult * sd;
    lower[i] = value - mult * sd;
    width[i] = (upper[i]! - lower[i]!) / value;
  });
  return { mid, upper, lower, width };
}

export function bollinger(values: number[], period = 20, mult = 2) {
  const { mid, upper, lower } = bands(values, period, mult, 0);
  return { mid, upper, lower };
}
