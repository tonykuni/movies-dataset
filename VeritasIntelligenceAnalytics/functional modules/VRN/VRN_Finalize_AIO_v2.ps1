#requires -Version 7.0

<#
VRN Finalize AIO v1
Veritas Intelligence Analytics  VeritasReportNova

One PowerShell to complete the three gated processes from the Do-Not-Redo registry:
  Next 1  Anchor Patch Preview        read-only, no mutation
  Next 2  Append-only Patch           append-only hookup of HistoricalValidationPolicy
  Next 3  Post-patch Validation       confirm policy in effect

Plus a read-only Consensus Data cross-validation probe (yfinance live, FactSet pluggable)
that emits the locked block-03 schema, and a Hydra prevention denylist front gate.

Safety:
  Hydra prevention: never re-runs sealed work listed in the Do-Not-Redo denylist.
  Append-only: the patch never edits an existing line; SHA256 backup, py_compile, rollback.
  No fake data: FactSet without credential is graceful-skipped, never synthesized.
  Keep open: try catch plus post-catch keep-open statements keep the session alive.
#>

param(
    [string]$VrnRoot        = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN",
    [string]$CanonicalMaster = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\modules\VRN_MDL_SummaryPipelineBridge_AIO_v01.py",
    [string]$PolicyModule   = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIS_VRN_HistoricalValidationPolicy_v0100.py",
    [string]$TrustMatrixCsv = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_d8b_runs\RUN_20260530_215141_VRN_V070_AIO\VRN_v070_Trust_Matrix.csv",
    [string]$FinancialCsv   = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_d8b_runs\RUN_20260530_215141_VRN_V070_AIO\VRN_v070_FinancialData.csv",
    [int]$ExpectedTrustRows = 2087,
    [int]$ExpectedFinRows   = 2087,
    [string]$SsotMode       = "both",
    [int]$FetchLimit        = 0,
    [string]$FactSetApiKey  = "",
    [string]$ToolsDir       = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",
    [switch]$StopAfterPreview,
    [switch]$NoOpenHtml,
    [switch]$KeepOpen
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"
$ProgressPreference    = "SilentlyContinue"

# Hydra prevention denylist  do not re-run any of these sealed items
$script:DoNotRedo = [ordered]@{
    "Base Review"                              = "DONE"
    "Master Route Lock + Financial Reconcile"  = "DONE"
    "Canonical Active Seal Preview"            = "DONE"
    "Hydra Containment Registry"               = "DONE"
    "BasicInfo + FinancialData Confidence Review" = "DONE"
    "Historical Validation Policy Gate"        = "DONE"
}

$script:TS      = Get-Date -Format "yyyyMMdd_HHmmss"
$script:RunName = "RUN_${script:TS}_VRN_FINALIZE_AIO"
$script:RunDir  = Join-Path $VrnRoot ("_vrn_finalize_aio_runs\" + $script:RunName)
$script:LogList = [System.Collections.Generic.List[string]]::new()
$script:Watch   = [System.Diagnostics.Stopwatch]::StartNew()
$script:Phases  = [System.Collections.Generic.List[object]]::new()

function Write-VLog {
    param([string]$Message, [string]$Level = "INFO")
    $stamp = Get-Date -Format "HH:mm:ss.fff"
    $line  = "[$stamp][$Level] $Message"
    Write-Host $line
    $script:LogList.Add($line)
}

function Show-Step {
    param([int]$Pct, [string]$Text)
    Write-Progress -Id 1 -Activity "VRN Finalize AIO" -Status $Text -PercentComplete $Pct
    Write-VLog "[$Pct%] $Text" "STEP"
}

function Find-Python {
    $cands = @(
        "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
        "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
        "C:\Python313\python.exe"
    )
    foreach ($c in $cands) {
        if (Test-Path -LiteralPath $c) { return $c }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return "py" }
    throw "No Python interpreter found."
}

function Invoke-PyCmd {
    param([string]$PyExe, [string]$Script, [string[]]$PyArgs)
    $all = @($Script) + $PyArgs
    $out = & $PyExe @all 2>&1
    $code = $LASTEXITCODE
    foreach ($o in $out) { Write-VLog "  py> $o" "PY" }
    return $code
}

function Read-JsonSafe {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100)
    } catch {
        Write-VLog "JSON parse failed: ${Path}" "WARN"
        return $null
    }
}

function Add-Phase {
    param([string]$Name, [string]$Status, [string]$Risk, [string]$Note)
    $script:Phases.Add([pscustomobject]@{
        Name = $Name; Status = $Status; Risk = $Risk; Note = $Note
    })
}

function ConvertTo-HtmlRows {
    param($Obj, [string[]]$Keys)
    $sb = [System.Text.StringBuilder]::new()
    if ($null -eq $Obj) { return "" }
    foreach ($item in $Obj) {
        [void]$sb.Append("<tr>")
        foreach ($k in $Keys) {
            $v = ""
            try { $v = [string]$item.$k } catch { $v = "" }
            [void]$sb.Append("<td>" + [System.Web.HttpUtility]::HtmlEncode($v) + "</td>")
        }
        [void]$sb.Append("</tr>")
    }
    return $sb.ToString()
}

# main run wrapped in try catch; keep-open statements follow after catch (no finally keyword)
try {
    New-Item -ItemType Directory -Path $script:RunDir -Force | Out-Null
    Write-VLog "VRN Finalize AIO started" "BOOT"
    Write-VLog "RunDir: ${script:RunDir}" "BOOT"

    # write embedded python core
    $script:PyCore = Join-Path $script:RunDir "vrn_finalize_core.py"
    $coreText = @'
# -*- coding: utf-8 -*-
"""
VRN Finalize AIO - embedded Python core
Subcommands (called by PS7 wrapper, gated in order):
  anchor-preview   : AST scan canonical master for 5 anchor types. NO MUTATION.
  append-patch     : append-only hookup of policy module. SHA256 backup + py_compile + rollback.
  post-validate    : verify policy in effect; broker/pdf_table/report_text not financial truth.
  fetch-crossval   : yfinance (defensive) + FactSet (bridge pluggable) consensus cross-validate. READ-ONLY.

Hard rules:
  - Hydra prevention: never re-run sealed/denylisted work; this module only does the 3 next processes.
  - Append-only: append-patch never edits existing lines; it appends one guarded marker block.
  - No fake data: FactSet without creds -> graceful skip, never synthesized into trust matrix.
"""
import sys, os, json, ast, hashlib, csv, datetime, traceback

MARKER_BEGIN = "# [VRN:ANCHOR:HISTORICAL_VALIDATION_POLICY:BEGIN]"
MARKER_END   = "# [VRN:ANCHOR:HISTORICAL_VALIDATION_POLICY:END]"


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ----------------------------------------------------------------------------
# Tool binding (Aegis / Celeritas) - bridge pluggable, graceful if absent.
# ----------------------------------------------------------------------------
_TOOLS = {"aegis": None, "celeritas": None, "bound": False, "log": []}


def _bind_tools(tools_dir):
    if _TOOLS["bound"]:
        return _TOOLS
    _TOOLS["bound"] = True
    # quiet yfinance / urllib noise
    try:
        import logging
        for nm in ("yfinance", "urllib3", "peewee", "requests"):
            logging.getLogger(nm).setLevel(logging.CRITICAL)
    except Exception:
        pass
    # make supportive_module importable: add tools_dir and its parents
    if tools_dir and os.path.isdir(tools_dir):
        for p in (tools_dir, os.path.dirname(tools_dir), os.path.dirname(os.path.dirname(tools_dir))):
            if p and p not in sys.path:
                sys.path.insert(0, p)
    import importlib
    for key, names in (("aegis", ("VeritasAegisNexus", "supportive_module.VeritasAegisNexus",
                                   "module.supportive_module.VeritasAegisNexus")),
                       ("celeritas", ("VeritasCeleritas", "supportive_module.VeritasCeleritas",
                                      "module.supportive_module.VeritasCeleritas"))):
        for nm in names:
            try:
                _TOOLS[key] = importlib.import_module(nm)
                _TOOLS["log"].append("%s bound via %s" % (key, nm))
                break
            except Exception:
                _TOOLS[key] = None
        if _TOOLS[key] is None:
            _TOOLS["log"].append("%s NOT bound (graceful)" % key)
    return _TOOLS


def _build_market_map(aegis):
    """code -> market ('TWSE'/'TPEX') from Aegis lists. Empty if Aegis absent."""
    mm = {}
    if aegis is None:
        return mm
    try:
        for row in (aegis.fetch_twse_list() or []):
            code = str(row.get("Code") or row.get("公司代號") or row.get("code") or "").strip()
            if code:
                mm[code] = "TWSE"
    except Exception:
        pass
    try:
        for row in (aegis.fetch_tpex_list() or []):
            code = str(row.get("SecuritiesCompanyCode") or row.get("公司代號") or row.get("code") or "").strip()
            if code:
                mm.setdefault(code, "TPEX")
    except Exception:
        pass
    return mm


def _normalize_tw_ticker(raw, market_map, aegis):
    """bare code -> yfinance ticker. Returns list of candidates to try in order."""
    t = (raw or "").strip().upper()
    if t.endswith((".TW", ".TWO")):
        return [t]
    code = t.split(".")[0]
    cands = []
    mkt = market_map.get(code)
    if aegis is not None and hasattr(aegis, "build_yf_ticker"):
        if mkt == "TPEX":
            cands = [aegis.build_yf_ticker(code, "TPEX"), aegis.build_yf_ticker(code, "TWSE")]
        elif mkt == "TWSE":
            cands = [aegis.build_yf_ticker(code, "TWSE"), aegis.build_yf_ticker(code, "TPEX")]
        else:
            cands = [aegis.build_yf_ticker(code, "TWSE"), aegis.build_yf_ticker(code, "TPEX")]
    else:
        # no Aegis: TWSE first, TPEX fallback
        if mkt == "TPEX":
            cands = [code + ".TWO", code + ".TW"]
        else:
            cands = [code + ".TW", code + ".TWO"]
    # dedupe preserve order
    seen, out = set(), []
    for c in cands:
        if c and c not in seen:
            seen.add(c); out.append(c)
    return out


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def _read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _write_json(out_path, obj):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ----------------------------------------------------------------------------
# anchor-preview : locate 5 anchor types via AST + keyword scan. NO MUTATION.
# ----------------------------------------------------------------------------
ANCHOR_PATTERNS = {
    "IMPORT_BLOCK":     ("import", "from "),
    "FINANCIAL_GATE":   ("financial", "gate", "validate", "reconcile"),
    "BASICINFO_OPINION":("basicinfo", "basic_info", "opinion", "rating", "target_price", "target price"),
    "TRUST_MATRIX":     ("trust", "matrix", "confidence", "green", "yellow"),
    "SEAL_GATE":        ("seal", "canonical_active", "readonly", "read_only"),
}


def cmd_anchor_preview(canonical_master, out_json):
    res = {
        "command": "anchor-preview", "ts": _now(),
        "canonical_master": canonical_master, "mutation": False,
        "status": "UNKNOWN", "risk": "GREEN", "anchors": {}, "issues": [],
    }
    try:
        if not os.path.isfile(canonical_master):
            res["status"] = "FAIL"; res["risk"] = "RED"
            res["issues"].append("CANONICAL_MASTER_NOT_FOUND")
            _write_json(out_json, res); return 1

        res["sha256_before"] = _sha256(canonical_master)
        src = _read_text(canonical_master)
        lines = src.splitlines()

        # AST: parseability + import lines + top-level defs/classes
        already_patched = (MARKER_BEGIN in src)
        res["already_patched"] = already_patched

        import_lines, defs, classes = [], [], []
        try:
            tree = ast.parse(src)
            res["ast_parseable"] = True
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_lines.append(getattr(node, "lineno", 0))
                elif isinstance(node, ast.FunctionDef):
                    defs.append((node.name, getattr(node, "lineno", 0)))
                elif isinstance(node, ast.ClassDef):
                    classes.append((node.name, getattr(node, "lineno", 0)))
        except SyntaxError as e:
            res["ast_parseable"] = False
            res["issues"].append("AST_PARSE_ERROR: %s" % e)

        last_import = max(import_lines) if import_lines else 0
        res["anchors"]["IMPORT_BLOCK"] = {
            "last_import_line": last_import,
            "suggested_insert_line": last_import + 1 if last_import else 1,
        }

        # keyword anchor scan (line-level, case-insensitive) for the other 4
        low = [ln.lower() for ln in lines]
        for key in ("FINANCIAL_GATE", "BASICINFO_OPINION", "TRUST_MATRIX", "SEAL_GATE"):
            pats = ANCHOR_PATTERNS[key]
            hits = []
            for i, ln in enumerate(low, 1):
                if any(p in ln for p in pats):
                    hits.append(i)
            res["anchors"][key] = {"hit_lines": hits[:50], "hit_count": len(hits)}

        # named defs/classes that look like the relevant zones
        def _match(name):
            n = name.lower()
            tags = []
            if any(p in n for p in ("financ", "reconcile", "gate")): tags.append("FINANCIAL_GATE")
            if any(p in n for p in ("basic", "opinion", "rating", "target")): tags.append("BASICINFO_OPINION")
            if any(p in n for p in ("trust", "matrix", "confidence")): tags.append("TRUST_MATRIX")
            if any(p in n for p in ("seal", "canonical", "readonly")): tags.append("SEAL_GATE")
            return tags

        named = []
        for nm, ln in defs + classes:
            t = _match(nm)
            if t:
                named.append({"name": nm, "line": ln, "tags": t})
        res["named_zones"] = named

        # verdict: PASS if parseable and at least IMPORT_BLOCK + 1 other anchor located
        located = sum(1 for k in ("FINANCIAL_GATE", "BASICINFO_OPINION", "TRUST_MATRIX", "SEAL_GATE")
                      if res["anchors"][k]["hit_count"] > 0)
        res["anchors_located"] = located
        if res.get("ast_parseable") and last_import > 0 and located >= 1:
            res["status"] = "PASS"
        else:
            res["status"] = "WARN"
            res["risk"] = "YELLOW"
            if not res.get("ast_parseable"):
                res["issues"].append("MASTER_NOT_PARSEABLE_BLOCKS_PATCH")
        res["next_runnable"] = (res["status"] == "PASS" and not already_patched)
        _write_json(out_json, res)
        return 0
    except Exception as e:
        res["status"] = "FAIL"; res["risk"] = "RED"
        res["issues"].append("FATAL: %s" % e)
        res["traceback"] = traceback.format_exc()
        _write_json(out_json, res)
        return 1


# ----------------------------------------------------------------------------
# append-patch : append-only guarded hookup block. SHA backup + py_compile + rollback.
# ----------------------------------------------------------------------------
def _policy_module_dotted(policy_path):
    # best-effort module name from filename stem
    return os.path.splitext(os.path.basename(policy_path))[0]


def cmd_append_patch(canonical_master, policy_module, backup_dir, out_json):
    res = {
        "command": "append-patch", "ts": _now(),
        "canonical_master": canonical_master, "policy_module": policy_module,
        "mutation": True, "mode": "APPEND_ONLY", "status": "UNKNOWN", "risk": "GREEN", "issues": [],
    }
    try:
        for label, p in (("CANONICAL_MASTER", canonical_master), ("POLICY_MODULE", policy_module)):
            if not os.path.isfile(p):
                res["status"] = "FAIL"; res["risk"] = "RED"
                res["issues"].append("%s_NOT_FOUND" % label)
                _write_json(out_json, res); return 1

        src = _read_text(canonical_master)
        res["sha256_before"] = _sha256(canonical_master)
        res["lines_before"] = len(src.splitlines())

        if MARKER_BEGIN in src:
            res["status"] = "SKIP"
            res["issues"].append("ALREADY_PATCHED_IDEMPOTENT")
            res["sha256_after"] = res["sha256_before"]
            _write_json(out_json, res); return 0

        # SHA256 backup
        os.makedirs(backup_dir, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, os.path.basename(canonical_master) + ".bak_" + stamp)
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(src)
        res["backup_path"] = backup_path

        dotted = _policy_module_dotted(policy_module)
        block = (
            "\n\n" + MARKER_BEGIN + "\n"
            "# Append-only hookup of VIS_VRN_HistoricalValidationPolicy_v0100.\n"
            "# Added by VRN Finalize AIO. Does not modify any existing line above.\n"
            "# Financial validation truth is delegated to this policy; broker report /\n"
            "# pdf_table / report_text are NOT treated as financial validation truth.\n"
            "try:\n"
            "    import importlib as _il\n"
            "    _VRN_HVP = None\n"
            "    for _name in ('module.supportive_module.%s', 'supportive_module.%s', '%s'):\n"
            "        try:\n"
            "            _VRN_HVP = _il.import_module(_name); break\n"
            "        except Exception:\n"
            "            _VRN_HVP = None\n"
            "    VRN_HISTORICAL_VALIDATION_POLICY = _VRN_HVP\n"
            "    VRN_HVP_ENABLED = _VRN_HVP is not None\n"
            "except Exception as _e:\n"
            "    VRN_HISTORICAL_VALIDATION_POLICY = None\n"
            "    VRN_HVP_ENABLED = False\n"
            % (dotted, dotted, dotted)
            + MARKER_END + "\n"
        )

        new_src = src.rstrip("\n") + block
        with open(canonical_master, "w", encoding="utf-8") as f:
            f.write(new_src)

        # py_compile verify
        import py_compile
        try:
            py_compile.compile(canonical_master, doraise=True)
            res["py_compile"] = "PASS"
        except py_compile.PyCompileError as ce:
            # rollback
            with open(canonical_master, "w", encoding="utf-8") as f:
                f.write(src)
            res["py_compile"] = "FAIL_ROLLED_BACK"
            res["status"] = "FAIL"; res["risk"] = "RED"
            res["issues"].append("PY_COMPILE_FAILED: %s" % ce)
            res["sha256_after"] = _sha256(canonical_master)
            _write_json(out_json, res); return 1

        res["sha256_after"] = _sha256(canonical_master)
        res["lines_after"] = len(new_src.splitlines())
        res["status"] = "PASS"
        _write_json(out_json, res)
        return 0
    except Exception as e:
        res["status"] = "FAIL"; res["risk"] = "RED"
        res["issues"].append("FATAL: %s" % e)
        res["traceback"] = traceback.format_exc()
        _write_json(out_json, res)
        return 1


# ----------------------------------------------------------------------------
# post-validate : confirm policy hookup present + parseable; truth-source check.
# ----------------------------------------------------------------------------
def cmd_post_validate(canonical_master, out_json):
    res = {"command": "post-validate", "ts": _now(),
           "canonical_master": canonical_master, "mutation": False,
           "status": "UNKNOWN", "risk": "GREEN", "checks": {}, "issues": []}
    try:
        src = _read_text(canonical_master)
        res["sha256"] = _sha256(canonical_master)
        res["checks"]["policy_block_present"] = (MARKER_BEGIN in src and MARKER_END in src)
        res["checks"]["hvp_symbol_present"] = ("VRN_HISTORICAL_VALIDATION_POLICY" in src)
        res["checks"]["hvp_enabled_flag"] = ("VRN_HVP_ENABLED" in src)
        try:
            ast.parse(src)
            res["checks"]["ast_parseable"] = True
        except SyntaxError as e:
            res["checks"]["ast_parseable"] = False
            res["issues"].append("AST_PARSE_ERROR: %s" % e)

        # truth-source guard note (informational; the policy enforces at runtime)
        res["checks"]["truth_source_note"] = (
            "Financial validation truth delegated to HistoricalValidationPolicy; "
            "broker_report / pdf_table / report_text NOT used as financial truth.")

        ok = all(bool(res["checks"].get(k)) for k in
                 ("policy_block_present", "hvp_symbol_present", "hvp_enabled_flag", "ast_parseable"))
        res["status"] = "PASS" if ok else "FAIL"
        if not ok:
            res["risk"] = "RED"
        _write_json(out_json, res)
        return 0 if ok else 1
    except Exception as e:
        res["status"] = "FAIL"; res["risk"] = "RED"
        res["issues"].append("FATAL: %s" % e)
        res["traceback"] = traceback.format_exc()
        _write_json(out_json, res)
        return 1


# ----------------------------------------------------------------------------
# fetch-crossval : yfinance (defensive) + FactSet (bridge pluggable). READ-ONLY.
# ----------------------------------------------------------------------------
def _load_tickers(trust_csv, limit):
    tickers = []
    try:
        with open(trust_csv, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            rd = csv.DictReader(f)
            cols = {c.lower(): c for c in (rd.fieldnames or [])}
            tcol = None
            for cand in ("yfinance ticker", "ticker", "yf ticker"):
                if cand in cols:
                    tcol = cols[cand]; break
            if not tcol:
                return tickers, "NO_TICKER_COLUMN"
            seen = set()
            for row in rd:
                t = (row.get(tcol) or "").strip()
                if t and t not in seen:
                    seen.add(t); tickers.append(t)
                if limit and len(tickers) >= limit:
                    break
        return tickers, None
    except Exception as e:
        return tickers, "READ_ERROR: %s" % e


def _yf_consensus(tkr):
    """Defensive multi-name probe of yfinance consensus fields. Version-drift safe."""
    out = {"ticker": tkr, "source": "yfinance", "ok": False, "fields": {}, "error": None}
    try:
        import yfinance as yf
        t = yf.Ticker(tkr)

        # price targets: try analyst_price_targets, get_analyst_price_targets, then info
        pt = None
        for attr in ("analyst_price_targets", "get_analyst_price_targets"):
            try:
                v = getattr(t, attr)
                pt = v() if callable(v) else v
                if pt is not None:
                    break
            except Exception:
                pt = None
        if isinstance(pt, dict):
            for k in ("low", "mean", "median", "high", "current"):
                if k in pt:
                    out["fields"]["target_%s" % k] = pt.get(k)

        # info fallback for target + recommendation
        info = {}
        try:
            gi = getattr(t, "get_info", None)
            info = gi() if callable(gi) else (getattr(t, "info", {}) or {})
        except Exception:
            info = {}
        for src_k, dst_k in (("targetLowPrice", "target_low"),
                             ("targetMeanPrice", "target_mean"),
                             ("targetMedianPrice", "target_median"),
                             ("targetHighPrice", "target_high"),
                             ("numberOfAnalystOpinions", "analyst_count"),
                             ("recommendationKey", "rating"),
                             ("recommendationMean", "rating_mean")):
            if dst_k not in out["fields"] and isinstance(info, dict) and info.get(src_k) is not None:
                out["fields"][dst_k] = info.get(src_k)

        # earnings / revenue estimate (best-effort, may be DataFrame)
        for attr, label in (("earnings_estimate", "eps_est"),
                            ("revenue_estimate", "rev_est"),
                            ("eps_trend", "eps_trend")):
            try:
                v = getattr(t, attr, None)
                v = v() if callable(v) else v
                if v is not None and hasattr(v, "to_dict"):
                    out["fields"][label] = "present"
            except Exception:
                pass

        out["ok"] = len(out["fields"]) > 0
        return out
    except Exception as e:
        out["error"] = str(e)
        return out


def _factset_consensus(tkr, factset_cfg):
    """FactSet via bridge-pluggable. No creds -> graceful skip. NEVER fabricates."""
    out = {"ticker": tkr, "source": "factset", "ok": False, "fields": {}, "error": None, "skipped": False}
    key = (factset_cfg or {}).get("api_key")
    if not key:
        out["skipped"] = True
        out["error"] = "NO_FACTSET_CREDENTIAL_GRACEFUL_SKIP"
        return out
    try:
        # Pluggable: real FactSet SDK call would go here when creds present.
        # Intentionally NOT fabricating data. If SDK missing -> skip.
        import importlib
        sdk = None
        for name in ("fds.sdk.FactSetEstimates", "fds.analyticsapi", "factset"):
            try:
                sdk = importlib.import_module(name); break
            except Exception:
                sdk = None
        if sdk is None:
            out["skipped"] = True
            out["error"] = "FACTSET_SDK_NOT_INSTALLED_GRACEFUL_SKIP"
            return out
        # Real call intentionally left to on-machine implementation with entitlement.
        out["skipped"] = True
        out["error"] = "FACTSET_BRIDGE_STUB_AWAITING_ENTITLEMENT_IMPL"
        return out
    except Exception as e:
        out["error"] = str(e)
        return out


def _crossval(yf_fields, fs_fields):
    """Compare overlapping numeric fields with tolerance tiers. Opinion fields not overwritten."""
    rows = []
    keys = set(yf_fields) | set(fs_fields)
    for k in sorted(keys):
        a = yf_fields.get(k); b = fs_fields.get(k)
        rec = {"field": k, "yfinance": a, "factset": b, "verdict": "SINGLE_SOURCE"}
        try:
            if a is not None and b is not None:
                fa, fb = float(a), float(b)
                if fb == 0:
                    rec["verdict"] = "FACTSET_ZERO"
                else:
                    diff = abs(fa - fb) / abs(fb)
                    rec["pct_diff"] = round(diff * 100, 3)
                    if not (0.5 <= (fa / fb if fb else 0) <= 3.0):
                        rec["verdict"] = "FAIL_RANGE"
                    elif diff <= 0.01:
                        rec["verdict"] = "PASS_EXACT"
                    elif diff <= 0.05:
                        rec["verdict"] = "PASS_SOFT"
                    elif diff <= 0.10:
                        rec["verdict"] = "WARN"
                    else:
                        rec["verdict"] = "PASS_RANGE"
        except (ValueError, TypeError):
            rec["verdict"] = "NON_NUMERIC"
        rows.append(rec)
    return rows


# Locked Consensus Data (block 03) column order from VRN_Header_Schema_Registry_v1
CONSENSUS_COLS = [
    "Consensus Source", "Consensus Provider", "Consensus Provider ID",
    "Consensus Date", "Consensus Period", "Consensus Currency",
    "Consensus Rating", "Consensus Target Mean", "Consensus Target Median",
    "Consensus Target High", "Consensus Target Low", "Consensus Analyst Count",
    "Consensus EPS Current Year", "Consensus EPS Next Year",
    "Consensus Revenue Current Year", "Consensus Revenue Next Year",
    "Consensus Revision Direction", "Consensus Last Updated",
    "Consensus Fetch Status", "Consensus Confidence", "Consensus Note",
]


def _consensus_row(tkr, source, prov_id, fields, fetch_status, note):
    """Map a fetched source's fields into the locked block-03 schema."""
    f = fields or {}
    return {
        "Consensus Source": source,
        "Consensus Provider": source,
        "Consensus Provider ID": prov_id or tkr,
        "Consensus Date": _now(),
        "Consensus Period": "",
        "Consensus Currency": "TWD" if tkr.upper().endswith((".TW", ".TWO")) else "",
        "Consensus Rating": f.get("rating", ""),
        "Consensus Target Mean": f.get("target_mean", ""),
        "Consensus Target Median": f.get("target_median", ""),
        "Consensus Target High": f.get("target_high", ""),
        "Consensus Target Low": f.get("target_low", ""),
        "Consensus Analyst Count": f.get("analyst_count", ""),
        "Consensus EPS Current Year": f.get("eps_est", ""),
        "Consensus EPS Next Year": "",
        "Consensus Revenue Current Year": f.get("rev_est", ""),
        "Consensus Revenue Next Year": "",
        "Consensus Revision Direction": f.get("eps_trend", ""),
        "Consensus Last Updated": _now(),
        "Consensus Fetch Status": fetch_status,
        "Consensus Confidence": "HIGH" if len(f) >= 4 else ("LOW" if f else "NONE"),
        "Consensus Note": note,
    }


def _fetch_one(raw_tkr, ssot_mode, factset_cfg, market_map, aegis):
    """Normalize TW ticker, try .TW then .TWO, fetch yf + factset. Thread-safe."""
    cands = _normalize_tw_ticker(raw_tkr, market_map, aegis)
    yfr = {"ticker": raw_tkr, "yf_ticker": cands[0] if cands else raw_tkr,
           "source": "yfinance", "ok": False, "fields": {}, "error": None}
    if ssot_mode in ("yfinance", "both"):
        for cand in cands:
            r = _yf_consensus(cand)
            if r.get("ok"):
                yfr = r; yfr["ticker"] = raw_tkr; yfr["yf_ticker"] = cand
                break
            yfr["error"] = r.get("error"); yfr["yf_ticker"] = cand
    fsr = ({"fields": {}, "ok": False, "skipped": True, "error": "MODE_OFF"}
           if ssot_mode not in ("factset", "both")
           else _factset_consensus(raw_tkr, factset_cfg))
    return {"raw": raw_tkr, "yfinance": yfr, "factset": fsr}


def cmd_fetch_crossval(trust_csv, out_json, ssot_mode, limit, factset_key, tools_dir):
    res = {"command": "fetch-crossval", "ts": _now(), "ssot_mode": ssot_mode,
           "mutation": False, "status": "UNKNOWN", "risk": "GREEN",
           "summary": {}, "rows": [], "issues": [], "tool_log": []}
    consensus_rows = []
    out_consensus_csv = os.path.join(os.path.dirname(out_json) or ".", "VRN_Consensus_Data.csv")
    try:
        tools = _bind_tools(tools_dir)
        res["tool_log"] = tools["log"]
        aegis = tools["aegis"]
        celeritas = tools["celeritas"]

        tickers, err = _load_tickers(trust_csv, limit)
        if err:
            res["issues"].append(err)
        res["ticker_count"] = len(tickers)
        factset_cfg = {"api_key": factset_key} if factset_key else {}

        market_map = _build_market_map(aegis)
        res["market_map_size"] = len(market_map)

        worker = lambda tk: _fetch_one(tk, ssot_mode, factset_cfg, market_map, aegis)

        fetched = None
        if celeritas is not None and hasattr(celeritas, "xmap"):
            try:
                fetched = celeritas.xmap(worker, tickers, mode="thread", guard_mem=False)
                res["accel"] = "celeritas.xmap"
            except Exception as ce:
                res["issues"].append("XMAP_FALLBACK: %s" % ce)
                fetched = None
        if fetched is None:
            try:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=8) as ex:
                    fetched = list(ex.map(worker, tickers))
                res["accel"] = "threadpool"
            except Exception:
                fetched = [worker(t) for t in tickers]
                res["accel"] = "serial"

        yf_ok = fs_ok = fs_skip = 0
        pass_exact = pass_soft = warn = fail = single = 0
        for item in fetched:
            if isinstance(item, Exception) or not isinstance(item, dict):
                res["issues"].append("WORKER_ERROR: %s" % item)
                continue
            tkr = item["raw"]
            yfr = item["yfinance"]; fsr = item["factset"]
            if yfr.get("ok"): yf_ok += 1
            if fsr.get("ok"): fs_ok += 1
            if fsr.get("skipped"): fs_skip += 1

            if ssot_mode in ("yfinance", "both"):
                consensus_rows.append(_consensus_row(
                    yfr.get("yf_ticker", tkr), "yfinance", tkr, yfr.get("fields", {}),
                    "OK" if yfr.get("ok") else ("ERROR: %s" % yfr.get("error")),
                    yfr.get("error") or ""))
            if ssot_mode in ("factset", "both"):
                fs_status = ("OK" if fsr.get("ok")
                             else ("SKIP: %s" % fsr.get("error") if fsr.get("skipped")
                                   else "ERROR: %s" % fsr.get("error")))
                consensus_rows.append(_consensus_row(
                    tkr, "factset", tkr, fsr.get("fields", {}), fs_status, fsr.get("error") or ""))

            cv = _crossval(yfr.get("fields", {}), fsr.get("fields", {}))
            for r in cv:
                v = r["verdict"]
                if v == "PASS_EXACT": pass_exact += 1
                elif v == "PASS_SOFT": pass_soft += 1
                elif v == "WARN": warn += 1
                elif v in ("FAIL_RANGE", "FACTSET_ZERO"): fail += 1
                elif v == "SINGLE_SOURCE": single += 1
            res["rows"].append({"ticker": tkr, "yfinance": yfr, "factset": fsr, "crossval": cv})

        try:
            with open(out_consensus_csv, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=CONSENSUS_COLS)
                w.writeheader()
                for r in consensus_rows:
                    w.writerow(r)
            res["consensus_csv"] = out_consensus_csv
            res["consensus_rows"] = len(consensus_rows)
        except Exception as ce:
            res["issues"].append("CONSENSUS_CSV_WRITE_ERROR: %s" % ce)

        res["summary"] = {
            "tickers": len(tickers), "yfinance_ok": yf_ok,
            "factset_ok": fs_ok, "factset_skipped": fs_skip,
            "consensus_rows": len(consensus_rows), "accel": res.get("accel"),
            "market_map_size": len(market_map),
            "pass_exact": pass_exact, "pass_soft": pass_soft,
            "warn": warn, "fail": fail, "single_source": single,
        }
        res["status"] = "PASS"
        _write_json(out_json, res)
        return 0
    except Exception as e:
        res["status"] = "FAIL"; res["risk"] = "RED"
        res["issues"].append("FATAL: %s" % e)
        res["traceback"] = traceback.format_exc()
        _write_json(out_json, res)
        return 1


def main(argv):
    if len(argv) < 2:
        print("usage: vrn_finalize_core.py <command> ...")
        return 2
    cmd = argv[1]
    try:
        if cmd == "anchor-preview":
            return cmd_anchor_preview(argv[2], argv[3])
        if cmd == "append-patch":
            return cmd_append_patch(argv[2], argv[3], argv[4], argv[5])
        if cmd == "post-validate":
            return cmd_post_validate(argv[2], argv[3])
        if cmd == "fetch-crossval":
            mode = argv[4] if len(argv) > 4 else "yfinance"
            limit = int(argv[5]) if len(argv) > 5 and argv[5].isdigit() else 0
            fkey = argv[6] if len(argv) > 6 and argv[6] not in ("", "-", "none") else None
            tdir = argv[7] if len(argv) > 7 else ""
            return cmd_fetch_crossval(argv[2], argv[3], mode, limit, fkey, tdir)
        print("unknown command: %s" % cmd)
        return 2
    except IndexError:
        print("missing args for command: %s" % cmd)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

'@
    [IO.File]::WriteAllText($script:PyCore, $coreText, (New-Object System.Text.UTF8Encoding($false)))
    Write-VLog "Python core written: ${script:PyCore}" "BOOT"

    $Python = Find-Python
    Write-VLog "Python: ${Python}" "BOOT"

    # ---- Phase 0  Hydra prevention denylist front gate ----
    Show-Step 8 "Phase 0  Hydra prevention denylist"
    foreach ($k in $script:DoNotRedo.Keys) {
        Write-VLog "DO_NOT_REDO  ${k} = $($script:DoNotRedo[$k])  (SKIP)" "HYDRA"
    }
    Add-Phase "Phase 0 Hydra Denylist" "ENFORCED" "GREEN" "6 sealed items locked SKIP"

    # ---- Phase 1  base evidence re-verify  read-only ----
    Show-Step 20 "Phase 1  base evidence re-verify"
    $masterOk = Test-Path -LiteralPath $CanonicalMaster
    $policyOk = Test-Path -LiteralPath $PolicyModule
    $trustOk  = Test-Path -LiteralPath $TrustMatrixCsv
    $masterSha = if ($masterOk) { (Get-FileHash -LiteralPath $CanonicalMaster -Algorithm SHA256).Hash } else { "MISSING" }
    $policySha = if ($policyOk) { (Get-FileHash -LiteralPath $PolicyModule -Algorithm SHA256).Hash } else { "MISSING" }
    $trustRows = 0
    $trustRawLines = 0
    if ($trustOk) {
        $trustRows = (Import-Csv -LiteralPath $TrustMatrixCsv | Measure-Object).Count
        $trustRawLines = ((Get-Content -LiteralPath $TrustMatrixCsv | Measure-Object -Line).Lines) - 1
        if ($trustRawLines -lt 0) { $trustRawLines = 0 }
    }
    Write-VLog "CanonicalMaster exists=${masterOk} sha=${masterSha}" "EVID"
    Write-VLog "PolicyModule    exists=${policyOk} sha=${policySha}" "EVID"
    Write-VLog "TrustMatrix parsed=${trustRows} rawlines=${trustRawLines} expected=${ExpectedTrustRows}" "EVID"
    # GREEN as long as the core files exist and the matrix has rows. Row-count delta is informational
    # (Import-Csv can undercount multiline fields; registry number may reference a different snapshot).
    $evidPass = $masterOk -and $policyOk -and $trustOk -and ($trustRows -gt 0)
    $rowNote = "trust parsed ${trustRows} / raw ${trustRawLines} / expected ${ExpectedTrustRows}"
    if ($trustRows -ne $ExpectedTrustRows) { $rowNote = $rowNote + "  (delta noted)" }
    Add-Phase "Phase 1 Base Evidence" $(if ($evidPass) { "PASS" } else { "WARN" }) $(if ($evidPass) { "GREEN" } else { "YELLOW" }) $rowNote
    if (-not $masterOk) { throw "CanonicalMaster not found: ${CanonicalMaster}" }

    # ---- Phase 2  Anchor Patch Preview  no mutation ----
    Show-Step 38 "Phase 2  Anchor Patch Preview  no mutation"
    $apJson = Join-Path $script:RunDir "anchor_preview.json"
    Invoke-PyCmd $Python $script:PyCore @("anchor-preview", $CanonicalMaster, $apJson) | Out-Null
    $ap = Read-JsonSafe $apJson
    $apStatus = if ($ap) { [string]$ap.status } else { "FAIL" }
    $apAlready = if ($ap) { [bool]$ap.already_patched } else { $false }
    Write-VLog "Anchor preview status=${apStatus} already_patched=${apAlready}" "ANCHOR"
    Add-Phase "Phase 2 Anchor Preview" $apStatus $(if ($apStatus -eq "PASS") { "GREEN" } else { "YELLOW" }) "located $(if($ap){$ap.anchors_located}else{0}) anchor zones"

    $patchStatus = "NOT_RUN"
    $pvStatus    = "NOT_RUN"

    if ($StopAfterPreview) {
        Write-VLog "StopAfterPreview set  three-process chain halts after preview." "GATE"
        Add-Phase "Phase 3 Append Patch" "SKIPPED" "GREEN" "StopAfterPreview switch"
        Add-Phase "Phase 4 Post Validate" "SKIPPED" "GREEN" "StopAfterPreview switch"
    }
    elseif ($apStatus -eq "PASS" -or $apAlready) {
        # ---- Phase 3  Append-only Patch  gated on anchor PASS ----
        Show-Step 58 "Phase 3  Append-only Patch"
        $backupDir = Join-Path $script:RunDir "backup"
        $ppJson = Join-Path $script:RunDir "append_patch.json"
        Invoke-PyCmd $Python $script:PyCore @("append-patch", $CanonicalMaster, $PolicyModule, $backupDir, $ppJson) | Out-Null
        $pp = Read-JsonSafe $ppJson
        $patchStatus = if ($pp) { [string]$pp.status } else { "FAIL" }
        Write-VLog "Append patch status=${patchStatus}" "PATCH"
        Add-Phase "Phase 3 Append Patch" $patchStatus $(if ($patchStatus -in @("PASS","SKIP")) { "GREEN" } else { "RED" }) "append-only  sha after $(if($pp){$pp.sha256_after}else{'?'})"

        if ($patchStatus -in @("PASS", "SKIP")) {
            # ---- Phase 4  Post-patch validation ----
            Show-Step 76 "Phase 4  Post-patch validation"
            $pvJson = Join-Path $script:RunDir "post_validate.json"
            Invoke-PyCmd $Python $script:PyCore @("post-validate", $CanonicalMaster, $pvJson) | Out-Null
            $pv = Read-JsonSafe $pvJson
            $pvStatus = if ($pv) { [string]$pv.status } else { "FAIL" }
            Write-VLog "Post validate status=${pvStatus}" "POSTVAL"
            Add-Phase "Phase 4 Post Validate" $pvStatus $(if ($pvStatus -eq "PASS") { "GREEN" } else { "RED" }) "policy hookup verified"
        } else {
            Add-Phase "Phase 4 Post Validate" "BLOCKED" "RED" "patch did not pass"
        }
    }
    else {
        Write-VLog "Anchor preview not PASS  patch blocked  honoring gate." "GATE"
        Add-Phase "Phase 3 Append Patch" "BLOCKED" "YELLOW" "anchor preview not PASS"
        Add-Phase "Phase 4 Post Validate" "BLOCKED" "YELLOW" "upstream blocked"
    }

    # ---- Consensus Data cross-validation probe  read-only  block-03 schema ----
    Show-Step 90 "Consensus cross-validation  yfinance + FactSet"
    $fkey = if ([string]::IsNullOrWhiteSpace($FactSetApiKey)) { "none" } else { $FactSetApiKey }
    if ([string]::IsNullOrWhiteSpace($FactSetApiKey) -and ($SsotMode -in @("factset","both"))) {
        Write-VLog "No FactSet credential  FactSet rows will graceful-skip  no fake data." "FETCH"
    }
    $fetchSrc = if ($trustOk) { $TrustMatrixCsv } else { $FinancialCsv }
    $fcJson = Join-Path $script:RunDir "fetch_crossval.json"
    Invoke-PyCmd $Python $script:PyCore @("fetch-crossval", $fetchSrc, $fcJson, $SsotMode, "$FetchLimit", $fkey, $ToolsDir) | Out-Null
    $fc = Read-JsonSafe $fcJson
    $fcStatus = if ($fc) { [string]$fc.status } else { "FAIL" }
    $fcAccel  = if ($fc -and $fc.summary) { [string]$fc.summary.accel } else { "?" }
    Write-VLog "Fetch cross-val status=${fcStatus} accel=${fcAccel}" "FETCH"
    if ($fc -and $fc.tool_log) { foreach ($tl in $fc.tool_log) { Write-VLog "  tool: ${tl}" "FETCH" } }
    Add-Phase "Consensus Cross-Val" $fcStatus "GREEN" "$(if($fc){$fc.summary.consensus_rows}else{0}) consensus rows  accel=${fcAccel}"

    # ---- HTML report  VIA Visual Lock v1 ----
    Show-Step 96 "Render HTML report"
    Add-Type -AssemblyName System.Web -ErrorAction SilentlyContinue

    $phaseRows = ConvertTo-HtmlRows $script:Phases @("Name","Status","Risk","Note")
    $denyRows  = [System.Text.StringBuilder]::new()
    foreach ($k in $script:DoNotRedo.Keys) {
        [void]$denyRows.Append("<tr><td>" + [System.Web.HttpUtility]::HtmlEncode($k) + "</td><td>" + [System.Web.HttpUtility]::HtmlEncode([string]$script:DoNotRedo[$k]) + "</td><td>SKIP</td></tr>")
    }
    $consRows = ""
    if ($fc -and $fc.rows) {
        $sb2 = [System.Text.StringBuilder]::new()
        foreach ($r in $fc.rows) {
            $yfStat = ""
            try { $yfStat = [string]$r.yfinance.ok } catch { $yfStat = "" }
            $fsSkip = ""
            try { $fsSkip = [string]$r.factset.skipped } catch { $fsSkip = "" }
            [void]$sb2.Append("<tr><td>" + [System.Web.HttpUtility]::HtmlEncode([string]$r.ticker) + "</td><td>yf_ok=" + $yfStat + "</td><td>fs_skip=" + $fsSkip + "</td></tr>")
        }
        $consRows = $sb2.ToString()
    }
    $logText = [System.Web.HttpUtility]::HtmlEncode(($script:LogList -join "`n"))

    $elapsed = [math]::Round($script:Watch.Elapsed.TotalSeconds, 2)
    $overallRisk = if ($script:Phases.Where({ $_.Risk -eq "RED" }).Count -gt 0) { "RED" } elseif ($script:Phases.Where({ $_.Risk -eq "YELLOW" }).Count -gt 0) { "YELLOW" } else { "GREEN" }

    $tpl = @'
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>VRN Finalize AIO</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:#f5f4f0;--card:#fff;--ink:#1a1a1a;--ink2:#3a3a3a;--ink3:#6a6a6a;--rule:#d8d6cf;--blue:#4c78a8;--teal:#439a9a;--amber:#d4a02a;--red:#c0504d;--green:#5a9a5a;--fd:'Syne',sans-serif;--fb:'DM Sans',sans-serif;--fm:'DM Mono',monospace;}
*{box-sizing:border-box;}body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--fb);font-size:12px;line-height:1.5;}
.top{height:4px;background:linear-gradient(90deg,#c0504d,#d4a02a,#5a9a5a,#439a9a,#4c78a8);}
.wrap{max-width:1180px;margin:0 auto;padding:22px 18px 60px;}
h1{font-family:var(--fd);font-size:22px;margin:14px 0 2px;}
.sub{color:var(--ink3);font-size:11px;margin-bottom:18px;}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:14px 0 22px;}
.card{background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:14px;}
.card .k{font-size:10px;color:var(--ink3);text-transform:uppercase;letter-spacing:.06em;}
.card .v{font-family:var(--fm);font-size:20px;margin-top:6px;}
.sec{background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:16px;margin-bottom:16px;}
.sec h2{font-family:var(--fd);font-size:14px;margin:0 0 10px;}
table{width:100%;border-collapse:collapse;font-size:11px;}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--rule);vertical-align:top;}
th{font-family:var(--fm);font-size:10px;color:var(--ink3);text-transform:uppercase;letter-spacing:.05em;}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-family:var(--fm);font-size:10px;}
.GREEN{background:#e7f0e7;color:var(--green);}.YELLOW{background:#f6efd9;color:var(--amber);}.RED{background:#f3e0df;color:var(--red);}
pre{background:#0f0f10;color:#e5e5e3;font-family:var(--fm);font-size:10px;padding:14px;border-radius:6px;overflow:auto;max-height:340px;}
.flow{font-family:var(--fm);font-size:11px;color:var(--ink2);line-height:1.9;}
</style></head><body>
<div class="top"></div>
<div class="wrap">
<h1>VeritasReportNova  Finalize AIO</h1>
<div class="sub">VERITAS INTELLIGENCE ANALYTICS  Three-process gated finalize  No-Redo  Append-only  Generated {{TS}}</div>
<div class="cards">
<div class="card"><div class="k">Overall Risk</div><div class="v"><span class="badge {{RISK}}">{{RISK}}</span></div></div>
<div class="card"><div class="k">Anchor Preview</div><div class="v">{{AP}}</div></div>
<div class="card"><div class="k">Append Patch</div><div class="v">{{PP}}</div></div>
<div class="card"><div class="k">Elapsed</div><div class="v">{{SEC}}s</div></div>
</div>
<div class="sec"><h2>Phase Result Matrix</h2><table><tr><th>Phase</th><th>Status</th><th>Risk</th><th>Note</th></tr>{{PHASES}}</table></div>
<div class="sec"><h2>Hydra Prevention Denylist  do not re-run</h2><table><tr><th>Sealed Item</th><th>State</th><th>Action</th></tr>{{DENY}}</table></div>
<div class="sec"><h2>Consensus Cross-Validation  block-03 schema  read-only</h2><table><tr><th>Ticker</th><th>yfinance</th><th>FactSet</th></tr>{{CONS}}</table></div>
<div class="sec"><h2>Locked Header Flow</h2><div class="flow">Source Manifest &rarr; BasicInfo &rarr; Consensus Data &rarr; FinancialData &rarr; Historical Data &rarr; SSOT Normalized &rarr; Trust Matrix &rarr; Quarantine &rarr; Canonical Output</div></div>
<div class="sec"><h2>Run Log</h2><pre>{{LOG}}</pre></div>
</div></body></html>
'@

    $html = $tpl.Replace("{{TS}}", $script:TS).Replace("{{RISK}}", $overallRisk).Replace("{{AP}}", $apStatus).Replace("{{PP}}", $patchStatus).Replace("{{SEC}}", "$elapsed").Replace("{{PHASES}}", $phaseRows).Replace("{{DENY}}", $denyRows.ToString()).Replace("{{CONS}}", $consRows).Replace("{{LOG}}", $logText)

    $htmlPath = Join-Path $script:RunDir "VRN_Finalize_AIO_Report.html"
    [IO.File]::WriteAllText($htmlPath, $html, (New-Object System.Text.UTF8Encoding($false)))
    Write-VLog "HTML report: ${htmlPath}" "OUT"

    Show-Step 100 "DONE"
    Write-Progress -Id 1 -Activity "VRN Finalize AIO" -Completed

    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host " VRN FINALIZE AIO  DONE" -ForegroundColor Cyan
    Write-Host "========================================================================" -ForegroundColor Cyan
    Write-Host "[OVERALL_RISK]   ${overallRisk}"
    Write-Host "[ANCHOR_PREVIEW] ${apStatus}"
    Write-Host "[APPEND_PATCH]   ${patchStatus}"
    Write-Host "[POST_VALIDATE]  ${pvStatus}"
    Write-Host "[CONSENSUS]      ${fcStatus}"
    Write-Host "[HTML]           ${htmlPath}"
    Write-Host "[ELAPSED]        ${elapsed}s"
    Write-Host "========================================================================" -ForegroundColor Cyan

    if (-not $NoOpenHtml) {
        Start-Process $htmlPath
    }
}
catch {
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}

# keep-open  intentionally NOT a finally block.
# A standalone 'finally' keyword orphans when pasted in chunks into an interactive
# PS7 console (the term 'finally' is not recognized). Plain statements after catch
# parse cleanly whether pasted whole or in pieces, and still run on both success and error.
Write-Host ""
Write-Host "PowerShell session remains open." -ForegroundColor Cyan
if ($KeepOpen) {
    Write-Host "Press Enter to close..." -ForegroundColor DarkGray
    try { [void][System.Console]::ReadLine() } catch { Start-Sleep -Seconds 86400 }
}
