#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [bool]$ActivateWhenEligible = $true,
    [bool]$OpenHtmlReport = $true,
    [int]$ActivationProbeSeconds = 5,
    [int]$UiPortStart = 8765,
    [string]$ApprovalPhrase = "I_APPROVE_VIA_v0133_ADJUDICATE_QUARANTINE_AND_ACTIVATE_VRN_VDF_20260725"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Version = "v0133"
$ExpectedApprovalPhrase = "I_APPROVE_VIA_v0133_ADJUDICATE_QUARANTINE_AND_ACTIVATE_VRN_VDF_20260725"
$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunName = "RUN_${RunStamp}_VIA_LIVE_BLOCKER_ADJUDICATE_ACTIVATE_${Version}"
$RunRoot = Join-Path $BaseDir "_via_live_blocker_adjudication_runs"
$RunDir = Join-Path $RunRoot $RunName
$CsvDir = Join-Path $RunDir "csv"
$JsonDir = Join-Path $RunDir "json"
$HtmlDir = Join-Path $RunDir "html"
$LogDir = Join-Path $RunDir "logs"
$BackupDir = Join-Path $RunDir "backups_preserve_original_paths"
$RuntimeCandidateDir = Join-Path $RunDir "runtime_candidate"
$PersistentQuarantineRoot = Join-Path $BaseDir "_via_live_blocker_quarantine\v0133"
$RuntimeDeployDir = Join-Path $BaseDir "supportive modules\VIA_AutoSandbox20_Runtime\v0133"

$GatePath = Join-Path $JsonDir "activation_gate.v0133.json"
$ManifestPath = Join-Path $RuntimeCandidateDir "VIA_LibraryManifest.v0133.json"
$PythonEnginePath = Join-Path $RuntimeCandidateDir "SUP_MDL114_UnifiedPythonEngine_v0133.py"
$SupportiveLoadListPath = Join-Path $RuntimeCandidateDir "supportive_loaded_modules.v0133.json"
$VrnBootstrapPath = Join-Path $RuntimeCandidateDir "Start-VIA-VRN-With-Supportive-v0133.ps1"
$VdfBootstrapPath = Join-Path $RuntimeCandidateDir "Start-VIA-VDF-With-Supportive-v0133.ps1"
$UnifiedLauncherPath = Join-Path $RuntimeCandidateDir "Invoke-VIA-VRN-VDF-UnifiedLauncher-v0133.ps1"
$ReportPath = Join-Path $HtmlDir "VIA_LiveBlocker_Adjudication_Activation_Matrix_v0133.html"

$AdjudicationCsvPath = Join-Path $CsvDir "blocker_adjudication.v0133.csv"
$QuarantineEvidenceCsvPath = Join-Path $CsvDir "quarantine_evidence.v0133.csv"
$PostErrorCsvPath = Join-Path $CsvDir "post_adjudication_errors.v0133.csv"
$SsotCsvPath = Join-Path $CsvDir "ssot_revalidation.v0133.csv"
$EntrypointCsvPath = Join-Path $CsvDir "entrypoint_revalidation.v0133.csv"
$SupportiveCsvPath = Join-Path $CsvDir "supportive_loaded_modules.v0133.csv"
$ActivationEvidenceCsvPath = Join-Path $CsvDir "activation_evidence.v0133.csv"
$StatusCsvPath = Join-Path $CsvDir "dynamic_status_narration.v0133.csv"
$SummaryJsonPath = Join-Path $JsonDir "summary.v0133.json"

$script:StatusEvents = New-Object System.Collections.Generic.List[object]
$script:ActivationEvidence = New-Object System.Collections.Generic.List[object]

$ExpectedBlockers = @(
    [pscustomobject]@{
        relative_path = "functional modules\VRN\complete_table_extractor (3)_shac8a818353c40.py"
        sha256 = "c8a818353c400954f0a90896f5786ca9a7214b4987a4ea0906b93573a375215e"
        class = "VRN_DERIVED_DUPLICATE_WITH_PARSE_OK_SIBLINGS"
    },
    [pscustomobject]@{
        relative_path = "supportive modules\audit_tools\AutoDevMaster_New_sha8950ec67ed20.ps1"
        sha256 = "8950ec67ed20d9bda93001d6838b8a689e08f315af4cb0263acf5868257661eb"
        class = "SUPPORTIVE_NONCORE_HASH_ARTIFACT"
    },
    [pscustomobject]@{
        relative_path = "supportive modules\audit_tools\healthcheck_fixed_sha6f5e39464c62.py"
        sha256 = "6f5e39464c62ef78b3262b45775fdbe59df37b62460f13f807d15af86c76d01f"
        class = "SUPPORTIVE_NONCORE_HASH_ARTIFACT"
    },
    [pscustomobject]@{
        relative_path = "supportive modules\registry\enhanced_autodevmaster_sha8d64df195de5.ps1"
        sha256 = "8d64df195de54921dea8fa586e4ac3976a99657bffc99092127ca99339770dcb"
        class = "SUPPORTIVE_NONCORE_HASH_ARTIFACT"
    }
)

function def_EnsureDir {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_WriteJson {
    param($Data,[Parameter(Mandatory)][string]$Path)
    def_EnsureDir -Path (Split-Path -Parent $Path)
    $Data | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_WriteCsv {
    param($Data,[Parameter(Mandatory)][string]$Path)
    def_EnsureDir -Path (Split-Path -Parent $Path)
    @($Data | ForEach-Object { $_ }) | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
}

function def_GetProperty {
    param($Object,[Parameter(Mandatory)][string]$Name,$Default=$null)
    if ($null -eq $Object) { return $Default }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function def_IsTrue {
    param($Value)
    if ($Value -is [bool]) { return [bool]$Value }
    if ($null -eq $Value) { return $false }
    return ([string]$Value).Trim().Equals("True",[System.StringComparison]::OrdinalIgnoreCase)
}

function def_GetHash {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return "" }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function def_GetRelativePath {
    param([Parameter(Mandatory)][string]$Path)
    try {
        $baseUri = [System.Uri]::new(($BaseDir.TrimEnd('\') + '\'))
        $targetUri = [System.Uri]::new($Path)
        return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString()).Replace("/","\")
    }
    catch {
        return [System.IO.Path]::GetFileName($Path)
    }
}

function def_HtmlEncode {
    param($Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_AddStatus {
    param(
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][string]$Message,
        [ValidateSet("INFO","OK","WARN","ERROR")][string]$Level = "INFO"
    )
    $row = [pscustomobject]@{
        timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss.fff")
        phase = $Phase
        level = $Level
        message = $Message
    }
    $script:StatusEvents.Add($row)
    $color = switch ($Level) {
        "OK" { "Green" }
        "WARN" { "Yellow" }
        "ERROR" { "Red" }
        default { "Cyan" }
    }
    Write-Host ("def [{0}] {1}" -f $Phase,$Message) -ForegroundColor $color
}

function def_ShowProgress {
    param([int]$Current,[int]$Total,[string]$Message)
    $safeTotal = [Math]::Max($Total,1)
    $pct = [Math]::Min(100,[Math]::Round(($Current / $safeTotal) * 100))
    $filled = [Math]::Floor($pct / 5)
    $bar = ("█" * $filled) + ("░" * (20 - $filled))
    Write-Host ("[{0,3}%] [{1}] {2}" -f $pct,$bar,$Message) -ForegroundColor Green
}

function def_TestPowerShellFile {
    param([Parameter(Mandatory)][string]$Path)
    try {
        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors) | Out-Null
        $arr = @($errors)
        return [pscustomobject]@{
            parse_ok = ($arr.Count -eq 0)
            error_count = $arr.Count
            first_error = if ($arr.Count -gt 0) { [string]$arr[0].Message } else { "" }
        }
    }
    catch {
        return [pscustomobject]@{parse_ok=$false;error_count=1;first_error=$_.Exception.Message}
    }
}

function def_ResolvePython {
    param($PriorGate)
    $candidates = New-Object System.Collections.Generic.List[string]
    $prior = [string](def_GetProperty -Object $PriorGate -Name "python_command" -Default "")
    if (-not [string]::IsNullOrWhiteSpace($prior)) { $candidates.Add($prior) }
    $candidates.Add("C:\Python313\python.exe")
    $candidates.Add("C:\Python312\python.exe")
    foreach ($name in @("python","py")) {
        try {
            $cmd = Get-Command $name -ErrorAction Stop
            if (-not [string]::IsNullOrWhiteSpace($cmd.Source)) { $candidates.Add($cmd.Source) }
        }
        catch {}
    }
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return ""
}

function def_FindFreePort {
    param([int]$StartPort)
    foreach ($port in $StartPort..($StartPort + 30)) {
        $listener = $null
        try {
            $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,$port)
            $listener.Start()
            $listener.Stop()
            return $port
        }
        catch {
            if ($null -ne $listener) { try { $listener.Stop() } catch {} }
        }
    }
    throw "No free localhost UI port found between $StartPort and $($StartPort + 30)."
}

function def_FindLatestV0132Run {
    $root = Join-Path $BaseDir "_via_autosandbox20_runs"
    if (-not (Test-Path -LiteralPath $root)) { throw "v0132 run root not found: $root" }
    $run = Get-ChildItem -LiteralPath $root -Directory -ErrorAction Stop |
        Where-Object { $_.Name -match '(?i)VIA_AUTOSANDBOX20_VRN_VDF_v0132$' } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($null -eq $run) { throw "No v0132 run directory found under $root" }
    return $run.FullName
}

function def_LoadV0132Evidence {
    param([Parameter(Mandatory)][string]$PriorRunDir)
    $paths = [ordered]@{
        analysis = Join-Path $PriorRunDir "csv\final_live_analysis.csv"
        ssot = Join-Path $PriorRunDir "csv\ssot_alignment.csv"
        entrypoints = Join-Path $PriorRunDir "csv\entrypoint_topology.csv"
        supportive_csv = Join-Path $PriorRunDir "csv\supportive_module_registry.v0132.csv"
        supportive_json = Join-Path $PriorRunDir "json\supportive_bootstrap_summary.v0132.json"
        gate = Join-Path $PriorRunDir "json\activation_gate.v0132.json"
        manifest = Join-Path $PriorRunDir "runtime_candidate\VIA_LibraryManifest.v0132.json"
        engine = Join-Path $PriorRunDir "runtime_candidate\VIA_UnifiedPythonEngine_v0132.py"
        report = Join-Path $PriorRunDir "html\VIA_AutoSandbox20_VRN_VDF_Matrix_v0132.html"
    }
    foreach ($key in $paths.Keys) {
        if (-not (Test-Path -LiteralPath $paths[$key])) { throw "Required v0132 evidence missing [$key]: $($paths[$key])" }
    }
    return [pscustomobject]@{
        paths = $paths
        analysis = @(Import-Csv -LiteralPath $paths.analysis -Encoding UTF8)
        ssot = @(Import-Csv -LiteralPath $paths.ssot -Encoding UTF8)
        entrypoints = @(Import-Csv -LiteralPath $paths.entrypoints -Encoding UTF8)
        supportive_rows = @(Import-Csv -LiteralPath $paths.supportive_csv -Encoding UTF8)
        supportive_summary = Get-Content -LiteralPath $paths.supportive_json -Raw -Encoding UTF8 | ConvertFrom-Json
        prior_gate = Get-Content -LiteralPath $paths.gate -Raw -Encoding UTF8 | ConvertFrom-Json
        prior_manifest = Get-Content -LiteralPath $paths.manifest -Raw -Encoding UTF8 | ConvertFrom-Json
    }
}

function def_BuildAdjudication {
    param($Evidence)
    $errors = @($Evidence.analysis | Where-Object { $_.status -eq "ERROR" })
    $rows = @()
    foreach ($expected in $ExpectedBlockers) {
        $actual = $errors | Where-Object {
            [string]::Equals([string]$_.relative_path,[string]$expected.relative_path,[System.StringComparison]::OrdinalIgnoreCase)
        } | Select-Object -First 1
        $matchFound = ($null -ne $actual)
        $hashMatch = $false
        $coreName = $false
        $parallelFixable = $false
        $sourcePath = Join-Path $BaseDir $expected.relative_path
        if ($matchFound) {
            $hashMatch = [string]::Equals([string]$actual.sha256,[string]$expected.sha256,[System.StringComparison]::OrdinalIgnoreCase)
            $coreName = def_IsTrue $actual.core_name
            $parallelFixable = ([string]$actual.fix_class -eq "Parallel-Fixable")
            $sourcePath = [string]$actual.path
        }
        $siblingCount = 0
        if ($expected.class -eq "VRN_DERIVED_DUPLICATE_WITH_PARSE_OK_SIBLINGS") {
            $siblingCount = @($Evidence.analysis | Where-Object {
                $_.status -eq "OK" -and
                $_.relative_path -like "functional modules\VRN\complete_table_extractor*.py" -and
                -not [string]::Equals([string]$_.relative_path,[string]$expected.relative_path,[System.StringComparison]::OrdinalIgnoreCase)
            }).Count
        }
        $eligible = ($matchFound -and $hashMatch -and -not $coreName -and $parallelFixable)
        if ($expected.class -eq "VRN_DERIVED_DUPLICATE_WITH_PARSE_OK_SIBLINGS") {
            $eligible = ($eligible -and $siblingCount -gt 0)
        }
        $rows += [pscustomobject]@{
            relative_path = $expected.relative_path
            source_path = $sourcePath
            expected_sha256 = $expected.sha256
            actual_sha256 = if ($matchFound) { [string]$actual.sha256 } else { "" }
            prior_status = if ($matchFound) { [string]$actual.status } else { "NOT_FOUND_IN_ERROR_SET" }
            prior_first_error = if ($matchFound) { [string]$actual.first_error } else { "" }
            adjudication_class = $expected.class
            match_found = $matchFound
            hash_match = $hashMatch
            core_name = $coreName
            parallel_fixable = $parallelFixable
            parse_ok_sibling_count = $siblingCount
            quarantine_eligible = $eligible
            decision = if ($eligible) { "QUARANTINE_NONCORE_DERIVED_ARTIFACT" } else { "FAIL_CLOSED_REVIEW" }
        }
    }
    $expectedPaths = @($ExpectedBlockers | ForEach-Object { $_.relative_path.ToLowerInvariant() })
    $extraErrors = @($errors | Where-Object { $expectedPaths -notcontains ([string]$_.relative_path).ToLowerInvariant() })
    return [pscustomobject]@{
        rows = @($rows)
        prior_errors = $errors
        extra_errors = $extraErrors
        exact_error_set = ($errors.Count -eq $ExpectedBlockers.Count -and $extraErrors.Count -eq 0 -and @($rows | Where-Object { -not $_.match_found }).Count -eq 0)
    }
}

function def_InvokeContentAddressedQuarantine {
    param($AdjudicationRows)
    $evidence = @()
    $index = 0
    foreach ($row in @($AdjudicationRows)) {
        $index++
        def_ShowProgress -Current $index -Total (@($AdjudicationRows).Count) -Message ("Quarantine adjudicated blocker · " + [System.IO.Path]::GetFileName($row.source_path))
        $source = [string]$row.source_path
        $relative = [string]$row.relative_path
        $expectedHash = [string]$row.expected_sha256
        $target = Join-Path (Join-Path $PersistentQuarantineRoot $expectedHash) $relative
        $result = [ordered]@{
            index = $index
            source_path = $source
            relative_path = $relative
            expected_sha256 = $expectedHash
            target_path = $target
            pre_source_exists = (Test-Path -LiteralPath $source)
            state = ""
            success = $false
            post_source_exists = $true
            target_exists = $false
            target_sha256 = ""
            error = ""
        }
        try {
            if (-not (def_IsTrue $row.quarantine_eligible)) {
                throw "Adjudication did not approve quarantine for $relative"
            }
            $sourceExists = Test-Path -LiteralPath $source
            $targetExists = Test-Path -LiteralPath $target
            if ($sourceExists) {
                $sourceHash = def_GetHash -Path $source
                if (-not [string]::Equals($sourceHash,$expectedHash,[System.StringComparison]::OrdinalIgnoreCase)) {
                    throw "Source hash changed. Expected=$expectedHash Actual=$sourceHash"
                }
                if (-not $targetExists) {
                    def_EnsureDir -Path (Split-Path -Parent $target)
                    Move-Item -LiteralPath $source -Destination $target -ErrorAction Stop
                    $result.state = "ORIGINAL_TO_CONTENT_ADDRESSED_QUARANTINE"
                }
                else {
                    $targetHash = def_GetHash -Path $target
                    if (-not [string]::Equals($targetHash,$expectedHash,[System.StringComparison]::OrdinalIgnoreCase)) {
                        throw "Existing quarantine target hash conflict: $target"
                    }
                    $repeatTarget = Join-Path (Join-Path $RunDir "repeat_quarantine_preserve_original_paths") $relative
                    def_EnsureDir -Path (Split-Path -Parent $repeatTarget)
                    Move-Item -LiteralPath $source -Destination $repeatTarget -ErrorAction Stop
                    $result.target_path = $repeatTarget
                    $result.state = "DUPLICATE_SOURCE_MOVED_TO_RUN_QUARANTINE"
                }
            }
            else {
                if ($targetExists -and [string]::Equals((def_GetHash -Path $target),$expectedHash,[System.StringComparison]::OrdinalIgnoreCase)) {
                    $result.state = "PROPOSED_ALREADY_PRESENT_SKIP"
                }
                else {
                    throw "Source absent and matching content-addressed quarantine evidence not found."
                }
            }
            $result.post_source_exists = Test-Path -LiteralPath $source
            $result.target_exists = Test-Path -LiteralPath $result.target_path
            if ($result.target_exists) { $result.target_sha256 = def_GetHash -Path $result.target_path }
            $result.success = (-not $result.post_source_exists -and $result.target_exists -and [string]::Equals($result.target_sha256,$expectedHash,[System.StringComparison]::OrdinalIgnoreCase))
            if (-not $result.success) { throw "Post-quarantine verification failed." }
        }
        catch {
            $result.state = if ([string]::IsNullOrWhiteSpace($result.state)) { "FAILED" } else { $result.state }
            $result.error = $_.Exception.Message
            $result.post_source_exists = Test-Path -LiteralPath $source
            $result.target_exists = Test-Path -LiteralPath $result.target_path
            if ($result.target_exists) { $result.target_sha256 = def_GetHash -Path $result.target_path }
            $result.success = $false
        }
        $evidence += [pscustomobject]$result
    }
    return @($evidence)
}

function def_RevalidateSsot {
    param($PriorSsot)
    $rows = @()
    foreach ($item in @($PriorSsot)) {
        $path = [string]$item.path
        $exists = Test-Path -LiteralPath $path
        $parseOk = $false
        $firstError = ""
        if ($exists) {
            try {
                $extension = [System.IO.Path]::GetExtension($path).ToLowerInvariant()
                if ($extension -eq ".json") {
                    Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null
                    $parseOk = $true
                }
                elseif ($extension -eq ".py") {
                    $parseOk = def_IsTrue $item.parse_ok
                    if (-not $parseOk) { $firstError = "Prior v0132 Python AST evidence was not clean." }
                }
                elseif ($extension -in @(".ps1",".psm1",".psd1")) {
                    $check = def_TestPowerShellFile -Path $path
                    $parseOk = $check.parse_ok
                    $firstError = $check.first_error
                }
                else {
                    $parseOk = def_IsTrue $item.parse_ok
                }
            }
            catch {
                $parseOk = $false
                $firstError = $_.Exception.Message
            }
        }
        $rows += [pscustomobject]@{
            name = [string]$item.name
            path = $path
            exists = $exists
            parse_ok = $parseOk
            status = if ($exists -and $parseOk) { "OK" } elseif (-not $exists) { "MISSING" } else { "ERROR" }
            first_error = $firstError
        }
    }
    return @($rows)
}

function def_SelectAndValidateEntrypoints {
    param($PriorEntrypoints)
    $preferred = @(
        [pscustomobject]@{subsystem="VRN";relative_path="functional modules\VRN\Invoke-VRN.ps1"},
        [pscustomobject]@{subsystem="VDF";relative_path="functional modules\VDF\Invoke-VDF.ps1"}
    )
    $rows = @()
    foreach ($want in $preferred) {
        $candidate = $PriorEntrypoints | Where-Object {
            $_.subsystem -eq $want.subsystem -and
            [string]::Equals([string]$_.relative_path,[string]$want.relative_path,[System.StringComparison]::OrdinalIgnoreCase)
        } | Select-Object -First 1
        if ($null -eq $candidate) {
            $candidate = $PriorEntrypoints | Where-Object { $_.subsystem -eq $want.subsystem } | Sort-Object {[int]$_.score} -Descending | Select-Object -First 1
        }
        $path = if ($null -ne $candidate) { [string]$candidate.path } else { Join-Path $BaseDir $want.relative_path }
        $exists = Test-Path -LiteralPath $path
        $check = if ($exists) { def_TestPowerShellFile -Path $path } else { [pscustomobject]@{parse_ok=$false;error_count=1;first_error="Entrypoint missing."} }
        $rows += [pscustomobject]@{
            subsystem = $want.subsystem
            selected_name = [System.IO.Path]::GetFileName($path)
            path = $path
            exists = $exists
            parse_ok = $check.parse_ok
            error_count = $check.error_count
            first_error = $check.first_error
            selection_policy = if ([System.IO.Path]::GetFileName($path) -eq ("Invoke-" + $want.subsystem + ".ps1")) { "PREFER_CANONICAL_INVOKE_ENTRYPOINT" } else { "FALLBACK_TO_v0132_TOP_SCORE" }
        }
    }
    return @($rows)
}

function def_BuildPostManifest {
    param($PriorManifest,$QuarantineEvidence,$SupportiveRows,$PriorRunDir)
    $blockedPaths = @($QuarantineEvidence | Where-Object { $_.success } | ForEach-Object { ([string]$_.source_path).ToLowerInvariant() })
    $activeLibraries = @()
    foreach ($library in @($PriorManifest.libraries)) {
        $path = [string](def_GetProperty -Object $library -Name "path" -Default "")
        if ($blockedPaths -contains $path.ToLowerInvariant()) { continue }
        $activeLibraries += $library
    }
    $quarantined = @($QuarantineEvidence | Select-Object source_path,target_path,expected_sha256,state,success)
    return [ordered]@{
        schema = "VIA_LIBRARY_MANIFEST_v0133"
        generated_at = (Get-Date).ToString("o")
        base_dir = $BaseDir
        prior_v0132_run = $PriorRunDir
        libraries = $activeLibraries
        supportive_loaded_modules = @($SupportiveRows)
        quarantined_components = $quarantined
        policy = [ordered]@{
            all_supportive_files_registered_by_v0132 = $true
            only_v0132_load_approved_supportive_modules_are_imported = $true
            noncore_derived_parse_failures_are_content_address_quarantined = $true
            high_hydra_parse_ok_components_are_monitored_not_modified = $true
            activation_requires_exact_gate = "FULL_ACTIVATION_ELIGIBLE"
            no_stop_process = $true
            non_blocking_child_processes = $true
        }
    }
}

function def_WriteSubsystemBootstrap {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Subsystem,
        [Parameter(Mandatory)][string]$EntrypointPath,
        [Parameter(Mandatory)][string]$SupportiveListPath,
        [Parameter(Mandatory)][string]$LogDirectory
    )
    $template = @'
#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$EntrypointPath = "__ENTRYPOINT__",
    [string]$SupportiveListPath = "__SUPPORTIVE_LIST__",
    [string]$LogDirectory = "__LOGDIR__"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
function EnsureDir([string]$Value) { if (-not (Test-Path -LiteralPath $Value)) { New-Item -ItemType Directory -Path $Value -Force | Out-Null } }
EnsureDir $LogDirectory
$events = @()
try {
    $modules = @(Get-Content -LiteralPath $SupportiveListPath -Raw -Encoding UTF8 | ConvertFrom-Json)
    foreach ($module in $modules) {
        $modulePath = [string]$module.path
        $extension = [System.IO.Path]::GetExtension($modulePath).ToLowerInvariant()
        if (-not (Test-Path -LiteralPath $modulePath)) { throw "Supportive module missing: $modulePath" }
        if ($extension -in @(".psm1",".psd1")) {
            Import-Module -Name $modulePath -Force -ErrorAction Stop
            $events += [pscustomobject]@{path=$modulePath;state="IMPORTED_MODULE";success=$true;error=""}
        }
        elseif ($extension -eq ".ps1") {
            $text = Get-Content -LiteralPath $modulePath -Raw -Encoding UTF8
            $dynamicName = "VIA_SAFE_" + ([System.IO.Path]::GetFileNameWithoutExtension($modulePath) -replace '[^A-Za-z0-9_]','_') + "_" + ([guid]::NewGuid().ToString("N").Substring(0,8))
            $dynamicModule = New-Module -Name $dynamicName -ScriptBlock ([scriptblock]::Create($text))
            Import-Module -ModuleInfo $dynamicModule -Force -ErrorAction Stop
            $events += [pscustomobject]@{path=$modulePath;state="IMPORTED_SAFE_DYNAMIC_MODULE";success=$true;error=""}
        }
        else {
            $events += [pscustomobject]@{path=$modulePath;state="REGISTERED_ONLY_NOT_IMPORTABLE";success=$true;error=""}
        }
    }
    $events | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $LogDirectory "__SUBSYSTEM___supportive_imports.json") -Encoding UTF8
    if (-not (Test-Path -LiteralPath $EntrypointPath)) { throw "Entrypoint missing: $EntrypointPath" }
    Write-Host "def __SUBSYSTEM__ Supportive Modules : IMPORTED" -ForegroundColor Green
    Write-Host "def __SUBSYSTEM__ Entrypoint          : $EntrypointPath" -ForegroundColor Cyan
    & $EntrypointPath
}
catch {
    $events += [pscustomobject]@{path=$EntrypointPath;state="BOOTSTRAP_OR_RUNTIME_ERROR";success=$false;error=$_.Exception.Message}
    $events | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $LogDirectory "__SUBSYSTEM___supportive_imports.json") -Encoding UTF8
    Write-Host "def __SUBSYSTEM__ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    Write-Host "def __SUBSYSTEM__ PowerShell remains open." -ForegroundColor Cyan
}
'@
    $content = $template.Replace("__ENTRYPOINT__",$EntrypointPath).Replace("__SUPPORTIVE_LIST__",$SupportiveListPath).Replace("__LOGDIR__",$LogDirectory).Replace("__SUBSYSTEM__",$Subsystem)
    Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
}

function def_WriteUnifiedLauncher {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$GateFile,
        [Parameter(Mandatory)][string]$VrnBootstrap,
        [Parameter(Mandatory)][string]$VdfBootstrap,
        [Parameter(Mandatory)][string]$PythonPath,
        [Parameter(Mandatory)][string]$EnginePath,
        [Parameter(Mandatory)][string]$HtmlReportPath,
        [Parameter(Mandatory)][string]$LauncherLogDir,
        [int]$UiPort
    )
    $template = @'
#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$GateFile = "__GATE__",
    [string]$VrnBootstrap = "__VRN_BOOTSTRAP__",
    [string]$VdfBootstrap = "__VDF_BOOTSTRAP__",
    [string]$PythonPath = "__PYTHON__",
    [string]$EnginePath = "__ENGINE__",
    [string]$HtmlReportPath = "__REPORT__",
    [string]$LauncherLogDir = "__LOGDIR__",
    [int]$UiPort = __PORT__
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
function EnsureDir([string]$Value) { if (-not (Test-Path -LiteralPath $Value)) { New-Item -ItemType Directory -Path $Value -Force | Out-Null } }
EnsureDir $LauncherLogDir
$gate = Get-Content -LiteralPath $GateFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$gate.gate -ne "FULL_ACTIVATION_ELIGIBLE") { throw "Activation blocked. Gate=$($gate.gate)" }
$pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$processes = @()
$vrn = Start-Process -FilePath $pwsh -ArgumentList @("-NoLogo","-NoProfile","-NoExit","-ExecutionPolicy","Bypass","-File",$VrnBootstrap) -PassThru
$processes += [pscustomobject]@{subsystem="VRN";pid=$vrn.Id;path=$VrnBootstrap;started_at=(Get-Date).ToString("o")}
$vdf = Start-Process -FilePath $pwsh -ArgumentList @("-NoLogo","-NoProfile","-NoExit","-ExecutionPolicy","Bypass","-File",$VdfBootstrap) -PassThru
$processes += [pscustomobject]@{subsystem="VDF";pid=$vdf.Id;path=$VdfBootstrap;started_at=(Get-Date).ToString("o")}
if ((Test-Path -LiteralPath $PythonPath) -and (Test-Path -LiteralPath $EnginePath)) {
    $ui = Start-Process -FilePath $PythonPath -ArgumentList @($EnginePath,"--serve-root",(Split-Path -Parent $HtmlReportPath),"--port",$UiPort) -PassThru
    $processes += [pscustomobject]@{subsystem="PYTHON_UI";pid=$ui.Id;path=$EnginePath;started_at=(Get-Date).ToString("o")}
    Start-Sleep -Milliseconds 900
    $url = "http://127.0.0.1:$UiPort/" + [uri]::EscapeDataString((Split-Path -Leaf $HtmlReportPath))
    Start-Process -FilePath $url
}
else {
    Start-Process -FilePath $HtmlReportPath
}
$processes | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $LauncherLogDir "activation_processes.json") -Encoding UTF8
Write-Host "def Gate              : FULL_ACTIVATION_ELIGIBLE" -ForegroundColor Green
Write-Host "def VRN               : STARTED AFTER SUPPORTIVE IMPORT" -ForegroundColor Green
Write-Host "def VDF               : STARTED AFTER SUPPORTIVE IMPORT" -ForegroundColor Green
Write-Host "def HTML UI           : STARTED NON-BLOCKING" -ForegroundColor Green
Write-Host "def Launcher remains open; child systems continue independently." -ForegroundColor Cyan
'@
    $content = $template.Replace("__GATE__",$GateFile).Replace("__VRN_BOOTSTRAP__",$VrnBootstrap).Replace("__VDF_BOOTSTRAP__",$VdfBootstrap).Replace("__PYTHON__",$PythonPath).Replace("__ENGINE__",$EnginePath).Replace("__REPORT__",$HtmlReportPath).Replace("__LOGDIR__",$LauncherLogDir).Replace("__PORT__",[string]$UiPort)
    Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
}

function def_DeployFileHashState {
    param([Parameter(Mandatory)][string]$Source,[Parameter(Mandatory)][string]$Destination)
    $row = [ordered]@{source=$Source;destination=$Destination;state="";success=$false;source_sha256="";destination_sha256="";error=""}
    try {
        if (-not (Test-Path -LiteralPath $Source)) { throw "Deployment source missing: $Source" }
        def_EnsureDir -Path (Split-Path -Parent $Destination)
        $sourceHash = def_GetHash -Path $Source
        $row.source_sha256 = $sourceHash
        if (Test-Path -LiteralPath $Destination) {
            $destinationHash = def_GetHash -Path $Destination
            if ([string]::Equals($destinationHash,$sourceHash,[System.StringComparison]::OrdinalIgnoreCase)) {
                $row.state = "PROPOSED_ALREADY_PRESENT_SKIP"
                $row.success = $true
                $row.destination_sha256 = $destinationHash
                return [pscustomobject]$row
            }
            $relative = def_GetRelativePath -Path $Destination
            $backup = Join-Path $BackupDir $relative
            def_EnsureDir -Path (Split-Path -Parent $backup)
            Copy-Item -LiteralPath $Destination -Destination $backup -Force
        }
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
        $row.destination_sha256 = def_GetHash -Path $Destination
        $row.success = [string]::Equals($row.destination_sha256,$sourceHash,[System.StringComparison]::OrdinalIgnoreCase)
        $row.state = if ($row.success) { "APPLIED_WITH_BACKUP_HASH_STATE" } else { "FAILED_POST_COPY_HASH" }
    }
    catch {
        $row.state = "FAILED"
        $row.error = $_.Exception.Message
        $row.success = $false
    }
    return [pscustomobject]$row
}

function def_ToHtmlTable {
    param($Rows,[int]$MaxRows=500)
    $arr = @($Rows | ForEach-Object { $_ })
    if ($arr.Count -eq 0) { return "<p class='muted'>No rows.</p>" }
    $properties = @($arr[0].PSObject.Properties.Name)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("<div class='tablewrap'><table><thead><tr>")
    foreach ($property in $properties) { [void]$sb.AppendLine("<th>$(def_HtmlEncode $property)</th>") }
    [void]$sb.AppendLine("</tr></thead><tbody>")
    foreach ($row in @($arr | Select-Object -First $MaxRows)) {
        [void]$sb.AppendLine("<tr>")
        foreach ($property in $properties) {
            $value = $row.PSObject.Properties[$property].Value
            [void]$sb.AppendLine("<td>$(def_HtmlEncode $value)</td>")
        }
        [void]$sb.AppendLine("</tr>")
    }
    [void]$sb.AppendLine("</tbody></table></div>")
    return $sb.ToString()
}

function def_WriteHtmlReport {
    param($Summary,$AdjudicationRows,$QuarantineRows,$PostErrors,$SsotRows,$EntrypointRows,$SupportiveRows,$HydraRows,$ActivationRows)
    $gateClass = if ($Summary.gate -eq "FULL_ACTIVATION_ELIGIBLE") { "green" } else { "red" }
    $activationClass = if ([string]$Summary.activation -match "RUNNING|STARTED|EXITED_0") { "green" } elseif ($Summary.activation -eq "NOT_EXECUTED") { "yellow" } else { "red" }
    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0133 Live Blocker Adjudication and VRN VDF Activation</title>
<style>
:root{--bg:#f7f8f5;--card:#ffffff;--line:#dce8e5;--ink:#1f2933;--muted:#64748b;--green:#0f766e;--yellow:#a16207;--red:#b91c1c}
*{box-sizing:border-box}body{margin:0;padding:24px;background:var(--bg);color:var(--ink);font-family:Inter,"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;font-size:11px;line-height:1.42}
h1{font-size:24px;margin:0 0 4px}h2{font-size:16px;margin:24px 0 8px;border-left:5px solid var(--green);padding-left:9px}.muted{color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:9px;margin:14px 0}.card{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:13px;box-shadow:0 5px 18px rgba(15,23,42,.04)}
.k{font-size:10px;color:var(--muted)}.v{font-size:15px;font-weight:800;overflow-wrap:anywhere}.green{color:var(--green)}.yellow{color:var(--yellow)}.red{color:var(--red)}
.tablewrap{overflow:auto;max-height:520px;border:1px solid var(--line);border-radius:10px;background:#fff}table{width:100%;border-collapse:collapse;table-layout:auto;font-size:10px}th{position:sticky;top:0;background:#e7f1ef;z-index:1}th,td{padding:6px;border:1px solid #e5ecea;text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:460px}tr:nth-child(even){background:#fbfdfc}
.code{font-family:Consolas,"Cascadia Mono",monospace;white-space:pre-wrap;overflow-wrap:anywhere}
</style>
</head>
<body>
<h1>VIA · Live Blocker Adjudication + VRN/VDF Activation · v0133</h1>
<div class="muted">Generated: $(def_HtmlEncode $Summary.generated_at) · Source v0132: $(def_HtmlEncode $Summary.prior_v0132_run)</div>
<div class="grid">
<div class="card"><div class="k">Gate</div><div class="v $gateClass">$(def_HtmlEncode $Summary.gate)</div></div>
<div class="card"><div class="k">Risk</div><div class="v">$(def_HtmlEncode $Summary.risk)</div></div>
<div class="card"><div class="k">Post Errors</div><div class="v">$(def_HtmlEncode $Summary.active_error_count)</div></div>
<div class="card"><div class="k">Supportive Ready</div><div class="v">$(def_HtmlEncode $Summary.supportive_ready)</div></div>
<div class="card"><div class="k">Supportive Loaded</div><div class="v">$(def_HtmlEncode $Summary.supportive_loaded)</div></div>
<div class="card"><div class="k">SSOT Bad</div><div class="v">$(def_HtmlEncode $Summary.ssot_bad_count)</div></div>
<div class="card"><div class="k">High Hydra</div><div class="v yellow">$(def_HtmlEncode $Summary.high_hydra_count) monitored</div></div>
<div class="card"><div class="k">Activation</div><div class="v $activationClass">$(def_HtmlEncode $Summary.activation)</div></div>
</div>
<h2>Decision</h2><div class="card code">$(def_HtmlEncode $Summary.decision)`nNext: $(def_HtmlEncode $Summary.next_step)</div>
<h2>MODULE · Blocker Adjudication</h2>$(def_ToHtmlTable -Rows $AdjudicationRows)
<h2>MODULE · Content-Addressed Quarantine Evidence</h2>$(def_ToHtmlTable -Rows $QuarantineRows)
<h2>MODULE · Post-Adjudication Error Set</h2>$(def_ToHtmlTable -Rows $PostErrors)
<h2>FUNCTION-LIB · Supportive Modules Imported Before VRN/VDF</h2>$(def_ToHtmlTable -Rows $SupportiveRows)
<h2>ENGINE · Entrypoint Revalidation</h2>$(def_ToHtmlTable -Rows $EntrypointRows)
<h2>ENGINE · Activation Evidence</h2>$(def_ToHtmlTable -Rows $ActivationRows)
<h2>OTHERS · SSOT Alignment</h2>$(def_ToHtmlTable -Rows $SsotRows)
<h2>OTHERS · High Hydra Parse-OK Monitoring</h2>$(def_ToHtmlTable -Rows $HydraRows)
<h2>Output Paths</h2><div class="card code">RunDir: $(def_HtmlEncode $RunDir)`nRuntimeDeployDir: $(def_HtmlEncode $RuntimeDeployDir)`nPersistentQuarantineRoot: $(def_HtmlEncode $PersistentQuarantineRoot)`nGate: $(def_HtmlEncode $GatePath)`nManifest: $(def_HtmlEncode $ManifestPath)`nHTML: $(def_HtmlEncode $ReportPath)</div>
</body></html>
"@
    def_EnsureDir -Path (Split-Path -Parent $ReportPath)
    Set-Content -LiteralPath $ReportPath -Value $html -Encoding UTF8
}

function def_Main {
    foreach ($dir in @($RunDir,$CsvDir,$JsonDir,$HtmlDir,$LogDir,$BackupDir,$RuntimeCandidateDir,$PersistentQuarantineRoot,$RuntimeDeployDir)) { def_EnsureDir -Path $dir }
    if ($ApprovalPhrase -ne $ExpectedApprovalPhrase) { throw "Approval phrase mismatch. No quarantine or activation executed." }

    def_AddStatus -Phase "BOOT" -Message "v0133 targeted post-v0132 adjudication starting; no broad 5424-file rescan" -Level "INFO"
    def_ShowProgress -Current 1 -Total 12 -Message "Locate latest v0132 evidence"
    $priorRunDir = def_FindLatestV0132Run
    $evidence = def_LoadV0132Evidence -PriorRunDir $priorRunDir

    def_ShowProgress -Current 2 -Total 12 -Message "Verify supportive bootstrap and exact four-error set"
    $supportiveReady = def_IsTrue (def_GetProperty -Object $evidence.supportive_summary -Name "ready" -Default $false)
    $supportiveLoadFail = [int](def_GetProperty -Object $evidence.supportive_summary -Name "load_fail_count" -Default 999)
    $supportiveCriticalMissing = [int](def_GetProperty -Object $evidence.supportive_summary -Name "critical_missing_count" -Default 999)
    $supportiveCriticalBad = [int](def_GetProperty -Object $evidence.supportive_summary -Name "critical_bad_count" -Default 999)
    $supportiveRegistered = [int](def_GetProperty -Object $evidence.supportive_summary -Name "registered_count" -Default 0)
    $supportiveLoaded = [int](def_GetProperty -Object $evidence.supportive_summary -Name "loaded_count" -Default 0)
    $loadedSupportiveRows = @($evidence.supportive_rows | Where-Object { def_IsTrue $_.loaded })
    $adjudication = def_BuildAdjudication -Evidence $evidence
    $allAdjudicationEligible = (@($adjudication.rows | Where-Object { -not (def_IsTrue $_.quarantine_eligible) }).Count -eq 0)
    if (-not $adjudication.exact_error_set) { throw "v0132 error set is not the exact four expected blockers. Fail closed." }
    if (-not $allAdjudicationEligible) { throw "One or more v0132 errors failed noncore-derived adjudication. Fail closed." }
    if (-not $supportiveReady -or $supportiveLoadFail -ne 0 -or $supportiveCriticalMissing -ne 0 -or $supportiveCriticalBad -ne 0) {
        throw "Supportive bootstrap is not clean. Ready=$supportiveReady LoadFail=$supportiveLoadFail CriticalMissing=$supportiveCriticalMissing CriticalBad=$supportiveCriticalBad"
    }
    def_WriteCsv -Data $adjudication.rows -Path $AdjudicationCsvPath

    def_ShowProgress -Current 3 -Total 12 -Message "Move exact noncore derived blockers into content-addressed quarantine"
    $quarantineRows = @(def_InvokeContentAddressedQuarantine -AdjudicationRows $adjudication.rows)
    def_WriteCsv -Data $quarantineRows -Path $QuarantineEvidenceCsvPath
    $quarantineFail = @($quarantineRows | Where-Object { -not (def_IsTrue $_.success) }).Count

    def_ShowProgress -Current 4 -Total 12 -Message "Derive post-adjudication live error set"
    $clearedPaths = @($quarantineRows | Where-Object { def_IsTrue $_.success } | ForEach-Object { ([string]$_.source_path).ToLowerInvariant() })
    $postErrors = @($adjudication.prior_errors | Where-Object { $clearedPaths -notcontains ([string]$_.path).ToLowerInvariant() })
    def_WriteCsv -Data $postErrors -Path $PostErrorCsvPath

    def_ShowProgress -Current 5 -Total 12 -Message "Revalidate SSOT and canonical entrypoints"
    $ssotRows = @(def_RevalidateSsot -PriorSsot $evidence.ssot)
    $ssotBad = @($ssotRows | Where-Object { $_.status -ne "OK" })
    $entrypointRows = @(def_SelectAndValidateEntrypoints -PriorEntrypoints $evidence.entrypoints)
    $entrypointBad = @($entrypointRows | Where-Object { -not (def_IsTrue $_.parse_ok) -or -not (def_IsTrue $_.exists) })
    def_WriteCsv -Data $ssotRows -Path $SsotCsvPath
    def_WriteCsv -Data $entrypointRows -Path $EntrypointCsvPath

    def_ShowProgress -Current 6 -Total 12 -Message "Build active library manifest and supportive load list"
    def_WriteCsv -Data $loadedSupportiveRows -Path $SupportiveCsvPath
    def_WriteJson -Data $loadedSupportiveRows -Path $SupportiveLoadListPath
    $postManifest = def_BuildPostManifest -PriorManifest $evidence.prior_manifest -QuarantineEvidence $quarantineRows -SupportiveRows $loadedSupportiveRows -PriorRunDir $priorRunDir
    def_WriteJson -Data $postManifest -Path $ManifestPath
    Copy-Item -LiteralPath $evidence.paths.engine -Destination $PythonEnginePath -Force

    $pythonCommand = def_ResolvePython -PriorGate $evidence.prior_gate
    $pythonHealthOk = $false
    $pythonHealthText = "NOT_EXECUTED"
    if (-not [string]::IsNullOrWhiteSpace($pythonCommand)) {
        try {
            $healthOutput = & $pythonCommand $PythonEnginePath --manifest $ManifestPath --health 2>&1
            $pythonHealthText = ($healthOutput -join " ")
            $pythonHealthOk = ($LASTEXITCODE -eq 0)
        }
        catch {
            $pythonHealthText = $_.Exception.Message
            $pythonHealthOk = $false
        }
    }

    def_ShowProgress -Current 7 -Total 12 -Message "Generate VRN and VDF bootstrappers with supportive import-first policy"
    $vrnEntry = $entrypointRows | Where-Object subsystem -eq "VRN" | Select-Object -First 1
    $vdfEntry = $entrypointRows | Where-Object subsystem -eq "VDF" | Select-Object -First 1
    def_WriteSubsystemBootstrap -Path $VrnBootstrapPath -Subsystem "VRN" -EntrypointPath $vrnEntry.path -SupportiveListPath $SupportiveLoadListPath -LogDirectory $LogDir
    def_WriteSubsystemBootstrap -Path $VdfBootstrapPath -Subsystem "VDF" -EntrypointPath $vdfEntry.path -SupportiveListPath $SupportiveLoadListPath -LogDirectory $LogDir
    $vrnBootstrapCheck = def_TestPowerShellFile -Path $VrnBootstrapPath
    $vdfBootstrapCheck = def_TestPowerShellFile -Path $VdfBootstrapPath

    $highHydraRows = @($evidence.analysis | Where-Object { $_.hydra_band -eq "HIGH" })
    $highHydraBad = @($highHydraRows | Where-Object { -not (def_IsTrue $_.parse_ok) -or $_.status -eq "ERROR" })
    $v012fClean = def_IsTrue (def_GetProperty -Object $evidence.prior_gate -Name "v012f_clean" -Default $false)

    $preGateEligible = (
        $supportiveReady -and
        $supportiveLoadFail -eq 0 -and
        $supportiveCriticalMissing -eq 0 -and
        $supportiveCriticalBad -eq 0 -and
        $loadedSupportiveRows.Count -eq $supportiveLoaded -and
        $quarantineFail -eq 0 -and
        $postErrors.Count -eq 0 -and
        $ssotBad.Count -eq 0 -and
        $entrypointBad.Count -eq 0 -and
        $highHydraBad.Count -eq 0 -and
        $v012fClean -and
        $pythonHealthOk -and
        $vrnBootstrapCheck.parse_ok -and
        $vdfBootstrapCheck.parse_ok
    )

    $uiPort = def_FindFreePort -StartPort $UiPortStart
    $gateText = if ($preGateEligible) { "FULL_ACTIVATION_ELIGIBLE" } else { "BLOCKED_REVIEW_REQUIRED" }
    $risk = if ($preGateEligible) { "LOW_CONTROLLED_WITH_HYDRA_MONITORING" } else { "HIGH" }
    $decision = if ($preGateEligible) {
        "Exact four noncore derived blockers were content-address quarantined; supportive, SSOT, entrypoints and Python health passed. Controlled VRN/VDF activation is permitted."
    }
    else {
        "Post-adjudication gate did not pass. No activation is permitted."
    }

    $summary = [ordered]@{
        generated_at = (Get-Date).ToString("o")
        version = $Version
        prior_v0132_run = $priorRunDir
        gate = $gateText
        risk = $risk
        decision = $decision
        activation = "NOT_EXECUTED"
        active_error_count = $postErrors.Count
        prior_error_count = @($adjudication.prior_errors).Count
        quarantined_count = @($quarantineRows | Where-Object { def_IsTrue $_.success }).Count
        quarantine_fail_count = $quarantineFail
        supportive_ready = $supportiveReady
        supportive_registered = $supportiveRegistered
        supportive_loaded = $supportiveLoaded
        supportive_load_fail = $supportiveLoadFail
        supportive_critical_missing = $supportiveCriticalMissing
        supportive_critical_bad = $supportiveCriticalBad
        ssot_bad_count = $ssotBad.Count
        entrypoint_bad_count = $entrypointBad.Count
        high_hydra_count = $highHydraRows.Count
        high_hydra_bad_count = $highHydraBad.Count
        high_hydra_policy = "PARSE_OK_MONITOR_NO_AUTO_MUTATION"
        v012f_clean = $v012fClean
        python_command = $pythonCommand
        python_health_ok = $pythonHealthOk
        python_health = $pythonHealthText
        vrn_entrypoint = $vrnEntry.path
        vdf_entrypoint = $vdfEntry.path
        ui_port = $uiPort
        run_dir = $RunDir
        runtime_deploy_dir = $RuntimeDeployDir
        persistent_quarantine_root = $PersistentQuarantineRoot
        manifest_path = $ManifestPath
        report_path = $ReportPath
        next_step = if ($preGateEligible -and $ActivateWhenEligible) { "Deploy v0133 runtime package and start VRN/VDF after supportive import" } elseif ($preGateEligible) { "Activation eligible but disabled by parameter" } else { "Review v0133 matrices; no bypass" }
    }
    def_WriteJson -Data $summary -Path $GatePath
    def_WriteJson -Data $summary -Path $SummaryJsonPath

    def_ShowProgress -Current 8 -Total 12 -Message "Generate pre-activation HTML matrix"
    def_WriteHtmlReport -Summary $summary -AdjudicationRows $adjudication.rows -QuarantineRows $quarantineRows -PostErrors $postErrors -SsotRows $ssotRows -EntrypointRows $entrypointRows -SupportiveRows $loadedSupportiveRows -HydraRows $highHydraRows -ActivationRows $script:ActivationEvidence

    def_ShowProgress -Current 9 -Total 12 -Message "Generate unified non-blocking launcher"
    def_WriteUnifiedLauncher -Path $UnifiedLauncherPath -GateFile $GatePath -VrnBootstrap $VrnBootstrapPath -VdfBootstrap $VdfBootstrapPath -PythonPath $pythonCommand -EnginePath $PythonEnginePath -HtmlReportPath $ReportPath -LauncherLogDir $LogDir -UiPort $uiPort
    $launcherCheck = def_TestPowerShellFile -Path $UnifiedLauncherPath
    if (-not $launcherCheck.parse_ok) {
        $summary.gate = "BLOCKED_GENERATED_LAUNCHER_AST"
        $summary.risk = "HIGH"
        $summary.decision = "Generated launcher AST failed. No activation."
        $summary.next_step = $launcherCheck.first_error
        def_WriteJson -Data $summary -Path $GatePath
        def_WriteJson -Data $summary -Path $SummaryJsonPath
    }

    def_ShowProgress -Current 10 -Total 12 -Message "Deploy v0133 runtime package with hash-state evidence"
    $deployRows = @()
    if ($summary.gate -eq "FULL_ACTIVATION_ELIGIBLE") {
        foreach ($source in @($GatePath,$ManifestPath,$PythonEnginePath,$SupportiveLoadListPath,$VrnBootstrapPath,$VdfBootstrapPath,$UnifiedLauncherPath,$ReportPath)) {
            $destination = Join-Path $RuntimeDeployDir (Split-Path -Leaf $source)
            $deployRows += def_DeployFileHashState -Source $source -Destination $destination
        }
        foreach ($row in $deployRows) { $script:ActivationEvidence.Add($row) }
    }
    $deployFail = @($deployRows | Where-Object { -not (def_IsTrue $_.success) }).Count

    def_ShowProgress -Current 11 -Total 12 -Message "Start VRN, VDF and HTML UI non-blocking"
    if ($summary.gate -eq "FULL_ACTIVATION_ELIGIBLE" -and $ActivateWhenEligible -and $deployFail -eq 0) {
        $deployedLauncher = Join-Path $RuntimeDeployDir (Split-Path -Leaf $UnifiedLauncherPath)
        $deployedGate = Join-Path $RuntimeDeployDir (Split-Path -Leaf $GatePath)
        $deployedManifest = Join-Path $RuntimeDeployDir (Split-Path -Leaf $ManifestPath)
        $deployedEngine = Join-Path $RuntimeDeployDir (Split-Path -Leaf $PythonEnginePath)
        $deployedSupportive = Join-Path $RuntimeDeployDir (Split-Path -Leaf $SupportiveLoadListPath)
        $deployedVrnBootstrap = Join-Path $RuntimeDeployDir (Split-Path -Leaf $VrnBootstrapPath)
        $deployedVdfBootstrap = Join-Path $RuntimeDeployDir (Split-Path -Leaf $VdfBootstrapPath)
        $deployedReport = Join-Path $RuntimeDeployDir (Split-Path -Leaf $ReportPath)

        def_WriteSubsystemBootstrap -Path $deployedVrnBootstrap -Subsystem "VRN" -EntrypointPath $vrnEntry.path -SupportiveListPath $deployedSupportive -LogDirectory $LogDir
        def_WriteSubsystemBootstrap -Path $deployedVdfBootstrap -Subsystem "VDF" -EntrypointPath $vdfEntry.path -SupportiveListPath $deployedSupportive -LogDirectory $LogDir
        def_WriteUnifiedLauncher -Path $deployedLauncher -GateFile $deployedGate -VrnBootstrap $deployedVrnBootstrap -VdfBootstrap $deployedVdfBootstrap -PythonPath $pythonCommand -EnginePath $deployedEngine -HtmlReportPath $deployedReport -LauncherLogDir $LogDir -UiPort $uiPort

        $deployedLauncherCheck = def_TestPowerShellFile -Path $deployedLauncher
        if (-not $deployedLauncherCheck.parse_ok) { throw "Deployed launcher AST failed: $($deployedLauncherCheck.first_error)" }
        $pwsh = (Get-Command pwsh -ErrorAction Stop).Source
        $launcherProcess = Start-Process -FilePath $pwsh -ArgumentList @("-NoLogo","-NoProfile","-NoExit","-ExecutionPolicy","Bypass","-File",$deployedLauncher) -PassThru
        Start-Sleep -Seconds $ActivationProbeSeconds
        $launcherState = if ($launcherProcess.HasExited) { "EXITED_$($launcherProcess.ExitCode)" } else { "RUNNING_NON_BLOCKING" }
        $launcherSuccess = (-not $launcherProcess.HasExited -or $launcherProcess.ExitCode -eq 0)
        $script:ActivationEvidence.Add([pscustomobject]@{
            source = $deployedLauncher
            destination = "launcher_process_pid_$($launcherProcess.Id)"
            state = $launcherState
            success = $launcherSuccess
            source_sha256 = def_GetHash -Path $deployedLauncher
            destination_sha256 = ""
            error = ""
        })
        $summary.activation = $launcherState
        $summary.next_step = "VRN and VDF launched in independent PowerShell windows after importing the v0132-approved supportive module set."
    }
    elseif ($summary.gate -eq "FULL_ACTIVATION_ELIGIBLE" -and -not $ActivateWhenEligible) {
        $summary.activation = "ELIGIBLE_NOT_REQUESTED"
    }
    elseif ($deployFail -gt 0) {
        $summary.gate = "BLOCKED_DEPLOYMENT_FAILURE"
        $summary.risk = "HIGH"
        $summary.activation = "NOT_EXECUTED"
        $summary.decision = "Runtime deployment failed; activation was not executed."
    }

    def_ShowProgress -Current 12 -Total 12 -Message "Write final evidence and open HTML matrix"
    def_WriteCsv -Data $script:ActivationEvidence -Path $ActivationEvidenceCsvPath
    def_WriteCsv -Data $script:StatusEvents -Path $StatusCsvPath
    def_WriteJson -Data $summary -Path $GatePath
    def_WriteJson -Data $summary -Path $SummaryJsonPath
    def_WriteHtmlReport -Summary $summary -AdjudicationRows $adjudication.rows -QuarantineRows $quarantineRows -PostErrors $postErrors -SsotRows $ssotRows -EntrypointRows $entrypointRows -SupportiveRows $loadedSupportiveRows -HydraRows $highHydraRows -ActivationRows $script:ActivationEvidence

    if (Test-Path -LiteralPath $RuntimeDeployDir) {
        foreach ($source in @($GatePath,$ReportPath)) {
            $destination = Join-Path $RuntimeDeployDir (Split-Path -Leaf $source)
            $row = def_DeployFileHashState -Source $source -Destination $destination
            $script:ActivationEvidence.Add($row)
        }
        def_WriteCsv -Data $script:ActivationEvidence -Path $ActivationEvidenceCsvPath
    }

    if ($OpenHtmlReport -and (Test-Path -LiteralPath $ReportPath)) { Start-Process -FilePath $ReportPath }

    Write-Host ""
    Write-Host ("=" * 108) -ForegroundColor DarkCyan
    Write-Host "def VIA · LIVE BLOCKER ADJUDICATION + VRN/VDF ACTIVATION · v0133" -ForegroundColor Cyan
    Write-Host ("=" * 108) -ForegroundColor DarkCyan
    Write-Host ("def Gate                 : {0}" -f $summary.gate) -ForegroundColor Cyan
    Write-Host ("def Risk                 : {0}" -f $summary.risk) -ForegroundColor Yellow
    Write-Host ("def PriorErrors          : {0}" -f $summary.prior_error_count) -ForegroundColor White
    Write-Host ("def Quarantined          : {0}" -f $summary.quarantined_count) -ForegroundColor Green
    Write-Host ("def QuarantineFail       : {0}" -f $summary.quarantine_fail_count) -ForegroundColor Red
    Write-Host ("def ActiveErrors         : {0}" -f $summary.active_error_count) -ForegroundColor White
    Write-Host ("def SupportiveReady      : {0}" -f $summary.supportive_ready) -ForegroundColor White
    Write-Host ("def SupportiveRegistered : {0}" -f $summary.supportive_registered) -ForegroundColor White
    Write-Host ("def SupportiveLoaded     : {0}" -f $summary.supportive_loaded) -ForegroundColor White
    Write-Host ("def SupportiveLoadFail   : {0}" -f $summary.supportive_load_fail) -ForegroundColor White
    Write-Host ("def SSOTBad              : {0}" -f $summary.ssot_bad_count) -ForegroundColor White
    Write-Host ("def HighHydraMonitored   : {0}" -f $summary.high_hydra_count) -ForegroundColor Yellow
    Write-Host ("def PythonHealthOK       : {0}" -f $summary.python_health_ok) -ForegroundColor White
    Write-Host ("def VRNEntrypoint        : {0}" -f $summary.vrn_entrypoint) -ForegroundColor White
    Write-Host ("def VDFEntrypoint        : {0}" -f $summary.vdf_entrypoint) -ForegroundColor White
    Write-Host ("def Activation           : {0}" -f $summary.activation) -ForegroundColor Green
    Write-Host ("def RunDir               : {0}" -f $RunDir) -ForegroundColor Green
    Write-Host ("def RuntimeDeployDir     : {0}" -f $RuntimeDeployDir) -ForegroundColor Green
    Write-Host ("def HTML                 : {0}" -f $ReportPath) -ForegroundColor Green
    Write-Host "def PowerShell remains open; VRN/VDF/UI child processes are non-blocking." -ForegroundColor Cyan
}

try {
    def_Main
}
catch {
    foreach ($dir in @($RunDir,$CsvDir,$JsonDir,$HtmlDir,$LogDir)) { try { def_EnsureDir -Path $dir } catch {} }
    $fatal = [ordered]@{
        generated_at = (Get-Date).ToString("o")
        version = $Version
        gate = "OUTER_SAFE_CATCH_BLOCKED"
        risk = "HIGH"
        decision = "Fatal error captured; no forced activation."
        activation = "NOT_EXECUTED"
        error_type = $_.Exception.GetType().FullName
        error = $_.Exception.Message
        stack_trace = $_.ScriptStackTrace
        run_dir = $RunDir
    }
    try { def_WriteJson -Data $fatal -Path $SummaryJsonPath } catch {}
    Write-Host ""
    Write-Host "def OUTER SAFE CATCH v0133" -ForegroundColor Red
    Write-Host ("def ErrorType    : {0}" -f $_.Exception.GetType().FullName) -ForegroundColor Red
    Write-Host ("def ErrorMessage : {0}" -f $_.Exception.Message) -ForegroundColor Red
    Write-Host ("def StackTrace   : {0}" -f $_.ScriptStackTrace) -ForegroundColor DarkRed
    Write-Host ("def RunDir       : {0}" -f $RunDir) -ForegroundColor Cyan
    Write-Host "def No forced activation was executed." -ForegroundColor Yellow
}
finally {
    Write-Host ""
    Write-Host "def PowerShell remains open." -ForegroundColor Cyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
