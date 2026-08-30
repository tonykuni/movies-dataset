#requires -Version 7.0
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
<#
==========================================================================================
 Invoke-VIA-TrinityClosure v0100 — VDF · VRN · VAP 結案器(ONE POWERSHELL)
------------------------------------------------------------------------------------------
 操作員令(2026/08/10):「將 VDF VRN VAP 結案 一個 POWERSHELL CODE TO HANDLE THE
 FOLLOWING PROCESSES」。本器一支跑完三子系統全部結案程序:
   [VDF] manifest/取數契約 JSON 驗證+14 域 277 項盤點 · MDL 引擎編譯 · 啟動器動態解析
   [VRN] 守護入口 AST · freeze.lock 凍結完整性 · VisualLock 正本 sha 封存驗證
   [VAP] manifest artifacts 逐件在位 · 引擎編譯 · spec SSOT JSON 驗證 · v002 升級鏈追源
   [共通] 三樹紅線稽核(.Send 零容忍)· 結案快照 JSON(append-only 時戳檔)· 誠實總結
 結案=盤點+封存基線,零觸碰正本(只讀;快照為新增檔)。每項誠實 OK/FAIL 不卡斷;
 三系統各自 Gate + 總 FinalGate=PASS 才算結案成立。可重跑(每跑一份新快照)。
 產物:VIA_Reports\closure\VIA_Trinity_Closure_Report.html + 快照 JSON。
==========================================================================================
#>
param([switch]$NoOpen)
$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
$FM = Join-Path $Root "functional modules"
$Checks = [System.Collections.Generic.List[object]]::new()
$Py = $null
foreach ($c in @("py", "python3", "python")) {
    $g = Get-Command $c -ErrorAction SilentlyContinue
    if ($g) { $Py = $g.Source; break }
}
function Check { param([string]$Sys, [string]$Name, [bool]$Ok, [string]$Detail = "")
    $Checks.Add([pscustomobject]@{ 系統 = $Sys; 項 = $Name; 結果 = $(if ($Ok) { "OK" } else { "FAIL" }); 摘 = $Detail })
    $c = if ($Ok) { "Green" } else { "Red" }
    Write-Host ("  [{0}] {1} · {2}  {3}" -f $(if ($Ok) { "OK " } else { "FAIL" }), $Sys, $Name, $Detail) -ForegroundColor $c
}
function Test-Json { param([string]$Path)
    try { $null = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json; return $true } catch { return $false }
}
function Test-PyCompile { param([string]$Path)
    if (-not $Py) { return $false }
    & $Py -m py_compile $Path 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}
function Test-PsAst { param([string]$Path)
    $tok = $null; $err = $null
    [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tok, [ref]$err) | Out-Null
    return (-not ($err -and $err.Count))
}
function Get-Sha16 { param([string]$Path)
    # 行尾正規化後計算(Windows autocrlf 簽出 CRLF、倉內 LF — 內容等值即同 sha,跨平台恆定)
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $text = [System.Text.Encoding]::UTF8.GetString($bytes).Replace("`r`n", "`n")
    [byte[]]$norm = [System.Text.Encoding]::UTF8.GetBytes($text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { (($sha.ComputeHash($norm) | ForEach-Object { $_.ToString("x2") }) -join "").Substring(0, 16) }
    finally { $sha.Dispose() }
}

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host "  VIA Trinity Closure v0100  |  VDF · VRN · VAP 結案盤點(唯讀;快照 append-only)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

# ================= VDF =================
Write-Host "`n──── VDF 資料取數子系統 ────" -ForegroundColor Cyan
$vdf = Join-Path $FM "VDF"
Check "VDF" "子系統 manifest JSON" (Test-Json (Join-Path $vdf "VDF_Subsystem_Manifest.json"))
$fc = Join-Path $vdf "registry\VIA_VDF_Fetch_Contract.json"
$fcOk = Test-Json $fc
$fcDetail = ""
if ($fcOk) {
    $c = Get-Content -LiteralPath $fc -Raw -Encoding UTF8 | ConvertFrom-Json
    $items = @($c.domains | ForEach-Object { $_.items }) | ForEach-Object { $_ }
    $nOk = @($items | Where-Object { $_.status -eq "ok" }).Count
    $nPx = @($items | Where-Object { $_.status -eq "proxy" }).Count
    $nTd = @($items | Where-Object { $_.status -eq "todo" }).Count
    $fcDetail = "{0} 域 {1} 項(ok {2}/proxy {3}/todo {4})" -f @($c.domains).Count, @($items).Count, $nOk, $nPx, $nTd
    $fcOk = (@($c.domains).Count -eq 14 -and @($items).Count -eq 277)
}
Check "VDF" "取數契約 SSOT 盤點" $fcOk $fcDetail
$mdlAll = $true
foreach ($m in (Get-ChildItem -Path $vdf -Filter "VDF_MDL*.py" -File)) {
    if (-not (Test-PyCompile $m.FullName)) { $mdlAll = $false; Write-Host ("    編譯失敗:{0}" -f $m.Name) -ForegroundColor Red }
}
Check "VDF" "MDL 引擎編譯" $mdlAll ("共 " + @(Get-ChildItem -Path $vdf -Filter "VDF_MDL*.py" -File).Count + " 支")
$starter = Get-ChildItem -Path $vdf -Filter "Start-VIA-VDF-v0*.ps1" -File | Sort-Object Name | Select-Object -Last 1
Check "VDF" "啟動器動態解析" ($null -ne $starter -and (Test-PsAst $starter.FullName)) $(if ($starter) { $starter.Name } else { "缺" })

# ================= VRN =================
Write-Host "`n──── VRN 報告修復子系統 ────" -ForegroundColor Cyan
$vrn = Join-Path $FM "VRN"
Check "VRN" "子系統 manifest JSON" (Test-Json (Join-Path $vrn "VRN_Subsystem_Manifest.json"))
$ge = Join-Path $vrn "Invoke-VRN-Guarded-Entry-v217.ps1"
Check "VRN" "守護入口 AST" ((Test-Path -LiteralPath $ge) -and (Test-PsAst $ge)) "Guarded-Entry v217"
$locks = @(Get-ChildItem -Path $vrn -Filter "*.freeze.lock.json" -File)
$lockOk = ($locks.Count -gt 0)
foreach ($lk in $locks) {
    $target = Join-Path $vrn ($lk.Name -replace "\.freeze\.lock\.json$", "")
    if (-not (Test-Path -LiteralPath $target)) { $lockOk = $false; Write-Host ("    凍結對象缺席:{0}" -f $lk.Name) -ForegroundColor Red }
}
Check "VRN" "freeze.lock 凍結完整性" $lockOk ("{0} 副鎖,對象逐一在位" -f $locks.Count)
$vl = Join-Path $Root "supportive modules\VIA_VisualLock\VIA_VRN_VisualLock_Sidebar_v0159.html"
$vlOk = (Test-Path -LiteralPath $vl) -and ((Get-Sha16 $vl) -eq "23000e2958e9aaf9")
Check "VRN" "VisualLock 正本 sha 封存" $vlOk "v0159 · 23000e2958e9aaf9(板 UI 風格源)"

# ================= VAP =================
Write-Host "`n──── VAP 自動繪圖子系統 ────" -ForegroundColor Cyan
$vap = Join-Path $FM "VAP"
$vmP = Join-Path $vap "VAP_Subsystem_Manifest.json"
$vmOk = Test-Json $vmP
$artOk = $false; $artDetail = ""
if ($vmOk) {
    $vm = Get-Content -LiteralPath $vmP -Raw -Encoding UTF8 | ConvertFrom-Json
    $arts = @($vm.artifacts)
    $missing = @($arts | Where-Object { -not (Test-Path -LiteralPath (Join-Path $vap $_.filename)) })
    $artOk = ($arts.Count -gt 0 -and $missing.Count -eq 0)
    $artDetail = "{0} artifacts 逐件在位" -f $arts.Count
    foreach ($ms in $missing) { Write-Host ("    缺席:{0}" -f $ms.filename) -ForegroundColor Red }
}
Check "VAP" "子系統 manifest JSON" $vmOk
Check "VAP" "manifest artifacts 在位" $artOk $artDetail
$e1 = Join-Path $vap "engine\VAP_ENG002_AutoplotEngine_v001.py"
$e2 = Join-Path $vap "engine\VAP_ENG001_AutoplotEngineChartlib_v002.py"
Check "VAP" "繪圖引擎編譯" ((Test-PyCompile $e1) -and (Test-PyCompile $e2)) "v001 + chartlib v002"
Check "VAP" "spec SSOT JSON" ((Test-Json (Join-Path $vap "spec\ssot\vap_spec.json")) -and (Test-Json (Join-Path $vap "spec\ssot\vap_chartlib.json"))) "vap_spec + vap_chartlib"
$promOk = $false
if (Test-Path -LiteralPath $e2) {
    $head = (Get-Content -LiteralPath $e2 -TotalCount 3 -Encoding UTF8) -join " "
    $promOk = ($head -match "2AE164B5082B2113")
}
Check "VAP" "v002 升級鏈追源" $promOk "PROMOTION_RECORD 含來源候選 sha(上傳件=已整合實證)"

# ================= 共通紅線 =================
Write-Host "`n──── 共通紅線稽核 ────" -ForegroundColor Cyan
$sendHits = 0
foreach ($tree in @($vdf, $vrn, $vap)) {
    foreach ($f in (Get-ChildItem -Path $tree -Recurse -File -Include "*.ps1", "*.py" -ErrorAction SilentlyContinue)) {
        $raw = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
        if ($null -eq $raw) { continue }
        $raw = $raw -replace "(?s)<#.*?#>", ""
        if ($raw -match "\.Send\s*\(") { $sendHits++; Write-Host ("    紅線命中:{0}" -f $f.FullName) -ForegroundColor Red }
    }
}
Check "共通" "紅線 .Send( 零容忍" ($sendHits -eq 0) "三樹全掃"

# ================= 總結+快照 =================
Write-Host "`n──── 結案總結 ────" -ForegroundColor Cyan
foreach ($r in $Checks) {
    $c = if ($r.結果 -eq "OK") { "Green" } else { "Red" }
    Write-Host ("  {0,-4} {1,-4} {2}  {3}" -f $r.結果, $r.系統, $r.項, $r.摘) -ForegroundColor $c
}
$gates = [ordered]@{}
foreach ($sys in @("VDF", "VRN", "VAP", "共通")) {
    $bad = @($Checks | Where-Object { $_.系統 -eq $sys -and $_.結果 -eq "FAIL" }).Count
    $gates[$sys] = $(if ($bad -eq 0) { "PASS" } else { "FAIL" })
}
$final = $(if (@($Checks | Where-Object { $_.結果 -eq "FAIL" }).Count -eq 0) { "PASS" } else { "FAIL" })
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$repDir = Join-Path $Root "VIA_Reports\closure"
if (-not (Test-Path $repDir)) { New-Item -ItemType Directory -Path $repDir -Force | Out-Null }
$snap = [ordered]@{
    ts = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss"); tool = "Invoke-VIA-TrinityClosure-v0100"
    gates = $gates; final_gate = $final
    checks = $Checks
    note = "結案=盤點封存基線(唯讀);編號永不變;子系統照常可用 — 結案非停用,是版本基線落印"
}
$snapP = Join-Path $repDir ("VIA_Trinity_Closure_Snapshot_" + $ts + ".json")
$snap | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $snapP -Encoding UTF8
$rows = ($Checks | ForEach-Object {
    "<tr class='" + $(if ($_.結果 -eq "OK") { "ok" } else { "bad" }) + "'><td>" + $_.系統 + "</td><td>" + $_.項 + "</td><td>" + $_.結果 + "</td><td>" + $_.摘 + "</td></tr>" }) -join ""
$grows = ($gates.Keys | ForEach-Object { "<div class='g " + $(if ($gates[$_] -eq "PASS") { "ok" } else { "bad" }) + "'><b>" + $_ + "</b>" + $gates[$_] + "</div>" }) -join ""
$html = "<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA Trinity Closure</title><style>" +
    "body{font:15px/1.6 'Noto Sans TC','Microsoft JhengHei',sans-serif;background:#f5f4f0;color:#23221e;padding:34px}" +
    "h1{font-size:24px}.k{font-family:'DM Mono',Consolas,monospace;font-size:11px;letter-spacing:.16em;color:#6f6c63}" +
    ".gates{display:flex;gap:12px;margin:16px 0}.g{background:#fff;border:1px solid #dedbd2;border-radius:10px;padding:10px 18px;font-size:14px}" +
    ".g b{display:block;font-size:12px;color:#6f6c63}.g.ok{border-color:#2f6f5e}.g.bad{border-color:#b04532}" +
    "table{border-collapse:collapse;background:#fff;border:1px solid #dedbd2;border-radius:10px;overflow:hidden}" +
    "th,td{padding:7px 14px;border-bottom:1px solid #e4e1d8;font-size:13.5px;text-align:left}th{background:#eceae3}" +
    "tr.bad td{color:#b04532;font-weight:700}.note{color:#6f6c63;font-size:13px;margin-top:14px}</style></head><body>" +
    "<div class='k'>VERITAS INTELLIGENCE ANALYTICS</div><h1>VDF · VRN · VAP 結案報告</h1>" +
    "<p>" + $snap.ts + " · FinalGate <b>" + $final + "</b></p><div class='gates'>" + $grows + "</div>" +
    "<table><tr><th>系統</th><th>檢核項</th><th>結果</th><th>摘要</th></tr>" + $rows + "</table>" +
    "<p class='note'>結案=盤點+封存基線(全程唯讀;快照 append-only)。結案非停用 — 三子系統照常可用;後續變更一律版本前送並可重跑本器再落新基線。</p>" +
    "</body></html>"
$htmlP = Join-Path $repDir "VIA_Trinity_Closure_Report.html"
$html | Set-Content -LiteralPath $htmlP -Encoding UTF8
Write-Host ("[快照] " + $snapP)
Write-Host ("[報告] " + $htmlP)
Write-Host ("[結案] FinalGate = " + $final + "(VDF " + $gates["VDF"] + " · VRN " + $gates["VRN"] + " · VAP " + $gates["VAP"] + " · 紅線 " + $gates["共通"] + ")") -ForegroundColor $(if ($final -eq "PASS") { "Green" } else { "Red" })
if (-not $NoOpen) { try { Start-Process $htmlP | Out-Null } catch { } }
if ($final -eq "PASS") { exit 0 } else { exit 1 }

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
