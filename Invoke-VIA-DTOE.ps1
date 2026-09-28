# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
<#
.SYNOPSIS
  VIA DTOE 單檔全景指令。引擎內嵌，不必再放一支 .py。
.DESCRIPTION
  存成：
    C:\新增資料夾\新增資料夾\VIA DataTransforminOrganizinEngine\Invoke-VIA-DTOE.ps1
  乾跑：
    pwsh -NoProfile -File "C:\新增資料夾\新增資料夾\VIA DataTransforminOrganizinEngine\Invoke-VIA-DTOE.ps1"
  落地：
    pwsh -NoProfile -File "C:\新增資料夾\新增資料夾\VIA DataTransforminOrganizinEngine\Invoke-VIA-DTOE.ps1" -Apply
  契約：點來源 VeritasCeleritas.PS7.Template.ps1。接不上就中止，不裸奔。
  只動本 PID。原檔預設不刪。分類樹在 _dtoe_organized（硬連結，失敗才複製）。
#>
[CmdletBinding()]
param(
    [string]$Root = 'C:\新增資料夾\新增資料夾\VIA DataTransforminOrganizinEngine',
    [switch]$Apply,
    [switch]$Quarantine,
    [switch]$NoInject,
    [switch]$NoOpen
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

function Set-DtoeSmallFont {
    if ($env:OS -ne 'Windows_NT') { return }
    if (-not ('DtoeConsoleFont' -as [type])) {
        $code = @'
using System;
using System.Runtime.InteropServices;
public static class DtoeConsoleFont {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct CONSOLE_FONT_INFO_EX {
        public int cbSize;
        public int nFont;
        public short FontWidth;
        public short FontHeight;
        public int FontFamily;
        public int FontWeight;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
        public string FaceName;
    }
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr GetStdHandle(int nStdHandle);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool SetCurrentConsoleFontEx(IntPtr h, bool max, ref CONSOLE_FONT_INFO_EX info);
}
'@
        try { Add-Type -TypeDefinition $code -ErrorAction Stop } catch { return }
    }
    try {
        $info = New-Object DtoeConsoleFont+CONSOLE_FONT_INFO_EX
        $info.cbSize = [Runtime.InteropServices.Marshal]::SizeOf($info)
        $info.FontFamily = 54
        $info.FontWeight = 400
        $info.FaceName = 'Consolas'
        $info.FontHeight = -12
        $info.FontWidth = 0
        $handle = [DtoeConsoleFont]::GetStdHandle(-11)
        [void][DtoeConsoleFont]::SetCurrentConsoleFontEx($handle, $false, [ref]$info)
    } catch { }
}

function Find-DtoeFile {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Name
    )
    $direct = @(
        (Join-Path $Root $Name),
        (Join-Path $Root "VeritasCeleritas-v1.14.0\$Name"),
        (Join-Path $Root "VeritasCeleritas-v1.14.0\ps7\$Name"),
        (Join-Path $Root "VeritasCeleritas-v1.14.0\engine\$Name"),
        (Join-Path $Root "ps7\$Name"),
        (Join-Path $Root "engine\$Name")
    )
    foreach ($candidate in $direct) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    $base = Join-Path $Root 'VeritasCeleritas-v1.14.0'
    $scopes = @()
    if (Test-Path -LiteralPath $base) { $scopes += $base }
    if (Test-Path -LiteralPath $Root) { $scopes += $Root }
    foreach ($scope in $scopes) {
        $hit = Get-ChildItem -LiteralPath $scope -Filter $Name -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '\\_dtoe_' } |
            Select-Object -First 1
        if ($null -ne $hit) { return $hit.FullName }
    }
    return $null
}

function Expand-DtoeAcceleratorZip {
    param([Parameter(Mandatory)][string]$Root)
    if (-not (Test-Path -LiteralPath $Root)) { return }
    $zips = @(Get-ChildItem -LiteralPath $Root -Filter '*.zip' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match 'Celeritas' })
    foreach ($zip in $zips) {
        $dest = Join-Path $Root ([IO.Path]::GetFileNameWithoutExtension($zip.Name))
        $already = @(
            (Join-Path $dest 'ps7\VeritasCeleritas.PS7.Template.ps1'),
            (Join-Path $dest 'VeritasCeleritas.PS7.Template.ps1'),
            (Join-Path $dest 'VeritasCeleritas.PS7.ps1')
        ) | Where-Object { Test-Path -LiteralPath $_ }
        if ($already.Count -gt 0) { continue }
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        Expand-Archive -LiteralPath $zip.FullName -DestinationPath $dest -Force
    }
}

function Resolve-DtoePython {
    foreach ($name in @('python', 'python3', 'py')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($null -ne $cmd -and $cmd.Source) { return $cmd.Source }
    }
    $fallback = @(
        (Join-Path $env:USERPROFILE 'anaconda3\python.exe'),
        (Join-Path $env:USERPROFILE 'miniconda3\python.exe'),
        'C:\ProgramData\anaconda3\python.exe',
        'C:\ProgramData\miniconda3\python.exe'
    )
    foreach ($candidate in $fallback) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
    throw "根目錄不在，先確認這條路徑：$Root"
}

$template = Find-DtoeFile -Root $Root -Name 'VeritasCeleritas.PS7.Template.ps1'
if (-not $template) {
    Expand-DtoeAcceleratorZip -Root $Root
    $template = Find-DtoeFile -Root $Root -Name 'VeritasCeleritas.PS7.Template.ps1'
}

$joinedOk = $false
if ($template) {
    . $template
    if (Get-Command Test-CeleritasJoin -ErrorAction SilentlyContinue) {
        $joined = Test-CeleritasJoin
        $joinedOk = [bool]$joined.Joined
    }
}

if (-not $joinedOk) {
    $ps7 = Find-DtoeFile -Root $Root -Name 'VeritasCeleritas.PS7.ps1'
    if ($ps7) {
        . $ps7
        $joinedOk = $null -ne (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue)
    }
}

if (-not $joinedOk) {
    throw "依契約不得裸奔。在 $Root 找不到可接上的 VeritasCeleritas.PS7.Template.ps1（或同層的 VeritasCeleritas.PS7.ps1）。"
}

if (-not (Get-Command Invoke-CeleritasGenerated -ErrorAction SilentlyContinue)) {
    function Invoke-CeleritasGenerated {
        param([Parameter(Mandatory)][scriptblock]$Body)
        try {
            & $Body
        }
        finally {
            if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) {
                Restore-CeleritasPS7
            }
        }
    }
}

$EngineSource = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA DTOE Panorama v0100 — 解壓、去重、全景分類、AST 融合、加速器掛載。

安全契約（只增不減）
--------------------
* 預設乾跑：只寫報告，不搬、不刪、不改原始碼。
* ``--apply`` 在 ``_dtoe_organized/`` 用硬連結（失敗才複製）建立分類樹。
* 原始夾與 ZIP 留在原地。``--quarantine`` 才把「內容指紋相同」的重複夾移入
  ``_dtoe_quarantine/``（可還原，不刪除）。
* 大小相同但內容指紋不同 = SIZE_TWIN，不當重複。
* 加速器以惰性 hook 掛上（import 期零成本）。不改 VeritasCeleritas 本體。
* AST 只定位、不執行被掃檔案。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import html
import json
import os
import re
import shutil
import sys
import tempfile
import textwrap
import webbrowser
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

VERSION = "v0100"
HOOK_MARK = "VIA-CELERITAS-HOOK"
HOOK_VERSION = "v2"
URN = "VIA-DTOE-0100"
REPORT_NAME = "MATRIX_REPORT.html"
CARDS_NAME = "PANORAMA_CARDS.jsonl"

SKIP_DIR_NAMES = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "site-packages",
    "_dtoe_organized", "_dtoe_quarantine", "_dtoe_reports", "_dtoe_work",
    "VeritasCeleritas-v1.14.0",
}
SKIP_PREFIXES = ("_dtoe_",)

TEXT_EXT = {
    ".py", ".ps1", ".psm1", ".cmd", ".bat", ".md", ".txt", ".json", ".csv",
    ".html", ".htm", ".css", ".js", ".ts", ".tsx", ".xml", ".yml", ".yaml",
    ".toml", ".ini", ".cfg", ".sql", ".r", ".ipynb",
}

# 第一個命中分數最高者勝。前綴表優先於關鍵字。
PREFIX_CLASS = {
    "CGC": "03_VCGC_Governance",
    "VCGC": "03_VCGC_Governance",
    "SUP": "03_VCGC_Governance",
    "SSOT": "03_VCGC_Governance",
    "VRN": "04_VRN_ReportNova",
    "VDF": "05_VDF_DataForge",
    "VAP": "06_Finance_Factors",
    "VETF": "06_Finance_Factors",
    "VIS": "01_Celeritas_Acceleration",
    "PDF": "07_Document_OCR",
    "NLP": "08_NLP_Fusion",
    "VPNS": "60_PowerShell_Entry",
}

# (class_id, weight, keywords)
KEYWORD_RULES: List[Tuple[str, int, Tuple[str, ...]]] = [
    ("01_Celeritas_Acceleration", 8, ("celeritas", "superaccel", "numba", "polars", "hyperdrive", "jit")),
    ("02_Aegis_Protection", 7, ("aegis", "shield", "quarantine", "visuallock", "hardgate")),
    ("03_VCGC_Governance", 9, ("vcgc", "panorama", "governance", "registry-sync", "mdl158")),
    ("04_VRN_ReportNova", 7, ("reportnova", "matrix report", "vrn_eng", "vrn_mdl")),
    ("05_VDF_DataForge", 8, ("yfinance", "akshare", "dataforge", "fetcher", "ticker")),
    ("06_Finance_Factors", 6, ("sharpe", "altman", "三大法人", "損益", "cashflow", "macro", "etf")),
    ("07_Document_OCR", 7, ("pymupdf", "pdfminer", "ocr", "tesseract")),
    ("08_NLP_Fusion", 6, ("synonym", "同義", "token", "nlp")),
    ("12_AST_Static", 5, ("ast.parse", "ast.walk", "ast.dump")),
]

EXT_CLASS = {
    ".ps1": "60_PowerShell_Entry",
    ".psm1": "60_PowerShell_Entry",
    ".cmd": "60_PowerShell_Entry",
    ".bat": "60_PowerShell_Entry",
    ".html": "10_HTML_UI",
    ".htm": "10_HTML_UI",
    ".css": "10_HTML_UI",
    ".tsx": "10_HTML_UI",
    ".jsx": "10_HTML_UI",
    ".csv": "11_Dataset_Tables",
    ".parquet": "11_Dataset_Tables",
    ".xlsx": "11_Dataset_Tables",
    ".xls": "11_Dataset_Tables",
    ".tsv": "11_Dataset_Tables",
}

CLASS_ORDER = [
    "01_Celeritas_Acceleration",
    "02_Aegis_Protection",
    "03_VCGC_Governance",
    "04_VRN_ReportNova",
    "05_VDF_DataForge",
    "06_Finance_Factors",
    "07_Document_OCR",
    "08_NLP_Fusion",
    "10_HTML_UI",
    "11_Dataset_Tables",
    "12_AST_Static",
    "60_PowerShell_Entry",
    "90_Unclassified",
    "90_FusedEngines",
]

PREFERRED_API = [
    "_LazyModule", "_LazyAttr", "LazyModule", "accelerate", "cross_init",
    "install", "enable", "boost",
]

COPY_SUFFIX = re.compile(
    r"(?i)(?:\s*[\(（]\d+[\)）]|\s*[-_ ]?(?:copy|複製|复件))+\s*$"
)
VERSION_TAG = re.compile(r"(?i)[_\-\.]v\d{3,6}")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def norm_folder_name(name: str) -> str:
    cleaned = COPY_SUFFIX.sub("", name).strip()
    return cleaned.lower()


def stem_key(filename: str) -> str:
    base = Path(filename).name
    base = COPY_SUFFIX.sub("", base)
    base = VERSION_TAG.sub("", base)
    base = re.sub(r"(?i)_v\d+", "", base)
    base = re.sub(r"\.(py|ps1|psm1)$", "", base, flags=re.I)
    return base.lower()


def sha256_file(path: Path, limit: Optional[int] = None) -> str:
    h = hashlib.sha256()
    remaining = limit
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            if remaining is not None:
                if remaining <= 0:
                    break
                if len(chunk) > remaining:
                    chunk = chunk[:remaining]
                    remaining = 0
                else:
                    remaining -= len(chunk)
            h.update(chunk)
            if remaining == 0:
                break
    return h.hexdigest()


def file_hash(path: Path) -> str:
    """Full hash. Celeritas fast_hash is used when the accelerator is mounted."""
    try:
        import VeritasCeleritas as cel  # type: ignore
        hasher = getattr(cel, "fast_hash", None)
        if callable(hasher):
            digest = hasher(path.read_bytes())
            if isinstance(digest, str) and digest:
                return digest
    except Exception:
        pass
    return sha256_file(path)


def read_text_sample(path: Path, limit: int = 12000) -> str:
    if path.suffix.lower() not in TEXT_EXT and path.stat().st_size > 0:
        # still peek py-less text; skip obvious binary
        pass
    try:
        raw = path.read_bytes()[: limit + 1]
    except OSError:
        return ""
    if b"\x00" in raw[:1024]:
        return ""
    return raw[:limit].decode("utf-8", errors="replace")


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.startswith(SKIP_PREFIXES) or name.startswith(".")


def safe_extract_zip(zip_path: Path, dest: Path) -> Tuple[int, str]:
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for info in zf.infolist():
                name = info.filename
                if not name or name.endswith("/"):
                    continue
                target = (dest / name).resolve()
                if dest.resolve() not in target.parents and target != dest.resolve():
                    return count, "ZIP_SLIP"
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, target.open("wb") as out:
                    shutil.copyfileobj(src, out)
                count += 1
    except zipfile.BadZipFile:
        return 0, "BAD_ZIP"
    except OSError as exc:
        return count, "OS:%s" % exc
    return count, ""


def folder_fingerprint(folder: Path) -> Dict[str, Any]:
    rows: List[str] = []
    total = 0
    files = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for name in filenames:
            path = Path(dirpath) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            rel = path.relative_to(folder).as_posix()
            digest = file_hash(path)
            rows.append("%s|%s|%s" % (rel, size, digest))
            total += size
            files += 1
    rows.sort()
    blob = "\n".join(rows).encode("utf-8")
    return {
        "files": files,
        "bytes": total,
        "fingerprint": hashlib.sha256(blob).hexdigest(),
    }


def classify_file(path: Path, sample: str) -> Tuple[str, str]:
    name = path.name
    prefix = ""
    match = re.match(r"^([A-Za-z]{2,6})_", name)
    if match:
        prefix = match.group(1).upper()
        mapped = PREFIX_CLASS.get(prefix)
        if mapped:
            return mapped, "PREFIX:%s" % prefix
    ext = path.suffix.lower()
    hay = (name + "\n" + sample[:4000]).lower()
    best_id = ""
    best_score = 0
    best_hit = ""
    for class_id, weight, words in KEYWORD_RULES:
        hits = [w for w in words if w in hay]
        if not hits:
            continue
        score = weight + len(hits)
        if score > best_score:
            best_score = score
            best_id = class_id
            best_hit = hits[0]
    if best_id:
        return best_id, "KW:%s" % best_hit
    if ext in EXT_CLASS:
        return EXT_CLASS[ext], "EXT:%s" % ext
    if ext == ".py":
        return "90_Unclassified", "PY"
    if ext == ".md":
        return "03_VCGC_Governance", "EXT:.md"
    return "90_Unclassified", "NONE"


def parse_defs(path: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {"ok": False, "error": "", "defs": [], "dup": []}
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        out["error"] = "OS:%s" % exc
        return out
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        out["error"] = "SYNTAX L%s: %s" % (exc.lineno, exc.msg)
        return out
    names: List[str] = []
    defs = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
            args = 0
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = len(node.args.args)
            defs.append({
                "name": node.name,
                "kind": type(node).__name__,
                "args": args,
                "nodes": sum(1 for _ in ast.walk(node)),
                "hash": hashlib.sha256(ast.dump(node).encode("utf-8")).hexdigest()[:16],
                "source": ast.get_source_segment(src, node) or "",
                "lineno": node.lineno,
            })
    seen: Set[str] = set()
    dups = []
    for name in names:
        if name in seen:
            dups.append(name)
        seen.add(name)
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.append(ast.get_source_segment(src, node) or "")
        elif isinstance(node, ast.ImportFrom):
            imports.append(ast.get_source_segment(src, node) or "")
    out.update({
        "ok": True,
        "defs": defs,
        "dup": dups,
        "imports": [i for i in imports if i],
        "names": set(names),
    })
    return out


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def version_num(name: str) -> int:
    found = re.findall(r"(?i)v(\d{3,6})", name)
    if not found:
        return 0
    return max(int(x) for x in found)


def cluster_python(records: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Greedy clusters. Same stem, or Jaccard >= 0.5 with >= 2 shared names."""
    usable = []
    for rec in records:
        parsed = rec.get("parsed") or {}
        if parsed.get("ok") and parsed.get("names"):
            usable.append(rec)
    usable.sort(key=lambda r: (-len(r["parsed"]["names"]), -version_num(r["name"]), -r["bytes"]))
    clusters: List[List[Dict[str, Any]]] = []
    used: Set[int] = set()
    for i, rec in enumerate(usable):
        if i in used:
            continue
        group = [rec]
        used.add(i)
        names = set(rec["parsed"]["names"])
        stem = stem_key(rec["name"])
        for j in range(i + 1, len(usable)):
            if j in used:
                continue
            other = usable[j]
            onames = set(other["parsed"]["names"])
            same_stem = stem_key(other["name"]) == stem and stem != ""
            shared = len(names & onames)
            if same_stem or (jaccard(names, onames) >= 0.5 and shared >= 2):
                group.append(other)
                used.add(j)
                names |= onames
        if len(group) >= 2:
            clusters.append(group)
    return clusters


def build_fused(group: List[Dict[str, Any]], class_id: str) -> str:
    ranked = sorted(
        group,
        key=lambda r: (
            -sum(d["nodes"] for d in r["parsed"]["defs"]),
            -version_num(r["name"]),
            -r["bytes"],
        ),
    )
    canon = ranked[0]
    taken: Dict[str, str] = {}
    blocks: List[str] = []
    sources = []
    for rec in ranked:
        sources.append("%s | %s" % (rec["rel"], rec["sha"][:12]))
        for item in rec["parsed"]["defs"]:
            name = item["name"]
            if name.startswith("_"):
                # private helpers stay with their owner unless canonical
                if rec is not canon:
                    continue
            body_hash = item["hash"]
            if name not in taken:
                taken[name] = body_hash
                origin = "" if rec is canon else "  # from %s" % rec["name"]
                blocks.append(item["source"].rstrip() + origin)
            elif taken[name] != body_hash:
                alias = "%s__from_%s" % (name, re.sub(r"[^0-9A-Za-z_]", "_", stem_key(rec["name"]))[:40])
                if alias in taken:
                    continue
                taken[alias] = body_hash
                renamed = re.sub(
                    r"^(async\s+def|def|class)\s+%s\b" % re.escape(name),
                    lambda m: "%s %s" % (m.group(1), alias),
                    item["source"].rstrip(),
                    count=1,
                )
                blocks.append(renamed + "  # clash-kept; canonical remains %s" % name)
    header = textwrap.dedent(
        '''\
        # -*- coding: utf-8 -*-
        """Fused engine {cls} — DTOE {ver}

        Canonical: {canon}
        Members stay on disk. This file is the stronger single facade:
        richest body wins a name; divergent bodies are kept under an alias.
        """
        from __future__ import annotations

        FUSED_CLASS = {cls!r}
        FUSED_SOURCES = (
        {sources}
        )
        '''
    ).format(
        cls=class_id,
        ver=VERSION,
        canon=canon["rel"],
        sources="\n".join("    %r," % s for s in sources),
    )
    import_block = "\n".join(canon["parsed"].get("imports") or [])
    parts = [header]
    if import_block.strip():
        parts.append(import_block)
    parts.append("\n\n".join(blocks))
    parts.append("\n")
    return "\n".join(parts)


def probe_celeritas(path: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "path": str(path), "ok": False, "exports": [], "chosen": [], "error": "",
    }
    if not path.is_file():
        result["error"] = "MISSING"
        return result
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        result["error"] = "SYNTAX L%s" % exc.lineno
        return result
    except OSError as exc:
        result["error"] = "OS:%s" % exc
        return result
    exports = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            exports.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    exports.append(target.id)
    available = set(exports)
    chosen = [name for name in PREFERRED_API if name in available]
    result.update({"ok": bool(chosen), "exports": sorted(available), "chosen": chosen})
    if not chosen:
        result["error"] = "NO_API"
    return result


def build_hook(supportive: Path, chosen: Sequence[str]) -> str:
    literal = str(supportive.resolve()).replace("\\", "\\\\")
    sample = ", ".join(list(chosen)[:4]) or "accelerate"
    return (
        "# --- {mark} {ver} ({urn} 自動插入；移除本區塊即完全還原) ---\n"
        "# 惰性綁定：import 期零成本，首次取用 _VIA.{sample} 才載入 VeritasCeleritas。\n"
        "class _ViaCeleritas:  # noqa: E402\n"
        "    _mod = None\n"
        "    _failed = False\n"
        "    @classmethod\n"
        "    def _load(cls):\n"
        "        if cls._mod is None and not cls._failed:\n"
        "            import os as _o, sys as _s\n"
        "            _p = _o.environ.get('VIA_SUPPORTIVE') or r'{literal}'\n"
        "            if _p and _p not in _s.path:\n"
        "                _s.path.insert(0, _p)\n"
        "            try:\n"
        "                import VeritasCeleritas as _c\n"
        "                cls._mod = _c\n"
        "            except Exception:\n"
        "                cls._failed = True\n"
        "        return cls._mod\n"
        "    def __getattr__(self, name):\n"
        "        _m = type(self)._load()\n"
        "        if _m is None:\n"
        "            raise AttributeError('VeritasCeleritas 不可用，無法取用 %s' % name)\n"
        "        return getattr(_m, name)\n"
        "_VIA = _ViaCeleritas()\n"
        "# --- end {mark} ---\n"
    ).format(mark=HOOK_MARK, ver=HOOK_VERSION, urn=URN, literal=literal, sample=sample)


_CODING = re.compile(r"coding[:=]\s*([-\w.]+)")
_SHEBANG = re.compile(r"^#!")


def insertion_line(text: str, tree: ast.Module) -> int:
    line = 1
    for raw in text.splitlines()[:2]:
        if _SHEBANG.match(raw) or _CODING.search(raw):
            line += 1
        else:
            break
    if tree.body:
        first = tree.body[0]
        line = max(line, first.lineno)
        if ast.get_docstring(tree) is not None:
            line = (getattr(first, "end_lineno", first.lineno) or first.lineno) + 1
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            line = max(line, (getattr(node, "end_lineno", node.lineno) or node.lineno) + 1)
    return line


def inject_hook(path: Path, hook: str, backup_dir: Path) -> Tuple[bool, str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return False, "OS:%s" % exc
    if HOOK_MARK in text:
        return True, "ALREADY"
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        return False, "SYNTAX L%s" % exc.lineno
    line = insertion_line(text, tree)
    rows = text.splitlines(keepends=True)
    # line is 1-based next line index to insert before
    idx = max(0, min(len(rows), line - 1))
    # if the chosen line is in the middle of a future import already consumed, idx is after it
    block = hook
    if not block.endswith("\n"):
        block += "\n"
    rows.insert(idx, block)
    new_text = "".join(rows)
    try:
        ast.parse(new_text, filename=str(path))
        compile(new_text, str(path), "exec")
    except SyntaxError as exc:
        return False, "HOOK_SYNTAX L%s" % exc.lineno
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / (path.name + ".bak")
    # unique backup
    n = 1
    while backup.exists():
        n += 1
        backup = backup_dir / ("%s.%s.bak" % (path.name, n))
    backup.write_text(text, encoding="utf-8")
    path.write_text(new_text, encoding="utf-8", newline="\n")
    return True, "INJECTED"


def place_file(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "EXISTS"
    try:
        os.link(src, dst)
        return "LINK"
    except OSError:
        shutil.copy2(src, dst)
        return "COPY"


def iter_dirs(root: Path) -> List[Path]:
    found = []
    for dirpath, dirnames, _filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        if Path(dirpath) == root:
            continue
        # only top-level-ish? User said 每個資料夾. Walk all, but fingerprint
        # every directory. Nested identical copies are handled.
        found.append(Path(dirpath))
    return found


def collect_top_folders(root: Path) -> List[Path]:
    folders = []
    try:
        for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if child.is_dir() and not should_skip_dir(child.name):
                folders.append(child)
    except OSError:
        return []
    return folders


def discover_zips(root: Path) -> List[Path]:
    zips = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for name in filenames:
            if name.lower().endswith(".zip"):
                zips.append(Path(dirpath) / name)
    return zips


def extract_all(root: Path, work: Path) -> List[Dict[str, Any]]:
    """Extract every zip, including zips that appear after extraction. Max 4 waves."""
    report = []
    seen: Set[str] = set()
    base = work / "extracted"
    for _wave in range(4):
        fresh = []
        for zp in discover_zips(root) + discover_zips(base if base.exists() else work):
            key = str(zp.resolve())
            if key in seen:
                continue
            # do not re-walk organized
            if any(part.startswith("_dtoe_") or part == "VeritasCeleritas-v1.14.0" for part in zp.parts):
                continue
            seen.add(key)
            fresh.append(zp)
        if not fresh:
            break
        for zp in fresh:
            rel = zp.name + "-" + sha256_file(zp, limit=65536)[:10]
            dest = base / rel
            if dest.exists() and any(dest.iterdir()):
                report.append({"zip": str(zp), "dest": str(dest), "files": 0, "error": "SKIP_EXISTS"})
                continue
            count, err = safe_extract_zip(zp, dest)
            report.append({"zip": str(zp), "dest": str(dest), "files": count, "error": err})
    return report


def walk_files(folder: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for name in filenames:
            if name.lower().endswith(".zip"):
                continue
            yield Path(dirpath) / name


def render_html(ctx: Dict[str, Any]) -> str:
    def cell(value: Any) -> str:
        return html.escape("" if value is None else str(value))

    def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
        th = "".join("<th>%s</th>" % cell(h) for h in headers)
        body = []
        for row in rows:
            body.append("<tr>" + "".join("<td>%s</td>" % cell(c) for c in row) + "</tr>")
        return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (th, "".join(body))

    kpis = ctx["kpis"]
    kpi_html = "".join(
        "<div class='kpi'><span>%s</span><b>%s</b></div>" % (cell(k), cell(v))
        for k, v in kpis
    )
    return """<!doctype html>
<html lang="zh-Hant">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DTOE MATRIX REPORT</title>
<style>
  :root {{
    --bg:#090a0c; --fg:#e8eaed; --muted:#8b919a; --line:#2a2e33;
    --accent:#9aa8b3; --ok:#7d9a86; --warn:#b9a27a; --bad:#a56b6b; --card:#121418;
  }}
  html,body {{ margin:0; background:var(--bg); color:var(--fg);
    font: 11px/1.35 "IBM Plex Sans","Noto Sans TC",sans-serif; }}
  main {{ padding: 14px 16px 48px; }}
  h1 {{ font-weight: 500; letter-spacing: -0.03em; font-size: 18px; margin: 4px 0; }}
  .mono {{ font-family: "IBM Plex Mono", ui-monospace, monospace; }}
  .eyebrow {{ color: var(--accent); letter-spacing: .18em; font-size: 10px; text-transform: uppercase; }}
  .kpis {{ display:grid; grid-template-columns: repeat(auto-fit,minmax(108px,1fr)); gap:6px; margin: 10px 0; }}
  .kpi {{ border:1px solid var(--line); background:var(--card); padding:8px; }}
  .kpi span {{ display:block; color:var(--muted); letter-spacing:.14em; font-size:9px; text-transform:uppercase; }}
  .kpi b {{ font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 14px; font-weight: 500; }}
  table {{ width:100%; border-collapse: collapse; margin: 8px 0 16px; }}
  th,td {{ border-bottom:1px solid var(--line); text-align:left; padding: 3px 6px; vertical-align: top; }}
  th {{ color: var(--muted); font-weight: 500; letter-spacing: .08em; font-size: 9px; text-transform: uppercase; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .ok {{ color: var(--ok); }} .warn {{ color: var(--warn); }} .bad {{ color: var(--bad); }}
  h2 {{ font-size: 12px; font-weight: 500; margin: 16px 0 4px; }}
  p.note {{ color: var(--muted); max-width: 980px; }}
</style>
<main>
  <p class="eyebrow mono">VIA · DTOE · PANORAMA · RICH MATRIX</p>
  <h1>分類矩陣 <span class="mono">{version}</span></h1>
  <p class="note">{mode} · {when} · root <span class="mono">{root}</span></p>
  <p class="note">{rule}</p>
  <div class="kpis">{kpis}</div>
  <h2>類別</h2>
  {classes}
  <h2>資料夾去重</h2>
  {folders}
  <h2>大小相同但內容不同（保留）</h2>
  {twins}
  <h2>AST 融合</h2>
  {fused}
  <h2>加速器</h2>
  {accel}
  <h2>解壓</h2>
  {zips}
</main>
</html>
""".format(
        version=VERSION,
        mode=cell(ctx["mode"]),
        when=cell(ctx["when"]),
        root=cell(ctx["root"]),
        rule=cell(ctx["rule"]),
        kpis=kpi_html,
        classes=table(
            ["CLASS", "FILES", "UNIQUE", "DUP_HASH", "CLUSTERS", "FUSED", "AST_ERR"],
            ctx["class_rows"],
        ),
        folders=table(
            ["KEEPER", "DROPPED", "BYTES", "FILES", "FINGERPRINT"],
            ctx["dup_rows"] or [["—", "0", "", "", ""]],
        ),
        twins=table(
            ["A", "B", "BYTES", "NOTE"],
            ctx["twin_rows"] or [["—", "—", "", "無"]],
        ),
        fused=table(
            ["ENGINE", "CLASS", "MEMBERS", "DEFS", "STATUS"],
            ctx["fuse_rows"] or [["—", "—", "0", "0", "無相似叢集"]],
        ),
        accel=table(
            ["ITEM", "VALUE"],
            ctx["accel_rows"],
        ),
        zips=table(
            ["ZIP", "FILES", "ERROR"],
            ctx["zip_rows"] or [["—", "0", "無 ZIP"]],
        ),
    )


def render_rich(ctx: Dict[str, Any]) -> str:
    """Live matrix. Uses rich when installed; otherwise a compact plain matrix."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
    except Exception:
        return render_plain(ctx)
    console = Console(record=True, force_terminal=True, soft_wrap=False)
    width = max(72, min(shutil.get_terminal_size(fallback=(120, 40)).columns, 160))
    console.width = width
    table = Table(
        title="DTOE MATRIX  %s  %s" % (VERSION, ctx["mode"]),
        show_lines=False,
        pad_edge=False,
        padding=(0, 1),
        expand=True,
        header_style="bold",
    )
    for header in ("CLASS", "FILES", "UNIQUE", "DUP", "CLUSTERS", "FUSED", "AST"):
        table.add_column(header, overflow="ellipsis", no_wrap=True)
    for row in ctx["class_rows"]:
        table.add_row(*[str(c) for c in row])
    console.print(Panel(table, subtitle="font compact · auto width %s" % width, padding=(0, 0)))
    fuse = Table(title="FUSED", pad_edge=False, padding=(0, 1), expand=True)
    for header in ("ENGINE", "CLASS", "MEMBERS", "DEFS", "STATUS"):
        fuse.add_column(header, overflow="ellipsis", no_wrap=True)
    for row in ctx["fuse_rows"] or [["—", "—", "0", "0", "none"]]:
        fuse.add_row(*[str(c) for c in row])
    console.print(fuse)
    accel = Table(title="CELERITAS", pad_edge=False, padding=(0, 1), expand=True)
    accel.add_column("ITEM", no_wrap=True)
    accel.add_column("VALUE", overflow="ellipsis")
    for row in ctx["accel_rows"]:
        accel.add_row(str(row[0]), str(row[1]))
    console.print(accel)
    text = console.export_text(clear=False)
    return text


def render_plain(ctx: Dict[str, Any]) -> str:
    lines = [
        "DTOE MATRIX %s  %s  (rich 未安裝，純文字矩陣；HTML 仍會跳出)" % (VERSION, ctx["mode"]),
    ]
    header = "{:<28} {:>6} {:>6} {:>6} {:>8} {:>6} {:>6}".format(
        "CLASS", "FILES", "UNIQUE", "DUP", "CLUSTERS", "FUSED", "AST"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for row in ctx["class_rows"]:
        lines.append("{:<28} {:>6} {:>6} {:>6} {:>8} {:>6} {:>6}".format(
            str(row[0])[:28], row[1], row[2], row[3], row[4], row[5], row[6]
        ))
    lines.append("FUSED")
    for row in ctx["fuse_rows"]:
        lines.append("  %s  members=%s defs=%s %s" % (row[0], row[2], row[3], row[4]))
    for row in ctx["accel_rows"]:
        lines.append("ACCEL  %s = %s" % (row[0], row[1]))
    return "\n".join(lines)


def open_report(path: Path) -> str:
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
            return "STARTFILE"
        webbrowser.open(path.as_uri())
        return "BROWSER"
    except Exception as exc:
        return "NO_OPEN:%s" % exc


def run(root: Path, celeritas: Path, apply: bool, quarantine: bool, inject: bool, open_ui: bool) -> Dict[str, Any]:
    root = root.resolve()
    reports = root / "_dtoe_reports"
    reports.mkdir(parents=True, exist_ok=True)
    work = root / "_dtoe_work"
    work.mkdir(parents=True, exist_ok=True)
    organized = root / "_dtoe_organized"
    probe = probe_celeritas(celeritas)
    supportive = celeritas.parent if celeritas.is_file() else celeritas

    zip_rows_raw = extract_all(root, work) if apply or True else []
    # Extraction writes files. Dry-run still extracts into _dtoe_work because
    # classification of ZIP contents is the first wave the operator asked for.
    # Originals are not removed. Re-runs skip existing dest folders.

    folders = collect_top_folders(root)
    # also consider extracted top folders as sources, not as user folders to quarantine
    fingerprints = {}
    for folder in folders:
        fingerprints[folder] = folder_fingerprint(folder)

    by_fp: Dict[str, List[Path]] = defaultdict(list)
    by_size: Dict[int, List[Path]] = defaultdict(list)
    for folder, info in fingerprints.items():
        if info["files"] == 0:
            continue
        by_fp[info["fingerprint"]].append(folder)
        by_size[info["bytes"]].append(folder)

    dup_groups = []
    dropped: Set[Path] = set()
    for fp, group in by_fp.items():
        if len(group) < 2:
            continue
        ranked = sorted(group, key=lambda p: (bool(COPY_SUFFIX.search(p.name)), len(p.name), p.name.lower()))
        keeper = ranked[0]
        extras = ranked[1:]
        dropped.update(extras)
        info = fingerprints[keeper]
        dup_groups.append({
            "keeper": keeper,
            "dropped": extras,
            "bytes": info["bytes"],
            "files": info["files"],
            "fingerprint": fp[:16],
        })

    twin_rows = []
    seen_pairs: Set[Tuple[str, str]] = set()
    for size, group in by_size.items():
        if len(group) < 2 or size == 0:
            continue
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if fingerprints[a]["fingerprint"] == fingerprints[b]["fingerprint"]:
                    continue
                key = tuple(sorted((str(a), str(b))))
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                twin_rows.append([
                    a.name, b.name, size, "SIZE_TWIN 內容指紋不同，保留兩邊",
                ])

    if quarantine and apply:
        qroot = root / "_dtoe_quarantine"
        for group in dup_groups:
            for extra in group["dropped"]:
                dest = qroot / extra.name
                n = 1
                while dest.exists():
                    n += 1
                    dest = qroot / ("%s__%s" % (extra.name, n))
                shutil.move(str(extra), str(dest))

    sources: List[Tuple[Path, Path]] = []  # file, rel base
    for folder in folders:
        if folder in dropped:
            continue
        for path in walk_files(folder):
            sources.append((path, folder.parent))
    # loose files directly under root
    try:
        for child in root.iterdir():
            if child.is_file() and not child.name.lower().endswith(".zip") and not child.name.startswith("_dtoe"):
                sources.append((child, root))
    except OSError:
        pass
    extracted = work / "extracted"
    if extracted.exists():
        for path in walk_files(extracted):
            sources.append((path, extracted))

    # content dedupe across the kept set
    seen_hash: Dict[str, Path] = {}
    unique_files: List[Dict[str, Any]] = []
    dup_file_count = 0
    for path, base in sources:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        digest = file_hash(path)
        if digest in seen_hash:
            dup_file_count += 1
            continue
        seen_hash[digest] = path
        try:
            rel = path.relative_to(base).as_posix()
        except ValueError:
            rel = path.name
        sample = read_text_sample(path)
        class_id, reason = classify_file(path, sample)
        parsed = parse_defs(path) if path.suffix.lower() == ".py" else None
        unique_files.append({
            "path": path,
            "rel": rel,
            "name": path.name,
            "bytes": size,
            "sha": digest,
            "class_id": class_id,
            "reason": reason,
            "sample_tokens": max(1, len(sample) // 2) if sample else 0,
            "parsed": parsed,
        })

    by_class: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for rec in unique_files:
        by_class[rec["class_id"]].append(rec)

    fuse_rows = []
    fused_payloads: List[Tuple[str, str, str]] = []  # class, filename, text
    cluster_count: Dict[str, int] = defaultdict(int)
    for class_id, records in by_class.items():
        py_recs = [r for r in records if r["path"].suffix.lower() == ".py" and r.get("parsed")]
        groups = cluster_python(py_recs)
        cluster_count[class_id] = len(groups)
        for index, group in enumerate(groups, start=1):
            text = build_fused(group, class_id)
            fname = "FUSED_%s_%02d.py" % (class_id, index)
            defs = text.count("\ndef ") + text.count("\nclass ") + text.count("\nasync def ")
            status = "PLANNED" if not apply else "WRITTEN"
            fuse_rows.append([fname, class_id, len(group), defs, status])
            fused_payloads.append((class_id, fname, text))

    placed = 0
    injected = 0
    inject_fail = 0
    inject_skip = 0
    hook = ""
    if probe.get("chosen"):
        hook = build_hook(supportive, probe["chosen"])
    if apply:
        for rec in unique_files:
            dest = organized / rec["class_id"] / rec["rel"]
            place_file(rec["path"], dest)
            placed += 1
        fuse_dir = organized / "90_FusedEngines"
        for _class_id, fname, text in fused_payloads:
            target = fuse_dir / fname
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
        if inject and hook:
            backup_dir = work / "hook_backups"
            for py in organized.rglob("*.py"):
                if py.name == "VeritasCeleritas.py":
                    inject_skip += 1
                    continue
                ok, status = inject_hook(py, hook, backup_dir)
                if status == "INJECTED":
                    injected += 1
                elif status == "ALREADY":
                    inject_skip += 1
                elif not ok:
                    inject_fail += 1

    class_rows = []
    ast_err_total = 0
    for class_id in CLASS_ORDER:
        records = by_class.get(class_id, [])
        if class_id == "90_FusedEngines":
            continue
        ast_err = 0
        for rec in records:
            parsed = rec.get("parsed")
            if parsed and (parsed.get("error") or parsed.get("dup")):
                ast_err += 1
        ast_err_total += ast_err
        fused_n = sum(1 for row in fuse_rows if row[1] == class_id)
        if not records and fused_n == 0:
            continue
        class_rows.append([
            class_id,
            len(records),
            len(records),
            0,
            cluster_count.get(class_id, 0),
            fused_n,
            ast_err,
        ])
    # file-level dup is global; show on a summary kpi not per class
    if not class_rows:
        class_rows.append(["90_Unclassified", 0, 0, 0, 0, 0, 0])

    cards_path = reports / CARDS_NAME
    with cards_path.open("w", encoding="utf-8") as handle:
        for rec in unique_files:
            parsed = rec.get("parsed") or {}
            card = {
                "rel": rec["rel"],
                "class": rec["class_id"],
                "why": rec["reason"],
                "bytes": rec["bytes"],
                "sha": rec["sha"][:16],
                "defs": [d["name"] for d in parsed.get("defs", [])][:40],
                "ast": parsed.get("error") or (",".join(parsed.get("dup") or []) and "DUPDEF") or "",
            }
            if parsed.get("dup"):
                card["ast"] = "DUPDEF:" + ",".join(parsed["dup"][:8])
            handle.write(json.dumps(card, ensure_ascii=False) + "\n")

    mode = "APPLY" if apply else "DRY-RUN"
    if quarantine and apply:
        mode += "+QUARANTINE"
    ctx = {
        "mode": mode,
        "when": utc_now(),
        "root": str(root),
        "rule": "指紋相同才去重。(1)(2) 只是名字。大小相同但指紋不同 = SIZE_TWIN，保留。分類樹只在 --apply 建立。加速器為惰性 hook，插在 from __future__ 之後。",
        "kpis": [
            ("MODE", mode),
            ("CLASSES", len([r for r in class_rows if r[1] or r[5]])),
            ("UNIQUE", len(unique_files)),
            ("FILE_DUP", dup_file_count),
            ("DIR_DUP", sum(len(g["dropped"]) for g in dup_groups)),
            ("TWINS", len(twin_rows)),
            ("FUSED", len(fuse_rows)),
            ("HOOK", injected if apply else "PLAN"),
            ("AST_ERR", ast_err_total),
            ("ZIPS", len(zip_rows_raw)),
        ],
        "class_rows": class_rows,
        "dup_rows": [
            [g["keeper"].name, len(g["dropped"]), g["bytes"], g["files"], g["fingerprint"]]
            for g in dup_groups
        ],
        "twin_rows": twin_rows,
        "fuse_rows": fuse_rows,
        "accel_rows": [
            ("CELERITAS", str(celeritas)),
            ("PROBE", "OK" if probe.get("ok") else probe.get("error") or "NO"),
            ("CHOSEN", ", ".join(probe.get("chosen") or []) or "—"),
            ("EXPORTS", len(probe.get("exports") or [])),
            ("INJECT", injected if apply else ("PLAN" if hook else "BLOCKED")),
            ("INJECT_FAIL", inject_fail),
            ("ALREADY", inject_skip),
            ("SUPPORTIVE", str(supportive)),
            ("CARDS", str(cards_path)),
        ],
        "zip_rows": [
            [Path(z["zip"]).name, z["files"], z["error"] or "OK"]
            for z in zip_rows_raw
        ],
    }
    html_path = reports / REPORT_NAME
    html_path.write_text(render_html(ctx), encoding="utf-8")
    matrix_text = render_rich(ctx)
    (reports / "MATRIX_REPORT.txt").write_text(matrix_text, encoding="utf-8")
    ledger = {
        "version": VERSION,
        "mode": mode,
        "root": str(root),
        "unique": len(unique_files),
        "file_dups": dup_file_count,
        "dir_dups": ctx["dup_rows"],
        "twins": twin_rows,
        "fused": fuse_rows,
        "placed": placed,
        "injected": injected,
        "report": str(html_path),
    }
    (reports / "LEDGER.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    opened = open_report(html_path) if open_ui else "SKIP"
    print(matrix_text)
    print("DTOE_REPORT=%s" % html_path)
    print("DTOE_OPEN=%s" % opened)
    print("DTOE_CARDS=%s" % cards_path)
    ctx["report"] = str(html_path)
    ctx["opened"] = opened
    return ctx


def _selftest() -> int:
    fails: List[str] = []

    def chk(name: str, cond: bool) -> None:
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory(prefix="dtoe_") as tmp:
        root = Path(tmp)
        engine = root / "VeritasCeleritas-v1.14.0" / "engine"
        engine.mkdir(parents=True)
        (engine / "VeritasCeleritas.py").write_text(
            "class _LazyModule:\n    pass\n\ndef accelerate(fn):\n    return fn\n",
            encoding="utf-8",
        )
        alpha = root / "alpha"
        alpha.mkdir()
        src_a = "def scan(x):\n    return x\n\ndef read(y):\n    return y\n\ndef slice(z):\n    return z\n"
        (alpha / "CGC_MDL158_Panorama_v0100.py").write_text(src_a, encoding="utf-8")
        (alpha / "notes.md").write_text("# panorama governance\n", encoding="utf-8")
        alpha1 = root / "alpha (1)"
        shutil.copytree(alpha, alpha1)
        beta = root / "beta"
        beta.mkdir()
        (beta / "CGC_MDL158_Panorama_v0101.py").write_text(
            src_a + "\ndef digest(log):\n    return log\n",
            encoding="utf-8",
        )
        twin_a = root / "twin_a"
        twin_b = root / "twin_b"
        twin_a.mkdir(); twin_b.mkdir()
        (twin_a / "only.txt").write_text("A" * 100, encoding="utf-8")
        (twin_b / "only.txt").write_text("B" * 100, encoding="utf-8")
        pack = root / "incoming.zip"
        with zipfile.ZipFile(pack, "w") as zf:
            zf.writestr("VDF_MDL001_fetcher_v0100.py", "def fetch_ticker(symbol):\n    return symbol\n")
        # syntax error sample
        bad = root / "broken"
        bad.mkdir()
        (bad / "VRN_ENG001_bad_v0100.py").write_text("def oops(:\n    pass\n", encoding="utf-8")

        ctx = run(
            root=root,
            celeritas=engine / "VeritasCeleritas.py",
            apply=True,
            quarantine=False,
            inject=True,
            open_ui=False,
        )
        organized = root / "_dtoe_organized"
        gov = list((organized / "03_VCGC_Governance").rglob("*.py")) if (organized / "03_VCGC_Governance").exists() else []
        fused = list((organized / "90_FusedEngines").glob("*.py"))
        vdf = list((organized / "05_VDF_DataForge").rglob("*.py")) if (organized / "05_VDF_DataForge").exists() else []
        chk("zip classified into VDF", len(vdf) == 1)
        chk("dir dup dropped alpha (1)", not any("alpha (1)" in p.as_posix() for p in organized.rglob("*") if "alpha (1)" in str(p)))
        chk("keeper alpha present", any(p.name.startswith("CGC_MDL158_Panorama_v0100") for p in gov))
        chk("size twin both kept", any("twin_a" in p.as_posix() for p in organized.rglob("only.txt")) and any("twin_b" in p.as_posix() for p in organized.rglob("only.txt")))
        chk("fused engine written", len(fused) >= 1)
        compiled_ok = True
        hooked = []
        for py in organized.rglob("*.py"):
            source = py.read_text(encoding="utf-8")
            if "def oops" in source:
                chk("syntax error not hooked", HOOK_MARK not in source)
                continue
            hooked.append(source)
            try:
                compile(source, str(py), "exec")
            except SyntaxError:
                compiled_ok = False
        chk("injected sources compile", compiled_ok)
        chk(
            "hook present and after future",
            bool(hooked) and all(
                HOOK_MARK in src and (
                    src.find("from __future__") < 0 or src.find("from __future__") < src.find(HOOK_MARK)
                )
                for src in hooked
            ),
        )
        chk("report exists", Path(ctx["report"]).is_file())
        chk("cards exist", (root / "_dtoe_reports" / CARDS_NAME).is_file())
        chk("probe saw _LazyModule", "_LazyModule" in (ctx["accel_rows"][2][1]))
        # originals remain
        chk("original alpha (1) still there", alpha1.is_dir())
        html_text = Path(ctx["report"]).read_text(encoding="utf-8")
        chk("html is small-font matrix", "font: 11px" in html_text and "MATRIX" in html_text)
        chk("bad py recorded", any(r[0] == "04_VRN_ReportNova" and int(r[6]) >= 1 for r in ctx["class_rows"]))

    if fails:
        print("SELFTEST FAIL %s" % ", ".join(fails))
        return 1
    print("SELFTEST OK")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="VIA DTOE panorama classify / dedupe / fuse")
    parser.add_argument("--root", default="")
    parser.add_argument("--celeritas", default="")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--quarantine", action="store_true")
    parser.add_argument("--no-inject", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.root:
        parser.error("--root is required")
    root = Path(args.root)
    if not root.is_dir():
        print("DTOE_ERROR=ROOT_MISSING %s" % root)
        return 2
    celeritas = Path(args.celeritas) if args.celeritas else (
        root / "VeritasCeleritas-v1.14.0" / "engine" / "VeritasCeleritas.py"
    )
    run(
        root=root,
        celeritas=celeritas,
        apply=args.apply,
        quarantine=args.quarantine,
        inject=not args.no_inject,
        open_ui=not args.no_open,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

'@

$work = Join-Path $Root '_dtoe_work'
New-Item -ItemType Directory -Force -Path $work | Out-Null
$Engine = Join-Path $work 'VIA_DTOE_Panorama_v0100.py'
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($Engine, ($EngineSource -replace "`r`n", "`n"), $utf8)

$Python = Resolve-DtoePython
if (-not $Python) { throw "找不到 Python。矩陣報告與 AST 融合都走 python。" }

$CeleritasPy = Find-DtoeFile -Root $Root -Name 'VeritasCeleritas.py'
if (-not $CeleritasPy) {
    $CeleritasPy = Join-Path $Root 'VeritasCeleritas-v1.14.0\engine\VeritasCeleritas.py'
}

Invoke-CeleritasGenerated -Body {
    Set-DtoeSmallFont
    $argList = @(
        $Engine,
        '--root', $Root,
        '--celeritas', $CeleritasPy
    )
    if ($Apply) { $argList += '--apply' }
    if ($Quarantine) { $argList += '--quarantine' }
    if ($NoInject) { $argList += '--no-inject' }
    if ($NoOpen) { $argList += '--no-open' }
    if ([System.IO.Path]::GetFileName($Python) -eq 'py.exe') {
        & $Python -3 @argList
    } else {
        & $Python @argList
    }
    if ($LASTEXITCODE -ne 0) { throw "DTOE exit $LASTEXITCODE" }
}
