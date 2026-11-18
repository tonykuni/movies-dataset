import "@tanstack/react-start/server-only";
import { existsSync, mkdirSync } from "node:fs";
import path from "node:path";
import { DuckDBInstance, type DuckDBAppender, type DuckDBConnection } from "@duckdb/node-api";
import type { CalcBar, CalcDef, Reading } from "./engine";
import { VQG, type VqgDef } from "./registry";
import type { SignalDef } from "./signals";
import type { TestRow } from "./test-engine";
import type { VersionNote } from "./types";

const DIR = path.join(process.cwd(), "data", "vqg");
const DB_PATH = path.join(DIR, "vqg.duckdb");

export const PARQUET = {
  indicators: path.join(DIR, "indicators.parquet"),
  bars: path.join(DIR, "bars.parquet"),
  readings: path.join(DIR, "readings.parquet"),
  signals: path.join(DIR, "signals.parquet"),
  tests: path.join(DIR, "tests.parquet"),
  versions: path.join(DIR, "versions.parquet"),
};

type GlobalDb = typeof globalThis & { __vqgConn?: Promise<DuckDBConnection> };

function sqlPath(file: string): string {
  return file.replaceAll("'", "''");
}

async function loadIndicators(conn: DuckDBConnection) {
  if (!existsSync(PARQUET.indicators)) return;
  await conn.run("DELETE FROM vqg_indicator");
  const described = await conn.runAndReadAll(`DESCRIBE SELECT * FROM read_parquet('${sqlPath(PARQUET.indicators)}')`);
  const names = new Set(described.getRowObjectsJson().map((row) => String(row.column_name)));
  const col = (name: string) => (names.has(name) ? name : "''");
  const version = names.has("version") ? "version" : "1";
  const note = names.has("change_note") ? "change_note" : "''";
  await conn.run(`
    INSERT INTO vqg_indicator
    SELECT id, category, theme, name, formula, params, windows, signal_rule, tv_ref, updated_on,
           ${col("purpose")} AS purpose, ${col("advantage")} AS advantage,
           ${col("disadvantage")} AS disadvantage, ${col("upgrade")} AS upgrade, ${col("naming")} AS naming,
           ${version} AS version, ${note} AS change_note
    FROM read_parquet('${sqlPath(PARQUET.indicators)}')
  `);
}

async function loadReadings(conn: DuckDBConnection) {
  if (!existsSync(PARQUET.readings)) return;
  await conn.run("DELETE FROM vqg_reading");
  const described = await conn.runAndReadAll(`DESCRIBE SELECT * FROM read_parquet('${sqlPath(PARQUET.readings)}')`);
  const names = new Set(described.getRowObjectsJson().map((row) => String(row.column_name)));
  const version = names.has("version") ? "version" : "1";
  await conn.run(`
    INSERT INTO vqg_reading
    SELECT id, theme, name, window_n, label, value, unit, percentile, signal, as_of, ${version} AS version
    FROM read_parquet('${sqlPath(PARQUET.readings)}')
  `);
}

async function loadVersions(conn: DuckDBConnection) {
  if (!existsSync(PARQUET.versions)) return;
  await conn.run("DELETE FROM vqg_indicator_version");
  await conn.run(`INSERT INTO vqg_indicator_version SELECT * FROM read_parquet('${sqlPath(PARQUET.versions)}')`);
}

async function loadParquet(conn: DuckDBConnection, table: string, file: string) {
  if (!existsSync(file)) return;
  await conn.run(`DELETE FROM ${table}`);
  await conn.run(`INSERT INTO ${table} SELECT * FROM read_parquet('${sqlPath(file)}')`);
}

async function loadBars(conn: DuckDBConnection) {
  if (!existsSync(PARQUET.bars)) return;
  await conn.run("DELETE FROM vqg_bar");
  const described = await conn.runAndReadAll(`DESCRIBE SELECT * FROM read_parquet('${sqlPath(PARQUET.bars)}')`);
  const names = new Set(described.getRowObjectsJson().map((row) => String(row.column_name)));
  const high = names.has("high") ? "high" : "NULL";
  const low = names.has("low") ? "low" : "NULL";
  const turnover = names.has("turnover") ? "turnover" : "NULL";
  const daytrade = names.has("daytrade") ? "daytrade" : "NULL";
  const activeEtf = names.has("active_etf") ? "active_etf" : "NULL";
  await conn.run(`
    INSERT INTO vqg_bar
    SELECT date, adj, deducted, foreign_net, trust_net, dealer_net, ${high} AS high, ${low} AS low,
           ${turnover} AS turnover, ${daytrade} AS daytrade, ${activeEtf} AS active_etf
    FROM read_parquet('${sqlPath(PARQUET.bars)}')
  `);
}

async function open(): Promise<DuckDBConnection> {
  mkdirSync(DIR, { recursive: true });
  const instance = await DuckDBInstance.create(DB_PATH);
  const conn = await instance.connect();
  await conn.run(`
    CREATE TABLE IF NOT EXISTS vqg_indicator (
      id VARCHAR PRIMARY KEY,
      category VARCHAR NOT NULL,
      theme VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      formula VARCHAR NOT NULL,
      params VARCHAR NOT NULL,
      windows VARCHAR NOT NULL,
      signal_rule VARCHAR NOT NULL,
      tv_ref VARCHAR NOT NULL,
      updated_on VARCHAR NOT NULL,
      purpose VARCHAR NOT NULL,
      advantage VARCHAR NOT NULL,
      disadvantage VARCHAR NOT NULL,
      upgrade VARCHAR NOT NULL,
      naming VARCHAR NOT NULL,
      version INTEGER NOT NULL,
      change_note VARCHAR NOT NULL
    );
    CREATE TABLE IF NOT EXISTS vqg_bar (
      date VARCHAR PRIMARY KEY,
      adj DOUBLE NOT NULL,
      deducted DOUBLE,
      foreign_net DOUBLE,
      trust_net DOUBLE,
      dealer_net DOUBLE,
      high DOUBLE,
      low DOUBLE,
      turnover DOUBLE,
      daytrade DOUBLE,
      active_etf DOUBLE
    );
    CREATE TABLE IF NOT EXISTS vqg_reading (
      id VARCHAR NOT NULL,
      theme VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      window_n INTEGER,
      label VARCHAR NOT NULL,
      value DOUBLE,
      unit VARCHAR NOT NULL,
      percentile DOUBLE,
      signal VARCHAR NOT NULL,
      as_of VARCHAR NOT NULL,
      version INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS vqg_indicator_version (
      id VARCHAR NOT NULL,
      version INTEGER NOT NULL,
      formula VARCHAR NOT NULL,
      params VARCHAR NOT NULL,
      windows VARCHAR NOT NULL,
      change_note VARCHAR NOT NULL,
      updated_on VARCHAR NOT NULL,
      PRIMARY KEY (id, version)
    );
    CREATE TABLE IF NOT EXISTS vqg_signal (
      id VARCHAR PRIMARY KEY,
      indicator_id VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      meaning VARCHAR NOT NULL,
      test_question VARCHAR NOT NULL,
      evidence_rule VARCHAR NOT NULL,
      noise_rule VARCHAR NOT NULL,
      saturation_rule VARCHAR NOT NULL
    );
    CREATE TABLE IF NOT EXISTS vqg_test (
      id VARCHAR NOT NULL,
      checks INTEGER NOT NULL,
      present_n INTEGER NOT NULL,
      absent_n INTEGER NOT NULL,
      insufficient_n INTEGER NOT NULL,
      noise_count INTEGER NOT NULL,
      saturation_count INTEGER NOT NULL,
      latest_status VARCHAR NOT NULL,
      latest_detail VARCHAR NOT NULL,
      noise_now VARCHAR NOT NULL,
      saturation_now VARCHAR NOT NULL,
      as_of VARCHAR NOT NULL
    );
  `);
  await conn.run("ALTER TABLE vqg_bar ADD COLUMN IF NOT EXISTS high DOUBLE");
  await conn.run("ALTER TABLE vqg_bar ADD COLUMN IF NOT EXISTS low DOUBLE");
  await conn.run("ALTER TABLE vqg_bar ADD COLUMN IF NOT EXISTS turnover DOUBLE");
  await conn.run("ALTER TABLE vqg_bar ADD COLUMN IF NOT EXISTS daytrade DOUBLE");
  await conn.run("ALTER TABLE vqg_bar ADD COLUMN IF NOT EXISTS active_etf DOUBLE");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS purpose VARCHAR");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS advantage VARCHAR");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS disadvantage VARCHAR");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS upgrade VARCHAR");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS naming VARCHAR");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS version INTEGER");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS change_note VARCHAR");
  await conn.run("ALTER TABLE vqg_reading ADD COLUMN IF NOT EXISTS version INTEGER");
  await loadIndicators(conn);
  await loadVersions(conn);
  await loadBars(conn);
  await loadReadings(conn);
  await loadParquet(conn, "vqg_signal", PARQUET.signals);
  await loadParquet(conn, "vqg_test", PARQUET.tests);
  return conn;
}

async function ensureLibraries(conn: DuckDBConnection) {
  await conn.run("ALTER TABLE vqg_bar ADD COLUMN IF NOT EXISTS high DOUBLE");
  await conn.run("ALTER TABLE vqg_bar ADD COLUMN IF NOT EXISTS low DOUBLE");
  await conn.run("ALTER TABLE vqg_bar ADD COLUMN IF NOT EXISTS turnover DOUBLE");
  await conn.run("ALTER TABLE vqg_bar ADD COLUMN IF NOT EXISTS daytrade DOUBLE");
  await conn.run("ALTER TABLE vqg_bar ADD COLUMN IF NOT EXISTS active_etf DOUBLE");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS purpose VARCHAR");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS advantage VARCHAR");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS disadvantage VARCHAR");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS upgrade VARCHAR");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS naming VARCHAR");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS version INTEGER");
  await conn.run("ALTER TABLE vqg_indicator ADD COLUMN IF NOT EXISTS change_note VARCHAR");
  await conn.run("ALTER TABLE vqg_reading ADD COLUMN IF NOT EXISTS version INTEGER");
  await conn.run(`
    CREATE TABLE IF NOT EXISTS vqg_indicator_version (
      id VARCHAR NOT NULL,
      version INTEGER NOT NULL,
      formula VARCHAR NOT NULL,
      params VARCHAR NOT NULL,
      windows VARCHAR NOT NULL,
      change_note VARCHAR NOT NULL,
      updated_on VARCHAR NOT NULL,
      PRIMARY KEY (id, version)
    );
  `);
  await conn.run(`
    CREATE TABLE IF NOT EXISTS vqg_signal (
      id VARCHAR PRIMARY KEY,
      indicator_id VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      meaning VARCHAR NOT NULL,
      test_question VARCHAR NOT NULL,
      evidence_rule VARCHAR NOT NULL,
      noise_rule VARCHAR NOT NULL,
      saturation_rule VARCHAR NOT NULL
    );
    CREATE TABLE IF NOT EXISTS vqg_test (
      id VARCHAR NOT NULL,
      checks INTEGER NOT NULL,
      present_n INTEGER NOT NULL,
      absent_n INTEGER NOT NULL,
      insufficient_n INTEGER NOT NULL,
      noise_count INTEGER NOT NULL,
      saturation_count INTEGER NOT NULL,
      latest_status VARCHAR NOT NULL,
      latest_detail VARCHAR NOT NULL,
      noise_now VARCHAR NOT NULL,
      saturation_now VARCHAR NOT NULL,
      as_of VARCHAR NOT NULL
    );
  `);
}

export async function connection(): Promise<DuckDBConnection> {
  const g = globalThis as GlobalDb;
  g.__vqgConn ??= open().catch((error) => {
    g.__vqgConn = undefined;
    throw error;
  });
  const conn = await g.__vqgConn;
  await ensureLibraries(conn);
  return conn;
}

async function exportTable(conn: DuckDBConnection, table: string, file: string) {
  await conn.run(`COPY ${table} TO '${sqlPath(file)}' (FORMAT PARQUET)`);
  await conn.run("CHECKPOINT");
}

type Cell = string | number | null;
type CellKind = "text" | "int" | "double";

function appendCell(appender: DuckDBAppender, value: Cell, kind: CellKind) {
  if (typeof value !== "number") {
    if (value == null) appender.appendNull();
    else appender.appendVarchar(value);
    return;
  }
  if (!Number.isFinite(value)) {
    appender.appendNull();
    return;
  }
  if (kind === "int") appender.appendInteger(Math.trunc(value));
  else if (kind === "double") appender.appendDouble(value);
  else appender.appendVarchar(String(value));
}

async function appendRows(conn: DuckDBConnection, table: string, kinds: CellKind[], rows: Cell[][]) {
  if (rows.length === 0) return;
  const appender = await conn.createAppender(table);
  try {
    for (const row of rows) {
      for (let i = 0; i < kinds.length; i++) appendCell(appender, row[i] ?? null, kinds[i]!);
      appender.endRow();
    }
    appender.flushSync();
  } finally {
    appender.closeSync();
  }
}

export async function saveIndicators(defs: VqgDef[]): Promise<VersionNote[]> {
  const conn = await connection();
  const notes: VersionNote[] = [];
  const prior = new Map<string, { formula: string; params: string; windows: string }>();
  const stored = await conn.runAndReadAll("SELECT id, version, formula, params, windows FROM vqg_indicator_version");
  for (const row of stored.getRowObjectsJson()) {
    prior.set(`${String(row.id)}@${Number(row.version)}`, {
      formula: String(row.formula),
      params: String(row.params),
      windows: String(row.windows),
    });
  }
  await conn.run("DELETE FROM vqg_indicator");
  const rows: Cell[][] = [];
  for (const def of defs) {
    const params = JSON.stringify(def.params);
    const windows = def.windows.join(",");
    const found = prior.get(`${def.id}@${def.version}`);
    const same = found != null && found.formula === def.formula && found.params === params && found.windows === windows;
    if (!found) {
      await conn.run(
      `INSERT INTO vqg_indicator_version VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [def.id, def.version, def.formula, params, windows, def.changeNote, def.updatedOn],
    );
      notes.push({ id: def.id, name: def.name, version: def.version, status: "新增", detail: def.changeNote });
    } else if (same) {
      notes.push({ id: def.id, name: def.name, version: def.version, status: "沿用", detail: "公式、參數和天數沒有變。" });
    } else {
      notes.push({
        id: def.id,
        name: def.name,
        version: def.version,
        status: "衝突",
        detail: "這個版本已經存過不同的公式或參數。舊版不覆蓋，請把版本加一。",
      });
    }
    rows.push([
      def.id,
      def.category,
      def.theme,
      def.name,
      def.formula,
      params,
      windows,
      def.signalRule,
      def.tvRef,
      def.updatedOn,
      def.purpose,
      def.advantage,
      def.disadvantage,
      def.upgrade,
      def.naming,
      def.version,
      def.changeNote,
    ]);
  }
  await appendRows(conn, "vqg_indicator", [
    "text", "text", "text", "text", "text", "text", "text", "text", "text", "text",
    "text", "text", "text", "text", "text", "int", "text",
  ], rows);
  await exportTable(conn, "vqg_indicator", PARQUET.indicators);
  await exportTable(conn, "vqg_indicator_version", PARQUET.versions);
  return notes;
}

export async function saveBars(bars: CalcBar[]) {
  const conn = await connection();
  await conn.run("DELETE FROM vqg_bar");
  const rows: Cell[][] = [];
  for (const bar of bars) {
    if (!Number.isFinite(bar.adj) || bar.adj <= 0) continue;
    rows.push([
      bar.date,
      bar.adj,
      bar.deducted,
      bar.foreign,
      bar.trust,
      bar.dealer,
      bar.high,
      bar.low,
      bar.turnover,
      bar.daytrade,
      bar.activeEtf,
    ]);
  }
  await appendRows(
    conn,
    "vqg_bar",
    ["text", "double", "double", "double", "double", "double", "double", "double", "double", "double", "double"],
    rows,
  );
  await exportTable(conn, "vqg_bar", PARQUET.bars);
}

export async function readIndicators(): Promise<Array<VqgDef & CalcDef>> {
  const conn = await connection();
  const reader = await conn.runAndReadAll(
    "SELECT id, category, theme, name, formula, params, windows, signal_rule, tv_ref, updated_on, purpose, advantage, disadvantage, upgrade, naming, version, change_note FROM vqg_indicator ORDER BY id",
  );
  return reader.getRowObjectsJson().map((row) => {
    const id = String(row.id);
    const spec = VQG.find((item) => item.id === id);
    return {
      id,
      category: String(row.category),
      theme: String(row.theme),
      name: String(row.name),
      naming: row.naming === "正式" ? "正式" : "自訂",
      formula: String(row.formula),
      params: JSON.parse(String(row.params ?? "{}")) as Record<string, number>,
      windows: String(row.windows ?? "")
        .split(",")
        .map((item) => Number(item))
        .filter((item) => Number.isFinite(item) && item > 0),
      purpose: String(row.purpose ?? ""),
      advantage: String(row.advantage ?? ""),
      disadvantage: String(row.disadvantage ?? ""),
      upgrade: String(row.upgrade ?? ""),
      signalRule: String(row.signal_rule),
      tvRef: String(row.tv_ref),
      updatedOn: String(row.updated_on),
      version: Number(row.version ?? 1),
      changeNote: String(row.change_note ?? ""),
      inputs: spec?.inputs ?? [],
      solutions: spec?.solutions ?? [],
      evidence: spec?.evidence ?? "",
    };
  });
}

function num(value: unknown): number | null {
  if (value == null || value === "") return null;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

export async function readBars(): Promise<CalcBar[]> {
  const conn = await connection();
  const reader = await conn.runAndReadAll(
    "SELECT date, adj, high, low, deducted, turnover, daytrade, active_etf, foreign_net, trust_net, dealer_net FROM vqg_bar WHERE adj > 0 ORDER BY date",
  );
  return reader.getRowObjectsJson().map((row) => ({
    date: String(row.date),
    adj: num(row.adj) ?? 0,
    high: num(row.high),
    low: num(row.low),
    deducted: num(row.deducted),
    turnover: num(row.turnover),
    daytrade: num(row.daytrade),
    activeEtf: num(row.active_etf),
    foreign: num(row.foreign_net),
    trust: num(row.trust_net),
    dealer: num(row.dealer_net),
  }));
}

export async function saveReadings(readings: Reading[], asOf: string) {
  const conn = await connection();
  const versions = new Map<string, number>();
  const found = await conn.runAndReadAll("SELECT id, version FROM vqg_indicator");
  for (const row of found.getRowObjectsJson()) versions.set(String(row.id), Number(row.version ?? 1));
  const seen = new Set<string>();
  await conn.run("DELETE FROM vqg_reading WHERE version IS NULL");
  const pending: Array<{ row: Reading; version: number }> = [];
  for (const row of readings) {
    const version = versions.get(row.id) ?? 1;
    seen.add(`${row.id.replaceAll("'", "''")}@${version}`);
    pending.push({ row, version });
  }
  if (seen.size > 0) {
    const list = [...seen].map((key) => `'${key}'`).join(",");
    await conn.run(`DELETE FROM vqg_reading WHERE id || '@' || CAST(version AS VARCHAR) IN (${list})`);
  }
  await appendRows(
    conn,
    "vqg_reading",
    ["text", "text", "text", "int", "text", "double", "text", "double", "text", "text", "int"],
    pending.map(({ row, version }) => [
      row.id,
      row.theme,
      row.name,
      row.window,
      row.label,
      row.value,
      row.unit,
      row.percentile,
      row.signal,
      asOf,
      version,
    ]),
  );
  await exportTable(conn, "vqg_reading", PARQUET.readings);
}

export type ThemeCount = { theme: string; indicators: number; filled: number };

export async function themeCounts(): Promise<ThemeCount[]> {
  const conn = await connection();
  const reader = await conn.runAndReadAll(`
    SELECT r.theme AS theme,
           count(DISTINCT r.id) AS indicators,
           count(r.value) AS filled
    FROM vqg_reading r
    JOIN vqg_indicator i ON i.id = r.id AND i.version = r.version
    GROUP BY r.theme
    ORDER BY r.theme
  `);
  return reader.getRowObjectsJson().map((row) => ({
    theme: String(row.theme),
    indicators: Number(row.indicators),
    filled: Number(row.filled),
  }));
}

export async function saveSignals(defs: SignalDef[]) {
  const conn = await connection();
  await conn.run("DELETE FROM vqg_signal");
  await appendRows(
    conn,
    "vqg_signal",
    ["text", "text", "text", "text", "text", "text", "text", "text"],
    defs.map((def) => [
      def.id,
      def.indicatorId,
      def.name,
      def.meaning,
      def.testQuestion,
      def.evidenceRule,
      def.noiseRule,
      def.saturationRule,
    ]),
  );
  await exportTable(conn, "vqg_signal", PARQUET.signals);
}

export async function readSignals(): Promise<SignalDef[]> {
  const conn = await connection();
  const reader = await conn.runAndReadAll(
    "SELECT id, indicator_id, name, meaning, test_question, evidence_rule, noise_rule, saturation_rule FROM vqg_signal ORDER BY id",
  );
  return reader.getRowObjectsJson().map((row) => ({
    id: String(row.id),
    indicatorId: String(row.indicator_id),
    name: String(row.name),
    meaning: String(row.meaning),
    testQuestion: String(row.test_question),
    evidenceRule: String(row.evidence_rule),
    noiseRule: String(row.noise_rule),
    saturationRule: String(row.saturation_rule),
  }));
}

export async function saveTests(rows: TestRow[], asOf: string) {
  const conn = await connection();
  await conn.run("DELETE FROM vqg_test");
  await appendRows(
    conn,
    "vqg_test",
    ["text", "int", "int", "int", "int", "int", "int", "text", "text", "text", "text", "text"],
    rows.map((row) => [
      row.id,
      row.checks,
      row.present,
      row.absent,
      row.insufficient,
      row.noiseCount,
      row.saturationCount,
      row.latestStatus,
      row.latestDetail,
      row.noiseNow,
      row.saturationNow,
      asOf,
    ]),
  );
  await exportTable(conn, "vqg_test", PARQUET.tests);
}

export async function readTests(): Promise<TestRow[]> {
  const conn = await connection();
  const signals = await readSignals();
  const byId = new Map(signals.map((row) => [row.id, row]));
  const reader = await conn.runAndReadAll(
    "SELECT id, checks, present_n, absent_n, insufficient_n, noise_count, saturation_count, latest_status, latest_detail, noise_now, saturation_now FROM vqg_test ORDER BY id",
  );
  return reader.getRowObjectsJson().map((row) => {
    const def = byId.get(String(row.id));
    const status = String(row.latest_status);
    return {
      id: String(row.id),
      name: def?.name ?? String(row.id),
      indicatorId: def?.indicatorId ?? "",
      meaning: def?.meaning ?? "",
      testQuestion: def?.testQuestion ?? "",
      evidenceRule: def?.evidenceRule ?? "",
      noiseRule: def?.noiseRule ?? "",
      saturationRule: def?.saturationRule ?? "",
      checks: Number(row.checks),
      present: Number(row.present_n),
      absent: Number(row.absent_n),
      insufficient: Number(row.insufficient_n),
      noiseCount: Number(row.noise_count),
      saturationCount: Number(row.saturation_count),
      latestStatus: status === "看得到" || status === "看不到" ? status : "樣本不足",
      latestDetail: String(row.latest_detail),
      noiseNow: String(row.noise_now),
      saturationNow: String(row.saturation_now),
    };
  });
}
