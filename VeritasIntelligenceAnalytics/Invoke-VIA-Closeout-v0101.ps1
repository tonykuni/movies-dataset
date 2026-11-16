# =====================================================================
# Invoke-VIA-Closeout-v0101.ps1 — 一支 PS 包辦三系統收尾 + 燈號合理性稽核(v0100 一字不動)
# 操作員 2026-11-16:「ONE PS TO HANDLE ALL · 記住要裝加速器 · 要三的獨立流程同步在不影響電腦正常運作 ·
#   在不發生九頭龍風險前提下 · 改成自動完成 · 回來希望看到輸出驗證過跳出 HTML」
#   「紅黃綠燈去檢查其合理性 · 生成一個 PS 指令去檢查三種燈號在各類規範是否合理」
# =====================================================================
# 做什麼(依序;零 Read-Host · 不卡窗 · 全自動):
#   0 九頭龍防護:同一台電腦同時只准一輪(具名互斥鎖);本行程降為低優先權,子行程跟著低(電腦照常可用)
#   1 加速器:PS 模板章 + PS 加速器章(檔頭);Python 端每支引擎自帶加速器橋
#   2 找 Python 3.10+ → 工作樹乾淨才 git pull --ff-only(絕不 stash / reset)
#   3 VCGC 省 Token 第一步
#   4 三系統收尾(VIA_LakeConsole 尾版 closeout):VCGC · VDF · VRN 三條獨立流程「平行」跑,各走自己的入口;
#     子行程最多 3 個同時、逾時整棵樹收掉、不留背景常駐
#   5 燈號合理性稽核(VIA_LampAudit 尾版):每顆紅黃綠燈照規則重算,不合理就點名對應的失敗情境與解法
#   6 全部跑完才自動跳出 HTML 報告(含稽核表);整段記錄存 VIA_Reports\lake\ps_logs
# 只檢查燈號(不重跑):  pwsh -File .\Invoke-VIA-Closeout-v0101.ps1 -LampCheck
# 列 100 條失敗情境:   pwsh -File .\Invoke-VIA-Closeout-v0101.ps1 -LampModes
# 其他參數:-Serve(另開本機操作台)· -Quick(略過三系統啟動)· -Serial(三條流程依序)· -NoPull · -NoOpen
# 不做:不改任何既有 .ps1(L70)· 不裝套件(L19)· 不設同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 是你的手)· 不推送
# 結束碼:0 = 可用且燈都合理 · 1 = 有紅或有不合理的燈 · 2 = 找不到 Python / 操作台 / 報告 · 3 = 另一輪正在跑
# =====================================================================
param([switch]$Serve, [switch]$Quick, [switch]$Serial, [switch]$NoPull, [switch]$NoOpen, [switch]$LampCheck, [switch]$LampModes)
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
$Mutex = $null
$LogOn = $false

function Get-Tail([string]$Dir, [string]$Pat) {
    (Get-ChildItem -Path $Dir -Filter $Pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}
function Write-Step([string]$n, [string]$t) { Write-Host ""; Write-Host ("[" + $n + "] " + $t) -ForegroundColor Cyan }
function Finish([int]$code) {
    if ($LogOn) { try { Stop-Transcript | Out-Null } catch { } }
    if ($Mutex) { try { $Mutex.ReleaseMutex() } catch { }; $Mutex.Dispose() }
    if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }
    exit $code
}

Write-Host "=== VIA 三系統收尾 · Invoke-VIA-Closeout-v0101(平行 · 低優先權 · 燈號稽核)===" -ForegroundColor Cyan
Write-Host ("  VIA 根:" + $VIA)

# --- 0 九頭龍防護 + 不影響電腦 --------------------------------------------
$created = $false
try { $Mutex = New-Object System.Threading.Mutex($true, "Global\VIA_Closeout_v0101", [ref]$created) } catch { $created = $true }
if (-not $created) {
    Write-Host "  [GRAY] 另一輪收尾正在跑 → 本輪不跑(九頭龍防護:同一台同時只准一輪)" -ForegroundColor DarkGray
    $Mutex = $null
    Finish 3
}
try { [System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal; Write-Host "  [GREEN] 本輪以低優先權執行(子行程跟著低;電腦照常可用)" -ForegroundColor Green }
catch { Write-Host "  [YELLOW] 無法調低優先權(照常執行)" -ForegroundColor Yellow }
$LogDir = Join-Path $VIA "VIA_Reports\lake\ps_logs"
try { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null; Start-Transcript -Path (Join-Path $LogDir ("closeout_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")) -Force | Out-Null; $LogOn = $true } catch { }

# --- 1 加速器 ---------------------------------------------------------
Write-Step "1/6" "加速器"
if ($VIACelTplOwn) { Write-Host "  [GREEN] PS7 模板(Celeritas)已載入,結束時還原" -ForegroundColor Green }
elseif ($PSVersionTable.PSVersion.Major -ge 7) { Write-Host "  [YELLOW] PS7 模板檔不在(supportive modules\ps7\VeritasCeleritas.PS7.ps1),照常執行" -ForegroundColor Yellow }
else { Write-Host "  [YELLOW] 這是 PowerShell 5.1:PS7 模板只在 pwsh 7 載入(用 pwsh 執行可得加速)" -ForegroundColor Yellow }
if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) { Write-Host "  [GREEN] PS 加速器模組已載入" -ForegroundColor Green }

# --- 2 Python + 同步 ---------------------------------------------------
Write-Step "2/6" "找 Python(3.10 以上)· 同步"
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
$env:VIA_FROM_VCGC = "YES"                       # 只在本行程內;不寫進系統環境
$env:PYTHONIOENCODING = "utf-8"
$Audit = Get-Tail (Join-Path $VIA "docs\handoff\ai") "VIA_LampAudit_v*.py"

if ($LampModes) {
    if (-not $Audit) { Write-Host "  [RED] 找不到 docs\handoff\ai\VIA_LampAudit_v*.py" -ForegroundColor Red; Finish 2 }
    & $PyExe @PyArgs $Audit modes
    Finish 0
}
if ($LampCheck) {
    Write-Step "燈號" "只檢查燈號合不合理(讀最近一次收尾報告,不重跑)"
    if (-not $Audit) { Write-Host "  [RED] 找不到 docs\handoff\ai\VIA_LampAudit_v*.py" -ForegroundColor Red; Finish 2 }
    & $PyExe @PyArgs $Audit audit
    $code = $LASTEXITCODE
    if ($code -eq 0) { Write-Host "  [合理] 每顆燈都對得上規則" -ForegroundColor Green }
    elseif ($code -eq 1) { Write-Host "  [不合理] 上面打 ✗ 的燈與規則不符,依所附解法處理" -ForegroundColor Red }
    else { Write-Host "  [GRAY] 沒有可稽核的報告:先不帶參數跑一次收尾" -ForegroundColor DarkGray }
    Finish $code
}

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
Write-Step "3/6" "VCGC 省 Token 第一步"
$Console = Get-Tail (Join-Path $VIA "supportive modules\registry") "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"
if ($Console) {
    $card = & $PyExe @PyArgs $Console token 2>&1
    Write-Host ("  " + ($card | Select-Object -First 1))
} else {
    Write-Host "  [YELLOW] 找不到 VCGC 主控台(略過這一步;收尾仍會照實判燈)" -ForegroundColor Yellow
}

# --- 4 + 5 三系統平行收尾 + 燈號稽核 ---------------------------------------
Write-Step "4/6" "三系統收尾(三條獨立流程平行 · 各走自己的入口)+ 燈號合理性稽核"
$Lake = Get-Tail (Join-Path $VIA "docs\handoff\ai") "VIA_LakeConsole_v*.py"
if (-not $Lake) {
    Write-Host "  [RED] 找不到 docs\handoff\ai\VIA_LakeConsole_v*.py(本機版本太舊?先同步)" -ForegroundColor Red
    Finish 2
}
Write-Host ("  操作台:" + (Split-Path $Lake -Leaf))
$runArgs = @($Lake, "closeout", "--no-open")
if ($Quick) { $runArgs += "--quick" }
if ($Serial) { $runArgs += "--serial" }
Push-Location $VIA
& $PyExe @PyArgs @runArgs
$rcClose = $LASTEXITCODE
Pop-Location
if ($rcClose -eq 2) { Write-Host "  [GRAY] 另一輪收尾正在跑或沒有資料(看上面訊息)" -ForegroundColor DarkGray }

# --- 6 總結 + 跳出 HTML -------------------------------------------------
Write-Step "5/6" "總結"
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
if ($rep.audit) {
    $ac = $color[[string]$rep.audit.lamp]; if (-not $ac) { $ac = "White" }
    Write-Host ("  燈號稽核 · " + $rep.audit.verdict + " · 合理 " + $rep.audit.counts.reasonable + " / " + $rep.audit.counts.steps) -ForegroundColor $ac
    foreach ($o in $rep.audit.non_green_by_owner.PSObject.Properties) { Write-Host ("    " + $o.Name + ":" + (@($o.Value) -join "、")) }
    if ([int]$rep.audit.counts.unreasonable -gt 0) { $Rc = 1 }
}
if ($rep.lamp -eq "RED") { $Rc = 1 }

Write-Step "6/6" "跳出 HTML"
if ($NoOpen) { Write-Host ("  [略] -NoOpen;報告:" + $ReportHtml) }
else {
    try { Invoke-Item -LiteralPath $ReportHtml; Write-Host ("  [GREEN] 已開:" + $ReportHtml) -ForegroundColor Green }
    catch { Write-Host ("  [YELLOW] 開頁失敗,請手動開:" + $ReportHtml) -ForegroundColor Yellow }
}
if ($Serve) {
    Write-Host "  [開] 本機操作台(另開視窗;按「三系統收尾」可重跑)" -ForegroundColor Cyan
    try { Start-Process -FilePath $PyExe -ArgumentList (@($PyArgs) + @(('"' + $Lake + '"'), "serve")) -WorkingDirectory $VIA -WindowStyle Minimized | Out-Null }
    catch { Write-Host "  [YELLOW] 操作台沒開起來:手動執行 python docs\handoff\ai\VIA_LakeConsole_v0103.py serve" -ForegroundColor Yellow }
}
Write-Host ""
Write-Host "[完成] 黃燈多半是你的手(例:VDF 同意閘未開)或他系統要補正本;紅燈與不合理的燈,報告頁都附了解法。" -ForegroundColor Green
Finish $Rc
