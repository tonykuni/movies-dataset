#requires -Version 7.0
param(
    [string]$MotherRoot   = 'C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics',
    [string[]]$Layers     = @('VAP', 'VDF', 'VRN'),
    [string]$SupportiveDir = '',
    [string]$WorkRoot     = 'C:\VeritasIntelligenceAnalytics\CGE\Console',
    [string]$PythonExe    = '',
    [switch]$DryRun,
    [switch]$InstallLibs,
    [switch]$NoBrowser
)

# ============================================================
# VIA Polyglot Repair + Import Injector v0100
# 針對 VAP / VDF / VRN 三個資料夾的 .py 做三輪全景處理：
#   Round 1  掃描 + 安全語法修復（BOM / NUL / Tab 縮排 / 換行）
#   Round 2  依規則注入必要 import（AST 定位插入點，非字串硬塞）
#   Round 3  複驗 + 彙整 import + 產出缺少的 libs 安裝清單
# 注入規則：
#   - 除 VeritasCeleritas.py 本身外，所有 .py 一律注入 VeritasCeleritas
#   - VDF 模組另外注入 Invoke-VeritasCodexNexus.ps1 的呼叫橋 via_codex_nexus()
#   - 任何會對外擷取資料的檔案，再注入 VIA_NetSupport
# 治理：只增不減。改寫前一律先備份到 _backup\<stamp>\，並產出 rollback 腳本。
#   預設實際套用（-DryRun 可只看不改）。注入區塊有標記，重跑冪等不會疊加。
# 執行：pwsh -NoProfile -ExecutionPolicy Bypass -File "<this file>"
# ============================================================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Script:Stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$Script:Log   = [System.Collections.Generic.List[string]]::new()

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Write-Stage {
    param([string]$Message, [int]$Percent = 0, [string]$Level = 'INFO')
    $line = '[' + (Get-Date).ToString('HH:mm:ss') + '][' + $Level + '] ' + $Message
    $Script:Log.Add($line)
    $color = 'Gray'
    if ($Level -eq 'OK')   { $color = 'Green' }
    if ($Level -eq 'WARN') { $color = 'Yellow' }
    if ($Level -eq 'FAIL') { $color = 'Red' }
    Write-Host $line -ForegroundColor $color
    Write-Progress -Activity 'VIA Polyglot Repair + Import Injector v0100' -Status $Message -PercentComplete ([math]::Min(100, [math]::Max(0, $Percent)))
}

function ConvertTo-HtmlText {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return $Text.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;').Replace('"', '&quot;')
}

function Resolve-PythonExe {
    param([string]$Preferred)
    if ($Preferred) { return $Preferred }
    foreach ($candidate in @('python', 'python3', 'py')) {
        $found = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $found) { return $found.Source }
    }
    return ''
}

Write-Stage -Message 'VIA Polyglot Repair + Import Injector v0100 starting' -Percent 1 -Level 'OK'

if (-not $SupportiveDir) { $SupportiveDir = Join-Path $MotherRoot 'supportive modules' }
$CodexPs1 = Join-Path $SupportiveDir 'Invoke-VeritasCodexNexus.ps1'

if (-not (Test-Path -LiteralPath $MotherRoot)) {
    Write-Stage -Message ('母系統根目錄不存在: ' + $MotherRoot) -Percent 100 -Level 'FAIL'
    return
}

# --- resolve the VAP / VDF / VRN folders (they may sit one level down) ---
$roots = [ordered]@{}
foreach ($layer in $Layers) {
    $direct = Join-Path $MotherRoot $layer
    if (Test-Path -LiteralPath $direct) { $roots[$layer] = $direct; continue }
    $found = @(Get-ChildItem -LiteralPath $MotherRoot -Directory -Recurse -Depth 2 -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ieq $layer } | Select-Object -First 1)
    if ($found.Count -gt 0) { $roots[$layer] = $found[0].FullName }
    else { Write-Stage -Message ('找不到 ' + $layer + ' 資料夾，略過') -Percent 4 -Level 'WARN' }
}
if ($roots.Keys.Count -eq 0) {
    Write-Stage -Message '三個資料夾都找不到，結束' -Percent 100 -Level 'FAIL'
    return
}
foreach ($key in $roots.Keys) { Write-Stage -Message ('  ' + $key + ' -> ' + $roots[$key]) -Percent 6 -Level 'OK' }

if (-not (Test-Path -LiteralPath $SupportiveDir)) {
    Write-Stage -Message ('Supportive Modules 資料夾不存在，注入仍會寫入但執行期會 fallback 成 None: ' + $SupportiveDir) -Percent 7 -Level 'WARN'
}
if (-not (Test-Path -LiteralPath $CodexPs1)) {
    Write-Stage -Message ('找不到 Invoke-VeritasCodexNexus.ps1，VDF 橋接函式會回傳 None: ' + $CodexPs1) -Percent 8 -Level 'WARN'
}

foreach ($sub in @('engine', 'inventory', 'out', 'plans', '_backup')) {
    $target = Join-Path $WorkRoot $sub
    if (-not (Test-Path -LiteralPath $target)) { New-Item -Path $target -ItemType Directory -Force | Out-Null }
}

$EnginePath = Join-Path $WorkRoot 'engine\via_polyglot_repair.py'
$ConfigPath = Join-Path $WorkRoot ('engine\repair_config_' + $Script:Stamp + '.json')
$ReportJson = Join-Path $WorkRoot ('inventory\polyglot_repair_' + $Script:Stamp + '.json')
$BackupDir  = Join-Path $WorkRoot ('_backup\' + $Script:Stamp)
$HtmlPath   = Join-Path $WorkRoot ('out\VIA_Polyglot_Repair_' + $Script:Stamp + '.html')
$RollbackPs = Join-Path $WorkRoot ('plans\rollback_polyglot_' + $Script:Stamp + '.ps1')

$pyExe = Resolve-PythonExe -Preferred $PythonExe
if (-not $pyExe) {
    Write-Stage -Message 'PATH 上找不到 python，無法進行 AST 修復' -Percent 100 -Level 'FAIL'
    return
}
Write-Stage -Message ('Python: ' + $pyExe) -Percent 10 -Level 'OK'

$PyEngine = @'
"""VIA Polyglot Repair + Import Injector engine - stdlib only, no network.

Round 1  scan + safe syntax repair (BOM / NUL / tab-indent)
Round 2  inject the mandated imports through AST-located insertion points
Round 3  verify, collect imports, resolve the missing-library install list

Nothing is deleted. Every file that is written is copied to backup_dir first.
"""
import ast
import io
import json
import os
import shutil
import sys
import importlib.util

MARK_BEGIN = "# ==VIA-INJECT-BEGIN v0100== managed block, do not edit by hand"
MARK_END = "# ==VIA-INJECT-END=="

FETCH_SIGNALS = (
    "requests", "urllib", "http.client", "httpx", "aiohttp", "socket",
    "ftplib", "yfinance", "selenium", "openapi", "twse", "tpex", "taifex",
    "urlopen", "web_fetch", "download", "api_key", "endpoint",
)

SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "env", "node_modules",
             "_legacy", "_to_delete", "_backup", "site-packages", ".idea", ".vs"}

STDLIB = set(getattr(sys, "stdlib_module_names", ()))
if not STDLIB:
    STDLIB = {"os", "sys", "json", "re", "ast", "io", "math", "time", "datetime",
              "subprocess", "shutil", "hashlib", "sqlite3", "csv", "typing",
              "pathlib", "collections", "itertools", "functools", "logging",
              "urllib", "http", "socket", "ftplib", "importlib", "argparse"}


def progress(pct, msg):
    sys.stdout.write("PROGRESS|%s|%s\n" % (pct, msg))
    sys.stdout.flush()


def decode(raw):
    for enc in ("utf-8-sig", "utf-8", "cp950", "latin-1"):
        try:
            return raw.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace"), "utf-8-replace"


def parse_error(text):
    try:
        ast.parse(text)
        return None
    except SyntaxError as exc:
        return "line %s: %s" % (exc.lineno, exc.msg)
    except ValueError as exc:
        return "value: %s" % exc


def collect_py(root):
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
        for name in files:
            if name.lower().endswith((".py", ".pyw")):
                out.append(os.path.join(base, name))
    return sorted(out)


def insertion_line(text):
    """1-based line number where the managed block may be inserted."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    line = 1
    lines = text.splitlines()
    # shebang / coding cookie must stay on top
    for idx in range(min(2, len(lines))):
        stripped = lines[idx].strip()
        if stripped.startswith("#!") or "coding" in stripped and stripped.startswith("#"):
            line = idx + 2
    for node in tree.body:
        is_doc = (isinstance(node, ast.Expr)
                  and isinstance(getattr(node, "value", None), ast.Constant)
                  and isinstance(node.value.value, str))
        is_future = isinstance(node, ast.ImportFrom) and node.module == "__future__"
        if is_doc or is_future:
            line = max(line, (getattr(node, "end_lineno", node.lineno) or node.lineno) + 1)
            continue
        break
    return line


def strip_block(text):
    """Remove a previously injected managed block so injection stays idempotent."""
    if MARK_BEGIN not in text:
        return text, False
    out = []
    inside = False
    for line in text.splitlines(True):
        if line.startswith(MARK_BEGIN):
            inside = True
            continue
        if inside:
            if line.startswith(MARK_END):
                inside = False
            continue
        out.append(line)
    return "".join(out), True


def build_block(cfg, needs):
    sup = cfg["supportive"].replace("\\", "\\\\")
    body = [MARK_BEGIN,
            "import os as _via_os, sys as _via_sys",
            '_VIA_SUPPORTIVE = r"%s"' % cfg["supportive"],
            "if _via_os.path.isdir(_VIA_SUPPORTIVE) and _VIA_SUPPORTIVE not in _via_sys.path:",
            "    _via_sys.path.insert(0, _VIA_SUPPORTIVE)"]
    if "celeritas" in needs:
        body += ["try:",
                 "    import VeritasCeleritas as VIA_ACCEL",
                 "except Exception as _via_err:",
                 "    VIA_ACCEL = None"]
    if "netsupport" in needs:
        body += ["try:",
                 "    import VIA_NetSupport as VIA_NET",
                 "except Exception as _via_err:",
                 "    VIA_NET = None"]
    if "codex" in needs:
        body += ['_VIA_CODEX_PS1 = r"%s"' % cfg["codex_ps1"],
                 '_VIA_CODEX_MODES = ("All", "Spec", "Visual", "Layout",',
                 '                    "Interaction", "Governance")',
                 "",
                 "",
                 'def via_codex_nexus(mode="Governance", task="", scan=".", out=None,',
                 "                    registry=None, serve=False, port=8770,",
                 '                    python_exe="python"):',
                 '    """Call the Codex Nexus hub (CORE-04) with its real signature."""',
                 "    import subprocess as _via_sp",
                 "    if mode not in _VIA_CODEX_MODES:",
                 '        raise ValueError("mode must be one of %s" % (_VIA_CODEX_MODES,))',
                 "    if not _via_os.path.isfile(_VIA_CODEX_PS1):",
                 "        return None",
                 '    argv = ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass",',
                 '            "-File", _VIA_CODEX_PS1, "-Mode", mode, "-Scan", scan]',
                 "    if task:",
                 '        argv += ["-Task", task]',
                 "    if out:",
                 '        argv += ["-Out", out]',
                 "    if registry:",
                 '        argv += ["-Registry", registry]',
                 "    if serve:",
                 '        argv += ["-Serve", "-Port", str(port)]',
                 '    argv += ["-Python", python_exe]',
                 "    return _via_sp.run(argv, check=False)"]
    body.append(MARK_END)
    return "\n".join(body) + "\n"


def main():
    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        cfg = json.load(handle)
    dry = bool(cfg.get("dry_run", False))
    backup_dir = cfg["backup_dir"]
    rows = []
    targets = []
    for layer, root in cfg["roots"].items():
        if not os.path.isdir(root):
            continue
        for path in collect_py(root):
            targets.append((layer, root, path))
    total = len(targets) or 1
    progress(2, "found %d python files" % len(targets))

    # ---------------- ROUND 1 : scan + safe repair ----------------
    for idx, (layer, root, path) in enumerate(targets):
        row = {"layer": layer, "path": path,
               "rel": os.path.relpath(path, root).replace("\\", "/"),
               "name": os.path.basename(path), "size": 0,
               "r1": "OK", "repairs": [], "r1_error": "",
               "r2": "SKIPPED", "injected": [], "r2_error": "",
               "r3": "PENDING", "imports": [], "written": False,
               "encoding": "", "fetcher": False}
        try:
            raw = open(path, "rb").read()
        except OSError as exc:
            row["r1"] = "READ_FAIL"
            row["r1_error"] = str(exc)
            rows.append(row)
            continue
        row["size"] = len(raw)
        text, enc = decode(raw)
        row["encoding"] = enc
        original = text

        if raw.startswith(b"\xef\xbb\xbf"):
            row["repairs"].append("strip BOM")
        if "\x00" in text:
            text = text.replace("\x00", "")
            row["repairs"].append("remove NUL bytes")

        err = parse_error(text)
        if err:
            if "\t" in text:
                for width in (8, 4):
                    candidate = text.expandtabs(width)
                    if parse_error(candidate) is None:
                        text = candidate
                        row["repairs"].append("expand tabs to %d spaces" % width)
                        err = None
                        break
            if err:
                candidate = text.replace("\r\n", "\n")
                if parse_error(candidate) is None:
                    text = candidate
                    row["repairs"].append("normalise line endings")
                    err = None
        if err:
            row["r1"] = "SYNTAX_ERROR"
            row["r1_error"] = err
        elif row["repairs"]:
            row["r1"] = "REPAIRED"
        row["_text"] = text
        row["_original"] = original
        rows.append(row)
        if idx % 50 == 0:
            progress(int(5 + idx * 25 / total), "round 1 %d/%d" % (idx, total))
    progress(30, "round 1 complete")

    # ---------------- ROUND 2 : mandated import injection ----------------
    self_names = {"veritasceleritas.py", "via_netsupport.py", "veritasaegisnexus.py"}
    for idx, row in enumerate(rows):
        if row["r1"] in ("SYNTAX_ERROR", "READ_FAIL"):
            row["r2"] = "BLOCKED"
            row["r2_error"] = "round 1 did not yield a parseable file"
            continue
        text = row["_text"]
        low_name = row["name"].lower()
        probe = text.lower()
        row["fetcher"] = any(sig in probe for sig in FETCH_SIGNALS)

        needs = []
        if low_name not in self_names:
            needs.append("celeritas")
        if row["fetcher"] and low_name != "via_netsupport.py":
            needs.append("netsupport")
        if row["layer"] == "VDF":
            needs.append("codex")
        if not needs:
            row["r2"] = "NOT_REQUIRED"
            continue

        stripped, had_block = strip_block(text)
        line = insertion_line(stripped)
        if line is None:
            row["r2"] = "INJECT_FAILED"
            row["r2_error"] = "no insertion point"
            continue
        lines = stripped.splitlines(True)
        block = build_block(cfg, needs)
        head = "".join(lines[: line - 1])
        tail = "".join(lines[line - 1:]).lstrip("\n")
        if head and not head.endswith("\n"):
            head += "\n"
        candidate = head + block + "\n" + tail
        err = parse_error(candidate)
        if err:
            row["r2"] = "INJECT_FAILED"
            row["r2_error"] = err
            continue
        row["_text"] = candidate
        row["injected"] = needs
        row["r2"] = "REINJECTED" if had_block else "INJECTED"
        if idx % 50 == 0:
            progress(int(30 + idx * 25 / total), "round 2 %d/%d" % (idx, total))
    progress(58, "round 2 complete")

    # ---------------- write (backup first, never delete) ----------------
    written = 0
    for row in rows:
        if row["r1"] == "READ_FAIL":
            continue
        if row["_text"] == row["_original"]:
            continue
        if dry:
            continue
        rel = os.path.join(row["layer"], row["rel"])
        dest = os.path.join(backup_dir, rel)
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(row["path"], dest)
            with io.open(row["path"], "w", encoding="utf-8", newline="") as handle:
                handle.write(row["_text"])
            row["written"] = True
            written += 1
        except OSError as exc:
            row["r2_error"] = (row["r2_error"] + " | write: %s" % exc).strip(" |")
    progress(72, "wrote %d files (backup kept)" % written)

    # ---------------- ROUND 3 : verify + library resolution ----------------
    all_imports = {}
    local_modules = set()
    for row in rows:
        local_modules.add(os.path.splitext(row["name"])[0].lower())
    sup = cfg.get("supportive", "")
    if os.path.isdir(sup):
        for name in os.listdir(sup):
            if name.lower().endswith(".py"):
                local_modules.add(os.path.splitext(name)[0].lower())

    for row in rows:
        text = row.get("_text", "")
        if not text:
            row["r3"] = "SKIPPED"
            continue
        if row["written"]:
            try:
                text = open(row["path"], "rb").read().decode("utf-8", "replace")
            except OSError:
                pass
        err = parse_error(text)
        if err:
            row["r3"] = "VERIFY_FAIL"
            row["r1_error"] = row["r1_error"] or err
            continue
        row["r3"] = "VERIFIED"
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mods.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    mods.add(node.module.split(".")[0])
        row["imports"] = sorted(mods)
        for mod in mods:
            all_imports.setdefault(mod, []).append(row["name"])

    missing = []
    for mod, users in sorted(all_imports.items()):
        low = mod.lower()
        if mod in STDLIB or low in local_modules or mod.startswith("_via"):
            continue
        try:
            found = importlib.util.find_spec(mod) is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            found = False
        if not found:
            missing.append({"module": mod, "used_by": sorted(set(users))[:12],
                            "count": len(set(users))})
    progress(92, "round 3 complete: %d missing libraries" % len(missing))

    for row in rows:
        row.pop("_text", None)
        row.pop("_original", None)

    payload = {
        "engine": "via_polyglot_repair",
        "version": "v0100",
        "dry_run": dry,
        "files": len(rows),
        "written": written,
        "syntax_errors": len([r for r in rows if r["r1"] == "SYNTAX_ERROR"]),
        "repaired": len([r for r in rows if r["r1"] == "REPAIRED"]),
        "injected": len([r for r in rows if r["r2"] in ("INJECTED", "REINJECTED")]),
        "inject_failed": len([r for r in rows if r["r2"] == "INJECT_FAILED"]),
        "verified": len([r for r in rows if r["r3"] == "VERIFIED"]),
        "missing_libraries": missing,
        "pip_command": ("pip install " + " ".join(m["module"] for m in missing)) if missing else "",
        "rows": rows,
    }
    with io.open(cfg["out_json"], "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1)
    progress(100, "report written")


if __name__ == "__main__":
    main()
'@

$rootMap = [ordered]@{}
foreach ($key in $roots.Keys) { $rootMap[$key] = $roots[$key] }
$config = [ordered]@{
    roots      = $rootMap
    supportive = $SupportiveDir
    codex_ps1  = $CodexPs1
    backup_dir = $BackupDir
    out_json   = $ReportJson
    dry_run    = $DryRun.IsPresent
}
Write-Utf8NoBom -Path $EnginePath -Text $PyEngine
Write-Utf8NoBom -Path $ConfigPath -Text ($config | ConvertTo-Json -Depth 5)
Write-Stage -Message ('Engine written: ' + $EnginePath) -Percent 12 -Level 'OK'
$modeText = 'APPLY (會實際改檔，改前先備份)'
if ($DryRun) { $modeText = 'DRY-RUN (只分析不改檔)' }
Write-Stage -Message ('Mode: ' + $modeText) -Percent 13

# --- run the engine live (no output redirection, LL#26) ---
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName  = $pyExe
$psi.Arguments = ('"' + $EnginePath + '" "' + $ConfigPath + '"')
$psi.UseShellExecute        = $false
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError  = $false
$psi.CreateNoWindow         = $true
$proc = [System.Diagnostics.Process]::Start($psi)
$proc.WaitForExit()
if ($proc.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $ReportJson)) {
    Write-Stage -Message ('引擎結束碼 ' + $proc.ExitCode + '，未產生報告') -Percent 100 -Level 'FAIL'
    return
}
Write-Stage -Message 'Engine finished, reading report' -Percent 70 -Level 'OK'

$report = Get-Content -LiteralPath $ReportJson -Raw -Encoding UTF8 | ConvertFrom-Json
$rows    = @($report.rows)
$missing = @($report.missing_libraries)

$manual  = @($rows | Where-Object { $_.r1 -eq 'SYNTAX_ERROR' -or $_.r1 -eq 'READ_FAIL' })
$failed  = @($rows | Where-Object { $_.r2 -eq 'INJECT_FAILED' })
$written = @($rows | Where-Object { $_.written })

Write-Stage -Message ('Round 1: ' + $report.files + ' files, ' + $report.repaired + ' repaired, ' + $report.syntax_errors + ' need manual fix') -Percent 74 -Level $(if ($report.syntax_errors -gt 0) { 'WARN' } else { 'OK' })
Write-Stage -Message ('Round 2: ' + $report.injected + ' injected, ' + $report.inject_failed + ' failed') -Percent 78 -Level $(if ($report.inject_failed -gt 0) { 'WARN' } else { 'OK' })
Write-Stage -Message ('Round 3: ' + $report.verified + ' verified, ' + $missing.Count + ' libraries missing') -Percent 82 -Level $(if ($missing.Count -gt 0) { 'WARN' } else { 'OK' })
Write-Stage -Message ('Files rewritten: ' + $written.Count + ' (backup: ' + $BackupDir + ')') -Percent 84 -Level 'OK'

# --- rollback plan (append-only: restores from backup, deletes nothing) ---
$rbLines = [System.Collections.Generic.List[string]]::new()
$rbLines.Add('#requires -Version 7.0')
$rbLines.Add('param([switch]$Commit)')
$rbLines.Add('# Rollback for VIA Polyglot Repair run ' + $Script:Stamp + ' - dry-run by default.')
$rbLines.Add('$ErrorActionPreference = ''Stop''')
$rbLines.Add('function Restore-One { param([string]$From, [string]$To)')
$rbLines.Add('    if (-not (Test-Path -LiteralPath $From)) { Write-Host (''missing backup: '' + $From) -ForegroundColor DarkGray; return }')
$rbLines.Add('    if (-not $Commit) { Write-Host (''[DRY] restore '' + $To) -ForegroundColor Yellow; return }')
$rbLines.Add('    Copy-Item -LiteralPath $From -Destination $To -Force')
$rbLines.Add('    Write-Host (''[RESTORED] '' + $To) -ForegroundColor Green }')
foreach ($row in $written) {
    $from = Join-Path $BackupDir (Join-Path $row.layer ($row.rel -replace '/', '\'))
    $rbLines.Add("Restore-One -From '" + $from.Replace("'", "''") + "' -To '" + ([string]$row.path).Replace("'", "''") + "'")
}
Write-Utf8NoBom -Path $RollbackPs -Text (($rbLines -join "`n") + "`n")

# --- optional library install ---
$installLog = ''
if ($InstallLibs -and $missing.Count -gt 0) {
    $args = @('-m', 'pip', 'install') + @($missing | ForEach-Object { [string]$_.module })
    Write-Stage -Message ('pip install ' + (($missing | ForEach-Object { $_.module }) -join ' ')) -Percent 88
    $ipsi = [System.Diagnostics.ProcessStartInfo]::new()
    $ipsi.FileName = $pyExe
    $ipsi.Arguments = ($args -join ' ')
    $ipsi.UseShellExecute = $false
    $ipsi.RedirectStandardOutput = $false
    $ipsi.RedirectStandardError = $false
    $iproc = [System.Diagnostics.Process]::Start($ipsi)
    $iproc.WaitForExit()
    $installLog = 'pip exit code ' + $iproc.ExitCode
    Write-Stage -Message $installLog -Percent 90 -Level $(if ($iproc.ExitCode -eq 0) { 'OK' } else { 'WARN' })
} elseif ($missing.Count -gt 0) {
    $installLog = '未安裝（加 -InstallLibs 才會實際安裝）'
}

# --- HTML ---
function New-Rows {
    param([object[]]$Items, [string[]]$Fields, [string]$StatusField = '', [int]$Limit = 600)
    $sb = [System.Text.StringBuilder]::new()
    $count = 0
    foreach ($item in $Items) {
        if ($count -ge $Limit) { break }
        $count++
        $null = $sb.Append('<tr>')
        foreach ($field in $Fields) {
            $value = ''
            if ($item.PSObject.Properties.Name -contains $field) {
                $raw = $item.$field
                if ($raw -is [System.Array]) { $value = ($raw -join ', ') }
                elseif ($raw -is [bool]) { $value = $(if ($raw) { 'YES' } else { '' }) }
                else { $value = [string]$raw }
            }
            $cls = ''
            if ($StatusField -and $field -eq $StatusField) {
                if ($value -match 'OK$|VERIFIED|INJECTED|REPAIRED') { $cls = " class='ok'" }
                elseif ($value -match 'FAIL|ERROR') { $cls = " class='fail'" }
                elseif ($value -match 'BLOCKED|SKIPPED|NOT_REQUIRED|PENDING') { $cls = " class='warn'" }
            }
            $null = $sb.Append('<td' + $cls + '>' + (ConvertTo-HtmlText -Text $value) + '</td>')
        }
        $null = $sb.Append('</tr>')
    }
    if ($count -eq 0) { $null = $sb.Append("<tr><td colspan='" + $Fields.Count + "' class='muted'>—— 無 ——</td></tr>") }
    return $sb.ToString()
}

$mainRowsHtml   = New-Rows -Items @($rows | Sort-Object -Property @{ e = 'layer'; desc = $false }, @{ e = 'name'; desc = $false }) -Fields @('layer','name','r1','repairs','r2','injected','r3','fetcher','written') -StatusField 'r3'
$manualRowsHtml = New-Rows -Items $manual -Fields @('layer','name','r1','r1_error','path') -StatusField 'r1'
$failRowsHtml   = New-Rows -Items $failed -Fields @('layer','name','r2_error','path')
$libRowsHtml    = New-Rows -Items $missing -Fields @('module','count','used_by')
$logText        = ConvertTo-HtmlText -Text ($Script:Log -join "`n")
$pipCommand     = [string]$report.pip_command

$overall = 'GREEN'
if ($missing.Count -gt 0 -or $report.inject_failed -gt 0) { $overall = 'AMBER' }
if ($report.syntax_errors -gt 0) { $overall = 'AMBER' }
$overallClass = 'ok'
if ($overall -eq 'AMBER') { $overallClass = 'warn' }

$html = @"
<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Polyglot Repair + Import Injector v0100</title>
<style>
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;padding:34px 40px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:14px}
.seal{display:inline-flex;width:42px;height:42px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:23px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:18px;letter-spacing:.16em;text-transform:uppercase;margin:12px 0 4px}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:16px;letter-spacing:.06em;margin:28px 0 6px}
.lede{color:#6c6e70;font-size:12.5px;margin:0 0 14px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:18px 0 6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:13px 15px}
.card .k{font-size:11px;letter-spacing:.12em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:23px;font-family:"Noto Serif TC",Georgia,serif;margin-top:4px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:12.5px}
th,td{border-bottom:1px solid #ececed;padding:7px 9px;text-align:left;vertical-align:top;word-break:break-all}
th{background:#eeeeef;font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:#5c5e60}
tr:hover td{background:#fbfbfb}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:16px}
pre{background:var(--panel);border:1px solid var(--line);padding:13px;font-size:12px;white-space:pre-wrap;max-height:40vh;overflow:auto}
code{background:#ececed;padding:2px 6px;border-radius:2px}
</style></head><body>
<div class="seal">修</div>
<h1>Polyglot Repair + Import Injector</h1>
<p class="lede">$(ConvertTo-HtmlText -Text ($Layers -join ' / ')) · $($Script:Stamp) · $modeText · 備份 $(ConvertTo-HtmlText -Text $BackupDir)</p>
<div class="cards">
  <div class="card"><div class="k">Overall</div><div class="v $overallClass">$overall</div></div>
  <div class="card"><div class="k">Python Files</div><div class="v">$($report.files)</div></div>
  <div class="card"><div class="k">R1 Repaired</div><div class="v ok">$($report.repaired)</div></div>
  <div class="card"><div class="k">R1 Manual</div><div class="v warn">$($report.syntax_errors)</div></div>
  <div class="card"><div class="k">R2 Injected</div><div class="v ok">$($report.injected)</div></div>
  <div class="card"><div class="k">R3 Verified</div><div class="v ok">$($report.verified)</div></div>
  <div class="card"><div class="k">Missing Libs</div><div class="v warn">$($missing.Count)</div></div>
  <div class="card"><div class="k">Rewritten</div><div class="v">$($written.Count)</div></div>
</div>

<h2>缺少的函式庫</h2>
<p class="lede">$(ConvertTo-HtmlText -Text $installLog)</p>
<p><code>$(ConvertTo-HtmlText -Text $pipCommand)</code></p>
<table><tr><th>Module</th><th>被幾個檔用</th><th>使用者</th></tr>$libRowsHtml</table>

<h2>需要人工修的語法錯誤</h2>
<p class="lede">這些檔案三輪都無法自動安全修復，注入也一律跳過（不會把壞檔改得更壞）。</p>
<table><tr><th>Layer</th><th>檔名</th><th>狀態</th><th>錯誤</th><th>路徑</th></tr>$manualRowsHtml</table>

<h2>三輪逐檔結果</h2>
<p class="lede">R1 語法修復 · R2 import 注入 · R3 複驗；fetcher＝偵測到對外擷取行為，已加掛 VIA_NetSupport。</p>
<table><tr><th>Layer</th><th>檔名</th><th>R1</th><th>修復動作</th><th>R2</th><th>注入</th><th>R3</th><th>Fetcher</th><th>已改寫</th></tr>$mainRowsHtml</table>

<h2>注入失敗</h2>
<table><tr><th>Layer</th><th>檔名</th><th>原因</th><th>路徑</th></tr>$failRowsHtml</table>

<h2>執行日誌</h2>
<pre>$logText</pre>
</body></html>
"@

Write-Utf8NoBom -Path $HtmlPath -Text $html
Write-Stage -Message ('Report rendered. Overall ' + $overall) -Percent 100 -Level 'OK'
Write-Progress -Activity 'VIA Polyglot Repair + Import Injector v0100' -Completed

Write-Host ''
Write-Host (' report   : ' + $HtmlPath)   -ForegroundColor DarkCyan
Write-Host (' json     : ' + $ReportJson) -ForegroundColor DarkCyan
Write-Host (' backup   : ' + $BackupDir)  -ForegroundColor DarkCyan
Write-Host (' rollback : ' + $RollbackPs) -ForegroundColor DarkCyan
if ($pipCommand) {
    Write-Host ''
    Write-Host ' 待安裝函式庫：' -ForegroundColor Yellow
    Write-Host ('   ' + $pipCommand) -ForegroundColor Yellow
}
Write-Host ''
Write-Host '============================================================'
Write-Host (' ROUND 1/2/3 COMPLETE  ->  ' + $overall)
Write-Host ' Append-only. 原檔已備份，rollback 腳本已產出。'
Write-Host '============================================================'

if (-not $NoBrowser) {
    try { Start-Process -FilePath $HtmlPath | Out-Null } catch { Write-Host ' (browser launch skipped)' -ForegroundColor DarkGray }
}
