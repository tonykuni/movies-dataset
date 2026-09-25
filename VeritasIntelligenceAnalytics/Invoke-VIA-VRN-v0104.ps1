# =====================================================================
# Invoke-VIA-VRN-v0104.ps1 —— 啟動 VRN(批677 操作員令「實測 VRN 驗證通過後
#   給我一個啟動 VRN 的 POWERSHELL CODE」)
# =====================================================================
# v0103→v0104(批731 操作員 2026-09-24「PS PY檔案都要依規定裝加速器  剛剛跑好慢」「自測報告要自動跳出來」;
#   L70 逐次許可=這兩道令;新版號檔,刪檔即回退;v0103 一字未動):
#   工作站實錄:第六步(106 份實檔自測迴圈)撞 Invoke-VIAPython 的 1800 秒保底天花板被停(rc 124),報告沒生、也沒跳出來;
#   Celeritas 模板「未接」(Z137:正主首載在 StrictMode 下炸,同批修好)。
#   ① 第六步天花板給 3600 秒(你自己設了 $env:VIA_PY_TIMEOUT_SEC 就照你的);迴圈本身同批已快很多
#      (整批入庫分給加速器預算的工作行程、每頁只解析一次、G08 冪等改抽 12 檔)。這是保底,不是判它壞。
#   ② 跑完**自動跳出自測報告頁**(VRN_AutoTest_Report.html),走 via-open——只用瀏覽器 exe(Edge/Chrome/Firefox),
#      永不經 .html 預設程式(工作站是 VS Code,批366/378);-NoOpen 照舊不跳。報告頁沒生出來就照實講。其餘一字不動。
# v0102→v0103(批728 操作員令「重整 VRN 實測修正到成功」+ 沿用令「"C:\測試樣本報告" 實測實修正直到成功」;
#   L70 逐次許可=這兩道令;新版號檔,刪檔即回退;v0102 一字未動):
#   +V6 VRN 實檔自測迴圈(functional modules\VRN\engine\VRN_AutoTestLoop.py,12 閘)——姊妹倉 2026-09-23 在 106 份
#   實檔上跑到 FAIL 0 的那一套,批728 搬回母倉正位後由這一步直接敲。樣本預設 C:\測試樣本報告;夾不在=改跑合成語料
#   並**講明不是實測**;-Truth 給人工真值檔才開 G11;落點 VIA_Reports\vrn_autotest\<時間>(不入 git)。
#   迴圈每檔印 [進度] k/K,Invoke-VIAPython 照它畫第六步的真百分比。-NoAutoTest 跳過第六步。
# v0101→v0102(批694 操作員三令「卡斷 · 25 個加速器 · 動態進度條及百分比」;L70 逐次許可=這三道令;新版號檔,刪檔即回退):
#   ① 起跑先印 `[加速器] N/25 冊在位`(讀 $global:VIA_ACCEL25;模組缺席就講缺席,不點假燈);
#   ② 五步走一條**真百分比**的動態條(Write-Progress Id 11:[Vk] k/5 · xx% · 經過秒),每步起跑印 `[進度] k/5 …` 一行
#      (啟動器協定:任何外層包裝都能照這行畫百分比;Invoke-VIAPython 在每一步裡面另畫引擎自己的 n/N);
#   ③ 每步印耗時秒數,收尾印五步總表(rc · 秒)——「卡斷」與「在算」從此分得出來。其餘一字不動。
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
#   .\Invoke-VIA-VRN-v0104.ps1              # 全跑(六步),最後跳出自測報告頁
#   .\Invoke-VIA-VRN-v0104.ps1 -NoOpen      # 全跑但不跳頁
#   .\Invoke-VIA-VRN-v0104.ps1 -Quick       # 每節點逾時 60s(快掃)
#   .\Invoke-VIA-VRN-v0104.ps1 -Samples 'D:\另一夾' -Truth 'C:\VRN_Truth\real_truth.json'   # 換樣本夾 + 開真值閘
#   .\Invoke-VIA-VRN-v0104.ps1 -NoAutoTest  # 只跑前五步
# =====================================================================
[CmdletBinding()]
param(
    [switch]$NoOpen,
    [switch]$Quick,
    [string]$Samples = 'C:\測試樣本報告',
    [string]$Truth = '',
    [int]$Rounds = 3,
    [switch]$NoAutoTest
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
# ── 批694:25 個加速器——讀冊上真有幾格,不點假燈
$accel = Get-Variable -Name VIA_ACCEL25 -Scope Global -ValueOnly -ErrorAction SilentlyContinue
if ($accel) { Write-Host ("  [加速器] " + [int]$accel.Count + "/25 冊在位(VIA_PS_Accel_Module;每一步 python 都經 Invoke-VIAPython 帶著跑)") -ForegroundColor DarkCyan }
else { Write-Host "  [加速器] 模組缺席(supportive modules\VIA_PS_Accel_Module.ps1 沒點到;不影響跑,只是沒加速)" -ForegroundColor Yellow }

# ===== [CELERITAS-TEMPLATE-JOIN v1] L102(批715 操作員令;rank 2):AI 產出的 .ps1 一律接 Celeritas 模板 =====
#   契約:只動 $PID · 關閉即還原 · 不改系統檔 · ErrorAction Continue。
#   模板在**自己的模組範圍**點源(New-Module):它的 Set-StrictMode 與 $script: 狀態都關在裡面,不外溢到本支與
#   Register 的函式(外溢會讓前五步的舊碼在嚴格模式下炸;批728 容器實測:直接點源就外溢)。
#   它要 PS7——PS 5.1 上不接,照實印一行,**不擋跑**。本支是新版號檔,刪檔即回退。
#   批728 實測:模組 VeritasCeleritas.PS7.ps1 第 24 行在嚴格模式下讀未設的 $script:CeleritasPS7,**第一次載入就炸**;
#   第 24 行改掉後第 83 行 `OFS = $OFS` 也炸(掉球 Z137,兩行改法已在沙盒副本實測;修它是改 .ps1,L70 候操作員許可)。
#   炸的時候這裡照實印「未接」與原因,不擋跑;修好就自動接上。
$celeritasTpl = Join-Path $here 'supportive modules\ps7\VeritasCeleritas.PS7.Template.ps1'
$celeritasJoin = $null; $celeritasWhy = ''
if ($PSVersionTable.PSVersion.Major -ge 7 -and (Test-Path -LiteralPath $celeritasTpl)) {
    try {
        New-Module -Name VIACeleritasJoin -ArgumentList $celeritasTpl -ScriptBlock {
            param($tplPath)
            . $tplPath
            Export-ModuleMember -Function Test-CeleritasJoin, Restore-CeleritasPS7
        } | Import-Module -Force -ErrorAction Stop
        $celeritasJoin = Test-CeleritasJoin
    } catch { $celeritasJoin = $null; $celeritasWhy = ($_.Exception.Message -split "`n")[0] }
}
if ($celeritasJoin -and $celeritasJoin.Joined) {
    Write-Host ("  [Celeritas] 模板已接(" + $celeritasJoin.Marker + " · 只動本行程 · 關閉即還原)") -ForegroundColor DarkCyan
} elseif ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Host ("  [Celeritas] 本窗是 PowerShell " + $PSVersionTable.PSVersion + ",模板要 PS7 —— 未接(不擋跑)") -ForegroundColor Yellow
} else {
    Write-Host ("  [Celeritas] 模板未接(" + $(if ($celeritasWhy) { $celeritasWhy } else { 'supportive modules\ps7\ 缺件' }) + ";掉球 Z137;不擋跑)") -ForegroundColor Yellow
}
# ===== [CELERITAS-TEMPLATE-JOIN:END] =====

if ($NoOpen) { $env:VIA_NO_OPEN = '1' }

# ── 同意閘:**永不代設**。沒開就把可貼的一行印出來,貼不貼是你的事。
foreach ($g in 'VIA_NET_CONSENT', 'VIA_SCRAPE_CONSENT') {
    if (-not (Get-Item -Path ("env:" + $g) -ErrorAction SilentlyContinue)) {
        Write-Host ("  [閘] " + $g + " 未開 —— 要觸網/擷取的站會判 GATED(缺料,不是壞掉)") -ForegroundColor Yellow
        Write-Host ('       要開就自己貼:$env:' + $g + "='YES'") -ForegroundColor DarkYellow
    }
}

# ── 五步(+批728 第六步),照順序。次序就是這一支存在的理由(LL272)。
# LL284 同族:if 的輸出經管線會把單元素陣列拆成字串,再 splat 就逐字元展開(v0100 工作站實錄:鏈收到 'r')。整段包 @()。
$chainArgs = @(if ($Quick) { 'run'; '--fast' } else { 'run' })
$steps = @(
    @{ id = 'V1'; name = 'VRN 六層冊重建(冊即鏈;冊釘舊版號就會敲到前一版)'; run = { via-vrnbook build } },
    @{ id = 'V2'; name = 'VRN 六層鏈實測(冊上節點全跑;批728 起含第二血統總驗;層間依序層內並行)';       run = { via-vrnchain @chainArgs } },
    @{ id = 'V3'; name = '庫價與上漲空間重算(零網路;不重新擷取任何報告)';   run = { via-repairprice --apply } },
    @{ id = 'V4'; name = '驗真矩陣(判對率 + 可判率;兩個都要 100% 才叫準確)'; run = { via-vrnmatrix } },
    @{ id = 'V5'; name = '標準 HTML U/I(左輸入 / 右矩陣四 TAB)';            run = { via-console } }
)
# ── 批728 第六步:實檔自測迴圈(12 閘)。樣本夾不在就講明「合成語料,不是實測」,不假裝。
$autoLoop = Join-Path $here 'functional modules\VRN\engine\VRN_AutoTestLoop.py'
$autoOut = Join-Path $here ('VIA_Reports\vrn_autotest\' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
$autoArgs = @('--out', $autoOut, '--rounds', [string]$Rounds)
if (Test-Path -LiteralPath $Samples -PathType Container) {
    $autoArgs += @('--samples', $Samples)
    $autoName = 'VRN 實檔自測迴圈(12 閘;樣本 ' + $Samples + ')'
} else {
    $autoArgs += @('--synthetic')
    $autoName = 'VRN 自測迴圈(12 閘;樣本夾 ' + $Samples + ' 不在 → 合成語料,**不是實測**)'
}
if ($Truth) {
    if (Test-Path -LiteralPath $Truth -PathType Leaf) { $autoArgs += @('--truth', $Truth) }
    else { Write-Host ('  [V6] 真值檔不在:' + $Truth + ' —— G11 真值閘略過(不是壞掉,是沒有真值)') -ForegroundColor Yellow }
}
if (-not $NoAutoTest) {
    if (Test-Path -LiteralPath $autoLoop -PathType Leaf) {
        # v0104:第六步保底天花板 3600 秒;你設了 $env:VIA_PY_TIMEOUT_SEC 就傳 0 = 照你的
        $v6Cap = if ($env:VIA_PY_TIMEOUT_SEC) { 0 } else { 3600 }
        $steps += @{ id = 'V6'; name = $autoName; run = { Invoke-VIAPython -Python (Get-VIAEnvPython "vrn") -TimeoutSec $v6Cap $autoLoop @autoArgs } }
    } else {
        Write-Host ('  [V6] 自測迴圈不在:' + $autoLoop + '(git pull 後再跑)') -ForegroundColor Yellow
    }
}

$i = 0; $t0all = Get-Date; $summary = @()
foreach ($s in $steps) {
    $i++
    $pct = [int](100 * ($i - 1) / $steps.Count)
    Write-Progress -Id 11 -Activity ("via-vrnrun " + $steps.Count + " 步(25 加速器)") -Status ("[" + $s.id + "] " + $i + "/" + $steps.Count + " · " + $pct + "% · " + $s.name) -PercentComplete $pct
    Write-Host ""
    Write-Host ("  [進度] " + $i + "/" + $steps.Count + " [" + $s.id + "] " + $s.name) -ForegroundColor DarkCyan
    Write-Host ("  [" + $s.id + "] " + $i + "/" + $steps.Count + "  " + $s.name) -ForegroundColor Cyan
    $t0 = Get-Date
    & $s.run
    $rcStep = $LASTEXITCODE; $secStep = [int]((Get-Date) - $t0).TotalSeconds
    Write-Host ("       rc=" + $rcStep + " · " + $secStep + "s") -ForegroundColor DarkGray
    $summary += [pscustomobject]@{ step = $s.id; rc = $rcStep; secs = $secStep }
}
Write-Progress -Id 11 -Activity ("via-vrnrun " + $steps.Count + " 步(25 加速器)") -Completed
Write-Host ""
Write-Host ("  [進度] " + $steps.Count + "/" + $steps.Count + " 完成 · 總計 " + [int]((Get-Date) - $t0all).TotalSeconds + "s · " + (($summary | ForEach-Object { $_.step + " rc=" + $_.rc + " " + $_.secs + "s" }) -join " · ")) -ForegroundColor DarkCyan

if (-not $NoAutoTest -and (Test-Path -LiteralPath $autoOut)) {
    Write-Host ("  [V6] 自測報告:" + (Join-Path $autoOut 'VRN_AutoTest_Report.json') + " · 頁 " + (Join-Path $autoOut 'VRN_AutoTest_Report.html')) -ForegroundColor Cyan
}
# v0104:跑完自動跳出自測報告頁(操作員 2026-09-24「自測報告要自動跳出來」)——只走瀏覽器 exe,-NoOpen 不跳
$autoHtml = Join-Path $autoOut 'VRN_AutoTest_Report.html'
if (-not $NoAutoTest -and -not $NoOpen) {
    if (Test-Path -LiteralPath $autoHtml) {
        if (Get-Command via-open -ErrorAction SilentlyContinue) { via-open $autoHtml }
        else { Write-Host ("  [V6] via-open 不在(短指令冊沒點到);請用瀏覽器開:" + $autoHtml) -ForegroundColor Yellow }
    } else {
        Write-Host ("  [V6] 自測報告頁沒生出來(第六步沒跑完,看上面 V6 的 rc);不跳頁") -ForegroundColor Yellow
    }
}
if ($celeritasJoin -and $celeritasJoin.Joined -and (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue)) {
    Restore-CeleritasPS7    # 契約:關閉即還原(只動本行程)
}
Write-Host ""
Write-Host "  [律] 誠實 rc:0 GREEN · 1 RED · 2 NODATA · 3 ABSENT · 4 GATED。" -ForegroundColor DarkGray
Write-Host "       GATED 不是壞掉,是**閘沒開**;NODATA 不是壞掉,是**量不到**。" -ForegroundColor DarkGray
Write-Host "       判對率與可判率**兩個都印**——不許只看好看的那一個。" -ForegroundColor DarkGray
if (-not $NoOpen) {
    Write-Host "  [頁] via-console 已把標準 U/I 落好;要看第一頁給 AI 的彙總:via-unified" -ForegroundColor Green
}
