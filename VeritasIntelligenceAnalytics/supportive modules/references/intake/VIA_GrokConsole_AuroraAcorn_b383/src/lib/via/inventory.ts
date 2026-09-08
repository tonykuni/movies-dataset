/** Job-based SSOT: same function → one live winner. Tools never decrease; old modules alias off the live path. */
import { ACCEL_TOOLS, GOV_TOOLS, NET_TOOLS, NLP_TOOLS, REGISTERED_ENGINES } from "./catalog.ts";
import { PS20 } from "./accel.ts";
import type { EngineRec, Light } from "./types.ts";

export type JobMap = {
  job: string;
  winner: string;
  aliases: string[];
  tools: string[];
};

export const JOBS: JobMap[] = [
  { job: "VRN_PARSE", winner: "VRN_MDL001", aliases: ["VRN_PDF", "VRN_CLASS"], tools: ["NLP-OCR", "NLP-063"] },
  { job: "VRN_LAYOUT", winner: "VRN_MDL002", aliases: [], tools: ["NLP-OCR"] },
  { job: "VRN_TABLE", winner: "VRN_MDL003", aliases: [], tools: ["NLP-OCR"] },
  { job: "VRN_OCR_TAB", winner: "VRN_MDL004", aliases: [], tools: ["NLP-OCR"] },
  { job: "VRN_BASIC", winner: "VRN_MDL005", aliases: [], tools: ["NLP-064"] },
  { job: "VRN_CONSOL", winner: "VRN_MDL006", aliases: [], tools: ["ACC-PS20", "NLP-064"] },
  { job: "VRN_API", winner: "VRN_MDL007", aliases: [], tools: ["NET-MOPS", "NET-YF"] },
  { job: "VRN_XVAL", winner: "VRN_MDL008", aliases: ["VRN_XVAL"], tools: ["NET-740"] },
  { job: "VRN_SUM", winner: "VRN_ENG062", aliases: ["VRN_SUM1", "VRN_SUM2"], tools: ["NLP-062", "NLP-066"] },
  { job: "VRN_HUB", winner: "VRN_ENG066", aliases: [], tools: ["NLP-066"] },
  { job: "VRN_KNOW", winner: "VRN_ENG064", aliases: [], tools: ["NLP-064"] },
  { job: "VRN_FMT", winner: "VRN_ENG_OFIE", aliases: [], tools: ["NLP-OFIE", "NLP-OCR"] },
  { job: "VRN_MD", winner: "VRN_ENG_MDE", aliases: [], tools: ["NLP-MDE"] },
  { job: "VRN_SEM", winner: "VRN_ENG_USIP", aliases: [], tools: ["NLP-USIP", "NLP-066"] },
  { job: "VRN_LEX", winner: "VRN_ENG063", aliases: [], tools: ["NLP-063"] },
  { job: "VRN_REG", winner: "VRN_MDL010", aliases: [], tools: ["NLP-063"] },
  { job: "VRN_TRUST", winner: "VRN_MDL009", aliases: [], tools: ["ACC-PS20"] },
  { job: "VRN_AUDIT", winner: "VRN_AUDITU", aliases: [], tools: ["ACC-PS20"] },
  { job: "VRN_REP", winner: "VRN_REP", aliases: [], tools: [] },
  { job: "VDF_UNI", winner: "VDF_MDL001", aliases: ["VDF_ENG040"], tools: ["ACC-CEL", "ACC-PS20"] },
  { job: "VDF_INJECT", winner: "VDF_MDL007", aliases: ["VDF_ENG039"], tools: ["NET-AEG", "NET-740"] },
  { job: "VDF_YF", winner: "VDF_MDL002", aliases: [], tools: ["NET-YF", "NET-AEG", "ACC-CEL"] },
  { job: "VDF_MACRO", winner: "VDF_ENG074", aliases: [], tools: ["NET-FRED", "NET-AEG", "ACC-CEL", "ACC-PS20"] },
  { job: "VDF_USDET", winner: "VDF_ENG047", aliases: [], tools: ["NET-FRED", "NET-AEG"] },
  { job: "VDF_SENT", winner: "VDF_MDL003", aliases: [], tools: ["NET-FRED", "NET-AK", "NET-AEG"] },
  { job: "VDF_FILTER", winner: "VDF_MDL005", aliases: [], tools: ["NET-YF", "NET-AEG"] },
  { job: "VDF_FIN", winner: "VDF_MDL006", aliases: [], tools: ["NET-YF", "NET-AEG"] },
  { job: "VDF_SSOT", winner: "VDF_MDL007", aliases: [], tools: ["NET-AEG", "NET-740"] },
  { job: "VDF_FETCH", winner: "VDF_FETCH", aliases: [], tools: ["NET-FRED", "NET-AEG", "ACC-CEL", "ACC-PS20"] },
  { job: "VDF_REV", winner: "VDF_ENG075", aliases: ["VDF_REV", "TWN_REV_ENG", "VIA_U"], tools: ["NET-MOPS", "NET-AEG", "ACC-CEL", "ACC-PS20"] },
  { job: "VIA_GLSS", winner: "VIA_GLSS", aliases: ["VIA_GFF"], tools: ["NET-MOPS", "ACC-PS20"] },
  { job: "VIA_AEA", winner: "VIA_AEA", aliases: ["VIA_AETF", "VIA_ActiveTWETF"], tools: ["NET-TWSE", "ACC-PS20", "LIB-DUCKDB"] },
  { job: "VIA_VAP", winner: "VAP_MDL001", aliases: [], tools: ["ACC-PS20"] },
  { job: "VDF_AETF", winner: "VDF_ENG076", aliases: ["VDF_ENG076"], tools: ["NET-TWSE", "NET-AEG", "LIB-DUCKDB"] },
  { job: "VIA_CNS", winner: "VIA_CNS", aliases: ["VIA_CNYES", "VIA_FACTSET"], tools: ["NET-CNYES", "NET-YF", "NET-AEG", "ACC-PS20", "LIB-DUCKDB", "LIB-POLARS"] },
  { job: "VDF_CNS", winner: "VDF_ENG077", aliases: [], tools: ["NET-CNYES", "NET-YF", "NET-AEG", "LIB-DUCKDB"] },
  { job: "VDF_INTAKE", winner: "VDF_ENG042", aliases: [], tools: ["ACC-CEL"] },
  { job: "VDF_ACCEL", winner: "ACC-CEL", aliases: ["ACC-737", "VDF_MDL000"], tools: ["ACC-CEL", "ACC-PS20"] },
  { job: "VDF_NET", winner: "NET-AEG", aliases: ["SUP_MDL740", "NET-740"], tools: ["NET-AEG"] },
];

export function aliasOf(id: string): string | null {
  for (const j of JOBS) {
    if (j.aliases.includes(id) && j.winner !== id) return j.winner;
  }
  return null;
}

export function isOrphanEngine(e: { id: string; path?: string; name?: string }): boolean {
  return !String(e.path ?? "").trim() || /orphan/i.test(e.id) || /orphan/i.test(e.name ?? "");
}

export function isolateOrphanNote(note: string): string {
  if (/UNREPAIRABLE|DETAILS 保留/.test(note)) return note;
  return `UNREPAIRABLE · DETAILS 保留 · 不自動修 · ${note}`;
}

export function isUnknownStub(e: { id: string; path?: string; name?: string }): boolean {
  const id = String(e.id ?? "");
  const name = String(e.name ?? "");
  return !String(e.path ?? "").trim() && (/orphan/i.test(id) || /orphan|stub/i.test(name));
}

export function applySsot(engines: EngineRec[] = REGISTERED_ENGINES): EngineRec[] {
  return engines
    .filter((e) => !isUnknownStub(e))
    .map((e) => {
    const win = aliasOf(e.id);
    if (win) {
      return {
        ...e,
        status: "idle" as Light,
        ssot: true,
        note: `ALIAS → ${win} · 模組退下活路 · 工具保留`,
      };
    }
    if (isOrphanEngine(e)) {
      return {
        ...e,
        status: "warn" as Light,
        note: isolateOrphanNote(e.note),
      };
    }
    return { ...e };
  });
}

export function liveEngines(engines: EngineRec[]): EngineRec[] {
  return engines.filter((e) => !aliasOf(e.id));
}

export type InvRow = { id: string; kind: string; name: string; status: Light; note: string };

export function moduleTable(engines: EngineRec[]): InvRow[] {
  const rows = applySsot(engines).map((e) => {
    const aliased = Boolean(aliasOf(e.id));
    const orphan = isOrphanEngine(e);
    const status: Light = aliased ? "idle" : orphan ? "warn" : e.status === "bad" ? "bad" : e.status === "warn" ? "warn" : e.status === "idle" ? "idle" : "ok";
    return {
      id: e.id,
      kind: e.kind,
      name: e.name,
      status,
      note: orphan ? isolateOrphanNote(e.note) : e.note,
    };
  });
  return rows.sort((a, b) => Number(Boolean(aliasOf(a.id))) - Number(Boolean(aliasOf(b.id))));
}

export function libTable(): InvRow[] {
  return [
    { id: "LIB-POLARS", kind: "compute", name: "polars", status: "ok", note: "via_vdf · 列裁剪" },
    { id: "LIB-DUCKDB", kind: "query", name: "duckdb", status: "ok", note: "via_vdf · 唯一 parquet catalog via_lake.duckdb" },
    { id: "LIB-ARROW", kind: "struct", name: "pyarrow", status: "ok", note: "via_vdf · parquet" },
    { id: "LIB-YF", kind: "net", name: "yfinance", status: "warn", note: "via_vdf · 第二閘關" },
    { id: "LIB-AK", kind: "net", name: "akshare", status: "warn", note: "via_vdf · 未掛" },
    { id: "LIB-FRED", kind: "net", name: "fredapi", status: "ok", note: "本台 FRED 適配" },
    { id: "LIB-EIA", kind: "net", name: "eia", status: "warn", note: "KEY 參數 · LIVE 以後再測" },
    { id: "LIB-PYPDF", kind: "nlp", name: "pypdf", status: "ok", note: "via_vrn" },
    { id: "LIB-PLUMB", kind: "nlp", name: "pdfplumber", status: "ok", note: "via_vrn" },
    { id: "LIB-OCC", kind: "nlp", name: "opencc", status: "ok", note: "via_nlp" },
    { id: "LIB-RUFF", kind: "gov", name: "ruff", status: "ok", note: "via_core" },
    { id: "LIB-NPY", kind: "compute", name: "numpy", status: "ok", note: "base 1.26.4 · via_vdf 2.1.1 · via_iso_numpy 1.x" },
    { id: "LIB-PDT", kind: "gov", name: "pydantic", status: "ok", note: "via_core" },
    { id: "LIB-SCI", kind: "compute", name: "scipy", status: "ok", note: "via_iso_numpy · 不進 PATH" },
    { id: "LIB-PLY", kind: "ui", name: "plotly", status: "ok", note: "via_iso_plotly · 不進 PATH" },
  ];
}

export function toolTable(): InvRow[] {
  const accels = PS20.map((a) => ({
    id: a.id,
    kind: `accel:${a.layer}`,
    name: a.name,
    status: "ok" as Light,
    note: a.note,
  }));
  const mounted = [...ACCEL_TOOLS, ...NET_TOOLS, ...NLP_TOOLS, ...GOV_TOOLS].map((t) => ({
    id: t.id,
    kind: t.kind,
    name: t.name,
    status: t.status,
    note: t.note,
  }));
  return [...accels, ...mounted];
}

export function jsLibTable(): InvRow[] {
  return [
    { id: "JS-REACT", kind: "ui", name: "react 19", status: "ok", note: "總管 DOM" },
    { id: "JS-ZUSTAND", kind: "state", name: "zustand", status: "ok", note: "唯一 store" },
    { id: "JS-TANSTACK", kind: "router", name: "tanstack start", status: "ok", note: "路由／查詢" },
    { id: "JS-PGLITE", kind: "db", name: "@electric-sql/pglite", status: "ok", note: "本台 SQL · 非湖" },
    { id: "JS-KYSELY", kind: "db", name: "kysely", status: "ok", note: "查詢建構" },
    { id: "JS-ZOD", kind: "schema", name: "zod", status: "ok", note: "契約" },
    { id: "JS-LUCIDE", kind: "ui", name: "lucide-react", status: "ok", note: "圖示" },
  ];
}

export type EnvPin = { env: string; pkg: string; ver: string };
export type EnvConflict = {
  pkg: string;
  left: string;
  right: string;
  light: Light;
  isolate: string;
  cmd: string;
};

export const ENV_PINS: EnvPin[] = [
  { env: "via_core", pkg: "python", ver: "3.11" },
  { env: "via_core", pkg: "ruff", ver: "0.6.9" },
  { env: "via_core", pkg: "pydantic", ver: "2.9.2" },
  { env: "via_vdf", pkg: "python", ver: "3.11" },
  { env: "via_vdf", pkg: "polars", ver: "1.9.0" },
  { env: "via_vdf", pkg: "duckdb", ver: "1.1.3" },
  { env: "via_vdf", pkg: "pyarrow", ver: "17.0.0" },
  { env: "via_vdf", pkg: "numpy", ver: "2.1.1" },
  { env: "via_vdf", pkg: "fredapi", ver: "0.5.2" },
  { env: "via_vdf", pkg: "yfinance", ver: "0.2.44" },
  { env: "via_vrn", pkg: "python", ver: "3.11" },
  { env: "via_vrn", pkg: "pypdf", ver: "5.0.1" },
  { env: "via_vrn", pkg: "pdfplumber", ver: "0.11.4" },
  { env: "via_nlp", pkg: "python", ver: "3.11" },
  { env: "via_nlp", pkg: "opencc", ver: "1.1.8" },
  { env: "via_vap", pkg: "python", ver: "3.11" },
  { env: "via_iso_plotly", pkg: "python", ver: "3.11" },
  { env: "via_iso_plotly", pkg: "plotly", ver: "5.24.1" },
  { env: "via_iso_numpy", pkg: "python", ver: "3.11" },
  { env: "via_iso_numpy", pkg: "numpy", ver: "1.26.4" },
  { env: "via_iso_numpy", pkg: "scipy", ver: "1.12.0" },
  { env: "base", pkg: "python", ver: "3.12" },
  { env: "base", pkg: "numpy", ver: "1.26.4" },
  { env: "base", pkg: "pandas", ver: "2.2.2" },
];

export function scanEnvConflicts(pins: EnvPin[] = ENV_PINS): EnvConflict[] {
  const byPkg = new Map<string, EnvPin[]>();
  for (const p of pins) {
    const list = byPkg.get(p.pkg) ?? [];
    list.push(p);
    byPkg.set(p.pkg, list);
  }
  const out: EnvConflict[] = [];
  for (const [pkg, list] of byPkg) {
    if (pkg === "python") continue;
    const versions = [...new Set(list.map((x) => x.ver))];
    if (versions.length < 2) continue;
    const via = list.find((x) => x.env.startsWith("via_"));
    const other = list.find((x) => x !== via) ?? list[1];
    if (!via || !other) continue;
    const iso = `via_iso_${pkg}`;
    out.push({
      pkg,
      left: `${via.env}@${via.ver}`,
      right: `${other.env}@${other.ver}`,
      light: "warn",
      isolate: iso,
      cmd: `conda create -n ${iso} python=3.11 ${pkg}==${other.ver} --yes; conda env update -n ${via.env} -f locks/${via.env}.yml --prune`,
    });
  }
  return out;
}

export function envTable(pins: EnvPin[] = ENV_PINS): InvRow[] {
  const names = [...new Set(pins.map((p) => p.env))];
  const conflicts = scanEnvConflicts(pins);
  return names.map((env) => {
    const hit = conflicts.filter((c) => c.left.startsWith(env) || c.right.startsWith(env));
    return {
      id: env,
      kind: env === "base" ? "host" : "via_*",
      name: env,
      status: hit.length ? "warn" : "ok",
      note: hit.length
        ? `衝突 ${hit.map((h) => h.pkg).join(",")} · 隔離 ${hit.map((h) => h.isolate).join(",")}`
        : "鎖檔一致 · 開機已核",
    };
  });
}

export function parquetAccelPresent(): boolean {
  return PS20.some((a) => /parquet|Partition/i.test(a.name + a.note));
}

/** PS-01..20 → 已有工具。ACC-PS20 為包裝；層級另綁 LIB／ACC／NET。 */
export const PS_TOOL_BIND: Record<string, string[]> = {
  "PS-01": ["ACC-PS20", "ACC-CEL", "ACC-737"],
  "PS-02": ["ACC-PS20", "ACC-CEL", "ACC-737"],
  "PS-03": ["ACC-PS20", "ACC-CEL", "ACC-737"],
  "PS-04": ["ACC-PS20", "ACC-CEL", "ACC-737"],
  "PS-05": ["ACC-PS20", "ACC-CEL", "NET-AEG", "NET-740"],
  "PS-06": ["ACC-PS20", "ACC-CEL"],
  "PS-07": ["ACC-PS20", "ACC-CEL", "LIB-ARROW"],
  "PS-08": ["ACC-PS20", "ACC-CEL", "LIB-ARROW"],
  "PS-09": ["ACC-PS20", "ACC-CEL", "LIB-ARROW"],
  "PS-10": ["ACC-PS20", "ACC-CEL", "LIB-ARROW"],
  "PS-11": ["ACC-PS20", "ACC-CEL", "LIB-DUCKDB"],
  "PS-12": ["ACC-PS20", "ACC-CEL", "LIB-DUCKDB"],
  "PS-13": ["ACC-PS20", "ACC-CEL", "LIB-ARROW"],
  "PS-14": ["ACC-PS20", "ACC-CEL", "LIB-ARROW"],
  "PS-15": ["ACC-PS20", "ACC-CEL", "LIB-ARROW"],
  "PS-16": ["ACC-PS20", "ACC-CEL", "LIB-POLARS"],
  "PS-17": ["ACC-PS20", "ACC-CEL"],
  "PS-18": ["ACC-PS20", "ACC-CEL", "LIB-DUCKDB"],
  "PS-19": ["ACC-PS20", "ACC-CEL", "LIB-DUCKDB"],
  "PS-20": ["ACC-PS20", "ACC-CEL", "ACC-737", "LIB-POLARS", "LIB-DUCKDB"],
};

export type AccelBindRow = {
  id: string;
  name: string;
  layer: string;
  tools: string;
  missing: string;
  light: Light;
};

export function catalogToolIds(): Set<string> {
  return new Set([
    ...PS20.map((a) => a.id),
    ...ACCEL_TOOLS.map((t) => t.id),
    ...NET_TOOLS.map((t) => t.id),
    ...NLP_TOOLS.map((t) => t.id),
    ...libTable().map((r) => r.id),
  ]);
}

export function accelBindTable(): AccelBindRow[] {
  const have = catalogToolIds();
  return PS20.map((a) => {
    const tools = PS_TOOL_BIND[a.id] ?? ["ACC-PS20"];
    const missing = tools.filter((t) => !have.has(t));
    return {
      id: a.id,
      name: a.name,
      layer: a.layer,
      tools: tools.join(" · "),
      missing: missing.join(",") || "—",
      light: missing.length ? "bad" : "ok",
    };
  });
}

export function accelBindSummary(): { lanes: number; bound: number; miss: number; wrappers: number } {
  const rows = accelBindTable();
  return {
    lanes: PS20.length,
    bound: rows.filter((r) => r.light === "ok").length,
    miss: rows.filter((r) => r.light === "bad").length,
    wrappers: ACCEL_TOOLS.length,
  };
}

export function mountAccelNet(confirmNet: boolean): { accel: number; net: number; live: number; note: string; light: Light } {
  const accel = ACCEL_TOOLS.length;
  const net = NET_TOOLS.length;
  const live = confirmNet ? net : 0;
  const s = accelBindSummary();
  const ok = accel >= 4 && net >= 8 && s.bound === 20 && s.miss === 0;
  return {
    accel,
    net,
    live,
    light: ok ? "ok" : "bad",
    note: ok
      ? `加速器 ${accel}+PS20 ${s.bound}/20 · 網具 ${net} 已掛 · LIVE ${live}`
      : `加速器缺綁 bound=${s.bound} miss=${s.miss}`,
  };
}

export type IsoStep = {
  id: string;
  title: string;
  cmd: string;
  light: Light;
  note: string;
};

export function lockfileYml(env: string, pins: EnvPin[] = ENV_PINS): string {
  const deps = pins.filter((p) => p.env === env);
  const lines = deps.map((p) => (p.pkg === "python" ? `  - python=${p.ver}` : `  - ${p.pkg}=${p.ver}`));
  return [`name: ${env}`, "channels:", "  - conda-forge", "dependencies:", ...lines].join("\n");
}

export function isolationSteps(conflicts: EnvConflict[] = scanEnvConflicts()): IsoStep[] {
  const steps: IsoStep[] = [
    {
      id: "ISO01",
      title: "掃描",
      cmd: "開機 scanEnvConflicts",
      light: conflicts.length ? "warn" : "ok",
      note: conflicts.length ? `${conflicts.map((c) => c.pkg).join(",")} 衝突` : "無衝突",
    },
  ];
  for (const c of conflicts) {
    const viaEnv = c.left.split("@")[0] ?? "via_vdf";
    steps.push({
      id: `ISO_${c.pkg}_NEW`,
      title: `建立 ${c.isolate}`,
      cmd: `conda create -n ${c.isolate} python=3.11 ${c.pkg}==${c.right.split("@")[1] ?? ""} --yes`,
      light: "warn",
      note: "只建隔離 env · 不刪 base",
    });
    steps.push({
      id: `ISO_${c.pkg}_LOCK`,
      title: `鎖檔 ${viaEnv}`,
      cmd: `conda env export -n ${viaEnv} --no-builds | Out-File -Encoding utf8 locks/${viaEnv}.yml`,
      light: "warn",
      note: "從 via_* 匯出 · 不改 base",
    });
    steps.push({
      id: `ISO_${c.pkg}_UPD`,
      title: `via_* 依鎖檔`,
      cmd: `conda env update -n ${viaEnv} -f locks/${viaEnv}.yml --prune`,
      light: "warn",
      note: "prune 只收 via_* · 禁止 conda remove",
    });
    steps.push({
      id: `ISO_${c.pkg}_VER`,
      title: "核對版本",
      cmd: `conda run -n ${c.isolate} python -c "import ${c.pkg} as m; print(m.__version__)"`,
      light: "pending",
      note: "母機跑完才綠",
    });
  }
  steps.push({
    id: "ISO99",
    title: "禁令",
    cmd: "禁止刪除／卸載／殺行程 · via_iso_numpy",
    light: "ok",
    note: "衝突件隔離不刪 · 例 via_iso_numpy",
  });
  return steps;
}

export function isolationScript(conflicts: EnvConflict[] = scanEnvConflicts()): string {
  const header = [
    "#requires -Version 7.0",
    "# VIA isolate · 本台不 spawn · 母機雙閘後才跑",
    "# 政策: 衝突件隔離不刪、不卸載、不殺行程、不 exit",
    "$ErrorActionPreference = 'Stop'",
    "$Lock = Join-Path $PSScriptRoot '..\\locks'",
    "if (-not (Test-Path -LiteralPath $Lock)) { New-Item -ItemType Directory -Path $Lock | Out-Null }",
  ];
  const body = conflicts.flatMap((c) => {
    const viaEnv = c.left.split("@")[0] ?? "via_vdf";
    const ver = c.left.split("@")[1] ?? "";
    return [
      `Write-Host "ISO  ${c.pkg}  ${c.left} vs ${c.right}  -> ${c.isolate}"`,
      `conda create -n ${c.isolate} python=3.11 ${c.pkg}==${ver} --yes`,
      `conda env export -n ${viaEnv} --no-builds | Out-File -Encoding utf8 (Join-Path $Lock '${viaEnv}.yml')`,
      `conda env update -n ${viaEnv} -f (Join-Path $Lock '${viaEnv}.yml') --prune`,
      `conda run -n ${c.isolate} python -c "import ${c.pkg} as m; print(m.__version__)"`,
    ];
  });
  const tail = [
    "Write-Host 'ISO  DONE · base 未刪 · 衝突件在 via_iso_*'",
    "return",
  ];
  return [...header, ...body, ...tail].join("\n");
}

export const HANDOVER_STAMP = {
  when: "2026-09-07 15:09 CST",
  from: "鮮況：Git fd42f5d5 只推 handover.md · AEA29 · U=ENG075 · LIVE 關",
  next: "2026-09-08 核 VIA-ALL.cmd 是否仍髒；foreach add；流/LIVE 另閘",
};
