#requires -Version 7.0
param(
    [string]$EngineRoot  = 'C:\VIA\via-markitdown',
    [string]$VenvPath    = 'C:\Users\tonyk\envs\via_markitdown',
    [string]$InputPath   = '',
    [string]$OutputPath  = '',
    [int]$MaxWorkers     = 8,
    [switch]$SkipInstall,
    [switch]$SelfTestOnly,
    [switch]$AllowRemote,
    [switch]$NoOpen
)

# =====================================================================
# VIA MarkItDown Engine (VMD)  ENG-006  v0100
# Subsystem : via-markitdown
# Purpose   : microsoft/markitdown full-tool engine
#             all converters + all optional extras + plugins
#             capability probe -> self-test -> batch convert -> HTML console
# Governance: append-only (only-increase). Nothing is deleted or
#             overwritten. Existing outputs get __v2/__v3 siblings.
# LL rules  : no aliases / no Read-Host / no exit / ProcessStartInfo
#             UTF8 no-BOM writes / param() first / # line comments only
# Run with  : pwsh -NoProfile -ExecutionPolicy Bypass -File <this file>
# =====================================================================

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$script:StartedAt = Get-Date
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:Phases    = [System.Collections.Generic.List[object]]::new()
$script:LogLines  = [System.Collections.Generic.List[string]]::new()
$script:EngineRoot = $EngineRoot
$script:RunId     = 'VIA-VMD-' + $script:StartedAt.ToString('yyyyMMdd') + '-' + ('{0:D6}' -f (Get-Random -Minimum 1 -Maximum 999999))

$script:Dirs = [ordered]@{
    root      = $EngineRoot
    bin       = Join-Path $EngineRoot 'bin'
    engine    = Join-Path $EngineRoot 'engine'
    config    = Join-Path $EngineRoot 'config'
    data      = Join-Path $EngineRoot 'data'
    logs      = Join-Path $EngineRoot 'logs'
    reports   = Join-Path $EngineRoot 'reports'
    inbox     = Join-Path $EngineRoot 'inbox'
    outbox    = Join-Path $EngineRoot 'outbox'
}

# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------

function Get-CleanPath {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
    return $Value.Trim().Trim("'").Trim('"').TrimEnd('\')
}

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $stamp = (Get-Date).ToString('HH:mm:ss')
    $line  = '[' + $stamp + '] [' + $Level + '] ' + $Message
    $script:LogLines.Add($line)
    $color = 'Gray'
    if ($Level -eq 'OK')    { $color = 'Green' }
    if ($Level -eq 'WARN')  { $color = 'Yellow' }
    if ($Level -eq 'FAIL')  { $color = 'Red' }
    if ($Level -eq 'PHASE') { $color = 'Cyan' }
    Write-Host $line -ForegroundColor $color
}

function Show-Prog {
    param([string]$Activity, [string]$Status, [int]$Percent)
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $Percent
}

function Save-PhaseLog {
    param([string]$Name, [string]$State, [string]$Detail = '')
    $script:Phases.Add([pscustomobject]@{
        Name   = $Name
        State  = $State
        Detail = $Detail
        At     = (Get-Date).ToString('HH:mm:ss')
    })
}

function Write-TextFile {
    param([string]$Path, [string]$Content)
    $dir = Split-Path -Path $Path -Parent
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

function Get-FileSha {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    $h = Get-FileHash -LiteralPath $Path -Algorithm SHA256
    return $h.Hash.Substring(0, 12).ToLower()
}

# ProcessStartInfo runner.
# Stream mode (LL#26): no redirect, child writes straight to the console,
# so long installs never look frozen.
function Invoke-VIAProcess {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList,
        [switch]$Capture,
        [string]$WorkDir = ''
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName  = $FilePath
    $psi.UseShellExecute = $false
    if ($WorkDir -ne '') { $psi.WorkingDirectory = $WorkDir }
    foreach ($a in $ArgumentList) { $psi.ArgumentList.Add($a) }
    if ($Capture) {
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
        $psi.StandardErrorEncoding  = [System.Text.Encoding]::UTF8
    } else {
        $psi.RedirectStandardOutput = $false
        $psi.RedirectStandardError  = $false
    }
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $stdout = ''
    $stderr = ''
    try {
        $proc.Start() | Out-Null
        if ($Capture) {
            # both streams drain concurrently; a full buffer on one can
            # never block the other, so the child cannot stall
            $tOut = $proc.StandardOutput.ReadToEndAsync()
            $tErr = $proc.StandardError.ReadToEndAsync()
            $proc.WaitForExit()
            $stdout = $tOut.GetAwaiter().GetResult()
            $stderr = $tErr.GetAwaiter().GetResult()
        } else {
            $proc.WaitForExit()
        }
        return [pscustomobject]@{ Code = $proc.ExitCode; Out = $stdout; Err = $stderr }
    } catch {
        return [pscustomobject]@{ Code = -1; Out = ''; Err = $_.Exception.Message }
    }
}

function Test-RealPython {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    if ($Path -match 'WindowsApps') { return $false }
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $item = Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue
    if ($null -eq $item) { return $false }
    if ($item.Length -lt 20000) { return $false }
    return $true
}

# ---------------------------------------------------------------------
# PHASE 1  paths (append-only: create only what is missing)
# ---------------------------------------------------------------------

Write-Host ''
Write-Host '  VeritasIntelligenceAnalytics MarkItDown Engine (VMD)' -ForegroundColor White
Write-Host '  VERITAS INTELLIGENCE SYSTEM' -ForegroundColor DarkGray
Write-Host '  ENG-006 v0101 · all-format document -> Markdown · append-only' -ForegroundColor DarkGray
Write-Host ''

Show-Prog -Activity 'VMD' -Status 'Phase 1 / 9  paths' -Percent 5
Write-Log 'Phase 1  bootstrap paths' 'PHASE'
foreach ($k in $script:Dirs.Keys) {
    $p = $script:Dirs[$k]
    if (-not (Test-Path -LiteralPath $p)) {
        New-Item -ItemType Directory -Path $p -Force | Out-Null
        Write-Log ('created  ' + $p) 'OK'
    } else {
        Write-Log ('reuse    ' + $p)
    }
}
Save-PhaseLog -Name 'Paths' -State 'OK' -Detail ($script:Dirs.Count.ToString() + ' directories')

# ---------------------------------------------------------------------
# PHASE 2  resolve a real Python 3.10+ runtime
# ---------------------------------------------------------------------

Show-Prog -Activity 'VMD' -Status 'Phase 2 / 9  python runtime' -Percent 12
Write-Log 'Phase 2  resolve python runtime (Store aliases rejected)' 'PHASE'

$script:BasePython = ''
$candidates = @(
    'C:\Users\tonyk\envs\via_core_312\Scripts\python.exe',
    'C:\Users\tonyk\envs\via_core\Scripts\python.exe',
    'C:\Users\tonyk\envs\venv_core\Scripts\python.exe',
    'C:\Python312\python.exe',
    'C:\Python311\python.exe',
    'C:\Program Files\Python312\python.exe',
    'C:\Program Files\Python311\python.exe'
)
foreach ($c in $candidates) {
    if (Test-RealPython -Path $c) { $script:BasePython = $c; break }
}

if ($script:BasePython -eq '') {
    foreach ($ver in @('-3.12', '-3.11', '-3.13')) {
        $probe = Invoke-VIAProcess -FilePath 'py' -ArgumentList @($ver, '-c', 'import sys;print(sys.executable)') -Capture
        if ($probe.Code -eq 0) {
            $exe = $probe.Out.Trim()
            if (Test-RealPython -Path $exe) { $script:BasePython = $exe; break }
        }
    }
}

if ($script:BasePython -eq '') {
    $cmd = Get-Command -Name 'python' -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        if (Test-RealPython -Path $cmd.Source) { $script:BasePython = $cmd.Source }
    }
}

if ($script:BasePython -eq '') {
    Write-Log 'BLOCKED_PYTHON_RUNTIME_ABSENT  no real python.exe found (Store/WindowsApps aliases rejected)' 'FAIL'
    Write-Log 'remedy: winget install Python.Python.3.12   then re-run this script' 'WARN'
    Save-PhaseLog -Name 'Python runtime' -State 'BLOCKED' -Detail 'no real interpreter'
} else {
    Write-Log ('runtime  ' + $script:BasePython) 'OK'
    Save-PhaseLog -Name 'Python runtime' -State 'OK' -Detail $script:BasePython
}

# ---------------------------------------------------------------------
# PHASE 3  isolated venv  (reuse if present)
# ---------------------------------------------------------------------

Show-Prog -Activity 'VMD' -Status 'Phase 3 / 9  venv' -Percent 20
Write-Log 'Phase 3  isolated venv' 'PHASE'

$script:VenvPython = Join-Path $VenvPath 'Scripts\python.exe'
$script:VenvReady  = $false

if ($script:BasePython -ne '') {
    if (Test-Path -LiteralPath $script:VenvPython) {
        Write-Log ('reuse venv  ' + $VenvPath) 'OK'
        $script:VenvReady = $true
    } else {
        Write-Log ('create venv ' + $VenvPath)
        $r = Invoke-VIAProcess -FilePath $script:BasePython -ArgumentList @('-m', 'venv', $VenvPath)
        if ($r.Code -eq 0 -and (Test-Path -LiteralPath $script:VenvPython)) {
            Write-Log 'venv created' 'OK'
            $script:VenvReady = $true
        } else {
            Write-Log ('venv creation failed: ' + $r.Err) 'FAIL'
        }
    }
}
if ($script:VenvReady) {
    Save-PhaseLog -Name 'Venv' -State 'OK' -Detail $VenvPath
} else {
    Save-PhaseLog -Name 'Venv' -State 'BLOCKED' -Detail $VenvPath
}

# ---------------------------------------------------------------------
# PHASE 4  install markitdown with every optional extra
#          NumPy golden rule enforced by constraints file
# ---------------------------------------------------------------------

Show-Prog -Activity 'VMD' -Status 'Phase 4 / 9  install all tools' -Percent 32
Write-Log 'Phase 4  install markitdown[all] + plugins' 'PHASE'

$constraintsPath = Join-Path $script:Dirs.engine 'constraints.txt'
Write-TextFile -Path $constraintsPath -Content @'
# VIA golden rule: NumPy must stay on the 1.x line
numpy>=1.24,<2.0
'@

$script:InstallState = 'SKIPPED'
if ($script:VenvReady -and -not $SkipInstall) {
    Write-Log 'pip upgrade  (live output, no buffering)'
    Invoke-VIAProcess -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel', '--disable-pip-version-check') | Out-Null

    Write-Log 'installing markitdown[all]  this pulls every converter extra'
    $mainArgs = @(
        '-m', 'pip', 'install', '--upgrade',
        'markitdown[all]',
        '-c', $constraintsPath,
        '--disable-pip-version-check'
    )
    $rm = Invoke-VIAProcess -FilePath $script:VenvPython -ArgumentList $mainArgs
    if ($rm.Code -eq 0) {
        Write-Log 'markitdown[all] installed' 'OK'
        $script:InstallState = 'OK'
    } else {
        Write-Log 'markitdown[all] failed, retrying extra-by-extra' 'WARN'
        $script:InstallState = 'PARTIAL'
        foreach ($x in @('pdf', 'docx', 'pptx', 'xlsx', 'xls', 'outlook', 'audio-transcription', 'youtube-transcription', 'az-doc-intel', 'az-content-understanding')) {
            $spec = 'markitdown[' + $x + ']'
            $ri = Invoke-VIAProcess -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '--upgrade', $spec, '-c', $constraintsPath, '--disable-pip-version-check')
            if ($ri.Code -eq 0) { Write-Log ('extra OK   ' + $x) 'OK' } else { Write-Log ('extra FAIL ' + $x) 'WARN' }
        }
    }

    # optional companions: OCR plugin + an OpenAI-compatible client for image
    # description. Both stay DORMANT until an endpoint/key is configured.
    foreach ($opt in @('markitdown-ocr', 'openai', 'magika')) {
        $ro = Invoke-VIAProcess -FilePath $script:VenvPython -ArgumentList @('-m', 'pip', 'install', '--upgrade', $opt, '-c', $constraintsPath, '--disable-pip-version-check')
        if ($ro.Code -eq 0) { Write-Log ('optional OK   ' + $opt) 'OK' } else { Write-Log ('optional skip ' + $opt) 'WARN' }
    }
} elseif ($SkipInstall) {
    Write-Log 'install skipped by switch' 'WARN'
}
Save-PhaseLog -Name 'Install' -State $script:InstallState -Detail 'markitdown[all] + markitdown-ocr + openai + magika'

# ---------------------------------------------------------------------
# PHASE 5  self-extract the Python engine + config + cmd shim
# ---------------------------------------------------------------------

Show-Prog -Activity 'VMD' -Status 'Phase 5 / 9  extract engine' -Percent 48
Write-Log 'Phase 5  self-extract engine' 'PHASE'

$enginePy = Join-Path $script:Dirs.engine 'VIA_MarkItDown_Engine.py'

$engineCode = @'
# ---------------------------------------------------------------------
# VIA MarkItDown Engine (VMD)  ENG-006
# Self-extracted by Invoke-VIA-MarkItDown-v0101.ps1
#
# Wraps every microsoft/markitdown capability behind one governed API:
#   - capability probe (converters + extras, ACTIVE / DORMANT)
#   - plugin discovery
#   - safe-tier conversion (convert_local by default; remote is opt-in)
#   - recursive batch with a thread pool
#   - append-only outputs (never overwrite; __v2, __v3 siblings)
#   - evidence-honesty tagging on every produced artifact
#   - JSONL SSOT manifest + JSON run summary for the PowerShell console
# ---------------------------------------------------------------------

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

VMD_VERSION = "v0101"
ENG_CODE = "ENG-006"
SUBSYSTEM = "via-markitdown"

# every optional extra markitdown ships, mapped to its import probe
EXTRA_PROBES = {
    "pdf": ["pdfminer"],
    "docx": ["mammoth"],
    "pptx": ["pptx"],
    "xlsx": ["openpyxl", "pandas"],
    "xls": ["xlrd"],
    "outlook": ["olefile"],
    "html": ["bs4", "markdownify"],
    "audio-transcription": ["speech_recognition", "pydub"],
    "youtube-transcription": ["youtube_transcript_api"],
    "az-doc-intel": ["azure.ai.documentintelligence"],
    "az-content-understanding": ["azure.identity"],
    "type-detection": ["magika"],
    "ocr-plugin": ["markitdown_ocr"],
    "llm-vision": ["openai"],
}

# extensions markitdown handles natively
SUPPORTED_EXT = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".csv", ".tsv",
    ".json", ".xml", ".html", ".htm", ".txt", ".md", ".msg", ".epub", ".zip",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
    ".wav", ".mp3", ".m4a", ".ipynb", ".rss", ".atom",
}

# formats whose extraction can carry financial figures -> never trusted raw
NUMERIC_RISK_EXT = {".pdf", ".xlsx", ".xls", ".csv", ".tsv", ".docx", ".pptx", ".msg"}
NUMBER_RE = re.compile(r"\d[\d,]{2,}(?:\.\d+)?")


def utcnow() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def via_code(kind: str, name: str, context: str = SUBSYSTEM) -> str:
    raw = "|".join([kind, name, context]).encode("utf-8")
    digest = hashlib.blake2s(raw, digest_size=3).hexdigest().upper()
    return "VIA-{0}-{1}".format(kind, digest)


def blake_of_file(path: Path, size: int = 8) -> str:
    h = hashlib.blake2s(digest_size=size)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 256), b""):
            h.update(chunk)
    return h.hexdigest()


def blake_of_text(text: str, size: int = 8) -> str:
    return hashlib.blake2s(text.encode("utf-8", "replace"), digest_size=size).hexdigest()


def probe_extras() -> dict:
    out = {}
    for extra, mods in EXTRA_PROBES.items():
        missing = []
        for m in mods:
            try:
                importlib.import_module(m)
            except Exception:
                missing.append(m)
        out[extra] = {
            "state": "ACTIVE" if not missing else "DORMANT",
            "modules": mods,
            "missing": missing,
        }
    return out


def list_converters(md) -> list:
    names = []
    for attr in ("_converters", "converters", "_page_converters"):
        regs = getattr(md, attr, None)
        if not regs:
            continue
        try:
            for r in regs:
                conv = getattr(r, "converter", r)
                names.append(type(conv).__name__)
            break
        except Exception:
            continue
    return sorted(set(names))


def list_plugins() -> list:
    found = []
    try:
        from importlib.metadata import entry_points
        eps = entry_points()
        try:
            group = eps.select(group="markitdown.plugin")
        except Exception:
            group = eps.get("markitdown.plugin", [])
        for ep in group:
            found.append(ep.name)
    except Exception:
        pass
    return sorted(set(found))


class VMDEngine:
    def __init__(self, root: Path, cfg: dict, allow_remote: bool = False):
        self.root = root
        self.cfg = cfg
        self.allow_remote = allow_remote
        self.manifest_path = root / "data" / "VMD_SSOT_manifest.jsonl"
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.md = None
        self.init_error = ""
        self._build()

    def _build(self):
        try:
            from markitdown import MarkItDown
        except Exception as exc:
            self.init_error = "markitdown import failed: {0}".format(exc)
            return

        kwargs = {"enable_plugins": bool(self.cfg.get("enable_plugins", True))}

        # LLM image description / OCR plugin  -> only if a key is configured
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if api_key and self.cfg.get("llm_model"):
            try:
                from openai import OpenAI
                kwargs["llm_client"] = OpenAI()
                kwargs["llm_model"] = self.cfg["llm_model"]
                if self.cfg.get("llm_prompt"):
                    kwargs["llm_prompt"] = self.cfg["llm_prompt"]
            except Exception:
                pass

        # Azure Document Intelligence  -> only if an endpoint is configured
        if self.cfg.get("docintel_endpoint"):
            kwargs["docintel_endpoint"] = self.cfg["docintel_endpoint"]

        # Azure Content Understanding  -> only if an endpoint is configured
        if self.cfg.get("cu_endpoint"):
            kwargs["cu_endpoint"] = self.cfg["cu_endpoint"]
            if self.cfg.get("cu_analyzer_id"):
                kwargs["cu_analyzer_id"] = self.cfg["cu_analyzer_id"]

        try:
            self.md = MarkItDown(**kwargs)
        except TypeError:
            # older wheel without CU support -> drop unknown kwargs and retry
            for k in ("cu_endpoint", "cu_analyzer_id"):
                kwargs.pop(k, None)
            self.md = MarkItDown(**kwargs)
        except Exception as exc:
            self.init_error = "MarkItDown init failed: {0}".format(exc)

    # -- safe tier: narrowest API that fits the input -------------------
    def _convert(self, target: str):
        low = target.lower()
        if low.startswith("http://") or low.startswith("https://"):
            if not self.allow_remote:
                raise PermissionError("REMOTE_BLOCKED  pass --allow-remote to enable URI fetch")
            if hasattr(self.md, "convert_uri"):
                return self.md.convert_uri(target)
            return self.md.convert(target)
        if hasattr(self.md, "convert_local"):
            return self.md.convert_local(target)
        return self.md.convert(target)

    @staticmethod
    def _markdown_of(result) -> str:
        for attr in ("markdown", "text_content"):
            val = getattr(result, attr, None)
            if isinstance(val, str):
                return val
        return str(result)

    @staticmethod
    def _classify(ext: str, body: str) -> str:
        if ext in NUMERIC_RISK_EXT and NUMBER_RE.search(body):
            return "UNVERIFIED_EXTRACTION"
        return "EXTRACTED_RAW"

    # -- append-only write ---------------------------------------------
    def _write_append_only(self, out_dir: Path, stem: str, body: str) -> dict:
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / (stem + ".md")
        new_hash = blake_of_text(body)
        if not target.exists():
            target.write_text(body, encoding="utf-8", newline="\n")
            return {"path": str(target), "write": "CREATED", "hash": new_hash}
        old = target.read_text(encoding="utf-8", errors="replace")
        if blake_of_text(old) == new_hash:
            return {"path": str(target), "write": "REUSED", "hash": new_hash}
        n = 2
        while True:
            sibling = out_dir / "{0}__v{1}.md".format(stem, n)
            if not sibling.exists():
                sibling.write_text(body, encoding="utf-8", newline="\n")
                return {"path": str(sibling), "write": "VERSIONED", "hash": new_hash}
            n += 1

    def convert_one(self, src: str, out_dir: Path) -> dict:
        started = time.perf_counter()
        p = Path(src)
        ext = p.suffix.lower()
        rec = {
            "id": "",
            "source": src,
            "ext": ext,
            "status": "FAIL",
            "write": "",
            "output": "",
            "chars": 0,
            "evidence": "",
            "source_hash": "",
            "error": "",
            "ms": 0,
            "at": utcnow(),
        }
        try:
            if p.exists() and p.is_file():
                rec["source_hash"] = blake_of_file(p)
            result = self._convert(src)
            body = self._markdown_of(result)
            stem = p.stem if p.name else "remote"
            header = "\n".join([
                "---",
                "via_engine: {0} {1}".format(ENG_CODE, VMD_VERSION),
                "source: {0}".format(src),
                "source_hash: {0}".format(rec["source_hash"]),
                "converted_at: {0}".format(rec["at"]),
                "evidence: {0}".format(self._classify(ext, body)),
                "---",
                "",
            ])
            full = header + body
            written = self._write_append_only(out_dir, stem, full)
            rec.update({
                "status": "OK",
                "write": written["write"],
                "output": written["path"],
                "chars": len(body),
                "evidence": self._classify(ext, body),
                "id": via_code("VMD", stem + "|" + rec["source_hash"]),
            })
        except Exception as exc:
            rec["error"] = "{0}: {1}".format(type(exc).__name__, exc)
        rec["ms"] = int((time.perf_counter() - started) * 1000)
        self._append_manifest(rec)
        return rec

    def _append_manifest(self, rec: dict):
        try:
            with self.manifest_path.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def batch(self, target: str, out_dir: Path, workers: int = 8) -> list:
        files = []
        tp = Path(target)
        if target.lower().startswith("http"):
            files = [target]
        elif tp.is_dir():
            for dirpath, dirnames, filenames in os.walk(tp):
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                for fn in filenames:
                    if Path(fn).suffix.lower() in SUPPORTED_EXT:
                        files.append(str(Path(dirpath) / fn))
        elif tp.is_file():
            files = [str(tp)]

        results = []
        if not files:
            return results
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = {pool.submit(self.convert_one, f, out_dir): f for f in files}
            for fut in as_completed(futures):
                try:
                    results.append(fut.result())
                except Exception as exc:
                    results.append({
                        "source": futures[fut], "status": "FAIL",
                        "error": str(exc), "ext": "", "chars": 0, "ms": 0,
                        "evidence": "", "write": "", "output": "",
                        "source_hash": "", "id": "", "at": utcnow(),
                    })
        results.sort(key=lambda r: r.get("source", ""))
        return results

    # -- self-test ------------------------------------------------------
    def selftest(self) -> list:
        import zipfile
        sandbox = self.root / "data" / "_selftest"
        sandbox.mkdir(parents=True, exist_ok=True)
        out_dir = self.root / "data" / "_selftest_out"

        samples = {}
        (sandbox / "t.txt").write_text("VIA selftest plain text.", encoding="utf-8")
        samples["txt"] = sandbox / "t.txt"
        (sandbox / "t.csv").write_text("ticker,close\n2330,1085\n2454,1420\n", encoding="utf-8")
        samples["csv"] = sandbox / "t.csv"
        (sandbox / "t.json").write_text(json.dumps({"engine": "VMD", "ok": True}), encoding="utf-8")
        samples["json"] = sandbox / "t.json"
        (sandbox / "t.xml").write_text("<root><item>via</item></root>", encoding="utf-8")
        samples["xml"] = sandbox / "t.xml"
        (sandbox / "t.html").write_text(
            "<html><body><h1>VIA</h1><table><tr><td>2330</td><td>1085</td></tr></table></body></html>",
            encoding="utf-8")
        samples["html"] = sandbox / "t.html"
        zp = sandbox / "t.zip"
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr("inner.txt", "zip iteration works")
        samples["zip"] = zp

        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["ticker", "close"])
            ws.append(["2330", 1085])
            xp = sandbox / "t.xlsx"
            wb.save(xp)
            samples["xlsx"] = xp
        except Exception:
            pass

        checks = []
        for kind, path in samples.items():
            rec = self.convert_one(str(path), out_dir)
            checks.append({
                "check": kind,
                "state": "PASS" if rec["status"] == "OK" and rec["chars"] > 0 else "FAIL",
                "detail": rec.get("error", "") or "{0} chars".format(rec["chars"]),
            })
        return checks


def load_config(root: Path) -> dict:
    cfg_path = root / "config" / "vmd_config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="VIA MarkItDown Engine")
    ap.add_argument("--root", required=True)
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--convert", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--allow-remote", action="store_true")
    ap.add_argument("--emit", default="")
    args = ap.parse_args()

    root = Path(args.root)
    cfg = load_config(root)
    engine = VMDEngine(root, cfg, allow_remote=args.allow_remote)

    payload = {
        "engine": {"code": ENG_CODE, "version": VMD_VERSION, "subsystem": SUBSYSTEM},
        "python": sys.version.split()[0],
        "at": utcnow(),
        "init_error": engine.init_error,
        "markitdown_version": "",
        "extras": {},
        "converters": [],
        "plugins": [],
        "gated": {},
        "selftest": [],
        "results": [],
    }

    try:
        from importlib.metadata import version as _v
        payload["markitdown_version"] = _v("markitdown")
    except Exception:
        payload["markitdown_version"] = "unknown"

    if args.probe or args.selftest or args.convert:
        payload["extras"] = probe_extras()
        payload["plugins"] = list_plugins()
        if engine.md is not None:
            payload["converters"] = list_converters(engine.md)
        payload["gated"] = {
            "llm_vision": "ACTIVE" if os.environ.get("OPENAI_API_KEY") and cfg.get("llm_model") else "DORMANT",
            "azure_doc_intel": "ACTIVE" if cfg.get("docintel_endpoint") else "DORMANT",
            "azure_content_understanding": "ACTIVE" if cfg.get("cu_endpoint") else "DORMANT",
            "remote_uri_fetch": "ACTIVE" if args.allow_remote else "DORMANT",
        }

    if engine.md is None:
        payload["init_error"] = payload["init_error"] or "engine not initialised"
    else:
        if args.selftest:
            payload["selftest"] = engine.selftest()
        if args.convert:
            out_dir = Path(args.out) if args.out else (root / "outbox")
            payload["results"] = engine.batch(args.convert, out_dir, args.workers)

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.emit:
        Path(args.emit).parent.mkdir(parents=True, exist_ok=True)
        Path(args.emit).write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
'@

Write-TextFile -Path $enginePy -Content $engineCode
Write-Log ('engine   ' + $enginePy + '  sha=' + (Get-FileSha -Path $enginePy)) 'OK'

# config is append-only: written once, then left alone so your endpoints survive
$cfgPath = Join-Path $script:Dirs.config 'vmd_config.json'
if (-not (Test-Path -LiteralPath $cfgPath)) {
    Write-TextFile -Path $cfgPath -Content @'
{
  "enable_plugins": true,
  "llm_model": "",
  "llm_prompt": "",
  "docintel_endpoint": "",
  "cu_endpoint": "",
  "cu_analyzer_id": "",
  "_note": "leave a field empty to keep that capability DORMANT. set OPENAI_API_KEY in the environment to activate llm_vision."
}
'@
    Write-Log 'config   created (all cloud tiers DORMANT)' 'OK'
} else {
    Write-Log 'config   reuse existing (append-only)' 'OK'
}

# one-word command shim, matching the bin\via-*.cmd convention
$shim = Join-Path $script:Dirs.bin 'via-md.cmd'
$shimBody = '@echo off' + "`r`n" +
            'pwsh -NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -InputPath %1 %2 %3 %4' + "`r`n"
Write-TextFile -Path $shim -Content $shimBody
Write-Log ('shim     ' + $shim) 'OK'
Save-PhaseLog -Name 'Extract engine' -State 'OK' -Detail (Get-FileSha -Path $enginePy)

# ---------------------------------------------------------------------
# PHASE 6  capability probe
# ---------------------------------------------------------------------

Show-Prog -Activity 'VMD' -Status 'Phase 6 / 9  capability probe' -Percent 62
Write-Log 'Phase 6  capability probe' 'PHASE'

$emitPath = Join-Path $script:Dirs.data 'vmd_last_run.json'
$script:Payload = $null

if ($script:VenvReady) {
    $probeArgs = @($enginePy, '--root', $script:Dirs.root, '--probe', '--emit', $emitPath)
    if ($AllowRemote) { $probeArgs += '--allow-remote' }
    $rp = Invoke-VIAProcess -FilePath $script:VenvPython -ArgumentList $probeArgs
    if (Test-Path -LiteralPath $emitPath) {
        $script:Payload = Get-Content -LiteralPath $emitPath -Raw -Encoding UTF8 | ConvertFrom-Json
        Write-Log ('markitdown ' + $script:Payload.markitdown_version + '  converters=' + $script:Payload.converters.Count) 'OK'
    } else {
        Write-Log 'probe produced no payload' 'FAIL'
    }
}
if ($null -ne $script:Payload) {
    Save-PhaseLog -Name 'Probe' -State 'OK' -Detail ('markitdown ' + $script:Payload.markitdown_version)
} else {
    Save-PhaseLog -Name 'Probe' -State 'FAIL' -Detail 'no payload'
}

# ---------------------------------------------------------------------
# PHASE 7  self-test  (7 format checks through the real pipeline)
# ---------------------------------------------------------------------

Show-Prog -Activity 'VMD' -Status 'Phase 7 / 9  self-test' -Percent 74
Write-Log 'Phase 7  self-test' 'PHASE'

if ($script:VenvReady) {
    $stArgs = @($enginePy, '--root', $script:Dirs.root, '--selftest', '--emit', $emitPath)
    if ($AllowRemote) { $stArgs += '--allow-remote' }
    Invoke-VIAProcess -FilePath $script:VenvPython -ArgumentList $stArgs | Out-Null
    if (Test-Path -LiteralPath $emitPath) {
        $script:Payload = Get-Content -LiteralPath $emitPath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
}

$stPass = 0
$stTotal = 0
if ($null -ne $script:Payload -and $null -ne $script:Payload.selftest) {
    $stTotal = @($script:Payload.selftest).Count
    foreach ($c in $script:Payload.selftest) {
        if ($c.state -eq 'PASS') { $stPass = $stPass + 1 }
        $lvl = 'OK'
        if ($c.state -ne 'PASS') { $lvl = 'FAIL' }
        Write-Log ('selftest ' + $c.check.PadRight(6) + ' ' + $c.state + '  ' + $c.detail) $lvl
    }
}
Write-Log ('self-test ' + $stPass + '/' + $stTotal + ' PASS') 'PHASE'
Save-PhaseLog -Name 'Self-test' -State ($stPass.ToString() + '/' + $stTotal) -Detail 'live conversions'

# ---------------------------------------------------------------------
# PHASE 8  batch conversion
# ---------------------------------------------------------------------

Show-Prog -Activity 'VMD' -Status 'Phase 8 / 9  batch convert' -Percent 86
Write-Log 'Phase 8  batch convert' 'PHASE'

$targetIn = $InputPath
if ($targetIn -eq '' -and -not $SelfTestOnly) { $targetIn = $script:Dirs.inbox }
$targetOut = $OutputPath
if ($targetOut -eq '') { $targetOut = $script:Dirs.outbox }

if ($script:VenvReady -and -not $SelfTestOnly -and $targetIn -ne '') {
    Write-Log ('input    ' + $targetIn)
    Write-Log ('output   ' + $targetOut)
    $cvArgs = @($enginePy, '--root', $script:Dirs.root, '--convert', $targetIn, '--out', $targetOut, '--workers', $MaxWorkers.ToString(), '--emit', $emitPath)
    if ($AllowRemote) { $cvArgs += '--allow-remote' }
    Invoke-VIAProcess -FilePath $script:VenvPython -ArgumentList $cvArgs | Out-Null
    if (Test-Path -LiteralPath $emitPath) {
        $script:Payload = Get-Content -LiteralPath $emitPath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
}

$okCount = 0
$failCount = 0
$totalChars = 0
$unverified = 0
if ($null -ne $script:Payload -and $null -ne $script:Payload.results) {
    foreach ($r in $script:Payload.results) {
        if ($r.status -eq 'OK') {
            $okCount = $okCount + 1
            $totalChars = $totalChars + [int]$r.chars
            if ($r.evidence -eq 'UNVERIFIED_EXTRACTION') { $unverified = $unverified + 1 }
        } else {
            $failCount = $failCount + 1
        }
    }
}
Write-Log ('converted ' + $okCount + ' OK / ' + $failCount + ' FAIL') 'PHASE'
Save-PhaseLog -Name 'Batch' -State ($okCount.ToString() + ' OK / ' + $failCount.ToString() + ' FAIL') -Detail $targetIn

# ---------------------------------------------------------------------
# PHASE 9  HTML console  (Visual Lock)
# ---------------------------------------------------------------------

Show-Prog -Activity 'VMD' -Status 'Phase 9 / 9  console' -Percent 95
Write-Log 'Phase 9  HTML console' 'PHASE'

$mdVersion = 'n/a'
$convCount = 0
$pluginList = 'none'
if ($null -ne $script:Payload) {
    $mdVersion = [string]$script:Payload.markitdown_version
    $convCount = @($script:Payload.converters).Count
    if (@($script:Payload.plugins).Count -gt 0) { $pluginList = ($script:Payload.plugins -join ', ') }
}

$extraRows = ''
if ($null -ne $script:Payload -and $null -ne $script:Payload.extras) {
    foreach ($prop in $script:Payload.extras.PSObject.Properties) {
        $st = $prop.Value.state
        $cls = 'dormant'
        if ($st -eq 'ACTIVE') { $cls = 'active' }
        $miss = ''
        if (@($prop.Value.missing).Count -gt 0) { $miss = ($prop.Value.missing -join ', ') }
        $extraRows = $extraRows + '<tr><td class="mono">' + $prop.Name + '</td><td><span class="pill ' + $cls + '">' + $st + '</span></td><td class="mono dim">' + (($prop.Value.modules) -join ', ') + '</td><td class="mono dim">' + $miss + '</td></tr>'
    }
}

$gateRows = ''
if ($null -ne $script:Payload -and $null -ne $script:Payload.gated) {
    foreach ($prop in $script:Payload.gated.PSObject.Properties) {
        $cls = 'dormant'
        if ($prop.Value -eq 'ACTIVE') { $cls = 'active' }
        $gateRows = $gateRows + '<tr><td class="mono">' + $prop.Name + '</td><td><span class="pill ' + $cls + '">' + $prop.Value + '</span></td></tr>'
    }
}

$stRows = ''
if ($null -ne $script:Payload -and $null -ne $script:Payload.selftest) {
    foreach ($c in $script:Payload.selftest) {
        $cls = 'bad'
        if ($c.state -eq 'PASS') { $cls = 'good' }
        $stRows = $stRows + '<tr><td class="mono">' + $c.check + '</td><td><span class="pill ' + $cls + '">' + $c.state + '</span></td><td class="mono dim">' + $c.detail + '</td></tr>'
    }
}

$resRows = ''
if ($null -ne $script:Payload -and $null -ne $script:Payload.results) {
    foreach ($r in $script:Payload.results) {
        $cls = 'bad'
        if ($r.status -eq 'OK') { $cls = 'good' }
        $evCls = 'ev-raw'
        if ($r.evidence -eq 'UNVERIFIED_EXTRACTION') { $evCls = 'ev-unv' }
        $srcName = Split-Path -Path ([string]$r.source) -Leaf
        $detail = [string]$r.error
        if ($r.status -eq 'OK') { $detail = [string]$r.write + '  ' + [string]$r.chars + ' chars  ' + [string]$r.ms + ' ms' }
        $resRows = $resRows + '<tr><td class="mono">' + $srcName + '</td><td class="mono dim">' + [string]$r.ext + '</td><td><span class="pill ' + $cls + '">' + [string]$r.status + '</span></td><td><span class="ev ' + $evCls + '">' + [string]$r.evidence + '</span></td><td class="mono dim">' + $detail + '</td></tr>'
    }
}
if ($resRows -eq '') {
    $resRows = '<tr><td colspan="5" class="dim">Nothing converted this run. Drop files into ' + $script:Dirs.inbox + ' and run again, or pass -InputPath.</td></tr>'
}

$phaseRows = ''
foreach ($p in $script:Phases) {
    $phaseRows = $phaseRows + '<tr><td class="mono">' + $p.At + '</td><td>' + $p.Name + '</td><td class="mono">' + $p.State + '</td><td class="mono dim">' + $p.Detail + '</td></tr>'
}

$elapsed = [int]((Get-Date) - $script:StartedAt).TotalSeconds
$logText = ($script:LogLines -join "`n")
$logText = $logText.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;')
$stampText = $script:StartedAt.ToString('yyyy-MM-dd HH:mm:ss')

$html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA MarkItDown Engine — $($script:RunId)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;800&family=DM+Sans:wght@400;500&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#f5f4f0; --paper:#fff; --ink:#1e1d1a; --line:#dbd9d3;
    --blue:#4c78a8; --teal:#439a9a; --up:#c96b5a; --down:#5a9e6f;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font-family:"DM Sans",-apple-system,"Segoe UI","Microsoft JhengHei",sans-serif;
         font-size:14px; line-height:1.6; }
  .wrap { max-width:1180px; margin:0 auto; padding:32px 20px 64px; }
  .seal { width:44px; height:44px; border-radius:3px; background:var(--up);
          color:#fff; display:flex; align-items:center; justify-content:center;
          font-family:"Syne",serif; font-size:22px; font-weight:800; flex:0 0 auto; }
  header { display:flex; gap:16px; align-items:center; }
  h1 { font-family:"Syne",sans-serif; font-weight:800; font-size:22px;
       letter-spacing:-0.01em; margin:0; }
  .sub { font-family:"DM Mono",monospace; font-size:11px; letter-spacing:0.08em;
         text-transform:uppercase; color:#8a877f; margin:2px 0 0; }
  .sub2 { font-family:"DM Mono",monospace; font-size:11px; color:#8a877f; margin:2px 0 0; }
  .strip { height:3px; margin:20px 0 28px; border-radius:2px;
           background:linear-gradient(90deg,#4c78a8,#439a9a,#5a9e6f,#c9a95a,#c96b5a,#a86b9a,#6b7ea8); }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }
  .kpi { background:var(--paper); border:1px solid var(--line); border-radius:3px; padding:14px 16px; }
  .kpi .n { font-family:"Syne",sans-serif; font-size:26px; font-weight:800; line-height:1.1; }
  .kpi .l { font-family:"DM Mono",monospace; font-size:10px; letter-spacing:0.08em;
            text-transform:uppercase; color:#8a877f; margin-top:4px; }
  section { margin-top:32px; }
  h2 { font-family:"Syne",sans-serif; font-size:13px; font-weight:600; letter-spacing:0.1em;
       text-transform:uppercase; color:#6d6a63; margin:0 0 10px;
       padding-bottom:6px; border-bottom:1px solid var(--line); }
  table { width:100%; border-collapse:collapse; background:var(--paper);
          border:1px solid var(--line); border-radius:3px; overflow:hidden; }
  th { text-align:left; font-family:"DM Mono",monospace; font-size:10px;
       letter-spacing:0.08em; text-transform:uppercase; color:#8a877f;
       padding:9px 12px; border-bottom:1px solid var(--line); font-weight:500; }
  td { padding:8px 12px; border-bottom:1px solid #eeece7; vertical-align:top; }
  tr:last-child td { border-bottom:none; }
  .mono { font-family:"DM Mono",monospace; font-size:12px; }
  .dim { color:#8a877f; }
  .pill { display:inline-block; font-family:"DM Mono",monospace; font-size:10px;
          letter-spacing:0.06em; padding:2px 8px; border-radius:2px; }
  .active,.good { background:rgba(90,158,111,.14); color:#41764f; }
  .dormant { background:rgba(0,0,0,.05); color:#8a877f; }
  .bad { background:rgba(201,107,90,.16); color:#a1503f; }
  .ev { font-family:"DM Mono",monospace; font-size:10px; padding:2px 8px; border-radius:2px; }
  .ev-raw { background:rgba(76,120,168,.13); color:#3a5d84; }
  .ev-unv { background:rgba(201,169,90,.2); color:#8a6c1f; }
  .note { background:var(--paper); border:1px solid var(--line); border-left:3px solid var(--teal);
          border-radius:3px; padding:14px 16px; }
  .note b { font-weight:500; }
  pre { background:#1e1d1a; color:#d9d6cf; font-family:"DM Mono",monospace; font-size:11.5px;
        padding:16px; border-radius:3px; overflow-x:auto; max-height:340px; line-height:1.55; }
  .chips { display:flex; flex-wrap:wrap; gap:6px; }
  .chip { font-family:"DM Mono",monospace; font-size:11px; background:var(--paper);
          border:1px solid var(--line); border-radius:2px; padding:3px 9px; }
  footer { margin-top:40px; font-family:"DM Mono",monospace; font-size:11px; color:#8a877f;
           border-top:1px solid var(--line); padding-top:14px; }
  @media (max-width:640px) { .wrap { padding:20px 14px 48px; } h1 { font-size:18px; } }
</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="seal">譯</div>
  <div>
    <h1>VeritasIntelligenceAnalytics MarkItDown Engine (VMD)</h1>
    <p class="sub">Veritas Intelligence System</p>
    <p class="sub2">ENG-006 v0101 · 全格式文件 → Markdown · 能力探測 → 自檢 → 批次轉換 · 只增不減</p>
  </div>
</header>

<div class="strip"></div>

<div class="kpis">
  <div class="kpi"><div class="n">$mdVersion</div><div class="l">markitdown</div></div>
  <div class="kpi"><div class="n">$convCount</div><div class="l">converters</div></div>
  <div class="kpi"><div class="n">$stPass / $stTotal</div><div class="l">self-test pass</div></div>
  <div class="kpi"><div class="n">$okCount</div><div class="l">converted</div></div>
  <div class="kpi"><div class="n">$failCount</div><div class="l">failed</div></div>
  <div class="kpi"><div class="n">$unverified</div><div class="l">unverified extraction</div></div>
  <div class="kpi"><div class="n">${elapsed}s</div><div class="l">elapsed</div></div>
</div>

<section>
  <h2>Capability matrix — every markitdown extra</h2>
  <table>
    <thead><tr><th>Extra</th><th>State</th><th>Probe modules</th><th>Missing</th></tr></thead>
    <tbody>$extraRows</tbody>
  </table>
</section>

<section>
  <h2>Gated tiers — off until you configure them</h2>
  <table>
    <thead><tr><th>Capability</th><th>State</th></tr></thead>
    <tbody>$gateRows</tbody>
  </table>
</section>

<section>
  <h2>Registered converters</h2>
  <div class="chips">$(if ($null -ne $script:Payload -and @($script:Payload.converters).Count -gt 0) { ($script:Payload.converters | ForEach-Object { '<span class="chip">' + $_ + '</span>' }) -join '' } else { '<span class="chip dim">none detected</span>' })</div>
</section>

<section>
  <h2>Self-test — live conversions through the real pipeline</h2>
  <table>
    <thead><tr><th>Check</th><th>State</th><th>Detail</th></tr></thead>
    <tbody>$stRows</tbody>
  </table>
</section>

<section>
  <h2>Conversion results</h2>
  <table>
    <thead><tr><th>Source</th><th>Type</th><th>Status</th><th>Evidence</th><th>Detail</th></tr></thead>
    <tbody>$resRows</tbody>
  </table>
</section>

<section>
  <h2>Evidence honesty</h2>
  <div class="note">
    Every output carries a YAML header with its source hash and an evidence tag.
    <b>EXTRACTED_RAW</b> means text-only content. <b>UNVERIFIED_EXTRACTION</b> means the file
    type can carry figures and numbers were found — those values must be re-fetched from
    TWSE / TAIFEX / TDCC or the original filing before anything enters an SSOT.
    Conversion is ingestion, never verification.
  </div>
</section>

<section>
  <h2>Run phases</h2>
  <table>
    <thead><tr><th>Time</th><th>Phase</th><th>State</th><th>Detail</th></tr></thead>
    <tbody>$phaseRows</tbody>
  </table>
</section>

<section>
  <h2>Console log</h2>
  <pre>$logText</pre>
</section>

<footer>
  $($script:RunId) · started $stampText · root $($script:Dirs.root) · venv $VenvPath · plugins: $pluginList<br>
  Append-only: existing outputs are never overwritten — a changed conversion is written as __v2, __v3.
</footer>

</div>
</body>
</html>
"@

$reportPath = Join-Path $script:Dirs.reports ('VMD_Console_' + $script:StartedAt.ToString('yyyyMMdd_HHmmss') + '.html')
Write-TextFile -Path $reportPath -Content $html
$latestPath = Join-Path $script:Dirs.reports 'VMD_Console.html'
Write-TextFile -Path $latestPath -Content $html
Write-Log ('report   ' + $reportPath) 'OK'

$logPath = Join-Path $script:Dirs.logs ('vmd_' + $script:StartedAt.ToString('yyyyMMdd_HHmmss') + '.log')
Write-TextFile -Path $logPath -Content $logText

# registry line, append-only
$regPath = Join-Path $script:Dirs.data 'VMD_run_registry.jsonl'
$regLine = (@{
    run_id     = $script:RunId
    eng        = 'ENG-006'
    version    = 'v0100'
    at         = $script:StartedAt.ToString('s')
    python     = $script:BasePython
    venv       = $VenvPath
    markitdown = $mdVersion
    selftest   = ($stPass.ToString() + '/' + $stTotal.ToString())
    converted  = $okCount
    failed     = $failCount
    report     = $reportPath
} | ConvertTo-Json -Compress)
[System.IO.File]::AppendAllText($regPath, $regLine + "`n", $script:Utf8NoBom)

Show-Prog -Activity 'VMD' -Status 'done' -Percent 100
Write-Progress -Activity 'VMD' -Completed

Write-Host ''
Write-Host ('  VMD ready  ·  markitdown ' + $mdVersion + '  ·  converters ' + $convCount + '  ·  self-test ' + $stPass + '/' + $stTotal) -ForegroundColor Green
Write-Host ('  inbox   ' + $script:Dirs.inbox) -ForegroundColor DarkGray
Write-Host ('  outbox  ' + $targetOut) -ForegroundColor DarkGray
Write-Host ('  console ' + $latestPath) -ForegroundColor DarkGray
Write-Host ''

if (-not $NoOpen) {
    Start-Process -FilePath $latestPath
}
