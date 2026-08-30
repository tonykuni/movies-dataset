# =============================================================================
# def 00 · Parameters
# =============================================================================
param(
    [string]$ViaBase,
    [string]$RepoDir,
    [string]$RunTag,
    [string]$DevHost = "127.0.0.1",
    [int]$DevPort = 5173,
    [bool]$OpenHtmlReport = $true,
    [bool]$OpenAppUrl = $true
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

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunId = "RUN_${Timestamp}_${RunTag}"
$RunRoot = Join-Path $ViaBase "_external_repos\_runs\$RunId"
$JsonDir = Join-Path $RunRoot "json"
$HtmlDir = Join-Path $RunRoot "html"
$LogDir = Join-Path $RunRoot "logs"
$Matrix = New-Object System.Collections.Generic.List[object]
$AppUrl = "http://$DevHost`:$DevPort"

# =============================================================================
# def 01 · Helpers
# =============================================================================
function def_ShowProgress {
    param(
        [int]$Step,
        [int]$Total,
        [string]$Message
    )

    $Percent = [math]::Round(($Step / $Total) * 100)
    $Filled = [math]::Floor($Percent / 5)
    $Empty = 20 - $Filled
    $Bar = ("█" * $Filled) + ("░" * $Empty)
    Write-Host ("[{0,3}%] [{1}] {2}" -f $Percent, $Bar, $Message) -ForegroundColor Cyan
}

function def_EnsureDirectory {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }

    return $Path
}

function def_AddMatrixRow {
    param(
        [string]$Step,
        [string]$Name,
        [string]$Status,
        [string]$Risk,
        [string]$Message,
        [string]$Path = ""
    )

    $script:Matrix.Add([pscustomobject]@{
        def_step = $Step
        def_name = $Name
        def_status = $Status
        def_risk = $Risk
        def_message = $Message
        def_path = $Path
        def_time = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }) | Out-Null
}

function def_TestCommand {
    param(
        [string]$CommandName
    )

    $Command = Get-Command $CommandName -ErrorAction SilentlyContinue

    if (-not $Command) {
        def_AddMatrixRow -Step "CHECK" -Name $CommandName -Status "FAIL" -Risk "HIGH" -Message "$CommandName not found"
        throw "$CommandName not found"
    }

    def_AddMatrixRow -Step "CHECK" -Name $CommandName -Status "PASS" -Risk "LOW" -Message "$CommandName found" -Path $Command.Source
}

function def_TestPortInUse {
    param(
        [int]$Port
    )

    $Conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue

    if ($Conn) {
        return $true
    }

    return $false
}

function def_ReadPackageScripts {
    param(
        [string]$RepoDir
    )

    $PackageJson = Join-Path $RepoDir "package.json"
    $Pkg = Get-Content -LiteralPath $PackageJson -Raw | ConvertFrom-Json

    $ScriptsJson = $Pkg.scripts | ConvertTo-Json -Depth 8 -Compress
    def_AddMatrixRow -Step "SCAN" -Name "package scripts" -Status "PASS" -Risk "LOW" -Message $ScriptsJson -Path $PackageJson
}

function def_InstallDependencies {
    param(
        [string]$RepoDir,
        [string]$LogDir
    )

    Set-Location -LiteralPath $RepoDir

    Write-Host "[INFO] Running npm install --legacy-peer-deps" -ForegroundColor Yellow

    npm install --legacy-peer-deps 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "npm_install_legacy_peer_deps.log")

    if ($LASTEXITCODE -ne 0) {
        def_AddMatrixRow -Step "INSTALL" -Name "npm install --legacy-peer-deps" -Status "FAIL" -Risk "HIGH" -Message "npm install failed" -Path $RepoDir
        throw "npm install --legacy-peer-deps failed"
    }

    def_AddMatrixRow -Step "INSTALL" -Name "npm install --legacy-peer-deps" -Status "PASS" -Risk "LOW" -Message "Dependencies installed" -Path $RepoDir
}

function def_StartDevServerNoClose {
    param(
        [string]$RepoDir,
        [string]$DevHost,
        [int]$DevPort,
        [string]$AppUrl,
        [bool]$OpenAppUrl
    )

    $Command = @"
cd /d "$RepoDir"
echo ================================================================================
echo def VIA STOCK DASHBOARD · VITE DEV SERVER
echo ================================================================================
echo def RepoDir: $RepoDir
echo def URL    : $AppUrl
echo def Policy : no close
echo.
npm run dev -- --host $DevHost --port $DevPort
echo.
echo PowerShell remains open. Press any key to close this server window.
pause
"@

    $CmdPath = Join-Path $RepoDir "_via_start_stock_dashboard_dev_server.cmd"
    Set-Content -LiteralPath $CmdPath -Value $Command -Encoding ASCII

    Start-Process -FilePath "cmd.exe" -ArgumentList "/k `"$CmdPath`""

    Start-Sleep -Seconds 5

    if ($OpenAppUrl) {
        Start-Process $AppUrl
    }

    def_AddMatrixRow -Step "LAUNCH" -Name "Vite dev server" -Status "PASS" -Risk "LOW" -Message "Started in a separate no-close cmd window: $AppUrl" -Path $CmdPath
}

function def_WriteOutputs {
    param(
        [string]$RunId,
        [string]$RunRoot,
        [string]$JsonDir,
        [string]$HtmlDir,
        [string]$RepoDir,
        [string]$AppUrl,
        [object[]]$Matrix,
        [bool]$OpenHtmlReport
    )

    $FailCount = ($Matrix | Where-Object { $_.def_status -eq "FAIL" }).Count
    $WarnCount = ($Matrix | Where-Object { $_.def_status -eq "WARN" }).Count
    $PassCount = ($Matrix | Where-Object { $_.def_status -eq "PASS" }).Count

    $FinalStatus = if ($FailCount -gt 0) {
        "FAIL"
    } elseif ($WarnCount -gt 0) {
        "PASS_WITH_WARN"
    } else {
        "PASS"
    }

    $Summary = [pscustomobject]@{
        def_run_id = $RunId
        def_generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        def_repo_dir = $RepoDir
        def_app_url = $AppUrl
        def_final_status = $FinalStatus
        def_pass = $PassCount
        def_warn = $WarnCount
        def_fail = $FailCount
        def_policy_no_pnpm = $true
        def_policy_no_corepack = $true
        def_install_mode = "npm install --legacy-peer-deps"
        def_matrix = $Matrix
    }

    $SummaryPath = Join-Path $JsonDir "VIA_supportive_install_launch_stock_dashboard_summary.json"
    $MatrixPath = Join-Path $JsonDir "VIA_supportive_install_launch_stock_dashboard_matrix.json"
    $HtmlPath = Join-Path $HtmlDir "VIA_supportive_install_launch_stock_dashboard_report.html"

    $Summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $SummaryPath -Encoding UTF8
    $Matrix | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $MatrixPath -Encoding UTF8

    $Rows = foreach ($Row in $Matrix) {
        "<tr><td>$($Row.def_step)</td><td>$($Row.def_name)</td><td class='$($Row.def_status)'>$($Row.def_status)</td><td>$($Row.def_risk)</td><td>$($Row.def_message)</td><td>$($Row.def_path)</td><td>$($Row.def_time)</td></tr>"
    }

    $Html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Supportive Install Launch Report</title>
<style>
body{font-family:Inter,'Noto Sans TC',Arial,sans-serif;background:#F9F9F6;color:#1F2933;margin:32px;}
h1{font-size:24px;margin:0 0 8px;}
h2{font-size:15px;color:#6B7C78;margin:0 0 24px;}
.card{background:#fff;border:1px solid #DFECEA;border-radius:18px;padding:20px;margin-bottom:18px;box-shadow:0 8px 24px rgba(31,41,51,.06);}
table{border-collapse:collapse;width:100%;font-size:13px;background:#fff;}
th,td{border-bottom:1px solid #DFECEA;padding:10px;text-align:left;vertical-align:top;}
th{background:#DFECEA;color:#1F2933;}
.PASS{color:#166534;font-weight:700;}
.FAIL{color:#B91C1C;font-weight:700;}
.WARN{color:#B7791F;font-weight:700;}
code{background:#F3F7F6;padding:2px 6px;border-radius:6px;}
a{color:#0F766E;font-weight:700;}
</style>
</head>
<body>
<div class="card">
<h1>Veritas Intelligence Analytics · Supportive Install Launch Report</h1>
<h2>$RunId</h2>
<p><b>Status:</b> <code>$FinalStatus</code></p>
<p><b>Repo:</b> <code>$RepoDir</code></p>
<p><b>App URL:</b> <a href="$AppUrl">$AppUrl</a></p>
<p><b>Install:</b> <code>npm install --legacy-peer-deps</code></p>
<p><b>Policy:</b> no pnpm · no corepack · no Program Files mutation · separate no-close server window</p>
</div>
<div class="card">
<table>
<thead>
<tr>
<th>Step</th><th>Name</th><th>Status</th><th>Risk</th><th>Message</th><th>Path</th><th>Time</th>
</tr>
</thead>
<tbody>
$($Rows -join "`n")
</tbody>
</table>
</div>
</body>
</html>
"@

    $Html | Set-Content -LiteralPath $HtmlPath -Encoding UTF8

    Write-Host ""
    Write-Host "[OK] Summary JSON : $SummaryPath" -ForegroundColor Green
    Write-Host "[OK] Matrix JSON  : $MatrixPath" -ForegroundColor Green
    Write-Host "[OK] HTML Report  : $HtmlPath" -ForegroundColor Green
    Write-Host "[OK] App URL      : $AppUrl" -ForegroundColor Green

    if ($OpenHtmlReport) {
        Start-Process $HtmlPath
    }
}

# =============================================================================
# def 99 · Main
# =============================================================================
try {
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA · SUPPORTIVE MODULE · INSTALL + LAUNCH STOCK DASHBOARD" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def Policy: npm legacy-peer-deps · no pnpm · no corepack · no Program Files mutation" -ForegroundColor Yellow
    Write-Host ""

    def_ShowProgress -Step 1 -Total 8 -Message "Prepare run directories"
    def_EnsureDirectory -Path $RunRoot | Out-Null
    def_EnsureDirectory -Path $JsonDir | Out-Null
    def_EnsureDirectory -Path $HtmlDir | Out-Null
    def_EnsureDirectory -Path $LogDir | Out-Null
    def_AddMatrixRow -Step "INIT" -Name "RunRoot" -Status "PASS" -Risk "LOW" -Message "Run root prepared" -Path $RunRoot

    def_ShowProgress -Step 2 -Total 8 -Message "Validate repo"
    if (-not (Test-Path -LiteralPath $RepoDir)) {
        throw "RepoDir not found: $RepoDir"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $RepoDir "package.json"))) {
        throw "package.json not found: $RepoDir"
    }
    def_AddMatrixRow -Step "CHECK" -Name "RepoDir" -Status "PASS" -Risk "LOW" -Message "Repo directory and package.json found" -Path $RepoDir

    def_ShowProgress -Step 3 -Total 8 -Message "Check node"
    def_TestCommand -CommandName "node"
    node --version | Tee-Object -FilePath (Join-Path $LogDir "node_version.log") | Out-Host

    def_ShowProgress -Step 4 -Total 8 -Message "Check npm"
    def_TestCommand -CommandName "npm"
    npm --version | Tee-Object -FilePath (Join-Path $LogDir "npm_version.log") | Out-Host

    def_ShowProgress -Step 5 -Total 8 -Message "Read package scripts"
    def_ReadPackageScripts -RepoDir $RepoDir

    def_ShowProgress -Step 6 -Total 8 -Message "Install dependencies"
    def_InstallDependencies -RepoDir $RepoDir -LogDir $LogDir

    def_ShowProgress -Step 7 -Total 8 -Message "Launch dev server"
    if (def_TestPortInUse -Port $DevPort) {
        def_AddMatrixRow -Step "PORT" -Name "Port $DevPort" -Status "WARN" -Risk "MEDIUM" -Message "Port already in use; Vite may choose another port or fail." -Path $AppUrl
        Write-Host "[WARN] Port $DevPort already in use. 若開不起來，請改 DevPort。" -ForegroundColor Yellow
    } else {
        def_AddMatrixRow -Step "PORT" -Name "Port $DevPort" -Status "PASS" -Risk "LOW" -Message "Port is available" -Path $AppUrl
    }

    def_StartDevServerNoClose -RepoDir $RepoDir -DevHost $DevHost -DevPort $DevPort -AppUrl $AppUrl -OpenAppUrl $OpenAppUrl

    def_ShowProgress -Step 8 -Total 8 -Message "Write JSON and HTML outputs"
    def_WriteOutputs -RunId $RunId -RunRoot $RunRoot -JsonDir $JsonDir -HtmlDir $HtmlDir -RepoDir $RepoDir -AppUrl $AppUrl -Matrix $Matrix.ToArray() -OpenHtmlReport $OpenHtmlReport

    Write-Host ""
    Write-Host "def FINAL_STATUS: VIA_SUPPORTIVE_INSTALL_LAUNCH_READY" -ForegroundColor Green
}
catch {
    def_AddMatrixRow -Step "FATAL" -Name "Exception" -Status "FAIL" -Risk "HIGH" -Message $_.Exception.Message
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed

    try {
        def_WriteOutputs -RunId $RunId -RunRoot $RunRoot -JsonDir $JsonDir -HtmlDir $HtmlDir -RepoDir $RepoDir -AppUrl $AppUrl -Matrix $Matrix.ToArray() -OpenHtmlReport $OpenHtmlReport
    }
    catch {
        Write-Host "[WARN] Failed to write final outputs: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
