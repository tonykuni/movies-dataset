#requires -Version 7.0
<#
Invoke-VIA-Bridge v0100 — 一支 PowerShell:前後端對接 + test/debug 迴圈 + 啟用 UI
流程:[1] sync(容錯)→ [2] 後端探測引擎(B1-B5)→ [3] TEST:state JSON 可解析 +
     前端頁存在 + TAB 元件齊全 → 失敗則 DEBUG 診斷後重試(上限 3 輪)→
     [4] ACTIVATE:非阻塞開啟 Command Bridge(首頁=總覽+狀態矩陣,多 TAB)。
慣例:無 Read-Host、無 exit;失敗誠實 FAIL 續行;結尾 OK/FAIL 總表。
回退:直接改跑 via-mega/via-ui(Bridge 為附加對接層,不影響既有接線)。
#>
param([int]$MaxRounds = 3)
$ErrorActionPreference = "Continue"
$VIA = $PSScriptRoot
$Engine = Join-Path $VIA "supportive modules\VIA_Governance_Runtime\SUP_MDL140_BridgeEngine_v0100.py"
$StateJson = Join-Path $VIA "VIA_Reports\bridge_state.json"
$FrontEnd = Join-Path $VIA "VIA_Reports\VIA_CommandBridge.html"
$Results = @()

Write-Host ("=" * 66) -ForegroundColor DarkCyan
Write-Host "  VIA BRIDGE v0100  |  前後端對接 · test/debug 迴圈 · 狀態矩陣" -ForegroundColor Cyan
Write-Host ("=" * 66) -ForegroundColor DarkCyan

# [1] SYNC(容錯:離線也能出本機真相)
Write-Host "`n[STATUS] (1/4) SYNC 同步 repo" -ForegroundColor Yellow
try { & pwsh -NoProfile -File (Join-Path $VIA "bin\via-sync.ps1") | Out-Host; $Results += [pscustomobject]@{ 階段 = "SYNC"; 結果 = "OK" } }
catch { Write-Host "[STATUS] sync 失敗(離線?)— 續行本機探測" -ForegroundColor DarkYellow; $Results += [pscustomobject]@{ 階段 = "SYNC"; 結果 = "WARN" } }

# [2]+[3] 後端 + TEST/DEBUG 迴圈
$passed = $false
for ($round = 1; $round -le $MaxRounds -and -not $passed; $round++) {
    Write-Host ("`n[STATUS] (2/4) 後端探測引擎 B1-B5(第 {0}/{1} 輪)" -f $round, $MaxRounds) -ForegroundColor Yellow
    & py $Engine --no-open
    $engOK = ($LASTEXITCODE -eq 0)
    Write-Host "[STATUS] (3/4) TEST:驗證前後端產物" -ForegroundColor Yellow
    $t1 = $false; $t2 = $false; $t3 = $false
    try { $state = Get-Content -LiteralPath $StateJson -Raw -Encoding UTF8 | ConvertFrom-Json; $t1 = ($null -ne $state.overall) } catch {}
    if (Test-Path -LiteralPath $FrontEnd) {
        $html = Get-Content -LiteralPath $FrontEnd -Raw -Encoding UTF8
        $t2 = ($html.Length -gt 10000)
        $t3 = (([regex]::Matches($html, "onclick='show")).Count -ge 5)
    }
    Write-Host ("         引擎={0} · stateJSON={1} · 前端頁={2} · TAB元件={3}" -f
        ($engOK ? "OK" : "FAIL"), ($t1 ? "OK" : "FAIL"), ($t2 ? "OK" : "FAIL"), ($t3 ? "OK" : "FAIL")) -ForegroundColor DarkGray
    $passed = ($engOK -and $t1 -and $t2 -and $t3)
    if (-not $passed -and $round -lt $MaxRounds) {
        Write-Host "[DEBUG] 未全過 — 診斷:檢查 py 版本與引擎 AST 後重試" -ForegroundColor Red
        & py --version | Out-Host
        & py -m py_compile $Engine
        Write-Host ("[DEBUG] py_compile exit={0}" -f $LASTEXITCODE) -ForegroundColor Red
    }
}
$Results += [pscustomobject]@{ 階段 = "後端引擎 B1-B5"; 結果 = ($passed ? "OK" : "FAIL") }
$Results += [pscustomobject]@{ 階段 = "TEST 前後端產物"; 結果 = ($passed ? "OK" : "FAIL") }

# [4] ACTIVATE:非阻塞開啟前端(首頁=總覽+狀態矩陣)
Write-Host "`n[STATUS] (4/4) ACTIVATE:開啟 Command Bridge UI" -ForegroundColor Yellow
if ($passed -and (Test-Path -LiteralPath $FrontEnd)) {
    Start-Process $FrontEnd | Out-Null
    $Results += [pscustomobject]@{ 階段 = "ACTIVATE UI"; 結果 = "OK" }
    if ($state) {
        Write-Host ("[真相] 總燈號 {0} · 接線 {1} 條 · SSOT {2} · 依賴 {3} · UI 頁 {4}" -f
            $state.overall, $state.wiring.Count, $state.ssot.Count, $state.deps.Count, $state.ui.total_pages) -ForegroundColor Green
    }
} else {
    $Results += [pscustomobject]@{ 階段 = "ACTIVATE UI"; 結果 = "FAIL" }
}

Write-Host ""
$Results | Format-Table -AutoSize
$okN = ($Results | Where-Object 結果 -eq "OK").Count
Write-Host ("[總結] {0}/{1} 階段 OK · 前端={2}(run-local,每跑必重生=永遠當下真相)" -f $okN, $Results.Count, $FrontEnd) -ForegroundColor Green

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
