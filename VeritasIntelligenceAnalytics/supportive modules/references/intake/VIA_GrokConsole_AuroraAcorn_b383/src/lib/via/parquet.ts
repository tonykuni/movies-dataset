/** Compact parquet-shaped pages. Year row-groups, footer-free skip by page header. */
import { compactBytes, type ColumnLake } from "./columnar.ts";
import { profileFromFlags } from "./cpu.ts";

export type ParquetPage = {
  year: number;
  n: number;
  offset: number;
  bytes: number;
};

/** DuckDB/Arrow 友善：1MiB 目標、8MiB 上限、列數對齊 64（AVX-512 f64 寬）。年資料小於一頁就不切。 */
export const PARQUET_PAGE = {
  minRows: 4096,
  targetBytes: 1024 * 1024,
  maxBytes: 8 * 1024 * 1024,
  alignRows: 64,
} as const;

export function pageRowCap(rowBytes: number): number {
  const rb = Math.max(1, rowBytes | 0);
  const byTarget = Math.max(1, Math.floor(PARQUET_PAGE.targetBytes / rb));
  const byMax = Math.max(1, Math.floor(PARQUET_PAGE.maxBytes / rb));
  let cap = Math.min(byTarget, byMax);
  cap = Math.max(PARQUET_PAGE.minRows, cap);
  cap = Math.floor(cap / PARQUET_PAGE.alignRows) * PARQUET_PAGE.alignRows;
  return Math.max(PARQUET_PAGE.alignRows, cap);
}

export function pageRowCounts(n: number, rowBytes: number): number[] {
  const rows = Math.max(0, n | 0);
  if (!rows) return [];
  const cap = pageRowCap(rowBytes);
  if (rows <= cap) return [rows];
  const out: number[] = [];
  let left = rows;
  while (left > 0) {
    const take = Math.min(left, cap);
    out.push(take);
    left -= take;
  }
  return out;
}

export type PageSlice = { year: number; start: number; end: number; n: number; bytes: number };

export function planParquetPages(lake: ColumnLake): PageSlice[] {
  const cw = codeWidthOf(lake);
  const rb = rowBytes(cw);
  const out: PageSlice[] = [];
  for (const part of lake.parts) {
    const n = Math.max(0, part.end - part.start);
    let i = part.start;
    for (const take of pageRowCounts(n, rb)) {
      out.push({ year: part.year, start: i, end: i + take, n: take, bytes: 2 + 4 + take * rb });
      i += take;
    }
  }
  return out;
}

export type ParquetBlob = {
  magic: "PAR1";
  layout: "year|series|date";
  rows: number;
  pages: ParquetPage[];
  bytes: number;
  compact: number;
  jsonBytes: number;
  tokenRatio: number;
  dictSeries: number;
};

export type ParquetRead = {
  lake: ColumnLake;
  pagesRead: number;
  pagesSkipped: number;
  rows: number;
};

const MAGIC = [0x50, 0x41, 0x52, 0x31];
const VER = 1;

function u16(n: number): number {
  return n < 0 ? 0 : n > 65535 ? 65535 : n | 0;
}

class Writer {
  buf: number[] = [];
  view = new DataView(new ArrayBuffer(8));
  u8(n: number) {
    this.buf.push(n & 255);
  }
  u16(n: number) {
    this.u8(n);
    this.u8(n >> 8);
  }
  u32(n: number) {
    this.u16(n);
    this.u16(n >> 16);
  }
  i32(n: number) {
    this.u32(n >>> 0);
  }
  f64(n: number) {
    this.view.setFloat64(0, n, true);
    for (let i = 0; i < 8; i++) this.u8(this.view.getUint8(i));
  }
  bytes() {
    return Uint8Array.from(this.buf);
  }
}

class Reader {
  buf: Uint8Array;
  i = 0;
  constructor(buf: Uint8Array, i = 0) {
    this.buf = buf;
    this.i = i;
  }
  u8() {
    return this.buf[this.i++] ?? 0;
  }
  u16() {
    return this.u8() | (this.u8() << 8);
  }
  u32() {
    return this.u16() | (this.u16() << 16);
  }
  i32() {
    return this.u32() | 0;
  }
  f64() {
    const v = new DataView(this.buf.buffer, this.buf.byteOffset + this.i, 8);
    this.i += 8;
    return v.getFloat64(0, true);
  }
  skip(n: number) {
    this.i += n;
  }
  expectMagic() {
    const ok = MAGIC.every((b, k) => this.buf[this.i + k] === b);
    this.i += 4;
    return ok;
  }
}

function codeWidthOf(lake: ColumnLake): 1 | 2 {
  return lake.series.values.length <= 256 ? 1 : 2;
}

function rowBytes(codeWidth: number): number {
  return 2 + codeWidth + 8;
}

export function writeParquetPayload(lake: ColumnLake): Uint8Array {
  const w = new Writer();
  for (const b of MAGIC) w.u8(b);
  w.u8(VER);
  const cw = codeWidthOf(lake);
  w.u8(cw);
  w.i32(lake.epoch);
  w.u32(lake.n);
  w.u32(lake.series.values.length);
  const enc = new TextEncoder();
  for (const s of lake.series.values) {
    const b = enc.encode(s.slice(0, 255));
    w.u8(b.length);
    for (const x of b) w.u8(x);
  }
  const plan = planParquetPages(lake);
  w.u16(u16(plan.length));
  for (const page of plan) {
    w.u16(u16(page.year < 0 ? 0 : page.year));
    w.u32(page.n);
    for (let i = page.start; i < page.end; i++) {
      w.u16(u16(lake.dateOrd[i] - lake.epoch));
      const code = Number(lake.series.codes[i] ?? 0);
      if (cw === 1) w.u8(code);
      else w.u16(code);
      w.f64(Number.isFinite(lake.value[i]) ? lake.value[i] : Number.NaN);
    }
  }
  for (const b of MAGIC) w.u8(b);
  return w.bytes();
}

export function encodeParquet(lake: ColumnLake): ParquetBlob {
  const bin = writeParquetPayload(lake);
  const pages: ParquetPage[] = [];
  let offset = 4 + 1 + 1 + 4 + 4 + 4;
  offset += lake.series.values.reduce((n, s) => n + 1 + Math.min(s.length, 255), 0);
  offset += 2;
  for (const slice of planParquetPages(lake)) {
    pages.push({ year: slice.year, n: slice.n, offset, bytes: slice.bytes });
    offset += slice.bytes;
  }
  const jsonBytes = lake.n * 96;
  return {
    magic: "PAR1",
    layout: lake.layout,
    rows: lake.n,
    pages,
    bytes: bin.length,
    compact: compactBytes(lake),
    jsonBytes,
    tokenRatio: jsonBytes ? Math.round((bin.length / jsonBytes) * 1000) / 1000 : 0,
    dictSeries: lake.series.values.length,
  };
}

export function parquetSavesTokens(blob: ParquetBlob): boolean {
  return blob.bytes < blob.jsonBytes && blob.pages.length > 0;
}

function dictFrom(values: string[]): { values: string[]; codes: Uint8Array } {
  const uniq: string[] = [];
  const index = new Map<string, number>();
  const codes = new Uint8Array(values.length);
  for (let i = 0; i < values.length; i++) {
    const v = values[i] ?? "";
    let id = index.get(v);
    if (id === undefined) {
      id = uniq.length;
      uniq.push(v);
      index.set(v, id);
    }
    codes[i] = id;
  }
  return { values: uniq, codes };
}

export function readParquetPayload(buf: Uint8Array, minYear = 0): ParquetRead {
  const r = new Reader(buf);
  if (!r.expectMagic()) throw new Error("PAR1 magic");
  const ver = r.u8();
  if (ver !== VER) throw new Error(`PAR1 ver ${ver}`);
  const cw = r.u8() === 2 ? 2 : 1;
  const epoch = r.i32();
  r.u32();
  const dictN = r.u32();
  const dec = new TextDecoder();
  const series: string[] = [];
  for (let i = 0; i < dictN; i++) {
    const len = r.u8();
    const slice = buf.subarray(r.i, r.i + len);
    r.skip(len);
    series.push(dec.decode(slice));
  }
  const pageCount = r.u16();
  const date: number[] = [];
  const value: number[] = [];
  const codes: number[] = [];
  let pagesRead = 0;
  let pagesSkipped = 0;
  const parts: ColumnLake["parts"] = [];
  for (let p = 0; p < pageCount; p++) {
    const year = r.u16();
    const n = r.u32();
    const body = n * rowBytes(cw);
    if (year < minYear) {
      r.skip(body);
      pagesSkipped += 1;
      continue;
    }
    const start = date.length;
    for (let i = 0; i < n; i++) {
      date.push(epoch + r.u16());
      codes.push(cw === 1 ? r.u8() : r.u16());
      value.push(r.f64());
    }
    parts.push({
      year,
      start,
      end: date.length,
      minDate: date[start] ?? -1,
      maxDate: date[date.length - 1] ?? -1,
    });
    pagesRead += 1;
  }
  if (!r.expectMagic()) throw new Error("PAR1 footer");
  const n = date.length;
  const dateOrd = new Int32Array(n);
  const val = new Float64Array(n);
  const valid = new Uint8Array(n);
  const status = new Uint8Array(n);
  const scodes = dictN <= 256 ? new Uint8Array(n) : new Uint16Array(n);
  for (let i = 0; i < n; i++) {
    dateOrd[i] = date[i] ?? -1;
    val[i] = value[i] ?? Number.NaN;
    valid[i] = 1;
    status[i] = 1;
    scodes[i] = codes[i] ?? 0;
  }
  const sidNames = codes.map((c) => series[c] ?? "");
  const cat = dictFrom(sidNames.map(() => "Rates"));
  const cpu = profileFromFlags("scalar");
  const chunks = parts.map((p) => ({
    start: p.start,
    end: p.end,
    minDate: p.minDate,
    maxDate: p.maxDate,
    minSeries: 0,
    maxSeries: Math.max(0, dictN - 1),
    bloom: 0xffffffff,
  }));
  const lake: ColumnLake = {
    n,
    phys: n,
    width: 1,
    align: cpu.align,
    isa: "scalar",
    chunkSize: Math.max(1, n),
    epoch,
    dateOrd,
    series: { values: series, codes: scodes },
    value: val,
    valid,
    category: cat,
    frequency: dictFrom(sidNames.map(() => "M")),
    units: dictFrom(sidNames.map(() => "x")),
    title: dictFrom(sidNames),
    source: dictFrom(sidNames.map(() => "VDF_CACHE")),
    status,
    chunks,
    parts,
    layout: "year|series|date",
  };
  return { lake, pagesRead, pagesSkipped, rows: n };
}
