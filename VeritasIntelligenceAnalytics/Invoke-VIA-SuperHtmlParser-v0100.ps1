#requires -Version 7.0
# ============================================================================
# Invoke-VIA-SuperHtmlParser.ps1  v1.1.0  (VSHP — VIA SuperHtml Parser Engine + VIA NLP One Engine bridge)
# HTML content + UI component + JS/CSS logic + backend (py/json/ps1) parser -> Markdown
# MS markdown lib: markitdown (Microsoft)  ·  bs4/lxml · esprima (JS AST) · tinycss2 (CSS AST) · Python ast
# v1.1: append-only NLP bridge -> VIA NLP One Engine v1.5 (FunctionClassifier / TextProcessor), ui_component_lexicon, engine-JSON gap hints
# Paste-and-run / one-click. LL: no aliases, no Read-Host, no exit, ProcessStartInfo, UTF8 no-BOM, append-only.
# Usage:  pwsh -ExecutionPolicy Bypass -File .\Invoke-VIA-SuperHtmlParser.ps1
#         pwsh -ExecutionPolicy Bypass -File .\Invoke-VIA-SuperHtmlParser.ps1 -Targets 'C:\path\to\ui', 'C:\path\file.html'
#         via-superhtml C:\path   (bin shim created by this script)
#         -NlpSource 'C:\path\VIA_NLP_OneEngine_v1.5.0.zip'  (or extracted folder; if omitted: script folder -> C:\VIA -> Downloads)
# ============================================================================
param(
    [string]$Root = 'C:\VIA\VeritasSuperHtmlParser',
    [string[]]$Targets = @(),
    [string]$NlpSource = '',
    [switch]$NoOpen,
    [switch]$ReinstallDeps
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
# LL#25 paste-safety: body wrapped in & { } so an interactive console parses it atomically.
# If pasted (param() never binds), the null-defaults below restore every parameter.
& {
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = 'C:\VIA\VeritasSuperHtmlParser' }
if ($null -eq $Targets) { $Targets = @() }
$Targets = @($Targets | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($null -eq $NlpSource) { $NlpSource = '' }
$OpenReport = -not [bool]$NoOpen
$ForceDeps = [bool]$ReinstallDeps

$ErrorActionPreference = 'Continue'
$script:T0 = Get-Date
$script:Stamp = $script:T0.ToString('yyyyMMdd_HHmmss')
$script:Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$script:Version = '1.1.0'
$script:CoreVersion = '1.0.0'
$script:LogLines = [System.Collections.Generic.List[string]]::new()

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $line = ('[{0}] [{1}] {2}' -f (Get-Date).ToString('HH:mm:ss'), $Level, $Message)
    $script:LogLines.Add($line)
    $color = switch ($Level) { 'OK' { 'Green' } 'WARN' { 'Yellow' } 'FAIL' { 'Red' } 'STEP' { 'Cyan' } default { 'Gray' } }
    Write-Host $line -ForegroundColor $color
}

function Save-TextNoBom {
    param([string]$Path, [string]$Content)
    $dir = Split-Path -Path $Path -Parent
    if (-not (Test-Path -LiteralPath $dir)) { [System.IO.Directory]::CreateDirectory($dir) | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

function Get-Sha8 {
    param([string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $bytes = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Text))
    return ([System.BitConverter]::ToString($bytes) -replace '-', '').Substring(0, 8).ToLower()
}

# Append-only writer: never overwrites an existing file with different content; writes a _sha<8> sibling instead
function Save-AppendOnly {
    param([string]$Path, [string]$Content)
    if (Test-Path -LiteralPath $Path) {
        $existing = [System.IO.File]::ReadAllText($Path, $script:Utf8NoBom)
        if ($existing -eq $Content) { return $Path }
        $ext = [System.IO.Path]::GetExtension($Path)
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($Path)
        $alt = Join-Path (Split-Path -Path $Path -Parent) ('{0}_sha{1}{2}' -f $stem, (Get-Sha8 -Text $Content), $ext)
        if (-not (Test-Path -LiteralPath $alt)) {
            Save-TextNoBom -Path $alt -Content $Content
            Write-Log -Message ('append-only: existing {0} kept; new version written as {1}' -f (Split-Path -Path $Path -Leaf), (Split-Path -Path $alt -Leaf)) -Level 'WARN'
        }
        return $alt
    }
    Save-TextNoBom -Path $Path -Content $Content
    return $Path
}

# ProcessStartInfo runner; no redirect => child output streams live to the console (LL#26 no-stall)
function Invoke-Proc {
    param([string]$Exe, [string[]]$Arguments, [string]$WorkDir)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $Exe
    foreach ($a in $Arguments) { $psi.ArgumentList.Add($a) }
    $psi.WorkingDirectory = $WorkDir
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $false
    $psi.RedirectStandardError = $false
    $psi.Environment['PYTHONIOENCODING'] = 'utf-8'
    $psi.Environment['PYTHONUTF8'] = '1'
    $p = [System.Diagnostics.Process]::Start($psi)
    $p.WaitForExit()
    return $p.ExitCode
}

function Find-Python {
    $candidates = @()
    $found = @()
    $py = Get-Command -Name 'py' -ErrorAction SilentlyContinue
    if ($py) { $candidates += ,@($py.Source, @('-3')) }
    foreach ($n in @('python', 'python3')) {
        $c = Get-Command -Name $n -ErrorAction SilentlyContinue
        if ($c -and $c.Source -notlike '*WindowsApps*') { $candidates += ,@($c.Source, @()) }
    }
    foreach ($cand in $candidates) {
        try {
            $psi = [System.Diagnostics.ProcessStartInfo]::new()
            $psi.FileName = $cand[0]
            foreach ($a in $cand[1]) { $psi.ArgumentList.Add($a) }
            $psi.ArgumentList.Add('-c'); $psi.ArgumentList.Add('import sys;print("%d.%d"%sys.version_info[:2])')
            $psi.UseShellExecute = $false; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
            $p = [System.Diagnostics.Process]::Start($psi)
            $v = $p.StandardOutput.ReadToEnd().Trim(); $p.WaitForExit()
            if ($p.ExitCode -eq 0 -and $v -match '^(\d+)\.(\d+)$' -and ([int]$Matches[1] -gt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 10))) {
                $found += ,@{ Exe = $cand[0]; Pre = $cand[1]; Version = $v; Minor = [int]$Matches[2] }
            }
        } catch { }
    }
    if ($found.Count -eq 0) { return $null }
    # prefer the newest interpreter (VIA NLP One Engine needs 3.11+)
    return ($found | Sort-Object -Property @{e='Minor';desc=$true})[0]
}

# Locate VIA NLP One Engine source: explicit path (folder or zip) -> previous extract -> C:\VIA -> Downloads (folder or zip)
function Find-NlpSource {
    param([string]$Explicit, [string]$ExtractDir, [string]$ScriptDir)
    $dl = ''
    if ($env:USERPROFILE) { $dl = Join-Path $env:USERPROFILE 'Downloads' }
    $folders = @()
    $zips = @()
    if ($Explicit) {
        if ($Explicit -like '*.zip') { $zips += $Explicit } else { $folders += $Explicit }
    }
    $folders += @((Join-Path $ExtractDir 'VIA_NLP_OneEngine_v1.5.0'), 'C:\VIA\VIA_NLP_OneEngine_v1.5.0', 'C:\VIA\VIA_NLP_OneEngine')
    if ($ScriptDir -and (Test-Path -LiteralPath $ScriptDir)) {
        $folders += @((Join-Path $ScriptDir 'VIA_NLP_OneEngine_v1.5.0'), (Join-Path $ScriptDir 'VIA_NLP_OneEngine'))
    }
    if ($dl) { $folders += @((Join-Path $dl 'VIA_NLP_OneEngine_v1.5.0'), (Join-Path $dl 'VIA_NLP_OneEngine')) }
    if (Test-Path -LiteralPath $ExtractDir) {
        foreach ($d in [System.IO.Directory]::EnumerateDirectories($ExtractDir)) { $folders += $d }
    }
    foreach ($f in $folders) {
        if ($f -and (Test-Path -LiteralPath (Join-Path $f 'pyproject.toml')) -and (Test-Path -LiteralPath (Join-Path $f 'src\via_nlp_engine'))) { return $f }
    }
    # zips next to the script (any VIA_NLP_OneEngine*.zip, newest first), then Downloads
    if ($ScriptDir -and (Test-Path -LiteralPath $ScriptDir)) {
        foreach ($z in ([System.IO.Directory]::EnumerateFiles($ScriptDir, 'VIA_NLP_OneEngine*.zip') | Sort-Object -Property @{e={ (Get-Item -LiteralPath $_).LastWriteTime };desc=$true})) { $zips += $z }
    }
    if ($dl) { $zips += @((Join-Path $dl 'VIA_NLP_OneEngine_v1_5_0.zip'), (Join-Path $dl 'VIA_NLP_OneEngine_v1.5.0.zip')) }
    if ($dl -and (Test-Path -LiteralPath $dl)) {
        foreach ($z in ([System.IO.Directory]::EnumerateFiles($dl, 'VIA_NLP_OneEngine*.zip') | Sort-Object -Property @{e={ (Get-Item -LiteralPath $_).LastWriteTime };desc=$true})) { $zips += $z }
    }
    foreach ($z in $zips) {
        if ($z -and (Test-Path -LiteralPath $z)) {
            Write-Log -Message ('extracting {0} -> {1}' -f $z, $ExtractDir) -Level 'STEP'
            Add-Type -AssemblyName 'System.IO.Compression.FileSystem' -ErrorAction SilentlyContinue
            if (-not (Test-Path -LiteralPath $ExtractDir)) { [System.IO.Directory]::CreateDirectory($ExtractDir) | Out-Null }
            try { [System.IO.Compression.ZipFile]::ExtractToDirectory($z, $ExtractDir, $true) } catch { Write-Log -Message ('extract failed: {0}' -f $_.Exception.Message) -Level 'WARN'; continue }
            foreach ($d in [System.IO.Directory]::EnumerateDirectories($ExtractDir)) {
                if ((Test-Path -LiteralPath (Join-Path $d 'pyproject.toml')) -and (Test-Path -LiteralPath (Join-Path $d 'src\via_nlp_engine'))) { return $d }
            }
        }
    }
    return $null
}

try {
    # ------------------------------------------------------------ 0. header
    Write-Host ''
    Write-Host '  VeritasIntelligenceAnalytics · SuperHtml Parser Engine (VSHP)' -ForegroundColor White
    Write-Host '  VERITAS INTELLIGENCE SYSTEM' -ForegroundColor DarkGray
    Write-Host ('  v{0} · HTML content + UI component + JS/CSS + backend → Markdown · markitdown(MS) · NLP One Engine bridge · append-only' -f $script:Version) -ForegroundColor DarkGray
    Write-Host ''

    # ------------------------------------------------------------ 1. layout
    Write-Log -Message ('Root = {0}' -f $Root) -Level 'STEP'
    $dirs = [ordered]@{
        engine  = Join-Path $Root 'engine'
        samples = Join-Path $Root 'samples'
        reports = Join-Path $Root 'reports'
        bin     = Join-Path $Root 'bin'
        logs    = Join-Path $Root 'logs'
        lexicon = Join-Path $Root 'lexicon'
        nlp     = Join-Path $Root 'nlp_engine'
    }
    foreach ($d in $dirs.Values) { if (-not (Test-Path -LiteralPath $d)) { [System.IO.Directory]::CreateDirectory($d) | Out-Null } }

    # ------------------------------------------------------------ 2. python
    $pyInfo = Find-Python
    if ($null -eq $pyInfo) {
        Write-Log -Message 'Python >= 3.10 not found (markitdown requires 3.10+). Install from python.org, then rerun.' -Level 'FAIL'
        $abort = $true
    } else {
        $abort = $false
        Write-Log -Message ('Python {0} at {1}' -f $pyInfo.Version, $pyInfo.Exe) -Level 'OK'
    }

    if (-not $abort) {
        # -------------------------------------------------------- 3. venv + deps (MS markitdown + AST libs)
        $venv = Join-Path $Root '.venv'
        $venvPy = Join-Path $venv 'Scripts\python.exe'
        if (-not (Test-Path -LiteralPath $venvPy)) {
            Write-Log -Message 'creating venv .venv' -Level 'STEP'
            $rc = Invoke-Proc -Exe $pyInfo.Exe -Arguments (@($pyInfo.Pre) + @('-m', 'venv', $venv)) -WorkDir $Root
            if ($rc -ne 0 -or -not (Test-Path -LiteralPath $venvPy)) { Write-Log -Message 'venv creation failed; falling back to system python' -Level 'WARN'; $venvPy = $pyInfo.Exe }
        }
        $depsMarker = Join-Path $venv ('deps_v{0}.ok' -f $script:Version)
        if ($ForceDeps -or -not (Test-Path -LiteralPath $depsMarker)) {
            Write-Log -Message 'pip install: markitdown (Microsoft) beautifulsoup4 lxml tinycss2 esprima markdownify' -Level 'STEP'
            $pipArgs = @('-m', 'pip', 'install', '--disable-pip-version-check', '--upgrade', 'pip')
            Invoke-Proc -Exe $venvPy -Arguments $pipArgs -WorkDir $Root | Out-Null
            $pipArgs = @('-m', 'pip', 'install', '--disable-pip-version-check', 'beautifulsoup4', 'lxml', 'tinycss2', 'esprima', 'markdownify')
            $rc1 = Invoke-Proc -Exe $venvPy -Arguments $pipArgs -WorkDir $Root
            $pipArgs = @('-m', 'pip', 'install', '--disable-pip-version-check', 'markitdown')
            $rc2 = Invoke-Proc -Exe $venvPy -Arguments $pipArgs -WorkDir $Root
            if ($rc1 -eq 0) { Save-TextNoBom -Path $depsMarker -Content ('installed {0} markitdown_rc={1}' -f (Get-Date -Format 's'), $rc2) } else { Write-Log -Message 'core deps install failed — engine will run in regex-fallback mode' -Level 'WARN' }
            if ($rc2 -ne 0) { Write-Log -Message 'markitdown install failed — content will fall back to markdownify/bs4' -Level 'WARN' }
        } else {
            Write-Log -Message 'deps already installed (marker present); use -ReinstallDeps to force' -Level 'OK'
        }

        # -------------------------------------------------------- 3b. VIA NLP One Engine (editable install, [zh] extra = jieba/opencc)
        $nlpRoot = $null
        $nlpMarker = Join-Path $venv 'deps_nlp_v1.ok'
        if ($pyInfo.Minor -lt 11) {
            Write-Log -Message ('Python 3.{0} found; VIA NLP One Engine needs 3.11+ -> semantic layer runs in degraded mode (component canonical + gap hints only)' -f $pyInfo.Minor) -Level 'WARN'
        } else {
            $scriptDir = ''
            if ($PSCommandPath) { $scriptDir = Split-Path -Path $PSCommandPath -Parent }
            $nlpRoot = Find-NlpSource -Explicit $NlpSource -ExtractDir $dirs.nlp -ScriptDir $scriptDir
            if ($null -eq $nlpRoot) {
                Write-Log -Message 'VIA NLP One Engine not found (searched -NlpSource, C:\VIA, Downloads); pass -NlpSource <zip or folder> to enable ②/④' -Level 'WARN'
            } else {
                Write-Log -Message ('NLP engine source = {0}' -f $nlpRoot) -Level 'OK'
                $needInstall = $ForceDeps -or -not (Test-Path -LiteralPath $nlpMarker)
                if (-not $needInstall) {
                    $prev = [System.IO.File]::ReadAllText($nlpMarker, $script:Utf8NoBom).Trim()
                    if ($prev -ne $nlpRoot) { $needInstall = $true }
                }
                if ($needInstall) {
                    Write-Log -Message 'pip install -e <NLP engine>[zh]' -Level 'STEP'
                    $rc3 = Invoke-Proc -Exe $venvPy -Arguments @('-m', 'pip', 'install', '--disable-pip-version-check', '-e', ('{0}[zh]' -f $nlpRoot)) -WorkDir $Root
                    if ($rc3 -eq 0) { Save-TextNoBom -Path $nlpMarker -Content $nlpRoot } else { Write-Log -Message 'NLP engine install failed; bridge will report unavailable' -Level 'WARN' }
                } else {
                    Write-Log -Message 'NLP engine already installed (marker matches source)' -Level 'OK'
                }
            }
        }

        # -------------------------------------------------------- 4. engine source (append-only)
        $engineSrc = @'
# -*- coding: utf-8 -*-
# VIA SuperHtml Parser Engine (VSHP) v1.0.0
# HTML content + UI component + JS/CSS logic + backend (py/json/ps1) parser -> Markdown
# Implements: read_html_ui / read_ui_logic / read_backend_logic (Tony's pseudocode) + Engine-JSON pipeline graph
# MS markdown lib: markitdown (Microsoft) for HTML content -> Markdown; fallback markdownify -> bs4 text
import sys, os, re, json, ast, time, html as _html, hashlib, argparse, traceback
from pathlib import Path
from collections import Counter, defaultdict

VERSION = "1.0.0"
T0 = time.time()

def log(kind, msg):
    print("[{0}] {1}".format(kind, msg), flush=True)

# ---------------------------------------------------------------- optional deps
try:
    from bs4 import BeautifulSoup, Tag
    HAS_BS4 = True
except Exception:
    HAS_BS4 = False
try:
    import lxml  # noqa
    BS_PARSER = "lxml"
except Exception:
    BS_PARSER = "html.parser"
try:
    import esprima
    HAS_ESPRIMA = True
except Exception:
    HAS_ESPRIMA = False
try:
    import tinycss2
    HAS_TINYCSS = True
except Exception:
    HAS_TINYCSS = False
try:
    from markitdown import MarkItDown
    HAS_MARKITDOWN = True
except Exception:
    HAS_MARKITDOWN = False
try:
    from markdownify import markdownify as _markdownify
    HAS_MARKDOWNIFY = True
except Exception:
    HAS_MARKDOWNIFY = False

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".vs", "dist", "build", "reports"}
HTML_EXT = {".html", ".htm"}
JS_EXT = {".js", ".mjs"}
CSS_EXT = {".css"}
PY_EXT = {".py"}
JSON_EXT = {".json"}
PS_EXT = {".ps1", ".psm1"}
SEMANTIC_TAGS = {"header", "nav", "main", "section", "article", "aside", "footer", "form", "table", "button",
                 "input", "select", "textarea", "canvas", "svg", "dialog", "details", "summary", "iframe", "video"}
COMPONENT_CLASS_RE = re.compile(r"(card|panel|modal|nav|btn|button|form|table|chart|widget|component|container|"
                                r"section|header|footer|sidebar|toolbar|tab|menu|dialog|grid|row|col|list|item|"
                                r"badge|seal|kpi|metric|tile|dash|console|progress|bar)", re.I)
DOM_WRITE_PROPS = {"innerHTML", "innerText", "textContent", "value", "src", "href", "checked", "disabled", "hidden", "className"}
DOM_WRITE_CALLS = {"classList.add", "classList.remove", "classList.toggle", "setAttribute", "removeAttribute",
                   "appendChild", "append", "prepend", "insertAdjacentHTML", "remove", "replaceChildren", "insertBefore"}
API_CALL_RE = re.compile(r"^(fetch|axios(\.\w+)?|\$\.ajax|\$\.get|\$\.post|\$\.getJSON|XMLHttpRequest|jQuery\.ajax)$")
LAYOUT_PROPS = {"display", "position", "float", "grid-template-columns", "grid-template-rows", "grid-area",
                "flex", "flex-direction", "justify-content", "align-items", "width", "height", "max-width",
                "min-width", "margin", "padding", "gap", "overflow", "top", "left", "right", "bottom", "z-index"}

# ---------------------------------------------------------------- helpers
def load_file(p):
    return Path(p).read_text(encoding="utf-8", errors="replace")

def sha8(s):
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:8]

def md_esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ").replace("\r", "")

def md_table(headers, rows, max_rows=400):
    if not rows:
        return "_(none)_\n"
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows[:max_rows]:
        out.append("| " + " | ".join(md_esc(c) for c in r) + " |")
    if len(rows) > max_rows:
        out.append("| ... | {0} more rows omitted | |".format(len(rows) - max_rows))
    return "\n".join(out) + "\n"

def clip(s, n=90):
    s = re.sub(r"\s+", " ", str(s)).strip()
    return s if len(s) <= n else s[:n - 1] + "…"

def safe_id(s):
    return re.sub(r"[^A-Za-z0-9_]", "_", s)[:40] or "n"

# ================================================================ HTML / DOM
def parse_html(raw):
    return BeautifulSoup(raw, BS_PARSER)

def node_selector(node):
    parts = []
    cur = node
    while cur is not None and getattr(cur, "name", None) and cur.name != "[document]":
        seg = cur.name
        nid = cur.get("id")
        if nid:
            parts.append("{0}#{1}".format(seg, nid))
            break
        cls = cur.get("class")
        if cls:
            seg += "." + ".".join(cls[:2])
        sib = [s for s in cur.parent.find_all(cur.name, recursive=False)] if cur.parent else []
        if len(sib) > 1:
            seg += ":nth-of-type({0})".format(sib.index(cur) + 1)
        parts.append(seg)
        cur = cur.parent
    return " > ".join(reversed(parts))

def node_depth(node):
    d = 0
    cur = node.parent
    while cur is not None and getattr(cur, "name", None) and cur.name != "[document]":
        d += 1
        cur = cur.parent
    return d

def build_dom_structure(soup):
    lines, tag_counter, max_depth = [], Counter(), 0
    root = soup.find("html") or soup

    def rec(node, depth):
        nonlocal max_depth
        if not isinstance(node, Tag):
            return
        max_depth = max(max_depth, depth)
        tag_counter[node.name] += 1
        label = node.name
        if node.get("id"):
            label += "#" + node.get("id")
        if node.get("class"):
            label += "." + ".".join(node.get("class")[:3])
        kids = [c for c in node.children if isinstance(c, Tag)]
        if node.name in ("script", "style"):
            label += "  [{0} chars]".format(len(node.get_text()))
        if depth <= 6 and len(lines) < 800:
            lines.append("  " * depth + "- " + label + ("  ({0} children)".format(len(kids)) if kids and depth == 6 else ""))
        if depth < 6:
            for k in kids:
                rec(k, depth + 1)
    rec(root, 0)
    return {"tree": lines, "tag_counter": tag_counter, "max_depth": max_depth}

def extract_components(soup):
    comps = []
    for node in soup.find_all(True):
        if node.name in ("html", "head", "body", "script", "style", "meta", "link", "title", "br"):
            continue
        cls = " ".join(node.get("class", []))
        data_attrs = {k: v for k, v in node.attrs.items() if k.startswith("data-")}
        events = [k for k in node.attrs if k.startswith("on")]
        is_comp = (node.name in SEMANTIC_TAGS or node.get("id") or data_attrs or events
                   or (cls and COMPONENT_CLASS_RE.search(cls)) or node.get("role"))
        if not is_comp:
            continue
        kids = [c for c in node.children if isinstance(c, Tag)]
        comps.append({
            "selector": node_selector(node), "tag": node.name, "id": node.get("id", ""),
            "class": cls, "role": node.get("role", ""), "data": json.dumps(data_attrs, ensure_ascii=False) if data_attrs else "",
            "events": ",".join(events), "children": len(kids), "depth": node_depth(node),
            "text": clip(node.get_text(" ", strip=True), 60),
        })
    return comps

def extract_dom_events(soup):
    evs = []
    for node in soup.find_all(True):
        for k, v in node.attrs.items():
            if k.startswith("on") and isinstance(v, str):
                evs.append({"selector": node_selector(node), "event": k, "handler": clip(v, 100),
                            "fn": (re.findall(r"([A-Za-z_$][\w$]*)\s*\(", v) or [""])[0]})
    return evs

def collect_assets(soup, base_dir, tag, attr, filt):
    inline, external = [], []
    for t in soup.find_all(tag):
        if not filt(t):
            continue
        src = t.get(attr)
        if src:
            local = (Path(base_dir) / src.split("?")[0]).resolve() if not re.match(r"^(https?:)?//", src) else None
            content = ""
            status = "remote-not-fetched"
            if local and local.exists():
                content = load_file(local)
                status = "local-loaded"
            elif local:
                status = "local-missing"
            external.append({"src": src, "status": status, "content": content})
        else:
            inline.append({"src": "(inline)", "status": "inline", "content": t.get_text()})
    return inline, external

# ================================================================ JS
def js_parse(src):
    if not HAS_ESPRIMA:
        return None
    for fn in (esprima.parseScript, esprima.parseModule):
        try:
            return fn(src, tolerant=True, loc=True).toDict()
        except Exception:
            continue
    return None

def js_walk(node, ctx, visitor):
    if isinstance(node, dict):
        t = node.get("type")
        new_ctx = visitor(node, ctx) if t else ctx
        for k, v in node.items():
            if k in ("loc", "range"):
                continue
            js_walk(v, new_ctx, visitor)
    elif isinstance(node, list):
        for it in node:
            js_walk(it, ctx, visitor)

def js_name(node):
    if not isinstance(node, dict):
        return ""
    t = node.get("type")
    if t == "Identifier":
        return node.get("name", "")
    if t == "ThisExpression":
        return "this"
    if t == "MemberExpression":
        obj = js_name(node.get("object"))
        prop = node.get("property", {})
        p = prop.get("name") if not node.get("computed") else "[{0}]".format(js_name(prop) or js_lit(prop))
        return "{0}.{1}".format(obj, p) if obj else str(p)
    if t == "CallExpression":
        return js_name(node.get("callee")) + "()"
    if t == "Literal":
        return repr(node.get("value"))
    return ""

def js_lit(node):
    if isinstance(node, dict) and node.get("type") == "Literal":
        return str(node.get("value"))
    if isinstance(node, dict) and node.get("type") == "TemplateLiteral":
        return "".join(q.get("value", {}).get("cooked", "") or "" for q in node.get("quasis", []))
    return ""

def js_line(node):
    try:
        return node["loc"]["start"]["line"]
    except Exception:
        return 0

def js_target_of(callee_node):
    # document.getElementById('x').addEventListener -> #x ; $('sel').on -> sel
    obj = callee_node.get("object") if isinstance(callee_node, dict) else None
    if isinstance(obj, dict) and obj.get("type") == "CallExpression":
        cn = js_name(obj.get("callee"))
        arg = js_lit((obj.get("arguments") or [{}])[0])
        if cn.endswith("getElementById"):
            return "#" + arg
        if cn.endswith("querySelector") or cn.endswith("querySelectorAll") or cn in ("$", "jQuery"):
            return arg
    return js_name(obj) if obj else ""

def analyze_js(scripts):
    logic = {"functions": [], "calls": [], "events": [], "data_flow": [], "control_flow": [], "modules": [],
             "dom_writes": [], "api_calls": [], "parse_errors": []}
    CF_TYPES = {"IfStatement", "ForStatement", "ForInStatement", "ForOfStatement", "WhileStatement",
                "DoWhileStatement", "SwitchStatement", "TryStatement", "ConditionalExpression"}
    for sc in scripts:
        src = sc.get("content") or ""
        if not src.strip():
            continue
        label = sc.get("src", "(inline)")
        tree = js_parse(src)
        if tree is None:
            logic["parse_errors"].append(label)
            analyze_js_regex(src, label, logic)
            continue
        cf = defaultdict(lambda: Counter())
        depth_now = {"d": 0}

        def visitor(node, ctx):
            t = node["type"]
            fn_ctx = ctx
            # function definitions
            if t in ("FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression", "MethodDefinition"):
                name = ""
                if t == "FunctionDeclaration" and node.get("id"):
                    name = node["id"].get("name", "")
                elif t == "MethodDefinition":
                    name = js_name(node.get("key"))
                if t in ("FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"):
                    params = [js_name(p) or p.get("type", "?") for p in node.get("params", [])]
                    name = name or node.get("_assigned_name", "") or "anon@L{0}".format(js_line(node))
                    logic["functions"].append({"file": label, "name": name, "params": ",".join(params),
                                               "line": js_line(node), "async": node.get("isAsync", False) or node.get("async", False),
                                               "kind": t.replace("Expression", "").replace("Declaration", "")})
                    fn_ctx = name
            if t == "VariableDeclarator" and isinstance(node.get("init"), dict) and node["init"].get("type") in ("FunctionExpression", "ArrowFunctionExpression"):
                node["init"]["_assigned_name"] = js_name(node.get("id"))
            if t == "AssignmentExpression" and isinstance(node.get("right"), dict) and node["right"].get("type") in ("FunctionExpression", "ArrowFunctionExpression"):
                node["right"]["_assigned_name"] = js_name(node.get("left"))
            if t == "Property" and isinstance(node.get("value"), dict) and node["value"].get("type") in ("FunctionExpression", "ArrowFunctionExpression"):
                node["value"]["_assigned_name"] = js_name(node.get("key"))
            # calls
            if t == "CallExpression":
                cname = js_name(node.get("callee"))
                args = node.get("arguments", [])
                logic["calls"].append({"file": label, "in": ctx, "callee": cname, "line": js_line(node)})
                base = cname.split(".")[-1]
                if base == "addEventListener" and args:
                    handler = args[1] if len(args) > 1 else {}
                    hname = js_name(handler) or ("anon@L{0}".format(js_line(handler)) if handler else "")
                    logic["events"].append({"file": label, "target": js_target_of(node.get("callee")), "event": js_lit(args[0]),
                                            "handler": hname, "line": js_line(node), "via": "addEventListener"})
                elif base in ("on", "click", "change", "submit", "input", "keyup", "keydown") and cname.startswith("$") or cname.startswith("jQuery"):
                    ev = js_lit(args[0]) if base == "on" and args else base
                    handler = args[-1] if args else {}
                    logic["events"].append({"file": label, "target": js_target_of(node.get("callee")), "event": ev,
                                            "handler": js_name(handler) or "anon@L{0}".format(js_line(handler)), "line": js_line(node), "via": "jQuery"})
                if API_CALL_RE.match(cname) or cname.endswith(".fetch"):
                    url = js_lit(args[0]) if args else ""
                    if not url and args and isinstance(args[0], dict) and args[0].get("type") == "ObjectExpression":
                        for p in args[0].get("properties", []):
                            if js_name(p.get("key")) == "url":
                                url = js_lit(p.get("value"))
                    logic["api_calls"].append({"file": label, "in": ctx, "call": cname, "url": url or "(dynamic)", "line": js_line(node)})
                if any(cname.endswith(w) for w in DOM_WRITE_CALLS):
                    logic["dom_writes"].append({"file": label, "in": ctx, "target": js_target_of(node.get("callee")) or cname.rsplit(".", 1)[0], "op": base, "line": js_line(node)})
                if cname == "require" and args:
                    logic["modules"].append({"file": label, "kind": "require", "module": js_lit(args[0])})
            # assignments / data flow
            if t == "AssignmentExpression":
                left = node.get("left", {})
                lname = js_name(left)
                logic["data_flow"].append({"file": label, "in": ctx, "target": lname, "op": node.get("operator", "="), "line": js_line(node)})
                prop = lname.split(".")[-1]
                if left.get("type") == "MemberExpression" and (prop in DOM_WRITE_PROPS or ".style." in lname or lname.startswith("on") or prop.startswith("on")):
                    if prop.startswith("on") and prop != "onload":
                        logic["events"].append({"file": label, "target": js_target_of({"object": left.get("object")}) or lname.rsplit(".", 1)[0],
                                                "event": prop, "handler": js_name(node.get("right")) or "anon@L{0}".format(js_line(node)), "line": js_line(node), "via": "property"})
                    else:
                        logic["dom_writes"].append({"file": label, "in": ctx, "target": lname.rsplit(".", 1)[0], "op": "set " + prop, "line": js_line(node)})
            if t == "VariableDeclarator":
                logic["data_flow"].append({"file": label, "in": ctx, "target": js_name(node.get("id")), "op": "declare", "line": js_line(node)})
            if t in ("ImportDeclaration",):
                logic["modules"].append({"file": label, "kind": "import", "module": js_lit(node.get("source"))})
            if t in ("ExportNamedDeclaration", "ExportDefaultDeclaration"):
                logic["modules"].append({"file": label, "kind": "export", "module": t})
            if t in CF_TYPES:
                cf[ctx][t] += 1
            if t == "AwaitExpression":
                cf[ctx]["await"] += 1
            return fn_ctx
        js_walk(tree, "(top)", visitor)
        for fn, c in cf.items():
            logic["control_flow"].append({"file": label, "fn": fn, **{k: v for k, v in c.items()}})
    return logic

def analyze_js_regex(src, label, logic):
    for m in re.finditer(r"function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)", src):
        logic["functions"].append({"file": label, "name": m.group(1), "params": m.group(2).strip(), "line": src[:m.start()].count("\n") + 1, "async": False, "kind": "regex"})
    for m in re.finditer(r"(const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(async\s*)?(\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>", src):
        logic["functions"].append({"file": label, "name": m.group(2), "params": m.group(4).strip("()"), "line": src[:m.start()].count("\n") + 1, "async": bool(m.group(3)), "kind": "regex-arrow"})
    for m in re.finditer(r"addEventListener\(\s*['\"](\w+)['\"]\s*,\s*([A-Za-z_$][\w$]*)?", src):
        logic["events"].append({"file": label, "target": "?", "event": m.group(1), "handler": m.group(2) or "anon", "line": src[:m.start()].count("\n") + 1, "via": "regex"})
    for m in re.finditer(r"\b(fetch|axios\.\w+|\$\.ajax|\$\.get|\$\.post)\(\s*['\"`]([^'\"`]+)", src):
        logic["api_calls"].append({"file": label, "in": "?", "call": m.group(1), "url": m.group(2), "line": src[:m.start()].count("\n") + 1})

# ================================================================ CSS
def analyze_css(sheets):
    out = {"rules": [], "classes": Counter(), "layout": [], "media": [], "animations": [], "cascade": {}, "parse_errors": []}
    specs, important, prop_dup = [], 0, defaultdict(list)
    for sh in sheets:
        css = sh.get("content") or ""
        if not css.strip():
            continue
        label = sh.get("src", "(inline)")
        if not HAS_TINYCSS:
            analyze_css_regex(css, label, out)
            continue
        try:
            rules = tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True)
        except Exception:
            out["parse_errors"].append(label)
            continue

        def handle_rule(rule, media=""):
            nonlocal important
            if rule.type == "qualified-rule":
                sel = tinycss2.serialize(rule.prelude).strip()
                decls = {}
                for d in tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True):
                    if d.type == "declaration":
                        decls[d.lower_name] = tinycss2.serialize(d.value).strip()
                        if d.important:
                            important += 1
                        prop_dup[(sel, d.lower_name)].append(label)
                spec = (sel.count("#"), sel.count(".") + sel.count("[") + sel.count(":"), len(re.findall(r"(^|[\s>+~])[a-zA-Z]", sel)))
                specs.append((sel, spec))
                for c in re.findall(r"\.([A-Za-z_-][\w-]*)", sel):
                    out["classes"][c] += 1
                lay = {k: v for k, v in decls.items() if k in LAYOUT_PROPS}
                out["rules"].append({"file": label, "media": media, "selector": sel, "props": len(decls), "spec": "{0},{1},{2}".format(*spec)})
                if lay:
                    out["layout"].append({"file": label, "selector": sel, "layout": "; ".join("{0}:{1}".format(k, v) for k, v in lay.items())})
                if "animation" in decls or "transition" in decls or "animation-name" in decls:
                    out["animations"].append({"file": label, "selector": sel, "kind": "usage", "value": decls.get("animation", decls.get("transition", decls.get("animation-name", "")))})
            elif rule.type == "at-rule":
                kw = rule.lower_at_keyword
                prelude = tinycss2.serialize(rule.prelude).strip()
                if kw == "media" and rule.content is not None:
                    inner = tinycss2.parse_rule_list(rule.content, skip_comments=True, skip_whitespace=True)
                    out["media"].append({"file": label, "query": prelude, "rules": len([r for r in inner if r.type == "qualified-rule"])})
                    for r in inner:
                        handle_rule(r, media=prelude)
                elif kw == "keyframes" or kw.endswith("keyframes"):
                    out["animations"].append({"file": label, "selector": "@" + kw + " " + prelude, "kind": "keyframes", "value": ""})
                else:
                    out["rules"].append({"file": label, "media": media, "selector": "@" + kw + " " + clip(prelude, 60), "props": 0, "spec": "-"})
        for r in rules:
            handle_rule(r)
    if specs:
        specs.sort(key=lambda x: x[1], reverse=True)
        dups = [k for k, v in prop_dup.items() if len(v) > 1]
        out["cascade"] = {"rule_count": len(specs), "important_count": important, "max_specificity": "{0} ({1},{2},{3})".format(specs[0][0], *specs[0][1]),
                          "duplicate_declarations": len(dups), "dup_examples": "; ".join("{0}{{{1}}}".format(s, p) for s, p in dups[:5])}
    return out

def analyze_css_regex(css, label, out):
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
        sel = m.group(1).strip()
        if sel.startswith("@"):
            out["media"].append({"file": label, "query": clip(sel, 60), "rules": 0})
            continue
        out["rules"].append({"file": label, "media": "", "selector": clip(sel, 60), "props": m.group(2).count(";"), "spec": "regex"})
        for c in re.findall(r"\.([A-Za-z_-][\w-]*)", sel):
            out["classes"][c] += 1

# ================================================================ content -> Markdown (MS markitdown)
_MID = None
def html_to_markdown(path, raw):
    global _MID
    if HAS_MARKITDOWN:
        try:
            if _MID is None:
                _MID = MarkItDown(enable_plugins=False)
            res = _MID.convert(str(path))
            txt = getattr(res, "markdown", None) or getattr(res, "text_content", "")
            return txt, "markitdown"
        except Exception as e:
            log("WARN", "markitdown failed on {0}: {1}".format(path, e))
    if HAS_MARKDOWNIFY:
        try:
            return _markdownify(raw, heading_style="ATX", strip=["script", "style"]), "markdownify"
        except Exception:
            pass
    if HAS_BS4:
        s = parse_html(raw)
        for t in s(["script", "style"]):
            t.decompose()
        return s.get_text("\n", strip=True), "bs4-text"
    return re.sub(r"<[^>]+>", " ", raw), "regex"

# ================================================================ UI behavior model
def build_ui_behavior_model(dom_structure, components, dom_events, js_logic):
    fn_index = defaultdict(lambda: {"calls": [], "api": [], "dom": []})
    for c in js_logic["calls"]:
        fn_index[c["in"]]["calls"].append(c["callee"])
    for a in js_logic["api_calls"]:
        fn_index[a["in"]]["api"].append("{0} {1}".format(a["call"], a["url"]))
    for d in js_logic["dom_writes"]:
        fn_index[d["in"]]["dom"].append("{0} {1}".format(d["op"], d["target"]))
    fn_names = {f["name"] for f in js_logic["functions"]}

    def resolve(fn, seen=None, depth=0):
        seen = seen or set()
        api, dom = list(fn_index[fn]["api"]), list(fn_index[fn]["dom"])
        if depth > 3:
            return api, dom
        for callee in fn_index[fn]["calls"]:
            base = callee.split(".")[-1].rstrip("()")
            if base in fn_names and base not in seen:
                seen.add(base)
                a2, d2 = resolve(base, seen, depth + 1)
                api += a2
                dom += d2
        return api, dom

    chains = []
    for e in dom_events:
        fn = e["fn"] or "(inline)"
        api, dom = resolve(fn) if fn in fn_names else ([], [])
        chains.append({"trigger": e["selector"], "event": e["event"], "handler": fn, "api": " ; ".join(dict.fromkeys(api)) or "-", "dom": " ; ".join(dict.fromkeys(dom)) or "-", "src": "html-attr"})
    for e in js_logic["events"]:
        fn = e["handler"]
        api, dom = resolve(fn)
        chains.append({"trigger": e["target"] or "?", "event": e["event"], "handler": fn, "api": " ; ".join(dict.fromkeys(api)) or "-", "dom": " ; ".join(dict.fromkeys(dom)) or "-", "src": e["via"]})
    forms = [c for c in components if c["tag"] == "form"]
    form_flows = [{"form": f["selector"], "submit": next((c["handler"] for c in chains if c["event"] in ("onsubmit", "submit") and (c["trigger"] == f["selector"] or f["id"] and f["id"] in c["trigger"])), "-"),
                   "inputs": f["children"]} for f in forms]
    states = sorted({d["target"] for d in js_logic["data_flow"] if d["op"] != "declare" and "." not in d["target"] and d["target"]})
    return {"chains": chains, "forms": form_flows, "state_vars": states}

def mermaid_ui(chains, limit=40):
    if not chains:
        return ""
    lines = ["```mermaid", "flowchart LR"]
    seen = set()
    for c in chains[:limit]:
        t = "T_" + safe_id(c["trigger"]); h = "H_" + safe_id(c["handler"])
        if t not in seen:
            lines.append('  {0}["{1}"]'.format(t, clip(c["trigger"], 30).replace('"', "'"))); seen.add(t)
        if h not in seen:
            lines.append('  {0}(("{1}"))'.format(h, clip(c["handler"], 30).replace('"', "'"))); seen.add(h)
        lines.append("  {0} -- {1} --> {2}".format(t, c["event"].replace("on", "", 1) if c["event"].startswith("on") else c["event"], h))
        for a in [x for x in c["api"].split(" ; ") if x != "-"][:3]:
            a_id = "A_" + safe_id(a)
            if a_id not in seen:
                lines.append('  {0}[/"{1}"/]'.format(a_id, clip(a, 30).replace('"', "'"))); seen.add(a_id)
            lines.append("  {0} --> {1}".format(h, a_id))
        for d in [x for x in c["dom"].split(" ; ") if x != "-"][:3]:
            d_id = "D_" + safe_id(d)
            if d_id not in seen:
                lines.append('  {0}[["{1}"]]'.format(d_id, clip(d, 30).replace('"', "'"))); seen.add(d_id)
            lines.append("  {0} -.-> {1}".format(h, d_id))
    lines.append("```")
    return "\n".join(lines)

# ================================================================ read_html_ui / read_ui_logic
def read_html_ui_and_logic(path):
    raw = load_file(path)
    base_dir = Path(path).parent
    if not HAS_BS4:
        raise RuntimeError("beautifulsoup4 missing")
    soup = parse_html(raw)
    nodes = soup.find_all(True)
    inline_js, ext_js = collect_assets(soup, base_dir, "script", "src", lambda t: (t.get("type") or "text/javascript").lower() in ("text/javascript", "module", "application/javascript", "text/babel"))
    inline_css, ext_css = collect_assets(soup, base_dir, "style", "href", lambda t: True)
    _, ext_links = collect_assets(soup, base_dir, "link", "href", lambda t: "stylesheet" in (t.get("rel") or []))
    ext_css += ext_links
    dom_structure = build_dom_structure(soup)
    components = extract_components(soup)
    dom_events = extract_dom_events(soup)
    js_logic = analyze_js(inline_js + ext_js)
    css_logic = analyze_css(inline_css + ext_css)
    content_md, content_engine = html_to_markdown(path, raw)
    ui_behavior = build_ui_behavior_model(dom_structure, components, dom_events, js_logic)
    attr_stats = Counter()
    for n in nodes:
        for k in n.attrs:
            attr_stats["data-*" if k.startswith("data-") else ("on*" if k.startswith("on") else k)] += 1
    return {"path": str(path), "raw_len": len(raw), "node_count": len(nodes), "attr_stats": attr_stats,
            "dom_structure": dom_structure, "components": components, "events": dom_events,
            "inline_scripts": inline_js, "external_scripts": ext_js, "inline_styles": inline_css, "external_stylesheets": ext_css,
            "js_logic": js_logic, "css_logic": css_logic, "ui_behavior": ui_behavior,
            "content_md": content_md, "content_engine": content_engine, "title": (soup.title.get_text(strip=True) if soup.title else "")}

def md_ui(model):
    p = Path(model["path"])
    js, css, ub = model["js_logic"], model["css_logic"], model["ui_behavior"]
    md = ["# UI Architecture — {0}".format(p.name), "",
          "- **Path**: `{0}`  ".format(p), "- **Title**: {0}  ".format(model["title"] or "-"),
          "- **Size**: {0:,} chars · **DOM nodes**: {1} · **max depth**: {2}  ".format(model["raw_len"], model["node_count"], model["dom_structure"]["max_depth"]),
          "- **Scripts**: {0} inline / {1} external · **Styles**: {2} inline / {3} external  ".format(len(model["inline_scripts"]), len(model["external_scripts"]), len(model["inline_styles"]), len(model["external_stylesheets"])),
          "- **Content engine**: {0}  ".format(model["content_engine"]), "", "## 1. DOM Structure (depth ≤ 6)", "",
          "Top tags: " + ", ".join("`{0}`×{1}".format(t, c) for t, c in model["dom_structure"]["tag_counter"].most_common(15)), "", "```text",
          *model["dom_structure"]["tree"], "```", "",
          "## 2. UI Components ({0})".format(len(model["components"])), "",
          md_table(["selector", "tag", "id", "class", "role", "data-*", "events", "children", "depth", "text"],
                   [[c["selector"], c["tag"], c["id"], clip(c["class"], 40), c["role"], clip(c["data"], 40), c["events"], c["children"], c["depth"], c["text"]] for c in model["components"]]),
          "## 3. Events", "", "### 3.1 HTML inline handlers ({0})".format(len(model["events"])), "",
          md_table(["selector", "event", "handler", "fn"], [[e["selector"], e["event"], e["handler"], e["fn"]] for e in model["events"]]),
          "### 3.2 JS-bound events ({0})".format(len(js["events"])), "",
          md_table(["file", "target", "event", "handler", "via", "line"], [[e["file"], e["target"], e["event"], e["handler"], e["via"], e["line"]] for e in js["events"]]),
          "## 4. JS Logic", "", "### 4.1 Functions ({0})".format(len(js["functions"])), "",
          md_table(["file", "name", "params", "kind", "async", "line"], [[f["file"], f["name"], f["params"], f["kind"], f["async"], f["line"]] for f in js["functions"]]),
          "### 4.2 Function calls (top 60 callees)", "",
          md_table(["callee", "count", "called from"], [[k, v, ", ".join(sorted({c["in"] for c in js["calls"] if c["callee"] == k})[:6])] for k, v in Counter(c["callee"] for c in js["calls"]).most_common(60)]),
          "### 4.3 API calls ({0})".format(len(js["api_calls"])), "",
          md_table(["file", "in function", "call", "url", "line"], [[a["file"], a["in"], a["call"], a["url"], a["line"]] for a in js["api_calls"]]),
          "### 4.4 DOM writes ({0})".format(len(js["dom_writes"])), "",
          md_table(["file", "in function", "target", "op", "line"], [[d["file"], d["in"], d["target"], d["op"], d["line"]] for d in js["dom_writes"]]),
          "### 4.5 Control flow per function", "",
          md_table(["file", "function", "if", "for/while", "switch", "try", "await", "ternary"],
                   [[c["file"], c["fn"], c.get("IfStatement", 0), sum(c.get(k, 0) for k in ("ForStatement", "ForInStatement", "ForOfStatement", "WhileStatement", "DoWhileStatement")),
                     c.get("SwitchStatement", 0), c.get("TryStatement", 0), c.get("await", 0), c.get("ConditionalExpression", 0)] for c in js["control_flow"]]),
          "### 4.6 Data flow — assignments ({0}, top 80)".format(len(js["data_flow"])), "",
          md_table(["file", "in function", "target", "op", "line"], [[d["file"], d["in"], d["target"], d["op"], d["line"]] for d in js["data_flow"][:80]]),
          "### 4.7 Modules", "", md_table(["file", "kind", "module"], [[m["file"], m["kind"], m["module"]] for m in js["modules"]]),
          ("> JS parse fallback (regex) used for: " + ", ".join(js["parse_errors"]) + "\n" if js["parse_errors"] else ""),
          "## 5. CSS Logic", "", "### 5.1 Classes ({0} distinct)".format(len(css["classes"])), "",
          ", ".join("`.{0}`({1})".format(k, v) for k, v in css["classes"].most_common(80)) or "_(none)_", "",
          "### 5.2 Layout rules ({0})".format(len(css["layout"])), "", md_table(["file", "selector", "layout"], [[l["file"], clip(l["selector"], 50), clip(l["layout"], 110)] for l in css["layout"]]),
          "### 5.3 Cascade", "", md_table(["metric", "value"], [[k, v] for k, v in css["cascade"].items()]),
          "### 5.4 Media queries ({0})".format(len(css["media"])), "", md_table(["file", "query", "rules"], [[m["file"], m["query"], m["rules"]] for m in css["media"]]),
          "### 5.5 Animations / transitions ({0})".format(len(css["animations"])), "", md_table(["file", "selector", "kind", "value"], [[a["file"], clip(a["selector"], 50), a["kind"], clip(a["value"], 60)] for a in css["animations"]]),
          "### 5.6 All rules ({0})".format(len(css["rules"])), "", md_table(["file", "media", "selector", "props", "specificity"], [[r["file"], clip(r["media"], 30), clip(r["selector"], 60), r["props"], r["spec"]] for r in css["rules"]], 300),
          "## 6. UI Behavior Model (HTML + JS + CSS)", "", "### 6.1 Interaction chains: trigger → event → handler → API → DOM update", "",
          md_table(["trigger", "event", "handler", "API", "DOM update", "source"], [[c["trigger"], c["event"], c["handler"], clip(c["api"], 70), clip(c["dom"], 70), c["src"]] for c in ub["chains"]]),
          mermaid_ui(ub["chains"]), "", "### 6.2 Forms", "", md_table(["form", "submit handler", "child elements"], [[f["form"], f["submit"], f["inputs"]] for f in ub["forms"]]),
          "### 6.3 UI state variables (assigned in JS)", "", (", ".join("`{0}`".format(s) for s in ub["state_vars"][:120]) or "_(none)_"), "",
          "## 7. Asset resolution", "", md_table(["kind", "src", "status", "chars"], [[k, a["src"], a["status"], len(a["content"])] for k, lst in (("script", model["inline_scripts"] + model["external_scripts"]), ("style", model["inline_styles"] + model["external_stylesheets"])) for a in lst]),
          "## 8. Page content (Markdown via {0})".format(model["content_engine"]), "", "<!-- content start -->", ""]
    content = model["content_md"] or "_(empty)_"
    if len(content) > 60000:
        content = content[:60000] + "\n\n…(content clipped at 60,000 chars; {0:,} total)".format(len(model["content_md"]))
    md.append(content)
    md += ["", "<!-- content end -->", ""]
    return "\n".join(md)

# ================================================================ Backend: Python
def py_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return py_name(node.value) + "." + node.attr
    if isinstance(node, ast.Call):
        return py_name(node.func) + "()"
    if isinstance(node, ast.Subscript):
        return py_name(node.value) + "[]"
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return type(node).__name__

ROUTE_RE = re.compile(r"\.(route|get|post|put|delete|patch|websocket|api_route|head|options)$")

def read_backend_logic(path):
    raw = load_file(path)
    tree = ast.parse(raw, filename=str(path))
    functions, classes, imports, calls, api_routes, control_flow, data_flow = [], [], [], [], [], [], []
    pipeline = []
    CF = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith)

    def cf_stats(fn_node):
        c, maxd = Counter(), 0

        def rec(n, d):
            nonlocal maxd
            for ch in ast.iter_child_nodes(n):
                if isinstance(ch, CF):
                    c[type(ch).__name__] += 1
                    maxd = max(maxd, d + 1)
                    rec(ch, d + 1)
                elif isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                else:
                    rec(ch, d)
        rec(fn_node, 0)
        c["return"] = sum(isinstance(n, ast.Return) for n in ast.walk(fn_node))
        c["max_depth"] = maxd
        return c

    def df_stats(fn_node):
        assigned, used, params = set(), set(), [a.arg for a in fn_node.args.args + fn_node.args.kwonlyargs]
        for n in ast.walk(fn_node):
            if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                for t in targets:
                    for x in ast.walk(t):
                        if isinstance(x, ast.Name):
                            assigned.add(x.id)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                used.add(n.id)
        return {"params": params, "assigned": sorted(assigned), "unused_params": [p for p in params if p not in used and p not in ("self", "cls")],
                "returns": [py_name(n.value) if n.value is not None else "None" for n in ast.walk(fn_node) if isinstance(n, ast.Return)][:5]}

    def handle_fn(fn, cls=""):
        decos = [py_name(d.func) if isinstance(d, ast.Call) else py_name(d) for d in fn.decorator_list]
        doc = (ast.get_docstring(fn) or "").split("\n")[0]
        name = "{0}.{1}".format(cls, fn.name) if cls else fn.name
        functions.append({"name": name, "args": ", ".join(a.arg for a in fn.args.args), "line": fn.lineno, "async": isinstance(fn, ast.AsyncFunctionDef),
                          "decorators": ", ".join(decos), "doc": clip(doc, 70), "lines": (fn.end_lineno or fn.lineno) - fn.lineno + 1})
        for d in fn.decorator_list:
            if isinstance(d, ast.Call) and ROUTE_RE.search(py_name(d.func)):
                url = next((a.value for a in d.args if isinstance(a, ast.Constant) and isinstance(a.value, str)), "")
                methods = next((ast.unparse(k.value) for k in d.keywords if k.arg == "methods"), py_name(d.func).split(".")[-1].upper())
                api_routes.append({"decorator": py_name(d.func), "url": url, "methods": methods, "handler": name, "line": fn.lineno})
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                calls.append({"in": name, "callee": py_name(n.func), "line": n.lineno})
        control_flow.append({"fn": name, **cf_stats(fn)})
        data_flow.append({"fn": name, **df_stats(fn)})

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports += [{"kind": "import", "module": a.name, "as": a.asname or "", "line": node.lineno} for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports += [{"kind": "from", "module": "{0}.{1}".format(node.module or "", a.name), "as": a.asname or "", "line": node.lineno} for a in node.names]
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [m for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append({"name": node.name, "bases": ", ".join(py_name(b) for b in node.bases), "methods": len(methods), "line": node.lineno, "doc": clip(ast.get_docstring(node) or "", 70)})
            for m in methods:
                handle_fn(m, node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            handle_fn(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                tn = py_name(t)
                if re.search(r"(pipeline|stages|steps|phases|chain|sequence)", tn, re.I) and isinstance(node.value, (ast.List, ast.Tuple)):
                    pipeline.append({"name": tn, "line": node.lineno, "steps": [py_name(e) if not isinstance(e, ast.Constant) else str(e.value) for e in node.value.elts]})
    top_calls = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            top_calls.append(py_name(node.value.func))
        if isinstance(node, ast.If) and "__main__" in ast.unparse(node.test):
            for s in node.body:
                for n in ast.walk(s):
                    if isinstance(n, ast.Call):
                        top_calls.append(py_name(n.func))
    if top_calls:
        pipeline.append({"name": "(module-level / __main__ call order)", "line": 0, "steps": top_calls[:40]})
    defined = {f["name"].split(".")[-1] for f in functions}
    for fn in [f for f in functions if f["name"] in ("main", "run", "execute", "pipeline")]:
        seq = [c["callee"] for c in calls if c["in"] == fn["name"] and c["callee"].split(".")[-1].rstrip("()") in defined]
        if seq:
            pipeline.append({"name": "{0}() → defined-function call order".format(fn["name"]), "line": fn["line"], "steps": seq[:40]})
    return {"path": str(path), "lines": raw.count("\n") + 1, "functions": functions, "function_calls": calls, "classes": classes, "imports": imports,
            "control_flow": control_flow, "data_flow": data_flow, "api_routes": api_routes, "pipeline": pipeline}

def mermaid_chain(name, steps):
    if not steps:
        return ""
    lines = ["```mermaid", "flowchart LR"]
    prev = None
    for i, s in enumerate(steps[:30]):
        nid = "S{0}".format(i)
        lines.append('  {0}["{1}"]'.format(nid, clip(s, 28).replace('"', "'")))
        if prev:
            lines.append("  {0} --> {1}".format(prev, nid))
        prev = nid
    lines.append("```")
    return "\n".join(lines)

def md_backend(b):
    p = Path(b["path"])
    md = ["# Backend Architecture — {0}".format(p.name), "", "- **Path**: `{0}`  ".format(p), "- **Lines**: {0} · **functions**: {1} · **classes**: {2} · **imports**: {3} · **calls**: {4}  ".format(b["lines"], len(b["functions"]), len(b["classes"]), len(b["imports"]), len(b["function_calls"])), "",
          "## 1. Imports", "", md_table(["kind", "module", "as", "line"], [[i["kind"], i["module"], i["as"], i["line"]] for i in b["imports"]]),
          "## 2. Classes", "", md_table(["name", "bases", "methods", "line", "doc"], [[c["name"], c["bases"], c["methods"], c["line"], c["doc"]] for c in b["classes"]]),
          "## 3. Functions", "", md_table(["name", "args", "decorators", "async", "line", "len", "doc"], [[f["name"], clip(f["args"], 50), f["decorators"], f["async"], f["line"], f["lines"], f["doc"]] for f in b["functions"]]),
          "## 4. Function calls (top 80 callees)", "", md_table(["callee", "count", "called from"], [[k, v, ", ".join(sorted({c["in"] for c in b["function_calls"] if c["callee"] == k})[:6])] for k, v in Counter(c["callee"] for c in b["function_calls"]).most_common(80)]),
          "## 5. Control flow", "", md_table(["function", "if", "for", "while", "try", "with", "return", "max nesting"], [[c["fn"], c.get("If", 0), c.get("For", 0) + c.get("AsyncFor", 0), c.get("While", 0), c.get("Try", 0), c.get("With", 0) + c.get("AsyncWith", 0), c.get("return", 0), c.get("max_depth", 0)] for c in b["control_flow"]]),
          "## 6. Data flow", "", md_table(["function", "params", "assigned", "unused params", "returns"], [[d["fn"], clip(", ".join(d["params"]), 40), clip(", ".join(d["assigned"]), 60), ", ".join(d["unused_params"]), clip(", ".join(d["returns"]), 40)] for d in b["data_flow"]]),
          "## 7. API routes", "", md_table(["decorator", "url", "methods", "handler", "line"], [[r["decorator"], r["url"], r["methods"], r["handler"], r["line"]] for r in b["api_routes"]]),
          "## 8. Pipeline", ""]
    for pl in b["pipeline"]:
        md += ["### {0} (line {1})".format(pl["name"], pl["line"]), "", " → ".join("`{0}`".format(s) for s in pl["steps"]) or "_(empty)_", "", mermaid_chain(pl["name"], pl["steps"]), ""]
    if not b["pipeline"]:
        md.append("_(no pipeline structure detected)_")
    return "\n".join(md)

# ================================================================ Backend: JSON engine spec
def read_engine_json(path):
    raw = load_file(path)
    data = json.loads(raw)
    eng = data.get("engine", data) if isinstance(data, dict) else {}
    modules = eng.get("modules") if isinstance(eng, dict) else None
    pipeline = eng.get("pipeline") if isinstance(eng, dict) else None
    if not isinstance(modules, dict):
        return {"path": str(path), "kind": "json-generic", "keys": list(data.keys()) if isinstance(data, dict) else ["<list:{0}>".format(len(data))], "size": len(raw), "raw": data}
    producers, consumers, rows = {}, defaultdict(list), []
    for mname, m in modules.items():
        ins, outs, params = m.get("inputs", []), m.get("outputs", []), m.get("parameters", {})
        rows.append({"module": mname, "inputs": ins, "outputs": outs, "params": params})
        for o in outs:
            producers.setdefault(o, mname)
        for i in ins:
            consumers[i].append(mname)
    edges, external, dead = [], [], []
    for r in rows:
        for i in r["inputs"]:
            if i in producers:
                edges.append((producers[i], r["module"], i))
            else:
                external.append((r["module"], i))
    for o, prod in producers.items():
        if o not in consumers:
            dead.append((prod, o))
    order_issues = []
    if isinstance(pipeline, list):
        pos = {m: i for i, m in enumerate(pipeline)}
        for a, b, v in edges:
            if a in pos and b in pos and pos[a] > pos[b]:
                order_issues.append((a, b, v))
        missing = [m for m in modules if m not in pos]
        unknown = [m for m in pipeline if m not in modules]
    else:
        missing, unknown = list(modules), []
    return {"path": str(path), "kind": "engine-spec", "name": eng.get("name", ""), "version": eng.get("version", ""), "modules": rows, "pipeline": pipeline or [],
            "edges": edges, "external_inputs": external, "dead_outputs": dead, "order_issues": order_issues, "missing_in_pipeline": missing, "unknown_in_pipeline": unknown, "size": len(raw)}

def md_engine(e):
    p = Path(e["path"])
    if e["kind"] == "json-generic":
        return "\n".join(["# JSON — {0}".format(p.name), "", "- **Path**: `{0}` · **size**: {1:,}  ".format(p, e["size"]), "", "Top-level keys: " + ", ".join("`{0}`".format(k) for k in e["keys"][:60]), "", "```json", json.dumps(e["raw"], ensure_ascii=False, indent=2)[:20000], "```"])
    md = ["# Engine Spec — {0} v{1}".format(e["name"] or p.stem, e["version"]), "", "- **Path**: `{0}`  ".format(p), "- **Modules**: {0} · **pipeline steps**: {1} · **data edges**: {2}  ".format(len(e["modules"]), len(e["pipeline"]), len(e["edges"])), "",
          "## 1. Pipeline order", "", " → ".join("`{0}`".format(s) for s in e["pipeline"]) or "_(none)_", "", mermaid_chain("pipeline", e["pipeline"]), "",
          "## 2. Modules", "", md_table(["module", "inputs", "outputs", "parameters"], [[m["module"], clip(", ".join(m["inputs"]), 90), clip(", ".join(m["outputs"]), 90), json.dumps(m["params"], ensure_ascii=False) if m["params"] else ""] for m in e["modules"]]),
          "## 3. Data-flow graph (producer → consumer)", "", "```mermaid", "flowchart TD"]
    seen = set()
    for a, b, v in e["edges"]:
        for n in (a, b):
            if n not in seen:
                md.append('  {0}["{0}"]'.format(n)); seen.add(n)
        md.append("  {0} -- {1} --> {2}".format(a, v, b))
    for m, i in e["external_inputs"]:
        ext = "EXT_" + safe_id(i)
        if ext not in seen:
            md.append('  {0}(["{1} (external)"])'.format(ext, i)); seen.add(ext)
        if m not in seen:
            md.append('  {0}["{0}"]'.format(m)); seen.add(m)
        md.append("  {0} -.-> {1}".format(ext, m))
    md += ["```", "", "## 4. Fact validation of the spec", ""]
    md += [md_table(["check", "result", "detail"], [
        ["external inputs (no producer)", "{0} found".format(len(e["external_inputs"])) if e["external_inputs"] else "OK", "; ".join("{0} ← {1}".format(m, i) for m, i in e["external_inputs"])],
        ["dead outputs (never consumed)", "{0} found".format(len(e["dead_outputs"])) if e["dead_outputs"] else "OK", "; ".join("{0} → {1}".format(m, o) for m, o in e["dead_outputs"])],
        ["pipeline order vs data deps", "{0} violations".format(len(e["order_issues"])) if e["order_issues"] else "OK", "; ".join("{0} feeds {1} via {2} but runs after it".format(a, b, v) for a, b, v in e["order_issues"])],
        ["modules missing from pipeline", "{0}".format(len(e["missing_in_pipeline"])) if e["missing_in_pipeline"] else "OK", ", ".join(e["missing_in_pipeline"])],
        ["pipeline steps with no module", "{0}".format(len(e["unknown_in_pipeline"])) if e["unknown_in_pipeline"] else "OK", ", ".join(e["unknown_in_pipeline"])],
    ])]
    md += ["", "> external inputs = 必須由 data_loader 或外部來源補上的欄位；dead outputs = 有產出但無人消費 (可保留 DORMANT)；order violations = pipeline 順序與資料依賴衝突。", ""]
    return "\n".join(md)

# ================================================================ Backend: PowerShell (regex, lightweight)
def read_ps_logic(path):
    raw = load_file(path)
    funcs = [{"name": m.group(1), "line": raw[:m.start()].count("\n") + 1} for m in re.finditer(r"(?im)^\s*function\s+([\w-]+)", raw)]
    names = {f["name"] for f in funcs}
    calls = Counter(m.group(1) for m in re.finditer(r"(?<![\w-])([A-Z][a-z]+-[A-Za-z]+)(?![\w-])", raw))
    params = [m.group(1) for m in re.finditer(r"\[(?:switch|string|int|bool|object|array|string\[\]|hashtable)\]\s*\$(\w+)", raw)]
    internal = [(n, calls.get(n, 0)) for n in names]
    top_cmdlets = [(k, v) for k, v in calls.most_common(60) if k not in names]
    regions = [m.group(1).strip() for m in re.finditer(r"(?im)^\s*#region\s+(.*)$", raw)]
    return {"path": str(path), "lines": raw.count("\n") + 1, "functions": funcs, "params": params, "internal_calls": internal, "cmdlets": top_cmdlets, "regions": regions,
            "starts_process": raw.count("Start-Process"), "psi": raw.count("ProcessStartInfo"), "here_strings": len(re.findall(r"@['\"]\r?\n", raw))}

def md_ps(b):
    p = Path(b["path"])
    return "\n".join(["# PowerShell Architecture — {0}".format(p.name), "", "- **Path**: `{0}` · **lines**: {1} · **functions**: {2} · **params**: {3} · Start-Process: {4} · ProcessStartInfo: {5} · here-strings: {6}  ".format(p, b["lines"], len(b["functions"]), len(b["params"]), b["starts_process"], b["psi"], b["here_strings"]), "",
                      "## 1. Regions", "", "\n".join("- " + r for r in b["regions"]) or "_(none)_", "", "## 2. Functions", "", md_table(["name", "line", "internal call count"], [[f["name"], f["line"], dict(b["internal_calls"]).get(f["name"], 0)] for f in b["functions"]]),
                      "## 3. Parameters", "", ", ".join("`${0}`".format(x) for x in b["params"]) or "_(none)_", "", "## 4. Cmdlets used (top 60)", "", md_table(["cmdlet", "count"], [[k, v] for k, v in b["cmdlets"]]),
                      "## 5. Pipeline (function definition order)", "", mermaid_chain("ps", [f["name"] for f in b["functions"]])])

# ================================================================ standalone JS / CSS files
def md_js_file(path):
    raw = load_file(path)
    logic = analyze_js([{"src": Path(path).name, "content": raw}])
    model = {"path": str(path), "raw_len": len(raw), "node_count": 0, "attr_stats": Counter(), "dom_structure": {"tree": [], "tag_counter": Counter(), "max_depth": 0}, "components": [], "events": [],
             "inline_scripts": [], "external_scripts": [{"src": Path(path).name, "status": "file", "content": raw}], "inline_styles": [], "external_stylesheets": [],
             "js_logic": logic, "css_logic": analyze_css([]), "ui_behavior": build_ui_behavior_model(None, [], [], logic), "content_md": "_(standalone JS — no page content)_", "content_engine": "n/a", "title": ""}
    return md_ui(model), {"functions": len(logic["functions"]), "events": len(logic["events"]), "api": len(logic["api_calls"])}

def md_css_file(path):
    raw = load_file(path)
    css = analyze_css([{"src": Path(path).name, "content": raw}])
    model = {"path": str(path), "raw_len": len(raw), "node_count": 0, "attr_stats": Counter(), "dom_structure": {"tree": [], "tag_counter": Counter(), "max_depth": 0}, "components": [], "events": [],
             "inline_scripts": [], "external_scripts": [], "inline_styles": [], "external_stylesheets": [{"src": Path(path).name, "status": "file", "content": raw}],
             "js_logic": analyze_js([]), "css_logic": css, "ui_behavior": build_ui_behavior_model(None, [], [], analyze_js([])), "content_md": "_(standalone CSS)_", "content_engine": "n/a", "title": ""}
    return md_ui(model), {"rules": len(css["rules"]), "classes": len(css["classes"])}

# ================================================================ runner
def discover(targets, exts):
    files = []
    for t in targets:
        tp = Path(t)
        if tp.is_file():
            files.append(tp)
            continue
        if not tp.exists():
            log("WARN", "target missing: {0}".format(tp))
            continue
        for root, dirs, fnames in os.walk(tp):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for f in fnames:
                if Path(f).suffix.lower() in exts:
                    files.append(Path(root) / f)
    return sorted(set(files))

def html_report(out_dir, results, run_info):
    ok = [r for r in results if r["status"] == "OK"]
    bad = [r for r in results if r["status"] != "OK"]
    rows = "".join("<tr><td>{0}</td><td>{1}</td><td class='{2}'>{3}</td><td>{4}</td><td>{5}</td><td><a href='{6}'>{6}</a></td></tr>".format(
        _html.escape(r["file"]), r["type"], "ok" if r["status"] == "OK" else "bad", r["status"], _html.escape(r["summary"]), "{0:.2f}s".format(r["secs"]), _html.escape(r["md"])) for r in results)
    kinds = Counter(r["type"] for r in results)
    css = ("body{background:#0f1117;color:#e6e6e6;font-family:Segoe UI,Consolas,monospace;margin:0;padding:24px}h1{font-size:20px;margin:0 0 4px}.sub{color:#8a8f98;font-size:12px;margin-bottom:18px}"
           ".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}.card{background:#181b24;border:1px solid #2a2f3a;border-radius:8px;padding:12px}"
           ".card b{display:block;font-size:24px}.card span{color:#8a8f98;font-size:11px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border-bottom:1px solid #2a2f3a;padding:6px 8px;text-align:left;vertical-align:top}"
           "th{color:#8a8f98;font-weight:600}.ok{color:#c96b5a;font-weight:700}.bad{color:#5a9e6f;font-weight:700}a{color:#7fb3ff}.log{background:#0b0d12;border:1px solid #2a2f3a;border-radius:8px;padding:10px;font-size:11px;white-space:pre-wrap;max-height:300px;overflow:auto;color:#a9b1bd}"
           ".bar{height:8px;background:#2a2f3a;border-radius:4px;overflow:hidden;margin:6px 0 18px}.bar i{display:block;height:100%;background:linear-gradient(90deg,#c96b5a,#e0a15f)}.seal{float:right;border:1px solid #c96b5a;color:#c96b5a;border-radius:4px;padding:2px 8px;font-size:11px}")
    page = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA SuperHtml Parser Report</title><style>{css}</style></head><body>"
            "<span class='seal'>VSHP v{ver} · {stamp}</span><h1>VIA SuperHtml Parser Engine — 解析報告</h1><div class='sub'>HTML content + UI component + JS/CSS logic + backend (py/json/ps1) → Markdown · engines: bs4/{parser} · esprima={esp} · tinycss2={tc} · markitdown={mid}</div>"
            "<div class='bar'><i style='width:{pct}%'></i></div>"
            "<div class='cards'><div class='card'><b>{n}</b><span>files parsed</span></div><div class='card'><b>{ok}</b><span>OK</span></div><div class='card'><b>{bad}</b><span>failed</span></div><div class='card'><b>{secs:.1f}s</b><span>total time</span></div>"
            "{kindcards}</div><table><thead><tr><th>file</th><th>type</th><th>status</th><th>summary</th><th>time</th><th>markdown</th></tr></thead><tbody>{rows}</tbody></table>"
            "<h3 style='margin-top:24px'>Targets</h3><div class='log'>{targets}</div><h3>Run log</h3><div class='log'>{log}</div></body></html>").format(
        css=css, ver=VERSION, stamp=run_info["stamp"], parser=BS_PARSER, esp=HAS_ESPRIMA, tc=HAS_TINYCSS, mid=HAS_MARKITDOWN, pct=100 if results else 0, n=len(results), ok=len(ok), bad=len(bad), secs=time.time() - T0,
        kindcards="".join("<div class='card'><b>{1}</b><span>{0}</span></div>".format(k, v) for k, v in kinds.items()), rows=rows,
        targets=_html.escape("\n".join(run_info["targets"])), log=_html.escape("\n".join(run_info["log"])))
    (Path(out_dir) / "VIA_SuperHtmlParser_Report.html").write_text(page, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(description="VIA SuperHtml Parser Engine")
    ap.add_argument("--targets", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ext", nargs="*", default=None, help="extensions to include, e.g. .html .py")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    exts = set(a.ext) if a.ext else HTML_EXT | JS_EXT | CSS_EXT | PY_EXT | JSON_EXT | PS_EXT
    log("INFO", "VSHP v{0} · bs4={1}/{2} esprima={3} tinycss2={4} markitdown={5} markdownify={6}".format(VERSION, HAS_BS4, BS_PARSER, HAS_ESPRIMA, HAS_TINYCSS, HAS_MARKITDOWN, HAS_MARKDOWNIFY))
    files = discover(a.targets, exts)
    log("INFO", "discovered {0} files".format(len(files)))
    results, run_log = [], []
    for i, f in enumerate(files, 1):
        t = time.time()
        ext = f.suffix.lower()
        stem = "{0}__{1}_{2}".format(f.stem, ext.lstrip("."), sha8(str(f.resolve())))
        md_path = out / (stem + ".md")
        try:
            if ext in HTML_EXT:
                model = read_html_ui_and_logic(f)
                md_text, typ = md_ui(model), "html-ui"
                summary = "nodes={0} components={1} js-fn={2} events={3} css-rules={4} chains={5}".format(model["node_count"], len(model["components"]), len(model["js_logic"]["functions"]), len(model["events"]) + len(model["js_logic"]["events"]), len(model["css_logic"]["rules"]), len(model["ui_behavior"]["chains"]))
            elif ext in JS_EXT:
                md_text, s = md_js_file(f); typ = "js"; summary = " ".join("{0}={1}".format(k, v) for k, v in s.items())
            elif ext in CSS_EXT:
                md_text, s = md_css_file(f); typ = "css"; summary = " ".join("{0}={1}".format(k, v) for k, v in s.items())
            elif ext in PY_EXT:
                b = read_backend_logic(f); md_text, typ = md_backend(b), "py-backend"
                summary = "fn={0} classes={1} imports={2} routes={3} pipelines={4}".format(len(b["functions"]), len(b["classes"]), len(b["imports"]), len(b["api_routes"]), len(b["pipeline"]))
            elif ext in JSON_EXT:
                e = read_engine_json(f); md_text, typ = md_engine(e), e["kind"]
                summary = "modules={0} edges={1} external={2} dead={3} order-issues={4}".format(len(e["modules"]), len(e["edges"]), len(e["external_inputs"]), len(e["dead_outputs"]), len(e["order_issues"])) if e["kind"] == "engine-spec" else "keys={0}".format(len(e["keys"]))
            elif ext in PS_EXT:
                b = read_ps_logic(f); md_text, typ = md_ps(b), "ps1"
                summary = "fn={0} params={1} regions={2}".format(len(b["functions"]), len(b["params"]), len(b["regions"]))
            else:
                continue
            header = "<!-- VIA SuperHtml Parser v{0} · {1} · source={2} -->\n\n".format(VERSION, time.strftime("%Y-%m-%d %H:%M:%S"), f)
            md_path.write_text(header + md_text, encoding="utf-8")
            status = "OK"
        except Exception as ex:
            status, typ, summary = "FAIL", ext.lstrip("."), "{0}: {1}".format(type(ex).__name__, clip(str(ex), 120))
            md_path.write_text("# FAILED — {0}\n\n```\n{1}\n```".format(f, traceback.format_exc()), encoding="utf-8")
        secs = time.time() - t
        results.append({"file": str(f), "type": typ, "status": status, "summary": summary, "secs": secs, "md": md_path.name})
        line = "[{0}/{1}] {2} {3} ({4:.2f}s) {5}".format(i, len(files), status, f.name, secs, summary)
        run_log.append(line)
        log("PROG", line)
    index = ["# VIA SuperHtml Parser — INDEX", "", "Generated {0} · {1} files".format(time.strftime("%Y-%m-%d %H:%M:%S"), len(results)), "",
             md_table(["file", "type", "status", "summary", "markdown"], [[r["file"], r["type"], r["status"], r["summary"], "[{0}]({0})".format(r["md"])] for r in results], 2000)]
    (out / "INDEX.md").write_text("\n".join(index), encoding="utf-8")
    (out / "run_manifest.json").write_text(json.dumps({"version": VERSION, "targets": a.targets, "results": results, "seconds": time.time() - T0}, ensure_ascii=False, indent=2), encoding="utf-8")
    html_report(out, results, {"stamp": time.strftime("%Y-%m-%d %H:%M:%S"), "targets": a.targets, "log": run_log})
    log("DONE", "{0} files → {1} · OK={2} FAIL={3} · {4:.1f}s".format(len(results), out, sum(r["status"] == "OK" for r in results), sum(r["status"] != "OK" for r in results), time.time() - T0))

if __name__ == "__main__":
    main()
'@
        $corePath = Save-AppendOnly -Path (Join-Path $dirs.engine 'via_superhtml_parser.py') -Content $engineSrc
        Write-Log -Message ('core engine v{0} = {1} ({2:N0} bytes)' -f $script:CoreVersion, $corePath, $engineSrc.Length) -Level 'OK'

        $bridgeSrc = @'
# -*- coding: utf-8 -*-
# VIA SuperHtml Parser — NLP Bridge v1.1.0 (append-only companion of via_superhtml_parser.py v1.0.0)
# Feeds VSHP's AST/DOM results INTO VIA NLP One Engine (v1.5) — never re-parses, so there is one truth.
#   ④ function intent      -> via_nlp_engine.function_classifier.FunctionClassifier  (VIA_FUNCTION_CLASSIFICATION/1.0)
#   ② content -> fields    -> via_nlp_engine.text_ops.TextProcessor (entities / keywords / rules / doc type)
#   ① component canonical  -> ui_component_lexicon.json (bilingual) + token/difflib match, needs_review flagged
#   ③ engine-JSON gap hints -> difflib name similarity (no model needed)
# If via_nlp_engine is not importable, ① and ③ still run; ② and ④ are reported as unavailable (no fake output).
import re, json, difflib, hashlib, importlib
from pathlib import Path
from collections import Counter

BRIDGE_VERSION = "1.1.0"
SECTION_TITLE = "## 9. Semantic Layer (VIA NLP One Engine bridge v{0})".format(BRIDGE_VERSION)

DEFAULT_UI_LEXICON = {
    "version": "1.0.0", "schema": "VIA_UI_COMPONENT_LEXICON/1.0", "locale": "zh-TW",
    "note": "append-only: add synonyms, never remove canonicals; VSHP bridge matches tag/id/class/data-*/role/text against these",
    "canonicals": {
        "navigation":       {"zh": "導覽列", "en": "Navigation", "synonyms": ["nav", "navbar", "menu", "breadcrumb", "導覽", "選單"]},
        "header":           {"zh": "頁首", "en": "Header", "synonyms": ["header", "masthead", "banner", "title-bar", "頁首", "標題列"]},
        "footer":           {"zh": "頁尾", "en": "Footer", "synonyms": ["footer", "copyright", "頁尾"]},
        "toolbar":          {"zh": "工具列", "en": "Toolbar", "synonyms": ["toolbar", "actions", "controls", "control-bar", "工具列", "控制"]},
        "panel":            {"zh": "面板", "en": "Panel", "synonyms": ["panel", "pane", "section", "container", "box", "面板", "區塊"]},
        "card":             {"zh": "卡片", "en": "Card", "synonyms": ["card", "tile", "widget", "卡片"]},
        "kpi_metric":       {"zh": "KPI 指標", "en": "KPI / Metric", "synonyms": ["kpi", "metric", "stat", "score", "rate", "指標", "成功率", "勝率"]},
        "table_grid":       {"zh": "表格", "en": "Table / Grid", "synonyms": ["table", "grid", "datagrid", "thead", "tbody", "row", "表格", "清單"]},
        "form":             {"zh": "表單", "en": "Form", "synonyms": ["form", "fieldset", "表單"]},
        "input_control":    {"zh": "輸入控制項", "en": "Input control", "synonyms": ["input", "select", "textarea", "field", "symbol", "ticker", "window", "輸入", "代碼"]},
        "button_action":    {"zh": "動作按鈕", "en": "Action button", "synonyms": ["button", "btn", "run", "submit", "execute", "apply", "按鈕", "執行"]},
        "status_indicator": {"zh": "狀態指示", "en": "Status indicator", "synonyms": ["status", "state", "badge", "seal", "live", "idle", "phase", "狀態", "階段", "封印"]},
        "chart":            {"zh": "圖表", "en": "Chart", "synonyms": ["chart", "plot", "graph", "canvas", "svg", "sparkline", "圖表", "走勢"]},
        "modal_dialog":     {"zh": "對話框", "en": "Modal / Dialog", "synonyms": ["modal", "dialog", "popup", "overlay", "對話框", "彈窗"]},
        "tabs":             {"zh": "分頁籤", "en": "Tabs", "synonyms": ["tab", "tabs", "tablist", "頁籤"]},
        "sidebar":          {"zh": "側欄", "en": "Sidebar", "synonyms": ["sidebar", "aside", "drawer", "側欄"]},
        "list":             {"zh": "列表", "en": "List", "synonyms": ["list", "ul", "ol", "li", "item", "列表"]},
        "progress":         {"zh": "進度", "en": "Progress", "synonyms": ["progress", "bar", "loader", "spinner", "進度"]},
        "console_log":      {"zh": "主控台 / 日誌", "en": "Console / Log", "synonyms": ["console", "log", "terminal", "output", "主控台", "日誌"]},
        "media":            {"zh": "媒體", "en": "Media", "synonyms": ["video", "audio", "iframe", "img", "image", "媒體"]},
    },
}

def _sha8(s):
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:8]

def _esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")

def _table(headers, rows, max_rows=300):
    if not rows:
        return "_(none)_\n"
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(_esc(c) for c in r) + " |" for r in rows[:max_rows]]
    if len(rows) > max_rows:
        out.append("| ... | {0} more | |".format(len(rows) - max_rows))
    return "\n".join(out) + "\n"

def _tokens(s):
    s = str(s or "")
    latin = [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9]*", s)]
    zh = re.findall(r"[\u4e00-\u9fff]{2,}", s)
    return latin, zh

class NlpBridge:
    def __init__(self, nlp_root=None, ui_lexicon_path=None, log=None):
        self.log = log or (lambda k, m: None)
        self.available, self.reason, self.engine_version, self.lexicon_path = False, "", "", ""
        self.text = self.fn_classifier = None
        self.ui_lexicon = DEFAULT_UI_LEXICON
        if ui_lexicon_path and Path(ui_lexicon_path).exists():
            try:
                self.ui_lexicon = json.loads(Path(ui_lexicon_path).read_text(encoding="utf-8"))
            except Exception as e:
                self.log("WARN", "ui lexicon unreadable ({0}); using built-in".format(e))
        try:
            import via_nlp_engine
            from via_nlp_engine.text_ops import TextProcessor
            from via_nlp_engine.function_classifier import FunctionClassifier
            self.engine_version = getattr(via_nlp_engine, "__version__", "?")
            roots = [Path(nlp_root)] if nlp_root else []
            try:
                from via_nlp_engine.config import PROJECT_ROOT
                roots.append(Path(PROJECT_ROOT))
            except Exception:
                pass
            lex = next((r / "data" / "lexicon" / "ssot_lexicon.json" for r in roots if (r / "data" / "lexicon" / "ssot_lexicon.json").exists()), None)
            if lex is None:
                raise FileNotFoundError("ssot_lexicon.json not found under {0}".format([str(r) for r in roots]))
            self.lexicon_path = str(lex)
            try:
                import jieba
                jieba.setLogLevel(60)
            except Exception:
                pass
            self.text = TextProcessor(lex)
            self.fn_classifier = FunctionClassifier()
            self.available = True
        except Exception as e:
            self.reason = "{0}: {1}".format(type(e).__name__, e)
        self.log("INFO", "NLP bridge v{0}: via_nlp_engine={1} lexicon={2}{3}".format(BRIDGE_VERSION, self.engine_version or "absent", self.lexicon_path or "-", "" if self.available else " · unavailable: " + self.reason))

    # ---------------------------------------------------------------- ④ function intent
    def classify_functions(self, source_label, language, functions, calls, imports, docs=None):
        if not self.available or not functions:
            return []
        docs = docs or {}
        calls_by_fn = {}
        for c in calls:
            calls_by_fn.setdefault(c.get("in", ""), []).append(c.get("callee", ""))
        names = [f if isinstance(f, str) else f.get("name", "") for f in functions]
        names = [n for n in names if n and not n.startswith("anon@")]
        block = {"code_id": "VSHP-{0}".format(_sha8(source_label)), "language": language, "sha256": None,
                 "engine_spec": {"functions": names, "imports": list(imports),
                                 "function_contracts": [{"name": n, "docstring": docs.get(n, ""), "calls": calls_by_fn.get(n, []) + calls_by_fn.get(n.split(".")[-1], [])} for n in names]}}
        try:
            return self.fn_classifier.build({"code_blocks": [block]}).get("records", [])
        except Exception as e:
            self.log("WARN", "function classification failed for {0}: {1}".format(source_label, e))
            return []

    # ---------------------------------------------------------------- ② content -> fields
    def content_semantics(self, text):
        if not self.available or not text or not text.strip():
            return None
        try:
            t = self.text.sanitize(text)[:200000]
            dt, dconf = self.text.detect_document_type(t)
            return {"language": self.text.detect_language(t), "doc_type": dt, "doc_type_conf": dconf,
                    "entities": self.text.entities(t), "keywords": self.text.keywords(t, 20), "rules": self.text.classify_rules(t),
                    "summary": self.text.summarize(t, 4)}
        except Exception as e:
            self.log("WARN", "content semantics failed: {0}".format(e))
            return None

    # ---------------------------------------------------------------- ① component canonical
    def component_canonicals(self, components):
        canon = self.ui_lexicon.get("canonicals", {})
        rows = []
        for c in components:
            structural = " ".join([c.get("tag", ""), c.get("id", ""), c.get("class", ""), c.get("role", ""), c.get("data", "")])
            s_latin, s_zh = _tokens(structural)
            t_latin, t_zh = _tokens(c.get("text", "")[:40])
            best, best_score, best_hit = "UNMAPPED", 0.0, ""
            for name, spec in canon.items():
                syns = [s.lower() for s in spec.get("synonyms", [])] + [name.lower(), name.replace("_", "-").lower()]
                ascii_syns = [s for s in syns if s.isascii()]
                score, hit = 0.0, ""
                # structural evidence (tag/id/class/role/data-*): full weight; text evidence: 0.7 weight
                for latin, zh, w, tag in ((s_latin, s_zh, 1.0, ""), (t_latin, t_zh, 0.7, "text:")):
                    for tok in latin:
                        if tok in syns:
                            if w > score:
                                score, hit = w, tag + tok
                            continue
                        m = difflib.get_close_matches(tok, ascii_syns, n=1, cutoff=0.82)
                        if m and len(tok) >= 4:
                            r = difflib.SequenceMatcher(None, tok, m[0]).ratio() * w
                            if r > score:
                                score, hit = r, "{0}{1}≈{2}".format(tag, tok, m[0])
                    for z in zh:
                        for s in syns:
                            if not s.isascii() and (s in z or z in s) and 0.95 * w > score:
                                score, hit = 0.95 * w, tag + s
                if score > best_score:
                    best, best_score, best_hit = name, score, hit
            rows.append({"selector": c.get("selector", ""), "canonical": best, "zh": canon.get(best, {}).get("zh", "-"), "score": round(best_score, 2),
                         "evidence": best_hit, "needs_review": best == "UNMAPPED" or best_score < 0.8})
        return rows

    # ---------------------------------------------------------------- ③ engine-JSON gap hints
    def engine_gap_suggestions(self, engine_model):
        if engine_model.get("kind") != "engine-spec":
            return [], []
        mods = engine_model["modules"]
        pos = {m: i for i, m in enumerate(engine_model.get("pipeline", []))}
        outputs = [(o, m["module"]) for m in mods for o in m["outputs"]]
        inputs = [(i, m["module"]) for m in mods for i in m["inputs"]]

        def sim(a, b):
            ta, tb = set(a.split("_")), set(b.split("_"))
            jac = len(ta & tb) / max(1, len(ta | tb))
            return round(0.5 * jac + 0.5 * difflib.SequenceMatcher(None, a, b).ratio(), 2)

        def upstream(a, b):   # is module a strictly before module b in pipeline (unknown order => allow)
            return pos.get(a, -1) < pos.get(b, 10**6) if a in pos and b in pos else a != b

        ext_rows = []
        for mod, inp in engine_model["external_inputs"]:
            cands = sorted(((sim(inp, o), o, om) for o, om in outputs if upstream(om, mod)), reverse=True)[:2]
            cands = [c for c in cands if c[0] >= 0.45]
            ext_rows.append({"module": mod, "input": inp, "candidates": "; ".join("{1} (from {2}, {0})".format(*c) for c in cands) or "-",
                             "hint": "上游 {0} 的 `{1}` 可能即此欄位 (命名不一致)；否則需新增產出模組".format(cands[0][2], cands[0][1]) if cands else "無相似上游產出 → 需由 data_loader 或外部來源供給", "needs_review": True})
        dead_rows = []
        for mod, out in engine_model["dead_outputs"]:
            c_in = sorted(((sim(out, i), i, im) for i, im in inputs if upstream(mod, im)), reverse=True)[:2]
            c_in = [c for c in c_in if c[0] >= 0.55]
            c_out = sorted(((sim(out, o), o, om) for o, om in outputs if upstream(mod, om)), reverse=True)[:2]
            c_out = [c for c in c_out if c[0] >= 0.55]
            in_wins = bool(c_in) and (not c_out or c_in[0][0] >= c_out[0][0])
            if in_wins:
                hint = "下游 {0} 的 input `{1}` 與此相似 → 疑似同一欄位、命名不一致".format(c_in[0][2], c_in[0][1])
            elif c_out:
                hint = "下游 {0} 產出 `{1}` 與此相似 → {0} 疑似漏列 input `{2}`".format(c_out[0][2], c_out[0][1], out)
            elif re.search(r"(rate|validation|score|state|phase|filter)$", out) or pos.get(mod, 0) == len(pos) - 1:
                hint = "終端輸出 (report/SSOT sink)，可標 DORMANT 保留"
            else:
                hint = "無下游消費者 → 標 DORMANT 或補接下游"
            cands = "; ".join(["in:{1} ({2}, {0})".format(*c) for c in c_in] + ["out:{1} ({2}, {0})".format(*c) for c in c_out])
            dead_rows.append({"module": mod, "output": out, "candidates": cands or "-", "hint": hint, "needs_review": True})
        return ext_rows, dead_rows

    # ---------------------------------------------------------------- section builder
    def section_md(self, kind, model):
        md = [SECTION_TITLE, "", "- **via_nlp_engine**: {0} · **status**: {1}{2}  ".format(self.engine_version or "absent", "available" if self.available else "unavailable", "" if self.available else " (" + self.reason + ")"),
              "- **ui lexicon**: {0} v{1} ({2} canonicals)  ".format(self.ui_lexicon.get("schema", "?"), self.ui_lexicon.get("version", "?"), len(self.ui_lexicon.get("canonicals", {}))),
              "- **rule**: bridge only *classifies* VSHP's AST/DOM output; nothing is re-parsed, nothing is auto-applied — every row with `needs_review=True` is a proposal.  ", ""]
        if kind in ("html-ui", "js", "css"):
            comps = model.get("components", [])
            rows = self.component_canonicals(comps) if comps else []
            md += ["### 9.1 Component → canonical (①)", "",
                   _table(["selector", "canonical", "zh", "score", "evidence", "needs_review"], [[r["selector"], r["canonical"], r["zh"], r["score"], r["evidence"], r["needs_review"]] for r in rows]),
                   "Canonical counts: " + (", ".join("`{0}`×{1}".format(k, v) for k, v in Counter(r["canonical"] for r in rows).most_common()) or "_(none)_"), ""]
            js = model.get("js_logic", {})
            fns = js.get("functions", [])
            files = sorted({f["file"] for f in fns})
            recs = []
            for fl in files:
                recs += self.classify_functions(fl, "javascript", [f for f in fns if f["file"] == fl], [c for c in js.get("calls", []) if c["file"] == fl], [m["module"] for m in js.get("modules", []) if m["file"] == fl])
            md += ["### 9.2 JS function intent (④ VIA_FUNCTION_CLASSIFICATION/1.0)", "", self._fn_table(recs, fns)]
            md += ["### 9.3 Interaction chain intent", "", self._chain_table(model.get("ui_behavior", {}).get("chains", []), recs)]
            md += ["### 9.4 Page content semantics (②)", "", self._content_table(self.content_semantics(model.get("content_md", "") if model.get("content_engine", "n/a") != "n/a" else ""))]
        elif kind == "py-backend":
            fns = model.get("functions", [])
            docs = {f["name"]: f.get("doc", "") for f in fns}
            recs = self.classify_functions(model["path"], "python", fns, model.get("function_calls", []), [i["module"] for i in model.get("imports", [])], docs)
            md += ["### 9.2 Python function intent (④ VIA_FUNCTION_CLASSIFICATION/1.0)", "", self._fn_table(recs, fns)]
            if model.get("pipeline"):
                md += ["### 9.3 Pipeline step intent", "", self._pipeline_intent(model["pipeline"], recs)]
        elif kind == "ps1":
            fns = [{"name": f["name"]} for f in model.get("functions", [])]
            calls = [{"in": "(script)", "callee": k} for k, _ in model.get("cmdlets", [])]
            recs = self.classify_functions(model["path"], "powershell", fns, calls, [])
            md += ["### 9.2 PowerShell function intent (④)", "", self._fn_table(recs, fns)]
        elif kind == "engine-spec":
            ext, dead = self.engine_gap_suggestions(model)
            md += ["### 9.1 External-input supply suggestions (③)", "", _table(["module", "input", "similar outputs", "hint", "needs_review"], [[r["module"], r["input"], r["candidates"], r["hint"], r["needs_review"]] for r in ext]),
                   "### 9.2 Dead-output disposition suggestions (③)", "", _table(["module", "output", "similar outputs", "hint", "needs_review"], [[r["module"], r["output"], r["candidates"], r["hint"], r["needs_review"]] for r in dead]),
                   "### 9.3 Module intent (④ by module name + I/O names)", ""]
            fns = [{"name": m["module"]} for m in model.get("modules", [])]
            calls = [{"in": m["module"], "callee": x} for m in model.get("modules", []) for x in (m["inputs"] + m["outputs"])]
            recs = self.classify_functions(model["path"], "json", fns, calls, [])
            md += [self._fn_table(recs, fns)]
        else:
            md += ["_(no semantic rules for kind `{0}`)_".format(kind), ""]
        return "\n".join(md)

    def _fn_table(self, recs, fns):
        if not self.available:
            return "_unavailable: via_nlp_engine not importable → install VIA NLP One Engine (Python ≥ 3.11) to enable_\n"
        if not fns:
            return "_(no functions)_\n"
        if not recs:
            return "_(no named functions to classify)_\n"
        return _table(["function", "primary", "zh", "secondary", "confidence", "evidence", "review"],
                      [[r["symbol_name"], r["primary_category"], r["primary_label"]["zh"], ", ".join(c["category"] for c in r["categories"][1:]) or "-", r["confidence"],
                        ", ".join(r["categories"][0]["evidence"][:5]), r["review_required"]] for r in recs])

    def _chain_table(self, chains, recs):
        if not chains:
            return "_(no interaction chains)_\n"
        cat = {r["symbol_name"]: r for r in recs}
        rows = []
        for c in chains:
            r = cat.get(c["handler"])
            intent = "{0} / {1}".format(r["primary_category"], r["primary_label"]["zh"]) if r else ("anonymous handler" if c["handler"].startswith("anon@") else "unclassified")
            flow = []
            if c.get("api", "-") != "-":
                flow.append("network")
            if c.get("dom", "-") != "-":
                flow.append("ui_reporting")
            rows.append([c["trigger"], c["event"], c["handler"], intent, " → ".join(flow) or "-"])
        return _table(["trigger", "event", "handler", "handler intent", "observed effects"], rows)

    def _content_table(self, sem):
        if sem is None:
            return "_unavailable_\n" if not self.available else "_(no page content)_\n"
        ents = Counter((e["label"], e["text"]) for e in sem["entities"])
        out = ["- language: `{0}` · doc type: `{1}` ({2:.2f}) · rules label: `{3}` ({4})  ".format(sem["language"], sem["doc_type"], sem["doc_type_conf"], sem["rules"]["label"], sem["rules"]["confidence"]),
               "- keywords: " + (", ".join("`{0}`({1})".format(k["term"], k["count"]) for k in sem["keywords"][:15]) or "-") + "  ", "",
               "**Entities (Tier-2 regex NER: TICKER / DATE / PERCENT / MONEY / URL / EMAIL)**", "",
               _table(["label", "text", "count"], [[l, t, n] for (l, t), n in ents.most_common(60)]),
               "**Extractive key points**", ""]
        out += ["- " + p for p in sem["summary"].get("key_points", [])] or ["_(none)_"]
        return "\n".join(out) + "\n"

    def _pipeline_intent(self, pipelines, recs):
        cat = {r["symbol_name"].split(".")[-1]: r for r in recs}
        rows = []
        for pl in pipelines:
            for s in pl["steps"][:40]:
                key = s.split(".")[-1].rstrip("()")
                r = cat.get(key)
                rows.append([pl["name"], s, "{0} / {1}".format(r["primary_category"], r["primary_label"]["zh"]) if r else "-"])
        return _table(["pipeline", "step", "intent"], rows)
'@
        $bridgePath = Save-AppendOnly -Path (Join-Path $dirs.engine 'via_superhtml_nlp_bridge.py') -Content $bridgeSrc
        Write-Log -Message ('nlp bridge = {0} ({1:N0} bytes)' -f $bridgePath, $bridgeSrc.Length) -Level 'OK'

        $runnerSrc = @'
# -*- coding: utf-8 -*-
# VIA SuperHtml Parser Engine v1.1.0 runner — append-only layer over via_superhtml_parser.py (v1.0.0, untouched)
# Adds "## 9. Semantic Layer" to every markdown via via_superhtml_nlp_bridge (VIA NLP One Engine v1.5)
import sys, time, json, argparse, traceback
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import via_superhtml_parser as v1
from via_superhtml_nlp_bridge import NlpBridge, BRIDGE_VERSION

VERSION = "1.1.0"

def main():
    ap = argparse.ArgumentParser(description="VIA SuperHtml Parser Engine v1.1 (v1.0 + NLP bridge)")
    ap.add_argument("--targets", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ext", nargs="*", default=None)
    ap.add_argument("--nlp-root", default=None, help="VIA NLP One Engine project root (for data/lexicon/ssot_lexicon.json)")
    ap.add_argument("--ui-lexicon", default=None, help="ui_component_lexicon.json path")
    ap.add_argument("--no-nlp", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    exts = set(a.ext) if a.ext else v1.HTML_EXT | v1.JS_EXT | v1.CSS_EXT | v1.PY_EXT | v1.JSON_EXT | v1.PS_EXT
    v1.log("INFO", "VSHP v{0} (core v{1}, bridge v{2}) · bs4={3}/{4} esprima={5} tinycss2={6} markitdown={7}".format(VERSION, v1.VERSION, BRIDGE_VERSION, v1.HAS_BS4, v1.BS_PARSER, v1.HAS_ESPRIMA, v1.HAS_TINYCSS, v1.HAS_MARKITDOWN))
    bridge = None if a.no_nlp else NlpBridge(a.nlp_root, a.ui_lexicon, log=v1.log)
    files = v1.discover(a.targets, exts)
    v1.log("INFO", "discovered {0} files".format(len(files)))
    results, run_log = [], []
    sem_stats = Counter()
    for i, f in enumerate(files, 1):
        t = time.time()
        ext = f.suffix.lower()
        stem = "{0}__{1}_{2}".format(f.stem, ext.lstrip("."), v1.sha8(str(f.resolve())))
        md_path = out / (stem + ".md")
        try:
            kind, model = None, None
            if ext in v1.HTML_EXT:
                model = v1.read_html_ui_and_logic(f); md_text, kind = v1.md_ui(model), "html-ui"
                summary = "nodes={0} components={1} js-fn={2} events={3} css-rules={4} chains={5}".format(model["node_count"], len(model["components"]), len(model["js_logic"]["functions"]), len(model["events"]) + len(model["js_logic"]["events"]), len(model["css_logic"]["rules"]), len(model["ui_behavior"]["chains"]))
            elif ext in v1.JS_EXT:
                raw = v1.load_file(f)
                logic = v1.analyze_js([{"src": f.name, "content": raw}])
                model = {"path": str(f), "raw_len": len(raw), "node_count": 0, "attr_stats": Counter(), "dom_structure": {"tree": [], "tag_counter": Counter(), "max_depth": 0}, "components": [], "events": [],
                         "inline_scripts": [], "external_scripts": [{"src": f.name, "status": "file", "content": raw}], "inline_styles": [], "external_stylesheets": [],
                         "js_logic": logic, "css_logic": v1.analyze_css([]), "ui_behavior": v1.build_ui_behavior_model(None, [], [], logic), "content_md": "_(standalone JS — no page content)_", "content_engine": "n/a", "title": ""}
                md_text, kind = v1.md_ui(model), "js"
                summary = "functions={0} events={1} api={2}".format(len(logic["functions"]), len(logic["events"]), len(logic["api_calls"]))
            elif ext in v1.CSS_EXT:
                md_text, s = v1.md_css_file(f); kind = "css"; model = {"components": [], "js_logic": {}, "content_engine": "n/a"}
                summary = " ".join("{0}={1}".format(k, v) for k, v in s.items())
            elif ext in v1.PY_EXT:
                model = v1.read_backend_logic(f); md_text, kind = v1.md_backend(model), "py-backend"
                summary = "fn={0} classes={1} imports={2} routes={3} pipelines={4}".format(len(model["functions"]), len(model["classes"]), len(model["imports"]), len(model["api_routes"]), len(model["pipeline"]))
            elif ext in v1.JSON_EXT:
                model = v1.read_engine_json(f); md_text, kind = v1.md_engine(model), model["kind"]
                summary = "modules={0} edges={1} external={2} dead={3} order-issues={4}".format(len(model["modules"]), len(model["edges"]), len(model["external_inputs"]), len(model["dead_outputs"]), len(model["order_issues"])) if model["kind"] == "engine-spec" else "keys={0}".format(len(model["keys"]))
            elif ext in v1.PS_EXT:
                model = v1.read_ps_logic(f); md_text, kind = v1.md_ps(model), "ps1"
                summary = "fn={0} params={1} regions={2}".format(len(model["functions"]), len(model["params"]), len(model["regions"]))
            else:
                continue
            if bridge is not None and kind != "json-generic":
                try:
                    sec = bridge.section_md(kind, model)
                    md_text = md_text.rstrip("\n") + "\n\n" + sec + "\n"
                    n_review = sec.count("| True |")
                    sem_stats["sections"] += 1; sem_stats["review_rows"] += n_review
                    summary += " · semantic: review_rows={0}".format(n_review)
                except Exception as e:
                    v1.log("WARN", "semantic layer failed for {0}: {1}".format(f.name, e))
                    md_text += "\n\n{0}\n\n_failed: {1}_\n".format("## 9. Semantic Layer", e)
            header = "<!-- VIA SuperHtml Parser v{0} (core {1} + bridge {2}) · {3} · source={4} -->\n\n".format(VERSION, v1.VERSION, BRIDGE_VERSION, time.strftime("%Y-%m-%d %H:%M:%S"), f)
            md_path.write_text(header + md_text, encoding="utf-8")
            status = "OK"
        except Exception as ex:
            status, kind, summary = "FAIL", ext.lstrip("."), "{0}: {1}".format(type(ex).__name__, v1.clip(str(ex), 120))
            md_path.write_text("# FAILED — {0}\n\n```\n{1}\n```".format(f, traceback.format_exc()), encoding="utf-8")
        secs = time.time() - t
        results.append({"file": str(f), "type": kind, "status": status, "summary": summary, "secs": secs, "md": md_path.name})
        line = "[{0}/{1}] {2} {3} ({4:.2f}s) {5}".format(i, len(files), status, f.name, secs, summary)
        run_log.append(line)
        v1.log("PROG", line)
    index = ["# VIA SuperHtml Parser — INDEX (v{0})".format(VERSION), "", "Generated {0} · {1} files · NLP bridge: {2}".format(time.strftime("%Y-%m-%d %H:%M:%S"), len(results), ("via_nlp_engine " + bridge.engine_version) if bridge and bridge.available else "unavailable"), "",
             v1.md_table(["file", "type", "status", "summary", "markdown"], [[r["file"], r["type"], r["status"], r["summary"], "[{0}]({0})".format(r["md"])] for r in results], 2000)]
    (out / "INDEX.md").write_text("\n".join(index), encoding="utf-8")
    (out / "run_manifest.json").write_text(json.dumps({"version": VERSION, "core": v1.VERSION, "bridge": BRIDGE_VERSION, "nlp_engine": bridge.engine_version if bridge else None, "nlp_available": bool(bridge and bridge.available),
                                                       "nlp_reason": bridge.reason if bridge else "disabled", "targets": a.targets, "results": results, "semantic": dict(sem_stats), "seconds": time.time() - v1.T0}, ensure_ascii=False, indent=2), encoding="utf-8")
    run_log.insert(0, "NLP bridge: " + (("via_nlp_engine " + bridge.engine_version + " · lexicon " + bridge.lexicon_path) if bridge and bridge.available else ("unavailable: " + (bridge.reason if bridge else "disabled"))))
    v1.VERSION = "{0} (core {1} · bridge {2})".format(VERSION, v1.VERSION, BRIDGE_VERSION)
    v1.html_report(out, results, {"stamp": time.strftime("%Y-%m-%d %H:%M:%S"), "targets": a.targets, "log": run_log})
    v1.log("DONE", "{0} files → {1} · OK={2} FAIL={3} · semantic sections={4} review_rows={5} · {6:.1f}s".format(len(results), out, sum(r["status"] == "OK" for r in results), sum(r["status"] != "OK" for r in results), sem_stats["sections"], sem_stats["review_rows"], time.time() - v1.T0))

if __name__ == "__main__":
    main()
'@
        $enginePath = Save-AppendOnly -Path (Join-Path $dirs.engine 'via_superhtml_parser_v110.py') -Content $runnerSrc
        Write-Log -Message ('runner v{0} = {1}' -f $script:Version, $enginePath) -Level 'OK'
        if ($corePath -ne (Join-Path $dirs.engine 'via_superhtml_parser.py') -or $bridgePath -ne (Join-Path $dirs.engine 'via_superhtml_nlp_bridge.py')) {
            Write-Log -Message 'core/bridge on disk differ from this script (append-only kept yours); runner imports the on-disk via_superhtml_parser.py / via_superhtml_nlp_bridge.py' -Level 'WARN'
        }

        # ui component lexicon: written once, never overwritten (Tony edits it; append-only by convention)
        $uiLexPath = Join-Path $dirs.lexicon 'ui_component_lexicon.json'
        if (-not (Test-Path -LiteralPath $uiLexPath)) {
            $uiLex = @'
{
  "version": "1.0.0",
  "schema": "VIA_UI_COMPONENT_LEXICON/1.0",
  "locale": "zh-TW",
  "note": "append-only: add synonyms, never remove canonicals; VSHP bridge matches tag/id/class/data-*/role/text against these",
  "canonicals": {
    "navigation": {
      "zh": "導覽列",
      "en": "Navigation",
      "synonyms": [
        "nav",
        "navbar",
        "menu",
        "breadcrumb",
        "導覽",
        "選單"
      ]
    },
    "header": {
      "zh": "頁首",
      "en": "Header",
      "synonyms": [
        "header",
        "masthead",
        "banner",
        "title-bar",
        "頁首",
        "標題列"
      ]
    },
    "footer": {
      "zh": "頁尾",
      "en": "Footer",
      "synonyms": [
        "footer",
        "copyright",
        "頁尾"
      ]
    },
    "toolbar": {
      "zh": "工具列",
      "en": "Toolbar",
      "synonyms": [
        "toolbar",
        "actions",
        "controls",
        "control-bar",
        "工具列",
        "控制"
      ]
    },
    "panel": {
      "zh": "面板",
      "en": "Panel",
      "synonyms": [
        "panel",
        "pane",
        "section",
        "container",
        "box",
        "面板",
        "區塊"
      ]
    },
    "card": {
      "zh": "卡片",
      "en": "Card",
      "synonyms": [
        "card",
        "tile",
        "widget",
        "卡片"
      ]
    },
    "kpi_metric": {
      "zh": "KPI 指標",
      "en": "KPI / Metric",
      "synonyms": [
        "kpi",
        "metric",
        "stat",
        "score",
        "rate",
        "指標",
        "成功率",
        "勝率"
      ]
    },
    "table_grid": {
      "zh": "表格",
      "en": "Table / Grid",
      "synonyms": [
        "table",
        "grid",
        "datagrid",
        "thead",
        "tbody",
        "row",
        "表格",
        "清單"
      ]
    },
    "form": {
      "zh": "表單",
      "en": "Form",
      "synonyms": [
        "form",
        "fieldset",
        "表單"
      ]
    },
    "input_control": {
      "zh": "輸入控制項",
      "en": "Input control",
      "synonyms": [
        "input",
        "select",
        "textarea",
        "field",
        "symbol",
        "ticker",
        "window",
        "輸入",
        "代碼"
      ]
    },
    "button_action": {
      "zh": "動作按鈕",
      "en": "Action button",
      "synonyms": [
        "button",
        "btn",
        "run",
        "submit",
        "execute",
        "apply",
        "按鈕",
        "執行"
      ]
    },
    "status_indicator": {
      "zh": "狀態指示",
      "en": "Status indicator",
      "synonyms": [
        "status",
        "state",
        "badge",
        "seal",
        "live",
        "idle",
        "phase",
        "狀態",
        "階段",
        "封印"
      ]
    },
    "chart": {
      "zh": "圖表",
      "en": "Chart",
      "synonyms": [
        "chart",
        "plot",
        "graph",
        "canvas",
        "svg",
        "sparkline",
        "圖表",
        "走勢"
      ]
    },
    "modal_dialog": {
      "zh": "對話框",
      "en": "Modal / Dialog",
      "synonyms": [
        "modal",
        "dialog",
        "popup",
        "overlay",
        "對話框",
        "彈窗"
      ]
    },
    "tabs": {
      "zh": "分頁籤",
      "en": "Tabs",
      "synonyms": [
        "tab",
        "tabs",
        "tablist",
        "頁籤"
      ]
    },
    "sidebar": {
      "zh": "側欄",
      "en": "Sidebar",
      "synonyms": [
        "sidebar",
        "aside",
        "drawer",
        "側欄"
      ]
    },
    "list": {
      "zh": "列表",
      "en": "List",
      "synonyms": [
        "list",
        "ul",
        "ol",
        "li",
        "item",
        "列表"
      ]
    },
    "progress": {
      "zh": "進度",
      "en": "Progress",
      "synonyms": [
        "progress",
        "bar",
        "loader",
        "spinner",
        "進度"
      ]
    },
    "console_log": {
      "zh": "主控台 / 日誌",
      "en": "Console / Log",
      "synonyms": [
        "console",
        "log",
        "terminal",
        "output",
        "主控台",
        "日誌"
      ]
    },
    "media": {
      "zh": "媒體",
      "en": "Media",
      "synonyms": [
        "video",
        "audio",
        "iframe",
        "img",
        "image",
        "媒體"
      ]
    }
  }
}
'@
            Save-TextNoBom -Path $uiLexPath -Content $uiLex
            Write-Log -Message ('ui lexicon seeded = {0}' -f $uiLexPath) -Level 'OK'
        } else {
            Write-Log -Message ('ui lexicon kept = {0}' -f $uiLexPath) -Level 'OK'
        }

        # -------------------------------------------------------- 5. samples (self-test corpus; append-only)
        $samples = [ordered]@{}
        $samples['AccumulationFactValidationEngine.json'] = @'
{
  "engine": {
    "name": "AccumulationFactValidationEngine",
    "version": "1.0",
    "modules": {
      "data_loader": { "inputs": ["date", "symbol", "ohlc", "volume", "sector"], "outputs": ["raw_data"] },
      "rolling_accumulation": { "inputs": ["raw_data"], "parameters": { "window": 20 },
        "outputs": ["acc_raw_vol","acc_raw_px","acc_raw_actor","acc_raw_struct","acc_rb_vol_20","acc_rb_px_20","acc_rb_actor_20","acc_rb_struct_20"] },
      "acc_state_classifier": { "inputs": ["acc_raw_vol","acc_rb_vol_20","acc_raw_px","acc_rb_px_20","acc_raw_actor","acc_rb_actor_20","acc_raw_struct","acc_rb_struct_20"],
        "outputs": ["acc_state_vol","acc_state_px","acc_state_actor","acc_state_struct"] },
      "market_noise_filter": { "inputs": ["index_data"], "parameters": { "noise_high": 2.0, "noise_mid": 1.0 },
        "outputs": ["market_noise","market_noise_state","acc_state_vol_adj","acc_state_px_adj","acc_state_actor_adj","acc_state_struct_adj","acc_phase_adj","fact_noise_filter"] },
      "phase_detector": { "inputs": ["leader_acc_state","peer_acc_state","lagger_acc_state"], "outputs": ["acc_phase"] },
      "fact_validation": { "inputs": ["acc_phase_adj","future_obv","future_hvn","future_turnover","leader_future","peer_future"],
        "outputs": ["vol_validation","struct_validation","group_validation","conceal_validation"] },
      "success_rate_calculator": { "inputs": ["vol_validation","struct_validation","group_validation","conceal_validation","acc_phase_adj"],
        "outputs": ["start_success_rate","confirm_success_rate","complete_success_rate","conceal_success_rate","group_success_rate"] }
    },
    "pipeline": ["data_loader","rolling_accumulation","acc_state_classifier","market_noise_filter","phase_detector","fact_validation","success_rate_calculator"]
  }
}
'@
        $samples['dashboard.html'] = @'
<!doctype html><html><head><meta charset="utf-8"><title>VIA Accumulation Dashboard</title>
<link rel="stylesheet" href="app.css"><link rel="stylesheet" href="https://cdn.example.com/x.css">
<style>body{background:#0f1117;color:#eee} .kpi{display:grid;grid-template-columns:1fr 1fr}</style></head>
<body><header class="toolbar"><h1>吸籌事實驗證</h1><nav><a href="#a">A</a><a href="#b">B</a></nav></header>
<main><section id="controls" class="panel" data-module="acc"><form id="f" onsubmit="submitForm(event)"><input id="symbol" value="2330"><select id="win"><option>20</option></select><button id="btnRun" type="button">Run</button></form></section>
<section class="kpi"><div class="card" data-kpi="start">Start 62%</div><div class="card" data-kpi="confirm">Confirm 48%</div></section>
<table id="grid"><tr><td>2026-09-01</td><td>START</td></tr></table><span id="status">idle</span></main>
<footer>© VIA</footer>
<script src="app.js" type="module"></script>
<script>function submitForm(e){ e.preventDefault(); document.getElementById('status').textContent='submitted'; fetch('/api/submit',{method:'POST'}); }</script>
</body></html>
'@
        $samples['app.js'] = @'
import { fmt } from './util.js';
const state = { symbol: '2330', rows: [] };
async function loadData(sym) {
  const res = await fetch('/api/accumulation/' + sym);
  state.rows = await res.json();
  renderTable(state.rows);
}
function renderTable(rows) {
  const tb = document.getElementById('grid');
  tb.innerHTML = rows.map(r => `<tr><td>${r.date}</td><td>${fmt(r.acc_phase)}</td></tr>`).join('');
  document.querySelector('#status').classList.add('live');
}
document.getElementById('btnRun').addEventListener('click', () => loadData(state.symbol));
$('#symbol').on('change', function(){ state.symbol = this.value; });
window.onresize = () => { if (state.rows.length > 100) { renderTable(state.rows.slice(0,100)); } };
'@
        $samples['app.css'] = @'
:root{--accent:#c96b5a}
.card{display:flex;padding:12px;transition:all .3s}
@media (max-width:600px){.card{display:block}}
@keyframes pulse{from{opacity:.4}to{opacity:1}}
#status.live{animation:pulse 1s infinite;color:var(--accent)!important}
'@
        $samples['backend.py'] = @'
"""Sample VIA backend."""
import json, pandas as pd
from flask import Flask, jsonify
app = Flask(__name__)
PIPELINE = ["data_loader", "rolling_accumulation", "acc_state_classifier"]

class AccEngine:
    """Accumulation engine."""
    def __init__(self, window=20):
        self.window = window
    def rolling(self, df):
        if df.empty:
            return None
        for c in ["vol", "px"]:
            df[c + "_rb"] = df[c].rolling(self.window).mean()
        return df

@app.route("/api/accumulation/<sym>", methods=["GET"])
def accumulation(sym):
    eng = AccEngine()
    df = load(sym)
    out = eng.rolling(df)
    return jsonify(out.to_dict())

def load(sym, unused=1):
    try:
        return pd.read_csv(sym + ".csv")
    except Exception:
        return pd.DataFrame()

def main():
    df = load("2330")
    AccEngine().rolling(df)

if __name__ == "__main__":
    main()
'@
        foreach ($k in $samples.Keys) { Save-AppendOnly -Path (Join-Path $dirs.samples $k) -Content $samples[$k] | Out-Null }
        Write-Log -Message ('samples ready: {0}' -f ($samples.Keys -join ', ')) -Level 'OK'

        # -------------------------------------------------------- 6. self-copy + bin shim
        $selfDst = Join-Path $Root 'Invoke-VIA-SuperHtmlParser.ps1'
        if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath)) {
            if ((Resolve-Path -LiteralPath $PSCommandPath).Path -ne $selfDst) {
                $selfDst = Save-AppendOnly -Path $selfDst -Content ([System.IO.File]::ReadAllText($PSCommandPath, $script:Utf8NoBom))
            }
        }
        # shim always points at the script version that actually ran (append-only may have produced a _sha sibling)
        $shim = '@echo off' + "`r`n" + ('pwsh -NoProfile -ExecutionPolicy Bypass -File "{0}" -Targets %*' -f $selfDst) + "`r`n"
        Save-TextNoBom -Path (Join-Path $dirs.bin 'via-superhtml.cmd') -Content $shim
        Save-TextNoBom -Path (Join-Path $Root 'LATEST_SCRIPT.txt') -Content ('{0}`r`nv{1} · {2}' -f $selfDst, $script:Version, $script:Stamp)

        # -------------------------------------------------------- 7. run engine (live output, no stall)
        $targetList = @()
        if ($Targets.Count -gt 0) { $targetList = @($Targets) } else { $targetList = @($dirs.samples, $dirs.engine) }
        $outDir = Join-Path $dirs.reports $script:Stamp
        Write-Log -Message ('parsing {0} target(s) → {1}' -f $targetList.Count, $outDir) -Level 'STEP'
        foreach ($t in $targetList) { Write-Log -Message ('  target: {0}' -f $t) }
        $engArgs = @($enginePath, '--targets') + $targetList + @('--out', $outDir, '--ui-lexicon', $uiLexPath)
        if ($nlpRoot) { $engArgs += @('--nlp-root', $nlpRoot) }
        $rc = Invoke-Proc -Exe $venvPy -Arguments $engArgs -WorkDir $Root
        $report = Join-Path $outDir 'VIA_SuperHtmlParser_Report.html'
        if ($rc -eq 0 -and (Test-Path -LiteralPath $report)) {
            Write-Log -Message ('engine rc=0 · report = {0}' -f $report) -Level 'OK'
            Save-TextNoBom -Path (Join-Path $dirs.reports 'LATEST.txt') -Content $outDir
            $mdCount = @([System.IO.Directory]::EnumerateFiles($outDir, '*.md')).Count
            Write-Log -Message ('{0} markdown files in {1}' -f $mdCount, $outDir) -Level 'OK'
            if ($OpenReport) { Start-Process -FilePath $report }
        } else {
            Write-Log -Message ('engine exit code {0}; see console output above' -f $rc) -Level 'FAIL'
        }
    }
}
catch {
    Write-Log -Message ('unhandled: {0} @ line {1}' -f $_.Exception.Message, $_.InvocationInfo.ScriptLineNumber) -Level 'FAIL'
}
finally {
    $elapsed = (Get-Date) - $script:T0
    Write-Log -Message ('done in {0:N1}s' -f $elapsed.TotalSeconds) -Level 'STEP'
    try { Save-TextNoBom -Path (Join-Path (Join-Path $Root 'logs') ('run_{0}.log' -f $script:Stamp)) -Content ($script:LogLines -join "`r`n") } catch { }
}
}
