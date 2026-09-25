/** DuckDB 唯一管理所有 parquet 湖。本台產 SQL；母機 via_vdf duckdb 1.1.3 執行。 */
import { ARROW_BATCH } from "./columnar.ts";
import { LAKE_GLOB, LAKE_REL } from "./lake-incr.ts";

export const DUCK_DB = "data/vdf/via_lake.duckdb";

export type ParquetLake = {
  id: string;
  root: string;
  view: string;
  latest: string;
  keys: string[];
  write: string;
};

/** 湖清單。GLSS 是模擬不落盤。L4 仍唯讀 fred；本檔只產 catalog SQL。 */
export const PARQUET_LAKES: ParquetLake[] = [
  { id: "fred", root: LAKE_REL, view: "v_fred_obs", latest: "v_fred_latest", keys: ["year"], write: "fred-cache" },
  { id: "rev", root: "data/vdf/rev", view: "v_rev_obs", latest: "v_rev_latest", keys: ["year"], write: "rev-cache" },
  { id: "aetf", root: "data/vdf/aetf", view: "v_aetf_hold", latest: "v_aetf_latest", keys: ["year"], write: "aetf-cache" },
  { id: "cns", root: "data/vdf/cns", view: "v_cns_obs", latest: "v_cns_latest", keys: ["year", "group"], write: "cns-cache" },
  { id: "px", root: "data/vdf/px", view: "v_px_obs", latest: "v_px_latest", keys: ["year"], write: "px-cache" },
  { id: "chip", root: "data/vdf/chip", view: "v_chip_obs", latest: "v_chip_latest", keys: ["year"], write: "chip-cache" },
  { id: "rest", root: "data/vdf/rest", view: "v_rest_obs", latest: "v_rest_latest", keys: ["year"], write: "rest-cache" },
];

export function lakeGlob(lake: ParquetLake, year?: number): string {
  if (year != null) return `${lake.root}/year=${year}/${LAKE_GLOB}`;
  return `${lake.root}/year=*/${LAKE_GLOB}`;
}

/** 1.1.3：hive year 目錄剪枝 + row-group min/max。union_by_name 會擋 hive prune，同構湖必須關。 */
export const PRED_PUSH = {
  hiveCol: "year",
  rowGroupCols: ["obs_date", "series_id", "ticker", "month"] as const,
  okOps: ["=", "IN", "BETWEEN", ">=", "<="] as const,
  killers: [
    "CAST(",
    "::VARCHAR",
    "date_trunc",
    "strftime",
    "EXTRACT(",
    "year * 100",
    "year*100",
    "last_date >=",
    "last_ym",
    "union_by_name=true",
  ],
} as const;

const HIVE_READ = "hive_partitioning=true, union_by_name=false, hive_types={'year': INTEGER}";

export function yearPred(sinceYear: number, untilYear?: number): string {
  const until = untilYear ?? sinceYear;
  if (until === sinceYear) return `year = ${sinceYear}`;
  if (until < sinceYear) return `year = ${sinceYear}`;
  return `year BETWEEN ${sinceYear} AND ${until}`;
}

export function readParquetArgs(lake: ParquetLake, years?: number[]): string {
  if (years && years.length === 1) {
    return `read_parquet('${lakeGlob(lake, years[0])}', ${HIVE_READ})`;
  }
  if (years && years.length > 1) {
    const list = [...years]
      .sort((a, b) => b - a)
      .map((y) => `'${lakeGlob(lake, y)}'`)
      .join(", ");
    return `read_parquet([${list}], ${HIVE_READ})`;
  }
  return `read_parquet('${lakeGlob(lake)}', ${HIVE_READ})`;
}

export function predPushOk(sql: string): { ok: boolean; note: string } {
  const hit = PRED_PUSH.killers.filter((k) => sql.toLowerCase().includes(k.toLowerCase()));
  const hasYear = /\byear\s*(=|IN|BETWEEN|>=|<=)/i.test(sql);
  if (hit.length) return { ok: false, note: `下推被殺：${hit.join(",")}` };
  if (!hasYear) return { ok: false, note: "缺 hive year 謂詞 · 會開全部 year= 目錄" };
  return { ok: true, note: "hive year 剪枝 + 檔內 min/max" };
}

export function bootSql(): string {
  return [
    "PRAGMA enable_object_cache",
    "SET enable_object_cache=true",
    "SET enable_http_metadata_cache=false",
    "SET preserve_insertion_order=false",
    "SET threads TO 4",
    "SET memory_limit='2GB'",
    `CREATE TABLE IF NOT EXISTS lake_ckpt (lake VARCHAR, year INTEGER, part INTEGER, done_series VARCHAR[], aborted BOOLEAN, updated TIMESTAMP)`,
    `CREATE TABLE IF NOT EXISTS lake_meta (lake VARCHAR, year INTEGER, file_name VARCHAR, row_group_id BIGINT, num_rows BIGINT, row_group_bytes BIGINT, col VARCHAR, stats_min VARCHAR, stats_max VARCHAR, footer_size UBIGINT, warmed_at TIMESTAMP)`,
  ].join(";\n");
}

export function metaFlushSql(): string {
  return ["PRAGMA disable_object_cache", "PRAGMA enable_object_cache", "SET enable_object_cache=true"].join(";\n");
}

export function metaWarmSql(lake: ParquetLake, year?: number): string {
  const glob = lakeGlob(lake, year);
  const yearExpr = year == null ? `CAST(regexp_extract(file_name, 'year=(\\d+)', 1) AS INTEGER)` : String(year);
  return `INSERT INTO lake_meta SELECT '${lake.id}', ${yearExpr}, file_name, row_group_id, row_group_num_rows, row_group_bytes, path_in_schema, stats_min_value, stats_max_value, NULL, now() FROM parquet_metadata('${glob}')`;
}

export function metaInvalidateSql(lake: ParquetLake, year: number): string {
  return `DELETE FROM lake_meta WHERE lake='${lake.id}' AND year=${year}`;
}

export function afterCopyMetaSql(lake: ParquetLake, year: number): string {
  return [metaFlushSql(), metaInvalidateSql(lake, year), metaWarmSql(lake, year)].join(";\n");
}

export function viewSql(lake: ParquetLake): string {
  const read = readParquetArgs(lake);
  if (lake.id === "rev") {
    return [
      `CREATE OR REPLACE VIEW ${lake.view} AS SELECT * FROM ${read}`,
      `CREATE OR REPLACE VIEW ${lake.latest} AS SELECT ticker, year, month, max(rev) AS last_rev FROM ${lake.view} GROUP BY ticker, year, month`,
    ].join(";\n");
  }
  if (lake.id === "aetf") {
    return [
      `CREATE OR REPLACE VIEW ${lake.view} AS SELECT * FROM ${read}`,
      `CREATE OR REPLACE VIEW ${lake.latest} AS SELECT fund, year, max(as_of) AS last_asof FROM ${lake.view} GROUP BY fund, year`,
      `CREATE OR REPLACE VIEW v_aetf_nav AS SELECT year, ticker, as_of, units, d_units, nav, units * nav AS aum, d_units * nav AS flow_1d FROM ${lake.view}`,
    ].join(";\n");
  }
  if (lake.id === "cns") {
    return [
      `CREATE OR REPLACE VIEW ${lake.view} AS SELECT * FROM ${read}`,
      `CREATE OR REPLACE VIEW ${lake.latest} AS SELECT code, year, metric, source, max(as_of) AS last_asof, arg_max(value, as_of) AS last_value FROM ${lake.view} GROUP BY code, year, metric, source`,
    ].join(";\n");
  }
  if (lake.id === "px") {
    return [
      `CREATE OR REPLACE VIEW ${lake.view} AS SELECT * FROM ${read}`,
      `CREATE OR REPLACE VIEW ${lake.latest} AS SELECT ticker, year, max(obs_date) AS last_date, arg_max(close, obs_date) AS last_close FROM ${lake.view} GROUP BY ticker, year`,
    ].join(";\n");
  }
  if (lake.id === "chip") {
    return [
      `CREATE OR REPLACE VIEW ${lake.view} AS SELECT * FROM ${read}`,
      `CREATE OR REPLACE VIEW ${lake.latest} AS SELECT ticker, year, max(obs_date) AS last_date FROM ${lake.view} GROUP BY ticker, year`,
    ].join(";\n");
  }
  if (lake.id === "rest") {
    return [
      `CREATE OR REPLACE VIEW ${lake.view} AS SELECT * FROM ${read}`,
      `CREATE OR REPLACE VIEW ${lake.latest} AS SELECT kind, ticker, year, metric, max(obs_date) AS last_date, arg_max(value, obs_date) AS last_value FROM ${lake.view} GROUP BY kind, ticker, year, metric`,
    ].join(";\n");
  }
  return [
    `CREATE OR REPLACE VIEW ${lake.view} AS SELECT * FROM ${read}`,
    `CREATE OR REPLACE VIEW ${lake.latest} AS SELECT series_id, year, max(obs_date) AS last_date, arg_max(value, obs_date) AS last_value FROM ${lake.view} GROUP BY series_id, year`,
  ].join(";\n");
}

export function allViewSql(): string {
  return PARQUET_LAKES.map(viewSql).join(";\n");
}

export function incrCopySql(lake: ParquetLake, year: number, part = 0): string {
  const n = String(part).padStart(3, "0");
  const dest = `${lake.root}/year=${year}/part-${n}.parquet`;
  const order = lake.id === "rev" ? "ticker, month" : lake.id === "aetf" ? "fund, as_of" : lake.id === "cns" ? "code, section, period, metric" : lake.id === "px" || lake.id === "chip" ? "ticker, obs_date" : lake.id === "rest" ? "kind, ticker, obs_date" : "series_id, obs_date";
  const copy = `COPY (SELECT * FROM ${readParquetArgs(lake, [year])} WHERE ${yearPred(year)} ORDER BY ${order}) TO '${dest}' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE ${ARROW_BATCH}, OVERWRITE_OR_IGNORE)`;
  return `${copy};\n${afterCopyMetaSql(lake, year)}`;
}

export function latestSql(lakeId: string, sinceYear: number, untilYear?: number): string {
  const lake = PARQUET_LAKES.find((l) => l.id === lakeId);
  if (!lake) return `-- unknown lake ${lakeId}`;
  const y = untilYear == null ? `year >= ${sinceYear}` : yearPred(sinceYear, untilYear);
  const span = untilYear == null ? null : Math.abs(untilYear - sinceYear);
  const src = span != null && span <= 3 ? readParquetArgs(lake, yearsClosed(sinceYear, untilYear!)) : lake.view;
  if (lake.id === "rev") {
    return `SELECT ticker, year, month, rev FROM ${src} WHERE ${y} QUALIFY row_number() OVER (PARTITION BY ticker ORDER BY year DESC, month DESC) = 1`;
  }
  if (lake.id === "aetf") {
    return `SELECT fund, year, max(as_of) AS last_asof FROM ${src} WHERE ${y} GROUP BY fund, year`;
  }
  if (lake.id === "cns") {
    return `SELECT code, metric, source, max(as_of) AS last_asof FROM ${src} WHERE ${y} GROUP BY code, metric, source`;
  }
  if (lake.id === "px") {
    return `SELECT ticker, max(obs_date) AS last_date, arg_max(close, obs_date) AS last_close FROM ${src} WHERE ${y} GROUP BY ticker`;
  }
  if (lake.id === "chip") {
    return `SELECT ticker, max(obs_date) AS last_date FROM ${src} WHERE ${y} GROUP BY ticker`;
  }
  if (lake.id === "rest") {
    return `SELECT kind, ticker, metric, max(obs_date) AS last_date, arg_max(value, obs_date) AS last_value FROM ${src} WHERE ${y} GROUP BY kind, ticker, metric`;
  }
  return `SELECT series_id, max(obs_date) AS last_date, arg_max(value, obs_date) AS last_value FROM ${src} WHERE ${y} AND obs_date >= DATE '${sinceYear}-01-01' GROUP BY series_id`;
}

function yearsClosed(since: number, until: number): number[] {
  const a = Math.min(since, until);
  const b = Math.max(since, until);
  const out: number[] = [];
  for (let y = b; y >= a; y--) out.push(y);
  return out;
}

export function explainPruneSql(lake: ParquetLake, sinceYear: number, untilYear: number): string {
  return `EXPLAIN SELECT count(*) FROM ${lake.view} WHERE ${yearPred(sinceYear, untilYear)}`;
}

export function maintainSql(): string {
  return [
    bootSql(),
    allViewSql(),
    ...PARQUET_LAKES.map((l) => metaWarmSql(l)),
    "CHECKPOINT",
    "ANALYZE",
  ].join(";\n");
}

export function duckCatalogNote(): string {
  return `DuckDB ${DUCK_DB} · object_cache parquet metadata · lake_meta 物化 · hive year 緊 glob · ROW_GROUP ${ARROW_BATCH}`;
}

export function lakesHydraOk(): boolean {
  const writes = PARQUET_LAKES.map((l) => l.write);
  return new Set(writes).size === writes.length;
}
