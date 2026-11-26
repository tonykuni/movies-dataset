#Requires -Version 5.1
<#
Start-VIA-VDF-v0100.ps1 — VDF 一鍵啟動(PS 只做兩件事:找到 Python 啟動器、原樣轉交參數)

操作員 2026-11-26:「接入排程優化加速器 · 不傷電腦不傷系統 · 現代化 U/I 動畫 · 主要功能寫在 py · ps 啟動」。
所有判斷(開跑前檢查 · 分支狀態 · 加速器真的載到 · 同意閘檢查 · 參數預設 · 動畫 · 結果框)都在
VDF_MDL022_SafeParallelLaunch 尾版的 launch 動詞(Python);排程、降壓、增量擷取、暫存併入也在那裡。
本檔不設同意閘。用法(參數照 Python 的寫法原樣轉交):
  pwsh -NoProfile -File Start-VIA-VDF-v0100.ps1 [--start 2018-01-01] [--data-home <資料家>] [--dry] [--no-merge] [--check] [--plain]
#>
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest)
$env:PYTHONUTF8 = '1'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { Write-Verbose 'console encoding unchanged' }
$tail = Get-ChildItem (Join-Path $PSScriptRoot 'functional modules\VDF') -Filter 'VDF_MDL022_SafeParallelLaunch_v*.py' -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if (-not $tail) { Write-Host '[RED] 找不到 VDF_MDL022_SafeParallelLaunch(請先 git pull)' -ForegroundColor Red; exit 1 }
$py = @(if (Get-Command py -ErrorAction SilentlyContinue) { 'py', '-3' } else { 'python' })
& $py[0] @($py | Select-Object -Skip 1) -X utf8 $tail.FullName launch @Rest
exit $LASTEXITCODE
