/** 本機 VIA_db 三庫：價量／籌碼／其餘。原件唯讀 COPY 進 GitHub 湖。本台不探 C:。 */
import { ARROW_BATCH } from "./columnar.ts";
import { PARQUET_LAKES, afterCopyMetaSql } from "./duck-catalog.ts";
import { DATA_ROOT, GITHUB_DIR, GITHUB_REPO, MOTHER_ROOTS } from "./coordinate.ts";
import { LAKE_START_YEAR } from "./lake-incr.ts";
import type { Light } from "./types.ts";

export const VIA_DB_ROOT = "C:\\新增資料夾\\新增資料夾";
export const GITHUB_LAKE_ROOT = `${GITHUB_DIR}\\movies-dataset\\data\\vdf`;
export const MOTHER_LAKE_ROOT = `${MOTHER_ROOTS[0]}\\data\\vdf`;
export const DATA_LAKE_ROOT = `${DATA_ROOT}\\dict\\VDF\\DATABASE`;

export type ViaDbPartId = "PX" | "CHIP" | "REST";
export type FetchTier = "LAKE" | "LOCAL" | "CACHE" | "LIVE" | "SKIP";

export type ViaDbPart = {
  id: ViaDbPartId;
  name: string;
  folder: string;
  pc: string;
  lake: "px" | "chip" | "rest";
  write: "px-cache" | "chip-cache" | "rest-cache";
  githubRel: string;
  githubPc: string;
  motherPc: string;
  dataPc: string;
  orderBy: string;
  schema: string;
  covers: string;
  light: Light;
  note: string;
};

export const VIA_DB_PARTS: ViaDbPart[] = [
  {
    id: "PX",
    name: "價量",
    folder: "VIA_db_part1_prices",
    pc: `${VIA_DB_ROOT}\\VIA_db_part1_prices`,
    lake: "px",
    write: "px-cache",
    githubRel: `${GITHUB_REPO}/data/vdf/px/year=*/part-*.parquet`,
    githubPc: `${GITHUB_LAKE_ROOT}\\px`,
    motherPc: `${MOTHER_LAKE_ROOT}\\px`,
    dataPc: `${DATA_LAKE_ROOT}\\px`,
    orderBy: "ticker, obs_date",
    schema: "ticker|obs_date|open|high|low|close|adj|volume|year",
    covers: "OHLCV／還原價 · 台股+全球",
    light: "ok",
    note: "原件不刪 · COPY→GitHub 湖 · 本台未探 C: · 契約 CACHE",
  },
  {
    id: "CHIP",
    name: "籌碼",
    folder: "VIA_db_part2_chips",
    pc: `${VIA_DB_ROOT}\\VIA_db_part2_chips`,
    lake: "chip",
    write: "chip-cache",
    githubRel: `${GITHUB_REPO}/data/vdf/chip/year=*/part-*.parquet`,
    githubPc: `${GITHUB_LAKE_ROOT}\\chip`,
    motherPc: `${MOTHER_LAKE_ROOT}\\chip`,
    dataPc: `${DATA_LAKE_ROOT}\\chip`,
    orderBy: "ticker, obs_date",
    schema: "ticker|obs_date|foreign_net|inst_net|dealer_net|margin|short|daytrade|year",
    covers: "三大法人／融資融券／當沖",
    light: "ok",
    note: "原件不刪 · COPY→GitHub 湖 · 本台未探 C: · 契約 CACHE",
  },
  {
    id: "REST",
    name: "其餘",
    folder: "VIA_db_part3_rest",
    pc: `${VIA_DB_ROOT}\\VIA_db_part3_rest`,
    lake: "rest",
    write: "rest-cache",
    githubRel: `${GITHUB_REPO}/data/vdf/rest/year=*/part-*.parquet`,
    githubPc: `${GITHUB_LAKE_ROOT}\\rest`,
    motherPc: `${MOTHER_LAKE_ROOT}\\rest`,
    dataPc: `${DATA_LAKE_ROOT}\\rest`,
    orderBy: "kind, ticker, obs_date",
    schema: "kind|ticker|obs_date|metric|value|year",
    covers: "財報／共識殘餘／非價非籌碼",
    light: "ok",
    note: "原件不刪 · COPY→GitHub 湖 · 本台未探 C: · 契約 CACHE",
  },
];

export const FETCH_PRIORITY: { rank: number; tier: FetchTier; note: string }[] = [
  { rank: 1, tier: "LAKE", note: "GitHub／母檔 hive year 已有 → 不外呼" },
  { rank: 2, tier: "LOCAL", note: "VIA_db_part* 原件 COPY 進湖 · 不刪不搬" },
  { rank: 3, tier: "CACHE", note: "期末種子 · 零外呼" },
  { rank: 4, tier: "LIVE", note: "雙閘 NET＋KEY · 預設關" },
];

export const LOCAL_LANE_IDS: ViaDbPartId[] = ["PX", "CHIP", "REST"];

export function isLocalLane(id: string): id is ViaDbPartId {
  return LOCAL_LANE_IDS.includes(id as ViaDbPartId);
}

export function viaDbPart(id: string): ViaDbPart | undefined {
  return VIA_DB_PARTS.find((p) => p.id === id);
}

/** 年檔已在湖就 SKIP；否則本機 COPY；再 CACHE；LIVE 最後且要雙閘。 */
export function decideFetch(input: {
  lakeHasYear: boolean;
  localHasYear: boolean;
  cacheHasYear: boolean;
  dualGate: boolean;
}): FetchTier {
  if (input.lakeHasYear) return "SKIP";
  if (input.localHasYear) return "LOCAL";
  if (input.cacheHasYear) return "CACHE";
  if (input.dualGate) return "LIVE";
  return "SKIP";
}

export type IngestRow = {
  id: ViaDbPartId;
  year: number;
  action: "COPY" | "PLAN";
  dest: string;
  light: Light;
  note: string;
};

export function ingestPlan(startYear = LAKE_START_YEAR, endYear = 2026): IngestRow[] {
  const out: IngestRow[] = [];
  for (const part of VIA_DB_PARTS) {
    for (let y = endYear; y >= startYear; y--) {
      out.push({
        id: part.id,
        year: y,
        action: "PLAN",
        dest: `${part.githubPc}\\year=${y}\\part-000.parquet`,
        light: "warn",
        note: `COPY_ONLY · 源 ${part.folder} · 不刪`,
      });
    }
  }
  return out;
}

export function localIngestSql(part: ViaDbPart, year: number): string {
  const lake = PARQUET_LAKES.find((l) => l.id === part.lake);
  if (!lake) return `-- missing lake ${part.lake}`;
  const src = part.pc.replace(/\\/g, "/");
  const dest = `${part.githubPc.replace(/\\/g, "/")}/year=${year}/part-000.parquet`;
  const copy = `COPY (SELECT * FROM read_parquet('${src}/**/*.parquet', hive_partitioning=true, union_by_name=false) WHERE year = ${year} ORDER BY ${part.orderBy}) TO '${dest}' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE ${ARROW_BATCH}, OVERWRITE_OR_IGNORE)`;
  return `-- COPY_ONLY never delete ${part.pc}\n${copy};\n${afterCopyMetaSql(lake, year)}`;
}

export function ingestSqlAll(startYear = LAKE_START_YEAR, endYear = 2026): string {
  return VIA_DB_PARTS.flatMap((p) => {
    const years: string[] = [];
    for (let y = endYear; y >= startYear; y--) years.push(localIngestSql(p, y));
    return years;
  }).join(";\n");
}

export function viaDbHydraOk(): boolean {
  const writes = VIA_DB_PARTS.map((p) => p.write);
  const lakeWrites = PARQUET_LAKES.map((l) => l.write);
  return new Set(writes).size === writes.length && writes.every((w) => lakeWrites.includes(w));
}

export function viaDbSealNote(): string {
  return `本機三庫 ${VIA_DB_PARTS.length} · 原件不刪 · COPY→${GITHUB_DIR} · 擷取 LAKE→LOCAL→CACHE→LIVE · 本台未探 C:`;
}

export function viaDbRows(): {
  id: string;
  name: string;
  folder: string;
  lake: string;
  github: string;
  pc: string;
  light: Light;
  note: string;
}[] {
  return VIA_DB_PARTS.map((p) => ({
    id: p.id,
    name: p.name,
    folder: p.folder,
    lake: p.lake,
    github: p.githubRel,
    pc: p.pc,
    light: p.light,
    note: p.note,
  }));
}
