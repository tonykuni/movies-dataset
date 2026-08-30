param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113B_ROOT = "",
    [bool]$def_PARAM_OPEN_HTML_REPORT = $true
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

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0113C_SECRET_RESOLUTION_GATE" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0113C_secret_resolution_gate"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_USER_EDIT_DIR = Join-Path $def_RUN_DIR "_user_edit_secret_resolution"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0113C_SecretResolutionGate.log"

function def_S {
    param($Value)
    if ($null -eq $Value) { return "" }
    try { return [string]$Value } catch { return "" }
}

function def_EnsureDir {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_USER_EDIT_DIR,$def_LOG_DIR)) {
    def_EnsureDir $d
}

function def_Log {
    param([string]$Level,[string]$Message,[ConsoleColor]$Color = [ConsoleColor]::Gray)
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line -ForegroundColor $Color
    Add-Content -LiteralPath $def_LOG -Value $line -Encoding UTF8
}

function def_Progress {
    param([int]$Step,[int]$Total,[string]$Status)
    $pct = [int](($Step / [Math]::Max(1,$Total)) * 100)
    Write-Progress -Activity "VIA v0113C Secret Resolution Gate" -Status $Status -PercentComplete $pct
    def_Log "RUN" "[$Step/$Total] $Status" Cyan
}

function def_Html {
    param($Text)
    return [System.Net.WebUtility]::HtmlEncode((def_S $Text))
}

function def_GetProp {
    param($Obj,[string]$Name)
    if ($null -eq $Obj) { return "" }
    if ($Obj.PSObject.Properties.Name -contains $Name) {
        return def_S $Obj.$Name
    }
    return ""
}

function def_LoadCsv {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            return @(Import-Csv -LiteralPath $Path)
        }
    } catch {
        def_Log "WARN" "CSV load failed: $Path :: $($_.Exception.Message)" Yellow
    }
    return @()
}

function def_LoadJson {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path) {
            return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    } catch {
        return $null
    }
    return $null
}

function def_WriteCsv {
    param([array]$Rows,[string]$Path)
    if ($Rows -and @($Rows).Count -gt 0) {
        $Rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    } else {
        [pscustomobject]@{ def_empty = "true" } | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    }
}

function def_WriteJson {
    param($Object,[string]$Path,[int]$Depth = 16)
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function def_GetLatestV0113B {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113B_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113B_ROOT) {
            return $def_PARAM_V0113B_ROOT
        }
        throw "Specified v0113B root does not exist: $def_PARAM_V0113B_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0113B_secret_triage_manual_gate"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113B output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0113B_SecretTriage_ManualGate_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113B output found under: $root"
    }

    return $candidates[0].FullName
}

function def_GetEnvPresenceOnly {
    param([string[]]$Names)

    $rows = New-Object System.Collections.ArrayList

    foreach ($name in $Names) {
        $value = [Environment]::GetEnvironmentVariable($name, "Process")
        if ([string]::IsNullOrWhiteSpace($value)) {
            $value = [Environment]::GetEnvironmentVariable($name, "User")
        }
        if ([string]::IsNullOrWhiteSpace($value)) {
            $value = [Environment]::GetEnvironmentVariable($name, "Machine")
        }

        $exists = -not [string]::IsNullOrWhiteSpace($value)
        $length = 0
        if ($exists) { $length = $value.Length }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_env_name = $name
            def_exists = [string]$exists
            def_value_length = [string]$length
            def_value_printed = "false"
            def_policy = "presence_only_no_secret_output"
        })
    }

    return @($rows)
}

function def_BuildResolutionBoard {
    param([array]$SecretTriage,[array]$EnvAudit)

    $rows = New-Object System.Collections.ArrayList
    $blockers = @($SecretTriage | Where-Object { (def_GetProp $_ "def_secret_block") -eq "true" })

    foreach ($r in $blockers) {
        $key = def_GetProp $r "def_normalized_key"
        $class = def_GetProp $r "def_secret_class"
        $sample = def_GetProp $r "def_sample_values_masked"

        $suggested = "MANUAL_REVIEW"
        $release = "false"
        $resolution = ""
        $reason = "Manual review required."

        if ($key -eq "ticker_tokens") {
            $suggested = "CLEAR_FALSE_POSITIVE"
            $release = "true_after_user_confirm"
            $resolution = "No credential pattern; code variable/list token only."
            $reason = "ticker_tokens appears to be internal variable/list handling, not a secret."
        }
        elseif ($key -eq "fred_api_key_env") {
            $suggested = "CLEAR_IF_ENV_NAME_ONLY"
            $release = "true_after_user_confirm"
            $resolution = "Accept only env var name FRED_API_KEY; never raw value."
            $reason = "ENV reference is safe only when no raw value is printed or stored."
        }
        elseif ($key -eq "FRED_API_KEY") {
            $suggested = "CONFIRM_ROTATED_OR_ENV_ONLY"
            $release = "false_until_user_confirms"
            $resolution = "If raw key was ever pasted, rotate it externally. Canonical may store only ENV:FRED_API_KEY."
            $reason = "Masked raw-looking secret marker was detected."
        }

        $envExists = ""
        $envLength = ""

        if ($key -match "fred") {
            $m = @($EnvAudit | Where-Object { (def_GetProp $_ "def_env_name") -eq "FRED_API_KEY" } | Select-Object -First 1)
            if (@($m).Count -gt 0) {
                $envExists = def_GetProp $m[0] "def_exists"
                $envLength = def_GetProp $m[0] "def_value_length"
            }
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "SECRET_RESOLUTION"
            def_normalized_key = $key
            def_owner_engine = def_GetProp $r "def_owner_engine"
            def_domain_family = def_GetProp $r "def_domain_family"
            def_secret_class = $class
            def_current_block = "true"
            def_user_secret_resolved = ""
            def_suggested_resolution = $suggested
            def_release_condition = $release
            def_selected_safe_canonical_value = $resolution
            def_env_exists_presence_only = $envExists
            def_env_value_length_only = $envLength
            def_value_printed = "false"
            def_rotate_if_raw_was_real = $(if ($key -eq "FRED_API_KEY") { "true" } else { "false" })
            def_reason = $reason
            def_sample_values_masked = $sample
        })
    }

    return @($rows)
}

function def_BuildReadiness {
    param([array]$ResolutionBoard,[array]$P0Refined,[array]$P1Refined,[array]$DirectBoard)

    $directOk = @($DirectBoard | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $directReview = @($DirectBoard | Where-Object { (def_GetProp $_ "def_direct_status") -ne "DIRECT_CONTRACT_SMOKE_OK" }).Count

    $secretResolved = @($ResolutionBoard | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count
    $secretTotal = @($ResolutionBoard).Count

    $p0Yes = @($P0Refined | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1Yes = @($P1Refined | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $gate = "BLOCKED_SECRET_RESOLUTION_REQUIRED"
    $allow = "false"
    $reason = "Secret resolution board generated; user_secret_resolved remains blank."

    if ($directReview -gt 0) {
        $gate = "BLOCKED_DIRECT_CONTRACT_REVIEW"
        $reason = "Direct smoke has review rows."
    }
    elseif ($secretTotal -eq 0) {
        $gate = "BLOCKED_MANUAL_ACCEPT_REQUIRED"
        $reason = "No remaining secret rows, but P0/P1 manual accept is still required."
    }
    elseif ($secretResolved -eq $secretTotal) {
        $gate = "BLOCKED_MANUAL_ACCEPT_REQUIRED_SECRET_RESOLVED"
        $reason = "Secret rows resolved, but P0/P1 manual accept is still required."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114 = $allow
            def_reason = $reason
            def_direct_ok = "$directOk"
            def_direct_review = "$directReview"
            def_secret_resolved = "$secretResolved"
            def_secret_total = "$secretTotal"
            def_p0_yes = "$p0Yes"
            def_p0_total = "$(@($P0Refined).Count)"
            def_p1_yes = "$p1Yes"
            def_p1_total = "$(@($P1Refined).Count)"
            def_next_allowed_phase = "v0114 sandbox patch candidate only after secret resolution and P0/P1 manual YES"
        }
    )
}

function def_BuildPrecheck {
    param(
        [string]$SecretResolutionCsv,
        [string]$P0Csv,
        [string]$P1Csv,
        [string]$Path
    )

    $code = @"
`$ErrorActionPreference = "Stop"

`$SecretResolutionCsv = "$SecretResolutionCsv"
`$P0Csv = "$P0Csv"
`$P1Csv = "$P1Csv"

function def_Load {
    param([string]`$Path)
    if (-not (Test-Path -LiteralPath `$Path)) { throw "Missing file: `$Path" }
    return @(Import-Csv -LiteralPath `$Path)
}

`$sec = def_Load `$SecretResolutionCsv
`$p0  = def_Load `$P0Csv
`$p1  = def_Load `$P1Csv

`$secPending = @(`$sec | Where-Object { ([string]`$_.def_user_secret_resolved).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p0Pending  = @(`$p0  | Where-Object { ([string]`$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p1Pending  = @(`$p1  | Where-Object { ([string]`$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114 Precheck after v0113C" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending : `$secPending / `$(`$sec.Count)" -ForegroundColor Yellow
Write-Host "P0 pending     : `$p0Pending / `$(`$p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending     : `$p1Pending / `$(`$p1.Count)" -ForegroundColor Yellow

if (`$secPending -gt 0) {
    throw "BLOCKED_SECRET_RESOLUTION_REQUIRED. Set def_user_secret_resolved=YES only after confirming env-only/rotation/false-positive."
}

if (`$p0Pending -gt 0 -or `$p1Pending -gt 0) {
    throw "BLOCKED_MANUAL_ACCEPT_REQUIRED. Edit P0/P1 refined CSV and set accepted rows to YES."
}

Write-Host "[OK] READY_FOR_V0114_SANDBOX_PATCH_CANDIDATE" -ForegroundColor Green
"@

    Set-Content -LiteralPath $Path -Value $code -Encoding UTF8
}

function def_BuildNextCommands {
    param(
        [string]$RunDir,
        [string]$SecretEdit,
        [string]$P0Edit,
        [string]$P1Edit,
        [string]$Precheck
    )

    $cmd = @"
# =============================================================================
# def VIA · Next Commands after v0113C
# =============================================================================

Start-Process "$RunDir\report\VIA_v0113C_SecretResolutionGate_Report.html"
Start-Process "$RunDir\output"
Start-Process "$RunDir\_user_edit_secret_resolution"

# Review secret resolution board
Import-Csv "$SecretEdit" | Format-Table -AutoSize

# Review readiness
Import-Csv "$RunDir\output\VIA_v0113C_ReadinessGate.csv" | Format-Table -AutoSize

# Open manual edit boards
Start-Process "$SecretEdit"
Start-Process "$P0Edit"
Start-Process "$P1Edit"

# After manual review/edit:
pwsh -NoProfile -ExecutionPolicy Bypass -File "$Precheck"

# Only after precheck returns OK:
# v0114 may generate sandbox patch candidate.
# Still no canonical overwrite.
"@

    $path = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113C.ps1"
    Set-Content -LiteralPath $path -Value $cmd -Encoding UTF8
    return $path
}

function def_Table {
    param([array]$Rows,[string[]]$Cols,[int]$Max=120)

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append("<table><thead><tr>")
    foreach ($c in $Cols) { [void]$sb.Append("<th>$(def_Html $c)</th>") }
    [void]$sb.Append("</tr></thead><tbody>")

    foreach ($r in (@($Rows | Select-Object -First $Max))) {
        [void]$sb.Append("<tr>")
        foreach ($c in $Cols) {
            $v = def_GetProp $r $c
            if ($v.Length -gt 260) { $v = $v.Substring(0,260) + "..." }
            [void]$sb.Append("<td>$(def_Html $v)</td>")
        }
        [void]$sb.Append("</tr>")
    }

    [void]$sb.Append("</tbody></table>")
    return $sb.ToString()
}

function def_WriteReport {
    param(
        $Summary,
        [array]$Readiness,
        [array]$ResolutionBoard,
        [array]$EnvAudit,
        [array]$DirectBoard,
        [array]$PS15Rows,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114",$Summary.AllowV0114),
        @("Direct OK",$Summary.DirectOk),
        @("Secret Rows",$Summary.SecretRows),
        @("Secret Resolved",$Summary.SecretResolved),
        @("P0 Rows",$Summary.P0Rows),
        @("P1 Rows",$Summary.P1Rows)
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0113C Secret Resolution Gate</title>
<style>
:root{--bg:#f7f6f2;--panel:#fffefa;--ink:#24231f;--mut:#706d64;--line:#dedbd2;--red:#c96b5a;--gn:#5a9e6f;--am:#c4943a;--bl:#4c72b0;--cyan:#6fa8ad}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at 10% 5%,rgba(111,168,173,.14),transparent 24%),linear-gradient(135deg,rgba(255,255,255,.5),rgba(230,226,216,.2)),var(--bg);color:var(--ink);font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:8.5px;line-height:1.32}
.wrap{max-width:1780px;margin:0 auto;padding:15px}
h1{font-size:14.4px;margin:0 0 4px;font-weight:650}
.sub{font-size:8.2px;color:var(--mut);margin-bottom:10px}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}
.card{background:rgba(255,254,250,.93);border:1px solid var(--line);border-radius:9px;padding:6px 7px;min-height:41px}
.k{font-size:7.6px;color:var(--mut)}
.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;align-items:stretch}
.sec{background:rgba(255,254,250,.9);border:1px solid var(--line);border-radius:11px;padding:8px;min-height:214px;overflow:hidden}
.wide{grid-column:1/-1}
h2{font-size:9.5px;margin:0 0 6px;font-weight:650}
.note{font-size:8.1px;color:var(--mut);margin:0 0 7px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.85px}
th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:var(--mut)}
.footer{margin-top:11px;color:var(--mut);font-size:8px}
</style>
</head>
<body>
<div class="wrap">
<h1>def VIA v0113C Secret Resolution Gate</h1>
<div class="sub">Resolve remaining secret blockers · env presence only · no value print · no auto accept</div>
<div class="cards">$cards</div>

<div class="sec wide">
<h2>def Executive Judgment</h2>
<div class="note">
v0113C 不會解除任何 gate。它只產生 secret resolution board：ticker_tokens 可視為假陽性候選；fred_api_key_env 可視為環境變數名稱候選；FRED_API_KEY 若曾貼過真值，應外部旋轉。所有欄位仍需人工填 YES。
</div>
<div>
<span class="tag">No Secret Print</span>
<span class="tag">Env Presence Only</span>
<span class="tag">No Auto YES</span>
<span class="tag">No Source Mutation</span>
<span class="tag">No Canonical Merge</span>
</div>
</div>

<div class="grid">
<div class="sec wide"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_v0114","def_reason","def_direct_ok","def_direct_review","def_secret_resolved","def_secret_total","def_p0_yes","def_p0_total","def_p1_yes","def_p1_total","def_next_allowed_phase") 20)</div>
<div class="sec wide"><h2>def Secret Resolution Board</h2>$(def_Table $ResolutionBoard @("def_priority","def_normalized_key","def_secret_class","def_current_block","def_user_secret_resolved","def_suggested_resolution","def_release_condition","def_selected_safe_canonical_value","def_env_exists_presence_only","def_env_value_length_only","def_value_printed","def_rotate_if_raw_was_real","def_reason") 80)</div>
<div class="sec wide"><h2>def Environment Audit Presence Only</h2>$(def_Table $EnvAudit @("def_env_name","def_exists","def_value_length","def_value_printed","def_policy") 20)</div>
<div class="sec wide"><h2>def Direct Smoke Board</h2>$(def_Table $DirectBoard @("def_project","def_direct_status","def_ready_for_v0114_candidate","def_review_reason","def_source_mutation","def_canonical_merge","def_db_write","def_contract_json") 40)</div>
<div class="sec wide"><h2>def 15 PowerShell Accelerators</h2>$(def_Table $PS15Rows @("def_no","def_accelerator") 20)</div>
</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0113B source: $(def_Html $Summary.LatestV0113B)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
User edit secret resolution: $(def_Html $Summary.UserEditDir)<br/>
Report: $(def_Html $ReportPath)
</div>
</div>
</body>
</html>
"@

    Set-Content -LiteralPath $ReportPath -Value $html -Encoding UTF8
}

function def_Main {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · v0113C SECRET RESOLUTION GATE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_Progress 1 9 "Find latest v0113B output"
    $latest = def_GetLatestV0113B
    $latestOut = Join-Path $latest "output"
    $latestUserEdit = Join-Path $latest "_user_edit_refined"
    def_Log "OK" "Latest v0113B: $latest" Green

    def_Progress 2 9 "Load v0113B boards"
    $directBoard = def_LoadCsv (Join-Path $latestOut "VIA_v0113B_DirectSmokeBoard_From_v0113A.csv")
    $secretTriage = def_LoadCsv (Join-Path $latestOut "VIA_v0113B_SecretTriage.csv")
    $p0Refined = def_LoadCsv (Join-Path $latestUserEdit "VIA_v0113B_USER_EDIT_P0_RefinedManualGate.csv")
    $p1Refined = def_LoadCsv (Join-Path $latestUserEdit "VIA_v0113B_USER_EDIT_P1_RefinedManualGate.csv")
    def_Log "OK" "Loaded Direct=$(@($directBoard).Count), Secret=$(@($secretTriage).Count), P0=$(@($p0Refined).Count), P1=$(@($p1Refined).Count)" Green

    def_Progress 3 9 "Run env presence-only audit"
    $envAudit = def_GetEnvPresenceOnly -Names @("FRED_API_KEY","VDF_FRED_API_KEY","VIA_FRED_API_KEY")

    def_Progress 4 9 "Build secret resolution board"
    $resolutionBoard = def_BuildResolutionBoard -SecretTriage $secretTriage -EnvAudit $envAudit

    def_Progress 5 9 "Build readiness gate"
    $readiness = def_BuildReadiness -ResolutionBoard $resolutionBoard -P0Refined $p0Refined -P1Refined $p1Refined -DirectBoard $directBoard

    def_Progress 6 9 "Write manual edit CSVs"
    $secretEdit = Join-Path $def_USER_EDIT_DIR "VIA_v0113C_USER_EDIT_SecretResolution.csv"
    $p0Edit = Join-Path $def_USER_EDIT_DIR "VIA_v0113C_USER_EDIT_P0_RefinedManualGate.csv"
    $p1Edit = Join-Path $def_USER_EDIT_DIR "VIA_v0113C_USER_EDIT_P1_RefinedManualGate.csv"

    def_WriteCsv $resolutionBoard $secretEdit
    def_WriteCsv $p0Refined $p0Edit
    def_WriteCsv $p1Refined $p1Edit

    def_Progress 7 9 "Build precheck and next commands"
    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114-Precheck-After-v0113C.ps1"
    def_BuildPrecheck -SecretResolutionCsv $secretEdit -P0Csv $p0Edit -P1Csv $p1Edit -Path $precheck

    $nextCmd = def_BuildNextCommands -RunDir $def_RUN_DIR -SecretEdit $secretEdit -P0Edit $p0Edit -P1Edit $p1Edit -Precheck $precheck

    def_Progress 8 9 "Write CSV/JSON outputs"
    $ps15Rows = New-Object System.Collections.ArrayList
    $accels = @(
        "A01 latest-v0113B auto discovery",
        "A02 no BASE re-scan",
        "A03 remaining secret blockers isolated",
        "A04 environment presence-only audit",
        "A05 no secret value printed",
        "A06 ticker_tokens false-positive candidate",
        "A07 FRED env-only confirmation candidate",
        "A08 FRED raw-key rotation warning",
        "A09 manual secret resolution board",
        "A10 manual P0/P1 board copied forward",
        "A11 no automatic YES",
        "A12 no source mutation",
        "A13 no canonical merge",
        "A14 compact HTML report",
        "A15 no delete / no Stop-Process"
    )

    for ($i=0; $i -lt $accels.Count; $i++) {
        [void]$ps15Rows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $accels[$i]
        })
    }

    def_WriteCsv $resolutionBoard (Join-Path $def_OUTPUT_DIR "VIA_v0113C_SecretResolutionBoard.csv")
    def_WriteCsv $envAudit (Join-Path $def_OUTPUT_DIR "VIA_v0113C_EnvPresenceOnlyAudit.csv")
    def_WriteCsv $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113C_ReadinessGate.csv")
    def_WriteCsv $directBoard (Join-Path $def_OUTPUT_DIR "VIA_v0113C_DirectSmokeBoard_From_v0113B.csv")
    def_WriteCsv $ps15Rows (Join-Path $def_OUTPUT_DIR "VIA_v0113C_PS15_Accelerators.csv")

    def_WriteJson $resolutionBoard (Join-Path $def_OUTPUT_DIR "VIA_v0113C_SecretResolutionBoard.json")
    def_WriteJson $envAudit (Join-Path $def_OUTPUT_DIR "VIA_v0113C_EnvPresenceOnlyAudit.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113C_ReadinessGate.json")

    $directOk = @($directBoard | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $secretResolved = @($resolutionBoard | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0113C_SECRET_RESOLUTION_GATE_READY"
        RunId = $def_RUN_ID
        LatestV0113B = $latest
        GateStatus = def_GetProp $readiness[0] "def_gate_status"
        AllowV0114 = def_GetProp $readiness[0] "def_allow_v0114"
        DirectOk = "$directOk"
        SecretRows = "$(@($resolutionBoard).Count)"
        SecretResolved = "$secretResolved"
        P0Rows = "$(@($p0Refined).Count)"
        P1Rows = "$(@($p1Refined).Count)"
        SecretEditCsv = $secretEdit
        P0EditCsv = $p0Edit
        P1EditCsv = $p1Edit
        Precheck = $precheck
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
        UserEditDir = $def_USER_EDIT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; no canonical merge; no secret print; no auto accept."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0113C_SecretResolutionGate_Summary.json")

    def_Progress 9 9 "Write compact HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_v0113C_SecretResolutionGate_Report.html"
    def_WriteReport `
        -Summary $summary `
        -Readiness $readiness `
        -ResolutionBoard $resolutionBoard `
        -EnvAudit $envAudit `
        -DirectBoard $directBoard `
        -PS15Rows $ps15Rows `
        -ReportPath $report

    Write-Progress -Activity "VIA v0113C Secret Resolution Gate" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113C Secret Resolution Gate COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status          : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate            : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114     : $($summary.AllowV0114)" -ForegroundColor Yellow
    Write-Host "Direct OK       : $($summary.DirectOk)" -ForegroundColor Green
    Write-Host "Secret Rows     : $($summary.SecretRows)" -ForegroundColor Yellow
    Write-Host "Secret Resolved : $($summary.SecretResolved)" -ForegroundColor Yellow
    Write-Host "Secret Edit     : $secretEdit" -ForegroundColor Cyan
    Write-Host "P0 Edit         : $p0Edit" -ForegroundColor Cyan
    Write-Host "P1 Edit         : $p1Edit" -ForegroundColor Cyan
    Write-Host "Precheck        : $precheck" -ForegroundColor Cyan
    Write-Host "Report          : $report" -ForegroundColor Cyan
    Write-Host "Output          : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd         : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_HTML_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_USER_EDIT_DIR } catch {}
    }
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No delete. No Stop-Process. No source mutation executed." -ForegroundColor Yellow
    exit 1
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
