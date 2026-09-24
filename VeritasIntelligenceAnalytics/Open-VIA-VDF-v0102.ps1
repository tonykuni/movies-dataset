# CELERITAS-TEMPLATE-JOIN v1(啟動器接法:不包裹,同 Invoke-VIA-VdfFetch-v0106/v0107;正主 supportive modules\ps7\VeritasCeleritas.PS7.ps1 關在動態模組裡,見掉球 Z136)
#Requires -Version 7.0
# =====================================================================
# Open-VIA-VDF-v0102.ps1 — 一個指令開 VDF:進環境 → 先跳 HTML 問要不要改參數 → 啟動擷取 → 看資料庫狀況
# 名字不叫 Start-VIA-VDF:functional modules\VDF 已有 Start-VIA-VDF-v0101~v0104(加速器導入 + 工作台啟動)那一族,
#   Invoke-VIA-TrinityClosure 用尾版 glob 取它;同名會讓本檔的 v0100 看起來像那一族的舊版(L04),所以另立一族。
# v0101→v0102(側線 2026-09-23;操作員看過問參數頁後令「每道上限檔數刪除 · 要抓就全抓 · 起始日期 YYYY-MM-DD · 截止日期自動帶入今天 ·
#   方便打勾方格自動 · 逐一引擎邊測邊修正到成功 · 輸入參數用大矩陣完整顯示」;v0101 留作版史 L04):
#   ③ 照新決定檔(since · until · steps · dry · noheal;VDF_ENG093 v0101)呼叫 Invoke-VIA-VdfFetch 尾版:-Since · -Steps · -Dry · -NoHeal,
#      永不送 -Limit(全市場全抓)。尾版若還不認得 -Since(舊樹)就退回 -Year = 起始日的年,並講明勾選的步沒法只跑那幾步。
#   ④ 狀況頁多帶 --decision(本次輸入參數 + CGC_MDL134 各步結果);決定檔跑完才刪。
# v0100→v0101(側線 2026-09-23;工作站第一次實跑,操作員「實測自測自修自完成」;v0100 留作版史 L04):
#   ① 模板章首載就炸(掉球 Z137 實證):正主 StrictMode 下讀還沒設的 $script:CeleritasPS7 → New-Module 失敗、紅字噴在視窗,
#      「第一個錯」還印成最後一個($Error[0])。改成下方 v0101 載法;Invoke-VIA-VdfFetch 同步出 v0106。
#   ② 起跑之後整段包 try/finally:按 Ctrl+C 也會依快照還原本行程減壓(v0100 只在正常出口還原)。
#   ③ 頁交給瀏覽器之後講明:沒跳到最前面就點工作列的瀏覽器;按完按鈕,這個視窗自己往下走。
# 側線 2026-09-23(主線批號由併線的手指定 L25)。操作員令:「給我一個指令含進入環境一件開啟 VDF 的 POWERSHELL CODE 實測 ·
#   應先跳出 HTML U/I 問我要不要改參數啟動 · 然後看到資料庫狀況」。這是新檔,既有 .ps1 一支都沒動(L70)。
#
# 一行即用(任何 pwsh 7 視窗、任何資料夾;前面是「一個點、一個空白」= 點源,短令冊才會留在這個視窗):
#   . (Get-ChildItem "<VIA 根>\Open-VIA-VDF-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName   (尾版;寫死版號也行)
# 雙擊:VIA 根的 Open-VIA-VDF.cmd(開一個 pwsh 7 視窗點源本檔;跑完視窗留著,via-* 短令照常可用)
# 用 & 跑也行,只是短令冊只活在本檔裡(via-* 靠的 Invoke-VIAPython 不是 global:);沒有 $PROFILE 載冊的視窗跑完會提醒你改用點源。
#
# 四步,每一步都印出在做什麼:
#   ① 進環境:點源本檔旁的 Register-VIA-Commands 尾版($VIA · via-* 短令 · 家族境 python)
#   ② 問:VDF_ENG093_LaunchConsole ask —— 起本機頁(只綁 127.0.0.1 · 一次性權杖 · 同源送出),本檔從它印的「頁:網址」那一行
#        取網址交給 via-open 開(只走瀏覽器 exe;零跳出律管的是沒人要求的頁,這一令是你親手打的,批474 B):
#        參數(預設讀自啟動器)· 啟動就緒 · 啟動前資料庫狀況;你按「用預設參數啟動 / 用上面的參數啟動 / 不啟動」
#   ③ 跑:照頁上的決定呼叫 Invoke-VIA-VdfFetch 尾版(-NoEnter;進度印在這個視窗)
#        本檔不碰同意閘:擷取車道在自己的子行程開閘(CGC_MDL134);直呼 via-price / via-chip 才要你自己開閘二
#   ④ 看:VDF_ENG093 status --refresh —— 委派 CGC_MDL123 重點目錄,排出資料庫狀況頁(分類燈 · 增量缺口 · 逐表),再交給 via-open 開
# 旗標:-NoUi 不開問參數頁,直接用啟動器預設跑(給排程;第 ④ 步照做但頁只落檔不跳——沒人在看就不跳)· -NoStatus 跑完不做第 ④ 步
# 還原:刪掉本檔與 Open-VIA-VDF.cmd。
# =====================================================================
param(
    [switch]$NoUi,
    [switch]$NoStatus
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

$ErrorActionPreference = "Continue"
function Restore-VIAFetchEnv {
    # 本檔只有模板章要還原(同名函式與 Invoke v0105 一致:正主減壓跑完即還原,重複呼叫無害)
    if ($script:VIACel) { try { & $script:VIACel { Restore-CeleritasPS7 } 2>$null } catch { } }
}
# ===== [VIA:CELERITAS-PS7:v0101] 模板章(L102;接法:不包裹,正主關在動態模組裡)=====
# v0101 載法(工作站 2026-09-23 第一次實跑,掉球 Z137 實證):正主第 18 行開 StrictMode,第 24 行就讀還沒設的 $script:CeleritasPS7,
#   快照還讀 $OFS(預設不存在)與 $PSNativeCommandArgumentPassing(7.3 起才有)→ 首載即炸,New-Module 整個失敗、紅字噴在視窗。
#   正主是 Celeritas 線的檔(批715),側線不改它;這裡先在模組 scope 把三個變數設好,正主自己的「$null 就初始化」才走得到。
#   -RestoreOnly 只載函式、不自動起跑;先試拍快照(拍不到就不起跑),起跑另外呼叫,驗「已套且有快照」,
#   沒套上就依快照還原(失敗也拿得到模組)。
#   錯誤只記進 $Error、不噴紅字,印一行「第一個錯」。正主修好之後這幾行是無害的重複。
$script:VIACel = $null
$script:VIACelNote = "正主缺(supportive modules\ps7\VeritasCeleritas.PS7.ps1),略過"
try {
    $celFile = $null
    $celProbe = $PSScriptRoot
    while ($celProbe -and (Split-Path $celProbe -Parent)) {
        $celTry = Join-Path $celProbe "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
        if (Test-Path -LiteralPath $celTry) { $celFile = $celTry; break }
        $celProbe = Split-Path $celProbe -Parent
    }
    if ($celFile) {
        $celErr0 = $Error.Count
        $script:VIACel = New-Module -Name "VIACeleritasPS7" -ArgumentList $celFile -ErrorAction SilentlyContinue -ScriptBlock {
            param($CelFile)
            $script:CeleritasPS7 = $null
            $OFS = " "
            if (-not (Get-Variable -Name PSNativeCommandArgumentPassing -ErrorAction SilentlyContinue)) { $PSNativeCommandArgumentPassing = $null }
            $null = . $CelFile -RestoreOnly 2>$null
            Export-ModuleMember -Function Restore-CeleritasPS7
        }
        $celOn = $false
        $celSnap = $null   # 先試拍快照(唯讀、零副作用):拍不到就不起跑——正主拍快照失敗仍會照套設定,那樣就再也還原不回來
        if ($script:VIACel) { try { $celSnap = & $script:VIACel { Get-CeleritasSnapshot } 2>$null } catch { $celSnap = $null } }
        if ($script:VIACel -and ($null -ne $celSnap)) {
            try { $null = & $script:VIACel { Start-CeleritasPS7 } 2>$null } catch { }
            try { $celOn = [bool](& $script:VIACel { $script:CeleritasPS7.Applied -and ($null -ne $script:CeleritasPS7.Snapshot) } 2>$null) } catch { $celOn = $false }
            if (-not $celOn) { try { & $script:VIACel { Restore-CeleritasPS7 } 2>$null } catch { } }
        }
        $script:VIACelNote = $(if ($celOn) { "本行程減壓已套(只動本行程;跑完還原)" } else { "正主在但沒套上,略過(擷取照跑)" })
        $celNew = [Math]::Min($Error.Count - $celErr0, $Error.Count)
        if ((-not $celOn) -and ($celNew -gt 0)) { $script:VIACelNote += ";正主第一個錯:" + ("" + $Error[$celNew - 1]) }
    }
} catch {
    $script:VIACel = $null
    $script:VIACelNote = "正主載入失敗,略過(擷取照跑):" + $_.Exception.Message
}
Write-Host ("  [Celeritas] " + $script:VIACelNote) -ForegroundColor DarkGray
# ===== [VIA:CELERITAS-PS7:END] =====

function Stop-VIAOpenVdf([int]$Code) {
    $global:LASTEXITCODE = $Code   # 還原交給下面的 finally(Ctrl+C 也走得到)
}
function Open-VIAVdfPage([string]$Target) {
    # 開頁一律委派短令冊的 via-open(只走瀏覽器 exe,永不經 .html 預設程式;VIA_NO_OPEN=1 擋不到它,因為開的是 exe)
    if (Get-Command via-open -ErrorAction SilentlyContinue) { via-open $Target }
    else { Write-Host ("  [開頁] 短令冊沒有 via-open;請手動用瀏覽器開:" + $Target) -ForegroundColor Yellow }
}

# 本檔的變數一律 svd 開頭:點源時它們落在呼叫端(通常是 global),不跟別人的 $p / $d 撞名
$svdHadPy = [bool](Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)   # 點冊之前就有 = 外層($PROFILE)已載過冊
$svdHow = "" + $MyInvocation.InvocationName

# 起跑之後整段包 try/finally:任何出口(含 return 與 Ctrl+C)都依快照還原本行程減壓。本體不另縮排,try 不開新 scope(點源照舊落在呼叫端)。
try {
# ---------------------------------------------------------------- ① 進環境
$svdReg = Get-ChildItem -LiteralPath $PSScriptRoot -Filter "Register-VIA-Commands-v*.ps1" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if (-not $svdReg) {
    Write-Host ("  [FAIL] 本檔旁找不到 Register-VIA-Commands-v*.ps1(本檔要放在 VIA 根):" + $PSScriptRoot) -ForegroundColor Red
    Stop-VIAOpenVdf 3
    return
}
. $svdReg.FullName
Write-Host ("  ① 進環境:已點源 " + $svdReg.Name + "(via-* 短令在這個視窗生效)") -ForegroundColor Cyan
if (-not (Get-Command Get-VIANewest -ErrorAction SilentlyContinue) -or -not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    Write-Host "  [FAIL] 短令冊載入後缺 Get-VIANewest / Invoke-VIAPython(短令冊太舊?先 via-reload)" -ForegroundColor Red
    Stop-VIAOpenVdf 3
    return
}
$svdConsole = Get-VIANewest (Join-Path $VIA "functional modules\VDF") "VDF_ENG093_LaunchConsole_v*.py"
$svdFetch = Get-VIANewest $VIA "Invoke-VIA-VdfFetch-v*.ps1"
if (-not $svdConsole -or -not $svdFetch) {
    Write-Host ("  [FAIL] 缺件:" + $(if (-not $svdConsole) { "VDF_ENG093_LaunchConsole_v*.py " } else { "" }) + $(if (-not $svdFetch) { "Invoke-VIA-VdfFetch-v*.ps1" } else { "" }) + "(先把分支拉進這棵樹)") -ForegroundColor Red
    Stop-VIAOpenVdf 3
    return
}

# ---------------------------------------------------------------- ② 問
$svdAns = Join-Path ([IO.Path]::GetTempPath()) ("VIA_VDF_ASK_" + $PID + ".json")
if (Test-Path -LiteralPath $svdAns) { Remove-Item -LiteralPath $svdAns -Force -ErrorAction SilentlyContinue }
$svdDecision = $null
if ($NoUi) {
    $svdDecision = [pscustomobject]@{ action = "launch"; mode = "default"; since = ""; steps = @(); dry = $false; noheal = $false }
    Write-Host "  ② 問:-NoUi,不開頁,用啟動器預設參數" -ForegroundColor Cyan
} else {
    Write-Host "  ② 問:瀏覽器會跳出「VDF 一鍵啟動」頁;選好之後回到這個視窗" -ForegroundColor Cyan
    $svdAskUrl = ""
    # 引擎等你按鈕時是阻塞的;Invoke-VIAPython 邊跑邊把 stdout 一行一行送下管線,所以網址一印出來這裡就接得到(引擎有 flush)
    Invoke-VIAPython -Family "vdf" -TimeoutSec 960 $svdConsole "ask" "--out" $svdAns "--timeout" "900" | ForEach-Object {
        $svdLine = "" + $_
        Write-Host $svdLine
        if (-not $svdAskUrl -and $svdLine -match '(http://127\.0\.0\.1:\d+/\?t=[A-Za-z0-9_\-]+)') {
            $svdAskUrl = $Matches[1]
            Open-VIAVdfPage $svdAskUrl
            Write-Host "  ② 頁交給瀏覽器了:沒跳到最前面就點工作列的瀏覽器(或把上面網址貼進去);按完按鈕,這個視窗自己往下走" -ForegroundColor Cyan
        }
    }
    if (Test-Path -LiteralPath $svdAns) {
        try { $svdDecision = Get-Content -LiteralPath $svdAns -Raw -Encoding utf8 | ConvertFrom-Json } catch { $svdDecision = $null }
    }
}
if (-not $svdDecision -or $svdDecision.action -ne "launch") {
    $svdWhy = $(if ($svdDecision) { "" + $svdDecision.action } else { "沒有收到決定" })
    Write-Host ("  [VDF] 不啟動(" + $svdWhy + ")。啟動前的資料庫狀況在剛才那一頁。") -ForegroundColor Yellow
    Remove-Item -LiteralPath $svdAns -Force -ErrorAction SilentlyContinue
    Stop-VIAOpenVdf 0
    return
}

# ---------------------------------------------------------------- ③ 跑
$svdParams = @{ NoEnter = $true }   # 永不送 -Limit:要抓就全抓(全市場)
$svdSince = "" + $svdDecision.since
$svdSteps = @($svdDecision.steps | Where-Object { $_ }) -join ","
$svdHasSince = (Get-Command -Name $svdFetch -ErrorAction SilentlyContinue).Parameters.ContainsKey("Since")
if ($svdSince -match "^\d{4}-\d{2}-\d{2}$") {
    if ($svdHasSince) { $svdParams["Since"] = $svdSince }
    else { $svdParams["Year"] = $svdSince.Substring(0, 4); Write-Host ("  [注意] " + (Split-Path $svdFetch -Leaf) + " 還不認得 -Since/-Steps(樹太舊):改用 -Year " + $svdParams["Year"] + ",勾選的步沒法只跑那幾步——先把分支拉進這棵樹") -ForegroundColor Yellow }
}
if ($svdSteps -and $svdHasSince) { $svdParams["Steps"] = $svdSteps }
if ($svdDecision.dry -eq $true) { $svdParams["Dry"] = $true }
if ($svdDecision.noheal -eq $true) { $svdParams["NoHeal"] = $true }
$svdParamTxt = ($svdParams.GetEnumerator() | Sort-Object Name | ForEach-Object { "-" + $_.Name + $(if ($_.Value -is [bool]) { "" } else { " " + $_.Value }) }) -join " "
Write-Host ("  ③ 跑:" + (Split-Path $svdFetch -Leaf) + " " + $svdParamTxt) -ForegroundColor Cyan
& $svdFetch @svdParams
$svdRcFetch = $LASTEXITCODE

# ---------------------------------------------------------------- ④ 看
if (-not $NoStatus) {
    Write-Host "  ④ 看:重點資料庫目錄 → 開資料庫狀況頁" -ForegroundColor Cyan
    $svdPage = ""
    $svdStatusArgs = @("status", "--refresh")
    if (Test-Path -LiteralPath $svdAns) { $svdStatusArgs += @("--decision", $svdAns) }   # 本次輸入參數 + 各步結果上頁
    Invoke-VIAPython -Family "vdf" $svdConsole $svdStatusArgs | ForEach-Object {   # 陣列當一個參數交給它,Invoke-VIAPython 自己攤平(不用陣列 splat)
        $svdLine = "" + $_
        Write-Host $svdLine
        if ($svdLine -match '\[VDF 資料庫狀況\] 頁:(.+?)\s*$') { $svdPage = $Matches[1] }
    }
    if (-not $svdPage) { Write-Host "  [VDF 資料庫狀況] 沒拿到頁的路徑(看上面的輸出)" -ForegroundColor Yellow }
    elseif ($NoUi) { Write-Host ("  ④ -NoUi(沒人在看):頁只落檔不跳;要看就 via-open " + $svdPage) -ForegroundColor DarkGray }
    else { Open-VIAVdfPage $svdPage }
}
Remove-Item -LiteralPath $svdAns -Force -ErrorAction SilentlyContinue   # 決定檔用完才刪(狀況頁要讀)
$svdStays = $svdHadPy -or ($svdHow -eq ".")
if (-not $svdStays) {
    Write-Host ('  [提醒] 這次不是點源跑的,短令冊只活在本檔裡;要讓 via-* 留在這個視窗,改用:. "' + $PSCommandPath + '"') -ForegroundColor Yellow
}
Write-Host ("=== [Open-VIA-VDF] 畢 · 擷取 rc=" + $svdRcFetch + $(if ($svdStays) { " · via-* 短令在這個視窗照常可用" } else { "" }) + " ===") -ForegroundColor Cyan
Stop-VIAOpenVdf $svdRcFetch
} finally {
    Restore-VIAFetchEnv
}
