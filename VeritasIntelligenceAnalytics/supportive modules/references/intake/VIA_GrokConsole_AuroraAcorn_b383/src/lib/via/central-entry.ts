/** 中央唯一入口：衝突解完 → 裝庫／PATH／工具 · 本台不 spawn。 */
import { GOV_TOOLS } from "./catalog.ts";
import { runEnvManager } from "./env-manager.ts";
import { isolationScript, scanEnvConflicts } from "./inventory.ts";
import { LKGC_UV, UV_MIRRORS } from "./gov-spec.ts";
import { motherPathScript } from "./gov-env.ts";
import type { Light } from "./types.ts";

export const PATH_SLOTS = [
  { id: "ROOT", role: "cwd", on: true, note: "專案根 · Set-Location" },
  { id: "VENV", role: "winner", on: true, note: ".venv-via_vdf\\Scripts · uv 裝庫優先" },
  { id: "VIA_VDF", role: "conda", on: true, note: "miniconda via_vdf · 有才 prepend" },
  { id: "SCRIPTS", role: "ps", on: true, note: "專案 scripts\\ · 短指令" },
  { id: "VIA_CORE", role: "gov", on: false, note: "via_core 不搶預設 python" },
  { id: "ISO", role: "off-path", on: false, note: "via_iso_* 永不進預設 PATH" },
] as const;

export function pathPlan(): { id: string; role: string; on: boolean; note: string }[] {
  return PATH_SLOTS.map((s) => ({ id: s.id, role: s.role, on: s.on, note: s.note }));
}

export function githubPushScript(): string {
  return [
    "#requires -Version 7.0",
    "# VIA GitHub 上傳 · 只 add 實際存在的路徑 · 禁止強制推送",
    "$ErrorActionPreference = 'Stop'",
    "$cands = @(",
    "  'C:\\Users\\tonyk\\movies-dataset\\VeritasIntelligenceAnalytics',",
    "  'C:\\Users\\tonyk\\Github\\movies-dataset\\VeritasIntelligenceAnalytics'",
    ")",
    "$Root = $cands | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1",
    "if (-not $Root) { Write-Host 'RED ROOT 找不到專案'; return }",
    "Set-Location -LiteralPath $Root",
    "if (-not (Test-Path -LiteralPath (Join-Path $Root '.git'))) { Write-Host 'RED GIT 不是 git 倉'; return }",
    "git rev-parse --abbrev-ref HEAD | ForEach-Object { Write-Host \"GREEN BR $_\" }",
    "git status -sb",
    "$prefer = @('src','public/via','public','scripts','locks','package.json','package-lock.json','AGENTS.md','VIA-ALL.cmd','logs/via_handover.md')",
    "[string[]]$add = @($prefer | Where-Object { Test-Path -LiteralPath (Join-Path $Root $_) })",
    "if ($env:VIA_GH_HTML -eq '1' -and (Test-Path -LiteralPath (Join-Path $Root 'logs\\via_aetf_board.html'))) { $add += 'logs/via_aetf_board.html' }",
    "if ($add -isnot [System.Array]) { $add = @($add) }",
    "Write-Host ('GREEN ADD ' + ($(if ($add.Count) { $add -join ' ' } else { '無' })))",
    "if ($env:VIA_GH_YES -ne '1') {",
    "  Write-Host 'YELLOW PLAN 預覽 · 設 VIA_GH_YES=1 才 add/commit/push'",
    "  Write-Host 'YELLOW SKIP 湖 parquet、.venv、.env、node_modules、logs（HTML 另開 VIA_GH_HTML=1）'",
    "  return",
    "}",
    "if (-not $add.Count) { Write-Host 'YELLOW SKIP 此倉無標準路徑（母倉可無 src）'; return }",
    "foreach ($p in $add) { git add -- $p }",
    "git status -sb",
    "$msg = $env:VIA_GH_MSG; if (-not $msg) { $msg = 'VIA central entry · EnvManager PATH isolate-not-delete' }",
    "git diff --cached --quiet; if ($LASTEXITCODE -eq 0) { Write-Host 'YELLOW SKIP 無暫存'; return }",
    "git commit -m $msg",
    "git push -u origin HEAD",
    "Write-Host 'GREEN GH push 完成 · 禁止強制推送'",
    "return",
  ].join("\n");
}

export function centralLaunchScript(): string {
  const iso = isolationScript(scanEnvConflicts());
  const idx = UV_MIRRORS.find((m) => m.id === LKGC_UV.winner)?.url ?? UV_MIRRORS[0]!.url;
  return [
    "#requires -Version 7.0",
    "# VIA 中央唯一入口 · 衝突隔離 → uv 裝庫 → PATH · 不刪 base",
    motherPathScript(),
    "$Venv = Join-Path (Get-Location) '.venv-via_vdf'",
    "if (Test-Path (Join-Path $Venv 'Scripts\\python.exe')) {",
    "  $env:VIA_VDF_PY = (Join-Path $Venv 'Scripts\\python.exe')",
    "  $env:PATH = ((Join-Path $Venv 'Scripts') + ';' + $env:PATH)",
    "  Write-Host 'GREEN PATH venv Scripts prepend'",
    "}",
    "$env:VIA_INDEX = '" + idx + "'",
    "Write-Host 'GREEN ENTRY 中央唯一入口 · LKGC " + LKGC_UV.when + " · iso 不進 PATH'",
    iso,
    githubPushScript().split("\n").map((l) => "# GH " + l).join("\n"),
  ].join("\n");
}

export function runCentralEntry(input: { consent?: boolean } = {}): {
  light: Light;
  note: string;
  path: ReturnType<typeof pathPlan>;
  tools: { id: string; name: string; note: string }[];
  env: ReturnType<typeof runEnvManager>;
  launch: string;
  github: string;
} {
  const env = runEnvManager({ consent: input.consent });
  const path = pathPlan();
  const tools = GOV_TOOLS.map((t) => ({ id: t.id, name: t.name, note: t.note }));
  const light: Light = env.light === "bad" ? "bad" : env.light === "warn" ? "warn" : "ok";
  return {
    light,
    note: `中央唯一入口 · ${env.plan}`,
    path,
    tools,
    env,
    launch: centralLaunchScript(),
    github: githubPushScript(),
  };
}
