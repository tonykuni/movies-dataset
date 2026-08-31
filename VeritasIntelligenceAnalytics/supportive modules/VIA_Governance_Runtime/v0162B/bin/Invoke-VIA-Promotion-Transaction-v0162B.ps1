#requires -Version 7.0
<#
VIA v0162B · Canonical Promotion Transaction · 正式版晉升單程序
================================================================
The separate hash-locked, operator-reviewed transaction required by the
VRN / VDF / VAP promotion gates. This is the ONLY sanctioned path for writing
a sandbox repair candidate back into a canonical tree.

Contract enforced here:
  1. 操作員審查 Operator review — nothing is promoted unless explicitly named
     in -Approve (or -Approve ALL). Default invocation only lists candidates.
  2. Exact-hash gate — the canonical target must still match the candidate's
     recorded original_sha256, and the sandbox copy must match its recorded
     sandbox_sha256, byte for byte, or that item is refused.
  3. Backup — the canonical file is copied into the transaction's backup
     directory (hash recorded) before it is replaced.
  4. Hash-chain — every transaction appends a record to promotion_chain.json;
     each record's chain_hash = SHA-256(prev_chain_hash + record JSON), so the
     ledger is tamper-evident from the genesis record onward.

Usage 用法:
  # 審查 review (no writes)
  ./Invoke-VIA-Promotion-Transaction-v0162B.ps1 -Base <Base> -RunDir <run>
  # 演練 dry run (all gates, no writes)
  ./Invoke-VIA-Promotion-Transaction-v0162B.ps1 -Base <Base> -RunDir <run> -Approve ALL -DryRun
  # 晉升 promote (writes canonical + backup + ledger)
  ./Invoke-VIA-Promotion-Transaction-v0162B.ps1 -Base <Base> -RunDir <run> -Approve <relative path>[,<relative path>...]
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Base,
    [Parameter(Mandatory)][string]$RunDir,
    [string[]]$Approve = @(),
    [switch]$DryRun
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-VIALog {
    param([Parameter(Mandatory)][string]$Message, [string]$Color = 'Gray')
    Write-Host ('[{0}] {1}' -f [DateTime]::Now.ToString('HH:mm:ss'), $Message) -ForegroundColor $Color
}

function Get-VIAFileSha {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-VIATextSha {
    param([Parameter(Mandatory)][string]$Text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $hash = [System.Security.Cryptography.SHA256]::HashData($bytes)
    return ([System.BitConverter]::ToString($hash) -replace '-', '').ToLowerInvariant()
}

$Base = (Resolve-Path -LiteralPath $Base).Path
$RunDir = (Resolve-Path -LiteralPath $RunDir).Path
$manifestPath = Join-Path -Path $RunDir -ChildPath 'deployment_candidates/deployment_manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw ('Deployment manifest not found: ' + $manifestPath)
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$candidates = @($manifest.candidates)

Write-Host ''
Write-Host 'VIA v0162B · CANONICAL PROMOTION TRANSACTION' -ForegroundColor Cyan
Write-VIALog -Message ('BASE   : ' + $Base) -Color DarkCyan
Write-VIALog -Message ('RUNDIR : ' + $RunDir) -Color DarkCyan
Write-VIALog -Message ('CANDIDATES : ' + @($candidates).Count) -Color DarkCyan

$rows = @()
$index = 0
foreach ($candidate in $candidates) {
    $index = $index + 1
    $originalPath = [string]$candidate.original_path
    $relative = $originalPath
    if ($originalPath.StartsWith($Base)) {
        $relative = $originalPath.Substring($Base.Length).TrimStart('/', '\')
    }
    $rows += [pscustomobject]@{
        Index = $index
        Relative = $relative
        Candidate = $candidate
    }
    Write-Host ''
    Write-Host ('  [' + $index + '] ' + $relative) -ForegroundColor White
    Write-Host ('      subsystem=' + $candidate.subsystem + ' · round=' + $candidate.round + ' · type=' + $candidate.repair_type)
    Write-Host ('      original sha256 ' + $candidate.original_sha256)
    Write-Host ('      sandbox  sha256 ' + $candidate.sandbox_sha256)
}

$approveList = @()
foreach ($raw in $Approve) {
    foreach ($piece in ([string]$raw).Split(',')) {
        $trimmed = $piece.Trim()
        if ($trimmed.Length -gt 0) { $approveList += $trimmed }
    }
}
$Approve = $approveList

if (@($Approve).Count -eq 0) {
    Write-Host ''
    Write-VIALog -Message 'REVIEW ONLY: no -Approve given, nothing promoted. Re-run with -Approve <relative path>[,...] or -Approve ALL (add -DryRun to rehearse).' -Color Yellow
    return
}

$approveAll = @($Approve | Where-Object { $_ -ieq 'ALL' }).Count -gt 0
$selected = @()
foreach ($row in $rows) {
    if ($approveAll) { $selected += $row; continue }
    foreach ($wanted in $Approve) {
        if ($row.Relative -ieq ([string]$wanted).Trim()) { $selected += $row; break }
    }
}
if (-not $approveAll) {
    foreach ($wanted in $Approve) {
        $hit = @($rows | Where-Object { $_.Relative -ieq ([string]$wanted).Trim() }).Count
        if ($hit -eq 0) { throw ('-Approve item not found among candidates: ' + $wanted) }
    }
}
if (@($selected).Count -eq 0) { throw 'No candidates selected for promotion.' }

$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$promotionRoot = Join-Path -Path $Base -ChildPath 'supportive modules/VIA_Governance_Runtime/v0162B/promotion'
$backupRoot = Join-Path -Path $promotionRoot -ChildPath ('backup/' + $stamp)
$ledgerPath = Join-Path -Path $promotionRoot -ChildPath 'promotion_chain.json'

$items = @()
foreach ($row in $selected) {
    $candidate = $row.Candidate
    $canonical = [string]$candidate.original_path
    $sandbox = [string]$candidate.sandbox_path
    Write-Host ''
    Write-VIALog -Message ('PROMOTE GATE : ' + $row.Relative) -Color Cyan
    if (-not (Test-Path -LiteralPath $canonical -PathType Leaf)) {
        throw ('Canonical target missing: ' + $canonical)
    }
    if (-not (Test-Path -LiteralPath $sandbox -PathType Leaf)) {
        throw ('Sandbox candidate missing: ' + $sandbox)
    }
    $canonicalSha = Get-VIAFileSha -Path $canonical
    if ($canonicalSha -ne [string]$candidate.original_sha256) {
        throw ('EXACT-HASH GATE REFUSED for ' + $row.Relative + ': canonical has drifted since the run. Expected=' + $candidate.original_sha256 + ' Actual=' + $canonicalSha + '. Re-run the engine and review again.')
    }
    $sandboxSha = Get-VIAFileSha -Path $sandbox
    if ($sandboxSha -ne [string]$candidate.sandbox_sha256) {
        throw ('EXACT-HASH GATE REFUSED for ' + $row.Relative + ': sandbox candidate does not match its recorded hash. Expected=' + $candidate.sandbox_sha256 + ' Actual=' + $sandboxSha)
    }
    Write-VIALog -Message 'OK  exact-hash gate (canonical + sandbox)' -Color Green
    if ($DryRun.IsPresent) {
        Write-VIALog -Message 'DRYRUN : gates passed, no write performed.' -Color Yellow
        $items += [ordered]@{ relative = $row.Relative; dry_run = $true; original_sha256 = $canonicalSha; promoted_sha256 = $sandboxSha }
        continue
    }
    $backupPath = Join-Path -Path $backupRoot -ChildPath ($row.Relative -replace '\\', '/')
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backupPath) | Out-Null
    Copy-Item -LiteralPath $canonical -Destination $backupPath -Force
    $backupSha = Get-VIAFileSha -Path $backupPath
    if ($backupSha -ne $canonicalSha) { throw ('Backup hash mismatch for ' + $row.Relative) }
    Write-VIALog -Message ('OK  backup → ' + $backupPath) -Color Green
    Copy-Item -LiteralPath $sandbox -Destination $canonical -Force
    $promotedSha = Get-VIAFileSha -Path $canonical
    if ($promotedSha -ne $sandboxSha) { throw ('Post-promotion hash mismatch for ' + $row.Relative) }
    Write-VIALog -Message ('OK  promoted, canonical sha256 now ' + $promotedSha) -Color Green
    $items += [ordered]@{
        relative = $row.Relative
        dry_run = $false
        original_sha256 = $canonicalSha
        promoted_sha256 = $promotedSha
        backup_path = $backupPath
        backup_sha256 = $backupSha
        repair_type = [string]$candidate.repair_type
        subsystem = [string]$candidate.subsystem
    }
}

if ($DryRun.IsPresent) {
    Write-Host ''
    Write-VIALog -Message ('DRYRUN COMPLETE : ' + @($items).Count + ' candidate(s) passed every gate; nothing written.') -Color Cyan
    return
}

$ledger = @()
if (Test-Path -LiteralPath $ledgerPath -PathType Leaf) {
    $ledger = @(Get-Content -LiteralPath $ledgerPath -Raw | ConvertFrom-Json)
}
$previousHash = 'GENESIS'
if (@($ledger).Count -gt 0) {
    $previousHash = [string]$ledger[-1].chain_hash
}
$record = [ordered]@{
    seq = @($ledger).Count + 1
    timestamp_utc = $stamp
    run_dir = $RunDir
    items = $items
    prev_chain_hash = $previousHash
}
$recordJson = $record | ConvertTo-Json -Depth 6 -Compress
$record['chain_hash'] = Get-VIATextSha -Text ($previousHash + $recordJson)
$ledger = @($ledger) + @([pscustomobject]$record)
New-Item -ItemType Directory -Force -Path $promotionRoot | Out-Null
$ledger | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ledgerPath -Encoding UTF8
Write-Host ''
Write-VIALog -Message ('TRANSACTION SEALED : seq ' + $record['seq'] + ' · chain_hash ' + ([string]$record['chain_hash']).Substring(0, 16) + '… · ledger ' + $ledgerPath) -Color Cyan
Write-VIALog -Message ('PROMOTION COMPLETE : ' + @($items).Count + ' file(s) promoted with backup + hash-chain.') -Color Cyan

