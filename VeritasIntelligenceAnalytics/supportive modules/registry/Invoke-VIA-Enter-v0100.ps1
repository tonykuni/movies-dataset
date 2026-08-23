#requires -Version 7.0
# =============================================================================
# Invoke-VIA-Enter-v0100.ps1 — 一支 PowerShell 統包「進入 via_core 環境」(TOOL-035)
# =============================================================================
# 操作員令(2026-08-17):ONE POWERSHELL TO HANDLE ALL·如何進入 via_core 環境。
# 契約:
#   ① 任意目錄可呼 — 自動定位正典 ~\movies-dataset,Set-Location 落位
#      (在呼叫者同一 runspace 執行,cwd/環境變數即時生效於當前視窗)
#   ② git pull 內建(git -C,不再吃「not a git repository」)
#   ③ 三層 VIA_MOTHER_ROOT 檢查(Process/User/Machine)+快速指標啟用:
#      秒級,不做全樹 SHA(舊樹 49,640 檔×23 檔/s≈35 分——那是深度取證,
#      走 via-govroot);User 層舊值先存證後改,Machine 層唯讀不碰
#   ④ VIA_PYTHON 解析+動詞可達性(bin 缺 PATH 則補 Process 層)
#   ⑤ 同意閘只報狀態永不代設(紅線);永不 exit 不關窗;誠實 OK/FAIL/HOLD
#   ⑥ 證據 JSON → VIA_Reports\enter_runs\(運行區)
# 用法:& "$env:USERPROFILE\movies-dataset\VeritasIntelligenceAnalytics\supportive modules\registry\Invoke-VIA-Enter-v0100.ps1"
#      參數:-NoPull 略過拉碼 · -Deep 進場後轉呼 via-govroot 深度取證
# =============================================================================
param([switch]$NoPull, [switch]$Deep)
$ErrorActionPreference = "Continue"
$TS = Get-Date -Format "yyyyMMdd_HHmmss"
$UserRoot = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }  # 非 Windows 後備(容器煙測)
$RepoRoot = Join-Path $UserRoot "movies-dataset"
$VIA = Join-Path $RepoRoot "VeritasIntelligenceAnalytics"
$Script:Log = @()

function def_Say([string]$State, [string]$Msg) {
    $c = @{ OK = "Green"; FAIL = "Red"; HOLD = "Yellow"; INFO = "Cyan"; 候 = "Yellow" }[$State]
    Write-Host ("def [{0,-4}] {1}" -f $State, $Msg) -ForegroundColor $(if ($c) { $c } else { "Gray" })
    $Script:Log += @{ ts = (Get-Date -Format o); state = $State; msg = $Msg }
}

Write-Host "=== VIA ENTER · 進入 via_core 環境 v0100 · $TS · 快速道(深度取證=via-govroot)===" -ForegroundColor Cyan

# ── ① 定位正典 ───────────────────────────────────────────────────
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    def_Say "HOLD" "正典樹缺:$RepoRoot 非 git repo——請確認 clone 位置(不在 Downloads 下)"
    return
}
if (-not (Test-Path $VIA)) {
    def_Say "HOLD" "VIA 母目錄缺:$VIA"
    return
}
Set-Location $RepoRoot
def_Say "OK" "落位正典:$RepoRoot(本視窗 cwd 已切換)"

# ── ② git pull ──────────────────────────────────────────────────
if ($NoPull) {
    def_Say "候" "git pull 略過(-NoPull)"
} else {
    $pull = git -C $RepoRoot pull 2>&1 | Out-String
    $tail = ($pull -split "`n" | Where-Object { $_.Trim() } | Select-Object -Last 1)
    if ($LASTEXITCODE -eq 0) { def_Say "OK" "git pull:$($tail.Trim())" }
    else { def_Say "FAIL" "git pull rc=${LASTEXITCODE} · $($tail.Trim())(誠實續行——環境進入不因網路斷)" }
}

# ── ③ 三層 VIA_MOTHER_ROOT + 快速指標啟用 ───────────────────────
$layers = @{}
foreach ($scope in "Process", "User", "Machine") {
    $v = [Environment]::GetEnvironmentVariable("VIA_MOTHER_ROOT", $scope)
    $cls = if ([string]::IsNullOrWhiteSpace($v)) { "UNSET" }
           elseif ($v -ieq $VIA) { "CANONICAL" }
           elseif ($v -like "*Downloads*") { "LEGACY/複本" }
           else { "UNKNOWN" }
    $layers[$scope] = @{ value = $v; class = $cls }
    def_Say "INFO" ("MOTHER_ROOT[{0,-7}] {1} · {2}" -f $scope, $cls, $(if ($v) { $v } else { "—" }))
}
$prevUser = $layers["User"].value
$env:VIA_MOTHER_ROOT = $VIA
if ($layers["User"].class -ne "CANONICAL") {
    [Environment]::SetEnvironmentVariable("VIA_MOTHER_ROOT", $VIA, "User")
    $m = "指標啟用:Process+User 層 → $VIA"
    if ($prevUser) { $m += "(舊值已入存證)" }
    def_Say "OK" $m
} else {
    def_Say "OK" "指標已正典:User 層無須變更;Process 層同步"
}
if ($layers["Machine"].class -notin "UNSET", "CANONICAL") {
    def_Say "HOLD" "Machine 層指標非正典(唯讀不碰,需管理員裁)——目前 User/Process 層已優先生效"
}

# ── ④ VIA_PYTHON + 動詞可達性 ───────────────────────────────────
$pyCmd = Get-Command py -ErrorAction SilentlyContinue
if (-not $pyCmd) { $pyCmd = Get-Command python -ErrorAction SilentlyContinue }
if ($pyCmd) {
    $env:VIA_PYTHON = $pyCmd.Path
    if ([Environment]::GetEnvironmentVariable("VIA_PYTHON", "User") -ne $pyCmd.Path) {
        [Environment]::SetEnvironmentVariable("VIA_PYTHON", $pyCmd.Path, "User")
    }
    def_Say "OK" "VIA_PYTHON = $($pyCmd.Path)"
} else {
    def_Say "FAIL" "py/python 不在 PATH——先跑 via-provision"
}
$binDir = Join-Path $VIA "bin"
if (Get-Command via-six -ErrorAction SilentlyContinue) {
    $n = (Get-ChildItem $binDir -Filter "*.cmd" -ErrorAction SilentlyContinue).Count
    def_Say "OK" "動詞可達:PATH 已含 bin(動詞 $n 支)"
} else {
    $env:PATH = "$binDir;$env:PATH"
    def_Say "OK" "動詞補位:bin 已加入本視窗 PATH(永久化走 via-provision,避免 setx 截斷風險)"
}

# ── ⑤ 同意閘狀態(只報不設——紅線)──────────────────────────────
$consent = $env:VIA_NET_CONSENT
$consentU = [Environment]::GetEnvironmentVariable("VIA_NET_CONSENT", "User")
def_Say "INFO" ("同意閘:本視窗={0} · User 層={1}(本器永不代設)" -f `
    $(if ($consent) { $consent } else { "未設" }), $(if ($consentU) { $consentU } else { "未設" }))

# ── ⑥ 證據 + 總結 ───────────────────────────────────────────────
$evDir = Join-Path $VIA "VIA_Reports\enter_runs"
New-Item -ItemType Directory -Force -Path $evDir | Out-Null
$evPath = Join-Path $evDir "ENTER_$TS.json"
@{ schema = "VIA.Enter.v1"; ts = $TS; repo = $RepoRoot; mother_root = $env:VIA_MOTHER_ROOT
   layers_before = $layers; prev_user_pointer = $prevUser; via_python = $env:VIA_PYTHON
   consent_process = $consent; consent_user = $consentU; log = $Script:Log
   policy = "fast_lane·no_full_tree_sha·machine_layer_readonly·consent_report_only"
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $evPath -Encoding utf8
$head = (git -C $RepoRoot log --oneline -1 2>$null | Out-String).Trim()
def_Say "OK" "存證:$(Split-Path $evPath -Leaf)"
Write-Host "=== 進場完成 · HEAD:$head ===" -ForegroundColor Green
Write-Host "    母根:$env:VIA_MOTHER_ROOT"
Write-Host "    深度取證(全樹 SHA,~35 分):via-govroot · 表格戰線:via-tables · 體檢:via-six"

if ($Deep) {
    $gv = Get-ChildItem (Join-Path $VIA "supportive modules\registry") -Filter "Invoke-VIA-Central-Governance-OneClick-v0*.ps1" |
          Sort-Object Name | Select-Object -Last 1
    if ($gv) { def_Say "INFO" "轉呼深度取證:$($gv.Name)"; & $gv.FullName }
    else { def_Say "FAIL" "治理一鍵器缺(先 git pull)" }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
