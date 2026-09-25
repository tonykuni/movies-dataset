/** 依 GOV_SPEC 檢查／隔離環境。本台只模擬，不 spawn uv/conda。 */
import { isolationScript, libTable, lockfileYml, scanEnvConflicts, ENV_PINS, type EnvPin } from "./inventory.ts";
import { COMPLETE_LANES, SIX_LANES, VRN_LANES } from "./processes.ts";
import {
  GOV_ACCEL,
  GOV_PIPELINES,
  GOV_REQUIRED_LIBS,
  GOV_ROUNDS,
  GOV_ZONES,
  LKGC_UV,
  UV_MIRRORS,
} from "./gov-spec.ts";
import { raceMirrors, runClashTools, uvRaceScript } from "./uv-clash.ts";
import type { Light } from "./types.ts";
import type { Seal } from "./seal.ts";

export type GovIssue = {
  id: string;
  zone: (typeof GOV_ZONES)[number];
  kind: "parallel" | "sequence";
  light: Light;
  note: string;
};

export type GovRound = {
  id: number;
  name: string;
  kind: "parallel" | "sequence" | "harden";
  did: string;
  light: Light;
};

export function hydraRiskGov(lanes = GOV_PIPELINES): { ok: boolean; light: Light; note: string } {
  const n = lanes.length;
  const uniq = (key: "job" | "winner" | "write" | "layer") => new Set(lanes.map((l) => l[key])).size === n;
  const taken = new Set([...SIX_LANES, ...COMPLETE_LANES, ...VRN_LANES].map((l) => l.write));
  const clash = lanes.filter((l) => taken.has(l.write));
  const ok = n === 6 && uniq("job") && uniq("winner") && uniq("write") && uniq("layer") && clash.length === 0;
  return {
    ok,
    light: ok ? "ok" : "bad",
    note: ok ? "治理六程 · 與 L/C/V 不互寫" : `治理程重疊 ${clash.map((c) => c.write).join(",") || "職能"}`,
  };
}

export function libCompleteness(pins: EnvPin[] = ENV_PINS): { miss: string[]; pinned: string[]; ok: boolean } {
  const pinned = [...new Set(pins.filter((p) => p.pkg !== "python").map((p) => p.pkg))];
  const miss = GOV_REQUIRED_LIBS.filter((x) => !pinned.includes(x));
  return { miss: [...miss], pinned, ok: miss.length === 0 };
}

export function motherPathScript(): string {
  return [
    "#requires -Version 7.0",
    "# VIA LKGC PATH · 先進入專案環境 · 本台不 spawn conda/uv",
    "$ErrorActionPreference = 'Stop'",
    "$cands = @(",
    "  'C:\\Users\\tonyk\\movies-dataset\\VeritasIntelligenceAnalytics',",
    "  'C:\\Users\\tonyk\\Github\\movies-dataset\\VeritasIntelligenceAnalytics',",
    "  'C:\\Users\\tonyk\\OneDrive\\Documents\\movies-dataset\\VeritasIntelligenceAnalytics'",
    ")",
    "$Root = $cands | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1",
    "if ($Root) { Set-Location -LiteralPath $Root }",
    "$env:PYTHONNOUSERSITE = '1'",
    "$env:VIA_LKGC = '2026-09-06'",
    "$env:VIA_START_YEAR = '2023'",
    "$env:VIA_NET = '0'",
    "$vdf = @(($env:USERPROFILE + '\\miniconda3\\envs\\via_vdf'), 'C:\\Users\\tonyk\\miniconda3\\envs\\via_vdf') | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1",
    "if ($vdf) { $env:CONDA_PREFIX = $vdf; $env:CONDA_DEFAULT_ENV = 'via_vdf'; $env:PATH = ($vdf + ';' + $vdf + '\\Scripts;' + $env:PATH) }",
    "$venv = Join-Path (Get-Location) '.venv-via_vdf\\Scripts'",
    "if (Test-Path -LiteralPath (Join-Path $venv 'python.exe')) { $env:PATH = ($venv + ';' + $env:PATH); $env:VIA_VDF_PY = (Join-Path $venv 'python.exe') }",
    "Write-Host 'LKGC PATH · 已進母目錄 · venv 優先 · via_iso_* 不進 PATH'",
    "Write-Host '衝突件 via_iso_* · 禁止刪槽／卸載'",
    "Write-Host 'VDF 啟動自動 CACHE；增量年檔請總管按「手動下一輪」（需閘1）'",
    "return",
  ].join("\n");
}

export function uvIndexUrl(): string {
  return (UV_MIRRORS.find((m) => m.id === LKGC_UV.winner) ?? UV_MIRRORS[0]!).url;
}

export function classifyIssues(pins: EnvPin[] = ENV_PINS): GovIssue[] {
  const issues: GovIssue[] = [];
  const hydra = hydraRiskGov();
  if (!hydra.ok) issues.push({ id: "HYDRA", zone: "ENGINE", kind: "sequence", light: "bad", note: hydra.note });
  else issues.push({ id: "HYDRA", zone: "ENGINE", kind: "sequence", light: "ok", note: hydra.note });
  const libs = libCompleteness(pins);
  if (!libs.ok) {
    issues.push({ id: "LIBS", zone: "FUNCTION-LIB", kind: "parallel", light: "bad", note: `缺 ${libs.miss.join(",")}` });
  } else {
    issues.push({ id: "LIBS", zone: "FUNCTION-LIB", kind: "parallel", light: "ok", note: `必裝 ${libs.pinned.length} 已釘` });
  }
  const hits = scanEnvConflicts(pins);
  const race = raceMirrors();
  for (const h of hits) {
    issues.push({
      id: `ISO_${h.pkg}`,
      zone: "ENGINE",
      kind: "sequence",
      light: "warn",
      note: `${h.left} vs ${h.right} → ${h.isolate} · 不刪`,
    });
  }
  issues.push({
    id: "UV_RACE",
    zone: "ENGINE",
    kind: "parallel",
    light: race.lkgcHold ? "ok" : "warn",
    note: race.note,
  });
  const clash = runClashTools(pins);
  issues.push({
    id: "UV_CLASH",
    zone: "FUNCTION-LIB",
    kind: "parallel",
    light: clash.fail ? "bad" : clash.warn ? "warn" : "ok",
    note: clash.note,
  });
  issues.push({
    id: "MOD",
    zone: "MODULE",
    kind: "parallel",
    light: "ok",
    note: `GA-${String(GOV_ACCEL.length).padStart(2, "0")} · 與 PS20 分冊`,
  });
  issues.push({
    id: "OTH",
    zone: "OTHERS",
    kind: "parallel",
    light: "ok",
    note: "本台不 spawn conda/uv · DCT 不動",
  });
  return issues;
}

export function govZoneRows(pins: EnvPin[] = ENV_PINS): { zone: string; n: number; light: Light; note: string }[] {
  const issues = classifyIssues(pins);
  return GOV_ZONES.map((zone) => {
    const rows = issues.filter((i) => i.zone === zone);
    const bad = rows.some((r) => r.light === "bad");
    const warn = rows.some((r) => r.light === "warn");
    return {
      zone,
      n: rows.length,
      light: (bad ? "bad" : warn ? "warn" : rows.length ? "ok" : "pending") as Light,
      note: rows.map((r) => r.note).join(" · ") || "無列",
    };
  });
}

export function libTableHealth(pins: EnvPin[] = ENV_PINS): { id: string; name: string; light: Light; note: string }[] {
  const libs = libCompleteness(pins);
  return libTable().map((r) => {
    const missing = libs.miss.includes(r.name);
    return {
      id: r.id,
      name: r.name,
      light: (missing ? "bad" : r.status) as Light,
      note: missing ? `缺釘 ${r.name}` : r.note,
    };
  });
}

export function runGovEnv(input: { apply?: boolean } = {}): {
  apply: boolean;
  issues: GovIssue[];
  rounds: GovRound[];
  script: string;
  lockVdf: string;
  uv: string;
  race: ReturnType<typeof raceMirrors>;
  clash: ReturnType<typeof runClashTools>;
  raceScript: string;
  seal: Seal;
} {
  const apply = Boolean(input.apply);
  const issues = classifyIssues();
  const hydra = hydraRiskGov();
  const libs = libCompleteness();
  const clashes = scanEnvConflicts();
  const script = isolationScript(clashes);
  const lockVdf = lockfileYml("via_vdf");
  const race = raceMirrors();
  const clash = runClashTools();
  const uv = uvIndexUrl();
  const raceScript = uvRaceScript();
  const rounds: GovRound[] = GOV_ROUNDS.map((r) => {
    if (r.id === 1) {
      return {
        id: r.id,
        name: r.name,
        kind: r.kind,
        did: apply ? "本台不 spawn · 只列平行可修" : "掃描平行可修 · 不改 disk",
        light: "ok",
      };
    }
    if (r.id === 2) {
      return {
        id: r.id,
        name: r.name,
        kind: r.kind,
        did: apply ? "不 spawn conda/uv · 指令留母機" : "序列依賴待母機雙閘",
        light: "warn",
      };
    }
    return {
      id: r.id,
      name: r.name,
      kind: r.kind,
      did: apply ? "鎖檔產出 · 不 spawn" : "鎖檔 via_vdf.yml 預覽",
      light: "ok",
    };
  });
  const sealLight: Light = !hydra.ok || !libs.ok ? "bad" : clashes.length ? "warn" : "ok";
  const seal: Seal = {
    id: "GOV",
    name: "環境治理",
    light: sealLight,
    note: `${hydra.note} · 必裝 ${libs.pinned.length} · 隔離 ${clashes.map((c) => c.isolate).join(",") || "無"} · GA ${GOV_ACCEL.length} · 競速 ${race.winner} · 八路 ${clash.ok}/8`,
  };
  return { apply, issues, rounds, script, lockVdf, uv, race, clash, raceScript, seal };
}
