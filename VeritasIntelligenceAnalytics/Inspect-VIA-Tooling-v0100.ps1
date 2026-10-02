# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
<#
.SYNOPSIS
  工具盤點矩陣:全景 AST + 中央編號 + 短令冊 + L103 三導入(PY 加速器 · VDF 網路工具 · PS 模板)一張 HTML 表。

.DESCRIPTION
  Inspect-VIA-Tooling-v0100.ps1 — 操作員 2026-10-02 貼來的 Inspect-VCGC-Tooling.ps1 + py_accelerator_check.py 的正式版。
  本檔**不另寫一份規則**:每一欄都交給正主 CGC_MDL253_ToolingInventory(經 VCGC 中央入口),它再問
    全景讀檔 CGC_MDL158 鎖版那一支(定義樹 · 匯入 · AST 問題 · 治理七類)· 中央編號冊 VIA_NumberBooks(編號 · 子系統 · 分類)·
    Register 尾版順點源鏈(短令 · 別名 · 新增於)· 掃橋器尾版的網路套件清單(VDF 要不要網路橋)· 排版規格 CGC_MDL173(HTML 殼)。
  與原貼稿的差別:不找根目錄 vcgc/vdf/vrn 夾(倉裡沒有)· 不寫倉根(輸出在 VIA_Reports\tooling,不進 git)·
  模板認 CELERITAS-TEMPLATE-JOIN / [VIA:ACCEL-BRIDGE / [VIA:NET-BRIDGE(倉裡沒有 New-VISMatrixReport / Invoke-VISAccelerator)。
  只讀:不改、不執行任何被掃的檔(只 ast.parse / 文字剖析);不代開任何同意閘;不 exit 主控台。

.EXAMPLE
  .\Inspect-VIA-Tooling-v0100.ps1                       # 預設範圍、只看尾版,跑完自動開 HTML
  .\Inspect-VIA-Tooling-v0100.ps1 -AllVersions -NoOpen  # 連舊版號一起盤點,不開頁
  .\Inspect-VIA-Tooling-v0100.ps1 -Path 'functional modules\VDF'   # 只盤一個夾
  .\Inspect-VIA-Tooling-v0100.ps1 -Commands -Recent 30  # 只印短令冊(新的在前)
  .\Inspect-VIA-Tooling-v0100.ps1 -Card 'supportive modules\references\intake\VIA_VDF_Engines_b716\VDF_MDL002_YFinanceFetchingEngine_1.py'
#>
param(
    [string]$RepoPath = "",
    [string]$PythonExe = "",
    [string[]]$Path = @(),
    [switch]$AllVersions,
    [switch]$Commands,
    [int]$Recent = 40,
    [string]$Card = "",
    [switch]$NoOpen
)
$ErrorActionPreference = 'Continue'

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

$here = if ($RepoPath) { (Resolve-Path -LiteralPath $RepoPath).ProviderPath } elseif ($env:VIA_ROOT) { $env:VIA_ROOT } else { $PSScriptRoot }
if (Test-Path -LiteralPath (Join-Path $here 'VeritasIntelligenceAnalytics\supportive modules\registry')) { $here = Join-Path $here 'VeritasIntelligenceAnalytics' }
$reg = Join-Path $here 'supportive modules\registry'
if (-not (Test-Path -LiteralPath $reg)) { Write-Host ("  [工具盤點] 找不到 VIA 倉根(要有 supportive modules\registry):" + $here) -ForegroundColor Red; $global:LASTEXITCODE = 3; return }

# ===== [CELERITAS-TEMPLATE-JOIN v1] L102:PS 導入模板(在自己的模組範圍點源,StrictMode 不外溢;關閉即還原) =====
$celeritasTpl = Join-Path $here 'supportive modules\ps7\VeritasCeleritas.PS7.Template.ps1'
$celeritasJoin = $null; $celeritasWhy = ''
if ($PSVersionTable.PSVersion.Major -ge 7 -and (Test-Path -LiteralPath $celeritasTpl)) {
    try {
        New-Module -Name VIACeleritasJoinTooling -ArgumentList $celeritasTpl -ScriptBlock {
            param($tplPath)
            . $tplPath
            Export-ModuleMember -Function Test-CeleritasJoin, Restore-CeleritasPS7
        } | Import-Module -Force -ErrorAction Stop
        $celeritasJoin = Test-CeleritasJoin
    } catch { $celeritasJoin = $null; $celeritasWhy = ($_.Exception.Message -split "`n")[0] }
}
if ($celeritasJoin -and $celeritasJoin.Joined) { Write-Host ("  [Celeritas] 模板已接(" + $celeritasJoin.Marker + " · 只動本行程 · 關閉即還原)") -ForegroundColor DarkCyan }
else { Write-Host ("  [Celeritas] 模板未接(" + $(if ($celeritasWhy) { $celeritasWhy } else { 'PowerShell 7 / supportive modules\ps7 缺件' }) + ";不擋跑)") -ForegroundColor Yellow }
# ===== [CELERITAS-TEMPLATE-JOIN:END] =====

try {
    $py = $PythonExe
    if (-not $py) {
        $py = (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1).Source
        if (-not $py) { $py = (Get-Command python3 -ErrorAction SilentlyContinue | Select-Object -First 1).Source }
    }
    $vc = Get-ChildItem -LiteralPath $reg -Filter 'CGC_MDL149_VeritasCentralGovernanceConsole_v*.py' -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if (-not $py -or -not $vc) { Write-Host ("  [工具盤點] 缺 " + $(if (-not $py) { 'python' } else { 'VCGC 主控台' })) -ForegroundColor Red; $global:LASTEXITCODE = 3; return }

    $verbArgs = if ($Card) { @('card', $Card) }
                elseif ($Commands) { @('cmds', '--recent', [string]$Recent) }
                else { @('scan') + @($Path) + $(if ($AllVersions) { @('--all-versions') } else { @() }) + $(if ($NoOpen) { @('--no-open') } else { @() }) }
    Write-Host ("=== [工具盤點 v0100] " + $here + " · " + ($verbArgs -join ' ') + " ===") -ForegroundColor Cyan
    $keepFrom = $env:VIA_FROM_VCGC; $keepUtf = $env:PYTHONUTF8
    $env:VIA_FROM_VCGC = 'YES'; $env:PYTHONUTF8 = '1'     # 只設本行程,跑完還原
    Push-Location -LiteralPath $here
    try { & $py -X utf8 $vc.FullName run CGC_MDL253_ToolingInventory @verbArgs; $rc = $LASTEXITCODE }
    finally { Pop-Location; $env:VIA_FROM_VCGC = $keepFrom; $env:PYTHONUTF8 = $keepUtf }
    $html = Join-Path $here 'VIA_Reports\tooling\TOOLING_latest.html'
    $color = if ($rc -eq 0) { 'Green' } elseif ($rc -eq 2) { 'Yellow' } else { 'Red' }
    Write-Host ("=== [工具盤點 v0100] rc " + $rc + "(0 全綠 · 2 有黃燈 / 有發現 · 1 紅)" + $(if (-not $Card -and -not $Commands) { " · 頁 " + $html } else { "" }) + " ===") -ForegroundColor $color
    $global:LASTEXITCODE = $rc
}
finally {
    if ($celeritasJoin -and $celeritasJoin.Joined -and (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue)) {
        Restore-CeleritasPS7    # 契約:關閉即還原(只動本行程)
    }
}
