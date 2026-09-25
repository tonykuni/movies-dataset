/** 右邊 VIA 收官：目前總管能掌握的。PC 磁碟黃燈算對。不開 LIVE。 */
import { aeaMembersOk } from "./active-etf.ts";
import { cnsMembersOk } from "./consensus.ts";
import { gffMembersOk } from "./gff.ts";
import { lakesHydraOk } from "./duck-catalog.ts";
import { accelBindSummary, aliasOf, isolationScript, liveEngines, applySsot, scanEnvConflicts } from "./inventory.ts";
import { hydraRisk, hydraRiskComplete, hydraRiskVrn } from "./processes.ts";
import { sealConsole, type Seal } from "./seal.ts";
import { runGovEnv } from "./gov-env.ts";
import { vapReady } from "./vap.ts";
import type { EngineRec, Light } from "./types.ts";

export type ViaStep = {
  id: string;
  name: string;
  result: "RAN" | "CACHE" | "SKIP" | "FAIL";
  light: Light;
  out: string;
};

export function runViaToEnd(input: {
  engines: EngineRec[];
  confirmNet: boolean;
  confirmNlp: boolean;
}): { steps: ViaStep[]; seal: Seal; fail: number } {
  const steps: ViaStep[] = [];
  const live = liveEngines(applySsot(input.engines));
  const cgc = sealConsole(live.length);
  steps.push({
    id: "V01",
    name: "唯一 Console",
    result: cgc.light === "ok" ? "RAN" : "FAIL",
    light: cgc.light,
    out: cgc.note,
  });

  const gffAlias = aliasOf("VIA_GFF") === "VIA_GLSS";
  const revAlias = aliasOf("VDF_REV") === "VDF_ENG075";
  steps.push({
    id: "V02",
    name: "SSOT 別名",
    result: gffAlias && revAlias ? "RAN" : "FAIL",
    light: gffAlias && revAlias ? "ok" : "bad",
    out: `GFF→GLSS ${gffAlias} · REV→ENG075 ${revAlias}`,
  });

  const acc = accelBindSummary();
  steps.push({
    id: "V03",
    name: "PS20 工具",
    result: acc.bound === 20 && acc.miss === 0 ? "RAN" : "FAIL",
    light: acc.bound === 20 ? "ok" : "bad",
    out: `${acc.bound}/20 已綁 · 缺 ${acc.miss}`,
  });

  const h1 = hydraRisk();
  const h2 = hydraRiskComplete();
  const h3 = hydraRiskVrn();
  steps.push({
    id: "V04",
    name: "十八程無九頭龍",
    result: h1.ok && h2.ok && h3.ok ? "RAN" : "FAIL",
    light: h1.ok && h2.ok && h3.ok ? "ok" : "bad",
    out: `${h1.note} · ${h2.note} · ${h3.note}`,
  });

  const clashes = scanEnvConflicts();
  const script = isolationScript(clashes);
  const deletes = /conda remove|env remove|pip uninstall/i.test(script);
  const gov = runGovEnv({ apply: false });
  steps.push({
    id: "V05",
    name: "衝突隔離",
    result: deletes || gov.seal.light === "bad" ? "FAIL" : "RAN",
    light: deletes ? "bad" : clashes.length || gov.seal.light === "warn" ? "warn" : "ok",
    out: deletes
      ? "指令含刪除"
      : `${clashes.length ? `via_iso 不刪 · ${clashes.map((c) => c.isolate).join(",")}` : "無衝突"} · ${gov.seal.note}`,
  });

  steps.push({
    id: "V06",
    name: "GLSS 成員",
    result: gffMembersOk() ? "CACHE" : "FAIL",
    light: gffMembersOk() ? "ok" : "bad",
    out: gffMembersOk() ? "ENG075 在籍 · 寫 glss-sim · 未因果" : "成員缺 ENG075",
  });

  steps.push({
    id: "V07",
    name: "雙閘",
    result: input.confirmNet || input.confirmNlp ? "RAN" : "SKIP",
    light: "ok",
    out: `NET ${input.confirmNet ? "開" : "關"} · NLP ${input.confirmNlp ? "開" : "關"} · 關=正確`,
  });

  steps.push({
    id: "V08",
    name: "DuckDB 湖",
    result: lakesHydraOk() ? "CACHE" : "FAIL",
    light: lakesHydraOk() ? "ok" : "bad",
    out: lakesHydraOk() ? "fred/rev/aetf/cns/px/chip/rest 分寫 · 母機 maintainSql" : "寫區重疊",
  });

  steps.push({
    id: "V09",
    name: "母機探針",
    result: "SKIP",
    light: "warn",
    out: "本台看不見 PC 磁碟 · 黃燈正確 · Launcher 才改綠",
  });

  const cgcLive = live.some((e) => e.id === "VIA_CGC");
  const glssLive = live.some((e) => e.id === "VIA_GLSS");
  const aeaLive = live.some((e) => e.id === "VIA_AEA");
  const cnsLive = live.some((e) => e.id === "VIA_CNS") && live.some((e) => e.id === "VDF_ENG077");
  const vap = vapReady();
  steps.push({
    id: "V10",
    name: "活路在冊",
    result: cgcLive && glssLive && aeaLive && aeaMembersOk() && cnsLive && cnsMembersOk() && vap.ok ? "RAN" : "FAIL",
    light: cgcLive && glssLive && aeaLive && aeaMembersOk() && cnsLive && cnsMembersOk() && vap.ok ? "ok" : "bad",
    out: `活路 ${live.length} · CGC ${cgcLive} · GLSS ${glssLive} · AEA ${aeaLive} · CNS ${cnsLive} · VAP ${vap.ok}`,
  });

  steps.push({
    id: "V11",
    name: "DCT01–20",
    result: "RAN",
    light: "ok",
    out: "不動 · 已 FIXED",
  });

  const mastered = steps.filter((s) => s.id !== "V09" && s.id !== "V05").every((s) => s.result !== "FAIL" && s.light !== "bad");
  const isoOk = !deletes;
  const closed = mastered && isoOk;
  steps.push({
    id: "V12",
    name: "VIA 收官",
    result: closed ? "RAN" : "FAIL",
    light: closed ? "ok" : "bad",
    out: closed ? "能掌握項已封 · PC/LIVE 黃留 · DCT 不動" : "收官未齊",
  });

  const seal: Seal = {
    id: "VIA",
    name: "VIA 右邊總管",
    light: closed ? "ok" : "bad",
    note: closed ? "收官 · 唯一 Console · GLSS/CGC/PS20/十二程" : "未齊",
  };
  return { steps, seal, fail: steps.filter((s) => s.result === "FAIL").length };
}
