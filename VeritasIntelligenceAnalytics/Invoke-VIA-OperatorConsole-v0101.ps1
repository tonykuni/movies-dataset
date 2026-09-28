# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-OperatorConsole-v0101.ps1 — VCGC 操作台一鍵(R25):選兩個資料夾 → VCGC→VDF 建庫 → 實測 → VCGC→VRN 經中介 → 開操作台
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
# 用法(站在倉根):.\VIA-OperatorConsole.ps1   參數:-Pick · -ApplyInput <json> · -SkipSweep · -NoOpen · -SystemDir <夾> · -DataDir <夾> · -BuildDb · -NoBuild
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
    [switch]$NoBuild
)

$VIA = $PSScriptRoot
$Repo = Split-Path $VIA -Parent
$StartDir = (Get-Location).Path
$prevHome = $env:VIA_DATA_HOME
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
    Write-Host "  ║  VIA 操作台 v0101 · 兩個資料夾 → VCGC→VDF 建庫 → VRN → 開頁  ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

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

    # ① VCGC 流程閘(PSGATE-1)
    $g = Invoke-OcPy $console.FullName @("status")
    $flow = @($g.lines | Where-Object { $_ -match '\[流程\]\s*政策過' } | Select-Object -First 1)
    if ($flow.Count -eq 0) {
        Write-Host "  [流程閘] 沒讀到「[流程] 政策過」→ 依 PSGATE-1 停在這裡" -ForegroundColor Red
        $exitCode = 3
        return
    }
    Write-Host ("  [流程閘] 過:" + $flow[0].Trim()) -ForegroundColor Green

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

    # ③ 全景實測
    if (-not $SkipSweep) {
        $sweep = Get-ChildItem -LiteralPath $VIA -Filter "Invoke-VIA-Sweep-v*.ps1" -File | Sort-Object Name | Select-Object -Last 1
        if ($null -eq $sweep) {
            Write-Host "  ③ 全景實測 · ABSENT(Invoke-VIA-Sweep 尾版不在)" -ForegroundColor Red
            $exitCode = 2
        } else {
            Write-Host ("  ▶ ③ 全景實測 " + $sweep.Name + "(VDF / VRN 鏈 · 橋 · 全景 · DB 面板 · 工具)") -ForegroundColor DarkGray
            & $sweep.FullName -NoClipboard
            $src = $LASTEXITCODE
            Write-Host ("  ③ 全景實測 · rc=" + $src) -ForegroundColor $(if ($src -eq 0) { "Green" } else { "Yellow" })
            Set-Location -LiteralPath $VIA
            if ($src -eq 3) { $exitCode = 3; return }
            if ($src -ne 0) { $exitCode = 2 }
        }
    }

    # ④ 輸出統一 Parquet(DuckDB 管家)
    $p = Invoke-OcPy $engine.FullName @("parquet", "--apply")
    Write-Host ("  ④ 輸出統一 Parquet · rc=" + $p.rc) -ForegroundColor $(if ($p.rc -eq 0) { "Green" } else { "Yellow" })
    $p.lines | Select-Object -Last 8 | ForEach-Object { Write-Host ("     " + $_) -ForegroundColor DarkGray }
    if ($p.rc -eq 1) { $exitCode = 2 }

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
    if (-not $NoOpen -and $pg.rc -eq 0 -and (Test-Path -LiteralPath $page)) { try { Invoke-Item -LiteralPath $page } catch { Write-Host "  [頁] 開不了瀏覽器(手動開上面的檔)" -ForegroundColor Yellow } }
} finally {
    $env:VIA_DATA_HOME = $prevHome
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }
    Set-Location -LiteralPath $StartDir
}
exit $exitCode
