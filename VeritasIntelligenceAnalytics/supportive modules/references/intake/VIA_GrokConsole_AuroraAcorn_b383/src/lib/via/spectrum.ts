/** Dual／N 源共識 → 同一列寬表。TARGET PRICE＝Median，不用 Mean。LIVE 關。 */
import { CNS_SEED, type CnsSeed } from "./consensus.ts";

export const TARGET_STAT = "median" as const;

export type SpecStats = {
  mean: number;
  median: number;
  low: number;
  high: number;
  std: number | null;
  n: number | null;
  asof: string | null;
};

export type SpecEpsRow = { period: string; label: string; eps: number | null; est?: boolean };

export type SpecWide = {
  code: string;
  title: string;
  unit: string;
  price: number;
  asof: string;
  fs: SpecStats;
  yf: SpecStats;
  gapMean: number;
  gapPct: number;
  gapMed: number;
  eps: SpecEpsRow[];
  per: Array<number | null>;
};

export function targetPrice(s: Pick<SpecStats, "median">): number {
  return s.median;
}

export function targetUpside(price: number, target: number): number | null {
  if (!price) return null;
  return target / price - 1;
}

export function statsOf(v: SpecStats | number[] | Record<string, unknown>): SpecStats {
  if (Array.isArray(v)) {
    const xs = [...v].map(Number).filter((n) => Number.isFinite(n)).sort((a, b) => a - b);
    const mean = xs.reduce((s, n) => s + n, 0) / (xs.length || 1);
    const mid = Math.floor(xs.length / 2);
    const median = xs.length % 2 ? xs[mid]! : (xs[mid - 1]! + xs[mid]!) / 2;
    const m = mean;
    const std = xs.length > 1 ? Math.sqrt(xs.reduce((s, n) => s + (n - m) ** 2, 0) / xs.length) : 0;
    return { mean, median, low: xs[0] ?? 0, high: xs[xs.length - 1] ?? 0, std, n: xs.length, asof: null };
  }
  const d = v as Record<string, unknown>;
  return {
    mean: Number(d.mean),
    median: Number(d.median),
    low: Number(d.low),
    high: Number(d.high),
    std: d.std == null ? null : Number(d.std),
    n: d.n == null ? null : Number(d.n),
    asof: d.asof == null ? null : String(d.asof),
  };
}

export function fillEps(rows: SpecEpsRow[], max = 4): SpecEpsRow[] {
  const out = rows.map((r) => ({ ...r }));
  const labels = ["今年 N", "明年 N+1", "後年 N+2", "N+3"];
  while (out.length < max) {
    const i = out.length;
    const prev = out.map((r) => r.eps).filter((e): e is number => e != null);
    const g = prev.length >= 2 && prev[prev.length - 2] ? prev[prev.length - 1]! / prev[prev.length - 2]! : 1;
    const last = prev[prev.length - 1];
    out.push({
      period: `FY${i}`,
      label: labels[i] ?? `N+${i}`,
      eps: last == null ? null : Number((last * g).toFixed(2)),
      est: true,
    });
  }
  return out.slice(0, max);
}

export function perOf(price: number, eps: number | null): number | null {
  if (eps == null || eps === 0) return null;
  return price / eps;
}

export function packSpectrum(cfg: {
  title?: string;
  unit?: string;
  price: number;
  asof?: string;
  code?: string;
  sources: Record<string, SpecStats | number[] | Record<string, unknown>>;
  eps?: { title?: string; rows: SpecEpsRow[] };
}): SpecWide {
  const names = Object.keys(cfg.sources);
  const fs = statsOf(cfg.sources[names[0] ?? "FactSet"] ?? { mean: 0, median: 0, low: 0, high: 0 });
  const yf = statsOf(cfg.sources[names[1] ?? "YFinance"] ?? { mean: 0, median: 0, low: 0, high: 0 });
  const eps = fillEps(cfg.eps?.rows ?? []);
  return {
    code: cfg.code ?? "2330",
    title: cfg.title ?? "Consensus Spectrum",
    unit: cfg.unit ?? "TWD",
    price: cfg.price,
    asof: cfg.asof ?? "",
    fs,
    yf,
    gapMean: yf.mean - fs.mean,
    gapPct: fs.median ? ((yf.median - fs.median) / fs.median) * 100 : 0,
    gapMed: yf.median - fs.median,
    eps,
    per: eps.map((r) => perOf(cfg.price, r.eps)),
  };
}

/** 附件 spectrum_input.json 樣本 · 與持股估均價不同價尺，寬表單列不混進成本列。 */
export const SPECTRUM_SAMPLE = packSpectrum({
  code: "2330",
  title: "2330 TSMC Target Price Consensus - Dual Spectrum",
  unit: "TWD",
  price: 140,
  asof: "2026-09-07",
  sources: {
    FactSet: { mean: 155, median: 152, low: 120, high: 185, n: 24, asof: "2026-09-05" },
    YFinance: [110, 135, 140, 148, 150, 155, 160, 168, 190],
  },
  eps: {
    title: "FactSet Consensus EPS",
    rows: [
      { period: "FY0", label: "今年 N", eps: 9.8 },
      { period: "FY1", label: "明年 N+1", eps: 11.5 },
      { period: "FY2", label: "後年 N+2", eps: 14.0 },
    ],
  },
});

export function spectrumCells(w: SpecWide): string[] {
  const n1 = w.eps.find((r) => r.period === "FY1") ?? w.eps[1];
  const per1 = n1 ? perOf(w.price, n1.eps) : null;
  const tFs = targetPrice(w.fs);
  const tYf = targetPrice(w.yf);
  const up = targetUpside(w.price, tFs);
  return [
    w.code,
    w.price.toFixed(0),
    w.fs.low.toFixed(0),
    tFs.toFixed(0),
    w.fs.mean.toFixed(1),
    w.fs.high.toFixed(0),
    w.fs.n == null ? "—" : String(w.fs.n),
    w.yf.low.toFixed(0),
    tYf.toFixed(0),
    w.yf.mean.toFixed(1),
    w.yf.high.toFixed(0),
    w.yf.n == null ? "—" : String(w.yf.n),
    `${w.gapMed >= 0 ? "+" : ""}${w.gapMed.toFixed(2)} (${w.gapPct >= 0 ? "+" : ""}${w.gapPct.toFixed(2)}%)`,
    up == null ? "—" : `${(up * 100).toFixed(1)}%`,
    n1?.eps == null ? "—" : n1.eps.toFixed(2),
    per1 == null ? "—" : `${per1.toFixed(1)}x`,
  ];
}

export function wideFromCns(s: CnsSeed): SpecWide | null {
  if (s.medianFs == null || s.medianYf == null || s.priceFs == null) return null;
  if (s.currencyFs !== s.currencyYf) return null;
  return packSpectrum({
    code: s.code,
    title: `${s.code} ${s.name}`,
    unit: s.currencyFs,
    price: s.priceFs,
    asof: s.asOf,
    sources: {
      FactSet: {
        mean: s.meanFs,
        median: s.medianFs ?? s.meanFs,
        low: s.lowFs ?? s.meanFs,
        high: s.highFs ?? s.meanFs,
        n: s.analystsFs,
        asof: s.asOf,
      },
      YFinance: {
        mean: s.meanYf,
        median: s.medianYf ?? s.meanYf,
        low: s.lowYf ?? s.meanYf,
        high: s.highYf ?? s.meanYf,
        n: s.analystsYf,
        asof: s.asOf,
      },
    },
    eps: {
      rows: [{ period: "FY1", label: "明年 N+1", eps: s.epsFs }],
    },
  });
}

export function specWideRows(): SpecWide[] {
  const cns = CNS_SEED.map(wideFromCns).filter((w): w is SpecWide => w != null);
  return [SPECTRUM_SAMPLE, ...cns];
}

export const SPEC_COLS = [
  "代號", "市價",
  "FS Low", "FS TARGET Med", "FS Mean", "FS High", "nFS",
  "YF Low", "YF TARGET Med", "YF Mean", "YF High", "nYF",
  "Med 缺口", "潛在(Med)", "N+1 EPS", "N+1 PER",
];
