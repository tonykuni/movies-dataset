import assert from "node:assert/strict";
import { test } from "node:test";
import { benchScan, compactBytes, dateOrd, encodeLake, queryLatest, rowObjectBytes, yearOfOrd, type Obs } from "./columnar.ts";
import { profileFromFlags } from "./cpu.ts";

function seed(nSeries = 26, months = 36): Obs[] {
  const cats = ["Rates", "Inflation", "Labor", "FX"];
  const out: Obs[] = [];
  for (let s = 0; s < nSeries; s++) {
    const id = `S${String(s).padStart(2, "0")}`;
    for (let m = 0; m < months; m++) {
      const y = 2024 + Math.floor(m / 12);
      const mo = (m % 12) + 1;
      out.push({
        seriesId: id,
        title: id,
        category: cats[s % cats.length],
        frequency: "M",
        units: "Index",
        date: `${y}-${String(mo).padStart(2, "0")}-01`,
        value: 100 + s + m * 0.1,
        source: "VDF_CACHE",
        status: "ok",
      });
    }
  }
  return out;
}

test("encode is year-partitioned, series-major, dictionary, chunked with minmax", () => {
  const lake = encodeLake(seed(8, 24));
  assert.equal(lake.n, 8 * 24);
  assert.equal(lake.series.values.length, 8);
  assert.ok(lake.chunks.length >= 1);
  assert.ok(lake.parts.length >= 2);
  assert.equal(lake.layout, "year|series|date");
  assert.equal(lake.series.codes.BYTES_PER_ELEMENT, 1);
  let i = 0;
  while (i < lake.n) {
    const sid = lake.series.codes[i];
    const y = yearOfOrd(lake.dateOrd[i]);
    let last = -1;
    while (i < lake.n && lake.series.codes[i] === sid && yearOfOrd(lake.dateOrd[i]) === y) {
      if (lake.valid[i]) {
        assert.ok(lake.dateOrd[i] >= last);
        last = lake.dateOrd[i];
      }
      i += 1;
    }
  }
  for (const ch of lake.chunks) {
    if (ch.maxDate >= 0) assert.ok(ch.maxDate >= ch.minDate);
  }
});

test("queryLatest returns one row per series with change", () => {
  const lake = encodeLake(seed(5, 12));
  const q = queryLatest(lake, 0);
  assert.equal(q.rows.length, 5);
  for (const r of q.rows) {
    assert.equal(typeof r.lastValue, "number");
    assert.ok(r.change != null);
    assert.ok(r.lastDate.startsWith("2024") || r.lastDate.startsWith("2025"));
  }
  assert.ok(q.scanned <= 5 * 2);
});

test("minmax skips early chunks when since is late", () => {
  const lake = encodeLake(seed(10, 48));
  const since = dateOrd("2026-01-01");
  const q = queryLatest(lake, since);
  assert.ok(q.skipped >= 1);
  assert.ok(q.scanned < lake.n);
  assert.equal(q.rows.length, 10);
});

test("column scan is not slower than object scan on 1k+ rows", () => {
  const lake = encodeLake(seed(20, 60));
  const since = dateOrd("2025-01-01");
  const b = benchScan(lake, since);
  assert.ok(b.colMs >= 0);
  assert.ok(b.rowMs >= 0);
  assert.ok(lake.n >= 1000);
});

test("avx512-shaped kernel matches scalar results and pads width", () => {
  const rows = seed(9, 17);
  const scalar = encodeLake(rows, profileFromFlags("sse4_1"));
  const wide = encodeLake(rows, profileFromFlags("avx2 avx512f"));
  assert.equal(scalar.width, 1);
  assert.equal(wide.width, 8);
  assert.equal(wide.phys % 8, 0);
  assert.ok(wide.phys >= wide.n);
  const a = queryLatest(scalar, 0);
  const b = queryLatest(wide, 0);
  assert.equal(a.rows.length, b.rows.length);
  for (let i = 0; i < a.rows.length; i++) {
    assert.equal(a.rows[i].seriesId, b.rows[i].seriesId);
    assert.equal(a.rows[i].lastValue, b.rows[i].lastValue);
    assert.equal(a.rows[i].lastDate, b.rows[i].lastDate);
  }
});

test("compact parquet shape is far smaller than row objects", () => {
  const lake = encodeLake(seed(20, 60));
  const c = compactBytes(lake);
  const r = rowObjectBytes(lake.n);
  assert.ok(c < r / 4);
  assert.ok(lake.parts.length >= 3);
});
