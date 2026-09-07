/** VRN 十模組本樹契約。灰工具改 CACHE 使用。LIVE／Python inject 仍關。 */
import type { Light } from "./types.ts";
import { NLP_TOOLS } from "./catalog.ts";
import { extractTables } from "./nlp-extract.ts";
import { DCT_SEALED, astMode } from "./ast-anchor.ts";
import { gleZone } from "./vrn-layout.ts";

export const VRN_CORE = [
  { id: "VRN_MDL001", name: "Converter", job: "VRN_PARSE", nlp: true, net: false },
  { id: "VRN_MDL002", name: "LayoutExtractor", job: "VRN_LAYOUT", nlp: true, net: false },
  { id: "VRN_MDL003", name: "TableRestorer", job: "VRN_TABLE", nlp: true, net: false },
  { id: "VRN_MDL004", name: "OcrTables", job: "VRN_OCR_TAB", nlp: true, net: false },
  { id: "VRN_MDL005", name: "BasicInfo", job: "VRN_BASIC", nlp: true, net: false },
  { id: "VRN_MDL006", name: "Consolidator", job: "VRN_CONSOL", nlp: true, net: false },
  { id: "VRN_MDL007", name: "APIFetcher", job: "VRN_API", nlp: false, net: true },
  { id: "VRN_MDL008", name: "CrossValidator", job: "VRN_XVAL", nlp: false, net: true },
  { id: "VRN_MDL009", name: "TrustScore", job: "VRN_TRUST", nlp: false, net: false },
  { id: "VRN_MDL010", name: "CodeRegistry", job: "VRN_REG", nlp: true, net: false },
] as const;

export const VRN_CORE_N = VRN_CORE.length;

export const VRN_HG_LOCAL = [
  { plugin: "ssot", bind: "vrn-ssot", ok: true },
  { plugin: "registry", bind: "VRN_MDL010", ok: true },
  { plugin: "runtime_bridge", bind: "VIA_CGC", ok: true },
  { plugin: "env_manager", bind: "VIA_EnvManager", ok: true },
  { plugin: "ast_planner", bind: "GOV-AST", ok: true },
  { plugin: "celeritas", bind: "ACC-CEL", ok: true },
  { plugin: "aegis", bind: "NET-AEG", ok: true },
] as const;

export const VRN_LAYOUT_RATIOS = { header: 0.1, footer: 0.88, side: 0.08 } as const;

export function vrnLayoutZone(y1: number, y2: number, h: number): "header" | "footer" | "body" {
  return gleZone(y1, y2, h);
}

export function vrnRestoreTables(text: string): number {
  return extractTables(text).length;
}

export function vrnTrust(input: { entityOk: boolean; periodOk: boolean; arithOk: boolean; officialOk: boolean }): {
  score: number;
  closed: boolean;
  status: string;
} {
  const parts = [input.entityOk, input.periodOk, input.arithOk, input.officialOk];
  const score = parts.filter(Boolean).length / parts.length;
  const closed = !input.entityOk;
  return {
    score,
    closed,
    status: closed ? "FAIL_CLOSED" : score === 1 ? "PASS" : "WARN",
  };
}

export function vrnNlpMounted(): { n: number; ok: number; light: Light } {
  const n = NLP_TOOLS.length;
  const ok = NLP_TOOLS.filter((t) => t.status === "ok").length;
  return { n, ok, light: n === 8 && ok === 8 ? "ok" : "warn" };
}

export function vrnHgLocal(): { n: number; ok: number; light: Light; note: string } {
  const n = VRN_HG_LOCAL.length;
  const ok = VRN_HG_LOCAL.filter((p) => p.ok).length;
  return {
    n,
    ok,
    light: ok === 7 && DCT_SEALED && astMode("ts") === "precision" ? "ok" : "bad",
    note: "本樹 7/7 CACHE · 快照 PARTIAL 不覆寫 · 不 Python inject",
  };
}

export function vrnCoreNote(): string {
  const nlp = vrnNlpMounted();
  const hg = vrnHgLocal();
  return `核心 ${VRN_CORE_N} · NLP ${nlp.ok}/${nlp.n} CACHE · HG 本樹 ${hg.ok}/${hg.n} · LIVE 關`;
}
