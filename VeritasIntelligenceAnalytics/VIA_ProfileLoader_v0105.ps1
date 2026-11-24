#Requires -Version 7.4
# ==============================================================================
# VIA_ProfileLoader_v0105.ps1 — VIA 唯一一支 PS(只負責啟動)· 作廢 v0100–v0104
# 操作員 2026-11-23:「PS 指令 PY 化 · 短指令 PY 寫完善 · PS 只是啟動用 · 選擇題 · 說明清楚 · ONE PS TO HANDLE ALL」
# 本檔沒有任何指令邏輯:
#   ① 找中樞(本檔同夾的 VCGC_CommandHub 尾版)
#   ② 照中樞指令冊(python 中樞 names --ps)生出全部 via-* 函式,每個都轉回 Python;清單依中樞檔時間快取,開 PS 不必每次叫 Python
#   ③ 舊短令(含 Override 改成 DEPRECATED 殘樁的、走 Invoke-VIA-Launch 的 via-vdf / via-vrn / via-vcgc / via-view)改導到 Python 新指令
#   ④ via = Python 選擇題主控台;互動式終端才自動開
# 看清單:via-help · 看某個:via-help via-tok · 緊急逃生:pwsh -NoProfile
# ==============================================================================
$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if ([string]::IsNullOrWhiteSpace($env:VIA_ROOT)) { $env:VIA_ROOT = $PSScriptRoot }
$PyCmd = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'python3' }
$ViaDataRoot = [Environment]::GetEnvironmentVariable('VIA_ROOT', 'User')
if ([string]::IsNullOrWhiteSpace($ViaDataRoot) -or -not (Test-Path $ViaDataRoot)) { $ViaDataRoot = $env:VIA_ROOT }
$ViaHub = Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'VCGC_CommandHub_v*.py' -File -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1

function Invoke-ViaHub {
    if (-not $ViaHub) { Write-Host "[VIA] $PSScriptRoot 下找不到 VCGC_CommandHub_v*.py" -ForegroundColor Yellow; return }
    $old = $env:VIA_ROOT; $oldCode = $env:VIA_CODE_ROOT
    try { $env:VIA_ROOT = $ViaDataRoot; $env:VIA_CODE_ROOT = $PSScriptRoot; & $PyCmd $ViaHub.FullName @args }
    finally {
        $env:VIA_ROOT = $old; $env:VIA_CODE_ROOT = $oldCode
        $u = [Environment]::GetEnvironmentVariable('FRED_API_KEY', 'User')   # via-auth 存的值讓本視窗也吃到(只在記憶體)
        if ($u) { $env:FRED_API_KEY = $u }
    }
}

# --- 指令清單(快取:中樞檔名 + 寫入時間 當鍵) ---
if ($ViaHub) {
    $cacheDir = Join-Path ([IO.Path]::GetTempPath()) 'VIA_hub_cmds'
    $key = '{0}_{1}' -f $ViaHub.BaseName, $ViaHub.LastWriteTimeUtc.Ticks
    $cache = Join-Path $cacheDir "$key.txt"
    if (-not (Test-Path $cache)) {
        New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
        $lines = & $PyCmd $ViaHub.FullName names --ps 2>$null
        if ($LASTEXITCODE -eq 0 -and $lines) { Set-Content -LiteralPath $cache -Value $lines -Encoding utf8 }
    }
    $pairs = if (Test-Path $cache) { Get-Content -LiteralPath $cache -Encoding utf8 } else { @() }
    foreach ($p in $pairs) {
        $name, $target = $p.Split('|', 2)
        if (-not $name -or $name -eq 'via') { continue }
        $isNew = ($name -eq $target)
        $exist = Get-Command $name -CommandType Function, Alias -ErrorAction SilentlyContinue
        $stub = $exist -and $exist.CommandType -eq 'Function' -and ("$($exist.Definition)" -match 'DEPRECATED|Invoke-VIASub|VIA_Launcher')
        if ($isNew -or -not $exist -or $stub) {
            Set-Item -Path "Function:\global:$name" -Value ([scriptblock]::Create("Invoke-ViaHub x '$name' @args")) -Force
        }
    }
}
function global:via { Invoke-ViaHub menu }

# 互動式終端才自動開主控台;-Command / -File / 非互動 / Claude Code 子行程 / VIA_NO_MENU 一律不開
$__viaArgs = [Environment]::GetCommandLineArgs() -join ' '
if ([Environment]::UserInteractive -and $Host.Name -eq 'ConsoleHost' -and
    ($__viaArgs -notmatch '(?i)\s-(c|command|f|file|e|ec|encodedcommand|noni|noninteractive)\b') -and
    -not $env:CLAUDECODE -and -not $env:VIA_NO_MENU) { via }
