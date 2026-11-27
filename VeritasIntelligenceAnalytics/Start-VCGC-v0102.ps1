# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
<#
Start-VCGC-v0102.ps1 — 一支 PS 啟用 VCGC(只啟 VCGC;VDF / VRN 各自的入口不經這支 · L119)。
作廢:Start-VCGC-v0100.ps1 · Start-VCGC-v0101.ps1(PR #773 Codex P1:選倉 · 核雜湊 · 落檔 · 刪檔都是邏輯,不該在 PS)。
PS 只進環境與呼叫 Python 入口(AGENTS.md · L117 · VCGC-REQ266):
  倉 = 本檔所在的 VeritasIntelligenceAnalytics 夾(本檔隨倉走,不另找副本、不落檔、不刪檔);
  叫 CGC_SystemManager 尾版的 launch(順序 · 道數 · 心跳 · 燈 · 收據 · 開頁全在 Python)。
用法:pwsh -NoProfile -File Start-VCGC-v0102.ps1 [--plan] [--full] [--lanes 3..6] [--no-open] [--timeout 秒]
#>
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { Write-Verbose 'PS accel bridge absent (graceful)' }
# ===== [VIA:PS-ACCEL:END] =====
$env:PYTHONUTF8 = '1'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { Write-Verbose 'console encoding unchanged' }
$sm = Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'supportive modules\registry') -Filter 'CGC_SystemManager_v*.py' -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if (-not $sm) { Write-Host "[RED] 本檔不在倉的 VeritasIntelligenceAnalytics 夾裡(找不到 CGC_SystemManager);請從倉內執行" -ForegroundColor Red; exit 1 }
$py = @(if (Get-Command py -ErrorAction SilentlyContinue) { 'py', '-3' } else { 'python' })
if (-not $Rest) { $Rest = @() }
if (-not $Host.UI.SupportsVirtualTerminal) { $Rest += '--plain' }
$pyArgs = @($py | Select-Object -Skip 1) + @('-X', 'utf8', $sm.FullName, 'launch') + $Rest
$rc = 1
Push-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
try {
    & $py[0] @pyArgs
    $rc = $LASTEXITCODE
} finally { Pop-Location }
exit $rc
