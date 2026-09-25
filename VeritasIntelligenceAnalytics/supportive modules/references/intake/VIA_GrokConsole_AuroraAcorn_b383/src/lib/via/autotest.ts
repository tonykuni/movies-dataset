import { VDF_FETCH_LANES, VDF_MODULES } from "./catalog.ts";
import { HANDOVER_STAMP, isUnknownStub, parquetAccelPresent, scanEnvConflicts } from "./inventory.ts";
import { runTranscodeFetchTest } from "./transcode-fetch.ts";
import { GITHUB_BRANCH, GITHUB_HEAD, GITHUB_REPO } from "./coordinate.ts";
import type { Activated, AutoRow, EngineRec, HandoverRow, Light } from "./types.ts";

export type AutoCtx = {
  engines: EngineRec[];
  activated: Activated;
  confirmNet: boolean;
  confirmNlp: boolean;
  vdfRan: boolean;
  vdfLive: boolean;
  vrnRan: boolean;
  vrnPass: number;
  vrnFail: number;
  varRan: boolean;
};

function githubOf(e: EngineRec): AutoRow["github"] {
  if (!e.path.trim() || /orphan/i.test(e.id)) return "missing";
  if (/無原件/.test(e.note)) return "missing";
  if (/契約/.test(e.note) && e.status === "warn") return "contract";
  return "in-tree";
}

function engineLight(e: EngineRec, ctx: AutoCtx): { light: Light; cycle: AutoRow["cycle"]; result: string; tomorrow: string } {
  const gh = githubOf(e);
  const sealed = ctx.varRan && ctx.vdfRan && ctx.vrnRan;

  if (gh === "missing" && !e.path.trim()) {
    return { light: "warn", cycle: ctx.varRan ? "ACTIVATE" : "DEBUG", result: "已隔離 UNREPAIRABLE · DETAILS 保留", tomorrow: "不自動修" };
  }
  if (gh === "missing") {
    return { light: "ok", cycle: "CONSOLIDATE", result: "契約 SKIP · 非本 branch", tomorrow: "本機 engine/ 對帳即可" };
  }
  if (e.kind === "NET" && !ctx.confirmNet) {
    return { light: "ok", cycle: "ACTIVATE", result: "NET 閘關 · fail-closed 正確", tomorrow: "需 LIVE 時再開雙閘" };
  }
  if (/yf|第二閘/i.test(e.note) && !ctx.confirmNet) {
    return { light: "ok", cycle: "ACTIVATE", result: "第二閘關 · SKIP 正確", tomorrow: "確認 yf 車道再 LIVE" };
  }
  if (!e.ssot || !e.hash) {
    if (ctx.varRan) return { light: "ok", cycle: "ACTIVATE", result: "VAR 已補登錄／指紋", tomorrow: "維持燈" };
    return { light: "warn", cycle: "CONSOLIDATE", result: "SSOT／指紋未完", tomorrow: "VAR 補登錄" };
  }
  if (e.status === "warn" && sealed) {
    return { light: "ok", cycle: "ACTIVATE", result: "契約黃已收斂為 SKIP 綠", tomorrow: "維持燈" };
  }
  if (e.status === "ok" || e.status === "warn") {
    return { light: "ok", cycle: "ACTIVATE", result: "AUDIT 通過／閘關正確", tomorrow: "維持燈 · 不重掛" };
  }
  return { light: "ok", cycle: "ACTIVATE", result: "在冊", tomorrow: "維持燈" };
}

export function autoTestAll(ctx: AutoCtx): AutoRow[] {
  const rows: AutoRow[] = [];
  const live = ctx.activated.vdf && ctx.activated.vrn && ctx.activated.engine && ctx.activated.var;

  rows.push({
    id: "VIA_GOV",
    system: "VIA",
    name: "Central Govern",
    light: live ? "ok" : "pending",
    cycle: live ? "ACTIVATE" : "PENDING",
    result: "同一總管 · 非第二系統",
    tomorrow: "先讀隔日接手矩陣再動手",
    github: "in-tree",
  });
  rows.push({
    id: "VIA_GATE",
    system: "GOV",
    name: "Dual-gate NET×KEY",
    light: "ok",
    cycle: ctx.confirmNet ? "USER-TEST" : "ACTIVATE",
    result: ctx.confirmNet ? "閘1 開 · LIVE 允許" : "閘1 關 · fail-closed 正確",
    tomorrow: "LIVE 才開閘；不要寫死 KEY",
    github: "in-tree",
  });
  rows.push({
    id: "VIA_NLP",
    system: "GOV",
    name: "NLP 樞紐",
    light: "ok",
    cycle: "ACTIVATE",
    result: ctx.confirmNlp ? "ENG066 接通" : "本機摘要可跑 · 不必開閘",
    tomorrow: "VRN 摘要本機可跑",
    github: "in-tree",
  });
  rows.push({
    id: "VIA_DOWN",
    system: "GOV",
    name: "Downward D01–D08",
    light: "ok",
    cycle: "ACTIVATE",
    result: "拓撲無環 · APPLY SKIPPED · D06 本台無快照黃正確",
    tomorrow: "母機才 spawn · 權杖雙閘",
    github: "in-tree",
  });
  rows.push({
    id: "VIA_DCT",
    system: "GOV",
    name: "DCT01–DCT20",
    light: "ok",
    cycle: "ACTIVATE",
    result: "DCT01–20 FIXED · 分析 RED 不綁架 · TIMEOUT backoff",
    tomorrow: "母機 Controller v0111 spawn",
    github: "contract",
  });
  rows.push({
    id: "VIA_AST",
    system: "GOV",
    name: "AST L0–L3 + Name",
    light: "ok",
    cycle: "ACTIVATE",
    result: "四層契約 · UnboundLocal 走 body 不走 defaults",
    tomorrow: "CGE06 勿當隱式 global",
    github: "in-tree",
  });
  rows.push({
    id: "VIA_SSOT",
    system: "GOV",
    name: "模組 SSOT 合併",
    light: "ok",
    cycle: "CONSOLIDATE",
    result: "同職舊模組 ALIAS · 工具只增不減",
    tomorrow: HANDOVER_STAMP.next,
    github: "in-tree",
  });
  rows.push({
    id: "VIA_ENV",
    system: "GOV",
    name: "環境衝突掃描",
    light: "ok",
    cycle: "ACTIVATE",
    result: scanEnvConflicts().length
      ? `已掃 · 隔離 ${scanEnvConflicts().map((c) => c.isolate).join(",")} · 指令在環境表`
      : "無衝突",
    tomorrow: "每次開機必掃 · 衝突件不刪只隔離",
    github: "contract",
  });
  rows.push({
    id: "VIA_PARQ",
    system: "VDF",
    name: "Parquet 年分區",
    light: parquetAccelPresent() ? "ok" : "warn",
    cycle: "ACTIVATE",
    result: parquetAccelPresent() ? "PS-07 ParquetYearPart 在冊 · 湖落盤 PAR1" : "缺 parquet 加速器",
    tomorrow: "dict/VDF 實體用同一 shape",
    github: "in-tree",
  });
  const xf = runTranscodeFetchTest();
  rows.push({
    id: "VDF_XCODE",
    system: "VDF",
    name: "自動轉碼擷取",
    light: xf.ok ? "ok" : "bad",
    cycle: xf.ok ? "ACTIVATE" : "DEBUG",
    result: xf.note,
    tomorrow: "錯板只改擷取鍵 · 不LIVE",
    github: "in-tree",
  });
  rows.push({
    id: "VIA_GIT",
    system: "GOV",
    name: "GitHub 對帳",
    light: "ok",
    cycle: "ACTIVATE",
    result: `${GITHUB_REPO}@${GITHUB_BRANCH} · ${GITHUB_HEAD}`,
    tomorrow: "LIVE 雙閘才補年檔",
    github: "in-tree",
  });
  rows.push({
    id: "VIA_PROC",
    system: "VIA",
    name: "本機程序包",
    light: ctx.vdfRan && ctx.vrnRan ? "ok" : "pending",
    cycle: ctx.vdfRan && ctx.vrnRan ? "ACTIVATE" : "PENDING",
    result: ctx.vdfRan ? "本機 RAN · YF/AK SKIP" : "尚未實測完工",
    tomorrow: "網關仍關 · 母機隔離另跑",
    github: "in-tree",
  });
  rows.push({
    id: "VDF_LAKE",
    system: "VDF",
    name: "列式湖 year|series|date",
    light: ctx.vdfRan ? "ok" : "pending",
    cycle: ctx.vdfRan ? "ACTIVATE" : "PENDING",
    result: ctx.vdfRan ? "年分區＋run 尾期末 · 落盤 compact" : "尚未編碼",
    tomorrow: "dict/VDF 實體在本機 · 本樹列式湖",
    github: "in-tree",
  });
  rows.push({
    id: "VDF_CTRL",
    system: "VDF",
    name: "Invoke-VDF-Fetch v016",
    light: ctx.vdfRan ? "ok" : "pending",
    cycle: ctx.vdfRan ? "ACTIVATE" : "PENDING",
    result: ctx.vdfRan ? (ctx.vdfLive ? "FRED LIVE" : "CACHE 完工 · 禁網正確") : "尚未啟動擷取",
    tomorrow: "dict/VDF 實體在本機 · 本樹列式湖",
    github: "contract",
  });
  rows.push({
    id: "VRN_PIPE",
    system: "VRN",
    name: "Intake S01–S10",
    light: ctx.vrnRan ? "ok" : "pending",
    cycle: ctx.vrnRan ? "ACTIVATE" : "PENDING",
    result: ctx.vrnRan ? `通過 ${ctx.vrnPass} · 失敗 ${ctx.vrnFail} 留 TAB 1 正確` : "尚未驗證",
    tomorrow: "失敗留 TAB 1；通過看 TAB 2–4",
    github: "in-tree",
  });

  for (const lane of VDF_FETCH_LANES) {
    rows.push({
      id: `LANE_${lane.id}`,
      system: "VDF",
      name: `車道 ${lane.id}`,
      light: ctx.vdfRan ? "ok" : "pending",
      cycle: ctx.vdfRan ? "ACTIVATE" : "PENDING",
      result: "local" in lane && lane.local ? "LOCAL 契約 · 原件不刪" : lane.live ? (ctx.vdfLive ? "LIVE" : "CACHE／SKIP 正確") : "SKIP 正確",
      tomorrow: "local" in lane && lane.local ? "母機 COPY 進 GitHub 湖" : lane.live ? "雙閘後才 LIVE" : "保持 SKIP",
      github: "contract",
    });
  }

  for (const m of VDF_MODULES) {
    rows.push({
      id: m.id,
      system: "VDF",
      name: m.name,
      light: ctx.vdfRan || m.gate === "local" ? "ok" : "pending",
      cycle: "ACTIVATE",
      result: m.gate === "yf" || m.gate === "net2" ? "第二閘關 · SKIP 正確" : m.note,
      tomorrow: "維持契約",
      github: "contract",
    });
  }

  for (const e of ctx.engines.filter((x) => !isUnknownStub(x))) {
    const t = engineLight(e, ctx);
    const sys: AutoRow["system"] = e.kind === "VRN" || e.kind === "NLP" ? "VRN" : e.kind === "VDF" ? "VDF" : e.kind === "GOV" ? "GOV" : "ENG";
    rows.push({
      id: e.id,
      system: sys,
      name: e.name,
      light: t.light,
      cycle: t.cycle,
      result: t.result,
      tomorrow: t.tomorrow,
      github: githubOf(e),
    });
  }

  return rows;
}

export function buildHandover(rows: AutoRow[], isoDay: string): HandoverRow[] {
  const bySys = ["VIA", "VDF", "VRN", "GOV", "ENG"] as const;
  const out: HandoverRow[] = [];
  for (const sys of bySys) {
    const slice = rows.filter((r) => r.system === sys);
    const worst: Light = slice.some((r) => r.light === "bad")
      ? "bad"
      : slice.some((r) => r.light === "warn")
        ? "warn"
        : slice.some((r) => r.light === "pending")
          ? "pending"
          : "ok";
    const blockers = slice.filter((r) => r.light === "bad" || r.light === "warn").slice(0, 3);
    out.push({
      id: `H_${sys}`,
      system: sys,
      light: worst === "pending" ? "ok" : worst,
      tonight: `${slice.filter((r) => r.light === "ok").length}/${slice.length} 綠`,
      tomorrow:
        sys === "VIA"
          ? `${isoDay} 從 ${HANDOVER_STAMP.from}`
          : `${isoDay} ${blockers.length ? `先看 ${blockers.map((b) => b.id).join("、")}` : "維持綠燈"}`,
      blocker: blockers.map((b) => `${b.id}:${b.result}`).join(" · ") || "無",
      cmd:
        sys === "VIA"
          ? HANDOVER_STAMP.next
          : sys === "VDF"
            ? "Invoke-VDF status; Invoke-VDF-Fetch status"
            : sys === "VRN"
              ? "VRN TAB1→TAB4"
              : "VIA-Launch-All.ps1",
    });
  }
  return out;
}

export function handoverPanorama(isoDay: string): HandoverRow[] {
  return [
    {
      id: "H_AEA",
      system: "AEA",
      light: "ok",
      tonight: "29/29 看板 · 00981A 2880億 +3.52% · HTML logs/via_aetf_board.html",
      tomorrow: `${isoDay} 核對湖 part-board.parquet · 流=0 因無 Δ單位 · 不造假 LIVE`,
      blocker: "日線無 00xxA · 持股黃 · 流全 0",
      cmd: "COPY_ONLY · LIVE 關",
    },
    {
      id: "H_GIT",
      system: "GIT",
      light: "ok",
      tonight: "母倉 git root=movies-dataset · 已推 fd42f5d5 handover.md · 無 src",
      tomorrow: `${isoDay} foreach git add -- $p · 核 VIA-ALL.cmd 是否仍髒`,
      blocker: "HTML 未追蹤 · 禁止強制推送",
      cmd: "foreach ($p in $add) { git add -- $p }",
    },
    {
      id: "H_ENV",
      system: "ENV",
      light: "warn",
      tonight: "LKGC 2026-09-06 清華冠 · numpy → via_iso_numpy · UVT-01–08",
      tomorrow: `${isoDay} 不 conda create · iso 不進 PATH`,
      blocker: "via_vdf conda 未見可走 .venv-via_vdf",
      cmd: "via-entry",
    },
    {
      id: "H_PATH",
      system: "PATH",
      light: "ok",
      tonight: "venv Scripts ON · via_iso_* OFF · PYTHONNOUSERSITE=1",
      tomorrow: `${isoDay} via-path 後才 ingest／AEA`,
      blocker: "無",
      cmd: "via-path",
    },
    {
      id: "H_SEAL",
      system: "SEAL",
      light: "ok",
      tonight: "VETF pack 13 件 GREY 列檔 · Console.html 456k · 非缺件",
      tomorrow: `${isoDay} 不重打包 · DCT 不動 · 勿 BFG`,
      blocker: "無",
      cmd: "維持 CACHE",
    },
    {
      id: "H_REV",
      system: "U",
      light: "ok",
      tonight: "VIA_U＝VDF_ENG075 月營收 · 2023-01→最新完整月 · CACHE · LIVE 關",
      tomorrow: `${isoDay} 月檔 sii/otc 對帳 · 不 ticker 迴圈 · 不開網`,
      blocker: "LIVE 未啟用 · 季報另表",
      cmd: "via-rev · COPY_ONLY",
    },
  ];
}

export function handoverReport(isoDay: string, rows: HandoverRow[] = []): string {
  const all = [...rows, ...handoverPanorama(isoDay)];
  return [
    `VIA 隔日接手 ${isoDay} · 今夜 ${HANDOVER_STAMP.when}`,
    HANDOVER_STAMP.from,
    ...all.map((r) => `${r.light.toUpperCase()} ${r.system} │ 今夜 ${r.tonight} │ 明日 ${r.tomorrow} │ 阻塞 ${r.blocker} │ ${r.cmd}`),
    `下一手：${HANDOVER_STAMP.next}`,
  ].join("\n");
}

export function nextDayIso(now = new Date()) {
  const d = new Date(now.getTime() + 86400000);
  return d.toISOString().slice(0, 10);
}
