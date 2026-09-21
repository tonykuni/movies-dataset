# =====================================================================
# Invoke-VIA-VRN-v0101.ps1 —— 啟動 VRN(批677 操作員令「實測 VRN 驗證通過後
#   給我一個啟動 VRN 的 POWERSHELL CODE」)
# =====================================================================
# v0100→v0101(側線 2026-09-21 工作站實錄修;L70 逐次許可=操作員本輪令「更新完 VRN 相關可以進行最後一次實測收尾」,
#   一行修、新版號檔、刪檔即回退):
#   操作員跑 via-vrnrun,V2 印「[用法] plan | run … (收到 'r')」rc=2 —— 六層鏈**根本沒跑**。
#   根因不在鏈,在這裡第 52 行:`$chainArgs = if ($Quick) { @('run','--fast') } else { @('run') }`
#   不帶 -Quick 時 `@('run')` 是單元素陣列,經 if 的輸出管線被 PowerShell **拆成字串 'run'**;
#   之後 `via-vrnchain @chainArgs` 對字串做 splat,字串被逐字元展開 → 鏈收到 r / u / n 三個參數。
#   帶 -Quick 是兩元素陣列不會被拆,所以批677 沒踩到。這是冊上 LL284 同一族
#   (ConvertTo-VIACleanArgs 回單元素陣列時必須包 @())。修法:整個 if 包 @(),單雙元素都是陣列。
# =====================================================================
# 為什麼要有這一支:VRN 的一輪實測是**五個動詞照順序**,少一個就會出現
#   「量到的是另一棵樹」或「頁上的數字是上一輪的」。把順序寫死在這裡,
#   就不必每次去記(L97:要人手打路徑就一定會打錯)。
#
# 它**不裝任何套件、不設任何同意閘**——那兩件是你的手。
#   缺套件或閘沒開,底下的引擎會誠實回 GATED/NODATA,不會假裝跑過。
#
# 用法:
#   .\Invoke-VIA-VRN-v0101.ps1              # 全跑,最後跳出 U/I
#   .\Invoke-VIA-VRN-v0101.ps1 -NoOpen      # 全跑但不跳頁
#   .\Invoke-VIA-VRN-v0101.ps1 -Quick       # 每節點逾時 60s(快掃)
# =====================================================================
[CmdletBinding()]
param(
    [switch]$NoOpen,
    [switch]$Quick
)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$ErrorActionPreference = 'Continue'

# ── 雙副本律(批397):先講清楚這一窗對著哪一棵樹做事。
#    站的位置不決定落點,**本視窗點源的那一份 Register 才決定**。
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$reg = Get-ChildItem -LiteralPath $here -Filter 'Register-VIA-Commands-v*.ps1' -File |
       Sort-Object Name | Select-Object -Last 1
if (-not $reg) {
    Write-Host "  [VRN] FAIL:$here 底下找不到 Register-VIA-Commands-v*.ps1" -ForegroundColor Red
    exit 3
}
. $reg.FullName
Write-Host ("  [VRN] 本窗對著這一棵樹:" + $here) -ForegroundColor Cyan
Write-Host ("  [VRN] 點的冊:" + $reg.Name) -ForegroundColor Cyan
$b = (git -C $here rev-parse --abbrev-ref HEAD 2>$null)
$h = (git -C $here rev-parse --short HEAD 2>$null)
if ($b) { Write-Host ("  [VRN] 分支 " + $b + " · HEAD " + $h) -ForegroundColor DarkGray }

if ($NoOpen) { $env:VIA_NO_OPEN = '1' }

# ── 同意閘:**永不代設**。沒開就把可貼的一行印出來,貼不貼是你的事。
foreach ($g in 'VIA_NET_CONSENT', 'VIA_SCRAPE_CONSENT') {
    if (-not (Get-Item -Path ("env:" + $g) -ErrorAction SilentlyContinue)) {
        Write-Host ("  [閘] " + $g + " 未開 —— 要觸網/擷取的站會判 GATED(缺料,不是壞掉)") -ForegroundColor Yellow
        Write-Host ('       要開就自己貼:$env:' + $g + "='YES'") -ForegroundColor DarkYellow
    }
}

# ── 五步,照順序。次序就是這一支存在的理由(LL272)。
# LL284 同族:if 的輸出經管線會把單元素陣列拆成字串,再 splat 就逐字元展開(v0100 工作站實錄:鏈收到 'r')。整段包 @()。
$chainArgs = @(if ($Quick) { 'run'; '--fast' } else { 'run' })
$steps = @(
    @{ id = 'V1'; name = 'VRN 六層冊重建(冊即鏈;冊釘舊版號就會敲到前一版)'; run = { via-vrnbook build } },
    @{ id = 'V2'; name = 'VRN 六層鏈實測(44 節點;層間依序層內並行)';       run = { via-vrnchain @chainArgs } },
    @{ id = 'V3'; name = '庫價與上漲空間重算(零網路;不重新擷取任何報告)';   run = { via-repairprice --apply } },
    @{ id = 'V4'; name = '驗真矩陣(判對率 + 可判率;兩個都要 100% 才叫準確)'; run = { via-vrnmatrix } },
    @{ id = 'V5'; name = '標準 HTML U/I(左輸入 / 右矩陣四 TAB)';            run = { via-console } }
)

$i = 0
foreach ($s in $steps) {
    $i++
    Write-Host ""
    Write-Host ("  [" + $s.id + "] " + $i + "/" + $steps.Count + "  " + $s.name) -ForegroundColor Cyan
    & $s.run
    Write-Host ("       rc=" + $LASTEXITCODE) -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  [律] 誠實 rc:0 GREEN · 1 RED · 2 NODATA · 3 ABSENT · 4 GATED。" -ForegroundColor DarkGray
Write-Host "       GATED 不是壞掉,是**閘沒開**;NODATA 不是壞掉,是**量不到**。" -ForegroundColor DarkGray
Write-Host "       判對率與可判率**兩個都印**——不許只看好看的那一個。" -ForegroundColor DarkGray
if (-not $NoOpen) {
    Write-Host "  [頁] via-console 已把標準 U/I 落好;要看第一頁給 AI 的彙總:via-unified" -ForegroundColor Green
}
