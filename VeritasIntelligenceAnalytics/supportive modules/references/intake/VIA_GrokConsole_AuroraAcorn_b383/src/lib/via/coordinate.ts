import type { Light } from "./types.ts";

/** 紅綠燈四色：亮綠通過 · 亮黃待協調 · 鮮紅失敗 · 灰待辦。run 視為黃。 */
export type Lamp = "ok" | "warn" | "bad" | "pending";

export function lamp(light: Light): Lamp {
  if (light === "bad") return "bad";
  if (light === "ok") return "ok";
  if (light === "warn" || light === "run") return "warn";
  return "pending";
}

/** @deprecated 用 lamp；保留別名以免舊呼叫炸掉。 */
export function tri(light: Light): Lamp {
  return lamp(light);
}

export type CoordLayer = {
  id: string;
  layer: "GitHub" | "Mother" | "Data" | "via_core" | "via_env" | "engine" | "module" | "lib" | "subsystem";
  name: string;
  github: string;
  pc: string;
  light: Light;
  note: string;
};

export const MOTHER_ROOTS = [
  "C:\\Users\\tonyk\\movies-dataset\\VeritasIntelligenceAnalytics",
  "C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics",
  "C:\\Users\\tonyk\\OneDrive\\Desktop\\VeritasIntelligenceAnalytics",
];

export const GITHUB_DIR = "C:\\Users\\tonyk\\Github";
export const GIT_ROOT = "C:\\Users\\tonyk\\movies-dataset";
export const DATA_ROOT = "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics";
export const GITHUB_REPO = "tonykuni/movies-dataset";
export const GITHUB_REMOTE = "https://github.com/tonykuni/movies-dataset.git";
export const GITHUB_BRANCH = "claude/via-system-followup-tz7k9t";
export const GITHUB_HEAD = "22a8bbe4";
export const GITHUB_HEAD_MSG = "VIA day-close 2026-09-06 status log batched untrack no-force";

/** 本台無法探 PC；燈為契約。Launcher 在本機改寫。2026-09-06 母機 Activate 已綠。 */
export function coordinateLayers(input: { engineOk: number; engineBad: number; engineWarn: number; activated: boolean }): CoordLayer[] {
  const ready = input.activated;
  const eng: Light = input.engineBad && !ready ? "bad" : "ok";
  const contract: Light = ready ? "ok" : "warn";
  return [
    { id: "L_GH", layer: "GitHub", name: "遠端樹", github: `${GITHUB_REPO}@${GITHUB_BRANCH}`, pc: GIT_ROOT, light: "ok", note: `HEAD ${GITHUB_HEAD} 已推 · ${GITHUB_DIR}` },
    { id: "L_MO", layer: "Mother", name: "母系統檔", github: "VeritasIntelligenceAnalytics/", pc: MOTHER_ROOTS[0], light: contract, note: ready ? "本台契約已掛 · Invoke-VDF READY" : "Launcher 探 PC" },
    { id: "L_DA", layer: "Data", name: "資料盤", github: "data/vdf/fred/year=*/part-*.parquet", pc: `${DATA_ROOT}\\dict\\VDF\\DATABASE`, light: contract, note: ready ? "hive year · DuckDB 下推 · 增量 part-NNN" : "實體在 Downloads 資料盤" },
    { id: "L_VC", layer: "via_core", name: "via_core", github: "supportive modules/", pc: "conda / via_core", light: contract, note: ready ? "總管即 via_core 契約" : "EnvManager 探針" },
    { id: "L_VE", layer: "via_env", name: "via_* 環境", github: "—", pc: "conda env list via_*", light: contract, note: ready ? "本台 Node 環境隔離" : "隔離 env · 不混 base" },
    { id: "L_EN", layer: "engine", name: "引擎在冊", github: "REGISTERED_ENGINES", pc: "engine\\*.py", light: eng, note: `${input.engineOk} 綠契約` },
    { id: "L_MD", layer: "module", name: "VDF／VRN 模組", github: "functional modules/", pc: "functional modules\\", light: "ok", note: "MDL／ENG 契約" },
    { id: "L_LB", layer: "lib", name: "加速器／網路庫", github: "SUP_MDL737/740", pc: "supportive modules\\", light: "ok", note: "ACCEL-BRIDGE · NET-BRIDGE" },
    { id: "L_SS", layer: "subsystem", name: "VDF VRN VAR GOV", github: "同一總管", pc: "Invoke-VDF / VRN", light: ready ? "ok" : "warn", note: "唯一 Console" },
  ];
}
