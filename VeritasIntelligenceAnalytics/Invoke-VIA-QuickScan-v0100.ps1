# CELERITAS-TEMPLATE-JOIN v1(葉子指令:本檔只依序叫既有正主,每步都經 VCGC;不自己立尺)
#Requires -Version 7.0
# Invoke-VIA-QuickScan v0100 — 全景快篩一鍵(唯讀):VCGC · VDF · VRN 的 py / ps 加速器覆蓋 · PS 加速模板 · AST · 動詞模組化 · 工具與環境衝突 → 自動開 HTML
#
# 操作員 2026-10-02:「vcgc vrn vdf 用全景式掃描的方式快速檢查所有py擋 ps擋都有加入加速器且覆蓋率100%  ps檔案都有加入加速模板且自動跳出html u/i
#   ast及每個動詞都模組化? 所有工具及環境都安裝且沒有衝突?  工作前製作葉子指令ps擋」
#
#   ① 閘        via-vcgc status(政策 · 子系統座位 · 加速器 / 網路已接;沒過照樣往下量,總判記紅)
#   ② 覆蓋率    via-vcgc run CGC_MDL230_ToolCoverageProbe matrix
#               ① PY 加速器橋 · ② 網路工具 · ③ VDF 網路橋 · ④ PS 加速器橋 · ⑥ PS 加速模板章 → COVERAGE_MATRIX_latest.html
#   ③ AST 全景  鎖冊 token 工具(CGC_MDL158;唯讀,只 ast.parse 不執行)scan --fast(治理七類)+ read VDF / VRN / registry(通用 AST 類)
#   ④ 動詞模組化 via-vcgc test --quick(盤點冊每個動詞 · 席位 · 必用卡 · 交接案 · 工作流步 · PS 入口都有站;家族尾版 compile 錯 · 缺橋)
#   ⑤ 工具與環境 via-vcgc run CGC_MDL240_EnvManager check(工具鎖 / 載入 · 家族境 · 上下 LIB 缺漏 · 執行檔)
#               + via-vcgc run CGC_MDL135_EnvGovernance eight-hub(八路現況衝突 + uv;只查不裝不刪)
#   ⑥ 總表 + 自動開 HTML(覆蓋矩陣頁 · 全景監控頁;-NoOpen 不開)
#   只量不修 · 不安裝 · 不代開同意閘 · 不推。rc:0 全綠 · 2 有發現(黃 / 沒料)· 1 有紅。
# 用法(站在倉根或 VIA 夾):pwsh -NoProfile -File .\VeritasIntelligenceAnalytics\Invoke-VIA-QuickScan-v0100.ps1 [-NoOpen] [-SkipEnv] [-SkipAst]
param(
    [switch]$NoOpen,
    [switch]$SkipEnv,
    [switch]$SkipAst,
    [string]$Root = ""
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

$ErrorActionPreference = "Continue"
$script:Dotted = ($MyInvocation.InvocationName -eq ".")
$VIA = if ($Root) { $Root } else { $PSScriptRoot }
$reg = Join-Path $VIA "supportive modules\registry"
$rep = Join-Path $VIA "VIA_Reports"
$vcgc = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" -ErrorAction SilentlyContinue |
    Sort-Object { [int]([regex]::Match($_.BaseName, '_v(\d+)$').Groups[1].Value) } | Select-Object -Last 1
if (-not $vcgc) {
    Write-Host "  [FAIL] VCGC 尾版不在(CGC_MDL149_VeritasCentralGovernanceConsole_v*.py)" -ForegroundColor Red
    if ($script:Dotted) { $global:LASTEXITCODE = 1; return } else { exit 1 }
}
$pyProg = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
if (Test-Path -LiteralPath $pyProg) { . $pyProg }
$fromBefore = $env:VIA_FROM_VCGC
$pushBefore = $env:VIA_VCGC_PUSH
$env:VIA_FROM_VCGC = "YES"
$env:VIA_VCGC_PUSH = "NO"
$rows = @()
$t0all = Get-Date

function Invoke-QSStep([string]$Name, [string[]]$Argv, [string]$Pattern) {
    Write-Host ("--- " + $Name + " …") -ForegroundColor Cyan
    $t0 = Get-Date
    $out = @(& python @Argv 2>&1 | ForEach-Object { "" + $_ })
    $rc = $LASTEXITCODE
    $out | Where-Object { $_ -match $Pattern } | Select-Object -Last 12 | ForEach-Object { Write-Host ("    " + $_) }
    $lamp = switch ($rc) { 0 { "GREEN" } 2 { "YELLOW" } 3 { "NODATA" } 4 { "GATE" } default { "RED" } }
    $line = @($out | Where-Object { $_ -match $Pattern } | Select-Object -Last 1) -join ""
    $script:rows += [pscustomobject]@{ Step = $Name; Lamp = $lamp; Rc = $rc; Secs = [int]((Get-Date) - $t0).TotalSeconds; Verdict = ($line.Trim() -replace "\s+", " ").Substring(0, [Math]::Min(110, $line.Trim().Length)) }
}

Write-Host ("=== [via-quickscan] 全景快篩 · VIA " + $VIA + " · VCGC " + $vcgc.Name + " ===") -ForegroundColor Cyan
Invoke-QSStep "① 閘(VCGC status)" @($vcgc.FullName, "status") "流程|政策過|GATE|第一步"
Invoke-QSStep "② 加速器 / 網路 / PS 模板覆蓋率" @($vcgc.FullName, "run", "CGC_MDL230_ToolCoverageProbe", "matrix") "^\s*\[(GREEN|YELLOW|RED|INFO) *\]|ToolMatrix\] 總判"
if (-not $SkipAst) {
    $tok = $null
    try { $tok = Join-Path (Split-Path $VIA -Parent) ((Get-Content -LiteralPath (Join-Path $reg "VIA_ToolVersion_Lock_v0100.json") -Raw -Encoding UTF8 | ConvertFrom-Json).token.path) } catch { }
    if ($tok -and (Test-Path -LiteralPath $tok)) {
        Invoke-QSStep "③ AST 全景(治理七類)" @($tok, "scan", "--fast") "\[計\]|錨點|治理|ACCEL|HARDIMP|PINVER|NET|VERB|SYSEXE|TALIB"
        Invoke-QSStep "③ AST 全景(通用 AST:VDF · VRN · registry)" @($tok, "read", (Join-Path $VIA "functional modules\VDF"), (Join-Path $VIA "functional modules\VRN"), $reg) "問題|SYNTAX|COMPILE|DUPDEF|TAILAPI|token 帳"
    } else {
        $script:rows += [pscustomobject]@{ Step = "③ AST 全景"; Lamp = "NODATA"; Rc = 3; Secs = 0; Verdict = "鎖冊 token 工具不在(VIA_ToolVersion_Lock_v0100.json token.path)" }
    }
}
Invoke-QSStep "④ 動詞模組化(VCGC test --quick)" @($vcgc.FullName, "test", "--quick") "VCGC 全功能串測\]|\[(RED|YELLOW) *\]|未登錄"
if (-not $SkipEnv) {
    Invoke-QSStep "⑤ 工具與環境(ENV MANAGER)" @($vcgc.FullName, "run", "CGC_MDL240_EnvManager", "check") "ENV MANAGER\] 總判|^\s*(AMBER|RED|NODATA) "
    Invoke-QSStep "⑤ 環境現況衝突(八路 + uv)" @($vcgc.FullName, "run", "CGC_MDL135_EnvGovernance", "eight-hub") "八路|BLOCK|衝突|NODATA|GREEN"
}
$env:VIA_FROM_VCGC = $fromBefore
$env:VIA_VCGC_PUSH = $pushBefore

Write-Host ("=== [via-quickscan] 總表 · " + [int]((Get-Date) - $t0all).TotalSeconds + "s ===") -ForegroundColor Cyan
$rows | Format-Table -AutoSize -Wrap | Out-String -Width 220 | Write-Host
$pages = @((Join-Path $rep "toolprobe\COVERAGE_MATRIX_latest.html"), (Join-Path $rep "panorama\monitor_latest.html")) | Where-Object { Test-Path -LiteralPath $_ }
foreach ($p in $pages) { Write-Host ("  [頁] " + $p) -ForegroundColor DarkGray }
if (-not $NoOpen) {
    foreach ($p in $pages) { try { Invoke-Item -LiteralPath $p } catch { Write-Host ("  [頁] 開不起來(照實):" + $_.Exception.Message) -ForegroundColor Yellow } }
}
$final = if ($rows | Where-Object { $_.Lamp -eq "RED" }) { 1 } elseif ($rows | Where-Object { $_.Lamp -ne "GREEN" }) { 2 } else { 0 }
Write-Host ("=== [via-quickscan] 畢 · 總判 " + @("GREEN", "RED", "YELLOW")[$final] + " · rc " + $final + " ===") -ForegroundColor $(@("Green", "Red", "Yellow")[$final])
if ($script:Dotted) { $global:LASTEXITCODE = $final; return } else { exit $final }
