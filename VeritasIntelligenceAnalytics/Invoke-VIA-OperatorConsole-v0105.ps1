# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-OperatorConsole-v0105.ps1 — **唯一入口**(R30)
#   v0104→v0105(Codex #356 P2 兩條 · Z282①② · 操作員 R30「記錄下為何一直重複出錯 logging lesson-learned 沒導入」):
#   ⓐ 全景實測只沿用「上一輪 rc 0」的結果(v0104 連 rc 2 = 有步沒跑完也沿用,會把不完整的結果留 12 小時)
#   ⓑ 資料家指紋全遞迴(v0104 只掃三層;消費端 EngineBus / DataBroker 是全遞迴,深層 .duckdb 改了指紋不變)
#   ⓒ ⑥b 教訓帳:每輪跑 CGC_MDL058 Lessons 尾版(收割存證 → RESULT MATRIX · ROOT CAUSES & SOLUTIONS;只增),把根因帳帶進流程,
#      畫面印根因筆數;操作員手記用 via-lessons --record 現象 --cause 根因 --fix 解法。其餘照 v0104。
# (v0104 起):VCGC → ENV → SYNC → VDF → VRN → 單一路徑交叉驗證 → 布建紀錄上傳 → 跳出簡單版 HTML
#   v0103→v0104(操作員 R29:「走整個 VCGC 流程還需要十分鐘 … 自 VCGC 更快速啟動所有」;容器實測 v0103 全程 118 秒):
#   ⓐ 流程閘只跑一次:① 過閘後在**本行程**設 VIA_GATE_PASSED_HEAD / _AT / _LINE(finally 還原);Invoke-VIA-Sweep v0104 起看到同一 HEAD、
#      15 分鐘內就沿用,不再自己跑一次 VCGC status(省約 15 秒)。
#   ⓑ 全景實測沒變就沿用:上一輪跑完時記下「樹指紋」(HEAD 之後的工作區差異 + 未追蹤檔;布建紀錄冊不算)與「資料家指紋」
#      (路徑 + 每本 .duckdb 的大小 / 時間)→ VIA_Reports\operator_console\SWEEP_REUSE_latest.json。本輪兩個指紋都一樣、HEAD 之間只差紀錄冊、
#      上一輪全景實測 12 小時內且不是流程閘擋下 → ③ 沿用上一輪(報告仍是那一份),印「沿用 · 幾分鐘前 · 要重跑加 -Full」。
#      -Full = 一律重跑。任何一樣對不上 = 照舊重跑(寧可多跑,不拿舊結果冒充)。
#   ⓒ 每步計時:結尾印「各步秒數」並寫 VIA_Reports\operator_console\TIMING_latest.json(單一路徑驗證頁讀它)。其餘照 v0103。
#   v0102→v0103(操作員 R27:「單一路徑實測 VCGC VDF VRN 邊實測邊修邊註冊 … 驗證結果交互比對 跳出簡單版 HTML 介面 整個收尾」
#   「加速器 網路工具 PS 工具標準模板都要加 環境工具布建完成紀錄上傳 收尾儲存備份」):
#   ⑥ 單一路徑驗證(CGC_MDL242):路徑每一步 · 實際執行的尾版 × 編號冊 × 註冊冊 × 鎖冊 · 兩鏈 × 燈鎖 × 上一輪 → 簡單版頁;
#      同時在 registry\VIA_EnvProvision_Ledger_v0100.jsonl 追加一行布建完成紀錄(只增)
#   ⑦ 上傳紀錄:「是 / 否」(預設「是」)→ git commit + push **只含那一本紀錄冊**(其他改動一個都不帶);-NoUpload 不問不傳
#   結尾只跳出簡單版驗證頁(頁上有連結到操作台 · SYNCHRONIZER · 全景報告)。其餘照 v0102。
#   v0101→v0102(操作員 R26:「都寫成一個 PS CODE 全部整合唯一解決問題 從 VCGC 的頭跑流程 ENV MANAGER 理應自動檢查上下所有 LIBS 跟環境
#   都有布建完畢 尤其是加速器 網路工具等輔助工具常被忽略 註冊更新 SYNC 跳出 HTML U/I」):
#   ①b PS 端事實(PS 版本 · Celeritas PS7 版號與是否已套 · Invoke-VIAPython / Invoke-VIACeleritasScoped 在位)→ env_manager\PS_SIDE_latest.json
#   ①c ENV MANAGER(CGC_MDL240,只查不裝):四件工具鎖版 + 載得起來(加速器 · 網路 · LAYOUT · NLP)· 覆蓋 · 家族境 · 工具冊 · 鏈上缺件 ·
#      執行檔 · PS 端 → 一個總判;缺的只印補法(一貼即用 .ps1 在 VIA_Reports\env_governance),裝件是你的手
#   ①d 註冊同步(CGC_MDL238 v0102 sync-check,乾跑):registry-sync(新 · 變更 · 退役)· VRN 邏輯冊 · 格式鎖 · 編號冊;
#      有待同步 → Windows「是 / 否」對話框(預設「否」)= 你對 VCGC registry-sync --apply 的明確批准(Master Prompt);-ApproveRegistrySync 不問直接批
#   ①e 換模板(CGC_MDL241 模板轉接器,零 token):把任何設計檔(W3C / Style Dictionary / Tokens Studio JSON · CSS :root · 含 <style> 的 HTML,
#      例 Claude Design 匯出頁 · 另一份 VIA TemplateSSOT)拖進 VIA_Reports\template_adapter\inbox\ → 自動對鍵 · 驗值 · 對比 · LAYOUT 多版型打分優化 ·
#      圖規格 → 候選 + 預覽頁;Windows「是 / 否」(預設「否」)→ 是 = 寫 TemplateSSOT 新版號 + CGC_MDL238 template --lock 重鎖;-TemplateIn <檔> 指定檔
#   ⑤ 頁尾同時跳出操作台與 SYNCHRONIZER(-NoOpen 不開)。其餘照 v0101。
#   v0100→v0101(操作員 R25:「從 VCGC 一路邊測邊修正邊編號註冊鎖定向下到 VDF 生成資料庫 再從 VCGC 一路向下 … 向 VRN 他需要擷取資料
#   透過 VCGC 進入資料庫或轉交 VDF 擷取透過 VCGC 返回 VRN … VCGC 統合 HTML U/I … SYNCHORIZER 交互整合一切」):
#   ②b VCGC→VDF 建庫計畫(CGC_MDL239 build,乾跑):庫表冊「正庫」逐張量在不在 / 新不新,缺的排 VDF 項;有得跑就跳 Windows「是 / 否」
#      對話框(滑鼠)問要不要建庫;「是」= build --apply。需網路的項要**操作員自己**先開同意閘 VIA_NET_CONSENT(本支不代設;
#      沒開 = GATED,照實列出)。-BuildDb 直接建(不問)· -NoBuild 不建不問。
#   ⑤ 操作台頁用 CGC_MDL238 最新版(v0101 起:總覽 +資料中介 · 繞道 · 建庫三燈;頁尾 dock 出 SYNCHRONIZER / 中央 UI 複本,掛本台外掛)。
#   ⑥ VCGC 資料中介摘要(路由 · 繞道 · 建庫 · 要料帳)。其餘照 v0100。
#   操作員 2026-09-28:「VCGC 全部步驟自動化 唯一要輸入的地方是系統檔案夾位置及資料庫檔案夾位置 WINDOW I/O 基本上整個輸入以滑鼠即可」
#   「第一頁高整合結果 三色燈掌握 其他頁是詳細結果及驗證 輸出統一為 PARQUET 最節省 TOKEN 架構」。
#   ⓪ 兩個資料夾(唯一的輸入):第一次或 -Pick 時跳 Windows 選夾視窗(系統資料夾 · 資料庫資料夾);記在
#      VIA_Reports\operator_console\OPERATOR_PATHS.json(本機檔,不進 git)。之後每次把資料庫資料夾設成**本行程**的 VIA_DATA_HOME
#      (CGC_MDL123 解析序第一順位;跑完還原,不動機器環境變數)。選的系統資料夾若是另一份副本,改跑那份副本的本支。
#   ① VCGC 入口 = 流程閘(PSGATE-1):沒讀到「[流程] 政策過」就停(exit 3),後面一步都不跑。
#   ② 有 -ApplyInput <輸入包.json>(操作台頁「匯出輸入包」):經 CGC_MDL238 apply 入冊(去重後只走 CGC_MDL139 apply_set)。
#   ③ 全景實測(Invoke-VIA-Sweep 最新一版:VDF / VRN 兩條鏈 · 橋 · 全景 · DB 面板 · 工具 · rich 矩陣);-SkipSweep 略過。
#   ④ 輸出統一 Parquet:CGC_MDL238 parquet --apply(每本 .duckdb 每張表 → parquet zstd;DuckDB 管家每表一個 VIEW;來源庫唯讀)。
#   ⑤ 操作台頁:CGC_MDL238 page(第一頁總覽三色燈;其後 輸入摘要 · 引擎 · 運作 · 驗證 · 輸出 · 資料庫擷取),跑完自動開(-NoOpen 不開)。
#   不代開網路同意閘(L07/L08);只經 Invoke-VIAPython 叫 python;每步包 Invoke-VIACeleritasScoped(有就套)。
# 用法(站在倉根):.\VIA-OperatorConsole.ps1   參數:-Full · -Pick · -ApplyInput <json> · -SkipSweep · -NoOpen · -SystemDir <夾> · -DataDir <夾> · -BuildDb · -NoBuild · -ApproveRegistrySync · -TemplateIn <檔> · -NoUpload
# 結束碼:0 = 每步跑完 · 2 = 有步沒跑完 · 3 = 流程閘沒過 / 沒選資料夾
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Pick,
    [string]$ApplyInput = "",
    [switch]$SkipSweep,
    [switch]$NoOpen,
    [string]$SystemDir = "",
    [string]$DataDir = "",
    [switch]$BuildDb,
    [switch]$NoBuild,
    [switch]$ApproveRegistrySync,
    [string]$TemplateIn = "",
    [switch]$NoUpload,
    [switch]$Full
)

$VIA = $PSScriptRoot
$Repo = Split-Path $VIA -Parent
$StartDir = (Get-Location).Path
$prevHome = $env:VIA_DATA_HOME
$prevGate = @($env:VIA_GATE_PASSED_HEAD, $env:VIA_GATE_PASSED_AT, $env:VIA_GATE_PASSED_LINE)
$exitCode = 0
try {
    Set-Location -LiteralPath $VIA
    try {
        $join = Join-Path $VIA "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
        if (Test-Path -LiteralPath $join) { . $join; Write-Host ("  [加速器] 套對 " + $script:CeleritasPS7.Version) -ForegroundColor DarkGray }
    } catch {
        Write-Host "  [加速器] 正主載入失敗,略過" -ForegroundColor DarkGray
    }
    $env:VIA_FROM_VCGC = "YES"
    $env:VIA_VCGC_PUSH = "NO"
    $env:VIA_NO_OPEN = "1"
    if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
        $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
        if (Test-Path -LiteralPath $pyMod) { . $pyMod }
    }
    if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
        Write-Host "  [操作台] 中央 Invoke-VIAPython 不在(VIA_PS_PyProgress_Module.ps1 缺);不繞過直呼 python,停。" -ForegroundColor Red
        $exitCode = 3
        return
    }
    $hasScoped = [bool](Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue)
    $reg = Join-Path $VIA "supportive modules\registry"
    $engine = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL238_OperatorConsole_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    $console = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    $broker = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL239_DataBroker_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    $envmgr = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL240_EnvManager_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    $adapter = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL241_TemplateAdapter_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    $pathv = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL242_PathVerify_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    if ($null -eq $engine -or $null -eq $console) {
        Write-Host "  [操作台] CGC_MDL238 或 CGC_MDL149 尾版不在(先 git pull)" -ForegroundColor Red
        $exitCode = 2
        return
    }

    function Invoke-OcPy {
        # 一步:包在 Invoke-VIACeleritasScoped(有就套)裡跑 Invoke-VIAPython;回 (rc, 輸出行)
        param([string]$Script, [string[]]$ArgList)
        $q = { param($v) "'" + (("" + $v) -replace "'", "''") + "'" }
        $cmd = "Invoke-VIAPython -Family 'vrn' " + (& $q $Script) + " " + ((@($ArgList) | ForEach-Object { & $q $_ }) -join " ") + " 2>&1"
        $body = [scriptblock]::Create($cmd)
        $global:LASTEXITCODE = 0
        $raw = if ($hasScoped) { Invoke-VIACeleritasScoped -Body $body } else { & $body }
        return [pscustomobject]@{ rc = $global:LASTEXITCODE; lines = @($raw | ForEach-Object { "" + $_ }) }
    }

    function Select-OcFolder {
        # Windows 選夾視窗(唯一的輸入);非 Windows 或沒有視窗環境 = 照實說並停
        param([string]$Title, [string]$Start)
        try {
            Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
            $dlg = [System.Windows.Forms.FolderBrowserDialog]::new()
            $dlg.Description = $Title
            $dlg.UseDescriptionForTitle = $true
            if ($Start -and (Test-Path -LiteralPath $Start)) { $dlg.SelectedPath = $Start }
            if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dlg.SelectedPath }
            return ""
        } catch {
            Write-Host ("  [操作台] 這個環境開不了 Windows 選夾視窗:" + $_.Exception.Message + "(改用 -SystemDir / -DataDir)") -ForegroundColor Yellow
            return ""
        }
    }

    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║  VIA 唯一入口 v0105 · VCGC→ENV→SYNC→VDF→VRN→驗證→紀錄→U/I  ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

    # 每步計時(ⓒ)
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $script:lap = 0.0
    $times = [ordered]@{}
    function Set-OcLap {
        param([string]$Name)
        $now = $clock.Elapsed.TotalSeconds
        $times[$Name] = [Math]::Round($now - $script:lap, 1)
        $script:lap = $now
    }

    function Get-OcTreeMark {
        # 樹指紋:HEAD 之後的工作區差異 + 未追蹤檔(名 · 大小 · 時間);布建紀錄冊不算(每輪都會多一行)
        $ex = ":(exclude)*VIA_EnvProvision_Ledger_v*.jsonl"
        $d = @(git -C $Repo diff HEAD --no-ext-diff --binary -- . $ex 2>$null) -join "`n"
        $u = @(git -C $Repo ls-files -o --exclude-standard -- . $ex 2>$null | ForEach-Object {
            $f = Join-Path $Repo $_
            if (Test-Path -LiteralPath $f -PathType Leaf) { $i = Get-Item -LiteralPath $f; $_ + "|" + $i.Length + "|" + $i.LastWriteTimeUtc.Ticks } else { "" + $_ }
        }) -join "`n"
        $sha = [Security.Cryptography.SHA256]::Create()
        return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($d + "`n--`n" + $u))) -replace "-", "").Substring(0, 16)
    }

    function Get-OcDataMark {
        param([string]$Dir)
        $f = @(Get-ChildItem -LiteralPath $Dir -Recurse -Filter "*.duckdb" -File -ErrorAction SilentlyContinue | Sort-Object FullName |
            ForEach-Object { $_.FullName + "|" + $_.Length + "|" + $_.LastWriteTimeUtc.Ticks })
        $sha = [Security.Cryptography.SHA256]::Create()
        return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Dir + "`n" + ($f -join "`n")))) -replace "-", "").Substring(0, 16)
    }

    # ⓪ 兩個資料夾
    $saved = $null
    $pathsFile = Join-Path $VIA "VIA_Reports\operator_console\OPERATOR_PATHS.json"
    if (Test-Path -LiteralPath $pathsFile) { try { $saved = Get-Content -LiteralPath $pathsFile -Raw -Encoding utf8 | ConvertFrom-Json } catch { $saved = $null } }
    $sys = if ($SystemDir) { $SystemDir } elseif ($saved -and $saved.system -and -not $Pick) { "" + $saved.system } else { "" }
    $dat = if ($DataDir) { $DataDir } elseif ($saved -and $saved.data -and -not $Pick) { "" + $saved.data } else { "" }
    if (-not $sys) { $sys = Select-OcFolder "① 選「系統資料夾」(VeritasIntelligenceAnalytics 所在的那一份)" $VIA }
    if (-not $dat) { $dat = Select-OcFolder "② 選「資料庫資料夾」(放 .duckdb 與 parquet 的資料家)" ("" + $env:VIA_DATA_HOME) }
    if (-not $sys -or -not $dat) {
        Write-Host "  [操作台] 兩個資料夾都要選(或給 -SystemDir / -DataDir);停。" -ForegroundColor Red
        $exitCode = 3
        return
    }
    $sysVia = if (Test-Path -LiteralPath (Join-Path $sys "supportive modules")) { $sys } elseif (Test-Path -LiteralPath (Join-Path $sys "VeritasIntelligenceAnalytics")) { Join-Path $sys "VeritasIntelligenceAnalytics" } else { $sys }
    if ((Resolve-Path -LiteralPath $sysVia -ErrorAction SilentlyContinue).Path -ne (Resolve-Path -LiteralPath $VIA).Path) {
        $other = Get-ChildItem -LiteralPath $sysVia -Filter "Invoke-VIA-OperatorConsole-v*.ps1" -File -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
        if ($null -ne $other) {
            Write-Host ("  [操作台] 系統資料夾是另一份副本 → 改跑 " + $other.FullName) -ForegroundColor Cyan
            $pass = @{ SystemDir = $sysVia; DataDir = $dat }
            if ($ApplyInput) { $pass["ApplyInput"] = $ApplyInput }
            if ($SkipSweep) { $pass["SkipSweep"] = $true }
            if ($NoOpen) { $pass["NoOpen"] = $true }
            if ($BuildDb) { $pass["BuildDb"] = $true }
            if ($NoBuild) { $pass["NoBuild"] = $true }
            if ($ApproveRegistrySync) { $pass["ApproveRegistrySync"] = $true }
            if ($TemplateIn) { $pass["TemplateIn"] = $TemplateIn }
            if ($NoUpload) { $pass["NoUpload"] = $true }
            if ($Full) { $pass["Full"] = $true }
            & $other.FullName @pass
            $exitCode = $LASTEXITCODE
            return
        }
        Write-Host "  [操作台] 選的系統資料夾裡沒有操作台;照這一份跑" -ForegroundColor Yellow
    }
    $null = Invoke-OcPy $engine.FullName @("paths", "--system", $sysVia, "--data", $dat)
    $env:VIA_DATA_HOME = $dat
    Write-Host ("  [資料夾] 系統 " + $sysVia) -ForegroundColor DarkGray
    Write-Host ("  [資料夾] 資料庫 " + $dat + "(本行程 VIA_DATA_HOME)") -ForegroundColor DarkGray
    Set-OcLap "⓪ 資料夾"

    # ① VCGC 流程閘(PSGATE-1)
    $g = Invoke-OcPy $console.FullName @("status")
    $flow = @($g.lines | Where-Object { $_ -match '\[流程\]\s*政策過' } | Select-Object -First 1)
    if ($flow.Count -eq 0) {
        Write-Host "  [流程閘] 沒讀到「[流程] 政策過」→ 依 PSGATE-1 停在這裡" -ForegroundColor Red
        $exitCode = 3
        return
    }
    Write-Host ("  [流程閘] 過:" + $flow[0].Trim()) -ForegroundColor Green
    # ⓐ 本行程記下「剛過閘」:子步(Invoke-VIA-Sweep v0104 起)同 HEAD、15 分鐘內沿用,不再跑第二次
    $env:VIA_GATE_PASSED_HEAD = ("" + (git -C $Repo rev-parse HEAD 2>$null)).Trim()
    $env:VIA_GATE_PASSED_AT = "" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $env:VIA_GATE_PASSED_LINE = $flow[0].Trim()
    Set-OcLap "① VCGC 流程閘"

    # ①b PS 端事實(ENV MANAGER 的 Ⓒ 區讀這一份;一小時內有效)
    $cel = $null
    if (Get-Command Get-CeleritasStatus -ErrorAction SilentlyContinue) { try { $cel = Get-CeleritasStatus } catch { $cel = $null } }
    $side = [ordered]@{
        ts                 = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        ps_version         = $PSVersionTable.PSVersion.ToString()
        ps_edition         = "" + $PSVersionTable.PSEdition
        celeritas_version  = if ($cel) { "" + $cel.Version } else { "" }
        celeritas_applied  = if ($cel) { [bool]$cel.Applied } else { $false }
        invoke_viapython   = [bool](Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)
        celeritas_scoped   = $hasScoped
        os                 = [System.Environment]::OSVersion.VersionString
    }
    $sideDir = Join-Path $VIA "VIA_Reports\env_manager"
    New-Item -ItemType Directory -Force -Path $sideDir | Out-Null
    ($side | ConvertTo-Json) | Set-Content -LiteralPath (Join-Path $sideDir "PS_SIDE_latest.json") -Encoding utf8

    # ①c ENV MANAGER(只查不裝)
    if ($null -eq $envmgr) {
        Write-Host "  ①c ENV MANAGER · ABSENT(CGC_MDL240 尾版不在;先 git pull)" -ForegroundColor Red
        $exitCode = 2
    } else {
        $ev = Invoke-OcPy $envmgr.FullName @()
        $verdictLine = @($ev.lines | Where-Object { $_ -match '\[ENV MANAGER\] 總判' } | Select-Object -Last 1)
        $ev.lines | Where-Object { $_ -match '^\s*(RED|AMBER|NODATA)\s' -or $_ -match '└ 補法' } | Select-Object -First 40 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
        $col = if ($ev.rc -eq 0) { "Green" } elseif ($ev.rc -eq 1) { "Red" } else { "Yellow" }
        Write-Host ("  ①c ENV MANAGER · " + $(if ($verdictLine.Count) { $verdictLine[0].Trim() } else { "rc=" + $ev.rc })) -ForegroundColor $col
        $plan = Join-Path $VIA "VIA_Reports\env_governance\TOOLS_PLAN_latest.ps1"
        if ($ev.rc -ne 0 -and (Test-Path -LiteralPath $plan)) { Write-Host ("     補法(一貼即用;裝件是你的手,要網路先開同意閘):" + $plan) -ForegroundColor Yellow }
        if ($ev.rc -eq 1) { $exitCode = 2 }
    }
    Set-OcLap "①b/①c PS 端 · ENV MANAGER"

    # ①d 註冊同步(乾跑)→ 有待同步才問(預設「否」)
    $sc = Invoke-OcPy $engine.FullName @("sync-check")
    $sc.lines | Where-Object { $_ -match '^\s*(OK|SKIP|FAIL|UNTESTED)\s' -or $_ -match '\[SYNC\]' } | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
    $pending = @($sc.lines | Where-Object { $_ -match '^\s*SKIP\s+VCGC 元件註冊冊' })
    if ($pending.Count -gt 0) {
        $go = [bool]$ApproveRegistrySync
        if (-not $go) {
            try {
                Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
                $msg = "VCGC 元件註冊冊有待同步:`n" + $pending[0].Trim() + "`n`n要批准 via-vcgc registry-sync --apply 嗎?(寫入已追蹤的註冊冊;之後要 commit)"
                $ans = [System.Windows.Forms.MessageBox]::Show($msg, "VIA 唯一入口 · 註冊同步批准", [System.Windows.Forms.MessageBoxButtons]::YesNo,
                    [System.Windows.Forms.MessageBoxIcon]::Question, [System.Windows.Forms.MessageBoxDefaultButton]::Button2)
                $go = ($ans -eq [System.Windows.Forms.DialogResult]::Yes)
            } catch {
                Write-Host "     這個環境開不了 Windows 對話框;不批准(要批請加 -ApproveRegistrySync)" -ForegroundColor Yellow
            }
        }
        if ($go) {
            $vc = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" -File | Sort-Object Name | Select-Object -Last 1
            $ra = Invoke-OcPy $vc.FullName @("registry-sync", "--apply")
            Write-Host ("  ①d registry-sync --apply(你批准)· rc=" + $ra.rc) -ForegroundColor $(if ($ra.rc -eq 0) { "Green" } else { "Yellow" })
            $ra.lines | Select-Object -Last 6 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
            Write-Host "     註冊冊是已追蹤檔:請 git add / commit / push(或交給 AI 下一輪開 PR)" -ForegroundColor Yellow
            if ($ra.rc -ne 0) { $exitCode = 2 }
            $null = Invoke-OcPy $engine.FullName @("sync-check")
        } else {
            Write-Host "  ①d 註冊同步 · 未批准(照舊乾跑;頁上黃燈)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ①d 註冊同步 · 無待同步" -ForegroundColor Green
    }
    Set-OcLap "①d 註冊同步"

    # ①e 換模板:inbox 有比上次候選新的設計檔(或 -TemplateIn)才動
    $inbox = Join-Path $VIA "VIA_Reports\template_adapter\inbox"
    New-Item -ItemType Directory -Force -Path $inbox | Out-Null
    $tplSrc = $null
    if ($TemplateIn -and (Test-Path -LiteralPath $TemplateIn)) {
        $tplSrc = (Resolve-Path -LiteralPath $TemplateIn).Path
    } else {
        $last = Join-Path $VIA "VIA_Reports\template_adapter\PLAN_latest.json"
        $cut = if (Test-Path -LiteralPath $last) { (Get-Item -LiteralPath $last).LastWriteTime } else { [datetime]::MinValue }
        $new = Get-ChildItem -LiteralPath $inbox -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match '^\.(json|css|html?|scss)$' -and $_.LastWriteTime -gt $cut } |
            Sort-Object LastWriteTime | Select-Object -Last 1
        if ($new) { $tplSrc = $new.FullName }
    }
    if ($null -eq $adapter) {
        Write-Host "  ①e 換模板 · ABSENT(CGC_MDL241 尾版不在)" -ForegroundColor Yellow
    } elseif ($null -eq $tplSrc) {
        Write-Host ("  ①e 換模板 · 沒有新設計檔(要換就把設計檔拖進 " + $inbox + ")") -ForegroundColor DarkGray
    } else {
        $tp = Invoke-OcPy $adapter.FullName @("plan", "--in", $tplSrc)
        $tp.lines | Where-Object { $_ -match '\[模板轉接\]|預覽' } | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
        $prev = Join-Path $VIA "VIA_Reports\template_adapter\PREVIEW_latest.html"
        if ($tp.rc -eq 0) {
            if (-not $NoOpen -and (Test-Path -LiteralPath $prev)) { try { Invoke-Item -LiteralPath $prev } catch { } }
            $go = $false
            try {
                Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
                $sum = @($tp.lines | Where-Object { $_ -match '\[模板轉接\]' } | Select-Object -First 1)
                $msg = "新設計檔:" + (Split-Path $tplSrc -Leaf) + "`n" + $(if ($sum.Count) { $sum[0].Trim() } else { "" }) + "`n`n預覽頁已開。要換成這個模板嗎?`n(寫 TemplateSSOT 新版號並重鎖格式鎖;舊版留著,可換回)"
                $ans = [System.Windows.Forms.MessageBox]::Show($msg, "VIA 唯一入口 · 換模板", [System.Windows.Forms.MessageBoxButtons]::YesNo,
                    [System.Windows.Forms.MessageBoxIcon]::Question, [System.Windows.Forms.MessageBoxDefaultButton]::Button2)
                $go = ($ans -eq [System.Windows.Forms.DialogResult]::Yes)
            } catch {
                Write-Host "     這個環境開不了 Windows 對話框;不換(候選與預覽留在 VIA_Reports\template_adapter)" -ForegroundColor Yellow
            }
            if ($go) {
                $ta = Invoke-OcPy $adapter.FullName @("apply")
                $ta.lines | Select-Object -Last 4 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
                if ($ta.rc -eq 0) {
                    $tl = Invoke-OcPy $engine.FullName @("template", "--lock")
                    Write-Host ("  ①e 換模板 · 已寫新版號並重鎖 · rc=" + $tl.rc + "(TemplateSSOT 與格式鎖是已追蹤檔:請 commit,或交給 AI 下一輪開 PR)") -ForegroundColor Green
                    if ($tl.rc -ne 0) { $exitCode = 2 }
                } else {
                    Write-Host "  ①e 換模板 · 沒寫(看上面原因)" -ForegroundColor Yellow
                    $exitCode = 2
                }
            } else {
                Write-Host "  ①e 換模板 · 未換(候選與預覽留著)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ①e 換模板 · 設計檔裡沒有對得上的鍵(看預覽頁的「沒對上」)" -ForegroundColor Yellow
        }
    }

    Set-OcLap "①e 換模板"
    # ② 輸入包入冊
    if ($ApplyInput) {
        $a = Invoke-OcPy $engine.FullName @("apply", "--file", $ApplyInput, "--apply")
        Write-Host ("  ② 輸入包入冊 · rc=" + $a.rc) -ForegroundColor $(if ($a.rc -eq 0) { "Green" } else { "Yellow" })
        $a.lines | Select-Object -Last 12 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
        if ($a.rc -ne 0) { $exitCode = 2 }
    }

    # ②b VCGC→VDF 建庫計畫(乾跑)→ 滑鼠「是 / 否」→ build --apply
    if ($null -eq $broker) {
        Write-Host "  ②b VDF 建庫計畫 · ABSENT(CGC_MDL239 DataBroker 尾版不在)" -ForegroundColor Yellow
    } elseif (-not $NoBuild) {
        $bp = Invoke-OcPy $broker.FullName @("build")
        $todo = @($bp.lines | Where-Object { $_ -match '^\s*(PLAN|GATED)\s' })
        $gated = @($todo | Where-Object { $_ -match '^\s*GATED\s' })
        Write-Host ("  ②b VCGC→VDF 建庫計畫(乾跑)· 待建 " + $todo.Count + " 張(其中需網路而同意閘未開 " + $gated.Count + ")") -ForegroundColor $(if ($todo.Count -eq 0) { "Green" } else { "Yellow" })
        $bp.lines | Select-Object -Last 24 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
        $go = [bool]$BuildDb
        if ($todo.Count -gt 0 -and -not $BuildDb) {
            try {
                Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
                $msg = "VCGC 量到 " + $todo.Count + " 張正庫表缺或舊了。`n要 VCGC 轉交 VDF 建庫嗎?`n`n需網路的 " + $gated.Count + " 項:同意閘 VIA_NET_CONSENT 由你自己開;沒開會照實標 GATED、不會跑。"
                $ans = [System.Windows.Forms.MessageBox]::Show($msg, "VIA 操作台 · VDF 建庫", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
                $go = ($ans -eq [System.Windows.Forms.DialogResult]::Yes)
            } catch {
                Write-Host "     這個環境開不了 Windows 對話框;不建庫(要建請加 -BuildDb)" -ForegroundColor Yellow
            }
        }
        if ($go -and $todo.Count -gt 0) {
            if ($env:VIA_NET_CONSENT -ne "YES" -and $gated.Count -gt 0) {
                Write-Host ("     同意閘未開:需網路的 " + $gated.Count + " 項不會跑(要跑 = 你先 `$env:VIA_NET_CONSENT='YES' 再重跑;本台不代設)") -ForegroundColor Yellow
            }
            Write-Host "  ▶ ②b VCGC 轉交 VDF 建庫(build --apply;長的項要幾分鐘,別按 Ctrl+C)" -ForegroundColor DarkGray
            $ba = Invoke-OcPy $broker.FullName @("build", "--apply")
            Write-Host ("  ②b VDF 建庫 · rc=" + $ba.rc) -ForegroundColor $(if ($ba.rc -eq 0) { "Green" } else { "Yellow" })
            $ba.lines | Select-Object -Last 24 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
            if ($ba.rc -ne 0) { $exitCode = 2 }                  # GATED / ABSENT / NODATA / RED / TIMEOUT: tables still missing = step not done
        }
    }

    Set-OcLap "②/②b 輸入包 · VDF 建庫"
    # ③ 全景實測(ⓑ 沒變就沿用上一輪;-Full 一律重跑)
    $reuseFile = Join-Path $VIA "VIA_Reports\operator_console\SWEEP_REUSE_latest.json"
    $sweepRan = $false
    $sweepReused = $null
    if (-not $SkipSweep -and -not $Full -and (Test-Path -LiteralPath $reuseFile)) {
        try {
            $ru = Get-Content -LiteralPath $reuseFile -Raw -Encoding utf8 | ConvertFrom-Json
            $age = ([DateTime]::UtcNow - [DateTime]::Parse("" + $ru.sweep_at_utc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AdjustToUniversal)).TotalMinutes
            $why = @()
            if ($age -lt 0 -or $age -gt 720) { $why += ("上一輪 " + [int]$age + " 分鐘前(超過 12 小時)") }
            if (("" + $ru.data_mark) -ne (Get-OcDataMark $dat)) { $why += "資料家變了" }
            if (("" + $ru.tree_mark) -ne (Get-OcTreeMark)) { $why += "工作區有改動" }
            $null = git -C $Repo diff --quiet ("" + $ru.head) HEAD -- . ":(exclude)*VIA_EnvProvision_Ledger_v*.jsonl" 2>$null
            if ($LASTEXITCODE -ne 0) { $why += "HEAD 之間有紀錄冊以外的改動" }
            if ([int]$ru.sweep_rc -ne 0) { $why += ("上一輪全景實測沒全過(rc=" + $ru.sweep_rc + ";只沿用 rc 0)") }
            if (-not (Test-Path -LiteralPath (Join-Path $VIA "VIA_Reports\sweep\SWEEP_SIDE_latest.json"))) { $why += "上一輪側車不在" }
            if ($why.Count -eq 0) {
                $sweepReused = $ru
                Write-Host ("  ③ 全景實測 · 沿用上一輪(" + [int]$age + " 分鐘前 · rc=" + $ru.sweep_rc + " · 程式與資料家都沒變;要重跑加 -Full)") -ForegroundColor Green
            } else {
                Write-Host ("  ③ 全景實測 · 重跑(" + ($why -join " · ") + ")") -ForegroundColor DarkGray
            }
        } catch {
            Write-Host ("  ③ 全景實測 · 沿用紀錄讀不動,重跑:" + $_.Exception.Message) -ForegroundColor DarkGray
        }
    }
    if ($null -ne $sweepReused) {
        $src = [int]$sweepReused.sweep_rc
        if ($src -ne 0) { $exitCode = 2 }
    } elseif (-not $SkipSweep) {
        $sweep = Get-ChildItem -LiteralPath $VIA -Filter "Invoke-VIA-Sweep-v*.ps1" -File | Sort-Object Name | Select-Object -Last 1
        if ($null -eq $sweep) {
            Write-Host "  ③ 全景實測 · ABSENT(Invoke-VIA-Sweep 尾版不在)" -ForegroundColor Red
            $exitCode = 2
        } else {
            $sweepRan = $true
            $sweepAt = [DateTime]::UtcNow.ToString("o")
            Write-Host ("  ▶ ③ 全景實測 " + $sweep.Name + "(VDF / VRN 鏈 · 橋 · 全景 · DB 面板 · 工具)") -ForegroundColor DarkGray
            & $sweep.FullName -NoClipboard
            $src = $LASTEXITCODE
            Write-Host ("  ③ 全景實測 · rc=" + $src) -ForegroundColor $(if ($src -eq 0) { "Green" } else { "Yellow" })
            Set-Location -LiteralPath $VIA
            if ($src -eq 3) { $exitCode = 3; return }
            if ($src -ne 0) { $exitCode = 2 }
        }
    }
    Set-OcLap $(if ($null -ne $sweepReused) { "③ 全景實測(沿用)" } else { "③ 全景實測" })

    # ④ 輸出統一 Parquet(DuckDB 管家)
    $p = Invoke-OcPy $engine.FullName @("parquet", "--apply")
    Write-Host ("  ④ 輸出統一 Parquet · rc=" + $p.rc) -ForegroundColor $(if ($p.rc -eq 0) { "Green" } else { "Yellow" })
    $p.lines | Select-Object -Last 8 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
    if ($p.rc -eq 1) { $exitCode = 2 }
    Set-OcLap "④ Parquet"

    # ⑤ 操作台頁 + 總覽三色燈
    $pg = Invoke-OcPy $engine.FullName @("page")
    $st = Invoke-OcPy $engine.FullName @("status")
    Write-Host ("  ⑤ 操作台頁 · rc=" + $pg.rc) -ForegroundColor $(if ($pg.rc -eq 0) { "Green" } else { "Yellow" })
    if ($pg.rc -ne 0) {
        $exitCode = 2
        $pg.lines | Select-Object -Last 8 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
    }
    try {
        $rows = ($st.lines -join "`n") | ConvertFrom-Json
        $lampRows = @($rows | ForEach-Object { [pscustomobject]@{ id = $_.item; title = $_.item; state = @{ OK = "GREEN"; SKIP = "AMBER"; FAIL = "RED"; UNTESTED = "EMPTY" }[$_.lamp]; note = $_.text } })
        if (Get-Command Write-CeleritasMatrixSummary -ErrorAction SilentlyContinue) {
            Write-CeleritasMatrixSummary -Rows $lampRows -Title "VIA 操作台 · 總覽(三色燈)"
        } else {
            $lampRows | ForEach-Object { Write-Host ("  " + $_.state.PadRight(6) + " " + $_.title + " · " + $_.note) }
        }
    } catch {
        Write-Host "  [總覽] 讀不到 status 輸出(看頁)" -ForegroundColor Yellow
    }
    if ($null -ne $broker) {
        $bs = Invoke-OcPy $engine.FullName @("broker")
        Write-Host "  ⑥ VCGC 資料中介(VRN 要料 → 讀庫 / 轉交 VDF → 回 VRN)" -ForegroundColor Cyan
        $bs.lines | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
    }
    $sync = Join-Path $VIA "VIA_Reports\operator_console\ui\VIA-SYNCHRONIZER-Standalone.html"
    if (Test-Path -LiteralPath $sync) { Write-Host ("  [SYNCHRONIZER] " + $sync) -ForegroundColor Cyan }
    $page = Join-Path $VIA "VIA_Reports\operator_console\VIA_OperatorConsole_latest.html"
    Write-Host ("  [頁] " + $page) -ForegroundColor Cyan
    if ($pg.rc -ne 0) { Write-Host "  [頁] 本次沒產出新頁(上面是舊頁,不自動開)" -ForegroundColor Yellow }
    Set-OcLap "⑤ 操作台頁 · 資料中介"
    # ⓑ 記下本輪全景實測的指紋(只在真的跑了才記;沿用不延長壽命)
    if ($sweepRan) {
        $mark = [ordered]@{ schema = "VIA.SweepReuse.v1"; sweep_at_utc = $sweepAt; sweep_rc = $src; head = ("" + (git -C $Repo rev-parse HEAD 2>$null)).Trim()
                            tree_mark = (Get-OcTreeMark); data_mark = (Get-OcDataMark $dat); data_home = $dat; entry = (Split-Path $PSCommandPath -Leaf) }
        New-Item -ItemType Directory -Force -Path (Split-Path $reuseFile -Parent) | Out-Null
        ($mark | ConvertTo-Json) | Set-Content -LiteralPath $reuseFile -Encoding utf8
    }
    # 計時先寫一份(⑥ 驗證頁讀它);⑦ 之後再補完整版
    $timingFile = Join-Path $VIA "VIA_Reports\operator_console\TIMING_latest.json"
    $tj = { [ordered]@{ schema = "VIA.EntryTiming.v1"; entry = (Split-Path $PSCommandPath -Leaf); at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
                        total_sec = [Math]::Round($clock.Elapsed.TotalSeconds, 1); sweep_reused = ($null -ne $sweepReused); full = [bool]$Full; steps = $times } }
    ((& $tj) | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $timingFile -Encoding utf8
    # ⑥ 單一路徑交叉驗證(+ 布建完成紀錄一行)
    $verifyPage = Join-Path $VIA "VIA_Reports\path_verify\PATH_VERIFY_latest.html"
    if ($null -eq $pathv) {
        Write-Host "  ⑥ 單一路徑驗證 · ABSENT(CGC_MDL242 尾版不在)" -ForegroundColor Yellow
        $exitCode = 2
    } else {
        $pv = Invoke-OcPy $pathv.FullName @("run")
        $pv.lines | Where-Object { $_ -match '^\s*(GREEN|AMBER|RED|NODATA)\s' -or $_ -match '版本交叉|和上一輪比|\[單一路徑驗證\]' } | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
        Write-Host ("  ⑥ 單一路徑驗證 · rc=" + $pv.rc) -ForegroundColor $(if ($pv.rc -eq 0) { "Green" } elseif ($pv.rc -eq 1) { "Red" } else { "Yellow" })
        if ($pv.rc -eq 1) { $exitCode = 2 }
    }
    Set-OcLap "⑥ 單一路徑驗證"
    # ⑥b 教訓帳(CGC_MDL058 Lessons 尾版;只增):根因帳進流程
    $lessons = Get-ChildItem -LiteralPath $reg -Filter "CGC_MDL058_Lessons_v*.py" -File | Sort-Object Name | Select-Object -Last 1
    if ($null -ne $lessons) {
        $ls = Invoke-OcPy $lessons.FullName @()
        $rcN = @($ls.lines | Where-Object { $_ -match 'RC-\d+' }).Count
        Write-Host ("  ⑥b 教訓帳 · rc=" + $ls.rc + " · 根因帳 " + $rcN + " 行(手記:via-lessons --record 現象 --cause 根因 --fix 解法)") -ForegroundColor $(if ($ls.rc -eq 0) { "Green" } else { "Yellow" })
        $ls.lines | Where-Object { $_ -match '存錄|本輪全文' } | Select-Object -Last 2 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
    } else {
        Write-Host "  ⑥b 教訓帳 · ABSENT(CGC_MDL058 尾版不在)" -ForegroundColor Yellow
    }
    Set-OcLap "⑥b 教訓帳"

    # ⑦ 布建完成紀錄上傳:只 commit + push 紀錄冊這一本
    $ledger = Join-Path $reg "VIA_EnvProvision_Ledger_v0100.jsonl"
    if (-not $NoUpload -and (Test-Path -LiteralPath $ledger)) {
        $up = $true
        try {
            Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
            $ans = [System.Windows.Forms.MessageBox]::Show("把這一次的環境 / 工具布建完成紀錄上傳嗎?`n(git commit + push,只含 VIA_EnvProvision_Ledger 這一本;其他改動一個都不帶)",
                "VIA 唯一入口 · 布建紀錄上傳", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
            $up = ($ans -eq [System.Windows.Forms.DialogResult]::Yes)
        } catch {
            $up = $false
            Write-Host "     這個環境開不了 Windows 對話框;紀錄留在本機(要傳請重跑並按「是」)" -ForegroundColor Yellow
        }
        if ($up) {
            $rel = [System.IO.Path]::GetRelativePath($Repo, $ledger)
            $g1 = @(git -C $Repo add -- $rel 2>&1 | ForEach-Object { "" + $_ })
            $g2 = @(git -C $Repo commit -m ("VIA 布建完成紀錄 " + (Get-Date).ToString("yyyy-MM-dd HH:mm") + "(唯一入口 v0105)") -- $rel 2>&1 | ForEach-Object { "" + $_ })
            $g3 = @(git -C $Repo push 2>&1 | ForEach-Object { "" + $_ })
            $pushed = ($LASTEXITCODE -eq 0)
            Write-Host ("  ⑦ 布建紀錄上傳 · " + $(if ($pushed) { "已推上遠端(備份完成)" } else { "已在本機提交,推送沒成功:" + ($g3 | Select-Object -Last 1) })) -ForegroundColor $(if ($pushed) { "Green" } else { "Yellow" })
        } else {
            Write-Host "  ⑦ 布建紀錄上傳 · 未傳(紀錄留在本機紀錄冊)" -ForegroundColor Yellow
        }
    }

    Set-OcLap "⑦ 布建紀錄上傳"
    ((& $tj) | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $timingFile -Encoding utf8
    Write-Host ("  [計時] 全程 " + [Math]::Round($clock.Elapsed.TotalSeconds, 1) + " 秒" + $(if ($null -ne $sweepReused) { "(全景實測沿用上一輪;要重跑加 -Full)" } else { "" })) -ForegroundColor Cyan
    foreach ($k in $times.Keys) { Write-Host ("     " + ("" + $times[$k]).PadLeft(6) + "s  " + $k) -ForegroundColor DarkGray }
    # 結尾:只跳出簡單版驗證頁
    if (-not $NoOpen) {
        $u = if (Test-Path -LiteralPath $verifyPage) { $verifyPage } elseif ($pg.rc -eq 0) { $page } else { $null }
        if ($u) { try { Invoke-Item -LiteralPath $u } catch { Write-Host ("  [頁] 開不了瀏覽器(手動開 " + $u + ")") -ForegroundColor Yellow } }
    }
    Write-Host ("  [簡單版驗證頁] " + $verifyPage) -ForegroundColor Cyan
} finally {
    $env:VIA_DATA_HOME = $prevHome
    $env:VIA_GATE_PASSED_HEAD, $env:VIA_GATE_PASSED_AT, $env:VIA_GATE_PASSED_LINE = $prevGate
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }
    Set-Location -LiteralPath $StartDir
}
exit $exitCode
