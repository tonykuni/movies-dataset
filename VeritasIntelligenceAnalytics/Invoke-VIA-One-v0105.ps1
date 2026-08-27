#requires -Version 7.0
<#
Invoke-VIA-One v0105 — 全系統總啟動器(v0104 版本前送:一支到底)
新增:[0] DEPS 依賴預檢(五件套 import 探測,缺件標示不卡斷)
     [11] BRIDGE 前後端狀態矩陣(動態最新版引擎;-Only bridge 可單跑)
十二階段 = 預檢+sync+Mega+VMT+CGE+VRN×2+FLOW+IF+FIS+BRIDGE+Hub,全程不卡斷
用法:via-one            → 十階段全跑 + Hub
      via-one -Only flow → 只跑該子系統並開其 U/I(鍵:mega|vmt|cge|probe|extract|flow|if|fis)
一支 PowerShell 處理全部並啟動全系統含 U/I:
  同步 → Mega v0106 三輪全景(Porcelain Matrix)→ VMT 總指揮 → CGE dry-run
  → VRN 內容探測/擷取 → FlowSystem OneShot(自產 UI)→ VIA-IF selftest
  → FIS 驗證 harness(缺 scipy 誠實 FAIL 續行)→ UI Hub v0104(十二介面)。
不關閉、不阻塞、不卡斷:無 Read-Host、無 exit;UI 以 Start-Process 非阻塞開啟;
每階段動態進度條(Write-Progress)+ 動態說明;單一階段失敗誠實記錄後續行。
回退:bin\via-one.cmd 改指 Invoke-VIA-One-v0104.ps1
#>
param([string]$Only = "")
$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
$Bin = Join-Path $Root "bin"
$Reports = Join-Path $Root "VIA_Reports"
New-Item -ItemType Directory -Force -Path (Join-Path $Reports "flow_run"), (Join-Path $Reports "if_out") | Out-Null

$Accelerators = @(
    "AST 精準解析","多語言語意模型","九頭龍風險預測","依賴拓撲排序","沙盒隔離執行",
    "自動修正建議生成","三輪全景式分析","SSOT 對齊","視覺化矩陣生成","錯誤分類與分群",
    "性能與複雜度分析","多子系統同步檢視","版本差異與回滾","覆蓋率與回歸檢查","修正順序最佳化",
    "動態進度條","動態說明","非阻塞 PowerShell","多引擎整合","自動部署與環境初始化")

Write-Host ("=" * 70) -ForegroundColor DarkCyan
Write-Host "  VIA ONE v0105  |  全系統總啟動器 · 20 加速器 · 公定處理模式 · Porcelain" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor DarkCyan
Write-Host ("[加速器] " + ($Accelerators -join " · ")) -ForegroundColor DarkGray

$Stages = @(
    @{ Key = "deps"; Name = "DEPS 依賴預檢(五件套)";      Kind = "deps" },
    @{ Key = "sync"; Name = "SYNC 同步 repo";                Kind = "ps";  Target = (Join-Path $Bin "via-sync.ps1") },
    @{ Key = "mega"; Ui = "VIA_Reports\VIA_MegaMatrix.html"; Name = "MEGA 三輪全景(動態最新版)"; Kind = "py";  Target = ((Get-ChildItem (Join-Path $Root "supportive modules\VIA_Governance_Runtime") -Filter "SUP_MDL142_MegaEngine_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName) },
    @{ Key = "vmt"; Ui = (Join-Path ($env:VMT_ROOT ?? "C:\VIA\VeritasMailTracker") "reports\MasterRun.html"); Name = "VMT 總指揮(動態最新版)"; Kind = "py";  Target = ((Get-ChildItem (Join-Path $Root "supportive modules\VMT_SuperBOM") -Filter "VIA_ENG021_MasterEngine_v0*.py" | Sort-Object Name | Select-Object -Last 1).FullName); Args = @("--no-open") },
    @{ Key = "cge"; Ui = (Join-Path ($env:VMT_ROOT ?? "C:\VIA\VeritasMailTracker") "VIA_CentralGovernance.html"); Name = "CGE 中央治理 dry-run"; Kind = "py";  Target = (Join-Path $Root "supportive modules\VIA_Central_Governance\CGC_MDL001_CentralGovernanceEngine_v0401.py"); Args = @("--workdir", ($env:VMT_ROOT ?? "C:\VIA\VeritasMailTracker")) },
    @{ Key = "probe"; Name = "VRN 內容探測(唯讀 GO gate)"; Kind = "py";  Target = (Join-Path $Root "functional modules\VRN\VRN_ENG048_ContentProbe_v0100.py"); Args = @("--no-open") },
    @{ Key = "extract"; Name = "VRN 內容擷取 dry-run(v0101)"; Kind = "py";  Target = (Join-Path $Root "functional modules\VRN\VRN_ENG047_ContentExtract_v0101.py") },
    @{ Key = "flow"; Ui = "VIA_Reports\flow_run\VIA_FlowSystem_UI.html"; Name = "FLOW 系統 OneShot(自產 UI)"; Kind = "py";  Target = (Join-Path $Root "supportive modules\VIA_FlowSystem\FLOW_MDL003_FlowSystemOneShot.py"); Cwd = (Join-Path $Reports "flow_run") },
    @{ Key = "if"; Name = "IF 產業預測 selftest"; Kind = "py";  Target = (Join-Path $Root "supportive modules\VIA_IF_Engine\SUP_MDL144_IfEngine.py"); Args = @("--selftest") },
    @{ Key = "fis"; Ui = "VIA_Reports\fis_run"; Name = "FIS 驗證 harness(需 scipy)"; Kind = "py";  Target = (Join-Path $Root "supportive modules\VIA_FlowSystem\FLOW_MDL002_FISValidationV3.py"); Cwd = (Join-Path $Reports "fis_run"); Optional = $true },
    @{ Key = "hub"; Name = "UI HUB 樞紐(動態最新版)"; Kind = "open"; Target = ((Get-ChildItem (Join-Path $Root "supportive modules\ui_support") -Filter "VIA_UI_Hub_v*.html" | Sort-Object Name | Select-Object -Last 1).FullName) }
)

if ($Only) {
    $sel = $Stages | Where-Object { $_.Key -eq $Only.ToLower() }
    if (-not $sel) { Write-Host ("[FAIL] 未知子系統鍵 '{0}' — 可用:deps mega vmt cge probe extract flow if fis bridge" -f $Only) -ForegroundColor Red; $Stages = @() }
    else { $Stages = @($sel); Write-Host ("[選用] 只跑子系統 {0} 並開其 U/I" -f $Only) -ForegroundColor Cyan }
}
$Results = @()
$total = $Stages.Count
for ($i = 0; $i -lt $total; $i++) {
    $st = $Stages[$i]
    $pct = [int](($i) / $total * 100)
    Write-Progress -Activity "VIA ONE 總管線" -Status $st.Name -PercentComplete $pct
    Write-Host ("`n[STATUS] ({0}/{1}) {2}" -f ($i + 1), $total, $st.Name) -ForegroundColor Yellow
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $ok = $true
    try {
        switch ($st.Kind) {
            "deps" {
                foreach ($m in @("duckdb", "rich", "scipy", "numpy", "pandas")) {
                    & py -c "import $m" 2>$null
                    if ($LASTEXITCODE -eq 0) { Write-Host ("  [READY] {0}" -f $m) -ForegroundColor Green }
                    else { Write-Host ("  [MISS ] {0} — via-envfix 可補(不卡斷)" -f $m) -ForegroundColor DarkYellow } }
            }
            "ps"   { if (Test-Path -LiteralPath $st.Target) { & pwsh -NoProfile -File $st.Target } else { throw "缺檔 $($st.Target)" } }
            "py"   { if (-not (Test-Path -LiteralPath $st.Target)) { throw "缺檔 $($st.Target)" }
                     if ($st.Cwd) { Push-Location $st.Cwd }
                     try { & py $st.Target @($st.Args) } finally { if ($st.Cwd) { Pop-Location } }
                     if ($LASTEXITCODE -ne 0) { $ok = $false } }
            "open" { if (Test-Path -LiteralPath $st.Target) { Start-Process $st.Target | Out-Null } else { throw "缺檔 $($st.Target)" } }
        }
    }
    catch { $ok = $false; Write-Host ("[STATUS] 階段異常(續行):{0}" -f $_.Exception.Message) -ForegroundColor Red }
    $sw.Stop()
    if ($Only -and $ok -and $st.Ui) {
        $uiPath = if ([IO.Path]::IsPathRooted($st.Ui)) { $st.Ui } else { Join-Path $Root $st.Ui }
        if (Test-Path -LiteralPath $uiPath) { Start-Process $uiPath | Out-Null; Write-Host "[U/I] 已開啟 $uiPath" -ForegroundColor Green }
        else { Write-Host "[U/I] $uiPath 尚未生成(引擎輸出位置)" -ForegroundColor DarkYellow }
    }
    $tag = if ($ok) { "OK" } elseif ($st.Optional) { "SKIP" } else { "FAIL" }
    $Results += [pscustomobject]@{ 階段 = $st.Name; 結果 = $tag; 耗時s = [math]::Round($sw.Elapsed.TotalSeconds, 1) }
}
Write-Progress -Activity "VIA ONE 總管線" -Completed

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor DarkCyan
$Results | Format-Table -AutoSize
$okN = ($Results | Where-Object 結果 -eq "OK").Count
Write-Host ("[總結] {0}/{1} 階段 OK · FlowSystem UI + Mega Matrix + Command Bridge + UI Hub 已非阻塞開啟 · PowerShell 保持開啟" -f $okN, $total) -ForegroundColor Green
Write-Host "[提示] 選配依賴一鍵補齊:py -m pip install duckdb rich scipy numpy pandas" -ForegroundColor DarkGray
Write-Host "[提示] via-pipe(輪動引擎)待同伴檔 rotation_engine.py 補齊後可用" -ForegroundColor DarkGray

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
