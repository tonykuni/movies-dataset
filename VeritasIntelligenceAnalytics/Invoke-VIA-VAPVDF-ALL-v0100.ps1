# Invoke-VIA-VAPVDF-ALL-v0100.ps1 — 一支 PowerShell 統包 VAP & VDF 全流程(操作員令 2026-08-13)。
# 六站順跑 · 誠實逐站 OK/FAIL 不卡斷 · 動態解析最新版引擎(嚴禁寫死版號)· 末尾總結矩陣 + 存證 JSON。
# 用法:pwsh -File Invoke-VIA-VAPVDF-ALL-v0100.ps1 [-Quick] [-SkipVDF] [-SkipVAP]
#   -Quick:只跑輕站(契約盤點+繪圖探測);預設=全六站。
# 站表:V1 VDF 契約盤點 · V2 VDF 302 全系統驗證 · V3 VDF 303 Registry 活化
#       A1 VAP 引擎探測 · A2 VAP chartlib 零依賴出圖 · A3 VAP seaborn/plotly selftest
param([switch]$Quick, [switch]$SkipVDF, [switch]$SkipVAP)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSCommandPath
$VDF = Join-Path $Root "functional modules\VDF"
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
Write-Host "=== VIA VAP+VDF 統包 v0100 · python=$py · $(if($Quick){'QUICK'}else{'FULL'}) ==="
$stages = @()
if (-not $SkipVDF) {
    $stages += , @("V1 VDF 契約盤點", @((Get-Newest $VDF "VDF_ENG019_MDL501FetchContractManager.py"), "check"), $VDF)
    if (-not $Quick) {
        $stages += , @("V2 VDF 302 全系統驗證", @((Get-Newest $VDF "VDF_ENG017_MDL302FinalActivation.py"), "--no-pause"), $VDF)
        $stages += , @("V3 VDF 303 Registry 活化", @((Get-Newest $VDF "VDF_MDL303_RegistryActivation.py"), "--no-pause"), $VDF)
    }
}
if (-not $SkipVAP) {
    $stages += , @("A1 VAP 引擎探測", @((Get-Newest $VAPE "VAP_ENG003_AutoplotSeabornPlotly_v0*.py"), "probe"), $Root)
    if (-not $Quick) {
        $stages += , @("A2 VAP chartlib 出圖", @((Get-Newest $VAPE "VAP_ENG001_AutoplotEngineChartlib_v0*.py"), "--demo", "--auto", "--base", $Root), $Root)
        $stages += , @("A3 VAP selftest 全譜", @((Get-Newest $VAPE "VAP_ENG003_AutoplotSeabornPlotly_v0*.py"), "selftest"), $Root)
    }
}

$results = @()
foreach ($s in $stages) {
    $name = $s[0]; $cmd = $s[1]; $wd = $s[2]
    if (-not $cmd[0]) {
        Write-Host ("  [SKIP] {0} — 引擎不在位(誠實列缺)" -f $name)
        $results += [pscustomobject]@{ stage = $name; verdict = "SKIP"; seconds = 0; note = "engine missing" }
        continue
    }
    Write-Host ("  ── {0} ──" -f $name)
    $t0 = Get-Date
    Push-Location $wd
    & $py @cmd 2>&1 | ForEach-Object { Write-Host ("     " + $_) }
    $rc = $LASTEXITCODE
    Pop-Location
    $dt = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    $v = if ($rc -eq 0) { "OK" } else { "FAIL(rc=$rc)" }
    Write-Host ("  [{0}] {1} · {2}s" -f $v, $name, $dt)
    $results += [pscustomobject]@{ stage = $name; verdict = $v; seconds = $dt; note = "" }
}

# ── 總結矩陣 ──
Write-Host ""
Write-Host "=== 總結矩陣 · VAP+VDF ==="
$w = ($results | ForEach-Object { $_.stage.Length } | Measure-Object -Maximum).Maximum
foreach ($r in $results) {
    Write-Host ("  {0}  {1,-10} {2,6}s" -f $r.stage.PadRight($w), $r.verdict, $r.seconds)
}
$nFail = @($results | Where-Object { $_.verdict -like "FAIL*" }).Count
$nOK = @($results | Where-Object { $_.verdict -eq "OK" }).Count
Write-Host ("  合計:OK {0} · FAIL {1} · SKIP {2}(誠實口徑,不卡斷)" -f $nOK, $nFail, (@($results).Count - $nOK - $nFail))

# ── 存證 JSON ──
$evDir = Join-Path $Root "VIA_Reports\vapvdf_runs"
New-Item -ItemType Directory -Path $evDir -Force | Out-Null
$ev = Join-Path $evDir ("vapvdf_all_{0}.json" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
[pscustomobject]@{
    version = "v0100"; generated_at = (Get-Date -Format s); mode = $(if ($Quick) { "quick" } else { "full" })
    ok = $nOK; fail = $nFail; results = $results
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ev -Encoding UTF8
Write-Host ("  存證:{0}" -f $ev)
exit $nFail

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
