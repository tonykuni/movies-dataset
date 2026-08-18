#requires -Version 7.0
# =============================================================================
# Invoke-VIA-Enter-v0101.ps1 — ONE POWERSHELL TO HANDLE ALL(TOOL-035)
# =============================================================================
# v0100→v0101(操作員令 2026-08-17):
#   ⑦ Git 自癒鏈 — 未完成合併(unmerged)自動處置:唯帳本檔衝突=呼
#      聯集助手(雙方零丟失)+續完合併;其他檔衝突=merge --abort 回
#      合併前態(已提交工作零損);分支非 main=自動切回(擋路則
#      AUTOSTASH 留名可還原);pull 後新衝突同規則遞迴一次
#   ⑧ Transcript 留痕(常備令①)— 全程 Start-Transcript;錯誤中斷
#      前紀錄必存 VIA_Reports\enter_runs\ENTER_TRANSCRIPT_<ts>.log
#   ⑨ 動態進度條+不卡斷(常備令②)— 階段加權 0→100% 單調遞增;
#      零 Read-Host;永不 exit 不關窗
# 其餘契約同 v0100(母根三層/VIA_PYTHON/動詞補位/同意閘只報不設)。
# 用法:& "$env:USERPROFILE\movies-dataset\VeritasIntelligenceAnalytics\supportive modules\registry\Invoke-VIA-Enter-v0101.ps1"
# =============================================================================
param([switch]$NoPull, [switch]$Deep)
$ErrorActionPreference = "Continue"
$TS = Get-Date -Format "yyyyMMdd_HHmmss"
$UserRoot = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
$RepoRoot = Join-Path $UserRoot "movies-dataset"
$VIA = Join-Path $RepoRoot "VeritasIntelligenceAnalytics"
$REG = Join-Path $VIA "supportive modules\registry"
$Script:Log = @()

function def_Say([string]$State, [string]$Msg) {
    $c = @{ OK = "Green"; FAIL = "Red"; HOLD = "Yellow"; INFO = "Cyan"; 候 = "Yellow" }[$State]
    Write-Host ("def [{0,-4}] {1}" -f $State, $Msg) -ForegroundColor $(if ($c) { $c } else { "Gray" })
    $Script:Log += @{ ts = (Get-Date -Format o); state = $State; msg = $Msg }
}
function def_Bar([int]$Pct, [string]$Stage) {
    $n = [math]::Round($Pct / 4)
    Write-Host ("def [{0,3}%] [{1}{2}] {3}" -f $Pct, ("█" * $n), ("░" * (25 - $n)), $Stage) -ForegroundColor DarkCyan
}

# ── ⑧ Transcript 留痕(常備令①:中斷前紀錄必存)─────────────────
$evDir = Join-Path $VIA "VIA_Reports\enter_runs"
$transDir = if (Test-Path $VIA) { New-Item -ItemType Directory -Force -Path $evDir | Out-Null; $evDir }
            else { [IO.Path]::GetTempPath() }
$transPath = Join-Path $transDir "ENTER_TRANSCRIPT_$TS.log"
try { Start-Transcript -LiteralPath $transPath -Append | Out-Null } catch { }

Write-Host "=== VIA ENTER · ONE POWERSHELL TO HANDLE ALL v0101 · $TS ===" -ForegroundColor Cyan
def_Say "INFO" "留痕:$transPath(錯誤中斷前紀錄必存——常備令①)"

def_Bar 5 "定位正典"
if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    def_Say "HOLD" "正典樹缺:$RepoRoot 非 git repo"
    try { Stop-Transcript | Out-Null } catch { }
    return
}
Set-Location $RepoRoot
def_Say "OK" "落位正典:$RepoRoot"

# ── ⑦ Git 自癒鏈 ────────────────────────────────────────────────
$RegistryRel = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_AutoCode_Registry_v0100.json"
function def_Unmerged { @(git -C $RepoRoot diff --name-only --diff-filter=U 2>$null) | Where-Object { $_ } }
function def_HealMerge([string]$Phase) {
    $um = def_Unmerged
    if ($um.Count -eq 0) { return $true }
    def_Say "INFO" "$Phase:未解衝突 $($um.Count) 檔:$($um -join ' · ')"
    if ($um.Count -eq 1 -and $um[0] -eq $RegistryRel) {
        $helper = Get-ChildItem $REG -Filter "CGC_MDL063_RegistryUnionmerge_v0*.py" | Sort-Object Name | Select-Object -Last 1
        if ($helper) {
            & $(if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python3" }) $helper.FullName
            if ((def_Unmerged).Count -eq 0) {
                git -C $RepoRoot commit --no-edit 2>&1 | Select-Object -Last 1 | ForEach-Object { def_Say "OK" "合併續完:$_" }
                return $true
            }
        }
        def_Say "HOLD" "聯集助手未能解——退 abort"
    }
    git -C $RepoRoot merge --abort 2>&1 | Out-Null
    if ((def_Unmerged).Count -eq 0) { def_Say "OK" "$Phase:已中止未完成合併(已提交工作零損,回合併前態)"; return $true }
    def_Say "HOLD" "$Phase:自癒未竟——輸出全在留痕檔,貼回裁決"
    return $false
}

def_Bar 20 "Git 自癒(合併態檢查)"
$gitdir = (git -C $RepoRoot rev-parse --git-dir 2>$null)
foreach ($bad in "rebase-merge", "rebase-apply", "CHERRY_PICK_HEAD") {
    if (Test-Path (Join-Path $gitdir $bad)) { def_Say "HOLD" "偵測 $bad 進行中(罕見態)——不自動動,貼回裁決" }
}
if (Test-Path (Join-Path $gitdir "MERGE_HEAD")) { [void](def_HealMerge "既存合併") }
else { def_Say "OK" "無未完成合併" }

def_Bar 35 "分支歸位 main"
$branch = (git -C $RepoRoot branch --show-current 2>$null)
if ($branch -ne "main") {
    def_Say "INFO" "當前分支:$($branch ?? '(detached)')——切回 main"
    $sw = git -C $RepoRoot switch main 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        $stashName = "VIA_ENTER_AUTOSTASH_$TS"
        git -C $RepoRoot stash push -m $stashName 2>&1 | Out-Null
        def_Say "INFO" "已修改檔擋路——AUTOSTASH:$stashName(git stash pop 可還原,零丟失)"
        $sw = git -C $RepoRoot switch main 2>&1 | Out-String
    }
    if ($LASTEXITCODE -eq 0) { def_Say "OK" "已在 main" } else { def_Say "HOLD" "切 main 未竟:$($sw.Trim())" }
} else { def_Say "OK" "已在 main" }

def_Bar 55 "git pull"
if ($NoPull) { def_Say "候" "pull 略過(-NoPull)" }
else {
    $pull = git -C $RepoRoot pull origin main 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        if ((def_Unmerged).Count -gt 0) { if (def_HealMerge "pull 後") { $pull = "自癒後完成" } }
        else { def_Say "FAIL" "pull rc=${LASTEXITCODE}:$(($pull -split "`n" | Where-Object { $_.Trim() } | Select-Object -Last 1))(誠實續行)" }
    }
    $tail = ($pull -split "`n" | Where-Object { $_.Trim() } | Select-Object -Last 1)
    def_Say "OK" "git pull:$($tail.Trim())"
}

def_Bar 70 "母根三層指標"
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
    if ($prevUser) { $m += "(舊值已入留痕)" }
    def_Say "OK" $m
} else { def_Say "OK" "指標已正典" }
if ($layers["Machine"].class -notin "UNSET", "CANONICAL") {
    def_Say "HOLD" "Machine 層指標非正典(唯讀不碰;User/Process 已優先生效)"
}

def_Bar 85 "VIA_PYTHON+動詞+同意閘"
$pyCmd = Get-Command py -ErrorAction SilentlyContinue
if (-not $pyCmd) { $pyCmd = Get-Command python -ErrorAction SilentlyContinue }
if ($pyCmd) {
    $env:VIA_PYTHON = $pyCmd.Path
    if ([Environment]::GetEnvironmentVariable("VIA_PYTHON", "User") -ne $pyCmd.Path) {
        [Environment]::SetEnvironmentVariable("VIA_PYTHON", $pyCmd.Path, "User")
    }
    def_Say "OK" "VIA_PYTHON = $($pyCmd.Path)"
} else { def_Say "FAIL" "py/python 不在 PATH——先跑 via-provision" }
$binDir = Join-Path $VIA "bin"
if (Get-Command via-six -ErrorAction SilentlyContinue) {
    def_Say "OK" "動詞可達:PATH 已含 bin($((Get-ChildItem $binDir -Filter '*.cmd' -ErrorAction SilentlyContinue).Count) 支)"
} else {
    $env:PATH = "$binDir;$env:PATH"
    def_Say "OK" "動詞補位:bin 已入本視窗 PATH"
}
def_Say "INFO" ("同意閘:本視窗={0} · User 層={1}(永不代設)" -f `
    $(if ($env:VIA_NET_CONSENT) { $env:VIA_NET_CONSENT } else { "未設" }), `
    $(if ([Environment]::GetEnvironmentVariable("VIA_NET_CONSENT", "User")) { [Environment]::GetEnvironmentVariable("VIA_NET_CONSENT", "User") } else { "未設" }))

def_Bar 100 "進場完成"
New-Item -ItemType Directory -Force -Path $evDir | Out-Null
@{ schema = "VIA.Enter.v2"; ts = $TS; repo = $RepoRoot; mother_root = $env:VIA_MOTHER_ROOT
   layers_before = $layers; prev_user_pointer = $prevUser; via_python = $env:VIA_PYTHON
   transcript = $transPath; log = $Script:Log
   policy = "git_selfheal·union_merge_registry·autostash_reversible·transcript_logs·no_full_tree_sha"
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evDir "ENTER_$TS.json") -Encoding utf8
$head = (git -C $RepoRoot log --oneline -1 2>$null | Out-String).Trim()
Write-Host "=== 進場完成 · HEAD:$head ===" -ForegroundColor Green
Write-Host "    母根:$env:VIA_MOTHER_ROOT · 留痕:$(Split-Path $transPath -Leaf)"
Write-Host "    次步:via-contract demo · via-run via-govroot · via-intake"
if ($Deep) {
    $gv = Get-ChildItem $REG -Filter "Invoke-VIA-Central-Governance-OneClick-v0*.ps1" | Sort-Object Name | Select-Object -Last 1
    if ($gv) { def_Say "INFO" "轉呼深度取證:$($gv.Name)"; & $gv.FullName }
}
try { Stop-Transcript | Out-Null } catch { }
