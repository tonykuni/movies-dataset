/** 本台實測編譯快照。LIVE／Nuitka／母機 engine 樹不在此沙盒。 */
import type { Light } from "./types.ts";

export const COMPILE_SNAP = {
  when: "2026-09-07",
  tsc: true,
  vite: true,
  viteModules: 1946,
  viaTests: 204,
  pyCompile: 19,
  ps1: 29,
  pwsh: false,
  winEngineTree: false,
  live: false,
} as const;

export type CompileTier = "bundle" | "syntax" | "host-missing" | "sealed";

export type CompileRow = {
  id: string;
  system: "VIA" | "VDF" | "VRN" | "GOV" | "AEA" | "NLP" | "PS";
  name: string;
  tier: CompileTier;
  can: boolean;
  light: Light;
  note: string;
};

export function compileRows(): CompileRow[] {
  return [
    { id: "CPL_VIA", system: "VIA", name: "Console TS bundle", tier: "bundle", can: true, light: "ok", note: `tsc+vite ${COMPILE_SNAP.viteModules} · 本台可編` },
    { id: "CPL_VDF_TS", system: "VDF", name: "湖／宇宙／月營收契約", tier: "bundle", can: true, light: "ok", note: "TS 契約可編 · LIVE 擷取關" },
    { id: "CPL_VDF_PY", system: "VDF", name: "functional modules/VDF", tier: "host-missing", can: false, light: "warn", note: "本台無 Windows engine 樹 · 不 Nuitka" },
    { id: "CPL_VRN_TS", system: "VRN", name: "MDL001–010 TS 埠", tier: "bundle", can: true, light: "ok", note: "HardGate 本樹 7/7 CACHE · inject 關" },
    { id: "CPL_VRN_PY", system: "VRN", name: "functional modules/VRN", tier: "host-missing", can: false, light: "warn", note: "原件不在本 branch · 附件語法另列" },
    { id: "CPL_AEA", system: "AEA", name: "主動 ETF 29 檔矩陣", tier: "bundle", can: true, light: "ok", note: "TS CACHE · LIVE 關" },
    { id: "CPL_NLP", system: "NLP", name: "四點／Layout／OCR 契約", tier: "bundle", can: true, light: "ok", note: "TS CACHE · 引擎 SKIPPED_UNAVAILABLE" },
    { id: "CPL_GOV", system: "GOV", name: "EnvManager TS+py", tier: "bundle", can: true, light: "ok", note: "public/via/VIA_EnvManager.py py_compile 過" },
    { id: "CPL_ATT", system: "VRN", name: "附件 18 py 語法", tier: "syntax", can: true, light: "ok", note: "py_compile 18+1 · 不 import 跑 · 缺 pandas/duckdb" },
    { id: "CPL_PS", system: "PS", name: "PS1 29 檔", tier: "syntax", can: false, light: "warn", note: "括號平衡 · 本台無 pwsh · 母機跑" },
    { id: "CPL_OFIE", system: "NLP", name: "OFIE／MDE／USIP", tier: "host-missing", can: false, light: "warn", note: "Downloads 路徑 · 本台未掛" },
    { id: "CPL_LIVE", system: "VDF", name: "YF／AK／MOPS LIVE", tier: "sealed", can: false, light: "ok", note: "雙閘關 · 政策不編 LIVE" },
  ];
}

export function compileQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const rows = compileRows();
  const yes = rows.filter((r) => r.can).length;
  const host = rows.filter((r) => r.tier === "host-missing").length;
  return [
    { id: "CPL_N", metric: "可編", value: `${yes}/${rows.length}`, light: yes >= 6 ? "ok" : "bad", note: "bundle+syntax 可編 · host 不在本台" },
    { id: "CPL_TSC", metric: "tsc/vite", value: COMPILE_SNAP.tsc && COMPILE_SNAP.vite ? "PASS" : "FAIL", light: COMPILE_SNAP.tsc && COMPILE_SNAP.vite ? "ok" : "bad", note: `vite ${COMPILE_SNAP.viteModules}` },
    { id: "CPL_TEST", metric: "VIA 測", value: String(COMPILE_SNAP.viaTests), light: COMPILE_SNAP.viaTests >= 200 ? "ok" : "bad", note: "src/lib/via/*.test.ts" },
    { id: "CPL_PY", metric: "py_compile", value: String(COMPILE_SNAP.pyCompile), light: COMPILE_SNAP.pyCompile >= 19 ? "ok" : "bad", note: "樹內 1 + 附件 18" },
    { id: "CPL_HOST", metric: "母機樹", value: COMPILE_SNAP.winEngineTree ? "在" : "缺", light: "warn", note: `host-missing ${host} · 不假裝可編` },
  ];
}

export function compileNote(): string {
  const rows = compileRows();
  const yes = rows.filter((r) => r.can).length;
  return `編譯 ${yes}/${rows.length} 可 · tsc/vite 過 · 母機 engine 樹缺 · LIVE 關 · ${COMPILE_SNAP.when}`;
}

/** 母機頂層已列 vs 本台附件。sha／閘鏈不要傳。 */
export type UploadNeed = {
  id: string;
  sys: "VDF" | "VRN" | "VAP" | "SUP";
  file: string;
  listed: boolean;
  staged: boolean;
  attached: boolean;
  pri: 1 | 2 | 3;
  why: string;
};

/** 母機三根。SixStreams 走 movies-dataset；暫存腳本誤掃 OneDrive。 */
export const HOST_ROOTS = [
  "C:\\Users\\tonyk\\movies-dataset\\VeritasIntelligenceAnalytics",
  "C:\\Users\\tonyk\\Github\\movies-dataset\\VeritasIntelligenceAnalytics",
  "C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics",
] as const;

export const UPLOAD_NEED: UploadNeed[] = [
  { id: "U_CEL", sys: "SUP", file: "VeritasCeleritas.py", listed: true, staged: false, attached: true, pri: 1, why: "VIS-SA-CEL-000001 · 242127B 附件 · 不灌原件" },
  { id: "U_AEG", sys: "SUP", file: "VeritasAegisNexus.py", listed: true, staged: false, attached: true, pri: 1, why: "無 VIS 編號 · v3.0 · 208495B 附件" },
  { id: "U_MDL009", sys: "VRN", file: "VRN_MDL009_TrustScore.py", listed: false, staged: false, attached: false, pri: 1, why: "OneDrive 無此檔 · 搜 movies-dataset" },
  { id: "U_NLP066", sys: "VRN", file: "VRN_ENG066_NLPSupportHub.py", listed: false, staged: false, attached: false, pri: 1, why: "OneDrive 無此檔 · 搜 npl_preprocessor" },
  { id: "U_ENG047", sys: "VDF", file: "VDF_ENG047_USMacroDetailFetcher.py", listed: false, staged: false, attached: false, pri: 1, why: "engine 夾沒有 · L3 winner" },
  { id: "U_ENG074", sys: "VDF", file: "VDF_ENG074_FredMacroSSOT_v0102.py", listed: false, staged: false, attached: false, pri: 1, why: "engine 夾沒有 · L1 winner" },
  { id: "U_ENG046", sys: "VDF", file: "VDF_ENG046_FetchMatrixRegistry.py", listed: false, staged: false, attached: false, pri: 1, why: "engine 夾沒有" },
  { id: "U_ENG053", sys: "VDF", file: "VDF_ENG053_ParamEngineMap_v0102.py", listed: false, staged: false, attached: false, pri: 1, why: "engine 夾沒有" },
  { id: "U_VDF066", sys: "VDF", file: "VDF_ENG066_GlobalUniverse_v0101.py", listed: false, staged: false, attached: false, pri: 1, why: "engine 夾沒有 · 非 NLP ENG066" },
  { id: "U_HG", sys: "VRN", file: "VIA_HardGate_BootPrecheck.py", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 10035B · 尚未貼本台" },
  { id: "U_MDL001", sys: "VRN", file: "VRN_MDL001_Converter.py", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 66857B" },
  { id: "U_MDL002", sys: "VRN", file: "VRN_MDL002_LayoutExtractor.py", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 89419B" },
  { id: "U_MDL003", sys: "VRN", file: "VRN_MDL003_TableRestorer.py", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 107997B" },
  { id: "U_MDL004", sys: "VRN", file: "VRN_MDL004_OCR_FetchingPDFTable_v1.py", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 97888B" },
  { id: "U_MDL005", sys: "VRN", file: "VRN_MDL005_OCRFetchingPDFText_v1.py", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 83534B" },
  { id: "U_MDL007", sys: "VRN", file: "VRN_MDL007_APIDataFetcher.py", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 54005B" },
  { id: "U_MDL010", sys: "VRN", file: "VRN_MDL010_CodeRegistry.py", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 22647B" },
  { id: "U_VDFINV", sys: "VDF", file: "Invoke-VDF.ps1", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 2084B" },
  { id: "U_VDFFET", sys: "VDF", file: "Invoke-VDF-Fetch.ps1", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 2703B" },
  { id: "U_VDFMAN", sys: "VDF", file: "VDF_Subsystem_Manifest.json", listed: true, staged: true, attached: false, pri: 1, why: "TEMP 已集 2422B" },
  { id: "U_ENGDIR", sys: "VDF", file: "engine\\ (部分)", listed: true, staged: true, attached: false, pri: 1, why: "有 039/040/042/STAT/MDL002-007/103/301 · 缺 046/047/053/066/074" },
  { id: "U_STAT", sys: "VDF", file: "engine\\Import-VDF-StatisticsEngine.ps1", listed: true, staged: true, attached: false, pri: 2, why: "TEMP 已集 33318B" },
  { id: "U_UNI", sys: "VDF", file: "VDF_MDL001_TWUniverseVerify.py", listed: true, staged: true, attached: false, pri: 2, why: "TEMP 已集 27770B" },
  { id: "U_SSOT", sys: "VDF", file: "VDF_MDL007_SSOTResolver.py", listed: true, staged: true, attached: false, pri: 2, why: "TEMP 已集 58962B" },
  { id: "U_PARAM", sys: "VDF", file: "VDF_Unified_Params_v0100.json", listed: true, staged: true, attached: false, pri: 2, why: "TEMP 已集 1013B" },
  { id: "U_ARCH", sys: "VDF", file: "VDF_Architecture_Clarification_v0100.md", listed: true, staged: true, attached: false, pri: 2, why: "TEMP 已集 6263B" },
  { id: "U_VAP", sys: "VAP", file: "functional modules\\VAP\\", listed: false, staged: false, attached: false, pri: 2, why: "S5 v025 回歸 exit 1 · 整夾未集" },
  { id: "U_SUP", sys: "SUP", file: "supportive modules\\40_Environment_Health\\", listed: false, staged: false, attached: false, pri: 2, why: "EnvManager 原樹" },
  { id: "U_REV", sys: "VDF", file: "new modules engines\\taiwan_revenue_engine\\", listed: false, staged: false, attached: false, pri: 2, why: "ENG075 月營收" },
  { id: "U_ACCEL", sys: "VDF", file: "VeritasDataForge\\accelerator\\", listed: false, staged: false, attached: false, pri: 3, why: "MDL000 加速核 · 可能藏 ENG047/074" },
];

export const UPLOAD_SKIP = [
  "*_sha*",
  "*.freeze.lock.json",
  "Invoke-VIA-v0113*",
  "Invoke-VIA-v0114*",
  "Invoke-VIA-Integration*",
  "vrn_report_digest_v0100–v0108（只留最新）",
  "VRN_ENG050_ContentStore_v0100–v0105（只留最新）",
  "CSV/HTML 報表與 table*_T1",
] as const;

export function uploadGapQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const n1 = UPLOAD_NEED.filter((r) => r.pri === 1 && !r.staged && !r.attached).length;
  const n2 = UPLOAD_NEED.filter((r) => r.pri === 2 && !r.staged && !r.attached).length;
  const staged = UPLOAD_NEED.filter((r) => r.staged && !r.attached).length;
  const missList = UPLOAD_NEED.filter((r) => !r.listed && !r.staged && !r.attached).length;
  return [
    { id: "UP_STAGED", metric: "TEMP 已集", value: String(staged), light: staged ? "ok" : "warn", note: "via_upload_gap · 尚未貼本台" },
    { id: "UP_P1", metric: "P1 仍缺", value: String(n1), light: n1 ? "warn" : "ok", note: "MDL009／NLP066／ENG046/047/053/066/074 · 換 movies-dataset 搜" },
    { id: "UP_P2", metric: "P2 仍缺", value: String(n2), light: "warn", note: "VAP（S5 exit 1）／EnvHealth／月營收" },
    { id: "UP_NOLIST", metric: "三根都沒列", value: String(missList), light: missList ? "warn" : "ok", note: HOST_ROOTS[0] },
    { id: "UP_SKIP", metric: "不要傳", value: String(UPLOAD_SKIP.length), light: "ok", note: "sha／freeze／v0113–v0114 閘鏈" },
  ];
}
