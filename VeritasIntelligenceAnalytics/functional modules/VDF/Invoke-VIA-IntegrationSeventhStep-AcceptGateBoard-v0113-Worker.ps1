param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0112_ROOT = "",
    [bool]$def_PARAM_OPEN_HTML_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_seventhstep_accept_gate"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_GATE_DIR = Join-Path $def_RUN_DIR "_accept_gate_user_edit"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_SeventhStep_AcceptGateBoard_v0113.log"

$def_PS15_ACCELERATORS = @(
    "A01 latest-v0112 auto discovery",
    "A02 no BASE re-scan",
    "A03 direct smoke result reuse",
    "A04 P0 manual accept board",
    "A05 P1 path alias accept board",
    "A06 editable accept CSV generation",
    "A07 v0114 blocker script generation",
    "A08 no automatic acceptance",
    "A09 no source mutation",
    "A10 no canonical merge",
    "A11 no DB write",
    "A12 dynamic progress",
    "A13 compact one-page HTML report",
    "A14 CSV + JSON synchronized outputs",
    "A15 no delete / no Stop-Process"
)

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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_GATE_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA SeventhStep Accept Gate Board v0113" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0112 {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0112_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0112_ROOT) {
            return $def_PARAM_V0112_ROOT
        }
        throw "Specified v0112 root does not exist: $def_PARAM_V0112_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_sixthstep_direct_smoke_gate"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0112 output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_SixthStep_DirectContractSmokeGate_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0112 output found under: $root"
    }

    return $candidates[0].FullName
}

function def_BuildP0Board {
    param([array]$P0Template)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P0Template) {
        $family = def_GetProp $r "def_domain_family"
        $owner = def_GetProp $r "def_owner_engine"
        $key = def_GetProp $r "def_normalized_key"

        $risk = "HIGH"
        $recommend = "MANUAL_REVIEW_REQUIRED"

        if ($family -match "VISUAL") {
            $risk = "MEDIUM"
            $recommend = "CAN_DEFER_IF_NOT_SCHEMA_OR_SOURCE"
        } elseif ($family -match "ENGINE") {
            $risk = "HIGH"
            $recommend = "REVIEW_BEFORE_ENGINE_BRIDGE"
        } elseif ($family -match "MARKET|DATA_SOURCE|SCHEMA|GOVERNANCE") {
            $risk = "HIGH"
            $recommend = "MUST_ACCEPT_BEFORE_CANONICAL_PATCH"
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "P0"
            def_gate_type = "DOMAIN_ACCEPT_GATE"
            def_accept_status = "WAIT_USER_DECISION"
            def_recommendation = $recommend
            def_risk = $risk
            def_owner_engine = $owner
            def_domain_family = $family
            def_normalized_key = $key
            def_distinct_values = def_GetProp $r "def_distinct_values"
            def_user_accept = ""
            def_selected_canonical_value = ""
            def_reject_reason = ""
            def_next_allowed_phase = "v0114_only_after_YES"
            def_source_mutation = "false"
            def_sample_values = def_GetProp $r "def_sample_values"
        })
    }

    return @($rows)
}

function def_BuildP1Board {
    param([array]$P1Template)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $P1Template) {
        $alias = def_GetProp $r "def_alias"
        $path = def_GetProp $r "def_path_value"
        $status = def_GetProp $r "def_status"

        $risk = "MEDIUM"
        $recommend = "REVIEW_REQUIRED"

        if ($alias -match "ONEDRIVE|LEGACY") {
            $risk = "MEDIUM_HIGH"
            $recommend = "DEFER_OR_REJECT_UNLESS_NEEDED"
        } elseif ($status -match "ACCEPT_CANONICAL_ROOT") {
            $risk = "LOW"
            $recommend = "ACCEPT_RECOMMENDED"
        } elseif ($alias -match "DOWNLOADS|VDF|FUNCTIONAL|SUPPORTIVE") {
            $risk = "LOW_MEDIUM"
            $recommend = "ACCEPT_RECOMMENDED_AFTER_PATH_VISIBLE"
        } elseif ($alias -match "ENV|PYTHON") {
            $risk = "MEDIUM"
            $recommend = "REVIEW_ENV_BEFORE_ACCEPT"
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_priority = "P1"
            def_gate_type = "PATH_ALIAS_ACCEPT_GATE"
            def_accept_status = "WAIT_USER_DECISION"
            def_recommendation = $recommend
            def_risk = $risk
            def_alias = $alias
            def_path_value = $path
            def_status = $status
            def_user_accept = ""
            def_selected_alias_value = ""
            def_reject_reason = ""
            def_scope = "future_generated_scripts_only"
            def_mutate_existing_source = "false"
        })
    }

    return @($rows)
}

function def_BuildDirectSmokeBoard {
    param([array]$DirectSmoke)

    $rows = New-Object System.Collections.ArrayList

    foreach ($r in $DirectSmoke) {
        $status = def_GetProp $r "def_direct_status"
        $ready = "false"
        if ($status -eq "DIRECT_CONTRACT_SMOKE_OK") {
            $ready = "true"
        }

        [void]$rows.Add([pscustomobject][ordered]@{
            def_project = def_GetProp $r "def_project"
            def_direct_status = $status
            def_ready_for_v0114_candidate = $ready
            def_review_reason = def_GetProp $r "def_review_reason"
            def_source_mutation = def_GetProp $r "def_source_mutation"
            def_canonical_merge = def_GetProp $r "def_canonical_merge"
            def_db_write = def_GetProp $r "def_db_write"
            def_contract_json = def_GetProp $r "def_contract_json"
        })
    }

    return @($rows)
}

function def_BuildReadiness {
    param([array]$DirectBoard,[array]$P0Board,[array]$P1Board)

    $directOk = @($DirectBoard | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $directReview = @($DirectBoard | Where-Object { (def_GetProp $_ "def_direct_status") -ne "DIRECT_CONTRACT_SMOKE_OK" }).Count

    $p0Yes = @($P0Board | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1Yes = @($P1Board | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $p0Total = @($P0Board).Count
    $p1Total = @($P1Board).Count

    $gate = "BLOCKED_MANUAL_ACCEPT_REQUIRED"
    $allow = "false"
    $reason = "Direct smoke is OK, but P0/P1 manual accept fields are blank."

    if ($directReview -gt 0) {
        $gate = "BLOCKED_DIRECT_CONTRACT_REVIEW"
        $reason = "At least one direct contract smoke row requires review."
    } elseif ($p0Total -eq 0 -or $p1Total -eq 0) {
        $gate = "BLOCKED_EMPTY_ACCEPT_TEMPLATE"
        $reason = "Accept template missing P0 or P1 rows."
    } elseif ($p0Yes -eq $p0Total -and $p1Yes -eq $p1Total) {
        $gate = "READY_FOR_V0114_PATCH_CANDIDATE"
        $allow = "true"
        $reason = "All P0/P1 rows explicitly accepted."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114 = $allow
            def_reason = $reason
            def_direct_ok = "$directOk"
            def_direct_review = "$directReview"
            def_p0_yes = "$p0Yes"
            def_p0_total = "$p0Total"
            def_p1_yes = "$p1Yes"
            def_p1_total = "$p1Total"
            def_source_mutation = "false"
            def_canonical_merge = "false"
            def_next_allowed_phase = "v0114 sandbox patch candidate only"
        }
    )
}

function def_BuildUserEditGuide {
    param([string]$P0Csv,[string]$P1Csv,[string]$RunDir)

    $guide = @"
# VIA v0113 Accept Gate User Edit Guide

目前狀態：
- Direct Contract Smoke 已可通過。
- P0/P1 仍等待人工接受。
- 不可直接 canonical merge。
- 不可改 source。

你要手動編輯兩個 CSV：

1. P0：
$P0Csv

需要填：
- def_user_accept = YES 或 NO
- def_selected_canonical_value = 選定值
- def_reject_reason = 若 NO，填原因

2. P1：
$P1Csv

需要填：
- def_user_accept = YES 或 NO
- def_selected_alias_value = 選定 alias/path
- def_reject_reason = 若 NO，填原因

只有 P0 與 P1 全部 YES，v0114 才允許生成 sandbox patch candidate。
"@

    $path = Join-Path $RunDir "VIA_v0113_UserEditGuide.md"
    Set-Content -LiteralPath $path -Value $guide -Encoding UTF8
    return $path
}

function def_BuildV0114Blocker {
    param([string]$P0Csv,[string]$P1Csv,[string]$Path)

    $code = @"
`$ErrorActionPreference = "Stop"

`$P0Csv = "$P0Csv"
`$P1Csv = "$P1Csv"

function def_GetRows {
    param([string]`$Path)
    if (-not (Test-Path -LiteralPath `$Path)) {
        throw "Missing accept CSV: `$Path"
    }
    return @(Import-Csv -LiteralPath `$Path)
}

`$p0 = def_GetRows `$P0Csv
`$p1 = def_GetRows `$P1Csv

`$p0No = @(`$p0 | Where-Object { ([string]`$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p1No = @(`$p1 | Where-Object { ([string]`$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114 Precheck Blocker" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "P0 pending: `$p0No / `$(`$p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending: `$p1No / `$(`$p1.Count)" -ForegroundColor Yellow

if (`$p0No -gt 0 -or `$p1No -gt 0) {
    throw "BLOCKED_MANUAL_ACCEPT_REQUIRED. Edit P0/P1 accept CSV before v0114."
}

Write-Host "[OK] READY_FOR_V0114_PATCH_CANDIDATE" -ForegroundColor Green
"@

    Set-Content -LiteralPath $Path -Value $code -Encoding UTF8
}

function def_BuildNextCommands {
    param([string]$RunDir,[string]$P0Csv,[string]$P1Csv,[string]$Blocker)

    $cmd = @"
# =============================================================================
# def VIA · Next Commands after v0113
# =============================================================================

Start-Process "$RunDir\report\VIA_SeventhStep_AcceptGateBoard_Report_v0113.html"
Start-Process "$RunDir\output"
Start-Process "$RunDir\_accept_gate_user_edit"

# Review direct smoke board
Import-Csv "$RunDir\output\VIA_v0113_DirectSmokeBoard.csv" | Format-Table -AutoSize

# Review readiness
Import-Csv "$RunDir\output\VIA_v0113_ReadinessGate.csv" | Format-Table -AutoSize

# Edit these manually:
Start-Process "$P0Csv"
Start-Process "$P1Csv"

# After manual edit, run precheck:
pwsh -NoProfile -ExecutionPolicy Bypass -File "$Blocker"

# Only after blocker returns OK:
# v0114 can generate sandbox patch candidate.
# Still no canonical overwrite.
"@

    $path = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113.ps1"
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
        [array]$DirectBoard,
        [array]$P0Board,
        [array]$P1Board,
        [array]$PS15Rows,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114",$Summary.AllowV0114),
        @("Direct OK",$Summary.DirectOk),
        @("P0 Rows",$Summary.P0Rows),
        @("P1 Rows",$Summary.P1Rows),
        @("P0 YES",$Summary.P0Yes),
        @("P1 YES",$Summary.P1Yes)
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA SeventhStep Accept Gate Board v0113</title>
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
<h1>def VIA Integration SeventhStep Accept Gate Board · v0113</h1>
<div class="sub">Manual P0/P1 acceptance · v0114 blocker · no mutation · no canonical merge</div>
<div class="cards">$cards</div>

<div class="sec wide">
<h2>def Executive Judgment</h2>
<div class="note">
v0112 已證明 Direct Contract Smoke OK=3、Direct Review=0。v0113 不會自動接受 P0/P1，因為這些是 domain owner 與 path alias 的人工決策。現在狀態應保持 BLOCKED_MANUAL_ACCEPT_REQUIRED，直到你手動編輯 P0/P1 CSV，把必要列填成 YES。
</div>
<div>
<span class="tag">No Delete</span>
<span class="tag">No Stop-Process</span>
<span class="tag">No Source Mutation</span>
<span class="tag">No Canonical Merge</span>
<span class="tag">Manual Accept Required</span>
</div>
</div>

<div class="grid">
<div class="sec wide"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_v0114","def_reason","def_direct_ok","def_direct_review","def_p0_yes","def_p0_total","def_p1_yes","def_p1_total","def_next_allowed_phase") 20)</div>
<div class="sec wide"><h2>def Direct Smoke Board</h2>$(def_Table $DirectBoard @("def_project","def_direct_status","def_ready_for_v0114_candidate","def_review_reason","def_source_mutation","def_canonical_merge","def_db_write","def_contract_json") 80)</div>
<div class="sec wide"><h2>def P0 Manual Accept Board</h2>$(def_Table $P0Board @("def_priority","def_gate_type","def_accept_status","def_recommendation","def_risk","def_owner_engine","def_domain_family","def_normalized_key","def_distinct_values","def_user_accept","def_selected_canonical_value","def_reject_reason","def_next_allowed_phase","def_sample_values") 180)</div>
<div class="sec wide"><h2>def P1 Path Alias Accept Board</h2>$(def_Table $P1Board @("def_priority","def_gate_type","def_accept_status","def_recommendation","def_risk","def_alias","def_path_value","def_status","def_user_accept","def_selected_alias_value","def_reject_reason","def_scope") 80)</div>
<div class="sec wide"><h2>def 15 PowerShell Accelerators</h2>$(def_Table $PS15Rows @("def_no","def_accelerator") 20)</div>
</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0112 source: $(def_Html $Summary.LatestV0112)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
Gate edit folder: $(def_Html $Summary.GateDir)<br/>
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
    Write-Host "def VIA · SEVENTHSTEP ACCEPT GATE BOARD · v0113" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan

    def_Progress 1 9 "Find latest v0112 output"
    $latest = def_GetLatestV0112
    $latestOut = Join-Path $latest "output"
    def_Log "OK" "Latest v0112: $latest" Green

    def_Progress 2 9 "Load v0112 matrices"
    $summaryV0112 = def_LoadJson (Join-Path $latestOut "VIA_SixthStep_DirectContractSmokeGate_Summary.json")
    $directSmoke = def_LoadCsv (Join-Path $latestOut "VIA_v0112_DirectContractSmoke.csv")
    $p0Template = def_LoadCsv (Join-Path $latestOut "VIA_v0112_P0_AcceptGate_Template.csv")
    $p1Template = def_LoadCsv (Join-Path $latestOut "VIA_v0112_P1_PathAlias_AcceptGate_Template.csv")
    def_Log "OK" "Loaded DirectSmoke=$(@($directSmoke).Count), P0=$(@($p0Template).Count), P1=$(@($p1Template).Count)" Green

    def_Progress 3 9 "Build direct smoke board"
    $directBoard = def_BuildDirectSmokeBoard -DirectSmoke $directSmoke

    def_Progress 4 9 "Build P0 manual accept board"
    $p0Board = def_BuildP0Board -P0Template $p0Template

    def_Progress 5 9 "Build P1 path alias accept board"
    $p1Board = def_BuildP1Board -P1Template $p1Template

    def_Progress 6 9 "Build readiness gate"
    $readiness = def_BuildReadiness -DirectBoard $directBoard -P0Board $p0Board -P1Board $p1Board

    def_Progress 7 9 "Write edit templates and blocker"
    $p0EditCsv = Join-Path $def_GATE_DIR "VIA_v0113_USER_EDIT_P0_AcceptGate.csv"
    $p1EditCsv = Join-Path $def_GATE_DIR "VIA_v0113_USER_EDIT_P1_PathAlias_AcceptGate.csv"
    def_WriteCsv $p0Board $p0EditCsv
    def_WriteCsv $p1Board $p1EditCsv

    $userGuide = def_BuildUserEditGuide -P0Csv $p0EditCsv -P1Csv $p1EditCsv -RunDir $def_GATE_DIR
    $blocker = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114-PrecheckBlocker.ps1"
    def_BuildV0114Blocker -P0Csv $p0EditCsv -P1Csv $p1EditCsv -Path $blocker

    $nextCmd = def_BuildNextCommands -RunDir $def_RUN_DIR -P0Csv $p0EditCsv -P1Csv $p1EditCsv -Blocker $blocker

    def_Progress 8 9 "Write CSV/JSON outputs"
    $ps15Rows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_PS15_ACCELERATORS.Count; $i++) {
        [void]$ps15Rows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_PS15_ACCELERATORS[$i]
        })
    }

    def_WriteCsv $directBoard (Join-Path $def_OUTPUT_DIR "VIA_v0113_DirectSmokeBoard.csv")
    def_WriteCsv $p0Board (Join-Path $def_OUTPUT_DIR "VIA_v0113_P0_ManualAcceptBoard.csv")
    def_WriteCsv $p1Board (Join-Path $def_OUTPUT_DIR "VIA_v0113_P1_PathAliasAcceptBoard.csv")
    def_WriteCsv $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113_ReadinessGate.csv")
    def_WriteCsv $ps15Rows (Join-Path $def_OUTPUT_DIR "VIA_v0113_PS15_Accelerators.csv")

    def_WriteJson $directBoard (Join-Path $def_OUTPUT_DIR "VIA_v0113_DirectSmokeBoard.json")
    def_WriteJson $p0Board (Join-Path $def_OUTPUT_DIR "VIA_v0113_P0_ManualAcceptBoard.json")
    def_WriteJson $p1Board (Join-Path $def_OUTPUT_DIR "VIA_v0113_P1_PathAliasAcceptBoard.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113_ReadinessGate.json")

    $directOk = @($directBoard | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $p0Yes = @($p0Board | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1Yes = @($p1Board | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113_READY"
        RunId = $def_RUN_ID
        LatestV0112 = $latest
        GateStatus = def_GetProp $readiness[0] "def_gate_status"
        AllowV0114 = def_GetProp $readiness[0] "def_allow_v0114"
        DirectOk = "$directOk"
        P0Rows = "$(@($p0Board).Count)"
        P1Rows = "$(@($p1Board).Count)"
        P0Yes = "$p0Yes"
        P1Yes = "$p1Yes"
        P0EditCsv = $p0EditCsv
        P1EditCsv = $p1EditCsv
        UserGuide = $userGuide
        V0114Blocker = $blocker
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
        GateDir = $def_GATE_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; no canonical merge; manual accept gate only."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_SeventhStep_AcceptGateBoard_Summary.json")

    def_Progress 9 9 "Write compact one-page HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_SeventhStep_AcceptGateBoard_Report_v0113.html"
    def_WriteReport `
        -Summary $summary `
        -Readiness $readiness `
        -DirectBoard $directBoard `
        -P0Board $p0Board `
        -P1Board $p1Board `
        -PS15Rows $ps15Rows `
        -ReportPath $report

    Write-Progress -Activity "VIA SeventhStep Accept Gate Board v0113" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA SeventhStep Accept Gate Board v0113 COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status     : $($summary.Status)" -ForegroundColor Green
    Write-Host "v0112      : $latest" -ForegroundColor Gray
    Write-Host "Gate       : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114: $($summary.AllowV0114)" -ForegroundColor Yellow
    Write-Host "Direct OK  : $($summary.DirectOk)" -ForegroundColor Green
    Write-Host "P0 YES     : $($summary.P0Yes) / $($summary.P0Rows)" -ForegroundColor Yellow
    Write-Host "P1 YES     : $($summary.P1Yes) / $($summary.P1Rows)" -ForegroundColor Yellow
    Write-Host "P0 Edit    : $p0EditCsv" -ForegroundColor Cyan
    Write-Host "P1 Edit    : $p1EditCsv" -ForegroundColor Cyan
    Write-Host "Blocker    : $blocker" -ForegroundColor Cyan
    Write-Host "Report     : $report" -ForegroundColor Cyan
    Write-Host "Output     : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd    : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_HTML_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_GATE_DIR } catch {}
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
