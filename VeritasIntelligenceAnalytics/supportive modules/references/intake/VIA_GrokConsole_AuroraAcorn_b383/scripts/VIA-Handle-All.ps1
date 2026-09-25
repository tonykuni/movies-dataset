# VIA-Handle-All · 貼在已開的 pwsh。不要 #requires。整段是一個 & { }
& {
    $ErrorActionPreference = 'Continue'
    $ProgressPreference = 'SilentlyContinue'
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $env:PYTHONNOUSERSITE = '1'
    $env:VIA_LKGC = '2026-09-06'
    $env:VIA_NET = '0'
    $env:VIA_START_YEAR = '2023'
    function Lamp([string]$c, [string]$layer, [string]$msg) {
        $col = switch ($c) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'GREY' { 'DarkGray' } default { 'Yellow' } }
        Write-Host ('{0,-7} {1,-12} {2}' -f $c, $layer, $msg) -ForegroundColor $col
    }
    $cands = @(
        'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics'
    )
    $Root = $cands | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $Root) { Lamp 'RED' 'ROOT' '找不到專案'; return }
    Set-Location -LiteralPath $Root
    Lamp 'GREEN' 'ENTER' $Root
    $venv = Join-Path $Root '.venv-via_vdf\Scripts'
    if (Test-Path -LiteralPath (Join-Path $venv 'python.exe')) {
        $env:PATH = "$venv;" + $env:PATH
        $env:VIA_VDF_PY = Join-Path $venv 'python.exe'
        Lamp 'GREEN' 'PATH' ('venv prepend ' + $venv)
    }
    else { Lamp 'YELLOW' 'PATH' '.venv-via_vdf 未見 · 不新建 conda' }
    Lamp 'GREEN' 'PATH' 'via_iso_* 不進 PATH · ISO99'
    $LogDir = Join-Path $Root 'logs'
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    $Hand = Join-Path $LogDir 'via_handover.md'
    $Br = 'nogit'
    $St = 'nogit'
    if (Test-Path -LiteralPath (Join-Path $Root '.git')) {
        $Br = [string](git rev-parse --abbrev-ref HEAD 2>$null)
        $St = [string](git status -sb 2>$null | Out-String)
    }
    $lines = @(
        ('# VIA handover 2026-09-08  ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
        ('root ' + $Root),
        ('branch ' + $Br),
        'LIVE off. DCT sealed. no force push. no conda remove. iso not on PATH.',
        'AEA 29/29 00981A 2880 yi +3.52pct flow=0 no dUnits HTML logs/via_aetf_board.html',
        'U VIA_U=VDF_ENG075 MOPS sii/otc month files 2023-01 CACHE not ticker loop',
        'GIT no src in mother repo. add each path in foreach. never splat single string.',
        'ENV LKGC 2026-09-06 tsinghua. numpy via_iso_numpy. UVT-01-08.',
        'SEAL VETF 13 GREY files are pack listing not missing.',
        'git status:',
        $St.Trim(),
        'next: set VIA_GH_YES=1 then paste this block again to commit/push'
    )
    Set-Content -LiteralPath $Hand -Value $lines -Encoding utf8
    Lamp 'GREEN' 'LOG' $Hand
    Lamp 'GREEN' 'AEA' 'BOARD 29 LIVE off'
    Lamp 'GREEN' 'U' 'VIA_U ENG075 revenue CACHE LIVE off'
    if (-not (Test-Path -LiteralPath (Join-Path $Root '.git'))) { Lamp 'RED' 'GIT' '不是 git 倉'; return }
    git status -sb
    $prefer = @('src', 'public/via', 'public', 'scripts', 'locks', 'package.json', 'package-lock.json', 'AGENTS.md', 'VIA-ALL.cmd', 'logs/via_handover.md')
    [string[]]$add = @($prefer | Where-Object { Test-Path -LiteralPath (Join-Path $Root $_) })
    if ($env:VIA_GH_HTML -eq '1' -and (Test-Path -LiteralPath (Join-Path $Root 'logs\via_aetf_board.html'))) {
        $add += 'logs/via_aetf_board.html'
    }
    if ($null -eq $add) { $add = @() }
    Lamp 'GREEN' 'ADD' $(if ($add.Count) { ($add -join ' ') } else { 'none' })
    if ($env:VIA_GH_YES -ne '1') {
        Lamp 'YELLOW' 'GH' 'preview only. then: $env:VIA_GH_YES=''1''  and paste this block again'
        return
    }
    if ($add.Count -lt 1) { Lamp 'YELLOW' 'GH' 'nothing to add'; return }
    foreach ($p in $add) { git add -- $p }
    git status -sb
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) { Lamp 'YELLOW' 'GH' 'empty index'; return }
    $msg = $env:VIA_GH_MSG
    if (-not $msg) { $msg = 'VIA handle-all AEA29 U-ENG075 handover log' }
    git commit -m $msg
    git push -u origin HEAD
    Lamp 'GREEN' 'GH' 'push done. read logs/via_handover.md'
}
