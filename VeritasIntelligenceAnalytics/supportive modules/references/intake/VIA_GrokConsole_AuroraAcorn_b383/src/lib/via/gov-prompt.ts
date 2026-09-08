/** 由 GOV_SPEC 生成可改旗艦 Prompt。改規範請改 gov-spec.ts。Mega 原文在 gov-mega.ts。 */
import { megaBoundText } from "./gov-mega.ts";
import {
  GOV_ACCEL,
  GOV_ENVS,
  GOV_ID,
  GOV_INVARIANTS,
  GOV_LAUNCHER,
  GOV_LOG,
  GOV_LOOP,
  GOV_PIPELINES,
  GOV_REQUIRED_LIBS,
  GOV_ROUNDS,
  GOV_ZONES,
  LKGC_UV,
  UV_CLASH_TOOLS,
  UV_MIRRORS,
} from "./gov-spec.ts";

export function govPrompt(lang: "zh" | "en" = "zh"): string {
  const acc = GOV_ACCEL.map((a) => `${a.id} ${a.name}`).join(" · ");
  const pipes = GOV_PIPELINES.map((p) => `${p.id} ${p.name} write=${p.write}`).join("\n");
  const envs = GOV_ENVS.map((e) => `${e.id} (${e.role}) ${e.note}`).join("\n");
  const inv = GOV_INVARIANTS.map((x, i) => `${i + 1}. ${x}`).join("\n");
  const mirrors = UV_MIRRORS.map((m) => `${m.id} ${m.url}`).join(" · ");
  const clash = UV_CLASH_TOOLS.map((t) => `${t.id} ${t.name}`).join(" · ");
  if (lang === "en") {
    return [
      `Activate ${GOV_ID}: VIA Central Governance Console EnvManager.`,
      `Future-action SSOT: mega-prompt sealed; "pull risk" = via_iso_* isolate not delete.`,
      `Enable GA-01–20 (governance) AND keep PS-01–20 (data) disjoint.`,
      `Mirrors race from LKGC ${LKGC_UV.when}: ${mirrors}`,
      `UV clash tools UVT-01–08: ${clash}`,
      `Envs:\n${envs}`,
      `Invariants:\n${inv}`,
      `Pipelines:\n${pipes}`,
      `Rounds: ${GOV_ROUNDS.map((r) => `R${r.id} ${r.name}`).join(" → ")}`,
      `Libs must exist: ${GOV_REQUIRED_LIBS.join(", ")}`,
      `UI zones: ${GOV_ZONES.join(" / ")} · small font · wrap · RYG`,
      `Loop: ${GOV_LOOP}`,
      `Log ${GOV_LOG} · launcher ${GOV_LAUNCHER} · no spawn on console host · isolate not delete`,
      `Accelerators: ${acc}`,
    ].join("\n\n");
  }
  return [
    `啟動 ${GOV_ID}：VIA Central Governance Console 環境治理引擎。`,
    megaBoundText(),
    `GA-01–20 治理加速器全開；PS-01–20 資料加速器分冊不混 ID。`,
    `鏡像競向（LKGC ${LKGC_UV.when} 清華冠）：${mirrors}`,
    `衝突快檢：${clash}`,
    `環境拓撲：\n${envs}`,
    `不變約束：\n${inv}`,
    `六程（寫區互斥）：\n${pipes}`,
    `三輪：${GOV_ROUNDS.map((r) => `第${r.id}輪 ${r.name}`).join(" → ")}`,
    `必裝函式庫：${GOV_REQUIRED_LIBS.join("、")}`,
    `HTML 四分區：${GOV_ZONES.join("／")} · 小字 · 自動換行 · 紅黃綠`,
    `循環：${GOV_LOOP}`,
    `日誌 ${GOV_LOG} · 啟動器 ${GOV_LAUNCHER} · 本台不 spawn · 衝突隔離不刪`,
    `加速器：${acc}`,
  ].join("\n\n");
}
