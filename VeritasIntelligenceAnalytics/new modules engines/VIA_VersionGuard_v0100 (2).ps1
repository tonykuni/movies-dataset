#requires -Version 7.0
param(
    [string]$ToolsDir = 'C:\VeritasIntelligenceAnalytics\CGE',
    [switch]$Quarantine,
    [switch]$Recurse,
    [switch]$NoBrowser
)

# ============================================================
# VIA Version Guard v0100
#
# 同一支工具留著兩個版本，遲早會執行到舊的那個 —— 而且不會有人發現，
# 因為兩者的報告長得一模一樣，只有日誌第一行的版本號不同。
#
# 這支的工作很單純：找出同族的多個版本，只留最高版，其餘搬進
# _superseded\ 讓它跑不到。預設 dry-run，-Quarantine 才真的搬。
#
# 一條安全規則：**新版本自己要能通過語法解析，才准把舊版收走。**
# 否則等於把唯一能跑的東西藏起來。
#
# 執行：pwsh -NoProfile -ExecutionPolicy Bypass -File "<this file>" -ToolsDir <資料夾>
# ============================================================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Script:Stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')

function Get-VersionRank {
    param([string]$Name)
    $m = [regex]::Match($Name, '[vV](\d{2,4})([A-Za-z]?)')
    if (-not $m.Success) { return 0 }
    $num = [int]$m.Groups[1].Value
    $suffix = 0
    if ($m.Groups[2].Value) { $suffix = [int][char]($m.Groups[2].Value.ToUpperInvariant()[0]) - 64 }
    return ($num * 100) + $suffix
}

function Get-FamilyKey {
    param([string]$Name)
    $base = [regex]::Replace($Name, '\.(ps1|psm1|py|pyw)$', '', 'IgnoreCase')
    $base = [regex]::Replace($base, '[ _-]?\(\d+\)', '')
    $base = [regex]::Replace($base, '\s*-\s*複製', '')
    $base = [regex]::Replace($base, '[_-]?v\d{2,4}[A-Za-z]?', '', 'IgnoreCase')
    $base = [regex]::Replace($base, '_\d{8}(_\d{6})?', '')
    return ([regex]::Replace($base, '[^A-Za-z0-9]', '')).ToLowerInvariant()
}

function Test-Parses {
    param([string]$Path)
    $ext = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
    if ($ext -eq '.ps1' -or $ext -eq '.psm1') {
        $tokens = $null
        $errs = $null
        try {
            $null = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errs)
            return ($null -eq $errs -or $errs.Count -eq 0)
        } catch { return $false }
    }
    if ($ext -eq '.py' -or $ext -eq '.pyw') {
        $py = Get-Command 'python' -ErrorAction SilentlyContinue
        if ($null -eq $py) { $py = Get-Command 'python3' -ErrorAction SilentlyContinue }
        if ($null -eq $py) { return $true }          # 沒有 python 就不評斷，視為可用
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $py.Source
        $psi.Arguments = ('-m py_compile "' + $Path + '"')
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $false
        $psi.RedirectStandardError = $false
        $psi.CreateNoWindow = $true
        try {
            $proc = [System.Diagnostics.Process]::Start($psi)
            if (-not $proc.WaitForExit(20000)) { $proc.Kill($true); return $false }
            return ($proc.ExitCode -eq 0)
        } catch { return $false }
    }
    return $true
}

if (-not (Test-Path -LiteralPath $ToolsDir)) {
    Write-Host ('資料夾不存在：' + $ToolsDir) -ForegroundColor Red
    return
}

Write-Host ''
Write-Host '  VIA VERSION GUARD v0100' -ForegroundColor Cyan
Write-Host ('  ' + $ToolsDir) -ForegroundColor DarkGray
Write-Host ''

$searchArgs = @{ LiteralPath = $ToolsDir; File = $true; ErrorAction = 'SilentlyContinue' }
if ($Recurse) { $searchArgs['Recurse'] = $true }
$files = @(Get-ChildItem @searchArgs |
    Where-Object { $_.Extension -match '(?i)^\.(ps1|psm1|py|pyw)$' } |
    Where-Object { $_.FullName -notmatch '(?i)[\\/]_superseded[\\/]' })

if ($files.Count -eq 0) {
    Write-Host '  沒有找到任何腳本' -ForegroundColor Yellow
    return
}

$families = @{}
foreach ($file in $files) {
    $key = Get-FamilyKey -Name $file.Name
    if (-not $key) { continue }
    if (-not $families.ContainsKey($key)) { $families[$key] = [System.Collections.Generic.List[object]]::new() }
    $families[$key].Add([pscustomobject]@{
        name = $file.Name; path = $file.FullName
        rank = (Get-VersionRank -Name $file.Name)
        mtime = $file.LastWriteTime
        size = $file.Length
    })
}

$rows = [System.Collections.Generic.List[object]]::new()
$moved = 0
$blocked = 0
$multiFamilies = 0

foreach ($key in ($families.Keys | Sort-Object)) {
    $members = @($families[$key] | Sort-Object -Property @{ e = 'rank'; desc = $true }, @{ e = 'mtime'; desc = $true })
    if ($members.Count -lt 2) { continue }
    $multiFamilies++
    $keep = $members[0]
    $keepOk = Test-Parses -Path $keep.path

    Write-Host ('  [' + $key + ']') -ForegroundColor White
    foreach ($member in $members) {
        $role = 'SUPERSEDED'
        $action = ''
        if ($member.path -eq $keep.path) {
            $role = 'CURRENT'
            $action = $(if ($keepOk) { '保留' } else { '保留（但語法解析未通過）' })
        } elseif (-not $keepOk) {
            # 最高版自己壞掉時，絕不收走舊版 —— 那是唯一還能跑的東西
            $role = 'KEPT_AS_FALLBACK'
            $action = '最高版無法解析，保留此版作為後援'
            $blocked++
        } elseif ($Quarantine) {
            $dest = Join-Path (Split-Path -Path $member.path -Parent) '_superseded'
            if (-not (Test-Path -LiteralPath $dest)) { New-Item -Path $dest -ItemType Directory -Force | Out-Null }
            Move-Item -LiteralPath $member.path -Destination (Join-Path $dest $member.name) -Force
            $action = '已搬移到 _superseded\'
            $moved++
        } else {
            $action = '[DRY] 將搬移到 _superseded\'
        }
        $color = 'DarkYellow'
        if ($role -eq 'CURRENT') { $color = 'Green' }
        if ($role -eq 'KEPT_AS_FALLBACK') { $color = 'Red' }
        Write-Host ('    ' + $role.PadRight(18) + $member.name.PadRight(52) + $action) -ForegroundColor $color
        $rows.Add([pscustomobject]@{
            family = $key; role = $role; name = $member.name
            rank = $member.rank; mtime = $member.mtime.ToString('yyyy-MM-dd HH:mm')
            action = $action; path = $member.path
        })
    }
    Write-Host ''
}

if ($multiFamilies -eq 0) {
    Write-Host '  沒有同族多版本 —— 每支工具都只有一個版本' -ForegroundColor Green
}

$reportDir = Join-Path $ToolsDir '_versionguard'
if (-not (Test-Path -LiteralPath $reportDir)) { New-Item -Path $reportDir -ItemType Directory -Force | Out-Null }
$jsonPath = Join-Path $reportDir ('versionguard_' + $Script:Stamp + '.json')
[System.IO.File]::WriteAllText($jsonPath, (([ordered]@{
    guard = 'VIA_VersionGuard'; version = 'v0100'; stamp = $Script:Stamp
    tools_dir = $ToolsDir; scanned = $files.Count
    families_with_multiple = $multiFamilies
    quarantined = $moved; kept_as_fallback = $blocked
    committed = $Quarantine.IsPresent
    rows = @($rows)
} | ConvertTo-Json -Depth 5)), [System.Text.UTF8Encoding]::new($false))

Write-Host '  ============================================================' -ForegroundColor DarkGray
Write-Host ('   同族多版本 ' + $multiFamilies + ' 組｜已搬移 ' + $moved + '｜因新版壞掉而保留 ' + $blocked)
if (-not $Quarantine -and $multiFamilies -gt 0) {
    Write-Host '   這是 DRY-RUN。加 -Quarantine 才會真的把舊版收走。' -ForegroundColor Yellow
}
Write-Host ('   報告：' + $jsonPath) -ForegroundColor DarkCyan
Write-Host '  ============================================================' -ForegroundColor DarkGray
