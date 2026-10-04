# CELERITAS-TEMPLATE-JOIN v1
# Start-VIA-UIEngine-v0101.ps1 — 一鍵:環境檢查 / 照測過版本安裝 → 匯入滑鼠輸入(下載夾)→ 產 HTML U/I → 自動跳出(不走伺服器)
#   v0101(操作員 2026-10-04「VCGC 輸入只有系統存放位置及資料庫兩個位置;避免用鍵盤,全用滑鼠:WINDOW I/O 拖曳式 · 下拉 · 打勾」
#     「自動跳出 HTML U/I 不走 SERVER;自適應銜接各種模板設計風格」):
#     · 匯入:頁上「匯出輸入」下載的 VIA_UI_Input*.json(下載夾最新一份,比上次匯入新才收)→ CGC_MDL261 import --apply
#       (位置 · 範本 · 主題 · 勾選族群 → ui_config.json;起始日 / 成員 / as-of → VDF 成員帳本);-NoImport 不匯入。
#     · -Pick:Windows 原生選夾窗(滑鼠)選 系統存放位置 / 資料庫位置,同一條匯入路徑寫進參數。
#     · -Run:照頁上勾選的族群(ui_config.json run_groups)經 VDF_MDL012 尾版擷取(大類起始日 · as-of · 成員都照帳本);live 要本視窗雙閘,沒開 = MDL012 照實 rc 4。
#     · 引擎取尾版 CGC_MDL261_UIEngine(v0101 起左面板全滑鼠、右面板首頁三矩陣 · 結果頁 · 末頁細節矩陣)。
#   操作員(2026-10-04):「一個引擎自動安裝所有工具跟環境,依照我測試過的結果,然後啟動 HTML U/I,讓操作介面全部都在上面實習而不動系統;
#     U/I 架構會自適應式吻合任何模板設計、參數可調整;啟動檔兼最簡單的 HTML 標準模板,未來的拿來套用;DuckDB 顯式資料庫於 U/I」。
#   ① 環境(不動系統):全部經 VCGC 唯一入口。
#       RunGate(CGC_MDL137)probe 家族境能不能跑 · EnvGovernance(CGC_MDL135)lkgc status = 你測過全綠時存的版本鎖。
#       -Install 才動手:LKGC 可用 → rollback --to LKGC_latest.json --execute --approve(uv pip sync 照鎖逐境重建;只進 via_* 隔離境,
#         不給 --approve-remove = 不刪 base 任何東西);LKGC 不可用 → RunGate run --approve-install(只把缺件裝進家族境)。
#       安裝要連網:本視窗先開雙閘(操作員的手;本檔只檢查、永不代設),沒開 = 跳過安裝、照實說。
#   ② 產頁:CGC_MDL261_UIEngine 尾版 build(引擎 → JSON 快照 → 頁;零 CDN)。參數疊層 = 正本 VIA_UI_EngineConfig_v*.json ←
#       工作副本 VIA_Reports\ui_engine\ui_config.json ← -Config ← -Set a.b=值。-Template X = 範本夾任何 .html(未來的設計);不給 = 內建標準範本。
#   ③ 開:預設瀏覽器直接開檔(file://,不需伺服器);-Serve = 另起只綁 127.0.0.1 的只讀樞紐(改 ui_config.json 重新整理即生效),開 http://127.0.0.1:埠/。
#   用法(在 VeritasIntelligenceAnalytics 根目錄):
#     .\Start-VIA-UIEngine-v0101.ps1                                   # 檢查環境 → 匯入下載夾的滑鼠輸入 → 內建標準範本 → 自動跳出
#     .\Start-VIA-UIEngine-v0101.ps1 -Pick                             # Windows 選夾窗選兩個位置(滑鼠)
#     .\Start-VIA-UIEngine-v0101.ps1 -Run                              # 照頁上勾選的族群擷取(live 先開雙閘)→ 重產 → 跳出
#     .\Start-VIA-UIEngine-v0101.ps1 -Install                          # 環境不綠就照 LKGC 裝(先開雙閘)
#     .\Start-VIA-UIEngine-v0101.ps1 -Template VDF_FetchGroups_Compact_v0100
#     .\Start-VIA-UIEngine-v0101.ps1 -Set "theme.primary_color=#c2410c","layout.sidebar_width=300px"
#     .\Start-VIA-UIEngine-v0101.ps1 -Serve -Port 8766                 # 本機只讀樞紐(參數熱更新)
#     .\Start-VIA-UIEngine-v0101.ps1 -InitConfig                       # 寫一份可改的 ui_config.json 工作副本
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
    [switch]$NoImport,
    [switch]$Run,
    [ValidateSet("live", "fixture", "block")][string]$Mode = "live",
    [switch]$Pick,
    [string]$Downloads = "",
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
$eng = Get-ChildItem $reg -Filter "CGC_MDL261_UIEngine_v*.py" -File | Sort-Object Name | Select-Object -Last 1
$workDir = Join-Path $VIA "VIA_Reports\ui_engine"
if (-not $vcgc -or -not $eng) { Write-Host "[UI 引擎] VCGC 入口或 CGC_MDL261_UIEngine 不在 $reg" -ForegroundColor Red; $global:LASTEXITCODE = 3; return }
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
    # ①' 滑鼠輸入:-Pick(Windows 選夾窗)與 下載夾的 VIA_UI_Input*.json
    New-Item -ItemType Directory -Force -Path $workDir | Out-Null
    $toImport = @()
    if ($Pick) {
        try {
            Add-Type -AssemblyName System.Windows.Forms
            $loc = @{}
            foreach ($k in @(@("system_root", "選『系統存放位置』(VeritasIntelligenceAnalytics 根)"), @("db_root", "選『資料庫位置』(含 .duckdb 的輸出根)"))) {
                $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
                $dlg.Description = $k[1]; $dlg.ShowNewFolderButton = $false
                if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $loc[$k[0]] = $dlg.SelectedPath }
            }
            if ($loc.Count) {
                $pf = Join-Path $workDir "_pick_input.json"
                (@{ schema = "VIA_UI_Input/1"; locations = $loc } | ConvertTo-Json -Depth 4) | Set-Content -Path $pf -Encoding utf8
                $toImport += $pf
                Write-Host ("[選夾] " + (($loc.GetEnumerator() | ForEach-Object { $_.Key + " = " + $_.Value }) -join " · ")) -ForegroundColor Cyan
            } else { Write-Host "[選夾] 沒選(照原設定)" -ForegroundColor DarkYellow }
        } catch { Write-Host ("[選夾] 這台開不了 Windows 選夾窗:" + $_.Exception.Message + " → 用頁上的下拉") -ForegroundColor Yellow }
    }
    if (-not $NoImport) {
        $dl = if ($Downloads) { $Downloads } else { Join-Path $HOME "Downloads" }
        $mark = Join-Path $workDir "_last_import.txt"
        $last = if (Test-Path $mark) { [datetime](Get-Content $mark -Raw).Trim() } else { [datetime]::MinValue }
        $inp = if (Test-Path $dl) { Get-ChildItem $dl -Filter "VIA_UI_Input*.json" -File | Sort-Object LastWriteTime | Select-Object -Last 1 } else { $null }
        if ($inp -and $inp.LastWriteTime -gt $last) { $toImport += $inp.FullName; Write-Host ("[匯入] 下載夾 " + $inp.Name + " · " + $inp.LastWriteTime) -ForegroundColor Cyan }
        elseif ($inp) { Write-Host ("[匯入] " + $inp.Name + " 已匯過(沒有更新的)") -ForegroundColor DarkGray }
    }
    foreach ($f in $toImport) {
        $im = Invoke-Py @($eng.FullName, "import", $f, "--apply") 600
        $im.out | Where-Object { $_ -match '^\s*(\[|  \[)' } | ForEach-Object { Write-Host "   $_" }
        $steps += ("匯入:" + (Split-Path $f -Leaf) + " rc " + $im.rc)
        if ($f -notlike "*_pick_input.json" -and $im.rc -le 2) { (Get-Date).ToString("o") | Set-Content -Path (Join-Path $workDir "_last_import.txt") -Encoding utf8 }
    }
    # ①'' 擷取(-Run):照頁上勾選的族群
    if ($Run) {
        $cfgW = Join-Path $workDir "ui_config.json"
        $rg = @(); $dbr = $FetchHome
        if (Test-Path $cfgW) { try { $cj = Get-Content $cfgW -Raw -Encoding utf8 | ConvertFrom-Json; if ($cj.run_groups) { $rg = @($cj.run_groups) }; if ($cj.locations.db_root) { $dbr = $cj.locations.db_root } } catch { } }
        $m12 = Get-ChildItem (Join-Path $VIA "functional modules\VDF") -Filter "VDF_MDL012_FetchGroups_v*.py" -File | Sort-Object Name | Select-Object -Last 1
        if (-not $rg.Count) { Write-Host "[擷取] 頁上沒有勾選族群(先在頁上打勾 → 匯出輸入)" -ForegroundColor Yellow; $steps += "擷取:沒有勾選族群" }
        elseif (-not $m12) { Write-Host "[擷取] VDF_MDL012_FetchGroups 不在" -ForegroundColor Red; $steps += "擷取:MDL012 不在" }
        else {
            Write-Host ("[擷取] " + ($rg -join ",") + " · 輸出根 " + $dbr + " · 模式 " + $Mode) -ForegroundColor Cyan
            $fr = Invoke-Py @($m12.FullName, "run", "--groups", ($rg -join ","), "--home", $dbr, "--mode", $Mode) $TimeoutSec
            $fr.out | Where-Object { $_ -match '^\s*(\[|[a-z0-9]{3,6}\s+rc)' } | Select-Object -Last 20 | ForEach-Object { Write-Host "   $_" }
            $steps += ("擷取:" + ($rg -join ",") + " rc " + $fr.rc + $(if ($fr.rc -eq 4) { "(雙閘沒開)" } else { "" }))
            $mo = Invoke-Py @($m12.FullName, "monitor", "--home", $dbr, "--no-write") 900
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
