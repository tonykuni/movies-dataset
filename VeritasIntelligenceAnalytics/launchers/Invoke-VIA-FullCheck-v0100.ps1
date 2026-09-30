# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-FullCheck-v0100.ps1 — 整合全景實測一鍵跑 · 跳出 HTML 總報告(側線 2026-09-30 b)
#   操作員令:「先把這個面檢視實測的工具整合為一」「給我一個整合後的 POWERSHELL 跳出 HTML 報告如今天清晨」(本令即 L70 逐次許可;新檔,不動任何舊 .ps1)
#   經 VCGC 主控台跑正主 CGC_MDL248_FullCheck 尾版,五段照順序跑到底(紅了照跑下一段):
#     ① VCGC 指令串測(CGC_MDL224)② SSOT 全景 VCGC→VDF→VRN→SUP(CGC_MDL247)③ 單一路徑驗證(CGC_MDL242)
#     ④ 自測格子(CGC_MDL064;預設讀最新存證,-Grid 才整張重跑 —— 會重寫已追蹤檔,跑完用 git 看一下)⑤ 交接防遺漏(CGC_MDL140)
#   每段的正主尾版 · 版號 · sha16 · UTC 時間 · 秒數只增寫 registry\VIA_VCGC_FullCheck_Ledger_v0100.jsonl;
#   頁:VIA_Reports\fullcheck\FULLCHECK_latest.html(與單一路徑驗證頁同一套版型),跑完自動開(-NoOpen 不開)。
# 用法(站在倉根或任何地方):.\VeritasIntelligenceAnalytics\launchers\Invoke-VIA-FullCheck-v0100.ps1  [-Full] [-Grid] [-NoOpen] [-Only 1,2] [-SystemDir <VIA 夾>]
#   -Full 全部重量(串測 · 全景都不沿用)· -Grid 自測格子整張重跑(約 15 分)· 結束碼 0 綠 · 2 黃 · 1 紅 · 3 環境缺件
# 不抓網路、不寫庫、不 push、不代開同意閘;只經 Invoke-VIAPython 叫 python。
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Full,
    [switch]$Grid,
    [switch]$NoOpen,
    [string]$Only = "",
    [string]$SystemDir = ""
)
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

$VIA = if ($SystemDir) { $SystemDir } else { Split-Path -Parent $PSScriptRoot }
$StartDir = (Get-Location).Path
$prev = @{ FROM = $env:VIA_FROM_VCGC; PUSH = $env:VIA_VCGC_PUSH; OPEN = $env:VIA_NO_OPEN }
$exitCode = 0
try {
    if (-not (Test-Path -LiteralPath (Join-Path $VIA "supportive modules\registry"))) {
        Write-Host ("  [整合全景實測] 找不到系統夾 " + $VIA + "(用 -SystemDir 指到 VeritasIntelligenceAnalytics)") -ForegroundColor Red
        $exitCode = 3
        return
    }
    Set-Location -LiteralPath $VIA
    try {
        $join = Join-Path $VIA "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
        if (Test-Path -LiteralPath $join) { . $join; Write-Host ("  [加速器] 套對 " + $script:CeleritasPS7.Version) -ForegroundColor DarkGray }
    } catch {
        Write-Host "  [加速器] 正主載入失敗,略過" -ForegroundColor DarkGray
    }
    $env:VIA_FROM_VCGC = "YES"
    $env:VIA_VCGC_PUSH = "NO"
    $env:VIA_NO_OPEN = "1"
    if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
        $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
        if (Test-Path -LiteralPath $pyMod) { . $pyMod }
    }
    if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
        Write-Host "  [整合全景實測] 中央 Invoke-VIAPython 不在(VIA_PS_PyProgress_Module.ps1 缺);不繞過直呼 python,停。" -ForegroundColor Red
        $exitCode = 3
        return
    }
    $reg = Join-Path $VIA "supportive modules\registry"
    $console = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    $engine = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL248_FullCheck_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    if ($null -eq $console -or $null -eq $engine) {
        Write-Host "  [整合全景實測] VCGC 主控台或 CGC_MDL248_FullCheck 尾版不在(先 git pull)" -ForegroundColor Red
        $exitCode = 3
        return
    }
    $argList = @("run", "--family", "core", "CGC_MDL248_FullCheck", "run")
    if ($Full) { $argList += "--full" }
    if ($Grid) { $argList += "--grid" }
    if ($Only) { $argList += @("--only", $Only) }
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║  VIA 整合全景實測 v0100 · VCGC → VDF → VRN → SUP · 紅了照跑   ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ("  [正主] " + $engine.Name + " · 經 " + $console.Name + $(if ($Full) { " · 全部重量" } else { " · 沒變的沿用" }) + $(if ($Grid) { " · 格子整張重跑" } else { " · 格子讀存證" })) -ForegroundColor DarkGray
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $timeout = if ($Grid) { 7200 } else { 3600 }
    $lines = [System.Collections.Generic.List[string]]::new()
    $body = { Invoke-VIAPython -Family 'core' -TimeoutSec $timeout $console.FullName @argList 2>&1 }
    $global:LASTEXITCODE = 0
    $raw = if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { Invoke-VIACeleritasScoped -Body $body } else { & $body }
    foreach ($ln in @($raw)) {
        $s = "" + $ln
        $lines.Add($s)
        $color = if ($s -match '\bRED\b|紅') { "Red" } elseif ($s -match '\bYELLOW\b|黃') { "Yellow" } elseif ($s -match '\bGREEN\b') { "Green" } else { "Gray" }
        Write-Host $s -ForegroundColor $color
    }
    $rc = $global:LASTEXITCODE
    $exitCode = if ($rc -in 0, 1, 2) { $rc } else { 1 }
    $page = Join-Path $VIA "VIA_Reports\fullcheck\FULLCHECK_latest.html"
    Write-Host ("  [計時] 全程 " + [Math]::Round($clock.Elapsed.TotalSeconds, 1) + " 秒 · 結束碼 " + $exitCode + "(0 綠 · 2 黃 · 1 紅)") -ForegroundColor Cyan
    Write-Host ("  [總報告] " + $page) -ForegroundColor Cyan
    if (-not $NoOpen) {
        if (Test-Path -LiteralPath $page) {
            try { Invoke-Item -LiteralPath $page } catch { Write-Host ("  [頁] 開不了瀏覽器(手動開 " + $page + ")") -ForegroundColor Yellow }
        } else {
            Write-Host "  [頁] 這輪沒產出總報告頁(看上面紅字)" -ForegroundColor Red
        }
    }
} finally {
    $env:VIA_FROM_VCGC = $prev.FROM
    $env:VIA_VCGC_PUSH = $prev.PUSH
    $env:VIA_NO_OPEN = $prev.OPEN
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] 關閉即還原
    Set-Location -LiteralPath $StartDir
}
exit $exitCode
