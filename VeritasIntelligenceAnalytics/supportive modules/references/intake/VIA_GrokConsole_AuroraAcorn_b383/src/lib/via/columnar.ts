import type { CpuProfile } from "./cpu.ts";
import { alignUp, profileFromFlags } from "./cpu.ts";
import type { FredRow, Light } from "./types.ts";

export type Obs = {
  seriesId: string;
  title: string;
  category: string;
  frequency: string;
  units: string;
  date: string;
  value: number | null;
  source: FredRow["source"];
  status: Light;
};

export type DictCol = { values: string[]; codes: Uint8Array | Uint16Array };

export type ChunkMeta = {
  start: number;
  end: number;
  minDate: number;
  maxDate: number;
  minSeries: number;
  maxSeries: number;
  bloom: number;
};

export type PartMeta = {
  year: number;
  start: number;
  end: number;
  minDate: number;
  maxDate: number;
};

export type ColumnLake = {
  n: number;
  phys: number;
  width: number;
  align: number;
  isa: CpuProfile["isa"];
  chunkSize: number;
  epoch: number;
  dateOrd: Int32Array;
  series: DictCol;
  value: Float64Array;
  valid: Uint8Array;
  category: DictCol;
  frequency: DictCol;
  units: DictCol;
  title: DictCol;
  source: DictCol;
  status: Uint8Array;
  chunks: ChunkMeta[];
  parts: PartMeta[];
  layout: "year|series|date";
};

const STATUS_CODE: Record<Light, number> = { idle: 0, ok: 1, warn: 2, bad: 3, run: 4, pending: 0 };
const STATUS_OF: Light[] = ["idle", "ok", "warn", "bad", "run"];

export const ARROW_BATCH = 65536;
export const HOT_COLUMNS = ["dateOrd", "series", "value"] as const;

export function dateOrd(iso: string): number {
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return -1;
  return Math.floor(t / 86400000);
}

export function yearOfOrd(ord: number): number {
  if (ord < 0) return -1;
  return new Date(ord * 86400000).getUTCFullYear();
}

function encodeDict(values: string[]): DictCol {
  const index = new Map<string, number>();
  const uniq: string[] = [];
  const raw: number[] = new Array(values.length);
  for (let i = 0; i < values.length; i++) {
    const v = values[i] ?? "";
    let id = index.get(v);
    if (id === undefined) {
      id = uniq.length;
      uniq.push(v);
      index.set(v, id);
    }
    raw[i] = id;
  }
  const codes = uniq.length <= 256 ? new Uint8Array(values.length) : new Uint16Array(values.length);
  for (let i = 0; i < values.length; i++) codes[i] = raw[i];
  return { values: uniq, codes };
}

function padCodes(col: DictCol, phys: number): DictCol {
  if (col.codes.length === phys) return col;
  const codes = col.values.length <= 256 ? new Uint8Array(phys) : new Uint16Array(phys);
  codes.set(col.codes);
  return { values: col.values, codes };
}

function chunkSizeFor(n: number, width: number): number {
  let size = n <= 64 ? Math.max(width, 8) : n <= 4096 ? 64 : 1024;
  size = alignUp(size, Math.max(1, width));
  return Math.min(Math.max(size, width), Math.max(n, width));
}

function strBytes(values: string[]): number {
  let n = 0;
  for (const v of values) n += v.length * 2;
  return n;
}

/** 熱欄靠前、年分區、序列主序（RLE／期末 O(序列)）、字典最小整數、minmax＋bloom。 */
export function encodeLake(obs: Obs[], cpu: CpuProfile = profileFromFlags("")): ColumnLake {
  const sorted = [...obs].sort((a, b) => {
    const da = dateOrd(a.date);
    const db = dateOrd(b.date);
    const ya = yearOfOrd(da) - yearOfOrd(db);
    if (ya !== 0) return ya;
    const s = a.seriesId.localeCompare(b.seriesId);
    if (s !== 0) return s;
    return da - db;
  });
  const n = sorted.length;
  const width = Math.max(1, cpu.f64Width);
  const phys = alignUp(n, width);
  const date = new Int32Array(phys);
  const value = new Float64Array(phys);
  const status = new Uint8Array(phys);
  const valid = new Uint8Array(phys);
  const series: string[] = [];
  const category: string[] = [];
  const frequency: string[] = [];
  const units: string[] = [];
  const title: string[] = [];
  const source: string[] = [];
  date.fill(-1);
  value.fill(Number.NaN);
  let epoch = 2147483647;
  for (let i = 0; i < n; i++) {
    const o = sorted[i];
    date[i] = dateOrd(o.date);
    if (date[i] >= 0 && date[i] < epoch) epoch = date[i];
    value[i] = o.value == null || !Number.isFinite(o.value) ? Number.NaN : o.value;
    status[i] = STATUS_CODE[o.status] ?? 0;
    valid[i] = date[i] >= 0 ? 1 : 0;
    series.push(o.seriesId);
    category.push(o.category);
    frequency.push(o.frequency);
    units.push(o.units);
    title.push(o.title);
    source.push(o.source);
  }
  if (epoch === 2147483647) epoch = 0;
  const seriesCol = padCodes(encodeDict(series), phys);
  const size = chunkSizeFor(phys, width);
  const chunks: ChunkMeta[] = [];
  for (let start = 0; start < phys; start += size) {
    const end = Math.min(phys, start + size);
    let minDate = 2147483647;
    let maxDate = -2147483648;
    let minSeries = 2147483647;
    let maxSeries = -1;
    let bloom = 0;
    for (let i = start; i < end; i++) {
      if (valid[i] === 0) continue;
      if (date[i] < minDate) minDate = date[i];
      if (date[i] > maxDate) maxDate = date[i];
      const sid = seriesCol.codes[i];
      if (sid < minSeries) minSeries = sid;
      if (sid > maxSeries) maxSeries = sid;
      bloom |= 1 << (sid & 31);
    }
    if (maxDate === -2147483648) {
      minDate = -1;
      maxDate = -1;
      minSeries = 0;
      maxSeries = 0;
    }
    chunks.push({ start, end, minDate, maxDate, minSeries, maxSeries, bloom });
  }
  const parts: PartMeta[] = [];
  let pStart = 0;
  while (pStart < n) {
    const year = yearOfOrd(date[pStart]);
    let pEnd = pStart + 1;
    while (pEnd < n && yearOfOrd(date[pEnd]) === year) pEnd += 1;
    let minDate = 2147483647;
    let maxDate = -2147483648;
    for (let i = pStart; i < pEnd; i++) {
      if (valid[i] === 0) continue;
      if (date[i] < minDate) minDate = date[i];
      if (date[i] > maxDate) maxDate = date[i];
    }
    parts.push({
      year,
      start: pStart,
      end: pEnd,
      minDate: maxDate === -2147483648 ? -1 : minDate,
      maxDate: maxDate === -2147483648 ? -1 : maxDate,
    });
    pStart = pEnd;
  }
  return {
    n,
    phys,
    width,
    align: cpu.align,
    isa: cpu.isa,
    chunkSize: size,
    epoch,
    dateOrd: date,
    value,
    status,
    valid,
    series: seriesCol,
    category: padCodes(encodeDict(category), phys),
    frequency: padCodes(encodeDict(frequency), phys),
    units: padCodes(encodeDict(units), phys),
    title: padCodes(encodeDict(title), phys),
    source: padCodes(encodeDict(source), phys),
    chunks,
    parts,
    layout: "year|series|date",
  };
}

export type QueryResult = {
  rows: FredRow[];
  skipped: number;
  scanned: number;
  width: number;
};

function decodeLight(code: number): Light {
  return STATUS_OF[code] ?? "idle";
}

function takeRun(
  last: Map<number, number>,
  prev: Map<number, number>,
  date: Int32Array,
  sid: number,
  best: number,
  second: number,
) {
  if (best < 0) return;
  const old = last.get(sid);
  if (old === undefined) {
    last.set(sid, best);
    if (second >= 0) prev.set(sid, second);
    return;
  }
  last.set(sid, best);
  if (second >= 0 && date[second] >= date[old]) prev.set(sid, second);
  else prev.set(sid, old);
}

/**
 * 年分區謂詞下推 + 序列 run 從尾取 2 點（latest + prev）。
 * JS 不發 ZMM；width 仍是 AVX 契約，padding 列 valid=0。
 */
export function queryLatest(lake: ColumnLake, sinceOrd = 0): QueryResult {
  const last = new Map<number, number>();
  const prev = new Map<number, number>();
  const date = lake.dateOrd;
  const codes = lake.series.codes;
  const valid = lake.valid;
  const n = lake.n;
  let skipped = 0;
  let scanned = 0;

  for (const ch of lake.chunks) {
    if (ch.maxDate < sinceOrd) skipped += 1;
  }

  for (const part of lake.parts) {
    if (part.maxDate < sinceOrd) continue;
    let i = part.start;
    const end = Math.min(part.end, n);
    while (i < end) {
      if (valid[i] === 0) {
        i += 1;
        continue;
      }
      const sid = codes[i];
      let j = i + 1;
      while (j < end && valid[j] === 1 && codes[j] === sid) j += 1;
      let best = -1;
      let second = -1;
      for (let k = j - 1; k >= i && second < 0; k--) {
        if (valid[k] === 0 || date[k] < sinceOrd) continue;
        scanned += 1;
        if (best < 0) best = k;
        else second = k;
      }
      takeRun(last, prev, date, sid, best, second);
      i = j;
    }
  }

  const rows: FredRow[] = [];
  for (const [sid, i] of last) {
    const p = prev.get(sid);
    const lastValue = Number.isFinite(lake.value[i]) ? lake.value[i] : null;
    const prevValue = p !== undefined && Number.isFinite(lake.value[p]) ? lake.value[p] : null;
    const src = lake.source.values[lake.source.codes[i]] as FredRow["source"];
    rows.push({
      seriesId: lake.series.values[sid],
      title: lake.title.values[lake.title.codes[i]],
      category: lake.category.values[lake.category.codes[i]],
      frequency: lake.frequency.values[lake.frequency.codes[i]],
      units: lake.units.values[lake.units.codes[i]],
      lastDate: new Date(lake.dateOrd[i] * 86400000).toISOString().slice(0, 10),
      lastValue,
      change: lastValue != null && prevValue != null ? lastValue - prevValue : null,
      source: src,
      status: decodeLight(lake.status[i]),
    });
  }
  rows.sort((a, b) => a.category.localeCompare(b.category) || a.seriesId.localeCompare(b.seriesId));
  return { rows, skipped, scanned, width: lake.width };
}

export function benchScan(lake: ColumnLake, sinceOrd: number): { rowMs: number; colMs: number; skipRatio: number } {
  const n = lake.n;
  const objects: Array<{ d: number; s: number }> = [];
  for (let i = 0; i < n; i++) objects.push({ d: lake.dateOrd[i], s: lake.series.codes[i] });
  const t0 = performance.now();
  const lastA = new Map<number, number>();
  for (let i = 0; i < objects.length; i++) {
    if (objects[i].d < sinceOrd) continue;
    lastA.set(objects[i].s, i);
  }
  const rowMs = performance.now() - t0;
  void lastA;
  const t1 = performance.now();
  const q = queryLatest(lake, sinceOrd);
  const colMs = performance.now() - t1;
  const skipRatio = lake.chunks.length ? q.skipped / lake.chunks.length : 0;
  return { rowMs, colMs, skipRatio };
}

export function compactBytes(lake: ColumnLake): number {
  const n = lake.n;
  const dict = (col: DictCol) => strBytes(col.values) + n * (col.values.length <= 256 ? 1 : 2);
  return (
    4 +
    n * 2 +
    n * 8 +
    Math.ceil(n / 8) +
    n +
    dict(lake.series) +
    dict(lake.category) +
    dict(lake.frequency) +
    dict(lake.units) +
    dict(lake.title) +
    dict(lake.source) +
    lake.chunks.length * 28 +
    lake.parts.length * 20
  );
}

export function rowObjectBytes(n: number): number {
  return n * (48 + 8 * 28 + 16);
}

export function lakeStats(lake: ColumnLake) {
  const compact = compactBytes(lake);
  const rowB = rowObjectBytes(lake.n);
  return {
    rows: lake.n,
    phys: lake.phys,
    width: lake.width,
    align: lake.align,
    isa: lake.isa,
    chunks: lake.chunks.length,
    chunkSize: lake.chunkSize,
    dictSeries: lake.series.values.length,
    dictCategory: lake.category.values.length,
    hot: HOT_COLUMNS.join(","),
    batchPolicy: ARROW_BATCH,
    partitions: lake.parts.length,
    layout: lake.layout,
    compactBytes: compact,
    rowBytes: rowB,
    storeRatio: rowB ? Math.round((compact / rowB) * 1000) / 1000 : 0,
    codeWidth: lake.series.values.length <= 256 ? 8 : 16,
  };
}
