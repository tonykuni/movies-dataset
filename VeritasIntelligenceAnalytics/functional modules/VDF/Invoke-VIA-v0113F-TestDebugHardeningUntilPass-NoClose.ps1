param(
    [string]$def_PARAM_VIA_ROOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [string]$def_PARAM_V0113D_ROOT = "",
    [int]$def_PARAM_MAX_ROUNDS = 3,
    [bool]$def_PARAM_AUTO_CLEAR_TICKER_TOKENS_FALSE_POSITIVE = $true,
    [bool]$def_PARAM_OPEN_REPORT = $true
)

$ErrorActionPreference = "Stop"

$def_RUN_ID = "RUN_{0}_VIA_v0113F_TEST_DEBUG_HARDENING" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$def_VDF = Join-Path $def_PARAM_VIA_ROOT "functional modules\VDF"
$def_RUN_ROOT = Join-Path $def_VDF "_integration_v0113F_test_debug_hardening"
$def_RUN_DIR = Join-Path $def_RUN_ROOT $def_RUN_ID
$def_OUTPUT_DIR = Join-Path $def_RUN_DIR "output"
$def_REPORT_DIR = Join-Path $def_RUN_DIR "report"
$def_USER_EDIT_DIR = Join-Path $def_RUN_DIR "_user_edit_after_secret_gate_cleared"
$def_UI_CONTRACT_DIR = Join-Path $def_RUN_DIR "_unified_html_ui_secret_parameter_contract"
$def_LOG_DIR = Join-Path $def_RUN_DIR "logs"
$def_LOG = Join-Path $def_LOG_DIR "VIA_v0113F_TestDebugHardening.log"

$def_ACCELERATORS = @(
    "A01 latest-v0113D auto discovery",
    "A02 same-session NoClose execution",
    "A03 no child process required",
    "A04 no BASE re-scan",
    "A05 direct smoke reuse",
    "A06 deterministic ticker_tokens false-positive resolution",
    "A07 FRED runtime password parameter contract",
    "A08 no secret value print",
    "A09 forbidden sink scanner",
    "A10 UI prototype scanner",
    "A11 precheck expected-block validation",
    "A12 P0/P1 no-auto-YES guard",
    "A13 PowerShell AST syntax gate",
    "A14 three-round convergence test",
    "A15 compact HTML matrix report"
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

foreach ($d in @($def_RUN_DIR,$def_OUTPUT_DIR,$def_REPORT_DIR,$def_USER_EDIT_DIR,$def_UI_CONTRACT_DIR,$def_LOG_DIR)) {
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
    Write-Progress -Activity "VIA v0113F Test Debug Hardening Until Pass" -Status $Status -PercentComplete $pct
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

function def_GetLatestV0113D {
    if (-not [string]::IsNullOrWhiteSpace($def_PARAM_V0113D_ROOT)) {
        if (Test-Path -LiteralPath $def_PARAM_V0113D_ROOT) {
            return $def_PARAM_V0113D_ROOT
        }
        throw "Specified v0113D root does not exist: $def_PARAM_V0113D_ROOT"
    }

    $root = Join-Path $def_VDF "_integration_v0113D_manual_secret_resolution"
    if (-not (Test-Path -LiteralPath $root)) {
        throw "v0113D output root not found: $root"
    }

    $candidates = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.FullName "output\VIA_v0113D_ManualSecretResolution_Summary.json")
        } |
        Sort-Object LastWriteTime -Descending

    if (-not $candidates -or @($candidates).Count -eq 0) {
        throw "No v0113D output found under: $root"
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

function def_ApplySecretPolicy {
    param([array]$SecretRows)

    $out = New-Object System.Collections.ArrayList

    foreach ($r in $SecretRows) {
        $key = def_GetProp $r "def_normalized_key"

        if ($key -eq "ticker_tokens") {
            if ($def_PARAM_AUTO_CLEAR_TICKER_TOKENS_FALSE_POSITIVE) {
                def_SetProp $r "def_user_secret_resolved" "YES"
                def_SetProp $r "def_selected_safe_canonical_value" "FALSE_POSITIVE_CODE_TOKEN_LIST; NO_SECRET; DO_NOT_TREAT_AS_CREDENTIAL"
                def_SetProp $r "def_manual_resolution_note" "Resolved by v0113F deterministic classifier: ticker_tokens is an internal code/list token, not a credential."
            } else {
                def_SetProp $r "def_user_secret_resolved" "NO"
                def_SetProp $r "def_manual_resolution_note" "ticker_tokens not auto-cleared by parameter."
            }
            def_SetProp $r "def_ui_secret_policy" "not_applicable_false_positive"
            def_SetProp $r "def_value_printed" "false"
            def_SetProp $r "def_resolution_timestamp" (Get-Date).ToString("s")
        }
        elseif ($key -eq "FRED_API_KEY") {
            def_SetProp $r "def_user_secret_resolved" "YES"
            def_SetProp $r "def_selected_safe_canonical_value" "UI_RUNTIME_SECRET_PARAMETER:FRED_API_KEY; INPUT_TYPE=password; RAW_VALUE_FORBIDDEN; NO_LOG; NO_CSV; NO_JSON; NO_LOCALSTORAGE"
            def_SetProp $r "def_manual_resolution_note" "Resolved by user policy: FRED_API_KEY will be entered as Unified HTML UI runtime password parameter. Canonical stores policy only, never raw value."
            def_SetProp $r "def_ui_secret_policy" "unified_html_ui_runtime_password_parameter"
            def_SetProp $r "def_value_printed" "false"
            def_SetProp $r "def_rotate_if_raw_was_real" "true"
            def_SetProp $r "def_resolution_timestamp" (Get-Date).ToString("s")
        }
        elseif ($key -eq "fred_api_key_env") {
            def_SetProp $r "def_user_secret_resolved" "YES"
            def_SetProp $r "def_selected_safe_canonical_value" "UI_PARAMETER_NAME:FRED_API_KEY; OPTIONAL_ENV_FALLBACK_NAME_ONLY; RAW_VALUE_FORBIDDEN"
            def_SetProp $r "def_manual_resolution_note" "Resolved by user policy: UI parameter name is FRED_API_KEY. Env fallback may exist by name only; raw value cannot be printed or persisted."
            def_SetProp $r "def_ui_secret_policy" "ui_parameter_name_with_optional_env_fallback"
            def_SetProp $r "def_value_printed" "false"
            def_SetProp $r "def_resolution_timestamp" (Get-Date).ToString("s")
        }

        [void]$out.Add($r)
    }

    return @($out)
}

function def_BuildUISecretContract {
    param([string]$PathJson,[string]$PathPs1,[string]$PathHtml)

    $contract = [ordered]@{
        schema_version = "VIA_UnifiedHtmlUI_SecretParameterContract_v0113F"
        generated_at = (Get-Date).ToString("s")
        provider = "FRED"
        parameter_name = "FRED_API_KEY"
        ui_field = [ordered]@{
            element_id = "via_secret_fred_api_key"
            input_type = "password"
            autocomplete = "off"
            required = $true
            placeholder = "Enter FRED API key for this runtime session"
        }
        allowed_flow = @(
            "User enters key in password field",
            "UI keeps value in runtime memory only",
            "UI passes value to fetch layer in memory",
            "Fetch layer uses key for request",
            "Response may be cached, key may not be cached"
        )
        forbidden_sinks = @(
            "HTML static file",
            "CSV",
            "JSON",
            "log",
            "console output",
            "localStorage",
            "sessionStorage",
            "URL query string",
            "PowerShell transcript",
            "canonical registry",
            "screenshots/report tables"
        )
        display_policy = [ordered]@{
            show_value = $false
            show_exists = $true
            show_length = $true
            show_last4 = $false
            print_value = $false
        }
        canonical_policy = "Store only policy reference UI_RUNTIME_SECRET_PARAMETER:FRED_API_KEY, never raw value."
        security_note = "If raw FRED key was ever pasted into files, logs, reports, or chat, rotate externally before production use."
    }

    def_WriteJson $contract $PathJson 16

    $ps1 = @"
# =============================================================================
# def VIA · Runtime Secret Parameter Bridge Candidate · v0113F
# Policy: never log secret value, never write secret value to disk.
# =============================================================================

function New-VIAFredRuntimeSecretPayload {
    param(
        [Parameter(Mandatory=`$true)]
        [SecureString]`$FRED_API_KEY
    )

    return [pscustomobject][ordered]@{
        provider = "FRED"
        secret_parameter_name = "FRED_API_KEY"
        secret_parameter_secure = `$FRED_API_KEY
        value_printed = `$false
        persistence = "runtime_memory_only"
        forbidden_sinks = "csv,json,html,log,localStorage,sessionStorage,url_query,canonical_registry"
    }
}
"@

    Set-Content -LiteralPath $PathPs1 -Value $ps1 -Encoding UTF8

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA Unified HTML UI · FRED Runtime Secret Parameter</title>
<style>
body{margin:0;background:#f7f6f2;color:#24231f;font-family:"Microsoft JhengHei",Arial,sans-serif}
.wrap{max-width:920px;margin:0 auto;padding:24px}
.card{background:#fffefa;border:1px solid #dedbd2;border-radius:14px;padding:18px;margin:14px 0}
h1{font-size:20px;margin:0 0 8px}
p{font-size:13px;color:#666;line-height:1.6}
label{display:block;font-size:12px;color:#555;margin-bottom:6px}
input{width:100%;padding:12px;border:1px solid #d7d1c5;border-radius:10px;background:#fff;font-size:14px}
button{margin-top:10px;padding:10px 14px;border:1px solid #b9b2a5;border-radius:999px;background:#fffefa;cursor:pointer}
pre{white-space:pre-wrap;background:#f1eee6;border:1px solid #dedbd2;border-radius:10px;padding:12px;font-size:12px}
.warn{color:#9a4d3f;font-weight:650}
</style>
</head>
<body>
<div class="wrap">
<h1>VIA Unified HTML UI · FRED Runtime Secret Parameter</h1>
<p class="warn">Policy: password input only. No persistence. Never print raw key.</p>

<div class="card">
<label for="via_secret_fred_api_key">FRED_API_KEY · runtime only</label>
<input id="via_secret_fred_api_key" name="FRED_API_KEY" type="password" autocomplete="off" placeholder="Enter FRED API key for this runtime session only"/>
<button type="button" onclick="viaValidateFredKeyRuntimeOnly()">Validate Runtime Presence</button>
<button type="button" onclick="viaClearFredKey()">Clear Input</button>
</div>

<div class="card">
<h2>Runtime Status</h2>
<pre id="via_secret_status">No key loaded. Value is never printed.</pre>
</div>
</div>

<script>
(function(){
  "use strict";
  window.viaValidateFredKeyRuntimeOnly = function(){
    const el = document.getElementById("via_secret_fred_api_key");
    const v = el.value || "";
    const status = {
      provider: "FRED",
      parameter_name: "FRED_API_KEY",
      exists: v.length > 0,
      value_length: v.length,
      value_printed: false,
      persistence: "runtime_memory_only"
    };
    document.getElementById("via_secret_status").textContent = JSON.stringify(status, null, 2);
  };
  window.viaClearFredKey = function(){
    document.getElementById("via_secret_fred_api_key").value = "";
    document.getElementById("via_secret_status").textContent = "Cleared. Value was not stored.";
  };
})();
</script>
</body>
</html>
"@

    Set-Content -LiteralPath $PathHtml -Value $html -Encoding UTF8
}

function def_BuildReadiness {
    param([array]$SecretRows,[array]$P0Rows,[array]$P1Rows,[array]$DirectRows)

    $directOk = @($DirectRows | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $directReview = @($DirectRows | Where-Object { (def_GetProp $_ "def_direct_status") -ne "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $secYes = @($SecretRows | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count
    $secTotal = @($SecretRows).Count
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
        $reason = "Secret gate resolved. P0/P1 manual acceptance still pending."
    }

    if ($directReview -eq 0 -and $secYes -eq $secTotal -and $p0Yes -eq @($P0Rows).Count -and $p1Yes -eq @($P1Rows).Count) {
        $gate = "READY_FOR_V0114_SANDBOX_PATCH_CANDIDATE"
        $allow = "true"
        $reason = "Direct smoke OK, secret policy resolved, P0/P1 all manually accepted."
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
            def_next_allowed_phase = "v0114 sandbox patch candidate only after P0/P1 manual YES"
        }
    )
}

function def_BuildPrecheck {
    param([string]$SecretCsv,[string]$P0Csv,[string]$P1Csv,[string]$Path)

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
Write-Host "def VIA · v0114 Precheck after v0113F" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending : `$secPending / `$(`$sec.Count)" -ForegroundColor Yellow
Write-Host "P0 pending     : `$p0Pending / `$(`$p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending     : `$p1Pending / `$(`$p1.Count)" -ForegroundColor Yellow

if (`$secPending -gt 0) {
    throw "BLOCKED_SECRET_RESOLUTION_REQUIRED."
}

if (`$p0Pending -gt 0 -or `$p1Pending -gt 0) {
    throw "BLOCKED_MANUAL_ACCEPT_REQUIRED. Edit P0/P1 CSV and set accepted rows to YES."
}

Write-Host "[OK] READY_FOR_V0114_SANDBOX_PATCH_CANDIDATE" -ForegroundColor Green
"@

    Set-Content -LiteralPath $Path -Value $code -Encoding UTF8
}

function def_AddTest {
    param(
        [System.Collections.ArrayList]$Rows,
        [int]$Round,
        [string]$Name,
        [bool]$Pass,
        [string]$Message,
        [string]$Path = ""
    )

    $status = "PASS"
    $risk = "LOW"
    if (-not $Pass) {
        $status = "FAIL"
        $risk = "HIGH"
    }

    [void]$Rows.Add([pscustomobject][ordered]@{
        def_round = "Round$Round"
        def_name = $Name
        def_status = $status
        def_risk = $risk
        def_message = $Message
        def_path = $Path
    })
}

function def_TestArtifacts {
    param(
        [int]$Round,
        [array]$SecretRows,
        [array]$P0Rows,
        [array]$P1Rows,
        [array]$DirectRows,
        [array]$EnvAudit,
        [string]$UiJson,
        [string]$UiPs1,
        [string]$UiHtml,
        [string]$Precheck,
        [string]$Report
    )

    $rows = New-Object System.Collections.ArrayList

    $directOk = @($DirectRows | Where-Object { (def_GetProp $_ "def_direct_status") -eq "DIRECT_CONTRACT_SMOKE_OK" }).Count
    $secretYes = @($SecretRows | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p0Yes = @($P0Rows | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1Yes = @($P1Rows | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    def_AddTest $rows $Round "Direct smoke 3/3 OK" ($directOk -eq 3) "Direct OK=$directOk / 3"
    def_AddTest $rows $Round "Secret rows all resolved" ($secretYes -eq @($SecretRows).Count -and @($SecretRows).Count -eq 3) "Secret resolved=$secretYes / $(@($SecretRows).Count)"
    def_AddTest $rows $Round "P0 not auto accepted" ($p0Yes -eq 0 -and @($P0Rows).Count -eq 150) "P0 YES=$p0Yes / $(@($P0Rows).Count)"
    def_AddTest $rows $Round "P1 not auto accepted" ($p1Yes -eq 0 -and @($P1Rows).Count -eq 12) "P1 YES=$p1Yes / $(@($P1Rows).Count)"

    $fredRow = @($SecretRows | Where-Object { (def_GetProp $_ "def_normalized_key") -eq "FRED_API_KEY" } | Select-Object -First 1)
    $fredPolicyOk = $false
    if (@($fredRow).Count -gt 0) {
        $safe = def_GetProp $fredRow[0] "def_selected_safe_canonical_value"
        $fredPolicyOk = ($safe -match "UI_RUNTIME_SECRET_PARAMETER:FRED_API_KEY" -and $safe -match "RAW_VALUE_FORBIDDEN")
    }
    def_AddTest $rows $Round "FRED UI runtime secret policy" $fredPolicyOk "Canonical stores policy only, not raw value."

    $envNoPrint = @($EnvAudit | Where-Object { (def_GetProp $_ "def_value_printed") -ne "false" }).Count -eq 0
    def_AddTest $rows $Round "Env audit no value print" $envNoPrint "Presence/length only."

    def_AddTest $rows $Round "UI contract JSON exists" (Test-Path -LiteralPath $UiJson) "UI contract JSON exists." $UiJson
    def_AddTest $rows $Round "UI bridge PS1 exists" (Test-Path -LiteralPath $UiPs1) "Runtime bridge candidate exists." $UiPs1
    def_AddTest $rows $Round "UI prototype HTML exists" (Test-Path -LiteralPath $UiHtml) "Password-input prototype exists." $UiHtml

    $htmlText = ""
    if (Test-Path -LiteralPath $UiHtml) {
        $htmlText = Get-Content -LiteralPath $UiHtml -Raw -Encoding UTF8
    }

    $htmlPassword = ($htmlText -match 'type="password"' -and $htmlText -match 'autocomplete="off"')
    def_AddTest $rows $Round "UI password input guard" $htmlPassword "type=password and autocomplete=off."

    $badSink = ($htmlText -match "localStorage\.setItem|sessionStorage\.setItem|console\.log\s*\(\s*v\s*\)|location\.search|URLSearchParams")
    def_AddTest $rows $Round "UI forbidden sink scanner" (-not $badSink) "No obvious raw-value sink pattern."

    $psUnsafe = $false
    foreach ($p in @($UiPs1,$Precheck)) {
        if (Test-Path -LiteralPath $p) {
            $t = Get-Content -LiteralPath $p -Raw -Encoding UTF8
            if ($t -match "(?im)^\s*exit\s+\d+|Stop-Process|Remove-Item\s") {
                $psUnsafe = $true
            }
        }
    }
    def_AddTest $rows $Round "NoClose safety scanner" (-not $psUnsafe) "No exit / Stop-Process / Remove-Item in generated critical scripts."

    $syntaxOk = $true
    $syntaxMsg = "Parser OK."
    foreach ($p in @($UiPs1,$Precheck)) {
        if (Test-Path -LiteralPath $p) {
            $tokens = $null
            $errors = $null
            [System.Management.Automation.Language.Parser]::ParseFile($p, [ref]$tokens, [ref]$errors) | Out-Null
            if ($errors -and @($errors).Count -gt 0) {
                $syntaxOk = $false
                $syntaxMsg = "Parser errors in $p"
            }
        }
    }
    def_AddTest $rows $Round "PowerShell AST syntax gate" $syntaxOk $syntaxMsg

    $precheckExpected = $false
    $precheckMsg = ""
    if (Test-Path -LiteralPath $Precheck) {
        try {
            $null = & $Precheck 2>&1 | Out-String
            $precheckMsg = "Precheck returned OK; P0/P1 may already be accepted."
            $precheckExpected = $true
        } catch {
            $precheckMsg = $_.Exception.Message
            if ($precheckMsg -match "BLOCKED_MANUAL_ACCEPT_REQUIRED") {
                $precheckExpected = $true
                $precheckMsg = "Expected manual P0/P1 block; secret gate cleared."
            }
        }
    }
    def_AddTest $rows $Round "v0114 precheck expected result" $precheckExpected $precheckMsg $Precheck

    def_AddTest $rows $Round "Report path prepared" (-not [string]::IsNullOrWhiteSpace($Report)) "Report path allocated." $Report

    return @($rows)
}

function def_Table {
    param([array]$Rows,[string[]]$Cols,[int]$Max=220)

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
        [array]$Tests,
        [array]$SecretRows,
        [array]$EnvAudit,
        [array]$AccelRows,
        [string]$ReportPath
    )

    $cards = ""
    foreach ($x in @(
        @("Status",$Summary.Status),
        @("Final",$Summary.FinalGate),
        @("Test Pass",$Summary.TestPass),
        @("Test Fail",$Summary.TestFail),
        @("Secret",$Summary.SecretResolved),
        @("P0 YES",$Summary.P0Yes),
        @("P1 YES",$Summary.P1Yes),
        @("NoClose","true")
    )) {
        $cards += "<div class='card'><div class='k'>$(def_Html $x[0])</div><div class='v'>$(def_Html $x[1])</div></div>"
    }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VIA v0113F Test Debug Hardening</title>
<style>
body{margin:0;background:#f7f6f2;color:#24231f;font-family:"Microsoft JhengHei",Arial,sans-serif;font-size:8.4px;line-height:1.32}
.wrap{max-width:1800px;margin:0 auto;padding:15px}
h1{font-size:14.5px;margin:0 0 4px;font-weight:650}
.sub{font-size:8.2px;color:#706d64;margin-bottom:10px}
.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin-bottom:10px}
.card{background:#fffefa;border:1px solid #dedbd2;border-radius:9px;padding:6px 7px;min-height:41px}
.k{font-size:7.6px;color:#706d64}.v{font:650 10.6px Consolas,monospace;margin-top:4px;word-break:break-word}
.sec{background:#fffefa;border:1px solid #dedbd2;border-radius:11px;padding:8px;margin-bottom:9px;overflow:hidden}
h2{font-size:9.5px;margin:0 0 6px;font-weight:650}
.note{font-size:8.1px;color:#706d64;margin:0 0 7px}
table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:7.8px}
th,td{border-bottom:1px solid #ebe8df;padding:3px 4px;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
th{background:#f0eee8;text-align:left;font-weight:650;color:#555149}
.tag{display:inline-block;border:1px solid #dedbd2;border-radius:999px;padding:2px 6px;background:#fff;margin-right:4px;color:#706d64}
.footer{margin-top:11px;color:#706d64;font-size:8px}
</style>
</head>
<body>
<div class="wrap">
<h1>def VIA v0113F · Test Debug Hardening Until Pass</h1>
<div class="sub">15 accelerators · no stall · no close · no secret print · secret gate convergence</div>
<div class="cards">$cards</div>

<div class="sec">
<h2>def Executive Judgment</h2>
<div class="note">
v0113F 的完美狀態不是直接進 canonical，也不是 P0/P1 全 YES；正確完美狀態是 Secret Gate 清除、Direct Smoke OK、P0/P1 繼續維持人工接受門檻。
</div>
<span class="tag">NoClose</span>
<span class="tag">No Stop-Process</span>
<span class="tag">No Secret Print</span>
<span class="tag">No Source Mutation</span>
<span class="tag">P0/P1 Manual</span>
</div>

<div class="sec"><h2>def Readiness Gate</h2>$(def_Table $Readiness @("def_gate_status","def_allow_v0114","def_reason","def_direct_ok","def_direct_review","def_secret_resolved","def_secret_total","def_p0_yes","def_p0_total","def_p1_yes","def_p1_total","def_next_allowed_phase") 20)</div>
<div class="sec"><h2>def Three-Round Test Matrix</h2>$(def_Table $Tests @("def_round","def_name","def_status","def_risk","def_message","def_path") 300)</div>
<div class="sec"><h2>def Secret Resolution Final</h2>$(def_Table $SecretRows @("def_normalized_key","def_user_secret_resolved","def_selected_safe_canonical_value","def_ui_secret_policy","def_value_printed","def_rotate_if_raw_was_real","def_manual_resolution_note") 20)</div>
<div class="sec"><h2>def Env Presence Only</h2>$(def_Table $EnvAudit @("def_env_name","def_exists","def_value_length","def_value_printed","def_policy") 20)</div>
<div class="sec"><h2>def 15 Accelerators</h2>$(def_Table $AccelRows @("def_no","def_accelerator") 20)</div>

<div class="footer">
Run: $(def_Html $Summary.RunId)<br/>
Latest v0113D: $(def_Html $Summary.LatestV0113D)<br/>
Output: $(def_Html $Summary.OutputDir)<br/>
User edit: $(def_Html $Summary.UserEditDir)<br/>
UI contract: $(def_Html $Summary.UIContractDir)<br/>
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
    Write-Host "def VIA · v0113F TEST DEBUG HARDENING UNTIL PASS · NOCLOSE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Policy: No close. No exit. No secret print. No source mutation. No Stop-Process." -ForegroundColor Yellow

    def_Progress 1 10 "Find latest v0113D output"
    $latest = def_GetLatestV0113D
    $latestOut = Join-Path $latest "output"
    $latestEdit = Join-Path $latest "_user_edit_after_secret_resolution"
    def_Log "OK" "Latest v0113D: $latest" Green

    def_Progress 2 10 "Load v0113D boards"
    $directRows = def_LoadCsv (Join-Path $latestOut "VIA_v0113D_DirectSmokeBoard_From_v0113C.csv")
    $secretRows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113D_USER_EDIT_SecretResolution_RESOLVED.csv")
    $p0Rows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113D_USER_EDIT_P0_RefinedManualGate.csv")
    $p1Rows = def_LoadCsv (Join-Path $latestEdit "VIA_v0113D_USER_EDIT_P1_RefinedManualGate.csv")
    def_Log "OK" "Loaded Direct=$(@($directRows).Count), Secret=$(@($secretRows).Count), P0=$(@($p0Rows).Count), P1=$(@($p1Rows).Count)" Green

    def_Progress 3 10 "Apply secret policy repair"
    $secretFinal = def_ApplySecretPolicy -SecretRows $secretRows

    def_Progress 4 10 "Run env presence-only audit"
    $envAudit = def_GetEnvPresenceOnly -Names @("FRED_API_KEY","VDF_FRED_API_KEY","VIA_FRED_API_KEY")

    def_Progress 5 10 "Generate UI secret contract"
    $uiJson = Join-Path $def_UI_CONTRACT_DIR "VIA_UnifiedHtmlUI_SecretParameterContract_v0113F.json"
    $uiPs1  = Join-Path $def_UI_CONTRACT_DIR "VIA_RuntimeSecretParameterBridge_Candidate_v0113F.ps1"
    $uiHtml = Join-Path $def_UI_CONTRACT_DIR "VIA_UnifiedHtmlUI_FRED_RuntimeSecretParameter_v0113F.html"
    def_BuildUISecretContract -PathJson $uiJson -PathPs1 $uiPs1 -PathHtml $uiHtml

    def_Progress 6 10 "Build readiness gate"
    $readiness = def_BuildReadiness -SecretRows $secretFinal -P0Rows $p0Rows -P1Rows $p1Rows -DirectRows $directRows

    def_Progress 7 10 "Write candidate outputs"
    $secretCsv = Join-Path $def_USER_EDIT_DIR "VIA_v0113F_USER_EDIT_SecretResolution_FINAL.csv"
    $p0Csv = Join-Path $def_USER_EDIT_DIR "VIA_v0113F_USER_EDIT_P0_RefinedManualGate.csv"
    $p1Csv = Join-Path $def_USER_EDIT_DIR "VIA_v0113F_USER_EDIT_P1_RefinedManualGate.csv"
    $precheck = Join-Path $def_OUTPUT_DIR "Invoke-VIA-v0114-Precheck-After-v0113F.ps1"
    $report = Join-Path $def_REPORT_DIR "VIA_v0113F_TestDebugHardening_Report.html"

    def_WriteCsv $secretFinal $secretCsv
    def_WriteCsv $p0Rows $p0Csv
    def_WriteCsv $p1Rows $p1Csv
    def_WriteCsv $directRows (Join-Path $def_OUTPUT_DIR "VIA_v0113F_DirectSmokeBoard.csv")
    def_WriteCsv $envAudit (Join-Path $def_OUTPUT_DIR "VIA_v0113F_EnvPresenceOnlyAudit.csv")
    def_WriteCsv $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113F_ReadinessGate.csv")
    def_WriteCsv $secretFinal (Join-Path $def_OUTPUT_DIR "VIA_v0113F_SecretResolution_FINAL.csv")

    def_WriteJson $secretFinal (Join-Path $def_OUTPUT_DIR "VIA_v0113F_SecretResolution_FINAL.json")
    def_WriteJson $envAudit (Join-Path $def_OUTPUT_DIR "VIA_v0113F_EnvPresenceOnlyAudit.json")
    def_WriteJson $readiness (Join-Path $def_OUTPUT_DIR "VIA_v0113F_ReadinessGate.json")

    def_BuildPrecheck -SecretCsv $secretCsv -P0Csv $p0Csv -P1Csv $p1Csv -Path $precheck

    def_Progress 8 10 "Run three-round test/debug convergence"
    $allTests = New-Object System.Collections.ArrayList

    for ($round = 1; $round -le [Math]::Max(1,$def_PARAM_MAX_ROUNDS); $round++) {
        Write-Progress `
            -Activity "VIA v0113F Three-Round Convergence" `
            -Status ("Round {0}/{1}" -f $round,$def_PARAM_MAX_ROUNDS) `
            -PercentComplete ([int](($round / [Math]::Max(1,$def_PARAM_MAX_ROUNDS)) * 100))

        $tests = def_TestArtifacts `
            -Round $round `
            -SecretRows $secretFinal `
            -P0Rows $p0Rows `
            -P1Rows $p1Rows `
            -DirectRows $directRows `
            -EnvAudit $envAudit `
            -UiJson $uiJson `
            -UiPs1 $uiPs1 `
            -UiHtml $uiHtml `
            -Precheck $precheck `
            -Report $report

        foreach ($t in $tests) { [void]$allTests.Add($t) }

        $failCountRound = @($tests | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
        if ($failCountRound -eq 0) {
            def_Log "OK" "Round $round PASS. Convergence achieved." Green
            break
        } else {
            def_Log "WARN" "Round $round has $failCountRound FAIL rows. Rechecking next round." Yellow
        }
    }

    Write-Progress -Activity "VIA v0113F Three-Round Convergence" -Completed

    def_Progress 9 10 "Build accelerator matrix and final summary"
    $accelRows = New-Object System.Collections.ArrayList
    for ($i=0; $i -lt $def_ACCELERATORS.Count; $i++) {
        [void]$accelRows.Add([pscustomobject][ordered]@{
            def_no = "$($i+1)"
            def_accelerator = $def_ACCELERATORS[$i]
        })
    }

    $passCount = @($allTests | Where-Object { (def_GetProp $_ "def_status") -eq "PASS" }).Count
    $failCount = @($allTests | Where-Object { (def_GetProp $_ "def_status") -ne "PASS" }).Count
    $secretYes = @($secretFinal | Where-Object { (def_GetProp $_ "def_user_secret_resolved").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p0Yes = @($p0Rows | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count
    $p1Yes = @($p1Rows | Where-Object { (def_GetProp $_ "def_user_accept").Trim().ToUpperInvariant() -eq "YES" }).Count

    $finalGate = "PASS_SECRET_GATE_CLEARED_P0P1_MANUAL_REQUIRED"
    if ($failCount -gt 0) {
        $finalGate = "REVIEW_TEST_FAILURES"
    }

    def_WriteCsv $allTests (Join-Path $def_OUTPUT_DIR "VIA_v0113F_TestDebugMatrix.csv")
    def_WriteCsv $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113F_15Accelerators.csv")
    def_WriteJson $allTests (Join-Path $def_OUTPUT_DIR "VIA_v0113F_TestDebugMatrix.json")
    def_WriteJson $accelRows (Join-Path $def_OUTPUT_DIR "VIA_v0113F_15Accelerators.json")

    $nextCmd = Join-Path $def_OUTPUT_DIR "Invoke-VIA-NextCommands-After-v0113F.ps1"
    $next = @"
Start-Process "$report"
Start-Process "$def_OUTPUT_DIR"
Start-Process "$def_USER_EDIT_DIR"
Start-Process "$def_UI_CONTRACT_DIR"
Start-Process "$uiHtml"

Import-Csv "$def_OUTPUT_DIR\VIA_v0113F_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "$def_OUTPUT_DIR\VIA_v0113F_TestDebugMatrix.csv" | Format-Table -AutoSize

# P0/P1 still manual:
Start-Process "$p0Csv"
Start-Process "$p1Csv"

# After manual P0/P1 edit:
pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "$precheck"
"@
    Set-Content -LiteralPath $nextCmd -Value $next -Encoding UTF8

    $summary = [pscustomobject][ordered]@{
        Status = "VIA_v0113F_TEST_DEBUG_HARDENING_READY"
        RunId = $def_RUN_ID
        LatestV0113D = $latest
        FinalGate = $finalGate
        GateStatus = def_GetProp $readiness[0] "def_gate_status"
        AllowV0114 = def_GetProp $readiness[0] "def_allow_v0114"
        TestPass = "$passCount"
        TestFail = "$failCount"
        SecretResolved = "$secretYes / $(@($secretFinal).Count)"
        P0Yes = "$p0Yes / $(@($p0Rows).Count)"
        P1Yes = "$p1Yes / $(@($p1Rows).Count)"
        SecretCsv = $secretCsv
        P0Csv = $p0Csv
        P1Csv = $p1Csv
        UIContractJson = $uiJson
        UIBridgePs1 = $uiPs1
        UIPrototypeHtml = $uiHtml
        Precheck = $precheck
        Report = $report
        OutputDir = $def_OUTPUT_DIR
        UserEditDir = $def_USER_EDIT_DIR
        UIContractDir = $def_UI_CONTRACT_DIR
        NextCommands = $nextCmd
        Policy = "No delete; No Stop-Process; No source mutation; no canonical merge; no secret print; NoExit."
    }

    def_WriteJson $summary (Join-Path $def_OUTPUT_DIR "VIA_v0113F_TestDebugHardening_Summary.json")

    def_Progress 10 10 "Write compact HTML report"
    def_WriteReport `
        -Summary $summary `
        -Readiness $readiness `
        -Tests $allTests `
        -SecretRows $secretFinal `
        -EnvAudit $envAudit `
        -AccelRows $accelRows `
        -ReportPath $report

    Write-Progress -Activity "VIA v0113F Test Debug Hardening Until Pass" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA v0113F Test Debug Hardening Until Pass COMPLETE" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "Status          : $($summary.Status)" -ForegroundColor Green
    Write-Host "Final Gate      : $($summary.FinalGate)" -ForegroundColor Green
    Write-Host "Gate Status     : $($summary.GateStatus)" -ForegroundColor Yellow
    Write-Host "Allow v0114     : $($summary.AllowV0114)" -ForegroundColor Yellow
    Write-Host "Test PASS       : $($summary.TestPass)" -ForegroundColor Green
    Write-Host "Test FAIL       : $($summary.TestFail)" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })
    Write-Host "Secret Resolved : $($summary.SecretResolved)" -ForegroundColor Green
    Write-Host "P0 YES          : $($summary.P0Yes)" -ForegroundColor Yellow
    Write-Host "P1 YES          : $($summary.P1Yes)" -ForegroundColor Yellow
    Write-Host "Report          : $report" -ForegroundColor Cyan
    Write-Host "Output          : $def_OUTPUT_DIR" -ForegroundColor Cyan
    Write-Host "User Edit       : $def_USER_EDIT_DIR" -ForegroundColor Cyan
    Write-Host "UI Contract     : $def_UI_CONTRACT_DIR" -ForegroundColor Cyan
    Write-Host "NextCmd         : $nextCmd" -ForegroundColor Cyan

    if ($def_PARAM_OPEN_REPORT) {
        try { Start-Process -FilePath $report } catch {}
        try { Start-Process -FilePath $def_OUTPUT_DIR } catch {}
        try { Start-Process -FilePath $def_USER_EDIT_DIR } catch {}
        try { Start-Process -FilePath $def_UI_CONTRACT_DIR } catch {}
    }
}

try {
    def_Main
} catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No delete. No Stop-Process. No source mutation executed. No exit." -ForegroundColor Yellow
    return
} finally {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA · PowerShell remains open" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor DarkCyan
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
