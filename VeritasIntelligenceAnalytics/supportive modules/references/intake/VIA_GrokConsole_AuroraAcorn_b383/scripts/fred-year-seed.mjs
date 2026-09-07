/** LIVE 年終種子。KEY 只讀 process.env.FRED_API_KEY，不寫檔。 */
import { writeFileSync } from "node:fs";
import { FRED_CATALOG } from "../src/lib/via/catalog.ts";

const KEY = String(process.env.FRED_API_KEY ?? "").trim();
const START = process.env.VIA_START_YEAR || "2023";
const API = "https://api.stlouisfed.org/fred/series/observations";

if (!/^[a-f0-9]{32}$/i.test(KEY)) {
  console.log(JSON.stringify({ ok: false, reason: "FRED_API_KEY missing or not 32 hex" }));
  process.exit(1);
}

async function pull(id) {
  const u = new URL(API);
  u.searchParams.set("series_id", id);
  u.searchParams.set("api_key", KEY);
  u.searchParams.set("file_type", "json");
  u.searchParams.set("observation_start", `${START}-01-01`);
  u.searchParams.set("sort_order", "asc");
  u.searchParams.set("limit", "20000");
  const r = await fetch(u, { signal: AbortSignal.timeout(20000) });
  const j = await r.json();
  if (!r.ok || j.error_code) return { id, ok: false, err: j.error_code || r.status, byYear: {} };
  const byYear = {};
  for (const o of j.observations ?? []) {
    if (o.value === "." || o.value == null) continue;
    const y = String(o.date).slice(0, 4);
    const v = Number(o.value);
    if (!Number.isFinite(v)) continue;
    byYear[y] = { date: o.date, value: v };
  }
  return { id, ok: true, err: null, byYear };
}

const ids = FRED_CATALOG.map((s) => s.seriesId);
const out = [];
for (let i = 0; i < ids.length; i += 6) {
  const chunk = ids.slice(i, i + 6);
  out.push(...(await Promise.all(chunk.map(pull))));
}

const years = {};
let ok = 0;
for (const row of out) {
  if (row.ok) ok += 1;
  for (const y of Object.keys(row.byYear)) years[y] = (years[y] ?? 0) + 1;
}

const payload = {
  start: Number(START),
  fetchedAt: new Date().toISOString(),
  catalog: ids.length,
  liveOk: ok,
  years,
  rows: out.filter((r) => r.ok).map((r) => ({ id: r.id, years: r.byYear })),
  fail: out.filter((r) => !r.ok).map((r) => r.id),
};

writeFileSync("src/lib/via/fred-year-seeds.json", JSON.stringify(payload, null, 0));
console.log(JSON.stringify({ ok: true, liveOk: ok, catalog: ids.length, years, fail: payload.fail.length }));
