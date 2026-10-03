# CELERITAS-TEMPLATE-JOIN v1
# Invoke-VDF-FetchFill-v0100.ps1 — VDF 補缺擷取一鍵:加速模組 · 動態百分比進度條 · Rich 詳細矩陣(AST 位置)
#   操作員(2026-10-03):「現在這個指令撰寫適用 PS 檔案也要加速模組及動態進度條百分比 DETAILED MATRIX SUMMARY BY RICH WITH AST POSITION」。
#   做的事:VDF System Manager 尾版 `fetch fill --progress`(MDL008 v0104 起)——只抓不足的部分 · 清單 MDL009 / MDL010 第一步 · 其餘依相依 ·
#     驗收 · DuckDB 視圖 · 報告 _reports\fill_*.json · 結尾詳細矩陣(每支:群組 · 檔 · AST 位置 名@行 · 補前理由 · 狀態 · rc · 秒 · 輸出 · 補後)。
#   加速 / 進度:點載 supportive modules\VIA_PS_PyProgress_Module.ps1 → Invoke-VIAPython(25 加速器點亮 · 動態條讀引擎 `[進度] i/n` 畫真百分比 ·
#     無輸出心跳 · 逾時才停)。模組不在 → 退回本檔自己的 Write-Progress(同一協定),照實說。
#   雙閘:live 要本視窗先設 $env:VIA_NET_CONSENT='YES' 與 $env:VIA_SCRAPE_CONSENT='YES'(操作員的手;本檔只檢查、永不代設)。沒開 = rc 4、零子行程。
#   用法(在 VeritasIntelligenceAnalytics 根目錄):
#     .\Invoke-VDF-FetchFill-v0100.ps1 -Plan                    # 只列計畫:每支為什麼不足(不連網、不寫檔)
#     .\Invoke-VDF-FetchFill-v0100.ps1                          # 只抓不足的部分
#     .\Invoke-VDF-FetchFill-v0100.ps1 -All                     # 35 支全部重抓
#     .\Invoke-VDF-FetchFill-v0100.ps1 -Group YFINANCE          # 只補一組(TWSE/TPEX · YFINANCE · FED · AKSHARE · OTHERS)
#   不碰 TA-Lib;不改其他 .ps1(L70);不裝套件(缺件照列 pip 指令)。
param(
    [string]$FetchHome = "C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_database\vdf_fetch",
    [switch]$All,
    [switch]$Plan,
    [string]$Group = "",
    [double]$MaxAgeH = 20,
    [ValidateSet("live", "fixture", "block")][string]$Mode = "live",
    [string]$Python = "",
    [int]$TimeoutSec = 14400     # 整輪上限 4 小時(Invoke-VIAPython 預設 30 分會砍掉 35 支的整輪);每支引擎另有 MDL008 的 30 分上限
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
    Write-Host "[VDF 補缺] 找不到 VeritasIntelligenceAnalytics 根目錄(要有 functional modules\VDF)。把本檔放在根目錄再跑。" -ForegroundColor Red
    $global:LASTEXITCODE = 2; return
}
$vdf = Join-Path $VIA "functional modules\VDF"
$mgr = Get-ChildItem -Path $vdf -Filter "VDF_SystemManager_v*.py" -File | Sort-Object Name | Select-Object -Last 1
if (-not $mgr) { Write-Host "[VDF 補缺] VDF_SystemManager_v*.py 不在 $vdf" -ForegroundColor Red; $global:LASTEXITCODE = 3; return }

$gateOpen = ($env:VIA_NET_CONSENT -eq "YES") -and ($env:VIA_SCRAPE_CONSENT -and $env:VIA_SCRAPE_CONSENT -ne "OFF")
if ($Mode -eq "live" -and -not $Plan -and -not $gateOpen) {
    Write-Host "[GATED] 雙閘沒開 —— 零子行程、零出網、零寫檔(不是壞掉)。本視窗開閘(操作員的手,本檔永不代設):" -ForegroundColor Yellow
    Write-Host "        `$env:VIA_NET_CONSENT='YES'; `$env:VIA_SCRAPE_CONSENT='YES'" -ForegroundColor Yellow
    $global:LASTEXITCODE = 4; return
}

$fillArgs = @("fetch", "fill", "--progress", "--home", $FetchHome, "--mode", $Mode, "--max-age-h", "$MaxAgeH")
if (-not $Plan) { $fillArgs += "--apply" }
if ($All) { $fillArgs += "--all" }
if ($Group) { $fillArgs += @("--group", $Group) }
if (-not $env:FORCE_COLOR) { $env:FORCE_COLOR = "1" }     # Rich 在被轉播的 stdout 上照樣出色彩表
if (-not $env:PYTHONIOENCODING) { $env:PYTHONIOENCODING = "utf-8" }
if (-not $env:PYTHONUTF8) { $env:PYTHONUTF8 = "1" }

Write-Host ("[VDF 補缺] 管理員 " + $mgr.Name + " · 輸出根 " + $FetchHome + " · 模式 " + $Mode + $(if ($Plan) { " · 只列計畫" } else { "" }) + $(if ($All) { " · 全部重抓" } else { " · 只抓不足" })) -ForegroundColor Cyan
$t0 = Get-Date
$prog = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
$rc = 1
Push-Location $VIA
try {
    if ((Test-Path $prog) -and -not $Python) {
        . $prog
        Invoke-VIAPython -Family vdf -TimeoutSec $TimeoutSec -Rest (@($mgr.FullName) + $fillArgs)   # 具名 -Rest:--apply 這類字串不會被當成參數名
        $rc = $LASTEXITCODE
    } else {
        if (-not (Test-Path $prog)) { Write-Host "[VDF 補缺] VIA_PS_PyProgress_Module.ps1 不在 → 用本檔的 Write-Progress(同一個 [進度] i/n 協定)" -ForegroundColor DarkYellow }
        $exe = if ($Python) { $Python } else { "python" }
        & $exe $mgr.FullName @fillArgs 2>&1 | ForEach-Object {
            $ln = "$_"
            if ($ln -match '^\s*\[進度\]\s*(\d+)\s*/\s*(\d+)\s*(.*)$') {
                $i = [int]$Matches[1]; $n = [int]$Matches[2]
                $pct = if ($n -gt 0) { [math]::Min(100, [int](100 * $i / $n)) } else { 100 }
                $sec = [int]((Get-Date) - $t0).TotalSeconds
                $eta = if ($i -gt 0 -and $i -lt $n) { [int]($sec * ($n - $i) / $i) } else { 0 }
                Write-Progress -Activity "VDF 補缺擷取" -Status ("$i/$n $pct% · 經過 ${sec}s · 剩約 ${eta}s · " + $Matches[3]) -PercentComplete $pct
            }
            if ($ln -notmatch '^##VIA-PROGRESS##') { Write-Host $ln }
        }
        $rc = $LASTEXITCODE
        Write-Progress -Activity "VDF 補缺擷取" -Completed
    }
} finally {
    Pop-Location
}
$secs = [int]((Get-Date) - $t0).TotalSeconds
$why = switch ($rc) { 0 { "PASS" } 1 { "有引擎失敗或輸出不合(看上面矩陣的 FAIL 列與報告)" } 2 { "參數錯或沒有總控入口" } 3 { "缺核心套件(照上面 pip 指令自己裝)" } 4 { "雙閘沒開(零寫)" } default { "rc $rc" } }
$color = if ($rc -eq 0) { "Green" } elseif ($rc -eq 4) { "Yellow" } else { "Red" }
Write-Host ("[VDF 補缺] 結束 rc $rc · $why · ${secs}s · 報告在 " + (Join-Path (Split-Path $FetchHome -Parent) "_reports")) -ForegroundColor $color
$global:LASTEXITCODE = $rc
