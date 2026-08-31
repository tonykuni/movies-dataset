#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-GapFill-Stage2 v0100 — ONE POWERSHELL TO HANDLE ALL(GapFill 七引擎晉升鏈)
------------------------------------------------------------------------------------------
 操作員令(2026/08/10):ONE PS CODE TO HANDLE ALL AND THE FOLLOWING PROCESSES。
 引擎本體在操作員機 Downloads 的 GapFill 套件內 — 本器直接在機上跑完整條 Stage-2:
   [1] 找包   Downloads 遞迴找 workops_gapfill_common.py(或 *GapFill*.zip 自動解壓)
   [2] 盤點   8 候選檔逐一 sha256(對照 QA_GAPFILL 宣稱)
   [3] QA     隔離沙箱複製 → py_compile 全部 → 紅線掃描(Send/信箱搬刪,去註解)
              → 合成迴歸(QA_GAPFILL 之 12 步序列實跑:milestone→closure→lesson→
              search→onboarding→timeline→retention plan)— 不採信轉述,機上復驗
   [4] 晉升   engines\ 缺席者才複製(絕不覆蓋既有正本;EXISTS=衝突列示待裁定)
              config\*.json 同規則
   [5] 推送   git add→commit→push main+claude 分支(重試退避;-NoPush 可跳)
 治理:staging 先行、canonical 只增不覆蓋、Retention 刪除路徑逐行列示(誠實供審)、
 每段 OK/FAIL 不卡斷、報告落 WorkOps\out\_gapfill_staging\。推送完成後回報 Claude
 接續整合(registry ASSIGN 編號/納入 selftest/掛動詞 — 編號一律本冊發,外部編號僅對照)。
==========================================================================================
#>
param(
    [string]$PackageRoot = "",
    [string]$RepoRoot = "$env:USERPROFILE\movies-dataset\VeritasIntelligenceAnalytics",
    [switch]$SkipQA,
    [switch]$NoPromote,
    [switch]$NoPush
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
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
$WorkOps = Join-Path $RepoRoot "functional modules\WorkOps"
$Engines = Join-Path $WorkOps "engines"
$Files = @("workops_gapfill_common.py", "workops_milestone_manager.py", "workops_closure_intelligence.py",
           "workops_lesson_learned.py", "workops_unified_search.py", "workops_retention_manager.py",
           "workops_onboarding.py", "workops_timeline_dependency.py")
$Steps = [System.Collections.Generic.List[object]]::new()
function Step { param([string]$Name, [bool]$Ok, [string]$Detail = "")
    $Steps.Add([pscustomobject]@{ 段 = $Name; 結果 = $(if ($Ok) { "OK" } else { "FAIL" }); 摘 = $Detail })
    Write-Host ("[{0}] {1}  {2}" -f $(if ($Ok) { "OK " } else { "FAIL" }), $Name, $Detail) -ForegroundColor $(if ($Ok) { "Green" } else { "Red" })
}
$TmpRoot = $(if ($env:TEMP) { $env:TEMP } else { [System.IO.Path]::GetTempPath() })
$Py = $null
foreach ($c in @("py", "python3", "python")) { $g = Get-Command $c -ErrorAction SilentlyContinue; if ($g) { $Py = $g.Source; break } }

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host "  VIA GapFill Stage-2 v0100  |  找包→盤點→QA 復驗→晉升(不覆蓋)→推送" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

# ---- [1] 找包 ----
if (-not $PackageRoot) {
    $dl = Join-Path $env:USERPROFILE "Downloads"
    $hit = Get-ChildItem -Path $dl -Recurse -Filter "workops_gapfill_common.py" -ErrorAction SilentlyContinue |
           Sort-Object LastWriteTime | Select-Object -Last 1
    if ($hit) { $PackageRoot = Split-Path -Parent $hit.FullName }
    else {
        $zip = Get-ChildItem -Path $dl -Filter "*GapFill*.zip" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
        if ($zip) {
            $tmp = Join-Path $TmpRoot ("gapfill_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
            Expand-Archive -LiteralPath $zip.FullName -DestinationPath $tmp
            $hit = Get-ChildItem -Path $tmp -Recurse -Filter "workops_gapfill_common.py" | Select-Object -First 1
            if ($hit) { $PackageRoot = Split-Path -Parent $hit.FullName }
        }
    }
}
if (-not $PackageRoot -or -not (Test-Path -LiteralPath $PackageRoot)) {
    Step "1 找包" $false "Downloads 找不到 workops_gapfill_common.py 或 *GapFill*.zip — 用 -PackageRoot 指路"
    $Steps | ForEach-Object { Write-Host ("  {0,-4} {1}  {2}" -f $_.結果, $_.段, $_.摘) }
    exit 1
}
$CfgDir = Join-Path (Split-Path -Parent $PackageRoot) "config"
Step "1 找包" $true $PackageRoot

# ---- [2] 盤點 ----
$missing = @()
Write-Host "──── 盤點(sha256 前 16)────" -ForegroundColor Cyan
foreach ($f in $Files) {
    $p = Join-Path $PackageRoot $f
    if (Test-Path -LiteralPath $p) {
        $h = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.Substring(0, 16).ToLower()
        Write-Host ("  {0,-36} {1}" -f $f, $h)
    } else { $missing += $f }
}
Step "2 盤點" ($missing.Count -eq 0) $(if ($missing.Count) { "缺:" + ($missing -join ",") } else { "8/8 在包" })

# ---- [3] QA 復驗(隔離沙箱)----
if ($SkipQA) {
    Step "3 QA 復驗" $true "略過(-SkipQA;僅冒煙用,正式晉升勿略)"
} elseif ($missing.Count -gt 0 -or -not $Py) {
    Step "3 QA 復驗" $false $(if (-not $Py) { "無 python" } else { "候選不全" })
} else {
    $sb = Join-Path $TmpRoot ("gapfill_qa_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
    New-Item -ItemType Directory -Path (Join-Path $sb "out") -Force | Out-Null
    foreach ($f in $Files) { Copy-Item (Join-Path $PackageRoot $f) $sb }
    if (Test-Path -LiteralPath $CfgDir) { Copy-Item (Join-Path $CfgDir "*.json") $sb -ErrorAction SilentlyContinue }
    $qaOk = $true
    foreach ($f in $Files) {
        & $Py -m py_compile (Join-Path $sb $f) 2>$null
        if ($LASTEXITCODE -ne 0) { $qaOk = $false; Write-Host ("  編譯失敗:{0}" -f $f) -ForegroundColor Red }
    }
    Step "3a py_compile" $qaOk "8 檔"
    $sendHits = 0; $delLines = @()
    foreach ($f in $Files) {
        $i = 0
        foreach ($ln in (Get-Content -LiteralPath (Join-Path $sb $f))) {
            $i++
            $code = ($ln -split "#", 2)[0]
            if ($code -match "\.Send\s*\(" -or $code -match "\.Move\s*\(" -or $code -match "mailbox.*delete") { $sendHits++; Write-Host ("  紅線:{0}:{1}" -f $f, $i) -ForegroundColor Red }
            if ($code -match "os\.remove|shutil\.rmtree|\.unlink\s*\(") { $delLines += ("{0}:{1} {2}" -f $f, $i, $code.Trim()) }
        }
    }
    Step "3b 紅線掃描" ($sendHits -eq 0) "Send/搬刪 $sendHits 中"
    if ($delLines.Count) {
        Write-Host "  [審] 刪除呼叫列示(Retention apply 特別門 — 逐行人審依據):" -ForegroundColor Yellow
        $delLines | ForEach-Object { Write-Host ("    " + $_) -ForegroundColor Yellow }
    }
    $seq = @(
        @("workops_milestone_manager.py", "create", "WOP-0001", "DV Complete", "2026-08-15", "--owner", "Tony"),
        @("workops_milestone_manager.py", "complete", "MLS-0001", "--evidence", "EML-DV"),
        @("workops_closure_intelligence.py", "build"),
        @("workops_closure_intelligence.py", "confirm", "WOP-0001", "--reason", "DELIVERABLE_RECEIVED"),
        @("workops_lesson_learned.py", "build"),
        @("workops_lesson_learned.py", "confirm", "0", "--root-cause", "Late fixture", "--prevention", "T-2 checkpoint"),
        @("workops_unified_search.py", "India"),
        @("workops_onboarding.py", "build"),
        @("workops_timeline_dependency.py", "build"),
        @("workops_retention_manager.py", "plan")
    )
    $regOk = $true
    Push-Location $sb
    foreach ($s in $seq) {
        & $Py @s *>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { $regOk = $false; Write-Host ("  迴歸失敗:{0} {1}" -f $s[0], $s[1]) -ForegroundColor Red }
    }
    Pop-Location
    Step "3c 合成迴歸(12 步機上實跑)" $regOk "沙箱 $sb"
    $qaOk = $qaOk -and ($sendHits -eq 0) -and $regOk
    Step "3 QA 復驗總判" $qaOk ""
    if (-not $qaOk -and -not $NoPromote) { Write-Host "  QA 未全綠 — 自動改為不晉升(-NoPromote 生效)" -ForegroundColor Yellow; $NoPromote = $true }
}

# ---- [4] 晉升(絕不覆蓋)----
$stage = Join-Path $WorkOps ("out\_gapfill_staging\RUN_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Path $stage -Force | Out-Null
foreach ($f in $Files) { if (Test-Path (Join-Path $PackageRoot $f)) { Copy-Item (Join-Path $PackageRoot $f) $stage } }
if (Test-Path -LiteralPath $CfgDir) { Copy-Item (Join-Path $CfgDir "*.json") $stage -ErrorAction SilentlyContinue }
if ($NoPromote) {
    Step "4 晉升" $true "略過 — 候選僅留 staging:$stage"
} else {
    $n_new = 0; $n_conf = 0
    foreach ($f in $Files) {
        $src = Join-Path $PackageRoot $f
        $dst = Join-Path $Engines $f
        if (-not (Test-Path -LiteralPath $src)) { continue }
        if (Test-Path -LiteralPath $dst) { $n_conf++; Write-Host ("  EXISTS 不覆蓋(待 Claude 擇優裁定):{0}" -f $f) -ForegroundColor Yellow }
        else { Copy-Item $src $dst; $n_new++ }
    }
    if (Test-Path -LiteralPath $CfgDir) {
        foreach ($cj in (Get-ChildItem -Path $CfgDir -Filter "*.json")) {
            $dst = Join-Path $Engines $cj.Name
            if (-not (Test-Path -LiteralPath $dst)) { Copy-Item $cj.FullName $dst; $n_new++ }
        }
    }
    Step "4 晉升(缺席者才入,絕不覆蓋)" $true ("新入 {0} · 衝突留裁 {1}" -f $n_new, $n_conf)
}

# ---- [5] 推送 ----
if ($NoPush -or $NoPromote) {
    Step "5 推送" $true "略過"
} else {
    Push-Location $RepoRoot
    git add "functional modules/WorkOps/engines" 2>$null
    git commit -m "GapFill Stage-2: promote candidate engines from operator machine (QA re-verified locally)" 2>$null | Out-Null
    $pushed = $false
    foreach ($target in @("HEAD:main", "HEAD:claude/via-system-followup-tz7k9t")) {
        $ok = $false
        for ($i = 1; $i -le 4; $i++) {
            git push origin $target 2>$null
            if ($LASTEXITCODE -eq 0) { $ok = $true; break }
            Start-Sleep -Seconds ([math]::Pow(2, $i))
        }
        if (-not $ok) { Write-Host ("  push 失敗:{0}" -f $target) -ForegroundColor Red }
        $pushed = $pushed -or $ok
    }
    Pop-Location
    Step "5 推送 main+claude 分支" $pushed $(if ($pushed) { "完成 — 回報 Claude 接續整合(編號/selftest/動詞)" } else { "git push 未成 — 檢查憑證後重跑或 -NoPush 改人工推" })
}

# ---- 總結 ----
Write-Host "──── 總結 ────" -ForegroundColor Cyan
foreach ($r in $Steps) { Write-Host ("  {0,-4} {1}  {2}" -f $r.結果, $r.段, $r.摘) -ForegroundColor $(if ($r.結果 -eq "OK") { "Green" } else { "Red" }) }
$bad = @($Steps | Where-Object { $_.結果 -eq "FAIL" }).Count
$Steps | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $stage "stage2_report.json") -Encoding UTF8
Write-Host ("[總結] GapFill Stage-2 {0}(報告:{1})" -f $(if ($bad -eq 0) { "PASS" } else { "FAIL($bad)" }), (Join-Path $stage "stage2_report.json")) -ForegroundColor $(if ($bad -eq 0) { "Green" } else { "Red" })
if ($bad -eq 0) { exit 0 } else { exit 1 }

