/** VIA_EnvManager Unified Governance Engine。從 LKGC 擴張 · 本台只檢查不 spawn。 */
import { GOV_ENVS, GOV_LOG, LKGC_UV } from "./gov-spec.ts";
import { runGovEnv } from "./gov-env.ts";
import { isolationSteps, scanEnvConflicts } from "./inventory.ts";
import type { Light } from "./types.ts";

export const ENV_MGR_ID = "VIA_EnvManager";
export const ENV_MGR_WHEN = "2026-09-07";

/** 過往 log 教訓 · 計畫必讀 · 不重蹈 */
export const GOV_LESSONS = [
  { id: "L01", when: "2026-09-06", light: "ok" as Light, note: "拔除≠刪 · 立 via_iso_* · 禁 conda remove／uninstall" },
  { id: "L02", when: "2026-09-06", light: "warn" as Light, note: "numpy 1.26.4 base vs 2.1.1 via_vdf → via_iso_numpy" },
  { id: "L03", when: "2026-09-06", light: "ok" as Light, note: "CPython 無 pandas · 湖用 duckdb · 不混 user site" },
  { id: "L04", when: "2026-09-06", light: "ok" as Light, note: "ingest 逐檔 date／as_of／ym 切年 · COPY_ONLY" },
  { id: "L05", when: "2026-09-06", light: "ok" as Light, note: "ETF as_of 民國 1150826 → 1911+年" },
  { id: "L06", when: "2026-09-06", light: "ok" as Light, note: "ISO99 永禁刪／卸載／殺行程" },
  { id: "L07", when: "2026-09-07", light: "ok" as Light, note: "三鏡競向清華冠 · LKGC 維持 · 未同意不切鏡" },
  { id: "L08", when: "2026-09-07", light: "ok" as Light, note: "UVT-01–08 與 GA／PS 分冊 · 不混 ID" },
  { id: "L09", when: "2026-09-07", light: "ok" as Light, note: "R3「刪死碼」＝不刪檔 · 只鎖 freeze／lock" },
  { id: "L10", when: "2026-09-07", light: "ok" as Light, note: "via_isolated_*／via_lib_plotly_v* 正名 via_iso_*" },
] as const;

export function runEnvManager(input: { consent?: boolean } = {}): {
  id: string;
  consent: boolean;
  apply: boolean;
  envs: { id: string; role: string; note: string }[];
  lessons: typeof GOV_LESSONS;
  gov: ReturnType<typeof runGovEnv>;
  iso: ReturnType<typeof isolationSteps>;
  log: string[];
  plan: string;
  light: Light;
  note: string;
} {
  const consent = Boolean(input.consent);
  const gov = runGovEnv({ apply: consent });
  const hits = scanEnvConflicts();
  const iso = isolationSteps(hits);
  const log = [
    `${ENV_MGR_WHEN} SCAN base／via_core／via_* · ${GOV_ENVS.length} 槽`,
    `${ENV_MGR_WHEN} RACE ${gov.race.note}`,
    `${ENV_MGR_WHEN} CLASH ${gov.clash.note}`,
    `${ENV_MGR_WHEN} LKGC ${LKGC_UV.when} ${LKGC_UV.winner} · freeze ${LKGC_UV.freeze}`,
    `${ENV_MGR_WHEN} LESSON ${GOV_LESSONS.length} 條 · 計畫只新增`,
    consent
      ? `${ENV_MGR_WHEN} CONSENT YES · 指令留母機 · 本台不 spawn · log ${GOV_LOG}`
      : `${ENV_MGR_WHEN} CONSENT NO · 沙盒計畫 · 不執行`,
  ];
  const plan = [
    `基於 LKGC ${LKGC_UV.when} 成功組合擴張`,
    `鏡像冠 ${gov.race.winner} · 八路 ${gov.clash.ok}/8`,
    hits.length ? `隔離 ${hits.map((h) => h.isolate).join(",")} · 不刪 base` : "無新槽",
    `建構 CACHE 槽 ${hits.length ? "iso 已列" : "齊"} · 鎖檔 ${LKGC_UV.freeze}`,
    consent ? "同意已錄 · 母機 launch.ps1／VIA_EnvManager.py" : "待使用者同意才 APPLY",
  ].join(" · ");
  const light: Light = gov.clash.fail ? "bad" : hits.length || gov.clash.warn ? "warn" : "ok";
  return {
    id: ENV_MGR_ID,
    consent,
    apply: gov.apply,
    envs: GOV_ENVS.map((e) => ({ id: e.id, role: e.role, note: e.note })),
    lessons: GOV_LESSONS,
    gov,
    iso,
    log,
    plan,
    light,
    note: `${ENV_MGR_ID} · ${plan}`,
  };
}
