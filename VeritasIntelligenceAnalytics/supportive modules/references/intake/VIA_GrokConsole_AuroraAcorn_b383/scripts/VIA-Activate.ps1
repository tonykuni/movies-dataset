# VIA Activate ALL · GitHub = C:\Users\tonyk\movies-dataset @ claude/via-system-followup-tz7k9t
# 另探 C:\Users\tonyk\Github · 資料盤 Downloads · 母檔 VeritasIntelligenceAnalytics
# 政策: 不刪、不卸載、不殺行程、不 exit、預設禁網、勿重做 DCT01–20
# 貼在 PowerShell 7（PS>）。不要貼 cmd。不要 cd /d。
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

function Lamp([string]$c, [string]$layer, [string]$msg) {
    $col = switch ($c) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'GREY' { 'DarkGray' } default { 'Yellow' } }
    Write-Host ('{0,-7} {1,-14} {2}' -f $c, $layer, $msg) -ForegroundColor $col
}

$WantRemote = 'https://github.com/tonykuni/movies-dataset'
$WantBranch = 'claude/via-system-followup-tz7k9t'
$GitRoots = @(
    'C:\Users\tonyk\movies-dataset',
    'C:\Users\tonyk\Github\movies-dataset',
    'C:\Users\tonyk\Github'
)
$CodeRoots = @(
    'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
    'C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics',
    'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
    'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics'
)
$DataRoots = @(
    'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics',
    'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics'
)

$here = (Get-Location).Path
$Code = @($here) + $CodeRoots | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique -First 1
if (-not $Code) { Lamp 'RED' 'Mother' '找不到母系統'; return }
Set-Location -LiteralPath $Code
Lamp 'GREEN' 'Mother' $Code

$Data = $DataRoots | Where-Object { Test-Path -LiteralPath (Join-Path $_ 'dict\VDF\DATABASE') } | Select-Object -First 1
if ($Data) { Lamp 'GREEN' 'Data' $Data } else { Lamp 'YELLOW' 'Data' 'dict\VDF\DATABASE 未見' }

$env:PYTHONNOUSERSITE = '1'
$env:VIA_LKGC = '2026-09-06'
$env:VIA_START_YEAR = '2023'
$env:VIA_NET = '0'
if ($Data) { $env:VIA_DATA_ROOT = $Data }
Lamp 'GREEN' 'PATH' 'LKGC · 起始年 2023 · 禁網 · via_iso_* 不刪'

$Git = $GitRoots | Where-Object { Test-Path -LiteralPath (Join-Path $_ '.git') } | Select-Object -First 1
if (-not $Git -and (Test-Path -LiteralPath (Join-Path $Code '.git'))) { $Git = $Code }

if ($Git) {
    $br = (git -C $Git rev-parse --abbrev-ref HEAD 2>$null)
    $rem = (git -C $Git remote get-url origin 2>$null)
    Lamp 'GREEN' 'GitHub' "$Git"
    Lamp 'GREEN' 'Remote' $(if ($rem) { $rem } else { $WantRemote })
    if (-not $rem) { git -C $Git remote add origin $WantRemote 2>$null }
    git -C $Git fetch origin --prune 2>&1 | Out-Host
    git -C $Git switch $WantBranch 2>$null
    if ($LASTEXITCODE -ne 0) { git -C $Git checkout -B $WantBranch "origin/$WantBranch" 2>$null }
    $br = (git -C $Git rev-parse --abbrev-ref HEAD 2>$null)
    Lamp $(if ($br -eq $WantBranch) { 'GREEN' } else { 'YELLOW' }) 'Branch' "$br  want $WantBranch"
    git -C $Git status -sb
    $add = @('scripts', 'functional modules', 'supportive modules', 'VeritasIntelligenceAnalytics') |
        Where-Object { Test-Path -LiteralPath (Join-Path $Git $_) }
    if ($add.Count -gt 0) { git -C $Git add -- $add }
    if (git -C $Git status --porcelain) {
        git -C $Git commit -m 'VIA Central Governance 2026-09-06 hive prune transcode fetch runSeal'
        git -C $Git push -u origin HEAD
        if ($LASTEXITCODE -eq 0) { Lamp 'GREEN' 'PUSH' "已推 $br → origin" } else { Lamp 'YELLOW' 'PUSH' '失敗 · gh auth login 後重跑' }
    }
    else {
        git -C $Git push -u origin HEAD
        Lamp 'GREEN' 'PUSH' '工作區乾淨 · 已對帳 origin'
    }
    git -C $Git log -1 --oneline
}
else {
    Lamp 'YELLOW' 'GitHub' 'C:\Users\tonyk\movies-dataset 無 .git · 不 init'
}

$vdf = Join-Path $Code 'functional modules\VDF'
$inv = Join-Path $vdf 'Invoke-VDF.ps1'
$fet = Join-Path $vdf 'Invoke-VDF-Fetch.ps1'
$con = Join-Path $Code 'scripts\VIA-Launch-Console.ps1'
Lamp $(if (Test-Path $vdf) { 'GREEN' } else { 'YELLOW' }) 'VDF' $vdf
Lamp $(if (Test-Path (Join-Path $Code 'functional modules\VRN')) { 'GREEN' } else { 'YELLOW' }) 'VRN' 'functional modules\VRN'
if (Test-Path $con) { & $con }
if (Test-Path $inv) { Write-Host '--- Invoke-VDF ---'; & $inv status }
if (Test-Path $fet) { Write-Host '--- Fetch 禁網 ---'; & $fet status }
Lamp 'YELLOW' 'NEXT' 'LIVE 雙閘才補 2023 · 勿重做 DCT01-20'
Write-Host 'GREEN   ACTIVATE DONE' -ForegroundColor Green
Get-Location | Format-List
