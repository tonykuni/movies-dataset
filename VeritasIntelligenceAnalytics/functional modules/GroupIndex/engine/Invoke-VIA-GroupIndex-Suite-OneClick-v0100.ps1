#requires -Version 7.0
<#
.SYNOPSIS
    VERITAS INTELLIGENCE ANALYTICS · GroupIndex Suite — ONE POWERSHELL TO HANDLE ALL (v0100)

.DESCRIPTION
    單一入口統包執行 GroupIndex 五引擎完整交付節奏(可從任意目錄以完整路徑執行):

      [S1] GIT-SYNC      還原本機再生的 evidence 差異 → fetch/checkout/pull 指定分支;
                         launcher 自身被更新時自動以新版重新執行一次
      [S2] HASH-AUDIT    引擎目錄 git 乾淨度 = 完整性驗證,並列印關鍵檔 SHA-256
      [S3] SMOKE-TOOLING M10 Chromium 煙霧測試工具檢查;缺 playwright-core 且 npm 可用時
                         安裝至 GroupIndex\smoke_tooling(僅此目錄,不污染全域)
      [0] ENV-PREFLIGHT  via_ 環境治理前哨(自動解析 via_core python + EnvManager 契約檢核)
      [1] COMPILE-GATE   Python 引擎 py_compile
      [1b] ACCEL20       中央治理主控台:20 加速器 × 全部 PY 引擎(AST/Hydra/SSOT/矩陣)
      [2] UNIT-TEST      pytest 六套件
      [3] SECTORFLOW     族群指數/資金流引擎(TEST→DEBUG→OPTIMIZE→BACK-TEST→CONSOLIDATE 收斂迴圈)
      [4] TRADE-BACKTEST 訊號交易層回測(T+1/成本/置換 null)
      [5] LIVEWIRE       接線合約轉接層(fail-closed/SSOT 對帳)
      [5b] ETF-CONSOLES  ETF 雙主控台收證(ActiveStockETF + GlobalETFFlow;
                         selftest + 本機 mock 整合測試,LiveData 邊界零外網)
      [5c] CHIPWAR-REV   籌碼戰四引擎(GovFund/SectorWhale/FinMind/Console 全循環)
                         + 月營收 twrevenue(selftest + demo 合成端到端)
      [6] DASHBOARD      ALL-IN-ONE 七分頁儀表板 + VAP 軸鎖合規
      [7] MASTER-VALIDATE套件級主驗證(UNIT→DEBUG→OPTIMIZE→INTEGRATE→SYSTEM→USER→ACTIVATE)
      [8] GATE-MATRIX    讀取各 run 總結,輸出最終矩陣;任一 Gate 未過即 fail-closed

    治理不變項:零網路、零下單、append-only、fail-closed、不可變 manifest。

.PARAMETER PythonExe     Python 直譯器(預設 python;自動優先解析 C:\Users\<u>\envs\via_* 管理環境)
.PARAMETER EnforceEnv    1=非 via_ 管理環境即 fail-closed(預設 1;沙盒/CI 可設 0 改報告模式)
.PARAMETER SyncRepo      1=執行 [S1] GIT-SYNC(預設 1;沙盒/離線設 0)
.PARAMETER ResetEvidence 1=同步前還原 evidence 子樹至 repo 版本(預設 1;本機再生檔屬暫態)
.PARAMETER SetupSmoke    1=允許 [S3] 於 smoke_tooling 安裝 playwright-core(預設 1)
.PARAMETER SkipEngines   只跑驗證(UNIT-TEST + MASTER-VALIDATE),不重跑引擎
.PARAMETER OpenHtml    完成後開啟儀表板(1=開啟)
.PARAMETER KeepOpen    結束後保留視窗等待 Enter

.EXAMPLE
    pwsh -ExecutionPolicy Bypass -File .\Invoke-VIA-GroupIndex-Suite-OneClick-v0100.ps1 -OpenHtml 1

.NOTES
    非阻塞模式(不關閉、不阻塞、不卡斷):改用同目錄 launch.ps1 背景派工,
    立即返回 PID 與 log 路徑,隨時 Get-Content -Wait 追蹤。
#>
[CmdletBinding()]
param(
    [string]$PythonExe = "python",
    [int]$EnforceEnv = 1,
    [int]$SyncRepo = 1,
    [int]$ResetEvidence = 1,
    [int]$SetupSmoke = 1,
    [int]$SkipEngines = 0,
    [int]$OpenHtml = 1,
    [int]$KeepOpen = 1
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$script:BoundParams = $PSBoundParameters   # 供 [S1] 自我更新後重新執行時轉發參數

$EngineDir = $PSScriptRoot
$ModuleDir = Split-Path $EngineDir -Parent
$EvidenceDir = Join-Path $ModuleDir "evidence"
$SmokeDir = Join-Path $ModuleDir "smoke_tooling"
$RepoRoot = Split-Path (Split-Path (Split-Path $ModuleDir -Parent) -Parent) -Parent
$Branch = "claude/via-group-classification-index-5h274b"
$DashboardHtml = Join-Path (Split-Path (Split-Path $ModuleDir -Parent) -Parent) "VIA_Reports\VIA_SectorFlow_AllInOne_Dashboard_v0100.html"

$Engines = @(
    "VIA_GroupIndex_EnvPreflight_v0100.py",
    "VIA_SectorFlow_AdaptiveChainedIndex_v0100.py",
    "VIA_SectorFlow_SignalTradeBacktest_v0100.py",
    "VIA_LiveWire_ContractAdapter_v0100.py",
    "VIA_SectorFlow_Dashboard_Builder_v0100.py",
    "VIA_GroupIndex_MasterValidation_v0100.py",
    "VIA_ActiveStockETF.py",
    "VIA_ActiveStockETF_mocktest.py",
    "VIA_GlobalETFFlow.py",
    "VIA_ETF_Consoles_Evidence_v0100.py",
    "VIA_FinMind_Ingest_v010.py",
    "VIA_SectorWhaleEngine_v020.py",
    "..\..\ChipWar\engines\VIA_GovFundEngine_v040.py",   # canonical 於 ChipWar 子系統(去重後不留副本)
    "VIA_ChipWar_Console_v010.py",
    "VIA_ChipWar_Revenue_Evidence_v0100.py",
    "VIA_GroupIndex_Accel20_Console_v0100.py"
)
$TestFiles = @(
    "test_VIA_GroupIndex_EnvPreflight_v0100.py",
    "test_VIA_SectorFlow_AdaptiveChainedIndex_v0100.py",
    "test_VIA_SectorFlow_SignalTradeBacktest_v0100.py",
    "test_VIA_SectorFlow_Dashboard_Builder_v0100.py",
    "test_VIA_LiveWire_ContractAdapter_v0100.py",
    "test_VIA_VAP_AxisLock_v0100.py",
    "test_VIA_ETF_Consoles_v0100.py",
    "test_VIA_ChipWar_Revenue_v0100.py",
    "test_VIA_GroupIndex_Accel20_v0100.py"
)

function def_ResolveViaPython {
    # via_ 管理環境自動解析(候選順序沿用 Invoke-VeritasNexusCore.ps1 契約)
    param([string]$Requested)
    if ($Requested -ne "python") { return $Requested }   # 使用者顯式指定 → 尊重不覆寫
    $candidates = @(
        (Join-Path $env:USERPROFILE "envs\via_groupindex_312\Scripts\python.exe"),
        (Join-Path $env:USERPROFILE "envs\via_core_313\Scripts\python.exe"),
        (Join-Path $env:USERPROFILE "envs\via_core_312\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $Requested
}

function def_SyncRepo {
    # [S1] GIT-SYNC:evidence 還原 → fetch/checkout/pull;launcher 自身更新時以新版重新執行
    if ($SyncRepo -ne 1) {
        def_WriteStep -Percent 1 -Message "GIT-SYNC(SyncRepo=0 → 沿用本地檔案)" -Status "SKIP"
        return
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue) -or -not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
        def_WriteStep -Percent 1 -Message "GIT-SYNC 不可用(git 或 .git 不存在)→ 沿用本地檔案" -Status "WARN"
        return
    }
    $selfBefore = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    $evidenceRel = "VeritasIntelligenceAnalytics/functional modules/GroupIndex/evidence"
    if ($ResetEvidence -eq 1) {
        git -C $RepoRoot restore --source=HEAD --worktree -- $evidenceRel
        def_WriteStep -Percent 1 -Message "evidence 子樹已還原至 repo 版本(本機再生檔屬暫態)" -Status "PASS"
    }
    git -C $RepoRoot fetch origin $Branch
    if ($LASTEXITCODE -ne 0) {
        def_WriteStep -Percent 1 -Message "GIT-SYNC fetch 失敗(離線?)→ 沿用本地檔案" -Status "WARN"
        return
    }
    git -C $RepoRoot checkout $Branch
    git -C $RepoRoot pull origin $Branch
    def_WriteStep -Percent 1 -Message "GIT-SYNC 分支 $Branch 已同步" -Status "PASS"
    $selfAfter = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    if ($selfAfter -ne $selfBefore -and $env:VIA_ONECLICK_RESYNCED -ne "1") {
        Write-Host "def launcher 已被同步更新 → 以新版重新執行一次" -ForegroundColor Yellow
        $env:VIA_ONECLICK_RESYNCED = "1"
        $fwd = @("-ExecutionPolicy", "Bypass", "-File", $PSCommandPath, "-SyncRepo", "0")
        foreach ($k in @($script:BoundParams.Keys)) {
            if ($k -ne "SyncRepo") { $fwd += @("-$k", [string]$script:BoundParams[$k]) }
        }
        & pwsh @fwd
        $script:KeepOpen = 0
        exit $LASTEXITCODE
    }
}

function def_HashAudit {
    # [S2] HASH-AUDIT:git 乾淨度即完整性;列印關鍵檔 SHA-256 供人工核對
    def_WriteStep -Percent 2 -Message "HASH-AUDIT 引擎目錄完整性"
    foreach ($f in @(
            "Invoke-VIA-GroupIndex-Suite-OneClick-v0100.ps1",
            "VIA_GroupIndex_EnvPreflight_v0100.py",
            "VIA_GroupIndex_MasterValidation_v0100.py")) {
        $h = (Get-FileHash -LiteralPath (Join-Path $EngineDir $f) -Algorithm SHA256).Hash
        Write-Host ("def   SHA256 {0}…  {1}" -f $h.Substring(0, 16), $f)
    }
    $dirty = @()
    if ((Get-Command git -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
        $dirty = @(git -C $RepoRoot status --porcelain -- "VeritasIntelligenceAnalytics/functional modules/GroupIndex/engine")
    }
    if ($dirty.Count -eq 0) {
        def_WriteStep -Percent 2 -Message "HASH-AUDIT engine 目錄與 repo HEAD 一致" -Status "PASS"
    }
    else {
        def_WriteStep -Percent 2 -Message "HASH-AUDIT engine 目錄有本地修改 x$($dirty.Count)(雜湊以本地為準)" -Status "WARN"
    }
}

function def_SmokeTooling {
    # [S3] SMOKE-TOOLING:M10 Chromium 煙霧測試依賴;只裝進 smoke_tooling,不污染全域
    $pwCore = Join-Path (Join-Path $SmokeDir "node_modules") "playwright-core"
    if (Test-Path -LiteralPath $pwCore) {
        def_WriteStep -Percent 3 -Message "SMOKE-TOOLING playwright-core 就緒 → M10 以系統 Edge/Chrome 執行" -Status "PASS"
        return
    }
    if ($SetupSmoke -ne 1) {
        def_WriteStep -Percent 3 -Message "SMOKE-TOOLING(SetupSmoke=0)→ M10 依賴缺席時降級 REVIEW" -Status "SKIP"
        return
    }
    if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command npm -ErrorAction SilentlyContinue)) {
        def_WriteStep -Percent 3 -Message "SMOKE-TOOLING 缺 Node.js/npm → M10 降級 REVIEW(winget install OpenJS.NodeJS.LTS 後重跑可補)" -Status "WARN"
        return
    }
    New-Item -ItemType Directory -Force -Path $SmokeDir | Out-Null
    Push-Location $SmokeDir
    try { npm install playwright-core --no-fund --no-audit --loglevel=error }
    finally { Pop-Location }
    if (Test-Path -LiteralPath $pwCore) {
        def_WriteStep -Percent 3 -Message "SMOKE-TOOLING playwright-core 安裝完成(smoke_tooling 專用目錄)" -Status "PASS"
    }
    else {
        def_WriteStep -Percent 3 -Message "SMOKE-TOOLING 安裝失敗 → M10 降級 REVIEW" -Status "WARN"
    }
}

function def_WriteBanner {
    param([string]$Title)
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
}

function def_WriteStep {
    param([int]$Percent, [string]$Message, [string]$Status = "RUN ")
    $filled = [Math]::Max(0, [Math]::Min(20, [Math]::Floor($Percent / 5)))
    $bar = ("█" * $filled) + ("░" * (20 - $filled))
    Write-Host ("def [{0,3}%] [{1}] [{2}] {3}" -f $Percent, $bar, $Status, $Message)
}

function def_InvokePython {
    param([string]$Label, [string[]]$Arguments, [int]$Percent)
    def_WriteStep -Percent $Percent -Message $Label
    & $PythonExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
    def_WriteStep -Percent $Percent -Message $Label -Status "PASS"
}

function def_ReadJson {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Summary not found: $Path" }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function def_Main {
    def_WriteBanner "VERITAS INTELLIGENCE ANALYTICS · GROUPINDEX SUITE · ONE POWERSHELL TO HANDLE ALL · v0100"
    # [S1]-[S3] 前置統包:同步 → 完整性 → 煙霧工具
    def_SyncRepo
    def_HashAudit
    def_SmokeTooling
    $script:PythonExe = def_ResolveViaPython -Requested $PythonExe
    Write-Host "def Python : $PythonExe" -ForegroundColor White
    Push-Location $EngineDir
    try {
        # [0] ENV-PREFLIGHT — via_ 環境治理前哨(VIA_EnvManager 契約;EnforceEnv=1 時 fail-closed)
        $preflightArgs = @("VIA_GroupIndex_EnvPreflight_v0100.py")
        if ($EnforceEnv -eq 1) { $preflightArgs += "--enforce" }
        def_InvokePython -Label "ENV-PREFLIGHT (via_ governance · EnvManager contract)" -Percent 3 -Arguments $preflightArgs

        # [1] COMPILE-GATE
        foreach ($engine in $Engines) {
            if (-not (Test-Path -LiteralPath (Join-Path $EngineDir $engine))) { throw "Engine missing: $engine" }
        }
        def_InvokePython -Label "COMPILE-GATE (py_compile x$($Engines.Count))" -Percent 6 -Arguments (@("-m", "py_compile") + $Engines)

        # [1b] ACCEL20 — 20 加速器全引擎治理掃描(分析-建議,零改寫)
        def_InvokePython -Label "ACCEL20 governance console (20 accelerators x all py engines)" -Percent 10 -Arguments @("VIA_GroupIndex_Accel20_Console_v0100.py")

        # [2] UNIT-TEST
        def_InvokePython -Label "UNIT-TEST (pytest x$($TestFiles.Count))" -Percent 15 -Arguments (@("-m", "pytest", "-q", "-W", "error::RuntimeWarning") + $TestFiles)

        if ($SkipEngines -ne 1) {
            # [3] SECTORFLOW
            def_InvokePython -Label "SECTORFLOW engine (index + flows + 4-scenario backtest)" -Percent 32 -Arguments @("VIA_SectorFlow_AdaptiveChainedIndex_v0100.py")
            # [4] TRADE-BACKTEST
            def_InvokePython -Label "TRADE-BACKTEST engine (T+1 + costs + permutation null)" -Percent 52 -Arguments @("VIA_SectorFlow_SignalTradeBacktest_v0100.py")
            # [5] LIVEWIRE
            def_InvokePython -Label "LIVEWIRE contract adapter (fail-closed + SSOT reconcile)" -Percent 64 -Arguments @("VIA_LiveWire_ContractAdapter_v0100.py")
            # [5b] ETF-CONSOLES(selftest + 本機 mock 整合;約 6-8 分鐘)
            def_InvokePython -Label "ETF-CONSOLES evidence (ActiveStockETF + GlobalETFFlow, 142 checks)" -Percent 70 -Arguments @("VIA_ETF_Consoles_Evidence_v0100.py")
            # [5c] CHIPWAR + REVENUE(四引擎全循環 + 月營收 selftest/demo)
            def_InvokePython -Label "CHIPWAR-REVENUE evidence (GovFund/SectorWhale/FinMind/Console + twrevenue)" -Percent 72 -Arguments @("VIA_ChipWar_Revenue_Evidence_v0100.py")
            # [6] DASHBOARD
            def_InvokePython -Label "DASHBOARD builder (7 tabs + VAP axis lock)" -Percent 74 -Arguments @("VIA_SectorFlow_Dashboard_Builder_v0100.py")
        }
        else {
            def_WriteStep -Percent 60 -Message "SkipEngines=1 → 只跑驗證(引擎 evidence 沿用現存)" -Status "SKIP"
        }

        # [7] MASTER-VALIDATE
        def_InvokePython -Label "MASTER-VALIDATE (UNIT→DEBUG→OPTIMIZE→INTEGRATE→SYSTEM→USER→ACTIVATE)" -Percent 88 -Arguments @("VIA_GroupIndex_MasterValidation_v0100.py")

        # [8] GATE-MATRIX
        def_WriteStep -Percent 95 -Message "GATE-MATRIX 讀取各 run 總結"
        $gateRows = @(
            @{ Name = "SectorFlow";  Json = Join-Path $EvidenceDir "RUN_SECTORFLOW_V0100\run_summary.json";                Field = "FinalGate";  Expect = "CONTROLLED_ACTIVATION_PASS" },
            @{ Name = "TradeBT";     Json = Join-Path $EvidenceDir "RUN_SECTORFLOW_TRADE_V0100\trade_run_summary.json";    Field = "Status";     Expect = "TRADE_BACKTEST_PASS" },
            @{ Name = "LiveWire";    Json = Join-Path $EvidenceDir "RUN_LIVEWIRE_ADAPTER_V0100\adapter_run_summary.json";  Field = "Status";     Expect = "ADAPTER_VERIFIED_FAIL_CLOSED" },
            @{ Name = "ETFConsoles"; Json = Join-Path $EvidenceDir "RUN_ETF_CONSOLES_V0100\etf_consoles_summary.json";     Field = "Status";     Expect = "ETF_CONSOLES_PASS" },
            @{ Name = "ChipWarRev";  Json = Join-Path $EvidenceDir "RUN_CHIPWAR_REVENUE_V0100\chipwar_revenue_summary.json"; Field = "Status";     Expect = "CHIPWAR_REVENUE_PASS" },
            @{ Name = "Accel20";     Json = Join-Path $EvidenceDir "RUN_ACCEL20_V0100\accel20_summary.json";               Field = "Status";     Expect = "ACCEL20_GOVERNANCE_PASS" },
            @{ Name = "MasterSuite"; Json = Join-Path $EvidenceDir "RUN_MASTER_VALIDATION_V0100\master_run_summary.json";  Field = "Status";     Expect = "CONTROLLED_SUITE_ACTIVATION_PASS" }
        )
        $blocked = @()
        Write-Host ""
        Write-Host ("{0,-14} {1,-46} {2}" -f "ENGINE", "GATE", "VERDICT") -ForegroundColor White
        foreach ($row in $gateRows) {
            $summary = def_ReadJson -Path $row.Json
            $value = [string]$summary.($row.Field)
            $ok = $value.StartsWith($row.Expect)
            $verdict = if ($ok) { "PASS" } else { "BLOCKED" }
            $color = if ($ok) { "Green" } else { "Red" }
            Write-Host ("{0,-14} {1,-46} {2}" -f $row.Name, $value, $verdict) -ForegroundColor $color
            if (-not $ok) { $blocked += $row.Name }
        }
        if ($blocked.Count -gt 0) {
            throw ("Gate blocked: " + ($blocked -join ", "))
        }

        Write-Host ""
        Write-Host "def Dashboard : $DashboardHtml" -ForegroundColor White
        Write-Host "def Evidence  : $EvidenceDir" -ForegroundColor White
        if ($OpenHtml -eq 1 -and (Test-Path -LiteralPath $DashboardHtml)) {
            Start-Process -FilePath $DashboardHtml
        }
        def_WriteStep -Percent 100 -Message "ALL GOVERNED PHASES COMPLETED — SUITE GREEN" -Status "PASS"
    }
    finally {
        Pop-Location
    }
}

try {
    def_Main
    $exitCode = 0
}
catch {
    Write-Host "def FAIL : $($_.Exception.Message)" -ForegroundColor Red
    $exitCode = 1
}
finally {
    if ($KeepOpen -eq 1) {
        Write-Host "def PowerShell remains open. Press Enter to finish." -ForegroundColor Yellow
        [void](Read-Host)
    }
}
exit $exitCode
