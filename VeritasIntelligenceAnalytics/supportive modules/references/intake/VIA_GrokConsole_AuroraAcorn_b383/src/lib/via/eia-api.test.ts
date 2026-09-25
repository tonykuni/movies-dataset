import assert from "node:assert/strict";
import { test } from "node:test";
import { DEFAULT_EIA_API, EIA_LIVE_ENABLED, canFetchEia, eiaKeyFormat, sanitizeEiaApi } from "./eia-api.ts";

test("EIA LIVE stays off until explicitly enabled", () => {
  assert.equal(EIA_LIVE_ENABLED, false);
});

test("empty EIA API falls back to official v2", () => {
  const s = sanitizeEiaApi("");
  assert.equal(s.ok, true);
  if (s.ok) assert.equal(s.url, DEFAULT_EIA_API);
});

test("rejects non-https and non-eia host", () => {
  assert.equal(sanitizeEiaApi("http://api.eia.gov/v2").ok, false);
  assert.equal(sanitizeEiaApi("https://example.com/v2").ok, false);
  assert.equal(sanitizeEiaApi("https://user:pass@api.eia.gov/v2").ok, false);
});

test("EIA key is not FRED 32-hex rule", () => {
  assert.equal(eiaKeyFormat("a".repeat(32)), true);
  assert.equal(eiaKeyFormat("AbCdEfGhIjKlMnOpQr1234"), true);
  assert.equal(eiaKeyFormat("short"), false);
  assert.equal(eiaKeyFormat(""), false);
});

test("filled key + NET still CACHE while LIVE flag off", () => {
  const g = canFetchEia({ confirmNet: true, apiKey: "eiaDemoKeyValue12", apiUrl: DEFAULT_EIA_API });
  assert.equal(g.ok, false);
  if (!g.ok) {
    assert.equal(g.mode, "CACHE");
    assert.match(g.reason, /以後再測/);
  }
});
