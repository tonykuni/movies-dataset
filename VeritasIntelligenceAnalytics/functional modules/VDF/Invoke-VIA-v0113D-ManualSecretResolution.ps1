param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113C_ROOT = "",
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0113D_MANUAL_SECRET_RESOLUTION" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0113D_manual_secret_resolution"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_USER_EDIT_DIR = Join-Path $def_RUN_DIR "_user_edit_after_secret_resolution"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0113D_ManualSecretResolution.log"

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
    Write-Progress -Activity "VIA v0113D Manual Secret Resolution" -Status $Status -PercentComplete $pct
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

function def_SetProp {
    param($Obj,[string]$Name,[string]$Value)
    if ($Obj.PSObject.Properties.Name -contains $Name) {
        $Obj.$Name = $Value
    } else {
        $Obj | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
    }
}

function def_LoadCsv {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "CSV missing: $Path"
    }
    return @(Import-Csv -LiteralPath $Path)
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

function def_GetLatestV0113C {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113C_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113C_ROOT) {
            return $def_PARAM_V0113C_ROOT
        }
        throw "Specified v0113C root does not exist: $def_PARAM_V0113C_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0113C_secret_resolution_gate"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113C output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0113C_SecretResolutionGate_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113C output found under: $root"
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

function def_AskYES {
    param(
        [string]$Title,
        [string]$Message
    )

    Write-Host ""
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host $Title -ForegroundColor Yellow
    Write-Host "--------------------------------------------------------------------------------" -ForegroundColor DarkYellow
    Write-Host $Message -ForegroundColor Gray
    Write-Host ""
    $ans = Read-Host "Type YES to confirm, anything else keeps it blocked"
    return (($ans.Trim().ToUpperInvariant()) -eq "YES")
}

function def_ResolveSecretsInteractively {
    param(
        [array]$SecretRows,
        [array]$EnvAudit
    )

    $out = New-Object System.Collections.ArrayList

    $fredEnv = @($EnvAudit | Where-Object { (def_GetProp $_ "def_env_name") -eq "FRED_API_KEY" } | Select-Object -First 1)
    $fredExists = "False"
    $fredLength = "0"
    if (@($fredEnv).Count -gt 0) {
        $fredExists = def_GetProp $fredEnv[0] "def_exists"
        $fredLength = def_GetProp $fredEnv[0] "def_value_length"
    }

    foreach ($r in $SecretRows) {
        $key = def_GetProp $r "def_normalized_key"
        $resolved = "NO"
        $resolutionNote = "Not confirmed by user."
        $safeCanonical = def_GetProp $r "def_selected_safe_canonical_value"

        if ($key -eq "ticker_tokens") {
            $ok = def_AskYES `
                -Title "SECRET CHECK 1/3 · ticker_tokens" `
                -Message "ticker_tokens 看起來是程式內部 token/list 變數，不是 credential。確認它不是密鑰、不是 API token、不是密碼，才輸入 YES。"

            if ($ok) {
                $resolved = "YES"
                $resolutionNote = "User confirmed ticker_tokens is a false-positive code/list token, not a secret."
                $safeCanonical = "FALSE_POSITIVE_CODE_TOKEN_LIST; NO_SECRET"
            }
        }
        elseif ($key -eq "fred_api_key_env") {
            $ok = def_AskYES `
                -Title "SECRET CHECK 2/3 · fred_api_key_env" `
                -Message "目前只確認 FRED_API_KEY 環境變數存在，不列印值。Env exists=$fredExists, length=$fredLength。確認 canonical 只能存 ENV:FRED_API_KEY，不存 raw key，才輸入 YES。"

            if ($ok) {
                $resolved = "YES"
                $resolutionNote = "User confirmed fred_api_key_env is env-name-only and raw value will not be stored."
                $safeCanonical = "ENV:FRED_API_KEY"
            }
        }
        elseif ($key -eq "FRED_API_KEY") {
            $ok = def_AskYES `
                -Title "SECRET CHECK 3/3 · FRED_API_KEY" `
                -Message "這筆曾被判為 raw-looking secret。若真值曾貼到任何檔案、log、聊天或報告，請先到 FRED 外部旋轉 key。確認已旋轉或確認從未外洩，且 canonical 只保留 ENV:FRED_API_KEY，才輸入 YES。"

            if ($ok) {
                $resolved = "YES"
                $resolutionNote = "User confirmed FRED key is rotated if exposed, or never exposed; canonical may only reference ENV:FRED_API_KEY."
                $safeCanonical = "ENV:FRED_API_KEY; RAW_VALUE_FORBIDDEN"
            }
        }

        def_SetProp $r "def_user_secret_resolved" $resolved
        def_SetProp $r "def_manual_resolution_note" $resolutionNote
        def_SetProp $r "def_selected_safe_canonical_value" $safeCanonical
        def_SetProp $r "def_resolution_timestamp" (Get-Date).ToString("s")
        def_SetProp $r "def_value_printed" "false"

        [void]$out.Add($r)
    }

    return @($out)
}

function def_BuildReadiness {
    param(
        [array]$SecretResolved,
        [array]$P0Rows,
        [array]$P1Rows,
        [array]$DirectRows
    )

    $directOk = @($DirectRows | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $directReview = @($DirectRows | Where-Object { (def_GetProp $_ "def_direct_status") -ne "DIRECT_CONTRACT_SMOKE_OK" }).Count

    $secYes = @($SecretResolved | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count
    $secTotal = @($SecretResolved).Count

    $p0Yes = @($P0Rows | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1Yes = @($P1Rows | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $gate = "BLOCKED_SECRET_RESOLUTION_REQUIRED"
    $allow = "false"
    $reason = "Secret rows still pending."

    if ($directReview -gt 0) {
        $gate = "BLOCKED_DIRECT_CONTRACT_REVIEW"
        $reason = "Direct smoke has review rows."
    }
    elseif ($secYes -eq $secTotal -and $secTotal -gt 0) {
        $gate = "BLOCKED_MANUAL_ACCEPT_REQUIRED_SECRET_RESOLVED"
        $reason = "Secret rows resolved. P0/P1 manual acceptance still pending."
    }
    elseif ($secTotal -eq 0) {
        $gate = "BLOCKED_MANUAL_ACCEPT_REQUIRED"
        $reason = "No secret rows. P0/P1 manual acceptance still pending."
    }

    if ($directReview -eq 0 -and $secYes -eq $secTotal -and $p0Yes -eq @($P0Rows).Count -and $p1Yes -eq @($P1Rows).Count) {
        $gate = "READY_FOR_V0114_SANDBOX_PATCH_CANDIDATE"
        $allow = "true"
        $reason = "Direct smoke OK, secret resolved, P0/P1 all manually accepted."
    }

    return @(
        [pscustomobject][ordered]@{
            def_gate_status = $gate
            def_allow_v0114 = $allow
            def_reason = $reason
            def_direct_ok = "$directOk"
            def_direct_review = "$directReview"
            def_secret_resolved = "$secYes"
            def_secret_total = "$secTotal"
            def_p0_yes = "$p0Yes"
            def_p0_total = "$(@($P0Rows).Count)"
            def_p1_yes = "$p1Yes"
            def_p1_total = "$(@($P1Rows).Count)"
            def_next_allowed_phase = "v0114 sandbox patch candidate only after all gates pass"
        }
    )
}

function def_BuildPrecheck {
    param(
        [string]$SecretCsv,
        [string]$P0Csv,
        [string]$P1Csv,
        [string]$Path
    )

    $code = @"
`$ErrorActionPreference = "Stop"

`$SecretCsv = "$SecretCsv"
`$P0Csv = "$P0Csv"
`$P1Csv = "$P1Csv"

function def_Load {
    param([string]`$Path)
    if (-not (Test-Path -LiteralPath `$Path)) { throw "Missing file: `$Path" }
    return @(Import-Csv -LiteralPath `$Path)
}

`$sec = def_Load `$SecretCsv
`$p0  = def_Load `$P0Csv
`$p1  = def_Load `$P1Csv

`$secPending = @(`$sec | Where-Object { ([string]`$_.def_user_secret_resolved).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p0Pending  = @(`$p0  | Where-Object { ([string]`$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
`$p1Pending  = @(`$p1  | Where-Object { ([string]`$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114 Precheck after v0113D" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending : `$secPending / `$(`$sec.Count)" -ForegroundColor Yellow
Write-Host "P0 pending     : `$p0Pending / `$(`$p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending     : `$p1Pending / `$(`$p1.Count)" -ForegroundColor Yellow

if (`$secPending -gt 0) {
    throw "BLOCKED_SECRET_RESOLUTION_REQUIRED. Resolve secret board first."
}

if (`$p0Pending -gt 0 -or `$p1Pending -gt 0) {
    throw "BLOCKED_MANUAL_ACCEPT_REQUIRED. Edit P0/P1 CSV and set accepted rows to YES."
}

Write-Host "[OK] READY_FOR_V0114_SANDBOX_PATCH_CANDIDATE" -ForegroundColor Green
"@

    Set-Content -LiteralPath $Path -Value $code -Encoding UTF8
}

function def_BuildNextCommands {
    param(
        [string]$RunDir,
        [string]$SecretCsv,
        [string]$P0Csv,
        [string]$P1Csv,
        [string]$Precheck
    )

    $cmd = @"
# =============================================================================
# def VIA · Next Commands after v0113D
# =============================================================================

Start-Process "$RunDir\report\VIA_v0113D_ManualSecretResolution_Report.html"
Start-Process "$RunDir\output"
Start-Process "$RunDir\_user_edit_after_secret_resolution"

Import-Csv "$RunDir\output\VIA_v0113D_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "$SecretCsv" | Format-Table -AutoSize

# P0/P1 still manual:
Start-Process "$P0Csv"
Start-Process "$P1Csv"

# After manual P0/P1 edit:
pwsh -NoProfile -ExecutionPolicy Bypass -File "$Precheck"

# v0114 may only generate sandbox patch candidate, not overwrite canonical source.
"@

    $path = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113D.ps1"
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
        [array]$SecretResolved,
        [array]$EnvAudit,
        [array]$DirectBoard,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Gate",$Summary.GateStatus),
        @("Allow v0114",$Summary.AllowV0114),
        @("Direct OK",$Summary.DirectOk),
        @("Secret Resolved",$Summary.SecretResolved),
        @("Secret Rows",$Summary.SecretRows),
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
<title>VIA v0113D Manual Secret Resolution</title>
<style>
body{margin:0;background:#f7f6f2;color:#24231f;font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:8.5px;line-height:1.32}
.wrap{max-width:1780px;margin:0 auto;padding:15px}
h1{font-size:14.4px;margin:0 0 4px;font-weight:650}
.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}
.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}
.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}
.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}
h2{font-size:9.5px;margin:0 0 6px;font-weight:650}
.note{font-size:8.1px;color:#706d64;margin:0 0 7px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.85px}
th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}
.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}
.footer{margin-top:11px;color:#706d64;font-size:8px}
</style>
</head>
<body>
<div class="wrap">
<h1>def VIA v0113D Manual Secret Resolution</h1>
<div class="sub">Interactive confirmation · no secret print · P0/P1 still manual · no mutation</div>
<div class="cards">$cards</div>

<div class="sec">
<h2>def Executive Judgment</h2>
<div class="note">
v0113D 只解除你親自輸入 YES 的 secret row。FRED_API_KEY 的值沒有被列印。即使 Secret Resolved 全部通過，P0/P1 仍必須人工接受，才可進 v0114 sandbox patch candidate。
</div>
<span class="tag">No Secret Print</span>
<span class="tag">No Auto P0/P1</span>
<span class="tag">No Source Mutation</span>
<span class="tag">No Canonical Merge</span>
</div>

<div class="sec"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_v0114","def_reason","def_direct_ok","def_direct_review","def_secret_resolved","def_secret_total","def_p0_yes","def_p0_total","def_p1_yes","def_p1_total","def_next_allowed_phase") 20)</div>
<div class="sec"><h2>def Secret Resolution Result</h2>$(def_Table $SecretResolved @("def_priority","def_normalized_key","def_user_secret_resolved","def_suggested_resolution","def_selected_safe_canonical_value","def_value_printed","def_rotate_if_raw_was_real","def_manual_resolution_note","def_resolution_timestamp","def_reason") 20)</div>
<div class="sec"><h2>def Environment Audit Presence Only</h2>$(def_Table $EnvAudit @("def_env_name","def_exists","def_value_length","def_value_printed","def_policy") 20)</div>
<div class="sec"><h2>def Direct Smoke Board</h2>$(def_Table $DirectBoard @("def_project","def_direct_status","def_ready_for_v0114_candidate","def_review_reason","def_source_mutation","def_canonical_merge","def_db_write","def_contract_json") 40)</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0113C source: $(def_Html $Summary.LatestV0113C)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
User edit: $(def_Html $Summary.UserEditDir)<br/>
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
    Write-Host "def VIA · v0113D MANUAL SECRET RESOLUTION" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: No delete · No Stop-Process · No source mutation · No canonical merge · No secret print" -ForegroundColor Yellow

    def_Progress 1 8 "Find latest v0113C output"
    $latest = def_GetLatestV0113C
    $latestOut = Join-Path $latest "output"
    $latestEdit = Join-Path $latest "_user_edit_secret_resolution"
    def_Log "OK" "Latest v0113C: $latest" Green

    def_Progress 2 8 "Load v0113C boards"
    $directBoard = def_LoadCsv (Join-Path $latestOut "VIA_v0113C_DirectSmokeBoard_From_v0113B.csv")
    $secretRows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113C_USER_EDIT_SecretResolution.csv")
    $p0Rows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113C_USER_EDIT_P0_RefinedManualGate.csv")
    $p1Rows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113C_USER_EDIT_P1_RefinedManualGate.csv")
    def_Log "OK" "Loaded Direct=$(@($directBoard).Count), Secret=$(@($secretRows).Count), P0=$(@($p0Rows).Count), P1=$(@($p1Rows).Count)" Green

    def_Progress 3 8 "Run env presence-only audit"
    $envAudit = def_GetEnvPresenceOnly -Names @("FRED_API_KEY","VDF_FRED_API_KEY","VIA_FRED_API_KEY")

    def_Progress 4 8 "Interactive manual secret confirmation"
    $secretResolved = def_ResolveSecretsInteractively -SecretRows $secretRows -EnvAudit $envAudit

    def_Progress 5 8 "Build readiness gate"
    $readiness = def_BuildReadiness -SecretResolved $secretResolved -P0Rows $p0Rows -P1Rows $p1Rows -DirectRows $directBoard

    def_Progress 6 8 "Write updated edit boards"
    $secretCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113D_USER_EDIT_SecretResolution_RESOLVED.csv"
    $p0Csv = Join-Path $def_USER_EDIT_DIR "VIA_v0113D_USER_EDIT_P0_RefinedManualGate.csv"
    $p1Csv = Join-Path $def_USER_EDIT_DIR "VIA_v0113D_USER_EDIT_P1_RefinedManualGate.csv"

    def_WriteCsv $secretResolved $secretCsv
    def_WriteCsv $p0Rows $p0Csv
    def_WriteCsv $p1Rows $p1Csv

    def_Progress 7 8 "Write outputs and precheck"
    def_WriteCsv $secretResolved (Join-Path $def_OUTPUT_DIR "VIA_v0113D_SecretResolutionResult.csv")
    def_WriteCsv $envAudit (Join-Path $def_OUTPUT_DIR "VIA_v0113D_EnvPresenceOnlyAudit.csv")
    def_WriteCsv $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113D_ReadinessGate.csv")
    def_WriteCsv $directBoard (Join-Path $def_OUTPUT_DIR "VIA_v0113D_DirectSmokeBoard_From_v0113C.csv")

    def_WriteJson $secretResolved (Join-Path $def_OUTPUT_DIR "VIA_v0113D_SecretResolutionResult.json")
    def_WriteJson $envAudit (Join-Path $def_OUTPUT_DIR "VIA_v0113D_EnvPresenceOnlyAudit.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113D_ReadinessGate.json")

    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114-Precheck-After-v0113D.ps1"
    def_BuildPrecheck -SecretCsv $secretCsv -P0Csv $p0Csv -P1Csv $p1Csv -Path $precheck

    $nextCmd = def_BuildNextCommands -RunDir $def_RUN_DIR -SecretCsv $secretCsv -P0Csv $p0Csv -P1Csv $p1Csv -Precheck $precheck

    $directOk = @($directBoard | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $secretYes = @($secretResolved | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p0Yes = @($p0Rows | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1Yes = @($p1Rows | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0113D_MANUAL_SECRET_RESOLUTION_READY"
        RunId = $def_RUN_ID
        LatestV0113C = $latest
        GateStatus = def_GetProp $readiness[0] "def_gate_status"
        AllowV0114 = def_GetProp $readiness[0] "def_allow_v0114"
        DirectOk = "$directOk"
        SecretResolved = "$secretYes"
        SecretRows = "$(@($secretResolved).Count)"
        P0Yes = "$p0Yes"
        P0Rows = "$(@($p0Rows).Count)"
        P1Yes = "$p1Yes"
        P1Rows = "$(@($p1Rows).Count)"
        SecretCsv = $secretCsv
        P0Csv = $p0Csv
        P1Csv = $p1Csv
        Precheck = $precheck
        OutputDir = $def_OUTPUT_DIR
        ReportDir = $def_REPORT_DIR
        UserEditDir = $def_USER_EDIT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; no canonical merge; no secret print; P0/P1 still manual."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0113D_ManualSecretResolution_Summary.json")

    def_Progress 8 8 "Write HTML report"
    $report = Join-Path $def_REPORT_DIR "VIA_v0113D_ManualSecretResolution_Report.html"
    def_WriteReport `
        -Summary $summary `
        -Readiness $readiness `
        -SecretResolved $secretResolved `
        -EnvAudit $envAudit `
        -DirectBoard $directBoard `
        -ReportPath $report

    Write-Progress -Activity "VIA v0113D Manual Secret Resolution" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113D Manual Secret Resolution COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status          : $($summary.Status)" -ForegroundColor Green
    Write-Host "Gate            : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114     : $($summary.AllowV0114)" -ForegroundColor Yellow
    Write-Host "Direct OK       : $($summary.DirectOk)" -ForegroundColor Green
    Write-Host "Secret Resolved : $($summary.SecretResolved) / $($summary.SecretRows)" -ForegroundColor Yellow
    Write-Host "P0 YES          : $($summary.P0Yes) / $($summary.P0Rows)" -ForegroundColor Yellow
    Write-Host "P1 YES          : $($summary.P1Yes) / $($summary.P1Rows)" -ForegroundColor Yellow
    Write-Host "Secret CSV      : $secretCsv" -ForegroundColor Cyan
    Write-Host "P0 CSV          : $p0Csv" -ForegroundColor Cyan
    Write-Host "P1 CSV          : $p1Csv" -ForegroundColor Cyan
    Write-Host "Precheck        : $precheck" -ForegroundColor Cyan
    Write-Host "Report          : $report" -ForegroundColor Cyan
    Write-Host "NextCmd         : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
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
