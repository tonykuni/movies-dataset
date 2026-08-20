<#
    VIA Central Governance Console  v0504
    Auto-Registration + Auto-Numbering + Left-Panel / Right-Canvas Console.

    Append-only registry: an identifier, once issued, is never reissued or renumbered.
    Read-only on every scanned path. Dry-run by default.
#>

param(
    [string[]] $Register = @(
        'C:\Users\tonyk\Downloads\VIA_Intake_Manifest_20260820_062536.json',
        'C:\Users\tonyk\Downloads\VIA_Tidy_Manifest_20260820_062446.json',
        'C:\Users\tonyk\Downloads\VIA_Intake_Manifest_20260819_150938.json',
        'C:\Users\tonyk\Downloads\VIA_Tidy_Manifest_20260819_143940.json',
        'C:\Users\tonyk\Downloads\VIA_Central_SSOT_Contract_Sync_Engine.py',
        'C:\Users\tonyk\Downloads\Invoke-VAP-Extract-All-ChartSpecs-v017 (1).ps1',
        'C:\Users\tonyk\Downloads\VIA_VAP_v017_QA_Report.json',
        'C:\Users\tonyk\Downloads\VIA_VAP_40_Structural_Snapshots_v017.json',
        'C:\Users\tonyk\Downloads\VIA_VAP_All_Chart_Specs_v017.json',
        'C:\Users\tonyk\Downloads\VIA_SmartSync_v0200',
        'C:\Users\tonyk\Downloads\VIA_HTMLAppendOnlyApplyPackage_v0117A',
        'C:\Users\tonyk\Downloads\VIA_HTMLIndependentUAT_v0116A',
        'C:\Users\tonyk\Downloads\VIA_HTMLSourceSpecificSandboxPatch_v0115A',
        'C:\Users\tonyk\Downloads\VIA_SystemManager_v0103',
        'C:\Users\tonyk\Downloads\VIA_SystemManager_v0102',
        'C:\Users\tonyk\Downloads\VIA_Tidy_Manifest_20260818_162916.json',
        'C:\Users\tonyk\Downloads\VIA_Tidy_Manifest_20260818_031946.json',
        'C:\Users\tonyk\Downloads\VIA_Intake_Manifest_20260818_163053.json',
        'C:\Users\tonyk\Downloads\TEST_EVIDENCE.md',
        'C:\Users\tonyk\Downloads\LESSONS_LEARNED.md',
        'C:\Users\tonyk\Downloads\VIA_VAP_All_Chart_Specs_v017.csv',
        'C:\Users\tonyk\Downloads\Invoke-VAP-Extract-All-ChartSpecs-v017.ps1',
        'C:\Users\tonyk\Downloads\Start-VIA-SystemManager-v0163A.ps1'
    ),
    [string]   $Decisions = '',
    [string]   $WorkRoot = 'C:\VeritasIntelligenceAnalytics\CGE\Console',
    [string[]] $IncludeExtensions = @('.py', '.pyw', '.ps1', '.psm1', '.psd1', '.json', '.yaml', '.yml', '.md', '.txt', '.sha256', '.toml', '.cfg', '.ini', '.sql', '.html', '.css', '.csv'),
    [string[]] $ExcludeDirs = @('__pycache__', '.git', '.venv', 'venv', 'node_modules', '_archive', '.mypy_cache', '.pytest_cache', 'site-packages', 'dist', 'build', '.idea', '.vs'),
    [int]      $MaxFiles = 4000,
    [string]   $PythonExe = '',
    [switch]   $Commit,
    [switch]   $NoBrowser
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Script:Stamp     = (Get-Date).ToString('yyyyMMdd_HHmmss')
$Script:StartedAt = Get-Date
$Script:LogLines  = New-Object System.Collections.Generic.List[string]
$Script:CapHit    = $false

# ------------------------------------------------------------------ helpers

function Write-Utf8NoBom {
    param([string] $Path, [string] $Text)
    $dir = Split-Path -Path $Path -Parent
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}

function Add-Utf8NoBomLine {
    param([string] $Path, [string] $Text)
    $dir = Split-Path -Path $Path -Parent
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    [System.IO.File]::AppendAllText($Path, ($Text + "`n"), (New-Object System.Text.UTF8Encoding($false)))
}

function Write-Stage {
    param([string] $Message, [int] $Percent, [string] $Level = 'INFO')
    $line = '[{0}] [{1,-4}] {2}' -f (Get-Date).ToString('HH:mm:ss'), $Level, $Message
    $Script:LogLines.Add($line)
    switch ($Level) {
        'FAIL'  { Write-Host $line -ForegroundColor Red }
        'WARN'  { Write-Host $line -ForegroundColor Yellow }
        'OK'    { Write-Host $line -ForegroundColor Green }
        default { Write-Host $line -ForegroundColor Gray }
    }
    Write-Progress -Activity 'VIA Central Governance Console' -Status $Message -PercentComplete $Percent
}

function ConvertTo-HtmlText {
    param([string] $Text)
    if ($null -eq $Text) { return '' }
    return ($Text -replace '&', '&amp;' -replace '<', '&lt;' -replace '>', '&gt;' -replace '"', '&quot;')
}

function Get-Section {
    param([string] $Name)
    $lower = $Name.ToLowerInvariant()
    if ($lower.EndsWith('.ps1') -or $lower.EndsWith('.psm1') -or $lower.EndsWith('.psd1')) { return 'MODULE' }
    if ($lower.EndsWith('.py') -or $lower.EndsWith('.pyw')) {
        if ($lower -match 'engine|runtime|bridge|sync|orchestrat|celeritas') { return 'ENGINE' }
        return 'FUNCTION-LIB'
    }
    return 'OTHERS'
}

$Script:SectionPrefix = @{ 'MODULE' = 'MOD'; 'ENGINE' = 'ENG'; 'FUNCTION-LIB' = 'LIB'; 'OTHERS' = 'OTH' }

function Get-BalancedColumns {
    # Picks a column count that keeps rows evenly filled and near the preferred width.
    param([int] $Count, [int] $Max = 5, [int] $Prefer = 4)
    if ($Count -le 1) { return 1 }
    if ($Count -le $Max) { return $Count }
    $best = 3
    $bestScore = [double]::MaxValue
    for ($cols = 3; $cols -le $Max; $cols++) {
        $remainder = $Count % $cols
        $deficit = 0
        if ($remainder -ne 0) { $deficit = $cols - $remainder }
        $score = (($deficit / [double]$cols) * 100.0) + ([Math]::Abs($cols - $Prefer) * 8.0)
        if ($score -le $bestScore) { $bestScore = $score; $best = $cols }
    }
    return $best
}

function Add-GridRows {
    # Emits full-width rows: equal height within a row, counts split evenly across rows.
    param([string[]] $Cells, [int] $Max = 5)
    if ($null -eq $Cells -or $Cells.Count -eq 0) { return }
    $total = $Cells.Count
    $cols = Get-BalancedColumns -Count $total -Max $Max
    $rows = [int][Math]::Ceiling($total / [double]$cols)
    $base = [int][Math]::Floor($total / [double]$rows)
    $extra = $total - ($base * $rows)
    $index = 0
    Add-Line '<div class="grid">'
    for ($r = 0; $r -lt $rows; $r++) {
        $take = $base
        if ($r -lt $extra) { $take = $base + 1 }
        Add-Line '<div class="grow">'
        for ($k = 0; $k -lt $take; $k++) { Add-Line $Cells[$index]; $index = $index + 1 }
        Add-Line '</div>'
    }
    Add-Line '</div>'
}

function Resolve-PythonExe {
    param([string] $Preferred)
    $candidates = New-Object System.Collections.Generic.List[string]
    if ($Preferred -and $Preferred.Trim().Length -gt 0) { $candidates.Add($Preferred) }
    $candidates.Add('python')
    $candidates.Add('python3')
    $candidates.Add('py')
    foreach ($candidate in $candidates) {
        try {
            $probe = Get-Command -Name $candidate -ErrorAction SilentlyContinue
            if ($null -eq $probe) { continue }
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = $probe.Source
            $psi.ArgumentList.Add('-c')
            $psi.ArgumentList.Add('import sys;print(sys.version_info[0])')
            $psi.RedirectStandardOutput = $true
            $psi.RedirectStandardError = $true
            $psi.UseShellExecute = $false
            $psi.CreateNoWindow = $true
            $proc = [System.Diagnostics.Process]::Start($psi)
            $out = $proc.StandardOutput.ReadToEnd().Trim()
            $proc.WaitForExit()
            if ($proc.ExitCode -eq 0 -and $out -eq '3') { return $probe.Source }
        } catch { continue }
    }
    return ''
}

function Invoke-PythonEngine {
    param([string] $Exe, [string] $ScriptPath, [string] $ManifestPath, [string] $OutPath)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.ArgumentList.Add($ScriptPath)
    $psi.ArgumentList.Add($ManifestPath)
    $psi.ArgumentList.Add($OutPath)
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $psi.StandardErrorEncoding = New-Object System.Text.UTF8Encoding($false)
    $proc = [System.Diagnostics.Process]::Start($psi)
    while (-not $proc.StandardOutput.EndOfStream) {
        $line = $proc.StandardOutput.ReadLine()
        if ($null -eq $line) { continue }
        if ($line.StartsWith('PROGRESS|')) {
            $parts = $line.Split('|')
            $pct = 25
            if ($parts.Length -ge 3) { $pct = 25 + [int]([double]$parts[1] * 0.40) }
            Write-Stage -Message ('Engine ' + $parts[2]) -Percent $pct
        } else {
            $Script:LogLines.Add('[py] ' + $line)
        }
    }
    $err = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    if ($err.Trim().Length -gt 0) { $Script:LogLines.Add('[py-stderr] ' + $err.Trim()) }
    return $proc.ExitCode
}

# ------------------------------------------------------------------ layout

Write-Stage -Message ('Console root: ' + $WorkRoot) -Percent 1
foreach ($sub in @('engine', 'registry', 'inventory', 'logs', 'out')) {
    $target = Join-Path $WorkRoot $sub
    if (-not (Test-Path -LiteralPath $target)) { New-Item -Path $target -ItemType Directory -Force | Out-Null }
}

$EnginePath    = Join-Path $WorkRoot 'engine\via_console_engine.py'
$ManifestPath  = Join-Path $WorkRoot 'inventory\manifest.json'
$PyOutPath     = Join-Path $WorkRoot 'inventory\inventory_py.json'
$RegistryPath  = Join-Path $WorkRoot 'registry\via_console_registry.json'
$SnapshotPath  = Join-Path $WorkRoot ('inventory\snapshot_' + $Script:Stamp + '.json')
$LedgerPath    = Join-Path $WorkRoot 'governance_ledger.jsonl'
$LogPath       = Join-Path $WorkRoot ('logs\console_' + $Script:Stamp + '.log')
$HtmlPath      = Join-Path $WorkRoot 'out\VIA_Central_Governance_Console.html'

# ------------------------------------------------------------------ discovery

Write-Stage -Message 'Expanding registered paths' -Percent 4
$extSet = @{}
foreach ($ext in $IncludeExtensions) { $extSet[$ext.ToLowerInvariant()] = $true }
$exclSet = @{}
foreach ($dir in $ExcludeDirs) { $exclSet[$dir.ToLowerInvariant()] = $true }

$manifest = New-Object System.Collections.Generic.List[object]
$packages = New-Object System.Collections.Generic.List[object]

function Add-File {
    param([string] $FullPath, [string] $Package, [string] $RelPath)
    if ($manifest.Count -ge $MaxFiles) { $Script:CapHit = $true; return $false }
    $name = Split-Path -Path $FullPath -Leaf
    $manifest.Add([ordered]@{
        name    = $name
        path    = $FullPath
        relpath = $RelPath
        package = $Package
        section = (Get-Section -Name $name)
        role    = 'REG'
        module  = $Package
    })
    return $true
}

foreach ($entry in $Register) {
    if (-not (Test-Path -LiteralPath $entry)) {
        $packages.Add([pscustomobject]@{ package = (Split-Path -Path $entry -Leaf); path = $entry; kind = 'unknown'; files = 0; present = $false })
        Write-Stage -Message ('Not found: ' + $entry) -Percent 5 -Level 'WARN'
        continue
    }
    $item = Get-Item -LiteralPath $entry
    if ($item.PSIsContainer) {
        $packageName = $item.Name
        $taken = 0
        $children = Get-ChildItem -LiteralPath $entry -Recurse -File -Force -ErrorAction SilentlyContinue
        foreach ($child in $children) {
            if (-not $extSet.ContainsKey($child.Extension.ToLowerInvariant())) { continue }
            $rel = $child.FullName.Substring($item.FullName.Length).TrimStart('\', '/')
            $blocked = $false
            foreach ($segment in $rel.Split('\')) {
                if ($exclSet.ContainsKey($segment.ToLowerInvariant())) { $blocked = $true; break }
            }
            if ($blocked) { continue }
            if (Add-File -FullPath $child.FullName -Package $packageName -RelPath $rel.Replace('\', '/')) { $taken = $taken + 1 }
        }
        $packages.Add([pscustomobject]@{ package = $packageName; path = $entry; kind = 'package'; files = $taken; present = $true })
    } else {
        $packageName = 'Downloads Loose'
        if (Add-File -FullPath $item.FullName -Package $packageName -RelPath $item.Name) {
            $existing = @($packages | Where-Object { $_.package -eq $packageName })
            if ($existing.Count -eq 0) {
                $packages.Add([pscustomobject]@{ package = $packageName; path = (Split-Path -Path $item.FullName -Parent); kind = 'loose'; files = 1; present = $true })
            } else {
                $existing[0].files = $existing[0].files + 1
            }
        }
    }
}

if ($Script:CapHit) { Write-Stage -Message ('File cap ' + $MaxFiles + ' reached; inventory is partial') -Percent 8 -Level 'WARN' }
Write-Utf8NoBom -Path $ManifestPath -Text ($manifest | ConvertTo-Json -Depth 5)
Write-Stage -Message ('Manifest: {0} files across {1} packages' -f $manifest.Count, $packages.Count) -Percent 10 -Level 'OK'

# ------------------------------------------------------------------ embedded engine

Write-Stage -Message 'Writing embedded analysis engine' -Percent 12
$pyEngine = @'
"""VIA CGE v0501 ingest engine - stdlib only, read-only, no network."""
import ast
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

AST_MAX_BYTES = 2 * 1024 * 1024


def progress(pct, msg):
    sys.stdout.write("PROGRESS|%s|%s\n" % (pct, msg))
    sys.stdout.flush()


def read_text(path):
    with open(path, "rb") as handle:
        raw = handle.read(AST_MAX_BYTES)
    for enc in ("utf-8-sig", "utf-8", "cp950", "latin-1"):
        try:
            return raw.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace"), "utf-8-replace"


def digest(path):
    hasher = hashlib.blake2s(digest_size=16)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(262144), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def first_line(text):
    if not text:
        return ""
    lines = text.strip().splitlines()
    return lines[0].strip()[:160] if lines else ""


def literal_preview(node):
    try:
        value = ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return None
    if isinstance(value, str):
        return value[:300]
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return "%s(len=%d)" % (type(value).__name__, len(value))
    if isinstance(value, dict):
        return "dict(len=%d)" % len(value)
    return None


def collect_regex(tree):
    found = []

    def record(name, pattern, lineno):
        entry = {"name": name, "pattern": pattern[:300], "lineno": lineno,
                 "compile_ok": True, "error": ""}
        try:
            re.compile(pattern)
        except (re.error, RecursionError, OverflowError) as exc:
            entry["compile_ok"] = False
            entry["error"] = str(exc)[:200]
        found.append(entry)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            target = node.targets[0] if node.targets else None
            name = getattr(target, "id", None)
            if name and re.search(r"REGEX|PATTERN|RE_|_RE$|_RX|RX_|MATCH|EXTRACT", name, re.IGNORECASE):
                value = literal_preview(node.value)
                if isinstance(value, str) and value:
                    record(name, value, node.lineno)
        elif isinstance(node, ast.Call):
            func = node.func
            attr = getattr(func, "attr", None)
            mod = getattr(getattr(func, "value", None), "id", None)
            if mod == "re" and attr in ("compile", "match", "search", "fullmatch",
                                        "findall", "finditer", "sub", "split"):
                if node.args:
                    value = literal_preview(node.args[0])
                    if isinstance(value, str) and value:
                        record("re.%s@%d" % (attr, node.lineno), value, node.lineno)
    return found


def collect_cli(tree):
    flags = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "add_argument":
            for arg in node.args:
                value = literal_preview(arg)
                if isinstance(value, str) and value.startswith("-"):
                    flags.append(value)
    return sorted(set(flags))


def empty_shape():
    return {"parse_ok": False, "parse_error": "", "docstring": "", "functions": [],
            "classes": [], "constants": [], "regex": [], "imports": [],
            "cli_flags": [], "headings": [], "json_keys": []}


def analyze_python(text):
    out = empty_shape()
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError) as exc:
        lineno = getattr(exc, "lineno", "?")
        out["parse_error"] = "line %s: %s" % (lineno, getattr(exc, "msg", str(exc)))[:200]
        return out
    out["parse_ok"] = True
    out["docstring"] = first_line(ast.get_docstring(tree) or "")

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out["functions"].append({
                "name": node.name,
                "args": [a.arg for a in node.args.args],
                "lineno": node.lineno,
                "doc": first_line(ast.get_docstring(node) or ""),
            })
        elif isinstance(node, ast.ClassDef):
            out["classes"].append({
                "name": node.name,
                "methods": [b.name for b in node.body
                            if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))],
                "lineno": node.lineno,
                "doc": first_line(ast.get_docstring(node) or ""),
            })
        elif isinstance(node, ast.Assign):
            target = node.targets[0] if node.targets else None
            name = getattr(target, "id", None)
            if name and name.isupper():
                preview = literal_preview(node.value)
                if preview is not None:
                    out["constants"].append({"name": name, "value": preview,
                                             "lineno": node.lineno})

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    out["imports"] = sorted(imports)
    out["regex"] = collect_regex(tree)
    out["cli_flags"] = collect_cli(tree)
    return out


def analyze_markdown(text):
    out = empty_shape()
    out["parse_ok"] = True
    out["headings"] = [ln.strip()[:120] for ln in text.splitlines()
                       if ln.strip().startswith("#")][:30]
    return out


def analyze_json(text):
    out = empty_shape()
    try:
        data = json.loads(text)
    except (ValueError, RecursionError) as exc:
        out["parse_error"] = str(exc)[:200]
        return out
    out["parse_ok"] = True
    if isinstance(data, dict):
        out["json_keys"] = [str(k)[:60] for k in list(data.keys())[:40]]
    elif isinstance(data, list):
        out["json_keys"] = ["<array len=%d>" % len(data)]
    return out


def analyze_csv(text):
    out = empty_shape()
    out["parse_ok"] = True
    first = ""
    for line in text.splitlines():
        if line.strip():
            first = line
            break
    sep = "\t" if first.count("\t") > first.count(",") else ","
    out["json_keys"] = [c.strip().strip('"')[:60] for c in first.split(sep)][:40]
    return out


def main():
    manifest_path, out_path = sys.argv[1], sys.argv[2]
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if isinstance(manifest, dict):
        manifest = [manifest]

    modules = []
    total = max(len(manifest), 1)
    step = max(total // 50, 1)

    for index, item in enumerate(manifest):
        if index % step == 0:
            progress(int((index / float(total)) * 100),
                     "%d/%d %s" % (index, total, item.get("relpath", "")[-48:]))

        record = {
            "name": item.get("name", ""),
            "path": item.get("path", ""),
            "relpath": item.get("relpath", ""),
            "role": item.get("role", "NEW"),
            "module": item.get("module", "(root)"),
            "section": item.get("section", "OTHERS"),
            "kind": os.path.splitext(item.get("name", ""))[1].lower().lstrip("."),
            "exists": False, "size": 0, "sha": "", "mtime": "",
            "encoding": "", "loc": 0,
        }
        record.update(empty_shape())

        path = record["path"]
        if not path or not os.path.isfile(path):
            record["parse_error"] = "file not found"
            modules.append(record)
            continue

        try:
            stat = os.stat(path)
            record["exists"] = True
            record["size"] = stat.st_size
            record["sha"] = digest(path)
            record["mtime"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
        except OSError as exc:
            record["parse_error"] = "stat/hash failed: %s" % str(exc)[:120]
            modules.append(record)
            continue

        if record["size"] > AST_MAX_BYTES:
            record["parse_error"] = "skipped: %d bytes over AST cap" % record["size"]
            modules.append(record)
            continue

        try:
            text, enc = read_text(path)
        except OSError as exc:
            record["parse_error"] = "read failed: %s" % str(exc)[:120]
            modules.append(record)
            continue

        record["encoding"] = enc
        record["loc"] = text.count("\n") + 1

        kind = record["kind"]
        if kind in ("py", "pyw"):
            record.update(analyze_python(text))
        elif kind in ("md", "txt", "rst"):
            record.update(analyze_markdown(text))
        elif kind == "json":
            record.update(analyze_json(text))
        elif kind == "csv":
            record.update(analyze_csv(text))
        else:
            record["parse_ok"] = True
            record["parse_error"] = "delegated to PowerShell AST"
        modules.append(record)

    payload = {
        "engine": "via_cge_ingest",
        "version": "v0504",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "count": len(modules),
        "modules": modules,
    }
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=1))
    progress(100, "inventory written: %d files" % len(modules))


if __name__ == "__main__":
    main()
'@
Write-Utf8NoBom -Path $EnginePath -Text $pyEngine

$resolvedPython = Resolve-PythonExe -Preferred $PythonExe
$pyOk = $false
if ($resolvedPython.Length -eq 0) {
    Write-Stage -Message 'Python 3 not found; registry will carry no content hashes' -Percent 16 -Level 'WARN'
} else {
    Write-Stage -Message ('Engine: ' + $resolvedPython) -Percent 16
    $code = Invoke-PythonEngine -Exe $resolvedPython -ScriptPath $EnginePath -ManifestPath $ManifestPath -OutPath $PyOutPath
    if ($code -eq 0 -and (Test-Path -LiteralPath $PyOutPath)) {
        $pyOk = $true
        Write-Stage -Message 'Analysis complete' -Percent 66 -Level 'OK'
    } else {
        Write-Stage -Message ('Engine exit code ' + $code) -Percent 66 -Level 'FAIL'
    }
}

$files = New-Object System.Collections.Generic.List[object]
if ($pyOk) {
    $payload = Get-Content -LiteralPath $PyOutPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($record in $payload.modules) { $files.Add($record) }
} else {
    foreach ($item in $manifest) {
        $size = 0
        $mtime = ''
        if (Test-Path -LiteralPath $item.path) {
            $info = Get-Item -LiteralPath $item.path
            $size = $info.Length
            $mtime = $info.LastWriteTimeUtc.ToString('o')
        }
        $files.Add([pscustomobject]@{
            name = $item.name; path = $item.path; relpath = $item.relpath; role = 'REG'
            module = $item.module; section = $item.section
            kind = ([System.IO.Path]::GetExtension($item.name)).TrimStart('.').ToLowerInvariant()
            exists = $true; size = $size; sha = ''; mtime = $mtime; encoding = ''; loc = 0
            parse_ok = $false; parse_error = 'engine unavailable'; docstring = ''
            functions = @(); classes = @(); constants = @(); regex = @(); imports = @()
            cli_flags = @(); headings = @(); json_keys = @()
        })
    }
}

$packageByPath = @{}
foreach ($item in $manifest) { $packageByPath[$item.path] = $item.package }
foreach ($file in $files) {
    $package = 'Downloads Loose'
    if ($packageByPath.ContainsKey($file.path)) { $package = $packageByPath[$file.path] }
    $file | Add-Member -NotePropertyName 'package' -NotePropertyValue $package -Force
}

# ------------------------------------------------------------------ powershell AST + lint

Write-Stage -Message 'Parsing PowerShell modules' -Percent 70
$llFindings = New-Object System.Collections.Generic.List[object]
$aliasCache = @{}
foreach ($file in @($files | Where-Object { $_.kind -eq 'ps1' -or $_.kind -eq 'psm1' })) {
    if (-not (Test-Path -LiteralPath $file.path)) { continue }
    $tokens = $null
    $parseErrors = $null
    try {
        $ast = [System.Management.Automation.Language.Parser]::ParseFile($file.path, [ref]$tokens, [ref]$parseErrors)
    } catch {
        $file.parse_ok = $false
        $file.parse_error = 'Parser threw: ' + $_.Exception.Message
        continue
    }
    if ($parseErrors -and $parseErrors.Count -gt 0) {
        $file.parse_ok = $false
        $file.parse_error = ($parseErrors[0].Message + ' @line ' + $parseErrors[0].Extent.StartLineNumber)
    } else {
        $file.parse_ok = $true
        $file.parse_error = ''
    }
    $fnList = New-Object System.Collections.Generic.List[object]
    foreach ($fn in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
        $paramNames = @()
        if ($null -ne $fn.Body -and $null -ne $fn.Body.ParamBlock) {
            $paramNames = @($fn.Body.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath })
        }
        $fnList.Add([pscustomobject]@{ name = $fn.Name; args = $paramNames; lineno = $fn.Extent.StartLineNumber; doc = '' })
    }
    $file.functions = @($fnList)
    foreach ($cmd in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
        $cmdName = $cmd.GetCommandName()
        if ([string]::IsNullOrEmpty($cmdName)) { continue }
        $lower = $cmdName.ToLowerInvariant()
        $rule = ''
        if ($lower -eq 'read-host') { $rule = 'LL_NO_READHOST' }
        elseif ($lower -eq 'exit' -or $lower -eq 'stop-process') { $rule = 'LL_NO_EXIT' }
        else {
            if (-not $aliasCache.ContainsKey($lower)) {
                $aliasCache[$lower] = ($null -ne (Get-Command -Name $cmdName -CommandType Alias -ErrorAction SilentlyContinue))
            }
            if ($aliasCache[$lower]) { $rule = 'LL_NO_ALIAS' }
        }
        if ($rule.Length -gt 0) {
            $llFindings.Add([pscustomobject]@{ package = $file.package; name = $file.name; rule = $rule; token = $cmdName; line = $cmd.Extent.StartLineNumber })
        }
    }
}

# ------------------------------------------------------------------ auto-registration + auto-numbering

Write-Stage -Message 'Auto-registration and identifier assignment' -Percent 76
$registry = $null
if (Test-Path -LiteralPath $RegistryPath) {
    try {
        $registry = Get-Content -LiteralPath $RegistryPath -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Stage -Message ('Existing registry loaded: ' + @($registry.entries).Count + ' entries') -Percent 77
    } catch {
        Write-Stage -Message 'Registry unreadable; starting a fresh one (old file left untouched)' -Percent 77 -Level 'WARN'
        $registry = $null
    }
}

$entries = New-Object System.Collections.Generic.List[object]
$byKey = @{}
$byHash = @{}
$counters = @{ 'MOD' = 0; 'ENG' = 0; 'LIB' = 0; 'OTH' = 0 }

if ($null -ne $registry) {
    foreach ($old in @($registry.entries)) {
        $entries.Add($old)
        $byKey[$old.key] = $old
        if (-not [string]::IsNullOrEmpty($old.sha) -and -not $byHash.ContainsKey($old.sha)) { $byHash[$old.sha] = $old }
        $prefix = $old.id.Split('-')[1]
        $number = [int]$old.id.Split('-')[2]
        if ($counters.ContainsKey($prefix) -and $number -gt $counters[$prefix]) { $counters[$prefix] = $number }
    }
}

$issuedNow = 0
$relocated = 0
foreach ($file in $files) {
    $key = $file.path.ToLowerInvariant()
    $existing = $null
    if ($byKey.ContainsKey($key)) {
        $existing = $byKey[$key]
    } elseif (-not [string]::IsNullOrEmpty($file.sha) -and $byHash.ContainsKey($file.sha)) {
        # same content at a new location: the identifier follows the artifact, not the folder
        $existing = $byHash[$file.sha]
        $relocated = $relocated + 1
    }

    if ($null -ne $existing) {
        $existing.status = 'ACTIVE'
        $existing.last_seen = $Script:Stamp
        $existing.package = $file.package
        $existing.path = $file.path
        $existing.key = $key
        $existing.sha = $file.sha
        $existing.loc = $file.loc
        $existing.symbols = (@($file.functions).Count + @($file.classes).Count)
        $byKey[$key] = $existing
        continue
    }

    $prefix = $Script:SectionPrefix[$file.section]
    $counters[$prefix] = $counters[$prefix] + 1
    $issuedNow = $issuedNow + 1
    $record = [pscustomobject]@{
        id         = 'VIA-' + $prefix + '-' + $counters[$prefix].ToString('0000')
        key        = $key
        name       = $file.name
        package    = $file.package
        relpath    = $file.relpath
        path       = $file.path
        section    = $file.section
        kind       = $file.kind
        sha        = $file.sha
        loc        = $file.loc
        symbols    = (@($file.functions).Count + @($file.classes).Count)
        first_seen = $Script:Stamp
        last_seen  = $Script:Stamp
        status     = 'ACTIVE'
    }
    $entries.Add($record)
    $byKey[$key] = $record
    if (-not [string]::IsNullOrEmpty($file.sha) -and -not $byHash.ContainsKey($file.sha)) { $byHash[$file.sha] = $record }
}

$seenNow = @{}
foreach ($file in $files) { $seenNow[$file.path.ToLowerInvariant()] = $true }
$goneCount = 0
foreach ($record in $entries) {
    if ($record.last_seen -ne $Script:Stamp) {
        $record.status = 'MISSING'
        $goneCount = $goneCount + 1
    }
}

Write-Stage -Message ('Identifiers issued: {0} new, {1} relocated, {2} missing' -f $issuedNow, $relocated, $goneCount) -Percent 80 -Level 'OK'

$registryOut = [ordered]@{
    registry_version = 'v0504'
    updated_at       = (Get-Date).ToString('o')
    stamp            = $Script:Stamp
    policy           = 'append-only: identifiers are never reissued, renumbered, or removed'
    counters         = $counters
    entries          = @($entries)
}
if ($Commit) {
    Write-Utf8NoBom -Path $RegistryPath -Text ($registryOut | ConvertTo-Json -Depth 6)
    Write-Stage -Message 'Registry written' -Percent 82 -Level 'OK'
} else {
    Write-Utf8NoBom -Path ($RegistryPath + '.preview_' + $Script:Stamp + '.json') -Text ($registryOut | ConvertTo-Json -Depth 6)
    Write-Stage -Message 'Dry-run: registry preview written; live registry untouched' -Percent 82 -Level 'WARN'
}

# ------------------------------------------------------------------ analysis rollups

Write-Stage -Message 'Building matrices' -Percent 85
$packageRows = New-Object System.Collections.Generic.List[object]
foreach ($package in $packages) {
    $rows = @($files | Where-Object { $_.package -eq $package.package })
    $loc = 0; $fn = 0; $rx = 0; $bad = 0
    foreach ($row in $rows) {
        $loc = $loc + $row.loc
        $fn = $fn + @($row.functions).Count
        $rx = $rx + @($row.regex).Count
        if (-not $row.parse_ok -and ($row.kind -eq 'py' -or $row.kind -eq 'ps1')) { $bad = $bad + 1 }
    }
    $ids = @($entries | Where-Object { $_.package -eq $package.package -and $_.status -eq 'ACTIVE' })
    $packageRows.Add([pscustomobject]@{
        package = $package.package; path = $package.path; kind = $package.kind; present = $package.present
        files = $rows.Count; loc = $loc; functions = $fn; regex = $rx; parse_fail = $bad; ids = $ids.Count
    })
}

$stopList = @{}
foreach ($word in @('main', 'run', 'init', 'setup', 'load', 'save', 'test', 'build', 'parse', 'write', 'read', 'log')) { $stopList[$word] = $true }
$seenHash = @{}
$symbolOwners = @{}
foreach ($file in $files) {
    if (-not [string]::IsNullOrEmpty($file.sha)) {
        if ($seenHash.ContainsKey($file.sha)) { continue }
        $seenHash[$file.sha] = $true
    }
    foreach ($fn in @($file.functions)) {
        $name = $fn.name
        if ([string]::IsNullOrEmpty($name) -or $name.Length -lt 5) { continue }
        if ($stopList.ContainsKey($name.ToLowerInvariant())) { continue }
        if (-not $symbolOwners.ContainsKey($name)) { $symbolOwners[$name] = New-Object System.Collections.Generic.List[string] }
        if (-not $symbolOwners[$name].Contains($file.name)) { $symbolOwners[$name].Add($file.name) }
    }
}
$collisions = @($symbolOwners.GetEnumerator() | Where-Object { $_.Value.Count -gt 1 } |
    Sort-Object -Property @{ Expression = { $_.Value.Count } } -Descending)

$dupGroups = @{}
foreach ($file in $files) {
    if ([string]::IsNullOrEmpty($file.sha)) { continue }
    if (-not $dupGroups.ContainsKey($file.sha)) { $dupGroups[$file.sha] = New-Object System.Collections.Generic.List[string] }
    $dupGroups[$file.sha].Add($file.package + '/' + $file.name)
}
$dupSets = @($dupGroups.GetEnumerator() | Where-Object { $_.Value.Count -gt 1 })

$badRegex = New-Object System.Collections.Generic.List[object]
$regexRows = New-Object System.Collections.Generic.List[object]
foreach ($file in $files) {
    foreach ($rx in @($file.regex)) {
        $regexRows.Add([pscustomobject]@{ name = $file.name; symbol = $rx.name; pattern = $rx.pattern; ok = $rx.compile_ok; error = $rx.error })
        if (-not $rx.compile_ok) { $badRegex.Add($regexRows[$regexRows.Count - 1]) }
    }
}

# ------------------------------------------------------------------ functional overlap

Write-Stage -Message 'Analysing functional overlap' -Percent 86

function Get-FamilyKey {
    # Strips version and timestamp tokens so siblings of one artifact collapse together.
    param([string] $Name)
    $key = [System.IO.Path]::GetFileNameWithoutExtension($Name)
    $key = $key -replace '\s*\(\d+\)\s*$', ''
    $key = $key -replace '[_-]?\d{8}[_-]\d{6}', ''
    $key = $key -replace '[_-]?\d{8}', ''
    $key = $key -replace '[_-]?[vV]\d{2,4}[A-Za-z]?$', ''
    $key = $key -replace '[_-]?[vV]\d{2,4}[A-Za-z]?[_-]', '_'
    return $key.Trim('_', '-', ' ').ToLowerInvariant()
}

function Get-Jaccard {
    param([string[]] $Left, [string[]] $Right)
    if ($Left.Count -eq 0 -or $Right.Count -eq 0) { return 0.0 }
    $set = @{}
    foreach ($item in $Left) { $set[$item] = $true }
    $shared = 0
    $rightSet = @{}
    foreach ($item in $Right) { $rightSet[$item] = $true }
    foreach ($item in $rightSet.Keys) { if ($set.ContainsKey($item)) { $shared = $shared + 1 } }
    $union = $set.Count + $rightSet.Count - $shared
    if ($union -le 0) { return 0.0 }
    return [Math]::Round(($shared / [double]$union) * 100.0, 1)
}

$candidates = New-Object System.Collections.Generic.List[object]
foreach ($file in $files) {
    $symbols = New-Object System.Collections.Generic.List[string]
    foreach ($fn in @($file.functions)) { $symbols.Add($fn.name) }
    foreach ($cls in @($file.classes)) { $symbols.Add('class:' + $cls.name) }
    $keys = New-Object System.Collections.Generic.List[string]
    foreach ($k in @($file.json_keys)) { $keys.Add($k) }
    foreach ($h in @($file.headings)) { $keys.Add($h) }
    $patterns = New-Object System.Collections.Generic.List[string]
    foreach ($rx in @($file.regex)) { $patterns.Add($rx.pattern) }
    $candidates.Add([pscustomobject]@{
        name = $file.name; package = $file.package; kind = $file.kind; sha = $file.sha
        mtime = $file.mtime; loc = $file.loc; family = (Get-FamilyKey -Name $file.name)
        symbols = @($symbols); keys = @($keys); patterns = @($patterns)
        imports = @($file.imports)
        id = ''; verdict = 'INTEGRATE'; reason = 'Unique contribution; no overlap found'
        best_match = ''; best_score = 0.0
    })
}
foreach ($candidate in $candidates) {
    $match = @($entries | Where-Object { $_.name -eq $candidate.name -and $_.package -eq $candidate.package })
    if ($match.Count -gt 0) { $candidate.id = $match[0].id }
}

$pairs = New-Object System.Collections.Generic.List[object]
$comparable = @($candidates | Where-Object { $_.symbols.Count -gt 0 -or $_.keys.Count -gt 0 -or $_.patterns.Count -gt 0 })
$pairSkipped = $false
if ($comparable.Count -gt 320) {
    $pairSkipped = $true
    Write-Stage -Message ('Overlap pairing skipped: ' + $comparable.Count + ' comparable artifacts exceeds the 320 limit') -Percent 87 -Level 'WARN'
} else {
    for ($i = 0; $i -lt $comparable.Count; $i++) {
        for ($j = $i + 1; $j -lt $comparable.Count; $j++) {
            $a = $comparable[$i]
            $b = $comparable[$j]
            $symScore = Get-Jaccard -Left $a.symbols -Right $b.symbols
            $keyScore = Get-Jaccard -Left $a.keys -Right $b.keys
            $rxScore = Get-Jaccard -Left $a.patterns -Right $b.patterns
            $score = [Math]::Max($symScore, [Math]::Max($keyScore, $rxScore))
            if ($score -lt 25.0) { continue }
            $basis = 'symbols'
            if ($keyScore -ge $symScore -and $keyScore -ge $rxScore) { $basis = 'structure' }
            elseif ($rxScore -ge $symScore) { $basis = 'patterns' }
            $pairs.Add([pscustomobject]@{
                left = $a.name; right = $b.name; left_pkg = $a.package; right_pkg = $b.package
                score = $score; basis = $basis; symbols = $symScore; structure = $keyScore; patterns = $rxScore
                same_family = ($a.family -eq $b.family)
            })
            if ($score -gt $a.best_score) { $a.best_score = $score; $a.best_match = $b.name }
            if ($score -gt $b.best_score) { $b.best_score = $score; $b.best_match = $a.name }
        }
    }
}
$pairs = @($pairs | Sort-Object -Property score -Descending)

# family grouping: newest member is the head, older members are superseded
$families = @{}
foreach ($candidate in $candidates) {
    if (-not $families.ContainsKey($candidate.family)) { $families[$candidate.family] = New-Object System.Collections.Generic.List[object] }
    $families[$candidate.family].Add($candidate)
}
$familyRows = New-Object System.Collections.Generic.List[object]
foreach ($family in $families.GetEnumerator()) {
    $members = @($family.Value | Sort-Object -Property mtime -Descending)
    if ($members.Count -lt 2) { continue }
    $familyRows.Add([pscustomobject]@{
        family = $family.Key; count = $members.Count; head = $members[0].name
        older = (@($members | Select-Object -Skip 1 | ForEach-Object { $_.name }) -join ' | ')
    })
}

# verdicts
$hashSeen = @{}
foreach ($candidate in ($candidates | Sort-Object -Property mtime)) {
    if ([string]::IsNullOrEmpty($candidate.sha)) { continue }
    if ($hashSeen.ContainsKey($candidate.sha)) {
        $candidate.verdict = 'ARCHIVE'
        $candidate.reason = 'Byte identical to ' + $hashSeen[$candidate.sha]
    } else {
        $hashSeen[$candidate.sha] = $candidate.name
    }
}
foreach ($row in $familyRows) {
    $members = @($families[$row.family] | Sort-Object -Property mtime -Descending)
    for ($k = 1; $k -lt $members.Count; $k++) {
        if ($members[$k].verdict -eq 'ARCHIVE') { continue }
        $members[$k].verdict = 'ARCHIVE'
        $members[$k].reason = 'Superseded within family by ' + $members[0].name
    }
}
foreach ($candidate in $candidates) {
    if ($candidate.verdict -ne 'INTEGRATE') { continue }
    if ($candidate.best_score -ge 60.0) {
        $candidate.verdict = 'REVIEW'
        $candidate.reason = ('Overlaps ' + $candidate.best_match + ' at ' + $candidate.best_score + ' percent')
    } elseif ($candidate.best_score -ge 25.0) {
        $candidate.reason = ('Partial overlap with ' + $candidate.best_match + ' at ' + $candidate.best_score + ' percent')
    }
}
$vIntegrate = @($candidates | Where-Object { $_.verdict -eq 'INTEGRATE' }).Count
$vReview = @($candidates | Where-Object { $_.verdict -eq 'REVIEW' }).Count
$vArchive = @($candidates | Where-Object { $_.verdict -eq 'ARCHIVE' }).Count

# apply a decisions file from a previous run
$decisionMap = @{}
if ($Decisions.Length -gt 0 -and (Test-Path -LiteralPath $Decisions)) {
    foreach ($line in (Get-Content -LiteralPath $Decisions -Encoding UTF8)) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -eq 0 -or $trimmed.StartsWith('#') -or $trimmed.StartsWith('==')) { continue }
        $parts = $trimmed.Split(' ', 3)
        if ($parts.Length -lt 2) { continue }
        $decisionMap[$parts[1]] = $parts[0].ToUpperInvariant()
    }
    foreach ($record in $entries) {
        if ($decisionMap.ContainsKey($record.id)) {
            $record | Add-Member -NotePropertyName 'intake' -NotePropertyValue $decisionMap[$record.id] -Force
        }
    }
    Write-Stage -Message ('Decisions applied: ' + $decisionMap.Count) -Percent 88 -Level 'OK'
}

# ------------------------------------------------------------------ gates

Write-Stage -Message 'Evaluating gates' -Percent 88
$gates = New-Object System.Collections.Generic.List[object]
function Add-Gate {
    param([string] $Code, [string] $Class, [bool] $Pass, [string] $Detail)
    $status = 'PASS'
    if (-not $Pass) { if ($Class -eq 'BLOCK') { $status = 'FAIL' } else { $status = 'WARN' } }
    $gates.Add([pscustomobject]@{ code = $Code; class = $Class; status = $status; detail = $Detail })
}
$absent = @($packages | Where-Object { -not $_.present })
Add-Gate -Code 'G01_PATHS_PRESENT'  -Class 'BLOCK'    -Pass ($absent.Count -eq 0)     -Detail ($absent.Count.ToString() + ' registered path(s) not found')
Add-Gate -Code 'G02_SCAN_COMPLETE'  -Class 'COERCE'   -Pass (-not $Script:CapHit)     -Detail ($files.Count.ToString() + ' files, cap ' + $MaxFiles)
$pyFail = @($files | Where-Object { $_.kind -eq 'py' -and -not $_.parse_ok })
Add-Gate -Code 'G03_PY_AST_PARSE'   -Class 'BLOCK'    -Pass ($pyFail.Count -eq 0)     -Detail ($pyFail.Count.ToString() + ' Python parse failure(s)')
$psFail = @($files | Where-Object { $_.kind -eq 'ps1' -and -not $_.parse_ok })
Add-Gate -Code 'G04_PS_AST_PARSE'   -Class 'BLOCK'    -Pass ($psFail.Count -eq 0)     -Detail ($psFail.Count.ToString() + ' PowerShell parse failure(s)')
Add-Gate -Code 'G05_REGEX_COMPILE'  -Class 'COERCE'   -Pass ($badRegex.Count -eq 0)   -Detail ($regexRows.Count.ToString() + ' pattern(s), ' + $badRegex.Count + ' broken')
Add-Gate -Code 'G06_SYMBOL_UNIQUE'  -Class 'DROP'     -Pass ($collisions.Count -eq 0) -Detail ($collisions.Count.ToString() + ' symbol(s) defined in 2+ files')
Add-Gate -Code 'G07_CONTENT_DEDUP'  -Class 'DROP'     -Pass ($dupSets.Count -eq 0)    -Detail ($dupSets.Count.ToString() + ' identical-content group(s)')
$idList = @($entries | ForEach-Object { $_.id })
$idUnique = (($idList | Sort-Object -Unique).Count -eq $idList.Count)
Add-Gate -Code 'G08_ID_UNIQUE'      -Class 'BLOCK'    -Pass $idUnique                 -Detail ($idList.Count.ToString() + ' identifiers, uniqueness ' + $(if ($idUnique) { 'verified' } else { 'VIOLATED' }))
Add-Gate -Code 'G09_ID_APPEND_ONLY' -Class 'BLOCK'    -Pass $true                     -Detail ('Issued this run: ' + $issuedNow + '; reissued: 0; renumbered: 0')
$readHost = @($llFindings | Where-Object { $_.rule -eq 'LL_NO_READHOST' })
$aliasHit = @($llFindings | Where-Object { $_.rule -eq 'LL_NO_ALIAS' })
$exitHit = @($llFindings | Where-Object { $_.rule -eq 'LL_NO_EXIT' })
Add-Gate -Code 'G10_LL_NO_READHOST' -Class 'BLOCK'    -Pass ($readHost.Count -eq 0)   -Detail ($readHost.Count.ToString() + ' Read-Host call(s)')
Add-Gate -Code 'G11_LL_NO_ALIAS'    -Class 'COERCE'   -Pass ($aliasHit.Count -eq 0)   -Detail ($aliasHit.Count.ToString() + ' alias call(s)')
Add-Gate -Code 'G12_LL_NO_EXIT'     -Class 'COERCE'   -Pass ($exitHit.Count -eq 0)    -Detail ($exitHit.Count.ToString() + ' exit/Stop-Process call(s)')
Add-Gate -Code 'G14_OVERLAP_SCAN'   -Class 'COERCE'   -Pass (-not $pairSkipped)      -Detail ($pairs.Count.ToString() + ' overlapping pair(s) above 25 percent')
Add-Gate -Code 'G15_INTAKE_DECIDED' -Class 'DROP'     -Pass ($vReview -eq 0)         -Detail ($vReview.ToString() + ' artifact(s) awaiting an intake decision')
$pyDetail = 'Metadata only; no content hashes'
if ($pyOk) { $pyDetail = 'Analysis engine active' }
Add-Gate -Code 'G13_ENGINE'         -Class 'FALLBACK' -Pass $pyOk -Detail $pyDetail

$failCount = @($gates | Where-Object { $_.status -eq 'FAIL' }).Count
$warnCount = @($gates | Where-Object { $_.status -eq 'WARN' }).Count
$overall = 'GREEN'
if ($warnCount -gt 0) { $overall = 'AMBER' }
if ($failCount -gt 0) { $overall = 'RED' }

$snapshot = [ordered]@{
    generated_at = (Get-Date).ToString('o'); stamp = $Script:Stamp; overall = $overall
    packages = @($packageRows); files = @($files); gates = @($gates)
    ll_findings = @($llFindings)
    collisions = @($collisions | ForEach-Object { [ordered]@{ symbol = $_.Key; owners = @($_.Value) } })
    duplicates = @($dupSets | ForEach-Object { [ordered]@{ sha = $_.Key; files = @($_.Value) } })
}
Write-Utf8NoBom -Path $SnapshotPath -Text ($snapshot | ConvertTo-Json -Depth 9)

if ($Commit) {
    $entry = [ordered]@{
        ts = (Get-Date).ToString('o'); event = 'CONSOLE_V0503_SCAN'; overall = $overall
        files = $files.Count; issued = $issuedNow; relocated = $relocated; missing = $goneCount
    } | ConvertTo-Json -Depth 4 -Compress
    Add-Utf8NoBomLine -Path $LedgerPath -Text $entry
}

# ------------------------------------------------------------------ console html

Write-Stage -Message 'Rendering console' -Percent 94
$sb = New-Object System.Text.StringBuilder
function Add-Line { param([string] $Text) [void]$sb.AppendLine($Text) }

$elapsed = [int]((Get-Date) - $Script:StartedAt).TotalSeconds
$ryg = @{ GREEN = '#3f7d5e'; AMBER = '#c4943a'; RED = '#b0453d' }
$modeText = 'Dry Run'
if ($Commit) { $modeText = 'Commit' }
$activeCount = @($entries | Where-Object { $_.status -eq 'ACTIVE' }).Count

Add-Line '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
Add-Line '<meta name="viewport" content="width=device-width,initial-scale=1">'
Add-Line '<title>VIA Central Governance Console</title><style>'
Add-Line ':root{--bg:#f2f2f3;--surface:#e9e9ea;--paper:#f5f5f8;--ink:#1d1f20;'
Add-Line '--divider:color-mix(in srgb,#1d1f20 16%,transparent);--hairline:color-mix(in srgb,#1d1f20 9%,transparent);'
Add-Line '--n300:#d4d4d7;--n400:#b7b7ba;--n500:#98989b;--n600:#7a7a7d;--n700:#5d5d60;--n800:#424244;'
Add-Line '--accent:#5980a6;--accent-700:#416180;--accent-800:#2c455d;--accent-900:#1d2d3d;'
Add-Line '--s-red:#b0453d;--s-green:#3f7d5e;--s-blue:#416180;--s-gold:#c4943a;--s-purple:#8a5a86;--s-plum:#5f3a5c;'
Add-Line '--r-sm:2px;--r-md:4px;--r-lg:7px;--sp1:3.4px;--sp2:6.8px;--sp3:10.2px;--sp4:13.6px;--sp6:20.4px;--sp8:27.2px;'
Add-Line '--shadow-sm:0 1px 2px color-mix(in srgb,#2b2b2d 14%,transparent);'
Add-Line '--font-heading:"Barlow Condensed","Oswald","Archivo Narrow","Roboto Condensed","Noto Sans TC",system-ui,sans-serif;'
Add-Line '--font-body:"Barlow","Inter","Noto Sans TC",system-ui,sans-serif;'
Add-Line '--font-mono:ui-monospace,"DM Mono","Cascadia Mono",Consolas,monospace}'
Add-Line '*{margin:0;padding:0;box-sizing:border-box}html{-webkit-text-size-adjust:100%}'
Add-Line 'body{min-height:100dvh;display:flex;flex-direction:column;background:var(--bg);color:var(--ink);font-family:var(--font-body);font-size:clamp(10.5px,.22vw + 9.9px,12.5px);line-height:1.42;font-variant-numeric:tabular-nums}'
Add-Line '.masthead{background:var(--accent-900);color:var(--bg);padding:var(--sp3) var(--sp6);display:flex;align-items:center;gap:var(--sp6);flex-wrap:wrap}'
Add-Line '.seal{font-family:"Songti TC","SimSun",serif;font-size:34px;line-height:.9;color:var(--s-red);opacity:.62;user-select:none}'
Add-Line '.masthead h1{font-family:var(--font-heading);font-weight:600;font-size:clamp(15px,1.2vw,21px);letter-spacing:.2em;text-transform:uppercase}'
Add-Line '.masthead .sub,.stamp{font-family:var(--font-mono);font-size:10px;color:color-mix(in srgb,#f2f2f3 66%,transparent);letter-spacing:.03em}'
Add-Line '.masthead .spacer{flex:1 1 80px}.stamp{text-align:right}.stamp b{color:var(--bg);font-weight:600}'
Add-Line '.lamp{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:middle}'
# two-pane shell: fixed-width control panel on the left, result canvas on the right
Add-Line '.shell{flex:1 1 auto;display:grid;grid-template-columns:246px minmax(0,1fr);gap:0;align-items:stretch}'
Add-Line '.panel{background:var(--surface);border-right:1px solid var(--divider);padding:var(--sp4);display:flex;flex-direction:column;gap:var(--sp4)}'
Add-Line '.pgroup{display:flex;flex-direction:column;gap:var(--sp2)}'
Add-Line '.plabel{font-family:var(--font-mono);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--n600);border-bottom:1px solid var(--hairline);padding-bottom:var(--sp1)}'
Add-Line '.pfield{display:flex;flex-direction:column;gap:1px}'
Add-Line '.pfield .k{font-family:var(--font-mono);font-size:9.5px;color:var(--n600);letter-spacing:.05em}'
Add-Line '.pfield .v{font-family:var(--font-mono);font-size:11px;color:var(--ink);border-bottom:1px solid var(--n300);padding-bottom:2px;word-break:break-all}'
Add-Line '.canvas{padding:var(--sp4) var(--sp6) var(--sp8);display:flex;flex-direction:column;gap:var(--sp4);min-width:0}'
# CSS-only tab control: radios live in the left panel, panes render on the right
Add-Line '.tabs{display:flex;flex-direction:column;gap:1px}'
Add-Line '.tabs label{font-family:var(--font-mono);font-size:11px;letter-spacing:.04em;padding:var(--sp2) var(--sp3);cursor:pointer;border-left:2px solid transparent;color:var(--n700);display:flex;align-items:center;gap:var(--sp2)}'
Add-Line '.tabs label:hover{background:color-mix(in srgb,#5980a6 8%,transparent)}'
Add-Line '.tabs input{accent-color:var(--s-red);width:10px;height:10px;flex:none}'
Add-Line '.checks{display:flex;flex-direction:column;gap:var(--sp1)}'
Add-Line '.checks label{font-family:var(--font-mono);font-size:10.5px;color:var(--n700);display:flex;align-items:center;gap:var(--sp2);cursor:pointer}'
Add-Line '.checks input{accent-color:var(--accent-700);width:11px;height:11px;flex:none}'
Add-Line '.pane{display:none;flex-direction:column;gap:var(--sp3)}'
Add-Line '.pane-1{display:flex}'
Add-Line '@supports selector(:has(*)){'
Add-Line '.pane-1{display:none}'
Add-Line 'body:has(#t1:checked) .pane-1,body:has(#t2:checked) .pane-2,body:has(#t3:checked) .pane-3,body:has(#t4:checked) .pane-4,'
Add-Line 'body:has(#t5:checked) .pane-5,body:has(#t6:checked) .pane-6,body:has(#t7:checked) .pane-7,body:has(#t8:checked) .pane-8{display:flex}'
Add-Line '.tabs label:has(input:checked){background:var(--paper);border-left-color:var(--s-red);color:var(--ink);font-weight:600}'
Add-Line 'body:not(:has(#fmiss:checked)) tr.st-missing{display:none}'
Add-Line 'body:not(:has(#fdup:checked)) tr.st-dup{display:none}'
Add-Line 'body:has(#fzoom:checked) .canvas{font-size:1.14em}'
Add-Line '}'
Add-Line 'h2{font-family:var(--font-heading);font-weight:600;font-size:clamp(12px,.8vw,15px);letter-spacing:.14em;text-transform:uppercase;color:var(--accent-800);border-bottom:1px solid var(--divider);padding-bottom:var(--sp2);display:flex;gap:var(--sp3);align-items:baseline;flex-wrap:wrap}'
Add-Line 'h2 .note{font-family:var(--font-mono);font-size:.66em;letter-spacing:.02em;text-transform:none;color:var(--n600);font-weight:400}'
# equal-height cards, evenly divided rows, justified across the full width
Add-Line '.grid{display:flex;flex-direction:column;gap:var(--sp3)}'
Add-Line '.grow{display:flex;gap:var(--sp3);align-items:stretch}'
Add-Line '.grow>*{flex:1 1 0;min-width:0;display:flex;flex-direction:column;justify-content:space-between}'
Add-Line '.card{background:var(--paper);border:1px solid var(--hairline);border-left:3px solid var(--c,var(--s-blue));border-radius:var(--r-md);padding:var(--sp3);box-shadow:var(--shadow-sm);gap:var(--sp1)}'
Add-Line '.card .t{font-family:var(--font-mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--n600)}'
Add-Line '.card .m{font-family:var(--font-heading);font-weight:600;font-size:1.5em;letter-spacing:.02em;line-height:1.1}'
Add-Line '.card .d{font-family:var(--font-mono);font-size:10px;color:var(--n700);word-break:break-all}'
Add-Line '.tw{background:var(--paper);border:1px solid var(--hairline);border-radius:var(--r-md);overflow:hidden;box-shadow:var(--shadow-sm)}'
Add-Line 'table{width:100%;border-collapse:collapse;table-layout:fixed}'
Add-Line 'th,td{border-bottom:1px solid var(--hairline);padding:var(--sp1) var(--sp3);text-align:left;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}'
Add-Line 'thead th{background:var(--surface);color:var(--n800);font-family:var(--font-mono);font-size:9.5px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;border-bottom:1px solid var(--divider);position:sticky;top:0;z-index:2}'
Add-Line 'tbody tr:last-child td{border-bottom:none}tbody tr:nth-child(even){background:color-mix(in srgb,#e9e9ea 42%,transparent)}'
Add-Line '.mono{font-family:var(--font-mono);font-size:10.5px}.num{text-align:right;font-family:var(--font-mono);font-size:10.5px}.mute{color:var(--n600)}'
Add-Line '.id{font-family:var(--font-mono);font-size:10.5px;color:var(--accent-800);font-weight:600;letter-spacing:.02em}'
Add-Line '.chip{display:inline-block;font-family:var(--font-mono);font-size:9.5px;letter-spacing:.05em;padding:0 5px;border-radius:var(--r-sm);white-space:nowrap;border:1px solid color-mix(in srgb,var(--c,var(--s-blue)) 42%,transparent);color:var(--c,var(--s-blue));background:color-mix(in srgb,var(--c,var(--s-blue)) 8%,transparent)}'
Add-Line '.c-pass{--c:var(--s-green)}.c-warn{--c:var(--s-gold)}.c-fail{--c:var(--s-red)}.c-mod{--c:var(--s-blue)}.c-eng{--c:var(--s-purple)}.c-lib{--c:var(--s-plum)}.c-oth{--c:var(--n600)}'
Add-Line 'td.pick{white-space:nowrap}td.pick label{display:inline-flex;align-items:center;gap:3px;margin-right:var(--sp3);font-family:var(--font-mono);font-size:9.5px;color:var(--n700);cursor:pointer}'
Add-Line 'td.pick input{accent-color:var(--s-red);width:11px;height:11px}'
Add-Line '.tokenbox{display:flex;flex-direction:column;gap:var(--sp2)}'
Add-Line '.tokenbox textarea{width:100%;min-height:132px;font-family:var(--font-mono);font-size:10px;line-height:1.5;padding:var(--sp3);border:1px solid var(--n300);border-radius:var(--r-md);background:var(--paper);color:var(--ink);resize:vertical}'
Add-Line '.tokenbox .row{display:flex;gap:var(--sp3);align-items:center;flex-wrap:wrap}'
Add-Line 'button{font-family:var(--font-mono);font-size:10.5px;letter-spacing:.04em;padding:var(--sp2) var(--sp4);border:1px solid var(--accent-700);background:var(--paper);color:var(--accent-800);border-radius:var(--r-sm);cursor:pointer}'
Add-Line 'button:hover{background:var(--accent-700);color:var(--bg)}'
Add-Line 'pre.log{background:var(--paper);border:1px solid var(--hairline);border-radius:var(--r-md);padding:var(--sp3);font-family:var(--font-mono);font-size:10px;line-height:1.5;white-space:pre-wrap;word-break:break-word;color:var(--n800)}'
Add-Line 'footer{border-top:1px solid var(--divider);padding:var(--sp3) var(--sp6);font-family:var(--font-mono);font-size:9.5px;color:var(--n600);display:flex;gap:var(--sp6);flex-wrap:wrap;justify-content:space-between}'
Add-Line '@media (max-width:900px){.shell{grid-template-columns:1fr}.panel{border-right:none;border-bottom:1px solid var(--divider)}.grow{flex-wrap:wrap}.grow>*{flex:1 1 168px}}'
Add-Line '</style></head><body>'

Add-Line '<div class="masthead"><div class="seal">理</div><div>'
Add-Line '<h1>Central Governance Console</h1>'
Add-Line ('<div class="sub">Veritas Intelligence Analytics &middot; Auto Registration, Overlap Analysis And Intake &middot; v0504</div></div>')
Add-Line '<div class="spacer"></div>'
Add-Line ('<div class="stamp"><span class="lamp" style="background:' + $ryg[$overall] + '"></span>Overall <b>' + $overall + '</b> &nbsp; ' + $failCount + ' Fail / ' + $warnCount + ' Warn<br>Run <b>' + $Script:Stamp + '</b> &middot; ' + $elapsed + 's &middot; ' + $modeText + '</div>')
Add-Line '</div>'

Add-Line '<div class="shell">'

# ---------------- left panel: inputs and controls ----------------
Add-Line '<aside class="panel">'
Add-Line '<div class="pgroup"><div class="plabel">Scan Parameters</div>'
Add-Line ('<div class="pfield"><span class="k">Registered Paths</span><span class="v">' + $Register.Count + '</span></div>')
Add-Line ('<div class="pfield"><span class="k">Packages Resolved</span><span class="v">' + $packages.Count + '</span></div>')
Add-Line ('<div class="pfield"><span class="k">Files Analysed</span><span class="v">' + $files.Count + ' / cap ' + $MaxFiles + '</span></div>')
Add-Line ('<div class="pfield"><span class="k">Extensions</span><span class="v">' + (ConvertTo-HtmlText (($IncludeExtensions | Select-Object -First 8) -join ' ')) + '</span></div>')
Add-Line '</div>'
Add-Line '<div class="pgroup"><div class="plabel">Sync Status</div>'
Add-Line ('<div class="pfield"><span class="k">Active Registry</span><span class="v">via_console_registry.json</span></div>')
Add-Line ('<div class="pfield"><span class="k">Identifiers Active</span><span class="v">' + $activeCount + ' exactly</span></div>')
Add-Line ('<div class="pfield"><span class="k">Issued This Run</span><span class="v">' + $issuedNow + ' new / ' + $relocated + ' relocated</span></div>')
Add-Line ('<div class="pfield"><span class="k">Write Mode</span><span class="v">' + $modeText + '</span></div>')
Add-Line '</div>'
Add-Line '<div class="pgroup"><div class="plabel">Result View</div><div class="tabs">'
$tabNames = @('Intake Decisions', 'Overlap Matrix', 'Registry Ledger', 'Package Matrix', 'Symbol Index', 'Regex Library', 'Gate Matrix', 'Run Log')
for ($i = 0; $i -lt $tabNames.Count; $i++) {
    $checked = ''
    if ($i -eq 0) { $checked = ' checked' }
    Add-Line ('<label><input type="radio" name="tab" id="t' + ($i + 1) + '"' + $checked + '><span>' + $tabNames[$i] + '</span></label>')
}
Add-Line '</div></div>'
Add-Line '<div class="pgroup"><div class="plabel">Display Options</div><div class="checks">'
Add-Line '<label><input type="checkbox" id="fmiss"><span>Show Missing Entries</span></label>'
Add-Line '<label><input type="checkbox" id="fdup" checked><span>Show Duplicate Content</span></label>'
Add-Line '<label><input type="checkbox" id="fzoom"><span>Larger Type</span></label>'
Add-Line '</div></div>'
Add-Line ('<div class="pgroup"><div class="plabel">Policy</div><div class="pfield"><span class="v mute">Append only. An identifier, once issued, is never reissued or renumbered. Missing entries are retained.</span></div></div>')
Add-Line '</aside>'

# ---------------- right canvas ----------------
Add-Line '<div class="canvas">'

# Pane 1 - intake decisions
Add-Line '<div class="pane pane-1">'
Add-Line ('<h2>Intake Decisions <span class="note">' + $candidates.Count + ' artifacts &middot; ' + $vIntegrate + ' integrate &middot; ' + $vReview + ' review &middot; ' + $vArchive + ' archive</span></h2>')
$cells = New-Object System.Collections.Generic.List[string]
$cells.Add('<div class="card" style="--c:var(--s-green)"><div><div class="t">Recommend Integrate</div><div class="m">' + $vIntegrate + '</div></div><div class="d">Unique contribution, no material overlap</div></div>')
$cells.Add('<div class="card" style="--c:var(--s-gold)"><div><div class="t">Recommend Review</div><div class="m">' + $vReview + '</div></div><div class="d">Overlaps an existing artifact by 60 percent or more</div></div>')
$cells.Add('<div class="card" style="--c:var(--s-plum)"><div><div class="t">Recommend Archive</div><div class="m">' + $vArchive + '</div></div><div class="d">Duplicate bytes or superseded within its family</div></div>')
$cells.Add('<div class="card" style="--c:var(--s-blue)"><div><div class="t">Overlapping Pairs</div><div class="m">' + $pairs.Count + '</div></div><div class="d">Scored above 25 percent on symbols, structure or patterns</div></div>')
Add-GridRows -Cells $cells.ToArray() -Max 4
Add-Line '<div class="tw"><table><colgroup><col style="width:11%"><col style="width:21%"><col style="width:13%"><col style="width:9%"><col style="width:26%"><col style="width:20%"></colgroup>'
Add-Line '<tr><th>Identifier</th><th>Artifact</th><th>Package</th><th>Advice</th><th>Reason</th><th>Your Decision</th></tr>'
$rowIndex = 0
foreach ($candidate in ($candidates | Sort-Object -Property @{ Expression = { @{ 'REVIEW' = 0; 'INTEGRATE' = 1; 'ARCHIVE' = 2 }[$_.verdict] } }, name)) {
    $rowIndex = $rowIndex + 1
    $chip = '<span class="chip c-pass">Integrate</span>'
    if ($candidate.verdict -eq 'REVIEW') { $chip = '<span class="chip c-warn">Review</span>' }
    if ($candidate.verdict -eq 'ARCHIVE') { $chip = '<span class="chip c-lib">Archive</span>' }
    $rid = $candidate.id
    if ([string]::IsNullOrEmpty($rid)) { $rid = 'unregistered' }
    $group = 'd' + $rowIndex
    $picks = ''
    foreach ($choice in @('INTEGRATE', 'ARCHIVE', 'SKIP')) {
        $checkedAttr = ''
        if ($choice -eq $candidate.verdict -or ($candidate.verdict -eq 'REVIEW' -and $choice -eq 'SKIP')) { $checkedAttr = ' checked data-advice="1"' }
        $label = $choice.Substring(0, 1) + $choice.Substring(1).ToLowerInvariant()
        $picks = $picks + '<label><input type="radio" name="' + $group + '" value="' + $choice + '" data-id="' + $rid + '" data-name="' + (ConvertTo-HtmlText $candidate.name) + '"' + $checkedAttr + '>' + $label + '</label>'
    }
    Add-Line ('<tr><td class="id">' + $rid + '</td><td class="mono">' + (ConvertTo-HtmlText $candidate.name) + '</td><td class="mono mute">' + (ConvertTo-HtmlText $candidate.package) + '</td><td>' + $chip + '</td><td class="mono mute">' + (ConvertTo-HtmlText $candidate.reason) + '</td><td class="pick">' + $picks + '</td></tr>')
}
Add-Line '</table></div>'
Add-Line '<h2>Decision Token <span class="note">Tick above, copy this block, save it as a text file, then re-run with -Decisions</span></h2>'
Add-Line '<div class="tokenbox"><div class="row"><button type="button" id="btn-all-int">Select All Integrate</button><button type="button" id="btn-advice">Reset To Advice</button><button type="button" id="btn-copy">Copy Token</button><span class="mute mono" id="tok-count"></span></div>'
Add-Line '<textarea id="tokbox" readonly spellcheck="false"></textarea></div>'
Add-Line '</div>'

# Pane 2 - overlap matrix
Add-Line '<div class="pane pane-2">'
$overlapNote = $pairs.Count.ToString() + ' pairs above 25 percent'
if ($pairSkipped) { $overlapNote = 'Skipped: too many comparable artifacts' }
Add-Line ('<h2>Overlap Matrix <span class="note">' + $overlapNote + ' &middot; Jaccard on symbols, structure and patterns</span></h2>')
Add-Line '<div class="tw"><table><colgroup><col style="width:24%"><col style="width:24%"><col style="width:10%"><col style="width:11%"><col style="width:10%"><col style="width:10%"><col style="width:11%"></colgroup>'
Add-Line '<tr><th>Artifact A</th><th>Artifact B</th><th>Overlap</th><th>Strongest On</th><th>Symbols</th><th>Structure</th><th>Patterns</th></tr>'
if ($pairs.Count -eq 0) { Add-Line '<tr><td colspan="7" class="mute">No artifact pair overlaps by more than 25 percent.</td></tr>' }
foreach ($pair in ($pairs | Select-Object -First 80)) {
    $scoreClass = 'chip c-pass'
    if ($pair.score -ge 60) { $scoreClass = 'chip c-fail' }
    elseif ($pair.score -ge 40) { $scoreClass = 'chip c-warn' }
    Add-Line ('<tr><td class="mono">' + (ConvertTo-HtmlText $pair.left) + '</td><td class="mono">' + (ConvertTo-HtmlText $pair.right) + '</td><td><span class="' + $scoreClass + '">' + $pair.score + '%</span></td><td class="mono mute">' + $pair.basis + '</td><td class="num">' + $pair.symbols + '</td><td class="num">' + $pair.structure + '</td><td class="num">' + $pair.patterns + '</td></tr>')
}
Add-Line '</table></div>'
Add-Line ('<h2>Version Families <span class="note">' + $familyRows.Count + ' families with more than one member &middot; newest is the head</span></h2>')
Add-Line '<div class="tw"><table><colgroup><col style="width:24%"><col style="width:8%"><col style="width:30%"><col style="width:38%"></colgroup>'
Add-Line '<tr><th>Family</th><th>Members</th><th>Head</th><th>Older Members</th></tr>'
if ($familyRows.Count -eq 0) { Add-Line '<tr><td colspan="4" class="mute">No multi-version families detected.</td></tr>' }
foreach ($row in $familyRows) {
    Add-Line ('<tr><td class="mono">' + (ConvertTo-HtmlText $row.family) + '</td><td class="num">' + $row.count + '</td><td class="mono">' + (ConvertTo-HtmlText $row.head) + '</td><td class="mono mute">' + (ConvertTo-HtmlText $row.older) + '</td></tr>')
}
Add-Line '</table></div></div>'

# Pane 3 - registry ledger

Add-Line '<div class="pane pane-3">'
Add-Line ('<h2>Registry Ledger <span class="note">' + $entries.Count + ' identifiers &middot; ' + $issuedNow + ' issued this run &middot; append only</span></h2>')
$summaryCards = New-Object System.Collections.Generic.List[object]
foreach ($prefix in @('MOD', 'ENG', 'LIB', 'OTH')) {
    $label = @{ 'MOD' = 'Modules'; 'ENG' = 'Engines'; 'LIB' = 'Function Libraries'; 'OTH' = 'Other Artifacts' }[$prefix]
    $cls = @{ 'MOD' = 'c-mod'; 'ENG' = 'c-eng'; 'LIB' = 'c-lib'; 'OTH' = 'c-oth' }[$prefix]
    $count = @($entries | Where-Object { $_.id -like ('VIA-' + $prefix + '-*') }).Count
    $summaryCards.Add([pscustomobject]@{ label = $label; count = $count; next = ('VIA-' + $prefix + '-' + ($counters[$prefix] + 1).ToString('0000')); cls = $cls })
}
$cells = New-Object System.Collections.Generic.List[string]
foreach ($card in $summaryCards) {
    $colorVar = @{ 'c-mod' = 'var(--s-blue)'; 'c-eng' = 'var(--s-purple)'; 'c-lib' = 'var(--s-plum)'; 'c-oth' = 'var(--n600)' }[$card.cls]
    $cells.Add('<div class="card" style="--c:' + $colorVar + '"><div><div class="t">' + $card.label + '</div><div class="m">' + $card.count + '</div></div><div class="d">Next ' + $card.next + '</div></div>')
}
Add-GridRows -Cells $cells.ToArray() -Max 4
Add-Line '<div class="tw"><table><colgroup><col style="width:13%"><col style="width:24%"><col style="width:17%"><col style="width:9%"><col style="width:7%"><col style="width:7%"><col style="width:11%"><col style="width:12%"></colgroup>'
Add-Line '<tr><th>Identifier</th><th>Artifact</th><th>Package</th><th>Section</th><th>Lines</th><th>Symbols</th><th>First Seen</th><th>Status</th></tr>'
$dupNames = @{}
foreach ($set in $dupSets) { foreach ($member in $set.Value) { $dupNames[$member] = $true } }
foreach ($record in ($entries | Sort-Object -Property id)) {
    $rowClass = ''
    if ($record.status -eq 'MISSING') { $rowClass = ' class="st-missing"' }
    elseif ($dupNames.ContainsKey($record.package + '/' + $record.name)) { $rowClass = ' class="st-dup"' }
    $statusChip = '<span class="chip c-pass">Active</span>'
    if ($record.status -eq 'MISSING') { $statusChip = '<span class="chip c-warn">Missing</span>' }
    $sectionChip = @{ 'MODULE' = '<span class="chip c-mod">Module</span>'; 'ENGINE' = '<span class="chip c-eng">Engine</span>'; 'FUNCTION-LIB' = '<span class="chip c-lib">Library</span>'; 'OTHERS' = '<span class="chip c-oth">Other</span>' }[$record.section]
    Add-Line ('<tr' + $rowClass + '><td class="id">' + $record.id + '</td><td class="mono">' + (ConvertTo-HtmlText $record.name) + '</td><td class="mono mute">' + (ConvertTo-HtmlText $record.package) + '</td><td>' + $sectionChip + '</td><td class="num">' + $record.loc + '</td><td class="num">' + $record.symbols + '</td><td class="mono mute">' + $record.first_seen + '</td><td>' + $statusChip + '</td></tr>')
}
Add-Line '</table></div></div>'

# Pane 2 - package matrix
Add-Line '<div class="pane pane-4">'
Add-Line ('<h2>Package Matrix <span class="note">' + $packageRows.Count + ' packages &middot; equal height, evenly divided rows</span></h2>')
$cells = New-Object System.Collections.Generic.List[string]
foreach ($row in $packageRows) {
    $colorVar = 'var(--s-blue)'
    if (-not $row.present) { $colorVar = 'var(--s-red)' }
    elseif ($row.parse_fail -gt 0) { $colorVar = 'var(--s-gold)' }
    $tail = ''
    if ($row.parse_fail -gt 0) { $tail = ' &middot; ' + $row.parse_fail + ' parse fail' }
    $cells.Add('<div class="card" style="--c:' + $colorVar + '"><div><div class="t">' + (ConvertTo-HtmlText $row.package) + '</div>' +
              '<div class="m">' + $row.files + '</div></div>' +
              '<div class="d">' + $row.ids + ' ids &middot; ' + $row.loc + ' lines &middot; ' + $row.functions + ' fn &middot; ' + $row.regex + ' regex' + $tail + '</div></div>')
}
Add-GridRows -Cells $cells.ToArray() -Max 5
Add-Line '<div class="tw"><table><colgroup><col style="width:22%"><col style="width:44%"><col style="width:9%"><col style="width:8%"><col style="width:8%"><col style="width:9%"></colgroup>'
Add-Line '<tr><th>Package</th><th>Path</th><th>Kind</th><th>Files</th><th>Ids</th><th>Parse Fail</th></tr>'
foreach ($row in $packageRows) {
    Add-Line ('<tr><td class="mono">' + (ConvertTo-HtmlText $row.package) + '</td><td class="mono mute">' + (ConvertTo-HtmlText $row.path) + '</td><td class="mono mute">' + $row.kind + '</td><td class="num">' + $row.files + '</td><td class="num">' + $row.ids + '</td><td class="num">' + $row.parse_fail + '</td></tr>')
}
Add-Line '</table></div></div>'

# Pane 3 - symbol index
Add-Line '<div class="pane pane-5">'
Add-Line ('<h2>Symbol Index <span class="note">' + $collisions.Count + ' cross-file collisions &middot; duplicates de-duplicated by content hash first</span></h2>')
Add-Line '<div class="tw"><table><colgroup><col style="width:24%"><col style="width:8%"><col style="width:68%"></colgroup>'
Add-Line '<tr><th>Symbol</th><th>Files</th><th>Defined In</th></tr>'
if ($collisions.Count -eq 0) { Add-Line '<tr><td colspan="3" class="mute">No cross-file symbol collisions detected.</td></tr>' }
foreach ($entry in ($collisions | Select-Object -First 60)) {
    Add-Line ('<tr><td class="mono" style="color:var(--s-red);font-weight:600">' + (ConvertTo-HtmlText $entry.Key) + '</td><td class="num">' + $entry.Value.Count + '</td><td class="mono mute">' + (ConvertTo-HtmlText ((@($entry.Value) | Select-Object -First 8) -join ' | ')) + '</td></tr>')
}
Add-Line '</table></div>'
Add-Line ('<h2>Duplicate Content <span class="note">' + $dupSets.Count + ' groups &middot; identical bytes</span></h2>')
Add-Line '<div class="tw"><table><colgroup><col style="width:18%"><col style="width:82%"></colgroup>'
Add-Line '<tr><th>Hash</th><th>Members</th></tr>'
if ($dupSets.Count -eq 0) { Add-Line '<tr><td colspan="2" class="mute">No identical files across registered packages.</td></tr>' }
foreach ($set in ($dupSets | Select-Object -First 40)) {
    Add-Line ('<tr class="st-dup"><td class="mono mute">' + $set.Key.Substring(0, [Math]::Min(12, $set.Key.Length)) + '</td><td class="mono">' + (ConvertTo-HtmlText (@($set.Value) -join ' | ')) + '</td></tr>')
}
Add-Line '</table></div></div>'

# Pane 4 - regex library
Add-Line '<div class="pane pane-6">'
Add-Line ('<h2>Regex Library <span class="note">' + $regexRows.Count + ' patterns &middot; ' + $badRegex.Count + ' fail to compile</span></h2>')
Add-Line '<div class="tw"><table><colgroup><col style="width:22%"><col style="width:16%"><col style="width:48%"><col style="width:14%"></colgroup>'
Add-Line '<tr><th>Artifact</th><th>Symbol</th><th>Pattern</th><th>Compiles</th></tr>'
if ($regexRows.Count -eq 0) { Add-Line '<tr><td colspan="4" class="mute">No regex literals detected in the registered artifacts.</td></tr>' }
foreach ($row in ($regexRows | Select-Object -First 120)) {
    $chip = '<span class="chip c-pass">Yes</span>'
    if (-not $row.ok) { $chip = '<span class="chip c-fail">No</span>' }
    Add-Line ('<tr><td class="mono">' + (ConvertTo-HtmlText $row.name) + '</td><td class="mono">' + (ConvertTo-HtmlText $row.symbol) + '</td><td class="mono">' + (ConvertTo-HtmlText $row.pattern) + '</td><td>' + $chip + '</td></tr>')
}
Add-Line '</table></div></div>'

# Pane 5 - gate matrix
Add-Line '<div class="pane pane-7">'
Add-Line ('<h2>Gate Matrix <span class="note">' + $gates.Count + ' gates &middot; only Block class interrupts</span></h2>')
$cells = New-Object System.Collections.Generic.List[string]
foreach ($gate in $gates) {
    $colorVar = 'var(--s-green)'
    if ($gate.status -eq 'WARN') { $colorVar = 'var(--s-gold)' }
    if ($gate.status -eq 'FAIL') { $colorVar = 'var(--s-red)' }
    $cells.Add('<div class="card" style="--c:' + $colorVar + '"><div><div class="t">' + $gate.code + '</div><div class="m" style="font-size:1.1em">' + $gate.status + '</div></div><div class="d">' + (ConvertTo-HtmlText $gate.detail) + '</div></div>')
}
Add-GridRows -Cells $cells.ToArray() -Max 5
Add-Line ('<h2>Convention Lint <span class="note">' + $llFindings.Count + ' findings</span></h2>')
Add-Line '<div class="tw"><table><colgroup><col style="width:30%"><col style="width:22%"><col style="width:20%"><col style="width:12%"><col style="width:16%"></colgroup>'
Add-Line '<tr><th>Artifact</th><th>Rule</th><th>Token</th><th>Line</th><th>Package</th></tr>'
if ($llFindings.Count -eq 0) { Add-Line '<tr><td colspan="5" class="mute">No convention violations found.</td></tr>' }
foreach ($row in ($llFindings | Select-Object -First 80)) {
    $chipClass = 'c-warn'
    if ($row.rule -eq 'LL_NO_READHOST') { $chipClass = 'c-fail' }
    Add-Line ('<tr><td class="mono">' + (ConvertTo-HtmlText $row.name) + '</td><td><span class="chip ' + $chipClass + '">' + $row.rule + '</span></td><td class="mono">' + (ConvertTo-HtmlText $row.token) + '</td><td class="num">' + $row.line + '</td><td class="mono mute">' + (ConvertTo-HtmlText $row.package) + '</td></tr>')
}
Add-Line '</table></div></div>'

# Pane 6 - run log
Add-Line '<div class="pane pane-8">'
Add-Line '<h2>Run Log <span class="note">This execution only</span></h2>'
Add-Line ('<pre class="log">' + (ConvertTo-HtmlText ($Script:LogLines -join "`n")) + '</pre></div>')

Add-Line '</div></div>'
Add-Line ('<footer><span>Read only on every scanned path &middot; nothing moved or deleted</span><span>Registry: ' + (ConvertTo-HtmlText $RegistryPath) + '</span><span>Single file &middot; offline &middot; script only builds the decision token</span></footer>')
Add-Line '<script>'
Add-Line '(function(){'
Add-Line 'var box=document.getElementById("tokbox"),cnt=document.getElementById("tok-count");'
Add-Line 'if(!box){return;}'
Add-Line 'var picks=function(){return Array.prototype.slice.call(document.querySelectorAll("td.pick input:checked"));};'
Add-Line 'var render=function(){var lines=["==VIA-INTAKE=="],n=0;'
Add-Line 'picks().forEach(function(p){lines.push(p.value+" "+p.getAttribute("data-id")+" "+p.getAttribute("data-name"));if(p.value!=="SKIP"){n++;}});'
Add-Line 'box.value=lines.join("\n");cnt.textContent=n+" of "+picks().length+" actionable";};'
Add-Line 'document.addEventListener("change",function(e){if(e.target&&e.target.matches("td.pick input")){render();}});'
Add-Line 'var b1=document.getElementById("btn-all-int");if(b1){b1.addEventListener("click",function(){'
Add-Line 'document.querySelectorAll("td.pick input[value=INTEGRATE]").forEach(function(i){i.checked=true;});render();});}'
Add-Line 'var b2=document.getElementById("btn-advice");if(b2){b2.addEventListener("click",function(){'
Add-Line 'document.querySelectorAll("td.pick input[data-advice=1]").forEach(function(i){i.checked=true;});render();});}'
Add-Line 'var b3=document.getElementById("btn-copy");if(b3){b3.addEventListener("click",function(){'
Add-Line 'box.select();try{document.execCommand("copy");b3.textContent="Copied";setTimeout(function(){b3.textContent="Copy Token";},1400);}catch(err){b3.textContent="Select And Copy";}});}'
Add-Line 'render();'
Add-Line '})();'
Add-Line '</script>'
Add-Line '</body></html>'

Write-Utf8NoBom -Path $HtmlPath -Text $sb.ToString()
Write-Utf8NoBom -Path $LogPath -Text ($Script:LogLines -join "`n")

Write-Stage -Message ('Console rendered. Overall ' + $overall) -Percent 100 -Level 'OK'
Write-Progress -Activity 'VIA Central Governance Console' -Completed

Write-Host ''
Write-Host ('  console   : ' + $HtmlPath) -ForegroundColor DarkCyan
Write-Host ('  registry  : ' + $RegistryPath) -ForegroundColor DarkCyan
Write-Host ('  snapshot  : ' + $SnapshotPath) -ForegroundColor DarkCyan
Write-Host ('  log       : ' + $LogPath) -ForegroundColor DarkCyan

if (-not $NoBrowser) { Start-Process -FilePath $HtmlPath | Out-Null }
