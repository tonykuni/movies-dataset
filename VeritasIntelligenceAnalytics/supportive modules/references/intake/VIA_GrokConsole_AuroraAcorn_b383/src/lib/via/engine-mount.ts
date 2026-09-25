/** 每引擎：有無自動編號、導入哪個加速／網路／NLP。不灌 CEL/AEG 原件。 */
import { NLP_TOOLS, REGISTERED_ENGINES } from "./catalog.ts";
import { CEL_ID, AEG_ID } from "./cel-aeg.ts";
import { aliasOf } from "./inventory.ts";
import type { EngineRec, Light } from "./types.ts";

/** 附件實測：Celeritas 有 VIS 編號；Aegis v3.0 無 __module_id__。 */
export const AUTO_REG: Record<string, string> = {
  "ACC-CEL": "VIS-SA-CEL-000001",
  "VIS-ENV-000001": "VIS-ENV-000001",
};

export type MountRow = {
  id: string;
  kind: string;
  name: string;
  reg: string;
  auto: boolean;
  accel: string;
  net: string;
  nlp: string;
  aliased: boolean;
  light: Light;
};

export function nlpToolOf(e: EngineRec): string {
  const mapped = NLP_MAP[e.id];
  if (mapped) return mapped;
  if (!e.nlp) return "—";
  return "NLP-066";
}

/** 引擎 → NLP 工具。未列且 nlp=false 為 —。 */
export const NLP_MAP: Record<string, string> = {
  VRN_MDL001: "NLP-063",
  VRN_MDL002: "NLP-OCR",
  VRN_MDL003: "NLP-OCR",
  VRN_MDL004: "NLP-OCR",
  VRN_MDL005: "NLP-064",
  VRN_MDL006: "NLP-064",
  VRN_MDL010: "NLP-063",
  VRN_PDF: "NLP-OCR",
  VRN_CLASS: "NLP-063",
  VRN_ENG062: "NLP-062",
  VRN_SUM1: "NLP-062",
  VRN_SUM2: "NLP-062",
  VRN_ENG063: "NLP-063",
  VRN_ENG064: "NLP-064",
  VRN_ENG066: "NLP-066",
  VRN_SYN: "NLP-063",
  VRN_ENG_OFIE: "NLP-OFIE",
  VRN_ENG_MDE: "NLP-MDE",
  VRN_ENG_USIP: "NLP-USIP",
};

export function accelToolOf(e: EngineRec): string {
  if (!e.accel) return "—";
  return CEL_ID;
}

export function netToolOf(e: EngineRec): string {
  if (!e.net) return "—";
  return AEG_ID;
}

export function autoRegOf(e: EngineRec): { reg: string; auto: boolean } {
  const vis = AUTO_REG[e.id];
  if (vis) return { reg: vis, auto: true };
  return { reg: `無 · ${e.hash}`, auto: false };
}

export function engineMountRows(engines: EngineRec[] = REGISTERED_ENGINES): MountRow[] {
  return engines.map((e) => {
    const { reg, auto } = autoRegOf(e);
    const aliased = Boolean(aliasOf(e.id));
    return {
      id: e.id,
      kind: e.kind,
      name: e.name,
      reg,
      auto,
      accel: accelToolOf(e),
      net: netToolOf(e),
      nlp: nlpToolOf(e),
      aliased,
      light: aliased ? "idle" : e.status === "bad" ? "bad" : e.status === "warn" ? "warn" : "ok",
    };
  });
}

export function engineMountQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const rows = engineMountRows();
  const live = rows.filter((r) => !r.aliased);
  const auto = live.filter((r) => r.auto).length;
  const accel = live.filter((r) => r.accel === CEL_ID).length;
  const net = live.filter((r) => r.net === AEG_ID).length;
  const nlp = live.filter((r) => r.nlp !== "—").length;
  const nlpOk = NLP_TOOLS.every((t) => t.status === "ok");
  return [
    { id: "EM_N", metric: "活路", value: String(live.length), light: "ok", note: `ALIAS ${rows.length - live.length}` },
    { id: "EM_REG", metric: "自動編號", value: `${auto}/${live.length}`, light: "warn", note: "僅 CEL／EnvManager 有 VIS- 編號" },
    { id: "EM_ACC", metric: "加速→CEL", value: `${accel}/${live.length}`, light: accel ? "ok" : "bad", note: "accel=true 一律 ACC-CEL" },
    { id: "EM_NET", metric: "網路→AEG", value: String(net), light: "ok", note: "net=true 一律 NET-AEG · LIVE 關" },
    { id: "EM_NLP", metric: "NLP 掛", value: String(nlp), light: nlpOk ? "ok" : "warn", note: "063 詞庫／OCR／062／064／066／OFIE／MDE／USIP" },
  ];
}

export function engineMountNote(): string {
  const qc = engineMountQc();
  const acc = qc.find((r) => r.id === "EM_ACC")?.value ?? "—";
  const net = qc.find((r) => r.id === "EM_NET")?.value ?? "—";
  return `掛載 CEL ${acc} · AEG ${net} · 自動編號僅 CEL／ENV · LIVE 關`;
}
