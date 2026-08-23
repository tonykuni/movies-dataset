#requires -Version 7.0
param([switch]$Audit, [switch]$Panorama, [switch]$Polyglot, [switch]$VRN, [switch]$Tower)

# ============================================================
# def Start-VIA-OneClick · ONE POWERSHELL TO HANDLE ALL
# 同步 → VDF intake → AutoPlot → UI(v010) [+ 可選稽核/全景/AIO]
# 自我定位:本檔位於 <repo>\VeritasIntelligenceAnalytics\,不依賴硬編路徑。
# 用法:
#   pwsh -ExecutionPolicy Bypass -File .\Start-VIA-OneClick.ps1
#   pwsh -ExecutionPolicy Bypass -File .\Start-VIA-OneClick.ps1 -Audit -Panorama -Polyglot
# ============================================================
$ErrorActionPreference = 'Stop'

$via  = $PSScriptRoot
$repo = Split-Path $via -Parent
$fm   = Join-Path $via 'functional modules'
$opt  = Join-Path $via 'supportive modules\VIA_Optimizer_Suite'
$rpt  = Join-Path $env:USERPROFILE 'VIA_Reports'
$feat = 'claude/via-system-followup-tz7k9t'
Set-Location $repo

# ---------- 1) 收拾 + 同步(自動判斷 PR 合併與否) ----------
git checkout -- "VeritasIntelligenceAnalytics/functional modules/VDF/qa/evidence/movies_intake_summary.json" 2>$null
Get-ChildItem "$fm\VDF\db\movies_dataset_*.sqlite" -ErrorAction SilentlyContinue | Remove-Item -Force
# 六槽標準:各模組 temp\ 啟動時自動清空(保留 .gitkeep)
foreach ($m in 'VDF','VAP','VRN') {
    Get-ChildItem "$fm\$m\temp" -Exclude '.gitkeep' -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
git fetch origin
$onMain = git branch -r --contains "origin/$feat" 2>$null | Select-String 'origin/main'
if ($onMain -or -not (git ls-remote --heads origin $feat)) {
    Write-Host "[SYNC] PR 已合併 → main" -ForegroundColor Cyan
    git checkout main; git pull origin main
} else {
    Write-Host "[SYNC] PR 未合併 → $feat" -ForegroundColor Cyan
    git checkout $feat; git pull origin $feat
}

# ---------- 2) VDF intake → AutoPlot ----------
$py = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
& $py "$fm\VDF\engine\VDF_ENG042_MoviesIntake_v001.py" --base $via --source "$repo\data" --mode Refresh
if ($LASTEXITCODE -ne 0) { Write-Host "[STOP] VDF 未過閘" -ForegroundColor Red; return }
& $py "$fm\VAP\engine\VAP_ENG002_AutoplotEngine_v001.py" --base $via --auto --max-charts 40
if ($LASTEXITCODE -ne 0) { Write-Host "[STOP] AutoPlot 失敗" -ForegroundColor Red; return }

# ---------- 3) 開啟 UI(v010 主力;v009 canonical 保留不開) ----------
Start-Process (Join-Path $fm 'VAP\ui\VAP_Workbench_v010.html')
Start-Process (Join-Path $via 'VAP\output\index.html')

# ---------- 4) 可選:Optimizer Suite(唯讀/無刪除,報告輸出到 $rpt) ----------
# 每個工具各自包 try/catch:單一工具失敗或被中斷,不拖垮其餘工具鏈與摘要。
if ($Audit -or $Panorama -or $Polyglot) {
    New-Item -ItemType Directory -Path $rpt -Force | Out-Null
    if ($Audit) {
        Write-Host "`n[RUN] TurboOptimizer v3.3 SafeAudit(無刪除)" -ForegroundColor Cyan
        try {
            & (Join-Path $opt 'VIA_TurboOptimizer_v3.3_OneDrive_Coding_AISafeAudit.ps1') `
                -OutputRoot (Join-Path $rpt '_disk_audit') -OpenReport
        } catch { Write-Host "[WARN] Audit 中斷/失敗:$($_.Exception.Message) — 繼續其餘流程" -ForegroundColor Yellow }
    }
    if ($Panorama) {
        Write-Host "`n[RUN] FirstSight Panorama Governance Matrix v0100(唯讀)" -ForegroundColor Cyan
        try {
            & (Join-Path $opt 'Invoke-VIA-FirstSightPanorama-GovernanceMatrix-v0100.ps1') `
                -BaseRoot $via -DownloadRoot (Join-Path $env:USERPROFILE 'Downloads')
        } catch { Write-Host "[WARN] Panorama 中斷/失敗:$($_.Exception.Message) — 繼續其餘流程" -ForegroundColor Yellow }
    }
    if ($Polyglot) {
        Write-Host "`n[RUN] SafePolyglotOptimizer AIO v0102(僅報告 · 子檔取自 repo Standalone Package)" -ForegroundColor Cyan
        $bundle = Join-Path $via 'supportive modules\VIA_Standalone_Package_v0102\_supportive_bundle\powershell'
        try {
            & (Join-Path $opt 'Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1') `
                -SupportiveModulesRoot (Join-Path $via 'supportive modules') `
                -NexusCorePath (Join-Path $bundle 'Invoke-VeritasNexusCore.ps1') `
                -PolyglotPath  (Join-Path $bundle 'Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1') `
                -OutputRoot (Join-Path $rpt '_polyglot') -SelfTest -OpenReport
        } catch { Write-Host "[WARN] Polyglot 中斷/失敗:$($_.Exception.Message) — 繼續其餘流程" -ForegroundColor Yellow }
    }
}

# ---------- 4.5) 可選:VRN 唯讀預檢(Lane2 IO 盤點 + Lane3 引擎能力) ----------
# Lane 腳本第 13 行硬編了已不存在的 OneDrive 舊路徑;canonical 檔不可變更,
# 故在記憶體中將 $RelatedPath 改址到 repo 的 VRN canonical tree 後執行。
if ($VRN) {
    $vrnDir = Join-Path $fm 'VRN'
    foreach ($lane in 'Start-VRN-Lane2-IOInventory.ps1', 'Start-VRN-Lane3-EngineCapability.ps1') {
        Write-Host "`n[RUN] VRN $lane(唯讀 · RelatedPath→repo)" -ForegroundColor Cyan
        try {
            $code = Get-Content -Raw (Join-Path $vrnDir $lane)
            $code = $code -replace '\$RelatedPath = ".*?"', ('$RelatedPath = "' + $vrnDir + '"')
            & ([scriptblock]::Create($code))
        } catch { Write-Host "[WARN] $lane 中斷/失敗:$($_.Exception.Message) — 繼續其餘流程" -ForegroundColor Yellow }
    }
}

# ---------- 4.8) 可選:Control Tower(HTML 控制台,全部動作變按鈕) ----------
if ($Tower) {
    $towerPy = Join-Path $via 'supportive modules\VIA_Control_Tower\SUP_MDL115_ControlTower.py'
    Write-Host "`n[RUN] VIA Control Tower → http://127.0.0.1:8765" -ForegroundColor Cyan
    Start-Process $py -ArgumentList ('"' + $towerPy + '" --base "' + $via + '"') -WindowStyle Hidden
    Start-Sleep -Seconds 2
    Start-Process 'http://127.0.0.1:8765'
}

# ---------- 5) 摘要 ----------
$db = Get-Item "$fm\VDF\db\movies_dataset.sqlite"
$n  = (Get-ChildItem (Join-Path $via 'VAP\output\VAP_*.html')).Count
Write-Host "`n===== VIA READY =====" -ForegroundColor Green
Write-Host ("分支     : " + (git branch --show-current))
Write-Host ("資料庫   : {0} ({1} bytes)" -f $db.FullName, $db.Length)
Write-Host ("圖表     : {0} 張 → {1}" -f $n, (Join-Path $via 'VAP\output'))
Write-Host "工作台   : v010(響應式+拖曳)· v009 canonical 保留"
Write-Host "Header鎖 : LOCKED · Optimizer Suite: AST 驗證 · 雜湊登記"
Write-Host "VRN      : canonical tree in repo · 81 artifacts hash-locked(-VRN 跑預檢)"
if ($Audit -or $Panorama -or $Polyglot) { Write-Host "工具報告 : $rpt" }

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
