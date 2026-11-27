# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 5.1
<#
Start-VIA-VDF-v0102.ps1 — VDF 一鍵啟動。PS 只做三件事:找到 Python 啟動器尾版 · 看主控台能不能畫進度條 · 叫它的 start 動詞。
v0102(2026-11-28 操作員同意):只補 PS-ACCEL 加速器橋(PS 尾版缺橋,pslint 紅);其餘一字不動。作廢:Start-VIA-VDF-v0101.ps1。

操作員 2026-11-26:「功能寫在 PY 裡 · PRINT DETAILED SUMMARY MATRIX BY RICH · PS 僅啟動加上檢測」。
AGENTS.md §3 / CLAUDE.md:PowerShell 只進環境與呼叫 Python 入口,判斷 · 迴圈 · 清單處理全寫在 Python(PR #764 Codex P1)。
所以開跑前檢查 → 背景跑 → 輪詢進度 → 進度條 → Ctrl+C 收行程樹 → Rich 詳細摘要矩陣,全在
VDF_MDL022_SafeParallelLaunch 尾版的 start 動詞裡:
  方案一 Rich 進度條(高質感;有裝 Rich 就用)· 方案二 原生 ANSI 八階平滑進度條(零依賴)。
  PwshSpectreConsole 是 PS 端的畫面庫,用它就得把輪詢迴圈寫在 PS,違反上一條,所以改由 Python 的 Rich 擔任方案一。
  不自動安裝任何模組(安裝只走 VCGC 安裝閘)。本檔不設同意閘。
用法:pwsh -NoProfile -File Start-VIA-VDF-v0102.ps1 [--start 2018-01-01] [--data-home <資料家>] [--dry] [--no-merge] [--check] [--plain] [--ui rich|ansi]
  --check / --plain / 主控台不支援 ANSI → 前景照 launch 跑(輸出照常顯示)。
作廢:Start-VIA-VDF-v0100.ps1(仍可用,但沒有進度條與摘要矩陣)。
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
$tail = Get-ChildItem (Join-Path $PSScriptRoot 'functional modules\VDF') -Filter 'VDF_MDL022_SafeParallelLaunch_v*.py' -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if (-not $tail) { Write-Host '[RED] 找不到 VDF_MDL022_SafeParallelLaunch(請先 git pull)' -ForegroundColor Red; exit 1 }
$py = @(if (Get-Command py -ErrorAction SilentlyContinue) { 'py', '-3' } else { 'python' })
$pyArgs = @($py | Select-Object -Skip 1) + @('-X', 'utf8', $tail.FullName, 'start')
if (-not $Rest) { $Rest = @() }
if (-not $Host.UI.SupportsVirtualTerminal) { $Rest += '--plain' }
& $py[0] @pyArgs @Rest
exit $LASTEXITCODE
