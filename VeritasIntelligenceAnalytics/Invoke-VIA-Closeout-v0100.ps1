# =====================================================================
# Invoke-VIA-Closeout-v0100.ps1 — 一支 PS 包辦三系統收尾(操作員 2026-11-16「ONE PS TO HANDLE ALL」)
# =====================================================================
# 做什麼(依序;零 Read-Host · 不卡窗):
#   1 找 VIA 根與 Python(py -3 → python → python3;要 3.10 以上)
#   2 同步:工作樹乾淨才 git pull --ff-only;有本機改動就略過並照實說(絕不 stash / reset)
#   3 VCGC 省 Token 第一步(token 卡)
#   4 三系統收尾:VCGC · VDF · VRN 各走自己的入口自測 → 兩套管理器自報 + 自檢 → SSOT 覆蓋
#      (= python docs\handoff\ai\VIA_LakeConsole_v*.py closeout 尾版;全部跑完才自動開收尾報告頁)
#   5 印三系統燈號總結;加 -Serve 再開本機操作台(按鈕可重跑任一步)
# 不做:不改任何既有 .ps1(L70)· 不裝套件(L19)· 不設同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是你的手)· 不推送
# 用法:
#   pwsh -File .\Invoke-VIA-Closeout-v0100.ps1            全流程,跑完開報告頁
#   pwsh -File .\Invoke-VIA-Closeout-v0100.ps1 -Serve     另外開本機操作台
#   pwsh -File .\Invoke-VIA-Closeout-v0100.ps1 -Quick     略過三系統啟動,只跑自報 / 自檢 / 覆蓋
#   參數:-NoPull(不同步)· -NoOpen(不開頁)
# 結束碼:0 = 綠或黃(可用)· 1 = 有紅 · 2 = 找不到 Python / 操作台 / 報告
# =====================================================================
param([switch]$Serve, [switch]$Quick, [switch]$NoPull, [switch]$NoOpen)
# CELERITAS-TEMPLATE-JOIN v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====
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
$ErrorActionPreference = "Continue"
$VIA = Split-Path -Parent $MyInvocation.MyCommand.Path
$Rc = 0

function Get-Tail([string]$Dir, [string]$Pat) {
    (Get-ChildItem -Path $Dir -Filter $Pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}
function Write-Step([string]$n, [string]$t) { Write-Host ""; Write-Host ("[" + $n + "] " + $t) -ForegroundColor Cyan }
function Finish([int]$code) {
    if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }
    exit $code
}

Write-Host "=== VIA 三系統收尾 · Invoke-VIA-Closeout-v0100 ===" -ForegroundColor Cyan
Write-Host ("  VIA 根:" + $VIA)

# --- 1 Python ---------------------------------------------------------
Write-Step "1/5" "找 Python(3.10 以上)"
$PyExe = $null; $PyArgs = @(); $PyVer = ""
foreach ($cand in @(@("py", @("-3")), @("python", @()), @("python3", @()))) {
    $exe = $cand[0]; $pre = @($cand[1])
    if (Get-Command $exe -ErrorAction SilentlyContinue) {
        $ver = & $exe @pre -c "import sys;print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($ver -and ([version]$ver -ge [version]"3.10")) { $PyExe = $exe; $PyArgs = $pre; $PyVer = $ver; break }
    }
}
if (-not $PyExe) {
    Write-Host "  [RED] 找不到 3.10 以上的 Python(py -3 / python / python3 都沒有)。本支不代裝,請先裝好再跑。" -ForegroundColor Red
    Finish 2
}
Write-Host ("  [GREEN] " + $PyExe + " " + ($PyArgs -join " ") + " · Python " + $PyVer) -ForegroundColor Green

# --- 2 同步 -----------------------------------------------------------
Write-Step "2/5" "同步(只做 fast-forward)"
if ($NoPull) {
    Write-Host "  [略] -NoPull:不同步"
} elseif (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "  [略] 這台沒有 git:不同步" -ForegroundColor Yellow
} else {
    $branch = git -C $VIA branch --show-current 2>$null
    $dirty = git -C $VIA status --porcelain --untracked-files=no 2>$null
    if ($dirty) {
        Write-Host ("  [YELLOW] 分支 " + $branch + " 有本機改動 → 不拉(不 stash、不 reset;先處理改動再跑)") -ForegroundColor Yellow
    } else {
        git -C $VIA pull --ff-only 2>&1 | ForEach-Object { Write-Host ("    " + $_) }
        if ($LASTEXITCODE -eq 0) { Write-Host ("  [GREEN] 分支 " + $branch + " 已同步") -ForegroundColor Green }
        else { Write-Host ("  [YELLOW] 分支 " + $branch + " 無法 fast-forward(照用本機版本續跑)") -ForegroundColor Yellow }
    }
}

# --- 3 VCGC 省 Token 第一步 ---------------------------------------------
Write-Step "3/5" "VCGC 省 Token 第一步"
$env:VIA_FROM_VCGC = "YES"                       # 只在本行程內;不寫進系統環境
$Console = Get-Tail (Join-Path $VIA "supportive modules\registry") "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
if ($Console) {
    $card = & $PyExe @PyArgs $Console token 2>&1
    Write-Host ("  " + ($card | Select-Object -First 1))
} else {
    Write-Host "  [YELLOW] 找不到 VCGC 主控台(略過這一步;收尾仍會照實判燈)" -ForegroundColor Yellow
}

# --- 4 三系統收尾 -------------------------------------------------------
Write-Step "4/5" "三系統收尾(VCGC · VDF · VRN 各走自己的入口)"
$Lake = Get-Tail (Join-Path $VIA "docs\handoff\ai") "VIA_LakeConsole_v*.py"
if (-not $Lake) {
    Write-Host "  [RED] 找不到 docs\handoff\ai\VIA_LakeConsole_v*.py(本機版本太舊?先同步)" -ForegroundColor Red
    Finish 2
}
Write-Host ("  操作台:" + (Split-Path $Lake -Leaf))
$runArgs = @($Lake, "closeout")
if ($Quick) { $runArgs += "--quick" }
if ($NoOpen) { $runArgs += "--no-open" }
Push-Location $VIA
& $PyExe @PyArgs @runArgs
Pop-Location

# --- 5 總結 -----------------------------------------------------------
Write-Step "5/5" "總結"
$ReportJson = Join-Path $VIA "VIA_Reports\lake\CLOSEOUT_3SYS_latest.json"
$ReportHtml = Join-Path $VIA "VIA_Reports\lake\CLOSEOUT_3SYS_latest.html"
if (-not (Test-Path -LiteralPath $ReportJson)) {
    Write-Host "  [RED] 收尾報告沒有產出(看上面第 4 步的訊息)" -ForegroundColor Red
    Finish 2
}
$rep = Get-Content -LiteralPath $ReportJson -Raw -Encoding UTF8 | ConvertFrom-Json
$color = @{ GREEN = "Green"; YELLOW = "Yellow"; RED = "Red"; GRAY = "DarkGray" }
foreach ($p in $rep.systems.PSObject.Properties) {
    $c = $color[[string]$p.Value.lamp]; if (-not $c) { $c = "White" }
    Write-Host ("  " + $p.Name.PadRight(5) + " " + ([string]$p.Value.lamp).PadRight(7) + " " + (@($p.Value.notes) -join " · ")) -ForegroundColor $c
}
$c = $color[[string]$rep.lamp]; if (-not $c) { $c = "White" }
Write-Host ("  總燈 " + $rep.lamp + " · " + $rep.verdict + " · " + $rep.why) -ForegroundColor $c
Write-Host ("  報告:" + $ReportHtml)
if ($rep.lamp -eq "RED") { $Rc = 1 }

if ($Serve) {
    Write-Host ""
    Write-Host "  [開] 本機操作台(另開視窗;按「三系統收尾」可重跑)" -ForegroundColor Cyan
    try { Start-Process -FilePath $PyExe -ArgumentList (@($PyArgs) + @(('"' + $Lake + '"'), "serve")) -WorkingDirectory $VIA -WindowStyle Minimized | Out-Null }
    catch { Write-Host "  [YELLOW] 操作台沒開起來:手動執行 python docs\handoff\ai\VIA_LakeConsole_v0102.py serve" -ForegroundColor Yellow }
}
Write-Host ""
Write-Host "[完成] 黃燈多半是你的手(例:VDF 同意閘未開);紅燈打開報告看最後一行判決。" -ForegroundColor Green
Finish $Rc
