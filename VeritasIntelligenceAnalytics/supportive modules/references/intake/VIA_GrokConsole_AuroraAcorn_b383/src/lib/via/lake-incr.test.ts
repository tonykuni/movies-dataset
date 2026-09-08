import assert from "node:assert/strict";
import { test } from "node:test";
import {
  applyAbort,
  applyYearDone,
  duckPruneSql,
  duckScanSql,
  emptyCkpt,
  incrPlan,
  lakeGithubPath,
  nextPartIndex,
  parquetYearPath,
  partitionPolicy,
  pruneYears,
  resumeSeries,
  seriesBatch,
  shouldSplitPart,
  stackFactor,
  yearsNewestFirst,
} from "./lake-incr.ts";

test("years run newest to oldest", () => {
  assert.deepEqual(yearsNewestFirst(2024, 2026), [2026, 2025, 2024]);
});

test("incremental skips have-years and resumes aborted year", () => {
  const ck = emptyCkpt(2024);
  const after = applyYearDone(ck, 2026);
  const halted = applyAbort(after, 2025, ["GDP"]);
  const jobs = incrPlan(2024, 2026, halted);
  assert.equal(jobs.find((j) => j.year === 2026)?.action, "SKIP");
  assert.equal(jobs.find((j) => j.year === 2025)?.action, "RESUME");
  assert.equal(jobs.find((j) => j.year === 2024)?.action, "FETCH");
  const rest = resumeSeries([{ seriesId: "GDP" }, { seriesId: "UNRATE" }], halted.doneSeries);
  assert.deepEqual(rest.map((s) => s.seriesId), ["UNRATE"]);
});

test("batch fetching and duckdb parquet sql", () => {
  assert.equal(seriesBatch(["a", "b", "c", "d", "e"], 2).length, 3);
  const sql = duckScanSql(2024);
  assert.match(sql, /read_parquet\('data\/vdf\/fred\/year=\*\/part-\*\.parquet'/);
  assert.match(sql, /hive_partitioning=true/);
  assert.match(sql, /union_by_name=false/);
  assert.match(sql, /year >= 2024/);
  assert.equal(parquetYearPath(2025), "data/vdf/fred/year=2025/part-000.parquet");
  assert.equal(parquetYearPath(2025, 1), "data/vdf/fred/year=2025/part-001.parquet");
  assert.match(lakeGithubPath(), /part-\*\.parquet/);
});

test("hive year prune skips out-of-range partitions; no series shards", () => {
  const p = partitionPolicy();
  assert.deepEqual(p.keys, ["year"]);
  assert.ok(p.skipKeys.includes("series_id"));
  const { read, skip } = pruneYears([2023, 2024, 2025, 2026], 2024, 2026);
  assert.deepEqual(read, [2026, 2025, 2024]);
  assert.deepEqual(skip, [2023]);
  assert.equal(nextPartIndex([0]), 1);
  assert.equal(shouldSplitPart(10, 100), false);
  assert.equal(shouldSplitPart(250_000, 1), true);
  assert.match(duckPruneSql(2025, 2026), /BETWEEN 2025 AND 2026/);
  assert.match(duckPruneSql(2025, 2026), /parquet_metadata_cache=true/);
});

test("stacked accelerators stay 20 and pipelined", () => {
  const st = stackFactor();
  assert.equal(st.active, 20);
  assert.equal(st.pipeline, true);
  assert.deepEqual(st.layers, ["fetch", "cache", "struct", "compute", "query"]);
  assert.ok(st.planFactor > 8);
});
