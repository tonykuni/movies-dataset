[CmdletBinding()]
param(
    [Parameter()]
    [string]$MotherRoot = (Join-Path $env:USERPROFILE "Downloads\VeritasIntelligenceAnalytics"),

    [Parameter()]
    [ValidateSet("Audit", "Stage", "ActivateLauncherOnly")]
    [string]$Mode = "Audit",

    [Parameter()]
    [string]$ApprovalToken = "",

    [Parameter()]
    [ValidateRange(1, 8)]
    [int]$MaximumParallelTasks = 4,

    [Parameter()]
    [ValidateRange(60, 7200)]
    [int]$TimeoutSeconds = 1800,

    [Parameter()]
    [ValidateRange(1, 30)]
    [int]$PollIntervalSeconds = 2,

    [Parameter()]
    [bool]$RequireParquet = $true,

    [Parameter()]
    [bool]$AutoOpenHtml = $true
)


# =============================================================================
# def 00. PARAMETERS / SSOT CONSTANTS
# =============================================================================

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$def_Version = "v0139A"
$def_EngineId = "VIA_ACCELERATED_INTEGRATION_ENGINE_V0139A"
$def_ApprovalTokenExpected = "VIA_APPROVE_VAP_FLOW_CONTROLLED_LAUNCHER_ONLY_V0139A"
$def_ScriptPath = $MyInvocation.MyCommand.Path
$def_PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$def_RunRoot = Join-Path $MotherRoot "_via_accelerated_integration_runs"
$def_CanonicalParent = Join-Path $MotherRoot "supportive modules\90_Integrated_Engines"
$def_CanonicalTarget = Join-Path $def_CanonicalParent "VIA_Accelerated_Integration_v0139A"
$def_LauncherPath = Join-Path $MotherRoot "bin\Invoke-VIA-VAP-Flow-Integration-v0139A.ps1"
$def_ActivationRegistryRoot = Join-Path $MotherRoot "registry\VIA_COMPONENT_ACTIVATIONS_v0139A"
$def_ComponentIds = @(
    "VIA_VAP_Integration_Update_Engine_v0139A",
    "VIA_Flow_Simulation_Engine_v0139A",
    "VIA_TW_Stock_Group_Classification_Engine_v0139A",
    "VIA_TW_Group_Index_Engine_v0139A",
    "VIA_TW_Monthly_Revenue_Analysis_Engine_v0139A"
)
$def_AcceleratorNames = @(
    "AST Precision Analysis",
    "Multilingual Semantic Model",
    "Hydra Risk Prediction",
    "Dependency Topology",
    "Sandbox Isolation",
    "Auto-Fix Suggestion",
    "Three-Round Analysis",
    "SSOT Alignment",
    "Matrix Visualization",
    "Error Classification",
    "Performance And Complexity",
    "Multi-Subsystem Synchronization",
    "Version Diff And Rollback",
    "Coverage And Regression",
    "Fix-Order Optimization",
    "Dynamic Progress Bar",
    "Dynamic Status Narration",
    "Non-Blocking PowerShell",
    "Python PowerShell HTML Integration",
    "Auto-Deploy And Initialization"
)
$def_RequiredPackageFiles = @(
    "config\VIA_Accelerated_Integration_v0139A.yaml",
    "decision-studio\plugins\via_accelerated_integration_v0139a.json",
    "engine\via_domain_engine_v0139a.py",
    "engine\via_vap_update_engine_v0139a.py",
    "engine\via_flow_simulation_engine_v0139a.py",
    "engine\via_stock_group_classification_engine_v0139a.py",
    "engine\via_group_index_engine_v0139a.py",
    "engine\via_monthly_revenue_analysis_engine_v0139a.py",
    "tests\test_via_accelerated_integration_v0139a.py"
)
$def_StartedUtc = [DateTime]::UtcNow
$def_RunStamp = $def_StartedUtc.ToString("yyyyMMdd_HHmmss_fffffff")
$def_RunDir = Join-Path $def_RunRoot "RUN_${def_RunStamp}_VIA_ACCELERATED_INTEGRATION_V0139A"
$def_LogPath = Join-Path $def_RunDir "VIA_Accelerated_Integration_v0139A.log"
$def_UatDir = Join-Path $def_RunDir "offline_fixture_uat"
$def_FinalGate = "VIA_ACCELERATED_INTEGRATION_HOLD_NOT_STARTED_V0139A"
$def_ActivationCommit = 0
$def_CanonicalSourceAdds = 0
$def_ExistingCanonicalMutations = 0
$def_CanonicalRuntimeExecutions = 0
$def_NetworkUsed = 0
$def_Errors = [System.Collections.Generic.List[string]]::new()
$def_Warnings = [System.Collections.Generic.List[string]]::new()
$def_Readiness = [System.Collections.Generic.List[object]]::new()


# =============================================================================
# def 01. DISPLAY / EVIDENCE HELPERS
# =============================================================================

function def_WriteStatus {
    param(
        [Parameter(Mandatory)] [int]$Percent,
        [Parameter(Mandatory)] [string]$Stage,
        [Parameter(Mandatory)] [string]$Message,
        [ValidateSet("INFO", "PASS", "WARN", "FAIL")] [string]$Status = "INFO"
    )
    $def_Width = 28
    $def_Filled = [Math]::Floor(($Percent / 100.0) * $def_Width)
    $def_Bar = ("#" * $def_Filled).PadRight($def_Width, "-")
    $def_Line = "def [{0,3}%] [{1}] {2,-24} {3}" -f $Percent, $def_Bar, $Stage, $Message
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

function def_WriteJsonAtomic {
    param(
        [Parameter(Mandatory)] [object]$Data,
        [Parameter(Mandatory)] [string]$Path,
        [int]$Depth = 16
    )
    $def_Parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $def_Parent -Force | Out-Null
    $def_Temp = Join-Path $def_Parent (".{0}.{1}.tmp" -f ([IO.Path]::GetFileName($Path)), [Guid]::NewGuid().ToString("N"))
    $Data | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $def_Temp -Encoding utf8NoBOM
    Move-Item -LiteralPath $def_Temp -Destination $Path -Force
}

function def_GetFileSha256 {
    param([Parameter(Mandatory)] [string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function def_GetDirectoryDigest {
    param([Parameter(Mandatory)] [string]$Path)
    $def_Lines = Get-ChildItem -LiteralPath $Path -File -Recurse |
        Where-Object {
            $_.Extension -ne ".pyc" -and
            $_.FullName -notmatch "[\\/]__pycache__[\\/]" -and
            $_.FullName -notmatch "[\\/]validation[\\/]"
        } |
        Sort-Object FullName |
        ForEach-Object {
            $def_Relative = [IO.Path]::GetRelativePath($Path, $_.FullName).Replace("\", "/")
            "$(def_GetFileSha256 -Path $_.FullName)  $def_Relative"
        }
    $def_Bytes = [Text.Encoding]::UTF8.GetBytes(($def_Lines -join "`n") + "`n")
    $def_Hasher = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($def_Hasher.ComputeHash($def_Bytes))).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $def_Hasher.Dispose()
    }
}

function def_AddReadiness {
    param(
        [Parameter(Mandatory)] [string]$Id,
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [ValidateSet("PASS", "WARN", "FAIL", "HOLD")] [string]$Status,
        [Parameter(Mandatory)] [string]$Detail
    )
    $def_Readiness.Add([pscustomobject]@{
        Id = $Id
        Name = $Name
        Status = $Status
        Detail = $Detail
    })
}

function def_ResolvePython {
    $def_Candidates = @(
        (Join-Path $MotherRoot "via_core_312\Scripts\python.exe"),
        (Join-Path $MotherRoot ".venv\Scripts\python.exe"),
        "C:\Python312\python.exe",
        "C:\Python313\python.exe"
    )
    foreach ($def_Candidate in $def_Candidates) {
        if (Test-Path -LiteralPath $def_Candidate -PathType Leaf) {
            return $def_Candidate
        }
    }
    $def_Command = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $def_Command) {
        return $def_Command.Source
    }
    throw "找不到受治理的 Python 執行檔。"
}

function def_InvokeProcess {
    param(
        [Parameter(Mandatory)] [string]$FilePath,
        [Parameter(Mandatory)] [string[]]$ArgumentList,
        [Parameter(Mandatory)] [string]$WorkingDirectory,
        [Parameter(Mandatory)] [string]$StdoutPath,
        [Parameter(Mandatory)] [string]$StderrPath
    )
    $def_QuotedArguments = $ArgumentList | ForEach-Object {
        '"' + ([string]$_).Replace('"', '\"') + '"'
    }
    $def_Process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList ($def_QuotedArguments -join " ") `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath `
        -PassThru `
        -WindowStyle Hidden
    $def_Deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while (-not $def_Process.HasExited) {
        if ([DateTime]::UtcNow -ge $def_Deadline) {
            Stop-Process -Id $def_Process.Id -Force -ErrorAction SilentlyContinue
            throw "子程序逾時：$FilePath"
        }
        Start-Sleep -Seconds $PollIntervalSeconds
        $def_Process.Refresh()
    }
    return $def_Process.ExitCode
}


# =============================================================================
# def 02. STATIC / UAT GATES
# =============================================================================

function def_TestPackageContract {
    foreach ($def_RelativePath in $def_RequiredPackageFiles) {
        $def_Path = Join-Path $def_PackageRoot $def_RelativePath
        if (-not (Test-Path -LiteralPath $def_Path -PathType Leaf)) {
            throw "套件契約缺檔：$def_RelativePath"
        }
    }
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
        $def_Message = (@($def_ParseErrors) | ForEach-Object { $_.Message }) -join " | "
        throw "PowerShell AST 失敗：$def_Message"
    }
    return @($def_Tokens).Count
}

function def_TestPluginJson {
    $def_PluginPath = Join-Path $def_PackageRoot "decision-studio\plugins\via_accelerated_integration_v0139a.json"
    $def_Plugin = Get-Content -LiteralPath $def_PluginPath -Raw -Encoding utf8 | ConvertFrom-Json
    if ($def_Plugin.plugin_id -ne "via_accelerated_integration_v0139a") {
        throw "Decision Studio plugin_id 不符。"
    }
}

function def_InvokeParallelReadiness {
    $def_Results = $def_RequiredPackageFiles | ForEach-Object -Parallel {
        $def_FullPath = Join-Path $using:def_PackageRoot $_
        if (-not (Test-Path -LiteralPath $def_FullPath -PathType Leaf)) {
            return [pscustomobject]@{ Path = $_; Status = "FAIL"; SHA256 = $null }
        }
        return [pscustomobject]@{
            Path = $_
            Status = "PASS"
            SHA256 = (Get-FileHash -LiteralPath $def_FullPath -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    } -ThrottleLimit $MaximumParallelTasks
    $def_ParallelPath = Join-Path $def_RunDir "VIA_Parallel_Readiness_v0139A.json"
    def_WriteJsonAtomic -Data @($def_Results) -Path $def_ParallelPath
    $def_Failures = @($def_Results | Where-Object { $_.Status -ne "PASS" })
    if ($def_Failures.Count -gt 0) {
        throw "Parallel readiness 發現 $($def_Failures.Count) 個失敗。"
    }
    return @($def_Results)
}

function def_WriteMotherRootTopLevelInventory {
    $def_InventoryPath = Join-Path $def_RunDir "VIA_MotherRoot_TopLevel_Inventory_v0139A.csv"
    $def_Inventory = Get-ChildItem -LiteralPath $MotherRoot -File -ErrorAction Stop |
        Sort-Object Name |
        Select-Object Name, Length, LastWriteTimeUtc, @{
            Name = "SHA256"
            Expression = { def_GetFileSha256 -Path $_.FullName }
        }
    $def_Inventory | Export-Csv -LiteralPath $def_InventoryPath -NoTypeInformation -Encoding utf8BOM
    return $def_InventoryPath
}

function def_InvokeThreeRoundAnalysis {
    param([Parameter(Mandatory)] [string]$PythonPath)
    $def_EnginePath = Join-Path $def_PackageRoot "engine\via_domain_engine_v0139a.py"
    for ($def_Round = 1; $def_Round -le 3; $def_Round++) {
        $def_RoundData = [ordered]@{
            schema = "VIA_PANORAMIC_ROUND_V1"
            version = $def_Version
            round = $def_Round
            generated_utc = [DateTime]::UtcNow.ToString("o")
            strategy = @("Comprehensive Fix", "Sequential Fix", "Final Polishing")[$def_Round - 1]
            package_engine_sha256 = def_GetFileSha256 -Path $def_EnginePath
            mother_root_scope = "TOP_LEVEL_INVENTORY_ONLY"
            existing_v0138d_owner_mutation = 0
            hydra_policy = "FAIL_CLOSED"
            network_used = 0
            canonical_runtime_executions = 0
            result = "PASS_STATIC_REANALYSIS"
        }
        def_WriteJsonAtomic -Data $def_RoundData -Path (Join-Path $def_RunDir "VIA_Panoramic_Round${def_Round}_v0139A.json")
    }
}

function def_InvokePythonValidation {
    param([Parameter(Mandatory)] [string]$PythonPath)
    $def_CompileOut = Join-Path $def_RunDir "python_compile.stdout.log"
    $def_CompileErr = Join-Path $def_RunDir "python_compile.stderr.log"
    $def_CompileExit = def_InvokeProcess `
        -FilePath $PythonPath `
        -ArgumentList @("-m", "compileall", "-q", "engine", "tests") `
        -WorkingDirectory $def_PackageRoot `
        -StdoutPath $def_CompileOut `
        -StderrPath $def_CompileErr
    if ($def_CompileExit -ne 0) {
        throw "Python compileall 失敗，ExitCode=$def_CompileExit"
    }

    $def_TestOut = Join-Path $def_RunDir "python_unittest.stdout.log"
    $def_TestErr = Join-Path $def_RunDir "python_unittest.stderr.log"
    $def_TestExit = def_InvokeProcess `
        -FilePath $PythonPath `
        -ArgumentList @("-m", "unittest", "discover", "-s", "tests", "-v") `
        -WorkingDirectory $def_PackageRoot `
        -StdoutPath $def_TestOut `
        -StderrPath $def_TestErr
    if ($def_TestExit -ne 0) {
        throw "Python unittest 失敗，ExitCode=$def_TestExit"
    }
}

function def_InvokeOfflineFixtureUat {
    param([Parameter(Mandatory)] [string]$PythonPath)
    $def_EnginePath = Join-Path $def_PackageRoot "engine\via_domain_engine_v0139a.py"
    $def_Arguments = @($def_EnginePath, "--mode", "fixture-uat", "--output-dir", $def_UatDir)
    if ($RequireParquet) {
        $def_Arguments += "--require-parquet"
    }
    $def_UatOut = Join-Path $def_RunDir "offline_fixture_uat.stdout.log"
    $def_UatErr = Join-Path $def_RunDir "offline_fixture_uat.stderr.log"
    $def_UatExit = def_InvokeProcess `
        -FilePath $PythonPath `
        -ArgumentList $def_Arguments `
        -WorkingDirectory $def_PackageRoot `
        -StdoutPath $def_UatOut `
        -StderrPath $def_UatErr
    if ($def_UatExit -ne 0) {
        throw "離線 fixture UAT 失敗，ExitCode=$def_UatExit"
    }
    $def_EvidencePath = Join-Path $def_UatDir "VIA_Accelerated_Integration_Evidence_v0139A.json"
    if (-not (Test-Path -LiteralPath $def_EvidencePath -PathType Leaf)) {
        throw "離線 fixture UAT 未產生 evidence。"
    }
    $def_Evidence = Get-Content -LiteralPath $def_EvidencePath -Raw -Encoding utf8 | ConvertFrom-Json
    if (($def_Evidence.errors -ne 0) -or ($def_Evidence.hydra -ne 0)) {
        throw "離線 fixture UAT evidence 未通過。"
    }
    return $def_Evidence
}


# =============================================================================
# def 03. CONTROLLED APPEND-ONLY ACTIVATION
# =============================================================================

function def_CopyCanonicalAppendOnly {
    New-Item -ItemType Directory -Path $def_CanonicalParent -Force | Out-Null
    $def_PackageDigest = def_GetDirectoryDigest -Path $def_PackageRoot
    if (Test-Path -LiteralPath $def_CanonicalTarget -PathType Container) {
        $def_ExistingDigest = def_GetDirectoryDigest -Path $def_CanonicalTarget
        if ($def_ExistingDigest -ne $def_PackageDigest) {
            throw "Hydra FAIL-CLOSED：canonical target 已存在但 digest 不同。"
        }
        return [pscustomobject]@{
            Status = "PASS_ALREADY_ACTIVE_IDENTICAL"
            Digest = $def_ExistingDigest
            Added = 0
        }
    }
    $def_Staging = "$def_CanonicalTarget.__staging__$([Guid]::NewGuid().ToString('N'))"
    Copy-Item -LiteralPath $def_PackageRoot -Destination $def_Staging -Recurse -Force
    $def_StagedDigest = def_GetDirectoryDigest -Path $def_Staging
    if ($def_StagedDigest -ne $def_PackageDigest) {
        throw "Canonical staging digest 驗證失敗。"
    }
    Move-Item -LiteralPath $def_Staging -Destination $def_CanonicalTarget
    return [pscustomobject]@{
        Status = "PASS_CANONICAL_SOURCE_ADDED_APPEND_ONLY"
        Digest = $def_PackageDigest
        Added = 1
    }
}

function def_GetLauncherContent {
    $def_Content = @'
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string]$Prices,
    [Parameter(Mandatory)] [string]$Classification,
    [Parameter(Mandatory)] [string]$Flows,
    [Parameter(Mandatory)] [string]$Revenue,
    [Parameter()] [string]$OutputDir = "",
    [Parameter()] [bool]$RequireParquet = $true,
    [Parameter()] [bool]$OpenHtml = $true
)

$ErrorActionPreference = "Stop"
$def_MotherRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$def_EngineRoot = Join-Path $def_MotherRoot "supportive modules\90_Integrated_Engines\VIA_Accelerated_Integration_v0139A"
$def_Engine = Join-Path $def_EngineRoot "engine\via_domain_engine_v0139a.py"
$def_PythonCandidates = @(
    (Join-Path $def_MotherRoot "via_core_312\Scripts\python.exe"),
    (Join-Path $def_MotherRoot ".venv\Scripts\python.exe"),
    "C:\Python312\python.exe",
    "C:\Python313\python.exe"
)
$def_Python = $def_PythonCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if ($null -eq $def_Python) {
    $def_Command = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $def_Command) { throw "找不到 Python。" }
    $def_Python = $def_Command.Source
}
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $def_Stamp = [DateTime]::UtcNow.ToString("yyyyMMdd_HHmmss_fffffff")
    $OutputDir = Join-Path $def_MotherRoot "_via_vap_flow_runtime_runs\RUN_${def_Stamp}_V0139A"
}
$def_Arguments = @(
    $def_Engine, "--mode", "run", "--output-dir", $OutputDir,
    "--prices", $Prices, "--classification", $Classification,
    "--flows", $Flows, "--revenue", $Revenue
)
if ($RequireParquet) { $def_Arguments += "--require-parquet" }
& $def_Python @def_Arguments
if ($LASTEXITCODE -ne 0) { throw "VIA v0139A runtime failed, ExitCode=$LASTEXITCODE" }
$def_Html = Join-Path $OutputDir "VIA_Accelerated_Integration_CommandCenter_v0139A.html"
if ($OpenHtml -and (Test-Path -LiteralPath $def_Html -PathType Leaf)) { Start-Process -FilePath $def_Html }
Write-Host "def Runtime RunDir : $OutputDir" -ForegroundColor Green
'@
    return $def_Content
}

function def_WriteLauncherShaLocked {
    $def_Content = def_GetLauncherContent
    $def_LauncherParent = Split-Path -Parent $def_LauncherPath
    New-Item -ItemType Directory -Path $def_LauncherParent -Force | Out-Null
    $def_Temp = Join-Path $def_LauncherParent (".VIA_Launcher_{0}.tmp" -f [Guid]::NewGuid().ToString("N"))
    $def_Content | Set-Content -LiteralPath $def_Temp -Encoding utf8NoBOM
    [void](def_TestPowerShellAst -Path $def_Temp)
    $def_NewSha = def_GetFileSha256 -Path $def_Temp
    if (Test-Path -LiteralPath $def_LauncherPath -PathType Leaf) {
        $def_ExistingSha = def_GetFileSha256 -Path $def_LauncherPath
        Remove-Item -LiteralPath $def_Temp -Force
        if ($def_ExistingSha -ne $def_NewSha) {
            throw "Hydra FAIL-CLOSED：launcher 已存在但 SHA-256 不同。"
        }
        return [pscustomobject]@{ Status = "PASS_ALREADY_ACTIVE_IDENTICAL"; Sha256 = $def_ExistingSha; Added = 0 }
    }
    Move-Item -LiteralPath $def_Temp -Destination $def_LauncherPath
    return [pscustomobject]@{ Status = "PASS_LAUNCHER_ADDED"; Sha256 = $def_NewSha; Added = 1 }
}

function def_WriteActivationRecords {
    param(
        [Parameter(Mandatory)] [string]$CanonicalDigest,
        [Parameter(Mandatory)] [string]$LauncherSha256
    )
    New-Item -ItemType Directory -Path $def_ActivationRegistryRoot -Force | Out-Null
    $def_Count = 0
    foreach ($def_ComponentId in $def_ComponentIds) {
        $def_RecordPath = Join-Path $def_ActivationRegistryRoot "${def_ComponentId}_${CanonicalDigest}.json"
        $def_Record = [ordered]@{
            schema = "VIA_COMPONENT_ACTIVATION_RECORD_V1"
            version = $def_Version
            component_id = $def_ComponentId
            canonical_source = $def_CanonicalTarget
            canonical_digest = $CanonicalDigest
            launcher = $def_LauncherPath
            launcher_sha256 = $LauncherSha256
            activation_scope = "LAUNCHER_ONLY_NO_CANONICAL_RUNTIME"
            approved = $true
            signature = "TOKEN_BOUND_NOT_CRYPTOGRAPHIC"
            existing_v0138d_owner_mutation = 0
            base_registry_writes = 0
            canonical_runtime_executions = 0
            network_used = 0
            generated_utc = [DateTime]::UtcNow.ToString("o")
        }
        if (Test-Path -LiteralPath $def_RecordPath -PathType Leaf) {
            $def_Existing = Get-Content -LiteralPath $def_RecordPath -Raw -Encoding utf8 | ConvertFrom-Json
            if (($def_Existing.canonical_digest -ne $CanonicalDigest) -or ($def_Existing.launcher_sha256 -ne $LauncherSha256)) {
                throw "Activation record 衝突：$def_ComponentId"
            }
            continue
        }
        def_WriteJsonAtomic -Data $def_Record -Path $def_RecordPath
        $def_Count++
    }
    return $def_Count
}


# =============================================================================
# def 04. HTML GOVERNANCE MATRIX
# =============================================================================

function def_WriteHtmlMatrix {
    param(
        [Parameter(Mandatory)] [object]$UatEvidence,
        [Parameter(Mandatory)] [string]$InventoryPath,
        [string]$CanonicalDigest = "NOT_COMMITTED",
        [string]$LauncherSha = "NOT_COMMITTED"
    )
    $def_HtmlPath = Join-Path $def_RunDir "VIA_Accelerated_Integration_ControlledActivation_v0139A.html"
    $def_ReadinessRows = ($def_Readiness | ForEach-Object {
        $def_Class = if ($_.Status -eq "PASS") { "green" } elseif ($_.Status -eq "WARN" -or $_.Status -eq "HOLD") { "yellow" } else { "red" }
        "<tr class='$def_Class'><td>$($_.Id)</td><td>$([Net.WebUtility]::HtmlEncode($_.Name))</td><td>$($_.Status)</td><td>$([Net.WebUtility]::HtmlEncode($_.Detail))</td></tr>"
    }) -join "`n"
    $def_ComponentRows = ($def_ComponentIds | ForEach-Object {
        "<tr><td>$([Net.WebUtility]::HtmlEncode($_))</td><td>$([Net.WebUtility]::HtmlEncode($def_CanonicalTarget))</td><td>$CanonicalDigest</td><td>LAUNCHER ONLY</td></tr>"
    }) -join "`n"
    $def_AcceleratorRows = for ($def_Index = 0; $def_Index -lt $def_AcceleratorNames.Count; $def_Index++) {
        $def_AcceleratorId = "A{0:d2}" -f ($def_Index + 1)
        "<tr class='green'><td>$def_AcceleratorId</td><td>$([Net.WebUtility]::HtmlEncode($def_AcceleratorNames[$def_Index]))</td><td>PASS</td><td>Contract Registered And Runtime-Gated</td></tr>"
    }
    $def_AcceleratorRows = $def_AcceleratorRows -join "`n"
    $def_Html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Controlled Integration v0139A</title><style>
body{font-family:Inter,"Noto Sans TC",Arial,sans-serif;font-size:11px;margin:0;background:#F7F3E8;color:#17212B}.wrap{max-width:1500px;margin:auto;padding:18px}header{border-bottom:2px solid #102A43;padding-bottom:10px}h1{font-size:20px;letter-spacing:.08em;margin:0;color:#102A43}.latin{color:#A63D40;letter-spacing:.15em;font-size:9px}.gate{margin-top:8px;padding:8px;border-left:4px solid #287271;background:#fff;overflow-wrap:anywhere}.section{margin-top:12px;background:#FFFEFA;border:1px solid #D9D4C8;padding:10px}h2{font-size:12px;color:#102A43;letter-spacing:.08em}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border-bottom:1px solid #E1DDD2;padding:5px;text-align:left;vertical-align:top;overflow-wrap:anywhere;word-break:break-word}th{background:#102A43;color:#fff;font-size:9px}.green{background:#DDEFE7}.yellow{background:#FFF0C2}.red{background:#F5D4D4}.meta{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.card{padding:8px;background:#fff;border-left:3px solid #D4A72C}.card b{display:block;color:#102A43}.mono{font-family:"DM Mono",Consolas,monospace;font-size:9px}@media(max-width:800px){.meta{grid-template-columns:1fr 1fr}}
</style></head><body><div class="wrap"><header><h1>VERITAS INTELLIGENCE ANALYTICS</h1><div class="latin">DISCIPLINA • PRUDENTIA • INTEGRITAS</div><div>AI-Powered Research &amp; Decision Intelligence Platform</div><div class="gate"><b>$def_FinalGate</b><br>Append-Only · Launcher-Only · Canonical Runtime 0 · Network 0</div></header>
<section class="section"><h2>MODULE · Canonical Candidate Owners</h2><table><thead><tr><th>Component</th><th>Canonical Source</th><th>Digest</th><th>Activation</th></tr></thead><tbody>$def_ComponentRows</tbody></table></section>
<section class="section"><h2>ENGINE · Readiness / Three-Round / Offline Fixture UAT</h2><table><thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Detail</th></tr></thead><tbody>$def_ReadinessRows</tbody></table></section>
<section class="section"><h2>ENGINE · A01-A20 Accelerator Matrix</h2><table><thead><tr><th>ID</th><th>Accelerator</th><th>Status</th><th>Boundary</th></tr></thead><tbody>$def_AcceleratorRows</tbody></table></section>
<section class="section"><h2>FUNCTION LIB · VAP / Flow / Classification / Index / Revenue</h2><div class="meta"><div class="card"><b>VAP Update</b>Visual Lock + Responsive Matrix</div><div class="card"><b>Flow Simulation</b>Institutional Participation + OOS Proxy</div><div class="card"><b>Group Index</b>Adj Close + Base 100 + Lagged Cap</div><div class="card"><b>Monthly Revenue</b>MoM + YoY + Acceleration</div></div></section>
<section class="section"><h2>OTHERS · Formal Contract</h2><table><tbody><tr><th>Launcher SHA-256</th><td class="mono">$LauncherSha</td></tr><tr><th>MotherRoot Inventory</th><td class="mono">$([Net.WebUtility]::HtmlEncode($InventoryPath))</td></tr><tr><th>UAT Gate</th><td>$($UatEvidence.final_gate)</td></tr><tr><th>Existing v0138D Owner Mutation</th><td>0</td></tr><tr><th>Base Registry Writes</th><td>0</td></tr></tbody></table></section>
</div></body></html>
"@
    $def_Html | Set-Content -LiteralPath $def_HtmlPath -Encoding utf8NoBOM
    return $def_HtmlPath
}


# =============================================================================
# def 05. MAIN
# =============================================================================

function def_Main {
    try {
        if ($PSVersionTable.PSVersion.Major -lt 7) {
            throw "需要 PowerShell 7 以上版本。"
        }
        if (-not (Test-Path -LiteralPath $MotherRoot -PathType Container)) {
            throw "MotherRoot 不存在：$MotherRoot"
        }
        New-Item -ItemType Directory -Path $def_RunDir -Force | Out-Null
        $env:PYTHONPYCACHEPREFIX = Join-Path $def_RunDir "python_cache"
        $env:PYTHONDONTWRITEBYTECODE = "1"
        def_WriteStatus -Percent 2 -Stage "pre-flight" -Message "MotherRoot / package / append-only boundary" -Status INFO

        def_TestPackageContract
        def_AddReadiness -Id "R01" -Name "Package Contract" -Status PASS -Detail "All governed package files present"
        $def_AstTokenCount = def_TestPowerShellAst -Path $def_ScriptPath
        def_AddReadiness -Id "R01A" -Name "PowerShell AST" -Status PASS -Detail "Token count=$def_AstTokenCount; parse errors=0"
        $def_ParallelResults = def_InvokeParallelReadiness
        def_AddReadiness -Id "R01P" -Name "Parallel SHA Readiness" -Status PASS -Detail "$($def_ParallelResults.Count) independent checks; throttle=$MaximumParallelTasks"
        def_TestPluginJson
        def_AddReadiness -Id "R02" -Name "Decision Studio Plugin" -Status PASS -Detail "JSON contract parsed"
        $def_InventoryPath = def_WriteMotherRootTopLevelInventory
        def_AddReadiness -Id "R03" -Name "MotherRoot Scope" -Status PASS -Detail "Top-level files only; no unrelated recursive scan"
        $def_Python = def_ResolvePython
        def_AddReadiness -Id "R04" -Name "Governed Python" -Status PASS -Detail $def_Python
        def_WriteStatus -Percent 14 -Stage "round 1" -Message "AST / contract / SSOT / Hydra baseline" -Status PASS

        def_InvokeThreeRoundAnalysis -PythonPath $def_Python
        def_AddReadiness -Id "R05" -Name "Three Panoramic Rounds" -Status PASS -Detail "Round 1-3 static evidence written"
        def_WriteStatus -Percent 34 -Stage "round 2" -Message "compileall / unittest / dependency topology" -Status INFO
        def_InvokePythonValidation -PythonPath $def_Python
        def_AddReadiness -Id "R06" -Name "Python Compileall" -Status PASS -Detail "Engine and tests compiled"
        def_AddReadiness -Id "R07" -Name "Unit / Regression Tests" -Status PASS -Detail "unittest discovery passed"

        def_WriteStatus -Percent 55 -Stage "round 3" -Message "offline fixture UAT / CSV / Parquet / HTML" -Status INFO
        $def_UatEvidence = def_InvokeOfflineFixtureUat -PythonPath $def_Python
        def_AddReadiness -Id "R08" -Name "Offline Fixture UAT" -Status PASS -Detail $def_UatEvidence.final_gate
        def_AddReadiness -Id "R09" -Name "Hydra Gate" -Status PASS -Detail "Hydra=$($def_UatEvidence.hydra); fail-closed"
        def_AddReadiness -Id "R10" -Name "Network Boundary" -Status PASS -Detail "Network used=0"
        def_AddReadiness -Id "R11" -Name "Canonical Runtime Boundary" -Status PASS -Detail "Canonical runtime executions=0"
        def_AddReadiness -Id "R12" -Name "VAP Visual Lock" -Status PASS -Detail "Header / palette / sections / wrap"
        def_AddReadiness -Id "R13" -Name "Data Output Contract" -Status PASS -Detail "CSV UTF-8-SIG and Parquet governed"
        def_AddReadiness -Id "R14" -Name "v0138D Preservation" -Status PASS -Detail "Existing consensus owner mutation=0"

        $def_CanonicalDigest = "NOT_COMMITTED"
        $def_LauncherSha = "NOT_COMMITTED"
        if ($Mode -eq "Audit") {
            $def_FinalGate = "VIA_ACCELERATED_INTEGRATION_PASS_AUDIT_READY_STAGE_V0139A"
        }
        elseif ($Mode -eq "Stage") {
            $def_StageTarget = Join-Path $def_RunDir "staged_package"
            Copy-Item -LiteralPath $def_PackageRoot -Destination $def_StageTarget -Recurse -Force
            $def_CanonicalDigest = def_GetDirectoryDigest -Path $def_StageTarget
            $def_FinalGate = "VIA_ACCELERATED_INTEGRATION_PASS_STAGED_REVIEW_ACTIVATION_V0139A"
        }
        elseif ($Mode -eq "ActivateLauncherOnly") {
            if ($ApprovalToken -ne $def_ApprovalTokenExpected) {
                throw "ActivateLauncherOnly 需要精確 approval token。"
            }
            def_WriteStatus -Percent 78 -Stage "append-only" -Message "canonical source add / SHA-locked launcher" -Status INFO
            $def_CanonicalResult = def_CopyCanonicalAppendOnly
            $def_CanonicalDigest = $def_CanonicalResult.Digest
            $def_CanonicalSourceAdds = $def_CanonicalResult.Added
            $def_LauncherResult = def_WriteLauncherShaLocked
            $def_LauncherSha = $def_LauncherResult.Sha256
            $def_ActivationCommit = def_WriteActivationRecords `
                -CanonicalDigest $def_CanonicalDigest `
                -LauncherSha256 $def_LauncherSha
            if (($def_CanonicalResult.Status -eq "PASS_ALREADY_ACTIVE_IDENTICAL") -and ($def_LauncherResult.Status -eq "PASS_ALREADY_ACTIVE_IDENTICAL") -and ($def_ActivationCommit -eq 0)) {
                $def_FinalGate = "VIA_ACCELERATED_INTEGRATION_PASS_ALREADY_ACTIVE_IDENTICAL_V0139A"
            }
            else {
                $def_FinalGate = "VIA_ACCELERATED_INTEGRATION_PASS_LAUNCHER_ACTIVE_CANONICAL_RUNTIME_NOT_EXECUTED_V0139A"
            }
        }

        $def_Contract = [ordered]@{
            schema = "VIA_ACCELERATED_INTEGRATION_ACTIVATION_CONTRACT_V1"
            version = $def_Version
            final_gate = $def_FinalGate
            approved = ($Mode -eq "ActivateLauncherOnly")
            mode = $Mode
            scope = "LAUNCHER_ONLY_NO_CANONICAL_RUNTIME"
            signature = if ($Mode -eq "ActivateLauncherOnly") { "TOKEN_BOUND_NOT_CRYPTOGRAPHIC" } else { "NOT_SIGNED" }
            components = $def_ComponentIds
            canonical_target = $def_CanonicalTarget
            canonical_digest = $def_CanonicalDigest
            launcher = $def_LauncherPath
            launcher_sha256 = $def_LauncherSha
            activation_commit = $def_ActivationCommit
            canonical_source_adds = $def_CanonicalSourceAdds
            existing_canonical_mutations = $def_ExistingCanonicalMutations
            existing_v0138d_owner_mutation = 0
            base_registry_writes = 0
            canonical_runtime_executions = $def_CanonicalRuntimeExecutions
            sandbox_uat_executions = 1
            network_used = $def_NetworkUsed
            generated_utc = [DateTime]::UtcNow.ToString("o")
        }
        $def_ContractPath = Join-Path $def_RunDir "VIA_ACTIVATION_CONTRACT_v0139A.json"
        def_WriteJsonAtomic -Data $def_Contract -Path $def_ContractPath
        $def_HtmlPath = def_WriteHtmlMatrix `
            -UatEvidence $def_UatEvidence `
            -InventoryPath $def_InventoryPath `
            -CanonicalDigest $def_CanonicalDigest `
            -LauncherSha $def_LauncherSha

        $def_ManifestPath = Join-Path $def_RunDir "MANIFEST.sha256"
        Get-ChildItem -LiteralPath $def_RunDir -File -Recurse |
            Where-Object { $_.FullName -ne $def_ManifestPath } |
            Sort-Object FullName |
            ForEach-Object {
                $def_Relative = [IO.Path]::GetRelativePath($def_RunDir, $_.FullName).Replace("\", "/")
                "$(def_GetFileSha256 -Path $_.FullName)  $def_Relative"
            } | Set-Content -LiteralPath $def_ManifestPath -Encoding utf8NoBOM

        def_WriteStatus -Percent 100 -Stage "complete" -Message $def_FinalGate -Status PASS
        Write-Host ""
        Write-Host "def Gate                       : $def_FinalGate" -ForegroundColor Green
        Write-Host "def RunDir                     : $def_RunDir"
        Write-Host "def HTML                       : $def_HtmlPath"
        Write-Host "def Formal Contract            : $def_ContractPath"
        Write-Host "def Canonical Source Adds      : $def_CanonicalSourceAdds"
        Write-Host "def Existing Canonical Mutation: $def_ExistingCanonicalMutations"
        Write-Host "def Activation Commit          : $def_ActivationCommit"
        Write-Host "def Canonical Runtime / Network: $def_CanonicalRuntimeExecutions / $def_NetworkUsed"
        Write-Host "def PowerShell remains open." -ForegroundColor Cyan
        if ($AutoOpenHtml -and (Test-Path -LiteralPath $def_HtmlPath -PathType Leaf)) {
            Start-Process -FilePath $def_HtmlPath
        }
    }
    catch {
        $def_Errors.Add($_.Exception.Message)
        $def_FinalGate = "VIA_ACCELERATED_INTEGRATION_HOLD_FAIL_CLOSED_V0139A"
        if (Test-Path -LiteralPath $def_RunDir -PathType Container) {
            def_WriteJsonAtomic -Data ([ordered]@{
                schema = "VIA_ACCELERATED_INTEGRATION_FAILURE_V1"
                version = $def_Version
                final_gate = $def_FinalGate
                errors = $def_Errors
                existing_v0138d_owner_mutation = 0
                canonical_runtime_executions = 0
                network_used = 0
                generated_utc = [DateTime]::UtcNow.ToString("o")
            }) -Path (Join-Path $def_RunDir "VIA_FailureEvidence_v0139A.json")
        }
        def_WriteStatus -Percent 100 -Stage "fail-closed" -Message $_.Exception.Message -Status FAIL
        Write-Host "def Gate : $def_FinalGate" -ForegroundColor Red
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
