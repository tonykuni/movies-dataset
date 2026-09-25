# ── 批612 解卡:零檔案依賴(不推、不碰 main、不 merge 別條分支)──────────────
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$B = 'claude/via-envmanager-governance-7cls8h'
$ok = $true
$repo = (git rev-parse --show-toplevel 2>$null)
if (-not $repo) { Write-Host "[停] 這裡不是 git 倉,先 cd 進 movies-dataset" -ForegroundColor Red; $ok = $false }
if ($ok) {
    Write-Host "[倉] $repo"                                   -ForegroundColor Cyan
    Write-Host "[枝] $(git rev-parse --abbrev-ref HEAD)"       -ForegroundColor Cyan
    git fetch origin $B 2>&1 | Out-Host

    $dirty = @(git diff --name-only)
    Write-Host "[髒] 追蹤檔 $($dirty.Count) 支(未追蹤件一根不碰)" -ForegroundColor Yellow

    if ($dirty.Count -gt 0) {
        $ts  = Get-Date -Format yyyyMMdd_HHmmss
        $bak = Join-Path $repo "VeritasIntelligenceAnalytics\VIA_Reports\presync_$ts"
        foreach ($f in $dirty) {
            $src = Join-Path $repo $f
            $dst = Join-Path $bak  $f
            New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
            Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction SilentlyContinue
        }
        Write-Host "[備] 整包複製 → $bak" -ForegroundColor Green
        git stash push -m "VIA-presync-$ts" 2>&1 | Out-Host
        Write-Host "[藏] git stash list 看得到;要拿回:git stash pop" -ForegroundColor DarkGray
    }

    git merge --ff-only "origin/$B" 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[綠] 已到 $(git rev-parse --short HEAD)" -ForegroundColor Green
    } else {
        Write-Host "[停] ff-only 不成 = 你本地有 origin 沒有的 commit。不自動 merge,先看:" -ForegroundColor Red
        Write-Host "     git log --oneline origin/$B..HEAD" -ForegroundColor Red
    }
}
