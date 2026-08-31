#requires -Version 7.0
<#
 Veritas EngineForge — P0 Convergence Orchestrator
 v1.0  -  One paste. Append-only. Originals never touched. Sealed only if parse=0.
 Runs the Three-Round Safe Convergence Spine over the 6 P0 parse blockers:
   Sandbox Gate -> R1 panoramic parse -> R2 deterministic repair (param-first + bare-if
   $()-wrap, each parse=0 gated) -> classify residual -> HTML matrix report.
 Deterministic fixes embodied (all proven in this session):
   F1 (LL-1) param-first relocation      -> clears "5:33 assignment is not valid"
   F2 (LL-5) bare-if $()-wrap            -> clears "Unexpected token 'if'" cascades
 Residual classification:
   parse=0                               -> SEALED_PARSE_0
   residual w/ "missing the terminator"  -> STRUCTURAL_REWRITE_REQUIRED (LL-6 nested quote;
                                            FLATTEN by hand, do NOT blind-fix)
   other residual                        -> NEEDS_REVIEW
 Paste-safe: body wrapped in a function; single-line Write-Host; $list.Count for Lists.
#>
param(
    [string]$Root = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics',
    [string[]]$Targets = @(),
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

# ----- F1: relocate pre-param statements to after param() (LL-1) -----
function def_RelocateParamFirst {
    param([string[]]$Lines)
    $pIdx = -1
    $i = 0
    while ($i -lt $Lines.Length) {
        $tl = $Lines[$i].Trim().ToLower()
        if ($tl.StartsWith('param')) {
            $after = $tl.Substring(5).TrimStart()
            if ($after.StartsWith('(')) { $pIdx = $i; break }
        }
        $i = $i + 1
    }
    if ($pIdx -lt 0) { return $null }
    $depth = 0; $closeIdx = -1; $j = $pIdx
    while ($j -lt $Lines.Length) {
        foreach ($ch in $Lines[$j].ToCharArray()) {
            if ($ch -eq '(') { $depth = $depth + 1 } elseif ($ch -eq ')') { $depth = $depth - 1 }
        }
        if ($depth -le 0) { $closeIdx = $j; break }
        $j = $j + 1
    }
    if ($closeIdx -lt 0) { return $null }
    $inBlock = $false; $headEnd = -1; $k = 0
    while ($k -lt $pIdx) {
        $t = $Lines[$k].Trim(); $isPre = $false
        if ($inBlock) { $isPre = $true; if ($t.Contains('#>')) { $inBlock = $false } }
        elseif ($t -eq '') { $isPre = $true }
        elseif ($t.ToLower().StartsWith('#requires')) { $isPre = $true }
        elseif ($t.StartsWith('<#')) { $isPre = $true; if (-not $t.Contains('#>')) { $inBlock = $true } }
        elseif ($t.StartsWith('#')) { $isPre = $true }
        if ($isPre) { $headEnd = $k } else { break }
        $k = $k + 1
    }
    $out = New-Object System.Collections.Generic.List[string]
    $a = 0
    while ($a -le $headEnd) { $out.Add($Lines[$a]); $a = $a + 1 }
    if ($headEnd -ge 0) { $out.Add('') }
    $b = $pIdx
    while ($b -le $closeIdx) { $out.Add($Lines[$b]); $b = $b + 1 }
    $movedAny = $false; $c = $headEnd + 1
    while ($c -lt $pIdx) {
        if ($Lines[$c].Trim() -ne '') {
            if (-not $movedAny) { $out.Add(''); $movedAny = $true }
            $out.Add($Lines[$c])
        }
        $c = $c + 1
    }
    $d = $closeIdx + 1
    while ($d -lt $Lines.Length) { $out.Add($Lines[$d]); $d = $d + 1 }
    return $out.ToArray()
}

# ----- F2: wrap bare if(){}else{} used as a value (LL-5) -----
function def_WrapBareIfInLine {
    param([string]$Line)
    $s = $Line; $n = $s.Length
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
                            $depth = 0; $end = -1; $m = $k
                            while ($m -lt $n) {
                                $cm = $s[$m]
                                if ($cm -eq '{') { $depth = $depth + 1 }
                                elseif ($cm -eq '}') {
                                    $depth = $depth - 1
                                    if ($depth -eq 0) {
                                        $p = $m + 1
                                        while (($p -lt $n) -and ($s[$p] -eq ' ')) { $p = $p + 1 }
                                        $isElse = $false
                                        if ($p -lt $n) {
                                            $rem = $n - $p
                                            if ($s.Substring($p, [Math]::Min(6, $rem)).StartsWith('elseif')) { $isElse = $true }
                                            elseif ($s.Substring($p, [Math]::Min(4, $rem)).StartsWith('else')) { $isElse = $true }
                                        }
                                        if (-not $isElse) { $end = $m; break }
                                    }
                                }
                                $m = $m + 1
                            }
                            if ($end -ge 0) { $opens.Add($i + 1); $closes.Add($end + 1) }
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
    $res = $s
    foreach ($pt in ($pts | Sort-Object @{e = 'Pos'; desc = $true })) {
        $res = $res.Substring(0, $pt.Pos) + $pt.Text + $res.Substring($pt.Pos)
    }
    return $res
}

function def_Parse {
    param([string]$Path)
    $tokens = $null; $perrs = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$perrs)
    return @($perrs)
}

function Invoke-VEFP0Convergence {
    param([string]$Root,[string[]]$Targets,[switch]$NoOpenSwitch)

    $stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
    $runRoot = Join-Path $Root ('tools\VIA_MultiProject_PanoramaSync\runs\RUN_' + $stamp + '_VEF_P0_CONVERGENCE')
    $sandbox = Join-Path $runRoot 'sandbox'
    $repaired = Join-Path $runRoot 'repaired'
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    $colGrey = '#9c9890'; $colTeal = '#439a9a'; $colUp = '#c96b5a'; $colDown = '#5a9e6f'; $colBlue = '#4c78a8'

    if ($Targets.Count -eq 0) {
        $Targets = @(
            (Join-Path $Root 'functional modules\VAP\ASSETS\SCOPE_COPY\VeritasIntelligenceAnalytics\_activation\VIA_ACTIVATION_GATEWAY_V02_GATEWAY_HOTFIX_20260609_035258\gateway\Invoke-VIA-ActivationGateway-Hardened.ps1'),
            (Join-Path $Root 'functional modules\VAP\ASSETS\SCOPE_COPY\VeritasIntelligenceAnalytics\_activation\VIA_ACTIVATION_GATEWAY_V03_STABLE_HOTFIX_20260609_035508\gateway\Invoke-VIA-ActivationGateway-Stable.ps1'),
            (Join-Path $Root 'functional modules\VAP\ASSETS\SCOPE_COPY\VeritasIntelligenceAnalytics\_activation\VIA_ACTIVATION_GATEWAY_V04_INLINE_READY_20260609_035734\gateway\Invoke-VIA-ActivationGateway-InlineReady.ps1'),
            (Join-Path $Root 'functional modules\VAP\ASSETS\SCOPE_COPY\VeritasIntelligenceAnalytics\_freeze\VIA_UNIFIED_INPUT_SSOT_FREEZE_GATEWAY_20260609_034130\gateway\Invoke-VIA-UnifiedInputGateway.ps1'),
            (Join-Path $Root 'functional modules\VAP\ASSETS\SCOPE_COPY\VAP\VIA_VEGN_Step1_v32.ps1'),
            (Join-Path $Root 'functional modules\VAP\INPUT\SOURCE_VAP_MODULE\VIA_VEGN_Step1_v32.ps1')
        )
    }

    New-Item -ItemType Directory -Path $sandbox -Force | Out-Null
    New-Item -ItemType Directory -Path $repaired -Force | Out-Null

    $enc = {
        param([string]$t)
        if ($null -eq $t) { return '' }
        $o = $t
        $o = $o.Replace('&','&amp;'); $o = $o.Replace('<','&lt;'); $o = $o.Replace('>','&gt;')
        $o = $o.Replace('"','&quot;'); $o = $o.Replace("'", '&#39;')
        return $o
    }

    $records = New-Object System.Collections.Generic.List[object]
    $shaMap = [ordered]@{}
    $idx = 0
    foreach ($src in $Targets) {
        $idx = $idx + 1
        $name = [IO.Path]::GetFileName($src)
        Write-Progress -Id 1 -Activity 'VEF P0 Convergence' -Status ('[' + $idx + '/' + $Targets.Count + '] ' + $name) -PercentComplete ([int](($idx / $Targets.Count) * 100))

        $exists = Test-Path -LiteralPath $src
        $before = -1; $after = -1; $status = 'MISSING'; $dup = ''; $changeCount = 0
        $outPath = ''; $residual = New-Object System.Collections.Generic.List[string]; $changeRows = New-Object System.Collections.Generic.List[string]

        if ($exists) {
            $sandboxCopy = Join-Path $sandbox ('{0:D2}__{1}' -f $idx, $name)
            Copy-Item -LiteralPath $src -Destination $sandboxCopy -Force
            $sha = (Get-FileHash -LiteralPath $sandboxCopy -Algorithm SHA256).Hash
            if ($shaMap.Contains($sha)) { $dup = $shaMap[$sha] } else { $g = 'G' + ($shaMap.Count + 1); $shaMap[$sha] = $g; $dup = $g }

            $before = @(def_Parse -Path $sandboxCopy).Count

            # F1 param-first
            $lines = [IO.File]::ReadAllLines($sandboxCopy, $utf8)
            $f1 = def_RelocateParamFirst -Lines $lines
            if ($null -ne $f1) { $work = $f1 } else { $work = $lines }

            # F2 bare-if wrap (per line), record diffs vs the ORIGINAL sandbox lines
            $newLines = New-Object System.Collections.Generic.List[string]
            $li = 0
            while ($li -lt $work.Length) {
                $orig = $work[$li]
                $fixed = def_WrapBareIfInLine -Line $orig
                $newLines.Add($fixed)
                $li = $li + 1
            }
            # diff vs original file (line-aligned best-effort: compare F2 output to raw original where same length)
            $rawLen = $lines.Length
            if ($newLines.Count -eq $rawLen) {
                $z = 0
                while ($z -lt $rawLen) {
                    if ($newLines[$z] -ne $lines[$z]) {
                        $changeCount = $changeCount + 1
                        if ($changeRows.Count -lt 40) {
                            $changeRows.Add('<div class="chg"><div class="cn">line ' + ($z + 1) + '</div><pre class="old">' + (& $enc $lines[$z]) + '</pre><pre class="new">' + (& $enc $newLines[$z]) + '</pre></div>')
                        }
                    }
                    $z = $z + 1
                }
            } else {
                $changeCount = -1  # structure changed by F1 relocation; count not line-aligned
            }

            $outPath = Join-Path $repaired ('{0:D2}__{1}' -f $idx, $name)
            [IO.File]::WriteAllText($outPath, ($newLines -join "`r`n"), $utf8)

            $errs = @(def_Parse -Path $outPath)
            $after = $errs.Count
            if ($after -eq 0) {
                $status = 'SEALED_PARSE_0'
            } else {
                $hasTerminator = $false
                foreach ($e in $errs) { if ($e.Message.Contains('missing the terminator')) { $hasTerminator = $true; break } }
                if ($hasTerminator) { $status = 'STRUCTURAL_REWRITE_REQUIRED' } else { $status = 'NEEDS_REVIEW' }
                $sortedE = $errs | Sort-Object @{e={$_.Extent.StartLineNumber};desc=$false}, @{e={$_.Extent.StartColumnNumber};desc=$false}
                $cnt = 0
                foreach ($e in $sortedE) {
                    if ($cnt -ge 12) { break }
                    $residual.Add(('{0}:{1}  {2}' -f $e.Extent.StartLineNumber, $e.Extent.StartColumnNumber, $e.Message))
                    $cnt = $cnt + 1
                }
            }
        }

        $records.Add([PSCustomObject]@{
            Idx=$idx; FileName=$name; Status=$status; Before=$before; After=$after; Dup=$dup;
            Changes=$changeCount; Repaired=$outPath; Origin=$src;
            Residual=($residual -join "`n"); ChangeRows=($changeRows -join "`n")
        })
    }

    Write-Progress -Id 1 -Activity 'VEF P0 Convergence' -Completed

    $sealed = @($records | Where-Object { $_.Status -eq 'SEALED_PARSE_0' }).Count
    $struct = @($records | Where-Object { $_.Status -eq 'STRUCTURAL_REWRITE_REQUIRED' }).Count
    $needs  = @($records | Where-Object { $_.Status -eq 'NEEDS_REVIEW' }).Count
    $total  = $records.Count

    # rows + sections
    $rows = New-Object System.Collections.Generic.List[string]
    $sections = New-Object System.Collections.Generic.List[string]
    foreach ($r in $records) {
        $stColor = $colGrey
        if ($r.Status -eq 'SEALED_PARSE_0') { $stColor = $colDown }
        elseif ($r.Status -eq 'STRUCTURAL_REWRITE_REQUIRED') { $stColor = $colUp }
        elseif ($r.Status -eq 'NEEDS_REVIEW') { $stColor = '#c9a14c' }
        $chg = $r.Changes
        if ($chg -lt 0) { $chg = 'n/a (relocated)' }
        $rows.Add('<tr><td class="num">' + $r.Idx + '</td><td class="fn">' + (& $enc $r.FileName) + '</td>' +
            '<td>' + $r.Dup + '</td>' +
            '<td><span class="pill" style="background:' + $stColor + '">' + $r.Status + '</span></td>' +
            '<td class="num">' + $r.Before + '</td><td class="num">' + $r.After + '</td>' +
            '<td class="num">' + $chg + '</td></tr>')

        $sub = ''
        if (-not [string]::IsNullOrWhiteSpace($r.Residual)) {
            $sub = $sub + '<h4>residual (first 12)</h4><pre class="err">' + (& $enc $r.Residual) + '</pre>'
            if ($r.Status -eq 'STRUCTURAL_REWRITE_REQUIRED') {
                $sub = $sub + '<div class="note">LL-6: double-quoted literal nested inside $(...) inside an expandable "..." string. FLATTEN — precompute each cell value into a local variable before the row string; leave only $var interpolations. Do NOT blind-fix.</div>'
            }
        }
        if (-not [string]::IsNullOrWhiteSpace($r.ChangeRows)) {
            $sub = $sub + '<details><summary>changed lines (before/after, first 40)</summary>' + $r.ChangeRows + '</details>'
        }
        if ($sub -ne '') {
            $sections.Add('<h3>#' + $r.Idx + ' ' + (& $enc $r.FileName) + ' <span style="color:' + $colGrey + ';font-size:11px">' + $r.Status + ' · ' + $r.Before + '→' + $r.After + '</span></h3>' + $sub)
        }
    }

    $cards = '<div class="cards">' +
        '<div class="card"><div class="k">Sealed parse=0</div><div class="v" style="color:' + $colDown + '">' + $sealed + ' / ' + $total + '</div></div>' +
        '<div class="card"><div class="k">Structural rewrite</div><div class="v" style="color:' + $colUp + '">' + $struct + '</div></div>' +
        '<div class="card"><div class="k">Needs review</div><div class="v" style="color:#c9a14c">' + $needs + '</div></div>' +
        '<div class="card"><div class="k">Originals</div><div class="v" style="font-size:13px;color:' + $colTeal + '">untouched</div></div>' +
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
.sub{color:var(--grey);font-family:"DM Mono",ui-monospace,monospace;font-size:12px;margin-bottom:14px}
.spine{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0;font-family:"DM Mono",monospace;font-size:11px}
.spine span{background:#1d2026;border:1px solid #2a2e36;border-radius:20px;padding:4px 10px;color:#cfd3da}
.cards{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}
.card{background:#1d2026;border:1px solid #2a2e36;border-radius:10px;padding:12px 16px;min-width:140px}
.card .k{color:var(--grey);font-size:11px;text-transform:uppercase;letter-spacing:.6px}
.card .v{font-family:"DM Mono",monospace;font-size:24px;font-weight:600}
h2{font-family:"Syne",sans-serif;font-size:15px;margin:24px 0 10px;color:var(--teal);border-left:3px solid var(--teal);padding-left:10px}
h3{font-family:"Syne",sans-serif;font-size:13px;margin:18px 0 8px;color:#e8e6e1}
h4{font-family:"DM Mono",monospace;font-size:11px;color:var(--grey);margin:10px 0 4px;text-transform:uppercase;letter-spacing:.5px}
table{width:100%;border-collapse:collapse;background:#1a1d23;border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:9px 11px;border-bottom:1px solid #25292f;vertical-align:top}
th{background:#22262e;color:var(--grey);font-size:11px;text-transform:uppercase;letter-spacing:.5px}
td.num,th.num{font-family:"DM Mono",monospace;text-align:right;white-space:nowrap}
td.fn{font-family:"DM Mono",monospace;color:#fff;white-space:nowrap}
.pill{display:inline-block;padding:2px 8px;border-radius:20px;color:#10131a;font-weight:700;font-size:10.5px;font-family:"DM Mono",monospace}
pre{margin:0;padding:9px 11px;overflow:auto;font-family:"DM Mono",ui-monospace,monospace;font-size:11.5px;white-space:pre;line-height:1.45;border-radius:8px}
pre.err{background:#241b1b;color:#e2b8b0;border:1px solid #322}
pre.old{background:#241b1b;color:#e2b8b0;border:1px solid #322;border-bottom:none}
pre.new{background:#1a241d;color:#bfe2c8;border:1px solid #243}
.chg{margin:8px 0}
.cn{background:#22262e;color:var(--grey);font-family:"DM Mono",monospace;font-size:11px;padding:4px 10px;border-radius:6px 6px 0 0}
.note{background:#1d2026;border:1px solid var(--up);border-radius:8px;padding:10px 12px;margin:8px 0;font-family:"DM Mono",monospace;font-size:11.5px;color:#e2b8b0}
details summary{cursor:pointer;color:var(--blue);font-family:"DM Mono",monospace;font-size:11px;margin:6px 0}
.hand{background:#1d2026;border:1px solid var(--teal);border-radius:10px;padding:14px 16px;margin:16px 0;font-family:"DM Mono",monospace;font-size:12px;color:#cfd3da}
.foot{color:var(--grey);font-size:11px;font-family:"DM Mono",monospace;margin-top:26px}
</style></head><body><div class="wrap">
<h1><span class="seal">&#29702;</span>@@TITLE@@</h1>
<div class="sub">@@TS@@ &middot; append-only / originals untouched / sealed only if parse=0 &middot; 判天地之美，析萬物之理</div>
<div class="spine"><span>Sandbox Gate</span><span>R1 全景分析</span><span>R2 順序修正 (param-first + bare-if)</span><span>residual classify</span><span>R3 收尾 (pending)</span><span>安全啟用 (HIGH=0 → user-test → activate)</span></div>
@@CARDS@@
<div class="hand">F1 param-first (LL-1) and F2 bare-if $()-wrap (LL-5) are deterministic and parse=0-gated. Anything still failing with "string missing terminator" is LL-6 (nested quotes) and is flagged STRUCTURAL_REWRITE_REQUIRED — flatten by hand, never blind-fix. Repaired copies live in repaired\; promote only on explicit instruction.</div>
<h2>P0 Convergence Matrix</h2>
<table><thead><tr><th class="num">#</th><th>File</th><th>Dup</th><th>Status</th><th class="num">Before</th><th class="num">After</th><th class="num">Changes</th></tr></thead><tbody>
@@ROWS@@
</tbody></table>
<h2>Per-file detail</h2>
@@SECTIONS@@
<div class="foot">RUN_@@STAMP@@_VEF_P0_CONVERGENCE &middot; twin-synced by SHA256 &middot; parse=0 gated &middot; bounded / NoHang.</div>
</div></body></html>
'@

    $html = $template
    $html = $html.Replace('@@TITLE@@', 'Veritas EngineForge — P0 Convergence')
    $html = $html.Replace('@@TS@@', $stamp)
    $html = $html.Replace('@@STAMP@@', $stamp)
    $html = $html.Replace('@@CARDS@@', $cards)
    $html = $html.Replace('@@ROWS@@', ($rows -join "`n"))
    $html = $html.Replace('@@SECTIONS@@', ($sections -join "`n"))

    $htmlPath = Join-Path $runRoot 'VEF_P0_Convergence_Matrix.html'
    [IO.File]::WriteAllText($htmlPath, $html, $utf8)

    $jsonPath = Join-Path $runRoot 'VEF_P0_Convergence.json'
    [IO.File]::WriteAllText($jsonPath, (($records | Select-Object Idx,FileName,Status,Before,After,Dup,Changes,Origin,Repaired) | ConvertTo-Json -Depth 5), $utf8)

    Write-Host ''
    Write-Host '理  Veritas EngineForge — P0 Convergence Orchestrator  -  DONE' -ForegroundColor Cyan
    Write-Host ('   RunRoot   : ' + $runRoot) -ForegroundColor Gray
    Write-Host ('   Sealed    : ' + $sealed + ' / ' + $total + '   Structural: ' + $struct + '   NeedsReview: ' + $needs) -ForegroundColor Gray
    foreach ($r in $records) {
        Write-Host ('   - ' + $r.FileName + '  [' + $r.Dup + ']  ' + $r.Status + '  ' + $r.Before + '->' + $r.After) -ForegroundColor Gray
    }
    Write-Host ('   HTML      : ' + $htmlPath) -ForegroundColor Gray
    Write-Host '   Originals untouched. Promotion to live tree requires an explicit instruction.' -ForegroundColor Gray
    Write-Host ''

    if (-not $NoOpenSwitch) {
        if (Test-Path -LiteralPath $htmlPath) { Start-Process $htmlPath | Out-Null }
    }
}

Invoke-VEFP0Convergence -Root $Root -Targets $Targets -NoOpenSwitch:$NoOpenSwitch

