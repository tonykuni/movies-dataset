# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 5.1
<#
Start-VIA-v0101.ps1 — 一支 PS 依序啟動 VCGC → 備份 + Graphify(VCGC · VDF)→ VDF。
v0101(2026-11-28 操作員同意):只補 PS-ACCEL 加速器橋(PS 尾版缺橋,pslint 紅);其餘一字不動。作廢:Start-VIA-v0100.ps1。

操作員 2026-11-27:「Activate vcgc vdf by insert order to ps and backup graphify the vcgc and vdf」。
PS 只做三件事:找到 VIA_HostBoot 尾版 · 主控台不支援 ANSI 時補 --plain · 叫它的 up 動詞。
順序 · 判斷 · 停不停全寫在 Python(VIA_HostBoot v0106 up):
  ① VCGC 主控台 enter(紅 = 黃字提醒,不擋後面;三系統獨立)
  ② VIA_DailyBackup full --sys VCGC,VDF(先刷齊三冊與 Graphify 圖 · 本機隔離區 · 5 份輪替 · Fail-Closed:前置閘紅就停,VDF 不跑)
  ③ VDF_MDL022 start(預設 --start 2018-01-01 --slots 3 · 加速器真的載到才跑 · 一次降壓後 3 道同步 · 摘要矩陣)
同意閘不在本檔設:跑之前在你自己的視窗開 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT(VDF 開跑前檢查會擋)。
用法:pwsh -NoProfile -File Start-VIA-v0101.ps1 [--skip-backup] [--start 2018-01-01] [--slots 3] [其他 VDF start 參數]
作廢(操作員要打的 PS 只留這一支):Start-VIA-VDF-v0101.ps1 · Start-VIA-VDF-v0100.ps1(檔仍在、仍可用,只是不再是建議入口)。
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
$hb = Get-ChildItem (Join-Path $PSScriptRoot 'docs\handoff\ai') -Filter 'VIA_HostBoot_v*.py' -ErrorAction SilentlyContinue |
    Sort-Object Name | Select-Object -Last 1
if (-not $hb) { Write-Host '[RED] 找不到 VIA_HostBoot(請先 git pull)' -ForegroundColor Red; exit 1 }
$py = @(if (Get-Command py -ErrorAction SilentlyContinue) { 'py', '-3' } else { 'python' })
$pyArgs = @($py | Select-Object -Skip 1) + @('-X', 'utf8', $hb.FullName, '--repo', (Split-Path $PSScriptRoot -Parent), 'up')
if (-not $Rest) { $Rest = @() }
if (-not $Host.UI.SupportsVirtualTerminal) { $Rest += '--plain' }
& $py[0] @pyArgs @Rest
exit $LASTEXITCODE
