<#
.SYNOPSIS
  VIA Micromamba 極速依賴解析與衝突檢測引擎 (VIA_EnvManager 加速貼片)
.DESCRIPTION
  本腳本旨在攔截 VIA_EnvManager.py 原本依賴 pip 的耗時解析動作。
  透過呼叫 C++ 底層的 Micromamba SAT Solver，以極速完成套件依賴樹的展開與 ABI 衝突檢測。
  掃描結果將轉換為 VIA_EnvManager 讀得懂的標準 JSON 格式。
.PARAMETER TargetEnv
  目標檢測的虛擬環境名稱 (例如: via_core, via_vdf, via_vrn_ocr)
.PARAMETER RequirementsFile
  包含待測套件清單的 txt 檔案路徑 (選填，若無則預設掃描 TargetEnv 目前所有安裝套件)
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$TargetEnv,

    [string]$RequirementsFile = $null
)
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

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " VIA MICROMAMBA RESOLVER: 啟動極速依賴衝突掃描" -ForegroundColor Cyan
Write-Host " 目標環境: $TargetEnv" -ForegroundColor Yellow
Write-Host "============================================================"

# 1. 檢查 Micromamba 是否已安裝於系統路徑
$mambaExe = Get-Command "micromamba" -ErrorAction SilentlyContinue
if (-not $mambaExe) {
    Write-Host "[!] 找不到 micromamba 執行檔。請確認已將其加入環境變數 PATH。" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] 準備 Micromamba 依賴解析任務..." -ForegroundColor Green

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$conflictLogPath = Join-Path $env:TEMP "via_mamba_conflict_$($TargetEnv).json"

# 2. 組合 Micromamba 預演指令 (Dry Run)
# 透過 create --dry-run 讓 SAT Solver 計算依賴樹，而不實際下載或安裝任何東西
$mambaArgs = @(
    "create",
    "-n", "via_dummy_test_$([guid]::NewGuid().ToString().Substring(0,8))",
    "--dry-run",
    "--json",
    "-c", "conda-forge" # 指定頻道，可依據需求改為清華/阿里等 conda 鏡像
)

if ($RequirementsFile -and (Test-Path $RequirementsFile)) {
    Write-Host "  -> 載入外部依賴清單: $RequirementsFile" -ForegroundColor DarkGray
    $mambaArgs += "--file", $RequirementsFile
} else {
    Write-Host "  -> 解析現有環境狀態 (Clone 模擬)..." -ForegroundColor DarkGray
    # 這裡簡化處理，實務上可先透過 conda list 匯出目前套件再餵給 mamba
    $mambaArgs += "--clone", $TargetEnv
}

Write-Host "[2/4] 觸發 C++ SAT Solver 進行拓撲運算與衝突比對..." -ForegroundColor Green

# 3. 執行解析並擷取 JSON 輸出
try {
    # 捕獲 stdout，忽略一般警告
    $mambaOutput = & micromamba $mambaArgs 2>$null

    if (-not $mambaOutput) {
        throw "Micromamba 未回傳任何 JSON 資料"
    }

    $jsonResult = $mambaOutput | ConvertFrom-Json -ErrorAction Stop
    $sw.Stop()

    Write-Host "[3/4] 依賴樹解析完成 (耗時: $($sw.ElapsedMilliseconds)ms)" -ForegroundColor Green

    # 4. 轉換為 VIA_EnvManager 相容格式
    Write-Host "[4/4] 產出 VIA 標準衝突報告..." -ForegroundColor Green

    $viaReport = @{
        Environment = $TargetEnv
        ScanTime_ms = $sw.ElapsedMilliseconds
        IsConflictFree = $true
        Conflicts = @()
        ResolvedPackages = @()
    }

    # 分析 Mamba 輸出
    if ($jsonResult.success -eq $true) {
        # 解析成功，無衝突。將解析出的套件寫入報告
        if ($jsonResult.actions.LINK) {
            $viaReport.ResolvedPackages = $jsonResult.actions.LINK | Select-Object -ExpandProperty name
        }
        Write-Host "  -> 狀態: [PASS] 未偵測到版本死鎖或 ABI 衝突。" -ForegroundColor Green
    } else {
        # 解析失敗，抽出衝突原因 (solver_problems)
        $viaReport.IsConflictFree = $false

        if ($jsonResult.solver_problems) {
            foreach ($prob in $jsonResult.solver_problems) {
                $viaReport.Conflicts += @{
                    Rule = $prob.rule
                    Description = $prob.description
                }
                Write-Host "  -> [衝突警告]: $($prob.description)" -ForegroundColor Red
            }
        } else {
            $viaReport.Conflicts += @{ Description = $jsonResult.error }
            Write-Host "  -> [解析錯誤]: $($jsonResult.error)" -ForegroundColor Red
        }
    }

    # 將轉換後的報告存為 JSON，供 VIA_EnvManager.py 讀取
    $viaReport | ConvertTo-Json -Depth 5 | Set-Content $conflictLogPath -Encoding UTF8

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host " ✅ 快篩完畢！結果已匯出至: $conflictLogPath" -ForegroundColor Green
    Write-Host " 請讓 VIA_EnvManager.py 讀取此檔案以生成 HTML UI Matrix。" -ForegroundColor DarkGray
    Write-Host "============================================================" -ForegroundColor Cyan

} catch {
    Write-Host "`n[!] 解析引擎發生例外錯誤: $_" -ForegroundColor Red
}

