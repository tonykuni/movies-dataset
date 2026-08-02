#requires -Version 7.0
param([switch]$Audit, [switch]$Panorama, [switch]$Polyglot)

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
& $py "$fm\VDF\engine\vdf_movies_intake_v001.py" --base $via --source "$repo\data" --mode Refresh
if ($LASTEXITCODE -ne 0) { Write-Host "[STOP] VDF 未過閘" -ForegroundColor Red; return }
& $py "$fm\VAP\engine\via_autoplot_engine_v001.py" --base $via --auto --max-charts 40
if ($LASTEXITCODE -ne 0) { Write-Host "[STOP] AutoPlot 失敗" -ForegroundColor Red; return }

# ---------- 3) 開啟 UI(v010 主力;v009 canonical 保留不開) ----------
Start-Process (Join-Path $fm 'VAP\ui\VAP_Workbench_v010.html')
Start-Process (Join-Path $via 'VAP\output\index.html')

# ---------- 4) 可選:Optimizer Suite(唯讀/無刪除,報告輸出到 $rpt) ----------
if ($Audit -or $Panorama -or $Polyglot) {
    New-Item -ItemType Directory -Path $rpt -Force | Out-Null
    if ($Audit) {
        Write-Host "`n[RUN] TurboOptimizer v3.3 SafeAudit(無刪除)" -ForegroundColor Cyan
        & (Join-Path $opt 'VIA_TurboOptimizer_v3.3_OneDrive_Coding_AISafeAudit.ps1') `
            -OutputRoot (Join-Path $rpt '_disk_audit') -OpenReport
    }
    if ($Panorama) {
        Write-Host "`n[RUN] FirstSight Panorama Governance Matrix v0100(唯讀)" -ForegroundColor Cyan
        & (Join-Path $opt 'Invoke-VIA-FirstSightPanorama-GovernanceMatrix-v0100.ps1') `
            -BaseRoot $via -DownloadRoot (Join-Path $env:USERPROFILE 'Downloads')
    }
    if ($Polyglot) {
        Write-Host "`n[RUN] SafePolyglotOptimizer AIO v0102(僅報告)" -ForegroundColor Cyan
        & (Join-Path $opt 'Invoke-VIA-SafePolyglotOptimizer-AIO-v0102.ps1') `
            -SelfTest -OpenReport
    }
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
if ($Audit -or $Panorama -or $Polyglot) { Write-Host "工具報告 : $rpt" }
