# =====================================================================
# Invoke-VIA-All-v0101.ps1 — 唯一總門(批260 立;批262 零彈窗;操作員令「one powershell
# to handle all·再一次不卡斷」)
# =====================================================================
# 卡斷根因清單(本檔全滅):
#   ①VIA.ps1 尾端 Read-Host「按 Enter 關閉」=前景卡斷→本檔零 Read-Host
#     零 pause;VIA.ps1 改「分離進程」啟動=它的提示只卡它自己的隱窗
#   ②多行貼令(pull+點源+via 三段)→本檔一檔統包;首跑後=桌面捷徑
#     「VIA-ALL」雙擊或短指令 via-all
#   ③短指令屢不識→本檔自己先點源(當場生效)+profile 尾版 glob 行
# 統包序(全非阻塞;子進程分離=關窗不斷):
#   1 同步自癒(再生頁還原+上游矯正+stash 留痕+pull --ff-only 重試)
#   2 點源短指令(本窗立即可用+profile 自註冊)
#   3 收容器(Downloads 名冊;有新件自動收+推)→分離背景
#   4 VIA 全自動(日更鏈+回補+指揮台橋)→分離背景
#   5 PS 修復 dry-run →分離背景
#   6 開三頁:Portal+治理主控台+測試結果總表
#   7 桌面捷徑 VIA-ALL(冪等)→列印總結後立即歸還提示字元
# 用法:pwsh -File .\Invoke-VIA-All-v0100.ps1   (或 via-all/雙擊捷徑)
# =====================================================================
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
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
$VIA = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-Tail([string]$Dir, [string]$Pat) {
    (Get-ChildItem -Path $Dir -Filter $Pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}
function Start-Detached([string]$label, [string]$exe, [string[]]$argv) {
    try {
        Start-Process $exe -ArgumentList $argv -WindowStyle Minimized | Out-Null
        Write-Host ("  [背景] " + $label + "(分離進程;關窗不斷)") -ForegroundColor Cyan
    } catch { Write-Host ("  [略] " + $label + " 啟動敗=誠實續走") -ForegroundColor Yellow }
}

Write-Host "=== VIA-ALL 唯一總門 v0100(批260)· 零卡斷 · 全背景 ===" -ForegroundColor Cyan

# --- 1 同步自癒 --------------------------------------------------------
git -C $VIA checkout -- "supportive modules/ui_support" 2>$null
if ((git -C $VIA branch --show-current 2>$null) -eq "main") {
    $up = git -C $VIA rev-parse --abbrev-ref --symbolic-full-name "main@{upstream}" 2>$null
    if ($up -and $up -ne "origin/main") { git -C $VIA branch --set-upstream-to=origin/main main 2>$null }
}
$dirty = git -C $VIA status --porcelain 2>$null | Where-Object { $_ -match "^ M" }
if ($dirty) { git -C $VIA stash push -m "VIA-local-traces-$(Get-Date -Format yyyyMMdd_HHmmss)" | Out-Null }
# 批262:零彈窗鐵則——本機分流(pull 產生合併)曾叫出 VSCode 編輯器
# →所有 git 一律 -c core.editor=true --no-edit;三段:ff-only→
# no-edit 自動合併→衝突則 abort 誠實續用現版(絕不開任何編輯器)
$pulled = $false
foreach ($try in 1..2) {
    $out = git -C $VIA -c core.editor=true pull --ff-only origin main 2>&1
    if ($LASTEXITCODE -eq 0) { $pulled = $true; break }
    Start-Sleep -Seconds (2 * $try)
}
if (-not $pulled) {
    $out = git -C $VIA -c core.editor=true pull --no-edit --no-rebase origin main 2>&1
    if ($LASTEXITCODE -eq 0) { $pulled = $true }
    else { git -C $VIA merge --abort 2>$null }
}
Write-Host ("  [同步] pull " + $(if ($pulled) { "OK:" + ($out | Select-Object -Last 1) } else { "衝突/離線=誠實續用現版(零彈窗)" }))

# --- 2 點源短指令(本窗立即生效+profile 自註冊) ------------------------
$reg = Get-Tail $VIA "Register-VIA-Commands-v*.ps1"
if ($reg) { . $reg } else { Write-Host "  [略] 指令定義檔缺(誠實)" -ForegroundColor Yellow }

# --- 3 收容器(有新件自動收+推;冪等 SKIP) -----------------------------
$col = Get-Tail $VIA "Collect-VIA-Intake-v*.ps1"
if ($col) { Start-Detached "Downloads 收容器" "pwsh" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $col) }

# --- 4 VIA 全自動(日更+回補+橋+Portal;其尾端提示只卡自己的隱窗) ------
Start-Detached "VIA 全自動(日更鏈+回補+指揮台橋)" "powershell" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $VIA "VIA.ps1"))

# --- 5 PS 修復 dry-run --------------------------------------------------
$psr = Get-Tail $VIA "Invoke-VIA-PSRepair-v*.ps1"
if ($psr) { Start-Detached "PS 修復三輪(dry-run)" "pwsh" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $psr, "-NoOpen") }

# --- 6 開三頁 -----------------------------------------------------------
foreach ($pg in @("VIA_UI_Portal_v0100.html", "VIA_UI_GovernanceConsole_v0100.html", "VIA_UI_TestResults_v0100.html")) {
    $f = Join-Path $VIA ("supportive modules\ui_support\" + $pg)
    if (Test-Path $f) { Start-Process $f }
}

# --- 7 桌面捷徑 VIA-ALL(冪等)+總結;立即歸還提示字元(零 Read-Host) --
try {
    $lnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "VIA-ALL.lnk"
    if (-not (Test-Path $lnk)) {
        $ws = New-Object -ComObject WScript.Shell
        $sc = $ws.CreateShortcut($lnk)
        $sc.TargetPath = "pwsh.exe"
        $sc.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
        $sc.WorkingDirectory = $VIA
        $sc.IconLocation = "shell32.dll,137"
        $sc.Save()
        Write-Host "  [捷徑] 桌面 VIA-ALL 已建(以後雙擊=一切)" -ForegroundColor Green
    }
} catch { }
Write-Host ""
Write-Host "[VIA-ALL] 派工畢:同步✓ 短指令✓(本窗直用)收容/日更/回補/PS修復=背景跑 · 三頁已開" -ForegroundColor Green
Write-Host "[VIA-ALL] 本窗不卡(零 Read-Host);進度看 Portal/狀態台,關窗不斷。" -ForegroundColor Green
exit 0
