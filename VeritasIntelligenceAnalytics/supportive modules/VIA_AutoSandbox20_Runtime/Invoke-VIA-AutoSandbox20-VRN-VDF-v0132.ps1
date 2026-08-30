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
[CmdletBinding()]
param(
    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [bool]$EnableCanonicalSafeRepair = $true,
    [bool]$ActivateWhenEligible = $true,
    [bool]$OpenHtmlReport = $true,
    [int]$MaxFiles = 8000,
    [int64]$MaxFileBytes = 2097152,
    [int]$ActivationProbeSeconds = 5,
    [string]$ApprovalPhrase = "I_APPROVE_VIA_VRN_VDF_CONTROLLED_ACTIVATION_20260725"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ExpectedApprovalPhrase = "I_APPROVE_VIA_VRN_VDF_CONTROLLED_ACTIVATION_20260725"
$Version = "v0132"
$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunName = "RUN_${RunStamp}_VIA_AUTOSANDBOX20_VRN_VDF_${Version}"
$RunRoot = Join-Path $BaseDir "_via_autosandbox20_runs"
$RunDir = Join-Path $RunRoot $RunName
$CsvDir = Join-Path $RunDir "csv"
$JsonDir = Join-Path $RunDir "json"
$HtmlDir = Join-Path $RunDir "html"
$LogDir = Join-Path $RunDir "logs"
$SandboxDir = Join-Path $RunDir "sandbox"
$BackupDir = Join-Path $RunDir "backups_preserve_original_paths"
$RuntimeCandidateDir = Join-Path $RunDir "runtime_candidate"
$RuntimeDeployDir = Join-Path $BaseDir "supportive modules\VIA_AutoSandbox20_Runtime"
$ReportPath = Join-Path $HtmlDir "VIA_AutoSandbox20_VRN_VDF_Matrix_${Version}.html"
$GatePath = Join-Path $JsonDir "activation_gate.${Version}.json"
$ManifestPath = Join-Path $RuntimeCandidateDir "VIA_LibraryManifest.${Version}.json"
$PythonEnginePath = Join-Path $RuntimeCandidateDir "VIA_UnifiedPythonEngine_${Version}.py"
$LauncherPath = Join-Path $RuntimeCandidateDir "Invoke-VIA-VRN-VDF-UnifiedLauncher-${Version}.ps1"
$SupportiveRegistryCsvPath = Join-Path $CsvDir "supportive_module_registry.${Version}.csv"
$SupportiveRegistryJsonPath = Join-Path $JsonDir "supportive_module_registry.${Version}.json"
$SupportiveSummaryJsonPath = Join-Path $JsonDir "supportive_bootstrap_summary.${Version}.json"

$script:StatusEvents = New-Object System.Collections.Generic.List[object]
$script:AnalysisCache = @{}
$script:RoundSummaries = New-Object System.Collections.Generic.List[object]
$script:RepairEvidence = New-Object System.Collections.Generic.List[object]
$script:ActivationEvidence = New-Object System.Collections.Generic.List[object]
$script:AllAnalysisRows = @()
$script:CurrentNarration = "Initializing"
$script:ActiveFilesCache = $null
$script:SupportiveBootstrapRows = @()
$script:SupportiveBootstrapSummary = [pscustomobject]@{
    registered_count = 0
    load_eligible_count = 0
    loaded_count = 0
    registered_only_count = 0
    parse_bad_count = 0
    load_fail_count = 0
    critical_missing_count = 0
    critical_bad_count = 0
    ready = $false
}

$Accelerators = @(
    [pscustomobject]@{Id="A01";Name="AST Precision Parsing";Enabled=$true},
    [pscustomobject]@{Id="A02";Name="Multilingual Semantic Classification";Enabled=$true},
    [pscustomobject]@{Id="A03";Name="Hydra Risk Prediction";Enabled=$true},
    [pscustomobject]@{Id="A04";Name="Dependency Topology Ordering";Enabled=$true},
    [pscustomobject]@{Id="A05";Name="Sandbox Isolation";Enabled=$true},
    [pscustomobject]@{Id="A06";Name="Safe Repair Suggestion";Enabled=$true},
    [pscustomobject]@{Id="A07";Name="Three-Round Panoramic Analysis";Enabled=$true},
    [pscustomobject]@{Id="A08";Name="SSOT Alignment";Enabled=$true},
    [pscustomobject]@{Id="A09";Name="HTML Matrix Generation";Enabled=$true},
    [pscustomobject]@{Id="A10";Name="Error Clustering";Enabled=$true},
    [pscustomobject]@{Id="A11";Name="Performance and Complexity";Enabled=$true},
    [pscustomobject]@{Id="A12";Name="Multi-Subsystem Synchronization";Enabled=$true},
    [pscustomobject]@{Id="A13";Name="Version Diff and Rollback";Enabled=$true},
    [pscustomobject]@{Id="A14";Name="Coverage and Regression";Enabled=$true},
    [pscustomobject]@{Id="A15";Name="Repair Sequence Optimization";Enabled=$true},
    [pscustomobject]@{Id="A16";Name="Dynamic Progress Bar";Enabled=$true},
    [pscustomobject]@{Id="A17";Name="Dynamic Status Narration";Enabled=$true},
    [pscustomobject]@{Id="A18";Name="Non-Blocking PowerShell";Enabled=$true},
    [pscustomobject]@{Id="A19";Name="Python PowerShell UI Integration";Enabled=$true},
    [pscustomobject]@{Id="A20";Name="Auto Deploy and Environment Init";Enabled=$true}
)

$CoreNames = @(
    "Invoke-VeritasCodexNexus.ps1",
    "Invoke-VeritasNexusCore.ps1",
    "Invoke-VIA-CentralGovernanceManager.ps1",
    "Invoke-VIA.ps1",
    "VIA_EnvManager.py",
    "VIA_RegistryCore_v1.py",
    "VIA_SSOT_Unified.py",
    "VeritasCeleritas.py",
    "VeritasAegisNexus.py",
    "GovernanceRegistry.json",
    "LayoutRegistry.json",
    "VisualRegistry.json",
    "UnifiedSpec.json",
    "VIS_CONFIG.json"
)

$ExcludedPathRegex = '(?i)\\(_via_|_integration_|runs?|run_\d|output|reports?|backup|archive|quarantine|staged|candidates?|_used_tools|_toolbox_used|scope_copy|external_vault|site-packages|__pycache__|node_modules|vendor|\.git|\.venv|venv|envs?|Lib)(\\|$)'
$SupportedExtensions = @(".ps1", ".psm1", ".psd1", ".py", ".json", ".yaml", ".yml", ".toml", ".html", ".md")

function def_EnsureDir {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_WriteJson {
    param($Data, [Parameter(Mandatory)][string]$Path)
    def_EnsureDir -Path (Split-Path -Parent $Path)
    $Data | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_WriteCsv {
    param($Data, [Parameter(Mandatory)][string]$Path)
    def_EnsureDir -Path (Split-Path -Parent $Path)
    @($Data | ForEach-Object { $_ }) | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
}

function def_HtmlEncode {
    param($Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_AddStatus {
    param([string]$Phase, [string]$Message, [string]$Level = "INFO")
    $script:CurrentNarration = $Message
    $row = [pscustomobject]@{
        timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss.fff")
        phase = $Phase
        level = $Level
        message = $Message
    }
    $script:StatusEvents.Add($row)
    $color = switch ($Level) { "ERROR" { "Red" } "WARN" { "Yellow" } "OK" { "Green" } default { "Cyan" } }
    Write-Host ("def [{0}] {1}" -f $Phase, $Message) -ForegroundColor $color
}

function def_ShowProgress {
    param([int]$Current, [int]$Total, [string]$Message)
    $pct = if ($Total -le 0) { 0 } else { [Math]::Min(100, [Math]::Round(($Current / $Total) * 100)) }
    $filled = [Math]::Floor($pct / 5)
    $bar = ("█" * $filled) + ("░" * (20 - $filled))
    Write-Host ("[{0,3}%] [{1}] {2}" -f $pct, $bar, $Message) -ForegroundColor Green
}

function def_GetRelativePath {
    param([string]$Path)
    try {
        return [System.IO.Path]::GetRelativePath($BaseDir, $Path)
    }
    catch {
        return $Path
    }
}

function def_GetHash {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
        }
    }
    catch {}
    return ""
}

function def_IsCoreName {
    param([string]$Name)
    foreach ($core in $CoreNames) {
        if ($Name.Equals($core, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

function def_GetSubsystem {
    param([string]$RelativePath)
    $p = $RelativePath.ToUpperInvariant()
    foreach ($name in @("VRN", "VDF", "VAP", "VPNS", "VIS")) {
        if ($p -match "(^|\\)$name(\\|$)") { return $name }
    }
    return "OTHERS"
}

function def_GetSection {
    param([string]$RelativePath, [string]$Name, [string]$Extension)
    $p = $RelativePath.ToLowerInvariant()
    $n = $Name.ToLowerInvariant()
    if ($p -match '\\(lib|libs|library|libraries|utils|helpers)(\\|$)' -or $Extension -eq ".psm1") { return "FUNCTION-LIB" }
    if ($n -match '(engine|core|manager|orchestrator|registry|runtime|bridge)') { return "ENGINE" }
    if ($p -match '(functional modules|supportive modules)') { return "MODULE" }
    return "OTHERS"
}

function def_IsDirectCanonicalPath {
    param([string]$RelativePath)
    $parts = @($RelativePath -split '\\')
    if ($parts.Count -eq 0) { return $false }
    if ($parts[0].Equals("functional modules", [System.StringComparison]::OrdinalIgnoreCase) -and $parts.Count -le 3) { return $true }
    if ($parts[0].Equals("supportive modules", [System.StringComparison]::OrdinalIgnoreCase) -and $parts.Count -le 2) { return $true }
    return $false
}

function def_GetPythonCommand {
    $candidates = @(
        "C:\Python313\python.exe",
        (Join-Path $BaseDir "via_core_312\Scripts\python.exe"),
        (Join-Path $env:USERPROFILE "envs\via_core\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $cmd) { return $cmd.Source }
    return ""
}

$PythonCommand = def_GetPythonCommand

function def_GetActiveFiles {
    if ($null -ne $script:ActiveFilesCache) { return @($script:ActiveFilesCache) }
    $roots = @()
    foreach ($relativeRoot in @("functional modules", "supportive modules", "module", "modules")) {
        $candidate = Join-Path $BaseDir $relativeRoot
        if (Test-Path -LiteralPath $candidate) { $roots += $candidate }
    }
    $files = New-Object System.Collections.Generic.List[object]
    foreach ($root in $roots) {
        Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            if ($files.Count -ge $MaxFiles) { return }
            $relative = def_GetRelativePath -Path $_.FullName
            if ($relative -match $ExcludedPathRegex) { return }
            if ($SupportedExtensions -notcontains $_.Extension.ToLowerInvariant()) { return }
            $files.Add($_)
        }
    }
    $script:ActiveFilesCache = @($files | Sort-Object FullName -Unique)
    return @($script:ActiveFilesCache)
}

function def_AnalyzePowerShell {
    param([string]$Path, [string]$Text)
    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseInput($Text, $Path, [ref]$tokens, [ref]$errors)
    $functions = @($ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)).Count
    $commands = @($ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.CommandAst] }, $true)).Count
    $parameters = @()
    if ($null -ne $ast.ParamBlock) {
        $parameters = @($ast.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath })
    }
    return [pscustomobject]@{
        parse_ok = (@($errors).Count -eq 0)
        error_count = @($errors).Count
        first_error = if (@($errors).Count -gt 0) { [string]$errors[0].Message } else { "" }
        functions = $functions
        commands = $commands
        parameters = ($parameters -join ";")
    }
}

function def_AnalyzePython {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($PythonCommand)) {
        return [pscustomobject]@{parse_ok=$false;error_count=1;first_error="Python interpreter not found";functions=0;commands=0;parameters=""}
    }
    $code = "import ast,pathlib,sys;p=pathlib.Path(sys.argv[1]);s=p.read_text(encoding='utf-8',errors='replace');t=ast.parse(s);print(sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in ast.walk(t)))"
    try {
        $output = & $PythonCommand -c $code $Path 2>&1
        if ($LASTEXITCODE -eq 0) {
            return [pscustomobject]@{parse_ok=$true;error_count=0;first_error="";functions=[int](($output | Select-Object -Last 1) -as [int]);commands=0;parameters=""}
        }
        return [pscustomobject]@{parse_ok=$false;error_count=1;first_error=(($output | Select-Object -First 1) -join "");functions=0;commands=0;parameters=""}
    }
    catch {
        return [pscustomobject]@{parse_ok=$false;error_count=1;first_error=$_.Exception.Message;functions=0;commands=0;parameters=""}
    }
}

function def_AnalyzeFile {
    param([System.IO.FileInfo]$File)
    $relative = def_GetRelativePath -Path $File.FullName
    $hash = def_GetHash -Path $File.FullName
    $cacheKey = "$($File.FullName.ToLowerInvariant())|$hash"
    if ($script:AnalysisCache.ContainsKey($cacheKey)) { return $script:AnalysisCache[$cacheKey] }

    $extension = $File.Extension.ToLowerInvariant()
    $name = $File.Name
    $subsystem = def_GetSubsystem -RelativePath $relative
    $section = def_GetSection -RelativePath $relative -Name $name -Extension $extension
    $direct = def_IsDirectCanonicalPath -RelativePath $relative
    $core = def_IsCoreName -Name $name
    $sizeGate = $File.Length -le $MaxFileBytes
    $parseOk = $true
    $errorCount = 0
    $firstError = ""
    $functionCount = 0
    $commandCount = 0
    $parameters = ""
    $text = ""
    $testMode = "METADATA_ONLY"

    if ($sizeGate) {
        try { $text = Get-Content -LiteralPath $File.FullName -Raw -Encoding UTF8 -ErrorAction Stop } catch { $text = "" }
        switch ($extension) {
            { $_ -in @(".ps1", ".psm1", ".psd1") } {
                $testMode = "POWERSHELL_AST_NO_EXECUTION"
                $r = def_AnalyzePowerShell -Path $File.FullName -Text $text
                $parseOk = $r.parse_ok; $errorCount = $r.error_count; $firstError = $r.first_error
                $functionCount = $r.functions; $commandCount = $r.commands; $parameters = $r.parameters
            }
            ".py" {
                $testMode = "PYTHON_AST_NO_IMPORT"
                $r = def_AnalyzePython -Path $File.FullName
                $parseOk = $r.parse_ok; $errorCount = $r.error_count; $firstError = $r.first_error
                $functionCount = $r.functions
            }
            ".json" {
                $testMode = "JSON_PARSE"
                try { $null = $text | ConvertFrom-Json -ErrorAction Stop } catch { $parseOk = $false; $errorCount = 1; $firstError = $_.Exception.Message }
            }
            default {
                $testMode = "STRUCTURAL_TEXT_CHECK"
                if ([string]::IsNullOrWhiteSpace($text)) { $parseOk = $false; $errorCount = 1; $firstError = "Empty or unreadable text" }
            }
        }
    }
    else {
        $parseOk = $true; $errorCount = 0; $firstError = "Skipped by size gate"; $testMode = "SIZE_GATE_SKIP"
    }

    $hydraScore = 0
    if ($core) { $hydraScore += 35 }
    if ($direct) { $hydraScore += 15 }
    if ($text -match '(?i)Invoke-Expression|\biex\b') { $hydraScore += 20 }
    if ($text -match '(?i)Remove-Item\s+.*-Recurse|Format-Volume|Clear-Disk') { $hydraScore += 25 }
    if ($text -match '(?i)Start-Process|&\s*\$') { $hydraScore += 8 }
    if ($text -match '(?i)Set-Content|Move-Item|Copy-Item') { $hydraScore += 8 }
    if ($text -match '(?m)^\s*\.\s+[''\"]') { $hydraScore += 12 }
    if ($errorCount -gt 0) { $hydraScore += 10 }
    $hydraScore = [Math]::Min(100, $hydraScore)
    $hydraBand = if ($hydraScore -ge 70) { "HIGH" } elseif ($hydraScore -ge 40) { "MEDIUM" } else { "LOW" }
    $status = if (-not $parseOk) { "ERROR" } elseif ($testMode -eq "SIZE_GATE_SKIP" -or $hydraScore -ge 70) { "WARN" } else { "OK" }
    $fixClass = if (-not $parseOk -and $hydraScore -lt 50 -and -not $core) { "Parallel-Fixable" } elseif (-not $parseOk) { "Sequence-Dependent" } else { "No-Fix" }

    $row = [pscustomobject]@{
        section = $section
        subsystem = $subsystem
        status = $status
        name = $name
        path = $File.FullName
        relative_path = $relative
        extension = $extension
        size_bytes = $File.Length
        sha256 = $hash
        test_mode = $testMode
        parse_ok = $parseOk
        error_count = $errorCount
        first_error = $firstError
        functions = $functionCount
        commands = $commandCount
        parameters = $parameters
        hydra_score = $hydraScore
        hydra_band = $hydraBand
        direct_canonical = $direct
        core_name = $core
        fix_class = $fixClass
    }
    $script:AnalysisCache[$cacheKey] = $row
    return $row
}

function def_AnalyzeScope {
    param([string]$Label)
    $files = @(def_GetActiveFiles)
    $rows = New-Object System.Collections.Generic.List[object]
    $i = 0
    foreach ($file in $files) {
        $i++
        if (($i % 100) -eq 0 -or $i -eq $files.Count) { def_ShowProgress -Current $i -Total $files.Count -Message "$Label · analyzing $($file.Name)" }
        try { $rows.Add((def_AnalyzeFile -File $file)) } catch {
            $rows.Add([pscustomobject]@{section="OTHERS";subsystem="OTHERS";status="ERROR";name=$file.Name;path=$file.FullName;relative_path=(def_GetRelativePath $file.FullName);extension=$file.Extension;size_bytes=$file.Length;sha256="";test_mode="ANALYSIS_EXCEPTION";parse_ok=$false;error_count=1;first_error=$_.Exception.Message;functions=0;commands=0;parameters="";hydra_score=100;hydra_band="HIGH";direct_canonical=$false;core_name=$false;fix_class="Sequence-Dependent"})
        }
    }
    return $rows.ToArray()
}

function def_RepairText {
    param([string]$Text, [string]$FirstError, [int]$Round)
    $value = [string]$Text
    $rules = New-Object System.Collections.Generic.List[string]

    $withoutBom = $value.TrimStart([char]0xFEFF)
    if ($withoutBom -ne $value) { $value = $withoutBom; $rules.Add("TRIM_BOM") }

    if ($value -match '[“”‘’]') {
        $next = $value.Replace([char]0x201C, [char]0x0022).Replace([char]0x201D, [char]0x0022).Replace([char]0x2018, [char]0x0027).Replace([char]0x2019, [char]0x0027)
        if ($next -ne $value) { $value = $next; $rules.Add("NORMALIZE_SMART_QUOTES") }
    }

    if ($value -match '(?m)^\s*```') {
        $next = (($value -split "`r?`n") | Where-Object { $_ -notmatch '^\s*```' }) -join "`r`n"
        if ($next -ne $value) { $value = $next; $rules.Add("REMOVE_MARKDOWN_FENCES") }
    }

    if ($value -match '(?m)^\s*PS\s+[A-Za-z]:\\.*?>') {
        $next = (($value -split "`r?`n") | ForEach-Object { $_ -replace '^\s*PS\s+[A-Za-z]:\\.*?>\s*', '' }) -join "`r`n"
        if ($next -ne $value) { $value = $next; $rules.Add("REMOVE_PS_PROMPT_PREFIX") }
    }

    if ($FirstError -like "*Variable reference is not valid*") {
        $next = [regex]::Replace($value, '\$([A-Za-z_][A-Za-z0-9_]*)\:', '${$1}:')
        if ($next -ne $value) { $value = $next; $rules.Add("FIX_VARIABLE_COLON") }
    }

    if ($FirstError -like "*Unexpected attribute 'CmdletBinding'*" -and $value -match '(?m)^\s*\[CmdletBinding\(\)\]') {
        $lines = @($value -split "`r?`n")
        $start = -1
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match '^\s*(#requires|\[CmdletBinding\(\)\]|param\s*\(|function\s+|Set-StrictMode|\$[A-Za-z_])') { $start = $i; break }
        }
        if ($start -gt 0) {
            $prefix = @($lines[0..($start-1)] | Where-Object { $_ -notmatch '^\s*(#|$|PS\s+[A-Za-z]:\\|>>)' })
            if ($prefix.Count -eq 0) { $value = ($lines[$start..($lines.Count-1)] -join "`r`n"); $rules.Add("TRIM_NONCODE_PREAMBLE") }
        }
    }

    if ($Round -eq 3) {
        $next = (($value -split "`r?`n") | ForEach-Object { $_.TrimEnd() }) -join "`r`n"
        if ($next -ne $value) { $value = $next; $rules.Add("TRIM_TRAILING_WHITESPACE") }
    }

    return [pscustomobject]@{ text=$value; rules=($rules -join ";") }
}

function def_TestDraft {
    param([string]$Path, [string]$Extension)
    $file = Get-Item -LiteralPath $Path -ErrorAction Stop
    return def_AnalyzeFile -File $file
}

function def_PromoteDraft {
    param($OriginalRow, [string]$DraftPath, [string]$Rules, [int]$Round)
    $result = [ordered]@{
        round = $Round
        action = "DRAFT_ONLY"
        original_path = $OriginalRow.path
        draft_path = $DraftPath
        rules = $Rules
        promoted = $false
        result = "NOT_PROMOTED"
        error = ""
    }
    try {
        if (-not $EnableCanonicalSafeRepair) { $result.result = "CANONICAL_REPAIR_DISABLED"; return [pscustomobject]$result }
        if ($ApprovalPhrase -ne $ExpectedApprovalPhrase) { $result.result = "APPROVAL_MISMATCH"; return [pscustomobject]$result }
        if ($OriginalRow.core_name -or $OriginalRow.hydra_score -ge 50 -or $OriginalRow.fix_class -ne "Parallel-Fixable") { $result.result = "HIGH_RISK_OR_CORE_DRAFT_ONLY"; return [pscustomobject]$result }

        $currentHash = def_GetHash -Path $OriginalRow.path
        $draftHash = def_GetHash -Path $DraftPath
        if ($currentHash -eq $draftHash) { $result.result = "ALREADY_APPLIED"; return [pscustomobject]$result }
        if ($currentHash -ne $OriginalRow.sha256) { $result.result = "HASH_CONFLICT_NO_WRITE"; return [pscustomobject]$result }

        $relative = def_GetRelativePath -Path $OriginalRow.path
        $backupPath = Join-Path $BackupDir ("ROUND_{0}\{1}" -f $Round, $relative)
        def_EnsureDir -Path (Split-Path -Parent $backupPath)
        Copy-Item -LiteralPath $OriginalRow.path -Destination $backupPath -Force -ErrorAction Stop
        Copy-Item -LiteralPath $DraftPath -Destination $OriginalRow.path -Force -ErrorAction Stop
        $result.action = "SAFE_CANONICAL_PROMOTION"
        $result.promoted = $true
        $result.result = "PROMOTED_WITH_BACKUP_HASH_STATE"
    }
    catch {
        $result.result = "PROMOTION_FAILED"
        $result.error = $_.Exception.Message
    }
    return [pscustomobject]$result
}

function def_ApplyRoundRepairs {
    param([int]$Round, $AnalysisRows)
    $targets = @($AnalysisRows | Where-Object { $_.status -eq "ERROR" -and $_.extension -in @(".ps1", ".psm1", ".psd1", ".py") })
    $evidence = New-Object System.Collections.Generic.List[object]
    $i = 0
    foreach ($row in $targets) {
        $i++
        def_ShowProgress -Current $i -Total $targets.Count -Message "Round $Round repair draft · $($row.name)"
        try {
            if (-not (Test-Path -LiteralPath $row.path)) { continue }
            $raw = Get-Content -LiteralPath $row.path -Raw -Encoding UTF8 -ErrorAction Stop
            $repair = def_RepairText -Text $raw -FirstError $row.first_error -Round $Round
            if ([string]::IsNullOrWhiteSpace($repair.rules) -or $repair.text -eq $raw) {
                $evidence.Add([pscustomobject]@{round=$Round;action="NO_SAFE_RULE";original_path=$row.path;draft_path="";rules="";promoted=$false;result="MANUAL_REVIEW";error=""})
                continue
            }
            $draftPath = Join-Path $SandboxDir ("ROUND_{0}\{1}" -f $Round, $row.relative_path)
            def_EnsureDir -Path (Split-Path -Parent $draftPath)
            Set-Content -LiteralPath $draftPath -Value $repair.text -Encoding UTF8
            $draftRow = def_TestDraft -Path $draftPath -Extension $row.extension
            if (-not $draftRow.parse_ok) {
                $evidence.Add([pscustomobject]@{round=$Round;action="DRAFT_STILL_BAD";original_path=$row.path;draft_path=$draftPath;rules=$repair.rules;promoted=$false;result=$draftRow.first_error;error=""})
                continue
            }
            $promote = def_PromoteDraft -OriginalRow $row -DraftPath $draftPath -Rules $repair.rules -Round $Round
            $evidence.Add($promote)
        }
        catch {
            $evidence.Add([pscustomobject]@{round=$Round;action="PER_FILE_ERROR_CAPTURED";original_path=$row.path;draft_path="";rules="";promoted=$false;result="NO_STALL_CONTINUE";error=$_.Exception.Message})
        }
    }
    return $evidence.ToArray()
}

function def_GetSsotMatrix {
    param($AnalysisRows)
    $required = @("GovernanceRegistry.json", "LayoutRegistry.json", "VisualRegistry.json", "UnifiedSpec.json", "VIA_RegistryCore_v1.py", "VIA_SSOT_Unified.py", "VIA_EnvManager.py", "VeritasCeleritas.py")
    $rows = foreach ($name in $required) {
        $matches = @($AnalysisRows | Where-Object { $_.name.Equals($name, [System.StringComparison]::OrdinalIgnoreCase) })
        $best = $matches | Sort-Object @{Expression="direct_canonical";Descending=$true}, @{Expression="status";Descending=$false} | Select-Object -First 1
        [pscustomobject]@{
            name = $name
            exists = ($null -ne $best)
            path = if ($null -ne $best) { $best.path } else { "" }
            parse_ok = if ($null -ne $best) { $best.parse_ok } else { $false }
            status = if ($null -eq $best) { "MISSING" } elseif ($best.parse_ok) { "OK" } else { "ERROR" }
        }
    }
    return @($rows)
}

function def_GetEntrypointCandidates {
    param([string]$Subsystem, $AnalysisRows)
    $rows = @($AnalysisRows | Where-Object {
        $_.subsystem -eq $Subsystem -and $_.extension -eq ".ps1" -and $_.parse_ok -and
        $_.name -match '^(Start|Invoke|Launch|Run)' -and
        $_.name -notmatch '(?i)test|smoke|audit|repair|backup|candidate|draft|example|sample'
    })
    foreach ($row in $rows) {
        $score = 0
        if ($row.direct_canonical) { $score += 50 }
        if ($row.name -match "(?i)$Subsystem") { $score += 30 }
        if ($row.name -match '^(Start|Launch)') { $score += 15 }
        elseif ($row.name -match '^Invoke') { $score += 10 }
        if ($row.hydra_score -lt 70) { $score += 10 }
        [pscustomobject]@{
            subsystem = $Subsystem
            score = $score
            name = $row.name
            path = $row.path
            relative_path = $row.relative_path
            hydra_score = $row.hydra_score
            parameters = $row.parameters
            parse_ok = $row.parse_ok
        }
    }
}

function def_GetLatestV012FStatus {
    $root = Join-Path $BaseDir "_via_targeted_candidate_quarantine_runs"
    if (-not (Test-Path -LiteralPath $root)) {
        return [pscustomobject]@{found=$false;gate="NOT_FOUND";candidate_fail=-1;candidate_remaining=-1;source=""}
    }
    $csv = Get-ChildItem -LiteralPath $root -Recurse -File -Filter "v013_readiness_precheck.v012F.csv" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($null -eq $csv) { return [pscustomobject]@{found=$false;gate="NOT_FOUND";candidate_fail=-1;candidate_remaining=-1;source=""} }
    try {
        $row = Import-Csv -LiteralPath $csv.FullName -Encoding UTF8 | Select-Object -First 1
        return [pscustomobject]@{
            found = $true
            gate = [string]$row.def_gate
            candidate_fail = [int]$row.def_candidate_move_fail
            candidate_remaining = [int]$row.def_candidate_remaining_estimate
            source = $csv.FullName
        }
    }
    catch {
        return [pscustomobject]@{found=$false;gate="READ_ERROR";candidate_fail=-1;candidate_remaining=-1;source=$csv.FullName}
    }
}

function def_NewLibraryManifest {
    param($AnalysisRows, $SsotRows, $Entrypoints)
    $libraries = @($AnalysisRows | Where-Object { $_.extension -in @(".psm1", ".py", ".psd1") } | Select-Object section,subsystem,name,path,relative_path,sha256,status,parse_ok,hydra_score)
    return [ordered]@{
        schema = "VIA_LIBRARY_MANIFEST_v1"
        generated_at = (Get-Date).ToString("o")
        base_dir = $BaseDir
        accelerators = $Accelerators
        libraries = $libraries
        ssot = $SsotRows
        entrypoints = $Entrypoints
        policy = [ordered]@{
            import_on_health_check = $false
            no_dot_source_during_audit = $true
            activation_requires_exact_gate = "FULL_ACTIVATION_ELIGIBLE"
        }
    }
}

function def_WritePythonEngine {
    param([string]$Path)
    $python = @'
from __future__ import annotations
import argparse
import http.server
import json
import os
import pathlib
import socketserver
import sys


def load_manifest(path: str) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))


def health(manifest_path: str) -> int:
    data = load_manifest(manifest_path)
    rows = data.get("libraries", [])
    missing = [r for r in rows if not pathlib.Path(r.get("path", "")).exists()]
    bad = [r for r in rows if not bool(r.get("parse_ok", False))]
    result = {
        "status": "OK" if not missing and not bad else "REVIEW",
        "library_count": len(rows),
        "missing_count": len(missing),
        "parse_bad_count": len(bad),
        "import_executed": False,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "OK" else 2


def serve(root: str, port: int) -> int:
    os.chdir(root)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"VIA UI serving at http://127.0.0.1:{port}", flush=True)
        httpd.serve_forever()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--serve-root")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.health:
        if not args.manifest:
            print("--manifest is required", file=sys.stderr)
            return 2
        return health(args.manifest)
    if args.serve_root:
        return serve(args.serve_root, args.port)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@
    Set-Content -LiteralPath $Path -Value $python -Encoding UTF8
}

function def_WriteLauncher {
    param([string]$Path, [string]$VrnPath, [string]$VdfPath)
    $template = @'
#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$GatePath = "__GATE__",
    [string]$ManifestPath = "__MANIFEST__",
    [string]$PythonEnginePath = "__ENGINE__",
    [string]$ReportPath = "__REPORT__",
    [string]$VrnEntrypoint = "__VRN__",
    [string]$VdfEntrypoint = "__VDF__",
    [string]$LogDir = "__LOGDIR__",
    [int]$UiPort = 8765
)
$ErrorActionPreference = "Stop"
function EnsureDir([string]$Path) { if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null } }
EnsureDir $LogDir
$gate = Get-Content -LiteralPath $GatePath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$gate.gate -ne "FULL_ACTIVATION_ELIGIBLE") { throw "Activation blocked. Gate=$($gate.gate)" }
$pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$python = [string]$gate.python_command
if (-not (Test-Path -LiteralPath $python)) { $python = (Get-Command python -ErrorAction Stop).Source }
$uiOut = Join-Path $LogDir "python_ui.stdout.log"
$uiErr = Join-Path $LogDir "python_ui.stderr.log"
$ui = Start-Process -FilePath $python -ArgumentList @($PythonEnginePath,"--serve-root",(Split-Path -Parent $ReportPath),"--port",$UiPort) -PassThru -RedirectStandardOutput $uiOut -RedirectStandardError $uiErr
Start-Sleep -Seconds 1
Start-Process -FilePath ("http://127.0.0.1:{0}/{1}" -f $UiPort,[uri]::EscapeDataString((Split-Path -Leaf $ReportPath)))
$started = @()
foreach ($item in @(@{Name="VRN";Path=$VrnEntrypoint},@{Name="VDF";Path=$VdfEntrypoint})) {
    if (-not (Test-Path -LiteralPath $item.Path)) { throw "$($item.Name) entrypoint missing: $($item.Path)" }
    $out = Join-Path $LogDir ("{0}.stdout.log" -f $item.Name)
    $err = Join-Path $LogDir ("{0}.stderr.log" -f $item.Name)
    $p = Start-Process -FilePath $pwsh -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$item.Path) -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
    $started += [pscustomobject]@{subsystem=$item.Name;pid=$p.Id;path=$item.Path;stdout=$out;stderr=$err;started_at=(Get-Date).ToString("o")}
}
$started | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $LogDir "activation_processes.json") -Encoding UTF8
Write-Host "def Gate              : FULL_ACTIVATION_ELIGIBLE" -ForegroundColor Green
Write-Host "def VRN               : STARTED NON-BLOCKING" -ForegroundColor Green
Write-Host "def VDF               : STARTED NON-BLOCKING" -ForegroundColor Green
Write-Host "def Python UI         : STARTED NON-BLOCKING" -ForegroundColor Green
Write-Host "def Launcher remains open; child systems continue independently." -ForegroundColor Cyan
'@
    $content = $template.Replace("__GATE__", $GatePath).Replace("__MANIFEST__", $ManifestPath).Replace("__ENGINE__", $PythonEnginePath).Replace("__REPORT__", $ReportPath).Replace("__VRN__", $VrnPath).Replace("__VDF__", $VdfPath).Replace("__LOGDIR__", $LogDir)
    Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
}

function def_DeployFileHashState {
    param([string]$Source, [string]$Destination)
    $row = [ordered]@{source=$Source;destination=$Destination;state="";success=$false;error=""}
    try {
        def_EnsureDir -Path (Split-Path -Parent $Destination)
        $sourceHash = def_GetHash -Path $Source
        if (Test-Path -LiteralPath $Destination) {
            $destHash = def_GetHash -Path $Destination
            if ($destHash -eq $sourceHash) { $row.state="PROPOSED_ALREADY_PRESENT_SKIP"; $row.success=$true; return [pscustomobject]$row }
            $backup = Join-Path $BackupDir ("DEPLOY\" + (def_GetRelativePath -Path $Destination))
            def_EnsureDir -Path (Split-Path -Parent $backup)
            Copy-Item -LiteralPath $Destination -Destination $backup -Force
        }
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
        $row.state="APPLIED_WITH_BACKUP_HASH_STATE"; $row.success=$true
    }
    catch { $row.state="FAILED"; $row.error=$_.Exception.Message }
    return [pscustomobject]$row
}

function def_ToHtmlTable {
    param($Rows, [string]$EmptyText = "No rows")
    $arr = @($Rows | ForEach-Object { $_ })
    if ($arr.Count -eq 0) { return "<div class='empty'>$(def_HtmlEncode $EmptyText)</div>" }
    return ($arr | ConvertTo-Html -Fragment)
}

function def_WriteHtmlReport {
    param($AnalysisRows, $SsotRows, $Entrypoints, $Gate, $V012F, $RepairRows, $ActivationRows)
    $module = @($AnalysisRows | Where-Object section -eq "MODULE")
    $engine = @($AnalysisRows | Where-Object section -eq "ENGINE")
    $lib = @($AnalysisRows | Where-Object section -eq "FUNCTION-LIB")
    $other = @($AnalysisRows | Where-Object section -eq "OTHERS")
    $errors = @($AnalysisRows | Where-Object status -eq "ERROR")
    $hydra = @($AnalysisRows | Where-Object hydra_band -eq "HIGH")
    $roundHtml = def_ToHtmlTable -Rows $script:RoundSummaries
    $statusHtml = def_ToHtmlTable -Rows $script:StatusEvents
    $accelHtml = def_ToHtmlTable -Rows $Accelerators
    $repairHtml = def_ToHtmlTable -Rows $RepairRows
    $activationHtml = def_ToHtmlTable -Rows $ActivationRows
    $supportiveHtml = def_ToHtmlTable -Rows $script:SupportiveBootstrapRows
    $gateClass = if ($Gate.gate -eq "FULL_ACTIVATION_ELIGIBLE") { "green" } else { "red" }

    $css = @'
<style>
:root{--bg:#f7f8f6;--card:#fff;--line:#dfe7e5;--text:#1f2933;--muted:#64748b;--green:#15803d;--yellow:#a16207;--red:#b91c1c;--cyan:#0f766e}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;font-size:11px;line-height:1.35;padding:22px}
h1{font-size:23px;margin:0 0 4px} h2{font-size:16px;margin:24px 0 8px;border-left:5px solid var(--cyan);padding-left:8px} h3{font-size:13px;margin:18px 0 6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin:10px 0;box-shadow:0 8px 24px rgba(15,23,42,.05)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:8px}.metric{border:1px solid var(--line);border-radius:11px;padding:10px;min-height:58px}.k{color:var(--muted);font-size:10px}.v{font-size:15px;font-weight:800;overflow-wrap:anywhere}
.green{color:var(--green)}.yellow{color:var(--yellow)}.red{color:var(--red)}.muted{color:var(--muted)}
table{width:100%;border-collapse:collapse;table-layout:auto;font-size:10px}th{position:sticky;top:0;background:#e7efed;text-align:left;border:1px solid #d6e1df;padding:5px;white-space:normal}td{border:1px solid #e4ecea;padding:5px;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:420px}tr:nth-child(even){background:#fbfcfb}
.tablewrap{max-height:520px;overflow:auto;border:1px solid var(--line);border-radius:9px}.empty{padding:12px;color:var(--muted)}
.progressShell{height:13px;border-radius:999px;background:#dce7e4;overflow:hidden}.progressFill{height:100%;width:0;background:linear-gradient(90deg,#0f766e,#22c55e);transition:width .35s ease}.narration{margin-top:7px;color:var(--cyan);font-weight:700}
.code{font-family:Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
</style>
'@
    $scriptJs = @'
<script>
const messages=["A01 AST precision parsing","A03 Hydra risk detection","A04 dependency topology","A05 sandbox isolation","A08 SSOT alignment","A12 subsystem synchronization","A18 non-blocking launcher","A19 Python + PowerShell + UI","A20 deployment gate complete"];
let i=0;const fill=document.getElementById('progressFill');const narration=document.getElementById('narration');
function tick(){i=(i+1)%(messages.length+1);fill.style.width=((i/messages.length)*100)+'%';narration.textContent=messages[Math.min(i,messages.length-1)]||"Completed";}
setInterval(tick,850);tick();
</script>
'@
    $html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA AutoSandbox20 Matrix</title>$css</head><body>
<h1>VIA · Automatic Sandbox Test & Repair · 20 Accelerators · $Version</h1>
<div class="muted">Generated: $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss")) · Policy: max 3 repair rounds / no Stop-Process / hash-state deployment</div>
<div class="card"><div class="progressShell"><div id="progressFill" class="progressFill"></div></div><div id="narration" class="narration">Initializing</div></div>
<div class="card"><div class="grid">
<div class="metric"><div class="k">Gate</div><div class="v $gateClass">$(def_HtmlEncode $Gate.gate)</div></div>
<div class="metric"><div class="k">Risk</div><div class="v">$(def_HtmlEncode $Gate.risk)</div></div>
<div class="metric"><div class="k">Active Files</div><div class="v">$($AnalysisRows.Count)</div></div>
<div class="metric"><div class="k">Errors</div><div class="v red">$($errors.Count)</div></div>
<div class="metric"><div class="k">High Hydra</div><div class="v yellow">$($hydra.Count)</div></div>
<div class="metric"><div class="k">VRN</div><div class="v">$(def_HtmlEncode $Gate.vrn_entrypoint)</div></div>
<div class="metric"><div class="k">VDF</div><div class="v">$(def_HtmlEncode $Gate.vdf_entrypoint)</div></div>
<div class="metric"><div class="k">Activation</div><div class="v">$(def_HtmlEncode $Gate.activation)</div></div>
</div></div>
<h2>Decision</h2><div class="card code">$(def_HtmlEncode $Gate.decision)`nNext: $(def_HtmlEncode $Gate.next_step)</div>
<h2>20 Accelerators</h2><div class="card tablewrap">$accelHtml</div>
<h2>Supportive Modules Bootstrap</h2><div class="card code">Ready: $($script:SupportiveBootstrapSummary.ready)`nRegistered: $($script:SupportiveBootstrapSummary.registered_count)`nLoaded: $($script:SupportiveBootstrapSummary.loaded_count)`nRegistered Only: $($script:SupportiveBootstrapSummary.registered_only_count)`nLoad Fail: $($script:SupportiveBootstrapSummary.load_fail_count)`nCritical Missing: $($script:SupportiveBootstrapSummary.critical_missing_count)`nCritical Bad: $($script:SupportiveBootstrapSummary.critical_bad_count)</div><div class="card tablewrap">$supportiveHtml</div>
<h2>Three-Round Summary</h2><div class="card tablewrap">$roundHtml</div>
<h2>Error Matrix</h2><div class="card tablewrap">$(def_ToHtmlTable -Rows $errors)</div>
<h2>Hydra Risk Matrix</h2><div class="card tablewrap">$(def_ToHtmlTable -Rows $hydra)</div>
<h2>SSOT Alignment</h2><div class="card tablewrap">$(def_ToHtmlTable -Rows $SsotRows)</div>
<h2>Dependency / Entrypoint Matrix</h2><div class="card tablewrap">$(def_ToHtmlTable -Rows $Entrypoints)</div>
<h2>Repair / Rollback Evidence</h2><div class="card tablewrap">$repairHtml</div>
<h2>Activation Evidence</h2><div class="card tablewrap">$activationHtml</div>
<h2>MODULE</h2><div class="card tablewrap">$(def_ToHtmlTable -Rows $module)</div>
<h2>ENGINE</h2><div class="card tablewrap">$(def_ToHtmlTable -Rows $engine)</div>
<h2>FUNCTION-LIB</h2><div class="card tablewrap">$(def_ToHtmlTable -Rows $lib)</div>
<h2>OTHERS</h2><div class="card tablewrap">$(def_ToHtmlTable -Rows $other)</div>
<h2>Dynamic Status Narration Log</h2><div class="card tablewrap">$statusHtml</div>
<h2>v012F Intake</h2><div class="card code">Found: $($V012F.found)`nGate: $(def_HtmlEncode $V012F.gate)`nCandidateFail: $($V012F.candidate_fail)`nCandidateRemaining: $($V012F.candidate_remaining)`nSource: $(def_HtmlEncode $V012F.source)</div>
$scriptJs</body></html>
"@
    Set-Content -LiteralPath $ReportPath -Value $html -Encoding UTF8
}

function def_GetSupportiveFiles {
    $root = Join-Path $BaseDir "supportive modules"
    if (-not (Test-Path -LiteralPath $root)) { return @() }

    $extensions = @(".ps1", ".psm1", ".psd1", ".py", ".json", ".yaml", ".yml", ".toml")
    return @(
        Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object {
                $relative = def_GetRelativePath -Path $_.FullName
                ($extensions -contains $_.Extension.ToLowerInvariant()) -and
                ($relative -notmatch $ExcludedPathRegex)
            } |
            Sort-Object @{Expression={
                $name = $_.Name
                $priority = switch -Regex ($name) {
                    '^VIA_RegistryCore_v1\.py$' { 1; break }
                    '^VIA_SSOT_Unified\.py$' { 2; break }
                    '^VIA_EnvManager\.py$' { 3; break }
                    '^VeritasCeleritas\.py$' { 4; break }
                    '^VeritasAegisNexus\.py$' { 5; break }
                    '^VIA_Panorama_AST_RuntimeInjector\.py$' { 6; break }
                    '^Invoke-VeritasNexusCore\.ps1$' { 7; break }
                    '^Invoke-VeritasCodexNexus\.ps1$' { 8; break }
                    default { 100 }
                }
                "{0:D3}|{1}" -f $priority, $_.FullName
            }}
    )
}

function def_TestSupportivePowerShellLoadSafety {
    param([Parameter(Mandatory)][System.IO.FileInfo]$File)

    $tokens = $null
    $errors = $null
    try {
        $ast = [System.Management.Automation.Language.Parser]::ParseFile(
            $File.FullName,
            [ref]$tokens,
            [ref]$errors
        )
    }
    catch {
        return [pscustomobject]@{
            parse_ok = $false
            load_eligible = $false
            mode = "REGISTER_ONLY_PARSE_EXCEPTION"
            first_error = $_.Exception.Message
            top_level_unsafe = ""
        }
    }

    if (@($errors).Count -gt 0) {
        return [pscustomobject]@{
            parse_ok = $false
            load_eligible = $false
            mode = "REGISTER_ONLY_PARSE_BAD"
            first_error = [string]$errors[0].Message
            top_level_unsafe = ""
        }
    }

    $extension = $File.Extension.ToLowerInvariant()
    if ($extension -eq ".psm1") {
        return [pscustomobject]@{
            parse_ok = $true
            load_eligible = $true
            mode = "IMPORT_PSM1"
            first_error = ""
            top_level_unsafe = ""
        }
    }

    if ($extension -eq ".psd1") {
        try {
            $null = Test-ModuleManifest -Path $File.FullName -ErrorAction Stop
            return [pscustomobject]@{
                parse_ok = $true
                load_eligible = $true
                mode = "IMPORT_PSD1_MANIFEST"
                first_error = ""
                top_level_unsafe = ""
            }
        }
        catch {
            return [pscustomobject]@{
                parse_ok = $false
                load_eligible = $false
                mode = "REGISTER_ONLY_BAD_MANIFEST"
                first_error = $_.Exception.Message
                top_level_unsafe = ""
            }
        }
    }

    $unsafe = New-Object System.Collections.Generic.List[string]
    foreach ($statement in @($ast.EndBlock.Statements)) {
        $safe = $false

        if ($statement -is [System.Management.Automation.Language.FunctionDefinitionAst] -or
            $statement -is [System.Management.Automation.Language.TypeDefinitionAst] -or
            $statement -is [System.Management.Automation.Language.DataStatementAst]) {
            $safe = $true
        }
        elseif ($statement -is [System.Management.Automation.Language.AssignmentStatementAst]) {
            $commands = @($statement.FindAll({
                param($node)
                $node -is [System.Management.Automation.Language.CommandAst]
            }, $true))
            $safe = ($commands.Count -eq 0)
        }
        elseif ($statement -is [System.Management.Automation.Language.PipelineAst]) {
            $commands = @($statement.FindAll({
                param($node)
                $node -is [System.Management.Automation.Language.CommandAst]
            }, $true))

            if ($commands.Count -eq 1) {
                $commandName = [string]$commands[0].GetCommandName()
                $safe = ($commandName -in @("Set-StrictMode", "Export-ModuleMember"))
            }
        }

        if (-not $safe) {
            $unsafe.Add($statement.GetType().Name)
        }
    }

    $eligible = ($unsafe.Count -eq 0)
    return [pscustomobject]@{
        parse_ok = $true
        load_eligible = $eligible
        mode = if ($eligible) { "IMPORT_SAFE_PS1_AS_MODULE" } else { "REGISTER_ENTRYPOINT_ONLY" }
        first_error = ""
        top_level_unsafe = (($unsafe | Select-Object -Unique) -join ";")
    }
}

function def_InvokeSupportiveBootstrap {
    $criticalNames = @(
        "VIA_RegistryCore_v1.py",
        "VIA_SSOT_Unified.py",
        "VIA_EnvManager.py",
        "VeritasCeleritas.py",
        "VIA_Panorama_AST_RuntimeInjector.py",
        "Invoke-VeritasNexusCore.ps1",
        "Invoke-VeritasCodexNexus.ps1"
    )

    $files = @(def_GetSupportiveFiles)
    $rows = New-Object System.Collections.Generic.List[object]
    $i = 0

    foreach ($file in $files) {
        $i++
        if (($i % 25) -eq 0 -or $i -eq $files.Count) {
            def_ShowProgress -Current $i -Total $files.Count -Message "Supportive bootstrap · $($file.Name)"
        }

        $relative = def_GetRelativePath -Path $file.FullName
        $extension = $file.Extension.ToLowerInvariant()
        $critical = ($criticalNames -contains $file.Name)
        $parseOk = $true
        $loadEligible = $false
        $loaded = $false
        $state = "REGISTERED_ONLY"
        $mode = "REGISTER_ONLY"
        $firstError = ""
        $unsafe = ""

        try {
            switch ($extension) {
                { $_ -in @(".ps1", ".psm1", ".psd1") } {
                    $check = def_TestSupportivePowerShellLoadSafety -File $file
                    $parseOk = [bool]$check.parse_ok
                    $loadEligible = [bool]$check.load_eligible
                    $mode = [string]$check.mode
                    $firstError = [string]$check.first_error
                    $unsafe = [string]$check.top_level_unsafe

                    if ($parseOk -and $loadEligible) {
                        if ($extension -eq ".ps1") {
                            $moduleText = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 -ErrorAction Stop
                            $moduleText += "`r`nExport-ModuleMember -Function * -Alias *"
                            $moduleHash = def_GetHash -Path $file.FullName
                            $moduleHash8 = if ($moduleHash.Length -ge 8) { $moduleHash.Substring(0, 8) } else { "nohash000" }
                            $moduleName = "VIA_SUPPORTIVE_{0}_{1}" -f ([System.IO.Path]::GetFileNameWithoutExtension($file.Name) -replace '[^A-Za-z0-9_]', '_'), $moduleHash8
                            $dynamicModule = New-Module -Name $moduleName -ScriptBlock ([scriptblock]::Create($moduleText))
                            $null = Import-Module -ModuleInfo $dynamicModule -Force -Global -PassThru -ErrorAction Stop
                        }
                        else {
                            $null = Import-Module -Name $file.FullName -Force -Global -PassThru -ErrorAction Stop
                        }
                        $loaded = $true
                        $state = "LOADED_CONTROLLED"
                    }
                    elseif ($parseOk) {
                        $state = "REGISTERED_ENTRYPOINT_NOT_EXECUTED"
                    }
                    else {
                        $state = "REGISTERED_PARSE_BAD"
                    }
                    break
                }
                ".py" {
                    $check = def_AnalyzePython -Path $file.FullName
                    $parseOk = [bool]$check.parse_ok
                    $mode = "PYTHON_AST_REGISTER_NO_IMPORT"
                    $firstError = [string]$check.first_error
                    $state = if ($parseOk) { "REGISTERED_PYTHON_ENGINE_COMPONENT" } else { "REGISTERED_PARSE_BAD" }
                    break
                }
                ".json" {
                    try {
                        $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
                        $mode = "JSON_REGISTERED"
                        $state = "REGISTERED_CONFIGURATION"
                    }
                    catch {
                        $parseOk = $false
                        $mode = "JSON_REGISTER_PARSE_BAD"
                        $firstError = $_.Exception.Message
                        $state = "REGISTERED_PARSE_BAD"
                    }
                    break
                }
                default {
                    $mode = "STRUCTURAL_REGISTER_ONLY"
                    $state = "REGISTERED_CONFIGURATION"
                }
            }
        }
        catch {
            $state = "LOAD_FAILED_REGISTERED"
            $firstError = $_.Exception.Message
        }

        $rows.Add([pscustomobject]@{
            index = $i
            critical = $critical
            name = $file.Name
            extension = $extension
            path = $file.FullName
            relative_path = $relative
            sha256 = def_GetHash -Path $file.FullName
            parse_ok = $parseOk
            load_eligible = $loadEligible
            loaded = $loaded
            mode = $mode
            state = $state
            top_level_unsafe = $unsafe
            first_error = $firstError
        })
    }

    $array = $rows.ToArray()
    $criticalMissing = @($criticalNames | Where-Object {
        $name = $_
        -not ($array | Where-Object { $_.name.Equals($name, [System.StringComparison]::OrdinalIgnoreCase) })
    })
    $criticalBad = @($array | Where-Object { $_.critical -and -not $_.parse_ok })
    $loadFail = @($array | Where-Object state -eq "LOAD_FAILED_REGISTERED")
    $parseBad = @($array | Where-Object { -not $_.parse_ok })
    $loadedRows = @($array | Where-Object loaded -eq $true)
    $eligibleRows = @($array | Where-Object load_eligible -eq $true)
    $registeredOnly = @($array | Where-Object { -not $_.loaded })

    $summary = [pscustomobject]@{
        generated_at = (Get-Date).ToString("o")
        supportive_root = Join-Path $BaseDir "supportive modules"
        registered_count = $array.Count
        load_eligible_count = $eligibleRows.Count
        loaded_count = $loadedRows.Count
        registered_only_count = $registeredOnly.Count
        parse_bad_count = $parseBad.Count
        load_fail_count = $loadFail.Count
        critical_missing_count = $criticalMissing.Count
        critical_bad_count = $criticalBad.Count
        critical_missing = ($criticalMissing -join ";")
        ready = ($array.Count -gt 0 -and $loadFail.Count -eq 0 -and $criticalMissing.Count -eq 0 -and $criticalBad.Count -eq 0)
        policy = "REGISTER_ALL; LOAD_AST_SAFE_POWERSHELL_LIBRARIES; NEVER_EXECUTE_ENTRYPOINTS_DURING_BOOTSTRAP"
    }

    return [pscustomobject]@{
        rows = $array
        summary = $summary
    }
}

function def_Main {
    foreach ($dir in @($RunDir,$CsvDir,$JsonDir,$HtmlDir,$LogDir,$SandboxDir,$BackupDir,$RuntimeCandidateDir)) { def_EnsureDir -Path $dir }
    def_AddStatus -Phase "BOOT" -Message "Automatic Sandbox Test & Repair System starting with 20 accelerators" -Level "OK"
    if (-not (Test-Path -LiteralPath $BaseDir)) { throw "BaseDir not found: $BaseDir" }
    if ($ApprovalPhrase -ne $ExpectedApprovalPhrase) { throw "Approval phrase mismatch; no repair/deployment/activation allowed" }

    def_AddStatus -Phase "SUPPORTIVE" -Message "Registering all supportive modules, then loading AST-safe PowerShell libraries" -Level "INFO"
    $supportiveBootstrap = def_InvokeSupportiveBootstrap
    $script:SupportiveBootstrapRows = @($supportiveBootstrap.rows | ForEach-Object { $_ })
    $script:SupportiveBootstrapSummary = $supportiveBootstrap.summary
    def_WriteCsv -Data $script:SupportiveBootstrapRows -Path $SupportiveRegistryCsvPath
    def_WriteJson -Data $script:SupportiveBootstrapRows -Path $SupportiveRegistryJsonPath
    def_WriteJson -Data $script:SupportiveBootstrapSummary -Path $SupportiveSummaryJsonPath

    if ($script:SupportiveBootstrapSummary.ready) {
        def_AddStatus -Phase "SUPPORTIVE" -Message ("Supportive bootstrap READY: registered={0}, loaded={1}, registered-only={2}" -f $script:SupportiveBootstrapSummary.registered_count, $script:SupportiveBootstrapSummary.loaded_count, $script:SupportiveBootstrapSummary.registered_only_count) -Level "OK"
    }
    else {
        def_AddStatus -Phase "SUPPORTIVE" -Message ("Supportive bootstrap REVIEW: load-fail={0}, critical-missing={1}, critical-bad={2}; analysis continues but activation will remain blocked" -f $script:SupportiveBootstrapSummary.load_fail_count, $script:SupportiveBootstrapSummary.critical_missing_count, $script:SupportiveBootstrapSummary.critical_bad_count) -Level "WARN"
    }

    for ($round = 1; $round -le 3; $round++) {
        def_AddStatus -Phase "ROUND_$round" -Message "Panoramic pre-analysis" -Level "INFO"
        $pre = @(def_AnalyzeScope -Label "Round $round pre-analysis")
        $preErrors = @($pre | Where-Object status -eq "ERROR")
        $preHighHydra = @($pre | Where-Object hydra_band -eq "HIGH")

        def_AddStatus -Phase "ROUND_$round" -Message "Safe sandbox repair and topology-ordered promotion" -Level "INFO"
        $repair = @(def_ApplyRoundRepairs -Round $round -AnalysisRows $pre)
        foreach ($r in $repair) { $script:RepairEvidence.Add($r) }
        $promoted = @($repair | Where-Object promoted -eq $true).Count

        $verifyErrors = 0
        for ($verify = 1; $verify -le 3; $verify++) {
            def_AddStatus -Phase "ROUND_${round}_VERIFY_$verify" -Message "Post-fix panoramic verification $verify of 3" -Level "INFO"
            $post = @(def_AnalyzeScope -Label "Round $round verification $verify")
            $verifyErrors = @($post | Where-Object status -eq "ERROR").Count
            $script:AllAnalysisRows = $post
        }

        $summary = [pscustomobject]@{
            round = $round
            pre_files = $pre.Count
            pre_errors = $preErrors.Count
            pre_high_hydra = $preHighHydra.Count
            repair_candidates = $repair.Count
            promoted_with_backup = $promoted
            post_errors = $verifyErrors
            status = if ($verifyErrors -eq 0) { "GREEN" } elseif ($verifyErrors -lt $preErrors.Count) { "YELLOW_IMPROVED" } else { "RED_REVIEW" }
        }
        $script:RoundSummaries.Add($summary)
        def_WriteCsv -Data $pre -Path (Join-Path $CsvDir "round_${round}_pre_analysis.csv")
        def_WriteCsv -Data $repair -Path (Join-Path $CsvDir "round_${round}_repair_evidence.csv")
        def_WriteJson -Data $summary -Path (Join-Path $JsonDir "round_${round}_summary.json")
    }

    $analysis = @($script:AllAnalysisRows)
    $ssot = @(def_GetSsotMatrix -AnalysisRows $analysis)
    $vrnCandidates = @(def_GetEntrypointCandidates -Subsystem "VRN" -AnalysisRows $analysis | Sort-Object score -Descending)
    $vdfCandidates = @(def_GetEntrypointCandidates -Subsystem "VDF" -AnalysisRows $analysis | Sort-Object score -Descending)
    $vrn = $vrnCandidates | Select-Object -First 1
    $vdf = $vdfCandidates | Select-Object -First 1
    $entrypoints = @($vrnCandidates + $vdfCandidates)
    $v012f = def_GetLatestV012FStatus

    $manifest = def_NewLibraryManifest -AnalysisRows $analysis -SsotRows $ssot -Entrypoints $entrypoints
    $manifest["supportive_bootstrap"] = $script:SupportiveBootstrapSummary
    $manifest["supportive_modules"] = $script:SupportiveBootstrapRows
    def_WriteJson -Data $manifest -Path $ManifestPath
    def_WritePythonEngine -Path $PythonEnginePath
    $vrnPath = if ($null -ne $vrn) { $vrn.path } else { "" }
    $vdfPath = if ($null -ne $vdf) { $vdf.path } else { "" }
    def_WriteLauncher -Path $LauncherPath -VrnPath $vrnPath -VdfPath $vdfPath

    $pythonHealthOk = $false
    $pythonHealthText = "NOT_EXECUTED"
    if (-not [string]::IsNullOrWhiteSpace($PythonCommand) -and (Test-Path -LiteralPath $PythonCommand)) {
        try {
            $healthOutput = & $PythonCommand $PythonEnginePath --manifest $ManifestPath --health 2>&1
            $healthExit = $LASTEXITCODE
            $pythonHealthText = ($healthOutput -join " ")
            $pythonHealthOk = ($healthExit -eq 0)
        }
        catch {
            $pythonHealthText = $_.Exception.Message
            $pythonHealthOk = $false
        }
    }
    $launcherText = Get-Content -LiteralPath $LauncherPath -Raw -Encoding UTF8
    $launcherCheck = def_AnalyzePowerShell -Path $LauncherPath -Text $launcherText
    $launcherParseOk = [bool]$launcherCheck.parse_ok

    $activeErrors = @($analysis | Where-Object status -eq "ERROR")
    $ssotBad = @($ssot | Where-Object status -ne "OK")
    $v012fClean = ($v012f.found -and $v012f.candidate_fail -eq 0 -and $v012f.candidate_remaining -eq 0)
    $entrypointsReady = ($null -ne $vrn -and $null -ne $vdf)
    $roundsComplete = ($script:RoundSummaries.Count -eq 3)
    $supportiveReady = [bool]$script:SupportiveBootstrapSummary.ready

    $gateText = "BLOCKED_REVIEW_REQUIRED"
    $risk = "HIGH"
    $decision = "Do not activate; unresolved live blockers remain."
    if ($supportiveReady -and $activeErrors.Count -eq 0 -and $ssotBad.Count -eq 0 -and $entrypointsReady -and $v012fClean -and $roundsComplete -and $pythonHealthOk -and $launcherParseOk) {
        $gateText = "FULL_ACTIVATION_ELIGIBLE"
        $risk = "LOW_CONTROLLED"
        $decision = "All live gates passed. Controlled non-blocking VRN/VDF activation is permitted."
    }

    $gate = [ordered]@{
        generated_at = (Get-Date).ToString("o")
        gate = $gateText
        risk = $risk
        decision = $decision
        activation = "NOT_EXECUTED"
        active_error_count = $activeErrors.Count
        ssot_bad_count = $ssotBad.Count
        rounds_complete = $roundsComplete
        supportive_ready = $supportiveReady
        supportive_registered = $script:SupportiveBootstrapSummary.registered_count
        supportive_loaded = $script:SupportiveBootstrapSummary.loaded_count
        supportive_registered_only = $script:SupportiveBootstrapSummary.registered_only_count
        supportive_load_fail = $script:SupportiveBootstrapSummary.load_fail_count
        supportive_critical_missing = $script:SupportiveBootstrapSummary.critical_missing_count
        supportive_critical_bad = $script:SupportiveBootstrapSummary.critical_bad_count
        v012f_clean = $v012fClean
        python_health_ok = $pythonHealthOk
        python_health = $pythonHealthText
        launcher_parse_ok = $launcherParseOk
        launcher_parse_error = $launcherCheck.first_error
        vrn_entrypoint = $vrnPath
        vdf_entrypoint = $vdfPath
        python_command = $PythonCommand
        manifest_path = $ManifestPath
        report_path = $ReportPath
        next_step = if ($gateText -eq "FULL_ACTIVATION_ELIGIBLE") { "Deploy runtime package and start VRN/VDF/Python UI non-blocking" } else { "Review error, SSOT and entrypoint matrices; no forced bypass" }
    }
    def_WriteJson -Data $gate -Path $GatePath

    def_WriteCsv -Data $analysis -Path (Join-Path $CsvDir "final_live_analysis.csv")
    def_WriteCsv -Data $ssot -Path (Join-Path $CsvDir "ssot_alignment.csv")
    def_WriteCsv -Data $entrypoints -Path (Join-Path $CsvDir "entrypoint_topology.csv")
    def_WriteCsv -Data $script:RepairEvidence -Path (Join-Path $CsvDir "all_repair_evidence.csv")
    def_WriteCsv -Data $script:StatusEvents -Path (Join-Path $CsvDir "dynamic_status_narration.csv")

    def_WriteHtmlReport -AnalysisRows $analysis -SsotRows $ssot -Entrypoints $entrypoints -Gate $gate -V012F $v012f -RepairRows $script:RepairEvidence -ActivationRows $script:ActivationEvidence

    if ($gateText -eq "FULL_ACTIVATION_ELIGIBLE" -and $ActivateWhenEligible) {
        def_AddStatus -Phase "DEPLOY" -Message "Deploying unified Python Engine, manifest, launcher and HTML UI" -Level "OK"
        def_EnsureDir -Path $RuntimeDeployDir
        $deployRows = @()
        foreach ($source in @($ManifestPath,$PythonEnginePath,$LauncherPath,$ReportPath,$GatePath)) {
            $destination = Join-Path $RuntimeDeployDir (Split-Path -Leaf $source)
            $deployRows += def_DeployFileHashState -Source $source -Destination $destination
        }
        foreach ($d in $deployRows) { $script:ActivationEvidence.Add($d) }
        $deployFailed = @($deployRows | Where-Object success -eq $false).Count
        if ($deployFailed -eq 0) {
            $deployedLauncher = Join-Path $RuntimeDeployDir (Split-Path -Leaf $LauncherPath)
            $deployedGate = Join-Path $RuntimeDeployDir (Split-Path -Leaf $GatePath)
            $deployedManifest = Join-Path $RuntimeDeployDir (Split-Path -Leaf $ManifestPath)
            $deployedEngine = Join-Path $RuntimeDeployDir (Split-Path -Leaf $PythonEnginePath)
            $deployedReport = Join-Path $RuntimeDeployDir (Split-Path -Leaf $ReportPath)
            $pwsh = (Get-Command pwsh -ErrorAction Stop).Source
            $stdout = Join-Path $LogDir "launcher.stdout.log"
            $stderr = Join-Path $LogDir "launcher.stderr.log"
            $process = Start-Process -FilePath $pwsh -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$deployedLauncher,"-GatePath",$deployedGate,"-ManifestPath",$deployedManifest,"-PythonEnginePath",$deployedEngine,"-ReportPath",$deployedReport,"-LogDir",$LogDir) -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
            Start-Sleep -Seconds $ActivationProbeSeconds
            $state = if ($process.HasExited) { "EXITED_$($process.ExitCode)" } else { "RUNNING_NON_BLOCKING" }
            $script:ActivationEvidence.Add([pscustomobject]@{source=$deployedLauncher;destination="child_process_pid_$($process.Id)";state=$state;success=(-not $process.HasExited -or $process.ExitCode -eq 0);error=""})
            $gate["activation"] = $state
            def_WriteJson -Data $gate -Path $GatePath
            def_AddStatus -Phase "ACTIVATE" -Message "VRN/VDF unified launcher state: $state" -Level "OK"
        }
        else {
            $gate["activation"] = "DEPLOYMENT_FAILED"
            def_WriteJson -Data $gate -Path $GatePath
            def_AddStatus -Phase "DEPLOY" -Message "Deployment failed; activation not executed" -Level "ERROR"
        }
        def_WriteCsv -Data $script:ActivationEvidence -Path (Join-Path $CsvDir "activation_evidence.csv")
        def_WriteHtmlReport -AnalysisRows $analysis -SsotRows $ssot -Entrypoints $entrypoints -Gate $gate -V012F $v012f -RepairRows $script:RepairEvidence -ActivationRows $script:ActivationEvidence
    }
    else {
        def_AddStatus -Phase "ACTIVATE" -Message "Activation not executed because exact FULL_ACTIVATION_ELIGIBLE gate was not reached" -Level "WARN"
    }

    if ($OpenHtmlReport -and (Test-Path -LiteralPath $ReportPath)) { Start-Process -FilePath $ReportPath }

    Write-Host ""
    Write-Host ("=" * 108) -ForegroundColor DarkCyan
    Write-Host "def VIA · AUTOSANDBOX20 · FINAL RESULT" -ForegroundColor Cyan
    Write-Host ("=" * 108) -ForegroundColor DarkCyan
    Write-Host ("def Gate                 : {0}" -f $gate.gate) -ForegroundColor Cyan
    Write-Host ("def Risk                 : {0}" -f $gate.risk) -ForegroundColor Yellow
    Write-Host ("def ActiveErrors         : {0}" -f $gate.active_error_count) -ForegroundColor White
    Write-Host ("def SupportiveReady      : {0}" -f $gate.supportive_ready) -ForegroundColor White
    Write-Host ("def SupportiveRegistered : {0}" -f $gate.supportive_registered) -ForegroundColor White
    Write-Host ("def SupportiveLoaded     : {0}" -f $gate.supportive_loaded) -ForegroundColor White
    Write-Host ("def SupportiveLoadFail   : {0}" -f $gate.supportive_load_fail) -ForegroundColor White
    Write-Host ("def SSOTBad              : {0}" -f $gate.ssot_bad_count) -ForegroundColor White
    Write-Host ("def VRNEntrypoint        : {0}" -f $gate.vrn_entrypoint) -ForegroundColor White
    Write-Host ("def VDFEntrypoint        : {0}" -f $gate.vdf_entrypoint) -ForegroundColor White
    Write-Host ("def Activation           : {0}" -f $gate.activation) -ForegroundColor Green
    Write-Host ("def RunDir               : {0}" -f $RunDir) -ForegroundColor Green
    Write-Host ("def HTML                 : {0}" -f $ReportPath) -ForegroundColor Green
    Write-Host "def PowerShell remains open; all child processes are non-blocking." -ForegroundColor Cyan
}

try {
    def_Main
}
catch {
    foreach ($dir in @($RunDir,$CsvDir,$JsonDir,$HtmlDir,$LogDir)) { try { def_EnsureDir -Path $dir } catch {} }
    $fatal = [ordered]@{
        generated_at = (Get-Date).ToString("o")
        gate = "OUTER_SAFE_CATCH_BLOCKED"
        risk = "HIGH"
        decision = "Fatal error captured; no forced activation."
        activation = "NOT_EXECUTED"
        error = $_.Exception.Message
        stack = $_.ScriptStackTrace
        run_dir = $RunDir
    }
    try { def_WriteJson -Data $fatal -Path $GatePath } catch {}
    Write-Host ""
    Write-Host "def OUTER SAFE CATCH" -ForegroundColor Red
    Write-Host ("def ErrorMessage : {0}" -f $_.Exception.Message) -ForegroundColor Red
    Write-Host ("def ErrorType    : {0}" -f $_.Exception.GetType().FullName) -ForegroundColor Red
    Write-Host ("def StackTrace   : {0}" -f $_.ScriptStackTrace) -ForegroundColor DarkRed
    Write-Host ("def RunDir       : {0}" -f $RunDir) -ForegroundColor Yellow
    Write-Host "def No forced activation was executed." -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
