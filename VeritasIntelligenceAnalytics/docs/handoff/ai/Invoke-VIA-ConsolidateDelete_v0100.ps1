<#
.SYNOPSIS
  VIA 整合只留一版(政策 L130)— 桌機同步刪除:照 VCGC 產出的刪除批清單,把本機 VIA 樹裡同一批檔刪掉。

.DESCRIPTION
  預設乾跑:只列出會刪哪些檔,不刪任何東西。核對清單無誤後加 -Apply 才真的刪。
  每一列都過三道檢查,任何一道不過就跳過、不刪:
    1. 要刪的檔在本機存在
    2. 本機檔的 SHA-256 與清單記錄相同(內容不同 = 本機有改過,不刪)
    3. 清單指定的「保留檔」在本機存在
  刪除只動清單上的檔,不碰其他檔;VRN-1 倉(倉外)不在清單內。
  刪後結果寫到 <Root>\VIA_Reports\consolidate\desktop_delete_<批>_<時間>.json。

.PARAMETER Root
  本機 VIA 根(含 functional modules / supportive modules 的那一層,例如 ...\VeritasIntelligenceAnalytics)。

.PARAMETER Batch
  刪除批清單路徑;預設 <Root>\docs\handoff\ai\VIA_Consolidate_Batch_20261113_01.json。

.PARAMETER Apply
  加上才真的刪;不加 = 乾跑。

.EXAMPLE
  pwsh -File .\Invoke-VIA-ConsolidateDelete_v0100.ps1 -Root "D:\VIA\VeritasIntelligenceAnalytics"
  pwsh -File .\Invoke-VIA-ConsolidateDelete_v0100.ps1 -Root "D:\VIA\VeritasIntelligenceAnalytics" -Apply
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Root,
    [string]$Batch,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw "找不到 VIA 根:$Root" }
if (-not $Batch) { $Batch = Join-Path $Root 'docs\handoff\ai\VIA_Consolidate_Batch_20261113_01.json' }
if (-not (Test-Path -LiteralPath $Batch -PathType Leaf)) { throw "找不到刪除批清單:$Batch(先 git pull 取得)" }

$manifest = Get-Content -LiteralPath $Batch -Raw -Encoding UTF8 | ConvertFrom-Json
$mode = if ($Apply) { 'APPLY(真的刪)' } else { '乾跑(只列清單)' }
Write-Host "[VIA 整合刪除] 批 $($manifest.batch) · $($manifest.count) 列 · 模式 $mode" -ForegroundColor Cyan

$results = @()
foreach ($row in $manifest.rows) {
    $target = Join-Path $Root ($row.path -replace '/', '\')
    $keep = Join-Path $Root ($row.keep -replace '/', '\')
    $state = ''
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        $state = '本機沒有(已刪或不存在)'
    } elseif (-not (Test-Path -LiteralPath $keep -PathType Leaf)) {
        $state = '跳過:保留檔不在本機'
    } else {
        $sha = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($sha -ne $row.sha256) {
            $state = '跳過:內容與清單不同(本機改過)'
        } elseif ($Apply) {
            Remove-Item -LiteralPath $target -Force
            $state = '已刪'
        } else {
            $state = '會刪(乾跑)'
        }
    }
    $color = if ($state -like '跳過*') { 'Yellow' } elseif ($state -eq '已刪' -or $state -like '會刪*') { 'Green' } else { 'DarkGray' }
    Write-Host ("  {0,-26} {1}" -f $state, $row.path) -ForegroundColor $color
    $results += [pscustomobject]@{ path = $row.path; keep = $row.keep; state = $state }
}

$summary = $results | Group-Object state | ForEach-Object { "$($_.Name) $($_.Count)" }
Write-Host ("[VIA 整合刪除] " + ($summary -join ' · ')) -ForegroundColor Cyan
$outDir = Join-Path $Root 'VIA_Reports\consolidate'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$out = Join-Path $outDir ("desktop_delete_{0}_{1}.json" -f $manifest.batch, $stamp)
[pscustomobject]@{ batch = $manifest.batch; mode = $mode; at = (Get-Date).ToString('o'); rows = $results } |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "  收據:$out"
if (-not $Apply) { Write-Host '  核對無誤後加 -Apply 再跑一次才會真的刪。' -ForegroundColor Cyan }
