#requires -Version 7
# ============================================================================================
#  Invoke-VIA-AKShareSuperEngine.ps1   v0200   VAKE = Veritas AKShare Knowledge & Extraction Engine
#  One-click: venv -> VDF_AkshareFetcher.py (single-file engine) -> AST+Docs scan -> local console (tree picker / start-date -> latest
#  incremental / DuckDB console) -> daily Task Scheduler entry -> HTML install report.
#  LL: no aliases, no Read-Host, no exit/Stop-Process, ProcessStartInfo, UTF8 no-BOM, append-only.
#  Paste-safe (LL#25): whole body is one &{ } block. Preferred: pwsh -ExecutionPolicy Bypass -File <this>
# ============================================================================================
&{
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$T0 = Get-Date
$Stamp = $T0.ToString('yyyyMMdd_HHmmss')

# ---------------------------------------------------------------- settings (edit here, no param())
$VakeRoot   = 'C:\VIA\VAKE'
$EnvRoot    = 'C:\Users\tonyk\envs'
$VenvName   = 'via_akshare'
$VenvDir    = Join-Path $EnvRoot $VenvName
$Port       = 8765
$TaskName   = 'VIA_VAKE_Daily_Incremental'
$TaskTime   = '18:40'
$RepoBin    = 'C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics\bin'
$VdfModules = 'C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VDF'
$Packages   = @('akshare','polars','duckdb','pyarrow','requests','pandas')
$ImportProbe = 'import akshare, polars, duckdb, pyarrow, requests, pandas; print("IMPORT_OK", akshare.__version__, polars.__version__, duckdb.__version__)'

$EngineDir  = Join-Path $VakeRoot 'engine'
$LogsDir    = Join-Path $VakeRoot 'logs'
$RunsDir    = Join-Path $VakeRoot 'runs'
$BinDir     = Join-Path $VakeRoot 'bin'
$ArchiveDir = Join-Path $VakeRoot '_archive'
$RunDir     = Join-Path $RunsDir ("INSTALL_" + $Stamp)
$LogFile    = Join-Path $LogsDir ("install_" + $Stamp + ".log")
$Phases     = [System.Collections.Generic.List[object]]::new()

foreach ($d in @($VakeRoot,$EngineDir,$LogsDir,$RunsDir,$BinDir,$ArchiveDir,$RunDir,(Join-Path $VakeRoot 'knowledge'),(Join-Path $VakeRoot 'store'),(Join-Path $VakeRoot 'db'),(Join-Path $VakeRoot 'selections'))) {
    if (-not (Test-Path -LiteralPath $d)) { [void](New-Item -ItemType Directory -Path $d -Force) }
}

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $line = ('[{0}] [{1}] {2}' -f (Get-Date).ToString('HH:mm:ss'), $Level, $Message)
    $color = 'Gray'
    if ($Level -eq 'OK') { $color = 'Green' } elseif ($Level -eq 'WARN') { $color = 'Yellow' } elseif ($Level -eq 'FAIL') { $color = 'Red' } elseif ($Level -eq 'STEP') { $color = 'Cyan' }
    Write-Host $line -ForegroundColor $color
    try { [System.IO.File]::AppendAllText($LogFile, $line + "`r`n", [System.Text.UTF8Encoding]::new($false)) } catch { }
}
function Add-Phase {
    param([string]$Name, [string]$Status, [string]$Detail, [datetime]$Start)
    $sec = [Math]::Round(((Get-Date) - $Start).TotalSeconds, 1)
    $Phases.Add([pscustomobject]@{ Name = $Name; Status = $Status; Detail = $Detail; Sec = $sec })
    Write-Log ("{0} -> {1} ({2}s) {3}" -f $Name, $Status, $sec, $Detail) $(if ($Status -eq 'OK') { 'OK' } elseif ($Status -eq 'SKIP') { 'INFO' } else { $Status })
}
function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}
function Get-Sha8 {
    param([string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hash = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Text))
    return ([System.BitConverter]::ToString($hash) -replace '-','').Substring(0,8).ToLower()
}
function Invoke-Proc {
    # LL#26: stream child output live (no redirect) unless -Capture; returns [pscustomobject] ExitCode/Output
    param([string]$Exe, [string[]]$ArgList, [string]$Cwd, [switch]$Capture, [switch]$NoWait, [hashtable]$EnvVars)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $Exe
    foreach ($a in $ArgList) { [void]$psi.ArgumentList.Add($a) }
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $NoWait.IsPresent
    $psi.RedirectStandardOutput = $Capture.IsPresent
    $psi.RedirectStandardError = $Capture.IsPresent
    if ($Cwd) { $psi.WorkingDirectory = $Cwd }
    $psi.Environment['PYTHONIOENCODING'] = 'utf-8'
    $psi.Environment['PYTHONUTF8'] = '1'
    if ($EnvVars) { foreach ($k in $EnvVars.Keys) { $psi.Environment[$k] = [string]$EnvVars[$k] } }
    $p = $null
    try { $p = [System.Diagnostics.Process]::Start($psi) } catch { Write-Log ("cannot start {0}: {1}" -f $Exe, $_.Exception.Message) 'WARN'; return [pscustomobject]@{ ExitCode = -2; Output = $_.Exception.Message; Pid = 0 } }
    if ($NoWait) { return [pscustomobject]@{ ExitCode = -1; Output = ''; Pid = $p.Id } }
    $out = ''
    if ($Capture) { $out = $p.StandardOutput.ReadToEnd() + $p.StandardError.ReadToEnd() }
    $p.WaitForExit()
    return [pscustomobject]@{ ExitCode = $p.ExitCode; Output = $out; Pid = $p.Id }
}

Write-Host ''
Write-Host '  VAKE  Veritas AKShare Knowledge & Extraction Engine  v0200' -ForegroundColor Yellow
Write-Host ('  root {0}   venv {1}   log {2}' -f $VakeRoot, $VenvDir, $LogFile) -ForegroundColor DarkGray
Write-Host ''

# ---------------------------------------------------------------- Phase 1  Python venv (isolated, only-increase)
$ps = Get-Date
Write-Log 'Phase 1  python venv' 'STEP'
$Py = Join-Path $VenvDir 'Scripts\python.exe'
$venvStatus = 'OK'; $venvDetail = 'exists'
if (-not (Test-Path -LiteralPath $Py)) {
    $venvDetail = ''
    $launchers = @()
    if (Get-Command py -ErrorAction SilentlyContinue) { $launchers += @(@('py',@('-3.12')), @('py',@('-3.11')), @('py',@('-3'))) }
    if (Get-Command python -ErrorAction SilentlyContinue) { $launchers += ,@('python',@()) }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { $launchers += ,@('python3',@()) }
    foreach ($L in $launchers) {
        $exe = $L[0]; $pre = @($L[1])
        $r = Invoke-Proc -Exe $exe -ArgList ($pre + @('-m','venv',$VenvDir)) -Capture
        if ($r.ExitCode -eq 0 -and (Test-Path -LiteralPath $Py)) { $venvDetail = ('created via {0} {1}' -f $exe, ($pre -join ' ')); break }
    }
    if (-not (Test-Path -LiteralPath $Py)) { $venvStatus = 'FAIL'; $venvDetail = 'no python launcher could create the venv (install Python 3.11/3.12 and re-run)' }
}
Add-Phase 'P1 venv' $venvStatus $venvDetail $ps

# ---------------------------------------------------------------- Phase 2  packages (probe first, install only missing)
$ps = Get-Date
Write-Log 'Phase 2  packages' 'STEP'
$pkgStatus = 'SKIP'; $pkgDetail = 'venv missing'
if (Test-Path -LiteralPath $Py) {
    $probe = Invoke-Proc -Exe $Py -ArgList @('-c', $ImportProbe) -Capture
    if ($probe.Output -match 'IMPORT_OK') {
        $pkgStatus = 'OK'; $pkgDetail = ('already installed: ' + ($probe.Output.Trim() -replace 'IMPORT_OK\s*',''))
    } else {
        Write-Log 'installing packages (first run, 1-3 min)…' 'INFO'
        $r = Invoke-Proc -Exe $Py -ArgList (@('-m','pip','install','--disable-pip-version-check','--quiet') + $Packages)
        $probe = Invoke-Proc -Exe $Py -ArgList @('-c', $ImportProbe) -Capture
        if ($probe.Output -match 'IMPORT_OK') { $pkgStatus = 'OK'; $pkgDetail = ('installed: ' + ($probe.Output.Trim() -replace 'IMPORT_OK\s*','')) }
        else { $pkgStatus = 'FAIL'; $pkgDetail = ('pip exit ' + $r.ExitCode + ' / ' + ($probe.Output -split "`n" | Select-Object -Last 2) -join ' ') }
    }
}
Add-Phase 'P2 packages' $pkgStatus $pkgDetail $ps

# ---------------------------------------------------------------- Phase 3  engine files (archive previous version if content differs)
$ps = Get-Date
Write-Log 'Phase 3  engine files' 'STEP'
$EngineFiles = [ordered]@{
    'VDF_AkshareFetcher.py' = @'
# -*- coding: utf-8 -*-
"""
VDF_AkshareFetcher.py  —  VIA / VDF (VeritasDataForge) AKShare Super Fetcher  (VAKE v0200, single-file build)
==========================================================================================================
One file = knowledge crawler + AST inventory + registry/param classification + Polars/Parquet/DuckDB store
+ symbol universes + batch fetch engine (newest-first, early-stop, TTL, fixed-quantity flush) + local console.

  python VDF_AkshareFetcher.py scan [--refresh-docs] [--offline]
  python VDF_AkshareFetcher.py serve [--port 8765] [--no-open]
  python VDF_AkshareFetcher.py fetch --selection <json> | --fns a,b,c [--start 2020-01-01] [--mode incremental|backfill]
  python VDF_AkshareFetcher.py schedule-run | views | params | compact [--min-parts 8] | universe <kind> [--refresh]

Data root: env VAKE_ROOT (default C:/VIA/VAKE). Governance: 只增不減 — parquet parts are never rewritten or deleted;
superseded files go to _archive/. LL: UTF-8 no-BOM, no interactive input.
Sections keep their original module names (C=config, K=knowledge, A=ast, R=registry, S=store, U=universe,
F=fetch, V=server, CLI) — the aliases below all point at this module so intra-section references are unchanged.
"""
import sys as _sys
C = K = A = R = S = U = F = V = _sys.modules[__name__]


# ====================================================================================================
# SECTION VAKE_CONFIG
# ====================================================================================================
"""VAKE - Veritas AKShare Knowledge & Extraction Engine :: config (v0100)
Append-only governance (只增不減): nothing here deletes; archives are versioned by stamp.
"""
import os, sys, json, pathlib, datetime, threading

VAKE_VERSION = "v0200"
ENGINE_NAME = "VDF_AkshareFetcher (VAKE — Veritas AKShare Knowledge & Extraction Engine)"

if os.name == "nt":
    _default_root = pathlib.Path(r"C:\VIA\VAKE")
else:
    _default_root = pathlib.Path.home() / "VAKE"
ROOT = pathlib.Path(os.environ.get("VAKE_ROOT") or _default_root)

DIR_ENGINE = ROOT / "engine"
DIR_KNOWLEDGE = ROOT / "knowledge"
DIR_DOCS = DIR_KNOWLEDGE / "docs"
DIR_STORE = ROOT / "store"
DIR_DB = ROOT / "db"
DIR_LOGS = ROOT / "logs"
DIR_RUNS = ROOT / "runs"
DIR_SELECTIONS = ROOT / "selections"
DIR_ARCHIVE = ROOT / "_archive"

ALL_DIRS = [DIR_ENGINE, DIR_KNOWLEDGE, DIR_DOCS, DIR_STORE, DIR_DB, DIR_LOGS, DIR_RUNS, DIR_SELECTIONS, DIR_ARCHIVE]

DB_PATH = DIR_DB / "vake.duckdb"
KNOWLEDGE_JSON = DIR_KNOWLEDGE / "akshare_knowledge.json"
AST_JSON = DIR_KNOWLEDGE / "akshare_ast.json"
REGISTRY_JSON = DIR_KNOWLEDGE / "vake_registry.json"
REGISTRY_PARQUET = DIR_KNOWLEDGE / "vake_registry.parquet"
DEFAULT_SELECTION = DIR_SELECTIONS / "default_selection.json"
DETAIL_LOG = DIR_LOGS / "vake_detail.log"

DOC_BASE = "https://akshare.akfamily.xyz"
DOC_INDEX_URL = DOC_BASE + "/data/index.html"
# fallback list (relative to /data/) -- used when index crawl fails; crawl result is unioned with this
FALLBACK_DOC_PAGES = [
    "stock/stock", "futures/futures", "bond/bond", "option/option", "fx/fx", "currency/currency",
    "spot/spot", "interest_rate/interest_rate", "fund/fund_private", "fund/fund_public", "index/index",
    "macro/macro", "dc/dc", "bank/bank", "article/article", "energy/energy", "event/event", "hf/hf",
    "nlp/nlp", "qdii/qdii", "others/others", "qhkc/index", "tool/tool",
]
CATEGORY_ZH = {
    "stock": "股票數據", "futures": "期貨數據", "bond": "債券數據", "option": "期權數據", "fx": "外匯數據",
    "currency": "貨幣數據", "spot": "現貨數據", "interest_rate": "利率數據", "fund": "基金數據",
    "index": "指數數據", "macro": "宏觀數據", "dc": "加密貨幣", "bank": "銀行數據", "article": "論文數據",
    "energy": "能源數據", "event": "遷徙/事件數據", "hf": "高頻數據", "nlp": "自然語言處理", "qdii": "QDII 數據",
    "others": "另類數據", "qhkc": "奇貨可查", "tool": "工具箱",
}

DEFAULT_PORT = 8765
DEFAULT_WORKERS = 4
MAX_ENUM_COMBOS = 600
MAX_SINGLE_DATE_CALLS = 400
OVERLAP_DAYS = 3
BATCH_ROWS = 20000          # fixed-quantity flush: one parquet part per 20k rows (or series end)
SNAPSHOT_TTL_HOURS = 12     # FULL_SNAPSHOT series not re-downloaded within this many hours (traffic saver)
COMPACT_MIN_PARTS = 8       # compaction threshold (old parts archived, never deleted)  # incremental re-fetch overlap so late revisions are captured (dedup by row hash)
TW_RED = "#c96b5a"
TW_GREEN = "#5a9e6f"

_log_lock = threading.Lock()


def ensure_dirs():
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


def stamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg, level="INFO", run_id=None):
    line = f"[{now_iso()}] [{level}] " + (f"[{run_id}] " if run_id else "") + str(msg)
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        DIR_LOGS.mkdir(parents=True, exist_ok=True)
        with _log_lock:
            with open(DETAIL_LOG, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        pass


def write_json(path, obj):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, default=str)
    if path.exists():
        # append-only: archive previous version before replacing
        DIR_ARCHIVE.mkdir(parents=True, exist_ok=True)
        try:
            path.replace(DIR_ARCHIVE / f"{path.stem}.{stamp()}{path.suffix}")
        except Exception:
            pass
    tmp.replace(path)


def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

# ====================================================================================================
# SECTION VAKE_KNOWLEDGE
# ====================================================================================================
"""VAKE knowledge engine: crawl AKShare docs (_sources/*.md.txt) and parse them into a structured
knowledge base: category -> heading path -> interface (function) -> params / outputs / example / enum tables.
"""
import re, ast, time, pathlib

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

HEAD_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
IFACE_RE = re.compile(r"^接口[:：]\s*([A-Za-z_][A-Za-z0-9_]*)")
FIELD_RES = {
    "target": re.compile(r"^目标地址[:：]\s*(.*)$"),
    "desc": re.compile(r"^描述[:：]\s*(.*)$"),
    "limit": re.compile(r"^限量[:：]\s*(.*)$"),
    "note": re.compile(r"^说明[:：]\s*(.*)$"),
}
CHOICE_RE = re.compile(r"choice of\s*\{(.*?)\}", re.S)
QUOTED_RE = re.compile(r"[\"'“”‘’]([^\"'“”‘’]+)[\"'“”‘’]")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
CALL_RE = re.compile(r"ak\.([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*$")


def _clean_heading(t):
    t = LINK_RE.sub(r"\1", t)
    return t.strip()


def _split_table_row(line):
    parts = line.strip().strip("|").split("|")
    return [p.strip() for p in parts]


def _is_sep_row(cells):
    return all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) or c == "" for c in cells) and any(c for c in cells)


def parse_tables(lines):
    """Return list of (label_before, header, rows) for all markdown tables in lines."""
    tables = []
    i = 0
    n = len(lines)
    last_label = ""
    while i < n:
        ln = lines[i]
        if ln.strip().startswith("|"):
            block = []
            while i < n and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            rows = [_split_table_row(b) for b in block]
            if not rows:
                continue
            header = rows[0]
            body = [r for r in rows[1:] if not _is_sep_row(r)]
            tables.append((last_label, header, body))
            last_label = ""
        else:
            s = ln.strip()
            if s and not s.startswith("```"):
                last_label = s
            i += 1
    return tables


def _parse_example_call(code_lines, fn):
    """Extract kwargs from `ak.fn(...)` in an example code block using ast (safe)."""
    src = "\n".join(code_lines)
    m = re.search(r"ak\." + re.escape(fn) + r"\((.*?)\)\s*(\n|$)", src, re.S)
    if not m:
        return {}
    argsrc = m.group(1).strip()
    if not argsrc:
        return {}
    try:
        node = ast.parse(f"f({argsrc})", mode="eval").body
        kw = {}
        for i, a in enumerate(node.args):
            try:
                kw[f"__pos{i}"] = ast.literal_eval(a)
            except Exception:
                kw[f"__pos{i}"] = ast.unparse(a)
        for k in node.keywords:
            try:
                kw[k.arg] = ast.literal_eval(k.value)
            except Exception:
                kw[k.arg] = ast.unparse(k.value)
        return kw
    except Exception:
        return {"__raw": argsrc}


def _param_choices(desc):
    m = CHOICE_RE.search(desc or "")
    if not m:
        return []
    inner = m.group(1)
    vals = QUOTED_RE.findall(inner)
    if not vals:
        vals = [v.strip() for v in inner.split(",") if v.strip()]
    return vals


def parse_markdown(text, category, page):
    lines = text.splitlines()
    entries = []
    stack = {}  # level -> title
    cur = None
    buf = []

    def flush():
        nonlocal cur, buf
        if cur is None:
            return
        body = buf
        # fields
        for ln in body:
            s = ln.strip()
            for k, rx in FIELD_RES.items():
                m = rx.match(s)
                if m and not cur.get(k):
                    cur[k] = m.group(1).strip()
        # tables
        tables = parse_tables(body)
        params, outputs, extra_tables = [], [], []
        for label, header, rows in tables:
            hl = " ".join(header)
            if label.startswith("输入参数") or (not params and "名称" in hl and "类型" in hl and not outputs and label != "输出参数" and "输入" in label):
                for r in rows:
                    if len(r) >= 3 and r[0] not in ("-", ""):
                        params.append({"name": r[0], "type": r[1], "desc": r[2], "choices": _param_choices(r[2])})
            elif label.startswith("输出参数"):
                for r in rows:
                    if len(r) >= 2 and r[0] not in ("-", ""):
                        outputs.append({"name": r[0], "type": r[1] if len(r) > 1 else "", "desc": r[2] if len(r) > 2 else ""})
            else:
                extra_tables.append({"label": label, "header": header, "rows": rows})
        # if 输入参数 label detection failed (label line may be separated), fallback: first 名称/类型/描述 table = params, second = outputs
        if not params and not outputs:
            nt = [t for t in tables if "名称" in " ".join(t[1])]
            if nt:
                for r in nt[0][2]:
                    if len(r) >= 3 and r[0] not in ("-", ""):
                        params.append({"name": r[0], "type": r[1], "desc": r[2], "choices": _param_choices(r[2])})
                if len(nt) > 1:
                    for r in nt[1][2]:
                        if len(r) >= 2 and r[0] not in ("-", ""):
                            outputs.append({"name": r[0], "type": r[1], "desc": r[2] if len(r) > 2 else ""})
        # enum tables whose header matches param names
        pnames = {p["name"] for p in params}
        enum_table = None
        for t in extra_tables:
            hdr = [h for h in t["header"]]
            if hdr and pnames and set(hdr) & pnames and len(set(hdr) & pnames) >= max(1, len(hdr) - 1):
                enum_table = {"columns": hdr, "rows": [r for r in t["rows"] if len(r) == len(hdr)]}
                break
        # example call
        code, incode = [], False
        for ln in body:
            if ln.strip().startswith("```"):
                incode = not incode
                continue
            if incode:
                code.append(ln)
        example_args = _parse_example_call(code, cur["fn"])
        cur.update({"params": params, "outputs": outputs, "enum_table": enum_table, "example_args": example_args,
                    "output_columns": [o["name"] for o in outputs],
                    "extra_tables": [t for t in extra_tables if t is not enum_table and len(t.get("rows", [])) <= 3000]})
        entries.append(cur)
        cur, buf = None, []

    for ln in lines:
        hm = HEAD_RE.match(ln)
        if hm:
            flush()
            lvl = len(hm.group(1))
            title = _clean_heading(hm.group(2))
            stack[lvl] = title
            for k in list(stack.keys()):
                if k > lvl:
                    del stack[k]
            continue
        im = IFACE_RE.match(ln.strip())
        if im:
            flush()
            path = [stack[k] for k in sorted(stack.keys()) if k >= 2]
            cur = {"fn": im.group(1), "category": category, "page": page, "heading_path": path,
                   "title": path[-1] if path else im.group(1)}
            buf = []
            continue
        if cur is not None:
            buf.append(ln)
    flush()
    return entries


# ---------------------------------------------------------------- crawl
def _get(url, retries=3, timeout=25):
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "VIA-VAKE/1.0"})
            if r.status_code == 200:
                r.encoding = "utf-8"
                return r.text
            last = f"HTTP {r.status_code}"
            if r.status_code in (403, 404, 410):
                break  # non-retryable
        except Exception as e:
            last = str(e)
        time.sleep(0.8 * (i + 1))
    raise RuntimeError(f"GET failed {url}: {last}")


def discover_pages():
    pages = set(C.FALLBACK_DOC_PAGES)
    try:
        html = _get(C.DOC_INDEX_URL)
        for m in re.finditer(r'href="([a-z_]+/[A-Za-z0-9_]+)\.html', html):
            pages.add(m.group(1))
        C.log(f"doc index crawl ok: {len(pages)} pages")
    except Exception as e:
        C.log(f"doc index crawl failed ({e}); using fallback list", "WARN")
    return sorted(pages)


def fetch_doc_page(rel, refresh=False):
    """rel like 'interest_rate/interest_rate' -> cached md text (append-only cache)."""
    C.DIR_DOCS.mkdir(parents=True, exist_ok=True)
    cache = C.DIR_DOCS / (rel.replace("/", "__") + ".md")
    if cache.exists() and not refresh:
        return cache.read_text(encoding="utf-8")
    url = f"{C.DOC_BASE}/_sources/data/{rel}.md.txt"
    text = _get(url)
    if cache.exists():
        cache.replace(C.DIR_ARCHIVE / f"{cache.stem}.{C.stamp()}.md")
    cache.write_text(text, encoding="utf-8")
    return text


def build_knowledge(refresh=False, offline=False):
    C.ensure_dirs()
    pages = C.FALLBACK_DOC_PAGES if offline else discover_pages()
    all_entries, page_stats = [], []
    for rel in pages:
        cat = rel.split("/")[0]
        try:
            if offline:
                cache = C.DIR_DOCS / (rel.replace("/", "__") + ".md")
                if not cache.exists():
                    page_stats.append({"page": rel, "status": "NO_CACHE", "entries": 0})
                    continue
                text = cache.read_text(encoding="utf-8")
            else:
                text = fetch_doc_page(rel, refresh=refresh)
            ents = parse_markdown(text, cat, rel)
            all_entries.extend(ents)
            page_stats.append({"page": rel, "status": "OK", "entries": len(ents)})
            C.log(f"doc parsed {rel}: {len(ents)} interfaces")
        except Exception as e:
            page_stats.append({"page": rel, "status": f"FAIL {e}", "entries": 0})
            C.log(f"doc failed {rel}: {e}", "WARN")
    # dedupe by fn (keep first occurrence, record duplicates)
    seen, uniq, dups = {}, [], []
    for e in all_entries:
        if e["fn"] in seen:
            dups.append({"fn": e["fn"], "page": e["page"], "heading_path": e["heading_path"]})
            seen[e["fn"]].setdefault("also_in", []).append({"page": e["page"], "heading_path": e["heading_path"]})
        else:
            seen[e["fn"]] = e
            uniq.append(e)
    kb = {"generated_at": C.now_iso(), "engine": C.ENGINE_NAME, "version": C.VAKE_VERSION,
          "pages": page_stats, "interfaces": uniq, "duplicates": dups, "count": len(uniq)}
    C.write_json(C.KNOWLEDGE_JSON, kb)
    C.log(f"knowledge base written: {len(uniq)} interfaces, {len(dups)} duplicate mentions")
    return kb

# ====================================================================================================
# SECTION VAKE_AST
# ====================================================================================================
"""VAKE AST engine: scan the installed akshare package (read-only) and inventory every public
interface with its module, signature, defaults and first docstring line. Classifies by package folder.
"""
import ast, pathlib, importlib, sys


def _unparse(node):
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _default_literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return _unparse(node)


def scan_function(fd, module_rel):
    a = fd.args
    params = []
    pos = a.posonlyargs + a.args
    defaults = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)
    for arg, d in zip(pos, defaults):
        params.append({"name": arg.arg, "annotation": _unparse(arg.annotation) if arg.annotation else None,
                       "default": _default_literal(d) if d is not None else None, "has_default": d is not None})
    for arg, d in zip(a.kwonlyargs, a.kw_defaults):
        params.append({"name": arg.arg, "annotation": _unparse(arg.annotation) if arg.annotation else None,
                       "default": _default_literal(d) if d is not None else None, "has_default": d is not None, "kwonly": True})
    doc = ast.get_docstring(fd) or ""
    return {"fn": fd.name, "module": module_rel, "params": params, "lineno": fd.lineno,
            "doc_first": doc.strip().splitlines()[0].strip() if doc.strip() else "",
            "returns": _unparse(fd.returns) if fd.returns else None}


def build_ast_inventory():
    C.ensure_dirs()
    ak = importlib.import_module("akshare")
    pkg_dir = pathlib.Path(ak.__file__).parent
    exported = set(n for n in dir(ak) if not n.startswith("_"))
    inv, modules, errors = {}, 0, []
    for py in sorted(pkg_dir.rglob("*.py")):
        rel = py.relative_to(pkg_dir).as_posix()
        if rel.startswith("__pycache__"):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            errors.append({"module": rel, "error": str(e)})
            continue
        modules += 1
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                if node.name in exported and node.name not in inv:
                    rec = scan_function(node, rel)
                    top = rel.split("/")[0] if "/" in rel else "root"
                    rec["ast_category"] = top
                    inv[node.name] = rec
    out = {"generated_at": C.now_iso(), "akshare_version": getattr(ak, "__version__", "?"),
           "package_dir": str(pkg_dir), "modules_scanned": modules, "exported_names": len(exported),
           "functions": inv, "count": len(inv), "parse_errors": errors}
    C.write_json(C.AST_JSON, out)
    C.log(f"AST inventory: akshare {out['akshare_version']}, {modules} modules, {len(inv)} public functions")
    return out

# ====================================================================================================
# SECTION VAKE_REGISTRY
# ====================================================================================================
"""VAKE registry: merge doc knowledge + AST inventory into one registry with a fetch-strategy
classification per interface, and a category/heading tree for the picker UI.

Strategies
  DATE_RANGE     start_date/end_date params -> incremental window from last_date-overlap to today (chunked by window_days)
  SINGLE_DATE    date param -> iterate calendar days (skip weekends) from last_date+1 to today
  YEAR           year / start_year params -> iterate years
  FULL_SNAPSHOT  no date params -> one call, row-hash anti-join keeps only new rows (append-only)
Modifiers
  ENUM           params with documented choices / enum tables -> cartesian combos (capped)
"""
import itertools, re, datetime

# ---------------------------------------------------------------- parameter classification (every param -> dropdown spec)
KNOWN_CHOICES = {
    "period": ["daily", "weekly", "monthly", "1", "5", "15", "30", "60"],
    "adjust": ["", "qfq", "hfq"],
    "timeout": [None],
}
SYMBOL_NAMES = {"symbol", "stock", "code", "ticker", "secid", "fund", "fund_code", "index", "bond", "contract", "stock_code", "etf", "name"}
UNIVERSE_BY_PREFIX = [("stock_board_industry", "board_industry"), ("stock_board_concept", "board_concept"), ("stock_hk", "hk"), ("stock_us", "us"), ("stock_zh_a", "stock_a"), ("stock_zh_b", "stock_b"), ("stock_a", "stock_a"),
                      ("stock_", "stock_a"), ("fund_etf", "etf"), ("fund_lof", "lof"), ("fund_", "fund"), ("index_", "index"),
                      ("bond_cb", "bond_cb"), ("bond_zh_cov", "bond_cb"), ("bond_", "bond_cb"), ("futures_", "futures"),
                      ("option_", "option"), ("macro_", None)]
QUOTED = re.compile(r"[\"'“”‘’]([^\"'“”‘’]{1,60})[\"'“”‘’]")
BRACES = re.compile(r"\{([^{}]{1,600})\}")


def universe_kind(fn, pname):
    if pname.lower() not in SYMBOL_NAMES:
        return None
    for pre, kind in UNIVERSE_BY_PREFIX:
        if fn.startswith(pre):
            return kind
    return None


def _candidates_from_desc(desc):
    out = []
    for m in BRACES.finditer(desc or ""):
        vals = QUOTED.findall(m.group(1))
        if not vals:
            vals = [v.strip() for v in m.group(1).split(",") if v.strip() and len(v.strip()) < 40]
        out.extend(vals)
    if not out:
        out.extend(QUOTED.findall(desc or ""))
    return list(dict.fromkeys(out))


def classify_params(entry, cls):
    """Return list of param specs: name, kind, candidates, default, multi, source, universe."""
    doc = {p["name"]: p for p in entry.get("params", [])}
    ast_p = {p["name"]: p for p in entry.get("ast_params", [])}
    names = list(dict.fromkeys(list(ast_p.keys()) + list(doc.keys())))
    ex = entry.get("example_args") or {}
    et = entry.get("enum_table")
    date_names = set(cls.get("date_params", {}).values())
    fn = entry["fn"]
    specs = []
    unmatched_tables = []
    for t in (entry.get("extra_tables") or []):
        unmatched_tables.append(t)
    for n in names:
        d = doc.get(n, {})
        a = ast_p.get(n, {})
        default = ex.get(n, a.get("default"))
        desc = d.get("desc", "") or ""
        cands, kind, source = [], "FREE", "default"
        if n in date_names:
            kind, source = "DATE", "strategy"
        elif et and n in et.get("columns", []):
            kind, source = "ENUM_TABLE", "doc-table"
            cands = list(dict.fromkeys(r[et["columns"].index(n)] for r in et["rows"]))
        elif d.get("choices"):
            kind, source = "ENUM_DOC", "doc-choice"
            cands = list(d["choices"])
        else:
            dc = _candidates_from_desc(desc)
            if len(dc) > 1:
                kind, source, cands = "ENUM_INFERRED", "doc-desc", dc
            elif n.lower() in KNOWN_CHOICES and KNOWN_CHOICES[n.lower()] != [None]:
                kind, source, cands = "ENUM_KNOWN", "known-dict", list(KNOWN_CHOICES[n.lower()])
            elif universe_kind(fn, n):
                kind, source = "SYMBOL", "universe"
            elif n.lower() in ("timeout", "proxies", "proxy"):
                kind, source = "TECH", "skip"
            if "参见" in desc or "参考" in desc:
                # doc points to a lookup table on the page whose header did not match param names
                for t in unmatched_tables:
                    hdr = t.get("header") or []
                    if hdr and len(t.get("rows", [])) > 1:
                        col = 0
                        for i, h in enumerate(hdr):
                            if n.lower() in h.lower() or h in ("代码", "symbol", "code", "品种", "名称"):
                                col = i
                                break
                        vals = [r[col] for r in t["rows"] if len(r) > col and r[col] not in ("-", "")]
                        if len(vals) > 1 and kind in ("FREE", "SYMBOL"):
                            kind, source, cands = "ENUM_TABLE", "doc-lookup-table", list(dict.fromkeys(vals))
                            break
        if default is not None and default not in cands and kind not in ("DATE", "TECH"):
            cands.insert(0, default)
        if kind == "FREE" and cands:
            kind = "ENUM_INFERRED" if len(cands) > 1 else "FREE"
        specs.append({"name": n, "kind": kind, "candidates": [c for c in cands if c is not None][:800], "default": default,
                      "source": source, "desc": desc[:200], "type": d.get("type") or a.get("annotation") or "",
                      "universe": universe_kind(fn, n) if kind == "SYMBOL" else None, "required": bool(a) and not a.get("has_default")})
    return specs

DATE_RANGE_NAMES = {("start_date", "end_date"), ("start_time", "end_time"), ("begin_date", "end_date"), ("from_date", "to_date")}
SINGLE_DATE_NAMES = ["date", "trade_date", "report_date", "quarter", "month"]
YEAR_NAMES = ["year", "start_year", "end_year"]
AST_CAT_TO_DOC = {"economic": "macro", "stock_feature": "stock", "stock_fundamental": "stock", "futures_derivative": "futures",
                  "rate": "interest_rate", "crypto": "dc", "forex": "fx", "reits": "fund", "qhkc_web": "qhkc",
                  "movie": "others", "air": "others", "fortune": "others", "news": "others", "cal": "tool", "other": "others",
                  "root": "tool", "utils": "tool", "datasets": "tool", "pro": "tool", "data": "tool", "cost": "others",
                  "cot": "futures", "hf": "hf", "bank": "bank", "article": "article", "energy": "energy", "event": "event",
                  "nlp": "nlp", "qdii": "qdii", "index": "index", "fund": "fund", "bond": "bond", "option": "option",
                  "spot": "spot", "stock": "stock", "futures": "futures", "currency": "currency", "fx": "fx",
                  "interest_rate": "interest_rate", "macro": "macro", "dc": "dc", "others": "others", "tool": "tool"}


def _date_fmt(sample):
    s = str(sample or "")
    if re.fullmatch(r"\d{8}", s):
        return "%Y%m%d"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return "%Y-%m-%d"
    if re.fullmatch(r"\d{4}/\d{2}/\d{2}", s):
        return "%Y/%m/%d"
    if re.fullmatch(r"\d{4}-\d{2}", s):
        return "%Y-%m"
    if re.fullmatch(r"\d{6}", s):
        return "%Y%m"
    if re.fullmatch(r"\d{4}", s):
        return "%Y"
    return "%Y%m%d"


def _window_days(limit_text):
    t = limit_text or ""
    if "一年" in t or "1年" in t or "一年内" in t:
        return 365
    if "半年" in t:
        return 180
    if "三个月" in t or "3个月" in t:
        return 90
    if "一个月" in t or "1个月" in t or "30" in t and "天" in t:
        return 30
    return None


def classify(entry):
    doc_params = {p["name"]: p for p in entry.get("params", [])}
    ast_params = {p["name"]: p for p in entry.get("ast_params", [])}
    names = list(dict.fromkeys(list(ast_params.keys()) + list(doc_params.keys())))
    lname = [n.lower() for n in names]
    strategy, date_params = "FULL_SNAPSHOT", {}
    for a, b in DATE_RANGE_NAMES:
        if a in lname and b in lname:
            strategy = "DATE_RANGE"
            date_params = {"start": names[lname.index(a)], "end": names[lname.index(b)]}
            break
    if strategy == "FULL_SNAPSHOT":
        for n in SINGLE_DATE_NAMES:
            if n in lname:
                strategy = "SINGLE_DATE"
                date_params = {"date": names[lname.index(n)]}
                break
    if strategy == "FULL_SNAPSHOT":
        for n in YEAR_NAMES:
            if n in lname:
                strategy = "YEAR"
                date_params = {"year": names[lname.index(n)]}
                break
    # sample values to infer date format
    sample = None
    ex = entry.get("example_args") or {}
    for k in date_params.values():
        if k in ex:
            sample = ex[k]
        elif k in ast_params and ast_params[k].get("default") is not None:
            sample = ast_params[k]["default"]
    date_fmt = _date_fmt(sample)
    # enumerations
    enum_axes = {}
    et = entry.get("enum_table")
    if et and et.get("rows"):
        enum_axes["__table__"] = {"columns": et["columns"], "rows": et["rows"]}
    else:
        for n, p in doc_params.items():
            if p.get("choices"):
                enum_axes[n] = list(dict.fromkeys(p["choices"]))
    # base kwargs = example args, else ast defaults (only for non-date params)
    base = {}
    for k, v in ex.items():
        if not k.startswith("__"):
            base[k] = v
    for n, p in ast_params.items():
        if n not in base and p.get("has_default") and p.get("default") is not None:
            base[n] = p["default"]
    for k in date_params.values():
        base.pop(k, None)
    required_missing = [n for n, p in ast_params.items() if not p.get("has_default") and n not in base and n not in date_params.values()]
    combos = 1
    if "__table__" in enum_axes:
        combos = len(enum_axes["__table__"]["rows"])
    else:
        for v in enum_axes.values():
            combos *= max(1, len(v))
    return {"strategy": strategy, "date_params": date_params, "date_fmt": date_fmt,
            "window_days": _window_days(entry.get("limit")), "enum_axes": enum_axes, "enum_combos": combos,
            "base_kwargs": base, "required_missing": required_missing,
            "runnable": len(required_missing) == 0}


def expand_params(reg_entry, max_combos=None, overrides=None):
    """Concrete kwargs dicts (without date params) for one registry entry.
    overrides = {param: [values...]} from the console dropdowns -> cartesian product (capped)."""
    max_combos = max_combos or C.MAX_ENUM_COMBOS
    base = dict(reg_entry.get("base_kwargs", {}))
    axes = reg_entry.get("enum_axes", {})
    out = []
    if overrides:
        keys = [k for k, v in overrides.items() if isinstance(v, list) and len(v) > 0]
        for k, v in overrides.items():
            if not isinstance(v, list) and v is not None:
                base[k] = v
        if keys:
            for combo in itertools.product(*[overrides[k] for k in keys]):
                d = dict(base)
                d.update(dict(zip(keys, combo)))
                out.append(d)
        else:
            out.append(base)
        return out[:max_combos]
    if "__table__" in axes:
        cols, rows = axes["__table__"]["columns"], axes["__table__"]["rows"]
        for r in rows:
            d = dict(base)
            d.update({c: v for c, v in zip(cols, r)})
            out.append(d)
    elif axes:
        keys = list(axes.keys())
        for combo in itertools.product(*[axes[k] for k in keys]):
            d = dict(base)
            d.update(dict(zip(keys, combo)))
            out.append(d)
    else:
        out.append(base)
    return out[:max_combos]


def build_registry(kb=None, ast_inv=None):
    kb = kb or C.read_json(C.KNOWLEDGE_JSON, {"interfaces": []})
    ast_inv = ast_inv or C.read_json(C.AST_JSON, {"functions": {}})
    fns = ast_inv.get("functions", {})
    reg, tree = {}, {}
    for e in kb.get("interfaces", []):
        fn = e["fn"]
        a = fns.get(fn)
        rec = dict(e)
        rec["has_docs"], rec["has_ast"] = True, a is not None
        rec["ast_params"] = a["params"] if a else []
        rec["module"] = a["module"] if a else None
        rec["doc_first"] = a["doc_first"] if a else ""
        rec.update(classify(rec))
        rec["param_specs"] = classify_params(rec, rec)
        reg[fn] = rec
    # AST-only functions (not documented in the crawled pages) -> category from module folder
    for fn, a in fns.items():
        if fn in reg:
            continue
        cat = AST_CAT_TO_DOC.get(a["ast_category"], a["ast_category"])
        rec = {"fn": fn, "category": cat, "page": None, "heading_path": ["未文件化 (AST only)", a["module"]],
               "title": a["doc_first"] or fn, "desc": a["doc_first"], "limit": "", "params": [], "outputs": [],
               "enum_table": None, "example_args": {}, "output_columns": [], "has_docs": False, "has_ast": True,
               "ast_params": a["params"], "module": a["module"], "doc_first": a["doc_first"]}
        rec.update(classify(rec))
        rec["param_specs"] = classify_params(rec, rec)
        reg[fn] = rec
    # tree
    for fn, r in reg.items():
        cat = r["category"]
        node = tree.setdefault(cat, {"label": f"{cat} · {C.CATEGORY_ZH.get(cat, cat)}", "children": {}, "fns": []})
        for h in r["heading_path"][:-1] if r["has_docs"] else r["heading_path"]:
            node = node["children"].setdefault(h, {"label": h, "children": {}, "fns": []})
        node["fns"].append(fn)
    stats = {"total": len(reg), "documented": sum(1 for r in reg.values() if r["has_docs"]),
             "ast_only": sum(1 for r in reg.values() if not r["has_docs"]),
             "doc_missing_in_ast": sum(1 for r in reg.values() if r["has_docs"] and not r["has_ast"]),
             "by_strategy": {}, "by_category": {}, "params_total": 0, "params_by_kind": {},
             "fns_all_params_selectable": 0}
    for r in reg.values():
        sel_ok = True
        for ps_ in r.get("param_specs", []):
            stats["params_total"] += 1
            stats["params_by_kind"][ps_["kind"]] = stats["params_by_kind"].get(ps_["kind"], 0) + 1
            if ps_["kind"] == "FREE" and not ps_["candidates"]:
                sel_ok = False
        if sel_ok:
            stats["fns_all_params_selectable"] += 1
        stats["by_strategy"][r["strategy"]] = stats["by_strategy"].get(r["strategy"], 0) + 1
        stats["by_category"][r["category"]] = stats["by_category"].get(r["category"], 0) + 1
    out = {"generated_at": C.now_iso(), "engine": C.ENGINE_NAME, "version": C.VAKE_VERSION,
           "akshare_version": ast_inv.get("akshare_version"), "stats": stats, "tree": tree, "registry": reg}
    C.write_json(C.REGISTRY_JSON, out)
    try:
        import polars as pl
        rows = [{"fn": fn, "category": r["category"], "title": r["title"], "heading_path": " / ".join(r["heading_path"]),
                 "strategy": r["strategy"], "window_days": r["window_days"], "enum_combos": r["enum_combos"],
                 "runnable": r["runnable"], "has_docs": r["has_docs"], "has_ast": r["has_ast"], "module": r["module"],
                 "desc": r.get("desc") or "", "limit": r.get("limit") or "", "params": ",".join(p["name"] for p in r["ast_params"]),
                 "output_columns": ",".join(r["output_columns"])} for fn, r in reg.items()]
        pl.DataFrame(rows).write_parquet(C.REGISTRY_PARQUET, compression="zstd")
    except Exception as e:
        C.log(f"registry parquet skipped: {e}", "WARN")
    C.log(f"registry built: {stats}")
    return out


def load_registry():
    return C.read_json(C.REGISTRY_JSON, {"registry": {}, "tree": {}, "stats": {}})

# ====================================================================================================
# SECTION VAKE_STORE
# ====================================================================================================
"""VAKE store: Polars normalisation -> Parquet partitions (append-only) -> DuckDB catalogue/manifest.

Layout
  store/<category>/<fn>/<param_hash>/part_<stamp>.parquet   (zstd, only NEW rows per run)
  db/vake.duckdb                                            (vake_manifest / vake_runs / vake_fetch_log + v_<fn> views)
Every row carries: _vake_fn, _vake_param_hash, _vake_params, _vake_fetched_at, _vake_date, _vake_row_hash
Row hash = hash of all source columns -> incremental anti-join means re-fetching overlapping windows never duplicates.
"""
import hashlib, json, time, datetime, pathlib, re, threading, uuid
import polars as pl
import duckdb

DATE_COL_CANDIDATES = ["日期", "date", "报告日", "trade_date", "时间", "datetime", "交易日", "发布时间", "公告日期", "统计日期",
                       "日期时间", "时间戳", "报告日期", "截止日期", "月份", "年份", "period", "day", "time", "报告期", "日期_str"]
_db_lock = threading.RLock()
_series_locks = {}
_series_guard = threading.Lock()


def series_lock(fn, ph):
    with _series_guard:
        return _series_locks.setdefault(f"{fn}|{ph}", threading.RLock())


META_COLS = ["_vake_fn", "_vake_param_hash", "_vake_params", "_vake_fetched_at", "_vake_date", "_vake_row_hash"]


def param_hash(params):
    s = json.dumps(params or {}, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.blake2s(s.encode("utf-8"), digest_size=6).hexdigest()


def _safe(name):
    return re.sub(r"[^A-Za-z0-9_\-]+", "_", str(name))


def fn_dir(category, fn):
    return C.DIR_STORE / _safe(category) / _safe(fn)


def to_polars(obj):
    """pandas DataFrame/Series/dict/list -> polars DataFrame with string-safe object columns."""
    import pandas as pd
    if obj is None:
        return None
    if isinstance(obj, pl.DataFrame):
        return obj
    if isinstance(obj, pd.Series):
        obj = obj.reset_index()
    elif isinstance(obj, dict):
        obj = pd.DataFrame([obj])
    elif isinstance(obj, (list, tuple)):
        obj = pd.DataFrame(obj)
    if not isinstance(obj, pd.DataFrame):
        obj = pd.DataFrame({"value": [str(obj)]})
    if obj.empty:
        return pl.DataFrame()
    df = obj.copy()
    df.columns = [str(c) if str(c).strip() else f"col_{i}" for i, c in enumerate(df.columns)]
    # de-duplicate column names
    seen, cols = {}, []
    for c in df.columns:
        if c in seen:
            seen[c] += 1
            cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            cols.append(c)
    df.columns = cols
    if not isinstance(df.index, pd.RangeIndex):
        df = df.reset_index()
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(lambda v: None if v is None or (isinstance(v, float) and v != v) else str(v))
            df[c] = df[c].astype("string")
    try:
        return pl.from_pandas(df, nan_to_null=True)
    except Exception:
        df = df.astype(str)
        return pl.from_pandas(df)


def _detect_date_col(pdf):
    lower = {c.lower(): c for c in pdf.columns}
    for cand in DATE_COL_CANDIDATES:
        if cand.lower() in lower:
            return lower[cand.lower()]
    for c, dt in zip(pdf.columns, pdf.dtypes):
        if dt in (pl.Date, pl.Datetime):
            return c
    for c in pdf.columns:
        if any(k in c for k in ("日期", "date", "Date", "时间")):
            return c
    return None


def _to_date_expr(col):
    s = pl.col(col).cast(pl.Utf8, strict=False).str.strip_chars()
    s8 = s.str.replace_all(r"[/.]", "-")
    return pl.coalesce([
        s8.str.to_date("%Y-%m-%d", strict=False),
        s8.str.slice(0, 10).str.to_date("%Y-%m-%d", strict=False),
        s.str.to_date("%Y%m%d", strict=False),
        s8.str.to_date("%Y-%m", strict=False),
        s.str.to_date("%Y", strict=False),
    ])


def normalize(pdf, fn, params, fetched_at=None):
    fetched_at = fetched_at or C.now_iso()
    if pdf is None or pdf.width == 0:
        return None
    src_cols = [c for c in pdf.columns if c not in META_COLS]
    dcol = _detect_date_col(pdf)
    exprs = []
    if dcol is not None:
        if pdf.schema[dcol] in (pl.Date,):
            exprs.append(pl.col(dcol).alias("_vake_date"))
        elif pdf.schema[dcol] in (pl.Datetime,):
            exprs.append(pl.col(dcol).cast(pl.Date).alias("_vake_date"))
        else:
            exprs.append(_to_date_expr(dcol).alias("_vake_date"))
    else:
        exprs.append(pl.lit(None, dtype=pl.Date).alias("_vake_date"))
    hash_expr = pl.concat_str([pl.col(c).cast(pl.Utf8, strict=False).fill_null("") for c in src_cols], separator="\x1f").hash(seed=7)
    out = pdf.with_columns(exprs + [
        pl.lit(fn).alias("_vake_fn"),
        pl.lit(param_hash(params)).alias("_vake_param_hash"),
        pl.lit(json.dumps(params or {}, ensure_ascii=False, sort_keys=True, default=str)).alias("_vake_params"),
        pl.lit(fetched_at).alias("_vake_fetched_at"),
        hash_expr.alias("_vake_row_hash"),
    ])
    return out


# ------------------------------------------------------------------ DuckDB
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS vake_manifest (
  fn VARCHAR, param_hash VARCHAR, category VARCHAR, params_json VARCHAR, strategy VARCHAR,
  first_date DATE, last_date DATE, rows_total BIGINT, parts INTEGER,
  last_run VARCHAR, last_status VARCHAR, last_error VARCHAR, updated_at TIMESTAMP,
  PRIMARY KEY (fn, param_hash));
CREATE TABLE IF NOT EXISTS vake_runs (
  run_id VARCHAR PRIMARY KEY, started TIMESTAMP, finished TIMESTAMP, mode VARCHAR, selected INTEGER,
  tasks INTEGER, ok INTEGER, fail INTEGER, skipped INTEGER, rows_fetched BIGINT, rows_new BIGINT, note VARCHAR);
CREATE TABLE IF NOT EXISTS vake_universe (
  kind VARCHAR, code VARCHAR, name VARCHAR, fetched_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS vake_compactions (
  fn VARCHAR, param_hash VARCHAR, ts TIMESTAMP, parts_before INTEGER, rows BIGINT, archive_dir VARCHAR);
CREATE TABLE IF NOT EXISTS vake_fetch_log (
  run_id VARCHAR, fn VARCHAR, param_hash VARCHAR, params_json VARCHAR, window_start VARCHAR, window_end VARCHAR,
  ts TIMESTAMP, status VARCHAR, rows_fetched BIGINT, rows_new BIGINT, elapsed_s DOUBLE, error VARCHAR, part_file VARCHAR);
"""


class _LockedCon:
    """Thin wrapper: releases _db_lock on close()."""
    def __init__(self, con):
        self._con = con

    def execute(self, *a, **k):
        return self._con.execute(*a, **k)

    def close(self):
        try:
            self._con.close()
        finally:
            try:
                _db_lock.release()
            except Exception:
                pass


class Store:
    def __init__(self, db_path=None):
        self.db_path = pathlib.Path(db_path or C.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self, retries=20):
        """Returns a connection; caller must close(). All DuckDB access is serialised in-process via _db_lock."""
        last = None
        _db_lock.acquire()
        for i in range(retries):
            try:
                con = duckdb.connect(str(self.db_path))
                con.execute(SCHEMA_SQL)
                return _LockedCon(con)
            except Exception as e:
                last = e
                time.sleep(0.5 + 0.25 * i)
        _db_lock.release()
        raise RuntimeError(f"duckdb connect failed: {last}")

    def existing_hashes(self, category, fn, ph):
        d = fn_dir(category, fn) / ph
        files = list(d.glob("*.parquet")) if d.exists() else []
        if not files:
            return None
        try:
            lf = pl.scan_parquet([str(f) for f in files])
            return lf.select(pl.col("_vake_row_hash")).unique().collect()
        except Exception as e:
            # a corrupt/partial part must never block the run: read valid parts one by one
            C.log(f"existing_hashes partial read ({fn}/{ph}): {e}", "WARN")
            parts = []
            for f in files:
                try:
                    parts.append(pl.read_parquet(f, columns=["_vake_row_hash"]))
                except Exception as e2:
                    C.log(f"unreadable part quarantined (kept on disk): {f} {e2}", "WARN")
            if parts:
                return pl.concat(parts).unique()
            return None

    def write_increment(self, category, fn, params, pdf, run_id, strategy="", window=("", "")):
        """Write only rows whose _vake_row_hash is not already stored. Returns (rows_fetched, rows_new, part_file)."""
        ph = param_hash(params)
        if pdf is None or pdf.height == 0:
            self._log_fetch(run_id, fn, ph, params, window, "EMPTY", 0, 0, 0.0, "", "")
            return 0, 0, None
        with series_lock(fn, ph):
            d = fn_dir(category, fn) / ph
            d.mkdir(parents=True, exist_ok=True)
            ex = self.existing_hashes(category, fn, ph)
            new = pdf
            if ex is not None and ex.height > 0:
                new = pdf.join(ex, on="_vake_row_hash", how="anti")
            new = new.unique(subset=["_vake_row_hash"], keep="first")
            part = None
            if new.height > 0:
                part = d / f"part_{C.stamp()}_{uuid.uuid4().hex[:6]}.parquet"
                tmp = part.with_suffix(".parquet.tmp")
                new.write_parquet(tmp, compression="zstd")
                tmp.replace(part)  # atomic: readers never see a half-written parquet
            self._update_manifest(category, fn, ph, params, strategy, run_id, "OK", "")
        return pdf.height, new.height, str(part) if part else None

    def _update_manifest(self, category, fn, ph, params, strategy, run_id, status, error):
        d = fn_dir(category, fn) / ph
        files = sorted(d.glob("*.parquet")) if d.exists() else []
        first_date = last_date = None
        rows_total = 0
        if files:
            try:
                agg = pl.scan_parquet([str(f) for f in files]).select(
                    pl.col("_vake_date").min().alias("mn"), pl.col("_vake_date").max().alias("mx"), pl.len().alias("n")).collect()
                first_date, last_date, rows_total = agg["mn"][0], agg["mx"][0], int(agg["n"][0])
            except Exception as e:
                C.log(f"manifest agg failed {fn}/{ph}: {e}", "WARN")
        con = self.connect()
        try:
            con.execute("INSERT OR REPLACE INTO vake_manifest VALUES (?,?,?,?,?,?,?,?,?,?,?,?,now())",
                        [fn, ph, category, json.dumps(params or {}, ensure_ascii=False, sort_keys=True, default=str), strategy,
                         first_date, last_date, rows_total, len(files), run_id, status, error[:500] if error else ""])
        finally:
            con.close()

    def mark_failed(self, category, fn, params, strategy, run_id, error, window=("", "")):
        ph = param_hash(params)
        with series_lock(fn, ph):
            self._update_manifest(category, fn, ph, params, strategy, run_id, "FAIL", str(error))
        self._log_fetch(run_id, fn, ph, params, window, "FAIL", 0, 0, 0.0, str(error), "")

    def mark_empty(self, category, fn, params, strategy, run_id):
        ph = param_hash(params)
        with series_lock(fn, ph):
            self._update_manifest(category, fn, ph, params, strategy, run_id, "EMPTY", "")

    def _log_fetch(self, run_id, fn, ph, params, window, status, rows_fetched, rows_new, elapsed, error, part):
        con = self.connect()
        try:
            con.execute("INSERT INTO vake_fetch_log VALUES (?,?,?,?,?,?,now(),?,?,?,?,?,?)",
                        [run_id, fn, ph, json.dumps(params or {}, ensure_ascii=False, sort_keys=True, default=str),
                         str(window[0] or ""), str(window[1] or ""), status, int(rows_fetched), int(rows_new), float(elapsed),
                         str(error)[:800] if error else "", part or ""])
        finally:
            con.close()

    def log_fetch(self, *a, **k):
        return self._log_fetch(*a, **k)

    def manifest(self):
        con = self.connect()
        try:
            rows = con.execute("SELECT fn, param_hash, category, params_json, strategy, first_date, last_date, rows_total, parts, last_run, last_status, last_error, updated_at FROM vake_manifest").fetchall()
        finally:
            con.close()
        cols = ["fn", "param_hash", "category", "params_json", "strategy", "first_date", "last_date", "rows_total", "parts", "last_run", "last_status", "last_error", "updated_at"]
        return [dict(zip(cols, [str(v) if isinstance(v, (datetime.date, datetime.datetime)) else v for v in r])) for r in rows]

    def manifest_by_fn(self):
        out = {}
        for m in self.manifest():
            f = out.setdefault(m["fn"], {"series": 0, "rows_total": 0, "last_date": None, "last_status": "", "last_run": None})
            f["series"] += 1
            f["rows_total"] += int(m["rows_total"] or 0)
            if m["last_date"] and (f["last_date"] is None or m["last_date"] > f["last_date"]):
                f["last_date"] = m["last_date"]
            if m["last_status"] == "FAIL":
                f["last_status"] = "FAIL"
            elif not f["last_status"]:
                f["last_status"] = m["last_status"]
            f["last_run"] = max(f["last_run"] or "", m["last_run"] or "")
        return out

    def last_date_for(self, fn, ph):
        con = self.connect()
        try:
            r = con.execute("SELECT last_date FROM vake_manifest WHERE fn=? AND param_hash=?", [fn, ph]).fetchone()
        finally:
            con.close()
        return r[0] if r and r[0] else None

    def run_begin(self, run_id, mode, selected, tasks):
        con = self.connect()
        try:
            con.execute("INSERT OR REPLACE INTO vake_runs VALUES (?,now(),NULL,?,?,?,0,0,0,0,0,'')", [run_id, mode, selected, tasks])
        finally:
            con.close()

    def run_end(self, run_id, ok, fail, skipped, rows_fetched, rows_new, note=""):
        con = self.connect()
        try:
            con.execute("UPDATE vake_runs SET finished=now(), ok=?, fail=?, skipped=?, rows_fetched=?, rows_new=?, note=? WHERE run_id=?",
                        [ok, fail, skipped, rows_fetched, rows_new, note, run_id])
        finally:
            con.close()

    def refresh_views(self):
        """CREATE OR REPLACE VIEW v_<fn> over all parquet parts of that function (union_by_name)."""
        n = 0
        con = self.connect()
        try:
            for cat_dir in sorted(C.DIR_STORE.glob("*")):
                if not cat_dir.is_dir():
                    continue
                for fdir in sorted(cat_dir.glob("*")):
                    if not fdir.is_dir() or not any(fdir.rglob("*.parquet")):
                        continue
                    glob = str(fdir / "**" / "*.parquet").replace("\\", "/")
                    view = "v_" + _safe(fdir.name)
                    try:
                        con.execute(f'CREATE OR REPLACE VIEW "{view}" AS SELECT * FROM read_parquet(\'{glob}\', union_by_name=true)')
                        n += 1
                    except Exception as e:
                        C.log(f"view {view} failed: {e}", "WARN")
        finally:
            con.close()
        C.log(f"duckdb views refreshed: {n}")
        return n

    # ---------------------------------------------------------- freshness / universe / compaction
    def fresh_within(self, fn, ph, hours):
        con = self.connect()
        try:
            r = con.execute("SELECT updated_at, last_status FROM vake_manifest WHERE fn=? AND param_hash=?", [fn, ph]).fetchone()
        finally:
            con.close()
        if not r or not r[0] or r[1] != "OK":
            return False
        return (datetime.datetime.now() - r[0]).total_seconds() < hours * 3600

    def universe_get(self, kind, ttl_hours):
        con = self.connect()
        try:
            r = con.execute("SELECT max(fetched_at) FROM vake_universe WHERE kind=?", [kind]).fetchone()
            if not r or not r[0] or (datetime.datetime.now() - r[0]).total_seconds() > ttl_hours * 3600:
                return None
            rows = con.execute("SELECT code, name FROM vake_universe WHERE kind=? AND fetched_at=? ORDER BY code", [kind, r[0]]).fetchall()
        finally:
            con.close()
        return [list(x) for x in rows]

    def universe_put(self, kind, rows):
        con = self.connect()
        try:
            ts = datetime.datetime.now()
            con.execute("DELETE FROM vake_universe WHERE kind=? AND fetched_at < ?", [kind, ts - datetime.timedelta(days=7)])
            con.executemany("INSERT INTO vake_universe VALUES (?,?,?,?)", [(kind, c, n, ts) for c, n in rows])
        finally:
            con.close()

    def compact(self, min_parts=8, category=None, fn_filter=None):
        """Merge many small parts of one series into a single consolidated part. Append-only: the old parts are MOVED to
        _archive/compact_<stamp>/ (never deleted). Returns list of (fn, ph, parts_before, rows)."""
        done = []
        for cat_dir in sorted(C.DIR_STORE.glob("*")):
            if not cat_dir.is_dir() or (category and cat_dir.name != category):
                continue
            for fdir in sorted(cat_dir.glob("*")):
                if not fdir.is_dir() or (fn_filter and fdir.name != fn_filter):
                    continue
                for pdir in sorted(fdir.glob("*")):
                    if not pdir.is_dir():
                        continue
                    parts = sorted(pdir.glob("part_*.parquet"))
                    if len(parts) < min_parts:
                        continue
                    with series_lock(fdir.name, pdir.name):
                        try:
                            df = pl.read_parquet([str(p) for p in parts], use_pyarrow=False).unique(subset=["_vake_row_hash"], keep="first")
                        except Exception:
                            frames = []
                            for p in parts:
                                try:
                                    frames.append(pl.read_parquet(p))
                                except Exception as e:
                                    C.log(f"compact skip unreadable {p}: {e}", "WARN")
                            if not frames:
                                continue
                            df = pl.concat(frames, how="diagonal_relaxed").unique(subset=["_vake_row_hash"], keep="first")
                        arc = C.DIR_ARCHIVE / f"compact_{C.stamp()}" / cat_dir.name / fdir.name / pdir.name
                        arc.mkdir(parents=True, exist_ok=True)
                        new = pdir / f"part_{C.stamp()}_compact.parquet"
                        tmp = new.with_suffix(".parquet.tmp")
                        df.write_parquet(tmp, compression="zstd")
                        tmp.replace(new)
                        for p in parts:
                            p.replace(arc / p.name)
                        con = self.connect()
                        try:
                            con.execute("INSERT INTO vake_compactions VALUES (?,?,now(),?,?,?)", [fdir.name, pdir.name, len(parts), df.height, str(arc)])
                        finally:
                            con.close()
                        self._update_manifest(cat_dir.name, fdir.name, pdir.name, json.loads(df["_vake_params"][0]) if "_vake_params" in df.columns else {}, "", "COMPACT", "OK", "")
                        done.append((fdir.name, pdir.name, len(parts), df.height))
                        C.log(f"compacted {fdir.name}/{pdir.name}: {len(parts)} parts -> 1 ({df.height} rows), old parts archived")
        return done

    def summary(self):
        con = self.connect()
        try:
            runs = con.execute("SELECT run_id, started, finished, mode, selected, tasks, ok, fail, skipped, rows_fetched, rows_new FROM vake_runs ORDER BY started DESC LIMIT 30").fetchall()
            tot = con.execute("SELECT count(*), coalesce(sum(rows_total),0), count(DISTINCT fn) FROM vake_manifest").fetchone()
        finally:
            con.close()
        return {"runs": [[str(x) for x in r] for r in runs], "series": tot[0], "rows_total": int(tot[1]), "functions": tot[2]}

# ====================================================================================================
# SECTION VAKE_UNIVERSE
# ====================================================================================================
"""VAKE symbol universes: code lists (A-share / HK / US / ETF / fund / index / boards / bonds / futures)
fetched ONCE per TTL via AKShare and cached in DuckDB (vake_universe) -> populates SYMBOL dropdowns without
re-hitting upstream on every page load (traffic saver)."""
import datetime

PROVIDERS = {
    "stock_a": ("stock_info_a_code_name", "code", "name"),
    "stock_b": ("stock_zh_b_spot_em", "代码", "名称"),
    "hk": ("stock_hk_spot_em", "代码", "名称"),
    "us": ("stock_us_spot_em", "代码", "名称"),
    "etf": ("fund_etf_spot_em", "代码", "名称"),
    "lof": ("fund_lof_spot_em", "代码", "名称"),
    "fund": ("fund_name_em", "基金代码", "基金简称"),
    "index": ("index_stock_info", "index_code", "display_name"),
    "board_industry": ("stock_board_industry_name_em", "板块名称", "板块代码"),
    "board_concept": ("stock_board_concept_name_em", "板块名称", "板块代码"),
    "bond_cb": ("bond_zh_cov", "债券代码", "债券简称"),
    "futures": ("futures_display_main_sina", "symbol", "name"),
    "option": ("option_finance_board", "合约交易代码", "合约交易代码"),
}
TTL_HOURS = 24


def get_universe(kind, refresh=False):
    if kind not in PROVIDERS:
        return {"kind": kind, "rows": [], "error": "unknown universe kind"}
    st = S.Store()
    if not refresh:
        cached = st.universe_get(kind, TTL_HOURS)
        if cached:
            return {"kind": kind, "rows": cached, "cached": True}
    fn, ccol, ncol = PROVIDERS[kind]
    try:
        import akshare as ak
        df = getattr(ak, fn)()
        cols = list(df.columns)
        if ccol not in cols:
            ccol = cols[0]
        if ncol not in cols:
            ncol = cols[1] if len(cols) > 1 else cols[0]
        rows = [(str(c), str(n)) for c, n in zip(df[ccol].tolist(), df[ncol].tolist())]
        st.universe_put(kind, rows)
        C.log(f"universe {kind} refreshed via {fn}: {len(rows)} codes")
        return {"kind": kind, "rows": rows, "cached": False, "source": fn}
    except Exception as e:
        C.log(f"universe {kind} failed: {e}", "WARN")
        stale = st.universe_get(kind, 24 * 365)
        return {"kind": kind, "rows": stale or [], "error": str(e), "stale": bool(stale)}

# ====================================================================================================
# SECTION VAKE_FETCH
# ====================================================================================================
"""VAKE batch fetch engine v0200
selection JSON
  {"fns": [...], "start_date": "2020-01-01", "mode": "incremental"|"backfill", "workers": 4, "max_combos": 600,
   "overrides": {"stock_zh_a_hist": {"symbol": ["000001","600519"], "adjust": "qfq"}},   # console dropdowns
   "batch_rows": 20000, "snapshot_ttl_hours": 12}

Traffic-saving design
  * one SERIES task per (fn, params) — its date windows run NEWEST -> OLDEST inside one worker
  * incremental early-stop: a window that yields 0 new rows (all hashes already stored) ends the series,
    so only the fresh tail is ever downloaded; the -3 day overlap catches late revisions
  * FULL_SNAPSHOT series are skipped when the manifest shows a successful fetch within snapshot_ttl_hours
  * fixed-quantity batching: rows accumulate per series and flush to ONE parquet part every batch_rows
    (or at series end) -> few large parts instead of one tiny part per window
"""
import datetime, time, random, threading, json, pathlib, concurrent.futures as cf
import polars as pl

STATE = {"run_id": None, "status": "idle", "total": 0, "done": 0, "ok": 0, "fail": 0, "empty": 0, "skipped_fresh": 0,
         "calls": 0, "calls_saved": 0, "rows_fetched": 0, "rows_new": 0, "current": [], "tasks": [], "started": None,
         "finished": None, "cancel": False, "message": ""}
_state_lock = threading.Lock()
_ak = None


def _akshare():
    global _ak
    if _ak is None:
        import akshare
        _ak = akshare
    return _ak


def _parse_date(s, default=None):
    if not s:
        return default
    if isinstance(s, datetime.datetime):
        return s.date()
    if isinstance(s, datetime.date):
        return s
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y-%m", "%Y%m", "%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return default


def _windows(r, start, today, mode):
    """Newest-first list of kwargs-fragments for the date params of one series."""
    strat, dp, fmt = r["strategy"], r["date_params"], r["date_fmt"]
    out = []
    if strat == "DATE_RANGE":
        win = r.get("window_days") or 36500
        end = today
        while end >= start:
            b = max(start, end - datetime.timedelta(days=win - 1))
            out.append(({dp["start"]: b.strftime(fmt), dp["end"]: end.strftime(fmt)}, (str(b), str(end))))
            end = b - datetime.timedelta(days=1)
    elif strat == "SINGLE_DATE":
        step = "month" if fmt in ("%Y-%m", "%Y%m") else ("year" if fmt == "%Y" else "day")
        d, n = today, 0
        while d >= start and n < C.MAX_SINGLE_DATE_CALLS:
            if not (step == "day" and d.weekday() >= 5):
                out.append(({dp["date"]: d.strftime(fmt)}, (str(d), str(d))))
                n += 1
            if step == "day":
                d -= datetime.timedelta(days=1)
            elif step == "month":
                d = (d.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
            else:
                d = d.replace(year=d.year - 1, month=12, day=31)
    elif strat == "YEAR":
        for y in range(today.year, start.year - 1, -1):
            out.append(({dp["year"]: str(y)}, (str(y), str(y))))
    else:
        out.append(({}, ("", "")))
    return out


def plan_series(selection, registry, store):
    reg = registry["registry"]
    start_default = _parse_date(selection.get("start_date"), datetime.date(2015, 1, 1))
    today = datetime.date.today()
    mode = selection.get("mode", "incremental")
    max_combos = int(selection.get("max_combos") or C.MAX_ENUM_COMBOS)
    ttl = float(selection.get("snapshot_ttl_hours", C.SNAPSHOT_TTL_HOURS))
    overrides_all = selection.get("overrides") or {}
    series, skipped = [], []
    for fn in selection.get("fns", []):
        r = reg.get(fn)
        if not r:
            skipped.append({"fn": fn, "reason": "not in registry"})
            continue
        if not r.get("has_ast"):
            skipped.append({"fn": fn, "reason": "not present in installed akshare"})
            continue
        ov = overrides_all.get(fn) or None
        for params in R.expand_params(r, max_combos, overrides=ov):
            params = {k: v for k, v in params.items() if k not in r["date_params"].values()}
            missing = [p["name"] for p in r.get("param_specs", []) if p.get("required") and p["kind"] not in ("DATE", "TECH") and p["name"] not in params]
            if missing:
                skipped.append({"fn": fn, "reason": f"required params missing: {missing}"})
                continue
            ph = S.param_hash(params)
            start = start_default
            if mode == "incremental" and r["strategy"] != "FULL_SNAPSHOT":
                ld = _parse_date(store.last_date_for(fn, ph))
                if ld and ld - datetime.timedelta(days=C.OVERLAP_DAYS) > start:
                    start = ld - datetime.timedelta(days=C.OVERLAP_DAYS)
            if r["strategy"] == "FULL_SNAPSHOT" and mode == "incremental" and ttl > 0 and store.fresh_within(fn, ph, ttl):
                series.append({"fn": fn, "category": r["category"], "strategy": r["strategy"], "params": params, "ph": ph,
                               "windows": [], "skip_fresh": True})
                continue
            wins = _windows(r, start, today, mode)
            series.append({"fn": fn, "category": r["category"], "strategy": r["strategy"], "params": params, "ph": ph,
                           "windows": wins, "skip_fresh": False, "early_stop": mode == "incremental"})
    return series, skipped


def _call(fn, kwargs, retries=3):
    ak = _akshare()
    f = getattr(ak, fn)
    last = None
    for i in range(retries):
        try:
            return f(**kwargs)
        except Exception as e:
            last = e
            msg = str(e)
            if "unexpected keyword" in msg or "positional argument" in msg or "does not accept" in msg:
                raise
            time.sleep((1.5 ** i) + random.random() * 0.8)
    raise last


def _set(**kw):
    with _state_lock:
        STATE.update(kw)


class _Batch:
    """Fixed-quantity buffer: flush one parquet part every `limit` rows (or on close)."""
    def __init__(self, store, sr, run_id, limit):
        self.store, self.sr, self.run_id, self.limit = store, sr, run_id, limit
        self.frames, self.rows, self.fetched, self.new_total, self.parts = [], 0, 0, 0, []

    def add(self, ndf):
        if ndf is None or ndf.height == 0:
            return
        self.frames.append(ndf)
        self.rows += ndf.height
        self.fetched += ndf.height
        if self.rows >= self.limit:
            return self.flush()
        return None

    def flush(self, window=("", "")):
        if not self.frames:
            return 0
        df = pl.concat(self.frames, how="diagonal_relaxed") if len(self.frames) > 1 else self.frames[0]
        self.frames, self.rows = [], 0
        fetched, new, part = self.store.write_increment(self.sr["category"], self.sr["fn"], self.sr["params"], df, self.run_id, self.sr["strategy"], window)
        self.new_total += new
        if part:
            self.parts.append(part)
        return new


def run_selection(selection, registry=None, run_id=None, progress_cb=None):
    registry = registry or R.load_registry()
    store = S.Store()
    run_id = run_id or f"RUN_{C.stamp()}"
    run_dir = C.DIR_RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    C.write_json(run_dir / "selection.json", selection)
    series, skipped = plan_series(selection, registry, store)
    batch_rows = int(selection.get("batch_rows") or C.BATCH_ROWS)
    with _state_lock:
        STATE.update({"run_id": run_id, "status": "running", "total": len(series), "done": 0, "ok": 0, "fail": 0, "empty": 0,
                      "skipped_fresh": 0, "calls": 0, "calls_saved": 0, "rows_fetched": 0, "rows_new": 0, "current": [],
                      "started": C.now_iso(), "finished": None, "cancel": False,
                      "message": f"{len(series)} series planned ({sum(len(s['windows']) for s in series)} windows max), {len(skipped)} skipped",
                      "tasks": [{"key": f"{s['fn']}|{s['ph']}", "fn": s["fn"], "params": s["params"], "status": "FRESH" if s["skip_fresh"] else "PENDING",
                                 "windows": len(s["windows"]), "calls": 0, "rows": 0, "new": 0, "parts": 0, "sec": 0.0, "err": ""} for s in series]})
    idx = {t["key"]: i for i, t in enumerate(STATE["tasks"])}
    store.run_begin(run_id, selection.get("mode", "incremental"), len(selection.get("fns", [])), len(series))
    C.log(f"run start: {len(series)} series / {len(selection.get('fns', []))} fns / skipped {len(skipped)} / batch_rows {batch_rows}", run_id=run_id)
    workers = int(selection.get("workers") or C.DEFAULT_WORKERS)

    def upd(key, **kw):
        with _state_lock:
            STATE["tasks"][idx[key]].update(kw)

    def work(sr):
        key = f"{sr['fn']}|{sr['ph']}"
        if sr["skip_fresh"]:
            with _state_lock:
                STATE["skipped_fresh"] += 1
                STATE["calls_saved"] += 1
                STATE["done"] += 1
            return
        if STATE["cancel"]:
            upd(key, status="CANCELLED")
            with _state_lock:
                STATE["done"] += 1
            return
        t0 = time.time()
        upd(key, status="RUNNING")
        with _state_lock:
            STATE["current"] = [x["fn"] for x in STATE["tasks"] if x["status"] == "RUNNING"][:8]
        batch = _Batch(store, sr, run_id, batch_rows)
        calls, err, stopped_early = 0, "", 0
        try:
            for i, (frag, window) in enumerate(sr["windows"]):
                if STATE["cancel"]:
                    break
                kw = dict(sr["params"])
                kw.update(frag)
                raw = _call(sr["fn"], kw)
                calls += 1
                with _state_lock:
                    STATE["calls"] += 1
                pdf = S.to_polars(raw)
                ndf = S.normalize(pdf, sr["fn"], sr["params"])
                fetched = ndf.height if ndf is not None else 0
                # early stop needs the dedupe result of THIS window -> flush per window when checking
                if sr.get("early_stop") and sr["strategy"] != "FULL_SNAPSHOT" and i < len(sr["windows"]) - 1:
                    batch.add(ndf)
                    new = batch.flush(window)
                    upd(key, calls=calls, rows=batch.fetched, new=batch.new_total, parts=len(batch.parts))
                    if fetched > 0 and new == 0:
                        stopped_early = len(sr["windows"]) - i - 1
                        with _state_lock:
                            STATE["calls_saved"] += stopped_early
                        C.log(f"early-stop {sr['fn']} {sr['params']} at {window}: {stopped_early} older windows already stored", run_id=run_id)
                        break
                else:
                    batch.add(ndf)
                    upd(key, calls=calls, rows=batch.fetched, new=batch.new_total, parts=len(batch.parts))
            batch.flush(sr["windows"][-1][1] if sr["windows"] else ("", ""))
            el = time.time() - t0
            status = "OK" if batch.fetched else "EMPTY"
            store.log_fetch(run_id, sr["fn"], sr["ph"], sr["params"], (sr["windows"][-1][1][0] if sr["windows"] else "", sr["windows"][0][1][1] if sr["windows"] else ""),
                            status, batch.fetched, batch.new_total, el, f"early_stop={stopped_early}" if stopped_early else "", ";".join(batch.parts))
            if not batch.fetched:
                store.mark_empty(sr["category"], sr["fn"], sr["params"], sr["strategy"], run_id)
            upd(key, status=status, calls=calls, rows=batch.fetched, new=batch.new_total, parts=len(batch.parts), sec=round(el, 2))
            with _state_lock:
                STATE["ok" if batch.fetched else "empty"] += 1
                STATE["rows_fetched"] += batch.fetched
                STATE["rows_new"] += batch.new_total
            C.log(f"{status} {sr['fn']} {sr['params']} calls={calls} rows={batch.fetched} new={batch.new_total} parts={len(batch.parts)} {el:.1f}s", run_id=run_id)
        except Exception as e:
            el = time.time() - t0
            err = f"{type(e).__name__}: {e}"
            try:
                batch.flush()
                store.mark_failed(sr["category"], sr["fn"], sr["params"], sr["strategy"], run_id, err)
            except Exception as e2:
                C.log(f"mark_failed error: {e2}", "WARN", run_id)
            upd(key, status="FAIL", calls=calls, rows=batch.fetched, new=batch.new_total, sec=round(el, 2), err=err[:300])
            with _state_lock:
                STATE["fail"] += 1
                STATE["rows_new"] += batch.new_total
            C.log(f"FAIL {sr['fn']} {sr['params']} {err}", "WARN", run_id)
        finally:
            with _state_lock:
                STATE["done"] += 1
                STATE["current"] = [x["fn"] for x in STATE["tasks"] if x["status"] == "RUNNING"][:8]
            if progress_cb:
                try:
                    progress_cb(dict(STATE))
                except Exception:
                    pass
            if STATE["done"] % 10 == 0 or STATE["done"] == STATE["total"]:
                _write_progress(run_dir)

    with cf.ThreadPoolExecutor(max_workers=workers, thread_name_prefix="vake") as ex:
        list(ex.map(work, series))
    with _state_lock:
        STATE["status"] = "cancelled" if STATE["cancel"] else "finished"
        STATE["finished"] = C.now_iso()
    store.run_end(run_id, STATE["ok"], STATE["fail"], len(skipped) + STATE["skipped_fresh"], STATE["rows_fetched"], STATE["rows_new"],
                  f"{STATE['status']} calls={STATE['calls']} saved={STATE['calls_saved']}")
    try:
        store.refresh_views()
    except Exception as e:
        C.log(f"refresh_views failed: {e}", "WARN", run_id)
    _write_progress(run_dir)
    report = write_report(run_dir, skipped, selection)
    C.log(f"run {STATE['status']}: ok={STATE['ok']} empty={STATE['empty']} fail={STATE['fail']} fresh-skip={STATE['skipped_fresh']} calls={STATE['calls']} saved={STATE['calls_saved']} rows_new={STATE['rows_new']} report={report}", run_id=run_id)
    return dict(STATE), report


def _write_progress(run_dir):
    try:
        with _state_lock:
            snap = dict(STATE)
        with open(run_dir / "progress.json", "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, default=str)
    except Exception:
        pass


def write_report(run_dir, skipped, selection):
    s = dict(STATE)
    rows = "".join(
        f"<tr class='{t['status']}'><td>{i+1}</td><td>{t['fn']}</td><td class='p'>{json.dumps(t['params'], ensure_ascii=False)}</td>"
        f"<td>{t['status']}</td><td>{t['windows']}</td><td>{t['calls']}</td><td>{t['rows']}</td><td>{t['new']}</td><td>{t['parts']}</td><td>{t['sec']}</td><td class='e'>{t['err']}</td></tr>"
        for i, t in enumerate(s["tasks"]))
    sk = "".join(f"<li><b>{x['fn']}</b> — {x['reason']}</li>" for x in skipped) or "<li>—</li>"
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VAKE Run {s['run_id']}</title>
<style>body{{font-family:'Segoe UI',Microsoft JhengHei,sans-serif;background:#0f1419;color:#e6e6e6;margin:0;padding:24px}}
h1{{font-size:20px;margin:0 0 4px}} .sub{{color:#8a94a6;font-size:12px;margin-bottom:16px}}
.kpi{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}} .k{{background:#182029;border:1px solid #2b3542;border-radius:8px;padding:10px 16px;min-width:110px}}
.k b{{display:block;font-size:22px}} .k span{{font-size:11px;color:#8a94a6}}
table{{border-collapse:collapse;width:100%;font-size:12px}} th,td{{border-bottom:1px solid #222b36;padding:5px 8px;text-align:left;vertical-align:top}}
th{{background:#182029;position:sticky;top:0}} tr.OK td:nth-child(4){{color:{C.TW_RED};font-weight:600}} tr.FAIL td:nth-child(4){{color:{C.TW_GREEN};font-weight:600}}
tr.EMPTY td:nth-child(4),tr.FRESH td:nth-child(4){{color:#8a94a6}} td.p,td.e{{font-family:Consolas,monospace;font-size:11px;color:#b8c2cc;max-width:520px;word-break:break-all}}
.seal{{margin-top:20px;font-size:11px;color:#8a94a6;border-top:1px dashed #2b3542;padding-top:10px}}</style></head><body>
<h1>VAKE 批次擷取報告 · {s['run_id']}</h1><div class="sub">{C.ENGINE_NAME} {C.VAKE_VERSION} · mode={selection.get('mode')} · start_date={selection.get('start_date')} · batch_rows={selection.get('batch_rows', C.BATCH_ROWS)} · {s['started']} → {s['finished']} · status={s['status']}</div>
<div class="kpi"><div class="k"><b>{s['total']}</b><span>series</span></div><div class="k"><b style="color:{C.TW_RED}">{s['ok']}</b><span>OK</span></div>
<div class="k"><b>{s['empty']}</b><span>EMPTY</span></div><div class="k"><b style="color:{C.TW_GREEN}">{s['fail']}</b><span>FAIL</span></div><div class="k"><b>{s['skipped_fresh']}</b><span>fresh-skip (TTL)</span></div>
<div class="k"><b>{s['calls']}</b><span>upstream calls</span></div><div class="k"><b>{s['calls_saved']}</b><span>calls saved (early-stop+TTL)</span></div>
<div class="k"><b>{s['rows_fetched']:,}</b><span>rows fetched</span></div><div class="k"><b>{s['rows_new']:,}</b><span>rows NEW (append-only)</span></div></div>
<h3>Skipped</h3><ul>{sk}</ul>
<table><thead><tr><th>#</th><th>function</th><th>params</th><th>status</th><th>windows</th><th>calls</th><th>rows</th><th>new</th><th>parts</th><th>sec</th><th>error</th></tr></thead><tbody>{rows}</tbody></table>
<div class="seal">Store: {C.DIR_STORE} · DuckDB: {C.DB_PATH} (views v_&lt;fn&gt;) · newest-first windows + early-stop + row-hash anti-join; parquet parts never rewritten (compaction archives, never deletes).</div>
</body></html>"""
    p = run_dir / "report.html"
    p.write_text(html, encoding="utf-8")
    return str(p)

# ====================================================================================================
# SECTION VAKE_SERVER
# ====================================================================================================
"""VAKE local console: http://127.0.0.1:<port>/  (stdlib only, no external web framework)
- tree picker (category -> heading -> interface) with checkboxes, search, strategy/last_date badges
- start date -> latest incremental run, live progress polling, cancel
- save selection as the scheduled-task default, DuckDB read-only SQL console, run history
"""
import json, threading, urllib.parse, socket, webbrowser, pathlib, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

_registry_cache = {"data": None, "ts": 0}
_run_thread = {"t": None}


def registry_lite():
    reg = R.load_registry()
    lite = {}
    for fn, r in reg.get("registry", {}).items():
        lite[fn] = {"title": r.get("title") or fn, "desc": (r.get("desc") or r.get("doc_first") or "")[:160],
                    "strategy": r.get("strategy"), "combos": r.get("enum_combos", 1), "window": r.get("window_days"),
                    "has_ast": r.get("has_ast"), "has_docs": r.get("has_docs"), "runnable": r.get("runnable"),
                    "params": [p["name"] for p in r.get("ast_params", [])], "limit": (r.get("limit") or "")[:80],
                    "category": r.get("category"), "module": r.get("module"),
                    "specs": [{"name": p["name"], "kind": p["kind"], "default": p.get("default"), "universe": p.get("universe"),
                               "candidates": p.get("candidates", [])[:200], "more": len(p.get("candidates", [])) > 200,
                               "desc": (p.get("desc") or "")[:120], "required": p.get("required", False)} for p in r.get("param_specs", [])],
                    "all_selectable": all(p["kind"] != "FREE" or p.get("candidates") for p in r.get("param_specs", []))}
    return {"tree": reg.get("tree", {}), "fns": lite, "stats": reg.get("stats", {}), "akshare_version": reg.get("akshare_version"),
            "generated_at": reg.get("generated_at")}


def _json(handler, obj, code=200):
    body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _html(handler, text, code=200):
    body = text.encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return {}

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/":
                return _html(self, PAGE.replace("__PORT__", str(self.server.server_address[1])).replace("__ROOT__", str(C.ROOT).replace("\\", "\\\\")))
            if u.path == "/api/registry":
                now = time.time()
                if _registry_cache["data"] is None or now - _registry_cache["ts"] > 30:
                    _registry_cache["data"] = registry_lite()
                    _registry_cache["ts"] = now
                d = dict(_registry_cache["data"])
                st = S.Store()
                d["manifest"] = st.manifest_by_fn()
                d["summary"] = st.summary()
                d["default_selection"] = C.read_json(C.DEFAULT_SELECTION, None)
                return _json(self, d)
            if u.path == "/api/status":
                with F._state_lock:
                    snap = dict(F.STATE)
                tasks = snap.get("tasks", [])
                running = [t for t in tasks if t["status"] == "RUNNING"]
                fails = [t for t in tasks if t["status"] == "FAIL"][-80:]
                done = [t for t in tasks if t["status"] in ("OK", "EMPTY", "FRESH")][-120:]
                snap["tasks"] = running + fails + done
                snap["tasks_total_listed"] = len(tasks)
                return _json(self, snap)
            if u.path == "/api/selection":
                return _json(self, C.read_json(C.DEFAULT_SELECTION, {}))
            if u.path == "/api/sql":
                sql = (q.get("q") or [""])[0].strip().rstrip(";")
                if not sql.lower().startswith(("select", "with", "show", "describe", "pragma")):
                    return _json(self, {"error": "read-only console: SELECT / WITH / SHOW / DESCRIBE only"}, 400)
                con = S.Store().connect()
                try:
                    cur = con.execute(f"SELECT * FROM ({sql}) LIMIT 500") if sql.lower().startswith(("select", "with")) else con.execute(sql)
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
                finally:
                    con.close()
                return _json(self, {"columns": cols, "rows": rows})
            if u.path.startswith("/report/"):
                rid = pathlib.Path(u.path.split("/report/", 1)[1]).name
                p = C.DIR_RUNS / rid / "report.html"
                if p.exists():
                    return _html(self, p.read_text(encoding="utf-8"))
                return _html(self, "<h3>no report</h3>", 404)
            if u.path == "/api/universe":
                kind = (q.get("kind") or [""])[0]
                return _json(self, U.get_universe(kind, refresh=(q.get("refresh") or ["0"])[0] == "1"))
            if u.path == "/api/fn":
                name = (q.get("name") or [""])[0]
                r = R.load_registry().get("registry", {}).get(name)
                return _json(self, r or {"error": "unknown fn"}, 200 if r else 404)
            if u.path == "/api/params":
                reg = R.load_registry()
                free = [{"fn": fn, "param": p["name"], "kind": p["kind"], "desc": p.get("desc", "")} for fn, r in reg.get("registry", {}).items()
                        for p in r.get("param_specs", []) if p["kind"] == "FREE" and not p.get("candidates")]
                return _json(self, {"stats": reg.get("stats", {}), "free_without_candidates": free})
            if u.path == "/api/runs":
                return _json(self, S.Store().summary())
            return _json(self, {"error": "not found"}, 404)
        except Exception as e:
            C.log(f"GET {u.path} error: {e}", "WARN")
            return _json(self, {"error": str(e)}, 500)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        body = self._body()
        try:
            if u.path == "/api/run":
                if F.STATE.get("status") == "running":
                    return _json(self, {"error": "a run is already in progress", "run_id": F.STATE.get("run_id")}, 409)
                sel = {"fns": list(dict.fromkeys(body.get("fns", []))), "start_date": body.get("start_date") or "2015-01-01",
                       "mode": body.get("mode") or "incremental", "workers": int(body.get("workers") or C.DEFAULT_WORKERS),
                       "max_combos": int(body.get("max_combos") or C.MAX_ENUM_COMBOS), "overrides": body.get("overrides") or {},
                       "batch_rows": int(body.get("batch_rows") or C.BATCH_ROWS), "snapshot_ttl_hours": float(body.get("snapshot_ttl_hours", C.SNAPSHOT_TTL_HOURS))}
                if not sel["fns"]:
                    return _json(self, {"error": "no interfaces selected"}, 400)
                rid = f"RUN_{C.stamp()}"
                C.DIR_SELECTIONS.mkdir(parents=True, exist_ok=True)
                (C.DIR_SELECTIONS / f"selection_{rid}.json").write_text(json.dumps(sel, ensure_ascii=False, indent=1), encoding="utf-8")
                t = threading.Thread(target=F.run_selection, args=(sel, None, rid), daemon=True, name="vake-run")
                _run_thread["t"] = t
                t.start()
                return _json(self, {"run_id": rid, "fns": len(sel["fns"])})
            if u.path == "/api/cancel":
                F._set(cancel=True)
                return _json(self, {"ok": True})
            if u.path == "/api/selection/save":
                sel = {"fns": list(dict.fromkeys(body.get("fns", []))), "start_date": body.get("start_date") or "2015-01-01",
                       "mode": "incremental", "workers": int(body.get("workers") or C.DEFAULT_WORKERS),
                       "max_combos": int(body.get("max_combos") or C.MAX_ENUM_COMBOS), "overrides": body.get("overrides") or {},
                       "batch_rows": int(body.get("batch_rows") or C.BATCH_ROWS), "snapshot_ttl_hours": float(body.get("snapshot_ttl_hours", C.SNAPSHOT_TTL_HOURS)),
                       "saved_at": C.now_iso()}
                C.write_json(C.DEFAULT_SELECTION, sel)
                return _json(self, {"ok": True, "path": str(C.DEFAULT_SELECTION), "fns": len(sel["fns"])})
            if u.path == "/api/rescan":
                def job():
                    try:
                        A.build_ast_inventory()
                        K.build_knowledge(refresh=bool(body.get("refresh")))
                        R.build_registry()
                        _registry_cache["data"] = None
                    except Exception as e:
                        C.log(f"rescan failed: {e}", "WARN")
                threading.Thread(target=job, daemon=True).start()
                return _json(self, {"ok": True})
            if u.path == "/api/compact":
                done = S.Store().compact(min_parts=int(body.get("min_parts") or C.COMPACT_MIN_PARTS))
                S.Store().refresh_views()
                return _json(self, {"compacted": len(done), "series": [list(x) for x in done]})
            if u.path == "/api/refresh_views":
                return _json(self, {"views": S.Store().refresh_views()})
            return _json(self, {"error": "not found"}, 404)
        except Exception as e:
            C.log(f"POST {u.path} error: {e}", "WARN")
            return _json(self, {"error": str(e)}, 500)


def free_port(start):
    for p in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start


def serve(port=None, open_browser=True):
    C.ensure_dirs()
    port = free_port(int(port or C.DEFAULT_PORT))
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.daemon_threads = True
    url = f"http://127.0.0.1:{port}/"
    (C.DIR_LOGS / "server_url.txt").write_text(url, encoding="utf-8")
    C.log(f"VAKE console listening at {url}")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


PAGE = r"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VAKE · AKShare 超級擷取控制台</title>
<style>
:root{--bg:#0f1419;--panel:#161d26;--line:#26303c;--txt:#e6e9ee;--mut:#8a94a6;--acc:#d9a441;--red:#c96b5a;--grn:#5a9e6f;--blu:#5b8fd6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:13px 'Segoe UI','Microsoft JhengHei',sans-serif}
header{padding:14px 20px;border-bottom:1px solid var(--line);display:flex;gap:18px;align-items:center;flex-wrap:wrap}
header h1{font-size:16px;margin:0}header small{color:var(--mut)}.kpis{display:flex;gap:10px;margin-left:auto;flex-wrap:wrap}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:6px 12px;text-align:center}.kpi b{display:block;font-size:16px}.kpi span{font-size:10px;color:var(--mut)}
main{display:grid;grid-template-columns:minmax(420px,1fr) minmax(460px,1fr);gap:0;height:calc(100vh - 62px)}
.col{overflow:auto;padding:14px 18px;border-right:1px solid var(--line)}
.tools{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}
input[type=text],input[type=date],select{background:#0b1015;border:1px solid var(--line);color:var(--txt);padding:6px 8px;border-radius:4px}
button{background:#1f2a36;border:1px solid #33404f;color:var(--txt);padding:6px 12px;border-radius:4px;cursor:pointer}button:hover{border-color:var(--acc)}
button.primary{background:var(--acc);color:#111;font-weight:600;border-color:var(--acc)}button.danger{border-color:var(--grn)}
.node{margin-left:14px}.cat{margin-left:0}.row{display:flex;align-items:center;gap:6px;padding:3px 0}.row.h{font-weight:600}
.tog{width:14px;display:inline-block;color:var(--mut);cursor:pointer;user-select:none}.fn{font-family:Consolas,monospace;font-size:12px}
.b{font-size:10px;padding:1px 5px;border-radius:3px;border:1px solid var(--line);color:var(--mut)}
.b.DATE_RANGE{color:var(--blu);border-color:var(--blu)}.b.SINGLE_DATE{color:#b48ad6;border-color:#b48ad6}.b.YEAR{color:#d6a95b;border-color:#d6a95b}.b.FULL_SNAPSHOT{color:var(--mut)}
.b.ok{color:var(--red);border-color:var(--red)}.b.fail{color:var(--grn);border-color:var(--grn)}.b.na{color:#666;border-color:#444}
.t{color:var(--mut);font-size:11px;margin-left:4px}.hidden{display:none}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin-bottom:12px}
.card h3{margin:0 0 8px;font-size:13px;color:var(--acc)}
.bar{height:10px;background:#0b1015;border-radius:5px;overflow:hidden;border:1px solid var(--line)}.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--acc),var(--red));width:0;transition:width .4s}
table{border-collapse:collapse;width:100%;font-size:11px}th,td{border-bottom:1px solid var(--line);padding:3px 6px;text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600}
td.mono{font-family:Consolas,monospace;word-break:break-all}.OK{color:var(--red)}.FAIL{color:var(--grn)}.RUNNING{color:var(--acc)}.EMPTY,.PENDING{color:var(--mut)}
textarea{width:100%;background:#0b1015;border:1px solid var(--line);color:var(--txt);font-family:Consolas,monospace;font-size:12px;padding:6px;border-radius:4px}
.sel{color:var(--acc);font-weight:600}.foot{font-size:10px;color:var(--mut);margin-top:6px}
.pp{margin:2px 0 6px 44px;background:#0b1015;border:1px solid var(--line);border-radius:6px;padding:8px 10px;font-size:11px}
.pp .pr{display:flex;gap:8px;align-items:flex-start;padding:3px 0;border-bottom:1px dashed #1c2530}.pp .pn{min-width:110px;font-family:Consolas,monospace;color:var(--acc)}
.pp .pk{min-width:95px;color:var(--mut);font-size:10px}.pp .opts{display:flex;flex-wrap:wrap;gap:4px 10px;max-height:120px;overflow:auto;flex:1}
.pp label{white-space:nowrap}.pp input[type=text],.pp textarea{width:100%;background:#0f1419;border:1px solid var(--line);color:var(--txt);font-family:Consolas,monospace;font-size:11px;padding:3px}
.gear{cursor:pointer;color:var(--mut);margin-left:auto;font-size:12px}.gear.on{color:var(--acc)}
</style></head><body>
<header><h1>VAKE · AKShare 超級知識 &amp; 擷取控制台</h1><small id="meta">loading…</small>
<div class="kpis"><div class="kpi"><b id="k_fn">–</b><span>接口 (AST)</span></div><div class="kpi"><b id="k_doc">–</b><span>已文件化</span></div><div class="kpi"><b id="k_series">–</b><span>已存序列</span></div><div class="kpi"><b id="k_rows">–</b><span>Parquet 列數</span></div><div class="kpi"><b id="k_sel">0</b><span>已勾選</span></div></div></header>
<main>
<div class="col">
 <div class="tools"><input type="text" id="q" placeholder="搜尋 接口名 / 標題 / 描述…" style="flex:1;min-width:200px"><button onclick="expandAll(true)">全部展開</button><button onclick="expandAll(false)">全部收合</button><button onclick="checkVisible(true)">勾選可見</button><button onclick="checkVisible(false)">清除</button><label><input type="checkbox" id="onlyDoc" onchange="render()"> 只顯示已文件化</label><label><input type="checkbox" id="onlyStored" onchange="render()"> 只顯示已存</label></div>
 <div id="tree"></div>
</div>
<div class="col" style="border-right:0">
 <div class="card"><h3>增量維護 · 選定起始日 → 最新</h3>
  <div class="tools"><label>起始日 <input type="date" id="start" value="2020-01-01"></label>
   <button onclick="qd(1)">1Y</button><button onclick="qd(3)">3Y</button><button onclick="qd(5)">5Y</button><button onclick="qd(10)">10Y</button><button onclick="qd(30)">ALL</button>
   <label>模式 <select id="mode"><option value="incremental">增量 (manifest.last_date−3d → 今日)</option><option value="backfill">回補 (start → 今日, 仍去重)</option></select></label>
   <label>併發 <select id="workers"><option>2</option><option selected>4</option><option>6</option><option>8</option></select></label>
   <label>列舉上限 <input type="text" id="maxc" value="600" style="width:60px"></label>
   <label>批次列數 <input type="text" id="batch" value="20000" style="width:70px"></label><label>快照TTL(h) <input type="text" id="ttl" value="12" style="width:40px"></label></div>
  <div class="tools"><button class="primary" onclick="run()">▶ 執行擷取（勾選項 → 最新）</button><button onclick="saveSel()">💾 儲存為每日排程預設</button><button onclick="loadSel()">↺ 載入排程預設</button><button class="danger" onclick="cancel()">■ 取消</button><button onclick="rescan()">⟳ 重掃 AKShare (AST+Docs)</button></div>
  <div id="planNote" class="foot">左側每個接口按 ⚙ 展開參數面板：每個參數都是下拉/多選（DATE 由起始日控制；ENUM 多選展開組合；SYMBOL 可載入代碼宇宙）。擷取由最新往舊、增量遇到已存視窗即提前停止；FULL_SNAPSHOT 在 TTL 內不重抓；每 批次列數 寫一個 parquet part。</div>
 </div>
 <div class="card"><h3>進度 <span id="rid" class="t"></span></h3>
  <div class="bar"><i id="bar"></i></div>
  <div class="tools" style="margin-top:8px"><span id="prog">idle</span><span id="cur" class="t"></span><a id="rep" href="#" target="_blank" class="hidden">開啟報告 ↗</a></div>
  <div style="max-height:320px;overflow:auto"><table><thead><tr><th>fn</th><th>params</th><th>狀態</th><th>視窗</th><th>calls</th><th>rows</th><th>new</th><th>parts</th><th>sec</th><th>err</th></tr></thead><tbody id="tasks"></tbody></table></div>
 </div>
 <div class="card"><h3>DuckDB 管理台（唯讀 SQL · v_&lt;fn&gt; 視圖 / vake_manifest / vake_runs / vake_fetch_log）</h3>
  <textarea id="sql" rows="3">SELECT fn, category, strategy, first_date, last_date, rows_total, parts, last_status FROM vake_manifest ORDER BY last_date DESC NULLS LAST LIMIT 100</textarea>
  <div class="tools" style="margin-top:6px"><button onclick="sql()">執行</button><button onclick="document.getElementById('sql').value='SELECT run_id, started, finished, mode, tasks, ok, fail, rows_new FROM vake_runs ORDER BY started DESC'">runs</button><button onclick="document.getElementById('sql').value='SELECT fn, status, count(*) n, sum(rows_new) new_rows FROM vake_fetch_log GROUP BY 1,2 ORDER BY 1,2'">fetch_log</button><button onclick="refreshViews()">重建視圖</button><button onclick="compact()">壓實 parts (≥8→1, 舊 part 歸檔)</button><button onclick="paramsReport()">參數分類報告</button><span class="foot">DB: __ROOT__\db\vake.duckdb</span></div>
  <div style="max-height:300px;overflow:auto;margin-top:6px"><table><thead id="sqlh"></thead><tbody id="sqlb"></tbody></table></div>
 </div>
 <div class="card"><h3>最近執行</h3><table><thead><tr><th>run</th><th>started</th><th>mode</th><th>tasks</th><th>ok</th><th>fail</th><th>new</th><th></th></tr></thead><tbody id="runs"></tbody></table></div>
</div></main>
<script>
let REG=null, checked=new Set(), openSet=new Set(), pollT=null, OV={}, OPEN_P=new Set(), UNI={};
function togP(fn){OPEN_P.has(fn)?OPEN_P.delete(fn):OPEN_P.add(fn);render();}
function ovGet(fn,p){return (OV[fn]||{})[p];}
function ovSet(fn,p,v){OV[fn]=OV[fn]||{};if(v===undefined||v===null||(Array.isArray(v)&&!v.length)){delete OV[fn][p];}else{OV[fn][p]=v;}}
function esc(v){return String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
function renderParams(fn){const f=REG.fns[fn];let h='<div class="pp">';
 for(const p of f.specs){if(p.kind==='TECH')continue;let body='';const cur=ovGet(fn,p.name);
  if(p.kind==='DATE'){body=`<span class="t">由「起始日 → 最新」與策略 ${f.strategy} 自動切片</span>`;}
  else if(p.kind==='SYMBOL'){const u=UNI[p.universe];const sel=Array.isArray(cur)?cur:(cur!==undefined?[cur]:(p.default!==null&&p.default!==undefined?[String(p.default)]:[]));
   body=`<div style="flex:1"><div class="tools" style="margin:0 0 4px"><button onclick="loadUni('${fn}','${p.name}','${p.universe}',0)">載入宇宙 ${p.universe}${u?` (${u.length})`:''}</button><button onclick="loadUni('${fn}','${p.name}','${p.universe}',1)">刷新</button>${u?`<button onclick="pickUni('${fn}','${p.name}','${p.universe}','all')">全部</button><button onclick="pickUni('${fn}','${p.name}','${p.universe}',50)">前50</button><input type="text" placeholder="篩選代碼/名稱" oninput="filterUni('${fn}','${p.name}','${p.universe}',this.value)" style="width:120px">`:''}</div>
   <textarea rows="2" onchange="ovSet('${fn}','${p.name}',this.value.split(/[\s,，;]+/).filter(Boolean))" placeholder="代碼，逗號分隔">${esc(sel.join(','))}</textarea>${u?`<select multiple size="4" style="width:100%;background:#0f1419;color:var(--txt);border:1px solid var(--line);margin-top:3px" id="uni_${fn}_${p.name}" onchange="uniSel('${fn}','${p.name}',this)">${u.slice(0,3000).map(r=>`<option value="${esc(r[0])}" ${sel.includes(String(r[0]))?'selected':''}>${esc(r[0])} ${esc(r[1])}</option>`).join('')}</select>`:''}</div>`;}
  else if(p.kind.startsWith('ENUM')){const sel=Array.isArray(cur)?cur:(cur!==undefined?[cur]:(p.default!==null&&p.default!==undefined?[String(p.default)]:(p.candidates.length?[String(p.candidates[0])]:[])));
   body=`<div class="opts"><label><input type="checkbox" onchange="enumAll('${fn}','${p.name}',this.checked)"> <i>全選(${p.candidates.length})</i></label>`+p.candidates.map(c=>`<label><input type="checkbox" ${sel.includes(String(c))?'checked':''} onchange="enumTog('${fn}','${p.name}','${esc(String(c))}',this.checked)"> ${esc(String(c)===''?'(空)':String(c))}</label>`).join('')+(p.more?'<i class="t">…僅列前200</i>':'')+`</div>`;}
  else{body=`<div style="flex:1"><input type="text" list="dl_${fn}_${p.name}" value="${esc(cur!==undefined?cur:(p.default??''))}" onchange="ovSet('${fn}','${p.name}',this.value)"><datalist id="dl_${fn}_${p.name}">${p.candidates.map(c=>`<option value="${esc(String(c))}">`).join('')}</datalist></div>`;}
  h+=`<div class="pr"><span class="pn">${p.name}${p.required?'*':''}</span><span class="pk">${p.kind}</span>${body}</div><div class="t" style="margin-left:118px">${esc(p.desc||'')}</div>`;}
 return h+'</div>';}
function enumTog(fn,p,v,on){const f=REG.fns[fn];const spec=f.specs.find(s=>s.name===p);let cur=ovGet(fn,p);if(!Array.isArray(cur))cur=(cur!==undefined?[cur]:(spec.default!==null&&spec.default!==undefined?[String(spec.default)]:[]));cur=cur.filter(x=>x!==v);if(on)cur.push(v);ovSet(fn,p,cur);}
function enumAll(fn,p,on){const spec=REG.fns[fn].specs.find(s=>s.name===p);ovSet(fn,p,on?spec.candidates.map(String):[]);render();}
async function loadUni(fn,p,kind,refresh){$('planNote').textContent=`載入 ${kind} 宇宙…`;const r=await fetch('/api/universe?kind='+kind+'&refresh='+refresh);const j=await r.json();UNI[kind]=j.rows||[];$('planNote').textContent=`${kind}: ${UNI[kind].length} 代碼 ${j.cached?'(DuckDB 快取)':'(已刷新)'} ${j.error?'錯誤:'+j.error:''}`;render();}
function pickUni(fn,p,kind,n){const u=UNI[kind]||[];ovSet(fn,p,(n==='all'?u:u.slice(0,n)).map(r=>String(r[0])));render();}
function filterUni(fn,p,kind,q){const el=$('uni_'+fn+'_'+p);if(!el)return;q=q.toLowerCase();for(const o of el.options)o.hidden=q&&!o.text.toLowerCase().includes(q);}
function uniSel(fn,p,el){ovSet(fn,p,[...el.selectedOptions].map(o=>o.value));const ta=el.parentElement.querySelector('textarea');if(ta)ta.value=[...el.selectedOptions].map(o=>o.value).join(',');}
async function compact(){$('planNote').textContent='壓實中…';const r=await fetch('/api/compact',{method:'POST',body:'{}'});const j=await r.json();$('planNote').textContent=`壓實完成：${j.compacted} 個序列（舊 part 已移至 _archive）`;}
async function paramsReport(){const r=await fetch('/api/params');const j=await r.json();const k=j.stats.params_by_kind||{};$('sqlh').innerHTML='<tr><th>kind</th><th>params</th></tr>';$('sqlb').innerHTML=Object.entries(k).map(([a,b])=>`<tr><td>${a}</td><td>${b}</td></tr>`).join('')+`<tr><td><b>接口全參數可選</b></td><td>${j.stats.fns_all_params_selectable} / ${j.stats.total}</td></tr>`+j.free_without_candidates.map(x=>`<tr><td class="mono">${x.fn}.${x.param}</td><td>${esc(x.desc)} (需手填)</td></tr>`).join('');}
const $=id=>document.getElementById(id);
function qd(y){const d=new Date();d.setFullYear(d.getFullYear()-y);$('start').value=d.toISOString().slice(0,10);}
async function load(){const r=await fetch('/api/registry');REG=await r.json();
 $('meta').textContent=`akshare ${REG.akshare_version} · registry ${REG.generated_at} · ${REG.summary.functions} fn stored`;
 $('k_fn').textContent=REG.stats.total||0;$('k_doc').textContent=REG.stats.documented||0;$('k_series').textContent=REG.summary.series;$('k_rows').textContent=(REG.summary.rows_total||0).toLocaleString();
 for(const c in REG.tree) openSet.add('cat:'+c); render(); runs(); poll();}
function fnMatch(fn){const q=$('q').value.trim().toLowerCase();const f=REG.fns[fn];if($('onlyDoc').checked&&!f.has_docs)return false;if($('onlyStored').checked&&!REG.manifest[fn])return false;
 if(!q)return true;return fn.toLowerCase().includes(q)||(f.title||'').toLowerCase().includes(q)||(f.desc||'').toLowerCase().includes(q);}
function collect(node){let out=[...node.fns];for(const k in node.children)out=out.concat(collect(node.children[k]));return out;}
function renderNode(node,key,depth){const fns=collect(node).filter(fnMatch);if(!fns.length)return '';const q=$('q').value.trim();const open=openSet.has(key)||q;
 const all=fns.every(f=>checked.has(f)),some=fns.some(f=>checked.has(f));
 let h=`<div class="${depth?'node':'cat'}"><div class="row h"><span class="tog" onclick="tog('${key}')">${open?'▾':'▸'}</span><input type="checkbox" ${all?'checked':''} ${(!all&&some)?'style="opacity:.5"':''} onchange="checkGroup('${key}',this.checked)"><span>${node.label}</span><span class="t">${fns.length}</span></div>`;
 if(open){h+='<div>';for(const fn of node.fns.filter(fnMatch)){const f=REG.fns[fn],m=REG.manifest[fn];
   const st=m?(m.last_status==='FAIL'?'fail':'ok'):'na';
   h+=`<div class="row" style="margin-left:22px"><input type="checkbox" ${checked.has(fn)?'checked':''} ${f.has_ast&&f.runnable?'':'disabled'} onchange="chk('${fn}',this.checked)"><span class="fn">${fn}</span><span class="t">${f.title!==fn?f.title:''}</span><span class="b ${f.strategy}">${f.strategy}${f.window?'/'+f.window+'d':''}</span>${f.combos>1?`<span class="b">×${f.combos}</span>`:''}${f.has_docs?'':'<span class="b">AST</span>'}${f.has_ast?'':'<span class="b na">缺</span>'}${m?`<span class="b ${st}">${m.last_date||'—'} · ${m.rows_total.toLocaleString()}</span>`:''}${f.all_selectable?'':'<span class="b na" title="有參數無候選值，需手動填">?</span>'}${f.specs.length?`<span class="gear ${OPEN_P.has(fn)?'on':''}" onclick="togP('${fn}')">⚙ ${f.specs.length}</span>`:''}</div>${OPEN_P.has(fn)?renderParams(fn):''}`;}
   for(const k in node.children)h+=renderNode(node.children[k],key+'/'+k,depth+1);h+='</div>';}
 return h+'</div>';}
function render(){let h='';const cats=Object.keys(REG.tree).sort();for(const c of cats)h+=renderNode(REG.tree[c],'cat:'+c,0);$('tree').innerHTML=h;$('k_sel').textContent=checked.size;}
function findNode(key){const parts=key.split('/');let node=REG.tree[parts[0].slice(4)];for(let i=1;i<parts.length;i++)node=node.children[parts[i]];return node;}
function tog(k){openSet.has(k)?openSet.delete(k):openSet.add(k);render();}
function chk(fn,v){v?checked.add(fn):checked.delete(fn);$('k_sel').textContent=checked.size;}
function checkGroup(key,v){for(const fn of collect(findNode(key)).filter(fnMatch)){const f=REG.fns[fn];if(f.has_ast&&f.runnable){v?checked.add(fn):checked.delete(fn);}}render();}
function expandAll(v){openSet=new Set();if(v){const walk=(n,k)=>{openSet.add(k);for(const c in n.children)walk(n.children[c],k+'/'+c)};for(const c in REG.tree)walk(REG.tree[c],'cat:'+c);}render();}
function checkVisible(v){for(const c in REG.tree)checkGroup('cat:'+c,v);}
$('q').addEventListener('input',()=>render());
function payload(){const ov={};for(const fn of checked)if(OV[fn]&&Object.keys(OV[fn]).length)ov[fn]=OV[fn];return {fns:[...checked],start_date:$('start').value,mode:$('mode').value,workers:+$('workers').value,max_combos:+$('maxc').value,overrides:ov,batch_rows:+$('batch').value,snapshot_ttl_hours:+$('ttl').value};}
async function run(){if(!checked.size){alert('未勾選任何接口');return;}const r=await fetch('/api/run',{method:'POST',body:JSON.stringify(payload())});const j=await r.json();if(j.error){alert(j.error);return;}$('rid').textContent=j.run_id;poll();}
async function cancel(){await fetch('/api/cancel',{method:'POST'});}
async function saveSel(){const r=await fetch('/api/selection/save',{method:'POST',body:JSON.stringify(payload())});const j=await r.json();$('planNote').innerHTML=`已儲存排程預設：<span class="sel">${j.fns}</span> 個接口 → ${j.path}（Windows 工作排程 VIA_VAKE_Daily_Incremental 每日使用）`;}
async function loadSel(){const r=await fetch('/api/selection');const j=await r.json();if(!j.fns){alert('尚無排程預設');return;}checked=new Set(j.fns);if(j.start_date)$('start').value=j.start_date;if(j.overrides)OV=j.overrides;render();}
async function rescan(){await fetch('/api/rescan',{method:'POST',body:'{}'});$('planNote').textContent='重掃已在背景啟動（AST + 文件），約 1–2 分鐘後重新整理頁面。';}
async function refreshViews(){const r=await fetch('/api/refresh_views',{method:'POST',body:'{}'});const j=await r.json();$('planNote').textContent=`DuckDB 視圖已重建：${j.views}`;}
async function poll(){const r=await fetch('/api/status');const s=await r.json();const pct=s.total?Math.round(100*s.done/s.total):0;$('bar').style.width=pct+'%';
 $('prog').innerHTML=`<b>${s.status}</b> ${s.done}/${s.total} 序列 · <span class="OK">OK ${s.ok}</span> · EMPTY ${s.empty} · <span class="FAIL">FAIL ${s.fail}</span> · TTL跳過 ${s.skipped_fresh||0} · 上游呼叫 ${s.calls||0} (省 ${s.calls_saved||0}) · rows ${s.rows_fetched.toLocaleString()} · <b>new ${s.rows_new.toLocaleString()}</b>`;
 $('cur').textContent=(s.current||[]).join(', ');if(s.run_id)$('rid').textContent=s.run_id;
 if(s.status==='finished'||s.status==='cancelled'){$('rep').href='/report/'+s.run_id;$('rep').classList.remove('hidden');}else{$('rep').classList.add('hidden');}
 $('tasks').innerHTML=(s.tasks||[]).map(t=>`<tr><td class="mono">${t.fn}</td><td class="mono">${JSON.stringify(t.params)}</td><td class="${t.status}">${t.status}</td><td>${t.windows??''}</td><td>${t.calls??''}</td><td>${t.rows}</td><td>${t.new}</td><td>${t.parts??''}</td><td>${t.sec}</td><td class="mono">${t.err||''}</td></tr>`).join('');
 clearTimeout(pollT);if(s.status==='running')pollT=setTimeout(poll,1500);else{setTimeout(()=>{fetch('/api/registry').then(r=>r.json()).then(j=>{REG.manifest=j.manifest;REG.summary=j.summary;$('k_series').textContent=j.summary.series;$('k_rows').textContent=(j.summary.rows_total||0).toLocaleString();render();runs();});},800);}}
async function sql(){const r=await fetch('/api/sql?q='+encodeURIComponent($('sql').value));const j=await r.json();if(j.error){$('sqlh').innerHTML='';$('sqlb').innerHTML=`<tr><td class="FAIL">${j.error}</td></tr>`;return;}
 $('sqlh').innerHTML='<tr>'+j.columns.map(c=>`<th>${c}</th>`).join('')+'</tr>';$('sqlb').innerHTML=j.rows.map(r=>'<tr>'+r.map(v=>`<td class="mono">${v===null?'':v}</td>`).join('')+'</tr>').join('');}
async function runs(){const r=await fetch('/api/runs');const j=await r.json();$('runs').innerHTML=j.runs.map(x=>`<tr><td class="mono">${x[0]}</td><td>${x[1].slice(0,19)}</td><td>${x[3]}</td><td>${x[5]}</td><td class="OK">${x[6]}</td><td class="FAIL">${x[7]}</td><td>${x[10]}</td><td><a href="/report/${x[0]}" target="_blank">報告</a></td></tr>`).join('');}
load();
</script></body></html>"""

# ====================================================================================================
# SECTION VAKE_CLI
# ====================================================================================================
"""VAKE command line.
  python VDF_AkshareFetcher.py scan [--refresh-docs] [--offline]   AST inventory + doc knowledge + registry + HTML matrix
  python VDF_AkshareFetcher.py serve [--port 8765] [--no-open]      local console (tree picker / incremental run / DuckDB)
  python VDF_AkshareFetcher.py fetch --selection <json> | --fns a,b,c [--start 2020-01-01] [--mode incremental|backfill]
  python VDF_AkshareFetcher.py schedule-run                          run selections/default_selection.json (Task Scheduler entry)
  python VDF_AkshareFetcher.py views                                 rebuild DuckDB v_<fn> views
  python VDF_AkshareFetcher.py params                                parameter classification matrix (HTML + JSON stats)
  python VDF_AkshareFetcher.py compact [--min-parts 8]               merge small parquet parts (old parts archived, never deleted)
  python VDF_AkshareFetcher.py universe <kind> [--refresh]           fetch/cache a symbol universe (stock_a/hk/us/etf/fund/index/...)
"""
import sys, os, argparse, json, pathlib, webbrowser


def scan_report(reg):
    st = reg["stats"]
    cats = sorted(st["by_category"].items(), key=lambda x: -x[1])
    rows = "".join(
        f"<tr><td class='mono'>{fn}</td><td>{r['category']}</td><td>{' / '.join(r['heading_path'])}</td><td class='{r['strategy']}'>{r['strategy']}{'/'+str(r['window_days'])+'d' if r['window_days'] else ''}</td>"
        f"<td>{r['enum_combos']}</td><td>{'✔' if r['has_docs'] else ''}</td><td>{'✔' if r['has_ast'] else '✖'}</td><td class='mono'>{','.join(p['name'] for p in r['ast_params'])}</td><td class='mono'>{r['module'] or ''}</td></tr>"
        for fn, r in sorted(reg["registry"].items(), key=lambda kv: (kv[1]["category"], kv[0])))
    catrows = "".join(f"<tr><td>{c}</td><td>{C.CATEGORY_ZH.get(c, '')}</td><td>{n}</td></tr>" for c, n in cats)
    strat = "".join(f"<div class='k'><b>{n}</b><span>{s}</span></div>" for s, n in sorted(st["by_strategy"].items(), key=lambda x: -x[1]))
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VAKE Registry Matrix</title>
<style>body{{font-family:'Segoe UI','Microsoft JhengHei',sans-serif;background:#0f1419;color:#e6e9ee;margin:0;padding:24px}}h1{{font-size:20px;margin:0 0 4px}}.sub{{color:#8a94a6;font-size:12px;margin-bottom:16px}}
.kpi{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}}.k{{background:#182029;border:1px solid #2b3542;border-radius:8px;padding:10px 16px;min-width:110px}}.k b{{display:block;font-size:22px}}.k span{{font-size:11px;color:#8a94a6}}
table{{border-collapse:collapse;width:100%;font-size:11px;margin-bottom:20px}}th,td{{border-bottom:1px solid #222b36;padding:4px 7px;text-align:left;vertical-align:top}}th{{background:#182029;position:sticky;top:0}}
td.mono{{font-family:Consolas,monospace}}.DATE_RANGE{{color:#5b8fd6}}.SINGLE_DATE{{color:#b48ad6}}.YEAR{{color:#d6a95b}}.FULL_SNAPSHOT{{color:#8a94a6}}
input{{background:#0b1015;border:1px solid #2b3542;color:#e6e9ee;padding:6px 8px;border-radius:4px;width:360px;margin-bottom:10px}}</style></head><body>
<h1>VAKE 註冊表矩陣 · AKShare {reg.get('akshare_version')}</h1><div class="sub">{C.ENGINE_NAME} {C.VAKE_VERSION} · {reg['generated_at']} · 文件來源 {C.DOC_BASE}/data/ (_sources md) + AST 掃描本機套件</div>
<div class="kpi"><div class="k"><b>{st['total']}</b><span>接口總數</span></div><div class="k"><b>{st['documented']}</b><span>已文件化</span></div><div class="k"><b>{st['ast_only']}</b><span>僅 AST</span></div><div class="k"><b>{st['doc_missing_in_ast']}</b><span>文件有/套件無</span></div>{strat}</div>
<table><thead><tr><th>category</th><th>中文</th><th>接口數</th></tr></thead><tbody>{catrows}</tbody></table>
<input id="q" placeholder="filter…" oninput="f()"><table id="m"><thead><tr><th>fn</th><th>category</th><th>heading path</th><th>strategy</th><th>combos</th><th>docs</th><th>ast</th><th>params</th><th>module</th></tr></thead><tbody>{rows}</tbody></table>
<script>function f(){{const q=document.getElementById('q').value.toLowerCase();for(const tr of document.querySelectorAll('#m tbody tr'))tr.style.display=tr.textContent.toLowerCase().includes(q)?'':'none';}}</script></body></html>"""
    p = C.DIR_KNOWLEDGE / "vake_registry_matrix.html"
    p.write_text(html, encoding="utf-8")
    return p


def params_report(reg):
    st = reg["stats"]
    kinds = "".join(f"<div class='k'><b>{n}</b><span>{k}</span></div>" for k, n in sorted(st.get("params_by_kind", {}).items(), key=lambda x: -x[1]))
    rows = []
    for fn, r in sorted(reg["registry"].items(), key=lambda kv: (kv[1]["category"], kv[0])):
        for p in r.get("param_specs", []):
            c = p.get("candidates", [])
            rows.append(f"<tr class='{p['kind']}'><td class='mono'>{fn}</td><td>{r['category']}</td><td class='mono'>{p['name']}{'*' if p.get('required') else ''}</td><td>{p['kind']}</td><td>{p.get('source','')}</td>"
                        f"<td>{len(c)}</td><td class='mono'>{', '.join(str(x) for x in c[:8])}{' …' if len(c) > 8 else ''}</td><td class='mono'>{p.get('universe') or ''}</td><td>{(p.get('desc') or '')[:90]}</td></tr>")
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VAKE Parameter Matrix</title>
<style>body{{font-family:'Segoe UI','Microsoft JhengHei',sans-serif;background:#0f1419;color:#e6e9ee;margin:0;padding:24px}}h1{{font-size:20px;margin:0 0 4px}}.sub{{color:#8a94a6;font-size:12px;margin-bottom:16px}}
.kpi{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}}.k{{background:#182029;border:1px solid #2b3542;border-radius:8px;padding:10px 16px;min-width:110px}}.k b{{display:block;font-size:22px}}.k span{{font-size:11px;color:#8a94a6}}
table{{border-collapse:collapse;width:100%;font-size:11px}}th,td{{border-bottom:1px solid #222b36;padding:4px 7px;text-align:left;vertical-align:top}}th{{background:#182029;position:sticky;top:0}}td.mono{{font-family:Consolas,monospace}}
tr.FREE td:nth-child(4){{color:#d6a95b}}tr.SYMBOL td:nth-child(4){{color:#5b8fd6}}tr.DATE td:nth-child(4){{color:#8a94a6}}tr.ENUM_DOC td:nth-child(4),tr.ENUM_TABLE td:nth-child(4),tr.ENUM_KNOWN td:nth-child(4),tr.ENUM_INFERRED td:nth-child(4){{color:#c96b5a}}
input{{background:#0b1015;border:1px solid #2b3542;color:#e6e9ee;padding:6px 8px;border-radius:4px;width:360px;margin-bottom:10px}}</style></head><body>
<h1>VAKE 參數分類矩陣 · 每個參數 → 下拉/多選候選值</h1><div class="sub">{C.ENGINE_NAME} {C.VAKE_VERSION} · {reg['generated_at']} · 接口 {st['total']} · 參數 {st.get('params_total',0)} · 全參數可選接口 {st.get('fns_all_params_selectable',0)}/{st['total']}</div>
<div class="kpi">{kinds}</div>
<div class="sub">DATE=由起始日與策略控制 · ENUM_DOC=文件 choice of · ENUM_TABLE=文件一覽表 · ENUM_KNOWN=已知字典(period/adjust) · ENUM_INFERRED=描述中抽取 · SYMBOL=代碼宇宙(DuckDB 快取) · FREE=預設值+手填 · TECH=timeout 等略過</div>
<input id="q" placeholder="filter…" oninput="f()"><table id="m"><thead><tr><th>fn</th><th>category</th><th>param</th><th>kind</th><th>source</th><th>#cand</th><th>candidates</th><th>universe</th><th>desc</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<script>function f(){{const q=document.getElementById('q').value.toLowerCase();for(const tr of document.querySelectorAll('#m tbody tr'))tr.style.display=tr.textContent.toLowerCase().includes(q)?'':'none';}}</script></body></html>"""
    p = C.DIR_KNOWLEDGE / "vake_param_matrix.html"
    p.write_text(html, encoding="utf-8")
    return p


def cmd_params(a):
    reg = R.load_registry()
    p = params_report(reg)
    print(json.dumps({"params_total": reg["stats"].get("params_total"), "by_kind": reg["stats"].get("params_by_kind"),
                      "fns_all_params_selectable": reg["stats"].get("fns_all_params_selectable"), "total": reg["stats"].get("total"), "matrix": str(p)}, ensure_ascii=False))
    return 0


def cmd_compact(a):
    done = S.Store().compact(min_parts=a.min_parts)
    S.Store().refresh_views()
    print(json.dumps({"compacted": len(done), "series": done}, ensure_ascii=False, default=str))
    return 0


def cmd_universe(a):
    r = U.get_universe(a.kind, refresh=a.refresh)
    print(json.dumps({"kind": a.kind, "codes": len(r.get("rows", [])), "cached": r.get("cached"), "error": r.get("error")}, ensure_ascii=False))
    return 0


def cmd_scan(a):
    C.ensure_dirs()
    inv = A.build_ast_inventory()
    kb = K.build_knowledge(refresh=a.refresh_docs, offline=a.offline)
    reg = R.build_registry(kb, inv)
    p = scan_report(reg)
    pm = params_report(reg)
    C.log(f"registry matrix: {p} / param matrix: {pm}")
    print(json.dumps({"akshare": inv.get("akshare_version"), "stats": reg["stats"], "matrix": str(p), "param_matrix": str(pm)}, ensure_ascii=False))
    return 0


def cmd_serve(a):
    V.serve(port=a.port, open_browser=not a.no_open)
    return 0


def cmd_fetch(a):
    if a.selection:
        sel = C.read_json(a.selection, None)
        if not sel:
            print(f"selection not found: {a.selection}")
            return 2
    else:
        sel = {"fns": [x.strip() for x in (a.fns or "").split(",") if x.strip()]}
    if a.start:
        sel["start_date"] = a.start
    if a.mode:
        sel["mode"] = a.mode
    if a.workers:
        sel["workers"] = a.workers
    sel.setdefault("start_date", "2015-01-01")
    sel.setdefault("mode", "incremental")
    state, report = F.run_selection(sel)
    print(json.dumps({"run_id": state["run_id"], "status": state["status"], "ok": state["ok"], "fail": state["fail"],
                      "empty": state["empty"], "rows_new": state["rows_new"], "report": report}, ensure_ascii=False))
    if a.open:
        try:
            webbrowser.open(report)
        except Exception:
            pass
    return 0 if state["fail"] == 0 else 1


def cmd_schedule_run(a):
    if not C.DEFAULT_SELECTION.exists():
        C.log("schedule-run: no default_selection.json yet (save one from the console)", "WARN")
        return 0
    a.selection = str(C.DEFAULT_SELECTION)
    a.fns = None
    a.start = None
    a.mode = "incremental"
    a.workers = None
    a.open = False
    return cmd_fetch(a)


def cmd_views(a):
    print(S.Store().refresh_views())
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="vake", description=C.ENGINE_NAME)
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("scan"); s.add_argument("--refresh-docs", action="store_true"); s.add_argument("--offline", action="store_true")
    s = sub.add_parser("serve"); s.add_argument("--port", type=int, default=C.DEFAULT_PORT); s.add_argument("--no-open", action="store_true")
    s = sub.add_parser("fetch"); s.add_argument("--selection"); s.add_argument("--fns"); s.add_argument("--start"); s.add_argument("--mode", choices=["incremental", "backfill"]); s.add_argument("--workers", type=int); s.add_argument("--open", action="store_true")
    sub.add_parser("schedule-run")
    sub.add_parser("views")
    sub.add_parser("params")
    s = sub.add_parser("compact"); s.add_argument("--min-parts", type=int, default=C.COMPACT_MIN_PARTS)
    s = sub.add_parser("universe"); s.add_argument("kind"); s.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "scan":
        return cmd_scan(a)
    if a.cmd == "serve":
        return cmd_serve(a)
    if a.cmd == "fetch":
        return cmd_fetch(a)
    if a.cmd == "schedule-run":
        return cmd_schedule_run(a)
    if a.cmd == "views":
        return cmd_views(a)
    if a.cmd == "params":
        return cmd_params(a)
    if a.cmd == "compact":
        return cmd_compact(a)
    if a.cmd == "universe":
        return cmd_universe(a)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
'@
}
$written = 0; $archived = 0; $same = 0
foreach ($name in $EngineFiles.Keys) {
    $target = Join-Path $EngineDir $name
    $content = [string]$EngineFiles[$name]
    if (Test-Path -LiteralPath $target) {
        $old = [System.IO.File]::ReadAllText($target, [System.Text.Encoding]::UTF8)
        if ((Get-Sha8 $old) -eq (Get-Sha8 $content)) { $same++; continue }
        $arc = Join-Path $ArchiveDir ('{0}.{1}.py' -f [System.IO.Path]::GetFileNameWithoutExtension($name), $Stamp)
        Copy-Item -LiteralPath $target -Destination $arc -Force
        $archived++
    }
    Write-Utf8NoBom -Path $target -Content $content
    $written++
}
Write-Utf8NoBom -Path (Join-Path $BinDir 'vake-console.cmd') -Content ('@echo off' + "`r`n" + ('set VAKE_ROOT={0}' -f $VakeRoot) + "`r`n" + ('"{0}" "{1}" serve --port {2}' -f $Py, (Join-Path $EngineDir 'VDF_AkshareFetcher.py'), $Port) + "`r`n")
Write-Utf8NoBom -Path (Join-Path $BinDir 'vake-schedule-run.cmd') -Content ('@echo off' + "`r`n" + ('set VAKE_ROOT={0}' -f $VakeRoot) + "`r`n" + ('"{0}" "{1}" schedule-run >> "{2}" 2>&1' -f $Py, (Join-Path $EngineDir 'VDF_AkshareFetcher.py'), (Join-Path $LogsDir 'schedule.log')) + "`r`n")
Write-Utf8NoBom -Path (Join-Path $BinDir 'vake-scan.cmd') -Content ('@echo off' + "`r`n" + ('set VAKE_ROOT={0}' -f $VakeRoot) + "`r`n" + ('"{0}" "{1}" scan --refresh-docs' -f $Py, (Join-Path $EngineDir 'VDF_AkshareFetcher.py')) + "`r`n")
$shim = ''
if (Test-Path -LiteralPath $RepoBin) {
    $shimPath = Join-Path $RepoBin 'via-vake.cmd'
    if (-not (Test-Path -LiteralPath $shimPath)) { Write-Utf8NoBom -Path $shimPath -Content ('@call "{0}" %*' -f (Join-Path $BinDir 'vake-console.cmd')) ; $shim = ' + via-vake.cmd shim' }
}
if (Test-Path -LiteralPath $VdfModules) {
    $vdfCopy = Join-Path $VdfModules 'VDF_AkshareFetcher.py'
    if (-not (Test-Path -LiteralPath $vdfCopy)) { Copy-Item -LiteralPath (Join-Path $EngineDir 'VDF_AkshareFetcher.py') -Destination $vdfCopy; $shim += ' + copy into functional modules\VDF' }
}
Add-Phase 'P3 engine files' 'OK' ("written {0}, unchanged {1}, archived {2}{3}" -f $written, $same, $archived, $shim) $ps

# ---------------------------------------------------------------- Phase 4  scan: AST inventory + doc knowledge + registry matrix
$ps = Get-Date
Write-Log 'Phase 4  scan (AST + docs + registry)' 'STEP'
$scanStatus = 'SKIP'; $scanDetail = 'packages missing'; $scanJson = $null
if ($pkgStatus -eq 'OK') {
    $r = Invoke-Proc -Exe $Py -ArgList @((Join-Path $EngineDir 'VDF_AkshareFetcher.py'),'scan') -Cwd $EngineDir -Capture -EnvVars @{ VAKE_ROOT = $VakeRoot }
    $lines = $r.Output -split "`n"
    foreach ($ln in $lines) { if ($ln.Trim()) { Write-Host ('   ' + $ln.TrimEnd()) -ForegroundColor DarkGray } }
    $jl = $lines | Where-Object { $_.TrimStart().StartsWith('{"akshare"') } | Select-Object -Last 1
    if ($r.ExitCode -eq 0 -and $jl) {
        try { $scanJson = $jl | ConvertFrom-Json } catch { }
        $scanStatus = 'OK'
        if ($scanJson) { $scanDetail = ('akshare {0} · total {1} · documented {2} · AST-only {3} · params {4} · all-params-selectable {5}' -f $scanJson.akshare, $scanJson.stats.total, $scanJson.stats.documented, $scanJson.stats.ast_only, $scanJson.stats.params_total, $scanJson.stats.fns_all_params_selectable) } else { $scanDetail = 'done' }
    } else { $scanStatus = 'FAIL'; $scanDetail = ('exit ' + $r.ExitCode + ' ' + (($lines | Select-Object -Last 3) -join ' | ')) }
}
Add-Phase 'P4 scan' $scanStatus $scanDetail $ps

# ---------------------------------------------------------------- Phase 5  console server (detached, reuse if already up)
$ps = Get-Date
Write-Log 'Phase 5  console server' 'STEP'
$Url = ('http://127.0.0.1:{0}/' -f $Port)
$srvStatus = 'SKIP'; $srvDetail = 'scan failed'
function Test-Url { param([string]$U) try { $x = Invoke-WebRequest -Uri ($U + 'api/runs') -TimeoutSec 2 -UseBasicParsing; return ($x.StatusCode -eq 200) } catch { return $false } }
if ($scanStatus -eq 'OK') {
    if (Test-Url $Url) { $srvStatus = 'OK'; $srvDetail = 'already running (reused)' }
    else {
        $urlFile = Join-Path $LogsDir 'server_url.txt'
        $r = Invoke-Proc -Exe $Py -ArgList @((Join-Path $EngineDir 'VDF_AkshareFetcher.py'),'serve','--port',"$Port",'--no-open') -Cwd $EngineDir -NoWait -EnvVars @{ VAKE_ROOT = $VakeRoot }
        $deadline = (Get-Date).AddSeconds(25)
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 500
            if (Test-Path -LiteralPath $urlFile) {
                $u = (Get-Content -LiteralPath $urlFile -Raw).Trim()
                if ($u -and (Test-Url $u)) { $Url = $u; break }
            }
        }
        if (Test-Url $Url) { $srvStatus = 'OK'; $srvDetail = ('pid {0} · {1}' -f $r.Pid, $Url) } else { $srvStatus = 'WARN'; $srvDetail = 'server did not answer within 25s — start manually: bin\vake-console.cmd' }
    }
    if ($srvStatus -eq 'OK') { try { Start-Process $Url } catch { Write-Log ('open browser failed: ' + $_.Exception.Message) 'WARN' } }
}
Add-Phase 'P5 console' $srvStatus $srvDetail $ps

# ---------------------------------------------------------------- Phase 6  daily Task Scheduler entry (create only if missing)
$ps = Get-Date
Write-Log 'Phase 6  task scheduler' 'STEP'
$tskStatus = 'OK'; $tskDetail = ''
$q = Invoke-Proc -Exe 'schtasks.exe' -ArgList @('/Query','/TN',$TaskName) -Capture
if ($q.ExitCode -eq 0) { $tskDetail = 'exists (untouched)' }
else {
    $c = Invoke-Proc -Exe 'schtasks.exe' -ArgList @('/Create','/TN',$TaskName,'/TR',('"' + (Join-Path $BinDir 'vake-schedule-run.cmd') + '"'),'/SC','DAILY','/ST',$TaskTime,'/RL','LIMITED') -Capture
    if ($c.ExitCode -eq 0) { $tskDetail = ('created · daily {0} · runs selections\default_selection.json (save it from the console)' -f $TaskTime) }
    else { $tskStatus = 'WARN'; $tskDetail = ('schtasks exit {0}: {1}' -f $c.ExitCode, $c.Output.Trim()) }
}
Add-Phase 'P6 schedule' $tskStatus $tskDetail $ps

# ---------------------------------------------------------------- Phase 7  HTML install report
$ps = Get-Date
$ok = ($Phases | Where-Object { $_.Status -eq 'OK' }).Count
$gate = if (($Phases | Where-Object { $_.Status -eq 'FAIL' }).Count -eq 0) { 'VAKE_INSTALL_PASS' } else { 'VAKE_INSTALL_PARTIAL' }
$rows = ($Phases | ForEach-Object { '<tr><td>{0}</td><td class="{1}">{1}</td><td>{2}</td><td>{3}</td></tr>' -f $_.Name, $_.Status, [System.Net.WebUtility]::HtmlEncode($_.Detail), $_.Sec }) -join ''
$statsHtml = ''
if ($scanJson) {
    $sb = ($scanJson.stats.by_strategy.PSObject.Properties | ForEach-Object { '<div class="k"><b>{0}</b><span>{1}</span></div>' -f $_.Value, $_.Name }) -join ''
    $cb = ($scanJson.stats.by_category.PSObject.Properties | Sort-Object -Property @{e='Value';desc=$true} | ForEach-Object { '<tr><td>{0}</td><td>{1}</td></tr>' -f $_.Name, $_.Value }) -join ''
    $statsHtml = ('<h3>策略分佈</h3><div class="kpi">{0}</div><h3>分類接口數</h3><table><thead><tr><th>category</th><th>接口</th></tr></thead><tbody>{1}</tbody></table>' -f $sb, $cb)
}
$html = @"
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VAKE Install $Stamp</title>
<style>body{font-family:'Segoe UI','Microsoft JhengHei',sans-serif;background:#0f1419;color:#e6e9ee;margin:0;padding:24px}h1{font-size:20px;margin:0 0 4px}.sub{color:#8a94a6;font-size:12px;margin-bottom:16px}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}.k{background:#182029;border:1px solid #2b3542;border-radius:8px;padding:10px 16px;min-width:110px}.k b{display:block;font-size:22px}.k span{font-size:11px;color:#8a94a6}
table{border-collapse:collapse;width:100%;font-size:12px;margin-bottom:18px}th,td{border-bottom:1px solid #222b36;padding:5px 8px;text-align:left;vertical-align:top}th{background:#182029}
td.OK{color:#c96b5a;font-weight:600}td.FAIL{color:#5a9e6f;font-weight:600}td.WARN{color:#d9a441}td.SKIP{color:#8a94a6}a{color:#d9a441}
.gate{display:inline-block;border:2px solid #d9a441;color:#d9a441;padding:6px 14px;border-radius:6px;font-weight:700;letter-spacing:1px}
code{background:#0b1015;padding:2px 5px;border-radius:3px;font-family:Consolas,monospace}h3{color:#d9a441;font-size:13px;margin:16px 0 6px}</style></head><body>
<h1>VAKE 安裝 / 啟動報告</h1><div class="sub">Veritas AKShare Knowledge &amp; Extraction Engine v0200 · $Stamp · $([Math]::Round(((Get-Date)-$T0).TotalSeconds,1))s</div>
<div class="gate">Gate: $gate</div><p></p>
<div class="kpi"><div class="k"><b>$ok / $($Phases.Count)</b><span>phases OK</span></div><div class="k"><b><a href="$Url" target="_blank">開啟控制台</a></b><span>$Url</span></div><div class="k"><b><a href="file:///$($VakeRoot -replace '\\','/')/knowledge/vake_registry_matrix.html" target="_blank">註冊表矩陣</a></b><span>knowledge\vake_registry_matrix.html</span></div></div>
<table><thead><tr><th>phase</th><th>status</th><th>detail</th><th>sec</th></tr></thead><tbody>$rows</tbody></table>
$statsHtml
<h3>使用方式</h3>
<ol><li>控制台左側樹狀清單 = AKShare 文件分類 → 標題 → 接口（勾選可級聯）；右側選「起始日」→ 按「執行擷取」= 起始日到最新的增量維護。</li>
<li>按「儲存為每日排程預設」後，工作排程 <code>$TaskName</code> 每日 $TaskTime 自動增量（僅寫入新列，Parquet 只增不減）。</li>
<li>資料：<code>$VakeRoot\store\&lt;category&gt;\&lt;fn&gt;\&lt;param_hash&gt;\part_*.parquet</code>；DuckDB：<code>$VakeRoot\db\vake.duckdb</code>（視圖 <code>v_&lt;fn&gt;</code>、<code>vake_manifest</code>、<code>vake_runs</code>、<code>vake_fetch_log</code>）。</li>
<li>參數分類矩陣：<code>knowledge\vake_param_matrix.html</code>（每個參數的 kind / 候選值 / 宇宙）；控制台每個接口 ⚙ 展開即為下拉/多選。</li>
<li>流量優化：視窗由最新往舊、增量遇已存視窗即提前停止；FULL_SNAPSHOT 在 TTL 內不重抓；代碼宇宙 DuckDB 快取 24h；每 batch_rows 列寫一個 part，<code>VDF_AkshareFetcher.py compact</code> 壓實（舊 part 歸檔不刪）。</li>
<li>指令：<code>bin\vake-console.cmd</code>（重開控制台）· <code>bin\vake-scan.cmd</code>（重掃文件+AST）· <code>bin\vake-schedule-run.cmd</code>（手動跑排程預設）。</li></ol>
<div class="sub">log: $LogFile · engine: $EngineDir · venv: $VenvDir</div></body></html>
"@
$reportPath = Join-Path $RunDir 'VAKE_install_report.html'
Write-Utf8NoBom -Path $reportPath -Content $html
Add-Phase 'P7 report' 'OK' $reportPath $ps
try { Start-Process $reportPath } catch { Write-Log ('open report failed: ' + $_.Exception.Message) 'WARN' }

Write-Host ''
Write-Host ('  Gate: {0}   phases OK {1}/{2}   console {3}' -f $gate, $ok, $Phases.Count, $Url) -ForegroundColor Yellow
Write-Host ('  report: {0}' -f $reportPath) -ForegroundColor DarkGray
Write-Host ''
}
