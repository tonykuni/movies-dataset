#requires -Version 7.0
param(
    [ValidateSet('none','aegis','celer','supportive','full')]
    [string]$Integrate = 'none',

    [ValidateSet('safe','balanced','maxsafe','aggressive')]
    [string]$Accel = 'maxsafe',

    [string]$InDir       = 'C:\VeritasIntelligenceAnalytics\VeritasReportNova\input',
    [string]$OutDir      = 'C:\VeritasIntelligenceAnalytics\VeritasReportNova\output',
    [string]$DbPath      = 'C:\VeritasIntelligenceAnalytics\VeritasReportNova\database\vrn_integrated.db',
    [string]$PdfTemp     = 'C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\pdf_temp',
    [int]   $Workers     = 0,
    [int]   $Batch       = 24,
    [int]   $Dpi         = 300,

    [string]$PythonExe   = 'C:\Users\tonyk\envs\via_core_312\Scripts\python.exe',
    [string]$ModuleFile  = 'C:\Users\tonyk\OneDrive\Desktop\新增資料夾 (4)\VRN\VRN_MDL001_StockReportPipeline.py',

    [string]$SupportiveDir = 'C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module',

    [switch]$Selftest,
    [switch]$Probe,
    [switch]$NoCache,
    [switch]$NoGov,
    [switch]$NoHtml,
    [switch]$OpenHtml
)

# ╔══════════════════════════════════════════════════════════════════════════════════════╗
# ║  VRN_PIPELINE_LAUNCHER.ps1                                                            ║
# ║  VRN MDL001 統一啟動器 · PS7 + VIA Visual Lock · paste-and-run                        ║
# ║  v1.0.0  · 2026-05                                                                     ║
# ╠══════════════════════════════════════════════════════════════════════════════════════╣
# ║  使用範例:                                                                             ║
# ║    .\VRN_PIPELINE_LAUNCHER.ps1                          # 預設: standalone           ║
# ║    .\VRN_PIPELINE_LAUNCHER.ps1 -Selftest               # 4-phase debug               ║
# ║    .\VRN_PIPELINE_LAUNCHER.ps1 -Probe                  # 健康偵測                     ║
# ║    .\VRN_PIPELINE_LAUNCHER.ps1 -Integrate supportive  # 載入 Tier 1 工具             ║
# ║    .\VRN_PIPELINE_LAUNCHER.ps1 -Integrate full        # 載入全部 9 支                ║
# ║    .\VRN_PIPELINE_LAUNCHER.ps1 -Accel aggressive      # 最大加速                     ║
# ║    .\VRN_PIPELINE_LAUNCHER.ps1 -OpenHtml              # 完成後自動開 HTML            ║
# ╚══════════════════════════════════════════════════════════════════════════════════════╝

$ErrorActionPreference = 'Continue'
$script:t0 = [datetime]::Now

# ── VIA Visual Lock (CLI 終端配色) ────────────────────────────────────────────
$script:CL = @{
    Bg     = 'Black'        ; Fg    = 'White'
    OK     = 'Green'        ; Err   = 'Red'
    Warn   = 'Yellow'       ; Info  = 'Cyan'
    Accent = 'DarkCyan'     ; Dim   = 'DarkGray'
}

function Write-Banner {
    param([string]$Title, [string]$Sub = '')
    $line = '═' * 76
    Write-Host ''
    Write-Host $line -ForegroundColor $script:CL.Accent
    Write-Host ("  {0}" -f $Title) -ForegroundColor $script:CL.Info
    if ($Sub) { Write-Host ("  {0}" -f $Sub) -ForegroundColor $script:CL.Dim }
    Write-Host $line -ForegroundColor $script:CL.Accent
}

function Write-Phase {
    param([string]$Code, [string]$Msg, [string]$Status = 'INFO')
    $color = switch ($Status) {
        'OK'   { $script:CL.OK }
        'ERR'  { $script:CL.Err }
        'WARN' { $script:CL.Warn }
        default{ $script:CL.Fg }
    }
    $mark = switch ($Status) {
        'OK'   { '✅' }
        'ERR'  { '❌' }
        'WARN' { '⚠️ ' }
        default{ '·' }
    }
    Write-Host ("  {0} [{1}] {2}" -f $mark, $Code, $Msg) -ForegroundColor $color
}

# ── Phase 0: 環境檢查 ─────────────────────────────────────────────────────────
Write-Banner 'VRN MDL001 PIPELINE LAUNCHER  v1.0.0' 'PS7 · VIA Visual Lock · paste-and-run'

$script:state = @{
    Phase  = @()
    Errors = @()
    Warns  = @()
}

function Add-State {
    param([string]$Code, [string]$Msg, [string]$Status)
    $script:state.Phase += [pscustomobject]@{
        Code   = $Code
        Msg    = $Msg
        Status = $Status
        Time   = ([datetime]::Now - $script:t0).TotalSeconds
    }
    Write-Phase -Code $Code -Msg $Msg -Status $Status
    if ($Status -eq 'ERR')  { $script:state.Errors += "$Code`: $Msg" }
    if ($Status -eq 'WARN') { $script:state.Warns  += "$Code`: $Msg" }
}

# Python 可用性
if (-not (Test-Path $PythonExe)) {
    Add-State 'P0-PY' "Python 不存在: $PythonExe" 'ERR'
    Write-Host ''
    Write-Host '  ✗ 致命錯誤: 找不到 Python 直譯器' -ForegroundColor $script:CL.Err
    exit 1
}
Add-State 'P0-PY' "Python: $PythonExe" 'OK'

# Module 檔案
if (-not (Test-Path $ModuleFile)) {
    Add-State 'P0-MOD' "找不到 MDL001: $ModuleFile" 'ERR'
    exit 1
}
Add-State 'P0-MOD' "MDL001: $(Split-Path $ModuleFile -Leaf)" 'OK'

# 路徑準備
foreach ($d in @($InDir, $OutDir, $PdfTemp, (Split-Path $DbPath -Parent))) {
    if (-not (Test-Path $d)) {
        try {
            New-Item -ItemType Directory -Path $d -Force | Out-Null
            Add-State 'P0-DIR' "建立: $d" 'OK'
        } catch {
            Add-State 'P0-DIR' "建立失敗: $d  $_" 'WARN'
        }
    }
}

# ── Phase 1: Supportive 模組偵測 (find-only, no load) ────────────────────────
Write-Banner 'Phase 1 · Supportive 模組健康偵測' '只用 find_spec 不會觸發 import'

$script:supModules = @(
    @{ Name='VIA_SSOT_Unified';                    Tier=1 ; Type='py' }
    @{ Name='VIA_RegistryCore_v1';                 Tier=1 ; Type='py' }
    @{ Name='VIS_InstallHealthRegistry';           Tier=1 ; Type='py' }
    @{ Name='VIA_EnvManager';                      Tier=1 ; Type='py' }
    @{ Name='VIA_Runtime_Bridge_All_in_One';       Tier=2 ; Type='py' }
    @{ Name='VIA_Supportive_Runtime_HardGate_Bridge'; Tier=2 ; Type='py' }
    @{ Name='VeritasCeleritas';                    Tier=2 ; Type='py' }
    @{ Name='VeritasAegisNexus';                   Tier=2 ; Type='py' }
    @{ Name='VIA_Panorama_AST_RuntimeInjector';    Tier=3 ; Type='py' }
)
$script:supPS = @(
    'Invoke-VIA-FinishProject-SafeFast.ps1'
    'Invoke-VIA-PanoramaHardGateSafeFix.ps1'
    'Invoke-VIA-SupportiveHardGate.ps1'
    'VIA_Supportive_HardGate_Seal.ps1'
    'VIA_Supportive_HardGate_Seal.json'
)

$presentPy = 0; $absentPy = 0
foreach ($m in $script:supModules) {
    $f = Join-Path $SupportiveDir "$($m.Name).py"
    if (Test-Path $f) {
        $presentPy++
        Write-Host ("    ✅ T{0} {1}" -f $m.Tier, $m.Name) -ForegroundColor $script:CL.OK
    } else {
        $absentPy++
        Write-Host ("    ⬜ T{0} {1}" -f $m.Tier, $m.Name) -ForegroundColor $script:CL.Dim
    }
}

Write-Host ''
$presentPS = 0
foreach ($p in $script:supPS) {
    $f = Join-Path $SupportiveDir $p
    if (Test-Path $f) {
        $presentPS++
        Write-Host ("    ✅ PS  {0}" -f $p) -ForegroundColor $script:CL.OK
    } else {
        Write-Host ("    ⬜ PS  {0}" -f $p) -ForegroundColor $script:CL.Dim
    }
}

Add-State 'P1-PROBE' "Python: $presentPy/$($script:supModules.Count) | PS: $presentPS/$($script:supPS.Count)" 'OK'

# ── Phase 2: Probe 模式快速退出 ──────────────────────────────────────────────
if ($Probe) {
    Write-Banner 'PROBE 完成' "Python module: $presentPy present / $absentPy absent"
    & $PythonExe $ModuleFile --probe
    exit 0
}

# ── Phase 3: Self-test 模式 ──────────────────────────────────────────────────
if ($Selftest) {
    Write-Banner 'Phase 3 · Self-Test (4-phase debug chain)' '不觸發任何外部模組'
    & $PythonExe $ModuleFile --selftest
    $rc = $LASTEXITCODE
    if ($rc -eq 0) {
        Add-State 'P3-ST' 'READY (0 fail)' 'OK'
    } elseif ($rc -eq 1) {
        Add-State 'P3-ST' 'NEAR-READY' 'WARN'
    } else {
        Add-State 'P3-ST' 'NOT-READY' 'ERR'
    }
    Write-Banner '完成' "elapsed: $([math]::Round(([datetime]::Now - $script:t0).TotalSeconds, 2))s"
    exit $rc
}

# ── Phase 4: 主流水線執行 ────────────────────────────────────────────────────
Write-Banner 'Phase 4 · 主流水線執行' "Integrate=$Integrate  Accel=$Accel  Workers=$Workers"

$pyArgs = @(
    $ModuleFile
    '--in_dir';    $InDir
    '--pdf_temp';  $PdfTemp
    '--out_dir';   $OutDir
    '--db';        $DbPath
    '--workers';   $Workers
    '--batch';     $Batch
    '--dpi';       $Dpi
    '--accel';     $Accel
    '--integrate'; $Integrate
)
if ($NoCache) { $pyArgs += '--no_cache' }
if ($NoGov)   { $pyArgs += '--no_gov' }

# 環境變數設定 (備援整合管道)
$env:VRN_INTEGRATE      = $Integrate
$env:VIA_ACCEL_MODE     = $Accel
$env:PYTHONIOENCODING   = 'utf-8'
$env:PYTHONUTF8         = '1'

Write-Host ''
Write-Host "  → 執行: $PythonExe $ModuleFile ..." -ForegroundColor $script:CL.Dim
Write-Host ''

try {
    & $PythonExe @pyArgs
    $rc = $LASTEXITCODE
    if ($rc -eq 0) {
        Add-State 'P4-RUN' "Pipeline 完成 (rc=0)" 'OK'
    } else {
        Add-State 'P4-RUN' "Pipeline 退出 rc=$rc" 'WARN'
    }
} catch {
    Add-State 'P4-RUN' "執行例外: $_" 'ERR'
    $rc = 99
}

# ── Phase 5: 輸出檢查 ────────────────────────────────────────────────────────
Write-Banner 'Phase 5 · 輸出檢查'

$outputs = @(
    @{ Name='JSON';    Path=(Join-Path $OutDir 'VRN_Integrated_Reports.json') }
    @{ Name='CSV';     Path=(Join-Path $OutDir 'VRN_Summary.csv') }
    @{ Name='HTML';    Path=(Join-Path $OutDir 'VRN_Report.html') }
    @{ Name='Parquet'; Path=(Join-Path $OutDir 'VRN_Financial.parquet') }
    @{ Name='SQLite';  Path=$DbPath }
)
foreach ($o in $outputs) {
    if (Test-Path $o.Path) {
        $sz = [math]::Round((Get-Item $o.Path).Length / 1KB, 1)
        Add-State "P5-$($o.Name)" "$($o.Path)  ($sz KB)" 'OK'
    } else {
        Add-State "P5-$($o.Name)" "$($o.Path) (missing)" 'WARN'
    }
}

# ── Phase 6: HTML 自動開啟 (LL#12 不阻塞) ────────────────────────────────────
$htmlPath = Join-Path $OutDir 'VRN_Report.html'
if ($OpenHtml -and (Test-Path $htmlPath)) {
    Add-State 'P6-HTML' "Start-Process $htmlPath" 'OK'
    Start-Process $htmlPath
}

# ── Phase 7: 總結報告 ────────────────────────────────────────────────────────
$elapsed = [math]::Round(([datetime]::Now - $script:t0).TotalSeconds, 2)
$nOK   = ($script:state.Phase | Where-Object Status -eq 'OK').Count
$nWarn = ($script:state.Phase | Where-Object Status -eq 'WARN').Count
$nErr  = ($script:state.Phase | Where-Object Status -eq 'ERR').Count
$total = $script:state.Phase.Count

Write-Banner '總結' "OK=$nOK  WARN=$nWarn  ERR=$nErr  total=$total  elapsed=${elapsed}s"

$readyState = if ($nErr -eq 0)         { 'READY'    ; $script:CL.OK }
              elseif ($nErr -le 2)     { 'NEAR-READY' ; $script:CL.Warn }
              else                     { 'NOT-READY'; $script:CL.Err }

Write-Host ''
Write-Host ("  狀態: {0}" -f $readyState[0]) -ForegroundColor $readyState[1]
Write-Host ''

# 寫出 JSON 啟動報告
$reportPath = Join-Path $OutDir 'VRN_Launcher_Report.json'
try {
    $report = @{
        version    = '1.0.0'
        timestamp  = [datetime]::Now.ToString('yyyy-MM-ddTHH:mm:ss')
        integrate  = $Integrate
        accel      = $Accel
        elapsed    = $elapsed
        ready      = $readyState[0]
        ok         = $nOK
        warn       = $nWarn
        err        = $nErr
        phases     = $script:state.Phase
        errors     = $script:state.Errors
        warns      = $script:state.Warns
    }
    $report | ConvertTo-Json -Depth 6 | Out-File -FilePath $reportPath -Encoding utf8
    Write-Host ("  Launcher report: {0}" -f $reportPath) -ForegroundColor $script:CL.Dim
} catch {
    Write-Host "  ⚠️  寫出 launcher report 失敗: $_" -ForegroundColor $script:CL.Warn
}

exit $rc
