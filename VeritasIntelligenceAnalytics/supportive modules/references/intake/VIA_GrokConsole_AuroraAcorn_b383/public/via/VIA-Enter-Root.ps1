#requires -Version 7.0
# VIA · 先進入專案環境（母系統根 + via_vdf）
# 貼在 PS>。不要貼 cmd。不要 cd /d。
# 政策: 不刪、不卸載、不殺行程、不 exit、禁網、via_iso_* 不混 base
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Lamp([string]$c, [string]$layer, [string]$msg) {
    $col = switch ($c) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'GREY' { 'DarkGray' } default { 'Yellow' } }
    Write-Host ('{0,-7} {1,-12} {2}' -f $c, $layer, $msg) -ForegroundColor $col
}

function Enter-ViaProject {
    $roots = @(
        'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics'
    )
    $root = $roots | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $root) {
        Lamp 'RED' 'ENTER' '找不到母系統 VeritasIntelligenceAnalytics'
        $roots | ForEach-Object { Lamp 'GREY' 'CAND' $_ }
        return $false
    }
    Set-Location -LiteralPath $root
    $env:PYTHONNOUSERSITE = '1'
    $env:VIA_LKGC = '2026-09-06'
    $env:VIA_START_YEAR = '2023'
    $env:VIA_NET = '0'
    $env:VIA_ROOT = $root

    $vdfHome = @(
        "$env:USERPROFILE\miniconda3\envs\via_vdf",
        "$env:USERPROFILE\anaconda3\envs\via_vdf",
        "$env:USERPROFILE\Miniconda3\envs\via_vdf",
        'C:\Users\tonyk\miniconda3\envs\via_vdf',
        'C:\Users\tonyk\anaconda3\envs\via_vdf',
        'C:\Users\tonyk\Miniconda3\envs\via_vdf'
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

    if ($vdfHome) {
        $env:CONDA_PREFIX = $vdfHome
        $env:CONDA_DEFAULT_ENV = 'via_vdf'
        $env:PATH = "$vdfHome;$vdfHome\Scripts;$vdfHome\Library\bin;" + $env:PATH
        Lamp 'GREEN' 'ENV' "via_vdf  $vdfHome"
    }
    else {
        Lamp 'YELLOW' 'ENV' 'via_vdf 未見 · 不 conda create · 不混 base'
    }

    Lamp 'GREEN' 'ENTER' $root
    Lamp 'GREEN' 'PATH' "LKGC $($env:VIA_LKGC) · 起始年 $($env:VIA_START_YEAR) · 網 $($env:VIA_NET) · via_iso_* 不刪"
    Lamp 'GREEN' 'CWD' (Get-Location).Path
    return $true
}

$ok = Enter-ViaProject
if (-not $ok) { return }
Get-Location | Format-List
Write-Host 'GREEN   已在專案環境 · 下一步跑 VIA-Ingest-2023.ps1 或 Invoke-VDF' -ForegroundColor Green
