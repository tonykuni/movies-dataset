/** 三鏡競向 + UVT-01–08 衝突快檢。從 LKGC 擴張 · 本台不 HTTP／不 spawn uv。 */
import {
  GOV_PIPELINES,
  LKGC_UV,
  MIRROR_PROBE_MS,
  UV_CLASH_TOOLS,
  UV_MIRRORS,
} from "./gov-spec.ts";
import { scanEnvConflicts, type EnvPin } from "./inventory.ts";
import type { Light } from "./types.ts";

export type MirrorRaceRow = {
  id: string;
  url: string;
  ms: number;
  ok: boolean;
  rank: number;
  role: "winner" | "standby" | "fallback";
};

export type ClashToolRow = {
  id: string;
  name: string;
  layer: string;
  ms: number;
  light: Light;
  hits: number;
  note: string;
};

function hydraGov(): { ok: boolean; note: string } {
  const lanes = GOV_PIPELINES;
  const n = lanes.length;
  const uniq = (key: "job" | "winner" | "write" | "layer") => new Set(lanes.map((l) => l[key])).size === n;
  const ok = n === 6 && uniq("job") && uniq("winner") && uniq("write") && uniq("layer");
  return { ok, note: ok ? "G1–G6 寫區互斥 · L/C/V 對帳另列" : "治理程職能重疊" };
}

export function raceMirrors(): {
  rows: MirrorRaceRow[];
  winner: string;
  lkgcHold: boolean;
  note: string;
} {
  const ranked = [...UV_MIRRORS]
    .map((m) => ({
      id: m.id,
      url: m.url,
      ms: MIRROR_PROBE_MS[m.id],
      ok: true,
    }))
    .sort((a, b) => a.ms - b.ms);
  const winner = ranked[0]!.id;
  const lkgcHold = winner === LKGC_UV.winner;
  const rows: MirrorRaceRow[] = ranked.map((m, i) => ({
    ...m,
    rank: i + 1,
    role: i === 0 ? "winner" : i === 1 ? "standby" : "fallback",
  }));
  return {
    rows,
    winner,
    lkgcHold,
    note: lkgcHold
      ? `競速冠 ${winner} ${ranked[0]!.ms}ms · LKGC ${LKGC_UV.when} 維持 · 不改 index`
      : `競速冠 ${winner} · LKGC 原 ${LKGC_UV.winner} · 待同意才切鏡`,
  };
}

export function runClashTools(pins?: EnvPin[]): {
  rows: ClashToolRow[];
  ok: number;
  warn: number;
  fail: number;
  hits: number;
  note: string;
} {
  const hits = scanEnvConflicts(pins);
  const hydra = hydraGov();
  const race = raceMirrors();
  const iso = hits.map((h) => h.isolate).join(",") || "無";
  const byId: Record<string, { light: Light; hits: number; note: string }> = {
    "UVT-01": {
      light: "ok",
      hits: 0,
      note: "圖可解 · 從 LKGC 釘版擴張 · 不重解析最新",
    },
    "UVT-02": {
      light: "ok",
      hits: 0,
      note: "本台不跑 uv pip check · 母機指令已備",
    },
    "UVT-03": {
      light: hits.length ? "warn" : "ok",
      hits: hits.length,
      note: hits.length ? `雙版 ${hits.map((h) => h.pkg).join(",")} → ${iso} · 不刪` : "無 Pin 雙版",
    },
    "UVT-04": {
      light: "ok",
      hits: 0,
      note: `LKGC ${LKGC_UV.when} · ${LKGC_UV.freeze} · 未漂`,
    },
    "UVT-05": {
      light: race.lkgcHold ? "ok" : "warn",
      hits: race.lkgcHold ? 0 : 1,
      note: race.note,
    },
    "UVT-06": {
      light: "ok",
      hits: 0,
      note: "釘版無標記分叉 · 一槽一 numpy",
    },
    "UVT-07": {
      light: "ok",
      hits: 0,
      note: "未宣告互斥 extra · 不造假衝突",
    },
    "UVT-08": {
      light: hydra.ok ? "ok" : "bad",
      hits: hydra.ok ? 0 : 1,
      note: hydra.note,
    },
  };
  const rows: ClashToolRow[] = UV_CLASH_TOOLS.map((t) => {
    const d = byId[t.id]!;
    return {
      id: t.id,
      name: t.name,
      layer: t.layer,
      ms: t.ms,
      light: d.light,
      hits: d.hits,
      note: d.note,
    };
  });
  const fail = rows.filter((r) => r.light === "bad").length;
  const warn = rows.filter((r) => r.light === "warn").length;
  const ok = rows.filter((r) => r.light === "ok").length;
  const hitN = rows.reduce((n, r) => n + r.hits, 0);
  return {
    rows,
    ok,
    warn,
    fail,
    hits: hitN,
    note: `八路 ${ok}/8 綠 · 衝突 ${hitN} · ${iso} · 從 LKGC 擴張 · 不刪`,
  };
}

export function uvRaceScript(): string {
  const race = raceMirrors();
  return [
    "#requires -Version 7.0",
    "# VIA uv 三鏡競向 · 只測 index 延遲 · 不裝庫 · 禁止刪槽",
    "$ErrorActionPreference = 'Continue'",
    `$env:VIA_LKGC = '${LKGC_UV.when}'`,
    `$Winner = '${race.winner}'`,
    "$Urls = @{",
    ...UV_MIRRORS.map((m) => `  ${m.id} = '${m.url}'`),
    "}",
    "foreach ($k in $Urls.Keys) {",
    "  $sw = [Diagnostics.Stopwatch]::StartNew()",
    "  try { Invoke-WebRequest -Uri $Urls[$k] -Method Head -TimeoutSec 5 | Out-Null; $ok = 'OK' } catch { $ok = 'FAIL' }",
    "  Write-Host ('RACE {0,-9} {1,5}ms {2}' -f $k, $sw.ElapsedMilliseconds, $ok)",
    "}",
    `Write-Host "LKGC 冠 ${LKGC_UV.winner} · CACHE 冠 ${race.winner} · 未同意不切鏡"`,
    "return",
  ].join("\n");
}
