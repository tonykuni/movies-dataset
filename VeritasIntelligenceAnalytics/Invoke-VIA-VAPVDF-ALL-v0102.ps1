# Invoke-VIA-VAPVDF-ALL-v0102.ps1 — 一支 PowerShell 統包三子系統 VDF+VRN+VAP(操作員令:VRN 一起,跳出 SUMMARY MATRIX)。
# 九站順跑 · 誠實逐站 OK/FAIL 不卡斷 · 動態解析最新版 · 末尾終端矩陣 + 自動跳出 HTML 專業矩陣報告 + 存證 JSON。
# 用法:via-vapvdf [-Quick] [-SkipVDF] [-SkipVRN] [-SkipVAP] [-NoOpen]
#   -Quick:每子系統只跑首站(V1/R1/A1)。-NoOpen:不自動開報告(排程用)。
param([switch]$Quick, [switch]$SkipVDF, [switch]$SkipVRN, [switch]$SkipVAP, [switch]$NoOpen)
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
$Root = Split-Path -Parent $PSCommandPath
$VDF = Join-Path $Root "functional modules\VDF"
$VRN = Join-Path $Root "functional modules\VRN"
$VAPE = Join-Path $Root "functional modules\VAP\engine"

function Get-Py {
    foreach ($c in @("py", "python3", "python")) {
        $g = Get-Command $c -ErrorAction SilentlyContinue
        if ($g) { return $g.Source }
    }
    throw "python 不在位"
}
function Get-Newest { param([string]$Dir, [string]$Pattern)
    $f = Get-ChildItem -LiteralPath $Dir -Filter $Pattern -File -ErrorAction SilentlyContinue |
        Sort-Object Name | Select-Object -Last 1
    if ($f) { return $f.FullName }
    return $null
}

$py = Get-Py
Write-Host "=== VIA 三子系統統包 v0102 · VDF+VRN+VAP · python=$py · $(if($Quick){'QUICK'}else{'FULL'}) ==="
$stages = @()
if (-not $SkipVDF) {
    $stages += , @("VDF", "V1 契約盤點", @((Get-Newest $VDF "VDF_ENG019_MDL501FetchContractManager.py"), "check"), $VDF)
    if (-not $Quick) {
        $stages += , @("VDF", "V2 302 全系統驗證", @((Get-Newest $VDF "VDF_ENG017_MDL302FinalActivation.py"), "--no-pause"), $VDF)
        $stages += , @("VDF", "V3 303 Registry 活化", @((Get-Newest $VDF "VDF_MDL303_RegistryActivation.py"), "--no-pause"), $VDF)
    }
}
if (-not $SkipVRN) {
    $stages += , @("VRN", "R1 SmokeTest", @((Get-Newest $VRN "VRN_ENG028_SmokeTest.py"), "--no-pause"), $VRN)
    if (-not $Quick) {
        $stages += , @("VRN", "R2 Panorama XCheck", @((Get-Newest $VRN "panorama_xcheck_v*.py"), "--no-pause"), $VRN)
        $inc = Join-Path $VRN "input\incoming"
        $stages += , @("VRN", "R3 進件矩陣驗證", @((Get-Newest $VRN "VRN_ENG054_InputMatrixValidator_v0*.py"), $inc), $VRN)
    }
}
if (-not $SkipVAP) {
    $stages += , @("VAP", "A1 引擎探測", @((Get-Newest $VAPE "VAP_ENG003_AutoplotSeabornPlotly_v0*.py"), "probe"), $Root)
    if (-not $Quick) {
        $stages += , @("VAP", "A2 chartlib 出圖", @((Get-Newest $VAPE "VAP_ENG001_AutoplotEngineChartlib_v0*.py"), "--demo", "--auto", "--base", $Root), $Root)
        $stages += , @("VAP", "A3 selftest 全譜", @((Get-Newest $VAPE "VAP_ENG003_AutoplotSeabornPlotly_v0*.py"), "selftest"), $Root)
    }
}

$results = @()
foreach ($s in $stages) {
    $sub = $s[0]; $name = $s[1]; $cmd = $s[2]; $wd = $s[3]
    if (-not $cmd[0]) {
        Write-Host ("  [SKIP] {0} {1} — 引擎不在位(誠實列缺)" -f $sub, $name)
        $results += [pscustomobject]@{ sub = $sub; stage = $name; verdict = "SKIP"; seconds = 0 }
        continue
    }
    Write-Host ("  ── {0} · {1} ──" -f $sub, $name)
    $t0 = Get-Date
    Push-Location $wd
    & $py @cmd 2>&1 | ForEach-Object { Write-Host ("     " + $_) }
    $rc = $LASTEXITCODE
    Pop-Location
    $dt = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    $v = if ($rc -eq 0) { "OK" } else { "FAIL(rc=$rc)" }
    Write-Host ("  [{0}] {1} {2} · {3}s" -f $v, $sub, $name, $dt)
    $results += [pscustomobject]@{ sub = $sub; stage = $name; verdict = $v; seconds = $dt }
}

# ── 終端總結矩陣 ──
Write-Host ""
Write-Host "=== 總結矩陣 · VDF+VRN+VAP ==="
$w = ($results | ForEach-Object { $_.stage.Length } | Measure-Object -Maximum).Maximum
foreach ($r in $results) {
    Write-Host ("  {0} {1}  {2,-10} {3,6}s" -f $r.sub, $r.stage.PadRight($w), $r.verdict, $r.seconds)
}
$nFail = @($results | Where-Object { $_.verdict -like "FAIL*" }).Count
$nOK = @($results | Where-Object { $_.verdict -eq "OK" }).Count
$nSkip = @($results).Count - $nOK - $nFail
$tot = [math]::Round((@($results | Measure-Object seconds -Sum).Sum), 1)
Write-Host ("  合計:OK {0} · FAIL {1} · SKIP {2} · {3}s(誠實口徑,不卡斷)" -f $nOK, $nFail, $nSkip, $tot)

# ── 存證 JSON ──
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$evDir = Join-Path $Root "VIA_Reports\vapvdf_runs"
New-Item -ItemType Directory -Path $evDir -Force | Out-Null
$ev = Join-Path $evDir ("trio_all_{0}.json" -f $ts)
[pscustomobject]@{
    version = "v0102"; generated_at = (Get-Date -Format s); mode = $(if ($Quick) { "quick" } else { "full" })
    ok = $nOK; fail = $nFail; skip = $nSkip; total_seconds = $tot; results = $results
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ev -Encoding UTF8

# ── 跳出 HTML SUMMARY MATRIX(小字級 · 自動調整 · 專業感;視覺鎖;零 CDN)──
$maxSec = [double](($results | Measure-Object seconds -Maximum).Maximum)
if ($maxSec -le 0) { $maxSec = 1 }
$rowsHtml = ""
$prevSub = ""
foreach ($r in $results) {
    if ($r.sub -ne $prevSub) {
        $subZh = @{ VDF = "VERITAS DATA FORGE · 資料鍛造"; VRN = "VERITAS REPORT NOVA · 研報治理"; VAP = "VERITAS AUTO PLOT · 繪圖稽核" }[$r.sub]
        $rowsHtml += ('<tr class="grp"><td colspan="4">{0} <span class="en">{1}</span></td></tr>' -f $r.sub, $subZh)
        $prevSub = $r.sub
    }
    $cls = if ($r.verdict -eq "OK") { "g" } elseif ($r.verdict -eq "SKIP") { "n" } else { "r" }
    $pct = [math]::Round(100 * [double]$r.seconds / $maxSec)
    $rowsHtml += ('<tr><td>{0}</td><td><span class="pill {1}">{2}</span></td><td class="num">{3}s</td><td><div class="tbar"><span style="width:{4}%"></span></div></td></tr>' `
        -f $r.stage, $cls, $r.verdict, $r.seconds, $pct)
}
$verdBig = if ($nFail -eq 0) { "ALL GREEN" } else { "$nFail FAIL" }
$verdCls = if ($nFail -eq 0) { "g" } else { "r" }
$html = @"
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Trio Summary Matrix $ts</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#f2f1ec;color:#33403f;font-family:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif;font-size:clamp(9.5px,.45vw + 8.5px,11px);padding:14px 18px;max-width:980px;margin:0 auto;line-height:1.45}
.mast{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;border-bottom:1px solid #dcdad3;padding-bottom:9px;margin-bottom:10px}
.lft{display:flex;align-items:flex-end;gap:11px}
.seal{width:30px;height:30px;background:#9e2b25;border-radius:4px;color:#f2f1ec;font-family:'Noto Serif CJK TC','PMingLiU',serif;font-weight:600;font-size:16px;line-height:30px;text-align:center}
.num0{font-family:'SFMono-Regular',Consolas,monospace;font-size:8px;letter-spacing:.16em;color:#6b6860;text-transform:uppercase}
h1{font-family:'Cormorant Garamond',Georgia,serif;font-size:16px;font-weight:500;letter-spacing:.055em;color:#1b1a17}
.st{font-family:'SFMono-Regular',Consolas,monospace;font-size:9px;text-align:right;color:#6b6860}
.st b{display:block;font-size:12px;color:$(if($nFail -eq 0){'#3d7a52'}else{'#9e2b25'})}
.kpis{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:5px;margin-bottom:9px}
.kpi{padding:7px 6px;background:#fff;border:1px solid #dcdad3;border-radius:4px}
.kpi .v{font-family:'SFMono-Regular',Consolas,monospace;font-size:13px;font-weight:700;color:#1b1a17;line-height:1}
.kpi .k{font-family:'SFMono-Regular',Consolas,monospace;font-size:7.5px;letter-spacing:.06em;color:#6b6860;text-transform:uppercase;margin-top:2px;display:block}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dbd9d3;border-radius:6px;font-size:inherit}
th,td{text-align:left;border-bottom:1px solid #ebe9e3;padding:4px 8px}
th{color:#6b6860;font-size:8px;text-transform:uppercase;font-family:'SFMono-Regular',Consolas,monospace;letter-spacing:.08em}
tr.grp td{background:#1b1a17;color:#f2f1ec;font-family:'Cormorant Garamond',Georgia,serif;font-size:11.5px;letter-spacing:.05em;padding:5px 8px}
tr.grp .en{font-family:'SFMono-Regular',Consolas,monospace;font-size:7.5px;letter-spacing:.12em;opacity:.65;margin-left:7px}
.num{font-family:'SFMono-Regular',Consolas,monospace;text-align:right}
.pill{display:inline-block;padding:1px 7px;border-radius:8px;font-family:'SFMono-Regular',Consolas,monospace;font-size:8px;font-weight:700}
.pill.g{background:#e6efec;color:#2c4f4a}.pill.r{background:#f3e7e6;color:#9e2b25}.pill.n{background:#efeeea;color:#6b6860}
.tbar{height:6px;border-radius:3px;background:#ebe9e3;min-width:90px;overflow:hidden}
.tbar span{display:block;height:100%;background:#3c6660;border-radius:3px}
.ft{font-family:'SFMono-Regular',Consolas,monospace;font-size:8px;color:#6b6860;border-top:1px solid #dbd9d3;padding-top:7px;margin-top:11px;text-align:center}
@media (max-width:700px){.kpis{grid-template-columns:repeat(3,minmax(0,1fr))}}
</style></head><body>
<div class="mast"><div class="lft"><span class="seal">理</span>
<div><div class="num0">Veritas Intelligence Analytics · Trio Orchestrator</div>
<h1>SUMMARY MATRIX · VDF + VRN + VAP</h1></div></div>
<div class="st"><b>$verdBig</b>$ts · $(if($Quick){"QUICK"}else{"FULL"}) · v0102</div></div>
<div class="kpis">
<div class="kpi"><span class="v">$(@($results).Count)</span><span class="k">Stages</span></div>
<div class="kpi"><span class="v" style="color:#3d7a52">$nOK</span><span class="k">OK</span></div>
<div class="kpi"><span class="v" style="color:#9e2b25">$nFail</span><span class="k">FAIL</span></div>
<div class="kpi"><span class="v">$nSkip</span><span class="k">SKIP</span></div>
<div class="kpi"><span class="v">${tot}s</span><span class="k">Elapsed</span></div>
<div class="kpi"><span class="v">3</span><span class="k">Subsystems</span></div></div>
<table><tr><th>Stage</th><th>Verdict</th><th class="num">Sec</th><th>Timing</th></tr>
$rowsHtml
</table>
<div class="ft">誠實口徑 · 不卡斷 · append-only · 存證 $([System.IO.Path]::GetFileName($ev)) · 視覺鎖 Veritas Header · 零 CDN · 非投資建議</div>
</body></html>
"@
$rep = Join-Path $evDir ("trio_matrix_{0}.html" -f $ts)
[System.IO.File]::WriteAllText($rep, $html)
Write-Host ("  報告:{0}" -f $rep)
Write-Host ("  存證:{0}" -f $ev)
if ((-not $NoOpen) -and ($env:OS -eq "Windows_NT")) { Start-Process -FilePath $rep }
exit $nFail

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
