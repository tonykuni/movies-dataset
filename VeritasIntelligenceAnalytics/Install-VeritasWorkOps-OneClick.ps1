# Install-VeritasWorkOps-OneClick.ps1 — 一鍵部署器 v0100(產品化令 2026/08/09)
# 情境:新進員工全新電腦,只有內建 Windows PowerShell 5.1 — 按下啟動鍵,系統自動部署
#       所有工具/環境/設定/PATH,全部自動完成;金基準=engines\standard_config.json。
# 相容:全檔為 PowerShell 5.1 語法(無 ??、無三元、無 pwsh7 專屬);pwsh7 由本器自裝。
# 誠實:逐步 OK/FAIL 不卡斷,總結表+out\bootstrap_report.json;本器在開發容器僅 AST 驗證,
#       Windows 實機安裝行為待操作員首跑回報。零互動(無任何提問);-NoSchedule 可跳過排程。
# 紅線:絕不代發送(排程只到「產草稿」);不動任何郵件/分類;機密只走環境變數。
param(
    [switch]$NoSchedule,
    [switch]$SkipSelftest
)
$ErrorActionPreference = "Continue"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkOps = Join-Path $Root "functional modules\WorkOps"
$Engines = Join-Path $WorkOps "engines"
$Tools = Join-Path $Root "tools"
$OutDir = Join-Path $WorkOps "out"
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }
if (-not (Test-Path $Tools)) { New-Item -ItemType Directory -Path $Tools -Force | Out-Null }
$Report = @()
function Step { param([string]$Name, [bool]$Ok, [string]$Detail)
    $g = "FAIL"; if ($Ok) { $g = "OK " }
    $script:Report += New-Object PSObject -Property @{ step = $Name; gate = $g.Trim(); detail = $Detail }
    $c = "Red"; if ($Ok) { $c = "Green" }
    Write-Host ("[{0}] {1}  {2}" -f $g, $Name, $Detail) -ForegroundColor $c
}
Write-Host "=============================================================" -ForegroundColor Cyan
Write-Host " Veritas WorkOps 一鍵部署(零互動;金基準 standard_config.json)" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Cyan

# ---- [1/8] 金基準快照 ----------------------------------------------------
$CfgP = Join-Path $Engines "standard_config.json"
$Cfg = $null
if (Test-Path $CfgP) {
    try { $Cfg = Get-Content $CfgP -Raw -Encoding UTF8 | ConvertFrom-Json } catch { }
}
Step "1/8 金基準快照" ($null -ne $Cfg) $CfgP

# ---- [2/8] pwsh 7(可攜,免管理員;動態解析最新,嚴禁寫死版號)---------
$Pwsh = $null
$cmd = Get-Command pwsh -ErrorAction SilentlyContinue
if ($cmd) { $Pwsh = $cmd.Source }
if (-not $Pwsh) {
    $local = Join-Path $Tools "pwsh\pwsh.exe"
    if (Test-Path $local) { $Pwsh = $local }
}
if (-not $Pwsh) {
    try {
        Write-Host "  [2/8] 下載 PowerShell 7 可攜版(GitHub 最新 release)..."
        $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/PowerShell/PowerShell/releases/latest" -UseBasicParsing
        $asset = $rel.assets | Where-Object { $_.name -match "win-x64\.zip$" } | Select-Object -First 1
        if ($asset) {
            $zip = Join-Path $env:TEMP $asset.name
            Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing
            $dst = Join-Path $Tools "pwsh"
            if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $dst)
            Remove-Item $zip -Force
            if (Test-Path (Join-Path $dst "pwsh.exe")) { $Pwsh = Join-Path $dst "pwsh.exe" }
        }
    } catch { Write-Host ("  [2/8] 下載失敗:{0}" -f $_.Exception.Message) -ForegroundColor Yellow }
}
$pv = ""
if ($Pwsh) { try { $pv = (& $Pwsh -NoProfile -Command '$PSVersionTable.PSVersion.ToString()' 2>$null) } catch { } }
Step "2/8 pwsh 7" ([bool]$Pwsh) ("{0} {1}" -f $Pwsh, $pv)

# ---- [3/8] Python 3.12(python.org 最新 3.12.x,使用者範圍靜默安裝)-----
$Py = $null
foreach ($cand in @("py", "python")) {
    $c = Get-Command $cand -ErrorAction SilentlyContinue
    if ($c) {
        try {
            $v = & $c.Source -c "import sys;print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($v -and [version]$v -ge [version]"3.10") { $Py = $c.Source; break }
        } catch { }
    }
}
if (-not $Py) {
    try {
        Write-Host "  [3/8] 下載 Python 3.12 安裝器(python.org 最新 3.12.x)..."
        $idx = (Invoke-WebRequest -Uri "https://www.python.org/ftp/python/" -UseBasicParsing).Content
        $vers = [regex]::Matches($idx, "3\.12\.(\d+)/") | ForEach-Object { [int]$_.Groups[1].Value } | Sort-Object -Unique
        if ($vers.Count -gt 0) {
            $ver = "3.12." + $vers[$vers.Count - 1]
            $exe = Join-Path $env:TEMP ("python-" + $ver + "-amd64.exe")
            Invoke-WebRequest -Uri ("https://www.python.org/ftp/python/" + $ver + "/python-" + $ver + "-amd64.exe") -OutFile $exe -UseBasicParsing
            Start-Process -FilePath $exe -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1" -Wait
            Remove-Item $exe -Force -ErrorAction SilentlyContinue
            $lp = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
            if (Test-Path $lp) { $Py = $lp }
            $plauncher = Get-Command py -ErrorAction SilentlyContinue
            if (-not $Py -and $plauncher) { $Py = $plauncher.Source }
        }
    } catch { Write-Host ("  [3/8] 安裝失敗:{0}" -f $_.Exception.Message) -ForegroundColor Yellow }
}
$pyv = ""
if ($Py) { try { $pyv = & $Py -c "import sys;print(sys.version.split()[0])" 2>$null } catch { } }
Step "3/8 Python 3.12" ([bool]$Py) ("{0} {1}" -f $Py, $pyv)

# ---- [4/8] 使用者 PATH(bin + tools\pwsh;免管理員)---------------------
$ok4 = $true
try {
    $want = @((Join-Path $Root "bin"), (Join-Path $Tools "pwsh"))
    $cur = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($null -eq $cur) { $cur = "" }
    $parts = $cur -split ";" | Where-Object { $_ -ne "" }
    $added = @()
    foreach ($w in $want) {
        if ((Test-Path $w) -and ($parts -notcontains $w)) { $parts += $w; $added += $w }
    }
    if ($added.Count -gt 0) {
        [Environment]::SetEnvironmentVariable("Path", ($parts -join ";"), "User")
        $env:Path = $env:Path + ";" + ($added -join ";")
    }
    Step "4/8 使用者 PATH" $true ("增列 " + $added.Count + " 項(既有不動)")
} catch { $ok4 = $false; Step "4/8 使用者 PATH" $false $_.Exception.Message }

# ---- [5/8] pm4py 隔離 venv(pmsetup 引擎;基底零觸碰)-------------------
$ok5 = $false
if ($Pwsh) {
    $pms = Get-ChildItem -Path $Engines -Filter "Invoke-VIA-WorkOps-PmSetup-v0*.ps1" | Sort-Object Name | Select-Object -Last 1
    if ($pms) {
        & $Pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $pms.FullName
        $ok5 = (Test-Path (Join-Path $Engines ".venv_pm\Scripts\python.exe"))
        Step "5/8 pm4py 隔離 venv" $ok5 $pms.Name
    } else { Step "5/8 pm4py 隔離 venv" $false "找不到 PmSetup 引擎" }
} else { Step "5/8 pm4py 隔離 venv" $false "無 pwsh 可執行(承上段)" }

# ---- [6/8] graphviz 可攜版(dotsetup 引擎;sha256 驗證)-----------------
$ok6 = $false
if ($Py) {
    & $Py (Join-Path $Engines "workops_graphviz_setup.py") install
    $ok6 = ($LASTEXITCODE -eq 0)
}
Step "6/8 graphviz 可攜版" $ok6 "dotsetup(免 winget/管理員)"

# ---- [7/8] 每日節奏排程(watchtower daily_rhythm;只到產草稿,絕不代寄)--
if ($NoSchedule) {
    Step "7/8 每日節奏排程" $true "略過(-NoSchedule)"
} else {
    $ok7 = $true
    $t16 = "16:00"; $t12 = "12:00"
    try {
        $wt = Get-Content (Join-Path $Engines "watchtower_params.json") -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($wt.daily_rhythm.generate_drafts_time) { $t16 = $wt.daily_rhythm.generate_drafts_time }
        if ($wt.daily_rhythm.reply_deadline_next_day) { $t12 = $wt.daily_rhythm.reply_deadline_next_day }
    } catch { }
    $cmdFile = Join-Path $Root "bin\via-workops.cmd"
    foreach ($t in @(
        @{ tn = "VeritasWorkOps_16點產草稿"; st = $t16; tr = ('"' + $cmdFile + '" silent') },
        @{ tn = "VeritasWorkOps_12點期限刷新"; st = $t12; tr = ('"' + $cmdFile + '" silent') })) {
        schtasks /Create /F /SC DAILY /TN $t.tn /TR $t.tr /ST $t.st | Out-Null
        if ($LASTEXITCODE -ne 0) { $ok7 = $false }
    }
    Step "7/8 每日節奏排程" $ok7 ("{0} 產草稿 / {1} 期限刷新(時間改 watchtower_params.json 後重跑本器)" -f $t16, $t12)
}

# ---- [8/8] 全鏈自測(ENG-032 沙箱五段 = 新機驗收門)---------------------
if ($SkipSelftest) {
    Step "8/8 全鏈自測" $true "略過(-SkipSelftest)"
} elseif ($Py) {
    & $Py (Join-Path $Engines "workops_selftest.py")
    Step "8/8 全鏈自測" ($LASTEXITCODE -eq 0) "FinalGate(詳 out\selftest_report.json)"
} else {
    Step "8/8 全鏈自測" $false "無 Python 可執行(承上段)"
}

# ---- 總結 ---------------------------------------------------------------
$nF = @($Report | Where-Object { $_.gate -eq "FAIL" }).Count
$final = "PASS"; if ($nF -gt 0) { $final = "FAIL" }
$rep = New-Object PSObject -Property @{
    ts = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss"); final_gate = $final; steps = $Report
    note = "紅線:排程只到產草稿,絕不代寄;郵件/分類零觸碰;還原只到暫存。"
}
$rep | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $OutDir "bootstrap_report.json") -Encoding UTF8
Write-Host "-------------------------------------------------------------"
Write-Host ("[總結] 部署 FinalGate = {0}({1}/{2} 步過)→ out\bootstrap_report.json" -f $final, ($Report.Count - $nF), $Report.Count) -ForegroundColor $(if ($nF -eq 0) { "Green" } else { "Red" })
Write-Host "下一步:重開一個新視窗(讓 PATH 生效)→ via-workops all"
if ($final -eq "PASS") { exit 0 } else { exit 1 }
