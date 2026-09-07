#requires -Version 7.0
<#
.SYNOPSIS
  全樹 Python 掛上 SuperAccel 加速器橋；VDF 外擷引擎加掛 NetUnified 網路工具組。

.DESCRIPTION
  正本定位（GitHub / 母系統同一相對路徑，三處 byte-identical）：
    supportive modules\VeritasCeleritas.py
    supportive modules\VeritasAegisNexus.py
  對外掛橋不直接 import 上述兩檔（避免循環與版號寫死）：
    加速器入口 = supportive modules\VIA_SuperAccel_Module.py
                 → glob 最新 SUP_MDL737_SuperAccelModule_v*.py
                 → 再委派 VeritasCeleritas
    網路入口   = supportive modules\network\via_net_unified_v*.py（最新）
                 → SUP_MDL740_NetUnified → VeritasAegisNexus
  原則：只增不減、已有橋標記則跳過、預設 DryRun、寫入前備份、語法抽檢。
  紅線：永不代設 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT。

.EXAMPLE
  # 預覽（零寫入）
  .\Invoke-VIA-AccelNetBridge-AllPy-v0100.ps1

.EXAMPLE
  # 正式寫入
  .\Invoke-VIA-AccelNetBridge-AllPy-v0100.ps1 -Apply

.EXAMPLE
  # 含 references/intake 收容件與測試檔
  .\Invoke-VIA-AccelNetBridge-AllPy-v0100.ps1 -Apply -IncludeIntake -IncludeTests
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$IncludeIntake,
    [switch]$IncludeTests,
    [switch]$SkipPyCompile,
    [string]$ViaHome = ""
)

Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# ===== [VIA:PS-ACCEL:v0100] =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    if (-not $VIAPSAccelProbe) { $VIAPSAccelProbe = (Get-Location).Path }
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path -LiteralPath $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

function Resolve-ViaHome {
    param([string]$Hint)
    $cands = [System.Collections.Generic.List[string]]::new()
    if ($Hint) { [void]$cands.Add($Hint) }
    if ($env:VIA_HOME) { [void]$cands.Add($env:VIA_HOME) }
    if ($PSScriptRoot) {
        [void]$cands.Add($PSScriptRoot)
        $parent = Split-Path $PSScriptRoot -Parent
        if ($parent) { [void]$cands.Add($parent) }
        $grand = if ($parent) { Split-Path $parent -Parent } else { $null }
        if ($grand) { [void]$cands.Add((Join-Path $grand "VeritasIntelligenceAnalytics")) }
    }
    [void]$cands.Add("C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics")
    [void]$cands.Add("C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics")
    foreach ($c in $cands) {
        if (-not $c) { continue }
        $cel = Join-Path $c "supportive modules\VeritasCeleritas.py"
        $aeg = Join-Path $c "supportive modules\VeritasAegisNexus.py"
        $acc = Join-Path $c "supportive modules\VIA_SuperAccel_Module.py"
        if ((Test-Path -LiteralPath $cel) -and (Test-Path -LiteralPath $aeg) -and (Test-Path -LiteralPath $acc)) {
            return (Resolve-Path -LiteralPath $c).Path
        }
    }
    return $null
}

$AccelBlock = @'
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
'@

$NetBlock = @'
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
'@

function Get-InsertIndex {
    param([string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return 0 }
    $idx = 0
    # BOM
    if ($Text.StartsWith([char]0xFEFF)) { $idx = 1 }
    $slice = $Text.Substring($idx)
    # shebang / encoding cookies at file head (repeat up to 4 lines)
    $guard = 0
    while ($guard -lt 6 -and $slice.Length -gt 0) {
        if ($slice -match '^(#![^\r\n]*\r?\n)') {
            $idx += $Matches[1].Length; $slice = $Text.Substring($idx); $guard++; continue
        }
        if ($slice -match '^(#.*coding[:=]\s*[-.\w]+[^\r\n]*\r?\n)') {
            $idx += $Matches[1].Length; $slice = $Text.Substring($idx); $guard++; continue
        }
        if ($slice -match '^(from __future__ import[^\r\n]*\r?\n)') {
            $idx += $Matches[1].Length; $slice = $Text.Substring($idx); $guard++; continue
        }
        if ($slice -match '^(# ===== \[VIA:ACCEL-BRIDGE[\s\S]*?# ===== \[VIA:ACCEL-BRIDGE:END\] =====\r?\n?)') {
            $idx += $Matches[1].Length; $slice = $Text.Substring($idx); $guard++; continue
        }
        break
    }
    # module docstring
    if ($slice -match '^(?s)([rubfRUBF]{0,3}"""[\s\S]*?"""\r?\n)') {
        $idx += $Matches[1].Length
    } elseif ($slice -match "^(?s)([rubfRUBF]{0,3}'''[\s\S]*?'''\r?\n)") {
        $idx += $Matches[1].Length
    }
    return $idx
}

function Test-IsVdfOutboundFetch {
    param([string]$Rel, [string]$Text, [string]$Name)
    $relN = $Rel -replace '/', '\'
    if ($relN -notmatch '(?i)\\functional modules\\VDF\\') { return $false }
    $denyName = @(
        'VeritasCeleritas.py', 'VeritasAegisNexus.py',
        'VIA_SuperAccel_Module.py', 'via_net_unified_', 'SUP_MDL740_NetUnified',
        'SUP_MDL737_SuperAccel'
    )
    foreach ($d in $denyName) { if ($Name -like "*$d*") { return $false } }
    if ($Name -match '(?i)(fetch|akshare|yfinance|http|download|scrape|crawler|finmind|mops|tpex|twse|fred|macro|price|yf_)') {
        return $true
    }
    if ($Text -match '(?i)(import\s+requests|from\s+requests\s+import|import\s+httpx|import\s+aiohttp|import\s+yfinance|import\s+akshare|urllib\.request|urlopen|yf\.download|http_json|http_text|VIA_NET_CONSENT)') {
        return $true
    }
    return $false
}

function Test-ShouldSkipFile {
    param([string]$Rel, [switch]$IncludeIntake, [switch]$IncludeTests)
    $relN = $Rel -replace '/', '\'
    $bits = @(
        '\__pycache__\', '\.git\', '\node_modules\', '\_FREEZE\',
        '\.venv\', '\venv\', '\_quarantine_'
    )
    foreach ($b in $bits) { if ($relN -like "*$b*") { return $true } }
    if (-not $IncludeIntake) {
        if ($relN -match '(?i)\\(references\\intake|_inbox_to_classify|SCOPE_COPY)\\') { return $true }
    }
    if (-not $IncludeTests) {
        if ($relN -match '(?i)\\tests\\' -or $Rel -match '(?i)(^|/)test_') { return $true }
    }
    $name = Split-Path $Rel -Leaf
    if ($name -match '(?i)^(VIA_SuperAccel_Module|SUP_MDL737_SuperAccelModule_v\d+|via_net_unified_v\d+|SUP_MDL740_NetUnified_v\d+)\.py$') {
        return $true
    }
    return $false
}

# -----------------------------------------------------------------------------
$viaHome = Resolve-ViaHome -Hint $ViaHome
if (-not $viaHome) {
    Write-Host "[FAIL] 找不到母系統。請確認存在：" -ForegroundColor Red
    Write-Host "  supportive modules\VeritasCeleritas.py"
    Write-Host "  supportive modules\VeritasAegisNexus.py"
    Write-Host "  supportive modules\VIA_SuperAccel_Module.py"
    exit 1
}

$celPath = Join-Path $viaHome "supportive modules\VeritasCeleritas.py"
$aegPath = Join-Path $viaHome "supportive modules\VeritasAegisNexus.py"
$accPath = Join-Path $viaHome "supportive modules\VIA_SuperAccel_Module.py"
$netDir  = Join-Path $viaHome "supportive modules\network"
$netHits = @(Get-ChildItem -LiteralPath $netDir -Filter "via_net_unified_v*.py" -ErrorAction SilentlyContinue | Sort-Object Name)
$stamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$reportRoot = Join-Path $env:USERPROFILE "VIA_Reports\accel_net_bridge_$stamp"
if (-not (Test-Path $reportRoot)) { New-Item -ItemType Directory -Path $reportRoot -Force | Out-Null }
$backupRoot = Join-Path $reportRoot "backup"
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null

Write-Host "===== VIA ACCEL + NET BRIDGE v0100 =====" -ForegroundColor Cyan
Write-Host ("VIA_HOME     : {0}" -f $viaHome)
Write-Host ("Celeritas    : {0}  ({1:N0} bytes)" -f $celPath, (Get-Item -LiteralPath $celPath).Length)
Write-Host ("AegisNexus   : {0}  ({1:N0} bytes)" -f $aegPath, (Get-Item -LiteralPath $aegPath).Length)
Write-Host ("SuperAccel   : {0}" -f $accPath)
Write-Host ("NetUnified   : {0}" -f $(if ($netHits) { $netHits[-1].Name } else { "MISSING" }))
Write-Host ("Mode         : {0}" -f $(if ($Apply) { "APPLY (will write)" } else { "DRY-RUN (zero write)" }))
Write-Host ("IncludeIntake: {0}   IncludeTests: {1}" -f [bool]$IncludeIntake, [bool]$IncludeTests)
Write-Host ("Report       : {0}" -f $reportRoot)

if (-not $netHits) {
    Write-Host "[WARN] network\via_net_unified_v*.py 缺席 — 仍會插入 NET-BRIDGE（執行期 graceful None）" -ForegroundColor Yellow
}

$allPy = @(Get-ChildItem -LiteralPath $viaHome -Recurse -Filter *.py -File -ErrorAction SilentlyContinue)
$rows = [System.Collections.Generic.List[object]]::new()
$stats = [ordered]@{
    scanned = 0; skipped_scope = 0; accel_present = 0; accel_inject = 0
    net_present = 0; net_inject = 0; net_not_needed = 0
    written = 0; backed_up = 0; compile_ok = 0; compile_fail = 0; error = 0
}

foreach ($f in $allPy) {
    $rel = $f.FullName.Substring($viaHome.Length).TrimStart('\', '/')
    $stats.scanned++
    if (Test-ShouldSkipFile -Rel $rel -IncludeIntake:$IncludeIntake -IncludeTests:$IncludeTests) {
        $stats.skipped_scope++
        continue
    }
    try {
        $raw = [System.IO.File]::ReadAllText($f.FullName)
    } catch {
        $stats.error++
        $rows.Add([pscustomobject]@{ Rel = $rel; Accel = "READ_FAIL"; Net = "READ_FAIL"; Action = $_.Exception.Message })
        continue
    }

    $needAccel = $raw -notmatch '\[VIA:ACCEL-BRIDGE'
    $isFetch   = Test-IsVdfOutboundFetch -Rel $rel -Text $raw -Name $f.Name
    $needNet   = $isFetch -and ($raw -notmatch '\[VIA:NET-BRIDGE')

    if (-not $needAccel) { $stats.accel_present++ }
    if ($isFetch -and -not $needNet) { $stats.net_present++ }
    if (-not $isFetch) { $stats.net_not_needed++ }

    if (-not $needAccel -and -not $needNet) {
        continue
    }

    $new = $raw
    $actions = [System.Collections.Generic.List[string]]::new()
    if ($needAccel) {
        $ins = Get-InsertIndex -Text $new
        $new = $new.Insert($ins, ($AccelBlock.TrimEnd() + "`r`n"))
        $stats.accel_inject++
        [void]$actions.Add("ACCEL")
    }
    if ($needNet) {
        $ins = Get-InsertIndex -Text $new
        $new = $new.Insert($ins, ($NetBlock.TrimEnd() + "`r`n"))
        $stats.net_inject++
        [void]$actions.Add("NET")
    }

    $action = ($actions -join "+")
    if ($Apply) {
        try {
            $destDir = Join-Path $backupRoot (Split-Path $rel -Parent)
            if (-not (Test-Path -LiteralPath $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $destDir (Split-Path $rel -Leaf)) -Force
            $stats.backed_up++
            $utf8NoBom = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllText($f.FullName, $new, $utf8NoBom)
            $stats.written++
            if (-not $SkipPyCompile) {
                $py = Get-Command py -ErrorAction SilentlyContinue
                if ($py) {
                    $p = Start-Process -FilePath "py" -ArgumentList @("-3", "-m", "py_compile", $f.FullName) -Wait -PassThru -NoNewWindow -RedirectStandardOutput (Join-Path $reportRoot "compile.out") -RedirectStandardError (Join-Path $reportRoot "compile.err")
                    if ($p.ExitCode -eq 0) { $stats.compile_ok++ } else { $stats.compile_fail++ }
                }
            }
            $rows.Add([pscustomobject]@{ Rel = $rel; Accel = $(if ($needAccel) { "INJECTED" } else { "KEEP" }); Net = $(if ($needNet) { "INJECTED" } elseif ($isFetch) { "KEEP" } else { "-" }); Action = $action })
        } catch {
            $stats.error++
            $rows.Add([pscustomobject]@{ Rel = $rel; Accel = "ERROR"; Net = "ERROR"; Action = $_.Exception.Message })
        }
    } else {
        $rows.Add([pscustomobject]@{ Rel = $rel; Accel = $(if ($needAccel) { "WOULD_INJECT" } else { "KEEP" }); Net = $(if ($needNet) { "WOULD_INJECT" } elseif ($isFetch) { "KEEP" } else { "-" }); Action = $action })
    }
}

$csvPath  = Join-Path $reportRoot "bridge_matrix.csv"
$htmlPath = Join-Path $reportRoot "bridge_report.html"
$rows | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8

$modeLabel = if ($Apply) { "APPLY" } else { "DRY-RUN" }
$html = @"
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VIA Accel+Net Bridge $modeLabel $stamp</title>
<style>
body{font-family:Segoe UI,Meiryo,sans-serif;background:#0b1220;color:#e8eef8;margin:24px}
h1{font-size:20px} table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border:1px solid #2a3a55;padding:6px 8px;text-align:left}
th{background:#152238} tr:nth-child(even){background:#101a2c}
.ok{color:#7dffa3} .warn{color:#ffd27d} .bad{color:#ff8a8a} code{color:#9cd1ff}
</style></head><body>
<h1>VIA Accel + Net Bridge · $modeLabel · $stamp</h1>
<p>母根 <code>$viaHome</code></p>
<p>加速器正本 <code>supportive modules\VeritasCeleritas.py</code> → 入口 <code>VIA_SuperAccel_Module.py</code></p>
<p>網路正本 <code>supportive modules\VeritasAegisNexus.py</code> → 入口 <code>network\via_net_unified_v*.py</code></p>
<table>
<tr><th>metric</th><th>value</th></tr>
<tr><td>scanned py</td><td>$($stats.scanned)</td></tr>
<tr><td>skipped scope</td><td>$($stats.skipped_scope)</td></tr>
<tr><td>accel already present</td><td>$($stats.accel_present)</td></tr>
<tr><td>accel inject</td><td>$($stats.accel_inject)</td></tr>
<tr><td>net already present</td><td>$($stats.net_present)</td></tr>
<tr><td>net inject (VDF outbound)</td><td>$($stats.net_inject)</td></tr>
<tr><td>written</td><td>$($stats.written)</td></tr>
<tr><td>backed up</td><td>$($stats.backed_up)</td></tr>
<tr><td>py_compile fail</td><td>$($stats.compile_fail)</td></tr>
<tr><td>error</td><td>$($stats.error)</td></tr>
</table>
<h2>變更列（僅列出需動作者）</h2>
<table><tr><th>file</th><th>accel</th><th>net</th><th>action</th></tr>
"@
foreach ($r in $rows) {
    $html += "<tr><td><code>$([System.Net.WebUtility]::HtmlEncode($r.Rel))</code></td><td>$($r.Accel)</td><td>$($r.Net)</td><td>$($r.Action)</td></tr>`n"
}
$html += "</table><p>備份：$backupRoot</p><p>還原：把 backup 相對路徑覆回 VIA_HOME。</p></body></html>"
[System.IO.File]::WriteAllText($htmlPath, $html, [System.Text.UTF8Encoding]::new($false))

Write-Host ""
Write-Host "----- MATRIX -----" -ForegroundColor Cyan
$stats.GetEnumerator() | ForEach-Object { "{0,-18} {1}" -f $_.Key, $_.Value }
Write-Host ""
Write-Host ("CSV  : {0}" -f $csvPath) -ForegroundColor Green
Write-Host ("HTML : {0}" -f $htmlPath) -ForegroundColor Green
if (-not $Apply) {
    Write-Host ""
    Write-Host "這是預覽。確認矩陣後再加 -Apply 才寫入。" -ForegroundColor Yellow
    Write-Host "  .\Invoke-VIA-AccelNetBridge-AllPy-v0100.ps1 -Apply"
    Write-Host "收容區 / 測試一併掛橋："
    Write-Host "  .\Invoke-VIA-AccelNetBridge-AllPy-v0100.ps1 -Apply -IncludeIntake -IncludeTests"
}
exit $(if ($stats.error -gt 0 -or $stats.compile_fail -gt 0) { 1 } else { 0 })
