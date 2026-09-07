/** 實測通過後，還要測試閘過才封印。 */
import { FOLDER_SEEDS } from "./catalog.ts";
import { hydraRiskVrn, runVrnLanes } from "./processes.ts";
import { packBasic, packFinance, packSummary, parseFilename } from "./vrn.ts";
import { runVrnToEnd } from "./vrn-end.ts";
import type { Seal } from "./seal.ts";

export function vrnReady(confirmNlp = false): {
  ok: boolean;
  fail: number;
  r11: string;
  hydra: string;
} {
  const hydra = hydraRiskVrn();
  const files = FOLDER_SEEDS.map((f) => ({
    ...f,
    status: f.size === 0 ? ("bad" as const) : ("ok" as const),
    stuckStep: f.size === 0 ? "S04" : null,
  }));
  const pass = files.filter((f) => f.status !== "bad" && !(f.skipDup && f.dupOf));
  const basics = pass.map((f) => packBasic(f, parseFilename(f.name), "ok"));
  const summaries = pass.flatMap((f) => packSummary(f, parseFilename(f.name)));
  const finances = pass.flatMap((f) => packFinance(f, parseFilename(f.name), "ok"));
  const ended = runVrnToEnd({ files, basics, summaries, finances, confirmNlp });
  const lanes = runVrnLanes({
    confirmNet: false,
    fredMode: "CACHE",
    vdfRows: 0,
    parquetOk: true,
    vrnPass: pass.length,
    vrnFail: 1,
    confirmNlp,
  });
  const v6 = lanes.find((r) => r.id === "V6");
  const r11 = ended.steps.find((s) => s.id === "R11");
  const ok = hydra.ok && ended.fail === 0 && r11?.light === "ok" && v6?.light === "ok";
  return { ok, fail: ok ? 0 : 1, r11: r11?.out ?? "", hydra: hydra.note };
}

export function completeVrn(input: { confirmNlp?: boolean; testsPass: boolean }): {
  seal: Seal;
  fail: number;
  r11: string;
  hydra: string;
} {
  const ready = vrnReady(input.confirmNlp);
  if (!input.testsPass) {
    return {
      seal: {
        id: "VRN",
        name: "VRN 管線",
        light: "warn",
        note: "測試未過 · 不封印",
      },
      fail: 1,
      r11: ready.r11,
      hydra: ready.hydra,
    };
  }
  if (!ready.ok) {
    return {
      seal: {
        id: "VRN",
        name: "VRN 管線",
        light: "bad",
        note: `VRN 未齊 · ${ready.r11} · ${ready.hydra}`,
      },
      fail: 1,
      r11: ready.r11,
      hydra: ready.hydra,
    };
  }
  return {
    seal: {
      id: "VRN",
      name: "VRN 管線",
      light: "ok",
      note: "VRN 完工 · 測試已過 · R11 綠 · 四引擎 CACHE · vintage 不平均 · 台股 · NLP LIVE 關 · DCT 不動",
    },
    fail: 0,
    r11: ready.r11,
    hydra: ready.hydra,
  };
}
