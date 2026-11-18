# =====================================================================
# Invoke-VIA-VrnVdf-HandleAll-v0100.ps1 — 一個指令:進環境 → 同步 → VRN → VDF → 總結
# 操作員 2026-11-16:「Integrate to one ps to enter the env and handle all」
# =====================================================================
# 做什麼(由上往下,一步失敗照實記、不假裝成功):
#   1 定位:本檔所在的 VeritasIntelligenceAnalytics 夾 = 工作樹(不寫死任何使用者路徑)
#   2 同步:git fetch + checkout --detach(有未提交改動會被 git 自己擋下,本檔不強制、不 stash、不 reset)
#   3 進環境(只影響這個視窗):VIA_ROOT · PYTHONPATH 最前面放本工作樹的啟動鉤 · UTF-8 · 不緩衝
#   4 VRN:VRN_MDL260_SafeParallelLaunch 尾版 run --source <樣本夾>
#   5 VDF:VDF_MDL022_SafeParallelLaunch 尾版 run [--data-home <資料家>]
#   6 總結:讀兩支啟動器自己寫的 *_Launch_latest.json,列每支流程的燈;日誌留在 VIA_Reports\handle_all
# 不做的:不設同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 只由操作員自己在視窗設)· 不安裝套件 · 不改任何檔。
# 用法(PowerShell 7):
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\Invoke-VIA-VrnVdf-HandleAll-v0100.ps1 -Source "<樣本夾>"
#   -Do all|vrn|vdf|preflight   -DataHome "<VDF 資料家>"   -NoSync   -NoOpen   -Branch <分支>
# rc:0 全綠 · 2 有黃 · 1 有紅或有步驟沒跑成。
# 註:本檔沒有內嵌 PS 加速器模板;加速器由它呼叫的兩支 Python 啟動器自己帶(橋 + 降壓)。
# =====================================================================
[CmdletBinding()]
param(
    [string]$Source = '',
    [string]$DataHome = '',
    [ValidateSet('all', 'vrn', 'vdf', 'preflight')][string]$Do = 'all',
    [string]$Branch = 'claude/optimistic-goodall-yhalc5',
    [switch]$NoSync,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Continue'
$Tag = 'Invoke-VIA-VrnVdf-HandleAll v0100'
$Via = $PSScriptRoot
$Repo = Split-Path $Via -Parent
$Steps = New-Object System.Collections.ArrayList

function Add-Step([string]$Name, [string]$Lamp, [string]$Detail) {
    $null = $Steps.Add([pscustomobject]@{ Step = $Name; Lamp = $Lamp; Detail = $Detail })
    Write-Host ("[{0}] {1} · {2}" -f $Lamp, $Name, $Detail)
}

function Get-Tail([string]$Folder, [string]$Stem) {
    $hit = Get-ChildItem -LiteralPath $Folder -Filter ($Stem + '_v*.py') -File -ErrorAction SilentlyContinue |
        Where-Object { $_.BaseName -match '_v(\d+)$' } |
        Sort-Object { [int]([regex]::Match($_.BaseName, '_v(\d+)$').Groups[1].Value) } |
        Select-Object -Last 1
    if ($hit) { return $hit.FullName }
    return $null
}

function Get-LampFromRc([int]$Rc) {
    if ($Rc -eq 0) { return 'GREEN' }
    if ($Rc -eq 2) { return 'YELLOW' }
    return 'RED'
}

Write-Host "=== $Tag ==="
if (-not (Test-Path -LiteralPath (Join-Path $Via 'functional modules'))) {
    Add-Step '1 定位' 'RED' "本檔不在 VeritasIntelligenceAnalytics 夾裡:$Via"
    exit 1
}
Add-Step '1 定位' 'GREEN' $Via

# ---------- 2 同步 ----------
if ($NoSync) {
    Add-Step '2 同步' 'INFO' '-NoSync:照現在的檔跑'
}
elseif (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Add-Step '2 同步' 'YELLOW' '找不到 git → 照現在的檔跑'
}
else {
    & git -C $Repo fetch origin $Branch 2>&1 | ForEach-Object { Write-Host "  $_" }
    $fetchRc = $LASTEXITCODE
    if ($fetchRc -ne 0) {
        Add-Step '2 同步' 'YELLOW' "git fetch rc $fetchRc → 照現在的檔跑"
    }
    else {
        & git -C $Repo checkout --detach FETCH_HEAD 2>&1 | ForEach-Object { Write-Host "  $_" }
        $coRc = $LASTEXITCODE
        $head = (& git -C $Repo rev-parse --short HEAD 2>$null)
        if ($coRc -eq 0) { Add-Step '2 同步' 'GREEN' "HEAD $head" }
        else { Add-Step '2 同步' 'YELLOW' "checkout 被 git 擋下(rc $coRc;多半是本機有未提交改動或同名未追蹤檔)→ 照現在的檔跑,HEAD $head" }
    }
}

# ---------- 3 進環境(只影響這個視窗)----------
$boot = Join-Path $Via 'supportive modules\bootstrap'
$env:VIA_ROOT = $Via
$parts = @($boot)
if ($env:PYTHONPATH) { $parts += ($env:PYTHONPATH -split ';' | Where-Object { $_ -and ($_ -ne $boot) }) }
$env:PYTHONPATH = ($parts -join ';')
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'
if ($NoOpen) { $env:VIA_NO_OPEN = '1' }

$PyExe = $null
$PyPre = @()
if (Get-Command py -ErrorAction SilentlyContinue) { $PyExe = 'py'; $PyPre = @('-3') }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $PyExe = 'python' }
if (-not $PyExe) {
    Add-Step '3 進環境' 'RED' '找不到 py 也找不到 python'
    exit 1
}
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$hook = (& $PyExe @PyPre -c "import sys, sitecustomize; print(sys.version.split()[0] + ' | ' + sitecustomize.__file__)" 2>&1 | Select-Object -Last 1)
$startSec = [math]::Round($sw.Elapsed.TotalSeconds, 1)
$hookLamp = 'GREEN'
if ($LASTEXITCODE -ne 0) { $hookLamp = 'YELLOW' }
elseif ($startSec -gt 15) { $hookLamp = 'YELLOW' }
Add-Step '3 進環境' $hookLamp "Python 與啟動鉤:$hook · 啟動 $startSec 秒"
$gates = @()
foreach ($g in 'VIA_NET_CONSENT', 'VIA_SCRAPE_CONSENT') {
    $v = [Environment]::GetEnvironmentVariable($g, 'Process')
    if ($v -and ($v.ToUpper() -in @('YES', '1', 'TRUE'))) { $gates += "$g=SET" } else { $gates += "$g=UNSET" }
}
Add-Step '3 同意閘(只看,不代設)' 'INFO' (($gates -join ' · ') + ' → 沒開時 VDF 不出網擷取、VRN 不補市場資料')

$logDir = Join-Path $Via 'VIA_Reports\handle_all'
$null = New-Item -ItemType Directory -Force -Path $logDir
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function Invoke-Launcher([string]$Name, [string]$Script, [string[]]$Rest) {
    if (-not $Script) {
        Add-Step $Name 'RED' '找不到啟動器尾版(同步沒成功?)'
        return 1
    }
    $log = Join-Path $logDir ("{0}_{1}.log" -f ($Name -replace '[^A-Za-z0-9]', ''), $stamp)
    Write-Host ("--- {0}:{1} {2}" -f $Name, (Split-Path $Script -Leaf), ($Rest -join ' '))
    & $PyExe @PyPre $Script @Rest 2>&1 | Tee-Object -FilePath $log | Out-Host    # 送到畫面,不混進函式回傳值
    $rc = $LASTEXITCODE
    Add-Step $Name (Get-LampFromRc $rc) "rc $rc · 日誌 $log"
    return $rc
}

$verb = 'run'
if ($Do -eq 'preflight') { $verb = 'check' }
$rcs = @()

# ---------- 4 VRN ----------
if ($Do -in @('all', 'vrn', 'preflight')) {
    $vrn = Get-Tail (Join-Path $Via 'functional modules\VRN') 'VRN_MDL260_SafeParallelLaunch'
    $vrnVerb = $verb
    if ($Do -eq 'preflight') { $vrnVerb = 'preflight' }
    $rest = @($vrnVerb)
    if ($Source) {
        if (Test-Path -LiteralPath $Source) { $rest += @('--source', $Source) }
        else { Add-Step '4 VRN 樣本夾' 'RED' "$Source 不存在"; $rcs += 1 }
    }
    else { Add-Step '4 VRN 樣本夾' 'YELLOW' '沒給 -Source → 管理器擷取不跑,文件整輪用它自己記得的來源' }
    if ($NoOpen) { $rest += '--no-open' }
    $rcs += (Invoke-Launcher '4 VRN' $vrn $rest)
}

# ---------- 5 VDF ----------
if ($Do -in @('all', 'vdf', 'preflight')) {
    $vdf = Get-Tail (Join-Path $Via 'functional modules\VDF') 'VDF_MDL022_SafeParallelLaunch'
    $rest = @($verb)
    if ($DataHome) { $rest += @('--data-home', $DataHome) }
    if ($NoOpen) { $rest += '--no-open' }
    $rcs += (Invoke-Launcher '5 VDF' $vdf $rest)
}

# ---------- 6 總結 ----------
Write-Host ''
Write-Host "=== $Tag 總結 ==="
foreach ($sys in 'vrn', 'vdf') {
    $jf = Join-Path $Via ("VIA_Reports\{0}\launch\{1}_Launch_latest.json" -f $sys, $sys.ToUpper())
    if (-not (Test-Path -LiteralPath $jf)) { continue }
    try {
        $j = Get-Content -LiteralPath $jf -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Host ("{0} · {1} · {2} · {3}" -f $sys.ToUpper(), $j.lamp, $j.engine, $j.at)
        if ($j.run -and $j.run.jobs) {
            foreach ($job in $j.run.jobs) { Write-Host ("    {0,-7}{1,-18}rc {2}  {3}s" -f $job.lamp, $job.id, $job.rc, $job.sec) }
        }
        foreach ($row in $j.env.rows) {
            if (($row.lamp -in @('RED', 'YELLOW')) -and ($row.item -like '*結果*' -or $row.item -like '*待看*' -or $row.item -like '*支援工具*')) {
                Write-Host ("    {0,-7}{1} · {2}" -f $row.lamp, $row.item, $row.detail)
            }
        }
    }
    catch { Write-Host "    讀不到 $jf :$($_.Exception.Message)" }
}
Write-Host ''
$Steps | Format-Table -AutoSize -Wrap | Out-String | Write-Host
$sumFile = Join-Path $logDir ("HandleAll_{0}.txt" -f $stamp)
$Steps | Format-Table -AutoSize -Wrap | Out-String | Set-Content -LiteralPath $sumFile -Encoding UTF8
Write-Host "步驟表:$sumFile(把這個檔或上面的總結貼回)"

$final = 0
$lamps = @($Steps | ForEach-Object { $_.Lamp })
if ($lamps -contains 'YELLOW') { $final = 2 }
if (($lamps -contains 'RED') -or ($rcs | Where-Object { $_ -ne 0 -and $_ -ne 2 })) { $final = 1 }
exit $final
