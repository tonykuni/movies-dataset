import assert from "node:assert/strict";
import { test } from "node:test";
import { lakesHydraOk, PARQUET_LAKES } from "./duck-catalog.ts";
import {
  VIA_DB_PARTS,
  VIA_DB_ROOT,
  GITHUB_LAKE_ROOT,
  FETCH_PRIORITY,
  decideFetch,
  ingestPlan,
  ingestSqlAll,
  localIngestSql,
  isLocalLane,
  viaDbHydraOk,
  viaDbSealNote,
} from "./via-db-parts.ts";

test("three VIA_db parts map to disjoint px/chip/rest lakes", () => {
  assert.equal(VIA_DB_PARTS.length, 3);
  assert.equal(VIA_DB_ROOT, "C:\\新增資料夾\\新增資料夾");
  assert.ok(VIA_DB_PARTS.every((p) => p.pc.startsWith(VIA_DB_ROOT)));
  assert.ok(VIA_DB_PARTS.some((p) => p.folder === "VIA_db_part1_prices"));
  assert.ok(VIA_DB_PARTS.some((p) => p.folder === "VIA_db_part2_chips"));
  assert.ok(VIA_DB_PARTS.some((p) => p.folder === "VIA_db_part3_rest"));
  assert.equal(viaDbHydraOk(), true);
  assert.equal(lakesHydraOk(), true);
  for (const p of VIA_DB_PARTS) {
    assert.ok(PARQUET_LAKES.some((l) => l.id === p.lake && l.write === p.write), p.id);
    assert.match(p.githubPc, /Github/);
    assert.match(GITHUB_LAKE_ROOT, /Github\\movies-dataset\\data\\vdf/);
  }
});

test("fetch is lake then local then cache then live; never deletes source", () => {
  assert.deepEqual(
    FETCH_PRIORITY.map((r) => r.tier),
    ["LAKE", "LOCAL", "CACHE", "LIVE"],
  );
  assert.equal(decideFetch({ lakeHasYear: true, localHasYear: true, cacheHasYear: true, dualGate: true }), "SKIP");
  assert.equal(decideFetch({ lakeHasYear: false, localHasYear: true, cacheHasYear: true, dualGate: true }), "LOCAL");
  assert.equal(decideFetch({ lakeHasYear: false, localHasYear: false, cacheHasYear: true, dualGate: true }), "CACHE");
  assert.equal(decideFetch({ lakeHasYear: false, localHasYear: false, cacheHasYear: false, dualGate: true }), "LIVE");
  assert.equal(decideFetch({ lakeHasYear: false, localHasYear: false, cacheHasYear: false, dualGate: false }), "SKIP");
  assert.equal(isLocalLane("PX"), true);
  assert.equal(isLocalLane("FRED"), false);
});

test("ingest plan is COPY_ONLY into GitHub hive year and bans union_by_name", () => {
  const plan = ingestPlan(2023, 2026);
  assert.equal(plan.length, 12);
  assert.ok(plan.every((r) => r.action === "PLAN"));
  assert.ok(plan.every((r) => r.note.includes("不刪")));
  assert.ok(plan.some((r) => r.dest.includes("year=2023") && r.dest.includes("px")));
  const sql = localIngestSql(VIA_DB_PARTS[0]!, 2024);
  assert.match(sql, /COPY_ONLY never delete/);
  assert.match(sql, /VIA_db_part1_prices/);
  assert.match(sql, /year=2024\/part-000.parquet/);
  assert.match(sql, /union_by_name=false/);
  assert.doesNotMatch(sql, /union_by_name=true/);
  assert.match(sql, /COMPRESSION ZSTD/);
  const all = ingestSqlAll(2023, 2026);
  assert.match(all, /VIA_db_part2_chips/);
  assert.match(all, /VIA_db_part3_rest/);
  assert.match(viaDbSealNote(), /原件不刪/);
});
