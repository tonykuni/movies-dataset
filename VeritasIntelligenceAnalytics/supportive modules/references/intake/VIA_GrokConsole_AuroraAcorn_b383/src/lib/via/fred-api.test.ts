import assert from "node:assert/strict";
import { test } from "node:test";
import { DEFAULT_FRED_API, buildFredObsUrl, canFetchFred, sanitizeFredApi } from "./fred-api.ts";

test("empty API falls back to official observations endpoint", () => {
  const s = sanitizeFredApi("");
  assert.equal(s.ok, true);
  if (s.ok) assert.equal(s.url, DEFAULT_FRED_API);
});

test("rejects non-https", () => {
  const s = sanitizeFredApi("http://api.stlouisfed.org/fred/series/observations");
  assert.equal(s.ok, false);
});

test("rejects embedded credentials", () => {
  const s = sanitizeFredApi("https://user:pass@api.stlouisfed.org/fred/series/observations");
  assert.equal(s.ok, false);
});

test("build puts series_id and api_key as query params", () => {
  const url = buildFredObsUrl(DEFAULT_FRED_API, "DGS10", "abc", "2024-01-01");
  const u = new URL(url);
  assert.equal(u.searchParams.get("series_id"), "DGS10");
  assert.equal(u.searchParams.get("api_key"), "abc");
  assert.equal(u.searchParams.get("file_type"), "json");
  assert.equal(u.searchParams.get("observation_start"), "2024-01-01");
  assert.equal(u.searchParams.get("limit"), "8");
  const wide = buildFredObsUrl(DEFAULT_FRED_API, "UNRATE", "abc", "2023-01-01", 1600);
  assert.equal(new URL(wide).searchParams.get("limit"), "1600");
});

test("dual gate AND blocks live without confirmNet even if key looks valid", () => {
  const g = canFetchFred({ confirmNet: false, apiKey: "a".repeat(32), apiUrl: DEFAULT_FRED_API });
  assert.equal(g.ok, false);
  if (!g.ok) assert.equal(g.mode, "CACHE");
});

test("dual gate opens only when NET and 32-hex and https", () => {
  const g = canFetchFred({ confirmNet: true, apiKey: "ab".repeat(16), apiUrl: DEFAULT_FRED_API });
  assert.equal(g.ok, true);
});
