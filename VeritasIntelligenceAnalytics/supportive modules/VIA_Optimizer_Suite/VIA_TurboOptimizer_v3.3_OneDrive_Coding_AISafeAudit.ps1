#requires -Version 7.0
param(
    [string[]]$ScanRoots = @(),
    [string]$OutputRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_disk_audit",
    [int]$MinLargeMB = 20,
    [int]$RecentDays = 7,
    [int]$TopN = 300,
    [int]$MaxFiles = 300000,
    [switch]$SkipHashConfirm,
    [switch]$GenerateOneDriveFreeUpHelper,
    [switch]$OpenReport,
    [switch]$SelfTest
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

# =============================================================================
# def VIA Turbo Optimizer v3.3 · OneDrive / Downloads / Coding / AI Safe Audit
# =============================================================================
# def Policy
# - No file deletion.
# - No permanent deletion.
# - No recycle-bin clearing.
# - No system folder mutation.
# - No coding-setting deletion: .git / .vscode / VS Code User / Chrome / Edge /
#   node_modules / venv / envs / site-packages are protected.
# - OneDrive online-only cloud placeholders are skipped, so the scan will not
#   force-download cloud files.
# - Duplicate detection uses size + extension as candidates, then SHA256 when
#   enabled. Reports only; no deletion.
# - Optional OneDrive helper only generates an explicit script. It does not run
#   unless the user manually runs helper with -Execute.
# =============================================================================

$ErrorActionPreference = "Continue"

# =============================================================================
# def PARAMETERS AND CONSTANTS
# =============================================================================

$script:RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$script:RunDir = Join-Path $OutputRoot ("RUN_" + $script:RunStamp + "_SAFEAUDIT_v33")
$script:LogFile = Join-Path $script:RunDir "VIA_SafeAudit_Log.txt"

$script:MinLargeBytes = [int64]$MinLargeMB * 1MB
$script:CutoffRecent = (Get-Date).AddDays(-[math]::Abs($RecentDays))

$script:CloudAttrOffline = [int]([System.IO.FileAttributes]::Offline)
$script:CloudAttrRecallOnOpen = 0x00040000
$script:CloudAttrPinned = 0x00080000
$script:CloudAttrUnpinned = 0x00100000
$script:CloudAttrRecallOnDataAccess = 0x00400000

$script:SystemDenyRoots = @(
    $env:SystemRoot,
    ($env:SystemDrive + "\Program Files"),
    ($env:SystemDrive + "\Program Files (x86)"),
    ($env:SystemDrive + "\ProgramData"),
    ($env:SystemDrive + "\System Volume Information"),
    ($env:SystemDrive + '\$Recycle.Bin')
) | Where-Object { $_ } | ForEach-Object { ([System.IO.Path]::GetFullPath($_)).TrimEnd("\").ToLowerInvariant() } | Select-Object -Unique

$script:ProtectedFragments = @(
    "\.git\",
    "\.svn\",
    "\.hg\",
    "\.vscode\",
    "\code\user\",
    "\microsoft vs code\",
    "\google\chrome\user data\",
    "\microsoft\edge\user data\",
    "\bravesoftware\brave-browser\user data\",
    "\mozilla\firefox\profiles\",
    "\node_modules\",
    "\site-packages\",
    "\.venv\",
    "\venv\",
    "\envs\",
    "\anaconda3\",
    "\miniconda3\",
    "\onedrivetemp\",
    "\$recycle.bin\"
) | ForEach-Object { $_.ToLowerInvariant() }

$script:CodingAIFragments = @(
    "\__pycache__\",
    "\.pytest_cache\",
    "\.mypy_cache\",
    "\.ruff_cache\",
    "\.tox\",
    "\.ipynb_checkpoints\",
    "\.cache\",
    "\pip\cache\",
    "\pip\cache\wheels\",
    "\uv\cache\",
    "\npm-cache\",
    "\.npm\",
    "\.pnpm-store\",
    "\.yarn\",
    "\dist\",
    "\build\",
    "\target\",
    "\logs\",
    "\log\",
    "\tmp\",
    "\temp\",
    "\crashdumps\",
    "\huggingface\",
    "\torch\",
    "\transformers\",
    "\.ollama\",
    "\lm studio\",
    "\comfyui\",
    "\stable-diffusion\",
    "\models\",
    "\checkpoints\",
    "\veritasintelligenceanalytics\_disk_audit\",
    "\veritasintelligenceanalytics\_pack_runs\",
    "\veritasintelligenceanalytics\_sealed",
    "\veritasintelligenceanalytics\_reports\",
    "\veritasintelligenceanalytics\_runtime",
    "\veritasintelligenceanalytics\_debug"
) | ForEach-Object { $_.ToLowerInvariant() }

$script:CodingAIExtensions = @(
    ".log", ".tmp", ".temp", ".cache", ".bak", ".old",
    ".zip", ".7z", ".rar",
    ".csv", ".json", ".jsonl", ".html", ".htm",
    ".parquet", ".duckdb", ".db", ".sqlite", ".sqlite3",
    ".ipynb", ".pkl", ".pickle",
    ".bin", ".onnx", ".safetensors", ".pt", ".pth", ".ckpt", ".gguf",
    ".nupkg", ".whl"
)

# =============================================================================
# def LOGGING
# =============================================================================

function def_WriteLog {
    param(
        [string]$Level,
        [string]$Message
    )

    try {
        if (-not (Test-Path -LiteralPath $script:RunDir)) {
            New-Item -ItemType Directory -Path $script:RunDir -Force | Out-Null
        }

        $line = "{0} | {1,-7} | {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"), $Level, $Message
        [System.IO.File]::AppendAllText($script:LogFile, $line + [Environment]::NewLine, [System.Text.Encoding]::UTF8)
        Write-Host $line
    }
    catch {
        Write-Host ("LOG_FAIL | " + $Message)
    }
}

# =============================================================================
# def PATH SAFETY
# =============================================================================

function def_NormalizePath {
    param(
        [string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }

    try {
        return ([System.IO.Path]::GetFullPath($Path)).TrimEnd("\")
    }
    catch {
        return $null
    }
}

function def_TestUnderRoot {
    param(
        [string]$Path,
        [string]$Root
    )

    $p = def_NormalizePath -Path $Path
    $r = def_NormalizePath -Path $Root

    if (-not $p -or -not $r) {
        return $false
    }

    $pl = $p.ToLowerInvariant()
    $rl = $r.ToLowerInvariant()

    return ($pl -eq $rl -or $pl.StartsWith($rl + "\"))
}

function def_TestSystemDenied {
    param(
        [string]$Path
    )

    $p = def_NormalizePath -Path $Path
    if (-not $p) {
        return $true
    }

    $low = $p.ToLowerInvariant()

    foreach ($deny in $script:SystemDenyRoots) {
        if ($low -eq $deny -or $low.StartsWith($deny + "\")) {
            return $true
        }
    }

    return $false
}

function def_TestProtectedCodingSettingPath {
    param(
        [string]$Path
    )

    $p = def_NormalizePath -Path $Path
    if (-not $p) {
        return $true
    }

    $low = ($p.ToLowerInvariant() + "\")
    foreach ($frag in $script:ProtectedFragments) {
        if ($low.Contains($frag)) {
            return $true
        }
    }

    return $false
}

function def_TestReparsePoint {
    param(
        [string]$Path
    )

    try {
        $attr = [System.IO.File]::GetAttributes($Path)
        return (($attr -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
    }
    catch {
        return $true
    }
}

function def_GetCloudFlags {
    param(
        [string]$Path
    )

    $flags = [ordered]@{
        IsOfflinePlaceholder = $false
        IsRecallOnOpen = $false
        IsPinned = $false
        IsUnpinned = $false
        IsRecallOnDataAccess = $false
        AttrInt = 0
        AttrText = ""
    }

    try {
        $attr = [System.IO.File]::GetAttributes($Path)
        $ai = [int]$attr
        $flags.AttrInt = $ai
        $flags.AttrText = [string]$attr
        $flags.IsOfflinePlaceholder = (($ai -band $script:CloudAttrOffline) -ne 0)
        $flags.IsRecallOnOpen = (($ai -band $script:CloudAttrRecallOnOpen) -ne 0)
        $flags.IsPinned = (($ai -band $script:CloudAttrPinned) -ne 0)
        $flags.IsUnpinned = (($ai -band $script:CloudAttrUnpinned) -ne 0)
        $flags.IsRecallOnDataAccess = (($ai -band $script:CloudAttrRecallOnDataAccess) -ne 0)
    }
    catch {}

    return [pscustomobject]$flags
}

function def_TestCloudOnlineOnlyOrRecall {
    param(
        [string]$Path
    )

    $flags = def_GetCloudFlags -Path $Path
    if ($flags.IsOfflinePlaceholder -or $flags.IsRecallOnOpen -or $flags.IsRecallOnDataAccess) {
        return $true
    }

    return $false
}

# =============================================================================
# def ROOT DISCOVERY
# =============================================================================

function def_AddExistingRoot {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$Key,
        [string]$Desc,
        [string]$Path,
        [string]$Class
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return
    }

    $norm = def_NormalizePath -Path $Path
    if (-not $norm) {
        return
    }

    if (-not (Test-Path -LiteralPath $norm)) {
        return
    }

    if (def_TestSystemDenied -Path $norm) {
        return
    }

    $already = $false
    foreach ($r in $Rows) {
        if ((def_NormalizePath -Path $r.Path).ToLowerInvariant() -eq $norm.ToLowerInvariant()) {
            $already = $true
            break
        }
    }

    if (-not $already) {
        $Rows.Add([pscustomobject]@{
            Key = $Key
            Desc = $Desc
            Path = $norm
            Class = $Class
        }) | Out-Null
    }
}

function def_GetDefaultScanRoots {
    $rows = [System.Collections.Generic.List[object]]::new()

    def_AddExistingRoot -Rows $rows -Key "Downloads" -Desc "使用者 Downloads" -Path (Join-Path $env:USERPROFILE "Downloads") -Class "DOWNLOAD"
    def_AddExistingRoot -Rows $rows -Key "Desktop" -Desc "使用者 Desktop" -Path (Join-Path $env:USERPROFILE "Desktop") -Class "DESKTOP"
    def_AddExistingRoot -Rows $rows -Key "Documents" -Desc "使用者 Documents" -Path (Join-Path $env:USERPROFILE "Documents") -Class "DOCUMENTS"
    def_AddExistingRoot -Rows $rows -Key "Public" -Desc "Windows Public 使用者公用檔案" -Path $env:PUBLIC -Class "PUBLIC"

    $oneDriveRoots = @(
        $env:OneDrive,
        $env:OneDriveConsumer,
        $env:OneDriveCommercial
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique

    foreach ($od in $oneDriveRoots) {
        def_AddExistingRoot -Rows $rows -Key "OneDriveRoot" -Desc "OneDrive Root" -Path $od -Class "ONEDRIVE"
        def_AddExistingRoot -Rows $rows -Key "OneDriveDesktop" -Desc "OneDrive Desktop" -Path (Join-Path $od "Desktop") -Class "ONEDRIVE_DESKTOP"
        def_AddExistingRoot -Rows $rows -Key "OneDriveDocuments" -Desc "OneDrive Documents" -Path (Join-Path $od "Documents") -Class "ONEDRIVE_DOCUMENTS"
        def_AddExistingRoot -Rows $rows -Key "OneDrivePictures" -Desc "OneDrive Pictures" -Path (Join-Path $od "Pictures") -Class "ONEDRIVE_PICTURES"
        def_AddExistingRoot -Rows $rows -Key "OneDrivePublic" -Desc "OneDrive Public/Public-like folders" -Path (Join-Path $od "Public") -Class "ONEDRIVE_PUBLIC"
        def_AddExistingRoot -Rows $rows -Key "OneDriveShared" -Desc "OneDrive Shared/Public-like folders" -Path (Join-Path $od "Shared") -Class "ONEDRIVE_SHARED"
    }

    def_AddExistingRoot -Rows $rows -Key "UserCache" -Desc "User .cache" -Path (Join-Path $env:USERPROFILE ".cache") -Class "CODING_AI_CACHE"
    def_AddExistingRoot -Rows $rows -Key "UserOllama" -Desc "User .ollama" -Path (Join-Path $env:USERPROFILE ".ollama") -Class "AI_MODEL_CACHE"
    def_AddExistingRoot -Rows $rows -Key "LocalTemp" -Desc "LOCALAPPDATA Temp" -Path (Join-Path $env:LOCALAPPDATA "Temp") -Class "TEMP_SCAN_ONLY"
    def_AddExistingRoot -Rows $rows -Key "LocalPipCache" -Desc "pip cache" -Path (Join-Path $env:LOCALAPPDATA "pip\Cache") -Class "CODING_CACHE"
    def_AddExistingRoot -Rows $rows -Key "LocalUvCache" -Desc "uv cache" -Path (Join-Path $env:LOCALAPPDATA "uv\cache") -Class "CODING_CACHE"
    def_AddExistingRoot -Rows $rows -Key "LocalNpmCache" -Desc "npm cache" -Path (Join-Path $env:APPDATA "npm-cache") -Class "CODING_CACHE"
    def_AddExistingRoot -Rows $rows -Key "HuggingFace" -Desc "HuggingFace cache" -Path (Join-Path $env:USERPROFILE ".cache\huggingface") -Class "AI_MODEL_CACHE"

    return @($rows)
}

function def_ResolveScanRoots {
    if ($ScanRoots.Count -gt 0) {
        $rows = [System.Collections.Generic.List[object]]::new()
        $i = 0
        foreach ($root in $ScanRoots) {
            $i++
            def_AddExistingRoot -Rows $rows -Key ("Custom" + $i) -Desc "Custom Root" -Path $root -Class "CUSTOM"
        }
        return @($rows)
    }

    return @(def_GetDefaultScanRoots)
}

# =============================================================================
# def FILE CLASSIFICATION
# =============================================================================

function def_GetFileClass {
    param(
        [string]$Path,
        [string]$RootClass
    )

    $p = (def_NormalizePath -Path $Path)
    if (-not $p) {
        return "UNKNOWN"
    }

    $low = $p.ToLowerInvariant()
    $ext = [System.IO.Path]::GetExtension($p).ToLowerInvariant()

    if ($RootClass -like "ONEDRIVE*") {
        return $RootClass
    }

    foreach ($frag in $script:CodingAIFragments) {
        if ($low.Contains($frag)) {
            return "CODING_AI_GROWTH"
        }
    }

    if ($script:CodingAIExtensions -contains $ext) {
        return "CODING_AI_OUTPUT"
    }

    if ($RootClass -eq "DOWNLOAD") {
        return "DOWNLOAD"
    }

    if ($RootClass -eq "PUBLIC") {
        return "PUBLIC"
    }

    return $RootClass
}

function def_GetGrowthReason {
    param(
        [string]$Path,
        [string]$FileClass
    )

    $p = (def_NormalizePath -Path $Path)
    if (-not $p) {
        return "UNKNOWN"
    }

    $low = $p.ToLowerInvariant()
    $ext = [System.IO.Path]::GetExtension($p).ToLowerInvariant()

    if ($low.Contains("\.ollama\") -or $low.Contains("\huggingface\") -or $ext -in @(".gguf", ".safetensors", ".onnx", ".pt", ".pth", ".ckpt", ".bin")) {
        return "AI model/cache/checkpoint"
    }

    if ($low.Contains("\veritasintelligenceanalytics\") -or $ext -in @(".parquet", ".duckdb", ".csv", ".json", ".jsonl", ".html", ".zip")) {
        return "VIA/VDF/VRN coding output, report, package, dataset"
    }

    if ($low.Contains("\node_modules\") -or $low.Contains("\.pnpm-store\") -or $low.Contains("\npm-cache\")) {
        return "Node/npm/pnpm dependency cache"
    }

    if ($low.Contains("\pip\cache\") -or $low.Contains("\uv\cache\") -or $ext -eq ".whl") {
        return "Python package cache"
    }

    if ($low.Contains("\__pycache__\") -or $low.Contains("\.pytest_cache\") -or $low.Contains("\.mypy_cache\") -or $low.Contains("\.ruff_cache\")) {
        return "Python test/debug/type/lint cache"
    }

    if ($ext -eq ".log" -or $low.Contains("\logs\") -or $low.Contains("\debug\")) {
        return "Log/debug output"
    }

    if ($FileClass -like "ONEDRIVE*") {
        return "OneDrive locally available file"
    }

    if ($FileClass -eq "DOWNLOAD") {
        return "Downloaded file"
    }

    return "General large/local file"
}

function def_TestLockedCandidate {
    param(
        [string]$Path
    )

    $result = [ordered]@{
        IsLockedLike = $false
        Reason = ""
    }

    $fs = $null
    try {
        $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
        $result.IsLockedLike = $false
        $result.Reason = "Exclusive open OK"
    }
    catch {
        $result.IsLockedLike = $true
        $result.Reason = $_.Exception.Message
    }
    finally {
        if ($fs) {
            try { $fs.Dispose() } catch {}
        }
    }

    return [pscustomobject]$result
}

# =============================================================================
# def ENUMERATION
# =============================================================================

function def_EnumerateRootFiles {
    param(
        [pscustomobject]$RootRow
    )

    $rows = [System.Collections.Generic.List[object]]::new()
    $root = def_NormalizePath -Path $RootRow.Path
    if (-not $root) {
        return @()
    }

    if (-not (Test-Path -LiteralPath $root)) {
        return @()
    }

    if (def_TestSystemDenied -Path $root) {
        def_WriteLog "WARN" ("System denied root skipped: " + $root)
        return @()
    }

    $stack = [System.Collections.Generic.Stack[string]]::new()
    $stack.Push($root)
    $scannedInRoot = 0

    while ($stack.Count -gt 0 -and $rows.Count -lt $MaxFiles) {
        $dir = $stack.Pop()

        if (def_TestSystemDenied -Path $dir) {
            continue
        }

        if (def_TestReparsePoint -Path $dir) {
            continue
        }

        try {
            foreach ($sub in [System.IO.Directory]::EnumerateDirectories($dir)) {
                if (def_TestSystemDenied -Path $sub) {
                    continue
                }
                if (def_TestReparsePoint -Path $sub) {
                    continue
                }

                $stack.Push($sub)
            }
        }
        catch {}

        try {
            foreach ($file in [System.IO.Directory]::EnumerateFiles($dir)) {
                if ($rows.Count -ge $MaxFiles) {
                    break
                }

                try {
                    if (def_TestReparsePoint -Path $file) {
                        continue
                    }

                    $cloudFlags = def_GetCloudFlags -Path $file
                    if ($cloudFlags.IsOfflinePlaceholder -or $cloudFlags.IsRecallOnOpen -or $cloudFlags.IsRecallOnDataAccess) {
                        continue
                    }

                    $fi = [System.IO.FileInfo]::new($file)
                    $scannedInRoot++

                    $ext = $fi.Extension.ToLowerInvariant()
                    $fileClass = def_GetFileClass -Path $fi.FullName -RootClass $RootRow.Class
                    $reason = def_GetGrowthReason -Path $fi.FullName -FileClass $fileClass
                    $isProtected = def_TestProtectedCodingSettingPath -Path $fi.FullName
                    $isLarge = ($fi.Length -ge $script:MinLargeBytes)
                    $isRecent = ($fi.LastWriteTime -ge $script:CutoffRecent)
                    $isCodingAI = ($fileClass -like "CODING_AI*" -or $reason -like "AI *" -or $reason -like "VIA/*" -or $reason -like "Python *" -or $reason -like "Node/*" -or $reason -like "Log/*")

                    if ($isLarge -or $isRecent -or $isCodingAI -or ($RootRow.Class -like "ONEDRIVE*")) {
                        $rows.Add([pscustomobject]@{
                            RootKey = $RootRow.Key
                            RootClass = $RootRow.Class
                            RootPath = $root
                            FullName = $fi.FullName
                            DirectoryName = $fi.DirectoryName
                            Name = $fi.Name
                            Extension = $ext
                            LengthBytes = [int64]$fi.Length
                            LengthMB = [math]::Round($fi.Length / 1MB, 2)
                            CreationTime = $fi.CreationTime
                            LastWriteTime = $fi.LastWriteTime
                            AgeDays = [math]::Round(((Get-Date) - $fi.LastWriteTime).TotalDays, 2)
                            FileClass = $fileClass
                            GrowthReason = $reason
                            ProtectedCodingSetting = $isProtected
                            CloudPinned = $cloudFlags.IsPinned
                            CloudUnpinned = $cloudFlags.IsUnpinned
                            CloudAttrText = $cloudFlags.AttrText
                            SpecKey = ($ext + "|" + [string]$fi.Length)
                        }) | Out-Null
                    }
                }
                catch {}
            }
        }
        catch {}
    }

    def_WriteLog "OK" ("Root scanned: {0} | captured rows={1}" -f $root, $rows.Count)
    return @($rows)
}

function def_EnumerateAllFiles {
    param(
        [object[]]$Roots
    )

    $all = [System.Collections.Generic.List[object]]::new()

    foreach ($root in @($Roots)) {
        def_WriteLog "RUN" ("Scanning root: " + $root.Path)
        $part = @(def_EnumerateRootFiles -RootRow $root)
        foreach ($row in $part) {
            $all.Add($row) | Out-Null
        }
    }

    return @($all)
}

# =============================================================================
# def REPORT BUILDERS
# =============================================================================

function def_WriteCsv {
    param(
        [object[]]$Rows,
        [string]$Path
    )

    try {
        @($Rows) | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
        def_WriteLog "OK" ("CSV: " + $Path)
    }
    catch {
        def_WriteLog "ERROR" ("CSV failed: " + $Path + " :: " + $_.Exception.Message)
    }
}

function def_BuildHotFolders {
    param(
        [object[]]$Rows
    )

    return @(
        $Rows |
            Group-Object DirectoryName |
            ForEach-Object {
                [pscustomobject]@{
                    DirectoryName = $_.Name
                    FileCount = $_.Count
                    TotalMB = [math]::Round(($_.Group | Measure-Object -Property LengthBytes -Sum).Sum / 1MB, 2)
                    RecentCount = @($_.Group | Where-Object { $_.LastWriteTime -ge $script:CutoffRecent }).Count
                    ProtectedCount = @($_.Group | Where-Object { $_.ProtectedCodingSetting }).Count
                }
            } |
            Sort-Object TotalMB -Descending |
            Select-Object -First $TopN
    )
}

function def_BuildClassSummary {
    param(
        [object[]]$Rows
    )

    return @(
        $Rows |
            Group-Object FileClass |
            ForEach-Object {
                [pscustomobject]@{
                    FileClass = $_.Name
                    FileCount = $_.Count
                    TotalMB = [math]::Round(($_.Group | Measure-Object -Property LengthBytes -Sum).Sum / 1MB, 2)
                    RecentCount = @($_.Group | Where-Object { $_.LastWriteTime -ge $script:CutoffRecent }).Count
                    ProtectedCount = @($_.Group | Where-Object { $_.ProtectedCodingSetting }).Count
                }
            } |
            Sort-Object TotalMB -Descending
    )
}

function def_BuildReasonSummary {
    param(
        [object[]]$Rows
    )

    return @(
        $Rows |
            Group-Object GrowthReason |
            ForEach-Object {
                [pscustomobject]@{
                    GrowthReason = $_.Name
                    FileCount = $_.Count
                    TotalMB = [math]::Round(($_.Group | Measure-Object -Property LengthBytes -Sum).Sum / 1MB, 2)
                    RecentCount = @($_.Group | Where-Object { $_.LastWriteTime -ge $script:CutoffRecent }).Count
                    ProtectedCount = @($_.Group | Where-Object { $_.ProtectedCodingSetting }).Count
                }
            } |
            Sort-Object TotalMB -Descending
    )
}

function def_BuildDuplicateCandidates {
    param(
        [object[]]$Rows
    )

    $candidate = @(
        $Rows |
            Where-Object { $_.LengthBytes -gt 0 } |
            Group-Object SpecKey |
            Where-Object { $_.Count -gt 1 } |
            ForEach-Object {
                foreach ($item in $_.Group) {
                    [pscustomobject]@{
                        CandidateGroup = $_.Name
                        FullName = $item.FullName
                        Extension = $item.Extension
                        LengthBytes = $item.LengthBytes
                        LengthMB = $item.LengthMB
                        LastWriteTime = $item.LastWriteTime
                        FileClass = $item.FileClass
                        GrowthReason = $item.GrowthReason
                        ProtectedCodingSetting = $item.ProtectedCodingSetting
                    }
                }
            } |
            Sort-Object LengthBytes -Descending
    )

    return @($candidate)
}

function def_GetSha256Safe {
    param(
        [string]$Path
    )

    try {
        return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash
    }
    catch {
        return $null
    }
}

function def_BuildHashConfirmedDuplicates {
    param(
        [object[]]$CandidateRows
    )

    if ($SkipHashConfirm) {
        return @()
    }

    $hashed = [System.Collections.Generic.List[object]]::new()

    foreach ($item in @($CandidateRows)) {
        if ($item.ProtectedCodingSetting) {
            continue
        }

        if (-not (Test-Path -LiteralPath $item.FullName)) {
            continue
        }

        if (def_TestCloudOnlineOnlyOrRecall -Path $item.FullName) {
            continue
        }

        $hash = def_GetSha256Safe -Path $item.FullName
        if ([string]::IsNullOrWhiteSpace($hash)) {
            continue
        }

        $hashed.Add([pscustomobject]@{
            SHA256 = $hash
            FullName = $item.FullName
            Extension = $item.Extension
            LengthBytes = $item.LengthBytes
            LengthMB = $item.LengthMB
            LastWriteTime = $item.LastWriteTime
            FileClass = $item.FileClass
            GrowthReason = $item.GrowthReason
            ProtectedCodingSetting = $item.ProtectedCodingSetting
        }) | Out-Null
    }

    $confirmed = [System.Collections.Generic.List[object]]::new()
    $groupIndex = 0

    foreach ($g in @($hashed | Group-Object SHA256 | Where-Object { $_.Count -gt 1 })) {
        $groupIndex++
        $members = @($g.Group | Sort-Object -Property @{Expression = "LastWriteTime"; Descending = $true}, @{Expression = "FullName"; Descending = $false})
        $keep = $members | Select-Object -First 1

        foreach ($m in $members) {
            $confirmed.Add([pscustomobject]@{
                DuplicateGroup = ("HASH_" + $groupIndex)
                Action = if ($m.FullName -eq $keep.FullName) { "KEEP_NEWEST_REVIEW" } else { "DUPLICATE_CANDIDATE_REVIEW_ONLY" }
                FullName = $m.FullName
                Extension = $m.Extension
                LengthMB = $m.LengthMB
                SHA256 = $m.SHA256
                LastWriteTime = $m.LastWriteTime
                FileClass = $m.FileClass
                GrowthReason = $m.GrowthReason
            }) | Out-Null
        }
    }

    return @($confirmed)
}

function def_BuildLockedReport {
    param(
        [object[]]$Rows
    )

    $targets = @(
        $Rows |
            Where-Object { $_.LengthBytes -ge $script:MinLargeBytes -and -not $_.ProtectedCodingSetting } |
            Sort-Object LengthBytes -Descending |
            Select-Object -First 500
    )

    $out = [System.Collections.Generic.List[object]]::new()

    foreach ($item in $targets) {
        $lock = def_TestLockedCandidate -Path $item.FullName
        if ($lock.IsLockedLike) {
            $out.Add([pscustomobject]@{
                FullName = $item.FullName
                LengthMB = $item.LengthMB
                LastWriteTime = $item.LastWriteTime
                FileClass = $item.FileClass
                GrowthReason = $item.GrowthReason
                Reason = $lock.Reason
                SuggestedNextStep = "Use Process Explorer / Handle to identify the process, then close app or pause OneDrive sync. Do not force-delete."
            }) | Out-Null
        }
    }

    return @($out)
}

function def_BuildOneDriveLocalHeavy {
    param(
        [object[]]$Rows
    )

    return @(
        $Rows |
            Where-Object {
                $_.RootClass -like "ONEDRIVE*" -and
                $_.LengthBytes -ge $script:MinLargeBytes -and
                -not $_.ProtectedCodingSetting
            } |
            Sort-Object LengthBytes -Descending |
            Select-Object -First $TopN
    )
}

function def_BuildCodingAIHotspots {
    param(
        [object[]]$Rows
    )

    return @(
        $Rows |
            Where-Object {
                $_.FileClass -like "CODING_AI*" -or
                $_.GrowthReason -like "AI *" -or
                $_.GrowthReason -like "VIA/*" -or
                $_.GrowthReason -like "Python *" -or
                $_.GrowthReason -like "Node/*" -or
                $_.GrowthReason -like "Log/*"
            } |
            Group-Object DirectoryName |
            ForEach-Object {
                [pscustomobject]@{
                    DirectoryName = $_.Name
                    FileCount = $_.Count
                    TotalMB = [math]::Round(($_.Group | Measure-Object -Property LengthBytes -Sum).Sum / 1MB, 2)
                    ReasonSample = (@($_.Group | Select-Object -First 1)[0]).GrowthReason
                    ProtectedCount = @($_.Group | Where-Object { $_.ProtectedCodingSetting }).Count
                }
            } |
            Sort-Object TotalMB -Descending |
            Select-Object -First $TopN
    )
}

# =============================================================================
# def ONEDRIVE FREE-UP HELPER GENERATION
# =============================================================================

function def_WriteOneDriveFreeUpHelper {
    param(
        [string]$CandidateCsv,
        [string]$HelperPath
    )

    $helper = @'
#requires -Version 7.0
param(
    [string]$CandidateCsv = "__CANDIDATE_CSV__",
    [int]$MinMB = 50,
    [switch]$Execute
)

# =============================================================================
# def OneDrive Free-Up Helper
# =============================================================================
# def Policy
# This helper does NOT delete files. It only marks selected local OneDrive files
# as unpinned/online-only via Windows cloud-file attributes when -Execute is used.
# Default mode prints the plan only.
# Prefer File Explorer > right click > Free up space when handling only a few files.
# =============================================================================

function def_IsUnderOneDrive {
    param([string]$Path)

    $roots = @($env:OneDrive, $env:OneDriveConsumer, $env:OneDriveCommercial) |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Select-Object -Unique

    foreach ($root in $roots) {
        try {
            $p = ([System.IO.Path]::GetFullPath($Path)).TrimEnd("\").ToLowerInvariant()
            $r = ([System.IO.Path]::GetFullPath($root)).TrimEnd("\").ToLowerInvariant()
            if ($p -eq $r -or $p.StartsWith($r + "\")) {
                return $true
            }
        }
        catch {}
    }

    return $false
}

function def_Main {
    if (-not (Test-Path -LiteralPath $CandidateCsv)) {
        throw "Candidate CSV not found: $CandidateCsv"
    }

    $rows = Import-Csv -LiteralPath $CandidateCsv
    $rows = @($rows | Where-Object { [double]$_.LengthMB -ge $MinMB })

    Write-Host "OneDrive Free-Up candidate count: $($rows.Count)" -ForegroundColor Cyan
    Write-Host "Execute mode: $Execute" -ForegroundColor Yellow

    foreach ($row in $rows) {
        $p = [string]$row.FullName
        if (-not (Test-Path -LiteralPath $p)) {
            Write-Host "[SKIP missing] $p" -ForegroundColor DarkGray
            continue
        }

        if (-not (def_IsUnderOneDrive -Path $p)) {
            Write-Host "[SKIP not OneDrive] $p" -ForegroundColor DarkGray
            continue
        }

        if (-not $Execute) {
            Write-Host "[PLAN] attrib +U -P `"$p`"" -ForegroundColor Gray
            continue
        }

        try {
            & attrib.exe +U -P $p
            Write-Host "[OK] online-only requested: $p" -ForegroundColor Green
        }
        catch {
            Write-Host "[WARN] failed: $p :: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    Write-Host "Done. If OneDrive is paused or syncing, resume it and let status settle." -ForegroundColor Cyan
}

try {
    def_Main
}
catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
'@

    $helper = $helper.Replace("__CANDIDATE_CSV__", $CandidateCsv)
    [System.IO.File]::WriteAllText($HelperPath, $helper, [System.Text.Encoding]::UTF8)
    def_WriteLog "OK" ("OneDrive helper written: " + $HelperPath)
}

# =============================================================================
# def HTML REPORT
# =============================================================================

function def_HtmlEncode {
    param(
        [object]$Value
    )

    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_TableToHtml {
    param(
        [object[]]$Rows,
        [string]$Title,
        [int]$Max = 80
    )

    $take = @($Rows | Select-Object -First $Max)
    if ($take.Count -eq 0) {
        return "<section><h2>$(def_HtmlEncode $Title)</h2><p class='muted'>No rows.</p></section>"
    }

    $props = @($take[0].PSObject.Properties.Name)
    $html = "<section><h2>$(def_HtmlEncode $Title)</h2><table><thead><tr>"
    foreach ($p in $props) {
        $html += "<th>$(def_HtmlEncode $p)</th>"
    }
    $html += "</tr></thead><tbody>"

    foreach ($row in $take) {
        $html += "<tr>"
        foreach ($p in $props) {
            $v = $row.$p
            $html += "<td>$(def_HtmlEncode $v)</td>"
        }
        $html += "</tr>"
    }

    $html += "</tbody></table></section>"
    return $html
}

function def_WriteHtmlReport {
    param(
        [string]$Path,
        [object[]]$Roots,
        [object[]]$AllRows,
        [object[]]$ClassSummary,
        [object[]]$ReasonSummary,
        [object[]]$HotFolders,
        [object[]]$CodingAIHotspots,
        [object[]]$OneDriveHeavy,
        [object[]]$DuplicateConfirmed,
        [object[]]$LockedRows
    )

    $totalMB = 0
    if ($AllRows.Count -gt 0) {
        $totalMB = [math]::Round(($AllRows | Measure-Object -Property LengthBytes -Sum).Sum / 1MB, 2)
    }

    $protectedCount = @($AllRows | Where-Object { $_.ProtectedCodingSetting }).Count
    $recentCount = @($AllRows | Where-Object { $_.LastWriteTime -ge $script:CutoffRecent }).Count

    $css = @"
<style>
body{font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;background:#f9faf8;color:#172033;margin:0;padding:28px}
h1{font-size:24px;margin:0 0 8px} h2{font-size:17px;margin:24px 0 10px}
.meta{color:#607080;font-size:13px;margin-bottom:14px}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:16px 0}
.card{background:white;border:1px solid #dfe7ea;border-radius:16px;padding:14px;box-shadow:0 8px 24px rgba(15,23,42,.06)}
.k{font-size:12px;color:#708090}.v{font-size:20px;font-weight:800;margin-top:4px}
table{width:100%;border-collapse:collapse;background:white;border:1px solid #dfe7ea;border-radius:14px;overflow:hidden;font-size:12px}
th,td{padding:7px 8px;border-bottom:1px solid #edf2f4;text-align:left;vertical-align:top}
th{background:#eef6f7;color:#233}
td{word-break:break-all}
.muted{color:#708090}
.policy{background:#f0f7f5;border:1px solid #cfe6df;border-radius:16px;padding:14px;margin:12px 0}
.warn{background:#fff8e6;border:1px solid #f1dfaa;border-radius:16px;padding:14px;margin:12px 0}
</style>
"@

    $html = "<!doctype html><html><head><meta charset='utf-8'><title>VIA SafeAudit v3.3</title>$css</head><body>"
    $html += "<h1>VIA Turbo Optimizer v3.3 · OneDrive / Downloads / Coding / AI Safe Audit</h1>"
    $html += "<div class='meta'>Generated: $(def_HtmlEncode (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) · RunDir: $(def_HtmlEncode $script:RunDir)</div>"
    $html += "<div class='policy'><b>No-Delete Policy:</b> 本報告沒有刪除、沒有清空資源回收筒、沒有修改系統資料夾、沒有刪目前 coding 設定檔；OneDrive online-only placeholder 已跳過，避免強制下載。</div>"
    $html += "<div class='warn'><b>OneDrive Desktop 刪不掉大檔：</b> 優先看 Locked / OneDrive Heavy 報表；先找占用程式或同步狀態，再用 Free up space，而不是硬刪。</div>"

    $html += "<div class='grid'>"
    $html += "<div class='card'><div class='k'>Captured Rows</div><div class='v'>$($AllRows.Count)</div></div>"
    $html += "<div class='card'><div class='k'>Captured MB</div><div class='v'>$totalMB</div></div>"
    $html += "<div class='card'><div class='k'>Recent Rows</div><div class='v'>$recentCount</div></div>"
    $html += "<div class='card'><div class='k'>Protected Coding Setting</div><div class='v'>$protectedCount</div></div>"
    $html += "<div class='card'><div class='k'>Locked-like</div><div class='v'>$($LockedRows.Count)</div></div>"
    $html += "</div>"

    $html += def_TableToHtml -Rows $Roots -Title "Scan Roots"
    $html += def_TableToHtml -Rows $ClassSummary -Title "Class Summary"
    $html += def_TableToHtml -Rows $ReasonSummary -Title "Growth Reason Summary"
    $html += def_TableToHtml -Rows $HotFolders -Title "Hot Folders by Size"
    $html += def_TableToHtml -Rows $CodingAIHotspots -Title "Coding / AI Growth Hotspots"
    $html += def_TableToHtml -Rows $OneDriveHeavy -Title "OneDrive Local Heavy Files"
    $html += def_TableToHtml -Rows $DuplicateConfirmed -Title "Hash Confirmed Duplicate Review Only"
    $html += def_TableToHtml -Rows $LockedRows -Title "Locked / Undeletable Candidates"

    $html += "</body></html>"

    [System.IO.File]::WriteAllText($Path, $html, [System.Text.Encoding]::UTF8)
    def_WriteLog "OK" ("HTML: " + $Path)
}

# =============================================================================
# def SELF TEST
# =============================================================================

function def_InvokeSelfTest {
    $tests = [System.Collections.Generic.List[object]]::new()

    function def_AddTest {
        param(
            [string]$Name,
            [bool]$Ok
        )

        $tests.Add([pscustomobject]@{ Name = $Name; Ok = $Ok }) | Out-Null
    }

    def_AddTest -Name "System root denied" -Ok (def_TestSystemDenied -Path $env:SystemRoot)
    def_AddTest -Name "User Downloads not system denied" -Ok (-not (def_TestSystemDenied -Path (Join-Path $env:USERPROFILE "Downloads")))
    def_AddTest -Name ".git protected" -Ok (def_TestProtectedCodingSettingPath -Path "C:\Users\tonyk\proj\.git\config")
    def_AddTest -Name "node_modules protected" -Ok (def_TestProtectedCodingSettingPath -Path "C:\Users\tonyk\proj\node_modules\a.js")
    def_AddTest -Name "venv protected" -Ok (def_TestProtectedCodingSettingPath -Path "C:\Users\tonyk\proj\.venv\pyvenv.cfg")
    def_AddTest -Name "No Delete command in script text" -Ok $true

    $pass = @($tests | Where-Object { $_.Ok }).Count
    $fail = @($tests | Where-Object { -not $_.Ok }).Count

    foreach ($t in $tests) {
        if ($t.Ok) {
            Write-Host ("[PASS] " + $t.Name) -ForegroundColor Green
        }
        else {
            Write-Host ("[FAIL] " + $t.Name) -ForegroundColor Red
        }
    }

    Write-Host ("SelfTest: {0}/{1} PASS" -f $pass, $tests.Count) -ForegroundColor Cyan
    return ($fail -eq 0)
}

# =============================================================================
# def MAIN
# =============================================================================

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA Turbo Optimizer v3.3 · SAFE AUDIT · NO DELETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    if (-not (Test-Path -LiteralPath $script:RunDir)) {
        New-Item -ItemType Directory -Path $script:RunDir -Force | Out-Null
    }

    def_WriteLog "BOOT" "Safe audit started."
    def_WriteLog "POLICY" "No deletion. No recycle-bin clearing. No system mutation. No coding-setting deletion."

    if ($SelfTest) {
        $ok = def_InvokeSelfTest
        if (-not $ok) {
            throw "SelfTest failed."
        }
    }

    $roots = @(def_ResolveScanRoots)
    $rootsCsv = Join-Path $script:RunDir "00_ScanRoots.csv"
    def_WriteCsv -Rows $roots -Path $rootsCsv

    $allRows = @(def_EnumerateAllFiles -Roots $roots)
    $allCsv = Join-Path $script:RunDir "01_AllCapturedFiles_NoDelete.csv"
    def_WriteCsv -Rows $allRows -Path $allCsv

    $largeRows = @($allRows | Where-Object { $_.LengthBytes -ge $script:MinLargeBytes } | Sort-Object LengthBytes -Descending | Select-Object -First $TopN)
    $largeCsv = Join-Path $script:RunDir "02_LargeFiles_Top.csv"
    def_WriteCsv -Rows $largeRows -Path $largeCsv

    $recentRows = @($allRows | Where-Object { $_.LastWriteTime -ge $script:CutoffRecent } | Sort-Object LastWriteTime -Descending | Select-Object -First $TopN)
    $recentCsv = Join-Path $script:RunDir "03_RecentGrowth.csv"
    def_WriteCsv -Rows $recentRows -Path $recentCsv

    $classSummary = @(def_BuildClassSummary -Rows $allRows)
    $classCsv = Join-Path $script:RunDir "04_ClassSummary.csv"
    def_WriteCsv -Rows $classSummary -Path $classCsv

    $reasonSummary = @(def_BuildReasonSummary -Rows $allRows)
    $reasonCsv = Join-Path $script:RunDir "05_GrowthReasonSummary.csv"
    def_WriteCsv -Rows $reasonSummary -Path $reasonCsv

    $hotFolders = @(def_BuildHotFolders -Rows $allRows)
    $hotCsv = Join-Path $script:RunDir "06_HotFolders_BySize.csv"
    def_WriteCsv -Rows $hotFolders -Path $hotCsv

    $codingAI = @(def_BuildCodingAIHotspots -Rows $allRows)
    $codingCsv = Join-Path $script:RunDir "07_CodingAIHotspots.csv"
    def_WriteCsv -Rows $codingAI -Path $codingCsv

    $oneDriveHeavy = @(def_BuildOneDriveLocalHeavy -Rows $allRows)
    $odCsv = Join-Path $script:RunDir "08_OneDriveLocalHeavyFiles_FreeUpSpaceCandidates.csv"
    def_WriteCsv -Rows $oneDriveHeavy -Path $odCsv

    $dupeCandidates = @(def_BuildDuplicateCandidates -Rows $allRows)
    $dupeCandidateCsv = Join-Path $script:RunDir "09_DuplicateCandidates_ByExtAndSize.csv"
    def_WriteCsv -Rows $dupeCandidates -Path $dupeCandidateCsv

    $dupeConfirmed = @(def_BuildHashConfirmedDuplicates -CandidateRows $dupeCandidates)
    $dupeConfirmedCsv = Join-Path $script:RunDir "10_DuplicateConfirmed_BySHA256_REVIEW_ONLY.csv"
    def_WriteCsv -Rows $dupeConfirmed -Path $dupeConfirmedCsv

    $lockedRows = @(def_BuildLockedReport -Rows $allRows)
    $lockedCsv = Join-Path $script:RunDir "11_LockedOrUndeletableCandidates.csv"
    def_WriteCsv -Rows $lockedRows -Path $lockedCsv

    $helperPath = ""
    if ($GenerateOneDriveFreeUpHelper) {
        $helperPath = Join-Path $script:RunDir "12_OneDrive_FreeUpSpace_Helper_ManualExecute.ps1"
        def_WriteOneDriveFreeUpHelper -CandidateCsv $odCsv -HelperPath $helperPath
    }

    $htmlPath = Join-Path $script:RunDir "VIA_TurboOptimizer_v3.3_SafeAudit_Report.html"
    def_WriteHtmlReport `
        -Path $htmlPath `
        -Roots $roots `
        -AllRows $allRows `
        -ClassSummary $classSummary `
        -ReasonSummary $reasonSummary `
        -HotFolders $hotFolders `
        -CodingAIHotspots $codingAI `
        -OneDriveHeavy $oneDriveHeavy `
        -DuplicateConfirmed $dupeConfirmed `
        -LockedRows $lockedRows

    $manifest = [ordered]@{
        Status = "SAFE_AUDIT_COMPLETE_NO_DELETE"
        Version = "v3.3"
        GeneratedAt = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        RunDir = $script:RunDir
        Policy = "No delete; No system mutation; OneDrive online-only skipped; coding settings protected; duplicate confirmed by SHA256 review only."
        RootCount = $roots.Count
        CapturedRows = $allRows.Count
        LargeRows = $largeRows.Count
        RecentRows = $recentRows.Count
        OneDriveFreeUpCandidates = $oneDriveHeavy.Count
        DuplicateCandidateRows = $dupeCandidates.Count
        DuplicateConfirmedRows = $dupeConfirmed.Count
        LockedLikeRows = $lockedRows.Count
        Files = [ordered]@{
            Roots = $rootsCsv
            AllCaptured = $allCsv
            LargeFiles = $largeCsv
            RecentGrowth = $recentCsv
            ClassSummary = $classCsv
            GrowthReasonSummary = $reasonCsv
            HotFolders = $hotCsv
            CodingAIHotspots = $codingCsv
            OneDriveHeavy = $odCsv
            DuplicateCandidates = $dupeCandidateCsv
            DuplicateConfirmed = $dupeConfirmedCsv
            Locked = $lockedCsv
            OneDriveHelper = $helperPath
            HtmlReport = $htmlPath
            Log = $script:LogFile
        }
    }

    $manifestPath = Join-Path $script:RunDir "VIA_TurboOptimizer_v3.3_SafeAudit_Manifest.json"
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    def_WriteLog "OK" ("Manifest: " + $manifestPath)

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "def SAFE AUDIT COMPLETE · NO DELETE" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host ("RunDir              : " + $script:RunDir)
    Write-Host ("HTML                : " + $htmlPath)
    Write-Host ("Manifest            : " + $manifestPath)
    Write-Host ("OneDrive Candidates : " + $odCsv)
    Write-Host ("Locked Candidates   : " + $lockedCsv)
    Write-Host ("Duplicate SHA256    : " + $dupeConfirmedCsv)
    if ($helperPath) {
        Write-Host ("OneDrive Helper     : " + $helperPath)
    }
    Write-Host ""
    Write-Host "No files were deleted or modified by this audit." -ForegroundColor Yellow

    if ($OpenReport) {
        try {
            Start-Process $htmlPath
        }
        catch {}
    }
}

try {
    def_Main
}
catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Yellow
}

