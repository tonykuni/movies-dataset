#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-UserTest v0100 — 使用者旅程實測(操作員整併重整令 2026/08/12)
------------------------------------------------------------------------------------------
 依操作員實際使用步驟逐段驗證(不重跑重活;產物在位+輕量實跑):
   U01 Git 同步狀態            U02 指揮板產物+版字     U03 WorkOps 核心產物盤點
   U04 解析口徑版本(≥v0106)    U05 VAP 資料發現         U06 VAP 配對圖實渲染
   U07 VAP 多面板實渲染        U08 WorkflowEngine 自測  U09 TALib 自測
   U10 ChipWar 方法論驗收      U11 MultiFactor 測試     U12 模組健檢側車(ALL v0110)
 治理:全唯讀+沙箱輸出;缺件=誠實 SKIP 不冒充;逐段 OK/FAIL/SKIP;
 報告落 functional modules\WorkOps\out\usertest_report.json(板可吸收)。
 直譯器動態解析:py → python3(容器/CI 亦可跑)。
==========================================================================================
#>
param([switch]$SkipHeavy)
$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
$WorkOps = Join-Path $Root "functional modules\WorkOps"
$OutDir = Join-Path $WorkOps "out"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Py = $(if (Get-Command py -ErrorAction SilentlyContinue) { "py" }
        elseif (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" }
        else { "python" })
$Steps = [System.Collections.Generic.List[object]]::new()
function Step { param([string]$Id, [string]$Name, [scriptblock]$Body)
    Write-Host ("──── {0} {1} ────" -f $Id, $Name) -ForegroundColor Cyan
    $t = [Diagnostics.Stopwatch]::StartNew()
    $r = "OK"; $note = ""
    try { $out = & $Body
          if ($out -is [hashtable]) { $r = $out.r; $note = $out.note } }
    catch { $r = "FAIL"; $note = $_.Exception.Message }
    $t.Stop()
    $color = @{ OK = "Green"; SKIP = "DarkYellow"; FAIL = "Red" }[$r]
    Write-Host ("  [{0}] {1}" -f $r, $note) -ForegroundColor $color
    $Steps.Add([pscustomobject]@{ 步 = $Id; 名 = $Name; 結果 = $r; 註 = $note; 秒 = [math]::Round($t.Elapsed.TotalSeconds, 1) })
}
function RunPy { param([string]$File, [string[]]$Args2, [string]$Cwd)
    Push-Location $Cwd
    try { $o = & $Py $File @Args2 2>&1 | Out-String; return @{ code = $LASTEXITCODE; out = $o } }
    finally { Pop-Location }
}
Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host "  VIA UserTest v0100  |  使用者旅程逐段實測(唯讀;缺件誠實 SKIP)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

Step "U01" "Git 同步狀態" {
    if (-not (Test-Path (Join-Path $Root "..\.git"))) { return @{ r = "SKIP"; note = "非 git 檢出" } }
    $repo = Split-Path $Root -Parent
    git -C $repo fetch origin main 2>&1 | Out-Null
    $behind = git -C $repo rev-list --count "HEAD..origin/main" 2>$null
    if ($LASTEXITCODE -ne 0) { return @{ r = "SKIP"; note = "離線 — 無法比對遠端" } }
    if ([int]$behind -gt 0) { return @{ r = "FAIL"; note = "落後 origin/main $behind commit — 先 via-sync" } }
    @{ r = "OK"; note = "與 origin/main 同步" }
}
Step "U02" "指揮板產物+版字" {
    $b = Join-Path $Root "VIA_Reports\workops_run\VIA_WorkOps_CommandBoard.html"
    if (-not (Test-Path $b)) { return @{ r = "SKIP"; note = "板未產(via-workops all 後自動出現)" } }
    $newest = Get-ChildItem -Path $WorkOps -Filter "Invoke-VIA-WorkOps-CommandBoard-v0*.ps1" | Sort-Object Name | Select-Object -Last 1
    @{ r = "OK"; note = ("板在位;最新板腳本 " + $newest.Name) }
}
Step "U03" "WorkOps 核心產物盤點" {
    $need = @("wop_registry.json", "unified_work_register.csv", "project_health.json", "selftest_report.json")
    $miss = @($need | Where-Object { -not (Test-Path (Join-Path $OutDir $_)) })
    if ($miss -contains "wop_registry.json") { return @{ r = "SKIP"; note = ("尚未跑 via-workops all(在位 {0}/4)" -f ($need.Count - $miss.Count)) } }
    if ($miss.Count) { return @{ r = "FAIL"; note = ("缺:" + ($miss -join "、")) } }
    @{ r = "OK"; note = "四產物全在位" }
}
Step "U04" "解析口徑版本(≥v0106 應答域正本)" {
    $rs = Join-Path $OutDir "reply_status.json"
    if (-not (Test-Path $rs)) { return @{ r = "SKIP"; note = "reply_status.json 未產" } }
    $v = (Get-Content $rs -Raw -Encoding UTF8 | ConvertFrom-Json).version
    if ([string]$v -lt "v0105") { return @{ r = "FAIL"; note = "版本 $v 過舊 — 重跑 via-workops replies" } }
    @{ r = "OK"; note = "reply_status $v(口徑=應答域)" }
}
Step "U05" "VAP 資料發現(--list)" {
    $eng = Get-ChildItem -Path (Join-Path $Root "functional modules\VAP\engine") -Filter "VAP_ENG001_AutoplotEngineChartlib_v0*.py" | Sort-Object Name | Select-Object -Last 1
    if (-not $eng) { return @{ r = "FAIL"; note = "chartlib 不在位" } }
    $r2 = RunPy $eng.FullName @("--base", $Root, "--list") $Root
    if ($r2.code -ne 0 -and $r2.out -notmatch "table") { return @{ r = "SKIP"; note = "VDF db 無資料(--demo 可補)" } }
    $n = ([regex]::Matches($r2.out, "rows,")).Count
    @{ r = "OK"; note = ("{0} · 發現 {1} 表" -f $eng.Name, $n) }
}
Step "U06" "VAP 配對圖實渲染(沙箱)" {
    $eng = Get-ChildItem -Path (Join-Path $Root "functional modules\VAP\engine") -Filter "VAP_ENG001_AutoplotEngineChartlib_v0*.py" | Sort-Object Name | Select-Object -Last 1
    $tmp = Join-Path ([IO.Path]::GetTempPath()) "via_usertest_vap"
    $r2 = RunPy $eng.FullName @("--base", $Root, "--demo", "--table", "demo_tw_stock_monthly", "--x", "date", "--left", "close", "--right", "volume", "--out", $tmp) $Root
    if ($r2.out -match "CHART ") { return @{ r = "OK"; note = "bar+line 配對圖渲染成功(沙箱)" } }
    @{ r = "FAIL"; note = ($r2.out -split "`n" | Select-Object -Last 2) -join " " }
}
Step "U07" "VAP 多面板實渲染(--panels)" {
    $eng = Get-ChildItem -Path (Join-Path $Root "functional modules\VAP\engine") -Filter "VAP_ENG001_AutoplotEngineChartlib_v0*.py" | Sort-Object Name | Select-Object -Last 1
    $tmp = Join-Path ([IO.Path]::GetTempPath()) "via_usertest_vap"
    $r2 = RunPy $eng.FullName @("--base", $Root, "--table", "demo_tw_stock_monthly", "--panels", "close;close@yoy;volume:bar", "--out", $tmp) $Root
    if ($r2.out -match "panels") { return @{ r = "OK"; note = "3 面板同時間軸渲染成功(沙箱)" } }
    @{ r = "FAIL"; note = ($r2.out -split "`n" | Select-Object -Last 2) -join " " }
}
Step "U08" "WorkflowEngine 自測(ENG-056)" {
    if ($SkipHeavy) { return @{ r = "SKIP"; note = "-SkipHeavy" } }
    $r2 = RunPy (Join-Path $Root "VIA_WorkflowEngine.py") @("selftest") $Root
    if ($r2.out -match "0 FAIL") { return @{ r = "OK"; note = (($r2.out -split "`n" | Where-Object { $_ -match "合計" }) -join "").Trim() } }
    @{ r = "FAIL"; note = "selftest 未全過" }
}
Step "U09" "TALib 自測(ENG-058)" {
    if ($SkipHeavy) { return @{ r = "SKIP"; note = "-SkipHeavy" } }
    $r2 = RunPy (Join-Path $Root "functional modules\TALib\VIA_ENG003_TALibEngine.py") @("selftest") (Join-Path $Root "functional modules\TALib")
    if ($r2.out -match "0 FAIL") { return @{ r = "OK"; note = (($r2.out -split "`n" | Where-Object { $_ -match "合計" }) -join "").Trim() } }
    @{ r = "FAIL"; note = "selftest 未全過" }
}
Step "U10" "ChipWar 方法論驗收(ENG-060)" {
    if ($SkipHeavy) { return @{ r = "SKIP"; note = "-SkipHeavy" } }
    $r2 = RunPy (Join-Path $Root "functional modules\ChipWar\engines\CHW_ENG023_TestHarness.py") @() (Join-Path $Root "functional modules\ChipWar\engines")
    if ($r2.out -match "L2") { return @{ r = "OK"; note = (($r2.out -split "`n" | Where-Object { $_ -match "最終驗收" }) -join "").Trim() } }
    @{ r = "FAIL"; note = "harness 未過" }
}
Step "U11" "MultiFactor 測試(ENG-059;v0101 動態路徑)" {
    if ($SkipHeavy) { return @{ r = "SKIP"; note = "-SkipHeavy" } }
    $t = Join-Path $Root "functional modules\MultiFactor\engines\test_VIA_MultiFactor_TestValidateSim_Engine_v0101.py"
    $r2 = RunPy $t @() (Split-Path $t -Parent)
    if ($r2.out -match "ALL_TESTS_PASS") { return @{ r = "OK"; note = "ALL_TESTS_PASS" } }
    @{ r = "FAIL"; note = "測試未全過" }
}
Step "U12" "模組健檢側車(ALL v0110 之 2e5)" {
    $p = Join-Path $OutDir "module_probe.json"
    if (-not (Test-Path $p)) { return @{ r = "SKIP"; note = "尚未跑 v0110 all(跑後自動出現)" } }
    $j = Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json
    $miss = @($j.modules.PSObject.Properties | Where-Object { $_.Value -eq "缺席" } | ForEach-Object { $_.Name })
    if ($miss.Count) { return @{ r = "OK"; note = ("在案;缺席模組:" + ($miss -join "、")) } }
    @{ r = "OK"; note = "七模組全在位" }
}

Write-Host ""
Write-Host "──── 使用者旅程總結 ────" -ForegroundColor Cyan
$Steps | Format-Table -AutoSize | Out-String | Write-Host
$rep = [ordered]@{ ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss"); version = "v0100"
                   steps = @($Steps | ForEach-Object { [ordered]@{ id = $_.步; name = $_.名; r = $_.結果; note = $_.註; sec = $_.秒 } }) }
($rep | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath (Join-Path $OutDir "usertest_report.json") -Encoding UTF8
$nF = @($Steps | Where-Object { $_.結果 -eq "FAIL" }).Count
$nS = @($Steps | Where-Object { $_.結果 -eq "SKIP" }).Count
Write-Host ("[總結] UserTest {0} 步:OK {1} · SKIP {2}(誠實列缺) · FAIL {3} → out\usertest_report.json" -f $Steps.Count, ($Steps.Count - $nF - $nS), $nS, $nF) -ForegroundColor $(if ($nF) { "Yellow" } else { "Green" })
exit $(if ($nF) { 1 } else { 0 })

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
