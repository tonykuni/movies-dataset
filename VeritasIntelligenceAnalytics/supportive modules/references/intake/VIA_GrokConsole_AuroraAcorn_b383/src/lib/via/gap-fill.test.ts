import assert from "node:assert/strict";
import { test } from "node:test";
import { emptyCkpt, applyYearDone } from "./lake-incr.ts";
import { LAKE_START_YEAR, afterCacheCoverage, dualGateNext, inspectGap, liveSeedCounts, nextRoundNeeded, seedCountByYear } from "./gap-fill.ts";

test("start year is 2023 and missing years fill newest first", () => {
  assert.equal(LAKE_START_YEAR, 2023);
  const g = inspectGap(emptyCkpt(2023), { start: 2023, end: 2026, live: false });
  assert.deepEqual(g.jobs.map((j) => j.year), [2026, 2025, 2024, 2023]);
  assert.ok(g.jobs.every((j) => j.action === "FETCH"));
  assert.equal(g.complete, false);
  assert.equal(nextRoundNeeded(g), true);
  assert.match(g.note, /2023/);
  assert.ok(g.copyPlan.includes("year=2023"));
  assert.ok(g.copyPlan.includes("year=2026"));
});

test("CACHE seeds stay on lastDate year; never copy 2026 into 2023", () => {
  const m = seedCountByYear(["2026-08-01", "2026-09-03", "2024-12-31"]);
  assert.equal(m[2026], 2);
  assert.equal(m[2024], 1);
  assert.equal(m[2023] ?? 0, 0);
  const g = inspectGap(emptyCkpt(2023), {
    start: 2023,
    end: 2026,
    live: false,
    seedDates: ["2026-08-01", "2026-09-03"],
  });
  assert.ok((g.rows.find((r) => r.year === 2026)?.seed ?? 0) >= 1);
  assert.equal(g.rows.find((r) => r.year === 2023)?.seed, 0);
  assert.match(g.rows.find((r) => r.year === 2023)?.note ?? "", /不抄新值/);
});

test("LIVE year seeds cover 2023–2025 without inventing from 2026 lastDate", () => {
  const y = liveSeedCounts();
  assert.ok((y[2023] ?? 0) >= 90);
  assert.ok((y[2024] ?? 0) >= 90);
  assert.ok((y[2025] ?? 0) >= 90);
  const g = inspectGap(emptyCkpt(2023), { start: 2023, end: 2026, live: false });
  assert.ok((g.rows.find((r) => r.year === 2023)?.seed ?? 0) >= 90);
  assert.equal(g.rows.find((r) => r.year === 2023)?.light, "ok");
  assert.match(g.rows.find((r) => r.year === 2023)?.note ?? "", /年檔槽保留/);
});

test("skip have-years; cache coverage only seals latest year", () => {
  let ck = emptyCkpt(2023);
  ck = applyYearDone(ck, 2026);
  ck = applyYearDone(ck, 2025);
  const g = inspectGap(ck, { start: 2023, end: 2026, live: true, seriesIds: ["GDP", "UNRATE"] });
  assert.equal(g.jobs.find((j) => j.year === 2026)?.action, "SKIP");
  assert.equal(g.jobs.find((j) => j.year === 2023)?.action, "FETCH");
  const sealed = afterCacheCoverage(ck, 2026, 2, 2);
  assert.ok(sealed.yearsHave.includes(2026));
});

test("dual-gate YES is round consent only; LIVE needs NET+KEY", () => {
  const yes = dualGateNext({ confirmNet: false, roundConsent: true, apiKey: "" });
  assert.equal(yes.gate2Round, true);
  assert.equal(yes.live, false);
  assert.equal(yes.cacheRound, true);
  const live = dualGateNext({
    confirmNet: true,
    roundConsent: true,
    apiKey: "0123456789abcdef0123456789abcdef",
  });
  assert.equal(live.live, true);
  assert.equal(dualGateNext({ confirmNet: true, roundConsent: false, apiKey: "0123456789abcdef0123456789abcdef" }).live, false);
});
