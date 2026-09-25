#requires -Version 7.0
# VIA GitHub 上傳 · 只 add 實際存在的路徑 · 禁止強制推送
# 預覽：直接貼。真的 push： $env:VIA_GH_YES='1'
# 看板 HTML：$env:VIA_GH_HTML='1'
$ErrorActionPreference = 'Stop'
$cands = @(
    'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
    'C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics'
)
$Root = $cands | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $Root) { Write-Host 'RED     ROOT         找不到專案'; return }
Set-Location -LiteralPath $Root
if (-not (Test-Path -LiteralPath (Join-Path $Root '.git'))) { Write-Host 'RED     GIT          不是 git 倉'; return }
git rev-parse --abbrev-ref HEAD | ForEach-Object { Write-Host "GREEN   BR           $_" }
git status -sb
$prefer = @('src', 'public/via', 'public', 'scripts', 'locks', 'package.json', 'package-lock.json', 'AGENTS.md', 'VIA-ALL.cmd')
[string[]]$add = @($prefer | Where-Object { Test-Path -LiteralPath (Join-Path $Root $_) })
if ($env:VIA_GH_HTML -eq '1' -and (Test-Path -LiteralPath (Join-Path $Root 'logs\via_aetf_board.html'))) {
    $add += 'logs/via_aetf_board.html'
}
if ($add -isnot [System.Array]) { $add = @($add) }
Write-Host ('GREEN   ADD          ' + ($(if ($add.Count) { $add -join ' ' } else { '無' })))
if ($env:VIA_GH_YES -ne '1') {
    Write-Host 'YELLOW  PLAN         預覽 · 設 VIA_GH_YES=1 才 add/commit/push'
    Write-Host 'YELLOW  SKIP         湖 parquet、.venv、.env、node_modules、logs（HTML 另開 VIA_GH_HTML=1）'
    return
}
if (-not $add.Count) { Write-Host 'YELLOW  SKIP         此倉無標準路徑（母倉可無 src）'; return }
foreach ($p in $add) { git add -- $p }
git status -sb
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { Write-Host 'YELLOW  SKIP         無暫存'; return }
$msg = $env:VIA_GH_MSG
if (-not $msg) { $msg = 'VIA central entry · EnvManager PATH isolate-not-delete' }
git commit -m $msg
git push -u origin HEAD
Write-Host 'GREEN   GH           push 完成 · 禁止強制推送'
return
