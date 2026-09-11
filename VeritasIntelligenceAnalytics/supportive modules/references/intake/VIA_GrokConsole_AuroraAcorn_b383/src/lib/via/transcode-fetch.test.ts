import assert from "node:assert/strict";
import { test } from "node:test";
import { parseFilename } from "./vrn.ts";
import { cacheFetchKey, runTranscodeFetchTest } from "./transcode-fetch.ts";

test("auto transcode fetch: 10 cases green, never fetch wrong board", () => {
  const out = runTranscodeFetchTest();
  assert.equal(out.fail, 0, out.rows.filter((r) => r.light === "bad").map((r) => r.note).join(" | "));
  assert.equal(out.ok, true);
  assert.equal(out.total, 10);
  assert.ok(out.fetchOk >= 9);
  const bad = out.rows.find((r) => r.id === "BAD2330");
  assert.equal(bad?.fetchKey, "2330.TW");
  assert.equal(bad?.recovered, true);
  assert.equal(bad?.fetched, true);
  const tpex = out.rows.find((r) => r.id === "BAD5347");
  assert.equal(tpex?.fetchKey, "5347.TWO");
  assert.equal(tpex?.recovered, true);
  assert.equal(out.rows.some((r) => r.fetchKey.endsWith(".TWO") && r.core === "2330"), false);
});

test("cache fetch key ignores wrong suffix", () => {
  assert.equal(cacheFetchKey("2330.TWO")?.key, "2330.TW");
  assert.equal(cacheFetchKey("5347.TW")?.key, "5347.TWO");
  assert.equal(cacheFetchKey("0050.TW"), null);
});

test("VRN filename uses recovered YF not raw .TWO", () => {
  const p = parseFilename("券商-2330.TWO-台積-1141202.pdf");
  assert.equal(p.ticker, "2330");
  assert.equal(p.yfinance, "2330.TW");
  assert.equal(p.yfinanceTwo, "—");
  assert.equal(p.tickerRecovered, true);
});
