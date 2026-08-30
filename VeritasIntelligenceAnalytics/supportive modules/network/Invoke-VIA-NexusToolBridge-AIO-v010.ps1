param(
    [string]$Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$SupportiveDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",
    [string]$ToolRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_NexusToolBridge",
    [bool]$AllowNetworkInstall = $true,
    [bool]$InstallPSModules = $true,
    [bool]$ImportPSModules = $true,
    [bool]$RunNexusCoreDryRun = $true,
    [bool]$RunPolyglotDryRun = $true,
    [bool]$GenerateBridgeModule = $true,
    [bool]$OpenReport = $true,
    [int]$TimeoutSec = 180,
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
# def PARAMETERS / POLICY
# =============================================================================
$def_PARAM_RUN_ID = "RUN_{0}_VIA_NEXUS_TOOLBRIDGE" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_PARAM_POLICY = [ordered]@{
    db_write           = $false
    canonical_merge    = $false
    destructive_delete = $false
    stop_process       = $false
    append_only        = $true
    repair_mode        = "DRY_RUN"
    network_install    = $AllowNetworkInstall
}
$def_PARAM_REQUIRED_FILES = @(
    (Join-Path $SupportiveDir "Read_Me_VeritasNexusCore.md"),
    (Join-Path $SupportiveDir "Invoke-VeritasNexusCore.ps1"),
    (Join-Path $SupportiveDir "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1")
)
$def_PARAM_PS_MODULES = @(
    [pscustomobject]@{Name="PSScriptAnalyzer"; Purpose="PowerShell static analysis / safe auto-fix candidate detection"; Required=$true},
    [pscustomobject]@{Name="Pester"; Purpose="PowerShell test runner"; Required=$true},
    [pscustomobject]@{Name="PSWriteHTML"; Purpose="HTML matrix report generation"; Required=$false},
    [pscustomobject]@{Name="ImportExcel"; Purpose="CSV/XLSX matrix review"; Required=$false},
    [pscustomobject]@{Name="PSFramework"; Purpose="structured logging helpers"; Required=$false},
    [pscustomobject]@{Name="CompletionPredictor"; Purpose="PSReadLine command prediction accelerator"; Required=$false},
    [pscustomobject]@{Name="Microsoft.PowerShell.SecretManagement"; Purpose="safe secret bridge"; Required=$false},
    [pscustomobject]@{Name="Microsoft.PowerShell.SecretStore"; Purpose="local secret vault bridge"; Required=$false},
    [pscustomobject]@{Name="WinGet.Client"; Purpose="package manager integration check"; Required=$false},
    [pscustomobject]@{Name="BurntToast"; Purpose="optional local notification"; Required=$false}
)
$def_PARAM_NATIVE_TOOLS = @("pwsh", "powershell", "python", "pip", "git", "winget", "curl")
$def_PARAM_ACCELERATORS = @(
    [pscustomobject]@{ID="A01"; Name="Run Isolation"; Detail="Each run writes into an isolated append-only run folder."},
    [pscustomobject]@{ID="A02"; Name="Timeout Guard"; Detail="External tools run through child process with timeout; parent does not hang."},
    [pscustomobject]@{ID="A03"; Name="AST Before Invoke"; Detail="PowerShell files are parse-checked before being called."},
    [pscustomobject]@{ID="A04"; Name="Module Cache First"; Detail="Detect installed modules before network install to reduce delay."},
    [pscustomobject]@{ID="A05"; Name="Network Retry Lite"; Detail="Installation attempts are isolated and failure becomes WARN, not fatal."},
    [pscustomobject]@{ID="A06"; Name="Hash Inventory"; Detail="SHA256 records protect against uncontrolled overwrite."},
    [pscustomobject]@{ID="A07"; Name="Bridge Wrapper"; Detail="Other scripts call a stable wrapper instead of raw tool paths."},
    [pscustomobject]@{ID="A08"; Name="Low-Memory Scan"; Detail="Streaming file inspection avoids loading the whole tree into memory."},
    [pscustomobject]@{ID="A09"; Name="Hydra Gate"; Detail="Parallel-safe tasks are separated from sequential gated tasks."},
    [pscustomobject]@{ID="A10"; Name="HTML Matrix"; Detail="Every phase emits CSV/JSON/HTML for review and later integration."}
)

# =============================================================================
# def RUNTIME PATHS
# =============================================================================
$def_RUN_ROOT = Join-Path $ToolRoot ("runs\" + $def_PARAM_RUN_ID)
$def_REGISTRY_DIR = Join-Path $def_RUN_ROOT "registry"
$def_LOG_DIR = Join-Path $def_RUN_ROOT "logs"
$def_REPORT_DIR = Join-Path $def_RUN_ROOT "report"
$def_BRIDGE_DIR = Join-Path $ToolRoot "bridge"
$def_MATRIX_CSV = Join-Path $def_REGISTRY_DIR "VIA_NexusToolBridge_Matrix.csv"
$def_MATRIX_JSON = Join-Path $def_REGISTRY_DIR "VIA_NexusToolBridge_Matrix.json"
$def_REPORT_HTML = Join-Path $def_REPORT_DIR "VIA_NexusToolBridge_Report.html"
$def_BRIDGE_PSM1 = Join-Path $def_BRIDGE_DIR "VIA_NexusToolBridge.psm1"
$def_BRIDGE_JSON = Join-Path $def_BRIDGE_DIR "VIA_NexusToolBridge.json"

# =============================================================================
# def GLOBAL STATE
# =============================================================================
$script:def_Rows = New-Object System.Collections.Generic.List[object]
$script:def_StartTime = Get-Date

# =============================================================================
# def CORE HELPERS
# =============================================================================
function def_EnsureDirectory {
    param([string]$Path)
    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function def_CountSafe {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return 0 }
    if ($InputObject -is [array]) { return $InputObject.Count }
    if ($InputObject -is [System.Collections.ICollection]) { return $InputObject.Count }
    return 1
}

function def_AsArraySafe {
    param([object]$InputObject)
    if ($null -eq $InputObject) { return @() }
    return @($InputObject)
}

function def_HtmlEncode {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_WriteLog {
    param(
        [string]$Level,
        [string]$Message
    )
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $color = "Gray"
    if ($Level -eq "OK") { $color = "Green" }
    elseif ($Level -eq "WARN") { $color = "Yellow" }
    elseif ($Level -eq "FAIL") { $color = "Red" }
    elseif ($Level -eq "RUN") { $color = "Cyan" }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

function def_ShowProgress {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Activity,
        [string]$Status
    )
    $pct = 0
    if ($Total -gt 0) {
        $pct = [math]::Min(100, [math]::Round(($Step / $Total) * 100, 0))
    }
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $pct
}

function def_AddRow {
    param(
        [string]$Round,
        [string]$Layer,
        [string]$Name,
        [string]$Status,
        [string]$Risk,
        [string]$Class,
        [string]$Priority,
        [string]$Metric,
        [object]$Value,
        [string]$Message,
        [string]$Path = ""
    )
    $row = [pscustomobject]@{
        Time     = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Round    = $Round
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
    $script:def_Rows.Add($row) | Out-Null
}

function def_GetSha256Safe {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        }
        return ""
    } catch {
        return ""
    }
}

function def_ExportMatrix {
    def_EnsureDirectory -Path $def_REGISTRY_DIR
    $rows = def_AsArraySafe $script:def_Rows
    $rows | Export-Csv -LiteralPath $def_MATRIX_CSV -NoTypeInformation -Encoding UTF8BOM
    $rows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $def_MATRIX_JSON -Encoding UTF8
}

function def_WriteHtmlReport {
    def_EnsureDirectory -Path $def_REPORT_DIR
    $rows = def_AsArraySafe $script:def_Rows
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $fail = def_CountSafe ($rows | Where-Object { $_.Status -like "FAIL*" -or $_.Risk -eq "HIGH" })
    $risk = "LOW"
    if ($fail -gt 0) { $risk = "HIGH" }
    elseif ($warn -gt 0) { $risk = "MEDIUM" }

    $trs = foreach ($r in $rows) {
        $riskClass = "risk-low"
        if ($r.Risk -eq "HIGH") { $riskClass = "risk-high" }
        elseif ($r.Risk -eq "MEDIUM") { $riskClass = "risk-medium" }
        "<tr class='$riskClass'><td>$(def_HtmlEncode $r.Round)</td><td>$(def_HtmlEncode $r.Layer)</td><td>$(def_HtmlEncode $r.Name)</td><td>$(def_HtmlEncode $r.Status)</td><td>$(def_HtmlEncode $r.Risk)</td><td>$(def_HtmlEncode $r.Class)</td><td>$(def_HtmlEncode $r.Priority)</td><td>$(def_HtmlEncode $r.Metric)</td><td>$(def_HtmlEncode $r.Value)</td><td>$(def_HtmlEncode $r.Message)</td><td>$(def_HtmlEncode $r.Path)</td></tr>"
    }

    $policyJson = ($def_PARAM_POLICY | ConvertTo-Json -Compress)
    $accelHtml = foreach ($a in $def_PARAM_ACCELERATORS) {
        "<div class='accel'><b>$(def_HtmlEncode $a.ID) · $(def_HtmlEncode $a.Name)</b><br><span>$(def_HtmlEncode $a.Detail)</span></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Nexus ToolBridge Report</title>
<style>
body{margin:0;background:#f8f8f4;color:#18211f;font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;}
header{padding:34px 42px;border-bottom:1px solid #d7ded8;background:linear-gradient(135deg,#f8f8f4,#e9f1ee);}
h1{margin:0;font-size:28px;font-weight:650;letter-spacing:.04em}
.sub{margin-top:8px;color:#53615c;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:20px 42px}
.card{background:white;border:1px solid #d7ded8;border-radius:18px;padding:16px;box-shadow:0 10px 30px rgba(20,40,35,.06)}
.k{font-size:12px;color:#6c7771}.v{font-size:24px;font-weight:700;margin-top:4px}
.accels{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;padding:0 42px 20px 42px}
.accel{background:#ffffffcc;border:1px solid #d7ded8;border-radius:14px;padding:10px;font-size:12px}
.accel span{color:#5b6863}
.wrap{padding:0 42px 42px 42px}
table{border-collapse:collapse;width:100%;font-size:12px;background:white;border-radius:16px;overflow:hidden}
th{position:sticky;top:0;background:#22342f;color:white;text-align:left;padding:9px}
td{border-bottom:1px solid #e4e8e5;padding:8px;vertical-align:top}
.risk-low td{background:#fbfffd}
.risk-medium td{background:#fffaf0}
.risk-high td{background:#fff3f1}
.path{font-family:Consolas,monospace}
</style>
</head>
<body>
<header>
<h1>理 · VIA Nexus ToolBridge · One PowerShell Independent Module</h1>
<div class="sub">Run ID: $def_PARAM_RUN_ID · Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss") · Policy: $(def_HtmlEncode $policyJson)</div>
</header>
<section class="grid">
<div class="card"><div class="k">Status</div><div class="v">$(if($fail -gt 0){"REVIEW"}elseif($warn -gt 0){"READY_WARN"}else{"READY"})</div></div>
<div class="card"><div class="k">Risk</div><div class="v">$risk</div></div>
<div class="card"><div class="k">OK</div><div class="v">$ok</div></div>
<div class="card"><div class="k">WARN/HIGH</div><div class="v">$warn / $fail</div></div>
</section>
<section class="accels">$($accelHtml -join "`n")</section>
<section class="wrap">
<table>
<thead><tr><th>Round</th><th>Layer</th><th>Name</th><th>Status</th><th>Risk</th><th>Class</th><th>Priority</th><th>Metric</th><th>Value</th><th>Message</th><th>Path</th></tr></thead>
<tbody>
$($trs -join "`n")
</tbody>
</table>
</section>
</body>
</html>
"@
    $html | Set-Content -LiteralPath $def_REPORT_HTML -Encoding UTF8
}

# =============================================================================
# def PROCESS / TOOL EXECUTION
# =============================================================================
function def_InvokeChildProcessSafe {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory,
        [int]$TimeoutSeconds = 180
    )
    $stdout = Join-Path $def_LOG_DIR ("{0}_stdout.log" -f ($Name -replace '[^\w\-]','_'))
    $stderr = Join-Path $def_LOG_DIR ("{0}_stderr.log" -f ($Name -replace '[^\w\-]','_'))
    try {
        if (-not (Test-Path -LiteralPath $FilePath)) {
            return [pscustomobject]@{Status="WARN_NOT_FOUND"; ExitCode=$null; TimedOut=$false; Stdout=$stdout; Stderr=$stderr; Message="Executable not found."}
        }
        $psiArgs = @()
        if ($ArgumentList) { $psiArgs = $ArgumentList }
        $p = Start-Process -FilePath $FilePath -ArgumentList $psiArgs -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -PassThru
        $finished = $p.WaitForExit($TimeoutSeconds * 1000)
        if (-not $finished) {
            return [pscustomobject]@{Status="WARN_TIMEOUT_CHILD_LEFT_RUNNING"; ExitCode=$null; TimedOut=$true; Stdout=$stdout; Stderr=$stderr; Message="Timeout reached; child not stopped due policy."}
        }
        return [pscustomobject]@{Status=("OK_EXIT_{0}" -f $p.ExitCode); ExitCode=$p.ExitCode; TimedOut=$false; Stdout=$stdout; Stderr=$stderr; Message="Child process completed."}
    } catch {
        return [pscustomobject]@{Status="WARN_PROCESS_ERROR"; ExitCode=$null; TimedOut=$false; Stdout=$stdout; Stderr=$stderr; Message=$_.Exception.Message}
    }
}

function def_TestPowerShellAstSafe {
    param([string]$Path)
    try {
        [System.Management.Automation.Language.Token[]]$tokens = $null
        [System.Management.Automation.Language.ParseError[]]$errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)
        return [pscustomobject]@{
            Ok = ((def_CountSafe $errors) -eq 0)
            ErrorCount = (def_CountSafe $errors)
            Errors = $errors
        }
    } catch {
        return [pscustomobject]@{
            Ok = $false
            ErrorCount = 1
            Errors = @([pscustomobject]@{Message=$_.Exception.Message; Extent="AST_PARSER_EXCEPTION"; StartLineNumber=0; StartColumnNumber=0})
        }
    }
}

# =============================================================================
# def ROUND0 INIT / INVENTORY
# =============================================================================
function def_Round0_Initialize {
    def_ShowProgress -Step 1 -Total 10 -Activity "VIA Nexus ToolBridge" -Status "Round0 initialize"
    def_EnsureDirectory -Path $ToolRoot
    def_EnsureDirectory -Path $def_RUN_ROOT
    def_EnsureDirectory -Path $def_REGISTRY_DIR
    def_EnsureDirectory -Path $def_LOG_DIR
    def_EnsureDirectory -Path $def_REPORT_DIR
    def_EnsureDirectory -Path $def_BRIDGE_DIR

    def_AddRow "Round0" "POLICY" "Safety Policy" "OK_LOCKED" "LOW" "SEQUENTIAL_GATED" "P0" "policy" "append-only" "No DB write, no canonical merge, no destructive delete, no stop-process." $ToolRoot
    foreach ($a in $def_PARAM_ACCELERATORS) {
        def_AddRow "Round0" "ACCELERATOR" $a.Name "OK_ENABLED" "LOW" "PARALLEL_SAFE" "P1" $a.ID "enabled" $a.Detail ""
    }

    if (Test-Path -LiteralPath $Root -PathType Container) {
        def_AddRow "Round0" "ROOT" "VIA Root" "OK_FOUND" "LOW" "PARALLEL_SAFE" "P0" "exists" $true "Root folder available." $Root
    } else {
        def_AddRow "Round0" "ROOT" "VIA Root" "FAIL_MISSING" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exists" $false "Root folder missing." $Root
    }
}

function def_Round0_CheckRequiredFiles {
    def_ShowProgress -Step 2 -Total 10 -Activity "VIA Nexus ToolBridge" -Status "Round0 required files"
    foreach ($f in $def_PARAM_REQUIRED_FILES) {
        $name = Split-Path $f -Leaf
        if (Test-Path -LiteralPath $f -PathType Leaf) {
            $hash = def_GetSha256Safe -Path $f
            def_AddRow "Round0" "SUPPORTIVE" $name "OK_FOUND" "LOW" "PARALLEL_SAFE" "P0" "sha256" $hash "Required supportive file found." $f
        } else {
            def_AddRow "Round0" "SUPPORTIVE" $name "FAIL_MISSING" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exists" $false "Required supportive file missing." $f
        }
    }
}

function def_Round0_CheckNativeTools {
    def_ShowProgress -Step 3 -Total 10 -Activity "VIA Nexus ToolBridge" -Status "Round0 native tools"
    foreach ($tool in $def_PARAM_NATIVE_TOOLS) {
        $cmd = Get-Command $tool -ErrorAction SilentlyContinue
        if ($cmd) {
            def_AddRow "Round0" "NATIVE_TOOL" $tool "OK_FOUND" "LOW" "PARALLEL_SAFE" "P1" "path" $cmd.Source "Native tool available." $cmd.Source
        } else {
            def_AddRow "Round0" "NATIVE_TOOL" $tool "WARN_MISSING" "MEDIUM" "PARALLEL_SAFE" "P2" "path" "" "Native tool not found; skipped, not fatal." ""
        }
    }
}

# =============================================================================
# def ROUND1 MODULE INSTALL / IMPORT
# =============================================================================
function def_Round1_InstallAndImportModules {
    def_ShowProgress -Step 4 -Total 10 -Activity "VIA Nexus ToolBridge" -Status "Round1 modules"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
    } catch {
        try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
    }

    foreach ($m in $def_PARAM_PS_MODULES) {
        $existing = Get-Module -ListAvailable -Name $m.Name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($existing) {
            def_AddRow "Round1" "PS_MODULE" $m.Name "OK_PRESENT" "LOW" "PARALLEL_SAFE" "P1" "version" $existing.Version "Module already installed. Purpose: $($m.Purpose)" $existing.Path
        } else {
            if ($InstallPSModules -and $AllowNetworkInstall) {
                try {
                    Install-Module -Name $m.Name -Scope CurrentUser -Force -AllowClobber -ErrorAction Stop
                    $installed = Get-Module -ListAvailable -Name $m.Name -ErrorAction SilentlyContinue | Select-Object -First 1
                    if ($installed) {
                        def_AddRow "Round1" "PS_MODULE" $m.Name "OK_INSTALLED" "LOW" "PARALLEL_SAFE" "P1" "version" $installed.Version "Module installed. Purpose: $($m.Purpose)" $installed.Path
                    } else {
                        def_AddRow "Round1" "PS_MODULE" $m.Name "WARN_INSTALL_UNCONFIRMED" "MEDIUM" "PARALLEL_SAFE" "P2" "installed" "unknown" "Install command completed but module not discovered." ""
                    }
                } catch {
                    $risk = if ($m.Required) { "MEDIUM" } else { "LOW" }
                    def_AddRow "Round1" "PS_MODULE" $m.Name "WARN_INSTALL_FAILED" $risk "PARALLEL_SAFE" "P2" "error" $_.Exception.Message "Module install failed; continuing." ""
                }
            } else {
                $risk = if ($m.Required) { "MEDIUM" } else { "LOW" }
                def_AddRow "Round1" "PS_MODULE" $m.Name "WARN_NOT_INSTALLED_BY_POLICY" $risk "PARALLEL_SAFE" "P2" "network" $AllowNetworkInstall "Install disabled or network disabled." ""
            }
        }

        if ($ImportPSModules) {
            try {
                Import-Module -Name $m.Name -ErrorAction Stop
                def_AddRow "Round1" "PS_MODULE_IMPORT" $m.Name "OK_IMPORTED" "LOW" "PARALLEL_SAFE" "P1" "import" $true "Module imported into current session." ""
            } catch {
                def_AddRow "Round1" "PS_MODULE_IMPORT" $m.Name "WARN_IMPORT_FAILED" "LOW" "PARALLEL_SAFE" "P3" "error" $_.Exception.Message "Import failed; bridge can still call tools directly." ""
            }
        }
    }
}

# =============================================================================
# def ROUND1 EXTERNAL COMMAND REVIEW
# =============================================================================
function def_Round1_ReviewExternalCommands {
    def_ShowProgress -Step 5 -Total 10 -Activity "VIA Nexus ToolBridge" -Status "Round1 external command review"
    foreach ($f in $def_PARAM_REQUIRED_FILES) {
        if (-not (Test-Path -LiteralPath $f -PathType Leaf)) { continue }
        $name = Split-Path $f -Leaf
        $contentSample = ""
        try {
            $contentSample = (Get-Content -LiteralPath $f -Raw -ErrorAction Stop)
        } catch {
            $contentSample = ""
        }

        $strength = New-Object System.Collections.Generic.List[string]
        $weakness = New-Object System.Collections.Generic.List[string]

        if ($contentSample -match "no DB write|DB write=false|no canonical|append-only|dry-run|DRY_RUN") { $strength.Add("Policy language detected") | Out-Null } else { $weakness.Add("Policy language not obvious") | Out-Null }
        if ($contentSample -match "HTML|Report|Matrix|CSV|JSON") { $strength.Add("Report/matrix output detected") | Out-Null } else { $weakness.Add("Report output not obvious") | Out-Null }
        if ($contentSample -match "try\s*\{|catch\s*\{") { $strength.Add("Error handling detected") | Out-Null } else { $weakness.Add("Error handling not obvious") | Out-Null }
        if ($contentSample -match "Write-Progress|progress") { $strength.Add("Progress indicator detected") | Out-Null } else { $weakness.Add("Progress indicator weak/missing") | Out-Null }
        if ($contentSample -match "Start-Process|pwsh|timeout|WaitForExit") { $strength.Add("Process isolation or external tool invocation detected") | Out-Null } else { $weakness.Add("Process isolation not obvious") | Out-Null }

        if ($name -like "*.ps1") {
            $parse = def_TestPowerShellAstSafe -Path $f
            if ($parse.Ok) {
                def_AddRow "Round1" "COMMAND_REVIEW" $name "OK_PARSE_REVIEWED" "LOW" "PARALLEL_SAFE" "P1" "pros/cons" "$(($strength -join '; ')) / $(($weakness -join '; '))" "External command reviewed and parse-clean." $f
            } else {
                def_AddRow "Round1" "COMMAND_REVIEW" $name "WARN_PARSE_REVIEW" "MEDIUM" "SEQUENTIAL_GATED" "P0" "parse_errors" $parse.ErrorCount "External command has parse review issue; do not dot-source directly." $f
            }
        } else {
            def_AddRow "Round1" "DOC_REVIEW" $name "OK_REVIEWED" "LOW" "PARALLEL_SAFE" "P1" "pros/cons" "$(($strength -join '; ')) / $(($weakness -join '; '))" "Documentation reviewed for method and tool-bridge cues." $f
        }
    }
}

# =============================================================================
# def ROUND2 TOOL BASELINE DRY-RUN
# =============================================================================
function def_Round2_RunSupportTools {
    def_ShowProgress -Step 6 -Total 10 -Activity "VIA Nexus ToolBridge" -Status "Round2 dry-run tools"
    $pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue)
    if (-not $pwsh) {
        def_AddRow "Round2" "PROCESS" "pwsh" "FAIL_NOT_FOUND" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "exists" $false "PowerShell 7 pwsh not found." ""
        return
    }

    $nexus = Join-Path $SupportiveDir "Invoke-VeritasNexusCore.ps1"
    if ($RunNexusCoreDryRun -and (Test-Path -LiteralPath $nexus -PathType Leaf)) {
        $res = def_InvokeChildProcessSafe -Name "Invoke_VeritasNexusCore" -FilePath $pwsh.Source -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$nexus) -WorkingDirectory $SupportiveDir -TimeoutSeconds $TimeoutSec
        $risk = if ($res.Status -like "OK_EXIT_0") { "LOW" } elseif ($res.TimedOut) { "MEDIUM" } else { "MEDIUM" }
        def_AddRow "Round2" "PROCESS" "Invoke-VeritasNexusCore" $res.Status $risk "PARALLEL_SAFE" "P2" "exit" $res.ExitCode $res.Message $nexus
    } else {
        def_AddRow "Round2" "PROCESS" "Invoke-VeritasNexusCore" "WARN_SKIPPED" "LOW" "PARALLEL_SAFE" "P3" "run" $RunNexusCoreDryRun "Skipped by policy or missing." $nexus
    }

    $poly = Join-Path $SupportiveDir "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"
    if ($RunPolyglotDryRun -and (Test-Path -LiteralPath $poly -PathType Leaf)) {
        $res = def_InvokeChildProcessSafe -Name "Invoke_VIA_PolyglotCTR" -FilePath $pwsh.Source -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$poly) -WorkingDirectory $SupportiveDir -TimeoutSeconds $TimeoutSec
        $risk = if ($res.Status -like "OK_EXIT_0") { "LOW" } elseif ($res.TimedOut) { "MEDIUM" } else { "MEDIUM" }
        def_AddRow "Round2" "PROCESS" "Invoke-VIA-PolyglotCheckTestRepair" $res.Status $risk "PARALLEL_SAFE" "P2" "exit" $res.ExitCode $res.Message $poly
    } else {
        def_AddRow "Round2" "PROCESS" "Invoke-VIA-PolyglotCheckTestRepair" "WARN_SKIPPED" "LOW" "PARALLEL_SAFE" "P3" "run" $RunPolyglotDryRun "Skipped by policy or missing." $poly
    }
}

# =============================================================================
# def ROUND2 SOURCE INVENTORY LIGHT
# =============================================================================
function def_Round2_SourceInventoryLight {
    def_ShowProgress -Step 7 -Total 10 -Activity "VIA Nexus ToolBridge" -Status "Round2 source inventory"
    $counts = [ordered]@{ps=0; py=0; js=0; cs=0}
    try {
        Get-ChildItem -LiteralPath $Root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            switch -Regex ($_.Extension.ToLowerInvariant()) {
                '^\.ps1$|^\.psm1$|^\.psd1$' { $counts.ps++; break }
                '^\.py$' { $counts.py++; break }
                '^\.js$|^\.ts$|^\.mjs$|^\.cjs$' { $counts.js++; break }
                '^\.cs$' { $counts.cs++; break }
            }
        }
        def_AddRow "Round2" "INVENTORY" "Source Inventory Light" "OK_SCANNED" "LOW" "PARALLEL_SAFE" "P2" "ps/py/js/cs" "$($counts.ps)/$($counts.py)/$($counts.js)/$($counts.cs)" "Low-memory file inventory completed." $Root
    } catch {
        def_AddRow "Round2" "INVENTORY" "Source Inventory Light" "WARN_SCAN_FAILED" "MEDIUM" "PARALLEL_SAFE" "P2" "error" $_.Exception.Message "Inventory failed but bridge continues." $Root
    }
}

# =============================================================================
# def ROUND3 BRIDGE GENERATION
# =============================================================================
function def_Round3_GenerateBridgeModule {
    def_ShowProgress -Step 8 -Total 10 -Activity "VIA Nexus ToolBridge" -Status "Round3 bridge module"
    if (-not $GenerateBridgeModule) {
        def_AddRow "Round3" "BRIDGE" "VIA_NexusToolBridge.psm1" "WARN_SKIPPED_BY_POLICY" "LOW" "PARALLEL_SAFE" "P3" "generate" $false "Bridge module generation disabled." $def_BRIDGE_PSM1
        return
    }

    $bridgeContent = @'
# VIA Nexus ToolBridge.psm1
# Generated by Invoke-VIA-NexusToolBridge-AIO-v010.ps1
# Purpose: stable wrapper for NexusCore / Polyglot CTR / future PowerShell modules.

function def_InvokeVIACommandSafe {
    param(
        [Parameter(Mandatory=$true)][string]$ScriptPath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = "",
        [int]$TimeoutSec = 180
    )
    if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) {
        return [pscustomobject]@{Status="WARN_SCRIPT_MISSING"; ExitCode=$null; Path=$ScriptPath; Message="Script missing."}
    }
    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if (-not $pwsh) {
        return [pscustomobject]@{Status="FAIL_PWSH_MISSING"; ExitCode=$null; Path=$ScriptPath; Message="pwsh missing."}
    }
    if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) {
        $WorkingDirectory = Split-Path $ScriptPath -Parent
    }
    $out = Join-Path $WorkingDirectory ("_via_bridge_stdout_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $err = Join-Path $WorkingDirectory ("_via_bridge_stderr_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $argList = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$ScriptPath) + $Arguments
    try {
        $p = Start-Process -FilePath $pwsh.Source -ArgumentList $argList -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden -PassThru
        $finished = $p.WaitForExit($TimeoutSec * 1000)
        if (-not $finished) {
            return [pscustomobject]@{Status="WARN_TIMEOUT_CHILD_LEFT_RUNNING"; ExitCode=$null; Path=$ScriptPath; Stdout=$out; Stderr=$err; Message="Timeout; child not stopped by policy."}
        }
        return [pscustomobject]@{Status=("OK_EXIT_{0}" -f $p.ExitCode); ExitCode=$p.ExitCode; Path=$ScriptPath; Stdout=$out; Stderr=$err; Message="Completed."}
    } catch {
        return [pscustomobject]@{Status="WARN_PROCESS_ERROR"; ExitCode=$null; Path=$ScriptPath; Stdout=$out; Stderr=$err; Message=$_.Exception.Message}
    }
}

function def_InvokeNexusCore {
    param(
        [string]$SupportiveDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",
        [int]$TimeoutSec = 180
    )
    $scriptPath = Join-Path $SupportiveDir "Invoke-VeritasNexusCore.ps1"
    return def_InvokeVIACommandSafe -ScriptPath $scriptPath -WorkingDirectory $SupportiveDir -TimeoutSec $TimeoutSec
}

function def_InvokePolyglotCTR {
    param(
        [string]$SupportiveDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules",
        [int]$TimeoutSec = 180
    )
    $scriptPath = Join-Path $SupportiveDir "Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1"
    return def_InvokeVIACommandSafe -ScriptPath $scriptPath -WorkingDirectory $SupportiveDir -TimeoutSec $TimeoutSec
}

function def_GetVIAAcceleratorMatrix {
    return @(
        [pscustomobject]@{ID="A01"; Name="Run Isolation"},
        [pscustomobject]@{ID="A02"; Name="Timeout Guard"},
        [pscustomobject]@{ID="A03"; Name="AST Before Invoke"},
        [pscustomobject]@{ID="A04"; Name="Module Cache First"},
        [pscustomobject]@{ID="A05"; Name="Network Retry Lite"},
        [pscustomobject]@{ID="A06"; Name="Hash Inventory"},
        [pscustomobject]@{ID="A07"; Name="Bridge Wrapper"},
        [pscustomobject]@{ID="A08"; Name="Low-Memory Scan"},
        [pscustomobject]@{ID="A09"; Name="Hydra Gate"},
        [pscustomobject]@{ID="A10"; Name="HTML Matrix"}
    )
}

Export-ModuleMember -Function def_InvokeVIACommandSafe,def_InvokeNexusCore,def_InvokePolyglotCTR,def_GetVIAAcceleratorMatrix
'@

    try {
        $bridgeContent | Set-Content -LiteralPath $def_BRIDGE_PSM1 -Encoding UTF8
        $bridgeMeta = [ordered]@{
            schema = "VIA.NexusToolBridge"
            version = "v0.1.0"
            generated = (Get-Date).ToString("s")
            root = $Root
            supportive_dir = $SupportiveDir
            bridge_module = $def_BRIDGE_PSM1
            required_files = $def_PARAM_REQUIRED_FILES
            accelerators = $def_PARAM_ACCELERATORS
            policy = $def_PARAM_POLICY
        }
        $bridgeMeta | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $def_BRIDGE_JSON -Encoding UTF8
        def_AddRow "Round3" "BRIDGE" "VIA_NexusToolBridge.psm1" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P0" "module" "ready" "Bridge module generated for reuse by other PowerShell scripts." $def_BRIDGE_PSM1
        def_AddRow "Round3" "BRIDGE" "VIA_NexusToolBridge.json" "OK_WRITTEN" "LOW" "PARALLEL_SAFE" "P0" "manifest" "ready" "Bridge manifest generated." $def_BRIDGE_JSON
    } catch {
        def_AddRow "Round3" "BRIDGE" "VIA_NexusToolBridge" "FAIL_WRITE_ERROR" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "error" $_.Exception.Message "Failed to generate bridge module." $def_BRIDGE_PSM1
    }
}

function def_Round3_FinalClassification {
    def_ShowProgress -Step 9 -Total 10 -Activity "VIA Nexus ToolBridge" -Status "Round3 classification"
    $rows = def_AsArraySafe $script:def_Rows
    $parallel = def_CountSafe ($rows | Where-Object { $_.Class -eq "PARALLEL_SAFE" -and $_.Risk -ne "HIGH" })
    $sequential = def_CountSafe ($rows | Where-Object { $_.Class -like "SEQUENTIAL*" -or $_.Risk -eq "HIGH" })
    $high = def_CountSafe ($rows | Where-Object { $_.Risk -eq "HIGH" })
    def_AddRow "Round3" "CLASSIFY" "Parallel Safe Items" "OK_CLASSIFIED" "LOW" "PARALLEL_SAFE" "P1" "count" $parallel "Can be handled independently." ""
    def_AddRow "Round3" "CLASSIFY" "Sequential / Gated Items" ($(if($high -gt 0){"WARN_REVIEW_REQUIRED"}else{"OK_CLASSIFIED"})) ($(if($high -gt 0){"HIGH"}else{"LOW"})) "SEQUENTIAL_GATED" "P0" "count" $sequential "Handle these in order to avoid Hydra risk." ""
    def_AddRow "Round3" "CLASSIFY" "Hydra Risk Gate" ($(if($high -gt 0){"WARN_HYDRA_REVIEW"}else{"OK_HYDRA_CLEAR"})) ($(if($high -gt 0){"HIGH"}else{"LOW"})) "SEQUENTIAL_GATED" "P0" "high_risk" $high "High-risk items isolated before broader integration." ""
}

function def_Finalize {
    def_ShowProgress -Step 10 -Total 10 -Activity "VIA Nexus ToolBridge" -Status "Finalize report"
    def_ExportMatrix
    def_WriteHtmlReport
    Write-Progress -Activity "VIA Nexus ToolBridge" -Completed

    $rows = def_AsArraySafe $script:def_Rows
    $ok = def_CountSafe ($rows | Where-Object { $_.Status -like "OK*" })
    $warn = def_CountSafe ($rows | Where-Object { $_.Status -like "WARN*" })
    $fail = def_CountSafe ($rows | Where-Object { $_.Status -like "FAIL*" -or $_.Risk -eq "HIGH" })
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA Nexus ToolBridge AIO v0.1 COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Run Root    : $def_RUN_ROOT"
    Write-Host "Bridge PSM1 : $def_BRIDGE_PSM1"
    Write-Host "Bridge JSON : $def_BRIDGE_JSON"
    Write-Host "HTML        : $def_REPORT_HTML"
    Write-Host "Matrix CSV  : $def_MATRIX_CSV"
    Write-Host "Matrix JSON : $def_MATRIX_JSON"
    Write-Host "OK/WARN/HIGH: $ok / $warn / $fail"
    Write-Host ""
    Write-Host "Import bridge in other scripts:" -ForegroundColor Green
    Write-Host "Import-Module `"$def_BRIDGE_PSM1`" -Force" -ForegroundColor DarkGreen
    Write-Host "def_InvokeNexusCore" -ForegroundColor DarkGreen
    Write-Host "def_InvokePolyglotCTR" -ForegroundColor DarkGreen

    if ($OpenReport -and (Test-Path -LiteralPath $def_REPORT_HTML)) {
        Start-Process $def_REPORT_HTML
    }
}

# =============================================================================
# def MAIN
# =============================================================================
function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA Nexus ToolBridge AIO v0.1" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Root         : $Root"
    Write-Host "Supportive   : $SupportiveDir"
    Write-Host "Tool Root    : $ToolRoot"
    Write-Host "Run ID       : $def_PARAM_RUN_ID"
    Write-Host "Policy       : no DB write · no canonical merge · no destructive delete · no stop-process · append-only"
    Write-Host ""

    def_Round0_Initialize
    def_Round0_CheckRequiredFiles
    def_Round0_CheckNativeTools
    def_Round1_InstallAndImportModules
    def_Round1_ReviewExternalCommands
    def_Round2_RunSupportTools
    def_Round2_SourceInventoryLight
    def_Round3_GenerateBridgeModule
    def_Round3_FinalClassification
    def_Finalize
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    try {
        def_AddRow "FATAL" "RUNTIME" "Unhandled Exception" "FAIL_FATAL" "HIGH" "SEQUENTIAL_REQUIRED" "P0" "error" $_.Exception.Message "Unhandled exception caught; writing final report if possible." ""
        def_Finalize
    } catch {}
} finally {
    if ($KeepPowerShellOpen) {
        Write-Host ""
        Write-Host "PowerShell session remains open." -ForegroundColor Cyan
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
