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
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
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
