#requires -Version 7.0
# via-sync [branch ...] — fetch, merge Claude work branches into main, push.
# 預設清單涵蓋目前活躍的 Claude 分支;也可指定:via-sync claude/some-branch
param(
    [string[]]$Branches = @(
        "claude/via-system-followup-tz7k9t",
        "claude/bilingual-transcript-restoration-portfolio-ksk0jd"
    )
)
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Push-Location $repo
try {
    git fetch origin 2>&1 | Out-Host
    foreach ($b in $Branches) {
        $exists = git ls-remote --heads origin $b
        if (-not $exists) { Write-Host "  [略過] origin/$b 不存在" -ForegroundColor DarkYellow; continue }
        $ahead = git rev-list --count "HEAD..origin/$b" 2>$null
        if ($ahead -eq "0") { Write-Host "  [已同步] $b(無新 commits)" -ForegroundColor DarkGray; continue }
        Write-Host "  [合併] $b($ahead 個新 commits)" -ForegroundColor Cyan
        git merge --no-edit "origin/$b" 2>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [衝突] $b 合併失敗,已中止此分支;請手動處理後再跑一次。" -ForegroundColor Red
            git merge --abort 2>&1 | Out-Null
        }
    }
    git push origin main 2>&1 | Out-Host
    git log --oneline -5 | Out-Host
}
finally { Pop-Location }
