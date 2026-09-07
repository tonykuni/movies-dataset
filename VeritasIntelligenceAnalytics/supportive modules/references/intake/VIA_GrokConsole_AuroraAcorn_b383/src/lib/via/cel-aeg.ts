/** VDF 加速／網路唯一正典。橋委派，不直 import，不代設 CONSENT。 */
import type { Light } from "./types.ts";

export const CEL_ID = "ACC-CEL";
export const AEG_ID = "NET-AEG";
export const CEL_FILE = "VeritasCeleritas.py";
export const AEG_FILE = "VeritasAegisNexus.py";
export const CEL_REL = "supportive modules/VeritasCeleritas.py";
export const AEG_REL = "supportive modules/VeritasAegisNexus.py";
export const CEL_HOST =
  "C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics\\supportive modules\\VeritasCeleritas.py";
export const AEG_HOST =
  "C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics\\supportive modules\\VeritasAegisNexus.py";

/** 只增不減：737/740 留作橋，活路是 CEL/AEG。 */
export const CEL_ALIASES = ["ACC-737", "VDF_MDL000"] as const;
export const AEG_ALIASES = ["SUP_MDL740", "NET-740"] as const;

export const CEL_REG = "VIS-SA-CEL-000001";
export const CEL_VER = "1.0.0";
export const AEG_VER = "3.0";
/** 附件無 __module_id__，不發明 VIS 編號。 */
export const AEG_REG = "無";
export const CEL_MODE = "maxsafe";
export const MDL000_OPTIONAL = true;
export const AEG_SECTIONS = 20;
export const CEL_ANCS = 25;
export const AEG_LIB_CATS = ["ANTI_RATELIMIT", "ANTI_BOT", "HTTP_RESILIENCE", "PARSE", "FINANCE", "DATA"] as const;
export const CEL_SURFACE = ["xmap", "xfetch", "xbatch", "cross_init", "VISAccelerator", "DataValidator"] as const;
export const AEG_SURFACE = ["LibraryRegistry", "ResilientHTTPClient", "yFinanceShield", "TaiwanDataSources", "def_smart_tw_basic_info"] as const;

export type CelAegRow = {
  id: string;
  role: "accel" | "net" | "bridge";
  file: string;
  winner: string;
  light: Light;
  note: string;
};

export function celAegRows(): CelAegRow[] {
  return [
    { id: CEL_ID, role: "accel", file: CEL_FILE, winner: CEL_ID, light: "ok", note: `${CEL_REG} · v${CEL_VER} · maxsafe · MDL000 可選` },
    { id: AEG_ID, role: "net", file: AEG_FILE, winner: AEG_ID, light: "ok", note: `${AEG_REG} VIS 編號 · v${AEG_VER} · ${AEG_SECTIONS} 節 · 閘關` },
    { id: "ACC-737", role: "bridge", file: "VIA_SuperAccel_Module.py", winner: CEL_ID, light: "ok", note: "ALIAS 橋 → CEL · 不直 import" },
    { id: "NET-740", role: "bridge", file: "via_net_unified_v*.py", winner: AEG_ID, light: "ok", note: "ALIAS 橋 → AEG · 不直 import" },
  ];
}

export function celAegNote(): string {
  return `${CEL_REG} 加速 · AEG ${AEG_REG}編號 v${AEG_VER} · 橋不直 import · LIVE 關`;
}

export function isCelAlias(id: string): boolean {
  return (CEL_ALIASES as readonly string[]).includes(id);
}

export function isAegAlias(id: string): boolean {
  return (AEG_ALIASES as readonly string[]).includes(id);
}

export function vdfAccelWinner(): string {
  return CEL_ID;
}

export function vdfNetWinner(): string {
  return AEG_ID;
}

export function consentUntouched(): boolean {
  return true;
}
