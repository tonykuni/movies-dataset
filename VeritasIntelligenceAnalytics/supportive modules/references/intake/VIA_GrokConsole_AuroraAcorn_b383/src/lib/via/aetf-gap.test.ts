import assert from "node:assert/strict";
import { test } from "node:test";
import { AETF_ANALYSIS, AETF_SEAL_DIRS, bookIsActiveEquity, cacheUniverseIncomplete, inspectAetfGap } from "./aetf-gap.ts";

test("active ETF analysis has 10 layers; cache universe is incomplete; 00980A in range", () => {
  assert.equal(AETF_ANALYSIS.length, 10);
  assert.equal(cacheUniverseIncomplete(), true);
  assert.equal(bookIsActiveEquity("00980A", "主動野村臺灣優選"), true);
  assert.equal(bookIsActiveEquity("0050", "元大台灣50"), false);
  assert.equal(bookIsActiveEquity("00982D"), false);
  assert.ok(AETF_SEAL_DIRS[0]!.includes("VETF_FINAL_SEAL"));
  assert.ok(AETF_SEAL_DIRS[1]!.includes("VIA_ActiveETF_FINAL"));
  const g = inspectAetfGap({ bookActive: 29 });
  assert.equal(g.rows.find((r) => r.id === "U")?.light, "ok");
  assert.match(g.note, /LIVE 關/);
});
