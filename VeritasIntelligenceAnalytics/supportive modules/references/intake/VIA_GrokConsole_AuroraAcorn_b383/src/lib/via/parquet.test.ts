import assert from "node:assert/strict";
import { test } from "node:test";
import { encodeLake, queryLatest } from "./columnar.ts";
import { profileFromFlags } from "./cpu.ts";
import { encodeParquet, pageRowCap, pageRowCounts, parquetSavesTokens, readParquetPayload, writeParquetPayload } from "./parquet.ts";
import type { Obs } from "./columnar.ts";

function obs(n: number, year = 2024): Obs[] {
  const out: Obs[] = [];
  for (let i = 0; i < n; i++) {
    out.push({
      seriesId: i % 3 === 0 ? "DGS10" : i % 3 === 1 ? "UNRATE" : "CPIAUCSL",
      title: "t",
      category: "Rates",
      frequency: "M",
      units: "x",
      date: `${year}-${String((i % 12) + 1).padStart(2, "0")}-01`,
      value: i + year,
      source: "VDF_CACHE",
      status: "ok",
    });
  }
  return out;
}

test("parquet pages beat JSON token cost", () => {
  const lake = encodeLake(obs(24), profileFromFlags("avx2", "phys"));
  const blob = encodeParquet(lake);
  assert.equal(blob.magic, "PAR1");
  assert.ok(blob.pages.length >= 1);
  assert.ok(parquetSavesTokens(blob));
  assert.ok(blob.bytes < blob.jsonBytes);
  const bin = writeParquetPayload(lake);
  assert.equal(bin.length, blob.bytes);
  assert.equal(bin[0], 0x50);
  assert.equal(bin[1], 0x41);
  assert.equal(bin[bin.length - 1], 0x31);
});

test("year page skip + round-trip latest counts", () => {
  const lake = encodeLake([...obs(12, 2023), ...obs(12, 2024)], profileFromFlags("avx2", "phys"));
  const bin = writeParquetPayload(lake);
  const all = readParquetPayload(bin, 0);
  assert.equal(all.pagesRead, 2);
  assert.equal(all.pagesSkipped, 0);
  const late = readParquetPayload(bin, 2024);
  assert.equal(late.pagesRead, 1);
  assert.equal(late.pagesSkipped, 1);
  assert.ok(late.rows < all.rows);
  const qLake = queryLatest(lake, Math.floor(Date.UTC(2024, 0, 1) / 86400000));
  const qPage = queryLatest(late.lake, Math.floor(Date.UTC(2024, 0, 1) / 86400000));
  assert.equal(qPage.rows.length, qLake.rows.length);
  for (const row of qLake.rows) {
    const hit = qPage.rows.find((r) => r.seriesId === row.seriesId);
    assert.equal(hit?.lastValue, row.lastValue);
  }
});

test("page size caps at ~1MiB aligned 64 rows; small years stay one page", () => {
  const rb = 11;
  const cap = pageRowCap(rb);
  assert.equal(cap % 64, 0);
  assert.ok(cap >= 4096);
  assert.ok(cap * rb <= 8 * 1024 * 1024);
  assert.deepEqual(pageRowCounts(24, rb), [24]);
  const big = pageRowCounts(cap * 2 + 10, rb);
  assert.equal(big.length, 3);
  assert.equal(big[0], cap);
  assert.equal(big[2], 10);
});
