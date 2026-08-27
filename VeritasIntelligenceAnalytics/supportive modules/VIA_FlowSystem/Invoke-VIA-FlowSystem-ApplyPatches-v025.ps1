#requires -Version 7.0
# VIA FlowSystem · APPLY REVIEWED SANDBOX PATCHES v025
# Applies the 5 human-reviewed temp-file reroutes + the _sandbox_tmp helper.
# DEFAULT = DRY-RUN (nothing written). Add -Apply to write, with per-file timestamped backup first.
# Precise substring replacement · idempotent · append-only backups · reversible.
# This is a DISTINCT tool from the read-only v024 scanner: only THIS runs with explicit -Apply.
param(
    [string]$BaseDir = "C:\Users\tonyk\Downloads\VIA_FlowSystem (2)\VIA_FlowSystem",
    [string]$HelperName = "_sandbox_tmp",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

# Reviewed, approved edits (exact substring before -> after). Nothing else is touched.
$script:Patches = @(
    @{ File = "engines\FLOW_ENG001_FlowAutotest.py"; Before = 'ROOT / "_test_sim.html"'; After = '_sandbox_tmp("_test_sim.html")' },
    @{ File = "engines\FLOW_ENG001_FlowAutotest.py"; Before = 'ROOT / "_test_perf.html"'; After = '_sandbox_tmp("_test_perf.html")' },
    @{ File = "engines\FLOW_ENG001_FlowAutotest.py"; Before = 'ROOT / "_test_mon.html"'; After = '_sandbox_tmp("_test_mon.html")' },
    @{ File = "engines\flow_bridge.py"; Before = 'Path("_v4_sample.csv")'; After = '_sandbox_tmp("_v4_sample.csv")' },
    @{ File = "engines\flow_perf.py"; Before = 'Path(out_path).with_suffix(".tmp.html")'; After = '_sandbox_tmp(Path(out_path).stem + ".tmp.html")' }
)

function def_WriteBanner {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 84) -ForegroundColor DarkCyan
    Write-Host ("def {0}" -f $Title) -ForegroundColor Cyan
    Write-Host ("=" * 84) -ForegroundColor DarkCyan
}

function def_BuildHelperBlock {
    param([string]$Helper)
    $t = @'
import tempfile
from pathlib import Path

def @@NAME@@(name: str) -> Path:
    d = Path(tempfile.gettempdir()) / "via_flow_sandbox"
    d.mkdir(parents=True, exist_ok=True)
    return d / name
'@
    return $t.Replace('@@NAME@@', $Helper)
}

function def_DetectNewline {
    param([string]$Text)
    if ($Text -match "`r`n") {
        return "`r`n"
    }
    return "`n"
}

function def_InsertHelper {
    param([string]$Text, [string]$Helper)
    if ($Text -match ('def\s+' + [regex]::Escape($Helper) + '\s*\(')) {
        return [pscustomobject]@{ Text = $Text; Status = "ALREADY" }
    }
    $nl = def_DetectNewline -Text $Text
    $lines = $Text -split "`r?`n"
    $lastImport = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^(import\s+\S+|from\s+\S+\s+import\s+)') {
            $lastImport = $i
        }
    }
    $blockLines = (def_BuildHelperBlock -Helper $Helper) -split "`r?`n"
    if ($lastImport -ge 0) {
        $head = @($lines[0..$lastImport])
        $tail = @()
        if (($lastImport + 1) -le ($lines.Count - 1)) {
            $tail = @($lines[($lastImport + 1)..($lines.Count - 1)])
        }
        $new = $head + @("") + @($blockLines) + $tail
    }
    else {
        $new = @($blockLines) + @("") + @($lines)
    }
    return [pscustomobject]@{ Text = ($new -join $nl); Status = "INSERTED" }
}

function def_ApplyReplacements {
    param([string]$Text, [object[]]$FilePatches)
    $results = @()
    $cur = $Text
    foreach ($p in $FilePatches) {
        if ($cur.Contains($p.After)) {
            $results += [pscustomobject]@{ Before = $p.Before; After = $p.After; Status = "ALREADY" }
            continue
        }
        if ($cur.Contains($p.Before)) {
            $cur = $cur.Replace($p.Before, $p.After)
            $results += [pscustomobject]@{ Before = $p.Before; After = $p.After; Status = "WILL_APPLY" }
            continue
        }
        $results += [pscustomobject]@{ Before = $p.Before; After = $p.After; Status = "NOT_FOUND" }
    }
    return [pscustomobject]@{ Text = $cur; Results = $results }
}

function def_Main {
    def_WriteBanner -Title "VIA FlowSystem · APPLY REVIEWED SANDBOX PATCHES v025"
    Write-Host ("def BaseDir : {0}" -f $BaseDir) -ForegroundColor White
    $mode = "DRY-RUN (no write)"
    if ($Apply) {
        $mode = "APPLY (writes with backup)"
    }
    Write-Host ("def Mode    : {0}" -f $mode) -ForegroundColor Yellow
    if (-not (Test-Path -LiteralPath $BaseDir)) {
        throw ("BaseDir not found: {0}" -f $BaseDir)
    }
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"

    $files = @($script:Patches | Select-Object -ExpandProperty File | Sort-Object -Unique)
    $summary = @()
    foreach ($rel in $files) {
        $full = Join-Path $BaseDir $rel
        if (-not (Test-Path -LiteralPath $full)) {
            Write-Host ("def [SKIP] {0} (not found)" -f $rel) -ForegroundColor Yellow
            $summary += [pscustomobject]@{ File = $rel; Helper = "N/A"; Applied = 0; Already = 0; NotFound = 0; Written = $false; Note = "SOURCE_NOT_FOUND" }
            continue
        }
        $orig = [System.IO.File]::ReadAllText($full)
        $hi = def_InsertHelper -Text $orig -Helper $HelperName
        $filePatches = @($script:Patches | Where-Object { $_.File -eq $rel })
        $ap = def_ApplyReplacements -Text $hi.Text -FilePatches $filePatches
        $newText = $ap.Text

        $willApply = @($ap.Results | Where-Object { $_.Status -eq "WILL_APPLY" }).Count
        $already = @($ap.Results | Where-Object { $_.Status -eq "ALREADY" }).Count
        $notFound = @($ap.Results | Where-Object { $_.Status -eq "NOT_FOUND" }).Count
        $changed = ($newText -ne $orig)

        Write-Host ""
        Write-Host ("def FILE {0}" -f $rel) -ForegroundColor Cyan
        Write-Host ("     helper: {0}" -f $hi.Status) -ForegroundColor Gray
        foreach ($r in $ap.Results) {
            $color = "Gray"
            if ($r.Status -eq "WILL_APPLY") {
                $color = "Green"
            }
            elseif ($r.Status -eq "NOT_FOUND") {
                $color = "Yellow"
            }
            Write-Host ("     [{0}] {1}  ->  {2}" -f $r.Status, $r.Before, $r.After) -ForegroundColor $color
        }

        $written = $false
        if ($Apply -and $changed) {
            $bak = $full + ".v024pre." + $stamp + ".bak"
            Copy-Item -LiteralPath $full -Destination $bak
            $enc = [System.Text.UTF8Encoding]::new($false)
            [System.IO.File]::WriteAllText($full, $newText, $enc)
            $written = $true
            Write-Host ("     WRITTEN. backup: {0}" -f $bak) -ForegroundColor Green
        }
        elseif ($Apply -and -not $changed) {
            Write-Host "     No change needed (idempotent)." -ForegroundColor DarkGray
        }
        else {
            Write-Host "     DRY-RUN: not written. Add -Apply to commit (backup will be made)." -ForegroundColor Yellow
        }

        $summary += [pscustomobject]@{ File = $rel; Helper = $hi.Status; Applied = $willApply; Already = $already; NotFound = $notFound; Written = $written; Note = "" }
    }

    def_WriteBanner -Title "VIA FlowSystem · v025 Summary"
    $summary | Format-Table -AutoSize -Wrap
    $totalApply = @($summary | ForEach-Object { $_.Applied } | Measure-Object -Sum).Sum
    $totalNotFound = @($summary | ForEach-Object { $_.NotFound } | Measure-Object -Sum).Sum
    Write-Host ("def Reroutes to apply : {0}" -f $totalApply) -ForegroundColor White
    Write-Host ("def Not found         : {0}" -f $totalNotFound) -ForegroundColor White
    Write-Host ""
    if ($Apply) {
        Write-Host "def Applied. Backups written next to each source (.v024pre.<stamp>.bak)." -ForegroundColor Green
        Write-Host "def Next: re-run the v024 scanner. Expect Pending=0 -> CLEAR_ACTIVATION_ALLOWED." -ForegroundColor Yellow
    }
    else {
        Write-Host "def DRY-RUN complete. Nothing was written. Re-run with -Apply to commit:" -ForegroundColor Yellow
        Write-Host "def   .\Invoke-VIA-FlowSystem-ApplyPatches-v025.ps1 -Apply" -ForegroundColor Yellow
    }
    if ($totalNotFound -gt 0) {
        Write-Host "def Some NOT_FOUND: those lines may already differ; review before -Apply." -ForegroundColor Yellow
    }
}

try {
    def_Main
}
catch {
    Write-Host ""
    Write-Host ("=" * 84) -ForegroundColor DarkRed
    Write-Host "def OUTER SAFE CATCH" -ForegroundColor Red
    Write-Host ("=" * 84) -ForegroundColor DarkRed
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "def PowerShell remains open. No activation." -ForegroundColor Yellow
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
