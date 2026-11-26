#Requires -Version 7.4
# ==============================================================================
# VIA_ProfileLoader_v0106.ps1 — VIA 唯一一支 PS(只負責啟動)· 作廢 v0100–v0105
# 操作員 2026-11-23:「PS 指令 PY 化 · 短指令 PY 寫完善 · PS 只是啟動用 · 選擇題 · 說明清楚 · ONE PS TO HANDLE ALL」
# 操作員 2026-11-25:「one py code with supports of accelerating module and one ps to activate it」
# v0106 比 v0105 只多三件(其餘逐字照 v0105):
#   ① PS-ACCEL 加速器橋(覆蓋矩陣 ps_accel 缺件 = v0105)
#   ② via-gov = 治理一支 Python(docs\handoff\ai\VIA_GovernanceApply 尾版):plan(唯讀)· apply · verify · selftest;不帶參數 = 選擇題
#   ③ 也能直接跑(不必先進 profile):pwsh -NoProfile -File .\VIA_ProfileLoader_v0106.ps1 gov plan
#      第一個字是 gov → via-gov;其他 → 中樞同名指令(例:... -File .\VIA_ProfileLoader_v0106.ps1 x via-tok)
# 本檔沒有任何指令邏輯:
#   ① 找中樞(本檔同夾的 VCGC_CommandHub 尾版)
#   ② 照中樞指令冊(python 中樞 names --ps)生出全部 via-* 函式,每個都轉回 Python;清單依中樞檔時間快取,開 PS 不必每次叫 Python
#   ③ 舊短令(含 Override 改成 DEPRECATED 殘樁的、走 Invoke-VIA-Launch 的 via-vdf / via-vrn / via-vcgc / via-view)改導到 Python 新指令
#   ④ via = Python 選擇題主控台;互動式終端才自動開
# 看清單:via-help · 看某個:via-help via-tok · 緊急逃生:pwsh -NoProfile
# 同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)本檔一律不設。
# ==============================================================================
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$ViaRun)

# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

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

# --- via-gov:治理一支 Python(VIA_GovernanceApply 尾版)· 不帶參數 = 選擇題 ---
function global:via-gov {
    $gov = Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'docs\handoff\ai') -Filter 'VIA_GovernanceApply_v*.py' -File -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if (-not $gov) {
        Write-Host "[VIA] 找不到 docs\handoff\ai\VIA_GovernanceApply_v*.py(先 git fetch / switch 到工作分支)" -ForegroundColor Yellow
        return
    }
    $a = @($args)
    if ($a.Count -eq 0) {
        Write-Host ""
        Write-Host "  VIA 治理(VCGC 工具組裝 · 加速器橋 · 零網路)" -ForegroundColor Cyan
        Write-Host "   1  plan      唯讀:五條車道各列 應做 / 可做 / 略過 與理由(不寫任何檔)"
        Write-Host "   2  apply     依序 退役合併 → 網路橋 → 加速器 → 參數解耦 → 驗證(每檔先過 TEMP 檢查,不過就還原)"
        Write-Host "   3  verify    只重跑驗證:新版自測 · 覆蓋矩陣 · ReworkGuard · 編號稽核"
        Write-Host "   4  selftest  工具自測(暫存夾造資料)"
        Write-Host "   0  離開"
        $c = Read-Host "  選 0-4"
        $a = switch ($c) { '1' { @('plan') } '2' { @('apply') } '3' { @('verify') } '4' { @('selftest') } default { @() } }
        if ($a.Count -eq 0) { return }
    }
    $old = $env:VIA_CODE_ROOT
    try { $env:VIA_CODE_ROOT = $PSScriptRoot; & $PyCmd $gov.FullName @a; $global:LASTEXITCODE = $LASTEXITCODE }
    finally { $env:VIA_CODE_ROOT = $old }
}

# --- 直接跑模式(pwsh -File 本檔 <動詞…>):跑完就結束,不開主控台 ---
if ($ViaRun -and $ViaRun.Count -gt 0) {
    if ($ViaRun[0] -eq 'gov') { via-gov @($ViaRun | Select-Object -Skip 1) } else { Invoke-ViaHub @ViaRun }
    exit $LASTEXITCODE
}

# 互動式終端才自動開主控台;-Command / -File / 非互動 / Claude Code 子行程 / VIA_NO_MENU 一律不開
$__viaArgs = [Environment]::GetCommandLineArgs() -join ' '
if ([Environment]::UserInteractive -and $Host.Name -eq 'ConsoleHost' -and
    ($__viaArgs -notmatch '(?i)\s-(c|command|f|file|e|ec|encodedcommand|noni|noninteractive)\b') -and
    -not $env:CLAUDECODE -and -not $env:VIA_NO_MENU) { via }
