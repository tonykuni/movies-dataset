# CELERITAS-TEMPLATE-JOIN v1
# Start-VIA-UIEngine-v0100.ps1 — 一鍵:照測過的環境檢查 / 安裝 → 產 HTML U/I(自適應範本 · 參數 · DuckDB 顯式)→ 開
#   操作員(2026-10-04):「一個引擎自動安裝所有工具跟環境,依照我測試過的結果,然後啟動 HTML U/I,讓操作介面全部都在上面實習而不動系統;
#     U/I 架構會自適應式吻合任何模板設計、參數可調整;啟動檔兼最簡單的 HTML 標準模板,未來的拿來套用;DuckDB 顯式資料庫於 U/I」。
#   ① 環境(不動系統):全部經 VCGC 唯一入口。
#       RunGate(CGC_MDL137)probe 家族境能不能跑 · EnvGovernance(CGC_MDL135)lkgc status = 你測過全綠時存的版本鎖。
#       -Install 才動手:LKGC 可用 → rollback --to LKGC_latest.json --execute --approve(uv pip sync 照鎖逐境重建;只進 via_* 隔離境,
#         不給 --approve-remove = 不刪 base 任何東西);LKGC 不可用 → RunGate run --approve-install(只把缺件裝進家族境)。
#       安裝要連網:本視窗先開雙閘(操作員的手;本檔只檢查、永不代設),沒開 = 跳過安裝、照實說。
#   ② 產頁:CGC_MDL257_UIEngine 尾版 build(引擎 → JSON 快照 → 頁;零 CDN)。參數疊層 = 正本 VIA_UI_EngineConfig_v*.json ←
#       工作副本 VIA_Reports\ui_engine\ui_config.json ← -Config ← -Set a.b=值。-Template X = 範本夾任何 .html(未來的設計);不給 = 內建標準範本。
#   ③ 開:預設瀏覽器直接開檔(file://,不需伺服器);-Serve = 另起只綁 127.0.0.1 的只讀樞紐(改 ui_config.json 重新整理即生效),開 http://127.0.0.1:埠/。
#   用法(在 VeritasIntelligenceAnalytics 根目錄):
#     .\Start-VIA-UIEngine-v0100.ps1                                   # 檢查環境 → 內建標準範本 → 開
#     .\Start-VIA-UIEngine-v0100.ps1 -Install                          # 環境不綠就照 LKGC 裝(先開雙閘)
#     .\Start-VIA-UIEngine-v0100.ps1 -Template VDF_FetchGroups_Compact_v0100
#     .\Start-VIA-UIEngine-v0100.ps1 -Set "theme.primary_color=#c2410c","layout.sidebar_width=300px"
#     .\Start-VIA-UIEngine-v0100.ps1 -Serve -Port 8766                 # 本機只讀樞紐(參數熱更新)
#     .\Start-VIA-UIEngine-v0100.ps1 -InitConfig                       # 寫一份可改的 ui_config.json 工作副本
#   不碰 TA-Lib;不改其他 .ps1(L70);不刪任何境;不讀寫同意閘以外的系統設定。
param(
    [string]$FetchHome = "C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_database\vdf_fetch",
    [string]$Family = "vdf",
    [switch]$Install,
    [switch]$SkipEnv,
    [string]$Template = "",
    [string]$Config = "",
    [string[]]$Set = @(),
    [switch]$InitConfig,
    [switch]$Serve,
    [int]$Port = 8766,
    [switch]$NoOpen,
    [string]$Python = "",
    [int]$TimeoutSec = 3600
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
while ($VIA -and -not (Test-Path (Join-Path $VIA "supportive modules\registry"))) { $VIA = Split-Path $VIA -Parent }
if (-not $VIA) { Write-Host "[UI 引擎] 找不到 VeritasIntelligenceAnalytics 根目錄" -ForegroundColor Red; $global:LASTEXITCODE = 2; return }
$reg = Join-Path $VIA "supportive modules\registry"
$vcgc = Get-ChildItem $reg -Filter "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" -File | Sort-Object { [int]([regex]::Match($_.BaseName, '_v(\d+)$').Groups[1].Value) } | Select-Object -Last 1
$eng = Get-ChildItem $reg -Filter "CGC_MDL257_UIEngine_v*.py" -File | Sort-Object Name | Select-Object -Last 1
if (-not $vcgc -or -not $eng) { Write-Host "[UI 引擎] VCGC 入口或 CGC_MDL257_UIEngine 不在 $reg" -ForegroundColor Red; $global:LASTEXITCODE = 3; return }
if (-not $env:PYTHONIOENCODING) { $env:PYTHONIOENCODING = "utf-8" }
if (-not $env:PYTHONUTF8) { $env:PYTHONUTF8 = "1" }
$env:VIA_FROM_VCGC = "YES"
if (Test-Path $FetchHome) { $env:VIA_VDF_FETCH_HOME = $FetchHome }
$prog = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
$useProg = (Test-Path $prog) -and -not $Python
if ($useProg) { . $prog }
$exe = if ($Python) { $Python } else { "python" }

function Invoke-Py([string[]]$ArgList, [int]$To = $TimeoutSec) {
    # 加速模組在 → Invoke-VIAPython(加速器 · 心跳 · 逾時);不在 → 直接 python(同一支、同參數)
    if ($useProg) { $o = Invoke-VIAPython -Family core -TimeoutSec $To -Rest $ArgList 6>&1 | ForEach-Object { "$_" } }
    else { $o = & $exe @ArgList 2>&1 | ForEach-Object { "$_" } }
    return @{ rc = $LASTEXITCODE; out = @($o) }
}

$t0 = Get-Date
$steps = @()
Write-Host ("[UI 引擎] " + $eng.Name + " · VCGC " + $vcgc.Name + " · 家族 " + $Family) -ForegroundColor Cyan
Push-Location $VIA
try {
    # ① 環境
    if ($SkipEnv) { $steps += "環境:略過(-SkipEnv)" }
    else {
        Write-Host "[1/3] 環境檢查(RunGate probe · LKGC status)" -ForegroundColor Cyan
        $g = Invoke-Py @($vcgc.FullName, "run", "CGC_MDL137_RunGate", "probe", "--family", $Family) 900
        $g.out | Select-Object -Last 6 | ForEach-Object { Write-Host "   $_" }
        $l = Invoke-Py @($vcgc.FullName, "run", "CGC_MDL135_EnvGovernance", "lkgc", "status") 600
        $l.out | Select-Object -Last 4 | ForEach-Object { Write-Host "   $_" }
        $lkgcFile = Join-Path $VIA "VIA_Reports\env_governance\LKGC_latest.json"
        $lk = $null; if (Test-Path $lkgcFile) { try { $lk = Get-Content $lkgcFile -Raw -Encoding utf8 | ConvertFrom-Json } catch { } }
        $envGreen = ($g.rc -eq 0)
        $steps += ("環境:RunGate rc " + $g.rc + " · LKGC " + $(if ($lk) { "$($lk.verdict) · 可用 $($lk.eligible)" } else { "無" }))
        if (-not $envGreen -and $Install) {
            $gate = ($env:VIA_NET_CONSENT -eq "YES") -and ($env:VIA_SCRAPE_CONSENT -and $env:VIA_SCRAPE_CONSENT -ne "OFF")
            if (-not $gate) {
                Write-Host "[GATED] 安裝要連網:本視窗先開雙閘(操作員的手,本檔永不代設):`$env:VIA_NET_CONSENT='YES'; `$env:VIA_SCRAPE_CONSENT='YES' → 本次跳過安裝" -ForegroundColor Yellow
                $steps += "安裝:跳過(雙閘沒開)"
            } elseif ($lk -and $lk.eligible) {
                Write-Host "[安裝] 照你測過的版本鎖(LKGC)重建隔離境:rollback --to LKGC_latest.json --execute --approve(不刪 base)" -ForegroundColor Cyan
                $r = Invoke-Py @($vcgc.FullName, "run", "CGC_MDL135_EnvGovernance", "rollback", "--to", "LKGC_latest.json", "--execute", "--approve") $TimeoutSec
                $r.out | Select-Object -Last 8 | ForEach-Object { Write-Host "   $_" }
                $steps += ("安裝:LKGC rollback rc " + $r.rc)
            } else {
                Write-Host "[安裝] LKGC 不可用(沒有全綠存檔)→ RunGate 只把缺件裝進家族境(--approve-install)" -ForegroundColor Cyan
                $r = Invoke-Py @($vcgc.FullName, "run", "CGC_MDL137_RunGate", "run", "--family", $Family, "--approve-install") $TimeoutSec
                $r.out | Select-Object -Last 8 | ForEach-Object { Write-Host "   $_" }
                $steps += ("安裝:RunGate approve-install rc " + $r.rc)
            }
        } elseif (-not $envGreen) {
            Write-Host "[環境] 家族境沒全綠;要照測過版本裝就加 -Install(先開雙閘)。U/I 只讀,照樣產頁。" -ForegroundColor Yellow
        }
    }
    # ② 參數 / 產頁
    $common = @()
    if ($Config) { $common += @("--config", $Config) }
    foreach ($s in $Set) { if ($s) { $common += @("--set", $s) } }
    if (Test-Path $FetchHome) { $common += @("--home", $FetchHome) }
    if ($InitConfig) {
        $c = Invoke-Py (@($eng.FullName, "config", "--init") + $common) 300
        $c.out | Select-Object -First 2 | ForEach-Object { Write-Host "   $_" }
    }
    Write-Host "[2/3] 產 HTML U/I(自適應範本 · 參數 · DuckDB 顯式)" -ForegroundColor Cyan
    $bArgs = @($eng.FullName, "build") + $common
    if ($Template) { $bArgs += @("--template", $Template) }
    $b = Invoke-Py $bArgs 900
    $b.out | Where-Object { $_ -match '^\[(ui-engine|範本|參數)\]' } | ForEach-Object { Write-Host "   $_" }
    if ($b.rc -ne 0) { Write-Host ("[UI 引擎] 產頁失敗 rc " + $b.rc) -ForegroundColor Red; $b.out | Select-Object -Last 8 | ForEach-Object { Write-Host "   $_" }; $global:LASTEXITCODE = $b.rc; return }
    $page = $null
    foreach ($ln in $b.out) { if ($ln -match '^\[ui-engine\] (.+?\.html) ·') { $page = $Matches[1]; break } }
    if (-not $page) { $page = Join-Path $VIA "VIA_Reports\ui_engine\VIA_UI_Engine_latest.html" }
    $steps += ("產頁:" + $page)
    # ③ 開
    Write-Host "[3/3] 開 U/I" -ForegroundColor Cyan
    if ($Serve) {
        $sArgs = @($eng.FullName, "serve", "--port", "$Port") + $common
        if ($Template) { $sArgs += @("--template", $Template) }
        $exeS = if ($Python) { $Python } elseif (Get-Command Get-VIAEnvPython -ErrorAction SilentlyContinue) { Get-VIAEnvPython "core" } else { "python" }
        $quoted = ($sArgs | ForEach-Object { $a = "$_" -replace '"', '\"'; if ($a -match '\s') { '"' + $a + '"' } else { $a } }) -join ' '
        try {
            $sp = Start-Process -FilePath $exeS -ArgumentList $quoted -WorkingDirectory $VIA -WindowStyle Hidden -PassThru
            Start-Sleep -Seconds 2
            $url = "http://127.0.0.1:$Port/"
            Write-Host ("[serve] " + $url + " · 只讀樞紐 PID " + $sp.Id + " · 改 VIA_Reports\ui_engine\ui_config.json 重新整理即生效 · 停:Stop-Process -Id " + $sp.Id) -ForegroundColor Green
            if (-not $NoOpen) { Start-Process $url }
            $steps += ("樞紐:" + $url + " PID " + $sp.Id)
        } catch { Write-Host ("[serve] 起不來:" + $_.Exception.Message + " → 改開靜態檔") -ForegroundColor Yellow; if (-not $NoOpen) { Start-Process -FilePath $page } }
    } elseif (-not $NoOpen) {
        try { Start-Process -FilePath $page; Write-Host "[開] 預設瀏覽器直接開檔(不經伺服器)" -ForegroundColor Green }
        catch { Write-Host ("[開] 開不起來:" + $_.Exception.Message + " · 自己開:" + $page) -ForegroundColor Yellow }
    }
} finally {
    Pop-Location
}
Write-Host "── 摘要 ──" -ForegroundColor Cyan
$steps | ForEach-Object { Write-Host "  · $_" }
Write-Host ("[UI 引擎] 結束 rc 0 · " + [int]((Get-Date) - $t0).TotalSeconds + "s · 範本夾 VIA_Reports\ui_engine\templates\ 或 supportive modules\ui_support\ui_templates\ 丟 .html → -Template 檔名") -ForegroundColor Green
$global:LASTEXITCODE = 0
