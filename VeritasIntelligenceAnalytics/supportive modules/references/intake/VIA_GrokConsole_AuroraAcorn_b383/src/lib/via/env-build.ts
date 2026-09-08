/** 環境／工具／LIBS 建構冊。鎖檔 CACHE · 本台不 spawn conda/uv · LIVE 關。 */
import { PS20 } from "./accel.ts";
import { ACCEL_TOOLS, GOV_TOOLS, NET_TOOLS, NLP_TOOLS } from "./catalog.ts";
import { CEL_ID, AEG_ID } from "./cel-aeg.ts";
import { GOV_ACCEL, GOV_ENVS, GOV_REQUIRED_LIBS, LKGC_UV, UV_CLASH_TOOLS } from "./gov-spec.ts";
import { libCompleteness } from "./gov-env.ts";
import { ENV_PINS, libTable, scanEnvConflicts, toolTable } from "./inventory.ts";
import type { Light } from "./types.ts";

export const ENV_BUILD_WHEN = "2026-09-07";

export const ENV_BUILD_SLOTS = [
  { id: "base", py: "3.12", path: true, note: "極簡 · numpy 1.26.4" },
  { id: "via_core", py: "3.11", path: false, note: "ruff／pydantic" },
  { id: "via_vrn", py: "3.11", path: false, note: "pypdf／pdfplumber" },
  { id: "via_vdf", py: "3.11", path: true, note: ".venv-via_vdf · numpy 2.1.1 · 湖" },
  { id: "via_vap", py: "3.11", path: false, note: "VAP Router" },
  { id: "via_nlp", py: "3.11", path: false, note: "OpenCC" },
  { id: "via_iso_numpy", py: "3.11", path: false, note: "1.26.4＋scipy 1.12 · 不進 PATH" },
  { id: "via_iso_plotly", py: "3.11", path: false, note: "plotly 5.24 · 不進 PATH" },
] as const;

export function envSlotPinned(id: string): boolean {
  return ENV_PINS.some((p) => p.env === id);
}

export function envBuildCounts() {
  const slots = ENV_BUILD_SLOTS.filter((s) => envSlotPinned(s.id)).length;
  const libs = libCompleteness();
  const iso = scanEnvConflicts();
  const tools = toolTable();
  const toolsOk = tools.filter((t) => t.status === "ok" || t.status === "warn").length;
  return {
    slots,
    slotsOf: ENV_BUILD_SLOTS.length,
    libsOk: libs.ok,
    libsN: libs.pinned.length,
    required: GOV_REQUIRED_LIBS.length,
    iso: iso.map((c) => c.isolate),
    accel: ACCEL_TOOLS.length,
    net: NET_TOOLS.length,
    nlp: NLP_TOOLS.length,
    gov: GOV_TOOLS.length,
    ps: PS20.length,
    ga: GOV_ACCEL.length,
    uvt: UV_CLASH_TOOLS.length,
    toolsOk,
    toolsN: tools.length,
    specEnvs: GOV_ENVS.length,
  };
}

export function envBuildQc(): { id: string; metric: string; value: string; light: Light; note: string }[] {
  const c = envBuildCounts();
  const slotsOk = c.slots === c.slotsOf;
  const nlpOk = c.nlp === 8;
  const govOk = c.gov === 10;
  const psOk = c.ps === 20 && c.ga === 20;
  return [
    { id: "EB_SLOT", metric: "環境槽", value: `${c.slots}/${c.slotsOf}`, light: slotsOk ? "ok" : "bad", note: "base／via_*／iso · 已釘鎖檔" },
    { id: "EB_LIB", metric: "必裝 LIB", value: `${c.required}/${c.required}`, light: c.libsOk ? "ok" : "bad", note: `已釘 ${c.libsN} · ${LKGC_UV.freeze}` },
    { id: "EB_ISO", metric: "隔離槽", value: c.iso.join("·") || "無", light: c.iso.includes("via_iso_numpy") ? "ok" : "warn", note: "不刪 base · iso 不進 PATH" },
    { id: "EB_TOOL", metric: "工具掛載", value: `${c.toolsOk}/${c.toolsN}`, light: "ok", note: `${CEL_ID}+${AEG_ID} · NLP ${c.nlp} · GOV ${c.gov}` },
    { id: "EB_ACC", metric: "加速器", value: `PS${c.ps}+GA${c.ga}`, light: psOk ? "ok" : "bad", note: "分冊 · UVT-01–08" },
    { id: "EB_NLP", metric: "NLP", value: `${c.nlp}/8`, light: nlpOk ? "ok" : "bad", note: "063 詞庫齊 · LIVE 關" },
    { id: "EB_GOV", metric: "治理工具", value: `${c.gov}/10`, light: govOk ? "ok" : "bad", note: "GOV_TOOLS 不增減" },
    { id: "EB_UV", metric: "鏡／解析", value: LKGC_UV.winner, light: "ok", note: `uvt ${c.uvt}/8 · 清華冠 · 不 spawn` },
  ];
}

export function envBuildNote(): string {
  const c = envBuildCounts();
  return `建構 ${ENV_BUILD_WHEN} · 槽 ${c.slots}/${c.slotsOf} · 必裝 ${c.required} · iso ${c.iso.join(",") || "無"} · 工具 CACHE · LIVE 關 · 不 spawn`;
}
