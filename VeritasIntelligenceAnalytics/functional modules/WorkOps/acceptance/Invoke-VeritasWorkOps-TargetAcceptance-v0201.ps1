#requires -Version 7.0
[CmdletBinding()]
param(
    [ValidateSet("Offline","LiveRead","LiveReadAndDraft")]
    [string]$Mode = "Offline",

    [string]$InstallRoot = "$env:LOCALAPPDATA\VeritasWorkOps",

    [string]$ClientId = "",
    [string]$TenantId = "organizations",
    [string]$ItReference = "",

    [string]$DraftRecipient = "",

    [bool]$AllowNetworkInstall = $true,
    [bool]$OpenReport = $true
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExpectedPayloadSha256 = "2fdc81639d8998ef77dcdee6c46aca009d5b433e6cebb8e8cefe10497553f708"
$BundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Payload = Join-Path $BundleRoot "payload\VeritasWorkOps_v0200_RC.zip"
$RunRoot = Join-Path $env:USERPROFILE "Downloads\VeritasWorkOps_TargetAcceptance_Runs"
$RunId = "RUN_{0}_WORKOPS_TARGET_ACCEPTANCE_v0201" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$RunDir = Join-Path $RunRoot $RunId
$StageDir = Join-Path $RunDir "staging"
$ReportJson = Join-Path $RunDir "TARGET_ACCEPTANCE_SUMMARY.json"
$ReportCsv = Join-Path $RunDir "TARGET_ACCEPTANCE_CHECKS.csv"
$ReportHtml = Join-Path $RunDir "TARGET_ACCEPTANCE_REPORT.html"
$Transcript = Join-Path $RunDir "TARGET_ACCEPTANCE_TRANSCRIPT.txt"

New-Item -ItemType Directory -Force -Path $RunDir,$StageDir | Out-Null
Start-Transcript -Path $Transcript -Force | Out-Null

$Checks = [System.Collections.Generic.List[object]]::new()

function def_Banner([string]$Title) {
    Write-Host ""
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
    Write-Host ("def " + $Title) -ForegroundColor Cyan
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
}
function def_Progress([int]$Pct,[string]$Text) {
    Write-Progress -Activity "Veritas WorkOps Target Acceptance v0201" -Status $Text -PercentComplete $Pct
    Write-Host ("def [{0,3}%] {1}" -f $Pct,$Text) -ForegroundColor Cyan
}
function def_AddCheck(
    [string]$Lane,
    [string]$Check,
    [string]$Status,
    [string]$Detail = "",
    [string]$Evidence = ""
) {
    $Checks.Add([pscustomobject]@{
        Lane = $Lane
        Check = $Check
        Status = $Status
        Detail = $Detail
        Evidence = $Evidence
        Timestamp = (Get-Date).ToString("o")
    })
    $color = switch ($Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "SKIP" { "DarkGray" }
        default { "Red" }
    }
    Write-Host ("def {0,-5} | {1} | {2}" -f $Status,$Lane,$Check) -ForegroundColor $color
    if ($Detail) { Write-Host ("    " + $Detail) -ForegroundColor DarkGray }
}
function def-Sha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}
function def-RunPython([string]$Python,[string]$WorkingDirectory,[string[]]$Args) {
    Push-Location $WorkingDirectory
    try {
        $output = & $Python @Args 2>&1
        $exit = $LASTEXITCODE
        return [pscustomobject]@{
            ExitCode = $exit
            Output = ($output -join [Environment]::NewLine)
        }
    }
    finally { Pop-Location }
}
function def-RunPythonInteractive([string]$Python,[string]$WorkingDirectory,[string[]]$Args) {
    Push-Location $WorkingDirectory
    try {
        $lines = [System.Collections.Generic.List[string]]::new()
        & $Python @Args 2>&1 | ForEach-Object {
            $s = [string]$_
            $lines.Add($s)
            Write-Host $s
        }
        $exit = $LASTEXITCODE
        return [pscustomobject]@{
            ExitCode = $exit
            Output = ($lines -join [Environment]::NewLine)
        }
    }
    finally { Pop-Location }
}
function def-ParseJsonOutput([string]$Text) {
    try {
        $start = $Text.IndexOf("{")
        $end = $Text.LastIndexOf("}")
        if ($start -ge 0 -and $end -gt $start) {
            return ($Text.Substring($start, $end - $start + 1) | ConvertFrom-Json -Depth 100)
        }
    } catch {}
    return $null
}
function def-AstCheck([string]$Root) {
    $issues = [System.Collections.Generic.List[object]]::new()
    Get-ChildItem -LiteralPath $Root -Recurse -File -Filter *.ps1 -ErrorAction SilentlyContinue | ForEach-Object {
        $tokens = $null
        $errors = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$errors)
        foreach ($e in @($errors)) {
            $issues.Add([pscustomobject]@{
                File = $_.FullName
                Message = $e.Message
                StartLine = $e.Extent.StartLineNumber
                StartColumn = $e.Extent.StartColumnNumber
            })
        }
    }
    return $issues
}
function def-WriteReports([string]$FinalGate,[string]$AppRoot,[string]$Python) {
    $payloadHashForReport = ""
    if (Test-Path -LiteralPath $Payload) { $payloadHashForReport = def-Sha256 $Payload }
    $summary = [ordered]@{
        Version = "v0201"
        RunId = $RunId
        Mode = $Mode
        FinalGate = $FinalGate
        StartedAt = $script:StartedAt
        FinishedAt = (Get-Date).ToString("o")
        RunDir = $RunDir
        InstallRoot = $InstallRoot
        AppRoot = $AppRoot
        Python = $Python
        PayloadSha256 = $payloadHashForReport
        Checks = @($Checks)
        Security = [ordered]@{
            AutoSend = $false
            MailboxMoveDelete = $false
            LiveGraphRequiresExplicitMode = $true
            DraftRequiresExplicitMode = $true
            RestoreIsStagingOnly = $true
        }
    }
    $summary | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $ReportJson -Encoding UTF8
    @($Checks) | Export-Csv -LiteralPath $ReportCsv -NoTypeInformation -Encoding UTF8

    $rows = foreach ($c in $Checks) {
        $cls = $c.Status.ToLowerInvariant()
        "<tr><td>$([System.Net.WebUtility]::HtmlEncode($c.Lane))</td><td class='$cls'>$([System.Net.WebUtility]::HtmlEncode($c.Status))</td><td>$([System.Net.WebUtility]::HtmlEncode($c.Check))</td><td>$([System.Net.WebUtility]::HtmlEncode($c.Detail))</td><td>$([System.Net.WebUtility]::HtmlEncode($c.Evidence))</td></tr>"
    }
    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>Veritas WorkOps Target Acceptance v0201</title>
<style>
body{font-family:Segoe UI,Arial,sans-serif;background:#f5f7fa;color:#263238;margin:0}
main{max-width:1400px;margin:26px auto;padding:0 20px}
.card{background:white;border:1px solid #e2e8f0;border-radius:12px;padding:18px;margin-bottom:14px}
h1{margin:0 0 8px;font-size:24px}.muted{color:#718096}
.gate{font-size:30px;font-weight:700}
.pass{color:#287271}.warn{color:#c17b1b}.fail{color:#b23a48}.skip{color:#718096}
table{width:100%;border-collapse:collapse;background:white}
th,td{padding:9px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}
th{background:#f8fafc}
code{background:#f1f5f9;padding:2px 5px;border-radius:5px}
</style>
</head>
<body><main>
<div class="card">
<h1>Veritas WorkOps · Target Acceptance v0201</h1>
<div class="gate $($FinalGate.ToLowerInvariant())">$FinalGate</div>
<div class="muted">Mode: $Mode · Run: $RunId</div>
<div class="muted">Install: $InstallRoot</div>
</div>
<div class="card">
<table>
<thead><tr><th>Lane</th><th>Gate</th><th>Check</th><th>Detail</th><th>Evidence</th></tr></thead>
<tbody>
$($rows -join "`n")
</tbody>
</table>
</div>
<div class="card muted">
Policy: localhost only · no auto-send · no mailbox move/delete · live M365 requires explicit mode.
</div>
</main></body></html>
"@
    $html | Set-Content -LiteralPath $ReportHtml -Encoding UTF8
}

$script:StartedAt = (Get-Date).ToString("o")
$AppRoot = ""
$Vpy = ""

try {
    def_Banner "VERITAS WORKOPS · TARGET ACCEPTANCE · v0201"
    Write-Host "def Mode       : $Mode"
    Write-Host "def RunDir     : $RunDir"
    Write-Host "def InstallRoot: $InstallRoot"

    def_Progress 5 "Lane 01 · Payload integrity"
    if (-not (Test-Path -LiteralPath $Payload)) {
        throw "RC payload not found: $Payload"
    }
    $actualSha = def-Sha256 $Payload
    if ($actualSha -ne $ExpectedPayloadSha256) {
        def_AddCheck "L01" "RC ZIP SHA-256" "FAIL" "Expected $ExpectedPayloadSha256; got $actualSha" $Payload
        throw "RC payload hash mismatch."
    }
    def_AddCheck "L01" "RC ZIP SHA-256" "PASS" $actualSha $Payload

    def_Progress 10 "Lane 01 · Extract isolated staging copy"
    $ExtractRoot = Join-Path $StageDir "rc"
    if (Test-Path $ExtractRoot) { throw "Run-local staging unexpectedly exists: $ExtractRoot" }
    Expand-Archive -LiteralPath $Payload -DestinationPath $ExtractRoot
    $PackageRoot = Get-ChildItem -LiteralPath $ExtractRoot -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName "installer\Install-VeritasWorkOps.ps1") } |
        Select-Object -First 1 -ExpandProperty FullName
    if (-not $PackageRoot) { throw "Extracted RC root not found." }
    def_AddCheck "L01" "Run-local extraction" "PASS" $PackageRoot $ExtractRoot

    def_Progress 15 "Lane 01 · PowerShell AST"
    $astIssues = @(def-AstCheck $PackageRoot)
    $selfIssues = @(def-AstCheck $BundleRoot)
    $allAst = @($astIssues + $selfIssues)
    if ($allAst.Count -gt 0) {
        $astFile = Join-Path $RunDir "POWERSHELL_AST_ERRORS.json"
        $allAst | ConvertTo-Json -Depth 20 | Set-Content $astFile -Encoding UTF8
        def_AddCheck "L01" "PowerShell AST" "FAIL" "$($allAst.Count) parser error(s)" $astFile
        throw "PowerShell AST validation failed."
    }
    def_AddCheck "L01" "PowerShell AST" "PASS" "All package and acceptance PS1 files parse successfully."

    def_Progress 25 "Lane 02 · Install / upgrade"
    $Installer = Join-Path $PackageRoot "installer\Install-VeritasWorkOps.ps1"
    if ($AllowNetworkInstall) {
        & $Installer -InstallRoot $InstallRoot
    } else {
        & $Installer -InstallRoot $InstallRoot -SkipDependencies
    }
    if ($LASTEXITCODE -ne 0) { throw "Installer failed with exit code $LASTEXITCODE." }
    $AppRoot = Join-Path $InstallRoot "app"
    $Vpy = Join-Path $InstallRoot "venv\Scripts\python.exe"
    if (-not (Test-Path $Vpy)) { throw "Installed venv Python not found: $Vpy" }
    def_AddCheck "L02" "Windows install/upgrade" "PASS" $AppRoot $Installer

    def_Progress 32 "Lane 02 · Python compile"
    $compile = def-RunPython $Vpy $AppRoot @("-m","compileall","-q","engines")
    if ($compile.ExitCode -ne 0) {
        def_AddCheck "L02" "Python compileall" "FAIL" $compile.Output
        throw "Python compile failed."
    }
    def_AddCheck "L02" "Python compileall" "PASS" "All engines compiled."

    def_Progress 40 "Lane 03 · Local RC acceptance"
    $local = def-RunPython $Vpy $AppRoot @("tests\rc_acceptance.py")
    if ($local.ExitCode -ne 0) {
        def_AddCheck "L03" "Local RC acceptance" "FAIL" $local.Output
        throw "Local RC acceptance failed."
    }
    $localJson = def-ParseJsonOutput $local.Output
    def_AddCheck "L03" "Local RC acceptance" "PASS" ($localJson | ConvertTo-Json -Compress -Depth 20) "tests\rc_acceptance.py"

    def_Progress 48 "Lane 03 · Native SSOT"
    $ssot = def-RunPython $Vpy $AppRoot @("engines\workops_ssot_store.py","snapshot")
    $ssotJson = def-ParseJsonOutput $ssot.Output
    if ($ssot.ExitCode -ne 0 -or -not $ssotJson) {
        def_AddCheck "L03" "SSOT snapshot" "FAIL" $ssot.Output
        throw "SSOT snapshot failed."
    }
    if ($ssotJson.mode -ne "DUCKDB_PARQUET") {
        def_AddCheck "L03" "Native DuckDB + Parquet" "FAIL" "Expected DUCKDB_PARQUET; got $($ssotJson.mode)" "out\ssot_status.json"
        throw "Target environment did not reach native DuckDB/Parquet mode."
    }
    def_AddCheck "L03" "Native DuckDB + Parquet" "PASS" "$($ssotJson.mode)" "out\ssot_status.json"

    def_Progress 55 "Lane 04 · Module health"
    $mh = def-RunPython $Vpy $AppRoot @("engines\workops_module_lifecycle_manager.py","health")
    $mhJson = def-ParseJsonOutput $mh.Output
    if ($mh.ExitCode -ne 0 -or -not $mhJson -or $mhJson.gate -ne "PASS") {
        def_AddCheck "L04" "LEGO module health" "FAIL" $mh.Output "out\module_registry_snapshot.json"
        throw "Module health gate failed."
    }
    def_AddCheck "L04" "LEGO module health" "PASS" "$($mhJson.count) registered modules" "out\module_registry_snapshot.json"

    def_Progress 62 "Lane 04 · Diagnostics"
    $diag = def-RunPython $Vpy $AppRoot @("engines\workops_diagnostics.py","build")
    $diagJson = def-ParseJsonOutput $diag.Output
    if ($diag.ExitCode -ne 0 -or -not $diagJson) {
        def_AddCheck "L04" "Diagnostics" "FAIL" $diag.Output
        throw "Diagnostics failed."
    }
    if ($diagJson.gate -eq "PASS") {
        def_AddCheck "L04" "Diagnostics" "PASS" $diagJson.gate "out\diagnostics.html"
    } else {
        def_AddCheck "L04" "Diagnostics" "WARN" $diagJson.gate "out\diagnostics.html"
    }

    def_Progress 68 "Lane 04 · Local API smoke"
    $apiUrl = "http://127.0.0.1:8775/api/status"
    $apiOk = $false
    try {
        $existing = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 2
        $apiOk = $true
        def_AddCheck "L04" "Local FastAPI" "PASS" "Existing WorkOps API responded." $apiUrl
    }
    catch {
        $server = Start-Process -FilePath $Vpy -ArgumentList @("engines\workops_api_server.py") -WorkingDirectory $AppRoot -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds 2
        try {
            $status = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 5
            $apiOk = $true
            def_AddCheck "L04" "Local FastAPI" "PASS" "Started PID $($server.Id); API responded." $apiUrl
        } catch {
            def_AddCheck "L04" "Local FastAPI" "FAIL" $_.Exception.Message $apiUrl
            throw "Local API smoke failed."
        }
    }

    if ($Mode -eq "Offline") {
        def_Progress 75 "Lane 05 · Microsoft 365 live gate skipped by mode"
        def_AddCheck "L05" "Live Microsoft Graph read" "SKIP" "Offline mode selected."
        def_AddCheck "L05" "Outlook Draft validation" "SKIP" "Offline mode selected."
    }
    else {
        def_Progress 75 "Lane 05 · Configure explicit IT-approved Graph read"
        if (-not $ClientId) { throw "LiveRead requires -ClientId from IT/Entra app registration." }
        if (-not $ItReference) { throw "LiveRead requires -ItReference (ticket/change/reference)." }

        $OutlookCfgPath = Join-Path $AppRoot "config\outlook_graph.json"
        $beforeCfg = Get-Content -LiteralPath $OutlookCfgPath -Raw | ConvertFrom-Json -Depth 100
        $beforeHash = def-Sha256 $OutlookCfgPath
        $cfgBackup = Join-Path $RunDir "outlook_graph.before.json"
        Copy-Item $OutlookCfgPath $cfgBackup -Force

        $beforeCfg.client_id = $ClientId
        $beforeCfg.tenant_id = $TenantId
        $beforeCfg.enabled = $true
        $beforeCfg.allow_send = $false
        $beforeCfg.allow_draft_write = $false
        $beforeCfg.it_approval.acknowledged = $true
        $beforeCfg.it_approval.ticket_or_reference = $ItReference
        $beforeCfg | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $OutlookCfgPath -Encoding UTF8
        $afterHash = def-Sha256 $OutlookCfgPath
        def_AddCheck "L05" "Graph configuration" "PASS" "Config hash $beforeHash → $afterHash; Mail.Read only." $OutlookCfgPath

        def_Progress 82 "Lane 05 · LIVE Graph read / delta sync"
        Write-Host ""
        Write-Host "def Microsoft sign-in may now request Device Code / interactive authentication." -ForegroundColor Yellow
        Write-Host "def Scope: signed-in user's authorized mailbox; WorkOps send remains disabled." -ForegroundColor Yellow
        $graph = def-RunPythonInteractive $Vpy $AppRoot @("engines\workops_outlook_graph_connector.py","sync")
        $graphJson = def-ParseJsonOutput $graph.Output
        if ($graph.ExitCode -ne 0 -or -not $graphJson -or $graphJson.gate -ne "PASS") {
            def_AddCheck "L05" "Live Microsoft Graph read" "FAIL" $graph.Output "out\graph_sync_report.json"
            throw "Live Microsoft Graph validation failed."
        }
        def_AddCheck "L05" "Live Microsoft Graph read" "PASS" "Folders=$($graphJson.folders); messages=$($graphJson.messages); changed=$($graphJson.changed)" "out\graph_sync_report.json"

        $refresh = def-RunPython $Vpy $AppRoot @("engines\workops_orchestrator.py","refresh")
        if ($refresh.ExitCode -eq 0) {
            def_AddCheck "L05" "Post-sync WorkOps refresh" "PASS" "Mailbox events propagated into WorkOps."
        } else {
            def_AddCheck "L05" "Post-sync WorkOps refresh" "FAIL" $refresh.Output
            throw "Post-sync refresh failed."
        }

        if ($Mode -eq "LiveReadAndDraft") {
            def_Progress 88 "Lane 05 · OPTIONAL draft validation"
            if (-not $DraftRecipient) {
                throw "LiveReadAndDraft requires -DraftRecipient. No email will be sent."
            }
            $cfg = Get-Content -LiteralPath $OutlookCfgPath -Raw | ConvertFrom-Json -Depth 100
            $cfg.allow_draft_write = $true
            $cfg.allow_send = $false
            $cfg | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $OutlookCfgPath -Encoding UTF8

            $subject = "[Veritas WorkOps Validation] Draft only - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            $body = "Veritas WorkOps target acceptance draft. This message was created as a draft only and was not sent automatically."
            $draft = def-RunPythonInteractive $Vpy $AppRoot @(
                "engines\workops_outlook_graph_connector.py","draft",
                "--subject",$subject,
                "--body",$body,
                "--to",$DraftRecipient
            )
            $draftJson = def-ParseJsonOutput $draft.Output

            # Fail-safe restore draft capability to disabled after the validation attempt.
            $cfg = Get-Content -LiteralPath $OutlookCfgPath -Raw | ConvertFrom-Json -Depth 100
            $cfg.allow_draft_write = $false
            $cfg.allow_send = $false
            $cfg | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $OutlookCfgPath -Encoding UTF8

            if ($draft.ExitCode -ne 0 -or -not $draftJson -or $draftJson.isDraft -ne $true) {
                def_AddCheck "L05" "Outlook Draft validation" "FAIL" $draft.Output
                throw "Draft validation failed."
            }
            def_AddCheck "L05" "Outlook Draft validation" "PASS" "Draft ID=$($draftJson.id); auto-send remains disabled." "Outlook Drafts"
        } else {
            def_AddCheck "L05" "Outlook Draft validation" "SKIP" "LiveRead mode does not request Mail.ReadWrite."
        }
    }

    def_Progress 92 "Lane 06 · Backup / restore safety"
    $backup = def-RunPython $Vpy $AppRoot @("engines\workops_backup_restore.py","backup")
    $backupJson = def-ParseJsonOutput $backup.Output
    if ($backup.ExitCode -ne 0 -or -not $backupJson -or $backupJson.gate -ne "PASS") {
        def_AddCheck "L06" "Backup" "FAIL" $backup.Output
        throw "Backup failed."
    }
    def_AddCheck "L06" "Backup" "PASS" "Files=$($backupJson.files); SHA256=$($backupJson.sha256)" $backupJson.backup

    $verify = def-RunPython $Vpy $AppRoot @("engines\workops_backup_restore.py","verify",$backupJson.backup)
    $verifyJson = def-ParseJsonOutput $verify.Output
    if ($verify.ExitCode -ne 0 -or $verifyJson.gate -ne "PASS") {
        def_AddCheck "L06" "Backup verify" "FAIL" $verify.Output
        throw "Backup verification failed."
    }
    def_AddCheck "L06" "Backup verify" "PASS" $verifyJson.sha256 $backupJson.backup

    $restore = def-RunPython $Vpy $AppRoot @("engines\workops_backup_restore.py","restore",$backupJson.backup)
    $restoreJson = def-ParseJsonOutput $restore.Output
    if ($restore.ExitCode -ne 0 -or $restoreJson.gate -ne "STAGED_REVIEW_REQUIRED" -or $restoreJson.canonical_mutation -ne $false) {
        def_AddCheck "L06" "Restore-to-staging" "FAIL" $restore.Output
        throw "Restore staging safety gate failed."
    }
    def_AddCheck "L06" "Restore-to-staging" "PASS" "No canonical mutation." $restoreJson.staging

    def_Progress 97 "Lane 06 · Final gate"
    $failCount = @($Checks | Where-Object Status -eq "FAIL").Count
    $warnCount = @($Checks | Where-Object Status -eq "WARN").Count
    if ($failCount -gt 0) {
        $FinalGate = "FAIL"
    } elseif ($warnCount -gt 0) {
        $FinalGate = "PASS_WITH_WARNINGS"
    } else {
        $FinalGate = "PASS"
    }
    $finalCheckStatus = if ($FinalGate -eq "PASS") { "PASS" } elseif ($FinalGate -eq "PASS_WITH_WARNINGS") { "WARN" } else { "FAIL" }
    def-WriteReports $FinalGate $AppRoot $Vpy
    def_AddCheck "L06" "Final target acceptance" $finalCheckStatus $FinalGate $ReportHtml

    # Rewrite after final check was added.
    def-WriteReports $FinalGate $AppRoot $Vpy

    Write-Progress -Activity "Veritas WorkOps Target Acceptance v0201" -Completed
    def_Banner "TARGET ACCEPTANCE RESULT"
    Write-Host "def Gate       : $FinalGate" -ForegroundColor $(if($FinalGate -eq "PASS"){"Green"}elseif($FinalGate -eq "PASS_WITH_WARNINGS"){"Yellow"}else{"Red"})
    Write-Host "def HTML       : $ReportHtml"
    Write-Host "def JSON       : $ReportJson"
    Write-Host "def CSV        : $ReportCsv"
    Write-Host "def Transcript : $Transcript"
    if ($OpenReport -and (Test-Path $ReportHtml)) { Start-Process $ReportHtml }
}
catch {
    $msg = $_.Exception.Message
    def_AddCheck "SYSTEM" "Unhandled target acceptance error" "FAIL" $msg
    try { def-WriteReports "FAIL" $AppRoot $Vpy } catch {}
    Write-Progress -Activity "Veritas WorkOps Target Acceptance v0201" -Completed
    Write-Host ""
    Write-Host "def TARGET ACCEPTANCE FAIL" -ForegroundColor Red
    Write-Host "def $msg" -ForegroundColor Red
    Write-Host "def RunDir: $RunDir"
    if ($OpenReport -and (Test-Path $ReportHtml)) { Start-Process $ReportHtml }
    throw
}
finally {
    try { Stop-Transcript | Out-Null } catch {}
}
