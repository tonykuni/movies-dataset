# =============================================================================
# def 00 · Parameters
# =============================================================================
param(
    [string]$RepoUrl,
    [string]$RepoName,
    [string]$ViaBase,
    [string]$ExternalRepoRoot,
    [string]$RunTag,
    [bool]$OpenHtmlReport = $true
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

$KeepPowerShellOpen = $false
$NoDeletePolicy = $true
$NoPnpmPolicy = $true
$NoNpmInstallPolicy = $true
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunId = "RUN_${Timestamp}_${RunTag}"
$RunRoot = Join-Path $ExternalRepoRoot "_runs\$RunId"
$JsonDir = Join-Path $RunRoot "json"
$HtmlDir = Join-Path $RunRoot "html"
$LogDir = Join-Path $RunRoot "logs"
$TargetRepoDir = Join-Path $ExternalRepoRoot $RepoName
$Matrix = New-Object System.Collections.Generic.List[object]

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

function def_InvokeGitCloneOrPull {
    param(
        [string]$RepoUrl,
        [string]$TargetRepoDir,
        [string]$ExternalRepoRoot
    )

    Set-Location -LiteralPath $ExternalRepoRoot

    if (Test-Path -LiteralPath $TargetRepoDir) {
        if (Test-Path -LiteralPath (Join-Path $TargetRepoDir ".git")) {
            Write-Host "[WARN] Repo already exists. Running git pull only." -ForegroundColor Yellow
            Set-Location -LiteralPath $TargetRepoDir

            git pull 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "git_pull.log")

            if ($LASTEXITCODE -ne 0) {
                def_AddMatrixRow -Step "GIT" -Name "git pull" -Status "FAIL" -Risk "HIGH" -Message "git pull failed" -Path $TargetRepoDir
                throw "git pull failed"
            }

            def_AddMatrixRow -Step "GIT" -Name "git pull" -Status "PASS" -Risk "LOW" -Message "Existing repo updated" -Path $TargetRepoDir
            return
        }

        def_AddMatrixRow -Step "GIT" -Name "existing folder" -Status "BLOCKED" -Risk "HIGH" -Message "Folder exists but is not a git repo. No delete policy blocks overwrite." -Path $TargetRepoDir
        throw "Target folder exists but is not a git repo: $TargetRepoDir"
    }

    git clone $RepoUrl $TargetRepoDir 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "git_clone.log")

    if ($LASTEXITCODE -ne 0) {
        def_AddMatrixRow -Step "GIT" -Name "git clone" -Status "FAIL" -Risk "HIGH" -Message "git clone failed" -Path $TargetRepoDir
        throw "git clone failed"
    }

    def_AddMatrixRow -Step "GIT" -Name "git clone" -Status "PASS" -Risk "LOW" -Message "Repo cloned successfully" -Path $TargetRepoDir
}

function def_ReadPackageInfo {
    param(
        [string]$TargetRepoDir
    )

    $PackageJson = Join-Path $TargetRepoDir "package.json"

    if (-not (Test-Path -LiteralPath $PackageJson)) {
        def_AddMatrixRow -Step "SCAN" -Name "package.json" -Status "WARN" -Risk "MEDIUM" -Message "package.json not found" -Path $PackageJson
        return
    }

    try {
        $Pkg = Get-Content -LiteralPath $PackageJson -Raw | ConvertFrom-Json
        $Scripts = $Pkg.scripts | ConvertTo-Json -Depth 5 -Compress
        def_AddMatrixRow -Step "SCAN" -Name "package.json" -Status "PASS" -Risk "LOW" -Message "package.json readable; scripts=$Scripts" -Path $PackageJson
    }
    catch {
        def_AddMatrixRow -Step "SCAN" -Name "package.json" -Status "WARN" -Risk "MEDIUM" -Message "package.json exists but parse failed: $($_.Exception.Message)" -Path $PackageJson
    }
}

function def_WriteOutputs {
    param(
        [string]$RunRoot,
        [string]$JsonDir,
        [string]$HtmlDir,
        [string]$RunId,
        [string]$RepoUrl,
        [string]$TargetRepoDir,
        [object[]]$Matrix,
        [bool]$OpenHtmlReport
    )

    $Summary = [pscustomobject]@{
        def_run_id = $RunId
        def_generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        def_repo_url = $RepoUrl
        def_target_repo_dir = $TargetRepoDir
        def_policy_no_delete = $true
        def_policy_no_pnpm = $true
        def_policy_no_npm_install = $true
        def_status = if (($Matrix | Where-Object { $_.def_status -eq "FAIL" }).Count -gt 0) { "FAIL" } elseif (($Matrix | Where-Object { $_.def_status -eq "BLOCKED" }).Count -gt 0) { "BLOCKED" } else { "PASS" }
        def_matrix = $Matrix
    }

    $SummaryPath = Join-Path $JsonDir "VIA_supportive_gitclone_stock_dashboard_summary.json"
    $MatrixPath = Join-Path $JsonDir "VIA_supportive_gitclone_stock_dashboard_matrix.json"
    $HtmlPath = Join-Path $HtmlDir "VIA_supportive_gitclone_stock_dashboard_report.html"

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
<title>VIA Supportive Git Clone Report</title>
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
.BLOCKED{color:#B91C1C;font-weight:700;}
code{background:#F3F7F6;padding:2px 6px;border-radius:6px;}
</style>
</head>
<body>
<div class="card">
<h1>Veritas Intelligence Analytics · Supportive Git Clone Report</h1>
<h2>$RunId</h2>
<p><b>Repo:</b> <code>$RepoUrl</code></p>
<p><b>Target:</b> <code>$TargetRepoDir</code></p>
<p><b>Status:</b> <code>$($Summary.def_status)</code></p>
<p><b>Policy:</b> no delete · no pnpm · no npm install · supportive wrapper</p>
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
    Write-Host "[OK] Repo Target  : $TargetRepoDir" -ForegroundColor Green

    if ($OpenHtmlReport) {
        Start-Process $HtmlPath
    }
}

# =============================================================================
# def 99 · Main
# =============================================================================
try {
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA · SUPPORTIVE MODULE · GIT CLONE STOCK DASHBOARD" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def Policy: no delete · no pnpm · no npm install · supportive only" -ForegroundColor Yellow
    Write-Host ""

    def_ShowProgress -Step 1 -Total 7 -Message "Prepare run directories"
    def_EnsureDirectory -Path $RunRoot | Out-Null
    def_EnsureDirectory -Path $JsonDir | Out-Null
    def_EnsureDirectory -Path $HtmlDir | Out-Null
    def_EnsureDirectory -Path $LogDir | Out-Null

    def_AddMatrixRow -Step "INIT" -Name "RunRoot" -Status "PASS" -Risk "LOW" -Message "Run root prepared" -Path $RunRoot

    def_ShowProgress -Step 2 -Total 7 -Message "Check git"
    def_TestCommand -CommandName "git"
    git --version | Tee-Object -FilePath (Join-Path $LogDir "git_version.log") | Out-Host

    def_ShowProgress -Step 3 -Total 7 -Message "Check node"
    def_TestCommand -CommandName "node"
    node --version | Tee-Object -FilePath (Join-Path $LogDir "node_version.log") | Out-Host

    def_ShowProgress -Step 4 -Total 7 -Message "Check npm"
    def_TestCommand -CommandName "npm"
    npm --version | Tee-Object -FilePath (Join-Path $LogDir "npm_version.log") | Out-Host

    def_ShowProgress -Step 5 -Total 7 -Message "Clone or update repo"
    def_InvokeGitCloneOrPull -RepoUrl $RepoUrl -TargetRepoDir $TargetRepoDir -ExternalRepoRoot $ExternalRepoRoot

    def_ShowProgress -Step 6 -Total 7 -Message "Read package info only"
    def_ReadPackageInfo -TargetRepoDir $TargetRepoDir

    def_ShowProgress -Step 7 -Total 7 -Message "Write JSON and HTML outputs"
    def_WriteOutputs -RunRoot $RunRoot -JsonDir $JsonDir -HtmlDir $HtmlDir -RunId $RunId -RepoUrl $RepoUrl -TargetRepoDir $TargetRepoDir -Matrix $Matrix.ToArray() -OpenHtmlReport $OpenHtmlReport

    Write-Host ""
    Write-Host "def FINAL_STATUS: VIA_SUPPORTIVE_GITCLONE_READY" -ForegroundColor Green
}
catch {
    def_AddMatrixRow -Step "FATAL" -Name "Exception" -Status "FAIL" -Risk "HIGH" -Message $_.Exception.Message
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed

    try {
        def_WriteOutputs -RunRoot $RunRoot -JsonDir $JsonDir -HtmlDir $HtmlDir -RunId $RunId -RepoUrl $RepoUrl -TargetRepoDir $TargetRepoDir -Matrix $Matrix.ToArray() -OpenHtmlReport $OpenHtmlReport
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
