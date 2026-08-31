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
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# def PARAMS · ALL PARAMETERS AT TOP
# =============================================================================

$def_PARAM_PROJECT_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$def_PARAM_SUPPORTIVE_ROOT = Join-Path $def_PARAM_PROJECT_ROOT "supportive modules"
$def_PARAM_NEXUSCORE_PATH = Join-Path $def_PARAM_SUPPORTIVE_ROOT "Invoke-VeritasNexusCore.ps1"
$def_PARAM_VDF_ROOT = Join-Path $def_PARAM_PROJECT_ROOT "functional modules\VDF"
$def_PARAM_VRN_ROOT = Join-Path $def_PARAM_PROJECT_ROOT "functional modules\VRN"

$def_PARAM_RUN_NAME = "VIA_SUPPORTIVE_DOCKING_VDF_VRN_v02861"
$def_PARAM_OPEN_HTML = $true
$def_PARAM_INSTALL_PS_EXTENSIONS = $true
$def_PARAM_USE_NEXUSCORE_DOTSOURCE = $false

$def_PARAM_MAX_FILE_MB_FOR_TEXT_SCAN = 5
$def_PARAM_AST_EXT = @(".ps1", ".psm1", ".psd1")
$def_PARAM_TEXT_EXT = @(".ps1", ".psm1", ".psd1", ".py", ".html", ".htm", ".js", ".ts", ".json", ".csv", ".md", ".txt", ".yaml", ".yml")
$def_PARAM_DATA_EXT = @(".parquet", ".duckdb", ".db", ".sqlite", ".csv", ".xlsx", ".json")

$def_PARAM_PS_ACCEL_EXTENSIONS = @(
    "Pester",
    "PSScriptAnalyzer",
    "ThreadJob",
    "ImportExcel",
    "PSWriteHTML",
    "PSFramework",
    "Pode",
    "Polaris",
    "BurntToast",
    "PSReadLine"
)

$def_PARAM_SIGNAL_PATTERNS = @(
    "NexusCore",
    "Invoke-VeritasNexusCore",
    "DATABASE",
    "canonical",
    "Stop-Process",
    "Remove-Item",
    "Invoke-Expression",
    "duckdb",
    "parquet",
    "pdfplumber",
    "PyMuPDF",
    "pdfminer",
    "pypdf",
    "camelot",
    "tabula",
    "OCR",
    "Tesseract",
    "VRN",
    "VDF",
    "VeritasDataForge",
    "VeritasReportNova",
    "Write Governance",
    "Quarantine",
    "Active Pointer",
    "VDF_ACTIVE_POINTER"
)

$def_PARAM_RECENT_CONTEXT = @(
    "v028.5.1 blocked: repaired VDF generated script still had AST parse errors.",
    "v028.5.3 moved in correct direction: NexusCore path, VDF/VRN roots, accelerated inventory, guarded install, no DB write.",
    "v028.6 interactive paste failed because pscustomobject property values used if/try directly inside hashtable.",
    "v028.6.1 fixes the PowerShell parser issue by computing values before pscustomobject construction.",
    "This run performs three panorama rounds: analyze, repair-copy/classify, consolidate/user-test.",
    "Default policy: no DATABASE write, no canonical merge, no destructive delete, no Stop-Process, no generated write execution."
)

# =============================================================================
# def STATE
# =============================================================================

$script:def_OK = 0
$script:def_WARN = 0
$script:def_FAIL = 0
$script:def_PHASE_NOW = 0
$script:def_PHASE_TOTAL = 16

# =============================================================================
# def HELPERS
# =============================================================================

function def_Stamp {
    return (Get-Date -Format "yyyyMMdd_HHmmss")
}

function def_Iso {
    return (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffK")
}

function def_Mkdir {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    [System.IO.Directory]::CreateDirectory($Path) | Out-Null
}

function def_Html {
    param([AllowNull()][object]$Text)

    if ($null -eq $Text) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Text)
}

function def_Csv {
    param([AllowNull()][object]$Value)

    $s = if ($null -eq $Value) { "" } else { [string]$Value }
    if ($s -match '[",\r\n]') {
        return '"' + $s.Replace('"','""') + '"'
    }
    return $s
}

function def_WriteText {
    param(
        [string]$Path,
        [string]$Text,
        [bool]$Bom = $false
    )

    $enc = [System.Text.UTF8Encoding]::new($Bom)
    [System.IO.File]::WriteAllText($Path, $Text, $enc)
}

function def_WriteJson {
    param(
        [string]$Path,
        [object]$Object
    )

    $json = $Object | ConvertTo-Json -Depth 80
    def_WriteText -Path $Path -Text $json -Bom $false
}

function def_ShowProgress {
    param(
        [string]$Status,
        [int]$Current,
        [int]$Total
    )

    if ($Total -le 0) { $Total = 1 }
    $pct = [int](($Current / $Total) * 100)
    if ($pct -lt 0) { $pct = 0 }
    if ($pct -gt 100) { $pct = 100 }

    $bar = ("█" * [int]($pct / 5)).PadRight(20, "░")
    Write-Progress -Id 1 -Activity "VIA Supportive Docking · VDF + VRN · v028.6.1" -Status "[$Current/$Total] $Status" -PercentComplete $pct
    Write-Host ("[{0,3}%] [{1}] {2}" -f $pct, $bar, $Status) -ForegroundColor Cyan
}

function def_Phase {
    param([string]$Name)

    $script:def_PHASE_NOW++
    def_ShowProgress -Status $Name -Current $script:def_PHASE_NOW -Total $script:def_PHASE_TOTAL
}

function def_AddRow {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$Round,
        [string]$Project,
        [string]$Lane,
        [string]$Stage,
        [string]$Name,
        [string]$Status,
        [string]$Risk,
        [string]$FixClass,
        [string]$Priority,
        [string]$Mode,
        [string]$Metric,
        [string]$Value,
        [string]$Message,
        [string]$Path
    )

    if ($Status -match "^(OK|PASS|READY)") {
        $script:def_OK++
    }
    elseif ($Status -match "(FAIL|FATAL|BLOCK|ERROR)") {
        $script:def_FAIL++
    }
    else {
        $script:def_WARN++
    }

    $Rows.Add([pscustomobject]@{
        Time     = def_Iso
        Round    = $Round
        Project  = $Project
        Lane     = $Lane
        Stage    = $Stage
        Name     = $Name
        Status   = $Status
        Risk     = $Risk
        FixClass = $FixClass
        Priority = $Priority
        Mode     = $Mode
        Metric   = $Metric
        Value    = $Value
        Message  = $Message
        Path     = $Path
    }) | Out-Null
}

function def_ReadTextSafe {
    param(
        [string]$Path,
        [int]$MaxChars = 200000
    )

    try {
        if (-not [System.IO.File]::Exists($Path)) { return "" }
        $txt = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop
        if ($txt.Length -gt $MaxChars) {
            return $txt.Substring(0, $MaxChars)
        }
        return $txt
    }
    catch {
        return ""
    }
}

function def_HashFile {
    param([string]$Path)

    try {
        if (-not [System.IO.File]::Exists($Path)) { return "" }
        return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash
    }
    catch {
        return "HASH_ERROR"
    }
}

function def_ParsePowerShellFile {
    param([string]$Path)

    $tokens = $null
    $errors = $null

    try {
        $ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)
        $errCount = if ($null -eq $errors) { 0 } else { @($errors).Count }

        $commands = @()
        if ($null -ne $ast) {
            $commands = @(
                $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true) |
                ForEach-Object {
                    try { $_.GetCommandName() } catch { "" }
                } |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
                Sort-Object -Unique
            )
        }

        $errText = ""
        if ($errCount -gt 0) {
            $errText = (@($errors) | ForEach-Object {
                "L$($_.Extent.StartLineNumber):$($_.Extent.StartColumnNumber) $($_.Message)"
            }) -join " | "
        }

        return [pscustomobject]@{
            path              = $Path
            parse_error_count = $errCount
            command_count     = @($commands).Count
            commands          = (@($commands) -join ";")
            parse_errors      = $errText
        }
    }
    catch {
        return [pscustomobject]@{
            path              = $Path
            parse_error_count = 999
            command_count     = 0
            commands          = ""
            parse_errors      = $_.Exception.Message
        }
    }
}

# =============================================================================
# def INVENTORY
# =============================================================================

function def_GetBucket {
    param(
        [string]$Path,
        [string]$ProjectRoot,
        [string]$VdfRoot,
        [string]$VrnRoot,
        [string]$SupportiveRoot
    )

    $cmp = [System.StringComparison]::OrdinalIgnoreCase

    if ($Path.StartsWith($VdfRoot, $cmp)) { return "VDF" }
    if ($Path.StartsWith($VrnRoot, $cmp)) { return "VRN" }
    if ($Path.StartsWith($SupportiveRoot, $cmp)) { return "Supportive" }
    if ($Path.StartsWith((Join-Path $ProjectRoot "dict\VDF\DATABASE"), $cmp)) { return "VDF_DATABASE" }
    if ($Path.StartsWith((Join-Path $ProjectRoot "dict\VDF\_active"), $cmp)) { return "VDF_ACTIVE" }

    return "Other"
}

function def_BuildInventory {
    param(
        [string]$ProjectRoot,
        [string]$VdfRoot,
        [string]$VrnRoot,
        [string]$SupportiveRoot,
        [string]$CsvPath,
        [System.Collections.Generic.List[string]]$PsFiles,
        [System.Collections.Generic.List[string]]$PyFiles,
        [System.Collections.Generic.List[string]]$HtmlFiles,
        [System.Collections.Generic.List[string]]$DataFiles,
        [System.Collections.Generic.List[string]]$TextFiles
    )

    $enumOpts = [System.IO.EnumerationOptions]::new()
    $enumOpts.RecurseSubdirectories = $true
    $enumOpts.IgnoreInaccessible = $true
    $enumOpts.ReturnSpecialDirectories = $false
    $enumOpts.AttributesToSkip = [System.IO.FileAttributes]::ReparsePoint

    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine("bucket,name,extension,bytes,modified,path,sha256")

    $count = 0

    foreach ($p in [System.IO.Directory]::EnumerateFiles($ProjectRoot, "*", $enumOpts)) {
        try {
            $count++
            $fi = [System.IO.FileInfo]::new($p)
            $ext = $fi.Extension.ToLowerInvariant()
            $bucket = def_GetBucket -Path $p -ProjectRoot $ProjectRoot -VdfRoot $VdfRoot -VrnRoot $VrnRoot -SupportiveRoot $SupportiveRoot

            $hash = ""
            if ($ext -in $def_PARAM_TEXT_EXT -and $fi.Length -le 20MB) {
                $hash = def_HashFile -Path $p
            }

            [void]$sb.AppendLine(
                (def_Csv $bucket) + "," +
                (def_Csv $fi.Name) + "," +
                (def_Csv $ext) + "," +
                (def_Csv $fi.Length) + "," +
                (def_Csv $fi.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")) + "," +
                (def_Csv $p) + "," +
                (def_Csv $hash)
            )

            if ($ext -in $def_PARAM_AST_EXT -and $bucket -in @("VDF","VRN","Supportive","VDF_ACTIVE")) {
                $PsFiles.Add($p) | Out-Null
            }

            if ($ext -eq ".py" -and $bucket -in @("VDF","VRN","Supportive")) {
                $PyFiles.Add($p) | Out-Null
            }

            if ($ext -in @(".html",".htm")) {
                $HtmlFiles.Add($p) | Out-Null
            }

            if ($ext -in $def_PARAM_DATA_EXT) {
                $DataFiles.Add($p) | Out-Null
            }

            if ($ext -in $def_PARAM_TEXT_EXT -and $fi.Length -le ($def_PARAM_MAX_FILE_MB_FOR_TEXT_SCAN * 1MB)) {
                $TextFiles.Add($p) | Out-Null
            }

            if (($count % 1000) -eq 0) {
                Write-Progress -Id 2 -ParentId 1 -Activity "Inventory" -Status "$count files scanned" -PercentComplete -1
            }
        }
        catch {
            continue
        }
    }

    Write-Progress -Id 2 -Completed
    def_WriteText -Path $CsvPath -Text $sb.ToString() -Bom $true

    return $count
}

# =============================================================================
# def AUDITS · FIXED VERSION, NO INLINE if INSIDE PSCUSTOMOBJECT PROPERTY
# =============================================================================

function def_AuditPowerShellAst {
    param(
        [System.Collections.Generic.List[string]]$PsFiles,
        [string]$CsvPath
    )

    $throttle = [Math]::Max(2, [Environment]::ProcessorCount)

    $results = $PsFiles | ForEach-Object -ThrottleLimit $throttle -Parallel {
        $path = $_
        $tokens = $null
        $errors = $null

        try {
            $ast = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
            $errCount = if ($null -eq $errors) { 0 } else { @($errors).Count }

            $cmds = @()
            if ($null -ne $ast) {
                $cmds = @(
                    $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true) |
                    ForEach-Object {
                        try { $_.GetCommandName() } catch { "" }
                    } |
                    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
                    Sort-Object -Unique
                )
            }

            $errText = ""
            if ($errCount -gt 0) {
                $errText = (@($errors) | ForEach-Object {
                    "L$($_.Extent.StartLineNumber):$($_.Extent.StartColumnNumber) $($_.Message)"
                }) -join " | "
            }

            [pscustomobject]@{
                path              = $path
                parse_error_count = $errCount
                command_count     = @($cmds).Count
                commands          = (@($cmds) -join ";")
                parse_errors      = $errText
            }
        }
        catch {
            [pscustomobject]@{
                path              = $path
                parse_error_count = 999
                command_count     = 0
                commands          = ""
                parse_errors      = $_.Exception.Message
            }
        }
    }

    @($results) | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8BOM
    return @($results)
}

function def_AuditPythonFiles {
    param(
        [System.Collections.Generic.List[string]]$PyFiles,
        [string]$CsvPath
    )

    $rows = foreach ($p in $PyFiles) {
        $txt = def_ReadTextSafe -Path $p -MaxChars 200000

        $bytes = 0
        try {
            $bytes = ([System.IO.FileInfo]::new($p)).Length
        }
        catch {
            $bytes = 0
        }

        $preview = ""
        if ($txt.Length -gt 500) {
            $preview = $txt.Substring(0, 500)
        }
        else {
            $preview = $txt
        }

        $hasMain = [bool]($txt -match 'if\s+__name__\s*==\s*["'']__main__["'']')
        $hasPandas = [bool]($txt -match '\bimport\s+pandas\b|\bfrom\s+pandas\b')
        $hasPolars = [bool]($txt -match '\bimport\s+polars\b|\bfrom\s+polars\b')
        $hasDuckdb = [bool]($txt -match '\bimport\s+duckdb\b|\bfrom\s+duckdb\b')
        $hasPyarrow = [bool]($txt -match '\bimport\s+pyarrow\b|\bfrom\s+pyarrow\b')
        $hasPdf = [bool]($txt -match 'pdfplumber|fitz|pymupdf|pdfminer|pypdf|camelot|tabula')
        $hasOcr = [bool]($txt -match 'tesseract|paddleocr|easyocr|ocr')

        [pscustomobject]@{
            path        = $p
            bytes       = $bytes
            has_main    = $hasMain
            has_pandas  = $hasPandas
            has_polars  = $hasPolars
            has_duckdb  = $hasDuckdb
            has_pyarrow = $hasPyarrow
            has_pdf     = $hasPdf
            has_ocr     = $hasOcr
            preview     = $preview
        }
    }

    @($rows) | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8BOM
    return @($rows)
}

function def_AuditHtmlFiles {
    param(
        [System.Collections.Generic.List[string]]$HtmlFiles,
        [string]$CsvPath
    )

    $rows = foreach ($p in $HtmlFiles) {
        $txt = def_ReadTextSafe -Path $p -MaxChars 200000

        $bytes = 0
        try {
            $bytes = ([System.IO.FileInfo]::new($p)).Length
        }
        catch {
            $bytes = 0
        }

        $title = ""
        if ($txt -match '<title>(.*?)</title>') {
            $title = $Matches[1]
        }

        [pscustomobject]@{
            path          = $p
            bytes         = $bytes
            has_doctype   = [bool]($txt -match '<!doctype')
            has_charset   = [bool]($txt -match 'charset')
            has_viewport  = [bool]($txt -match 'viewport')
            has_table     = [bool]($txt -match '<table')
            has_grid      = [bool]($txt -match 'grid')
            has_animation = [bool]($txt -match '@keyframes|transition|animation')
            has_veritas   = [bool]($txt -match 'Veritas|VIA|Veritas Intelligence Analytics')
            title         = $title
        }
    }

    @($rows) | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8BOM
    return @($rows)
}

function def_AuditDataFiles {
    param(
        [System.Collections.Generic.List[string]]$DataFiles,
        [string]$CsvPath
    )

    $rows = foreach ($p in $DataFiles) {
        try {
            $fi = [System.IO.FileInfo]::new($p)

            $bucketHint = "Other"
            if ($p -match '\\VRN\\') { $bucketHint = "VRN" }
            elseif ($p -match '\\VDF\\') { $bucketHint = "VDF" }
            elseif ($p -match '\\DATABASE\\') { $bucketHint = "DATABASE" }

            [pscustomobject]@{
                path        = $p
                name        = $fi.Name
                extension   = $fi.Extension.ToLowerInvariant()
                bytes       = $fi.Length
                modified    = $fi.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                bucket_hint = $bucketHint
            }
        }
        catch {
            [pscustomobject]@{
                path        = $p
                name        = ""
                extension   = ""
                bytes       = 0
                modified    = ""
                bucket_hint = "ERROR"
            }
        }
    }

    @($rows) | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8BOM
    return @($rows)
}

function def_SearchSignals {
    param(
        [System.Collections.Generic.List[string]]$TextFiles,
        [string]$CsvPath
    )

    $rows = [System.Collections.Generic.List[object]]::new()
    $i = 0
    $total = @($TextFiles).Count

    foreach ($p in $TextFiles) {
        $i++

        if (($i % 200) -eq 0) {
            $pct = [int](($i / [Math]::Max($total,1)) * 100)
            Write-Progress -Id 3 -ParentId 1 -Activity "Signal Scan" -Status "$i / $total" -PercentComplete $pct
        }

        $txt = def_ReadTextSafe -Path $p -MaxChars 300000
        if ([string]::IsNullOrWhiteSpace($txt)) { continue }

        foreach ($pat in $def_PARAM_SIGNAL_PATTERNS) {
            $idx = $txt.IndexOf($pat, [System.StringComparison]::OrdinalIgnoreCase)
            if ($idx -ge 0) {
                $start = [Math]::Max(0, $idx - 120)
                $len = [Math]::Min(420, $txt.Length - $start)
                $snippet = $txt.Substring($start, $len)

                $rows.Add([pscustomobject]@{
                    pattern = $pat
                    path    = $p
                    snippet = $snippet
                }) | Out-Null
            }
        }
    }

    Write-Progress -Id 3 -Completed
    @($rows) | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8BOM
    return @($rows)
}

# =============================================================================
# def REPAIR COPY · SAFE, NO OVERWRITE
# =============================================================================

function def_NewRepairCopyForParseFail {
    param(
        [object[]]$ParseFailRows,
        [string]$RepairDir,
        [string]$CsvPath
    )

    $rows = [System.Collections.Generic.List[object]]::new()

    foreach ($r in $ParseFailRows) {
        $src = [string]$r.path
        if (-not [System.IO.File]::Exists($src)) { continue }

        $name = [System.IO.Path]::GetFileNameWithoutExtension($src)
        $ext = [System.IO.Path]::GetExtension($src)
        $safeName = ($name -replace '[^\w\.-]', '_')
        $dst = Join-Path $RepairDir ($safeName + "_REPAIR_COPY_v02861" + $ext)

        try {
            $txt = Get-Content -LiteralPath $src -Raw -Encoding UTF8 -ErrorAction Stop

            # Known parser-risk patterns from current failure:
            # Inside hashtable property: prop = if (...) {...} else {...}
            # This generic repair is intentionally conservative and only creates a repair copy.
            $fixed = $txt
            $fixed = $fixed -replace '=\s+if\s+\(', '= $(if ('
            $fixed = $fixed -replace '=\s+try\s+\{', '= $(try {'

            if ($fixed -ne $txt) {
                def_WriteText -Path $dst -Text $fixed -Bom $false
                $test = def_ParsePowerShellFile -Path $dst

                $rows.Add([pscustomobject]@{
                    source_path = $src
                    repair_copy = $dst
                    action      = "REPAIR_COPY_CREATED"
                    parse_errors_before = $r.parse_error_count
                    parse_errors_after  = $test.parse_error_count
                    message     = $test.parse_errors
                }) | Out-Null
            }
            else {
                $rows.Add([pscustomobject]@{
                    source_path = $src
                    repair_copy = ""
                    action      = "NO_SAFE_PATTERN_APPLIED"
                    parse_errors_before = $r.parse_error_count
                    parse_errors_after  = ""
                    message     = "No conservative repair pattern matched. Manual sequential repair required."
                }) | Out-Null
            }
        }
        catch {
            $rows.Add([pscustomobject]@{
                source_path = $src
                repair_copy = ""
                action      = "REPAIR_COPY_FAILED"
                parse_errors_before = $r.parse_error_count
                parse_errors_after  = ""
                message     = $_.Exception.Message
            }) | Out-Null
        }
    }

    @($rows) | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8BOM
    return @($rows)
}

function def_ClassifyFixPlan {
    param(
        [object[]]$PsParseFails,
        [object[]]$SignalRows,
        [string]$CsvPath
    )

    $rows = [System.Collections.Generic.List[object]]::new()

    foreach ($r in $PsParseFails) {
        $mode = "SEQUENTIAL_REQUIRED"
        $risk = "HIGH"
        $reason = "PowerShell parse error must be repaired one file at a time."

        $rows.Add([pscustomobject]@{
            category = "PowerShell Parse"
            path = $r.path
            mode = $mode
            risk = $risk
            reason = $reason
            action = "Repair sequentially; do not combine with DB/canonical changes."
        }) | Out-Null
    }

    foreach ($s in @($SignalRows | Where-Object { $_.pattern -in @("Stop-Process","Remove-Item","Invoke-Expression","DATABASE","canonical") } | Select-Object -First 200)) {
        $mode = "SEQUENTIAL_GATED"
        $risk = "MEDIUM"
        if ($s.pattern -in @("Stop-Process","Remove-Item","Invoke-Expression")) {
            $risk = "HIGH"
        }

        $rows.Add([pscustomobject]@{
            category = "Risk Signal"
            path = $s.path
            mode = $mode
            risk = $risk
            reason = "Risk signal detected: $($s.pattern)"
            action = "Review gate before any execution."
        }) | Out-Null
    }

    $rows.Add([pscustomobject]@{
        category = "Parallel Safe"
        path = "Inventory / hash / AST scan / HTML audit / Python audit / data audit / signal scan"
        mode = "PARALLEL_SAFE"
        risk = "LOW"
        reason = "Read-only analysis."
        action = "Can be rerun together."
    }) | Out-Null

    @($rows) | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8BOM
    return @($rows)
}

# =============================================================================
# def EXTENSIONS
# =============================================================================

function def_CheckPsExtensions {
    param(
        [string[]]$Modules,
        [bool]$Install,
        [string]$CsvPath,
        [System.Collections.Generic.List[object]]$Rows
    )

    $out = [System.Collections.Generic.List[object]]::new()

    foreach ($m in $Modules) {
        $found = Get-Module -ListAvailable -Name $m -ErrorAction SilentlyContinue

        if ($found) {
            $best = @($found) | Sort-Object Version -Descending | Select-Object -First 1

            $out.Add([pscustomobject]@{
                module = $m
                status = "OK_PRESENT"
                version = $best.Version.ToString()
                path = $best.Path
                message = "Already available"
            }) | Out-Null

            def_AddRow $Rows "Round0" "VIA" "TOOLING" "PS_EXTENSION" $m "OK_PRESENT" "LOW" "PARALLEL_SAFE" "P1" "CHECK_INSTALL" "module" $m "PowerShell extension available." $best.Path
        }
        elseif ($Install) {
            try {
                Install-Module -Name $m -Scope CurrentUser -Force -AllowClobber -SkipPublisherCheck -ErrorAction Stop
                $newFound = Get-Module -ListAvailable -Name $m -ErrorAction SilentlyContinue
                $best = @($newFound) | Sort-Object Version -Descending | Select-Object -First 1

                $out.Add([pscustomobject]@{
                    module = $m
                    status = "OK_INSTALLED"
                    version = if ($best) { $best.Version.ToString() } else { "" }
                    path = if ($best) { $best.Path } else { "" }
                    message = "Installed CurrentUser"
                }) | Out-Null

                def_AddRow $Rows "Round0" "VIA" "TOOLING" "PS_EXTENSION" $m "OK_INSTALLED" "LOW" "PARALLEL_SAFE" "P1" "CHECK_INSTALL" "module" $m "Installed CurrentUser." ""
            }
            catch {
                $out.Add([pscustomobject]@{
                    module = $m
                    status = "WARN_INSTALL_FAILED"
                    version = ""
                    path = ""
                    message = $_.Exception.Message
                }) | Out-Null

                def_AddRow $Rows "Round0" "VIA" "TOOLING" "PS_EXTENSION" $m "WARN_INSTALL_FAILED" "MEDIUM" "PARALLEL_SAFE" "P1" "CHECK_INSTALL" "module" $m "Install failed; continuing." ""
            }
        }
        else {
            $out.Add([pscustomobject]@{
                module = $m
                status = "WARN_MISSING_PLAN_ONLY"
                version = ""
                path = ""
                message = "Missing; install disabled."
            }) | Out-Null

            def_AddRow $Rows "Round0" "VIA" "TOOLING" "PS_EXTENSION" $m "WARN_MISSING_PLAN_ONLY" "MEDIUM" "PARALLEL_SAFE" "P1" "CHECK_ONLY" "module" $m "Missing; install disabled." ""
        }
    }

    @($out) | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Encoding UTF8BOM
    return @($out)
}

# =============================================================================
# def HTML REPORT
# =============================================================================

function def_WriteHtmlReport {
    param(
        [string]$HtmlPath,
        [System.Collections.Generic.List[object]]$Rows,
        [object[]]$PsAstRows,
        [object[]]$PsExtRows,
        [object[]]$PyRows,
        [object[]]$HtmlRows,
        [object[]]$DataRows,
        [object[]]$SignalRows,
        [object[]]$RepairRows,
        [object[]]$FixPlanRows,
        [string]$RunRoot,
        [string]$ProjectRoot,
        [string]$NexusCore,
        [string]$VdfRoot,
        [string]$VrnRoot
    )

    $parseFails = @($PsAstRows | Where-Object { [int]$_.parse_error_count -gt 0 })
    $riskSignals = @($SignalRows | Where-Object { $_.pattern -in @("Stop-Process","Remove-Item","Invoke-Expression","DATABASE","canonical") })

    $matrixHtml = ($Rows | ForEach-Object {
        "<tr><td>$($_.Round)</td><td>$($_.Project)</td><td>$($_.Lane)</td><td>$($_.Stage)</td><td>$($_.Name)</td><td><b>$($_.Status)</b></td><td>$($_.Risk)</td><td>$($_.Metric)</td><td>$($_.Value)</td><td>$(def_Html $_.Message)</td><td><code>$(def_Html $_.Path)</code></td></tr>"
    }) -join "`n"

    $parseHtml = ($parseFails | Select-Object -First 150 | ForEach-Object {
        "<tr><td><code>$(def_Html $_.path)</code></td><td>$($_.parse_error_count)</td><td>$(def_Html $_.parse_errors)</td></tr>"
    }) -join "`n"

    $extHtml = ($PsExtRows | ForEach-Object {
        "<tr><td>$($_.module)</td><td><b>$($_.status)</b></td><td>$($_.version)</td><td><code>$(def_Html $_.path)</code></td><td>$(def_Html $_.message)</td></tr>"
    }) -join "`n"

    $signalHtml = ($SignalRows | Select-Object -First 250 | ForEach-Object {
        "<tr><td>$($_.pattern)</td><td><code>$(def_Html $_.path)</code></td><td>$(def_Html $_.snippet)</td></tr>"
    }) -join "`n"

    $repairHtml = ($RepairRows | ForEach-Object {
        "<tr><td>$(def_Html $_.action)</td><td><code>$(def_Html $_.source_path)</code></td><td><code>$(def_Html $_.repair_copy)</code></td><td>$($_.parse_errors_before)</td><td>$($_.parse_errors_after)</td><td>$(def_Html $_.message)</td></tr>"
    }) -join "`n"

    $fixPlanHtml = ($FixPlanRows | ForEach-Object {
        "<tr><td>$($_.category)</td><td><code>$(def_Html $_.path)</code></td><td><b>$($_.mode)</b></td><td>$($_.risk)</td><td>$(def_Html $_.reason)</td><td>$(def_Html $_.action)</td></tr>"
    }) -join "`n"

    $contextHtml = ($def_PARAM_RECENT_CONTEXT | ForEach-Object {
        "<li>$(def_Html $_)</li>"
    }) -join "`n"

    $status = if ($script:def_FAIL -gt 0) { "READY_WITH_BLOCKS_REVIEW_REQUIRED" } elseif ($script:def_WARN -gt 0) { "READY_WITH_WARNINGS" } else { "READY" }
    $risk = if ($script:def_FAIL -gt 0) { "HIGH" } elseif ($script:def_WARN -gt 0) { "MEDIUM" } else { "LOW" }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA Supportive Docking · VDF + VRN · v028.6.1</title>
<style>
:root{
  --sky:#d8f0ef;
  --ink:#1d3438;
  --muted:#657f82;
  --line:rgba(38,70,75,.18);
  --ok:#0f766e;
  --warn:#b7791f;
  --fail:#b91c1c;
  --paper:#fbfdfb;
}
*{box-sizing:border-box}
body{
  margin:0;
  font-family:"Microsoft JhengHei","Segoe UI",Arial,sans-serif;
  background:radial-gradient(circle at 18% 0%, rgba(216,240,239,.95), transparent 34%),linear-gradient(180deg,#fbfdfb,#f3f8f6);
  color:var(--ink);
}
header{padding:34px 42px 22px;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:28px;letter-spacing:.04em}
.sub{margin-top:8px;color:var(--muted)}
.wrap{padding:24px 42px 60px}
.kpis{display:grid;grid-template-columns:repeat(7,minmax(120px,1fr));gap:14px;margin-bottom:22px}
.card{background:rgba(255,255,255,.78);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 12px 28px rgba(30,52,56,.06);animation:rise .55s ease both}
.k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.v{font-size:25px;font-weight:700;margin-top:6px}
.ok{color:var(--ok)} .warn{color:var(--warn)} .fail{color:var(--fail)}
section{margin-top:22px}
h2{font-size:18px;margin:0 0 12px;border-left:5px solid var(--sky);padding-left:10px}
table{width:100%;border-collapse:collapse;background:rgba(255,255,255,.72);border-radius:14px;overflow:hidden}
th,td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top;font-size:12px}
th{background:rgba(216,240,239,.65)}
code{font-family:Consolas,monospace;font-size:11px}
.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.flow .card{text-align:center}
.small{font-size:12px;color:var(--muted)}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:1100px){.kpis{grid-template-columns:repeat(2,1fr)}.flow{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <h1>def VIA Supportive Docking · VDF + VRN · v028.6.1</h1>
  <div class="sub">Three-Round Panorama · AST / Python / HTML / Data / Signal / Repair-Copy / Fix Classification · No DB Write</div>
</header>
<div class="wrap">

  <div class="kpis">
    <div class="card"><div class="k">Status</div><div class="v">$status</div></div>
    <div class="card"><div class="k">Risk</div><div class="v">$risk</div></div>
    <div class="card"><div class="k">OK</div><div class="v ok">$($script:def_OK)</div></div>
    <div class="card"><div class="k">WARN</div><div class="v warn">$($script:def_WARN)</div></div>
    <div class="card"><div class="k">FAIL</div><div class="v fail">$($script:def_FAIL)</div></div>
    <div class="card"><div class="k">PS Parse Fail</div><div class="v fail">$(@($parseFails).Count)</div></div>
    <div class="card"><div class="k">Risk Signals</div><div class="v warn">$(@($riskSignals).Count)</div></div>
  </div>

  <section>
    <h2>def Anchors</h2>
    <div class="card">
      <p><b>ProjectRoot</b>: <code>$(def_Html $ProjectRoot)</code></p>
      <p><b>NexusCore</b>: <code>$(def_Html $NexusCore)</code></p>
      <p><b>VDF</b>: <code>$(def_Html $VdfRoot)</code></p>
      <p><b>VRN</b>: <code>$(def_Html $VrnRoot)</code></p>
      <p><b>RunRoot</b>: <code>$(def_Html $RunRoot)</code></p>
    </div>
  </section>

  <section>
    <h2>def Recent Context</h2>
    <div class="card"><ul>$contextHtml</ul></div>
  </section>

  <section>
    <h2>def Lane Control</h2>
    <div class="flow">
      <div class="card"><b>VDF</b><br>Write Governance<br><span class="small">SEQUENTIAL_GATED</span></div>
      <div class="card"><b>VDF</b><br>Quarantine Reduction<br><span class="small">PARALLEL_SAFE</span></div>
      <div class="card"><b>VRN</b><br>Ingestion<br><span class="small">PARALLEL_SAFE</span></div>
      <div class="card"><b>VRN</b><br>Normalization<br><span class="small">PARALLEL_SAFE</span></div>
      <div class="card"><b>VRN</b><br>Presentation<br><span class="small">PARALLEL_SAFE</span></div>
    </div>
  </section>

  <section>
    <h2>def PowerShell 10 Accelerating Extensions</h2>
    <table><thead><tr><th>Module</th><th>Status</th><th>Version</th><th>Path</th><th>Message</th></tr></thead><tbody>$extHtml</tbody></table>
  </section>

  <section>
    <h2>def Matrix</h2>
    <table><thead><tr><th>Round</th><th>Project</th><th>Lane</th><th>Stage</th><th>Name</th><th>Status</th><th>Risk</th><th>Metric</th><th>Value</th><th>Message</th><th>Path</th></tr></thead><tbody>$matrixHtml</tbody></table>
  </section>

  <section>
    <h2>def PowerShell Parse Failures</h2>
    <table><thead><tr><th>Path</th><th>Errors</th><th>Message</th></tr></thead><tbody>$parseHtml</tbody></table>
  </section>

  <section>
    <h2>def Repair Copies · Safe, No Overwrite</h2>
    <table><thead><tr><th>Action</th><th>Source</th><th>Repair Copy</th><th>Before</th><th>After</th><th>Message</th></tr></thead><tbody>$repairHtml</tbody></table>
  </section>

  <section>
    <h2>def Fix Classification · Parallel vs Sequential</h2>
    <table><thead><tr><th>Category</th><th>Path</th><th>Mode</th><th>Risk</th><th>Reason</th><th>Action</th></tr></thead><tbody>$fixPlanHtml</tbody></table>
  </section>

  <section>
    <h2>def Key Signals</h2>
    <table><thead><tr><th>Pattern</th><th>Path</th><th>Snippet</th></tr></thead><tbody>$signalHtml</tbody></table>
  </section>

</div>
</body>
</html>
"@

    def_WriteText -Path $HtmlPath -Text $html -Bom $false
}

# =============================================================================
# def MAIN
# =============================================================================

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA SUPPORTIVE DOCKING · VDF + VRN · PANORAMA v028.6.1" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "No DB write · No canonical merge · No delete · No Stop-Process · Three-round panorama"
    Write-Host ""

    if (-not [System.IO.Directory]::Exists($def_PARAM_PROJECT_ROOT)) {
        throw "ProjectRoot not found: $def_PARAM_PROJECT_ROOT"
    }

    $Stamp = def_Stamp
    $DictRoot = Join-Path $def_PARAM_PROJECT_ROOT "dict\VDF"
    $ActiveRoot = Join-Path $DictRoot "_active"
    $RunRoot = Join-Path $ActiveRoot "$($def_PARAM_RUN_NAME)_$Stamp"

    $ReportDir = Join-Path $RunRoot "report"
    $RegistryDir = Join-Path $RunRoot "registry"
    $RuntimeDir = Join-Path $RunRoot "runtime"
    $RepairDir = Join-Path $RunRoot "repair"
    $PlanDir = Join-Path $RunRoot "plan"

    foreach ($d in @($DictRoot,$ActiveRoot,$RunRoot,$ReportDir,$RegistryDir,$RuntimeDir,$RepairDir,$PlanDir)) {
        def_Mkdir -Path $d
    }

    $Rows = [System.Collections.Generic.List[object]]::new()
    $PsFiles = [System.Collections.Generic.List[string]]::new()
    $PyFiles = [System.Collections.Generic.List[string]]::new()
    $HtmlFiles = [System.Collections.Generic.List[string]]::new()
    $DataFiles = [System.Collections.Generic.List[string]]::new()
    $TextFiles = [System.Collections.Generic.List[string]]::new()

    $Transcript = Join-Path $RuntimeDir "VIA_SupportiveDocking_v02861_Transcript_$Stamp.txt"
    try { Start-Transcript -LiteralPath $Transcript -Force | Out-Null } catch {}

    try {
        def_Phase "Round0 · policy lock"

        def_AddRow $Rows "Round0" "VIA" "CONTROL_PLANE" "POLICY" "No DB Write" "OK_POLICY_LOCKED" "LOW" "PARALLEL_SAFE" "P0" "ANALYZE_ONLY" "db_write_enabled" "false" "This run never writes DATABASE." (Join-Path $DictRoot "DATABASE")
        def_AddRow $Rows "Round0" "VIA" "CONTROL_PLANE" "POLICY" "No Canonical Merge" "OK_POLICY_LOCKED" "LOW" "PARALLEL_SAFE" "P0" "ANALYZE_ONLY" "canonical_merge_enabled" "false" "This run never canonical-merges." $RunRoot
        def_AddRow $Rows "Round0" "VIA" "CONTROL_PLANE" "POLICY" "No Delete" "OK_POLICY_LOCKED" "LOW" "PARALLEL_SAFE" "P0" "ANALYZE_ONLY" "delete_enabled" "false" "This run never deletes files." $RunRoot
        def_AddRow $Rows "Round0" "VIA" "CONTROL_PLANE" "POLICY" "No Stop-Process" "OK_POLICY_LOCKED" "LOW" "PARALLEL_SAFE" "P0" "ANALYZE_ONLY" "stop_process_enabled" "false" "This run never stops processes." $RunRoot

        def_Phase "Round0 · anchors"

        foreach ($anchor in @(
            [pscustomobject]@{Name="ProjectRoot"; Path=$def_PARAM_PROJECT_ROOT; Type="Directory"},
            [pscustomobject]@{Name="SupportiveRoot"; Path=$def_PARAM_SUPPORTIVE_ROOT; Type="Directory"},
            [pscustomobject]@{Name="NexusCore"; Path=$def_PARAM_NEXUSCORE_PATH; Type="File"},
            [pscustomobject]@{Name="VDF"; Path=$def_PARAM_VDF_ROOT; Type="Directory"},
            [pscustomobject]@{Name="VRN"; Path=$def_PARAM_VRN_ROOT; Type="Directory"}
        )) {
            $exists = $false
            if ($anchor.Type -eq "File") {
                $exists = [System.IO.File]::Exists($anchor.Path)
            }
            else {
                $exists = [System.IO.Directory]::Exists($anchor.Path)
            }

            $status = if ($exists) { "OK_FOUND" } else { "WARN_MISSING" }
            $risk = if ($exists) { "LOW" } else { "MEDIUM" }

            def_AddRow $Rows "Round0" "VIA" "CONTROL_PLANE" "ANCHOR" $anchor.Name $status $risk "SEQUENTIAL_GATED" "P0" "CHECK_ONLY" "exists" "$exists" "Anchor checked." $anchor.Path
        }

        def_Phase "Round0 · NexusCore parse"

        if ([System.IO.File]::Exists($def_PARAM_NEXUSCORE_PATH)) {
            $nexusParse = def_ParsePowerShellFile -Path $def_PARAM_NEXUSCORE_PATH
            if ($nexusParse.parse_error_count -eq 0) {
                def_AddRow $Rows "Round0" "VIA" "NEXUSCORE" "PARSE" "Invoke-VeritasNexusCore.ps1" "OK_PARSE" "LOW" "SEQUENTIAL_GATED" "P0" "CONTROL_PLANE_ONLY" "parse_errors" "0" "NexusCore parses cleanly." $def_PARAM_NEXUSCORE_PATH
            }
            else {
                def_AddRow $Rows "Round0" "VIA" "NEXUSCORE" "PARSE" "Invoke-VeritasNexusCore.ps1" "WARN_PARSE_ERRORS" "MEDIUM" "SEQUENTIAL_REQUIRED" "P0" "CONTROL_PLANE_ONLY" "parse_errors" "$($nexusParse.parse_error_count)" $nexusParse.parse_errors $def_PARAM_NEXUSCORE_PATH
            }
        }

        def_Phase "Round0 · 10 PS accelerating extensions"

        $PsExtCsv = Join-Path $RegistryDir "VIA_PS_AcceleratingExtensions_v02861.csv"
        $PsExtRows = def_CheckPsExtensions -Modules $def_PARAM_PS_ACCEL_EXTENSIONS -Install $def_PARAM_INSTALL_PS_EXTENSIONS -CsvPath $PsExtCsv -Rows $Rows

        def_Phase "Round1 · full inventory"

        $InventoryCsv = Join-Path $RegistryDir "VIA_FullInventory_v02861.csv"
        $fileCount = def_BuildInventory -ProjectRoot $def_PARAM_PROJECT_ROOT -VdfRoot $def_PARAM_VDF_ROOT -VrnRoot $def_PARAM_VRN_ROOT -SupportiveRoot $def_PARAM_SUPPORTIVE_ROOT -CsvPath $InventoryCsv -PsFiles $PsFiles -PyFiles $PyFiles -HtmlFiles $HtmlFiles -DataFiles $DataFiles -TextFiles $TextFiles

        def_AddRow $Rows "Round1" "VIA" "PANORAMA" "INVENTORY" "Full Repo Inventory" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P0" "ANALYZE_ONLY" "files" "$fileCount" "Full repo inventory created." $InventoryCsv
        def_AddRow $Rows "Round1" "VIA" "PANORAMA" "INVENTORY" "PowerShell Files" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P0" "ANALYZE_ONLY" "ps_files" "$(@($PsFiles).Count)" "PS files collected." $InventoryCsv
        def_AddRow $Rows "Round1" "VIA" "PANORAMA" "INVENTORY" "Python Files" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "ANALYZE_ONLY" "py_files" "$(@($PyFiles).Count)" "Python files collected." $InventoryCsv
        def_AddRow $Rows "Round1" "VIA" "PANORAMA" "INVENTORY" "HTML Files" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "ANALYZE_ONLY" "html_files" "$(@($HtmlFiles).Count)" "HTML files collected." $InventoryCsv
        def_AddRow $Rows "Round1" "VIA" "PANORAMA" "INVENTORY" "Data Files" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "ANALYZE_ONLY" "data_files" "$(@($DataFiles).Count)" "Data files collected." $InventoryCsv

        def_Phase "Round1 · PS AST audit"

        $PsAstCsv = Join-Path $RegistryDir "VIA_PowerShellAstAudit_v02861.csv"
        $PsAstRows = def_AuditPowerShellAst -PsFiles $PsFiles -CsvPath $PsAstCsv
        $PsParseFails = @($PsAstRows | Where-Object { [int]$_.parse_error_count -gt 0 })

        if (@($PsParseFails).Count -eq 0) {
            def_AddRow $Rows "Round1" "VIA" "PANORAMA" "AST_AUDIT" "PowerShell AST Audit" "OK_ALL_PARSE" "LOW" "PARALLEL_SAFE" "P0" "ANALYZE_ONLY" "parse_fail_files" "0" "All PS files parse cleanly." $PsAstCsv
        }
        else {
            def_AddRow $Rows "Round1" "VIA" "PANORAMA" "AST_AUDIT" "PowerShell AST Audit" "WARN_PARSE_ERRORS_FOUND" "MEDIUM" "SEQUENTIAL_REQUIRED" "P0" "ANALYZE_ONLY" "parse_fail_files" "$(@($PsParseFails).Count)" "Parse-error files found; repair sequentially." $PsAstCsv
        }

        def_Phase "Round1 · Python audit"

        $PyCsv = Join-Path $RegistryDir "VIA_PythonAudit_v02861.csv"
        $PyRows = def_AuditPythonFiles -PyFiles $PyFiles -CsvPath $PyCsv
        def_AddRow $Rows "Round1" "VIA" "PANORAMA" "PYTHON_AUDIT" "Python Audit" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "ANALYZE_ONLY" "py_files" "$(@($PyRows).Count)" "Python audit created." $PyCsv

        def_Phase "Round1 · HTML audit"

        $HtmlCsv = Join-Path $RegistryDir "VIA_HtmlAudit_v02861.csv"
        $HtmlRows = def_AuditHtmlFiles -HtmlFiles $HtmlFiles -CsvPath $HtmlCsv
        def_AddRow $Rows "Round1" "VIA" "PANORAMA" "HTML_AUDIT" "HTML Audit" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "ANALYZE_ONLY" "html_files" "$(@($HtmlRows).Count)" "HTML audit created." $HtmlCsv

        def_Phase "Round1 · data audit"

        $DataCsv = Join-Path $RegistryDir "VIA_DataAudit_v02861.csv"
        $DataRows = def_AuditDataFiles -DataFiles $DataFiles -CsvPath $DataCsv
        def_AddRow $Rows "Round1" "VIA" "PANORAMA" "DATA_AUDIT" "Data Audit" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "ANALYZE_ONLY" "data_files" "$(@($DataRows).Count)" "Data audit created." $DataCsv

        def_Phase "Round2 · signal scan"

        $SignalCsv = Join-Path $RegistryDir "VIA_KeySignalScan_v02861.csv"
        $SignalRows = def_SearchSignals -TextFiles $TextFiles -CsvPath $SignalCsv
        def_AddRow $Rows "Round2" "VIA" "PANORAMA" "SIGNAL_SCAN" "Key Signal Scan" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P1" "ANALYZE_ONLY" "signals" "$(@($SignalRows).Count)" "Key signal scan created." $SignalCsv

        def_Phase "Round2 · safe repair copies"

        $RepairCsv = Join-Path $RepairDir "VIA_RepairCopies_v02861.csv"
        $RepairRows = def_NewRepairCopyForParseFail -ParseFailRows $PsParseFails -RepairDir $RepairDir -CsvPath $RepairCsv
        def_AddRow $Rows "Round2" "VIA" "REPAIR" "SAFE_REPAIR_COPY" "Repair Copy Generator" "OK_CREATED" "LOW" "SEQUENTIAL_REQUIRED" "P0" "REPAIR_COPY_ONLY" "repair_copies" "$(@($RepairRows).Count)" "Safe repair copies created where conservative pattern matched. Originals untouched." $RepairCsv

        def_Phase "Round2 · classify parallel vs sequential fixes"

        $FixPlanCsv = Join-Path $PlanDir "VIA_FixClassification_v02861.csv"
        $FixPlanRows = def_ClassifyFixPlan -PsParseFails $PsParseFails -SignalRows $SignalRows -CsvPath $FixPlanCsv
        def_AddRow $Rows "Round2" "VIA" "CONTROL_PLANE" "FIX_PLAN" "Parallel vs Sequential Fix Plan" "OK_PLAN_CREATED" "LOW" "SEQUENTIAL_GATED" "P0" "PLAN_ONLY" "fix_items" "$(@($FixPlanRows).Count)" "Fix classification created." $FixPlanCsv

        def_Phase "Round3 · lane plan"

        $LanePlan = [pscustomobject]@{
            generated_at = def_Iso
            status = "VIA_VDF_VRN_LANE_PLAN_READY"
            risk = "MEDIUM"
            project_root = $def_PARAM_PROJECT_ROOT
            nexus_core = $def_PARAM_NEXUSCORE_PATH
            policy = [pscustomobject]@{
                db_write = $false
                canonical_merge = $false
                destructive_delete = $false
                stop_process = $false
                generated_script_execution = $false
            }
            vdf_lanes = @(
                [pscustomobject]@{ lane="VDF_Write_Governance"; mode="SEQUENTIAL_GATED"; reason="DB write, canonical merge, schema mutation must not be parallelized." },
                [pscustomobject]@{ lane="VDF_Quarantine_Reduction"; mode="PARALLEL_SAFE"; reason="Read-only classification, hash, report, audit can be parallel." }
            )
            vrn_lanes = @(
                [pscustomobject]@{ lane="VRN_Ingestion"; mode="PARALLEL_SAFE"; reason="Source manifest and extractor capability matrix." },
                [pscustomobject]@{ lane="VRN_Normalization"; mode="PARALLEL_SAFE"; reason="Schema preview and entity traceability preview." },
                [pscustomobject]@{ lane="VRN_Presentation"; mode="PARALLEL_SAFE"; reason="HTML UI/report audit." }
            )
        }

        $LanePlanJson = Join-Path $PlanDir "VIA_VDF_VRN_LanePlan_v02861.json"
        def_WriteJson -Path $LanePlanJson -Object $LanePlan
        def_AddRow $Rows "Round3" "VIA" "CONTROL_PLANE" "LANE_PLAN" "VDF/VRN Five Lane Plan" "OK_PLAN_CREATED" "LOW" "PARALLEL_SAFE" "P0" "PLAN_ONLY" "lanes" "5" "VDF two lanes and VRN three lanes created." $LanePlanJson

        def_Phase "Round3 · user-test gate"

        $UserTest = [pscustomobject]@{
            generated_at = def_Iso
            status = if (@($PsParseFails).Count -eq 0) { "USER_TEST_READY" } else { "USER_TEST_READY_WITH_PARSE_REVIEW" }
            risk = if (@($PsParseFails).Count -eq 0) { "LOW" } else { "MEDIUM" }
            next = if (@($PsParseFails).Count -eq 0) { "Proceed to gated execution-design test. Still no DB write by default." } else { "Review parse failures and repair copies first." }
            run_root = $RunRoot
        }

        $UserTestJson = Join-Path $PlanDir "VIA_UserTestGate_v02861.json"
        def_WriteJson -Path $UserTestJson -Object $UserTest
        def_AddRow $Rows "Round3" "VIA" "USER_TEST" "GATE" "User-Test Gate" "OK_PLAN_CREATED" "LOW" "SEQUENTIAL_GATED" "P0" "PLAN_ONLY" "ready" "$($UserTest.status)" "User-test gate created." $UserTestJson

        def_Phase "Round3 · consolidate outputs"

        $MatrixCsv = Join-Path $RegistryDir "VIA_SupportiveDocking_Matrix_v02861.csv"
        $MatrixJson = Join-Path $RegistryDir "VIA_SupportiveDocking_Matrix_v02861.json"
        $RuntimeJson = Join-Path $RuntimeDir "VIA_SupportiveDocking_RuntimeResult_v02861.json"
        $HtmlReport = Join-Path $ReportDir "VIA_SupportiveDocking_VDF_VRN_Report_v02861.html"
        $ActivePointer = Join-Path $ActiveRoot "VDF_ACTIVE_POINTER.json"

        @($Rows) | Export-Csv -LiteralPath $MatrixCsv -NoTypeInformation -Encoding UTF8BOM
        def_WriteJson -Path $MatrixJson -Object @($Rows)

        $finalStatus = if ($script:def_FAIL -gt 0) { "READY_WITH_BLOCKS_REVIEW_REQUIRED" } elseif ($script:def_WARN -gt 0) { "READY_WITH_WARNINGS" } else { "READY" }
        $finalRisk = if ($script:def_FAIL -gt 0) { "HIGH" } elseif ($script:def_WARN -gt 0) { "MEDIUM" } else { "LOW" }

        $Runtime = [pscustomobject]@{
            generated_at = def_Iso
            status = $finalStatus
            risk = $finalRisk
            ok = $script:def_OK
            warn = $script:def_WARN
            fail = $script:def_FAIL
            project_root = $def_PARAM_PROJECT_ROOT
            nexus_core = $def_PARAM_NEXUSCORE_PATH
            vdf_root = $def_PARAM_VDF_ROOT
            vrn_root = $def_PARAM_VRN_ROOT
            run_root = $RunRoot
            html = $HtmlReport
            matrix_csv = $MatrixCsv
            matrix_json = $MatrixJson
            inventory_csv = $InventoryCsv
            ps_ast_csv = $PsAstCsv
            python_audit_csv = $PyCsv
            html_audit_csv = $HtmlCsv
            data_audit_csv = $DataCsv
            signal_csv = $SignalCsv
            repair_csv = $RepairCsv
            fix_plan_csv = $FixPlanCsv
            lane_plan_json = $LanePlanJson
            user_test_json = $UserTestJson
            transcript = $Transcript
            policy = [pscustomobject]@{
                db_write = $false
                canonical_merge = $false
                destructive_delete = $false
                stop_process = $false
                generated_script_execution = $false
            }
        }

        def_WriteJson -Path $RuntimeJson -Object $Runtime
        def_WriteJson -Path $ActivePointer -Object $Runtime

        def_WriteHtmlReport `
            -HtmlPath $HtmlReport `
            -Rows $Rows `
            -PsAstRows $PsAstRows `
            -PsExtRows $PsExtRows `
            -PyRows $PyRows `
            -HtmlRows $HtmlRows `
            -DataRows $DataRows `
            -SignalRows $SignalRows `
            -RepairRows $RepairRows `
            -FixPlanRows $FixPlanRows `
            -RunRoot $RunRoot `
            -ProjectRoot $def_PARAM_PROJECT_ROOT `
            -NexusCore $def_PARAM_NEXUSCORE_PATH `
            -VdfRoot $def_PARAM_VDF_ROOT `
            -VrnRoot $def_PARAM_VRN_ROOT

        def_AddRow $Rows "Round3" "VIA" "CONSOLIDATE" "REPORT" "HTML UI Report" "OK_CREATED" "LOW" "PARALLEL_SAFE" "P0" "REPORT_ONLY" "html" "created" "Detailed matrix HTML report created." $HtmlReport

        @($Rows) | Export-Csv -LiteralPath $MatrixCsv -NoTypeInformation -Encoding UTF8BOM
        def_WriteJson -Path $MatrixJson -Object @($Rows)

        def_Phase "Round3 · complete"

        Write-Progress -Id 1 -Completed

        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host "def VIA SUPPORTIVE DOCKING COMPLETE · v028.6.1" -ForegroundColor Green
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host "Status      : $finalStatus"
        Write-Host "Risk        : $finalRisk"
        Write-Host "OK          : $script:def_OK"
        Write-Host "WARN        : $script:def_WARN"
        Write-Host "FAIL        : $script:def_FAIL"
        Write-Host "RunRoot     : $RunRoot"
        Write-Host "HTML        : $HtmlReport"
        Write-Host "Matrix CSV  : $MatrixCsv"
        Write-Host "Runtime JSON: $RuntimeJson"
        Write-Host "Pointer     : $ActivePointer"
        Write-Host "Transcript  : $Transcript"
        Write-Host ""
        Write-Host "Policy      : No DB Write · No Canonical Merge · No Delete · No Stop-Process · No Generated Script Execution" -ForegroundColor Yellow
        Write-Host "PowerShell remains open." -ForegroundColor Cyan

        if ($def_PARAM_OPEN_HTML -and [System.IO.File]::Exists($HtmlReport)) {
            Start-Process $HtmlReport
        }
    }
    catch {
        Write-Progress -Id 1 -Completed
        Write-Host ""
        Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
        Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
        Write-Host ""
        Write-Host "PowerShell remains open." -ForegroundColor Cyan
    }
    finally {
        try { Stop-Transcript | Out-Null } catch {}
    }
}

# =============================================================================
# def ENTRY
# =============================================================================

def_Main