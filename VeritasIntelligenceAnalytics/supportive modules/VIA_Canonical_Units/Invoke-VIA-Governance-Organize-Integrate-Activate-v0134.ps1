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
====================================================================================================
def VIA · GOVERNANCE ORGANIZE / REGISTER / INTEGRATE / ACTIVATE · v0134
====================================================================================================
Purpose
-------
1. Inventory and logically number the VIA folder.
2. Register every in-scope file in an append-only governance overlay.
3. Classify MODULE / ENGINE / FUNCTION-LIB / SSOT / UI / DOCUMENT / DATA / EVIDENCE / OTHER.
4. Create suggested target-folder mappings without breaking existing dependency paths.
5. Automatically quarantine only deterministic noncanonical duplicate / deletion candidates.
6. Preserve canonical paths; no broad rename and no blind move.
7. Integrate registry, taxonomy, manifests and launchers under a governed runtime folder.
8. Re-launch VRN and VDF after importing the v0133-approved supportive module set.
9. Use EncodedCommand so paths containing spaces are not split by Start-Process.
10. Produce HTML / CSV / JSON evidence and keep the parent PowerShell open.

Safety
------
- No Stop-Process.
- No permanent deletion by default.
- No broad canonical rename.
- No direct mutation of functional modules or core supportive files.
- Exact duplicate and deletion candidates are content-address quarantined.
- Ambiguous move candidates are registered with suggested targets only.
- Every physical move is hash-state guarded and preserves the original relative path.
- VRN / VDF launch occurs only when v0133 gate, SSOT, entrypoints and supportive registry are clean.
====================================================================================================
#>

[CmdletBinding()]
param(
    [string]$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",

    [bool]$ApplySafeOrganization = $true,
    [bool]$ActivateVrnVdf = $true,
    [bool]$OpenHtmlReport = $true,
    [bool]$KeepParentPowerShellOpen = $true,

    [int]$ActivationProbeSeconds = 8,
    [int64]$HashSizeGateBytes = 16777216,

    [string]$ApprovalPhrase = "I_APPROVE_VIA_v0134_SAFE_ORGANIZATION_AND_ACTIVATION"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedApprovalPhrase = "I_APPROVE_VIA_v0134_SAFE_ORGANIZATION_AND_ACTIVATION"
$Version = "v0134"
$Now = Get-Date
$RunStamp = $Now.ToString("yyyyMMdd_HHmmss")
$RunName = "RUN_${RunStamp}_VIA_GOVERNANCE_ORGANIZE_INTEGRATE_ACTIVATE_v0134"

$RunRoot = Join-Path $BaseDir "_via_governance_organization_runs"
$RunDir = Join-Path $RunRoot $RunName

$CsvDir = Join-Path $RunDir "csv"
$JsonDir = Join-Path $RunDir "json"
$HtmlDir = Join-Path $RunDir "html"
$LogDir = Join-Path $RunDir "logs"
$CandidateDir = Join-Path $RunDir "runtime_candidate"

$PersistentGovernanceDir = Join-Path $BaseDir "supportive modules\VIA_Governance_Runtime\v0134"
$PersistentRegistryDir = Join-Path $PersistentGovernanceDir "registry"
$PersistentLauncherDir = Join-Path $PersistentGovernanceDir "launcher"
$PersistentHtmlDir = Join-Path $PersistentGovernanceDir "html"
$PersistentLogDir = Join-Path $PersistentGovernanceDir "logs"
$PersistentManifestDir = Join-Path $PersistentGovernanceDir "manifests"

$OrganizationQuarantineRoot = Join-Path $BaseDir "_via_organization_quarantine\v0134"
$DeletionQuarantineRoot = Join-Path $BaseDir "_via_deletion_candidates_quarantine\v0134"

$InventoryCsv = Join-Path $CsvDir "VIA_FileRegistry.v0134.csv"
$ActionCsv = Join-Path $CsvDir "VIA_OrganizationActions.v0134.csv"
$MoveEvidenceCsv = Join-Path $CsvDir "VIA_OrganizationMoveEvidence.v0134.csv"
$ActivationEvidenceCsv = Join-Path $CsvDir "VIA_ActivationEvidence.v0134.csv"

$InventoryJson = Join-Path $JsonDir "VIA_FileRegistry.v0134.json"
$TaxonomyJson = Join-Path $JsonDir "VIA_FolderTaxonomy.v0134.json"
$ActionJson = Join-Path $JsonDir "VIA_OrganizationActions.v0134.json"
$MoveEvidenceJson = Join-Path $JsonDir "VIA_OrganizationMoveEvidence.v0134.json"
$ActivationEvidenceJson = Join-Path $JsonDir "VIA_ActivationEvidence.v0134.json"
$SummaryJson = Join-Path $JsonDir "summary.v0134.json"
$GateJson = Join-Path $JsonDir "governance_activation_gate.v0134.json"

$ReportHtml = Join-Path $HtmlDir "VIA_Governance_Organization_Activation_Matrix_v0134.html"

$SupportiveListCandidate = Join-Path $CandidateDir "supportive_loaded_modules.v0134.json"
$VrnBootstrapCandidate = Join-Path $CandidateDir "Start-VIA-VRN-With-Supportive-v0134.ps1"
$VdfBootstrapCandidate = Join-Path $CandidateDir "Start-VIA-VDF-With-Supportive-v0134.ps1"
$ActivationManifestCandidate = Join-Path $CandidateDir "VIA_ActivationManifest.v0134.json"

$VrnBootstrapDeployed = Join-Path $PersistentLauncherDir "Start-VIA-VRN-With-Supportive-v0134.ps1"
$VdfBootstrapDeployed = Join-Path $PersistentLauncherDir "Start-VIA-VDF-With-Supportive-v0134.ps1"
$SupportiveListDeployed = Join-Path $PersistentManifestDir "supportive_loaded_modules.v0134.json"
$ActivationManifestDeployed = Join-Path $PersistentManifestDir "VIA_ActivationManifest.v0134.json"

$VrnStatusPath = Join-Path $PersistentLogDir "VRN_activation_status.v0134.json"
$VdfStatusPath = Join-Path $PersistentLogDir "VDF_activation_status.v0134.json"

$script:Narration = New-Object System.Collections.Generic.List[object]
$script:MoveEvidence = New-Object System.Collections.Generic.List[object]
$script:ActivationEvidence = New-Object System.Collections.Generic.List[object]

function def_EnsureDir {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function def_Banner {
    param([Parameter(Mandatory)][string]$Title)

    Write-Host ""
    Write-Host ("=" * 112) -ForegroundColor DarkCyan
    Write-Host ("def {0}" -f $Title) -ForegroundColor Cyan
    Write-Host ("=" * 112) -ForegroundColor DarkCyan
}

function def_Narrate {
    param(
        [Parameter(Mandatory)][string]$Stage,
        [Parameter(Mandatory)][string]$Message,
        [ValidateSet("INFO","OK","WARN","ERROR")][string]$Level = "INFO"
    )

    $row = [pscustomobject]@{
        timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss.fff")
        stage = $Stage
        level = $Level
        message = $Message
    }
    $script:Narration.Add($row)

    $color = switch ($Level) {
        "OK"    { "Green" }
        "WARN"  { "Yellow" }
        "ERROR" { "Red" }
        default { "Cyan" }
    }

    Write-Host ("def [{0}] {1}" -f $Stage,$Message) -ForegroundColor $color
}

function def_Progress {
    param(
        [int]$Current,
        [int]$Total,
        [string]$Message
    )

    $safeTotal = [Math]::Max($Total,1)
    $pct = [Math]::Min(100,[Math]::Round(($Current / $safeTotal) * 100))
    $filled = [Math]::Floor($pct / 5)
    $bar = ("█" * $filled) + ("░" * (20 - $filled))
    Write-Host ("[{0,3}%] [{1}] {2}" -f $pct,$bar,$Message) -ForegroundColor Green
}

function def_WriteJson {
    param(
        $Data,
        [Parameter(Mandatory)][string]$Path
    )

    def_EnsureDir -Path (Split-Path -Parent $Path)
    $Data | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_WriteCsv {
    param(
        $Data,
        [Parameter(Mandatory)][string]$Path
    )

    def_EnsureDir -Path (Split-Path -Parent $Path)
    @($Data) | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
}

function def_GetStringHash {
    param([AllowEmptyString()][string]$Value)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes([string]$Value)
    $sha = [System.Security.Cryptography.SHA256]::Create()

    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-","").ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function def_GetFileHashSafe {
    param(
        [Parameter(Mandatory)][string]$Path,
        [int64]$SizeGateBytes = $HashSizeGateBytes
    )

    try {
        $item = Get-Item -LiteralPath $Path -ErrorAction Stop

        if ($item.Length -gt $SizeGateBytes) {
            $meta = "{0}|{1}|{2}" -f $item.FullName,$item.Length,$item.LastWriteTimeUtc.Ticks
            return [pscustomobject]@{
                hash = def_GetStringHash -Value $meta
                hash_mode = "METADATA_SHA256_SIZE_GATE"
                content_hashed = $false
                error = ""
            }
        }

        return [pscustomobject]@{
            hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
            hash_mode = "CONTENT_SHA256"
            content_hashed = $true
            error = ""
        }
    }
    catch {
        return [pscustomobject]@{
            hash = ""
            hash_mode = "HASH_ERROR"
            content_hashed = $false
            error = $_.Exception.Message
        }
    }
}

function def_GetRelativePath {
    param(
        [Parameter(Mandatory)][string]$BasePath,
        [Parameter(Mandatory)][string]$TargetPath
    )

    try {
        return [System.IO.Path]::GetRelativePath($BasePath,$TargetPath)
    }
    catch {
        return $TargetPath
    }
}

function def_IsExcludedPath {
    param([Parameter(Mandatory)][string]$FullPath)

    $p = $FullPath.ToLowerInvariant()

    $patterns = @(
        "\.git\",
        "\node_modules\",
        "\site-packages\",
        "\__pycache__\",
        "\.venv\",
        "\venv\",
        "\envs\",
        "\lib\site-packages\",
        "\appdata\",
        "\_via_governance_organization_runs\",
        "\supportive modules\via_governance_runtime\v0134\"
    )

    foreach ($pattern in $patterns) {
        if ($p.Contains($pattern)) {
            return $true
        }
    }

    return $false
}

function def_GetSubsystem {
    param([Parameter(Mandatory)][string]$RelativePath)

    $p = $RelativePath.ToUpperInvariant()

    if ($p -match "(^|\\)VRN(\\|$)")  { return "VRN" }
    if ($p -match "(^|\\)VDF(\\|$)")  { return "VDF" }
    if ($p -match "(^|\\)VAP(\\|$)")  { return "VAP" }
    if ($p -match "(^|\\)VPNS(\\|$)") { return "VPNS" }
    if ($p -match "(^|\\)VIS(\\|$)")  { return "VIS" }
    if ($p -match "MARKETFLOW")       { return "MKT" }

    return "VIA"
}

function def_GetSection {
    param(
        [Parameter(Mandatory)][string]$RelativePath,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Extension
    )

    $p = $RelativePath.ToLowerInvariant()
    $n = $Name.ToLowerInvariant()
    $e = $Extension.ToLowerInvariant()

    if ($p.Contains("\quarantine\") -or $p.StartsWith("_via_live_blocker_quarantine\") -or $p.StartsWith("_via_organization_quarantine\") -or $p.StartsWith("_via_deletion_candidates_quarantine\")) {
        return "QUARANTINE"
    }

    if ($p -match "(^|\\)(_via_.*_runs|run_\d{8}|evidence|report|reports|audit|matrix|logs?)(\\|$)") {
        return "EVIDENCE"
    }

    if ($p.StartsWith("functional modules\")) {
        return "MODULE"
    }

    if ($e -in @(".psm1",".psd1")) {
        return "FUNCTION_LIB"
    }

    if ($n -match "(registry|ssot|schema|taxonomy|manifest|pointer|contract|seal)" -and $e -in @(".json",".yaml",".yml",".toml",".csv")) {
        return "SSOT"
    }

    if ($n -match "(engine|manager|core|bridge|runtime|injector|loader|executor|processor|fetcher|builder|optimizer)" -and $e -in @(".py",".ps1",".psm1")) {
        return "ENGINE"
    }

    if ($e -in @(".html",".htm",".css",".js",".jsx",".tsx",".svg",".png",".jpg",".jpeg",".webp")) {
        return "UI"
    }

    if ($e -in @(".md",".txt",".pdf",".doc",".docx",".rtf")) {
        return "DOCUMENT"
    }

    if ($e -in @(".csv",".parquet",".duckdb",".db",".sqlite",".sql",".xlsx",".xls",".jsonl")) {
        return "DATA"
    }

    if ($e -in @(".py",".ps1",".bat",".cmd")) {
        return "ENGINE"
    }

    return "OTHER"
}

function def_GetSectionCode {
    param([Parameter(Mandatory)][string]$Section)

    switch ($Section) {
        "MODULE"       { return "MOD" }
        "ENGINE"       { return "ENG" }
        "FUNCTION_LIB" { return "LIB" }
        "SSOT"         { return "SST" }
        "UI"           { return "UIX" }
        "DOCUMENT"     { return "DOC" }
        "DATA"         { return "DAT" }
        "EVIDENCE"     { return "EVD" }
        "QUARANTINE"   { return "QRN" }
        default        { return "OTH" }
    }
}

function def_GetSuggestedTarget {
    param(
        [Parameter(Mandatory)][string]$Section,
        [Parameter(Mandatory)][string]$Subsystem
    )

    switch ($Section) {
        "MODULE"       { return "functional modules\$Subsystem" }
        "ENGINE"       { return "supportive modules\engine\$Subsystem" }
        "FUNCTION_LIB" { return "supportive modules\function_lib" }
        "SSOT"         { return "supportive modules\ssot" }
        "UI"           { return "supportive modules\ui_support" }
        "DOCUMENT"     { return "documents\$Subsystem" }
        "DATA"         { return "data\$Subsystem" }
        "EVIDENCE"     { return "_via_evidence_archive\$Subsystem" }
        "QUARANTINE"   { return "_via_quarantine_registry" }
        default        { return "supportive modules\others" }
    }
}

function def_IsCanonicalStablePath {
    param([Parameter(Mandatory)][string]$RelativePath)

    $p = $RelativePath.ToLowerInvariant()

    $stablePrefixes = @(
        "functional modules\",
        "supportive modules\",
        "documents\",
        "data\"
    )

    foreach ($prefix in $stablePrefixes) {
        if ($p.StartsWith($prefix)) {
            return $true
        }
    }

    return $false
}

function def-IsDisposableCandidatePath {
    param(
        [Parameter(Mandatory)][string]$RelativePath,
        [Parameter(Mandatory)][string]$Name
    )

    $p = $RelativePath.ToLowerInvariant()
    $n = $Name.ToLowerInvariant()

    $pathSignals = @(
        "\_inbox_to_classify\",
        "\sandbox\",
        "\staged\",
        "\candidates\",
        "\candidate\",
        "\_source_backups\",
        "\temp\",
        "\tmp\"
    )

    foreach ($signal in $pathSignals) {
        if ($p.Contains($signal)) {
            return $true
        }
    }

    if ($n -match "\.dup\." -or $n -match "\(\d+\)" -or $n -match "_copy" -or $n -match "\.tmp$") {
        return $true
    }

    return $false
}

function def_TestPowerShellFile {
    param([Parameter(Mandatory)][string]$Path)

    $tokens = $null
    $errors = $null

    try {
        [System.Management.Automation.Language.Parser]::ParseFile(
            $Path,
            [ref]$tokens,
            [ref]$errors
        ) | Out-Null

        return [pscustomobject]@{
            parse_ok = (@($errors).Count -eq 0)
            error_count = @($errors).Count
            first_error = if (@($errors).Count -gt 0) { [string]$errors[0].Message } else { "" }
        }
    }
    catch {
        return [pscustomobject]@{
            parse_ok = $false
            error_count = 1
            first_error = $_.Exception.Message
        }
    }
}

function def_FindLatestV0133Gate {
    $gateCandidates = @(
        Get-ChildItem -LiteralPath (Join-Path $BaseDir "_via_live_blocker_adjudication_runs") `
            -Recurse `
            -File `
            -Filter "activation_gate.v0133.json" `
            -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending
    )

    foreach ($candidate in $gateCandidates) {
        try {
            $gate = Get-Content -LiteralPath $candidate.FullName -Raw -Encoding UTF8 | ConvertFrom-Json

            if ([string]$gate.gate -eq "FULL_ACTIVATION_ELIGIBLE") {
                return [pscustomobject]@{
                    path = $candidate.FullName
                    data = $gate
                }
            }
        }
        catch {
            continue
        }
    }

    $deployedGate = Join-Path $BaseDir "supportive modules\VIA_AutoSandbox20_Runtime\v0133\activation_gate.v0133.json"

    if (Test-Path -LiteralPath $deployedGate) {
        try {
            $gate = Get-Content -LiteralPath $deployedGate -Raw -Encoding UTF8 | ConvertFrom-Json

            if ([string]$gate.gate -eq "FULL_ACTIVATION_ELIGIBLE") {
                return [pscustomobject]@{
                    path = $deployedGate
                    data = $gate
                }
            }
        }
        catch {}
    }

    return $null
}

function def_FindApprovedSupportiveList {
    $preferred = Join-Path $BaseDir "supportive modules\VIA_AutoSandbox20_Runtime\v0133\supportive_loaded_modules.v0133.json"

    if (Test-Path -LiteralPath $preferred) {
        return $preferred
    }

    $candidate = Get-ChildItem -LiteralPath (Join-Path $BaseDir "_via_live_blocker_adjudication_runs") `
        -Recurse `
        -File `
        -Filter "supportive_loaded_modules.v0133.json" `
        -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($null -ne $candidate) {
        return $candidate.FullName
    }

    return ""
}

function def_GetApprovedSupportivePaths {
    param([Parameter(Mandatory)][string]$SupportiveListPath)

    $paths = @()

    try {
        $rows = @(Get-Content -LiteralPath $SupportiveListPath -Raw -Encoding UTF8 | ConvertFrom-Json)

        foreach ($row in $rows) {
            $path = [string]$row.path

            if (-not [string]::IsNullOrWhiteSpace($path)) {
                $paths += $path
            }
        }
    }
    catch {}

    return @($paths)
}

function def_BuildInventory {
    param([string[]]$ApprovedSupportivePaths)

    def_Narrate -Stage "INVENTORY" -Message "Enumerating VIA files with virtual-environment and current-run exclusions."

    $files = @(
        Get-ChildItem -LiteralPath $BaseDir -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object { -not (def_IsExcludedPath -FullPath $_.FullName) } |
        Sort-Object FullName
    )

    $approvedLookup = @{}

    foreach ($path in $ApprovedSupportivePaths) {
        $approvedLookup[$path.ToLowerInvariant()] = $true
    }

    $rawRows = New-Object System.Collections.Generic.List[object]
    $total = @($files).Count
    $index = 0

    foreach ($file in $files) {
        $index++

        if ($index -eq 1 -or $index -eq $total -or ($index % 100) -eq 0) {
            def_Progress -Current $index -Total $total -Message ("Inventory {0}/{1}: {2}" -f $index,$total,$file.Name)
        }

        try {
            $relative = def_GetRelativePath -BasePath $BaseDir -TargetPath $file.FullName
            $extension = $file.Extension.ToLowerInvariant()
            $section = def_GetSection -RelativePath $relative -Name $file.Name -Extension $extension
            $subsystem = def_GetSubsystem -RelativePath $relative
            $hashInfo = def_GetFileHashSafe -Path $file.FullName
            $stablePath = def_IsCanonicalStablePath -RelativePath $relative
            $disposable = def-IsDisposableCandidatePath -RelativePath $relative -Name $file.Name
            $approvedSupportive = $approvedLookup.ContainsKey($file.FullName.ToLowerInvariant())
            $suggestedTarget = def_GetSuggestedTarget -Section $section -Subsystem $subsystem

            $rawRows.Add([pscustomobject]@{
                index = $index
                name = $file.Name
                extension = $extension
                full_path = $file.FullName
                relative_path = $relative
                section = $section
                subsystem = $subsystem
                size_bytes = [int64]$file.Length
                last_write_utc = $file.LastWriteTimeUtc.ToString("o")
                sha256 = $hashInfo.hash
                hash_mode = $hashInfo.hash_mode
                content_hashed = $hashInfo.content_hashed
                hash_error = $hashInfo.error
                canonical_path_stable = $stablePath
                disposable_candidate_path = $disposable
                approved_supportive_load = $approvedSupportive
                suggested_target_folder = $suggestedTarget
            })
        }
        catch {
            $rawRows.Add([pscustomobject]@{
                index = $index
                name = $file.Name
                extension = $file.Extension.ToLowerInvariant()
                full_path = $file.FullName
                relative_path = def_GetRelativePath -BasePath $BaseDir -TargetPath $file.FullName
                section = "OTHER"
                subsystem = "VIA"
                size_bytes = [int64]$file.Length
                last_write_utc = $file.LastWriteTimeUtc.ToString("o")
                sha256 = ""
                hash_mode = "INVENTORY_ERROR"
                content_hashed = $false
                hash_error = $_.Exception.Message
                canonical_path_stable = $false
                disposable_candidate_path = $false
                approved_supportive_load = $false
                suggested_target_folder = "supportive modules\others"
            })
        }
    }

    $rows = @($rawRows.ToArray())
    $sequenceByBucket = @{}

    foreach ($row in $rows) {
        $bucket = "{0}|{1}" -f $row.section,$row.subsystem

        if (-not $sequenceByBucket.ContainsKey($bucket)) {
            $sequenceByBucket[$bucket] = 0
        }

        $sequenceByBucket[$bucket]++
        $sectionCode = def_GetSectionCode -Section $row.section
        $sha12 = if ([string]::IsNullOrWhiteSpace([string]$row.sha256)) { "nohash000000" } else { ([string]$row.sha256).Substring(0,[Math]::Min(12,([string]$row.sha256).Length)) }
        $logicalId = "VIA-{0}-{1}-{2:D6}-{3}" -f $sectionCode,$row.subsystem,$sequenceByBucket[$bucket],$sha12

        Add-Member -InputObject $row -NotePropertyName logical_id -NotePropertyValue $logicalId
        Add-Member -InputObject $row -NotePropertyName action -NotePropertyValue "REGISTER_ONLY"
        Add-Member -InputObject $row -NotePropertyName keeper_path -NotePropertyValue ""
        Add-Member -InputObject $row -NotePropertyName action_reason -NotePropertyValue ""
    }

    return @($rows)
}

function def_ClassifyOrganizationActions {
    param([object[]]$InventoryRows)

    def_Narrate -Stage "CLASSIFY" -Message "Classifying keep, integrate, folder-suggestion, duplicate-quarantine and deletion-quarantine actions."

    $contentHashGroups = @(
        $InventoryRows |
        Where-Object {
            $_.content_hashed -eq $true -and
            -not [string]::IsNullOrWhiteSpace([string]$_.sha256)
        } |
        Group-Object sha256
    )

    $keeperByHash = @{}

    foreach ($group in $contentHashGroups) {
        $ordered = @(
            $group.Group |
            Sort-Object `
                @{Expression={ if ($_.approved_supportive_load) { 0 } else { 1 } }},
                @{Expression={ if ($_.canonical_path_stable -and -not $_.disposable_candidate_path) { 0 } else { 1 } }},
                @{Expression={ ([string]$_.relative_path).Length }},
                relative_path
        )

        if (@($ordered).Count -gt 0) {
            $keeperByHash[$group.Name] = $ordered[0]
        }
    }

    foreach ($row in $InventoryRows) {
        $action = "REGISTER_ONLY"
        $reason = "Registered in governance overlay; path preserved."
        $keeperPath = ""

        if ($row.approved_supportive_load) {
            $action = "KEEP_APPROVED_SUPPORTIVE"
            $reason = "v0133-approved supportive module; protected from organization moves."
        }
        elseif ($row.section -eq "QUARANTINE") {
            $action = "KEEP_EXISTING_QUARANTINE"
            $reason = "Existing quarantine evidence remains immutable."
        }
        elseif ($row.section -eq "EVIDENCE") {
            $action = "KEEP_EVIDENCE_APPEND_ONLY"
            $reason = "Run/evidence artifact retained append-only."
        }
        elseif ($row.canonical_path_stable -and -not $row.disposable_candidate_path) {
            $action = "KEEP_CANONICAL_PATH_REGISTER"
            $reason = "Canonical path preserved to avoid breaking imports and entrypoints."
        }
        elseif ($row.disposable_candidate_path -and $row.size_bytes -eq 0) {
            $action = "QUARANTINE_DELETION_CANDIDATE"
            $reason = "Zero-byte file in a disposable location; quarantine replaces permanent deletion."
        }
        elseif (
            $row.disposable_candidate_path -and
            $row.content_hashed -eq $true -and
            -not [string]::IsNullOrWhiteSpace([string]$row.sha256) -and
            $keeperByHash.ContainsKey([string]$row.sha256)
        ) {
            $keeper = $keeperByHash[[string]$row.sha256]

            if ([string]$keeper.full_path -ne [string]$row.full_path) {
                $action = "QUARANTINE_EXACT_DUPLICATE_NONCANONICAL"
                $reason = "Exact content duplicate in a disposable location; keeper selected by canonical priority."
                $keeperPath = [string]$keeper.full_path
            }
            else {
                $action = "KEEP_DUPLICATE_GROUP_KEEPER"
                $reason = "Selected keeper for exact-content duplicate group."
            }
        }
        elseif (-not $row.canonical_path_stable) {
            $action = "REGISTER_SUGGEST_TARGET_NO_MOVE"
            $reason = "Suggested target recorded; no blind move because dependency use is not proven."
        }

        $row.action = $action
        $row.keeper_path = $keeperPath
        $row.action_reason = $reason
    }

    return @($InventoryRows)
}

function def_GetQuarantineTarget {
    param(
        [Parameter(Mandatory)][object]$Row,
        [Parameter(Mandatory)][string]$Root
    )

    $hashFolder = if ([string]::IsNullOrWhiteSpace([string]$Row.sha256)) {
        def_GetStringHash -Value ([string]$Row.relative_path)
    }
    else {
        [string]$Row.sha256
    }

    return Join-Path (Join-Path $Root $hashFolder) ([string]$Row.relative_path)
}

function def_MoveHashState {
    param(
        [Parameter(Mandatory)][object]$Row,
        [Parameter(Mandatory)][string]$TargetRoot
    )

    $source = [string]$Row.full_path
    $target = def_GetQuarantineTarget -Row $Row -Root $TargetRoot

    $evidence = [ordered]@{
        logical_id = [string]$Row.logical_id
        action = [string]$Row.action
        source_path = $source
        target_path = $target
        expected_sha256 = [string]$Row.sha256
        state = ""
        success = $false
        pre_source_exists = (Test-Path -LiteralPath $source)
        pre_target_exists = (Test-Path -LiteralPath $target)
        post_source_exists = $null
        post_target_exists = $null
        target_sha256 = ""
        error = ""
    }

    try {
        $sourceExists = Test-Path -LiteralPath $source
        $targetExists = Test-Path -LiteralPath $target

        if ($sourceExists -and -not $targetExists) {
            def_EnsureDir -Path (Split-Path -Parent $target)

            if ($Row.content_hashed -eq $true) {
                $actualSourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()

                if ($actualSourceHash -ne [string]$Row.sha256) {
                    throw "Source hash changed after inventory."
                }
            }

            Move-Item -LiteralPath $source -Destination $target -Force -ErrorAction Stop
            $evidence.state = "ORIGINAL_TO_CONTENT_ADDRESSED_QUARANTINE"
            $evidence.success = $true
        }
        elseif (-not $sourceExists -and $targetExists) {
            $evidence.state = "ALREADY_QUARANTINED_IDEMPOTENT"
            $evidence.success = $true
        }
        elseif ($sourceExists -and $targetExists) {
            $evidence.state = "BOTH_EXIST_REVIEW_NO_DELETE"
            $evidence.success = $false
            $evidence.error = "Both source and target exist; no destructive action executed."
        }
        else {
            $evidence.state = "SOURCE_AND_TARGET_MISSING"
            $evidence.success = $false
            $evidence.error = "Neither source nor target exists."
        }

        if (Test-Path -LiteralPath $target) {
            $targetHashInfo = def_GetFileHashSafe -Path $target
            $evidence.target_sha256 = $targetHashInfo.hash

            if (
                $Row.content_hashed -eq $true -and
                -not [string]::IsNullOrWhiteSpace([string]$Row.sha256) -and
                $targetHashInfo.hash -ne [string]$Row.sha256
            ) {
                throw "Target hash verification failed."
            }
        }
    }
    catch {
        $evidence.success = $false
        $evidence.error = $_.Exception.Message

        if ([string]::IsNullOrWhiteSpace([string]$evidence.state)) {
            $evidence.state = "MOVE_ERROR_CAPTURED_NO_STALL"
        }
    }
    finally {
        $evidence.post_source_exists = Test-Path -LiteralPath $source
        $evidence.post_target_exists = Test-Path -LiteralPath $target
    }

    return [pscustomobject]$evidence
}

function def_ApplySafeOrganization {
    param([object[]]$InventoryRows)

    $candidates = @(
        $InventoryRows |
        Where-Object {
            $_.action -in @(
                "QUARANTINE_EXACT_DUPLICATE_NONCANONICAL",
                "QUARANTINE_DELETION_CANDIDATE"
            )
        }
    )

    if (-not $ApplySafeOrganization) {
        def_Narrate -Stage "ORGANIZE" -Message "Safe physical organization disabled; action plan only." -Level "WARN"
        return @()
    }

    def_Narrate -Stage "ORGANIZE" -Message ("Applying {0} deterministic hash-state quarantine actions." -f @($candidates).Count)

    $total = @($candidates).Count
    $index = 0

    foreach ($candidate in $candidates) {
        $index++
        def_Progress -Current $index -Total $total -Message ("Safe organization {0}/{1}: {2}" -f $index,$total,$candidate.name)

        $targetRoot = if ($candidate.action -eq "QUARANTINE_DELETION_CANDIDATE") {
            $DeletionQuarantineRoot
        }
        else {
            $OrganizationQuarantineRoot
        }

        $result = def_MoveHashState -Row $candidate -TargetRoot $targetRoot
        $script:MoveEvidence.Add($result)
    }

    return @($script:MoveEvidence.ToArray())
}

function def_WriteSubsystemBootstrap {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Subsystem,
        [Parameter(Mandatory)][string]$EntrypointPath,
        [Parameter(Mandatory)][string]$SupportiveListPath,
        [Parameter(Mandatory)][string]$StatusPath,
        [Parameter(Mandatory)][string]$TranscriptPath
    )

    $template = @'
#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$EntrypointPath = "__ENTRYPOINT__",
    [string]$SupportiveListPath = "__SUPPORTIVE_LIST__",
    [string]$StatusPath = "__STATUS__",
    [string]$TranscriptPath = "__TRANSCRIPT__"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function EnsureDir([string]$Value) {
    if (-not (Test-Path -LiteralPath $Value)) {
        New-Item -ItemType Directory -Path $Value -Force | Out-Null
    }
}

function WriteStatus(
    [string]$State,
    [bool]$Success,
    [string]$Message,
    [string]$ErrorText = ""
) {
    $payload = [ordered]@{
        subsystem = "__SUBSYSTEM__"
        state = $State
        success = $Success
        message = $Message
        error = $ErrorText
        pid = $PID
        timestamp = (Get-Date).ToString("o")
        entrypoint = $EntrypointPath
        supportive_list = $SupportiveListPath
    }

    $temp = "$StatusPath.tmp.$PID"
    $payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $temp -Encoding UTF8
    Move-Item -LiteralPath $temp -Destination $StatusPath -Force
}

EnsureDir (Split-Path -Parent $StatusPath)
EnsureDir (Split-Path -Parent $TranscriptPath)

try {
    try {
        Start-Transcript -LiteralPath $TranscriptPath -Append | Out-Null
    }
    catch {}

    WriteStatus -State "BOOTSTRAP_STARTED" -Success $true -Message "Bootstrap process started."

    if (-not (Test-Path -LiteralPath $SupportiveListPath)) {
        throw "Approved supportive list missing: $SupportiveListPath"
    }

    $modules = @(Get-Content -LiteralPath $SupportiveListPath -Raw -Encoding UTF8 | ConvertFrom-Json)
    $events = @()

    foreach ($module in $modules) {
        $modulePath = [string]$module.path
        $extension = [System.IO.Path]::GetExtension($modulePath).ToLowerInvariant()

        if (-not (Test-Path -LiteralPath $modulePath)) {
            throw "Supportive module missing: $modulePath"
        }

        if ($extension -in @(".psm1",".psd1")) {
            Import-Module -Name $modulePath -Force -ErrorAction Stop
            $events += [pscustomobject]@{
                path = $modulePath
                state = "IMPORTED_MODULE"
                success = $true
                error = ""
            }
        }
        elseif ($extension -eq ".ps1") {
            $text = Get-Content -LiteralPath $modulePath -Raw -Encoding UTF8
            $dynamicName = "VIA_SAFE_" +
                ([System.IO.Path]::GetFileNameWithoutExtension($modulePath) -replace '[^A-Za-z0-9_]','_') +
                "_" +
                ([guid]::NewGuid().ToString("N").Substring(0,8))

            $dynamicModule = New-Module -Name $dynamicName -ScriptBlock ([scriptblock]::Create($text))
            Import-Module -ModuleInfo $dynamicModule -Force -ErrorAction Stop

            $events += [pscustomobject]@{
                path = $modulePath
                state = "IMPORTED_SAFE_DYNAMIC_MODULE"
                success = $true
                error = ""
            }
        }
        else {
            $events += [pscustomobject]@{
                path = $modulePath
                state = "REGISTERED_ONLY_NOT_IMPORTABLE"
                success = $true
                error = ""
            }
        }
    }

    $eventPath = Join-Path (Split-Path -Parent $StatusPath) "__SUBSYSTEM___supportive_imports.v0134.json"
    $events | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $eventPath -Encoding UTF8

    WriteStatus -State "SUPPORTIVE_IMPORTED" -Success $true -Message ("Imported approved supportive modules: {0}" -f @($events).Count)

    if (-not (Test-Path -LiteralPath $EntrypointPath)) {
        throw "Entrypoint missing: $EntrypointPath"
    }

    $tokens = $null
    $errors = $null

    [System.Management.Automation.Language.Parser]::ParseFile(
        $EntrypointPath,
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null

    if (@($errors).Count -gt 0) {
        throw "Entrypoint AST failed: $([string]$errors[0].Message)"
    }

    WriteStatus -State "ENTRYPOINT_STARTED" -Success $true -Message "Canonical entrypoint invoked."

    Write-Host "def __SUBSYSTEM__ Supportive Modules : IMPORTED" -ForegroundColor Green
    Write-Host "def __SUBSYSTEM__ Entrypoint          : $EntrypointPath" -ForegroundColor Cyan

    & $EntrypointPath

    WriteStatus -State "COMPLETED" -Success $true -Message "Entrypoint returned without uncaught exception."
}
catch {
    WriteStatus -State "FAILED" -Success $false -Message "Bootstrap or runtime failed." -ErrorText $_.Exception.Message
    Write-Host "def __SUBSYSTEM__ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    try {
        Stop-Transcript | Out-Null
    }
    catch {}

    Write-Host "def __SUBSYSTEM__ child PowerShell remains open for operator review." -ForegroundColor Cyan
}
'@

    $content = $template.
        Replace("__ENTRYPOINT__",$EntrypointPath).
        Replace("__SUPPORTIVE_LIST__",$SupportiveListPath).
        Replace("__STATUS__",$StatusPath).
        Replace("__TRANSCRIPT__",$TranscriptPath).
        Replace("__SUBSYSTEM__",$Subsystem)

    Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
}

function def_DeployFileHashState {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )

    $row = [ordered]@{
        source = $Source
        destination = $Destination
        state = ""
        success = $false
        source_sha256 = ""
        destination_sha256 = ""
        backup_path = ""
        error = ""
    }

    try {
        if (-not (Test-Path -LiteralPath $Source)) {
            throw "Deployment source missing: $Source"
        }

        def_EnsureDir -Path (Split-Path -Parent $Destination)

        $sourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash.ToLowerInvariant()
        $row.source_sha256 = $sourceHash

        if (-not (Test-Path -LiteralPath $Destination)) {
            Copy-Item -LiteralPath $Source -Destination $Destination -Force
            $row.state = "ORIGINAL_TO_APPLY"
        }
        else {
            $destinationHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()

            if ($destinationHash -eq $sourceHash) {
                $row.state = "PROPOSED_ALREADY_APPLIED_SKIP"
                $row.destination_sha256 = $destinationHash
                $row.success = $true
                return [pscustomobject]$row
            }

            $backupPath = "{0}.backup.{1}.{2}" -f $Destination,(Get-Date -Format "yyyyMMdd_HHmmss"),$destinationHash.Substring(0,12)
            Copy-Item -LiteralPath $Destination -Destination $backupPath -Force
            $row.backup_path = $backupPath

            Copy-Item -LiteralPath $Source -Destination $Destination -Force
            $row.state = "OTHER_TO_BACKUP_APPLY"
        }

        $deployedHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
        $row.destination_sha256 = $deployedHash

        if ($deployedHash -ne $sourceHash) {
            throw "Deployment hash verification failed."
        }

        $row.success = $true
    }
    catch {
        $row.error = $_.Exception.Message

        if ([string]::IsNullOrWhiteSpace([string]$row.state)) {
            $row.state = "DEPLOY_ERROR"
        }
    }

    return [pscustomobject]$row
}

function def_NewEncodedCommand {
    param([Parameter(Mandatory)][string]$ScriptPath)

    $escaped = $ScriptPath.Replace("'","''")
    $command = "& '$escaped'"
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($command)
    return [Convert]::ToBase64String($bytes)
}

function def_StartSubsystemEncoded {
    param(
        [Parameter(Mandatory)][string]$Subsystem,
        [Parameter(Mandatory)][string]$BootstrapPath,
        [Parameter(Mandatory)][string]$StatusPath
    )

    $row = [ordered]@{
        subsystem = $Subsystem
        bootstrap = $BootstrapPath
        status_path = $StatusPath
        pid = 0
        process_state = ""
        child_state = ""
        success = $false
        error = ""
    }

    try {
        if (Test-Path -LiteralPath $StatusPath) {
            Remove-Item -LiteralPath $StatusPath -Force -ErrorAction SilentlyContinue
        }

        $pwsh = (Get-Command pwsh -ErrorAction Stop).Source
        $encoded = def_NewEncodedCommand -ScriptPath $BootstrapPath

        $process = Start-Process `
            -FilePath $pwsh `
            -ArgumentList @(
                "-NoLogo",
                "-NoProfile",
                "-NoExit",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                $encoded
            ) `
            -PassThru

        $row.pid = $process.Id

        Start-Sleep -Seconds $ActivationProbeSeconds

        $process.Refresh()
        $row.process_state = if ($process.HasExited) {
            "EXITED_$($process.ExitCode)"
        }
        else {
            "RUNNING_WINDOW"
        }

        if (Test-Path -LiteralPath $StatusPath) {
            try {
                $status = Get-Content -LiteralPath $StatusPath -Raw -Encoding UTF8 | ConvertFrom-Json
                $row.child_state = [string]$status.state

                if ([string]$status.state -eq "FAILED") {
                    $row.success = $false
                    $row.error = [string]$status.error
                }
                elseif ([string]$status.state -in @("BOOTSTRAP_STARTED","SUPPORTIVE_IMPORTED","ENTRYPOINT_STARTED","COMPLETED")) {
                    $row.success = $true
                }
                else {
                    $row.success = (-not $process.HasExited)
                }
            }
            catch {
                $row.child_state = "STATUS_PARSE_ERROR"
                $row.success = (-not $process.HasExited)
                $row.error = $_.Exception.Message
            }
        }
        else {
            $row.child_state = "STATUS_NOT_YET_WRITTEN"
            $row.success = (-not $process.HasExited)
        }
    }
    catch {
        $row.process_state = "START_ERROR"
        $row.child_state = "NOT_STARTED"
        $row.success = $false
        $row.error = $_.Exception.Message
    }

    return [pscustomobject]$row
}

function def_GetTaxonomy {
    return [ordered]@{
        version = $Version
        generated_at = (Get-Date).ToString("o")
        principle = "Logical numbering and registry are authoritative; existing canonical paths are preserved."
        logical_id_format = "VIA-<SECTION>-<SUBSYSTEM>-<SEQUENCE>-<SHA12>"
        sections = @(
            [ordered]@{code="MOD";name="MODULE";target="functional modules\<SUBSYSTEM>";physical_policy="KEEP_CANONICAL"},
            [ordered]@{code="ENG";name="ENGINE";target="supportive modules\engine\<SUBSYSTEM>";physical_policy="REGISTER_OR_SUGGEST"},
            [ordered]@{code="LIB";name="FUNCTION_LIB";target="supportive modules\function_lib";physical_policy="KEEP_APPROVED_IMPORTS"},
            [ordered]@{code="SST";name="SSOT";target="supportive modules\ssot";physical_policy="KEEP_CANONICAL"},
            [ordered]@{code="UIX";name="UI";target="supportive modules\ui_support";physical_policy="REGISTER_OR_SUGGEST"},
            [ordered]@{code="DOC";name="DOCUMENT";target="documents\<SUBSYSTEM>";physical_policy="REGISTER_OR_SUGGEST"},
            [ordered]@{code="DAT";name="DATA";target="data\<SUBSYSTEM>";physical_policy="REGISTER_OR_SUGGEST"},
            [ordered]@{code="EVD";name="EVIDENCE";target="_via_evidence_archive\<SUBSYSTEM>";physical_policy="APPEND_ONLY"},
            [ordered]@{code="QRN";name="QUARANTINE";target="_via_quarantine_registry";physical_policy="IMMUTABLE"},
            [ordered]@{code="OTH";name="OTHER";target="supportive modules\others";physical_policy="REGISTER_OR_SUGGEST"}
        )
        deletion_policy = [ordered]@{
            permanent_delete_default = $false
            zero_byte_disposable_files = "CONTENT_ADDRESSED_DELETION_QUARANTINE"
            exact_noncanonical_duplicates = "CONTENT_ADDRESSED_ORGANIZATION_QUARANTINE"
            ambiguous_files = "NO_MOVE_SUGGEST_TARGET_ONLY"
        }
    }
}

function def_HtmlEncode {
    param($Value)

    if ($null -eq $Value) {
        return ""
    }

    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_ToHtmlTable {
    param(
        $Rows,
        [int]$MaxRows = 1000
    )

    $array = @($Rows)

    if ($array.Count -eq 0) {
        return "<div class='empty'>No rows.</div>"
    }

    $properties = @($array[0].PSObject.Properties.Name)
    $sb = New-Object System.Text.StringBuilder

    [void]$sb.AppendLine("<div class='table-wrap'><table><thead><tr>")

    foreach ($property in $properties) {
        [void]$sb.AppendLine("<th>$(def_HtmlEncode $property)</th>")
    }

    [void]$sb.AppendLine("</tr></thead><tbody>")

    foreach ($row in @($array | Select-Object -First $MaxRows)) {
        [void]$sb.AppendLine("<tr>")

        foreach ($property in $properties) {
            $value = $row.$property
            [void]$sb.AppendLine("<td>$(def_HtmlEncode $value)</td>")
        }

        [void]$sb.AppendLine("</tr>")
    }

    [void]$sb.AppendLine("</tbody></table></div>")
    return $sb.ToString()
}

function def_WriteHtmlReport {
    param(
        [Parameter(Mandatory)]$Summary,
        [Parameter(Mandatory)]$Taxonomy,
        [Parameter(Mandatory)]$InventoryRows,
        [Parameter(Mandatory)]$MoveRows,
        [Parameter(Mandatory)]$ActivationRows,
        [Parameter(Mandatory)]$NarrationRows
    )

    $sectionSummary = @(
        $InventoryRows |
        Group-Object section |
        Sort-Object Name |
        ForEach-Object {
            [pscustomobject]@{
                section = $_.Name
                files = $_.Count
                bytes = [int64](($_.Group | Measure-Object size_bytes -Sum).Sum)
            }
        }
    )

    $actionSummary = @(
        $InventoryRows |
        Group-Object action |
        Sort-Object Name |
        ForEach-Object {
            [pscustomobject]@{
                action = $_.Name
                files = $_.Count
            }
        }
    )

    $inventoryPreview = @(
        $InventoryRows |
        Sort-Object section,subsystem,relative_path |
        Select-Object -First 1500
    )

    $css = @'
<style>
:root{
  --bg:#f7f8f6;
  --card:#ffffff;
  --line:#d8e2df;
  --text:#24312f;
  --muted:#63706d;
  --ok:#18794e;
  --warn:#9a6700;
  --bad:#b42318;
  --accent:#0f766e;
}
*{box-sizing:border-box}
body{
  margin:0;
  padding:22px;
  background:var(--bg);
  color:var(--text);
  font-family:Inter,"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;
  font-size:12px;
}
h1{font-size:24px;margin:0 0 5px}
h2{font-size:17px;margin-top:26px;border-left:5px solid var(--accent);padding-left:9px}
h3{font-size:14px}
.card{
  background:var(--card);
  border:1px solid var(--line);
  border-radius:13px;
  padding:14px;
  margin:12px 0;
  box-shadow:0 8px 24px rgba(20,40,35,.05);
}
.grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:9px;
}
.metric{
  border:1px solid var(--line);
  border-radius:10px;
  padding:10px;
  min-height:72px;
}
.k{font-size:10px;color:var(--muted);text-transform:uppercase}
.v{font-size:16px;font-weight:800;margin-top:4px;overflow-wrap:anywhere}
.ok{color:var(--ok)}
.warn{color:var(--warn)}
.bad{color:var(--bad)}
.table-wrap{
  width:100%;
  overflow:auto;
  max-height:620px;
  border:1px solid var(--line);
  border-radius:9px;
}
table{
  width:100%;
  border-collapse:collapse;
  table-layout:auto;
  font-size:10.5px;
}
th{
  position:sticky;
  top:0;
  z-index:2;
  background:#e7efed;
  text-align:left;
  padding:6px;
  border:1px solid #d2dfdc;
  white-space:normal;
}
td{
  padding:5px 6px;
  border:1px solid #e2eae8;
  vertical-align:top;
  white-space:normal;
  overflow-wrap:anywhere;
  word-break:break-word;
  max-width:460px;
}
tr:nth-child(even){background:#fbfcfb}
.code{
  font-family:Consolas,"Cascadia Mono",monospace;
  white-space:pre-wrap;
  overflow-wrap:anywhere;
}
.empty{padding:14px;color:var(--muted)}
.small{font-size:10px;color:var(--muted)}
</style>
'@

    $gateClass = if ($Summary.gate -eq "FULL_ACTIVATION_SUCCESS") {
        "ok"
    }
    elseif ($Summary.gate -eq "ORGANIZATION_COMPLETE_ACTIVATION_REVIEW") {
        "warn"
    }
    else {
        "bad"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>VIA Governance Organization Activation v0134</title>
$css
</head>
<body>
<h1>VIA · Governance Organization / Integration / Activation · v0134</h1>
<div class="small">Generated: $(def_HtmlEncode $Summary.generated_at) · No permanent deletion · No broad canonical rename · EncodedCommand activation</div>

<div class="card">
  <div class="grid">
    <div class="metric"><div class="k">Gate</div><div class="v $gateClass">$(def_HtmlEncode $Summary.gate)</div></div>
    <div class="metric"><div class="k">Risk</div><div class="v">$(def_HtmlEncode $Summary.risk)</div></div>
    <div class="metric"><div class="k">Registered Files</div><div class="v">$($Summary.registered_files)</div></div>
    <div class="metric"><div class="k">Physical Moves</div><div class="v">$($Summary.organization_moved)</div></div>
    <div class="metric"><div class="k">Move Fail</div><div class="v">$($Summary.organization_fail)</div></div>
    <div class="metric"><div class="k">VRN</div><div class="v">$(def_HtmlEncode $Summary.vrn_activation)</div></div>
    <div class="metric"><div class="k">VDF</div><div class="v">$(def_HtmlEncode $Summary.vdf_activation)</div></div>
    <div class="metric"><div class="k">Permanent Delete</div><div class="v">NOT EXECUTED</div></div>
  </div>
</div>

<h2>Decision</h2>
<div class="card code">$(def_HtmlEncode $Summary.decision)

Next: $(def_HtmlEncode $Summary.next_step)</div>

<h2>Folder Taxonomy</h2>
<div class="card">$(def_ToHtmlTable -Rows $Taxonomy.sections -MaxRows 100)</div>

<h2>Section Summary</h2>
<div class="card">$(def_ToHtmlTable -Rows $sectionSummary -MaxRows 100)</div>

<h2>Action Summary</h2>
<div class="card">$(def_ToHtmlTable -Rows $actionSummary -MaxRows 100)</div>

<h2>Organization Move Evidence</h2>
<div class="card">$(def_ToHtmlTable -Rows $MoveRows -MaxRows 1000)</div>

<h2>VRN / VDF Activation Evidence</h2>
<div class="card">$(def_ToHtmlTable -Rows $ActivationRows -MaxRows 100)</div>

<h2>File Registry Preview</h2>
<div class="card">$(def_ToHtmlTable -Rows $inventoryPreview -MaxRows 1500)</div>

<h2>Dynamic Status Narration</h2>
<div class="card">$(def_ToHtmlTable -Rows $NarrationRows -MaxRows 1000)</div>

<h2>Output Paths</h2>
<div class="card code">
RunDir: $(def_HtmlEncode $Summary.run_dir)
PersistentGovernanceDir: $(def_HtmlEncode $Summary.persistent_governance_dir)
InventoryCsv: $(def_HtmlEncode $InventoryCsv)
ActionCsv: $(def_HtmlEncode $ActionCsv)
MoveEvidenceCsv: $(def_HtmlEncode $MoveEvidenceCsv)
ActivationEvidenceCsv: $(def_HtmlEncode $ActivationEvidenceCsv)
HTML: $(def_HtmlEncode $ReportHtml)
OrganizationQuarantine: $(def_HtmlEncode $OrganizationQuarantineRoot)
DeletionCandidatesQuarantine: $(def_HtmlEncode $DeletionQuarantineRoot)
</div>
</body>
</html>
"@

    def_EnsureDir -Path (Split-Path -Parent $ReportHtml)
    Set-Content -LiteralPath $ReportHtml -Value $html -Encoding UTF8
}

function def_Main {
    def_Banner -Title "VIA · GOVERNANCE ORGANIZE / REGISTER / INTEGRATE / ACTIVATE v0134"

    if (-not (Test-Path -LiteralPath $BaseDir)) {
        throw "BaseDir does not exist: $BaseDir"
    }

    if ($ApprovalPhrase -ne $ExpectedApprovalPhrase) {
        throw "Approval phrase mismatch. No physical organization or activation executed."
    }

    foreach ($dir in @(
        $RunDir,
        $CsvDir,
        $JsonDir,
        $HtmlDir,
        $LogDir,
        $CandidateDir,
        $PersistentGovernanceDir,
        $PersistentRegistryDir,
        $PersistentLauncherDir,
        $PersistentHtmlDir,
        $PersistentLogDir,
        $PersistentManifestDir,
        $OrganizationQuarantineRoot,
        $DeletionQuarantineRoot
    )) {
        def_EnsureDir -Path $dir
    }

    def_Narrate -Stage "BOOT" -Message "v0134 started; parent process will remain non-blocking and no permanent delete is allowed."
    def_Narrate -Stage "V0133" -Message "Locating clean v0133 gate and approved supportive module set."

    $v0133Gate = def_FindLatestV0133Gate

    if ($null -eq $v0133Gate) {
        throw "No FULL_ACTIVATION_ELIGIBLE v0133 gate found."
    }

    $supportiveListSource = def_FindApprovedSupportiveList

    if ([string]::IsNullOrWhiteSpace($supportiveListSource) -or -not (Test-Path -LiteralPath $supportiveListSource)) {
        throw "v0133-approved supportive module list not found."
    }

    $approvedSupportivePaths = @(def_GetApprovedSupportivePaths -SupportiveListPath $supportiveListSource)

    if (@($approvedSupportivePaths).Count -eq 0) {
        throw "Approved supportive module list is empty."
    }

    def_Narrate -Stage "V0133" -Message ("Gate clean; approved supportive modules: {0}" -f @($approvedSupportivePaths).Count) -Level "OK"

    $inventory = @(def_BuildInventory -ApprovedSupportivePaths $approvedSupportivePaths)
    $inventory = @(def_ClassifyOrganizationActions -InventoryRows $inventory)

    $taxonomy = def_GetTaxonomy

    def_Narrate -Stage "REGISTER" -Message ("Writing logical IDs and registry for {0} files." -f @($inventory).Count)

    def_WriteCsv -Data $inventory -Path $InventoryCsv
    def_WriteJson -Data $inventory -Path $InventoryJson
    def_WriteJson -Data $taxonomy -Path $TaxonomyJson

    $actions = @(
        $inventory |
        Where-Object { $_.action -ne "REGISTER_ONLY" } |
        Select-Object logical_id,action,action_reason,section,subsystem,relative_path,full_path,keeper_path,suggested_target_folder,sha256,size_bytes
    )

    def_WriteCsv -Data $actions -Path $ActionCsv
    def_WriteJson -Data $actions -Path $ActionJson

    $moveRows = @(def_ApplySafeOrganization -InventoryRows $inventory)

    def_WriteCsv -Data $moveRows -Path $MoveEvidenceCsv
    def_WriteJson -Data $moveRows -Path $MoveEvidenceJson

    $moveSuccess = @($moveRows | Where-Object { $_.success -eq $true -or $_.success -eq "True" }).Count
    $moveFail = @($moveRows | Where-Object { -not ($_.success -eq $true -or $_.success -eq "True") }).Count

    def_Narrate -Stage "INTEGRATE" -Message "Deploying registry, taxonomy and manifests into VIA_Governance_Runtime v0134."

    $supportiveRows = @(Get-Content -LiteralPath $supportiveListSource -Raw -Encoding UTF8 | ConvertFrom-Json)
    def_WriteJson -Data $supportiveRows -Path $SupportiveListCandidate

    $vrnEntrypoint = Join-Path $BaseDir "functional modules\VRN\Invoke-VRN.ps1"
    $vdfEntrypoint = Join-Path $BaseDir "functional modules\VDF\Invoke-VDF.ps1"

    $vrnCheck = if (Test-Path -LiteralPath $vrnEntrypoint) {
        def_TestPowerShellFile -Path $vrnEntrypoint
    }
    else {
        [pscustomobject]@{parse_ok=$false;error_count=1;first_error="Missing"}
    }

    $vdfCheck = if (Test-Path -LiteralPath $vdfEntrypoint) {
        def_TestPowerShellFile -Path $vdfEntrypoint
    }
    else {
        [pscustomobject]@{parse_ok=$false;error_count=1;first_error="Missing"}
    }

    def_WriteSubsystemBootstrap `
        -Path $VrnBootstrapCandidate `
        -Subsystem "VRN" `
        -EntrypointPath $vrnEntrypoint `
        -SupportiveListPath $SupportiveListDeployed `
        -StatusPath $VrnStatusPath `
        -TranscriptPath (Join-Path $PersistentLogDir "VRN_transcript.v0134.txt")

    def_WriteSubsystemBootstrap `
        -Path $VdfBootstrapCandidate `
        -Subsystem "VDF" `
        -EntrypointPath $vdfEntrypoint `
        -SupportiveListPath $SupportiveListDeployed `
        -StatusPath $VdfStatusPath `
        -TranscriptPath (Join-Path $PersistentLogDir "VDF_transcript.v0134.txt")

    $vrnBootstrapCheck = def_TestPowerShellFile -Path $VrnBootstrapCandidate
    $vdfBootstrapCheck = def_TestPowerShellFile -Path $VdfBootstrapCandidate

    $activationManifest = [ordered]@{
        version = $Version
        generated_at = (Get-Date).ToString("o")
        source_gate = $v0133Gate.path
        source_gate_value = [string]$v0133Gate.data.gate
        approved_supportive_list_source = $supportiveListSource
        approved_supportive_count = @($supportiveRows).Count
        vrn_entrypoint = $vrnEntrypoint
        vdf_entrypoint = $vdfEntrypoint
        vrn_entrypoint_parse_ok = $vrnCheck.parse_ok
        vdf_entrypoint_parse_ok = $vdfCheck.parse_ok
        vrn_bootstrap_parse_ok = $vrnBootstrapCheck.parse_ok
        vdf_bootstrap_parse_ok = $vdfBootstrapCheck.parse_ok
        activation_transport = "POWERSHELL_ENCODED_COMMAND_PATH_SAFE"
        policy = [ordered]@{
            no_stop_process = $true
            no_permanent_delete = $true
            no_broad_canonical_move = $true
            supportive_import_before_entrypoint = $true
            child_status_json_required = $true
        }
    }

    def_WriteJson -Data $activationManifest -Path $ActivationManifestCandidate

    $deployPlan = @(
        [pscustomobject]@{source=$InventoryJson;destination=(Join-Path $PersistentRegistryDir "VIA_FileRegistry.v0134.json")},
        [pscustomobject]@{source=$InventoryCsv;destination=(Join-Path $PersistentRegistryDir "VIA_FileRegistry.v0134.csv")},
        [pscustomobject]@{source=$TaxonomyJson;destination=(Join-Path $PersistentRegistryDir "VIA_FolderTaxonomy.v0134.json")},
        [pscustomobject]@{source=$ActionJson;destination=(Join-Path $PersistentRegistryDir "VIA_OrganizationActions.v0134.json")},
        [pscustomobject]@{source=$ActionCsv;destination=(Join-Path $PersistentRegistryDir "VIA_OrganizationActions.v0134.csv")},
        [pscustomobject]@{source=$SupportiveListCandidate;destination=$SupportiveListDeployed},
        [pscustomobject]@{source=$ActivationManifestCandidate;destination=$ActivationManifestDeployed},
        [pscustomobject]@{source=$VrnBootstrapCandidate;destination=$VrnBootstrapDeployed},
        [pscustomobject]@{source=$VdfBootstrapCandidate;destination=$VdfBootstrapDeployed}
    )

    $deployRows = @()

    foreach ($item in $deployPlan) {
        $deployResult = def_DeployFileHashState -Source $item.source -Destination $item.destination
        $deployRows += $deployResult
        $script:ActivationEvidence.Add($deployResult)
    }

    $deployFail = @($deployRows | Where-Object { -not ($_.success -eq $true -or $_.success -eq "True") }).Count

    $activationEligible = (
        [string]$v0133Gate.data.gate -eq "FULL_ACTIVATION_ELIGIBLE" -and
        $vrnCheck.parse_ok -and
        $vdfCheck.parse_ok -and
        $vrnBootstrapCheck.parse_ok -and
        $vdfBootstrapCheck.parse_ok -and
        $deployFail -eq 0 -and
        @($supportiveRows).Count -gt 0
    )

    $vrnActivation = "NOT_EXECUTED"
    $vdfActivation = "NOT_EXECUTED"

    if ($activationEligible -and $ActivateVrnVdf) {
        def_Narrate -Stage "ACTIVATE" -Message "Starting VRN and VDF with EncodedCommand and child status evidence."

        $vrnStart = def_StartSubsystemEncoded `
            -Subsystem "VRN" `
            -BootstrapPath $VrnBootstrapDeployed `
            -StatusPath $VrnStatusPath

        $script:ActivationEvidence.Add($vrnStart)

        $vdfStart = def_StartSubsystemEncoded `
            -Subsystem "VDF" `
            -BootstrapPath $VdfBootstrapDeployed `
            -StatusPath $VdfStatusPath

        $script:ActivationEvidence.Add($vdfStart)

        $vrnActivation = "{0}/{1}" -f $vrnStart.process_state,$vrnStart.child_state
        $vdfActivation = "{0}/{1}" -f $vdfStart.process_state,$vdfStart.child_state

        if ($vrnStart.success) {
            def_Narrate -Stage "VRN" -Message ("VRN activation evidence: {0}" -f $vrnActivation) -Level "OK"
        }
        else {
            def_Narrate -Stage "VRN" -Message ("VRN activation failed: {0}" -f $vrnStart.error) -Level "ERROR"
        }

        if ($vdfStart.success) {
            def_Narrate -Stage "VDF" -Message ("VDF activation evidence: {0}" -f $vdfActivation) -Level "OK"
        }
        else {
            def_Narrate -Stage "VDF" -Message ("VDF activation failed: {0}" -f $vdfStart.error) -Level "ERROR"
        }
    }
    elseif ($activationEligible) {
        $vrnActivation = "ELIGIBLE_NOT_REQUESTED"
        $vdfActivation = "ELIGIBLE_NOT_REQUESTED"
        def_Narrate -Stage "ACTIVATE" -Message "Activation gate is clean but activation parameter is disabled." -Level "WARN"
    }
    else {
        def_Narrate -Stage "ACTIVATE" -Message "Activation blocked by v0134 live gate; no bypass executed." -Level "ERROR"
    }

    $activationRows = @($script:ActivationEvidence.ToArray())

    def_WriteCsv -Data $activationRows -Path $ActivationEvidenceCsv
    def_WriteJson -Data $activationRows -Path $ActivationEvidenceJson

    $activationFailures = @(
        $activationRows |
        Where-Object {
            $_.PSObject.Properties.Name -contains "success" -and
            -not ($_.success -eq $true -or $_.success -eq "True")
        }
    ).Count

    $vrnGood = $vrnActivation -notmatch "FAILED|EXITED_|NOT_EXECUTED|NOT_STARTED|START_ERROR"
    $vdfGood = $vdfActivation -notmatch "FAILED|EXITED_|NOT_EXECUTED|NOT_STARTED|START_ERROR"

    $gate = "BLOCKED_REVIEW_REQUIRED"
    $risk = "HIGH"
    $decision = "Governance evidence generated, but activation or deployment blockers remain."
    $nextStep = "Review move and activation evidence; no forced bypass."

    if ($activationEligible -and $ActivateVrnVdf -and $vrnGood -and $vdfGood -and $activationFailures -eq 0 -and $moveFail -eq 0) {
        $gate = "FULL_ACTIVATION_SUCCESS"
        $risk = "LOW_CONTROLLED_WITH_HYDRA_MONITORING"
        $decision = "VIA files were logically numbered and registered; deterministic cleanup candidates were quarantined; VRN and VDF started through path-safe EncodedCommand launchers."
        $nextStep = "Use the v0134 HTML matrix and child status/transcript logs for ongoing operations."
    }
    elseif ($activationEligible -and $moveFail -eq 0) {
        $gate = "ORGANIZATION_COMPLETE_ACTIVATION_REVIEW"
        $risk = "MEDIUM_REVIEW"
        $decision = "Folder governance and registration completed; activation requires review of child status evidence."
        $nextStep = "Inspect VRN/VDF status JSON and transcript logs; do not repeat broad folder scans."
    }

    $summary = [ordered]@{
        version = $Version
        generated_at = (Get-Date).ToString("o")
        gate = $gate
        risk = $risk
        decision = $decision
        next_step = $nextStep

        v0133_gate_path = $v0133Gate.path
        v0133_gate = [string]$v0133Gate.data.gate
        supportive_list_source = $supportiveListSource
        supportive_approved = @($supportiveRows).Count

        registered_files = @($inventory).Count
        organization_candidates = @(
            $inventory |
            Where-Object {
                $_.action -in @(
                    "QUARANTINE_EXACT_DUPLICATE_NONCANONICAL",
                    "QUARANTINE_DELETION_CANDIDATE"
                )
            }
        ).Count
        organization_moved = $moveSuccess
        organization_fail = $moveFail
        permanent_delete = "NOT_EXECUTED"

        vrn_entrypoint = $vrnEntrypoint
        vdf_entrypoint = $vdfEntrypoint
        vrn_activation = $vrnActivation
        vdf_activation = $vdfActivation
        activation_failures = $activationFailures

        run_dir = $RunDir
        persistent_governance_dir = $PersistentGovernanceDir
        organization_quarantine_root = $OrganizationQuarantineRoot
        deletion_candidates_quarantine_root = $DeletionQuarantineRoot
        inventory_csv = $InventoryCsv
        action_csv = $ActionCsv
        move_evidence_csv = $MoveEvidenceCsv
        activation_evidence_csv = $ActivationEvidenceCsv
        html = $ReportHtml
        vrn_status = $VrnStatusPath
        vdf_status = $VdfStatusPath
    }

    def_WriteJson -Data $summary -Path $SummaryJson
    def_WriteJson -Data $summary -Path $GateJson

    def_WriteHtmlReport `
        -Summary ([pscustomobject]$summary) `
        -Taxonomy ([pscustomobject]$taxonomy) `
        -InventoryRows $inventory `
        -MoveRows $moveRows `
        -ActivationRows $activationRows `
        -NarrationRows @($script:Narration.ToArray())

    $htmlDeploy = def_DeployFileHashState `
        -Source $ReportHtml `
        -Destination (Join-Path $PersistentHtmlDir (Split-Path -Leaf $ReportHtml))

    $script:ActivationEvidence.Add($htmlDeploy)
    $activationRows = @($script:ActivationEvidence.ToArray())

    def_WriteCsv -Data $activationRows -Path $ActivationEvidenceCsv
    def_WriteJson -Data $activationRows -Path $ActivationEvidenceJson

    if ($OpenHtmlReport -and (Test-Path -LiteralPath $ReportHtml)) {
        Start-Process -FilePath $ReportHtml
    }

    def_Banner -Title "VIA · v0134 FINAL RESULT"

    Write-Host ("def Gate                    : {0}" -f $summary.gate) -ForegroundColor Cyan
    Write-Host ("def Risk                    : {0}" -f $summary.risk) -ForegroundColor Yellow
    Write-Host ("def RegisteredFiles         : {0}" -f $summary.registered_files) -ForegroundColor White
    Write-Host ("def OrganizationCandidates  : {0}" -f $summary.organization_candidates) -ForegroundColor White
    Write-Host ("def OrganizationMoved       : {0}" -f $summary.organization_moved) -ForegroundColor Green
    Write-Host ("def OrganizationFail        : {0}" -f $summary.organization_fail) -ForegroundColor Red
    Write-Host ("def PermanentDelete         : NOT_EXECUTED") -ForegroundColor Yellow
    Write-Host ("def SupportiveApproved      : {0}" -f $summary.supportive_approved) -ForegroundColor Green
    Write-Host ("def VRNActivation           : {0}" -f $summary.vrn_activation) -ForegroundColor Green
    Write-Host ("def VDFActivation           : {0}" -f $summary.vdf_activation) -ForegroundColor Green
    Write-Host ("def RunDir                  : {0}" -f $summary.run_dir) -ForegroundColor Cyan
    Write-Host ("def GovernanceRuntime       : {0}" -f $summary.persistent_governance_dir) -ForegroundColor Cyan
    Write-Host ("def VRNStatus               : {0}" -f $summary.vrn_status) -ForegroundColor Cyan
    Write-Host ("def VDFStatus               : {0}" -f $summary.vdf_status) -ForegroundColor Cyan
    Write-Host ("def HTML                    : {0}" -f $summary.html) -ForegroundColor Green
}

try {
    def_Main
}
catch {
    def_Banner -Title "VIA · v0134 OUTER SAFE CATCH"

    Write-Host ("def ErrorType    : {0}" -f $_.Exception.GetType().FullName) -ForegroundColor Red
    Write-Host ("def ErrorMessage : {0}" -f $_.Exception.Message) -ForegroundColor Red
    Write-Host ("def StackTrace   : {0}" -f $_.ScriptStackTrace) -ForegroundColor DarkRed
    Write-Host ("def RunDir       : {0}" -f $RunDir) -ForegroundColor Cyan
    Write-Host "def No forced activation or permanent deletion was executed after the captured failure." -ForegroundColor Yellow

    try {
        $fallback = [ordered]@{
            version = $Version
            generated_at = (Get-Date).ToString("o")
            gate = "OUTER_SAFE_CATCH"
            risk = "HIGH_REVIEW"
            error_type = $_.Exception.GetType().FullName
            error_message = $_.Exception.Message
            stack_trace = $_.ScriptStackTrace
            run_dir = $RunDir
            permanent_delete = "NOT_EXECUTED"
        }

        def_WriteJson -Data $fallback -Path $SummaryJson
    }
    catch {}
}
finally {
    if ($KeepParentPowerShellOpen) {
        Write-Host ""
        Write-Host "def Parent PowerShell remains open. No Stop-Process and no permanent deletion were used." -ForegroundColor Cyan
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
