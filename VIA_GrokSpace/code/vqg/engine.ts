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

function trueRanges(bars: CalcBar[]): (number | null)[] {
  return bars.map((bar, i) => {
    if (bar.high == null || bar.low == null) return null;
    const span = bar.high - bar.low;
    if (i === 0) return span;
    const prev = bars[i - 1]!.adj;
    return Math.max(span, Math.abs(bar.high - prev), Math.abs(bar.low - prev));
  });
}

function wilderSeeded(values: (number | null)[], period: number): (number | null)[] {
  const out: (number | null)[] = values.map(() => null);
  const alpha = 1 / period;
  let i = 0;
  while (i < values.length) {
    while (i < values.length && values[i] == null) i += 1;
    const start = i;
    while (i < values.length && values[i] != null) i += 1;
    const end = i;
    if (end - start < period) continue;
    let seed = 0;
    for (let k = start; k < start + period; k += 1) seed += values[k]!;
    let prev = seed / period;
    out[start + period - 1] = prev;
    for (let k = start + period; k < end; k += 1) {
      prev = values[k]! * alpha + prev * (1 - alpha);
      out[k] = prev;
    }
  }
  return out;
}

function rollingMean(values: (number | null)[], period: number): (number | null)[] {
  return strictWindow(values, period, (slice) => slice.reduce((sum, item) => sum + item, 0) / slice.length);
}

function cleanTurnover(bars: CalcBar[]): (number | null)[] {
  return bars.map((bar) => {
    const total = bar.turnover;
    const daytrade = bar.daytrade;
    if (total == null || daytrade == null) return null;
    if (total < 0 || daytrade < 0 || daytrade > total) return null;
    return total - daytrade;
  });
}

function cleanDirection(bars: CalcBar[], clean: (number | null)[]): (number | null)[] {
  return bars.map((bar, i) => {
    const amount = clean[i];
    if (i === 0 || amount == null) return null;
    const diff = bar.adj - bars[i - 1]!.adj;
    const sign = diff > 0 ? 1 : diff < 0 ? -1 : 0;
    return sign * amount;
  });
}

function ratioOfSums(flow: (number | null)[], base: (number | null)[], period: number): (number | null)[] {
  return flow.map((_, i) => {
    if (i + 1 < period) return null;
    let numerator = 0;
    let denominator = 0;
    for (let k = i + 1 - period; k <= i; k += 1) {
      const part = flow[k];
      const amount = base[k];
      if (part == null || amount == null) return null;
      numerator += part;
      denominator += amount;
    }
    if (denominator === 0) return null;
    return numerator / denominator;
  });
}

function meanShiftRatio(values: (number | null)[], period: number): (number | null)[] {
  const means = rollingMean(values, period);
  return means.map((current, i) => {
    const prior = i >= period ? means[i - period] : null;
    if (current == null || prior == null || prior === 0) return null;
    return current / prior;
  });
}

function sampleStd(values: number[]): number | null {
  if (values.length < 2) return null;
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  const ss = values.reduce((sum, value) => sum + (value - mean) ** 2, 0);
  return Math.sqrt(ss / (values.length - 1));
}

function windowSlice(adj: number[], period: number): (number[] | null)[] {
  const ret = returns(adj);
  return ret.map((_, i) => {
    if (i < period) return null;
    const slice: number[] = [];
    for (let k = i + 1 - period; k <= i; k += 1) {
      const value = ret[k];
      if (value == null) return null;
      slice.push(value);
    }
    return slice;
  });
}

function sharpeRaw(adj: number[], period: number): (number | null)[] {
  return windowSlice(adj, period).map((slice) => {
    if (slice == null) return null;
    const sd = sampleStd(slice);
    if (sd == null || sd === 0) return null;
    const mean = slice.reduce((sum, value) => sum + value, 0) / slice.length;
    return mean / sd;
  });
}

function sortinoRaw(adj: number[], period: number): (number | null)[] {
  return windowSlice(adj, period).map((slice) => {
    if (slice == null) return null;
    const downside = Math.sqrt(slice.reduce((sum, value) => sum + Math.min(value, 0) ** 2, 0) / slice.length);
    if (downside === 0) return null;
    const mean = slice.reduce((sum, value) => sum + value, 0) / slice.length;
    return mean / downside;
  });
}

function unavailable(def: CalcDef, text: string): Reading[] {
  return [blank(def, null, "", "", text)];
}

function blank(def: CalcDef, window: number | null, label: string, unit: string, reason: string): Reading {
  return {
    id: def.id,
    theme: def.theme,
    name: def.name,
    window,
    label,
    value: null,
    unit,
    percentile: null,
    signal: label ? `${def.name}${label}：${reason}` : reason,
  };
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
  if (def.id.endsWith("CMP012")) {
    return [
      blank(def, 60, " S1", "比例", "沒有另一條同市場基準，留空。"),
      blank(def, 60, " S2", "比例", "沒有另一條同市場基準，留空。"),
      blank(def, 60, " S3", "比例", "沒有台積電的調整後收盤序列，留空。"),
    ];
  }
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

function pairsCorr(left: number[], right: number[]): number | null {
  const count = left.length;
  if (count < 3 || right.length !== count) return null;
  let meanLeft = 0;
  let meanRight = 0;
  for (let i = 0; i < count; i++) {
    meanLeft += left[i]!;
    meanRight += right[i]!;
  }
  meanLeft /= count;
  meanRight /= count;
  let cross = 0;
  let leftSq = 0;
  let rightSq = 0;
  for (let i = 0; i < count; i++) {
    const dx = left[i]! - meanLeft;
    const dy = right[i]! - meanRight;
    cross += dx * dy;
    leftSq += dx * dx;
    rightSq += dy * dy;
  }
  if (leftSq === 0 || rightSq === 0) return null;
  return cross / Math.sqrt(leftSq * rightSq);
}

function finiteSeries(series: (number | null)[]): (number | null)[] {
  return series.map((value) => (value == null || !Number.isFinite(value) ? null : value));
}

function quantileLinear(values: number[], q: number): number {
  const sorted = [...values].sort((a, b) => a - b);
  const pos = q * (sorted.length - 1);
  const low = Math.floor(pos);
  const high = Math.ceil(pos);
  if (low === high) return sorted[low]!;
  const weight = pos - low;
  return sorted[low]! * (1 - weight) + sorted[high]! * weight;
}

function rangeWindow(bars: CalcBar[], index: number, period: number): { high: number; low: number } | null {
  let high = -Infinity;
  let low = Infinity;
  for (let k = index + 1 - period; k <= index; k++) {
    const barHigh = bars[k]!.high;
    const barLow = bars[k]!.low;
    if (barHigh == null || barLow == null) return null;
    high = Math.max(high, barHigh);
    low = Math.min(low, barLow);
  }
  return { high, low };
}

function hasRange(bars: CalcBar[]): boolean {
  return bars.some((bar) => bar.high != null && bar.low != null);
}

function ewmReset(values: (number | null)[], alpha: number, minSamples: number): (number | null)[] {
  const out: (number | null)[] = values.map(() => null);
  let prev: number | null = null;
  let count = 0;
  for (let i = 0; i < values.length; i++) {
    const value = values[i];
    if (value == null) {
      prev = null;
      count = 0;
      continue;
    }
    prev = prev == null ? value : value * alpha + prev * (1 - alpha);
    count += 1;
    if (count >= minSamples) out[i] = prev;
  }
  return out;
}

function equityPath(adj: number[]): (number | null)[] {
  const change = returns(adj);
  const out: (number | null)[] = adj.map(() => null);
  let equity = 1;
  let alive = true;
  out[0] = 1;
  for (let i = 1; i < adj.length; i++) {
    const step = change[i];
    if (!alive || step == null) {
      alive = false;
      continue;
    }
    equity *= 1 + step;
    out[i] = equity;
  }
  return out;
}

function drawdownFromPeak(equity: (number | null)[]): (number | null)[] {
  const out: (number | null)[] = equity.map(() => null);
  let peak: number | null = null;
  for (let i = 0; i < equity.length; i++) {
    const value = equity[i];
    if (value == null || value <= 0) {
      peak = null;
      continue;
    }
    peak = peak == null ? value : Math.max(peak, value);
    out[i] = value / peak - 1;
  }
  return out;
}

function rollingMaxDrawdown(equity: (number | null)[], period: number): (number | null)[] {
  return finiteSeries(
    strictWindow(equity, period, (slice) => {
      let peak = slice[0]!;
      let worst = 0;
      for (const value of slice) {
        if (value <= 0) return Number.NaN;
        peak = Math.max(peak, value);
        worst = Math.min(worst, value / peak - 1);
      }
      return worst;
    }),
  );
}

function tail(series: (number | null)[]): number | null {
  return series.at(-1) ?? null;
}

function publish(
  def: CalcDef,
  window: number | null,
  label: string,
  unit: string,
  series: (number | null)[],
  fact: string,
  blankText: string | null,
): Reading {
  const value = tail(series);
  if (value == null) {
    if (blankText) return blank(def, window, label, unit, blankText);
    return reading(def, window, label, null, unit, [], fact);
  }
  return reading(def, window, label, value, unit, series, fact);
}

function tailEqual(bars: CalcBar[], period: number): boolean {
  const index = bars.length - 1;
  if (index + 1 < period) return false;
  const span = rangeWindow(bars, index, period);
  return span != null && span.high === span.low;
}

function tailMadZero(bars: CalcBar[], period: number): boolean {
  const index = bars.length - 1;
  if (index + 1 < period) return false;
  const slice: number[] = [];
  for (let k = index + 1 - period; k <= index; k++) {
    const bar = bars[k]!;
    if (bar.high == null || bar.low == null) return false;
    slice.push((bar.high + bar.low + bar.adj) / 3);
  }
  const mean = slice.reduce((sum, value) => sum + value, 0) / slice.length;
  return slice.every((value) => value === mean);
}

function flatReturns(adj: number[], period: number): boolean {
  const change = returns(adj);
  const index = change.length - 1;
  if (index < period) return false;
  const slice: number[] = [];
  for (let k = index + 1 - period; k <= index; k++) {
    const current = change[k];
    const lagged = change[k - 1];
    if (current == null || lagged == null) return false;
    slice.push(current);
  }
  return slice.every((value) => value === slice[0]);
}

function noShares(def: CalcDef, window: number | null, labels: string[]): Reading[] {
  return labels.map((label) => blank(def, window, label, "", "沒有扣當沖成交股數。不拿成交值代替股數，留空。"));
}

function noBenchmark(def: CalcDef, window: number | null, label: string): Reading[] {
  return [blank(def, window, label, "", "沒有另一條同市場基準的調整後收盤，留空。不拿這條價格對自己算。")];
}

function noRange(def: CalcDef, window: number | null, labels: string[]): Reading[] {
  return labels.map((label) => blank(def, window, label, "", "沒有最高價或最低價，留空。"));
}

function directional(bars: CalcBar[], period: number) {
  const plusDm: (number | null)[] = bars.map(() => null);
  const minusDm: (number | null)[] = bars.map(() => null);
  for (let i = 1; i < bars.length; i++) {
    const high = bars[i]!.high;
    const low = bars[i]!.low;
    const prevHigh = bars[i - 1]!.high;
    const prevLow = bars[i - 1]!.low;
    if (high == null || low == null || prevHigh == null || prevLow == null) continue;
    const up = high - prevHigh;
    const down = prevLow - low;
    plusDm[i] = up > down && up > 0 ? up : 0;
    minusDm[i] = down > up && down > 0 ? down : 0;
  }
  const atr = wilderSeeded(trueRanges(bars), period);
  const plus = wilderSeeded(plusDm, period);
  const minus = wilderSeeded(minusDm, period);
  const plusDi = plus.map((value, i) => (value == null || atr[i] == null || atr[i] === 0 ? null : (100 * value) / atr[i]!));
  const minusDi = minus.map((value, i) => (value == null || atr[i] == null || atr[i] === 0 ? null : (100 * value) / atr[i]!));
  const dx = plusDi.map((value, i) => {
    const other = minusDi[i];
    if (value == null || other == null || value + other === 0) return null;
    return (100 * Math.abs(value - other)) / (value + other);
  });
  return { plusDi, minusDi, adx: wilderSeeded(dx, period) };
}

function stochastic(bars: CalcBar[], period: number) {
  const rsv: (number | null)[] = bars.map(() => null);
  for (let i = period - 1; i < bars.length; i++) {
    const span = rangeWindow(bars, i, period);
    if (span == null || span.high === span.low) continue;
    rsv[i] = ((bars[i]!.adj - span.low) / (span.high - span.low)) * 100;
  }
  const k = ewmReset(rsv, 1 / 3, period);
  return { rsv, k, d: ewmReset(k, 1 / 3, period) };
}

function williamsR(bars: CalcBar[], period: number): (number | null)[] {
  return bars.map((bar, i) => {
    if (i + 1 < period) return null;
    const span = rangeWindow(bars, i, period);
    if (span == null || span.high === span.low) return null;
    return (-100 * (span.high - bar.adj)) / (span.high - span.low);
  });
}

function cciSeries(bars: CalcBar[], period: number): (number | null)[] {
  const typical = bars.map((bar) => (bar.high == null || bar.low == null ? null : (bar.high + bar.low + bar.adj) / 3));
  return finiteSeries(
    strictWindow(typical, period, (slice) => {
      const mean = slice.reduce((sum, value) => sum + value, 0) / slice.length;
      const mad = slice.reduce((sum, value) => sum + Math.abs(value - mean), 0) / slice.length;
      if (mad === 0) return Number.NaN;
      return (slice[slice.length - 1]! - mean) / (0.015 * mad);
    }),
  );
}

function donchian(bars: CalcBar[], period: number) {
  const upper: (number | null)[] = bars.map(() => null);
  const lower: (number | null)[] = bars.map(() => null);
  const width: (number | null)[] = bars.map(() => null);
  bars.forEach((bar, i) => {
    if (i + 1 < period) return;
    const span = rangeWindow(bars, i, period);
    if (span == null) return;
    upper[i] = span.high;
    lower[i] = span.low;
    width[i] = bar.adj === 0 ? null : (span.high - span.low) / bar.adj;
  });
  return { upper, lower, width };
}

function autocorr(adj: number[], period: number): (number | null)[] {
  const change = returns(adj);
  return change.map((_, i) => {
    if (i < period) return null;
    const left: number[] = [];
    const right: number[] = [];
    for (let k = i + 1 - period; k <= i; k++) {
      const current = change[k];
      const lagged = change[k - 1];
      if (current == null || lagged == null) return null;
      left.push(current);
      right.push(lagged);
    }
    return pairsCorr(left, right);
  });
}

function momentSeries(adj: number[], period: number, kind: "skew" | "kurt"): (number | null)[] {
  const change = returns(adj);
  return finiteSeries(
    strictWindow(change, period, (slice) => {
      const mean = slice.reduce((sum, value) => sum + value, 0) / slice.length;
      let second = 0;
      let third = 0;
      let fourth = 0;
      for (const value of slice) {
        const delta = value - mean;
        second += delta ** 2;
        third += delta ** 3;
        fourth += delta ** 4;
      }
      second /= slice.length;
      third /= slice.length;
      fourth /= slice.length;
      if (second <= 1e-24) return Number.NaN;
      if (kind === "skew") return third / Math.sqrt(second) ** 3;
      return fourth / second ** 2 - 3;
    }),
  );
}

function lossQuantile(adj: number[], period: number, q: number): (number | null)[] {
  const loss = returns(adj).map((value) => (value == null ? null : -value));
  return strictWindow(loss, period, (slice) => quantileLinear(slice, q));
}

function conditionalLoss(adj: number[], period: number, q: number): (number | null)[] {
  const loss = returns(adj).map((value) => (value == null ? null : -value));
  return finiteSeries(
    strictWindow(loss, period, (slice) => {
      const level = quantileLinear(slice, q);
      const tail = slice.filter((value) => value >= level);
      if (tail.length === 0) return Number.NaN;
      return tail.reduce((sum, value) => sum + value, 0) / tail.length;
    }),
  );
}

function wma(values: (number | null)[], period: number): (number | null)[] {
  const denom = (period * (period + 1)) / 2;
  return values.map((_, i) => {
    if (i + 1 < period) return null;
    let acc = 0;
    for (let k = 0; k < period; k++) {
      const value = values[i - (period - 1) + k];
      if (value == null) return null;
      acc += value * (k + 1);
    }
    return acc / denom;
  });
}

function demaSeries(values: number[], period: number): (number | null)[] {
  const first = ema(values, period);
  const second = emaNullable(first, period);
  return first.map((value, i) => (value == null || second[i] == null ? null : 2 * value - second[i]!));
}

function temaSeries(values: number[], period: number): (number | null)[] {
  const first = ema(values, period);
  const second = emaNullable(first, period);
  const third = emaNullable(second, period);
  return first.map((value, i) => (value == null || second[i] == null || third[i] == null ? null : 3 * value - 3 * second[i]! + third[i]!));
}

function hmaSeries(values: number[], period: number): (number | null)[] {
  const half = Math.round(period / 2);
  const root = Math.round(Math.sqrt(period));
  const fast = wma(values, half);
  const slow = wma(values, period);
  const raw = fast.map((value, i) => (value == null || slow[i] == null ? null : 2 * value - slow[i]!));
  return wma(raw, root);
}

function aroonSeries(bars: CalcBar[], period: number): { up: (number | null)[]; down: (number | null)[]; osc: (number | null)[] } {
  const up: (number | null)[] = bars.map(() => null);
  const down: (number | null)[] = bars.map(() => null);
  const osc: (number | null)[] = bars.map(() => null);
  for (let i = period; i < bars.length; i++) {
    let highAt = i;
    let lowAt = i;
    let ok = true;
    for (let k = i - period; k <= i; k++) {
      const bar = bars[k]!;
      if (bar.high == null || bar.low == null) {
        ok = false;
        break;
      }
      if (bar.high >= bars[highAt]!.high!) highAt = k;
      if (bar.low <= bars[lowAt]!.low!) lowAt = k;
    }
    if (!ok) continue;
    up[i] = (100 * (period - (i - highAt))) / period;
    down[i] = (100 * (period - (i - lowAt))) / period;
    osc[i] = up[i]! - down[i]!;
  }
  return { up, down, osc };
}

function linregSlope(values: number[], period: number): (number | null)[] {
  return values.map((_, i) => {
    if (i + 1 < period) return null;
    let sumX = 0;
    let sumY = 0;
    let sumXY = 0;
    let sumXX = 0;
    for (let k = 0; k < period; k++) {
      const y = values[i - (period - 1) + k]!;
      sumX += k;
      sumY += y;
      sumXY += k * y;
      sumXX += k * k;
    }
    const denom = period * sumXX - sumX * sumX;
    if (denom === 0) return null;
    return (period * sumXY - sumX * sumY) / denom;
  });
}

function momentumDiff(values: number[], period: number): (number | null)[] {
  return values.map((price, i) => (i < period ? null : price - values[i - period]!));
}

function ppoSeries(values: number[], fast: number, slow: number, signal: number) {
  const fastLine = ema(values, fast);
  const slowLine = ema(values, slow);
  const line = fastLine.map((value, i) => {
    const base = slowLine[i];
    return value == null || base == null || base === 0 ? null : ((value - base) / base) * 100;
  });
  const signalLine = emaNullable(line, signal);
  const hist = line.map((value, i) => (value == null || signalLine[i] == null ? null : value - signalLine[i]!));
  return { line, signalLine, hist };
}

function tsiSeries(values: number[], long: number, short: number): (number | null)[] {
  const change = values.map((price, i) => (i === 0 ? null : price - values[i - 1]!));
  const magnitude = change.map((value) => (value == null ? null : Math.abs(value)));
  const num = emaNullable(emaNullable(change, long), short);
  const den = emaNullable(emaNullable(magnitude, long), short);
  return num.map((value, i) => (value == null || den[i] == null || den[i] === 0 ? null : (100 * value) / den[i]!));
}

function ultimateSeries(bars: CalcBar[], fast: number, mid: number, slow: number): (number | null)[] {
  const bp: (number | null)[] = bars.map(() => null);
  const tr: (number | null)[] = bars.map(() => null);
  for (let i = 1; i < bars.length; i++) {
    const bar = bars[i]!;
    if (bar.high == null || bar.low == null) continue;
    const prev = bars[i - 1]!.adj;
    bp[i] = bar.adj - Math.min(bar.low, prev);
    tr[i] = Math.max(bar.high, prev) - Math.min(bar.low, prev);
  }
  const avg = (period: number, index: number) => {
    if (index + 1 < period) return null;
    let num = 0;
    let den = 0;
    for (let k = index + 1 - period; k <= index; k++) {
      if (bp[k] == null || tr[k] == null) return null;
      num += bp[k]!;
      den += tr[k]!;
    }
    if (den === 0) return null;
    return num / den;
  };
  return bars.map((_, i) => {
    const a = avg(fast, i);
    const b = avg(mid, i);
    const c = avg(slow, i);
    if (a == null || b == null || c == null) return null;
    return (100 * (4 * a + 2 * b + c)) / 7;
  });
}

function awesomeSeries(bars: CalcBar[], fast: number, slow: number): (number | null)[] {
  const mid = bars.map((bar) => (bar.high == null || bar.low == null ? null : (bar.high + bar.low) / 2));
  const a = rollingMean(mid, fast);
  const b = rollingMean(mid, slow);
  return a.map((value, i) => (value == null || b[i] == null ? null : value - b[i]!));
}

function parkinsonSeries(bars: CalcBar[], period: number): (number | null)[] {
  const ln2 = Math.log(2);
  return bars.map((_, i) => {
    if (i + 1 < period) return null;
    let sum = 0;
    for (let k = i + 1 - period; k <= i; k++) {
      const bar = bars[k]!;
      if (bar.high == null || bar.low == null || bar.high <= 0 || bar.low <= 0 || bar.high < bar.low) return null;
      sum += Math.log(bar.high / bar.low) ** 2;
    }
    return Math.sqrt(sum / (4 * period * ln2)) * Math.sqrt(252);
  });
}

function ulcerSeries(values: number[], period: number): (number | null)[] {
  return values.map((_, i) => {
    if (i + 1 < period) return null;
    let peak = -Infinity;
    let ss = 0;
    for (let k = i + 1 - period; k <= i; k++) {
      const price = values[k]!;
      if (!(price > 0)) return null;
      peak = Math.max(peak, price);
      const dd = (price / peak - 1) * 100;
      ss += dd * dd;
    }
    return Math.sqrt(ss / period);
  });
}

function chaikinVolSeries(bars: CalcBar[], period: number): (number | null)[] {
  const span = bars.map((bar) => (bar.high == null || bar.low == null || bar.high < bar.low ? null : bar.high - bar.low));
  const smooth = emaNullable(span, period);
  return smooth.map((value, i) => {
    const prior = i >= period ? smooth[i - period] : null;
    if (value == null || prior == null || prior === 0) return null;
    return ((value - prior) / prior) * 100;
  });
}

function closeStdSeries(values: number[], period: number): (number | null)[] {
  return values.map((_, i) => {
    if (i + 1 < period) return null;
    const sd = stdev(values.slice(i + 1 - period, i + 1));
    return sd == null || sd === 0 ? null : sd;
  });
}

function downsideDevSeries(values: number[], period: number): (number | null)[] {
  const change = returns(values);
  return change.map((_, i) => {
    if (i + 1 < period || period < 2) return null;
    let ss = 0;
    for (let k = i + 1 - period; k <= i; k++) {
      const value = change[k];
      if (value == null) return null;
      const loss = Math.min(value, 0);
      ss += loss * loss;
    }
    return Math.sqrt(ss / (period - 1));
  });
}

function painSeries(values: number[], period: number): (number | null)[] {
  return values.map((_, i) => {
    if (i + 1 < period) return null;
    let peak = -Infinity;
    let sum = 0;
    for (let k = i + 1 - period; k <= i; k++) {
      const price = values[k]!;
      if (!(price > 0)) return null;
      peak = Math.max(peak, price);
      sum += price / peak - 1;
    }
    return sum / period;
  });
}

function burkeSeries(values: number[], period: number): (number | null)[] {
  return values.map((_, i) => {
    if (i + 1 < period) return null;
    const start = values[i - (period - 1)]!;
    const end = values[i]!;
    if (!(start > 0) || !(end > 0)) return null;
    let peak = -Infinity;
    let ss = 0;
    for (let k = i + 1 - period; k <= i; k++) {
      const price = values[k]!;
      peak = Math.max(peak, price);
      const dd = price / peak - 1;
      ss += dd * dd;
    }
    if (ss <= 1e-16) return null;
    const growth = (end / start) ** (252 / (period - 1)) - 1;
    return growth / Math.sqrt(ss);
  });
}

function zScoreSeries(values: number[], period: number): (number | null)[] {
  const mid = sma(values, period);
  return values.map((price, i) => {
    const mean = mid[i];
    if (mean == null) return null;
    const sd = stdev(values.slice(i + 1 - period, i + 1));
    if (sd == null || sd === 0) return null;
    return (price - mean) / sd;
  });
}

function medianSeries(values: number[], period: number): (number | null)[] {
  return values.map((_, i) => {
    if (i + 1 < period) return null;
    const slice = values.slice(i + 1 - period, i + 1).slice().sort((a, b) => a - b);
    const mid = Math.floor(slice.length / 2);
    return slice.length % 2 === 1 ? slice[mid]! : (slice[mid - 1]! + slice[mid]!) / 2;
  });
}

function returnMadSeries(values: number[], period: number): (number | null)[] {
  const change = returns(values);
  return change.map((_, i) => {
    if (i + 1 < period) return null;
    const slice: number[] = [];
    for (let k = i + 1 - period; k <= i; k++) {
      const value = change[k];
      if (value == null) return null;
      slice.push(value);
    }
    const mean = slice.reduce((sum, value) => sum + value, 0) / slice.length;
    return slice.reduce((sum, value) => sum + Math.abs(value - mean), 0) / slice.length;
  });
}

function flatTail(values: number[], period: number): boolean {
  if (values.length < period) return false;
  const slice = values.slice(-period);
  return slice.every((value) => value === slice[0]);
}

function noDrawdown(values: number[], period: number): boolean {
  if (values.length < period) return false;
  let peak = -Infinity;
  for (const price of values.slice(-period)) {
    if (!(price > 0)) return false;
    if (price < peak - 1e-12) return false;
    peak = Math.max(peak, price);
  }
  return true;
}

export function addedSeries(bars: CalcBar[]) {
  const adj = bars.map((bar) => bar.adj);
  const aroon = aroonSeries(bars, 25);
  const ppo = ppoSeries(adj, 12, 26, 9);
  return {
    dema: demaSeries(adj, 20),
    tema: temaSeries(adj, 20),
    hma: hmaSeries(adj, 16),
    aroonUp: aroon.up,
    aroonDown: aroon.down,
    slope: linregSlope(adj, 20),
    momentum: momentumDiff(adj, 10),
    ppoHist: ppo.hist,
    tsi: tsiSeries(adj, 25, 13),
    ultimate: ultimateSeries(bars, 7, 14, 28),
    awesome: awesomeSeries(bars, 5, 34),
    parkinson: parkinsonSeries(bars, 20),
    ulcer: ulcerSeries(adj, 14),
    chaikin: chaikinVolSeries(bars, 10),
    closeStd: closeStdSeries(adj, 20),
    downside: downsideDevSeries(adj, 20),
    pain: painSeries(adj, 60),
    burke: burkeSeries(adj, 60),
    zscore: zScoreSeries(adj, 20),
    median: medianSeries(adj, 20),
    returnMad: returnMadSeries(adj, 20),
  };
}

function addedReading(def: CalcDef, bars: CalcBar[], adj: number[]): Reading[] | null {
  if (def.id === "VIA-VQG-TA-TRD006") {
    const period = def.windows[0] ?? 20;
    return [publish(def, period, " 窗口", "點", demaSeries(adj, period), "先做兩次指數均線，再把第一條乘 2 減掉第二條。", null)];
  }
  if (def.id === "VIA-VQG-TA-TRD007") {
    const period = def.windows[0] ?? 20;
    return [publish(def, period, " 窗口", "點", temaSeries(adj, period), "三次指數均線組合成 3、負 3、1。", null)];
  }
  if (def.id === "VIA-VQG-TA-TRD008") {
    const period = def.windows[0] ?? 16;
    return [publish(def, period, " 窗口", "點", hmaSeries(adj, period), "半窗加權減全窗加權，再對平方根窗做加權。", null)];
  }
  if (def.id === "VIA-VQG-TA-TRD009") {
    const period = def.windows[0] ?? 25;
    if (!hasRange(bars)) return noRange(def, period, [" Up", " Down", " 振盪"]);
    const line = aroonSeries(bars, period);
    return [
      publish(def, period, " Up", "點", line.up, "距窗口內最近一次最高有幾根。", null),
      publish(def, period, " Down", "點", line.down, "距窗口內最近一次最低有幾根。", null),
      publish(def, period, " 振盪", "點", line.osc, "Up 減 Down。", null),
    ];
  }
  if (def.id === "VIA-VQG-TA-TRD010") {
    const period = def.windows[0] ?? 20;
    return [publish(def, period, " 窗口", "點/日", linregSlope(adj, period), "這一段收盤對時間的斜率。正值只表示這一段往上傾斜。", null)];
  }
  if (def.id === "VIA-VQG-TA-MOM008") {
    const period = def.windows[0] ?? 10;
    return [publish(def, period, " 窗口", "點", momentumDiff(adj, period), "今天的調整後收盤減 n 日前。這是點數差，不是漲跌幅。", null)];
  }
  if (def.id === "VIA-VQG-TA-MOM009") {
    const fast = def.params.fast ?? 12;
    const slow = def.params.slow ?? 26;
    const signal = def.params.signal ?? 9;
    const line = ppoSeries(adj, fast, slow, signal);
    return [
      publish(def, null, " 線", "%", line.line, "快線減慢線，再除以慢線。", null),
      publish(def, null, " 訊號", "%", line.signalLine, "線的指數均線。", null),
      publish(def, null, " 柱", "%", line.hist, "線減訊號。和 MACD 的點數柱不是同一個單位。", null),
    ];
  }
  if (def.id === "VIA-VQG-TA-MOM010") {
    const long = def.params.long ?? 25;
    const short = def.params.short ?? 13;
    return [publish(def, null, " 窗口", "點", tsiSeries(adj, long, short), "漲跌點數做兩次指數平滑，再除以絕對值的同樣平滑。", null)];
  }
  if (def.id === "VIA-VQG-TA-MOM011") {
    const fast = def.params.fast ?? 7;
    const mid = def.params.mid ?? 14;
    const slow = def.params.slow ?? 28;
    if (!hasRange(bars)) return noRange(def, slow, [" 窗口"]);
    return [publish(def, slow, " 窗口", "點", ultimateSeries(bars, fast, mid, slow), "7、14、28 日買壓比，權重 4、2、1。", null)];
  }
  if (def.id === "VIA-VQG-TA-MOM012") {
    const fast = def.params.fast ?? 5;
    const slow = def.params.slow ?? 34;
    if (!hasRange(bars)) return noRange(def, slow, [" 窗口"]);
    return [publish(def, slow, " 窗口", "點", awesomeSeries(bars, fast, slow), "中間價的 5 日平均減 34 日平均。", null)];
  }
  if (def.id === "VIA-VQG-TA-VOL007") {
    const period = def.windows[0] ?? 20;
    if (!hasRange(bars)) return noRange(def, period, [" 窗口"]);
    return [publish(def, period, " 窗口", "倍", parkinsonSeries(bars, period), "只用最高和最低。乘上 252 的平方根。", null)];
  }
  if (def.id === "VIA-VQG-TA-VOL008") {
    const period = def.windows[0] ?? 14;
    return [publish(def, period, " 窗口", "點", ulcerSeries(adj, period), "窗口內每日自高點回落的百分比，取方均根。", null)];
  }
  if (def.id === "VIA-VQG-TA-VOL009") {
    const period = def.windows[0] ?? 10;
    if (!hasRange(bars)) return noRange(def, period, [" 窗口"]);
    return [publish(def, period, " 窗口", "%", chaikinVolSeries(bars, period), "高低差的指數均線，和 n 日前那條比。", null)];
  }
  if (def.id === "VIA-VQG-TA-VOL010") {
    const period = def.windows[0] ?? 20;
    const reason = flatTail(adj, period) ? "這一段收盤沒有起伏，留空。" : null;
    return [publish(def, period, " 窗口", "點", closeStdSeries(adj, period), "收盤的標準差，分母是天數。這不是日漲跌的波動。", reason)];
  }
  if (def.id === "VIA-VQG-TA-RSK009") {
    const period = def.windows[0] ?? 20;
    return [publish(def, period, " 窗口", "比例", downsideDevSeries(adj, period), "只累下跌日的平方，分母是天數減 1。不年化。", null)];
  }
  if (def.id === "VIA-VQG-TA-RSK010") {
    const period = def.windows[0] ?? 60;
    return [publish(def, period, " 窗口", "比例", painSeries(adj, period), "窗口內每日相對這段高點的回落，取平均。這是價格路徑，不是策略損益。", null)];
  }
  if (def.id === "VIA-VQG-TA-RSK011") {
    const period = def.windows[0] ?? 60;
    const reason = noDrawdown(adj, period) ? "這一段沒有回撤，留空。不拿它排賺賠。" : null;
    return [publish(def, period, " 窗口", "倍", burkeSeries(adj, period), "價格路徑的年化漲跌，除以窗口內回撤平方和的平方根。不是策略損益。", reason)];
  }
  if (def.id === "VIA-VQG-TA-STA006") {
    const period = def.windows[0] ?? 20;
    const reason = flatTail(adj, period) ? "這一段收盤沒有起伏，留空。" : null;
    return [publish(def, period, " 窗口", "倍", zScoreSeries(adj, period), "收盤減平均，再除以同一段的標準差。標準差分母是天數。", reason)];
  }
  if (def.id === "VIA-VQG-TA-STA007") {
    const period = def.windows[0] ?? 20;
    return [publish(def, period, " 窗口", "點", medianSeries(adj, period), "窗口內調整後收盤的中位數。偶數窗口取中間兩筆的平均。", null)];
  }
  if (def.id === "VIA-VQG-TA-STA008") {
    const period = def.windows[0] ?? 20;
    return [publish(def, period, " 窗口", "比例", returnMadSeries(adj, period), "日漲跌對自己平均的絕對離差，再取平均。", null)];
  }
  return null;
}

function libraryReading(def: CalcDef, bars: CalcBar[], adj: number[]): Reading[] | null {
  if (def.id === "VIA-VQG-TA-TRD005") {
    const period = def.windows[0] ?? 14;
    if (!hasRange(bars)) return noRange(def, period, [" +DI", " -DI", " ADX"]);
    const line = directional(bars, period);
    return [
      publish(def, period, " +DI", "點", line.plusDi, "", null),
      publish(def, period, " -DI", "點", line.minusDi, "", null),
      publish(def, period, " ADX", "點", line.adx, "這是方向的強度，不是上漲或下跌。", null),
    ];
  }
  if (def.id === "VIA-VQG-TA-MOM005") {
    const period = def.windows[0] ?? 14;
    if (!hasRange(bars)) return noRange(def, period, [" RSV", " K", " D"]);
    if (tailEqual(bars, period)) {
      const reason = "最高等於最低，留空。這一段重新暖機。";
      return [" RSV", " K", " D"].map((label) => blank(def, period, label, "點", reason));
    }
    const line = stochastic(bars, period);
    return [
      publish(def, period, " RSV", "點", line.rsv, "最高等於最低就留空，並重新暖機。", null),
      publish(def, period, " K", "點", line.k, "平滑係數是 1/3。這不是 KDJ。", null),
      publish(def, period, " D", "點", line.d, "D 是 K 的再平滑。", null),
    ];
  }
  if (def.id === "VIA-VQG-TA-MOM006") {
    const period = def.windows[0] ?? 20;
    if (!hasRange(bars)) return noRange(def, period, [" 窗口"]);
    const series = cciSeries(bars, period);
    const reason = tailMadZero(bars, period) ? "平均絕對離差是 0，留空。" : null;
    return [publish(def, period, " 窗口", "點", series, "用平均絕對離差，不是標準差。", reason)];
  }
  if (def.id === "VIA-VQG-TA-MOM007") {
    const period = def.windows[0] ?? 14;
    if (!hasRange(bars)) return noRange(def, period, [" 窗口"]);
    const series = williamsR(bars, period);
    const reason = tailEqual(bars, period) ? "最高等於最低，留空。" : null;
    return [publish(def, period, " 窗口", "點", series, "數值在 0 到 -100。越靠近 0，收盤越靠近這一段最高。", reason)];
  }
  if (def.id === "VIA-VQG-TA-VOL004") {
    if (!hasRange(bars)) return noRange(def, 1, [" 當天"]);
    const series = trueRanges(bars);
    return [publish(def, 1, " 當天", "點", series, "第一筆只用最高減最低。之後取三段裡的最大。", null)];
  }
  if (def.id === "VIA-VQG-TA-VOL005") {
    const period = def.windows[0] ?? 20;
    if (!hasRange(bars)) return noRange(def, period, [" 上軌", " 下軌", " 寬度"]);
    const line = donchian(bars, period);
    return [
      publish(def, period, " 上軌", "點", line.upper, "", null),
      publish(def, period, " 下軌", "點", line.lower, "", null),
      publish(def, period, " 寬度", "倍收盤", line.width, "寬度是上下軌差除以調整後收盤。", null),
    ];
  }
  if (def.id === "VIA-VQG-TA-VOL006") {
    const period = def.windows[0] ?? 20;
    const atrPeriod = def.params.atr ?? 14;
    const mult = def.params.mult ?? 2;
    if (!hasRange(bars)) return noRange(def, period, [" 中軌", " 上軌", " 下軌", " 寬度"]);
    const basis = ema(adj, period);
    const atr = wilderSeeded(trueRanges(bars), atrPeriod);
    const upper = basis.map((value, i) => (value == null || atr[i] == null ? null : value + mult * atr[i]!));
    const lower = basis.map((value, i) => (value == null || atr[i] == null ? null : value - mult * atr[i]!));
    const width = basis.map((value, i) => (value == null || value === 0 || atr[i] == null ? null : (2 * mult * atr[i]!) / value));
    return [
      publish(def, period, " 中軌", "點", basis, "中軌用這一引擎的指數均線。", null),
      publish(def, period, " 上軌", "點", upper, "", null),
      publish(def, period, " 下軌", "點", lower, "", null),
      publish(def, period, " 寬度", "倍中軌", width, "波幅用真實波幅的 Wilder 解。", null),
    ];
  }
  if (def.id === "VIA-VQG-TA-FLW007") return noShares(def, def.windows[0] ?? 14, [" 窗口"]);
  if (def.id === "VIA-VQG-TA-FLW008") return noShares(def, def.windows[0] ?? 20, [" 窗口"]);
  if (def.id === "VIA-VQG-TA-FLW009") return noShares(def, null, [" 累計"]);
  if (def.id === "VIA-VQG-TA-FLW010") return noShares(def, def.windows[0] ?? 20, [" 當日", " 滾動"]);
  if (def.id === "VIA-VQG-TA-RSK004") return noBenchmark(def, def.windows[0] ?? 60, " 窗口");
  if (def.id === "VIA-VQG-TA-RSK005") {
    const period = def.windows[0] ?? 60;
    const equity = equityPath(adj);
    const draw = rollingMaxDrawdown(equity, period);
    const series = equity.map((value, i) => {
      const base = i + 1 >= period ? equity[i - (period - 1)] : null;
      const worst = draw[i];
      if (value == null || base == null || base <= 0 || value <= 0 || worst == null || Math.abs(worst) < 1e-12) return null;
      const growth = (value / base) ** (252 / (period - 1)) - 1;
      return growth / Math.abs(worst);
    });
    const worst = tail(draw);
    const reason = worst != null && Math.abs(worst) < 1e-12 ? "這一段最大回撤是 0，留空。不拿它排賺賠。" : null;
    return [publish(def, period, " 窗口", "倍", series, "這是價格路徑，不是策略損益。", reason)];
  }
  if (def.id === "VIA-VQG-TA-RSK006") {
    const period = def.windows[0] ?? 60;
    const equity = equityPath(adj);
    const current = drawdownFromPeak(equity);
    const worst = rollingMaxDrawdown(equity, period);
    return [
      publish(def, null, " 當前", "比例", current, "相對自己一路以來的高點。", null),
      publish(def, period, " 60日", "比例", worst, "只看這 60 日裡面的最大回撤。", null),
    ];
  }
  if (def.id === "VIA-VQG-TA-RSK007" || def.id === "VIA-VQG-TA-RSK008") {
    const period = def.windows[0] ?? 60;
    const q = def.params.confidence ?? 0.95;
    const series = def.id.endsWith("007") ? lossQuantile(adj, period, q) : conditionalLoss(adj, period, q);
    const fact = def.id.endsWith("007")
      ? "損失分位。正值是這一段偏大的單日下跌。負值表示連偏大的日子仍是上漲。"
      : "大於等於損失分位的那些單日，取平均。";
    return [publish(def, period, " 窗口", "比例", series, fact, null)];
  }
  if (def.id === "VIA-VQG-TA-STA001") {
    return def.windows.map((period) => {
      const series = autocorr(adj, period);
      const reason = flatReturns(adj, period) ? "漲跌沒有起伏，留空。" : null;
      return publish(def, period, ` ${period}日`, "倍", series, "漲跌沒有起伏就留空。", reason);
    });
  }
  if (def.id === "VIA-VQG-TA-STA002") return noBenchmark(def, def.windows[0] ?? 60, " 窗口");
  if (def.id === "VIA-VQG-TA-STA003") {
    const period = def.windows[0] ?? 60;
    const paired = autocorr(adj, period).map((value) => (value == null ? null : value ** 2));
    const reason = flatReturns(adj, period) ? "漲跌沒有起伏，留空。" : null;
    return [
      publish(def, period, " 滯後", "倍", paired, "這一解是滯後一期自相關的平方。", reason),
      ...noBenchmark(def, period, " 基準"),
    ];
  }
  if (def.id === "VIA-VQG-TA-STA004" || def.id === "VIA-VQG-TA-STA005") {
    const period = def.windows[0] ?? 60;
    const kind = def.id.endsWith("004") ? "skew" : "kurt";
    const series = momentSeries(adj, period, kind);
    const fact = kind === "skew" ? "三階動差。漲跌沒有起伏就留空。" : "超額峰態，常態是 0。不是樣本峰態的另一套分母。";
    const reason = flatReturns(adj, period) ? "漲跌沒有起伏，留空。" : null;
    return [publish(def, period, " 窗口", "倍", series, fact, reason)];
  }
  const added = addedReading(def, bars, adj);
  if (added) return added;
  return null;
}

function computeIndicator(def: CalcDef, bars: CalcBar[]): Reading[] {
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
  if (def.id === "VIA-VQG-TA-VOL003") {
    const period = def.windows[0] ?? 14;
    const tr = trueRanges(bars);
    const wilder = wilderSeeded(tr, period);
    const simple = rollingMean(tr, period);
    const ratio = simple.map((value, i) => (value == null || bars[i]!.adj === 0 ? null : value / bars[i]!.adj));
    const missing = tr.every((value) => value == null);
    if (missing) {
      const reason = "沒有最高價或最低價，三個解都留空。";
      return [
        blank(def, period, " S1", "點", reason),
        blank(def, period, " S2", "點", reason),
        blank(def, period, " S3", "倍收盤", reason),
      ];
    }
    return [
      reading(def, period, " S1", lastOf(wilder), "點", wilder, "Wilder 平滑，係數是 1 除以天數。"),
      reading(def, period, " S2", lastOf(simple), "點", simple, "簡單平均。窗口缺一天，整段不算。"),
      reading(def, period, " S3", lastOf(ratio), "倍收盤", ratio, "S2 除以調整後收盤，方便不同價位比較。"),
    ];
  }
  if (def.id === "VIA-VQG-TA-FLW005") {
    const period = def.windows[0] ?? 20;
    const clean = cleanTurnover(bars);
    const ratio = ratioOfSums(cleanDirection(bars, clean), clean, period);
    return [
      blank(def, period, " S1", "股", "沒有成交股數，留空。"),
      blank(def, period, " S2", "倍", "沒有成交股數，留空。"),
      reading(def, period, " S3", lastOf(ratio), "倍", ratio, "用扣當沖後的成交值。當沖欄缺了就留空。"),
    ];
  }
  if (def.id === "VIA-VQG-TA-FLW006") {
    const period = def.windows[0] ?? 20;
    const ratio = meanShiftRatio(cleanTurnover(bars), period);
    return [
      blank(def, period, " S1", "倍", "沒有成交股數，留空。"),
      reading(def, period, " S2", lastOf(ratio), "倍", ratio, "近一段扣當沖成交值的平均，除以前一段。大於 1 只表示這一段比較厚。缺了當沖欄就留空。"),
      blank(def, period, " S3", "倍", "中位數要用成交股數，這張表沒有，留空。"),
    ];
  }
  if (def.id === "VIA-VQG-TA-RSK003") {
    const period = def.windows[0] ?? 60;
    const raw = sharpeRaw(adj, period);
    const down = sortinoRaw(adj, period);
    return [
      blank(def, period, " S1", "倍", "沒有利率序列，不把無風險利率寫成 0。留空。"),
      reading(def, period, " S2", lastOf(raw), "倍", raw, "平均日漲跌除以標準差。不年化。標準差分母是天數減 1。"),
      reading(def, period, " S3", lastOf(down), "倍", down, "平均日漲跌除以下跌日的振幅。下跌振幅是 0 就留空。"),
    ];
  }
  const extended = libraryReading(def, bars, adj);
  if (extended) return extended;
  return [reading(def, null, "", null, "", [], "這個編號還沒有接上計算式。")];
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
  atrS3: (number | null)[];
  sharpe60: (number | null)[];
  dema: (number | null)[];
  tema: (number | null)[];
  hma: (number | null)[];
  aroonUp: (number | null)[];
  aroonDown: (number | null)[];
  slope: (number | null)[];
  momentum: (number | null)[];
  ppoHist: (number | null)[];
  tsi: (number | null)[];
  ultimate: (number | null)[];
  awesome: (number | null)[];
  parkinson: (number | null)[];
  ulcer: (number | null)[];
  chaikin: (number | null)[];
  closeStd: (number | null)[];
  downside: (number | null)[];
  pain: (number | null)[];
  burke: (number | null)[];
  zscore: (number | null)[];
  median: (number | null)[];
  returnMad: (number | null)[];
};

export function marketSeries(bars: CalcBar[]): MarketSeries {
  const adj = bars.map((bar) => bar.adj);
  const band = bands(adj, 20, 2, 0);
  const osc = macd(adj, 12, 26, 9);
  const kd = kdj(bars, 9);
  const tr = trueRanges(bars);
  const atrSimple = rollingMean(tr, 14);
  const added = addedSeries(bars);
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
    atrS3: atrSimple.map((value, i) => (value == null || bars[i]!.adj === 0 ? null : value / bars[i]!.adj)),
    sharpe60: sharpeRaw(adj, 60),
    ...added,
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
