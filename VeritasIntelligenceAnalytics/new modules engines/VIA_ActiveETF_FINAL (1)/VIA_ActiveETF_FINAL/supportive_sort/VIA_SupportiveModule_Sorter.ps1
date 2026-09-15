#requires -Version 7.0
# ============================================================================
# VIA_SupportiveModule_Sorter.ps1
# 將 supportive_module 分兩堆：
#   USED（主動式 ETF 系統依賴）→ 複製到 Desktop 乾淨 modules 夾（保留原檔）
#   OTHER（VRN 管線/HardGate/備份/複本/索引…）→ 移到 supportive_module\others
# 安全：預設 DRY-RUN（只列計畫 + 寫 CSV），加 -Execute 才實際動作。append-only：USED 用複製不刪原檔。
# LL：param 頂部 / 全名函式 / [IO.File] 寫 log / 無 Start-Process
# ============================================================================
param(
    [string]$Source    = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",
    [string]$UsedDest  = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\supportive modules",
    [string]$OtherDest = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\others",
    [switch]$Execute
)

# 主動式 ETF 系統實際會用到的支援性模組（目前版本，非備份）
$script:Used = @(
    "VeritasAegisNexus.py",     # 取數防護：robots / offline_mode / timeout
    "VeritasCeleritas.py",      # 並行加速：lazy-import / safe_jit / parallel_map
    "VIA_EnvManager.py",        # 環境治理 + eco-check 守門
    "VIA_SSOT_Unified.py"       # SSOT / TW_TICKER_REGEX 規則
)
# 連同這幾支當前版（若存在）一起帶到 USED（資料層真來源時可能參照）
$script:UsedOptional = @(
    "VIS_VRN_TWOfficialYFinance_v06051.py"   # 官方 + yfinance 量價（可作真來源參照）
)

function Write-Status { param([string]$Level,[string]$Message)
    Write-Host ("[{0}][{1}] {2}" -f (Get-Date -Format "HH:mm:ss"), $Level.ToUpper(), $Message) }

function Test-IsUsed { param([string]$Name)
    return ($script:Used -contains $Name) -or ($script:UsedOptional -contains $Name)
}

if (-not (Test-Path $Source)) { Write-Status FAIL "找不到來源：$Source"; exit 1 }
Write-Status INFO ("Source    = {0}" -f $Source)
Write-Status INFO ("UsedDest  = {0}" -f $UsedDest)
Write-Status INFO ("OtherDest = {0}" -f $OtherDest)
Write-Status INFO ("Mode      = {0}" -f ($(if ($Execute) { "EXECUTE（實際動作）" } else { "DRY-RUN（僅預覽，加 -Execute 才動）" })))

if ($Execute) {
    foreach ($d in @($UsedDest,$OtherDest)) { if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null } }
}

# 只處理檔案；排除 others/ 夾與本腳本本身
$selfName = Split-Path $PSCommandPath -Leaf
$otherLeaf = Split-Path $OtherDest -Leaf
$files = Get-ChildItem -LiteralPath $Source -File | Where-Object { $_.Name -ne $selfName }

$plan = New-Object System.Collections.Generic.List[object]
foreach ($f in $files) {
    $isUsed = Test-IsUsed -Name $f.Name
    $action = if ($isUsed) { "COPY→USED" } else { "MOVE→OTHER" }
    $dest   = if ($isUsed) { Join-Path $UsedDest $f.Name } else { Join-Path $OtherDest $f.Name }
    $plan.Add([pscustomobject]@{ Action=$action; File=$f.Name; Dest=$dest })
}

$used  = @($plan | Where-Object { $_.Action -eq "COPY→USED" })
$other = @($plan | Where-Object { $_.Action -eq "MOVE→OTHER" })
Write-Status INFO ("Plan: USED(複製) = {0} 檔 ; OTHER(移動) = {1} 檔 ; 合計 {2}" -f $used.Count, $other.Count, $plan.Count)
foreach ($u in $used) { Write-Status OK ("USED  {0}" -f $u.File) }

# 寫計畫 CSV（log）
$logDir = if ($Execute) { $UsedDest } else { $Source }
$logPath = Join-Path $logDir ("VIA_SortPlan_{0}.csv" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$plan | Export-Csv -LiteralPath $logPath -NoTypeInformation -Encoding UTF8
Write-Status OK ("計畫已寫出：{0}" -f $logPath)

if (-not $Execute) {
    Write-Status WARN "DRY-RUN 結束。確認 CSV 無誤後，加 -Execute 實際執行（USED 複製、OTHER 移動）。"
    exit 0
}

# 實際動作
$okC = 0; $okM = 0; $fail = 0
foreach ($p in $plan) {
    $src = Join-Path $Source $p.File
    try {
        if ($p.Action -eq "COPY→USED") { Copy-Item -LiteralPath $src -Destination $p.Dest -Force; $okC++ }
        else { Move-Item -LiteralPath $src -Destination $p.Dest -Force; $okM++ }
    } catch { $fail++; Write-Status WARN ("失敗 {0}：{1}" -f $p.File, $_.Exception.Message) }
}
Write-Status OK ("完成：USED 複製 {0} ; OTHER 移動 {1} ; 失敗 {2}" -f $okC, $okM, $fail)
Write-Status OK "USED 原檔保留於 supportive_module；OTHER 已移入 others。append-only：未刪除任何檔案。"
exit 0
