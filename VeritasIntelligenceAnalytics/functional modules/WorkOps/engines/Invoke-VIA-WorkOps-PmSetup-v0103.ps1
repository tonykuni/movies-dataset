#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-WorkOps-PmSetup v0103 — v0102 + graphviz 免 winget 可攜式路徑
------------------------------------------------------------------------------------------
 v0103(操作員實機:winget 不存在):[5/6] 加認 engines\.graphviz 可攜版(dotsetup
   產物;user-scope 免管理員),缺席時首推 via-workops dotsetup install(動態抓官方
   最新 win64 ZIP + sha256 驗證),winget 降為替代方案。analytics 執行期自動接上
   可攜式 dot,免動系統 PATH、免重開終端。
 v0102(操作員指示:用 VIA_EnvManager.py 來試試能否成功安裝):
   安裝不再由本檔直呼 pip,而是經 VIA_ENG069_WorkopsEnvmanagerBridge.py 送入平台中央
   環境治理核心 VIA_EnvManager 的 gatekeeper:plan-install 決策(風險分級/目標環境
   /封鎖理由)→ 以其產生之命令執行(pip install + pip check)→ 決策與逐命令結果
   落 WorkOps\out\envmanager\ JSON。EnvManager 正本零改動(橋於執行期覆蓋治理範圍
   至 engines\.venv_pm)。容器 QA 實證:pm4py 經此路成功安裝+pip check 通過。
   後備:橋或 EnvManager 缺席/被封鎖時,退回 v0101 直裝路(誠實標注哪條路成功)。
 沿用 v0101:不試 numpy<2(過時釘選,pm4py 自帶相容 numpy);[VERIFY] 只印真實
   版本;graphviz 偵測。金律核心不變:pm4py 一族絕不入基底,隔離 venv 照舊。
 回退:刪本檔即回 v0102(graphviz 提示只剩 winget 句)。
==========================================================================================
#>
param([switch]$Recreate)
$ErrorActionPreference = "Continue"
$Here   = $PSScriptRoot
$Venv   = Join-Path $Here ".venv_pm"
$VPy    = Join-Path $Venv "Scripts\python.exe"
$Bridge = Join-Path $Here "VIA_ENG069_WorkopsEnvmanagerBridge.py"

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host "  WorkOps PmSetup v0103  |  VIA_EnvManager 中央治理安裝" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

if ($Recreate -and (Test-Path -LiteralPath $Venv)) {
    Write-Host "[0/6] -Recreate:移除舊 venv..." -ForegroundColor DarkYellow
    Remove-Item -LiteralPath $Venv -Recurse -Force
}
if (-not (Test-Path -LiteralPath $VPy)) {
    Write-Host "[1/6] 建立隔離環境 engines\.venv_pm ..." -ForegroundColor Yellow
    & py -m venv $Venv
    if (-not (Test-Path -LiteralPath $VPy)) { Write-Host "[FAIL] venv 建立失敗(py -m venv)— 停止,基底未被觸碰" -ForegroundColor Red; return }
} else {
    Write-Host "[1/6] venv 已在位(-Recreate 可重建)" -ForegroundColor Green
}

$HasBridge = Test-Path -LiteralPath $Bridge
if (-not $HasBridge) { Write-Host "[提示] 橋不在位($Bridge)— 全程走直裝後備" -ForegroundColor DarkYellow }

function Install-ViaGovernance {
    param([string]$Pkg, [string]$Ver, [switch]$WheelsOnly)
    $label = "$Pkg$Ver"
    if ($HasBridge) {
        $bArgs = @($Bridge, "install", $Pkg); if ($Ver) { $bArgs += $Ver }
        if ($WheelsOnly) { $bArgs += "--wheels-only" }
        & py @bArgs
        if ($LASTEXITCODE -eq 0) { return @{ ok = $true; via = "EnvManager" } }
        Write-Host ("  [後備] {0} 經 EnvManager 未成(exit {1})— 改直裝" -f $label, $LASTEXITCODE) -ForegroundColor DarkYellow
    }
    $pipArgs = @("-m", "pip", "install", "--disable-pip-version-check", "-q")
    if ($WheelsOnly) { $pipArgs += "--only-binary=:all:" }
    $pipArgs += $label
    & $VPy @pipArgs
    if ($LASTEXITCODE -eq 0) { return @{ ok = $true; via = "直裝後備" } }
    return @{ ok = $false; via = "皆未成" }
}

Write-Host "[2/6] 核心套件經 EnvManager gatekeeper(決策→執行,wheels-only)..." -ForegroundColor Yellow
$ok = @(); $fail = @()
foreach ($p in @(@("pandas", "<3"), @("scikit-learn", ""), @("pm4py", ""))) {
    $r = Install-ViaGovernance -Pkg $p[0] -Ver $p[1] -WheelsOnly
    $label = "$($p[0])$($p[1])"
    if ($r.ok) { $ok += $label; Write-Host ("  [OK  ] {0}({1})" -f $label, $r.via) -ForegroundColor Green }
    else { $fail += $label; Write-Host ("  [FAIL] {0}" -f $label) -ForegroundColor Red }
}
Write-Host "[3/6] jieba(純 Python 無 wheel,不限 binary)..." -ForegroundColor Yellow
$r = Install-ViaGovernance -Pkg "jieba" -Ver ""
if ($r.ok) { $ok += "jieba"; Write-Host ("  [OK  ] jieba({0})" -f $r.via) -ForegroundColor Green }
else { $fail += "jieba"; Write-Host "  [FAIL] jieba" -ForegroundColor Red }

Write-Host "[4/6] import 實測(只報真實版本,不做宣稱)..." -ForegroundColor Yellow
& $VPy -c "import numpy, pm4py; print('  [VERIFY] numpy', numpy.__version__, '· pm4py', pm4py.__version__, '· 於隔離 venv 共存實測通過(基底零觸碰)')"
if ($LASTEXITCODE -ne 0) { Write-Host "  [VERIFY-FAIL] pm4py import 未過 — analytics 將續用基底(無 pm4py 降級)" -ForegroundColor Red }

Write-Host "[5/6] graphviz 偵測(DFG 流程圖選配)..." -ForegroundColor Yellow
$dotPortable = Get-ChildItem -Path (Join-Path $Here ".graphviz") -Filter "dot.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
$dot = Get-Command dot -ErrorAction SilentlyContinue
if ($dotPortable) {
    Write-Host ("  [OK  ] 可攜式 dot 就位:{0} — analytics 自動接上,可輸出 DFG 圖" -f $dotPortable.FullName) -ForegroundColor Green
} elseif ($dot) {
    Write-Host ("  [OK  ] dot 在 PATH:{0} — analytics 可輸出 DFG 圖" -f $dot.Source) -ForegroundColor Green
} else {
    Write-Host "  [提示] 未偵測到 graphviz 的 dot — analytics 會誠實略過 DFG 圖(其餘照常)。" -ForegroundColor DarkYellow
    Write-Host "         首推(免 winget/管理員):via-workops dotsetup install(官方最新可攜版+sha256 驗證)" -ForegroundColor DarkYellow
    Write-Host "         替代:winget install Graphviz.Graphviz(若機上有 winget;裝後重開終端)" -ForegroundColor DarkYellow
}

Write-Host ("[總結] 成功 {0} / 失敗 {1} · 決策紀錄 out\envmanager\ · 基底零觸碰 · analytics/deep 自動優先此 venv" -f $ok.Count, $fail.Count) -ForegroundColor Green
if ($fail.Count) { Write-Host ("[誠實清單] 未成:{0}" -f ($fail -join ", ")) -ForegroundColor Yellow }

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
