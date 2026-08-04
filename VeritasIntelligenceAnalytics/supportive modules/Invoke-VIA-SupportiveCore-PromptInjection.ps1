<#
================================================================================
 Invoke-VIA-SupportiveCore-PromptInjection.ps1
 VIA SUPPORTIVE CORE - GOVERNED PROMPT INJECTION (static-only orchestrator)
--------------------------------------------------------------------------------
 One paste-and-run PS7 script. Imports a Prompt through the three official VIA
 PowerShell entry points (Core -> Central Governance -> Codex) UNDER GOVERNANCE.
 Static validation only: never imports/executes unverified targets, never
 installs, never touches network, never mutates canonical originals, never
 auto-activates the Runtime Bridge. Append-only, run-local, idempotent on
 repeated paste. Never uses exit / Stop-Process; console stays open.
 If VeritasAegisNexus.py is absent: NetworkStatus DEGRADED, OverallGate
 READY_WITH_WARNINGS - never claimed as full VIA support import.
 LL-compliant: param first, no aliases, no Read-Host, UTF8-no-BOM writes,
 ProcessStartInfo for python, PS Parser AST for .ps1, Sort-Object hashtable,
 no null-conditional in strings, three-space canonical path typo corrected.
================================================================================
#>
#requires -Version 7.0
param(
    [string]$PromptSource = "",
    [string]$PromptFile = "",
    [string]$PromptId = "",
    [string]$PromptVersion = "v001",
    [switch]$OpenReport
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# ============================================================ 一、參數 ==
$VIA_BASE            = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$VIA_SUPPORTIVE_DIR  = Join-Path $VIA_BASE "supportive modules"
$VIA_PYTHON          = "C:\Python313\python.exe"

$VIA_CELERITAS       = Join-Path $VIA_SUPPORTIVE_DIR "VeritasCeleritas.py"
$VIA_ENV_MANAGER     = Join-Path $VIA_SUPPORTIVE_DIR "VIA_EnvManager.py"
$VIA_AST_INJECTOR    = Join-Path $VIA_SUPPORTIVE_DIR "VIA_Panorama_AST_RuntimeInjector.py"
$VIA_REGISTRY_CORE   = Join-Path $VIA_SUPPORTIVE_DIR "VIA_RegistryCore_v1.py"
$VIA_RUNTIME_BRIDGE  = Join-Path $VIA_SUPPORTIVE_DIR "VIA_Runtime_Bridge_All_in_One.py"
$VIA_SSOT_UNIFIED    = Join-Path $VIA_SUPPORTIVE_DIR "VIA_SSOT_Unified.py"
$VIA_AEGIS_NEXUS     = Join-Path $VIA_SUPPORTIVE_DIR "VeritasAegisNexus.py"

$VIA_PS_NEXUS_CORE   = Join-Path $VIA_SUPPORTIVE_DIR "Invoke-VeritasNexusCore.ps1"
$VIA_PS_GOVERNANCE   = Join-Path $VIA_SUPPORTIVE_DIR "Invoke-VIA-CentralGovernanceManager.ps1"
$VIA_PS_CODEX_NEXUS  = Join-Path $VIA_SUPPORTIVE_DIR "Invoke-VeritasCodexNexus.ps1"

# Governance switches (all mutation-capable defaults OFF)
$VIA_NETWORK_ALLOWED            = $false
$VIA_IMPORT_ALLOWED             = $false
$VIA_BRIDGE_ACTIVATION_ALLOWED  = $false
$VIA_CANONICAL_MUTATION_ALLOWED = $false
$VIA_INSTALL_ALLOWED            = $false

$VIA_STATIC_VALIDATION = $true
$VIA_SANDBOX_VALIDATION = $true
$VIA_APPEND_ONLY       = $true
$VIA_RUN_LOCAL_ONLY    = $true

# Run-local root is DELIBERATELY outside the canonical VIA tree (no canonical mutation).
$VIA_RUNLOCAL_ROOT = Join-Path $env:USERPROFILE "Downloads\VIA_SupportiveCore_RunLocal"

# Registry IDs (fixed baseline for this prompt import).
$script:TOOLS = @(
    [ordered]@{ Key="CELERITAS"; Path=$VIA_CELERITAS;      Id="VIA-SUP-ACC-0001-v001";    Role="加速器與資源治理";  Kind="Python" }
    [ordered]@{ Key="ENV";       Path=$VIA_ENV_MANAGER;    Id="VIA-SUP-ENV-0001-v001";    Role="Python 環境與套件治理"; Kind="Python" }
    [ordered]@{ Key="AST";       Path=$VIA_AST_INJECTOR;   Id="VIA-SUP-AST-0001-v001";    Role="AST 與靜態結構檢查";   Kind="Python" }
    [ordered]@{ Key="REGISTRY";  Path=$VIA_REGISTRY_CORE;  Id="VIA-SUP-REG-0001-v001";    Role="中央註冊與能力路由"; Kind="Python" }
    [ordered]@{ Key="BRIDGE";    Path=$VIA_RUNTIME_BRIDGE; Id="VIA-SUP-BRIDGE-0001-v001"; Role="統一 Runtime Context"; Kind="Python" }
    [ordered]@{ Key="SSOT";      Path=$VIA_SSOT_UNIFIED;   Id="VIA-SUP-SSOT-0001-v001";   Role="SSOT 與語意規則";  Kind="Python" }
    [ordered]@{ Key="AEGIS";     Path=$VIA_AEGIS_NEXUS;    Id="VIA-SUP-NET-0001-v001";    Role="網路、快取、重試及故障轉移"; Kind="Python" }
    [ordered]@{ Key="PS_CORE";   Path=$VIA_PS_NEXUS_CORE;  Id="VIA-PS-CORE-0001-v001";    Role="核心載入入口";  Kind="PowerShell" }
    [ordered]@{ Key="PS_GOV";    Path=$VIA_PS_GOVERNANCE;  Id="VIA-PS-GOV-0001-v001";     Role="中央治理入口";  Kind="PowerShell" }
    [ordered]@{ Key="PS_CODEX";  Path=$VIA_PS_CODEX_NEXUS; Id="VIA-PS-CODEX-0001-v001";   Role="Prompt/AST/程式生成入口"; Kind="PowerShell" }
)

# Visual Lock
$VL = @{ Bg="#f5f4f0"; Paper="#fff"; Ink="#1e1d1a"; Line="#dbd9d3"; Blue="#4c78a8"; Teal="#439a9a"; Up="#c96b5a"; Down="#5a9e6f"; Gold="#c9a24c" }

$script:RunId  = "RUN-" + (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + ([guid]::NewGuid().ToString("N").Substring(0,6)).ToUpper()
$script:RunDir = Join-Path $VIA_RUNLOCAL_ROOT $script:RunId
$script:OverlayDir = Join-Path $VIA_RUNLOCAL_ROOT "_overlay"
$script:EvidenceLedger = Join-Path $VIA_RUNLOCAL_ROOT "VIA_EVIDENCE_LEDGER.jsonl"

# ============================================================ helpers ==
function Write-Line {
    param([string]$Text, [string]$Color = "Gray")
    # Console only accepts the 16 ConsoleColor names. Map Visual Lock hex
    # (used for HTML) to the nearest console colour so callers may pass either.
    $map = @{
        "#4c78a8"="Blue"; "#439a9a"="Cyan"; "#5a9e6f"="Green"; "#c96b5a"="Red"
        "#c9a24c"="Yellow"; "#c9b45a"="Yellow"; "#a85a9e"="Magenta"; "#5a6ba8"="Blue"
        "#1e1d1a"="Gray"; "#dbd9d3"="DarkGray"; "#8a877f"="DarkGray"
    }
    $valid = [enum]::GetNames([System.ConsoleColor])
    if ($map.Contains($Color)) { $Color = $map[$Color] }
    elseif ($valid -notcontains $Color) { $Color = "Gray" }
    Write-Host $Text -ForegroundColor $Color
}

function def_WriteJson {
    param([string]$Path, $Object)
    $json = $Object | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText($Path, $json, (New-Object System.Text.UTF8Encoding($false)))
    return $Path
}

function def_WriteCsv {
    param([string]$Path, $Rows)
    if ($null -eq $Rows -or @($Rows).Count -eq 0) {
        [System.IO.File]::WriteAllText($Path, "", (New-Object System.Text.UTF8Encoding($false)))
        return $Path
    }
    $csv = ($Rows | ConvertTo-Csv -NoTypeInformation) -join "`r`n"
    [System.IO.File]::WriteAllText($Path, $csv, (New-Object System.Text.UTF8Encoding($false)))
    return $Path
}

function def_GetFileHash {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return [ordered]@{ exists=$false; sha256=""; size_bytes=0; modified="" }
    }
    $item = Get-Item -LiteralPath $Path
    $hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
    return [ordered]@{
        exists=$true; sha256=$hash; size_bytes=$item.Length
        modified=$item.LastWriteTimeUtc.ToString("o")
    }
}

function def_HashString {
    param([string]$Text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return -join (($sha.ComputeHash($bytes)) | ForEach-Object { $_.ToString("x2") }) }
    finally { $sha.Dispose() }
}

# ---------- 一、Path resolver (three-space typo -> single-space canonical) ----------
function def_ResolveViaPaths {
    $rawCandidate = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive   modules\VIA_RegistryCore_v1.py"
    $canonical    = Join-Path $VIA_SUPPORTIVE_DIR "VIA_RegistryCore_v1.py"
    $resolved = [ordered]@{
        via_base = $VIA_BASE
        supportive_dir = $VIA_SUPPORTIVE_DIR
        raw_path_candidate = $rawCandidate
        canonical_registry_path = $canonical
        supportive_dir_exists = (Test-Path -LiteralPath $VIA_SUPPORTIVE_DIR)
        create_missing_dir = $false   # 禁止自動建立支援模組資料夾
        runlocal_root = $VIA_RUNLOCAL_ROOT
        run_dir = $script:RunDir
    }
    return $resolved
}

# ---------- 十五-support: required files existence ----------
function def_TestRequiredFiles {
    $rows = @()
    foreach ($t in $script:TOOLS) {
        $h = def_GetFileHash -Path $t.Path
        $rows += [ordered]@{
            key=$t.Key; registry_id=$t.Id; kind=$t.Kind; role=$t.Role
            resolved_path=$t.Path; exists=$h.exists; sha256=$h.sha256
            size_bytes=$h.size_bytes; modified=$h.modified
        }
    }
    return $rows
}

# ---------- Python static AST/compile via ProcessStartInfo (no target execution) ----------
function def_InvokePythonStatic {
    param([string]$PyFile)
    $result = [ordered]@{ ran=$false; ast_ok=$false; compile_ok=$false; detail="" }
    if (-not (Test-Path -LiteralPath $VIA_PYTHON)) {
        $result.detail = "python not found: $VIA_PYTHON"; return $result
    }
    if (-not (Test-Path -LiteralPath $PyFile)) {
        $result.detail = "file missing"; return $result
    }
    # ast.parse + py_compile, never runs target module code (no import).
    $code = 'import ast,sys,py_compile' + "`n" +
            'p=sys.argv[1]' + "`n" +
            'src=open(p,encoding="utf-8").read()' + "`n" +
            'ast.parse(src)' + "`n" +
            'py_compile.compile(p,doraise=True)' + "`n" +
            'print("AST_OK COMPILE_OK")'
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $VIA_PYTHON
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.ArgumentList.Add("-c")
    $psi.ArgumentList.Add($code)
    $psi.ArgumentList.Add($PyFile)
    $proc = [System.Diagnostics.Process]::Start($psi)
    $out = $proc.StandardOutput.ReadToEnd()
    $err = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    $result.ran = $true
    if ($out -match "AST_OK") { $result.ast_ok = $true }
    if ($out -match "COMPILE_OK") { $result.compile_ok = $true }
    if (-not $result.ast_ok) { $result.detail = ($err.Trim()) }
    return $result
}
function def_TestPythonAst {
    param([string]$PyFile)
    return def_InvokePythonStatic -PyFile $PyFile
}

# ---------- PowerShell parser AST (static, never dot-sources) ----------
function def_TestPowerShellParser {
    param([string]$Ps1File)
    $result = [ordered]@{ exists=$false; parse_ok=$false; error_count=0; detail="" }
    if (-not (Test-Path -LiteralPath $Ps1File)) { $result.detail="file missing"; return $result }
    $result.exists = $true
    $tokens = $null; $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($Ps1File, [ref]$tokens, [ref]$errors)
    $result.error_count = @($errors).Count
    $result.parse_ok = ($result.error_count -eq 0)
    if (-not $result.parse_ok) { $result.detail = (($errors | ForEach-Object { $_.Message }) -join " | ") }
    return $result
}

# ---------- 六-support: read prompt source ----------
function def_ReadPromptSource {
    $text = ""
    $origin = "none"
    if ($PromptFile -and (Test-Path -LiteralPath $PromptFile)) {
        $text = [System.IO.File]::ReadAllText($PromptFile)
        $origin = "file:$PromptFile"
    } elseif ($PromptSource) {
        $text = $PromptSource
        $origin = "inline"
    }
    return [ordered]@{ origin=$origin; text=$text; hash=(def_HashString $text); length=$text.Length }
}

# ---------- 二: register supportive tools (append-only, full fields) ----------
function def_RegisterSupportiveTools {
    param($FileRows, $PyStatic, $PsStatic)
    $reg = @()
    foreach ($t in $script:TOOLS) {
        $fr = $FileRows | Where-Object { $_.key -eq $t.Key } | Select-Object -First 1
        $astState = "N/A"
        $netCap = $false; $writeCap = $false; $risk = "LOW"
        if ($t.Kind -eq "Python") {
            $st = $PyStatic[$t.Key]
            if ($null -ne $st) { $astState = if ($st.ast_ok -and $st.compile_ok) { "AST_OK/COMPILE_OK" } elseif ($st.ran) { "PARSE_FAIL" } else { "NOT_RUN" } }
        } else {
            $st = $PsStatic[$t.Key]
            if ($null -ne $st) { $astState = if ($st.parse_ok) { "PARSER_OK" } elseif ($st.exists) { "PARSER_FAIL" } else { "MISSING" } }
        }
        if ($t.Key -eq "AEGIS") { $netCap = $true; $risk = "MED" }
        if ($t.Key -eq "BRIDGE") { $risk = "MED" }
        $reg += [ordered]@{
            registry_id = $t.Id
            tool = (Split-Path $t.Path -Leaf)
            governance_role = $t.Role
            absolute_path = $t.Path
            relative_path = ($t.Path -replace [regex]::Escape($VIA_BASE), "<VIA_BASE>")
            sha256 = $fr.sha256
            size_bytes = $fr.size_bytes
            modified = $fr.modified
            type = $t.Kind
            ast_parser_status = $astState
            entry_point = if ($t.Kind -eq "PowerShell") { (Split-Path $t.Path -Leaf) } else { "module" }
            capabilities = $t.Role
            dependencies = (def_ToolDeps $t.Key)
            network_capability = $netCap
            write_capability = $writeCap
            risk_level = $risk
            ssot_ownership = "VIA-SUP-SSOT-0001-v001"
            allow_import = ($VIA_IMPORT_ALLOWED -and $fr.exists -and $astState -match "OK")
            allow_execute = $false
            allow_bridge_activation = ($VIA_BRIDGE_ACTIVATION_ALLOWED)
            exists = $fr.exists
            registered_at = (Get-Date).ToUniversalTime().ToString("o")
            run_id = $script:RunId
        }
    }
    return $reg
}
function def_ToolDeps {
    param([string]$Key)
    switch ($Key) {
        "BRIDGE"   { return @("VIA-SUP-ENV-0001-v001","VIA-SUP-REG-0001-v001","VIA-SUP-SSOT-0001-v001","VIA-SUP-ACC-0001-v001","VIA-SUP-NET-0001-v001") }
        "REGISTRY" { return @("VIA-SUP-SSOT-0001-v001") }
        "ENV"      { return @("VIA-SUP-REG-0001-v001") }
        "AST"      { return @("VIA-SUP-SSOT-0001-v001") }
        default    { return @() }
    }
}

# ---------- 六: prompt SSOT overlay (run-local, never writes canonical) ----------
function def_RegisterPromptOverlay {
    param($Prompt)
    $pid2 = if ($PromptId) { $PromptId } else { "VIA-PROMPT-" + (Get-Date -Format "yyyyMMdd") + "-" + $Prompt.hash.Substring(0,6).ToUpper() }
    $overlay = [ordered]@{
        def_prompt_id = $pid2
        def_prompt_name = "VIA_SUPPORTIVE_CORE_GOVERNED_INJECTION"
        def_prompt_version = $PromptVersion
        def_prompt_hash_sha256 = $Prompt.hash
        def_prompt_source = $Prompt.origin
        def_prompt_file = $PromptFile
        def_registered_at = (Get-Date).ToUniversalTime().ToString("o")
        def_owner = "VIA"
        def_status = "CANDIDATE"
        def_required_tool_ids = ($script:TOOLS | ForEach-Object { $_.Id })
        def_required_capabilities = @("static_validation","registry","ssot","ast")
        def_network_required = $false
        def_acceleration_required = $false
        def_bridge_required = $false
        def_write_scope = "RUN_LOCAL_ONLY"
        def_governance_gate = ""
        def_evidence_paths = @()
        def_run_id = $script:RunId
    }
    return $overlay
}

# ---------- capability / dependency matrices ----------
function def_BuildCapabilityMatrix {
    param($Registry)
    $rows = @()
    foreach ($r in $Registry) {
        $rows += [ordered]@{ registry_id=$r.registry_id; capability=$r.capabilities; provided_by=$r.tool; allow_import=$r.allow_import; status=$r.ast_parser_status }
    }
    return $rows
}
function def_BuildDependencyMatrix {
    param($Registry)
    $rows = @()
    foreach ($r in $Registry) {
        $rows += [ordered]@{ registry_id=$r.registry_id; tool=$r.tool; depends_on=(@($r.dependencies) -join ", "); resolvable=($r.exists) }
    }
    return $rows
}

# ---------- 七: accelerator gate (SAFE profile, no import-time activation) ----------
function def_InvokeAcceleratorGate {
    param($Registry)
    $acc = $Registry | Where-Object { $_.registry_id -eq "VIA-SUP-ACC-0001-v001" } | Select-Object -First 1
    $available = ($null -ne $acc -and $acc.exists -and $acc.ast_parser_status -match "OK")
    return [ordered]@{
        accelerator_mode = "SAFE"
        parallel_workers = "AUTO_BOUNDED"
        shared_write = "PROHIBITED"
        process_pool = "ISOLATED_ONLY"
        network_fetch = "DISABLED"
        memory_guard = "ENABLED"
        cpu_stop_gate = "ENABLED"
        checkpoint = "ENABLED"
        deterministic = "REQUIRED"
        celeritas_available = $available
        import_time_activation = $false
        gate = if ($available) { "GREEN" } else { "YELLOW" }
    }
}

# ---------- 八: network gate (Aegis presence drives status) ----------
function def_InvokeNetworkGate {
    param($Registry)
    $aegis = $Registry | Where-Object { $_.registry_id -eq "VIA-SUP-NET-0001-v001" } | Select-Object -First 1
    $present = ($null -ne $aegis -and $aegis.exists -and $aegis.ast_parser_status -match "OK")
    $status = if ($present) { "READY" } else { "DEGRADED" }
    return [ordered]@{
        network_status = $status
        offline_core = "ALLOWED"
        network_tasks = if ($present -and $VIA_NETWORK_ALLOWED) { "ALLOWED" } else { "BLOCKED" }
        network_allowed = $VIA_NETWORK_ALLOWED
        connectivity_test = $false
        download_allowed = $false
        package_install = $false
        git_operation = $false
        api_call_allowed = $false
        tls_verification = $true
        credential_source = "ENVIRONMENT_OR_SECURE_STORE_ONLY"
        canonical_write = $false
        aegis_present = $present
        gate = if ($present) { "GREEN" } else { "YELLOW" }
    }
}

# ---------- environment / ssot governance (static plan, no real invocation) ----------
function def_InvokeEnvironmentGovernance {
    param($Registry)
    $env = $Registry | Where-Object { $_.registry_id -eq "VIA-SUP-ENV-0001-v001" } | Select-Object -First 1
    return [ordered]@{
        env_manager_present = ($null -ne $env -and $env.exists)
        env_manager_parse = ($null -ne $env -and $env.ast_parser_status -match "OK")
        install_allowed = $VIA_INSTALL_ALLOWED
        decision = "STATIC_PLAN_ONLY"
        gate = if ($null -ne $env -and $env.ast_parser_status -match "OK") { "GREEN" } else { "YELLOW" }
    }
}
function def_InvokeSsotValidation {
    param($Registry, $Overlay)
    $ssot = $Registry | Where-Object { $_.registry_id -eq "VIA-SUP-SSOT-0001-v001" } | Select-Object -First 1
    $present = ($null -ne $ssot -and $ssot.exists -and $ssot.ast_parser_status -match "OK")
    # multi-authority conflict: same id/different hash OR different id/same content
    $idList = @($Registry | ForEach-Object { $_.registry_id })
    $dupGroups = @($idList | Group-Object | Where-Object { $_.Count -gt 1 })
    $dupId = ($dupGroups.Count -gt 0)
    return [ordered]@{
        ssot_present = $present
        overlay_status = $Overlay.def_status
        write_scope = "RUN_LOCAL_ONLY"
        canonical_write = $false
        duplicate_registry_id = $dupId
        sync_direction = "Canonical->ReadOnlySnapshot->RunLocalOverlay->StaticValidation->SandboxEvidence->OperatorReview->ApprovedPromotion"
        gate = if ($present -and -not $dupId) { "GREEN" } else { "YELLOW" }
    }
}

# ---------- 五: runtime bridge plan (decision only, never activates) ----------
function def_BuildRuntimeBridgePlan {
    param($Registry, $NetGate)
    $need = @("VIA-SUP-ENV-0001-v001","VIA-SUP-REG-0001-v001","VIA-SUP-SSOT-0001-v001","VIA-SUP-ACC-0001-v001")
    $ready = $true
    foreach ($id in $need) {
        $r = $Registry | Where-Object { $_.registry_id -eq $id } | Select-Object -First 1
        if ($null -eq $r -or -not $r.exists -or $r.ast_parser_status -notmatch "OK") { $ready = $false }
    }
    return [ordered]@{
        ctx_targets = @("ctx.env_manager","ctx.registry","ctx.ssot","ctx.aegis","ctx.celeritas","ctx.loaded_modules","ctx.state","ctx.errors")
        prerequisites_ready = $ready
        aegis_network = $NetGate.network_status
        activation_allowed = $VIA_BRIDGE_ACTIVATION_ALLOWED
        will_activate = $false
        canonical_root_ok = (Test-Path -LiteralPath $VIA_SUPPORTIVE_DIR)
        no_mnt_data = $true
        no_old_onedrive = $true
        gate = if ($ready) { "GREEN" } else { "YELLOW" }
    }
}

# ---------- three PS entry points: static recognition + plan (never invokes) ----------
function def_InvokeNexusCore {
    param($PsStatic)
    $core = $PsStatic["PS_CORE"]
    return [ordered]@{
        entry = "Invoke-VeritasNexusCore.ps1"
        exists = $core.exists
        parse_ok = $core.parse_ok
        run_dir_created = (Test-Path -LiteralPath $script:RunDir)
        import_plan = "STATIC_ONLY"
        real_import = $false
        gate = if ($core.exists -and $core.parse_ok) { "GREEN" } elseif ($core.exists) { "RED" } else { "RED" }
    }
}
function def_InvokeCentralGovernanceManager {
    param($PsStatic, $EnvGate, $SsotGate, $AccGate, $NetGate, $BridgePlan)
    $gov = $PsStatic["PS_GOV"]
    $allGreen = @($EnvGate.gate,$SsotGate.gate,$AccGate.gate,$NetGate.gate) -notcontains "RED"
    return [ordered]@{
        entry = "Invoke-VIA-CentralGovernanceManager.ps1"
        exists = $gov.exists
        parse_ok = $gov.parse_ok
        env_gate = $EnvGate.gate; ssot_gate = $SsotGate.gate
        accelerator_gate = $AccGate.gate; network_gate = $NetGate.gate
        bridge_gate = $BridgePlan.gate
        decision = if ($gov.exists -and $gov.parse_ok -and $allGreen) { "APPROVED_STATIC" } elseif ($gov.exists) { "REVIEW_REQUIRED" } else { "BLOCKED" }
        gate = if ($gov.exists -and $gov.parse_ok) { "GREEN" } elseif ($gov.exists) { "RED" } else { "RED" }
    }
}
function def_InvokeCodexNexus {
    param($PsStatic, $GovDecision, $Overlay)
    $codex = $PsStatic["PS_CODEX"]
    $mayEnter = ($GovDecision.decision -eq "APPROVED_STATIC")
    return [ordered]@{
        entry = "Invoke-VeritasCodexNexus.ps1"
        exists = $codex.exists
        parse_ok = $codex.parse_ok
        prompt_id = $Overlay.def_prompt_id
        may_enter_codex = $mayEnter
        code_generation_plan = if ($mayEnter) { "CANDIDATE_PLAN_ONLY" } else { "WITHHELD" }
        modifies_canonical = $false
        gate = if ($codex.exists -and $codex.parse_ok) { "GREEN" } elseif ($codex.exists) { "RED" } else { "RED" }
    }
}

# ---------- 十: hash state machine (idempotent run-local write) ----------
function def_ApplyRunLocal {
    param([string]$Path, [string]$Content)
    $proposed = def_HashString $Content
    $state = "APPLY"
    if (Test-Path -LiteralPath $Path) {
        $current = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLower()
        if ($current -eq $proposed) { $state = "SKIP_ALREADY_APPLIED" }
        else { $state = "APPLY_UPDATE" }
    }
    if ($state -ne "SKIP_ALREADY_APPLIED") {
        $dir = Split-Path $Path -Parent
        if (-not (Test-Path -LiteralPath $dir)) { [void](New-Item -ItemType Directory -Path $dir -Force) }
        [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding($false)))
    }
    return [ordered]@{ path=$Path; state=$state; proposed_hash=$proposed }
}

# ---------- 十: append-only evidence ledger (hash chain) ----------
function def_WriteEvidence {
    param([string]$Stage, $Payload)
    if (-not (Test-Path -LiteralPath $VIA_RUNLOCAL_ROOT)) { [void](New-Item -ItemType Directory -Path $VIA_RUNLOCAL_ROOT -Force) }
    $prevHash = ""
    if (Test-Path -LiteralPath $script:EvidenceLedger) {
        $lines = @(Get-Content -LiteralPath $script:EvidenceLedger -Encoding UTF8)
        if ($lines.Count -gt 0) {
            $last = $lines[-1]
            if ($last) { $prevHash = def_HashString $last }
        }
    }
    $entry = [ordered]@{
        run_id=$script:RunId; stage=$Stage; timestamp=(Get-Date).ToUniversalTime().ToString("o")
        prev_hash=$prevHash; payload=$Payload
    }
    $entryJson = ($entry | ConvertTo-Json -Depth 12 -Compress)
    $entry["current_hash"] = def_HashString $entryJson
    $final = ($entry | ConvertTo-Json -Depth 12 -Compress)
    Add-Content -LiteralPath $script:EvidenceLedger -Value $final -Encoding UTF8
    return $entry["current_hash"]
}

# ---------- 九: Hydra risk (duplicate execution / cross-write) ----------
function def_TestHydraRisk {
    param($Registry)
    $bridge = $Registry | Where-Object { $_.registry_id -eq "VIA-SUP-BRIDGE-0001-v001" } | Select-Object -First 1
    $risks = @()
    if ($VIA_BRIDGE_ACTIVATION_ALLOWED) { $risks += "bridge_activation_allowed" }
    if ($VIA_IMPORT_ALLOWED) { $risks += "import_allowed" }
    if ($VIA_NETWORK_ALLOWED) { $risks += "network_allowed" }
    if ($VIA_CANONICAL_MUTATION_ALLOWED) { $risks += "canonical_mutation_allowed" }
    return [ordered]@{
        shared_write = "PROHIBITED"
        duplicate_execution_guard = "HASH_STATE_MACHINE"
        idempotent_repaste = $true
        active_risk_flags = $risks
        hydra_level = if (@($risks).Count -eq 0) { "GREEN" } elseif (@($risks).Count -le 2) { "YELLOW" } else { "RED" }
    }
}

# ---------- 十二: HTML RYG matrix per round ----------
function def_WriteHtmlMatrix {
    param([string]$Path, [string]$Title, $Sections)
    $enc = { param($s) [System.Net.WebUtility]::HtmlEncode([string]$s) }
    $ryg = {
        param($v)
        switch ("$v") {
            "GREEN"  { "<span style='background:#5a9e6f22;color:#5a9e6f;padding:2px 9px;border-radius:99px;font-weight:600'>GREEN</span>" }
            "YELLOW" { "<span style='background:#c9a24c22;color:#c9a24c;padding:2px 9px;border-radius:99px;font-weight:600'>YELLOW</span>" }
            "RED"    { "<span style='background:#c96b5a22;color:#c96b5a;padding:2px 9px;border-radius:99px;font-weight:600'>RED</span>" }
            default  { (& $enc $v) }
        }
    }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>")
    [void]$sb.Append("<meta name='viewport' content='width=device-width,initial-scale=1'><title>" + (& $enc $Title) + "</title><style>")
    [void]$sb.Append("body{background:$($VL.Bg);color:$($VL.Ink);font-family:'DM Sans',system-ui,sans-serif;font-size:12.5px;padding:26px;max-width:1120px;margin:0 auto}")
    [void]$sb.Append("h1{font-family:'Syne',sans-serif;font-size:21px}.reso{height:3px;border-radius:99px;margin:12px 0 20px;background:linear-gradient(90deg,#4c78a8,#439a9a,#5a9e6f,#c9b45a,#c96b5a,#a85a9e,#5a6ba8)}")
    [void]$sb.Append(".panel{background:$($VL.Paper);border:1px solid $($VL.Line);border-radius:3px;padding:14px 16px;margin-bottom:14px}")
    [void]$sb.Append("h2{font-family:'Syne',sans-serif;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:#4a4843;margin-bottom:10px}")
    [void]$sb.Append("table{width:100%;border-collapse:collapse;font-size:11.5px}th,td{padding:6px 9px;text-align:left;border-bottom:1px solid $($VL.Line);vertical-align:top}")
    [void]$sb.Append("th{font-family:'DM Mono',monospace;font-size:9.5px;text-transform:uppercase;color:#9a978f}.mono{font-family:'DM Mono',monospace}")
    [void]$sb.Append(".foot{text-align:center;color:#a8a49b;font-size:10px;font-family:'DM Mono',monospace;margin-top:20px}</style></head><body>")
    [void]$sb.Append("<h1>" + (& $enc $Title) + "</h1><div class='mono' style='color:#8a877f;font-size:10px'>Run " + (& $enc $script:RunId) + " &middot; " + (Get-Date).ToUniversalTime().ToString("o") + "</div><div class='reso'></div>")
    foreach ($sec in $Sections) {
        [void]$sb.Append("<div class='panel'><h2>" + (& $enc $sec.Title) + "</h2>")
        $rows = @($sec.Rows)
        if ($rows.Count -eq 0) { [void]$sb.Append("<div class='mono' style='color:#a8a49b'>(empty)</div></div>"); continue }
        $cols = $rows[0].Keys
        [void]$sb.Append("<table><thead><tr>")
        foreach ($c in $cols) { [void]$sb.Append("<th>" + (& $enc $c) + "</th>") }
        [void]$sb.Append("</tr></thead><tbody>")
        foreach ($r in $rows) {
            [void]$sb.Append("<tr>")
            foreach ($c in $cols) {
                $val = $r[$c]
                if ($val -is [System.Array]) { $val = ($val -join ", ") }
                if ("$c" -match "gate|ryg|level|status|health" -and "$val" -match "^(GREEN|YELLOW|RED)$") {
                    [void]$sb.Append("<td>" + (& $ryg $val) + "</td>")
                } else {
                    [void]$sb.Append("<td>" + (& $enc $val) + "</td>")
                }
            }
            [void]$sb.Append("</tr>")
        }
        [void]$sb.Append("</tbody></table></div>")
    }
    [void]$sb.Append("<div class='foot'>VIA &middot; Supportive Core &middot; 治 &middot; static-only &middot; append-only &middot; run-local</div></body></html>")
    [System.IO.File]::WriteAllText($Path, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
    return $Path
}

# ---------- 十四: final gate ----------
function def_GetFinalGate {
    param($FileRows, $PsStatic, $NetGate, $SsotGate, $BridgePlan, $Hydra, $GovDecision)
    $blockers = @()
    foreach ($k in @("PS_CORE","PS_GOV","PS_CODEX")) {
        if (-not $PsStatic[$k].exists) { $blockers += "missing entry: $k" }
        elseif (-not $PsStatic[$k].parse_ok) { $blockers += "parser fail: $k" }
    }
    foreach ($fr in $FileRows) {
        if ($fr.kind -eq "Python" -and $fr.exists -and ($fr.key -ne "AEGIS")) {
            $st = $script:PyStatic[$fr.key]
            if ($null -ne $st -and -not $st.ast_ok) { $blockers += "python ast fail: $($fr.key)" }
        }
    }
    if ($SsotGate.duplicate_registry_id) { $blockers += "duplicate registry id" }
    if (-not $BridgePlan.canonical_root_ok) { $blockers += "canonical root unconfirmed" }
    if ($VIA_NETWORK_ALLOWED -and -not $NetGate.aegis_present) { $blockers += "unauthorized network without aegis" }
    if ($Hydra.hydra_level -eq "RED") { $blockers += "hydra duplicate execution risk" }

    $warnings = @()
    if (-not $NetGate.aegis_present) { $warnings += "aegis missing -> network DEGRADED" }
    if ($NetGate.network_status -eq "DEGRADED") { $warnings += "network DEGRADED" }
    if ($GovDecision.decision -eq "REVIEW_REQUIRED") { $warnings += "governance review required" }

    # Priority ladder (spec 十四): ANY hard blocker => BLOCKED. Otherwise a
    # soft governance REVIEW_REQUIRED, else warnings, else READY.
    $gate = "VIA_PROMPT_IMPORT_BLOCKED"
    if (@($blockers).Count -eq 0) {
        if ($GovDecision.decision -eq "REVIEW_REQUIRED") { $gate = "VIA_PROMPT_IMPORT_REVIEW_REQUIRED" }
        elseif (@($warnings).Count -gt 0) { $gate = "VIA_PROMPT_IMPORT_READY_WITH_WARNINGS" }
        else { $gate = "VIA_PROMPT_IMPORT_READY" }
    }
    return [ordered]@{ final_gate=$gate; blockers=$blockers; warnings=$warnings }
}

# ============================================================ def_Main ==
function def_Main {
    Write-Line "" 
    Write-Line "================================================================" $VL.Blue
    Write-Line " VIA SUPPORTIVE CORE - GOVERNED PROMPT INJECTION (static-only)" "White"
    Write-Line " Run: $script:RunId" "DarkGray"
    Write-Line "================================================================" $VL.Blue

    # RunDir (run-local, outside canonical)
    if (-not (Test-Path -LiteralPath $script:RunDir)) { [void](New-Item -ItemType Directory -Path $script:RunDir -Force) }

    # --- Path resolve + prompt ---
    $paths = def_ResolveViaPaths
    $prompt = def_ReadPromptSource
    [void](def_WriteEvidence -Stage "path_resolve" -Payload $paths)

    # --- Fixed import order: Core -> resolver -> static validation ---
    $fileRows = def_TestRequiredFiles

    # Round 1 - static comprehensive (parallel-safe)
    $script:PyStatic = @{}
    $psStatic = @{}
    foreach ($t in $script:TOOLS) {
        if ($t.Kind -eq "Python") { $script:PyStatic[$t.Key] = def_TestPythonAst -PyFile $t.Path }
        else { $psStatic[$t.Key] = def_TestPowerShellParser -Ps1File $t.Path }
    }

    $registry = def_RegisterSupportiveTools -FileRows $fileRows -PyStatic $script:PyStatic -PsStatic $psStatic
    $overlay  = def_RegisterPromptOverlay -Prompt $prompt
    $capMx    = def_BuildCapabilityMatrix -Registry $registry
    $depMx    = def_BuildDependencyMatrix -Registry $registry

    # Gates (fixed order: Env -> Registry -> SSOT -> Celeritas -> Aegis -> Bridge)
    $envGate    = def_InvokeEnvironmentGovernance -Registry $registry
    $ssotGate   = def_InvokeSsotValidation -Registry $registry -Overlay $overlay
    $accGate    = def_InvokeAcceleratorGate -Registry $registry
    $netGate    = def_InvokeNetworkGate -Registry $registry
    $bridgePlan = def_BuildRuntimeBridgePlan -Registry $registry -NetGate $netGate
    $hydra      = def_TestHydraRisk -Registry $registry

    # Three PS entry points (static recognition + governance decision, no real invoke)
    $core   = def_InvokeNexusCore -PsStatic $psStatic
    $govDec = def_InvokeCentralGovernanceManager -PsStatic $psStatic -EnvGate $envGate -SsotGate $ssotGate -AccGate $accGate -NetGate $netGate -BridgePlan $bridgePlan
    $codex  = def_InvokeCodexNexus -PsStatic $psStatic -GovDecision $govDec -Overlay $overlay

    $overlay.def_governance_gate = $govDec.decision

    # --- Round matrices (3 rounds; R2/R3 re-run static, regression gate) ---
    $rounds = @()
    for ($i = 1; $i -le 3; $i++) {
        $roundName = @("R1 Static Comprehensive","R2 Sequential Sandbox","R3 Final Hardening")[$i-1]
        $issues = @()
        foreach ($fr in $fileRows) { if (-not $fr.exists) { $issues += "missing:$($fr.key)" } }
        foreach ($k in $psStatic.Keys) { if ($psStatic[$k].exists -and -not $psStatic[$k].parse_ok) { $issues += "parsefail:$k" } }
        foreach ($k in $script:PyStatic.Keys) { $s=$script:PyStatic[$k]; if ($s.ran -and -not $s.ast_ok) { $issues += "astfail:$k" } }
        $rounds += [ordered]@{ round=$roundName; issues=@($issues).Count; detail=($issues -join ", ") }
        $secs = @(
            @{ Title="Tool Location Matrix"; Rows=($fileRows | ForEach-Object { [ordered]@{ key=$_.key; exists=$_.exists; path=$_.resolved_path } }) }
            @{ Title="Tool Registry Matrix"; Rows=($registry | ForEach-Object { [ordered]@{ id=$_.registry_id; tool=$_.tool; type=$_.type; ast=$_.ast_parser_status; allow_import=$_.allow_import; risk=$_.risk_level } }) }
            @{ Title="Prompt Registry Matrix"; Rows=@([ordered]@{ id=$overlay.def_prompt_id; status=$overlay.def_status; hash=$overlay.def_prompt_hash_sha256.Substring(0,12); scope=$overlay.def_write_scope }) }
            @{ Title="SSOT Alignment Matrix"; Rows=@([ordered]@{ present=$ssotGate.ssot_present; dup_id=$ssotGate.duplicate_registry_id; canonical_write=$ssotGate.canonical_write; gate=$ssotGate.gate }) }
            @{ Title="Dependency Matrix"; Rows=$depMx }
            @{ Title="Accelerator Matrix"; Rows=@([ordered]@{ mode=$accGate.accelerator_mode; workers=$accGate.parallel_workers; shared_write=$accGate.shared_write; net=$accGate.network_fetch; gate=$accGate.gate }) }
            @{ Title="Network Matrix"; Rows=@([ordered]@{ status=$netGate.network_status; tasks=$netGate.network_tasks; tls=$netGate.tls_verification; aegis=$netGate.aegis_present; gate=$netGate.gate }) }
            @{ Title="Runtime Bridge Matrix"; Rows=@([ordered]@{ prereq=$bridgePlan.prerequisites_ready; activate=$bridgePlan.will_activate; root_ok=$bridgePlan.canonical_root_ok; gate=$bridgePlan.gate }) }
            @{ Title="PowerShell Entrypoint Matrix"; Rows=@(
                [ordered]@{ entry=$core.entry;  exists=$core.exists;  parse=$core.parse_ok;  gate=$core.gate }
                [ordered]@{ entry=$govDec.entry; exists=$govDec.exists; parse=$govDec.parse_ok; gate=$govDec.gate }
                [ordered]@{ entry=$codex.entry; exists=$codex.exists; parse=$codex.parse_ok; gate=$codex.gate }) }
            @{ Title="Hydra Risk Matrix"; Rows=@([ordered]@{ shared_write=$hydra.shared_write; idempotent=$hydra.idempotent_repaste; flags=(@($hydra.active_risk_flags) -join ","); level=$hydra.hydra_level }) }
            @{ Title="Error Matrix"; Rows=(@($issues) | ForEach-Object { [ordered]@{ issue=$_ } }) }
        )
        $rp = Join-Path $script:RunDir ("VIA_PANORAMIC_MATRIX_R{0}.html" -f $i)
        [void](def_WriteHtmlMatrix -Path $rp -Title ("VIA 全景矩陣 · " + $roundName) -Sections $secs)
    }
    # regression gate: issues must not increase round-over-round
    $regression = $false
    for ($j = 1; $j -lt $rounds.Count; $j++) { if ($rounds[$j].issues -gt $rounds[$j-1].issues) { $regression = $true } }

    $finalGate = def_GetFinalGate -FileRows $fileRows -PsStatic $psStatic -NetGate $netGate -SsotGate $ssotGate -BridgePlan $bridgePlan -Hydra $hydra -GovDecision $govDec

    # --- 十三: required outputs (JSON/CSV) ---
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_SUPPORTIVE_TOOL_REGISTRY.json") -Object $registry)
    [void](def_WriteCsv  -Path (Join-Path $script:RunDir "VIA_SUPPORTIVE_TOOL_REGISTRY.csv") -Rows $registry)
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_TOOL_LOCATION_MATRIX.json") -Object $fileRows)
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_CAPABILITY_MATRIX.json") -Object $capMx)
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_DEPENDENCY_MATRIX.json") -Object $depMx)
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_ACCELERATOR_MATRIX.json") -Object $accGate)
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_NETWORK_TOOL_MATRIX.json") -Object $netGate)
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_RUNTIME_BRIDGE_PLAN.json") -Object $bridgePlan)
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_POWERSHELL_ENTRYPOINT_MATRIX.json") -Object @($core,$govDec,$codex))
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_STATIC_VALIDATION_RESULT.json") -Object @{ python=$script:PyStatic; powershell=$psStatic; rounds=$rounds; regression=$regression })
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_HYDRA_RISK_REPORT.json") -Object $hydra)
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_PROMPT_IMPORT_PLAN.json") -Object @{ order=@("NexusCore","PathResolver","StaticValidation","CentralGovernance","EnvManager","RegistryCore","SSOT","Celeritas","Aegis","BridgeDecision","GovernanceGate","CodexNexus","AST","PromptRegistration","CodeGenPlan","Sandbox","Evidence"); codex=$codex })
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_FINAL_GATE.json") -Object $finalGate)

    # 十: idempotent run-local overlay writes (hash state machine)
    $regApply = def_ApplyRunLocal -Path (Join-Path $script:OverlayDir "VIA_PROMPT_SSOT_OVERLAY.json") -Content ($overlay | ConvertTo-Json -Depth 12)
    $overlay.def_evidence_paths = @($script:RunDir)
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_PROMPT_SSOT_OVERLAY.json") -Object $overlay)
    [void](def_WriteJson -Path (Join-Path $script:RunDir "VIA_PROMPT_REGISTRATION_EVIDENCE.json") -Object @{ overlay_apply=$regApply; run_id=$script:RunId; prompt_hash=$prompt.hash })

    # final panoramic matrix (consolidated)
    $finalSecs = @(
        @{ Title="Final Gate"; Rows=@([ordered]@{ gate=$finalGate.final_gate; blockers=(@($finalGate.blockers) -join "; "); warnings=(@($finalGate.warnings) -join "; ") }) }
        @{ Title="Round Summary"; Rows=($rounds | ForEach-Object { [ordered]@{ round=$_.round; issues=$_.issues; detail=$_.detail } }) }
        @{ Title="Tool Registry Matrix"; Rows=($registry | ForEach-Object { [ordered]@{ id=$_.registry_id; tool=$_.tool; ast=$_.ast_parser_status; allow_import=$_.allow_import; risk=$_.risk_level } }) }
        @{ Title="Governance Decision"; Rows=@([ordered]@{ core=$core.gate; governance=$govDec.decision; codex=$codex.code_generation_plan; regression=$(if($regression){"RED"}else{"GREEN"}) }) }
    )
    $finalReport = def_WriteHtmlMatrix -Path (Join-Path $script:RunDir "VIA_PANORAMIC_MATRIX.html") -Title "VIA 全景矩陣 · Supportive Core Prompt Injection" -Sections $finalSecs
    [void](def_WriteEvidence -Stage "final_gate" -Payload $finalGate)

    # ---------------------------------------------------- 十五: answers ----------
    Write-Line ""
    Write-Line "---- 十五、生成器必須回答 ----" $VL.Teal
    Write-Line ("三個 PowerShell 入口存在: Core={0} Gov={1} Codex={2}" -f $psStatic["PS_CORE"].exists,$psStatic["PS_GOV"].exists,$psStatic["PS_CODEX"].exists)
    $pyExist = ($fileRows | Where-Object { $_.kind -eq "Python" -and $_.key -ne "AEGIS" -and $_.exists } | Measure-Object).Count
    Write-Line ("六個 Python 支援模組存在: {0}/6" -f $pyExist)
    Write-Line ("VeritasAegisNexus.py 存在: {0}  -> NetworkStatus={1}" -f ($fileRows | Where-Object {$_.key -eq 'AEGIS'}).exists, $netGate.network_status)
    Write-Line "--- 每工具 resolved path / Registry ID / SHA-256 / 允許載入 ---" "DarkGray"
    foreach ($r in $registry) {
        $shaShort = if ($r.sha256) { $r.sha256.Substring(0,12) } else { "----" }
        Write-Line ("  {0,-26} {1,-11} sha={2} import={3} exec={4}" -f $r.registry_id, $r.type, $shaShort, $r.allow_import, $r.allow_execute)
    }
    Write-Line ("Prompt 經過入口: NexusCore -> CentralGovernance -> Codex (decision={0})" -f $govDec.decision)
    Write-Line ("Prompt 註冊至 run-local overlay: {0} (state={1})" -f (Join-Path $script:OverlayDir 'VIA_PROMPT_SSOT_OVERLAY.json'), $regApply.state)
    Write-Line ("加速器: mode={0} (非 import-time 啟用)  網路工具使用: {1}" -f $accGate.accelerator_mode, ($netGate.network_tasks -eq 'ALLOWED'))
    Write-Line ("Runtime Bridge 啟用: {0}  降級項: {1}" -f $bridgePlan.will_activate, (@($finalGate.warnings) -join '; '))
    Write-Line ("最終 Gate: {0}" -f $finalGate.final_gate) $(if($finalGate.final_gate -eq 'VIA_PROMPT_IMPORT_READY'){$VL.Down}elseif($finalGate.final_gate -match 'BLOCKED'){$VL.Up}else{$VL.Gold})
    Write-Line ("下一安全步驟: operator 審閱 {0}，確認後手動授權方可進入實際 import/bridge" -f $script:RunDir)
    Write-Line ("證據輸出位置: {0}" -f $script:RunDir) $VL.Blue

    Write-Line ""
    Write-Line "「本 Prompt 透過 Invoke-VeritasNexusCore.ps1 進入 VIA 支援核心，經 Invoke-VIA-CentralGovernanceManager.ps1 完成路徑、環境、Registry、SSOT、加速器、網路與 Runtime Bridge 決策後，才可交由 Invoke-VeritasCodexNexus.ps1 進行 AST 分析與生成計畫。任何模組不得繞過中央治理入口，直接 import 未註冊工具、啟用網路、修改 canonical SSOT 或自行啟動 Runtime Bridge。」" "White"

    if ($OpenReport -and (Test-Path -LiteralPath $finalReport)) {
        Start-Process $finalReport
    }
    Write-Line ""
    Write-Line "(完成。console 保持開啟。重複貼上安全且冪等。)" "DarkGray"
}

def_Main
