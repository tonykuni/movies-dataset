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
<# =====================================================================
 VRN Batch AllInOne v0102 — v0101 全功能保留 + -Only 單檔補擷車道(只增不減)
 ---------------------------------------------------------------------
 動機:對帳 63/64,MQ-1560 缺擷取。引擎輸出為單一扁平表
 (VRN_MDL005_Text/VRN_MDL004_Tables),整夾重跑=覆蓋 59 檔成果,故:
   -Only <pattern>:①匹配檔複製到獨立 solo 收件夾 ②引擎只跑該夾
   ③產物「合併回主表」:主表先備份 .pre_<ts>.bak → 剔除同 pdf_name 舊列
     → 追加新列 → 重寫 parquet+csv(append-only:備份永留)
 無 -Only:完整委派 v0101(-OCR 三段)/ v0100(No-OCR)。
 用法:via-batch -OCR -Only "MQ-1560*"     → 單檔補擷+合併
===================================================================== #>
param(
    [switch]$OCR,
    [string]$Only = "",
    [switch]$Probe,
    [switch]$NoOpen,
    [int]$Throttle = 3,
    [int]$TimeoutSec = 240,
    [int]$StageTimeoutSec = 5400,
    [int]$Workers = 0,
    [switch]$Fresh
)
Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$vrn = $PSScriptRoot
$via = $vrn | Split-Path -Parent | Split-Path -Parent

# ── 無 -Only:完整委派 v0101(行為不變)──────────────────────────────
if (-not $Only) {
    $v0101 = Join-Path $vrn "Invoke-VRN-Batch-AllInOne-v0101.ps1"
    $fw = @()
    if ($OCR) { $fw += "-OCR" }; if ($Probe) { $fw += "-Probe" }; if ($NoOpen) { $fw += "-NoOpen" }; if ($Fresh) { $fw += "-Fresh" }
    & pwsh -NoProfile -File $v0101 @fw -Throttle $Throttle -TimeoutSec $TimeoutSec -StageTimeoutSec $StageTimeoutSec -Workers $Workers
    exit $LASTEXITCODE
}

# ── -Only 單檔補擷車道 ────────────────────────────────────────────────
$inbox   = Join-Path $vrn "input\incoming"
$stageRt = Join-Path $vrn "staging\ocr_out"
$ts      = Get-Date -Format "yyyyMMdd_HHmmss"
$soloIn  = Join-Path $stageRt "_solo\$ts\inbox"
$solo005 = Join-Path $stageRt "_solo\$ts\mdl005_temp"
$solo004 = Join-Path $stageRt "_solo\$ts\mdl004_temp"
$repDir  = Join-Path $via "VIA_Reports\vrn_ocr_runs"
foreach ($d in @($soloIn, $solo005, $solo004, $repDir)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

$matched = @(Get-ChildItem -LiteralPath $inbox -Filter $Only -File -ErrorAction SilentlyContinue)
Write-Host "=== VRN 單檔補擷 v0102 · -Only '$Only' → $($matched.Count) 檔 ===" -ForegroundColor Cyan
if (-not $matched.Count) { Write-Host "  [FAIL] 收件夾無匹配 — 誠實停止" -ForegroundColor Red; exit 1 }
$matched | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $soloIn; Write-Host "  [收] $($_.Name)" }

$py = @("$env:USERPROFILE\envs\via_core_312\Scripts\python.exe", "py", "python", "python3") |
      Where-Object { (($_ -match '\\') -and (Test-Path $_)) -or (($_ -notmatch '\\') -and (Get-Command $_ -ErrorAction SilentlyContinue)) } |
      Select-Object -First 1
$eng005 = Join-Path $vrn "VRN_ENG018_MDL005OCRFetchingPDFText.py"
$eng004 = Join-Path $vrn "VRN_ENG017_MDL004OCRFetchingPDFTable.py"

function Run-Solo([string]$Name, [string]$Eng, [string[]]$EngArgs) {
    $log = Join-Path $repDir "solo_$($Name)_$ts.log"
    Write-Host "  ── $Name(solo)──" -ForegroundColor Yellow
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $spArgs = @{ FilePath = $py; ArgumentList = (@("`"$Eng`"") + $EngArgs)
                 RedirectStandardOutput = $log; RedirectStandardError = "$log.err"; PassThru = $true }
    if ($IsWindows) { $spArgs.WindowStyle = "Hidden" }
    $proc = Start-Process @spArgs
    if (-not $proc.WaitForExit($StageTimeoutSec * 1000)) { try { $proc.Kill($true) } catch {}; Write-Host "  [TIMEOUT] $Name" -ForegroundColor Yellow; return $false }
    $sec = [math]::Round($sw.Elapsed.TotalSeconds, 1)
    $v = if ($proc.ExitCode -eq 0) { "OK" } else { "FAIL" }
    Write-Host "  [$v] $Name · ${sec}s (exit=$($proc.ExitCode) · log=$(Split-Path $log -Leaf))" -ForegroundColor $(if ($v -eq "OK") { "Green" } else { "Red" })
    # 缺料診斷:log 尾段拉出該檔相關訊息(誠實呈現引擎自述)
    Get-Content $log -Tail 200 -ErrorAction SilentlyContinue | Where-Object { $_ -match [regex]::Escape(($matched[0].BaseName)) } |
        Select-Object -First 6 | ForEach-Object { Write-Host "     ↳ $_" -ForegroundColor DarkGray }
    return ($v -eq "OK")
}
$ok5 = Run-Solo "MDL005" $eng005 @("--pdf-temp", "`"$soloIn`"", "--mdl005-temp", "`"$solo005`"", "--workers", "$Workers")
$ok4 = Run-Solo "MDL004" $eng004 @("--pdf-temp", "`"$soloIn`"", "--mdl004-temp", "`"$solo004`"", "--workers", "$Workers")

# ── 合併回主表(python;主表先備份;同 pdf_name 舊列剔除後追加)─────────
Write-Host "  ── 合併 solo 產物回主表 ──" -ForegroundColor Yellow
$mergePy = @'
import sys, os, json, shutil, datetime
import pandas as pd
main_dir, solo_dir, stem, ts = sys.argv[1:5]
mp, sp = os.path.join(main_dir, stem + ".parquet"), os.path.join(solo_dir, stem + ".parquet")
if not os.path.exists(sp):
    sp_csv = os.path.join(solo_dir, stem + ".csv")
    if not os.path.exists(sp_csv):
        print(json.dumps({"stem": stem, "ok": False, "note": "solo 無產物(引擎對該檔仍零輸出)"})); sys.exit(0)
    solo = pd.read_csv(sp_csv, encoding="utf-8-sig")
else:
    solo = pd.read_parquet(sp)
if not len(solo):
    print(json.dumps({"stem": stem, "ok": False, "note": "solo 產物 0 列(引擎零輸出)"})); sys.exit(0)
main = pd.read_parquet(mp) if os.path.exists(mp) else pd.DataFrame()
key = "pdf_name" if "pdf_name" in solo.columns else next((c for c in ("source_document","source_pdf","file_name") if c in solo.columns), None)
if os.path.exists(mp):
    shutil.copy2(mp, mp.replace(".parquet", f".pre_{ts}.bak.parquet"))
if len(main) and key and key in main.columns:
    names = set(solo[key].astype(str))
    before = len(main)
    main = main[~main[key].astype(str).isin(names)]
    dropped = before - len(main)
else:
    dropped = 0
merged = pd.concat([main, solo], ignore_index=True) if len(main) else solo
merged.to_parquet(mp, index=False)
merged.to_csv(mp.replace(".parquet", ".csv"), index=False, encoding="utf-8-sig")
print(json.dumps({"stem": stem, "ok": True, "solo_rows": len(solo), "dropped_old": dropped,
                  "total_rows": len(merged), "backup": os.path.basename(mp).replace(".parquet", f".pre_{ts}.bak.parquet")},
                 ensure_ascii=False))
'@
$mtmp = Join-Path $repDir "solo_merge_$ts.py"
[IO.File]::WriteAllText($mtmp, $mergePy, [Text.UTF8Encoding]::new($false))
foreach ($pair in @(
        @((Join-Path $stageRt "mdl005_temp"), $solo005, "VRN_MDL005_Text"),
        @((Join-Path $stageRt "mdl004_temp"), $solo004, "VRN_MDL004_Tables"))) {
    $r = & $py $mtmp $pair[0] $pair[1] $pair[2] $ts 2>&1 | Select-Object -Last 1
    Write-Host "  [合併] $r"
}
Write-Host "`n=== 單檔補擷完成 · 建議續跑:via-reconcile(驗 64/64)===" -ForegroundColor Cyan
exit $(if ($ok5 -and $ok4) { 0 } else { 1 })

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
