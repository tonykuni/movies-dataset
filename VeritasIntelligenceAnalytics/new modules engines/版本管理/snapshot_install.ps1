<#
.SYNOPSIS
    VIA Snapshot Integration Installer (L+N+O+M 一鍵安裝)
.DESCRIPTION
    把 via_snapshot_integration.py + VIA_Snapshot_Console.html
    + via_inventory.py 安裝到 Forge 生出的 VIA 產品包，並把
    snapshot 指令註冊到 via 主路由。

    遵守 VIA PS7 規則:
      - param() at top
      - $script: prefix for cross-scope vars
      - 全名函式 (no SL/SP/WL conflicts)
      - 不使用 `Sort-Object Prop -Descending, Prop2` (用 hashtable 語法)
.PARAMETER Base
    VIA 產品根目錄。預設: C:\VeritasIntelligenceAnalytics
.PARAMETER SourceDir
    本安裝包來源目錄 (放有 via_snapshot_integration.py 等)。預設: 同此腳本目錄
.PARAMETER InjectHooks
    是否注入 via.ps1 的 post-activate hook。預設: $true
.EXAMPLE
    .\snapshot_install.ps1 -Base "C:\VeritasIntelligenceAnalytics"
#>

param(
    [string]$Base = "C:\VeritasIntelligenceAnalytics",
    [string]$SourceDir = $PSScriptRoot,
    [bool]$InjectHooks = $true
)

#requires -Version 7

$ErrorActionPreference = "Stop"

# ============================================================
# Helpers
# ============================================================
function Write-Banner {
    param([string]$Text)
    $line = "=" * 66
    Write-Host ""
    Write-Host "  $line" -ForegroundColor DarkGray
    Write-Host "   $Text" -ForegroundColor Cyan
    Write-Host "  $line" -ForegroundColor DarkGray
}

function Write-Step {
    param([string]$Text, [string]$Color = "White")
    Write-Host "  $Text" -ForegroundColor $Color
}

function Show-Prog {
    param([string]$Phase, [int]$Current, [int]$Total)
    $pct = if ($Total -gt 0) { [int](100 * $Current / $Total) } else { 0 }
    Write-Host ("  [PROGRESS] [{0}/{1}] {2}%  {3}" -f $Current, $Total, $pct, $Phase) -ForegroundColor DarkGray
}

# ============================================================
# Pre-flight
# ============================================================
Write-Banner "VIA Snapshot Integration Installer · v1.0"
Write-Step "Base       : $Base"
Write-Step "Source     : $SourceDir"
Write-Step "InjectHooks: $InjectHooks"

if (-not (Test-Path $Base)) {
    Write-Step "✗ Base 目錄不存在: $Base" "Red"
    Write-Step "  請先用 via_package_forge.py 生產品包" "DarkGray"
    exit 1
}

$script:viaPs1   = Join-Path $Base "via.ps1"
$script:cfgJson  = Join-Path $Base "config\via.config.json"
$script:cmdsJson = Join-Path $Base "config\commands.json"

if (-not (Test-Path $script:viaPs1)) {
    Write-Step "✗ 找不到 $script:viaPs1" "Red"
    Write-Step "  此處看起來不是 Forge 生的 VIA 產品包" "DarkGray"
    exit 1
}

# 來源檔案
$script:srcInventory   = Join-Path $SourceDir "via_inventory.py"
$script:srcIntegration = Join-Path $SourceDir "via_snapshot_integration.py"
$script:srcConsole     = Join-Path $SourceDir "VIA_Snapshot_Console.html"

# via_inventory.py 是必要前置；若缺失就只裝整合層
$inventoryExists = Test-Path $script:srcInventory

# ============================================================
# Step 1/6: 建立目標資料夾
# ============================================================
Show-Prog "creating dirs" 1 6
foreach ($d in @("tools", "config", "snapshots", "logs\runtime")) {
    $full = Join-Path $Base $d
    if (-not (Test-Path $full)) {
        New-Item -ItemType Directory -Path $full -Force | Out-Null
        Write-Step "  + mkdir $d" "DarkGray"
    }
}

# ============================================================
# Step 2/6: 複製檔案
# ============================================================
Show-Prog "copying files" 2 6

$copied = @()
$missing = @()

if ($inventoryExists) {
    Copy-Item $script:srcInventory (Join-Path $Base "tools\via_inventory.py") -Force
    $copied += "tools\via_inventory.py"
} else {
    $missing += "via_inventory.py (前置依賴；snapshot/diff/verify 將無法運作)"
}

if (Test-Path $script:srcIntegration) {
    Copy-Item $script:srcIntegration (Join-Path $Base "tools\via_snapshot_integration.py") -Force
    $copied += "tools\via_snapshot_integration.py"
} else {
    Write-Step "✗ 找不到 via_snapshot_integration.py" "Red"; exit 1
}

if (Test-Path $script:srcConsole) {
    Copy-Item $script:srcConsole (Join-Path $Base "tools\VIA_Snapshot_Console.html") -Force
    $copied += "tools\VIA_Snapshot_Console.html"
} else {
    $missing += "VIA_Snapshot_Console.html (儀表板將不可用)"
}

foreach ($f in $copied)  { Write-Step "  ✓ $f" "Green" }
foreach ($m in $missing) { Write-Step "  ⚠ MISSING: $m" "Yellow" }

# ============================================================
# Step 3/6: 註冊指令到 commands.json
# ============================================================
Show-Prog "registering commands" 3 6

# 透過 Python 呼叫 install (避免在 PS7 裡硬編 JSON 結構)
$py = Join-Path $Base "tools\via_snapshot_integration.py"
$registerCmd = "py -3.11 `"$py`" install"
Write-Step "  > $registerCmd" "DarkGray"
$out = & py -3.11 "$py" install 2>&1
$out | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }

# ============================================================
# Step 4/6: 寫預設 retention policy
# ============================================================
Show-Prog "writing default retention policy" 4 6

$retentionPath = Join-Path $Base "config\snapshot_retention.json"
if (-not (Test-Path $retentionPath)) {
    $retentionDefault = @{
        keep_all_major    = $true
        keep_all_minor    = $true
        keep_recent_patch = 10
        keep_all_archived = $true
        min_age_days      = 1
        max_total         = 100
    } | ConvertTo-Json -Depth 4
    [IO.File]::WriteAllText($retentionPath, $retentionDefault, [Text.Encoding]::UTF8)
    Write-Step "  ✓ config\snapshot_retention.json" "Green"
} else {
    Write-Step "  ⊘ config\snapshot_retention.json (已存在，保留)" "DarkGray"
}

# 預設啟用的 hooks
$hooksPath = Join-Path $Base "config\snapshot_hooks.json"
if (-not (Test-Path $hooksPath)) {
    $hooksDefault = @{
        enabled        = @("post-activate", "post-forge")
        auto_retention = $true
    } | ConvertTo-Json -Depth 4
    [IO.File]::WriteAllText($hooksPath, $hooksDefault, [Text.Encoding]::UTF8)
    Write-Step "  ✓ config\snapshot_hooks.json (預設啟用: post-activate, post-forge)" "Green"
} else {
    Write-Step "  ⊘ config\snapshot_hooks.json (已存在，保留)" "DarkGray"
}

# ============================================================
# Step 5/6: 注入 via.ps1 hooks (可選)
# ============================================================
Show-Prog "injecting via.ps1 hooks" 5 6

if ($InjectHooks) {
    $viaContent = Get-Content $script:viaPs1 -Raw -Encoding UTF8

    $hookMarker = "# ===== SNAPSHOT HOOKS (auto-injected by snapshot_install.ps1) ====="
    if ($viaContent -match [regex]::Escape($hookMarker)) {
        Write-Step "  ⊘ via.ps1 hooks 已存在，跳過注入" "DarkGray"
    } else {
        $hookCode = @"

$hookMarker
# Auto-snapshot triggers wrapped around command dispatch.
# 觸發點由 config\snapshot_hooks.json 控制；可用 via via-snap-hook 管理。
function Invoke-SnapshotHook {
    param([string]`$Trigger, [string]`$Note = "")
    `$hookCfg = Join-Path `$script:VIA_HOME "config\snapshot_hooks.json"
    if (-not (Test-Path `$hookCfg)) { return }
    try {
        `$cfg = Get-Content `$hookCfg -Raw | ConvertFrom-Json
        if (`$cfg.enabled -contains `$Trigger) {
            `$intPy = Join-Path `$script:VIA_HOME "tools\via_snapshot_integration.py"
            if (Test-Path `$intPy) {
                Write-Log "INFO" "snapshot hook fired: `$Trigger"
                & py -3.11 `$intPy auto --trigger `$Trigger --note `$Note 2>&1 |
                    ForEach-Object { Write-Log "HOOK" `$_ } | Out-Null
            }
        }
    } catch {
        Write-Log "WARN" "snapshot hook error: `$_"
    }
}
# ===== END SNAPSHOT HOOKS =====
"@
        # 注入點：在 `exit `$exit` 之前
        if ($viaContent -match "exit\s+\`$exit") {
            # 在 exec 之後、exit 之前插入 hook 觸發
            $hookCall = @"
# Fire post-* hooks based on command id
switch -Wildcard (`$cmd.id) {
    "VIA.AUTH.ACTIVATE.*" { Invoke-SnapshotHook -Trigger "post-activate" -Note "after `$(`$cmd.alias)" }
    "VIA.SYS.SELFTEST.*"  { if (`$exit -eq 0) { Invoke-SnapshotHook -Trigger "post-selftest" -Note "selftest passed" } }
}

"@
            $newContent = $viaContent -replace "(?s)(exit\s+\`$exit)", "$hookCall`$1"
            $newContent = $newContent + "`n" + $hookCode
            [IO.File]::WriteAllText($script:viaPs1, $newContent, [Text.Encoding]::UTF8)
            Write-Step "  ✓ via.ps1 已注入 snapshot hooks" "Green"
        } else {
            Write-Step "  ⚠ 找不到 'exit `$exit' 注入點；hooks 未注入" "Yellow"
            Write-Step "    可手動加入: Invoke-SnapshotHook -Trigger post-activate" "DarkGray"
        }
    }
} else {
    Write-Step "  ⊘ -InjectHooks `$false，略過 via.ps1 注入" "DarkGray"
}

# ============================================================
# Step 6/6: Smoke test
# ============================================================
Show-Prog "smoke test" 6 6

Push-Location $Base
try {
    Write-Step "  > via via-snap-status" "DarkGray"
    & py -3.11 (Join-Path $Base "tools\via_snapshot_integration.py") status 2>&1 |
        ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
} finally {
    Pop-Location
}

# ============================================================
# Summary
# ============================================================
Write-Banner "✓ INSTALLATION COMPLETE"
Write-Host ""
Write-Host "  接下來:" -ForegroundColor White
Write-Host "    cd $Base"                                       -ForegroundColor DarkGray
Write-Host "    via via-snap-status         # 查看快照狀態"      -ForegroundColor Gray
Write-Host "    via via-snapshot            # 拍第一張快照"      -ForegroundColor Gray
Write-Host "    via via-snap-list           # 列出所有快照"      -ForegroundColor Gray
Write-Host "    via via-snap-console        # 開啟 HTML 儀表板"  -ForegroundColor Gray
Write-Host "    via via-snap-sync           # 設定遠端同步"      -ForegroundColor Gray
Write-Host "    via via-snap-hook --list    # 查看自動觸發點"    -ForegroundColor Gray
Write-Host ""
Write-Host "  已啟用的 hooks (自動拍快照):" -ForegroundColor White
Write-Host "    ✓ post-activate    每次 via via-activate 成功後" -ForegroundColor Green
Write-Host "    ✓ post-forge       (需手動觸發 from Forge)"      -ForegroundColor Green
Write-Host ""
