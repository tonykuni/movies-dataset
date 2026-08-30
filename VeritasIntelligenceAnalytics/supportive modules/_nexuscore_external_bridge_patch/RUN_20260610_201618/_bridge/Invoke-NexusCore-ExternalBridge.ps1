#requires -Version 7.0
param(
    [ValidateSet(
        "ProbeAll",
        "ProbeAegis",
        "ProbeEnvManager",
        "ProbeCeleritas",
        "HardGateBridge",
        "EnvPlanBridge",
        "AccelerationBridge",
        "DownloadOnlyBridge",
        "ValidateBridge",
        "Install"
    )]
    [string]$Action = "ProbeAll",

    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",

    [string]$PythonExe = "",

    [switch]$OpenReport,

    [switch]$ForceInstallUnlock
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

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# def PARAMS
# =============================================================================
$def_PARAM_BASE_DIR = $BaseDir
$def_PARAM_RUN_STAMP = Get-Date -Format "yyyyMMdd_HHmmss"

$def_PARAM_AEGIS_PY = Join-Path $def_PARAM_BASE_DIR "50_Protection_Acceleration\VeritasAegisNexus.py"
$def_PARAM_CELERITAS_PY = Join-Path $def_PARAM_BASE_DIR "50_Protection_Acceleration\VeritasCeleritas.py"
$def_PARAM_ENVMANAGER_PY = Join-Path $def_PARAM_BASE_DIR "40_Environment_Health\VIA_EnvManager.py"

$def_PARAM_OUT_ROOT = Join-Path $def_PARAM_BASE_DIR "_nexuscore_external_bridge\RUN_$def_PARAM_RUN_STAMP"
$def_PARAM_REPORT_DIR = Join-Path $def_PARAM_OUT_ROOT "_reports"
$def_PARAM_LOG_DIR = Join-Path $def_PARAM_OUT_ROOT "_logs"

$def_PARAM_REPORT_JSON = Join-Path $def_PARAM_REPORT_DIR "NEXUSCORE_EXTERNAL_BRIDGE_REPORT.json"
$def_PARAM_REPORT_CSV = Join-Path $def_PARAM_REPORT_DIR "NEXUSCORE_EXTERNAL_BRIDGE_REPORT.csv"
$def_PARAM_REPORT_HTML = Join-Path $def_PARAM_REPORT_DIR "NEXUSCORE_EXTERNAL_BRIDGE_REPORT.html"
$def_PARAM_LOG = Join-Path $def_PARAM_LOG_DIR "NEXUSCORE_EXTERNAL_BRIDGE.log"

$def_PARAM_TIMEOUT_SECONDS = 25

# =============================================================================
# def UTIL
# =============================================================================
function def_WriteLine {
    param(
        [string]$Level,
        [string]$Message
    )

    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[$ts] [$Level] $Message"
    $color = "Gray"

    if ($Level -eq "OK") { $color = "Green" }
    elseif ($Level -eq "WARN") { $color = "Yellow" }
    elseif ($Level -eq "FAIL") { $color = "Red" }
    elseif ($Level -eq "RUN") { $color = "Cyan" }
    elseif ($Level -eq "SKIP") { $color = "DarkYellow" }

    Write-Host $line -ForegroundColor $color

    if (Test-Path -LiteralPath $def_PARAM_LOG_DIR) {
        Add-Content -LiteralPath $def_PARAM_LOG -Value $line -Encoding UTF8
    }
}

function def_EnsureDir {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_EnsureOutputDirs {
    foreach ($dir in @(
        $def_PARAM_OUT_ROOT,
        $def_PARAM_REPORT_DIR,
        $def_PARAM_LOG_DIR
    )) {
        def_EnsureDir -Path $dir
    }
}

function def_ResolvePython {
    if ($PythonExe -and (Test-Path -LiteralPath $PythonExe)) {
        return $PythonExe
    }

    $candidates = @(
        "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_core_313\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_vrn_312\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe"
    )

    foreach ($p in $candidates) {
        if (Test-Path -LiteralPath $p) {
            return $p
        }
    }

    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        return $cmd.Source
    }

    return ""
}

function def_InvokeProcessWithTimeout {
    param(
        [string]$FileName,
        [string[]]$Arguments,
        [int]$TimeoutSeconds
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FileName

    foreach ($arg in $Arguments) {
        [void]$psi.ArgumentList.Add($arg)
    }

    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi

    [void]$p.Start()

    $completed = $p.WaitForExit($TimeoutSeconds * 1000)

    if (-not $completed) {
        try {
            $p.Kill()
        } catch {}

        return [pscustomobject]@{
            ExitCode = 124
            StdOut = ""
            StdErr = "TIMEOUT_AFTER_${TimeoutSeconds}s"
            Status = "TIMEOUT"
        }
    }

    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()

    return [pscustomobject]@{
        ExitCode = $p.ExitCode
        StdOut = $stdout
        StdErr = $stderr
        Status = if ($p.ExitCode -eq 0) { "PASS" } else { "REVIEW" }
    }
}

function def_WriteHtmlTable {
    param(
        [array]$Rows,
        [string]$Title,
        [string]$OutPath,
        [string]$Description = ""
    )

    $table = $Rows | ConvertTo-Html -Fragment

    $html = @"
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>$Title</title>
<style>
body { font-family: Arial, "Microsoft JhengHei", sans-serif; background:#f6f7fb; color:#111827; margin:24px; }
.card { background:#fff; border:1px solid #e5e7eb; border-radius:16px; padding:18px; margin:16px 0; box-shadow:0 2px 12px rgba(15,23,42,.06); }
table { width:100%; border-collapse:collapse; font-size:12px; }
th { background:#111827; color:white; padding:8px; text-align:left; position:sticky; top:0; }
td { border-bottom:1px solid #e5e7eb; padding:7px; vertical-align:top; }
.badge { display:inline-block; background:#eef2ff; color:#3730a3; padding:4px 9px; border-radius:999px; font-size:12px; }
pre { white-space:pre-wrap; background:#f3f4f6; padding:12px; border-radius:12px; }
</style>
</head>
<body>
<h1>$Title</h1>
<p class="badge">Generated: $def_PARAM_RUN_STAMP</p>
<div class="card">
<p>$Description</p>
$table
</div>
</body>
</html>
"@

    $html | Set-Content -LiteralPath $OutPath -Encoding UTF8
}

function def_GetPythonAstSummary {
    param(
        [string]$PythonExe,
        [string]$ScriptPath
    )

    $code = @"
import ast, json, pathlib
p = pathlib.Path(r'''$ScriptPath''')
text = p.read_text(encoding='utf-8', errors='replace')
tree = ast.parse(text)
funcs = []
classes = []
imports = []
hits = []
safe_keywords = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        funcs.append(node.name)
    elif isinstance(node, ast.ClassDef):
        classes.append(node.name)
    elif isinstance(node, ast.Import):
        for a in node.names:
            imports.append(a.name)
    elif isinstance(node, ast.ImportFrom):
        imports.append(node.module or '')
for key in ['argparse','click','typer','fire','sys.argv','ArgumentParser']:
    if key in text:
        hits.append(key)
for key in ['dry','dry_run','dry-run','plan','scan','probe','validate','check','report','download','install','force']:
    if key in text.lower():
        safe_keywords.append(key)
print(json.dumps({
    'functions': funcs[:120],
    'classes': classes[:60],
    'imports': sorted(list(set(imports)))[:120],
    'argparse_hits': hits,
    'safe_keywords': sorted(list(set(safe_keywords))),
    'function_count': len(funcs),
    'class_count': len(classes),
    'import_count': len(set(imports))
}, ensure_ascii=False))
"@

    $proc = def_InvokeProcessWithTimeout -FileName $PythonExe -Arguments @("-c", $code) -TimeoutSeconds 25

    if ($proc.ExitCode -ne 0) {
        return [pscustomobject]@{
            Status = "FAIL"
            FunctionCount = 0
            ClassCount = 0
            ImportCount = 0
            ArgparseHits = ""
            SafeKeywords = ""
            FunctionsTop = ""
            ClassesTop = ""
            Detail = $proc.StdErr
        }
    }

    try {
        $obj = $proc.StdOut | ConvertFrom-Json
        return [pscustomobject]@{
            Status = "PASS"
            FunctionCount = $obj.function_count
            ClassCount = $obj.class_count
            ImportCount = $obj.import_count
            ArgparseHits = (($obj.argparse_hits | Select-Object -First 20) -join ", ")
            SafeKeywords = (($obj.safe_keywords | Select-Object -First 30) -join ", ")
            FunctionsTop = (($obj.functions | Select-Object -First 30) -join ", ")
            ClassesTop = (($obj.classes | Select-Object -First 30) -join ", ")
            Detail = "AST parsed"
        }
    } catch {
        return [pscustomobject]@{
            Status = "REVIEW"
            FunctionCount = 0
            ClassCount = 0
            ImportCount = 0
            ArgparseHits = ""
            SafeKeywords = ""
            FunctionsTop = ""
            ClassesTop = ""
            Detail = $_.Exception.Message
        }
    }
}

function def_ProbeHelp {
    param(
        [string]$PythonExe,
        [string]$ScriptPath
    )

    foreach ($helpArg in @("--help", "-h")) {
        $proc = def_InvokeProcessWithTimeout -FileName $PythonExe -Arguments @($ScriptPath, $helpArg) -TimeoutSeconds $def_PARAM_TIMEOUT_SECONDS
        $combined = (($proc.StdOut + "`n" + $proc.StdErr).Trim())

        if ($combined.Length -gt 0) {
            return [pscustomobject]@{
                Status = if ($proc.ExitCode -eq 0) { "PASS" } else { "REVIEW" }
                ExitCode = $proc.ExitCode
                HelpArg = $helpArg
                HelpPreview = $combined.Substring(0, [Math]::Min(2000, $combined.Length))
            }
        }
    }

    return [pscustomobject]@{
        Status = "NO_HELP_OUTPUT"
        ExitCode = 0
        HelpArg = ""
        HelpPreview = ""
    }
}

function def_ProbeTool {
    param(
        [string]$ToolName,
        [string]$ToolPath,
        [string]$TargetAction,
        [string]$AllowedMode,
        [string]$BlockedMode
    )

    $python = def_ResolvePython

    if (-not $python) {
        throw "Python not found."
    }

    $exists = Test-Path -LiteralPath $ToolPath
    $size = 0
    $modified = ""

    if ($exists) {
        $item = Get-Item -LiteralPath $ToolPath
        $size = $item.Length
        $modified = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    }

    $ast = if ($exists) {
        def_GetPythonAstSummary -PythonExe $python -ScriptPath $ToolPath
    } else {
        [pscustomobject]@{
            Status = "MISSING"
            FunctionCount = 0
            ClassCount = 0
            ImportCount = 0
            ArgparseHits = ""
            SafeKeywords = ""
            FunctionsTop = ""
            ClassesTop = ""
            Detail = "missing"
        }
    }

    $help = if ($exists) {
        def_ProbeHelp -PythonExe $python -ScriptPath $ToolPath
    } else {
        [pscustomobject]@{
            Status = "MISSING"
            ExitCode = 999
            HelpArg = ""
            HelpPreview = ""
        }
    }

    $status = if ($exists -and $ast.Status -eq "PASS") {
        "READY"
    } elseif ($exists) {
        "REVIEW"
    } else {
        "MISSING"
    }

    $risk = if ($status -eq "READY") {
        "LOW"
    } elseif ($status -eq "REVIEW") {
        "MEDIUM"
    } else {
        "HIGH"
    }

    return [pscustomobject]@{
        ToolName = $ToolName
        ToolPath = $ToolPath
        TargetAction = $TargetAction
        AllowedMode = $AllowedMode
        BlockedMode = $BlockedMode
        Exists = $exists
        SizeBytes = $size
        ModifiedTime = $modified
        AstStatus = $ast.Status
        FunctionCount = $ast.FunctionCount
        ClassCount = $ast.ClassCount
        ImportCount = $ast.ImportCount
        ArgparseHits = $ast.ArgparseHits
        SafeKeywords = $ast.SafeKeywords
        FunctionsTop = $ast.FunctionsTop
        ClassesTop = $ast.ClassesTop
        HelpStatus = $help.Status
        HelpExitCode = $help.ExitCode
        HelpArg = $help.HelpArg
        HelpPreview = $help.HelpPreview
        Status = $status
        Risk = $risk
    }
}

function def_RunProbeAll {
    $rows = @()

    $rows += def_ProbeTool `
        -ToolName "VeritasAegisNexus" `
        -ToolPath $def_PARAM_AEGIS_PY `
        -TargetAction "HardGateBridge" `
        -AllowedMode "check/scan/probe/report only" `
        -BlockedMode "environment modification"

    $rows += def_ProbeTool `
        -ToolName "VIA_EnvManager" `
        -ToolPath $def_PARAM_ENVMANAGER_PY `
        -TargetAction "EnvPlanBridge" `
        -AllowedMode "plan/report only" `
        -BlockedMode "global environment mutation"

    $rows += def_ProbeTool `
        -ToolName "VeritasCeleritas" `
        -ToolPath $def_PARAM_CELERITAS_PY `
        -TargetAction "AccelerationBridge/DownloadOnlyBridge" `
        -AllowedMode "plan/cache/wheelhouse/download-only" `
        -BlockedMode "install without Aegis LOW"

    return @($rows)
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def NEXUSCORE EXTERNAL BRIDGE SAFE RUNNER" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    def_EnsureOutputDirs

    def_WriteLine "RUN" "Action : $Action"
    def_WriteLine "RUN" "BaseDir: $def_PARAM_BASE_DIR"
    def_WriteLine "RUN" "OutDir : $def_PARAM_OUT_ROOT"
    def_WriteLine "RUN" "Install: LOCKED"

    if ($Action -eq "Install") {
        if (-not $ForceInstallUnlock) {
            throw "INSTALL_LOCKED: External bridge does not install."
        }
        throw "INSTALL_BLOCKED_SAFE_VERSION: This bridge intentionally does not install."
    }

    $rows = @()

    if ($Action -eq "ProbeAll") {
        $rows = def_RunProbeAll
    } elseif ($Action -eq "ProbeAegis" -or $Action -eq "HardGateBridge") {
        $rows += def_ProbeTool -ToolName "VeritasAegisNexus" -ToolPath $def_PARAM_AEGIS_PY -TargetAction "HardGateBridge" -AllowedMode "check/scan/probe/report only" -BlockedMode "environment modification"
    } elseif ($Action -eq "ProbeEnvManager" -or $Action -eq "EnvPlanBridge") {
        $rows += def_ProbeTool -ToolName "VIA_EnvManager" -ToolPath $def_PARAM_ENVMANAGER_PY -TargetAction "EnvPlanBridge" -AllowedMode "plan/report only" -BlockedMode "global environment mutation"
    } elseif ($Action -eq "ProbeCeleritas" -or $Action -eq "AccelerationBridge" -or $Action -eq "DownloadOnlyBridge") {
        $rows += def_ProbeTool -ToolName "VeritasCeleritas" -ToolPath $def_PARAM_CELERITAS_PY -TargetAction "AccelerationBridge/DownloadOnlyBridge" -AllowedMode "plan/cache/wheelhouse/download-only" -BlockedMode "install without Aegis LOW"
    } elseif ($Action -eq "ValidateBridge") {
        $rows = def_RunProbeAll
    } else {
        throw "Unknown bridge action: $Action"
    }

    $rows | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $def_PARAM_REPORT_JSON -Encoding UTF8
    $rows | Export-Csv -LiteralPath $def_PARAM_REPORT_CSV -NoTypeInformation -Encoding UTF8BOM
    def_WriteHtmlTable -Rows $rows -Title "NexusCore External Bridge Report" -OutPath $def_PARAM_REPORT_HTML -Description "Safe external bridge probe. No install."

    $failCount = @($rows | Where-Object { $_.Risk -eq "HIGH" }).Count
    $warnCount = @($rows | Where-Object { $_.Risk -eq "MEDIUM" }).Count
    $okCount = @($rows | Where-Object { $_.Risk -eq "LOW" }).Count

    $risk = if ($failCount -gt 0) {
        "HIGH"
    } elseif ($warnCount -gt 0) {
        "MEDIUM"
    } else {
        "LOW"
    }

    $status = if ($risk -eq "LOW") {
        "NEXUSCORE_EXTERNAL_BRIDGE_READY"
    } else {
        "NEXUSCORE_EXTERNAL_BRIDGE_REVIEW_REQUIRED"
    }

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def EXTERNAL BRIDGE COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Status  : $status"
    Write-Host "Risk    : $risk"
    Write-Host "OK      : $okCount"
    Write-Host "WARN    : $warnCount"
    Write-Host "FAIL    : $failCount"
    Write-Host "Install : LOCKED"
    Write-Host "HTML    : $def_PARAM_REPORT_HTML"
    Write-Host "JSON    : $def_PARAM_REPORT_JSON"
    Write-Host "CSV     : $def_PARAM_REPORT_CSV"
    Write-Host "Log     : $def_PARAM_LOG"

    if ($OpenReport -and (Test-Path -LiteralPath $def_PARAM_REPORT_HTML)) {
        Start-Process $def_PARAM_REPORT_HTML
    }
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell session remains open." -ForegroundColor Cyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
