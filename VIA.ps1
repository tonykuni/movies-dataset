#requires -Version 7.0
<#
VIA · 統一主控 · One PowerShell to integrate all (repo-resident edition)
========================================================================
本檔案住在 repo 裡:git pull 之後永遠是最新版,不需下載附件。

日常一鍵(整合啟動 VRN / VDF / VAP / 支援性工具):
  pwsh -NoProfile -ExecutionPolicy Bypass -File "$HOME\Downloads\movies-dataset\VIA.ps1"

動作(-Do,可多選,預設 StartAll):
  StartAll  ★六流程整合:Sync → QA → UI(AutoPlot 工作台)→ Launch(三輪全景
            分析,涵蓋 VRN / VDF / VAP / SUPPORTIVE,20 加速器,結束開矩陣)
  Sync      GitHub 拉最新 + 套件安裝到 Base
  Install   只把套件從 repo 複製到 Base(不拉 GitHub)
  QA        套件 AST + roundtrip 驗證
  UI        產生並開啟 AutoPlot Workbench(v0162C 格式)
  Plot      VeritasAutoPlot CLI(-PlotArgs '--list' / '--auto' / '--table t --left a --right b')
  Launch    SHA 閘門 + AST 閘門 → AllInOne 三輪分析
  Promote   canonical 晉升單程序(需 -RunDir;-ApprovePromotion / -PromoteDryRun)

參數:-Base(預設 C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics)、
      -UiOnly、-NoOpenHtml、-PlotArgs、-RunDir、-ApprovePromotion、-PromoteDryRun
#>
[CmdletBinding()]
param(
    [string]$Base = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics',
    [string[]]$Do = @('StartAll'),
    [switch]$UiOnly,
    [switch]$NoOpenHtml,
    [string]$PlotArgs = '--list',
    [string]$RunDir = '',
    [string[]]$ApprovePromotion = @(),
    [switch]$PromoteDryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoPath = $PSScriptRoot
$FeatureBranch = 'claude/via-system-integration-completion-k2lf85'
$PackageName = 'VeritasIntelligenceAnalytics'
$AllInOneRelative = 'supportive modules/VIA_Governance_Runtime/v0162B/bin/Invoke-VIA-SystemManager-AllInOne-v0162B.ps1'
$QaRelative = 'supportive modules/VIA_Governance_Runtime/v0162B/qa/Invoke-VIA-QA-AST-v0162B.ps1'
$QaOutRelative = 'supportive modules/VIA_Governance_Runtime/v0162B/qa/evidence/master_qa_results.json'
$PromoteToolRelative = 'supportive modules/VIA_Governance_Runtime/v0162B/bin/Invoke-VIA-Promotion-Transaction-v0162B.ps1'
$AutoPlotRelative = 'functional modules/VAP/engine/via_autoplot_engine_v001.py'

function Write-VIALog {
    param([Parameter(Mandatory)][string]$Message, [string]$Color = 'Gray')
    Write-Host ('[{0}] {1}' -f [DateTime]::Now.ToString('HH:mm:ss'), $Message) -ForegroundColor $Color
}

function ConvertTo-VIATarget {
    param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][string]$Relative)
    $separator = [string][System.IO.Path]::DirectorySeparatorChar
    return Join-Path -Path $Root -ChildPath ($Relative.Replace('/', $separator))
}

function Get-VIAFileSha {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-VIAPython {
    foreach ($candidate in @('py', 'python3', 'python')) {
        if ($null -ne (Get-Command -Name $candidate -ErrorAction SilentlyContinue)) { return $candidate }
    }
    throw 'Python not found on PATH (need py / python3 / python).'
}

function Invoke-VIAPy {
    param([Parameter(Mandatory)][string[]]$Arguments)
    $python = Get-VIAPython
    $argv = @()
    if ($python -eq 'py') { $argv += '-3' }
    $argv += $Arguments
    & $python @argv
    if ($LASTEXITCODE -ne 0) { throw ('python exited ' + $LASTEXITCODE) }
}

function Install-VIAPackage {
    $source = Join-Path -Path $RepoPath -ChildPath $PackageName
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw ('Package folder missing in repo: ' + $source)
    }
    New-Item -ItemType Directory -Force -Path $Base | Out-Null
    Copy-Item -Path (Join-Path -Path $source -ChildPath '*') -Destination $Base -Recurse -Force
    Write-VIALog -Message ('OK  package installed from repo → ' + $Base) -Color Green
}

function Sync-VIA {
    Write-Host ''
    Write-VIALog -Message 'SYNC → git pull + package install' -Color Cyan
    if ($null -eq (Get-Command -Name git -ErrorAction SilentlyContinue)) {
        throw 'git not found on PATH.'
    }
    git -C $RepoPath pull origin $FeatureBranch
    if ($LASTEXITCODE -ne 0) { throw 'git pull failed — check network/credentials, then re-run.' }
    Install-VIAPackage
    Write-VIALog -Message 'SYNC COMPLETE' -Color Cyan
}

function Invoke-VIAQa {
    Write-Host ''
    Write-VIALog -Message 'QA → package AST + roundtrip suite' -Color Cyan
    $qaScript = ConvertTo-VIATarget -Root $Base -Relative $QaRelative
    if (-not (Test-Path -LiteralPath $qaScript -PathType Leaf)) {
        throw ('QA script missing: ' + $qaScript + '. Run -Do Sync first.')
    }
    $qaOut = ConvertTo-VIATarget -Root $Base -Relative $QaOutRelative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $qaOut) | Out-Null
    & $qaScript -PackageRoot $Base -OutputJson $qaOut
    $qaExit = 0
    if (Test-Path -Path variable:LASTEXITCODE) { $qaExit = [int]$LASTEXITCODE }
    if ($qaExit -ne 0) { throw ('QA FAIL (exit ' + $qaExit + '). Details: ' + $qaOut) }
    Write-VIALog -Message ('QA COMPLETE : ' + $qaOut) -Color Cyan
}

function Open-VIAWorkbench {
    Write-Host ''
    Write-VIALog -Message 'UI → AutoPlot Workbench (v0162C format)' -Color Cyan
    $engine = ConvertTo-VIATarget -Root $Base -Relative $AutoPlotRelative
    if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) {
        throw ('AutoPlot engine missing: ' + $engine + '. Run -Do Sync first.')
    }
    Invoke-VIAPy -Arguments @($engine, '--base', $Base, '--ui')
    $workbench = Join-Path -Path $Base -ChildPath 'VAP/output/VAP_Workbench.html'
    Write-VIALog -Message ('UI COMPLETE : ' + $workbench) -Color Cyan
    if (-not $NoOpenHtml.IsPresent) {
        try { Start-Process $workbench } catch { Write-VIALog -Message 'Open the workbench above in your browser.' -Color Yellow }
    }
}

function Invoke-VIAPlot {
    Write-Host ''
    Write-VIALog -Message ('PLOT → VeritasAutoPlot ' + $PlotArgs) -Color Cyan
    $engine = ConvertTo-VIATarget -Root $Base -Relative $AutoPlotRelative
    if (-not (Test-Path -LiteralPath $engine -PathType Leaf)) {
        throw ('AutoPlot engine missing: ' + $engine + '. Run -Do Sync first.')
    }
    $arguments = @($engine, '--base', $Base)
    foreach ($piece in ($PlotArgs -split '\s+')) {
        if ($piece.Length -gt 0) { $arguments += $piece }
    }
    Invoke-VIAPy -Arguments $arguments
    $index = Join-Path -Path $Base -ChildPath 'VAP/output/index.html'
    if ((-not $NoOpenHtml.IsPresent) -and (Test-Path -LiteralPath $index -PathType Leaf)) {
        try { Start-Process $index } catch { Write-VIALog -Message 'Open the index above in your browser.' -Color Yellow }
    }
}

function Invoke-VIALaunch {
    Write-Host ''
    Write-VIALog -Message 'LAUNCH → exact-SHA gate + AST gate + AllInOne 三輪全景(VRN/VDF/VAP/SUPPORTIVE)' -Color Cyan
    $allInOne = ConvertTo-VIATarget -Root $Base -Relative $AllInOneRelative
    $repoCopy = ConvertTo-VIATarget -Root (Join-Path -Path $RepoPath -ChildPath $PackageName) -Relative $AllInOneRelative
    if (-not (Test-Path -LiteralPath $allInOne -PathType Leaf)) {
        throw ('AllInOne launcher missing: ' + $allInOne + '. Run -Do Sync first.')
    }
    $expected = Get-VIAFileSha -Path $repoCopy
    $actual = Get-VIAFileSha -Path $allInOne
    if ($actual -ne $expected) {
        throw ('AllInOne SHA-256 mismatch vs repo authority. Expected=' + $expected + ' Actual=' + $actual + '. Run -Do Sync to repair.')
    }
    Write-VIALog -Message ('OK  exact-SHA gate : ' + $expected.Substring(0, 12) + '…') -Color Green
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($allInOne, [ref]$tokens, [ref]$parseErrors) | Out-Null
    if (@($parseErrors).Count -gt 0) {
        foreach ($parseError in @($parseErrors)) {
            Write-VIALog -Message ('AST line {0}: {1}' -f $parseError.Extent.StartLineNumber, $parseError.Message) -Color Red
        }
        throw 'AllInOne AST validation failed.'
    }
    Write-VIALog -Message 'OK  Microsoft AST gate' -Color Green
    $extra = @{}
    if ($UiOnly.IsPresent) { $extra['UiOnly'] = $true }
    if ($NoOpenHtml.IsPresent) { $extra['NoOpenHtml'] = $true }
    & $allInOne -Base $Base @extra
}

function Invoke-VIAPromote {
    Write-Host ''
    Write-VIALog -Message 'PROMOTE → canonical promotion transaction' -Color Cyan
    if ([string]::IsNullOrWhiteSpace($RunDir)) {
        throw 'Promote requires -RunDir <engine run directory>.'
    }
    $tool = ConvertTo-VIATarget -Root $Base -Relative $PromoteToolRelative
    if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) {
        throw ('Promotion tool missing: ' + $tool + '. Run -Do Sync first.')
    }
    $extra = @{}
    if (@($ApprovePromotion).Count -gt 0) { $extra['Approve'] = $ApprovePromotion }
    if ($PromoteDryRun.IsPresent) { $extra['DryRun'] = $true }
    & $tool -Base $Base -RunDir $RunDir @extra
}

Write-Host ''
Write-Host 'VIA · MASTER (repo edition) · VRN / VDF / VAP / SUPPORTIVE' -ForegroundColor Cyan

$ValidActions = @('StartAll', 'Sync', 'Install', 'QA', 'UI', 'Plot', 'Launch', 'Promote')
$requested = [System.Collections.Generic.List[string]]::new()
foreach ($raw in $Do) {
    foreach ($piece in ([string]$raw).Split(',')) {
        $name = $piece.Trim()
        if ($name.Length -eq 0) { continue }
        $match = $ValidActions | Where-Object { $_ -ieq $name }
        if ($null -eq $match) {
            throw ('Unknown -Do action "' + $name + '". Valid: ' + ($ValidActions -join ', '))
        }
        $requested.Add([string]$match)
    }
}
if ($requested.Count -eq 0) { $requested.Add('StartAll') }

$plan = [System.Collections.Generic.List[string]]::new()
foreach ($action in $requested) {
    if ($action -eq 'StartAll') {
        foreach ($step in @('Sync', 'QA', 'UI', 'Launch')) {
            if (-not $plan.Contains($step)) { $plan.Add($step) }
        }
    }
    elseif (-not $plan.Contains($action)) { $plan.Add($action) }
}
Write-VIALog -Message ('PLAN : ' + ($plan -join ' → ')) -Color DarkCyan

foreach ($action in $plan) {
    switch ($action) {
        'Sync' { Sync-VIA }
        'Install' { Install-VIAPackage }
        'QA' { Invoke-VIAQa }
        'UI' { Open-VIAWorkbench }
        'Plot' { Invoke-VIAPlot }
        'Launch' { Invoke-VIALaunch }
        'Promote' { Invoke-VIAPromote }
    }
}

Write-Host ''
Write-VIALog -Message ('MASTER COMPLETE : ' + ($plan -join ', ')) -Color Cyan
