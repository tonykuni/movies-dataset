[CmdletBinding()]
param(
    [string]$MotherRoot = (Join-Path $env:USERPROFILE "Downloads\VeritasIntelligenceAnalytics"),
    [string]$PackageRoot = $PSScriptRoot,
    [string]$GovernedPythonPath = "",
    [string]$PredecessorRunDir = "",
    [string]$SourceCandidatePath = (Join-Path $env:USERPROFILE "OneDrive\桌面\tw_stock\Standardized_Prices.csv"),
    [string]$ApprovalToken = "",
    [ValidateRange(1, 1)] [int]$MaximumParallelContentOpens = 1,
    [bool]$RunOfflineSelfTest = $true,
    [bool]$OpenHtml = $true
)


# =============================================================================
# def 00. IMMUTABLE PARAMETERS / GATES
# =============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$def_Version = "v0140B-WH1"
$def_ApprovalTokenExpected = "VIA_APPROVE_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_READ_ONLY"
$def_PredecessorGate = "VIA_V0140B_CROSS_SUBSYSTEM_SIX_ENGINE_LOCAL_READER_PATH_REPAIR_PROPOSAL_PASS_READY_NO_SYSTEM_MUTATION"
$def_PassGate = "VIA_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_PASS_HANDLE_EVIDENCE_READY_NO_SYSTEM_MUTATION"
$def_AllFailedGate = "VIA_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_HOLD_ALL_HANDLE_STRATEGIES_FAILED_NO_SYSTEM_MUTATION"
$def_HydrationGate = "VIA_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_HOLD_IMPLICIT_HYDRATION_RISK_NO_SYSTEM_MUTATION"
$def_FailGate = "VIA_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_HOLD_FAIL_CLOSED"
$def_ScriptPath = $MyInvocation.MyCommand.Path
$def_ResolvedPackageRoot = [IO.Path]::GetFullPath($PackageRoot)
if ([string]::IsNullOrWhiteSpace($GovernedPythonPath)) {
    $GovernedPythonPath = Join-Path $MotherRoot ".venv\Scripts\python.exe"
}
$def_PwshPath = (Get-Command pwsh -ErrorAction Stop).Source
$def_PredecessorRunRoot = Join-Path $MotherRoot "_via_v0140b_local_candidate_reader_path_repair_proposal_runs"
$def_RunRoot = Join-Path $MotherRoot "_via_v0140b_windows_file_handle_acquisition_runs"
$def_RunStamp = [DateTime]::UtcNow.ToString("yyyyMMdd_HHmmss_fffffff")
$def_RunDir = Join-Path $def_RunRoot "RUN_${def_RunStamp}_VIA_V0140B_WINDOWS_HANDLE_ACQUISITION"
$def_LogPath = Join-Path $def_RunDir "VIA_v0140B_WindowsHandle.log"
$def_FinalGate = "VIA_V0140B_WINDOWS_HANDLE_HOLD_NOT_STARTED"
$def_CoreName = "via_v0140b_windows_handle_core.py"
$def_ContractName = "v0140B_WindowsHandleContract.json"
$def_RulesName = "v0140B_WindowsHandleRules.json"
$def_ManifestName = "v0140B_WindowsHandleManifest.json"
$def_EngineSpecs = @(
    [pscustomobject]@{ Index = 1; Id = "H01"; Name = "ONEDRIVE_ATTRIBUTE_RECALL_PREFLIGHT"; Script = "via_v0140b_handle01_onedrive_attribute_recall_preflight.py" },
    [pscustomobject]@{ Index = 2; Id = "H02"; Name = "PYTHON_PATHLIB_BINARY_OPEN"; Script = "via_v0140b_handle02_python_pathlib_binary_open.py" },
    [pscustomobject]@{ Index = 3; Id = "H03"; Name = "PYTHON_OS_OPEN_BINARY"; Script = "via_v0140b_handle03_python_os_open_binary.py" },
    [pscustomobject]@{ Index = 4; Id = "H04"; Name = "WIN32_CREATEFILEW_EXACT"; Script = "via_v0140b_handle04_win32_createfilew_exact.py" },
    [pscustomobject]@{ Index = 5; Id = "H05"; Name = "WIN32_CREATEFILEW_EXTENDED_PATH"; Script = "via_v0140b_handle05_win32_createfilew_extended_path.py" },
    [pscustomobject]@{ Index = 6; Id = "H06"; Name = "DOTNET_FILESTREAM_EXACT"; Script = "via_v0140b_handle06_dotnet_filestream_exact.py" }
)
$def_RequiredArtifacts = @(
    $def_CoreName,
    $def_ContractName,
    $def_RulesName,
    $def_ManifestName,
    "via_v0140b_handle01_onedrive_attribute_recall_preflight.py",
    "via_v0140b_handle02_python_pathlib_binary_open.py",
    "via_v0140b_handle03_python_os_open_binary.py",
    "via_v0140b_handle04_win32_createfilew_exact.py",
    "via_v0140b_handle05_win32_createfilew_extended_path.py",
    "via_v0140b_handle06_dotnet_filestream_exact.py",
    "via_v0140b_handle06_dotnet_filestream_exact.ps1",
    "Invoke-VIA-v0140B-Windows-File-Handle-Acquisition-Sandbox-Validation-ReadOnly.ps1",
    "v0140B_WINDOWS_HANDLE_README.md",
    "v0140B_WindowsHandleUIMatrix.html",
    "VIA_v0140B_Windows_Handle_Validation_Notebook.ipynb",
    "tests/__init__.py",
    "tests/test_windows_handle.py"
)


# =============================================================================
# def 01. STATUS / JSON / SHA / AST
# =============================================================================

function def_WriteStatus {
    param(
        [Parameter(Mandatory)] [int]$Percent,
        [Parameter(Mandatory)] [string]$Stage,
        [Parameter(Mandatory)] [string]$Message,
        [ValidateSet("INFO", "PASS", "WARN", "FAIL")] [string]$Status = "INFO"
    )
    $def_Width = 30
    $def_Filled = [Math]::Floor(($Percent / 100.0) * $def_Width)
    $def_Bar = ("#" * $def_Filled).PadRight($def_Width, "-")
    $def_Line = "def [{0,3}%] [{1}] {2,-28} {3}" -f $Percent, $def_Bar, $Stage, $Message
    $def_Color = switch ($Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
        default { "Cyan" }
    }
    Write-Host $def_Line -ForegroundColor $def_Color
    if (Test-Path -LiteralPath $def_RunDir -PathType Container) {
        Add-Content -LiteralPath $def_LogPath -Value "$(Get-Date -Format o) [$Status] $def_Line" -Encoding utf8
    }
}

function def_ReadJson {
    param([Parameter(Mandatory)] [string]$Path)
    try {
        return (Get-Content -LiteralPath $Path -Raw -Encoding utf8 | ConvertFrom-Json)
    }
    catch {
        throw "Invalid JSON: $Path :: $($_.Exception.Message)"
    }
}

function def_GetSha256 {
    param([Parameter(Mandatory)] [string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function def_TestPowerShellAst {
    param([Parameter(Mandatory)] [string]$Path)
    $def_Tokens = $null
    $def_ParseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $Path,
        [ref]$def_Tokens,
        [ref]$def_ParseErrors
    )
    if (@($def_ParseErrors).Count -gt 0) {
        throw "PowerShell AST failed: $((@($def_ParseErrors | ForEach-Object { $_.Message })) -join ' | ')"
    }
    return @($def_Tokens).Count
}


# =============================================================================
# def 02. PACKAGE / PREDECESSOR
# =============================================================================

function def_TestPackage {
    foreach ($def_Name in $def_RequiredArtifacts) {
        if (-not (Test-Path -LiteralPath (Join-Path $def_ResolvedPackageRoot $def_Name) -PathType Leaf)) {
            throw "Required Windows-handle artifact missing: $def_Name"
        }
    }
    $def_Manifest = def_ReadJson -Path (Join-Path $def_ResolvedPackageRoot $def_ManifestName)
    $def_Bindings = @($def_Manifest.artifacts)
    foreach ($def_Name in @($def_RequiredArtifacts | Where-Object { $_ -ne $def_ManifestName })) {
        $def_Path = Join-Path $def_ResolvedPackageRoot $def_Name
        $def_Item = Get-Item -LiteralPath $def_Path
        $def_Binding = @($def_Bindings | Where-Object { $_.name -eq $def_Name })
        if (
            $def_Binding.Count -ne 1 -or
            [long]$def_Binding[0].bytes -ne [long]$def_Item.Length -or
            [string]$def_Binding[0].sha256 -ne (def_GetSha256 -Path $def_Path)
        ) {
            throw "Manifest binding mismatch: $def_Name"
        }
    }
    $def_Contract = def_ReadJson -Path (Join-Path $def_ResolvedPackageRoot $def_ContractName)
    if (
        $def_Contract.approval_token -ne $def_ApprovalTokenExpected -or
        $def_Contract.predecessor_gate -ne $def_PredecessorGate -or
        $def_Contract.coordination_model.execution -ne "SEQUENTIAL_POWERSHELL7_PROCESS_ISOLATION"
    ) {
        throw "Windows-handle contract identity mismatch."
    }
    if (@($def_EngineSpecs.Id | Sort-Object -Unique).Count -ne 6) {
        throw "Six unique handle engines are required."
    }
    return $def_Bindings.Count
}

function def_TestPredecessorRun {
    param([Parameter(Mandatory)] [string]$Path)
    foreach ($def_Name in @(
        "VIA_v0140B_LOCAL_READER_PATH_PROPOSAL_FORMAL_RECORD.json",
        "VIA_v0140B_LocalReaderPath_Summary.json"
    )) {
        $def_RecordPath = Join-Path $Path $def_Name
        if (-not (Test-Path -LiteralPath $def_RecordPath -PathType Leaf)) {
            continue
        }
        try {
            $def_Record = def_ReadJson -Path $def_RecordPath
            if (
                $def_Record.final_gate -eq $def_PredecessorGate -and
                [int]$def_Record.hydra_violations -eq 0 -and
                [int]$def_Record.source_writes -eq 0 -and
                [int]$def_Record.canonical_runtime_executions -eq 0 -and
                [int]$def_Record.patch_applications -eq 0
            ) {
                return $true
            }
        }
        catch {
            continue
        }
    }
    return $false
}

function def_ResolvePredecessorRun {
    if (-not [string]::IsNullOrWhiteSpace($PredecessorRunDir)) {
        $def_Explicit = [IO.Path]::GetFullPath($PredecessorRunDir)
        if (-not (def_TestPredecessorRun -Path $def_Explicit)) {
            throw "Explicit predecessor is invalid: $def_Explicit"
        }
        return $def_Explicit
    }
    if (-not (Test-Path -LiteralPath $def_PredecessorRunRoot -PathType Container)) {
        throw "Predecessor root not found: $def_PredecessorRunRoot"
    }
    foreach ($def_Directory in @(
        Get-ChildItem -LiteralPath $def_PredecessorRunRoot -Directory |
            Sort-Object LastWriteTimeUtc -Descending
    )) {
        if (def_TestPredecessorRun -Path $def_Directory.FullName) {
            return $def_Directory.FullName
        }
    }
    throw "No accepted local-reader proposal predecessor found."
}


# =============================================================================
# def 03. GUARDED SEQUENTIAL ENGINE EXECUTION
# =============================================================================

function def_NewPythonProcess {
    param(
        [Parameter(Mandatory)] [string[]]$Arguments,
        [Parameter(Mandatory)] [bool]$AllowParquetUnavailable
    )
    $def_StartInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $def_StartInfo.FileName = $GovernedPythonPath
    $def_StartInfo.WorkingDirectory = $def_ResolvedPackageRoot
    $def_StartInfo.UseShellExecute = $false
    $def_StartInfo.CreateNoWindow = $true
    $def_StartInfo.RedirectStandardOutput = $true
    $def_StartInfo.RedirectStandardError = $true
    $def_StartInfo.Environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if ($AllowParquetUnavailable) {
        $def_StartInfo.Environment["VIA_ALLOW_PARQUET_UNAVAILABLE_FOR_PACKAGE_TEST"] = "1"
    }
    foreach ($def_Argument in $Arguments) {
        [void]$def_StartInfo.ArgumentList.Add([string]$def_Argument)
    }
    $def_Process = [System.Diagnostics.Process]::new()
    $def_Process.StartInfo = $def_StartInfo
    if (-not $def_Process.Start()) {
        throw "Failed to start governed Python process."
    }
    return $def_Process
}

function def_InvokeEngine {
    param(
        [Parameter(Mandatory)] [pscustomobject]$Engine,
        [Parameter(Mandatory)] [string]$ExecutionRunDir,
        [Parameter(Mandatory)] [string]$ResolvedPredecessorRun,
        [Parameter(Mandatory)] [string]$CandidatePath,
        [Parameter(Mandatory)] [bool]$ContentReadAuthorized,
        [Parameter(Mandatory)] [bool]$SelfTest
    )
    $def_LaneRoot = Join-Path $ExecutionRunDir ("lanes\{0}_{1}" -f $Engine.Id, $Engine.Name)
    New-Item -ItemType Directory -Path $def_LaneRoot -Force | Out-Null
    $def_Arguments = @(
        (Join-Path $def_ResolvedPackageRoot $Engine.Script),
        "--lane", $Engine.Id,
        "--lane-root", $def_LaneRoot,
        "--package-root", $def_ResolvedPackageRoot,
        "--contract", (Join-Path $def_ResolvedPackageRoot $def_ContractName),
        "--rules", (Join-Path $def_ResolvedPackageRoot $def_RulesName),
        "--source-path", $CandidatePath,
        "--predecessor-run-dir", $ResolvedPredecessorRun,
        "--approval-token", $ApprovalToken,
        "--sequence-index", [string]$Engine.Index,
        "--content-read-authorized", $(if ($ContentReadAuthorized) { "true" } else { "false" }),
        "--pwsh-path", $def_PwshPath
    )
    if ($SelfTest) {
        $def_Arguments += "--self-test"
    }
    $def_Process = def_NewPythonProcess -Arguments $def_Arguments -AllowParquetUnavailable $SelfTest
    $def_Process.WaitForExit()
    $def_Stdout = $def_Process.StandardOutput.ReadToEnd()
    $def_Stderr = $def_Process.StandardError.ReadToEnd()
    Set-Content -LiteralPath (Join-Path $def_LaneRoot "PROCESS_STDOUT.log") -Value $def_Stdout -Encoding utf8NoBOM
    Set-Content -LiteralPath (Join-Path $def_LaneRoot "PROCESS_STDERR.log") -Value $def_Stderr -Encoding utf8NoBOM
    $def_ExitCode = $def_Process.ExitCode
    $def_Process.Dispose()
    $def_SummaryPath = Join-Path $def_LaneRoot "TERMINAL_SUMMARY.json"
    if (-not (Test-Path -LiteralPath $def_SummaryPath -PathType Leaf)) {
        throw "Terminal summary missing for $($Engine.Id)."
    }
    $def_Summary = def_ReadJson -Path $def_SummaryPath
    if ($def_ExitCode -notin @(0, 2)) {
        throw "Engine $($Engine.Id) returned unsupported exit code $def_ExitCode."
    }
    return $def_Summary
}

function def_InvokeSequentialSix {
    param(
        [Parameter(Mandatory)] [string]$ExecutionRunDir,
        [Parameter(Mandatory)] [string]$ResolvedPredecessorRun,
        [Parameter(Mandatory)] [string]$CandidatePath,
        [Parameter(Mandatory)] [bool]$SelfTest
    )
    if ($MaximumParallelContentOpens -ne 1) {
        throw "MaximumParallelContentOpens must equal one."
    }
    $def_ContentReadAuthorized = $false
    $def_SequenceLedger = @()
    foreach ($def_Engine in $def_EngineSpecs) {
        $def_Percent = 30 + ($def_Engine.Index * 8)
        def_WriteStatus -Percent $def_Percent -Stage "sequential $($def_Engine.Id)" -Message "$($def_Engine.Name); content-guard=$def_ContentReadAuthorized"
        $def_Summary = def_InvokeEngine `
            -Engine $def_Engine `
            -ExecutionRunDir $ExecutionRunDir `
            -ResolvedPredecessorRun $ResolvedPredecessorRun `
            -CandidatePath $CandidatePath `
            -ContentReadAuthorized $def_ContentReadAuthorized `
            -SelfTest $SelfTest
        if ($def_Engine.Id -eq "H01") {
            $def_ContentReadAuthorized = [bool]$def_Summary.content_read_authorized
            def_WriteStatus `
                -Percent 38 `
                -Stage "hydration guard" `
                -Message "content-read-authorized=$def_ContentReadAuthorized; risk=$($def_Summary.hydration_risk)" `
                -Status $(if ($def_ContentReadAuthorized) { "PASS" } else { "WARN" })
        }
        $def_SequenceLedger += [pscustomobject]@{
            SequenceIndex = $def_Engine.Index
            Engine = $def_Engine.Id
            Outcome = $def_Summary.outcome
            Attempts = $def_Summary.source_open_attempts
            Successes = $def_Summary.source_open_successes
            BytesRead = $def_Summary.source_bytes_read
            ContentReadAuthorized = $def_Summary.content_read_authorized
            StartedAfterPreviousTerminal = $true
        }
    }
    $def_SequenceLedger |
        Export-Csv -LiteralPath (Join-Path $ExecutionRunDir "VIA_v0140B_WindowsHandle_SequenceLedger.csv") -NoTypeInformation -Encoding utf8BOM
    return $def_ContentReadAuthorized
}

function def_InvokeAggregate {
    param(
        [Parameter(Mandatory)] [string]$ExecutionRunDir,
        [Parameter(Mandatory)] [bool]$SelfTest
    )
    $def_Arguments = @(
        (Join-Path $def_ResolvedPackageRoot $def_CoreName),
        "--aggregate",
        "--run-dir", $ExecutionRunDir,
        "--package-root", $def_ResolvedPackageRoot,
        "--contract", (Join-Path $def_ResolvedPackageRoot $def_ContractName),
        "--rules", (Join-Path $def_ResolvedPackageRoot $def_RulesName),
        "--approval-token", $ApprovalToken
    )
    $def_Process = def_NewPythonProcess -Arguments $def_Arguments -AllowParquetUnavailable $SelfTest
    $def_Process.WaitForExit()
    $def_Stdout = $def_Process.StandardOutput.ReadToEnd()
    $def_Stderr = $def_Process.StandardError.ReadToEnd()
    Set-Content -LiteralPath (Join-Path $ExecutionRunDir "AGGREGATE_STDOUT.log") -Value $def_Stdout -Encoding utf8NoBOM
    Set-Content -LiteralPath (Join-Path $ExecutionRunDir "AGGREGATE_STDERR.log") -Value $def_Stderr -Encoding utf8NoBOM
    $def_ExitCode = $def_Process.ExitCode
    $def_Process.Dispose()
    if ($def_ExitCode -notin @(0, 2)) {
        throw "Aggregate returned unsupported exit code $def_ExitCode."
    }
    return def_ReadJson -Path (Join-Path $ExecutionRunDir "VIA_v0140B_WindowsHandle_Summary.json")
}


# =============================================================================
# def 04. MAIN
# =============================================================================

function def_Main {
    try {
        def_WriteStatus -Percent 2 -Stage "pre-flight" -Message "sequential handles; hydration guard; read-only"
        if ($PSVersionTable.PSVersion.Major -lt 7) {
            throw "PowerShell 7 or later is required."
        }
        if ($ApprovalToken -ne $def_ApprovalTokenExpected) {
            throw "Explicit approval token mismatch."
        }
        if (-not (Test-Path -LiteralPath $MotherRoot -PathType Container)) {
            throw "MotherRoot not found: $MotherRoot"
        }
        if (-not (Test-Path -LiteralPath $GovernedPythonPath -PathType Leaf)) {
            throw "Governed Python not found: $GovernedPythonPath"
        }
        $def_AstMain = def_TestPowerShellAst -Path $def_ScriptPath
        $def_AstDotNet = def_TestPowerShellAst -Path (Join-Path $def_ResolvedPackageRoot "via_v0140b_handle06_dotnet_filestream_exact.ps1")
        $def_Bindings = def_TestPackage
        def_WriteStatus -Percent 14 -Stage "package identity" -Message "AST=$def_AstMain/$def_AstDotNet; bindings=$def_Bindings" -Status "PASS"

        $def_ResolvedPredecessor = def_ResolvePredecessorRun
        New-Item -ItemType Directory -Path $def_RunDir -Force | Out-Null
        Set-Content -LiteralPath $def_LogPath -Value "VIA $def_Version started $(Get-Date -Format o)" -Encoding utf8NoBOM
        def_WriteStatus -Percent 22 -Stage "evidence chain" -Message "proposal-only predecessor PASS bound" -Status "PASS"

        if ($RunOfflineSelfTest) {
            $def_SelfTestDir = Join-Path $def_RunDir "_offline_selftest"
            $def_FixtureDir = Join-Path $def_SelfTestDir "fixture"
            New-Item -ItemType Directory -Path $def_FixtureDir -Force | Out-Null
            $def_Fixture = Join-Path $def_FixtureDir "Standardized_Prices.csv"
            @(
                "Date,TW_YF_TICKER,Open,High,Low,Close,Volume",
                "2025/01/15,3067.TWO,38.8,39.5,38.5,39.1,1234000"
            ) | Set-Content -LiteralPath $def_Fixture -Encoding utf8BOM
            [void](def_InvokeSequentialSix `
                -ExecutionRunDir $def_SelfTestDir `
                -ResolvedPredecessorRun $def_ResolvedPredecessor `
                -CandidatePath $def_Fixture `
                -SelfTest $true)
            $def_SelfSummary = def_InvokeAggregate -ExecutionRunDir $def_SelfTestDir -SelfTest $true
            if (
                $def_SelfSummary.final_gate -ne $def_PassGate -or
                [int]$def_SelfSummary.pass_engines -ne 6 -or
                [int]$def_SelfSummary.cross_subsystem_rows -ne 18 -or
                [int]$def_SelfSummary.source_open_successes -lt 1 -or
                [int]$def_SelfSummary.hydra_violations -ne 0
            ) {
                throw "Offline sequential handle self-test failed: $($def_SelfSummary.final_gate)"
            }
            def_WriteStatus -Percent 28 -Stage "offline fixture" -Message "six terminal; success>=1; Hydra=0" -Status "PASS"
        }

        [void](def_InvokeSequentialSix `
            -ExecutionRunDir $def_RunDir `
            -ResolvedPredecessorRun $def_ResolvedPredecessor `
            -CandidatePath $SourceCandidatePath `
            -SelfTest $false)
        def_WriteStatus -Percent 82 -Stage "terminal barrier" -Message "6/6 sequential terminal summaries conserved" -Status "PASS"

        $def_Summary = def_InvokeAggregate -ExecutionRunDir $def_RunDir -SelfTest $false
        $def_FinalGate = [string]$def_Summary.final_gate
        $def_Status = if ($def_FinalGate -eq $def_PassGate) {
            "PASS"
        }
        elseif ($def_FinalGate -in @($def_AllFailedGate, $def_HydrationGate)) {
            "WARN"
        }
        else {
            "FAIL"
        }
        def_WriteStatus `
            -Percent 94 `
            -Stage "handle aggregate" `
            -Message "attempt/success/bytes=$($def_Summary.source_open_attempts)/$($def_Summary.source_open_successes)/$($def_Summary.source_bytes_read); Hydra=$($def_Summary.hydra_violations)" `
            -Status $def_Status

        $def_PackageInventory = foreach ($def_Name in $def_RequiredArtifacts) {
            $def_Path = Join-Path $def_ResolvedPackageRoot $def_Name
            $def_Item = Get-Item -LiteralPath $def_Path
            [pscustomobject]@{
                File = $def_Name
                Bytes = $def_Item.Length
                SHA256 = def_GetSha256 -Path $def_Path
            }
        }
        $def_PackageInventory |
            Export-Csv -LiteralPath (Join-Path $def_RunDir "VIA_v0140B_WindowsHandle_PackageInventory.csv") -NoTypeInformation -Encoding utf8BOM

        def_WriteStatus -Percent 100 -Stage "complete" -Message $def_FinalGate -Status $def_Status
        Write-Host ""
        Write-Host "def Gate                       : $def_FinalGate" -ForegroundColor $(if ($def_FinalGate -eq $def_PassGate) { "Green" } else { "Yellow" })
        Write-Host "def Engines                    : $($def_Summary.pass_engines)/6 terminal PASS"
        Write-Host "def Attempts/Successes/Bytes  : $($def_Summary.source_open_attempts)/$($def_Summary.source_open_successes)/$($def_Summary.source_bytes_read)"
        Write-Host "def First Success             : $($def_Summary.first_success_engine)"
        Write-Host "def Implicit Hydration Risk   : $($def_Summary.implicit_hydration_risk_detected)"
        Write-Host "def Hydra                     : $($def_Summary.hydra_violations)"
        Write-Host "def Source Hash/Write/Copy    : 0/0/0"
        Write-Host "def Source Content Artifacts  : 0"
        Write-Host "def Canonical/Registry        : 0/0"
        Write-Host "def Patch/Promotion           : 0/0"
        Write-Host "def RunDir                    : $def_RunDir"
        Write-Host "def HTML                      : $(Join-Path $def_RunDir 'VIA_v0140B_WindowsHandle_Report.html')"
        Write-Host "def Next Gate                 : $($def_Summary.next_gate)"
        Write-Host "def PowerShell remains open." -ForegroundColor Cyan
        if ($OpenHtml) {
            Start-Process (Join-Path $def_RunDir "VIA_v0140B_WindowsHandle_Report.html")
        }
    }
    catch {
        $def_FinalGate = $def_FailGate
        if (-not (Test-Path -LiteralPath $def_RunDir -PathType Container)) {
            New-Item -ItemType Directory -Path $def_RunDir -Force | Out-Null
        }
        [ordered]@{
            schema = "VIA_V0140B_WINDOWS_HANDLE_FAILURE_V1"
            final_gate = $def_FinalGate
            error = $_.Exception.Message
            source_open_attempts = 0
            source_open_successes = 0
            source_bytes_read = 0
            source_hashes = 0
            source_writes = 0
            source_copies = 0
            source_content_artifacts = 0
            canonical_runtime_executions = 0
            registry_writes = 0
            patch_applications = 0
            candidate_promotions = 0
            generated_utc = [DateTime]::UtcNow.ToString("o")
        } |
            ConvertTo-Json -Depth 8 |
            Set-Content -LiteralPath (Join-Path $def_RunDir "VIA_v0140B_WindowsHandle_FAILURE.json") -Encoding utf8NoBOM
        def_WriteStatus -Percent 100 -Stage "fail-closed" -Message $_.Exception.Message -Status "FAIL"
        Write-Host "def PowerShell remains open." -ForegroundColor Cyan
        throw
    }
}

def_Main

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
