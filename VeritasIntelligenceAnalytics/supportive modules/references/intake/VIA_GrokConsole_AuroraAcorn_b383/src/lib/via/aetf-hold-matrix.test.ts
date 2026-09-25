import assert from "node:assert/strict";
import { test } from "node:test";
import {
  SEAL_HOLD_FUNDS,
  aggregateHolds,
  costPnl,
  defaultPicked,
  fsUpside,
  fundPickList,
  holdKpis,
  yfUpside,
} from "./aetf-hold-matrix.ts";

test("all-checked 9 funds: TSMC 25.8% 9/9 with cost 519.5 vs adj 560", () => {
  const rows = aggregateHolds([...SEAL_HOLD_FUNDS]);
  assert.equal(rows[0]?.stock, "2330");
  assert.equal(rows[0]?.wgt, 25.8);
  assert.equal(rows[0]?.holdN, 9);
  assert.equal(rows[0]?.cost, 519.5);
  assert.equal(rows[0]?.adj, 560);
  assert.ok((costPnl(519.5, 560) ?? 0) > 0.07);
  assert.ok((fsUpside(560, 611.9) ?? 0) > 0.08);
  assert.ok((fsUpside(560, 611.9) ?? 0) < (696.2 / 560 - 1));
  assert.equal(rows[0]?.yfMedian, 1170);
  assert.ok(Math.abs((yfUpside(918, 1170) ?? 0) - (1170 / 918 - 1)) < 1e-9);
  assert.equal(rows.length, 6);
});

test("single 00980A uses CACHE weights not 25.8 aggregate", () => {
  const rows = aggregateHolds(["00980A"]);
  const tsmc = rows.find((r) => r.stock === "2330");
  assert.ok(tsmc);
  assert.equal(tsmc!.wgt, 28.4);
  assert.equal(tsmc!.action, "單檔持有");
  assert.equal(tsmc!.cost, 519.5);
});

test("29-fund pick list; 20 without holdings stay empty", () => {
  const list = fundPickList();
  assert.equal(list.length, 29);
  assert.equal(list.filter((f) => f.hasHold).length >= 9, true);
  assert.equal(aggregateHolds(["00400A"]).length, 0);
  assert.equal(defaultPicked().length, 9);
  const k = holdKpis(aggregateHolds(defaultPicked()));
  assert.match(k.pe, /15\.6/);
});
