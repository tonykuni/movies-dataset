#requires -Version 7.0
<#
 VIA P0 VEGN Residual-Error Locator  (Class B round-2 follow-up)
 v0.1  -  Append-only. Originals never touched.
 The bare-if $()-wrap fix cleared 21 of 119 errors; 98 remain from a second,
 previously-masked defect. This re-applies the SAME bare-if fix to a working copy,
 re-parses it, and reports the residual parse errors (line:col:message) plus the
 source regions around the new first-error lines, so the next defect can be fixed
 with a line-exact, parse=0-gated repair (Command #7).
 Paste-safe: body in a function; single-line Write-Host; $list.Count for Lists.
#>
param(
    [string]$Root = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics',
    [int]$DistinctLines = 10,
    [switch]$NoOpenSwitch
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

function def_WrapBareIfInLine {
    param([string]$Line)
    $s = $Line
    $n = $s.Length
    $opens = New-Object System.Collections.Generic.List[int]
    $closes = New-Object System.Collections.Generic.List[int]
    $i = 0
    while ($i -lt $n) {
        if ($s[$i] -eq '(') {
            $prev = ''
            if ($i -gt 0) { $prev = $s[$i - 1] }
            if (($prev -ne '$') -and ($prev -ne '@')) {
                $j = $i + 1
                while (($j -lt $n) -and ($s[$j] -eq ' ')) { $j = $j + 1 }
                if (($j + 1 -lt $n) -and ($s[$j] -eq 'i') -and ($s[$j + 1] -eq 'f')) {
                    $after = ''
                    if ($j + 2 -lt $n) { $after = $s[$j + 2] }
                    if (($after -eq '(') -or ($after -eq ' ')) {
                        $k = $j
                        while (($k -lt $n) -and ($s[$k] -ne '{')) { $k = $k + 1 }
                        if ($k -lt $n) {
                            $depth = 0
                            $end = -1
                            $m = $k
                            while ($m -lt $n) {
                                $cm = $s[$m]
                                if ($cm -eq '{') {
                                    $depth = $depth + 1
                                } elseif ($cm -eq '}') {
                                    $depth = $depth - 1
                                    if ($depth -eq 0) {
                                        $p = $m + 1
                                        while (($p -lt $n) -and ($s[$p] -eq ' ')) { $p = $p + 1 }
                                        $isElse = $false
                                        if ($p -lt $n) {
                                            $rem = $n - $p
                                            $look6 = $s.Substring($p, [Math]::Min(6, $rem))
                                            $look4 = $s.Substring($p, [Math]::Min(4, $rem))
                                            if ($look6.StartsWith('elseif')) { $isElse = $true }
                                            elseif ($look4.StartsWith('else')) { $isElse = $true }
                                        }
                                        if (-not $isElse) { $end = $m; break }
                                    }
                                }
                                $m = $m + 1
                            }
                            if ($end -ge 0) {
                                $opens.Add($i + 1)
                                $closes.Add($end + 1)
                            }
                        }
                    }
                }
            }
        }
        $i = $i + 1
    }
    if ($opens.Count -eq 0) { return $Line }
    $pts = New-Object System.Collections.Generic.List[object]
    $q = 0
    while ($q -lt $opens.Count) {
        $pts.Add([PSCustomObject]@{ Pos = $closes[$q]; Text = ')' })
        $pts.Add([PSCustomObject]@{ Pos = $opens[$q]; Text = '$(' })
        $q = $q + 1
    }
    $sorted = $pts | Sort-Object @{e = 'Pos'; desc = $true }
    $res = $s
    foreach ($pt in $sorted) {
        $res = $res.Substring(0, $pt.Pos) + $pt.Text + $res.Substring($pt.Pos)
    }
    return $res
}

function Invoke-VIAVEGNResidualLocate {
    param([string]$Root,[int]$DistinctLines,[switch]$NoOpenSwitch)

    $stamp   = (Get-Date).ToString('yyyyMMdd_HHmmss')
    $runRoot = Join-Path $Root ('tools\VIA_MultiProject_PanoramaSync\runs\RUN_' + $stamp + '_VIA_P0_VEGN_RESIDUAL')
    $repaired = Join-Path $runRoot 'repaired'
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    $colGrey = '#9c9890'; $colTeal = '#439a9a'; $colUp = '#c96b5a'; $colDown = '#5a9e6f'; $colBlue = '#4c78a8'

    $src = Join-Path $Root 'functional modules\VAP\ASSETS\SCOPE_COPY\VAP\VIA_VEGN_Step1_v32.ps1'
    $name = [IO.Path]::GetFileName($src)

    New-Item -ItemType Directory -Path $repaired -Force | Out-Null

    if (-not (Test-Path -LiteralPath $src)) {
        Write-Host ('MISSING: ' + $src) -ForegroundColor Red
        return
    }

    $enc = {
        param([string]$t)
        if ($null -eq $t) { return '' }
        $o = $t
        $o = $o.Replace('&','&amp;'); $o = $o.Replace('<','&lt;'); $o = $o.Replace('>','&gt;')
        $o = $o.Replace('"','&quot;'); $o = $o.Replace("'", '&#39;')
        return $o
    }

    # apply bare-if fix to a working copy
    $lines = [IO.File]::ReadAllLines($src, $utf8)
    $newLines = New-Object System.Collections.Generic.List[string]
    foreach ($ln in $lines) { $newLines.Add((def_WrapBareIfInLine -Line $ln)) }
    $repairedPath = Join-Path $repaired ('01__' + $name)
    [IO.File]::WriteAllText($repairedPath, ($newLines -join "`r`n"), $utf8)

    # parse repaired, collect residual errors
    $rLines = [IO.File]::ReadAllLines($repairedPath, $utf8)
    $tokens = $null
    $perrs = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($repairedPath, [ref]$tokens, [ref]$perrs)
    $errs = @($perrs)
    $errCount = $errs.Count

    $sorted = $errs | Sort-Object @{e={$_.Extent.StartLineNumber};desc=$false}, @{e={$_.Extent.StartColumnNumber};desc=$false}

    # error table (first 30)
    $errRows = New-Object System.Collections.Generic.List[string]
    $packLines = New-Object System.Collections.Generic.List[string]
    $packLines.Add('VIA VEGN Residual Errors after bare-if fix  -  RUN ' + $stamp)
    $packLines.Add('Residual parse errors: ' + $errCount)
    $packLines.Add('')
    $packLines.Add('--- FIRST ERRORS (line:col  message) ---')
    $shown = 0
    foreach ($e in $sorted) {
        if ($shown -ge 30) { break }
        $line = $e.Extent.StartLineNumber
        $col = $e.Extent.StartColumnNumber
        $msg = $e.Message
        $errRows.Add('<tr><td class="num">' + $line + ':' + $col + '</td><td class="msg">' + (& $enc $msg) + '</td></tr>')
        $packLines.Add(('{0}:{1}  {2}' -f $line, $col, $msg))
        $shown = $shown + 1
    }

    # distinct first lines
    $distinct = New-Object System.Collections.Generic.List[int]
    foreach ($e in $sorted) {
        $line = $e.Extent.StartLineNumber
        if (-not $distinct.Contains($line)) {
            $distinct.Add($line)
            if ($distinct.Count -ge $DistinctLines) { break }
        }
    }

    $regionSections = New-Object System.Collections.Generic.List[string]
    $packLines.Add('')
    $packLines.Add('--- REGIONS AROUND FIRST ' + $distinct.Count + ' DISTINCT ERROR LINES ---')
    foreach ($dl in $distinct) {
        $from = $dl - 7
        if ($from -lt 0) { $from = 0 }
        $to = $dl + 4
        if ($to -ge $rLines.Length) { $to = $rLines.Length - 1 }
        $rg = New-Object System.Collections.Generic.List[string]
        $r = $from
        while ($r -le $to) {
            $lno = $r + 1
            $mk = '   '
            if ($lno -eq $dl) { $mk = 'E> ' }
            $rg.Add($mk + ('{0,5}' -f $lno) + ' | ' + $rLines[$r])
            $r = $r + 1
        }
        $regionText = ($rg -join "`n")
        $regionSections.Add('<h3>line ' + $dl + '</h3><pre>' + (& $enc $regionText) + '</pre>')
        $packLines.Add('')
        $packLines.Add('=== line ' + $dl + ' ===')
        $packLines.Add($regionText)
    }

    $packPath = Join-Path $runRoot 'VEGN_RESIDUAL_PACK.txt'
    [IO.File]::WriteAllText($packPath, ($packLines -join "`r`n"), $utf8)

    $cards = '<div class="cards">' +
        '<div class="card"><div class="k">Residual errors</div><div class="v" style="color:' + $colUp + '">' + $errCount + '</div></div>' +
        '<div class="card"><div class="k">After bare-if fix</div><div class="v" style="font-size:13px;color:' + $colTeal + '">119 &rarr; ' + $errCount + '</div></div>' +
        '<div class="card"><div class="k">Distinct lines</div><div class="v" style="color:' + $colBlue + '">' + $distinct.Count + '</div></div>' +
        '</div>'

    $template = @'
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>@@TITLE@@</title>
<style>
:root{--blue:#4c78a8;--grey:#9c9890;--teal:#439a9a;--up:#c96b5a;--down:#5a9e6f;}
*{box-sizing:border-box}body{margin:0;background:#14161a;color:#e8e6e1;font-family:"DM Sans",system-ui,sans-serif;font-size:14px;line-height:1.5}
.wrap{max-width:1500px;margin:0 auto;padding:24px}
h1{font-family:"Syne","DM Sans",sans-serif;font-size:22px;margin:0 0 2px}
.seal{color:var(--teal);font-weight:700;margin-right:8px}
.sub{color:var(--grey);font-family:"DM Mono",ui-monospace,monospace;font-size:12px;margin-bottom:18px}
.cards{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
.card{background:#1d2026;border:1px solid #2a2e36;border-radius:10px;padding:12px 16px;min-width:130px}
.card .k{color:var(--grey);font-size:11px;text-transform:uppercase;letter-spacing:.6px}
.card .v{font-family:"DM Mono",monospace;font-size:24px;font-weight:600}
h2{font-family:"Syne",sans-serif;font-size:15px;margin:24px 0 10px;color:var(--teal);border-left:3px solid var(--teal);padding-left:10px}
h3{font-family:"DM Mono",monospace;font-size:12px;color:var(--blue);margin:14px 0 4px}
table{width:100%;border-collapse:collapse;background:#1a1d23;border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:8px 11px;border-bottom:1px solid #25292f;vertical-align:top}
th{background:#22262e;color:var(--grey);font-size:11px;text-transform:uppercase;letter-spacing:.5px}
td.num,th.num{font-family:"DM Mono",monospace;text-align:right;white-space:nowrap}
td.msg{font-family:"DM Mono",monospace;font-size:11.5px}
pre{background:#0f1116;border:1px solid #262a31;border-radius:8px;padding:10px;overflow:auto;font-family:"DM Mono",ui-monospace,monospace;font-size:11.5px;color:#cfd3da;white-space:pre;line-height:1.45}
.hand{background:#1d2026;border:1px solid var(--teal);border-radius:10px;padding:14px 16px;margin:18px 0;font-family:"DM Mono",monospace;font-size:12px;color:#cfd3da}
.foot{color:var(--grey);font-size:11px;font-family:"DM Mono",monospace;margin-top:26px}
</style></head><body><div class="wrap">
<h1><span class="seal">&#29702;</span>@@TITLE@@</h1>
<div class="sub">@@TS@@ &middot; append-only / originals untouched &middot; 判天地之美，析萬物之理</div>
@@CARDS@@
<div class="hand">The bare-if fix is applied to a working copy; these are the SECOND-class defects it revealed. Open <b>VEGN_RESIDUAL_PACK.txt</b> and paste it back for the line-exact, parse=0-gated repair (Command #7).</div>
<h2>Residual Errors (first 30)</h2>
<table><thead><tr><th class="num">L:C</th><th>Message</th></tr></thead><tbody>
@@ERRROWS@@
</tbody></table>
<h2>Source Regions around first distinct error lines</h2>
@@REGIONS@@
<div class="foot">RUN_@@STAMP@@_VIA_P0_VEGN_RESIDUAL &middot; locate only.</div>
</div></body></html>
'@

    $html = $template
    $html = $html.Replace('@@TITLE@@', 'VIA VEGN Residual-Error Locator')
    $html = $html.Replace('@@TS@@', $stamp)
    $html = $html.Replace('@@STAMP@@', $stamp)
    $html = $html.Replace('@@CARDS@@', $cards)
    $html = $html.Replace('@@ERRROWS@@', ($errRows -join "`n"))
    $html = $html.Replace('@@REGIONS@@', ($regionSections -join "`n"))

    $htmlPath = Join-Path $runRoot 'VIA_VEGN_Residual_Locator.html'
    [IO.File]::WriteAllText($htmlPath, $html, $utf8)

    Write-Host ''
    Write-Host '理  VIA VEGN Residual-Error Locator  -  DONE' -ForegroundColor Cyan
    Write-Host ('   RunRoot   : ' + $runRoot) -ForegroundColor Gray
    Write-Host ('   Residual  : ' + $errCount + ' parse errors after bare-if fix (119 -> ' + $errCount + ')') -ForegroundColor Yellow
    Write-Host ('   Pack      : ' + $packPath) -ForegroundColor Gray
    Write-Host ('   HTML      : ' + $htmlPath) -ForegroundColor Gray
    Write-Host '   Next      : paste VEGN_RESIDUAL_PACK.txt back -> Command #7 = line-exact repair of the second defect.' -ForegroundColor Gray
    Write-Host ''

    if (-not $NoOpenSwitch) {
        if (Test-Path -LiteralPath $htmlPath) { Start-Process $htmlPath | Out-Null }
    }
}

Invoke-VIAVEGNResidualLocate -Root $Root -DistinctLines $DistinctLines -NoOpenSwitch:$NoOpenSwitch

