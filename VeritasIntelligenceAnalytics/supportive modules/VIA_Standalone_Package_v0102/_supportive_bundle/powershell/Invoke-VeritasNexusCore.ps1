#requires -Version 7.0
param(
    [ValidateSet(
        "ScanOnly",
        "BuildRegistry",
        "HardGate",
        "EnvPlan",
        "AccelerationPlan",
        "DownloadOnly",
        "Validate",
        "Matrix",
        "Install"
    )]
    [string]$Action = "Matrix",

    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",

    [string]$PythonExe = "",

    [switch]$OpenReport,

    [switch]$ForceInstallUnlock
)

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
$def_PARAM_README = Join-Path $def_PARAM_BASE_DIR "Read_Me_VeritasNexusCore.md"

$def_PARAM_OUT_ROOT = Join-Path $def_PARAM_BASE_DIR "_nexuscore_action_runner\RUN_$def_PARAM_RUN_STAMP"
$def_PARAM_REGISTRY_DIR = Join-Path $def_PARAM_OUT_ROOT "_supportive_registry"
$def_PARAM_HARDGATE_DIR = Join-Path $def_PARAM_OUT_ROOT "_supportive_hardgate"
$def_PARAM_ENV_DIR = Join-Path $def_PARAM_OUT_ROOT "_supportive_env"
$def_PARAM_INSTALLPLAN_DIR = Join-Path $def_PARAM_OUT_ROOT "_supportive_install_plans"
$def_PARAM_REPORT_DIR = Join-Path $def_PARAM_OUT_ROOT "_supportive_reports"
$def_PARAM_LOG_DIR = Join-Path $def_PARAM_OUT_ROOT "_logs"
$def_PARAM_CACHE_DIR = Join-Path $def_PARAM_OUT_ROOT "_supportive_cache"
$def_PARAM_WHEELHOUSE_DIR = Join-Path $def_PARAM_OUT_ROOT "_supportive_wheelhouse"
$def_PARAM_DOWNLOAD_DIR = Join-Path $def_PARAM_OUT_ROOT "_supportive_downloads"

$def_PARAM_ACTION_LOG = Join-Path $def_PARAM_LOG_DIR "NEXUSCORE_ACTION_RUNNER.log"

# =============================================================================
# def UTIL
# =============================================================================
function def_WriteLine {
    param([string]$Level, [string]$Message)

    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[$ts] [$Level] $Message"
    $color = "Gray"

    if ($Level -eq "OK") { $color = "Green" }
    elseif ($Level -eq "WARN") { $color = "Yellow" }
    elseif ($Level -eq "FAIL") { $color = "Red" }
    elseif ($Level -eq "RUN") { $color = "Cyan" }

    Write-Host $line -ForegroundColor $color

    if (Test-Path -LiteralPath $def_PARAM_LOG_DIR) {
        Add-Content -LiteralPath $def_PARAM_ACTION_LOG -Value $line -Encoding UTF8
    }
}

function def_EnsureDir {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_EnsureOutputDirs {
    foreach ($dir in @(
        $def_PARAM_OUT_ROOT,
        $def_PARAM_REGISTRY_DIR,
        $def_PARAM_HARDGATE_DIR,
        $def_PARAM_ENV_DIR,
        $def_PARAM_INSTALLPLAN_DIR,
        $def_PARAM_REPORT_DIR,
        $def_PARAM_LOG_DIR,
        $def_PARAM_CACHE_DIR,
        $def_PARAM_WHEELHOUSE_DIR,
        $def_PARAM_DOWNLOAD_DIR
    )) {
        def_EnsureDir -Path $dir
    }
}

function def_ResolvePython {
    if ($PythonExe -and (Test-Path -LiteralPath $PythonExe)) { return $PythonExe }

    $candidates = @(
        "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_core_313\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_vrn_312\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe"
    )

    foreach ($p in $candidates) {
        if (Test-Path -LiteralPath $p) { return $p }
    }

    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $cmd) { return $cmd.Source }

    return ""
}

function def_WriteHtmlTable {
    param([array]$Rows, [string]$Title, [string]$OutPath, [string]$Description = "")

    $table = $Rows | ConvertTo-Html -Fragment | Out-String

    $html = @"
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>$Title</title>
<style>
body { font-family: Arial, "Microsoft JhengHei", sans-serif; background:#f6f7fb; color:#111827; margin:24px; }
.card { background:white; border:1px solid #e5e7eb; border-radius:16px; padding:18px; margin:16px 0; box-shadow:0 2px 12px rgba(15,23,42,.06); }
table { width:100%; border-collapse:collapse; font-size:12px; }
th { background:#111827; color:white; padding:8px; text-align:left; position:sticky; top:0; }
td { border-bottom:1px solid #e5e7eb; padding:7px; vertical-align:top; }
.badge { display:inline-block; background:#eef2ff; color:#3730a3; padding:4px 9px; border-radius:999px; font-size:12px; }
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

    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($OutPath, $html, $enc)
}

function def_Action_Matrix {
    $outJson = Join-Path $def_PARAM_REPORT_DIR "NEXUSCORE_ACTION_RUNNER_MATRIX.json"
    $outHtml = Join-Path $def_PARAM_REPORT_DIR "NEXUSCORE_ACTION_RUNNER_MATRIX.html"

    $rows = @()
    foreach ($a in @("ScanOnly","BuildRegistry","HardGate","EnvPlan","AccelerationPlan","DownloadOnly","Validate","Matrix","Install")) {
        $rows += [pscustomobject]@{
            Action = $a
            Enabled = if ($a -eq "Install") { $false } else { $true }
            Status = if ($a -eq "Install") { "LOCKED" } else { "READY" }
            Risk = if ($a -eq "Install") { "MEDIUM_WHEN_UNLOCKED" } else { "LOW" }
            Rule = if ($a -eq "Install") { "Locked by default." } else { "Safe action." }
        }
    }

    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($outJson, ($rows | ConvertTo-Json -Depth 8), $enc)
    def_WriteHtmlTable -Rows $rows -Title "NexusCore Action Runner Matrix" -OutPath $outHtml -Description "Install is locked."

    return $outHtml
}

function def_Action_ScanOnly {
    $outJson = Join-Path $def_PARAM_REGISTRY_DIR "NEXUSCORE_SCANONLY_INVENTORY.json"
    $outCsv = Join-Path $def_PARAM_REGISTRY_DIR "NEXUSCORE_SCANONLY_INVENTORY.csv"
    $outHtml = Join-Path $def_PARAM_REGISTRY_DIR "NEXUSCORE_SCANONLY_INVENTORY.html"

    $files = Get-ChildItem -LiteralPath $def_PARAM_BASE_DIR -Recurse -File |
        Where-Object {
            $_.FullName -notmatch "\\_nexuscore_action_runner\\"
        } |
        Sort-Object FullName

    $rows = $files | ForEach-Object {
        [pscustomobject]@{
            FileName = $_.Name
            Path = $_.FullName
            SizeBytes = $_.Length
            ModifiedTime = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            Status = if ($_.Length -gt 0) { "FOUND" } else { "EMPTY" }
            Risk = if ($_.Length -gt 0) { "LOW" } else { "MEDIUM" }
        }
    }

    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($outJson, ($rows | ConvertTo-Json -Depth 8), $enc)
    $rows | Export-Csv -LiteralPath $outCsv -NoTypeInformation -Encoding UTF8BOM
    def_WriteHtmlTable -Rows $rows -Title "NexusCore ScanOnly Inventory" -OutPath $outHtml -Description "Read-only scan."

    return $outHtml
}

function def_Action_BuildRegistry {
    $outJson = Join-Path $def_PARAM_REGISTRY_DIR "NEXUSCORE_ACTION_REGISTRY.json"
    $outCsv = Join-Path $def_PARAM_REGISTRY_DIR "NEXUSCORE_ACTION_REGISTRY.csv"
    $outHtml = Join-Path $def_PARAM_REGISTRY_DIR "NEXUSCORE_ACTION_REGISTRY.html"

    $files = Get-ChildItem -LiteralPath $def_PARAM_BASE_DIR -Recurse -File |
        Where-Object {
            $_.FullName -notmatch "\\_nexuscore_action_runner\\"
        } |
        Sort-Object FullName

    $rows = @()
    $i = 0

    foreach ($f in $files) {
        $i++
        $ext = $f.Extension.ToLowerInvariant()
        $type = if ($ext -eq ".py") { "python" } elseif ($ext -eq ".ps1") { "powershell" } elseif ($ext -eq ".json") { "json" } elseif ($ext -eq ".csv") { "csv" } elseif ($ext -match "html|htm") { "html" } else { "other" }

        $rows += [pscustomobject]@{
            ToolID = "VIA-SUP-{0:0000}" -f $i
            ToolName = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
            FileName = $f.Name
            Path = $f.FullName
            ToolType = $type
            Status = if ($f.Length -gt 0) { "FOUND" } else { "EMPTY" }
            Risk = if ($f.Length -gt 0) { "LOW" } else { "MEDIUM" }
            EntryMode = if ($f.Name -eq "Invoke-VeritasNexusCore.ps1") { "DirectAllowed" } else { "NexusCoreManaged" }
        }
    }

    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($outJson, ($rows | ConvertTo-Json -Depth 8), $enc)
    $rows | Export-Csv -LiteralPath $outCsv -NoTypeInformation -Encoding UTF8BOM
    def_WriteHtmlTable -Rows $rows -Title "NexusCore Action Registry" -OutPath $outHtml -Description "Registry generated by Action Runner."

    return $outHtml
}

function def_Action_HardGate {
    $outJson = Join-Path $def_PARAM_HARDGATE_DIR "NEXUSCORE_HARDGATE_REPORT.json"
    $outHtml = Join-Path $def_PARAM_HARDGATE_DIR "NEXUSCORE_HARDGATE_REPORT.html"

    $py = def_ResolvePython
    $pythonExists = ($py -ne "" -and (Test-Path -LiteralPath $py))

    $rows = @()
    $rows += [pscustomobject]@{ Check="Python"; Detail=$py; Status=if($pythonExists){"PASS"}else{"FAIL"}; Risk=if($pythonExists){"LOW"}else{"HIGH"} }
    $rows += [pscustomobject]@{ Check="Aegis"; Detail=$def_PARAM_AEGIS_PY; Status=if(Test-Path -LiteralPath $def_PARAM_AEGIS_PY){"PASS"}else{"FAIL"}; Risk=if(Test-Path -LiteralPath $def_PARAM_AEGIS_PY){"LOW"}else{"HIGH"} }
    $rows += [pscustomobject]@{ Check="Celeritas"; Detail=$def_PARAM_CELERITAS_PY; Status=if(Test-Path -LiteralPath $def_PARAM_CELERITAS_PY){"PASS"}else{"FAIL"}; Risk=if(Test-Path -LiteralPath $def_PARAM_CELERITAS_PY){"LOW"}else{"HIGH"} }
    $rows += [pscustomobject]@{ Check="EnvManager"; Detail=$def_PARAM_ENVMANAGER_PY; Status=if(Test-Path -LiteralPath $def_PARAM_ENVMANAGER_PY){"PASS"}else{"FAIL"}; Risk=if(Test-Path -LiteralPath $def_PARAM_ENVMANAGER_PY){"LOW"}else{"HIGH"} }
    $rows += [pscustomobject]@{ Check="InstallLock"; Detail="Install locked by default"; Status="PASS"; Risk="LOW" }

    if ($pythonExists) {
        try {
            $pipVersion = & $py -m pip --version 2>&1
            $rows += [pscustomobject]@{ Check="pip"; Detail=($pipVersion -join " "); Status="PASS"; Risk="LOW" }
        } catch {
            $rows += [pscustomobject]@{ Check="pip"; Detail=$_.Exception.Message; Status="WARN"; Risk="MEDIUM" }
        }
    }

    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($outJson, ($rows | ConvertTo-Json -Depth 8), $enc)
    def_WriteHtmlTable -Rows $rows -Title "NexusCore HardGate Report" -OutPath $outHtml -Description "No environment modification."

    return $outHtml
}

function def_Action_EnvPlan {
    $outJson = Join-Path $def_PARAM_ENV_DIR "NEXUSCORE_ENVMANAGER_PLAN.json"
    $outHtml = Join-Path $def_PARAM_ENV_DIR "NEXUSCORE_ENVMANAGER_PLAN.html"

    $rows = @(
        [pscustomobject]@{ TargetEnv="via_core_312"; Purpose="Core Nexus / Aegis / Celeritas"; Policy="No global pollution"; Status="PLANNED"; Risk="LOW" },
        [pscustomobject]@{ TargetEnv="via_vdf_312"; Purpose="DataForge / yfinance / TWSE / FRED"; Policy="Partitioned"; Status="PLANNED"; Risk="LOW" },
        [pscustomobject]@{ TargetEnv="via_vrn_312"; Purpose="ReportNova / PDF extraction"; Policy="Partitioned"; Status="PLANNED"; Risk="LOW" },
        [pscustomobject]@{ TargetEnv="via_viz_312"; Purpose="HTML / dashboard / visualization"; Policy="Partitioned"; Status="PLANNED"; Risk="LOW" },
        [pscustomobject]@{ TargetEnv="via_ocr_312"; Purpose="OCR / CV heavy packages"; Policy="Isolated"; Status="PLANNED"; Risk="LOW" }
    )

    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($outJson, ($rows | ConvertTo-Json -Depth 8), $enc)
    def_WriteHtmlTable -Rows $rows -Title "NexusCore EnvManager Plan" -OutPath $outHtml -Description "No venv creation in this safe action."

    return $outHtml
}

function def_Action_AccelerationPlan {
    $outJson = Join-Path $def_PARAM_INSTALLPLAN_DIR "NEXUSCORE_CELERITAS_ACCELERATION_PLAN.json"
    $outHtml = Join-Path $def_PARAM_INSTALLPLAN_DIR "NEXUSCORE_CELERITAS_ACCELERATION_PLAN.html"

    $rows = @()
    $rows += [pscustomobject]@{ Item="CacheDir"; Path=$def_PARAM_CACHE_DIR; Mode="prepare"; Status="READY"; Risk="LOW" }
    $rows += [pscustomobject]@{ Item="WheelhouseDir"; Path=$def_PARAM_WHEELHOUSE_DIR; Mode="prepare"; Status="READY"; Risk="LOW" }
    $rows += [pscustomobject]@{ Item="DownloadDir"; Path=$def_PARAM_DOWNLOAD_DIR; Mode="prepare"; Status="READY"; Risk="LOW" }
    $rows += [pscustomobject]@{ Item="Celeritas"; Path=$def_PARAM_CELERITAS_PY; Mode="plan only"; Status=if(Test-Path -LiteralPath $def_PARAM_CELERITAS_PY){"FOUND"}else{"MISSING"}; Risk=if(Test-Path -LiteralPath $def_PARAM_CELERITAS_PY){"LOW"}else{"HIGH"} }
    $rows += [pscustomobject]@{ Item="Install"; Path="LOCKED"; Mode="blocked"; Status="LOCKED"; Risk="LOW" }

    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($outJson, ($rows | ConvertTo-Json -Depth 8), $enc)
    def_WriteHtmlTable -Rows $rows -Title "NexusCore Celeritas Acceleration Plan" -OutPath $outHtml -Description "Plan only. Install locked."

    return $outHtml
}

function def_Action_DownloadOnly {
    $outJson = Join-Path $def_PARAM_INSTALLPLAN_DIR "NEXUSCORE_DOWNLOADONLY_REPORT.json"
    $outHtml = Join-Path $def_PARAM_INSTALLPLAN_DIR "NEXUSCORE_DOWNLOADONLY_REPORT.html"

    foreach ($dir in @($def_PARAM_CACHE_DIR, $def_PARAM_WHEELHOUSE_DIR, $def_PARAM_DOWNLOAD_DIR)) {
        def_EnsureDir -Path $dir
    }

    $rows = @()
    $rows += [pscustomobject]@{ Item="CacheDir"; Path=$def_PARAM_CACHE_DIR; Status="READY"; Risk="LOW" }
    $rows += [pscustomobject]@{ Item="WheelhouseDir"; Path=$def_PARAM_WHEELHOUSE_DIR; Status="READY"; Risk="LOW" }
    $rows += [pscustomobject]@{ Item="DownloadDir"; Path=$def_PARAM_DOWNLOAD_DIR; Status="READY"; Risk="LOW" }
    $rows += [pscustomobject]@{ Item="NetworkDownload"; Path="SKIPPED_SAFE_MODE"; Status="SKIPPED"; Risk="LOW" }
    $rows += [pscustomobject]@{ Item="Install"; Path="LOCKED"; Status="LOCKED"; Risk="LOW" }

    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($outJson, ($rows | ConvertTo-Json -Depth 8), $enc)
    def_WriteHtmlTable -Rows $rows -Title "NexusCore DownloadOnly Report" -OutPath $outHtml -Description "No pip install."

    return $outHtml
}

function def_Action_Validate {
    $outJson = Join-Path $def_PARAM_REPORT_DIR "NEXUSCORE_VALIDATE_REPORT.json"
    $outHtml = Join-Path $def_PARAM_REPORT_DIR "NEXUSCORE_VALIDATE_REPORT.html"

    $py = def_ResolvePython
    $pythonExists = ($py -ne "" -and (Test-Path -LiteralPath $py))
    $rows = @()

    $rows += [pscustomobject]@{ Check="PythonResolved"; Detail=$py; Status=if($pythonExists){"PASS"}else{"FAIL"}; Risk=if($pythonExists){"LOW"}else{"HIGH"} }

    foreach ($p in @($def_PARAM_AEGIS_PY, $def_PARAM_CELERITAS_PY, $def_PARAM_ENVMANAGER_PY, $def_PARAM_README)) {
        $rows += [pscustomobject]@{
            Check="FileExists"
            Detail=$p
            Status=if(Test-Path -LiteralPath $p){"PASS"}else{"FAIL"}
            Risk=if(Test-Path -LiteralPath $p){"LOW"}else{"HIGH"}
        }
    }

    if ($pythonExists) {
        foreach ($moduleName in @("json","pathlib","subprocess","hashlib","ssl")) {
            try {
                $code = "import $moduleName; print('IMPORT_OK:$moduleName')"
                $result = & $py -c $code 2>&1
                $rows += [pscustomobject]@{ Check="Import:$moduleName"; Detail=($result -join " "); Status="PASS"; Risk="LOW" }
            } catch {
                $rows += [pscustomobject]@{ Check="Import:$moduleName"; Detail=$_.Exception.Message; Status="FAIL"; Risk="HIGH" }
            }
        }
    }

    $enc = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($outJson, ($rows | ConvertTo-Json -Depth 8), $enc)
    def_WriteHtmlTable -Rows $rows -Title "NexusCore Validate Report" -OutPath $outHtml -Description "Basic validation only."

    return $outHtml
}

function def_Action_Install {
    if (-not $ForceInstallUnlock) {
        throw "INSTALL_LOCKED: Install is disabled by default."
    }

    throw "INSTALL_BLOCKED_SAFE_VERSION: This runner intentionally does not install."
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VERITAS NEXUSCORE ACTION RUNNER" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    def_EnsureOutputDirs

    def_WriteLine "RUN" "Action : $Action"
    def_WriteLine "RUN" "BaseDir: $def_PARAM_BASE_DIR"
    def_WriteLine "RUN" "OutDir : $def_PARAM_OUT_ROOT"

    $reportPath = ""

    if ($Action -eq "Matrix") { $reportPath = def_Action_Matrix }
    elseif ($Action -eq "ScanOnly") { $reportPath = def_Action_ScanOnly }
    elseif ($Action -eq "BuildRegistry") { $reportPath = def_Action_BuildRegistry }
    elseif ($Action -eq "HardGate") { $reportPath = def_Action_HardGate }
    elseif ($Action -eq "EnvPlan") { $reportPath = def_Action_EnvPlan }
    elseif ($Action -eq "AccelerationPlan") { $reportPath = def_Action_AccelerationPlan }
    elseif ($Action -eq "DownloadOnly") { $reportPath = def_Action_DownloadOnly }
    elseif ($Action -eq "Validate") { $reportPath = def_Action_Validate }
    elseif ($Action -eq "Install") { $reportPath = def_Action_Install }
    else { throw "Unknown action: $Action" }

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def NEXUSCORE ACTION COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Status : NEXUSCORE_ACTION_COMPLETE"
    Write-Host "Action : $Action"
    Write-Host "Risk   : LOW"
    Write-Host "Report : $reportPath"
    Write-Host "Log    : $def_PARAM_ACTION_LOG"

    if ($OpenReport -and $reportPath -and (Test-Path -LiteralPath $reportPath)) {
        Start-Process $reportPath
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
# =============================================================================
# def NEXUSCORE_EXTERNAL_BRIDGE_SAFE_PATCH_MARKER
# =============================================================================
# External bridge created:
# C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_nexuscore_external_bridge_patch\RUN_20260610_201459\_bridge\Invoke-NexusCore-ExternalBridge.ps1
#
# Safe bridge commands:
# pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_nexuscore_external_bridge_patch\RUN_20260610_201459\_bridge\Invoke-NexusCore-ExternalBridge.ps1" -Action ProbeAll -OpenReport
# pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_nexuscore_external_bridge_patch\RUN_20260610_201459\_bridge\Invoke-NexusCore-ExternalBridge.ps1" -Action HardGateBridge -OpenReport
# pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_nexuscore_external_bridge_patch\RUN_20260610_201459\_bridge\Invoke-NexusCore-ExternalBridge.ps1" -Action EnvPlanBridge -OpenReport
# pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_nexuscore_external_bridge_patch\RUN_20260610_201459\_bridge\Invoke-NexusCore-ExternalBridge.ps1" -Action AccelerationBridge -OpenReport
# pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_nexuscore_external_bridge_patch\RUN_20260610_201459\_bridge\Invoke-NexusCore-ExternalBridge.ps1" -Action DownloadOnlyBridge -OpenReport
# Install remains LOCKED.
