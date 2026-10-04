# CELERITAS-TEMPLATE-JOIN v1
# Invoke-VDF-FetchGroupsUI-v0100.ps1 — VDF 擷取大族群 U/I 一鍵:啟動指令對接 U/I · 自適應任何範本 · 加速模組
#   操作員(2026-10-04):「將啟動指令對接 U/I,可以自適應式其他模板範本」。
#   做的事:VDF_MDL012_FetchGroups 尾版 `ui`(引擎 → JSON 快照 → 頁;零 server · 零 CDN · file://):
#     · 不給 -Template = 正典族群頁(左面板 回母系統 / 跳其他系統 / 功能 / Live log;右面板 ① 輸入 · 引擎 · 運作 · 結果 · 每族群一頁 · 末頁流程圖 + 六矩陣)
#     · -Template X.html = 任何範本(functional modules\VDF\ui_templates\ 或 VIA_Reports\vdf\ui\templates\ 或直接路徑):
#       Jinja 沙盒渲染(沒裝 jinja2 就只代換雙大括號變數)+ 注入 window.VIA 快照 · 鎖定色 · 四燈;範本原檔零觸碰
#     · 每次都寫對接快照 VIA_Reports\vdf\ui\VDF_FetchGroups_SNAPSHOT_latest.json(其他 U/I 讀它就接上)
#     · -List 列可用範本與各自用到的變數;-Watch N 另起背景行程每 N 秒重產(擷取停了 30 分鐘自停),本視窗不卡
#   加速:點載 supportive modules\VIA_PS_PyProgress_Module.ps1 → Invoke-VIAPython(加速器點亮 · 心跳 · 逾時才停);
#     模組不在 → 直接 python(同一支、同參數),照實說。PS 加速器走本檔開頭的 PS-ACCEL 橋(VIA_PS_Accel_Module.ps1),缺席零影響。
#   開頁:預設用系統預設瀏覽器直接開檔(不經伺服器);-NoOpen 只產不開。
#   用法(在 VeritasIntelligenceAnalytics 根目錄):
#     .\Invoke-VDF-FetchGroupsUI-v0100.ps1                                  # 正典族群頁
#     .\Invoke-VDF-FetchGroupsUI-v0100.ps1 -List                            # 列範本
#     .\Invoke-VDF-FetchGroupsUI-v0100.ps1 -Template VDF_FetchGroups_Compact_v0100
#     .\Invoke-VDF-FetchGroupsUI-v0100.ps1 -Template C:\path\MyTemplate.html -AsOf 2026-10-02
#     .\Invoke-VDF-FetchGroupsUI-v0100.ps1 -Watch 15                        # 擷取中 Live log 每 15 秒更新
#   不碰 TA-Lib;不改其他 .ps1(L70);不裝套件;不讀寫同意閘(本頁零網路)。
param(
    [string]$FetchHome = "C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_database\vdf_fetch",
    [string]$Template = "",
    [string]$AsOf = "",
    [switch]$List,
    [int]$Watch = 0,
    [switch]$NoOpen,
    [string]$Python = "",
    [int]$TimeoutSec = 900
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
$VIA = $PSScriptRoot
while ($VIA -and -not (Test-Path (Join-Path $VIA "functional modules\VDF"))) { $VIA = Split-Path $VIA -Parent }
if (-not $VIA) {
    Write-Host "[VDF 族群 U/I] 找不到 VeritasIntelligenceAnalytics 根目錄(要有 functional modules\VDF)。把本檔放在根目錄再跑。" -ForegroundColor Red
    $global:LASTEXITCODE = 2; return
}
$vdf = Join-Path $VIA "functional modules\VDF"
$mdl = Get-ChildItem -Path $vdf -Filter "VDF_MDL012_FetchGroups_v*.py" -File | Sort-Object Name | Select-Object -Last 1
if (-not $mdl) { Write-Host "[VDF 族群 U/I] VDF_MDL012_FetchGroups_v*.py 不在 $vdf" -ForegroundColor Red; $global:LASTEXITCODE = 3; return }

$uiArgs = @("ui")
if ($List) { $uiArgs += "--list-templates" }
else {
    if (Test-Path $FetchHome) { $uiArgs += @("--home", $FetchHome) }
    else { Write-Host "[VDF 族群 U/I] 輸出根 $FetchHome 不在 → 用 MDL012 預設輸出根(VIA_VDF_FETCH_HOME 或冊上 home_default)" -ForegroundColor DarkYellow }
    if ($Template) { $uiArgs += @("--template", $Template) }
    if ($AsOf) { $uiArgs += @("--as-of", $AsOf) }
}
if (-not $env:PYTHONIOENCODING) { $env:PYTHONIOENCODING = "utf-8" }
if (-not $env:PYTHONUTF8) { $env:PYTHONUTF8 = "1" }
$env:VIA_FROM_VCGC = "YES"

Write-Host ("[VDF 族群 U/I] " + $mdl.Name + " · " + $(if ($List) { "列範本" } elseif ($Template) { "範本 " + $Template } else { "正典族群頁" }) + $(if ($AsOf) { " · as-of " + $AsOf } else { "" })) -ForegroundColor Cyan
$t0 = Get-Date
$prog = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
$out = @()
Push-Location $VIA
try {
    if ((Test-Path $prog) -and -not $Python) {
        . $prog
        $out = Invoke-VIAPython -Family vdf -TimeoutSec $TimeoutSec -Rest (@($mdl.FullName) + $uiArgs) 6>&1 | ForEach-Object { "$_" }
        $rc = $LASTEXITCODE
    } else {
        if (-not (Test-Path $prog)) { Write-Host "[VDF 族群 U/I] VIA_PS_PyProgress_Module.ps1 不在 → 直接 python(同一支、同參數)" -ForegroundColor DarkYellow }
        $exe = if ($Python) { $Python } else { "python" }
        $out = & $exe $mdl.FullName @uiArgs 2>&1 | ForEach-Object { "$_" }
        $rc = $LASTEXITCODE
    }
} finally {
    Pop-Location
}
$out | ForEach-Object { Write-Host $_ }
if ($List -or $rc -ne 0) {
    $color = if ($rc -eq 0) { "Green" } else { "Red" }
    Write-Host ("[VDF 族群 U/I] 結束 rc $rc · " + [int]((Get-Date) - $t0).TotalSeconds + "s") -ForegroundColor $color
    $global:LASTEXITCODE = $rc; return
}

# 頁的位置:以產生器印出的路徑為準(範本頁 = 「→ 路徑 ·」;正典頁 = 「[ui] 路徑 ·」);抓不到才用預設位置
$page = $null
foreach ($ln in $out) {
    if ($ln -match '^\[ui · 範本\] .+? → (.+?\.html) ·') { $page = $Matches[1]; break }
    if ($ln -match '^\[ui\] (.+?\.html) ·') { $page = $Matches[1]; break }
}
if (-not $page) {
    $page = if ($Template) {
        $stem = [IO.Path]::GetFileNameWithoutExtension($Template)
        $name = if ($stem.StartsWith("VDF_FetchGroups_")) { $stem + ".html" } else { "VDF_FetchGroups_" + $stem + ".html" }
        Join-Path $VIA ("VIA_Reports\vdf\ui\" + $name)
    } else { Join-Path $VIA "supportive modules\ui_support\VIA_UI_VDFFetchGroups_v0100.html" }
}
$snap = Join-Path $VIA "VIA_Reports\vdf\ui\VDF_FetchGroups_SNAPSHOT_latest.json"
Write-Host ("[建] " + $page) -ForegroundColor Green
Write-Host ("[對接] 快照 " + $snap + $(if (Test-Path $snap) { "" } else { "(沒寫成)" })) -ForegroundColor $(if (Test-Path $snap) { "Green" } else { "Yellow" })

if ($Watch -gt 0) {
    $exeW = if ($Python) { $Python } elseif (Get-Command Get-VIAEnvPython -ErrorAction SilentlyContinue) { Get-VIAEnvPython "vdf" } else { "python" }
    $wArgs = @($mdl.FullName) + ($uiArgs) + @("--watch", "$Watch")
    $quoted = ($wArgs | ForEach-Object { $a = "$_" -replace '"', '\"'; if ($a -match '\s') { '"' + $a + '"' } else { $a } }) -join ' '
    try {
        $wp = Start-Process -FilePath $exeW -ArgumentList $quoted -WorkingDirectory $VIA -WindowStyle Hidden -PassThru
        Write-Host ("[Live] 背景每 $Watch 秒重產 · PID " + $wp.Id + " · 擷取停了 30 分鐘自停;要先停:Stop-Process -Id " + $wp.Id) -ForegroundColor Cyan
    } catch {
        Write-Host ("[Live] 背景重產起不來:" + $_.Exception.Message + "(頁照樣可開,只是不會自己更新)") -ForegroundColor Yellow
    }
}
if (-not $NoOpen) {
    if (Test-Path $page) {
        try { Start-Process -FilePath $page; Write-Host "[開] 預設瀏覽器直接開檔(不經伺服器)" -ForegroundColor Green }
        catch { Write-Host ("[開] 開不起來:" + $_.Exception.Message + " · 自己開:" + $page) -ForegroundColor Yellow }
    } else { Write-Host ("[開] 頁不在:" + $page) -ForegroundColor Red; $rc = 1 }
}
Write-Host ("[VDF 族群 U/I] 結束 rc $rc · " + [int]((Get-Date) - $t0).TotalSeconds + "s · 範本夾 functional modules\VDF\ui_templates\ 丟任何 .html → -Template 檔名") -ForegroundColor $(if ($rc -eq 0) { "Green" } else { "Red" })
$global:LASTEXITCODE = $rc
