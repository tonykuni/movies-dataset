param(
    [string]$Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$Downloads = "C:\Users\tonyk\Downloads",
    [string]$SupportiveDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",
    [string]$FunctionalRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules",
    [string]$ToolRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_UltimateEngineForge",
    [string[]]$ProjectNames = @("VRN","VPNS","VAP","VDF"),
    [string[]]$ExtraProjectPaths = @(),
    [string[]]$ConversationLensPaths = @(),
    [bool]$CreateSandbox = $true,
    [bool]$RunCandidateDryProbe = $true,
    [bool]$RunUserSmokeTest = $false,
    [bool]$EnableExternalAiHook = $false,
    [string]$AiHookCommand = "",
    [string]$ApprovalToken = "",
    [bool]$OpenReport = $true,
    [int]$TimeoutSec = 180,
    [int]$MaxRounds = 3,
    [int]$MaxFilesPerProjectCopy = 2500,
    [int]$MaxFilesPerScanRoot = 6000,
    [string]$ConfigJson = "",
    [ValidateSet("InspectOnly","SandboxDryRun","SandboxBuild")]
    [string]$Mode = "SandboxDryRun",
    [bool]$FreezeAfterExpanded = $true,
    [bool]$BuildEngineStubs = $true,
    [bool]$KeepPowerShellOpen = $true
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
# def VIA ULTIMATE ENGINE FORGE · JSON CONTRACT · FREEZE GATE AIO v0.6.0
# =============================================================================
# Purpose:
# - Consolidate the best patterns from VIA v040-v044, FirstStep, RedFinding,
#   NexusBridge, Polyglot Stabilizer, VDF Gate, OnePowerShell AutoPilot, NetGuard,
#   and UltimateFirstModule v050.
# - Convert discovered capabilities into isolated multi-language Function Engines.
# - Enforce JSON-only parameters, sandbox-first smoke tests, engine registry, and
#   freeze manifests after each engine is expanded to its safe boundary.
# - Avoid Hydra risk: syntax blockers first, contract blockers second, optimization last.
#
# Policy:
# - no DB write
# - no canonical merge
# - no destructive delete
# - no stop-process
# - append-only
# - sandbox-first
# - max 3 rounds
# - no original repair unless future explicitly reviewed and approved
# =============================================================================


# =============================================================================
# def JSON CONFIG PRELOAD / PARAMETER CONTRACT
# =============================================================================
# If -ConfigJson is provided, it becomes the external parameter contract.
# CLI parameters remain the emergency fallback. Unknown fields are ignored.
$script:def_ConfigLoaded = $false
if (-not [string]::IsNullOrWhiteSpace($ConfigJson) -and (Test-Path -LiteralPath $ConfigJson)) {
    try {
        $script:def_ExternalConfig = Get-Content -LiteralPath $ConfigJson -Raw | ConvertFrom-Json
        $props = @($script:def_ExternalConfig.PSObject.Properties.Name)
        if ($props -contains "root") { $Root = [string]$script:def_ExternalConfig.root }
        if ($props -contains "downloads") { $Downloads = [string]$script:def_ExternalConfig.downloads }
        if ($props -contains "supportive_dir") { $SupportiveDir = [string]$script:def_ExternalConfig.supportive_dir }
        if ($props -contains "functional_root") { $FunctionalRoot = [string]$script:def_ExternalConfig.functional_root }
        if ($props -contains "tool_root") { $ToolRoot = [string]$script:def_ExternalConfig.tool_root }
        if ($props -contains "mode") { $Mode = [string]$script:def_ExternalConfig.mode }
        if ($props -contains "freeze_after_expanded") { $FreezeAfterExpanded = [bool]$script:def_ExternalConfig.freeze_after_expanded }
        if ($props -contains "build_engine_stubs") { $BuildEngineStubs = [bool]$script:def_ExternalConfig.build_engine_stubs }
        if ($props -contains "project_names") { $ProjectNames = @($script:def_ExternalConfig.project_names | ForEach-Object { [string]$_ }) }
        if ($props -contains "extra_project_paths") { $ExtraProjectPaths = @($script:def_ExternalConfig.extra_project_paths | ForEach-Object { [string]$_ }) }
        if ($props -contains "conversation_lens_paths") { $ConversationLensPaths = @($script:def_ExternalConfig.conversation_lens_paths | ForEach-Object { [string]$_ }) }
        $script:def_ConfigLoaded = $true
    } catch {
        Write-Host ("[WARN] ConfigJson read failed: " + $_.Exception.Message) -ForegroundColor Yellow
    }
}

$def_PARAM_VERSION = "v0.6.0"
$def_PARAM_RUN_ID = "RUN_{0}_VIA_ULTIMATE_ENGINE_FORGE" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_PARAM_POLICY = [ordered]@{
    db_write           = $false
    canonical_merge    = $false
    destructive_delete = $false
    stop_process       = $false
    append_only        = $true
    sandbox_first      = $true
    max_rounds         = $MaxRounds
    user_smoke_test    = $RunUserSmokeTest
    external_ai_hook   = $EnableExternalAiHook
    mode               = $Mode
    freeze_after_expanded = $FreezeAfterExpanded
    build_engine_stubs = $BuildEngineStubs
}

$def_PARAM_SUPPORTIVE_FILES = @(
    (Join-Path $SupportiveDir "Read_Me_VeritasNexusCore.md"),
    (Join-Path $SupportiveDir "Invoke-VeritasNexusCore.ps1"),
    (Join-Path $SupportiveDir "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1")
)

$def_PARAM_CANONICAL_COMMANDS = @(
    (Join-Path $Downloads "Invoke-VIA-MultiProject-PanoramaSync-AIO-v044-RiskTriageTrueProgress.ps1"),
    (Join-Path $Downloads "Invoke-VIA-MultiProject-PanoramaSync-AIO-v043-CompletionAnchorEngine.ps1"),
    (Join-Path $Downloads "Invoke-VIA-MultiProject-PanoramaSync-AIO-v042-SafeHtmlRendererHotfix.ps1"),
    (Join-Path $Downloads "Invoke-VIA-MultiProject-PanoramaSync-AIO-v041-HistoryLensHotfix.ps1"),
    (Join-Path $Downloads "Invoke-VIA-MultiProject-PanoramaSync-AIO-v040.ps1"),
    (Join-Path $Downloads "Invoke-VIA-FirstStep-PanoramaSandbox-AIO-v032-PlainArrayHotfix.ps1"),
    (Join-Path $Downloads "Invoke-VIA-FirstStep-PanoramaSandbox-AIO-v031-Hotfix.ps1"),
    (Join-Path $Downloads "Invoke-VIA-FirstStep-PanoramaSandbox-AIO-v030.ps1"),
    (Join-Path $Downloads "Invoke-VIA-RedFinding-Triage-v01.ps1"),
    (Join-Path $Downloads "Invoke-VIA-RedFinding-Triage-v01 (1).ps1"),
    (Join-Path $Downloads "Invoke-VIA-NexusToolBridge-Unified-v02.ps1"),
    (Join-Path $Downloads "Invoke-VIA-NexusToolBridge-AIO-v010.ps1"),
    (Join-Path $Downloads "Invoke-VIA-Polyglot-RedFindingStabilizer-v0122-AstParserHotfix.ps1"),
    (Join-Path $Downloads "Invoke-VIA-Polyglot-RedFindingStabilizer-v0121-Hotfix.ps1"),
    (Join-Path $Downloads "Invoke-VIA-Polyglot-RedFindingStabilizer-v012.ps1"),
    (Join-Path $Downloads "Invoke-VDF-Nexus-Panorama3RoundGate.ps1"),
    (Join-Path $Downloads "Invoke-VIA-OnePowerShell-AutoPilot3Round-v020.ps1"),
    (Join-Path $Downloads "VIA_NetGuardTuner_v2.ps1"),
    (Join-Path $Downloads "VIA_NetGuardTuner_v1.ps1")
)

$def_PARAM_ADVANTAGE_RULES = @(
    [pscustomobject]@{ID="F01"; Feature="MultiProject Panorama"; Pattern="MultiProject|ProjectNames|functional modules|PanoramaSync"; Weight=12; Source="v040-v044"; Benefit="多專案同步盤點與整合入口"},
    [pscustomobject]@{ID="F02"; Feature="History Lens"; Pattern="HistoryLens|PastRun|RUN_|history"; Weight=8; Source="v041"; Benefit="讀取歷史 RUN 與報告，不重犯舊錯"},
    [pscustomobject]@{ID="F03"; Feature="Safe HTML Renderer"; Pattern="HtmlEncode|SafeHtml|HTML Matrix|WriteHtml"; Weight=8; Source="v042"; Benefit="HTML 報告穩定輸出，不因特殊字元爆掉"},
    [pscustomobject]@{ID="F04"; Feature="Completion Anchor Engine"; Pattern="CompletionAnchor|AnchorMap|CompletionScore|Anchor"; Weight=10; Source="v043"; Benefit="用完成度與錨點判斷專案真實狀態"},
    [pscustomobject]@{ID="F05"; Feature="Risk Triage True Progress"; Pattern="RiskTriage|TrueProgress|Remaining|CompletedTasks"; Weight=12; Source="v044"; Benefit="真進度、風險分層、下一步行動收斂"},
    [pscustomobject]@{ID="F06"; Feature="FirstStep Methodology"; Pattern="FirstStep|Methodology|Top10|PM4Py|ProcessMining|EnterpriseForms"; Weight=8; Source="FirstStep v030-v032"; Benefit="方法論、工具矩陣、企業表單到流程探勘路徑"},
    [pscustomobject]@{ID="F07"; Feature="Red Finding Triage"; Pattern="RedFinding|red finding|Triage|P0|P1"; Weight=10; Source="RedFinding"; Benefit="紅燈分類，避免把所有錯誤同時修壞"},
    [pscustomobject]@{ID="F08"; Feature="Nexus Tool Bridge"; Pattern="NexusToolBridge|VeritasNexusCore|ToolBridge|Bridge"; Weight=8; Source="NexusBridge"; Benefit="支援性模組與功能性模組橋接"},
    [pscustomobject]@{ID="F09"; Feature="Polyglot AST Stabilizer"; Pattern="Polyglot|AST|ParseFile|ChildParser|PowerShell AST"; Weight=10; Source="Polyglot v0122"; Benefit="先清語法紅燈，再允許其他修復"},
    [pscustomobject]@{ID="F10"; Feature="VDF Domain Gate"; Pattern="VDF|Manifest|yfinance|FRED|parquet|DuckDB"; Weight=7; Source="VDF Gate"; Benefit="資料擷取/manifest/金融資料管線專項檢查"},
    [pscustomobject]@{ID="F11"; Feature="OnePowerShell Sandbox Repair"; Pattern="SandboxRepair|ApplyPlan|ApplyToOriginal|AutoPilot|sandbox repair"; Weight=10; Source="OnePowerShell"; Benefit="沙盒修復、審核計畫、禁止直接改原始碼"},
    [pscustomobject]@{ID="F12"; Feature="NetGuard / Network Safety"; Pattern="NetGuard|network|retry|offline|online"; Weight=6; Source="NetGuard"; Benefit="網路/安裝/連線風險分離"}
)

$def_PARAM_ACCELERATORS = @(
    [pscustomobject]@{ID="A01"; Name="Run Isolation"; Function="Append-only run folders; no overwrite of canonical source."},
    [pscustomobject]@{ID="A02"; Name="Conversation Lens"; Function="Scan pasted text, logs, and history reports as context artifacts."},
    [pscustomobject]@{ID="A03"; Name="Command Advantage Extraction"; Function="Score every known command by inherited strengths."},
    [pscustomobject]@{ID="A04"; Name="Three-Round Panorama"; Function="Round1 inspect, Round2 sandbox test, Round3 converge."},
    [pscustomobject]@{ID="A05"; Name="AST Before Invoke"; Function="Parse-check PowerShell scripts before dry probe."},
    [pscustomobject]@{ID="A06"; Name="Sandbox Copy"; Function="Copy scripts/docs/configs into isolated test area."},
    [pscustomobject]@{ID="A07"; Name="Hydra Gate"; Function="Split sequential blockers from parallel-safe improvements."},
    [pscustomobject]@{ID="A08"; Name="Timeout Guard"; Function="Child probes are bounded; parent does not hang."},
    [pscustomobject]@{ID="A09"; Name="AI Sandbox Prompt Pack"; Function="Generate structured AI review prompts; optional hook disabled by default."},
    [pscustomobject]@{ID="A10"; Name="HTML/CSV/JSON Matrix"; Function="Every result is auditable and exportable."},
    [pscustomobject]@{ID="A11"; Name="JSON Contract Gate"; Function="All engine runtime parameters are expressed as JSON contracts."},
    [pscustomobject]@{ID="A12"; Name="Freeze Manifest"; Function="Expanded engines are hash-tracked and frozen behind adapter policy."}
)

$def_PARAM_SCAN_EXTENSIONS = @(".ps1",".psm1",".psd1",".py",".json",".md",".html",".htm",".csv",".yaml",".yml",".toml",".txt",".log")
$def_PARAM_EXCLUDE_DIR_NAMES = @(".git",".svn",".hg","__pycache__",".pytest_cache",".ruff_cache","node_modules",".next","dist","build",".venv","venv","env","site-packages",".mypy_cache")
$def_PARAM_PHASES = @(
    "Round1.Initialize",
    "Round1.CommandAdvantageLens",
    "Round1.FolderPanoramaLens",
    "Round1.ConversationHistoryLens",
    "Round1.PolicyAndSupportiveCheck",
    "Round1.EngineExpansionLens",
    "Round2.JsonContractAndEngineForge",
    "Round2.EngineSmokeTest",
    "Round2.SandboxCopy",
    "Round2.PowerShellAstSandbox",
    "Round2.PythonCompileSandbox",
    "Round2.CandidateDryProbe",
    "Round2.HydraRiskGate",
    "Round3.MultiProjectConvergence",
    "Round3.AISandboxPromptPack",
    "Round3.BridgeAndFirstCommand",
    "Round3.EngineFreezeGate",
    "Round3.ReportSeal"
)

$def_RUN_ROOT = Join-Path $ToolRoot ("runs\" + $def_PARAM_RUN_ID)
$def_SANDBOX_ROOT = Join-Path $def_RUN_ROOT "sandbox"
$def_RUNTIME_DIR = Join-Path $def_RUN_ROOT "runtime"
$def_REGISTRY_DIR = Join-Path $def_RUN_ROOT "registry"
$def_REPORT_DIR = Join-Path $def_RUN_ROOT "report"
$def_LOG_DIR = Join-Path $def_RUN_ROOT "logs"
$def_PLAN_DIR = Join-Path $def_RUN_ROOT "plans"
$def_PROMPT_DIR = Join-Path $def_RUN_ROOT "ai_prompt_pack"
$def_BRIDGE_DIR = Join-Path $ToolRoot "bridge"

$def_ENGINE_FORGE_DIR = Join-Path $def_RUN_ROOT "engine_forge"
$def_ENGINE_DIR = Join-Path $def_ENGINE_FORGE_DIR "engines"
$def_ENGINE_CONFIG_DIR = Join-Path $def_ENGINE_FORGE_DIR "config"
$def_ENGINE_REGISTRY_DIR = Join-Path $def_ENGINE_FORGE_DIR "registry"
$def_ENGINE_FREEZE_DIR = Join-Path $def_ENGINE_FORGE_DIR "freeze"
$def_ENGINE_REGISTRY_JSON = Join-Path $def_ENGINE_REGISTRY_DIR "VIA_EngineRegistry.json"
$def_ENGINE_REGISTRY_CSV = Join-Path $def_ENGINE_REGISTRY_DIR "VIA_EngineRegistry.csv"
$def_ENGINE_CAPABILITY_CSV = Join-Path $def_ENGINE_REGISTRY_DIR "VIA_EngineCapabilityMatrix.csv"
$def_ENGINE_DEPENDENCY_CSV = Join-Path $def_ENGINE_REGISTRY_DIR "VIA_EngineDependencyMatrix.csv"
$def_ENGINE_FREEZE_JSON = Join-Path $def_ENGINE_FREEZE_DIR "VIA_EngineFreezeRegistry.json"
$def_ENGINE_FREEZE_CSV = Join-Path $def_ENGINE_FREEZE_DIR "VIA_EngineFreezeMatrix.csv"
$def_ENGINE_CONFIG_JSON = Join-Path $def_ENGINE_CONFIG_DIR "VIA_EngineForge_Config.json"


$def_MATRIX_CSV = Join-Path $def_REGISTRY_DIR "VIA_UltimateFirstModule_Matrix.csv"
$def_MATRIX_JSON = Join-Path $def_REGISTRY_DIR "VIA_UltimateFirstModule_Matrix.json"
$def_COMMAND_CSV = Join-Path $def_REGISTRY_DIR "VIA_Command_AdvantageLens.csv"
$def_PROJECT_CSV = Join-Path $def_REGISTRY_DIR "VIA_Project_FolderLens.csv"
$def_CONVO_CSV = Join-Path $def_REGISTRY_DIR "VIA_Conversation_HistoryLens.csv"
$def_RISK_CSV = Join-Path $def_REGISTRY_DIR "VIA_HydraRisk_Triage.csv"
$def_SEQ_PLAN_CSV = Join-Path $def_PLAN_DIR "VIA_Sequential_RepairPlan.csv"
$def_PAR_PLAN_CSV = Join-Path $def_PLAN_DIR "VIA_ParallelSafe_OptimizationPlan.csv"
$def_NEXT_ACTION_CSV = Join-Path $def_PLAN_DIR "VIA_NextAction_ConvergencePlan.csv"
$def_FIRST_COMMAND_PS1 = Join-Path $def_PLAN_DIR "VIA_Best_Generic_FirstCommand.ps1"
$def_AI_PROMPT_MD = Join-Path $def_PROMPT_DIR "VIA_AI_Sandbox_ReviewPrompt.md"
$def_BRIDGE_PSM1 = Join-Path $def_BRIDGE_DIR "VIA_UltimateEngineForgeBridge.psm1"
$def_REPORT_HTML = Join-Path $def_REPORT_DIR "VIA_UltimateFirstModule_AISandboxSync_Report.html"
$def_LOG_FILE = Join-Path $def_LOG_DIR "run.log"
$def_PARSER_PS1 = Join-Path $def_RUNTIME_DIR "VIA_PS_AstParser_Child.ps1"

$script:def_Rows = @()
$script:def_CommandRows = @()
$script:def_ProjectRows = @()
$script:def_ConversationRows = @()
$script:def_RiskRows = @()
$script:def_SequentialPlanRows = @()
$script:def_ParallelPlanRows = @()
$script:def_NextActionRows = @()
$script:def_EngineRows = @()
$script:def_EngineCapabilityRows = @()
$script:def_EngineDependencyRows = @()
$script:def_FreezeRows = @()
$script:def_TotalTasks = 1
$script:def_CompletedTasks = 0
$script:def_LastProgressTick = [DateTime]::MinValue
$script:def_PwshPath = $null
$script:def_PythonPath = $null

function def_EnsureDirectory {
    param([string]$Path)
    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function def_AsPlainArray {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return @() }
    if ($InputObject -is [string]) { return @($InputObject) }
    if ($InputObject -is [System.Collections.IDictionary]) { return @($InputObject) }
    try {
        if ($InputObject.PSObject.Methods.Name -contains "ToArray") {
            $arr = $InputObject.ToArray()
            $out = @()
            foreach ($item in $arr) { $out += $item }
            return @($out)
        }
    } catch {}
    try {
        $out = @()
        foreach ($item in $InputObject) { $out += $item }
        return @($out)
    } catch {
        return @($InputObject)
    }
}

function def_CountSafe {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return 0 }
    if ($InputObject -is [string]) { return 1 }
    if ($InputObject -is [array]) { return $InputObject.Count }
    if ($InputObject -is [System.Collections.ICollection]) { return $InputObject.Count }
    try {
        $c = 0
        foreach ($item in $InputObject) { $c++ }
        return $c
    } catch {
        return 1
    }
}

function def_HtmlEncode {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_WriteLog {
    param([string]$Level,[string]$Message)
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[{0}] [{1}] {2}" -f $ts,$Level,$Message
    $color = "Gray"
    if ($Level -eq "OK") { $color = "Green" }
    elseif ($Level -eq "WARN") { $color = "Yellow" }
    elseif ($Level -eq "FAIL" -or $Level -eq "FATAL") { $color = "Red" }
    elseif ($Level -eq "RUN") { $color = "Cyan" }
    Write-Host $line -ForegroundColor $color
    try { Add-Content -LiteralPath $def_LOG_FILE -Value $line -Encoding UTF8 } catch {}
}

function def_GetPercent {
    param([int]$Done,[int]$Total)
    if ($Total -le 0) { return 0 }
    $pct = [math]::Round(($Done / [double]$Total) * 100, 1)
    if ($pct -gt 100) { return 100 }
    if ($pct -lt 0) { return 0 }
    return $pct
}

function def_UpdateProgress {
    param([string]$Activity,[string]$Status)
    $now = Get-Date
    if (($now - $script:def_LastProgressTick).TotalMilliseconds -lt 250) { return }
    $script:def_LastProgressTick = $now
    $pct = def_GetPercent -Done $script:def_CompletedTasks -Total $script:def_TotalTasks
    $remaining = [math]::Max(0, $script:def_TotalTasks - $script:def_CompletedTasks)
    Write-Progress -Id 1 -Activity $Activity -Status ("{0} · completed {1}/{2} · remaining {3}" -f $Status,$script:def_CompletedTasks,$script:def_TotalTasks,$remaining) -PercentComplete $pct
}

function def_TaskDone {
    param([string]$Activity,[string]$Status)
    $script:def_CompletedTasks++
    def_UpdateProgress -Activity $Activity -Status $Status
}

function def_AddRow {
    param(
        [string]$Round,
        [string]$Scope,
        [string]$Layer,
        [string]$Name,
        [string]$Status,
        [string]$Risk,
        [string]$Class,
        [string]$Priority,
        [string]$Metric,
        [object]$Value,
        [string]$Message,
        [string]$Path
    )
    $script:def_Rows += [pscustomobject]@{
        Time     = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        Round    = $Round
        Scope    = $Scope
        Layer    = $Layer
        Name     = $Name
        Status   = $Status
        Risk     = $Risk
        Class    = $Class
        Priority = $Priority
        Metric   = $Metric
        Value    = [string]$Value
        Message  = $Message
        Path     = $Path
    }
}

function def_GetSha256Safe {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        }
    } catch {}
    return ""
}

function def_ReadTextSafe {
    param([string]$Path,[int]$MaxChars = 1500000)
    try {
        if (-not (Test-Path -LiteralPath $Path)) { return "" }
        $text = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
        if ($text.Length -gt $MaxChars) { return $text.Substring(0,$MaxChars) }
        return $text
    } catch {
        return ""
    }
}

function def_SaveCsv {
    param([object[]]$Rows,[string]$Path)
    try { @($Rows) | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8BOM } catch { def_WriteLog "WARN" ("CSV export failed: {0}" -f $Path) }
}

function def_SaveJson {
    param([object]$Object,[string]$Path,[int]$Depth = 8)
    try { $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8 } catch { def_WriteLog "WARN" ("JSON export failed: {0}" -f $Path) }
}

function def_IsExcludedPath {
    param([string]$Path)
    foreach ($name in $def_PARAM_EXCLUDE_DIR_NAMES) {
        if ($Path -match ("\\" + [regex]::Escape($name) + "(\\|$)")) { return $true }
    }
    return $false
}

function def_GetFilesLight {
    param([string]$Path,[int]$MaxFiles = 6000)
    $out = @()
    if (-not (Test-Path -LiteralPath $Path)) { return @() }
    try {
        $items = Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue
        foreach ($f in $items) {
            if ((def_CountSafe $out) -ge $MaxFiles) { break }
            if (def_IsExcludedPath $f.FullName) { continue }
            if ($def_PARAM_SCAN_EXTENSIONS -contains $f.Extension.ToLowerInvariant()) { $out += $f }
        }
    } catch {}
    return @($out)
}

function def_ResolvePwsh {
    if (-not [string]::IsNullOrWhiteSpace($script:def_PwshPath)) { return $script:def_PwshPath }
    $candidates = @()
    try { $cmd = Get-Command pwsh -ErrorAction SilentlyContinue; if ($cmd) { $candidates += $cmd.Source } } catch {}
    $candidates += "C:\Program Files\PowerShell\7\pwsh.exe"
    foreach ($c in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($c) -and (Test-Path -LiteralPath $c)) {
            $script:def_PwshPath = $c
            return $c
        }
    }
    return ""
}

function def_ResolvePython {
    if (-not [string]::IsNullOrWhiteSpace($script:def_PythonPath)) { return $script:def_PythonPath }
    $candidates = @()
    try { $cmd = Get-Command python -ErrorAction SilentlyContinue; if ($cmd) { $candidates += $cmd.Source } } catch {}
    try { $cmd = Get-Command py -ErrorAction SilentlyContinue; if ($cmd) { $candidates += $cmd.Source } } catch {}
    $candidates += (Join-Path $Root "_envs\via_operation_optimizer_2026\Scripts\python.exe")
    $candidates += "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\_envs\via_operation_optimizer_2026\Scripts\python.exe"
    foreach ($c in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($c) -and (Test-Path -LiteralPath $c)) {
            $script:def_PythonPath = $c
            return $c
        }
    }
    return ""
}

function def_InvokeChildProcessSafe {
    param(
        [string]$Exe,
        [string[]]$Arguments,
        [string]$Name,
        [int]$Timeout = 180
    )
    $stdout = Join-Path $def_RUNTIME_DIR ("{0}_stdout.txt" -f ([regex]::Replace($Name,"[^A-Za-z0-9_.-]","_")))
    $stderr = Join-Path $def_RUNTIME_DIR ("{0}_stderr.txt" -f ([regex]::Replace($Name,"[^A-Za-z0-9_.-]","_")))
    $result = [ordered]@{Name=$Name; Exe=$Exe; ExitCode=$null; TimedOut=$false; Stdout=$stdout; Stderr=$stderr; Message=""}
    if ([string]::IsNullOrWhiteSpace($Exe) -or -not (Test-Path -LiteralPath $Exe)) {
        $result.Message = "Executable not found."
        return [pscustomobject]$result
    }
    try {
        $p = Start-Process -FilePath $Exe -ArgumentList $Arguments -NoNewWindow -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $exited = $p.WaitForExit($Timeout * 1000)
        if ($exited) {
            $result.ExitCode = $p.ExitCode
            $result.Message = "ExitCode $($p.ExitCode)"
        } else {
            $result.TimedOut = $true
            $result.Message = "Timed out after $Timeout sec. Child was not stopped due to no-stop-process policy."
        }
    } catch {
        $result.Message = $_.Exception.Message
    }
    return [pscustomobject]$result
}

function def_CreateParserScript {
    $parser = @'
param([string]$Target)
try {
    if (-not (Test-Path -LiteralPath $Target)) {
        Write-Output "MISSING`t$Target"
        exit 8
    }
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($Target, [ref]$tokens, [ref]$errors) | Out-Null
    if ($null -ne $errors -and $errors.Count -gt 0) {
        foreach ($e in $errors) {
            $line = 0
            $column = 0
            try { $line = $e.Extent.StartLineNumber; $column = $e.Extent.StartColumnNumber } catch {}
            Write-Output ("PARSE_ERROR`t{0}`t{1}`t{2}" -f $line,$column,$e.Message)
        }
        exit 2
    }
    Write-Output "OK"
    exit 0
} catch {
    Write-Output ("PARSER_FATAL`t" + $_.Exception.Message)
    exit 20
}
'@
    Set-Content -LiteralPath $def_PARSER_PS1 -Value $parser -Encoding UTF8
}

function def_TestPowerShellAstByChild {
    param([string]$Path)
    $pwsh = def_ResolvePwsh
    if ([string]::IsNullOrWhiteSpace($pwsh)) {
        return [pscustomobject]@{Path=$Path; Status="WARN_NO_PWSH"; ErrorCount=0; Message="pwsh not found"}
    }
    if (-not (Test-Path -LiteralPath $def_PARSER_PS1)) { def_CreateParserScript }
    $res = def_InvokeChildProcessSafe -Exe $pwsh -Arguments @("-NoProfile","-ExecutionPolicy","Bypass","-File",$def_PARSER_PS1,"-Target",$Path) -Name ("parse_" + [IO.Path]::GetFileName($Path)) -Timeout 60
    $text = ""
    try { if (Test-Path -LiteralPath $res.Stdout) { $text = Get-Content -LiteralPath $res.Stdout -Raw } } catch {}
    if ($res.ExitCode -eq 0 -and $text -match "OK") {
        return [pscustomobject]@{Path=$Path; Status="OK_PARSE"; ErrorCount=0; Message="PowerShell AST parse clean"}
    }
    $errCount = 0
    if ($text) { $errCount = ([regex]::Matches($text,"PARSE_ERROR")).Count }
    if ($errCount -le 0 -and $res.ExitCode -ne 0) { $errCount = 1 }
    return [pscustomobject]@{Path=$Path; Status="FAIL_PARSE"; ErrorCount=$errCount; Message=($text.Trim())}
}

function def_GetProjectPath {
    param([string]$Project)
    if ($Project -eq "ROOT") { return $Root }
    if ($Project -eq "SUPPORTIVE") { return $SupportiveDir }
    if ($Project -eq "TOOLS") { return (Join-Path $Root "tools") }
    return (Join-Path $FunctionalRoot $Project)
}

function def_Initialize {
    foreach ($dir in @($ToolRoot,$def_RUN_ROOT,$def_SANDBOX_ROOT,$def_RUNTIME_DIR,$def_REGISTRY_DIR,$def_REPORT_DIR,$def_LOG_DIR,$def_PLAN_DIR,$def_PROMPT_DIR,$def_BRIDGE_DIR,$def_ENGINE_FORGE_DIR,$def_ENGINE_DIR,$def_ENGINE_CONFIG_DIR,$def_ENGINE_REGISTRY_DIR,$def_ENGINE_FREEZE_DIR)) {
        def_EnsureDirectory $dir
    }
    $phaseCount = def_CountSafe $def_PARAM_PHASES
    $laneCount = 3 + (def_CountSafe $ProjectNames) + (def_CountSafe $ExtraProjectPaths)
    $script:def_TotalTasks = [math]::Max(1, $phaseCount + ($laneCount * 4))
    def_CreateParserScript
    def_WriteEngineForgeConfig
    def_AddRow "Round0" "GLOBAL" "POLICY" "Safety Policy" "OK_POLICY_LOCKED" "LOW" "PARALLEL_SAFE" "P0" "policy" (($def_PARAM_POLICY | ConvertTo-Json -Compress)) "Append-only sandbox-first policy is locked." $Root
    foreach ($a in $def_PARAM_ACCELERATORS) {
        def_AddRow "Round0" "GLOBAL" "ACCELERATOR" $a.Name "OK_ENABLED" "LOW" "PARALLEL_SAFE" "P1" $a.ID $a.Function "Accelerator enabled." ""
    }
    def_WriteLog "OK" ("Initialized run root: {0}" -f $def_RUN_ROOT)
    def_TaskDone "VIA Ultimate First Module" "Initialize complete"
}

function def_GetCommandFeatureScore {
    param([string]$Text)
    $score = 0
    $hits = @()
    foreach ($rule in $def_PARAM_ADVANTAGE_RULES) {
        if ($Text -match $rule.Pattern) {
            $score += [int]$rule.Weight
            $hits += $rule.Feature
        }
    }
    return [pscustomobject]@{Score=$score; Hits=($hits -join "; ")}
}

function def_Round1_CommandAdvantageLens {
    def_WriteLog "RUN" "Round1 Command Advantage Lens started."
    $all = @()
    foreach ($p in $def_PARAM_CANONICAL_COMMANDS) { $all += $p }
    try {
        if (Test-Path -LiteralPath $Downloads) {
            $downloadPs = Get-ChildItem -LiteralPath $Downloads -File -Filter "Invoke-VIA*.ps1" -ErrorAction SilentlyContinue
            foreach ($f in $downloadPs) { $all += $f.FullName }
        }
    } catch {}
    try {
        if (Test-Path -LiteralPath $Root) {
            $rootPs = Get-ChildItem -LiteralPath $Root -File -Filter "Invoke-VIA*.ps1" -ErrorAction SilentlyContinue
            foreach ($f in $rootPs) { $all += $f.FullName }
        }
    } catch {}
    $unique = @()
    foreach ($p in $all) {
        if ([string]::IsNullOrWhiteSpace($p)) { continue }
        if ($unique -notcontains $p) { $unique += $p }
    }
    foreach ($p in $unique) {
        $exists = Test-Path -LiteralPath $p
        $text = ""
        $hash = ""
        $lines = 0
        $bytes = 0
        if ($exists) {
            $text = def_ReadTextSafe -Path $p -MaxChars 1000000
            $hash = def_GetSha256Safe $p
            try { $lines = (Get-Content -LiteralPath $p -ErrorAction SilentlyContinue | Measure-Object -Line).Lines } catch {}
            try { $bytes = (Get-Item -LiteralPath $p).Length } catch {}
        }
        $sc = def_GetCommandFeatureScore -Text $text
        $status = "WARN_MISSING"
        $risk = "MEDIUM"
        $priority = "P2"
        if ($exists -and $sc.Score -ge 55) { $status = "OK_FIRST_TIER"; $risk = "LOW"; $priority = "P0" }
        elseif ($exists -and $sc.Score -ge 30) { $status = "OK_USEFUL"; $risk = "LOW"; $priority = "P1" }
        elseif ($exists) { $status = "WARN_LOW_SIGNAL"; $risk = "MEDIUM"; $priority = "P2" }
        $row = [pscustomobject]@{
            CommandPath = $p
            Exists = $exists
            Score = $sc.Score
            FeatureHits = $sc.Hits
            Lines = $lines
            Bytes = $bytes
            Sha256 = $hash
            Status = $status
            Risk = $risk
            Priority = $priority
        }
        $script:def_CommandRows += $row
        def_AddRow "Round1" "COMMAND" "ADVANTAGE_LENS" ([IO.Path]::GetFileName($p)) $status $risk "PARALLEL_SAFE" $priority "score" $sc.Score $sc.Hits $p
    }
    def_TaskDone "VIA Ultimate First Module" "Command Advantage Lens complete"
}

function def_Round1_FolderPanoramaLens {
    def_WriteLog "RUN" "Round1 Folder Panorama Lens started."
    $targets = @()
    $targets += [pscustomobject]@{Name="ROOT"; Path=$Root; Type="ROOT"}
    $targets += [pscustomobject]@{Name="SUPPORTIVE"; Path=$SupportiveDir; Type="SUPPORTIVE"}
    $targets += [pscustomobject]@{Name="TOOLS"; Path=(Join-Path $Root "tools"); Type="TOOLS"}
    foreach ($p in $ProjectNames) { $targets += [pscustomobject]@{Name=$p; Path=(def_GetProjectPath $p); Type="FUNCTIONAL"} }
    $idx = 1
    foreach ($p in $ExtraProjectPaths) { $targets += [pscustomobject]@{Name=("EXTRA_{0}" -f $idx); Path=$p; Type="EXTRA"}; $idx++ }
    foreach ($t in $targets) {
        $exists = Test-Path -LiteralPath $t.Path
        $files = @()
        if ($exists) { $files = def_GetFilesLight -Path $t.Path -MaxFiles $MaxFilesPerScanRoot }
        $psCount = def_CountSafe ($files | Where-Object { $_.Extension -in @(".ps1",".psm1",".psd1") })
        $pyCount = def_CountSafe ($files | Where-Object { $_.Extension -eq ".py" })
        $jsonCount = def_CountSafe ($files | Where-Object { $_.Extension -eq ".json" })
        $htmlCount = def_CountSafe ($files | Where-Object { $_.Extension -in @(".html",".htm") })
        $runCount = 0
        $reportCount = 0
        try {
            if ($exists) {
                $runCount = def_CountSafe (Get-ChildItem -LiteralPath $t.Path -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "RUN_*" })
                $reportCount = def_CountSafe (Get-ChildItem -LiteralPath $t.Path -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "report|matrix|summary" -and $_.Extension -in @(".html",".csv",".json") })
            }
        } catch {}
        $status = "WARN_MISSING"
        $risk = "MEDIUM"
        if ($exists -and (def_CountSafe $files) -gt 0) { $status = "OK_SCANNED"; $risk = "LOW" }
        elseif ($exists) { $status = "WARN_EMPTY_OR_FILTERED"; $risk = "MEDIUM" }
        $row = [pscustomobject]@{
            Project = $t.Name
            Type = $t.Type
            Path = $t.Path
            Exists = $exists
            ScannedFiles = def_CountSafe $files
            PowerShellFiles = $psCount
            PythonFiles = $pyCount
            JsonFiles = $jsonCount
            HtmlFiles = $htmlCount
            RunFolders = $runCount
            Reports = $reportCount
            Status = $status
            Risk = $risk
        }
        $script:def_ProjectRows += $row
        def_AddRow "Round1" $t.Name "FOLDER_LENS" "Folder Panorama" $status $risk "PARALLEL_SAFE" "P1" "files" (def_CountSafe $files) ("PS={0}; PY={1}; RUN={2}; REPORT={3}" -f $psCount,$pyCount,$runCount,$reportCount) $t.Path
    }
    def_TaskDone "VIA Ultimate First Module" "Folder Panorama Lens complete"
}

function def_GetConversationCandidateFiles {
    $candidates = @()
    foreach ($p in $ConversationLensPaths) { if (-not [string]::IsNullOrWhiteSpace($p)) { $candidates += $p } }
    try {
        if (Test-Path -LiteralPath $Downloads) {
            $patterns = @("已貼上文字*.txt","pasted*.txt","*.log","*conversation*.txt","*ChatGPT*.txt")
            foreach ($pat in $patterns) {
                $items = Get-ChildItem -LiteralPath $Downloads -File -Filter $pat -ErrorAction SilentlyContinue
                foreach ($i in $items) { $candidates += $i.FullName }
            }
        }
    } catch {}
    try {
        if (Test-Path -LiteralPath $Root) {
            $items = Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
                -not (def_IsExcludedPath $_.FullName) -and ($_.Name -match "已貼上文字|conversation|ChatGPT|run\.log|fatal|error") -and $_.Length -lt 5000000
            }
            foreach ($i in $items) { $candidates += $i.FullName }
        }
    } catch {}
    $unique = @()
    foreach ($p in $candidates) { if ($unique -notcontains $p) { $unique += $p } }
    return @($unique)
}

function def_Round1_ConversationHistoryLens {
    def_WriteLog "RUN" "Round1 Conversation / History Lens started."
    $files = def_GetConversationCandidateFiles
    foreach ($p in $files) {
        $exists = Test-Path -LiteralPath $p
        $text = ""
        $bytes = 0
        $fatal = 0
        $fail = 0
        $warn = 0
        $high = 0
        $ready = 0
        if ($exists) {
            try { $bytes = (Get-Item -LiteralPath $p).Length } catch {}
            $text = def_ReadTextSafe -Path $p -MaxChars 1000000
            $fatal = ([regex]::Matches($text,"\[FATAL\]|FAIL_FATAL|Exception")).Count
            $fail = ([regex]::Matches($text,"\bFAIL\b|FAIL_")).Count
            $warn = ([regex]::Matches($text,"\bWARN\b|WARN_")).Count
            $high = ([regex]::Matches($text,"\bHIGH\b|Risk\s*:?\s*HIGH")).Count
            $ready = ([regex]::Matches($text,"READY|COMPLETE|OK_")).Count
        }
        $signal = $fatal * 5 + $fail * 3 + $high * 2 + $warn
        $status = "OK_CONTEXT_READ"
        $risk = "LOW"
        $priority = "P2"
        if (-not $exists) { $status = "WARN_MISSING"; $risk = "MEDIUM" }
        elseif ($fatal -gt 0 -or $high -gt 10) { $status = "WARN_HISTORY_HAS_RED_FINDINGS"; $risk = "HIGH"; $priority = "P0" }
        elseif ($fail -gt 0 -or $warn -gt 10) { $status = "WARN_HISTORY_HAS_REVIEW_ITEMS"; $risk = "MEDIUM"; $priority = "P1" }
        $row = [pscustomobject]@{
            Path=$p; Exists=$exists; Bytes=$bytes; Fatal=$fatal; Fail=$fail; Warn=$warn; High=$high; Ready=$ready; Signal=$signal; Status=$status; Risk=$risk; Priority=$priority
        }
        $script:def_ConversationRows += $row
        def_AddRow "Round1" "CONVERSATION" "HISTORY_LENS" ([IO.Path]::GetFileName($p)) $status $risk "SEQUENTIAL_REQUIRED" $priority "signal" $signal ("fatal={0}; fail={1}; warn={2}; high={3}; ready={4}" -f $fatal,$fail,$warn,$high,$ready) $p
    }
    if ((def_CountSafe $files) -eq 0) {
        def_AddRow "Round1" "CONVERSATION" "HISTORY_LENS" "Local conversation/log files" "WARN_NO_LOCAL_RECORDS" "MEDIUM" "SEQUENTIAL_REQUIRED" "P1" "files" 0 "No local pasted/conversation/log files found. Current ChatGPT conversation cannot be read from Windows unless exported or pasted as files." $Downloads
    }
    def_TaskDone "VIA Ultimate First Module" "Conversation History Lens complete"
}

function def_Round1_PolicyAndSupportiveCheck {
    foreach ($p in $def_PARAM_SUPPORTIVE_FILES) {
        $exists = Test-Path -LiteralPath $p
        $status = "WARN_MISSING"
        $risk = "MEDIUM"
        if ($exists) { $status = "OK_FOUND"; $risk = "LOW" }
        def_AddRow "Round1" "SUPPORTIVE" "SUPPORTIVE_FILE" ([IO.Path]::GetFileName($p)) $status $risk "PARALLEL_SAFE" "P1" "exists" $exists "Supportive file availability check." $p
    }
    $pwsh = def_ResolvePwsh
    $python = def_ResolvePython
    $pwshStatus = "WARN_PWSH_NOT_FOUND"
    $pwshRisk = "HIGH"
    if (-not [string]::IsNullOrWhiteSpace($pwsh)) { $pwshStatus = "OK_PWSH_FOUND"; $pwshRisk = "LOW" }
    def_AddRow "Round1" "GLOBAL" "NATIVE_TOOL" "PowerShell 7" $pwshStatus $pwshRisk "SEQUENTIAL_REQUIRED" "P0" "path" $pwsh "PowerShell is required for AST and child dry probes." $pwsh
    $pyStatus = "WARN_PYTHON_NOT_FOUND"
    $pyRisk = "MEDIUM"
    if (-not [string]::IsNullOrWhiteSpace($python)) { $pyStatus = "OK_PYTHON_FOUND"; $pyRisk = "LOW" }
    def_AddRow "Round1" "GLOBAL" "NATIVE_TOOL" "Python" $pyStatus $pyRisk "PARALLEL_SAFE" "P1" "path" $python "Python is used for optional compile checks." $python
    def_TaskDone "VIA Ultimate First Module" "Policy and supportive check complete"
}

function def_CopyFileToSandbox {
    param([string]$Source,[string]$RelativeRoot)
    try {
        if (-not (Test-Path -LiteralPath $Source)) { return $false }
        $safeRoot = [regex]::Replace($RelativeRoot,"[^A-Za-z0-9_.-]","_")
        $targetDir = Join-Path $def_SANDBOX_ROOT $safeRoot
        def_EnsureDirectory $targetDir
        $target = Join-Path $targetDir ([IO.Path]::GetFileName($Source))
        Copy-Item -LiteralPath $Source -Destination $target -Force
        return $true
    } catch {
        return $false
    }
}

function def_Round2_SandboxCopy {
    def_WriteLog "RUN" "Round2 Sandbox Copy started."
    if (-not $CreateSandbox) {
        def_AddRow "Round2" "SANDBOX" "COPY" "Sandbox copy" "WARN_DISABLED" "MEDIUM" "SEQUENTIAL_REQUIRED" "P1" "enabled" $false "Sandbox creation was disabled by parameter." $def_SANDBOX_ROOT
        def_TaskDone "VIA Ultimate First Module" "Sandbox copy skipped"
        return
    }
    $copied = 0
    foreach ($r in @(def_AsPlainArray $script:def_CommandRows)) {
        if ($r.Exists) { if (def_CopyFileToSandbox -Source $r.CommandPath -RelativeRoot "commands") { $copied++ } }
    }
    foreach ($proj in @(def_AsPlainArray $script:def_ProjectRows)) {
        if (-not $proj.Exists) { continue }
        $files = def_GetFilesLight -Path $proj.Path -MaxFiles $MaxFilesPerProjectCopy
        $count = 0
        foreach ($f in $files) {
            if ($count -ge $MaxFilesPerProjectCopy) { break }
            try {
                $rel = [regex]::Replace($proj.Project,"[^A-Za-z0-9_.-]","_")
                $targetDir = Join-Path $def_SANDBOX_ROOT ("project_" + $rel)
                def_EnsureDirectory $targetDir
                $target = Join-Path $targetDir ([IO.Path]::GetFileName($f.FullName))
                if (-not (Test-Path -LiteralPath $target)) {
                    Copy-Item -LiteralPath $f.FullName -Destination $target -Force
                    $copied++
                    $count++
                }
            } catch {}
        }
    }
    def_AddRow "Round2" "SANDBOX" "COPY" "Sandbox Copy" "OK_SANDBOX_CREATED" "LOW" "PARALLEL_SAFE" "P0" "files" $copied "Selected scripts/docs/configs copied into isolated sandbox." $def_SANDBOX_ROOT
    def_TaskDone "VIA Ultimate First Module" "Sandbox copy complete"
}

function def_Round2_PowerShellAstSandbox {
    def_WriteLog "RUN" "Round2 PowerShell AST Sandbox started."
    $psFiles = @()
    try {
        if (Test-Path -LiteralPath $def_SANDBOX_ROOT) {
            $psFiles = Get-ChildItem -LiteralPath $def_SANDBOX_ROOT -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in @(".ps1",".psm1",".psd1") }
        }
    } catch {}
    $totalErr = 0
    $checked = 0
    foreach ($f in $psFiles) {
        $checked++
        $r = def_TestPowerShellAstByChild -Path $f.FullName
        $totalErr += [int]$r.ErrorCount
        if ($r.Status -ne "OK_PARSE") {
            def_AddRow "Round2" "SANDBOX" "POWERSHELL_AST" $f.Name $r.Status "HIGH" "SEQUENTIAL_REQUIRED" "P0" "parse_errors" $r.ErrorCount $r.Message $f.FullName
        }
    }
    $status = "OK_ALL_PARSE"
    $risk = "LOW"
    $class = "PARALLEL_SAFE"
    if ($totalErr -gt 0) { $status = "FAIL_PARSE_FOUND"; $risk = "HIGH"; $class = "SEQUENTIAL_REQUIRED" }
    elseif ($checked -eq 0) { $status = "WARN_NO_PS_FILES"; $risk = "MEDIUM" }
    def_AddRow "Round2" "SANDBOX" "POWERSHELL_AST" "PowerShell AST Summary" $status $risk $class "P0" "errors/files" ("{0}/{1}" -f $totalErr,$checked) "PowerShell syntax gate controls whether broad repair is allowed." $def_SANDBOX_ROOT
    def_TaskDone "VIA Ultimate First Module" "PowerShell AST sandbox complete"
}

function def_Round2_PythonCompileSandbox {
    def_WriteLog "RUN" "Round2 Python Compile Sandbox started."
    $python = def_ResolvePython
    $pyFiles = @()
    try {
        if (Test-Path -LiteralPath $def_SANDBOX_ROOT) {
            $pyFiles = Get-ChildItem -LiteralPath $def_SANDBOX_ROOT -Recurse -File -Filter "*.py" -ErrorAction SilentlyContinue
        }
    } catch {}
    if ([string]::IsNullOrWhiteSpace($python)) {
        def_AddRow "Round2" "SANDBOX" "PYTHON_COMPILE" "Python compile" "WARN_PYTHON_NOT_FOUND" "MEDIUM" "SEQUENTIAL_REQUIRED" "P1" "files" (def_CountSafe $pyFiles) "Python not found; compile check skipped." ""
        def_TaskDone "VIA Ultimate First Module" "Python compile skipped"
        return
    }
    $fail = 0
    $checked = 0
    foreach ($f in $pyFiles) {
        $checked++
        $res = def_InvokeChildProcessSafe -Exe $python -Arguments @("-m","py_compile",$f.FullName) -Name ("pycompile_" + $f.Name) -Timeout 60
        if ($res.ExitCode -ne 0 -or $res.TimedOut) {
            $fail++
            $msg = $res.Message
            try { if (Test-Path -LiteralPath $res.Stderr) { $msg = (Get-Content -LiteralPath $res.Stderr -Raw).Trim() } } catch {}
            def_AddRow "Round2" "SANDBOX" "PYTHON_COMPILE" $f.Name "FAIL_COMPILE" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exit" $res.ExitCode $msg $f.FullName
        }
    }
    $status = "OK_ALL_COMPILE"
    $risk = "LOW"
    $class = "PARALLEL_SAFE"
    if ($fail -gt 0) { $status = "FAIL_COMPILE_FOUND"; $risk = "HIGH"; $class = "SEQUENTIAL_REQUIRED" }
    elseif ($checked -eq 0) { $status = "WARN_NO_PY_FILES"; $risk = "LOW" }
    def_AddRow "Round2" "SANDBOX" "PYTHON_COMPILE" "Python Compile Summary" $status $risk $class "P1" "fail/files" ("{0}/{1}" -f $fail,$checked) "Python syntax gate completed." $def_SANDBOX_ROOT
    def_TaskDone "VIA Ultimate First Module" "Python compile sandbox complete"
}

function def_Round2_CandidateDryProbe {
    def_WriteLog "RUN" "Round2 Candidate Dry Probe started."
    if (-not $RunCandidateDryProbe) {
        def_AddRow "Round2" "COMMAND" "DRY_PROBE" "Candidate dry probe" "WARN_DISABLED" "MEDIUM" "SEQUENTIAL_REQUIRED" "P1" "enabled" $false "Dry probe disabled by parameter." ""
        def_TaskDone "VIA Ultimate First Module" "Candidate dry probe skipped"
        return
    }
    $pwsh = def_ResolvePwsh
    if ([string]::IsNullOrWhiteSpace($pwsh)) {
        def_AddRow "Round2" "COMMAND" "DRY_PROBE" "Candidate dry probe" "WARN_NO_PWSH" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "pwsh" "" "pwsh not found." ""
        def_TaskDone "VIA Ultimate First Module" "Candidate dry probe skipped"
        return
    }
    $firstTier = @(def_AsPlainArray $script:def_CommandRows | Where-Object { $_.Exists -and $_.Score -ge 55 } | Sort-Object Score -Descending | Select-Object -First 5)
    foreach ($cmd in $firstTier) {
        $parse = def_TestPowerShellAstByChild -Path $cmd.CommandPath
        if ($parse.Status -ne "OK_PARSE") {
            def_AddRow "Round2" "COMMAND" "DRY_PROBE" ([IO.Path]::GetFileName($cmd.CommandPath)) "WARN_PROBE_BLOCKED_BY_PARSE" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "parse" $parse.ErrorCount "Dry probe blocked because AST parse failed." $cmd.CommandPath
            continue
        }
        # We intentionally avoid invoking unknown repair/apply behavior. Probe with a safe parser only.
        def_AddRow "Round2" "COMMAND" "DRY_PROBE" ([IO.Path]::GetFileName($cmd.CommandPath)) "OK_PARSE_PROBE_ONLY" "LOW" "PARALLEL_SAFE" "P1" "score" $cmd.Score "Candidate passes parse probe. Full execution remains manual/controlled by this first module." $cmd.CommandPath
    }
    def_TaskDone "VIA Ultimate First Module" "Candidate dry probe complete"
}

function def_Round2_HydraRiskGate {
    def_WriteLog "RUN" "Round2 Hydra Risk Gate started."
    $rows = @(def_AsPlainArray $script:def_Rows)
    $seq = @($rows | Where-Object { $_.Risk -eq "HIGH" -or $_.Status -like "FAIL*" -or $_.Class -eq "SEQUENTIAL_REQUIRED" })
    $parallel = @($rows | Where-Object { $_.Risk -ne "HIGH" -and $_.Status -notlike "FAIL*" -and $_.Class -eq "PARALLEL_SAFE" })
    foreach ($r in $seq) {
        $kind = "Review"
        if ($r.Name -match "AST|Parse|PowerShell" -or $r.Status -match "PARSE") { $kind = "SyntaxFirst" }
        elseif ($r.Name -match "Python|Compile" -or $r.Status -match "COMPILE") { $kind = "CompileFirst" }
        elseif ($r.Scope -match "CONVERSATION" -or $r.Layer -match "HISTORY") { $kind = "HistoryRedFinding" }
        elseif ($r.Layer -match "NATIVE_TOOL|SUPPORTIVE") { $kind = "EnvironmentFirst" }
        $plan = [pscustomobject]@{Kind=$kind; Priority=$r.Priority; Risk=$r.Risk; Scope=$r.Scope; Name=$r.Name; Status=$r.Status; Action="Fix or review this before any broad repair/merge."; Path=$r.Path; Message=$r.Message}
        $script:def_SequentialPlanRows += $plan
        $script:def_RiskRows += [pscustomobject]@{RiskGate="SEQUENTIAL_REQUIRED"; Kind=$kind; Scope=$r.Scope; Name=$r.Name; Status=$r.Status; Priority=$r.Priority; Path=$r.Path}
    }
    foreach ($r in $parallel | Select-Object -First 500) {
        $script:def_ParallelPlanRows += [pscustomobject]@{Priority=$r.Priority; Scope=$r.Scope; Name=$r.Name; Status=$r.Status; Action="Can be checked/optimized after P0 blockers are cleared."; Path=$r.Path; Message=$r.Message}
    }
    $status = "OK_HYDRA_CLEAR"
    $risk = "LOW"
    $msg = "No sequential blockers detected."
    if ((def_CountSafe $seq) -gt 0) {
        $status = "WARN_HYDRA_GATED"
        $risk = "HIGH"
        $msg = "Sequential blockers detected. Broad repair and canonical merge remain blocked."
    }
    def_AddRow "Round2" "GLOBAL" "HYDRA_GATE" "Hydra Risk Gate" $status $risk "SEQUENTIAL_REQUIRED" "P0" "seq/parallel" ("{0}/{1}" -f (def_CountSafe $seq),(def_CountSafe $parallel)) $msg $def_RUN_ROOT
    def_TaskDone "VIA Ultimate First Module" "Hydra risk gate complete"
}


function def_NormalizeEngineId {
    param([string]$Name,[int]$Index)
    $base = [regex]::Replace([string]$Name, "[^A-Za-z0-9]+", "_").Trim("_")
    if ([string]::IsNullOrWhiteSpace($base)) { $base = "ENGINE" }
    return ("VIA_ENGINE_{0:000}_{1}" -f $Index,$base)
}

function def_WriteEngineForgeConfig {
    $cfgTarget = $def_ENGINE_CONFIG_JSON
    if (-not [string]::IsNullOrWhiteSpace($ConfigJson)) { $cfgTarget = $ConfigJson }
    $cfg = [ordered]@{
        schema = "VIA.EngineForge.Config"
        version = $def_PARAM_VERSION
        generated_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        mode = $Mode
        root = $Root
        downloads = $Downloads
        supportive_dir = $SupportiveDir
        functional_root = $FunctionalRoot
        tool_root = $ToolRoot
        run_root = $def_RUN_ROOT
        policy = $def_PARAM_POLICY
        supportive_files = $def_PARAM_SUPPORTIVE_FILES
        rules = [ordered]@{
            json_only_parameters = $true
            sandbox_first = $true
            freeze_after_expanded = $FreezeAfterExpanded
            no_original_apply_without_token = $true
            no_broad_autofix_before_parse_clean = $true
            max_rounds = $MaxRounds
        }
    }
    def_SaveJson -Object $cfg -Path $cfgTarget -Depth 10
    if ($cfgTarget -ne $def_ENGINE_CONFIG_JSON) { def_SaveJson -Object $cfg -Path $def_ENGINE_CONFIG_JSON -Depth 10 }
    def_AddRow "Round0" "ENGINE_FORGE" "CONFIG" "JSON Contract Config" "OK_CONFIG_READY" "LOW" "PARALLEL_SAFE" "P0" "file" $cfgTarget "Engine Forge config generated. JSON is the sole parameter contract." $cfgTarget
}

function def_DecideEngineLanguage {
    param([string]$FunctionName,[string]$SourcePath,[string]$Text)
    $n = [string]$FunctionName
    $p = [string]$SourcePath
    $t = [string]$Text
    if ($n -match "Html|Report|Renderer|UI|Matrix" -or $p -match "html") { return "JavaScript" }
    if ($n -match "Data|Parquet|DuckDB|Csv|Json|Manifest|Schema|Hash|Freeze|Registry|Lens|Score|Triage" -or $t -match "pandas|duckdb|pyarrow|ConvertTo-Json") { return "Python" }
    if ($n -match "Invoke|Start|Copy|Path|Sandbox|Nexus|Bridge|PowerShell|Ast|Process|Launcher|Gate") { return "PowerShell" }
    return "PowerShell"
}

function def_GetEngineType {
    param([string]$FunctionName,[string]$Text)
    $n = [string]$FunctionName
    if ($n -match "Lens|Scan|Inventory|History") { return "LensEngine" }
    if ($n -match "Triage|Risk|Hydra") { return "RiskEngine" }
    if ($n -match "Bridge|Nexus|Adapter") { return "BridgeEngine" }
    if ($n -match "Html|Report|Renderer") { return "RendererEngine" }
    if ($n -match "Freeze|Hash|Seal") { return "FreezeEngine" }
    if ($n -match "Sandbox|Smoke|Probe|Test") { return "SandboxTestEngine" }
    if ($n -match "Json|Schema|Contract|Manifest") { return "ContractEngine" }
    return "FunctionEngine"
}

function def_GetEngineRisk {
    param([string]$FunctionName,[string]$Text)
    $n = [string]$FunctionName
    $t = [string]$Text
    if ($t -match "Remove-Item|Stop-Process|Set-Content|Copy-Item|Move-Item|Invoke-Expression|iex|Start-Process" -and $n -notmatch "Report|Export|Html") { return "MEDIUM" }
    if ($t -match "DROP TABLE|DELETE FROM|canonical|merge|db_write") { return "HIGH" }
    return "LOW"
}

function def_ExtractFunctionDefinitions {
    param([string]$Path,[string]$Text)
    $out = @()
    if ([string]::IsNullOrWhiteSpace($Text)) { return @() }
    $matches = [regex]::Matches($Text, "(?m)^\s*function\s+([A-Za-z_][A-Za-z0-9_\-]*)")
    foreach ($m in $matches) {
        $fn = $m.Groups[1].Value
        if ([string]::IsNullOrWhiteSpace($fn)) { continue }
        $out += [pscustomobject]@{FunctionName=$fn; SourcePath=$Path}
    }
    return @($out)
}

function def_Round1_EngineExpansionLens {
    def_WriteLog "RUN" "Round1 Engine Expansion Lens started."
    $index = 1
    $seen = @()
    $commandRows = @(def_AsPlainArray $script:def_CommandRows | Where-Object { $_.Exists -eq $true } | Sort-Object Score -Descending | Select-Object -First 30)
    foreach ($cmd in $commandRows) {
        $path = [string]$cmd.CommandPath
        $text = def_ReadTextSafe -Path $path -MaxChars 1200000
        $defs = def_ExtractFunctionDefinitions -Path $path -Text $text
        foreach ($d in $defs) {
            $key = ("{0}|{1}" -f $d.FunctionName,$path)
            if ($seen -contains $key) { continue }
            $seen += $key
            $lang = def_DecideEngineLanguage -FunctionName $d.FunctionName -SourcePath $path -Text $text
            $etype = def_GetEngineType -FunctionName $d.FunctionName -Text $text
            $risk = def_GetEngineRisk -FunctionName $d.FunctionName -Text $text
            $engineId = def_NormalizeEngineId -Name $d.FunctionName -Index $index
            $status = "OK_ENGINE_CANDIDATE"
            $priority = "P2"
            if ($risk -eq "HIGH") { $status = "WARN_REQUIRES_SEQUENTIAL_GATE"; $priority = "P0" }
            elseif ($etype -in @("ContractEngine","RiskEngine","BridgeEngine","SandboxTestEngine","FreezeEngine")) { $priority = "P1" }
            $row = [pscustomobject]@{
                EngineID = $engineId
                FunctionName = $d.FunctionName
                EngineName = $d.FunctionName
                EngineType = $etype
                Language = $lang
                SourcePath = $path
                SourceSha256 = def_GetSha256Safe $path
                Risk = $risk
                Priority = $priority
                Status = $status
                InputContract = "input.schema.json"
                OutputContract = "output.schema.json"
                FreezePolicy = "Freeze after expanded; future change through adapter or new version."
            }
            $script:def_EngineRows += $row
            $script:def_EngineCapabilityRows += [pscustomobject]@{EngineID=$engineId; Capability=$etype; Language=$lang; FunctionName=$d.FunctionName; SourcePath=$path; Risk=$risk; Priority=$priority}
            $script:def_EngineDependencyRows += [pscustomobject]@{EngineID=$engineId; DependencyType="Runtime"; DependencyName=$lang; Required=$true; Status="PLANNED"; Note="Resolved by launcher before smoke test."}
            def_AddRow "Round1" "ENGINE" "EXPANSION_LENS" $d.FunctionName $status $risk "ENGINE_CANDIDATE" $priority "language" $lang ("Type={0}; JSON contract required; FreezeAfterExpanded={1}" -f $etype,$FreezeAfterExpanded) $path
            $index++
            if ($index -gt 120) { break }
        }
        if ($index -gt 120) { break }
    }
    if ((def_CountSafe $script:def_EngineRows) -eq 0) {
        def_AddRow "Round1" "ENGINE" "EXPANSION_LENS" "No Function Engines Detected" "WARN_NO_ENGINE_CANDIDATE" "MEDIUM" "SEQUENTIAL_REQUIRED" "P1" "count" 0 "No function definitions found in available command files." ""
    }
    def_TaskDone "VIA Ultimate Engine Forge" "Engine Expansion Lens complete"
}

function def_GetEngineRunScript {
    param([string]$Language,[string]$EngineName)
    if ($Language -eq "Python") {
        return (@'
import json, sys, pathlib, datetime

def main():
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else "engine.config.json"
    data = {}
    try:
        data = json.loads(pathlib.Path(cfg_path).read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"status":"FAIL_CONFIG_READ","engine":"__ENGINE_NAME__","error":str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status":"OK_DRY_RUN","engine":"__ENGINE_NAME__","mode":data.get("mode","dry_run"),"timestamp":datetime.datetime.now().isoformat()}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'@).Replace("__ENGINE_NAME__", $EngineName)
    }
    if ($Language -eq "JavaScript") {
        return (@'
const fs = require("fs");
const path = process.argv[2] || "engine.config.json";
try {
  const cfg = JSON.parse(fs.readFileSync(path, "utf8"));
  console.log(JSON.stringify({status:"OK_DRY_RUN", engine:"__ENGINE_NAME__", mode:cfg.mode || "dry_run", timestamp:new Date().toISOString()}));
  process.exit(0);
} catch (err) {
  console.log(JSON.stringify({status:"FAIL_CONFIG_READ", engine:"__ENGINE_NAME__", error:String(err)}));
  process.exit(2);
}
'@).Replace("__ENGINE_NAME__", $EngineName)
    }
    return (@'
param([string]$ConfigPath = "engine.config.json")
try {
    $cfg = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
    [pscustomobject]@{status="OK_DRY_RUN"; engine="__ENGINE_NAME__"; mode=$cfg.mode; timestamp=(Get-Date -Format o)} | ConvertTo-Json -Compress
    exit 0
} catch {
    [pscustomobject]@{status="FAIL_CONFIG_READ"; engine="__ENGINE_NAME__"; error=$_.Exception.Message} | ConvertTo-Json -Compress
    exit 2
}
'@).Replace("__ENGINE_NAME__", $EngineName)
}

function def_WriteEngineFiles {
    param([object]$EngineRow)
    $enginePath = Join-Path $def_ENGINE_DIR $EngineRow.EngineID
    def_EnsureDirectory $enginePath
    $entry = "run.ps1"
    if ($EngineRow.Language -eq "Python") { $entry = "run.py" }
    elseif ($EngineRow.Language -eq "JavaScript") { $entry = "run.js" }
    $manifest = [ordered]@{
        schema = "VIA.Engine.Manifest"
        engine_id = $EngineRow.EngineID
        engine_name = $EngineRow.EngineName
        function_name = $EngineRow.FunctionName
        engine_type = $EngineRow.EngineType
        version = "1.0.0"
        language = $EngineRow.Language
        entrypoint = $entry
        source_path = $EngineRow.SourcePath
        source_sha256 = $EngineRow.SourceSha256
        policy = $def_PARAM_POLICY
        json_contract_required = $true
        freeze_after_expanded = $FreezeAfterExpanded
    }
    $inputSchema = [ordered]@{
        '$schema' = "https://json-schema.org/draft/2020-12/schema"
        title = $EngineRow.EngineName + " Input"
        type = "object"
        required = @("engine_id","mode","input","policy")
        properties = [ordered]@{
            engine_id = [ordered]@{type="string"}
            mode = [ordered]@{type="string"; enum=@("dry_run","sandbox","actual")}
            input = [ordered]@{type="object"}
            options = [ordered]@{type="object"}
            policy = [ordered]@{type="object"}
        }
    }
    $outputSchema = [ordered]@{
        '$schema' = "https://json-schema.org/draft/2020-12/schema"
        title = $EngineRow.EngineName + " Output"
        type = "object"
        required = @("status","engine")
        properties = [ordered]@{
            status = [ordered]@{type="string"}
            engine = [ordered]@{type="string"}
            result = [ordered]@{type="object"}
            error = [ordered]@{type="string"}
        }
    }
    $engineConfig = [ordered]@{
        schema = "VIA.Engine.RuntimeConfig"
        engine_id = $EngineRow.EngineID
        mode = "dry_run"
        input = [ordered]@{}
        options = [ordered]@{}
        policy = $def_PARAM_POLICY
        paths = [ordered]@{root=$Root; run_root=$def_RUN_ROOT; engine_path=$enginePath}
    }
    def_SaveJson -Object $manifest -Path (Join-Path $enginePath "manifest.json") -Depth 12
    def_SaveJson -Object $inputSchema -Path (Join-Path $enginePath "input.schema.json") -Depth 12
    def_SaveJson -Object $outputSchema -Path (Join-Path $enginePath "output.schema.json") -Depth 12
    def_SaveJson -Object $engineConfig -Path (Join-Path $enginePath "engine.config.json") -Depth 12
    $runText = def_GetEngineRunScript -Language $EngineRow.Language -EngineName $EngineRow.EngineName
    Set-Content -LiteralPath (Join-Path $enginePath $entry) -Value $runText -Encoding UTF8
    $readme = "# " + $EngineRow.EngineName + "`r`n`r`nGenerated by VIA Ultimate Engine Forge v0.6.0.`r`n`r`n- Engine ID: " + $EngineRow.EngineID + "`r`n- Language: " + $EngineRow.Language + "`r`n- Source: " + $EngineRow.SourcePath + "`r`n- Policy: JSON-only input, sandbox-first, freeze-after-expanded.`r`n"
    Set-Content -LiteralPath (Join-Path $enginePath "README.md") -Value $readme -Encoding UTF8
    return [pscustomobject]@{EngineID=$EngineRow.EngineID; EnginePath=$enginePath; Entrypoint=$entry}
}

function def_Round2_JsonContractAndEngineForge {
    def_WriteLog "RUN" "Round2 JSON Contract and Engine Forge started."
    if (-not $BuildEngineStubs) {
        def_AddRow "Round2" "ENGINE" "JSON_CONTRACT" "Engine Stub Build" "WARN_DISABLED" "MEDIUM" "SEQUENTIAL_REQUIRED" "P1" "build" $false "BuildEngineStubs is disabled." $def_ENGINE_DIR
        def_TaskDone "VIA Ultimate Engine Forge" "JSON Contract and Engine Forge skipped"
        return
    }
    $rows = @(def_AsPlainArray $script:def_EngineRows)
    foreach ($er in $rows) {
        $created = def_WriteEngineFiles -EngineRow $er
        $manifestPath = Join-Path $created.EnginePath "manifest.json"
        $inputPath = Join-Path $created.EnginePath "input.schema.json"
        $outputPath = Join-Path $created.EnginePath "output.schema.json"
        $status = "OK_ENGINE_STUB_READY"
        $risk = "LOW"
        if (-not (Test-Path -LiteralPath $manifestPath) -or -not (Test-Path -LiteralPath $inputPath) -or -not (Test-Path -LiteralPath $outputPath)) { $status = "FAIL_CONTRACT_MISSING"; $risk = "HIGH" }
        def_AddRow "Round2" "ENGINE" "JSON_CONTRACT" $er.EngineName $status $risk "CONTRACT_GATE" "P0" "engine_id" $er.EngineID "Engine manifest/input schema/output schema/config generated." $created.EnginePath
    }
    def_SaveJson -Object @(def_AsPlainArray $script:def_EngineRows) -Path $def_ENGINE_REGISTRY_JSON -Depth 12
    def_TaskDone "VIA Ultimate Engine Forge" "JSON Contract and Engine Forge complete"
}

function def_Round2_EngineSmokeTest {
    def_WriteLog "RUN" "Round2 Engine Smoke Test started."
    $rows = @(def_AsPlainArray $script:def_EngineRows | Select-Object -First 40)
    foreach ($er in $rows) {
        $enginePath = Join-Path $def_ENGINE_DIR $er.EngineID
        $cfg = Join-Path $enginePath "engine.config.json"
        $status = "WARN_SMOKE_SKIPPED"
        $risk = "MEDIUM"
        $msg = "Runtime not available or mode InspectOnly."
        if ($Mode -eq "InspectOnly") {
            $msg = "Mode InspectOnly: smoke test intentionally skipped."
        } else {
            if ($er.Language -eq "PowerShell") {
                $pwsh = def_ResolvePwsh
                if (-not [string]::IsNullOrWhiteSpace($pwsh)) {
                    $res = def_InvokeChildProcessSafe -Exe $pwsh -Arguments @("-NoProfile","-ExecutionPolicy","Bypass","-File",(Join-Path $enginePath "run.ps1"),"-ConfigPath",$cfg) -Name ("engine_" + $er.EngineID) -Timeout 45
                    if ($res.ExitCode -eq 0) { $status = "OK_SMOKE_PASS"; $risk = "LOW" } else { $status = "WARN_SMOKE_REVIEW"; $risk = "MEDIUM" }
                    $msg = $res.Message
                }
            } elseif ($er.Language -eq "Python") {
                $py = def_ResolvePython
                if (-not [string]::IsNullOrWhiteSpace($py)) {
                    $res = def_InvokeChildProcessSafe -Exe $py -Arguments @((Join-Path $enginePath "run.py"),$cfg) -Name ("engine_" + $er.EngineID) -Timeout 45
                    if ($res.ExitCode -eq 0) { $status = "OK_SMOKE_PASS"; $risk = "LOW" } else { $status = "WARN_SMOKE_REVIEW"; $risk = "MEDIUM" }
                    $msg = $res.Message
                }
            } elseif ($er.Language -eq "JavaScript") {
                $node = ""
                try { $cmd = Get-Command node -ErrorAction SilentlyContinue; if ($cmd) { $node = $cmd.Source } } catch {}
                if (-not [string]::IsNullOrWhiteSpace($node)) {
                    $res = def_InvokeChildProcessSafe -Exe $node -Arguments @((Join-Path $enginePath "run.js"),$cfg) -Name ("engine_" + $er.EngineID) -Timeout 45
                    if ($res.ExitCode -eq 0) { $status = "OK_SMOKE_PASS"; $risk = "LOW" } else { $status = "WARN_SMOKE_REVIEW"; $risk = "MEDIUM" }
                    $msg = $res.Message
                }
            }
        }
        def_AddRow "Round2" "ENGINE" "SMOKE_TEST" $er.EngineName $status $risk "SANDBOX_TEST" "P1" "language" $er.Language $msg $enginePath
    }
    def_TaskDone "VIA Ultimate Engine Forge" "Engine Smoke Test complete"
}

function def_Round3_EngineFreezeGate {
    def_WriteLog "RUN" "Round3 Engine Freeze Gate started."
    $rows = @(def_AsPlainArray $script:def_EngineRows)
    foreach ($er in $rows) {
        $enginePath = Join-Path $def_ENGINE_DIR $er.EngineID
        $manifestPath = Join-Path $enginePath "manifest.json"
        $inputPath = Join-Path $enginePath "input.schema.json"
        $outputPath = Join-Path $enginePath "output.schema.json"
        $entry = "run.ps1"
        if ($er.Language -eq "Python") { $entry = "run.py" }
        elseif ($er.Language -eq "JavaScript") { $entry = "run.js" }
        $entryPath = Join-Path $enginePath $entry
        $freeze = [ordered]@{
            schema = "VIA.Engine.FreezeManifest"
            engine_id = $er.EngineID
            engine_name = $er.EngineName
            version = "1.0.0"
            language = $er.Language
            entrypoint = $entry
            generated_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
            freeze_enabled = $FreezeAfterExpanded
            freeze_reason = "Expanded to safe first boundary with JSON input/output contract and sandbox smoke gate."
            source_hash = $er.SourceSha256
            manifest_hash = def_GetSha256Safe $manifestPath
            input_schema_hash = def_GetSha256Safe $inputPath
            output_schema_hash = def_GetSha256Safe $outputPath
            entrypoint_hash = def_GetSha256Safe $entryPath
            allowed_future_changes = @("engine.config.json", "adapter", "wrapper", "new engine version", "test cases", "report views")
            forbidden_future_changes = @("direct source mutation without approval token", "hidden parameters", "unclear side effects", "canonical merge during dry-run")
            adapter_policy = "Freeze core; future changes through versioned adapter or new engine version."
            rollback_path = $enginePath
        }
        $freezePath = Join-Path $enginePath "freeze.manifest.json"
        def_SaveJson -Object $freeze -Path $freezePath -Depth 12
        $status = "OK_FREEZE_READY"
        $risk = "LOW"
        if (-not $FreezeAfterExpanded) { $status = "WARN_FREEZE_DISABLED"; $risk = "MEDIUM" }
        if (-not (Test-Path -LiteralPath $freezePath)) { $status = "FAIL_FREEZE_MISSING"; $risk = "HIGH" }
        $fr = [pscustomobject]@{
            EngineID = $er.EngineID
            EngineName = $er.EngineName
            Language = $er.Language
            Status = $status
            Risk = $risk
            FreezeManifest = $freezePath
            ManifestHash = $freeze.manifest_hash
            InputSchemaHash = $freeze.input_schema_hash
            OutputSchemaHash = $freeze.output_schema_hash
            EntrypointHash = $freeze.entrypoint_hash
            AdapterPolicy = $freeze.adapter_policy
        }
        $script:def_FreezeRows += $fr
        def_AddRow "Round3" "ENGINE" "FREEZE_GATE" $er.EngineName $status $risk "FREEZE_GATE" "P0" "engine_id" $er.EngineID "Freeze manifest generated; direct core mutation blocked by policy." $freezePath
    }
    def_SaveJson -Object @(def_AsPlainArray $script:def_FreezeRows) -Path $def_ENGINE_FREEZE_JSON -Depth 12
    def_TaskDone "VIA Ultimate Engine Forge" "Engine Freeze Gate complete"
}

function def_Round3_MultiProjectConvergence {
    def_WriteLog "RUN" "Round3 MultiProject Convergence started."
    $cmdBest = @(def_AsPlainArray $script:def_CommandRows | Where-Object { $_.Exists } | Sort-Object Score -Descending | Select-Object -First 1)
    $bestName = "This v0.5.0 first module"
    $bestPath = $PSCommandPath
    if ((def_CountSafe $cmdBest) -gt 0) {
        $bestName = [IO.Path]::GetFileName($cmdBest[0].CommandPath)
        $bestPath = $cmdBest[0].CommandPath
    }
    $seqCount = def_CountSafe $script:def_SequentialPlanRows
    $parCount = def_CountSafe $script:def_ParallelPlanRows
    $nextStatus = "READY"
    $nextRisk = "LOW"
    $nextAction = "Run v0.5.0 as the generic first entry, then handle sequential P0 items only."
    if ($seqCount -gt 0) {
        $nextStatus = "READY_WITH_REVIEW"
        $nextRisk = "HIGH"
        $nextAction = "Do not broad-fix. Clear P0 sequential blockers, then rerun this first module."
    }
    $script:def_NextActionRows += [pscustomobject]@{Step=1; Phase="First Entry"; Action="Run this v0.5.0 Ultimate First Module"; Command=("pwsh -NoProfile -ExecutionPolicy Bypass -File `"{0}`"" -f $PSCommandPath); Risk="LOW"; Why="It consolidates command advantage lens, folder lens, conversation lens, sandbox gate, Hydra triage and report seal."}
    $script:def_NextActionRows += [pscustomobject]@{Step=2; Phase="Sequential P0"; Action="Fix only P0 syntax/environment/history red findings"; Command="Review VIA_Sequential_RepairPlan.csv"; Risk="HIGH"; Why="Avoid Hydra risk by not repairing unrelated modules simultaneously."}
    $script:def_NextActionRows += [pscustomobject]@{Step=3; Phase="Parallel Safe"; Action="After P0 is zero, apply parallel-safe optimizations in sandbox"; Command="Review VIA_ParallelSafe_OptimizationPlan.csv"; Risk="MEDIUM"; Why="Low-coupling improvements should wait until blockers are cleared."}
    $script:def_NextActionRows += [pscustomobject]@{Step=4; Phase="Rerun"; Action="Rerun v0.5.0 and compare history"; Command=("pwsh -NoProfile -ExecutionPolicy Bypass -File `"{0}`"" -f $PSCommandPath); Risk="LOW"; Why="Repeat a few rounds until HIGH/P0 converges to zero."}
    def_AddRow "Round3" "GLOBAL" "CONVERGENCE" "Best First Entry" $nextStatus $nextRisk "SEQUENTIAL_REQUIRED" "P0" "seq/parallel" ("{0}/{1}" -f $seqCount,$parCount) ("Best inherited command signal: {0}; next action: {1}" -f $bestName,$nextAction) $bestPath
    def_TaskDone "VIA Ultimate First Module" "Multi-project convergence complete"
}

function def_Round3_AISandboxPromptPack {
    def_WriteLog "RUN" "Round3 AI Sandbox Prompt Pack started."
    $highRows = @(def_AsPlainArray $script:def_Rows | Where-Object { $_.Risk -eq "HIGH" -or $_.Status -like "FAIL*" } | Select-Object -First 80)
    $prompt = @()
    $prompt += "# VIA AI Sandbox Review Prompt Pack"
    $prompt += ""
    $prompt += "Run ID: $def_PARAM_RUN_ID"
    $prompt += "Policy: no DB write; no canonical merge; no destructive delete; no stop-process; append-only; sandbox-first; max 3 rounds."
    $prompt += ""
    $prompt += "## Objective"
    $prompt += "Review the following sequential blockers and produce a minimal P0-only repair plan. Do not propose broad rewrite or canonical merge until parse/compile/environment blockers are zero."
    $prompt += ""
    $prompt += "## High-risk findings"
    foreach ($r in $highRows) {
        $prompt += ("- [{0}] {1}/{2}/{3}: {4} | {5} | {6}" -f $r.Priority,$r.Scope,$r.Layer,$r.Name,$r.Status,$r.Message,$r.Path)
    }
    if ((def_CountSafe $highRows) -eq 0) { $prompt += "- No HIGH/FAIL findings detected in this run." }
    $prompt += ""
    $prompt += "## Required response format"
    $prompt += "1. P0 sequential fixes only."
    $prompt += "2. Parallel-safe improvements after P0 zero."
    $prompt += "3. Sandbox test commands."
    $prompt += "4. Rerun command."
    $prompt += "5. Explicit Hydra-risk notes."
    Set-Content -LiteralPath $def_AI_PROMPT_MD -Value ($prompt -join "`r`n") -Encoding UTF8
    if ($EnableExternalAiHook -and -not [string]::IsNullOrWhiteSpace($AiHookCommand)) {
        def_AddRow "Round3" "AI" "AI_HOOK" "External AI Hook" "WARN_HOOK_DECLARED_NOT_AUTO_RUN" "MEDIUM" "SEQUENTIAL_REQUIRED" "P1" "enabled" $true "External AI hook command was declared, but this script does not auto-send private project files. Use the prompt pack manually or wire a reviewed local hook." $AiHookCommand
    } else {
        def_AddRow "Round3" "AI" "PROMPT_PACK" "AI Sandbox Review Prompt" "OK_PROMPT_PACK_READY" "LOW" "PARALLEL_SAFE" "P1" "file" $def_AI_PROMPT_MD "AI review pack generated locally. No external network or AI call was made." $def_AI_PROMPT_MD
    }
    def_TaskDone "VIA Ultimate First Module" "AI sandbox prompt pack complete"
}

function def_Round3_BridgeAndFirstCommand {
    def_WriteLog "RUN" "Round3 Bridge and First Command started."
    $first = @'
param(
    [string]$ScriptPath = "__SCRIPT_PATH__"
)
pwsh -NoProfile -ExecutionPolicy Bypass -File $ScriptPath
'@
    $first = $first.Replace("__SCRIPT_PATH__", $PSCommandPath)
    Set-Content -LiteralPath $def_FIRST_COMMAND_PS1 -Value $first -Encoding UTF8
    $bridge = @'
function def_InvokeVIAUltimateEngineForge {
    param([string]$ScriptPath = "__SCRIPT_PATH__")
    pwsh -NoProfile -ExecutionPolicy Bypass -File $ScriptPath
}
function def_GetVIAUltimateEngineForgeArtifacts {
    [pscustomobject]@{
        ReportHtml = "__REPORT_HTML__"
        MatrixCsv  = "__MATRIX_CSV__"
        CommandCsv = "__COMMAND_CSV__"
        ProjectCsv = "__PROJECT_CSV__"
        RiskCsv    = "__RISK_CSV__"
        PromptPack = "__AI_PROMPT__"
        RunRoot    = "__RUN_ROOT__"
    }
}
Export-ModuleMember -Function def_InvokeVIAUltimateFirstModule, def_GetVIAUltimateEngineForgeArtifacts
'@
    $bridge = $bridge.Replace("__SCRIPT_PATH__", $PSCommandPath)
    $bridge = $bridge.Replace("__REPORT_HTML__", $def_REPORT_HTML)
    $bridge = $bridge.Replace("__MATRIX_CSV__", $def_MATRIX_CSV)
    $bridge = $bridge.Replace("__COMMAND_CSV__", $def_COMMAND_CSV)
    $bridge = $bridge.Replace("__PROJECT_CSV__", $def_PROJECT_CSV)
    $bridge = $bridge.Replace("__RISK_CSV__", $def_RISK_CSV)
    $bridge = $bridge.Replace("__AI_PROMPT__", $def_AI_PROMPT_MD)
    $bridge = $bridge.Replace("__RUN_ROOT__", $def_RUN_ROOT)
    Set-Content -LiteralPath $def_BRIDGE_PSM1 -Value $bridge -Encoding UTF8
    def_AddRow "Round3" "GLOBAL" "FIRST_COMMAND" "Best Generic First Command" "OK_READY" "LOW" "PARALLEL_SAFE" "P0" "file" $def_FIRST_COMMAND_PS1 "Reusable first command wrapper generated." $def_FIRST_COMMAND_PS1
    def_AddRow "Round3" "GLOBAL" "BRIDGE" "Ultimate First Module Bridge" "OK_READY" "LOW" "PARALLEL_SAFE" "P1" "file" $def_BRIDGE_PSM1 "Bridge module generated for later orchestration." $def_BRIDGE_PSM1
    def_TaskDone "VIA Ultimate First Module" "Bridge and first command complete"
}

function def_ExportAll {
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_Rows) -Path $def_MATRIX_CSV
    def_SaveJson -Object @(def_AsPlainArray $script:def_Rows) -Path $def_MATRIX_JSON -Depth 10
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_CommandRows) -Path $def_COMMAND_CSV
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_ProjectRows) -Path $def_PROJECT_CSV
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_ConversationRows) -Path $def_CONVO_CSV
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_RiskRows) -Path $def_RISK_CSV
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_SequentialPlanRows) -Path $def_SEQ_PLAN_CSV
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_ParallelPlanRows) -Path $def_PAR_PLAN_CSV
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_NextActionRows) -Path $def_NEXT_ACTION_CSV
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_EngineRows) -Path $def_ENGINE_REGISTRY_CSV
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_EngineCapabilityRows) -Path $def_ENGINE_CAPABILITY_CSV
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_EngineDependencyRows) -Path $def_ENGINE_DEPENDENCY_CSV
    def_SaveCsv -Rows @(def_AsPlainArray $script:def_FreezeRows) -Path $def_ENGINE_FREEZE_CSV
    def_SaveJson -Object @(def_AsPlainArray $script:def_EngineRows) -Path $def_ENGINE_REGISTRY_JSON -Depth 12
    def_SaveJson -Object @(def_AsPlainArray $script:def_FreezeRows) -Path $def_ENGINE_FREEZE_JSON -Depth 12
}

function def_BuildHtmlTable {
    param([object[]]$Rows,[string[]]$Columns)
    if ((def_CountSafe $Rows) -eq 0) { return "<p class='muted'>No rows.</p>" }
    $html = @()
    $html += "<table>"
    $html += "<thead><tr>"
    foreach ($c in $Columns) { $html += ("<th>{0}</th>" -f (def_HtmlEncode $c)) }
    $html += "</tr></thead><tbody>"
    foreach ($r in $Rows) {
        $html += "<tr>"
        foreach ($c in $Columns) {
            $v = ""
            try { $prop = $r.PSObject.Properties[$c]; if ($null -ne $prop) { $v = $prop.Value } } catch {}
            $html += ("<td>{0}</td>" -f (def_HtmlEncode $v))
        }
        $html += "</tr>"
    }
    $html += "</tbody></table>"
    return ($html -join "`r`n")
}

function def_WriteHtmlReport {
    $rows = @(def_AsPlainArray $script:def_Rows)
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $fail = def_CountSafe ($rows | Where-Object { $_.Status -like "FAIL*" })
    $high = def_CountSafe ($rows | Where-Object { $_.Risk -eq "HIGH" })
    $seq = def_CountSafe $script:def_SequentialPlanRows
    $par = def_CountSafe $script:def_ParallelPlanRows
    $pct = def_GetPercent -Done $script:def_CompletedTasks -Total $script:def_TotalTasks
    $status = "READY"
    $risk = "LOW"
    if ($fail -gt 0 -or $high -gt 0 -or $seq -gt 0) { $status = "READY_WITH_REVIEW"; $risk = "HIGH" }
    elseif ($warn -gt 0) { $status = "READY_WITH_WARNINGS"; $risk = "MEDIUM" }
    $matrixHtml = def_BuildHtmlTable -Rows ($rows | Select-Object -First 600) -Columns @("Round","Scope","Layer","Name","Status","Risk","Class","Priority","Metric","Value","Message","Path")
    $cmdHtml = def_BuildHtmlTable -Rows (@(def_AsPlainArray $script:def_CommandRows) | Sort-Object Score -Descending | Select-Object -First 80) -Columns @("Score","Status","Risk","Priority","FeatureHits","CommandPath","Lines","Bytes","Sha256")
    $engineHtml = def_BuildHtmlTable -Rows (@(def_AsPlainArray $script:def_EngineRows) | Select-Object -First 120) -Columns @("EngineID","EngineName","EngineType","Language","Status","Risk","Priority","SourcePath","FreezePolicy")
    $freezeHtml = def_BuildHtmlTable -Rows (@(def_AsPlainArray $script:def_FreezeRows) | Select-Object -First 120) -Columns @("EngineID","EngineName","Language","Status","Risk","FreezeManifest","AdapterPolicy")
    $capHtml = def_BuildHtmlTable -Rows (@(def_AsPlainArray $script:def_EngineCapabilityRows) | Select-Object -First 120) -Columns @("EngineID","Capability","Language","FunctionName","Risk","Priority")
    $projHtml = def_BuildHtmlTable -Rows @(def_AsPlainArray $script:def_ProjectRows) -Columns @("Project","Type","Exists","ScannedFiles","PowerShellFiles","PythonFiles","RunFolders","Reports","Status","Risk","Path")
    $convoHtml = def_BuildHtmlTable -Rows (@(def_AsPlainArray $script:def_ConversationRows) | Sort-Object Signal -Descending | Select-Object -First 80) -Columns @("Signal","Status","Risk","Priority","Fatal","Fail","Warn","High","Ready","Path")
    $seqHtml = def_BuildHtmlTable -Rows @(def_AsPlainArray $script:def_SequentialPlanRows) -Columns @("Kind","Priority","Risk","Scope","Name","Status","Action","Path","Message")
    $parHtml = def_BuildHtmlTable -Rows (@(def_AsPlainArray $script:def_ParallelPlanRows) | Select-Object -First 200) -Columns @("Priority","Scope","Name","Status","Action","Path","Message")
    $nextHtml = def_BuildHtmlTable -Rows @(def_AsPlainArray $script:def_NextActionRows) -Columns @("Step","Phase","Action","Command","Risk","Why")
    $css = @'
:root{--ink:#24332f;--muted:#6d7d77;--line:#d8dfda;--paper:#f7f8f4;--card:#ffffffcc;--accent:#8aa7a0;--red:#9b2f2f;--green:#2d6d57;--gold:#9f8453;}
*{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 10% 10%,#eaf1ee 0,transparent 30%),radial-gradient(circle at 90% 5%,#f0ede0 0,transparent 25%),var(--paper);font-family:"Noto Sans TC","Segoe UI",Arial,sans-serif;color:var(--ink)}
.wrap{max-width:1480px;margin:0 auto;padding:36px}.hero{padding:34px;border:1px solid var(--line);background:linear-gradient(135deg,#ffffffd9,#f9fbf8cc);border-radius:28px;box-shadow:0 18px 60px #52625d1c}.seal{display:inline-grid;place-items:center;width:52px;height:52px;border-radius:14px;background:#a83b36;color:white;font-size:30px;font-family:serif;margin-right:14px}.title{display:flex;align-items:center;gap:12px}.title h1{font-size:28px;margin:0;letter-spacing:.02em}.subtitle{margin-top:10px;color:var(--muted)}.kpis{display:grid;grid-template-columns:repeat(8,1fr);gap:12px;margin:22px 0}.kpi{padding:16px;border:1px solid var(--line);border-radius:18px;background:var(--card)}.kpi .n{font-size:24px;font-weight:800}.kpi .l{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.section{margin-top:24px;padding:22px;border:1px solid var(--line);border-radius:22px;background:var(--card)}h2{font-size:19px;margin:0 0 14px 0}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border-bottom:1px solid var(--line);padding:8px 9px;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#eef4f1;color:#33423e;z-index:1}td{max-width:420px;word-break:break-word}.pill{display:inline-block;padding:5px 10px;border-radius:999px;border:1px solid var(--line);background:#fff}.risk-high{color:var(--red);font-weight:800}.risk-low{color:var(--green);font-weight:800}.muted{color:var(--muted)}.cmd{font-family:"Cascadia Mono","Consolas",monospace;background:#eef3ef;border:1px solid var(--line);border-radius:14px;padding:12px;white-space:pre-wrap}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}@media(max-width:980px){.kpis{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}.wrap{padding:16px}}
'@
    $html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>VIA Ultimate Engine Forge</title><style>$css</style></head><body><div class="wrap">
<div class="hero"><div class="title"><div class="seal">理</div><div><h1>Veritas Intelligence Analytics · Ultimate Engine Forge</h1><div class="subtitle">JSON Contract · Multi-Language Function Engine · Freeze Gate · Three-Round Hydra-Safe Gate · $def_PARAM_VERSION</div></div></div>
<p class="subtitle">判天地之美，析萬物之理。此報告只做 append-only 沙盒檢視、測試、分流與收斂；不寫 DB、不 canonical merge、不刪除、不 stop-process。</p>
<div class="kpis"><div class="kpi"><div class="n">$status</div><div class="l">Status</div></div><div class="kpi"><div class="n">$risk</div><div class="l">Risk</div></div><div class="kpi"><div class="n">$ok</div><div class="l">OK</div></div><div class="kpi"><div class="n">$warn</div><div class="l">WARN</div></div><div class="kpi"><div class="n">$fail</div><div class="l">FAIL</div></div><div class="kpi"><div class="n">$high</div><div class="l">HIGH</div></div><div class="kpi"><div class="n">$seq</div><div class="l">Sequential</div></div><div class="kpi"><div class="n">$pct%</div><div class="l">Progress</div></div></div>
<div class="cmd">First command:

pwsh -NoProfile -ExecutionPolicy Bypass -File "$PSCommandPath"</div>
</div>
<div class="section"><h2>Next Action Convergence Plan</h2>$nextHtml</div>
<div class="section"><h2>Function Engine Registry · JSON Contract</h2>$engineHtml</div>
<div class="grid2"><div class="section"><h2>Engine Capability Matrix</h2>$capHtml</div><div class="section"><h2>Engine Freeze Gate</h2>$freezeHtml</div></div>
<div class="grid2"><div class="section"><h2>Command Advantage Lens</h2>$cmdHtml</div><div class="section"><h2>Project Folder Lens</h2>$projHtml</div></div>
<div class="section"><h2>Conversation / History Lens</h2>$convoHtml</div>
<div class="section"><h2>Sequential Repair Plan · Hydra Gate</h2>$seqHtml</div>
<div class="section"><h2>Parallel-Safe Optimization Plan</h2>$parHtml</div>
<div class="section"><h2>Full Matrix</h2>$matrixHtml</div>
<div class="section"><h2>Artifacts</h2><div class="cmd">Run Root: $def_RUN_ROOT
Matrix CSV: $def_MATRIX_CSV
Command CSV: $def_COMMAND_CSV
Project CSV: $def_PROJECT_CSV
Conversation CSV: $def_CONVO_CSV
Risk CSV: $def_RISK_CSV
Sequential Plan: $def_SEQ_PLAN_CSV
Parallel Plan: $def_PAR_PLAN_CSV
Next Action: $def_NEXT_ACTION_CSV
AI Prompt Pack: $def_AI_PROMPT_MD
Bridge: $def_BRIDGE_PSM1
Engine Config: $def_ENGINE_CONFIG_JSON
Engine Registry: $def_ENGINE_REGISTRY_JSON
Engine Freeze Registry: $def_ENGINE_FREEZE_JSON</div></div>
</div></body></html>
"@
    Set-Content -LiteralPath $def_REPORT_HTML -Value $html -Encoding UTF8
}

function def_Round3_ReportSeal {
    def_ExportAll
    def_WriteHtmlReport
    def_AddRow "Round3" "GLOBAL" "REPORT_SEAL" "HTML/CSV/JSON Seal" "OK_EXPORTED" "LOW" "PARALLEL_SAFE" "P0" "report" $def_REPORT_HTML "Final report and registries exported." $def_REPORT_HTML
    def_ExportAll
    def_WriteHtmlReport
    def_TaskDone "VIA Ultimate First Module" "Report seal complete"
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA Ultimate Engine Forge · JSON Contract · Freeze Gate AIO $def_PARAM_VERSION" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Root       : $Root"
    Write-Host "Downloads  : $Downloads"
    Write-Host "Supportive : $SupportiveDir"
    Write-Host "Functional : $FunctionalRoot"
    Write-Host "Tool Root  : $ToolRoot"
    Write-Host "Run ID     : $def_PARAM_RUN_ID"
    Write-Host "Policy     : no DB write · no canonical merge · no destructive delete · no stop-process · append-only · sandbox-first"
    Write-Host ""

    def_Initialize
    def_Round1_CommandAdvantageLens
    def_Round1_FolderPanoramaLens
    def_Round1_ConversationHistoryLens
    def_Round1_PolicyAndSupportiveCheck
    def_Round1_EngineExpansionLens
    def_Round2_JsonContractAndEngineForge
    def_Round2_EngineSmokeTest
    def_Round2_SandboxCopy
    def_Round2_PowerShellAstSandbox
    def_Round2_PythonCompileSandbox
    def_Round2_CandidateDryProbe
    def_Round2_HydraRiskGate
    def_Round3_MultiProjectConvergence
    def_Round3_AISandboxPromptPack
    def_Round3_BridgeAndFirstCommand
    def_Round3_EngineFreezeGate
    def_Round3_ReportSeal

    Write-Progress -Id 1 -Activity "VIA Ultimate First Module" -Completed
    $rows = @(def_AsPlainArray $script:def_Rows)
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $fail = def_CountSafe ($rows | Where-Object { $_.Status -like "FAIL*" })
    $high = def_CountSafe ($rows | Where-Object { $_.Risk -eq "HIGH" })
    $seq = def_CountSafe $script:def_SequentialPlanRows
    $pct = def_GetPercent -Done $script:def_CompletedTasks -Total $script:def_TotalTasks
    $finalStatus = "READY"
    if ($fail -gt 0 -or $high -gt 0 -or $seq -gt 0) { $finalStatus = "READY_WITH_REVIEW" }
    elseif ($warn -gt 0) { $finalStatus = "READY_WITH_WARNINGS" }

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA ULTIMATE ENGINE FORGE COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Status       : $finalStatus"
    Write-Host "OK/WARN/FAIL : $ok / $warn / $fail"
    Write-Host "HIGH/SEQ     : $high / $seq"
    Write-Host "Progress     : $script:def_CompletedTasks / $script:def_TotalTasks · $pct%"
    Write-Host "Run Root     : $def_RUN_ROOT"
    Write-Host "HTML         : $def_REPORT_HTML"
    Write-Host "Matrix CSV   : $def_MATRIX_CSV"
    Write-Host "Command CSV  : $def_COMMAND_CSV"
    Write-Host "Project CSV  : $def_PROJECT_CSV"
    Write-Host "Convo CSV    : $def_CONVO_CSV"
    Write-Host "Risk CSV     : $def_RISK_CSV"
    Write-Host "Seq Plan     : $def_SEQ_PLAN_CSV"
    Write-Host "Parallel Plan: $def_PAR_PLAN_CSV"
    Write-Host "Next Action  : $def_NEXT_ACTION_CSV"
    Write-Host "AI Prompt    : $def_AI_PROMPT_MD"
    Write-Host "Bridge       : $def_BRIDGE_PSM1"
    Write-Host "Engine Config: $def_ENGINE_CONFIG_JSON"
    Write-Host "Engine Reg   : $def_ENGINE_REGISTRY_JSON"
    Write-Host "Freeze Reg   : $def_ENGINE_FREEZE_JSON"
    Write-Host ""
    Write-Host "Best first command:" -ForegroundColor Green
    Write-Host "pwsh -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -ForegroundColor Green
    Write-Host ""
    if ($OpenReport -and (Test-Path -LiteralPath $def_REPORT_HTML)) { Start-Process $def_REPORT_HTML }
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host ("[FATAL] " + $_.Exception.Message) -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    try {
        def_AddRow "FATAL" "GLOBAL" "RUNTIME" "Unhandled Exception" "FAIL_FATAL" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "error" $_.Exception.Message "Unhandled exception; exporting partial report." ""
        def_ExportAll
        def_WriteHtmlReport
    } catch {}
} finally {
    if ($KeepPowerShellOpen) {
        Write-Host ""
        Write-Host "PowerShell session remains open." -ForegroundColor Cyan
    }
}

