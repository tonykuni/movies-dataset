import assert from "node:assert/strict";
import { test } from "node:test";
import { ARROW_BATCH } from "./columnar.ts";
import {
  PARQUET_LAKES,
  allViewSql,
  afterCopyMetaSql,
  bootSql,
  duckCatalogNote,
  incrCopySql,
  lakesHydraOk,
  latestSql,
  maintainSql,
  metaFlushSql,
  predPushOk,
  viewSql,
} from "./duck-catalog.ts";

test("duckdb manages all parquet lakes with disjoint writes", () => {
  assert.equal(lakesHydraOk(), true);
  assert.ok(PARQUET_LAKES.some((l) => l.id === "fred"));
  assert.ok(PARQUET_LAKES.some((l) => l.id === "rev"));
  assert.ok(PARQUET_LAKES.some((l) => l.id === "cns"));
  assert.ok(PARQUET_LAKES.some((l) => l.id === "px"));
  assert.ok(PARQUET_LAKES.some((l) => l.id === "chip"));
  assert.ok(PARQUET_LAKES.some((l) => l.id === "rest"));
  assert.equal(PARQUET_LAKES.some((l) => l.id === "glss"), false);
});

test("boot views copy and maintain use hive zstd arrow batch", () => {
  assert.match(bootSql(), /PRAGMA enable_object_cache/);
  assert.match(bootSql(), /SET enable_object_cache=true/);
  assert.doesNotMatch(bootSql(), /parquet_metadata_cache/);
  assert.match(bootSql(), /lake_meta/);
  const fred = viewSql(PARQUET_LAKES[0]!);
  assert.match(fred, /v_fred_obs/);
  assert.match(fred, /union_by_name=false/);
  assert.doesNotMatch(fred, /union_by_name=true/);
  assert.match(allViewSql(), /v_rev_obs/);
  assert.match(allViewSql(), /v_aetf_hold/);
  assert.match(allViewSql(), /v_cns_obs/);
  assert.match(allViewSql(), /v_px_obs/);
  assert.match(allViewSql(), /v_chip_obs/);
  assert.match(allViewSql(), /v_rest_obs/);
  const copy = incrCopySql(PARQUET_LAKES[0]!, 2026, 0);
  assert.match(copy, /FORMAT PARQUET/);
  assert.match(copy, /COMPRESSION ZSTD/);
  assert.match(copy, new RegExp(`ROW_GROUP_SIZE ${ARROW_BATCH}`));
  assert.match(copy, /year=2026\/part-000.parquet/);
  assert.match(copy, /DELETE FROM lake_meta WHERE lake='fred' AND year=2026/);
  assert.match(copy, /parquet_metadata\('data\/vdf\/fred\/year=2026\/part-\*\.parquet'\)/);
  assert.match(metaFlushSql(), /disable_object_cache/);
  assert.match(afterCopyMetaSql(PARQUET_LAKES[0]!, 2025), /year=2025/);
  assert.match(copy, /ORDER BY series_id, obs_date/);
  assert.match(latestSql("fred", 2024), /WHERE year >= 2024 AND obs_date >= DATE '2024-01-01'/);
  assert.equal(predPushOk(latestSql("fred", 2024)).ok, true);
  assert.equal(predPushOk(latestSql("rev", 2024)).ok, true);
  assert.equal(predPushOk(latestSql("px", 2024)).ok, true);
  assert.equal(predPushOk(latestSql("chip", 2023, 2026)).ok, true);
  assert.doesNotMatch(latestSql("rev", 2024), /year \* 100/);
  assert.doesNotMatch(allViewSql(), /year \* 100/);
  assert.match(latestSql("fred", 2024, 2026), /year=2026\/part-\*\.parquet/);
  assert.match(latestSql("fred", 2024, 2026), /year BETWEEN 2024 AND 2026/);
  assert.equal(predPushOk("SELECT * FROM v_fred_latest WHERE last_date >= DATE '2024-01-01'").ok, false);
  assert.equal(predPushOk("SELECT * FROM v_fred_obs WHERE CAST(year AS VARCHAR)='2024'").ok, false);
  assert.match(maintainSql(), /CHECKPOINT/);
  assert.match(maintainSql(), /ANALYZE/);
  assert.match(maintainSql(), /parquet_metadata\('data\/vdf\/fred\/year=\*\/part-\*\.parquet'\)/);
  assert.match(duckCatalogNote(), /object_cache parquet metadata/);
});
