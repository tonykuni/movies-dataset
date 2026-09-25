import assert from "node:assert/strict";
import { test } from "node:test";
import { SPECTRUM_SAMPLE, packSpectrum, spectrumCells, statsOf, targetPrice, targetUpside } from "./spectrum.ts";

test("YF samples flatten to stats; one ticker one row with FS+YF+EPS", () => {
  const yf = statsOf([110, 135, 140, 148, 150, 155, 160, 168, 190]);
  assert.equal(yf.n, 9);
  assert.equal(yf.low, 110);
  assert.equal(yf.high, 190);
  assert.ok(Math.abs(yf.mean - 150.666) < 0.01);
  assert.equal(yf.median, 150);
  const w = SPECTRUM_SAMPLE;
  assert.equal(w.fs.mean, 155);
  assert.equal(targetPrice(w.fs), 152);
  assert.equal(w.fs.n, 24);
  assert.equal(w.gapMed, -2);
  const up = targetUpside(w.price, targetPrice(w.fs));
  assert.ok(Math.abs((up ?? 0) - 0.08571) < 0.001);
  assert.equal(w.eps[3]?.est, true);
  assert.equal(w.eps[3]?.eps, 17.04);
  const cells = spectrumCells(w);
  assert.equal(cells[0], "2330");
  assert.equal(cells.length, 16);
  assert.equal(cells[3], "152");
  assert.match(cells[13], /8\.6%/);
  assert.match(cells[15], /12\.2x/);
});

test("third source still packs first two onto the same row", () => {
  const w = packSpectrum({
    price: 140,
    sources: {
      FactSet: { mean: 155, median: 152, low: 120, high: 185, n: 24 },
      YFinance: { mean: 150, median: 150, low: 110, high: 190, n: 9 },
      Bloomberg: { mean: 160, median: 158, low: 130, high: 200, n: 12 },
    },
    eps: { rows: [{ period: "FY0", label: "今年 N", eps: 9.8 }] },
  });
  assert.equal(w.fs.mean, 155);
  assert.equal(w.yf.mean, 150);
});
