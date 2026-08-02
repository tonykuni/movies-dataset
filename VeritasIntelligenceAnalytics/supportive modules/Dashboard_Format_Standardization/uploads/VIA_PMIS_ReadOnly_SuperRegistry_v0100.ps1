<#
VIA PMIS-Lite Read-Only Super Registry Builder v0100
Policy: read-only target scan, no execution of target scripts, no source mutation, append-only output.
#>

# =============================================================================
# def 00 PARAMETERS
# =============================================================================

$BasePath = "C:\Users\tonyk\Downloads\PMIS-Lite (4)\pmis_lite"
$RunRootName = "_via_readonly_runs"
$RegistryBuilderPath = Join-Path $PSScriptRoot "via_pmis_registry_builder_v0100.py"
$PythonExe = "python"
$OpenHtmlReport = $true
$KeepPowerShellOpen = $true
$HashAlgorithm = "SHA256"
$MaxTextBytes = 2000000
$ProgressWidth = 28
$FileExtensionsForTextScan = @(".py", ".ps1", ".bat", ".cmd", ".html", ".htm", ".json", ".md", ".txt", ".csv", ".svg")
$ExcludedDirectoryNames = @(".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache")

# =============================================================================
# def 01 SAFETY POLICY
# =============================================================================

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function def_WriteHeader {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 88) -ForegroundColor DarkCyan
    Write-Host "def $Title" -ForegroundColor Cyan
    Write-Host ("=" * 88) -ForegroundColor DarkCyan
}

function def_WritePolicy {
    Write-Host "def Policy: READ-ONLY · NO TARGET EXECUTION · NO SOURCE MUTATION · APPEND-ONLY OUTPUT" -ForegroundColor Yellow
    Write-Host "def Base  : $BasePath" -ForegroundColor Gray
}

function def_ShowProgress {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Message
    )
    if ($Total -le 0) { $Total = 1 }
    $pct = [math]::Min(100, [math]::Max(0, [int](($Step / $Total) * 100)))
    $filled = [int](($pct / 100) * $ProgressWidth)
    $bar = ("█" * $filled) + ("░" * ($ProgressWidth - $filled))
    Write-Host ("[{0,3}%] [{1}] {2}" -f $pct, $bar, $Message) -ForegroundColor Green
}

function def_GetTimestamp {
    return (Get-Date).ToString("yyyyMMdd_HHmmss")
}

function def_EnsureDirectory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_GetRelativePath {
    param(
        [string]$FullPath,
        [string]$RootPath
    )
    $root = [System.IO.Path]::GetFullPath($RootPath).TrimEnd('\') + '\'
    $full = [System.IO.Path]::GetFullPath($FullPath)
    if ($full.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $full.Substring($root.Length)
    }
    return $full
}

function def_TestExcludedPath {
    param([System.IO.FileSystemInfo]$Item)
    $parts = $Item.FullName -split "[\\/]"
    foreach ($x in $ExcludedDirectoryNames) {
        if ($parts -contains $x) { return $true }
    }
    return $false
}

function def_GetSafeHash {
    param([string]$Path)
    try {
        return (Get-FileHash -LiteralPath $Path -Algorithm $HashAlgorithm).Hash
    } catch {
        return "HASH_FAIL: $($_.Exception.Message)"
    }
}

function def_WriteJsonUtf8 {
    param(
        [string]$Path,
        [object]$Payload
    )
    $json = $Payload | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText($Path, $json, [System.Text.UTF8Encoding]::new($false))
}

function def_WriteCsvUtf8Bom {
    param(
        [string]$Path,
        [object[]]$Rows
    )
    if (-not $Rows -or $Rows.Count -eq 0) {
        "empty" | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8BOM
        return
    }
    $Rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8BOM
}

# =============================================================================
# def 02 READ-ONLY INVENTORY
# =============================================================================

function def_NewRunDirectories {
    param([string]$Base)
    $runId = "RUN_$(def_GetTimestamp)_PMIS_LITE_READONLY_SUPER_REGISTRY_v0100"
    $runRoot = Join-Path $Base $RunRootName
    $runDir = Join-Path $runRoot $runId
    $registryDir = Join-Path $runDir "registry"
    $reportDir = Join-Path $runDir "report"
    $logDir = Join-Path $runDir "logs"
    def_EnsureDirectory $runRoot
    def_EnsureDirectory $runDir
    def_EnsureDirectory $registryDir
    def_EnsureDirectory $reportDir
    def_EnsureDirectory $logDir
    return [ordered]@{
        run_id = $runId
        run_root = $runRoot
        run_dir = $runDir
        registry_dir = $registryDir
        report_dir = $reportDir
        log_dir = $logDir
    }
}

function def_GetInventoryRows {
    param([string]$Base)
    $items = Get-ChildItem -LiteralPath $Base -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { -not (def_TestExcludedPath $_) }
    $rows = New-Object System.Collections.Generic.List[object]
    $i = 0
    $total = [Math]::Max(1, $items.Count)
    foreach ($item in $items) {
        $i++
        if (($i % 50) -eq 0 -or $i -eq 1 -or $i -eq $total) {
            def_ShowProgress -Step $i -Total $total -Message "Inventory static scan: $i / $total"
        }
        $isDir = $item.PSIsContainer
        $ext = ""
        $size = 0
        $sha = ""
        if (-not $isDir) {
            $ext = [System.IO.Path]::GetExtension($item.FullName).ToLowerInvariant()
            $size = $item.Length
            $sha = def_GetSafeHash -Path $item.FullName
        }
        $rows.Add([pscustomobject][ordered]@{
            full_path = $item.FullName
            relative_path = def_GetRelativePath -FullPath $item.FullName -RootPath $Base
            name = $item.Name
            extension = $ext
            is_directory = [bool]$isDir
            size_bytes = [Int64]$size
            created_time = $item.CreationTime.ToString("yyyy-MM-dd HH:mm:ss")
            modified_time = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            sha256 = $sha
            scan_policy = "READ_ONLY_STATIC_SCAN_NO_EXECUTION"
        })
    }
    return $rows.ToArray()
}

function def_GetAnchorPreviewRows {
    param(
        [object[]]$InventoryRows,
        [string]$Base
    )
    $anchorTerms = @(
        "SAP", "T-Code", "MM01", "CS01", "C223", "MRP", "Production Version", "Routing",
        "PLM", "EBOM", "MBOM", "ECO", "ECN", "Revision", "Lifecycle",
        "MS Project", "WBS", "Task", "Milestone", "Critical Path", "Baseline",
        "PMBOK", "Scope", "Schedule", "Cost", "Risk", "Stakeholder", "Change Control",
        "BOM", "SUPER BOM", "MPN", "IPN", "CPN", "AML", "AVL", "RefDes",
        "SSOT", "DuckDB", "Parquet", "Auto Coding", "Process Mining", "Data Mining"
    )
    $rows = New-Object System.Collections.Generic.List[object]
    $files = $InventoryRows | Where-Object { -not $_.is_directory -and ($FileExtensionsForTextScan -contains $_.extension) }
    $i = 0
    $total = [Math]::Max(1, $files.Count)
    foreach ($file in $files) {
        $i++
        if (($i % 25) -eq 0 -or $i -eq 1 -or $i -eq $total) {
            def_ShowProgress -Step $i -Total $total -Message "Keyword anchor preview: $i / $total"
        }
        try {
            $bytes = [System.IO.File]::ReadAllBytes($file.full_path)
            if ($bytes.Length -gt $MaxTextBytes) {
                $bytes = $bytes[0..($MaxTextBytes - 1)]
            }
            $text = [System.Text.Encoding]::UTF8.GetString($bytes)
            $found = @()
            foreach ($term in $anchorTerms) {
                if ($text.IndexOf($term, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
                    $found += $term
                }
            }
            if ($found.Count -gt 0) {
                $rows.Add([pscustomobject][ordered]@{
                    relative_path = $file.relative_path
                    name = $file.name
                    extension = $file.extension
                    matched_terms = ($found | Select-Object -Unique) -join " | "
                    matched_count = ($found | Select-Object -Unique).Count
                    registry_hint = "Python builder will expand into SAP/PLM/MSP/PMBOK/BOM/SSOT matrices"
                })
            }
        } catch {
            $rows.Add([pscustomobject][ordered]@{
                relative_path = $file.relative_path
                name = $file.name
                extension = $file.extension
                matched_terms = "READ_FAIL"
                matched_count = 0
                registry_hint = $_.Exception.Message
            })
        }
    }
    return $rows.ToArray()
}

# =============================================================================
# def 03 PYTHON REGISTRY BUILDER CALL
# =============================================================================

function def_InvokePythonRegistryBuilder {
    param(
        [string]$Base,
        [string]$RunDir,
        [string]$InventoryJson
    )
    if (-not (Test-Path -LiteralPath $RegistryBuilderPath)) {
        Write-Host "[WARN] Python registry builder not found: $RegistryBuilderPath" -ForegroundColor Yellow
        Write-Host "[WARN] Skipping deep AST/doc/UI registry build. Inventory files were still generated." -ForegroundColor Yellow
        return 10
    }
    Write-Host "def Python Registry Builder: $RegistryBuilderPath" -ForegroundColor Gray
    $args = @(
        $RegistryBuilderPath,
        "--base", $Base,
        "--run-dir", $RunDir,
        "--inventory-json", $InventoryJson,
        "--max-text-bytes", $MaxTextBytes
    )
    & $PythonExe @args
    return $LASTEXITCODE
}

# =============================================================================
# def 04 MAIN
# =============================================================================

function def_InvokeMain {
    def_WriteHeader "VIA PMIS-Lite · READ-ONLY SUPER REGISTRY BUILDER · v0100"
    def_WritePolicy

    if (-not (Test-Path -LiteralPath $BasePath)) {
        throw "BasePath not found: $BasePath"
    }

    def_ShowProgress -Step 1 -Total 7 -Message "Create append-only run directories"
    $dirs = def_NewRunDirectories -Base $BasePath
    $runDir = [string]$dirs.run_dir
    $registryDir = [string]$dirs.registry_dir
    $reportDir = [string]$dirs.report_dir

    def_ShowProgress -Step 2 -Total 7 -Message "Build read-only file inventory with SHA256"
    $inventoryRows = def_GetInventoryRows -Base $BasePath
    $inventoryCsv = Join-Path $registryDir "PMIS_Lite_File_Inventory.csv"
    $inventoryJson = Join-Path $registryDir "PMIS_Lite_File_Inventory.json"
    def_WriteCsvUtf8Bom -Path $inventoryCsv -Rows $inventoryRows
    def_WriteJsonUtf8 -Path $inventoryJson -Payload @{ files = $inventoryRows }

    def_ShowProgress -Step 3 -Total 7 -Message "Build first-pass anchor preview"
    $anchorPreviewRows = def_GetAnchorPreviewRows -InventoryRows $inventoryRows -Base $BasePath
    $anchorPreviewCsv = Join-Path $registryDir "PMIS_Lite_Anchor_Preview.csv"
    def_WriteCsvUtf8Bom -Path $anchorPreviewCsv -Rows $anchorPreviewRows

    def_ShowProgress -Step 4 -Total 7 -Message "Write run manifest"
    $manifest = [ordered]@{
        run_id = $dirs.run_id
        generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        base_path = $BasePath
        run_dir = $runDir
        policy = "READ_ONLY_STATIC_SCAN_NO_TARGET_EXECUTION_NO_SOURCE_MUTATION"
        file_count = ($inventoryRows | Where-Object { -not $_.is_directory }).Count
        directory_count = ($inventoryRows | Where-Object { $_.is_directory }).Count
        anchor_preview_count = $anchorPreviewRows.Count
        registry_builder_path = $RegistryBuilderPath
        python_exe = $PythonExe
    }
    $manifestJson = Join-Path $registryDir "PMIS_Lite_Run_Manifest.json"
    def_WriteJsonUtf8 -Path $manifestJson -Payload $manifest

    def_ShowProgress -Step 5 -Total 7 -Message "Invoke Python deep registry builder in read-only mode"
    $pyExit = def_InvokePythonRegistryBuilder -Base $BasePath -RunDir $runDir -InventoryJson $inventoryJson

    def_ShowProgress -Step 6 -Total 7 -Message "Resolve HTML report path"
    $htmlReport = Join-Path $reportDir "PMIS_Lite_SuperSSOT_ReadOnly_Report.html"
    if (-not (Test-Path -LiteralPath $htmlReport)) {
        $fallbackHtml = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA PMIS-Lite Read-Only Report</title></head>
<body style="font-family:Segoe UI,Noto Sans TC,Arial;padding:24px;background:#F9F9F6;color:#1F2933">
<h1>def VIA PMIS-Lite Read-Only Inventory Report</h1>
<p>Python deep registry builder did not generate report. Inventory and anchor preview were generated successfully.</p>
<ul><li>File Inventory: $inventoryCsv</li><li>Anchor Preview: $anchorPreviewCsv</li><li>Manifest: $manifestJson</li><li>Python Exit: $pyExit</li></ul>
</body></html>
"@
        [System.IO.File]::WriteAllText($htmlReport, $fallbackHtml, [System.Text.UTF8Encoding]::new($false))
    }

    def_ShowProgress -Step 7 -Total 7 -Message "Done"
    def_WriteHeader "READ-ONLY OUTPUTS"
    Write-Host "def Run Dir        : $runDir" -ForegroundColor Cyan
    Write-Host "def Inventory CSV  : $inventoryCsv" -ForegroundColor Cyan
    Write-Host "def Inventory JSON : $inventoryJson" -ForegroundColor Cyan
    Write-Host "def Anchor Preview : $anchorPreviewCsv" -ForegroundColor Cyan
    Write-Host "def HTML Report    : $htmlReport" -ForegroundColor Cyan
    Write-Host "def Python Exit    : $pyExit" -ForegroundColor Gray
    Write-Host ""
    Write-Host "def Status: READ_ONLY_SUPER_REGISTRY_COMPLETE" -ForegroundColor Green

    if ($OpenHtmlReport -and (Test-Path -LiteralPath $htmlReport)) {
        Start-Process $htmlReport
    }
}

# =============================================================================
# def 99 OUTER SAFE CATCH
# =============================================================================

try {
    def_InvokeMain
} catch {
    def_WriteHeader "OUTER SAFE CATCH"
    Write-Host "def FATAL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
} finally {
    if ($KeepPowerShellOpen) {
        Write-Host ""
        Write-Host "def PowerShell remains open. No exit. No destructive action was executed." -ForegroundColor Yellow
        Read-Host "Press Enter to return to prompt"
    }
}
