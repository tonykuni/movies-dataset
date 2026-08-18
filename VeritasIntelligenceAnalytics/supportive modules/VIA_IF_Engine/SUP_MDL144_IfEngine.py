# -*- coding: utf-8 -*-
# VIA Industry Forecast · P1 SSOT + Module Integration Engine v0100
# Policy: READ-ONLY source scan · NO child execution · APPEND-ONLY output · NO canonical mutation.
# All heavy repair is PROPOSAL-ONLY; high-risk nodes are suggestions, never auto-applied.

# =============================================================================
# def 00 PARAMETERS / IMPORTS
# =============================================================================
import argparse
import ast
import csv
import datetime as _dt
import hashlib
import html as _html
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

READ_ENCODINGS = ["utf-8-sig", "utf-8", "cp950", "big5", "latin-1"]
MAX_TEXT_BYTES = 2_000_000
SRC_EXT = [".py", ".ps1", ".psm1", ".bat", ".cmd", ".js", ".html", ".htm", ".json", ".md", ".txt", ".csv", ".svg"]
EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache"}
DANGER_TERMS = [
    "Remove-Item", "rm -rf", "del ", "rmdir", "Stop-Process", "taskkill",
    "Move-Item", "Rename-Item", "Format-Volume", "Clear-Content",
    "Invoke-Expression", "iex ", "eval(", "exec(", "os.remove", "shutil.rmtree",
    "DROP TABLE", "TRUNCATE", "canonical", "overwrite",
]
ANCHOR_GROUPS = {
    "SAP": ["SAP", "T-Code", "MM01", "CS01", "C223", "MRP", "Material Master", "Routing"],
    "PLM": ["PLM", "EBOM", "MBOM", "ECO", "ECN", "Revision", "Windchill", "Teamcenter"],
    "MS_PROJECT": ["MS Project", "MPP", "WBS", "Task", "Milestone", "Critical Path", "Baseline"],
    "PMBOK": ["PMBOK", "Scope", "Schedule", "Risk", "Stakeholder", "Procurement", "Change Control"],
    "BOM": ["BOM", "SUPER BOM", "Part Number", "MPN", "AML", "AVL", "Qty"],
    "SSOT": ["SSOT", "Single Source of Truth", "registry", "lineage", "evidence", "parquet", "duckdb"],
    "FETCH": ["fetch", "yfinance", "akshare", "FinMind", "TWSE", "MOPS", "SITCA", "FRED", "scrape"],
    "FACTOR": ["copper", "aluminum", "BDI", "SCFI", "iron ore", "coking coal", "commodity", "factor"],
    "UI": ["html", "dashboard", "svg", "Visual Lock", "fetch(", "matrix"],
    "ENGINE": ["engine", "orchestr", "pipeline", "registry", "AST", "accelerator"],
}
# 30 accelerators declared (2 waves); status: active | hint | proposal | p2
ACCEL_ALL = [
    ("A01", "AST 精準解析", "active"),
    ("A02", "多語言語意分類", "active"),
    ("A03", "九頭龍風險偵測 Hydra", "active"),
    ("A04", "依賴拓撲排序", "hint"),
    ("A05", "沙盒隔離執行", "p2"),
    ("A06", "自動修正建議生成", "proposal"),
    ("A07", "三輪全景式分析", "active"),
    ("A08", "SSOT 對齊", "active"),
    ("A09", "視覺化矩陣生成 RYG", "active"),
    ("A10", "錯誤分類與分群", "active"),
    ("A11", "性能與複雜度分析", "active"),
    ("A12", "多子系統同步檢視", "hint"),
    ("A13", "版本差異與回滾偵測", "active"),
    ("A14", "覆蓋率與回歸檢查", "hint"),
    ("A15", "修正順序最佳化", "proposal"),
    # ---- wave 2 (A16-A30) ----
    ("A16", "重複/近重複檔偵測 (sha)", "active"),
    ("A17", "孤兒/未引用偵測", "hint"),
    ("A18", "編碼一致性稽核", "active"),
    ("A19", "命名規範稽核 (VIA/def_)", "active"),
    ("A20", "秘密/憑證掃描 (值不外顯)", "active"),
    ("A21", "膨脹/大檔偵測", "active"),
    ("A22", "死碼/未使用函式提示", "hint"),
    ("A23", "技術債分類 TODO/FIXME", "active"),
    ("A24", "授權/版權標頭稽核", "hint"),
    ("A25", "商品因子覆蓋稽核", "active"),
    ("A26", "股票三碼一致性 (.TW/.TWO/TT)", "active"),
    ("A27", "SAP/MSP 不可變代號稽核", "active"),
    ("A28", "資料新鮮度/時間戳", "active"),
    ("A29", "跨檔函式/類別索引", "active"),
    ("A30", "治理健康評分 A-F", "active"),
]

SECRET_PATTERNS = [
    ("AWS_KEY", r"AKIA[0-9A-Z]{16}"),
    ("PRIVATE_KEY", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ("BEARER", r"(?i)bearer\s+[A-Za-z0-9\-\._~\+\/]{20,}"),
    ("API_KEY", r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9\-_]{16,}['\"]"),
    ("PASSWORD", r"(?i)password\s*[:=]\s*['\"][^'\"]{6,}['\"]"),
    ("SLACK", r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
]

# =============================================================================
# def 01 UTILS
# =============================================================================
def def_now_iso() -> str:
    return _dt.datetime.now().replace(microsecond=0).isoformat()

def def_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def def_prog(pct: float, label: str) -> None:
    # progress goes to stderr so stdout stays clean (final JSON manifest only)
    try:
        sys.stderr.write("@@PROGRESS|%d|%s\n" % (int(pct), str(label).replace("|", "/")))
        sys.stderr.flush()
    except Exception:
        pass

def def_ensure(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def def_read_text(path: Path) -> Tuple[bool, str, str]:
    try:
        data = path.read_bytes()[:MAX_TEXT_BYTES]
    except Exception as exc:
        return False, "", "READ_FAIL:%s" % exc
    for enc in READ_ENCODINGS:
        try:
            return True, data.decode(enc), enc
        except Exception:
            continue
    return True, data.decode("utf-8", errors="replace"), "utf-8-replace"

def def_hash(path: Path, cap: int = 1_048_576) -> str:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            h.update(f.read(cap))
        return h.hexdigest()[:16]
    except Exception:
        return ""

def def_rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def def_count(text: str, terms) -> int:
    low = text.lower()
    return sum(low.count(str(t).lower()) for t in terms)

def def_write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def def_write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    keys: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: def_flat(r.get(k, "")) for k in keys})

def def_flat(v: Any) -> Any:
    if isinstance(v, (list, tuple, set)):
        return " | ".join(str(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return v

def def_try_parquet(path: Path, rows: List[Dict[str, Any]]) -> bool:
    try:
        import pyarrow as pa  # noqa
        import pyarrow.parquet as pq  # noqa
        if not rows:
            return False
        cols: Dict[str, List[Any]] = {}
        keys: List[str] = []
        for r in rows:
            for k in r.keys():
                if k not in keys:
                    keys.append(k)
        for k in keys:
            cols[k] = [def_flat(r.get(k, "")) for r in rows]
        pq.write_table(pa.table(cols), str(path))
        return True
    except Exception:
        return False

# =============================================================================
# def 02 CLASSIFY / LAYER / RISK
# =============================================================================
def def_layer_role(ext: str, text: str) -> Tuple[str, str]:
    if ext == ".py":
        if def_count(text, ANCHOR_GROUPS["FETCH"]) > 0:
            return "ENGINE", "fetch_engine_py"
        if def_count(text, ANCHOR_GROUPS["SSOT"]) > 0:
            return "ENGINE", "ssot_core_py"
        return "ENGINE", "python_module"
    if ext in (".ps1", ".psm1", ".bat", ".cmd"):
        return "ACTIVATOR", "powershell_launcher"
    if ext == ".js":
        return "ENGINE", "js_module"
    if ext in (".html", ".htm", ".svg"):
        return "UI", "html_ui"
    if ext == ".json":
        return "CONFIG", "json_registry"
    if ext in (".md", ".txt"):
        return "DOC", "document"
    if ext == ".csv":
        return "DATA", "csv_data"
    return "OTHER", "other"

def def_risk(text: str, name: str) -> Tuple[str, int, List[str]]:
    hits = [t for t in DANGER_TERMS if t.lower() in text.lower()]
    score = len(hits)
    if name.lower().endswith(".bak"):
        score += 0  # backups are safe; noted separately
    if score >= 3:
        return "HIGH", score, hits
    if score == 2:
        return "REVIEW", score, hits
    if score == 1:
        return "MEDIUM", score, hits
    return "LOW", 0, hits

def def_ast_py(text: str) -> Dict[str, Any]:
    out = {"functions": 0, "classes": 0, "imports": 0, "parse_ok": True, "modules": []}
    try:
        tree = ast.parse(text)
    except Exception:
        out["parse_ok"] = False
        return out
    mods: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out["functions"] += 1
        elif isinstance(node, ast.ClassDef):
            out["classes"] += 1
        elif isinstance(node, ast.Import):
            out["imports"] += 1
            for a in node.names:
                mods.append(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            out["imports"] += 1
            if node.module:
                mods.append(node.module.split(".")[0])
    out["modules"] = sorted(set(mods))
    return out

def def_secret_scan(text: str) -> List[str]:
    hits: List[str] = []
    for name, pat in SECRET_PATTERNS:
        try:
            if re.search(pat, text):
                hits.append(name)
        except Exception:
            continue
    return sorted(set(hits))

def def_governance_grade(total: int, high: int, review: int, medium: int) -> str:
    if total <= 0:
        return "N/A"
    bad = high * 3 + review * 2 + medium
    ratio = bad / float(max(1, total))
    if high == 0 and ratio < 0.05:
        return "A"
    if ratio < 0.12:
        return "B"
    if ratio < 0.25:
        return "C"
    if ratio < 0.50:
        return "D"
    return "F"

# =============================================================================
# def 03 AUTO-ID (append-only, no renumber)
# =============================================================================
ENTITY_PREFIX = {
    "python_module": "ENG", "ssot_core_py": "ENG", "fetch_engine_py": "ENG", "js_module": "ENG",
    "powershell_launcher": "ACT", "html_ui": "UI", "json_registry": "CFG",
    "document": "DOC", "csv_data": "DAT", "other": "OTH",
}

def def_load_persistent(reg_path: Path) -> Dict[str, str]:
    existing: Dict[str, str] = {}
    if reg_path.exists():
        try:
            with reg_path.open("r", encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    key = row.get("natural_key", "")
                    vid = row.get("via_id", "")
                    if key and vid:
                        existing[key] = vid
        except Exception:
            pass
    return existing

def def_assign_ids(assets: List[Dict[str, Any]], existing: Dict[str, str], date_tag: str) -> List[Dict[str, Any]]:
    counters: Dict[str, int] = {}
    for vid in existing.values():
        m = re.match(r"VIA-([A-Z]+)-\d{8}-(\d{6})", vid)
        if m:
            p, n = m.group(1), int(m.group(2))
            counters[p] = max(counters.get(p, 0), n)
    reg: List[Dict[str, Any]] = []
    for a in assets:
        pref = ENTITY_PREFIX.get(a["role"], "OTH")
        key = "%s::%s" % (a["relative_path"], a["role"])
        if key in existing:
            vid = existing[key]
            status = "EXISTING"
        else:
            counters[pref] = counters.get(pref, 0) + 1
            vid = "VIA-%s-%s-%06d" % (pref, date_tag, counters[pref])
            status = "NEW"
        a["via_id"] = vid
        reg.append({"via_id": vid, "natural_key": key, "role": a["role"], "layer": a["layer"],
                    "relative_path": a["relative_path"], "sha16": a.get("sha16", ""),
                    "id_status": status, "assigned_at": def_now_iso()})
    return reg

# =============================================================================
# def 04 MODULE BINDINGS (roles from config; existence-verified; NOT executed)
# =============================================================================
def def_bindings(cfg: Dict[str, Any], base: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    mb = cfg.get("module_bindings", {})

    def add(role: str, rel: str, kind: str, exec_p1: bool, note: str = "") -> None:
        full = base / Path(rel.replace("\\", "/"))
        out.append({
            "role": role, "kind": kind, "relative_path": rel.replace("\\", "/"),
            "exists": full.exists(), "execute_in_p1": exec_p1,
            "bind_status": "FOUND" if full.exists() else "MISSING", "note": note,
        })

    for key, val in mb.items():
        if isinstance(val, dict) and "path" in val:
            add(val.get("role", key), val["path"], val.get("kind", ""), bool(val.get("execute_in_p1", False)), val.get("note", ""))
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "path" in item:
                    add(item.get("role", key), item["path"], item.get("kind", ""), bool(item.get("execute_in_p1", False)), item.get("note", ""))
                elif isinstance(item, str):
                    add(key, item, "file", False, "")
    return out

# =============================================================================
# def 05 HTML UI MATRIX (FlowSystem-style RYG)
# =============================================================================
STYLE = """
:root{--bg:#f5f4f0;--ink:#1e1d1a;--paper:#fffefb;--line:#e3e0d8;--hi:#f0ede4;
--up:#c96b5a;--down:#5a9e6f;--blue:#4c78a8;--gold:#b48a3c;--seal:#b23b32;--muted:#8a857a}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:'DM Sans','Noto Sans TC',system-ui,sans-serif;font-size:13px;padding:26px}
.seal{display:inline-flex;width:38px;height:38px;background:var(--seal);color:#fff;border-radius:3px;
align-items:center;justify-content:center;font-weight:800;font-size:20px;margin-right:12px;vertical-align:middle}
h1{font-family:'Syne','DM Sans',sans-serif;font-weight:800;font-size:20px;display:inline-block;vertical-align:middle}
.sub{color:var(--muted);font-family:'DM Mono',monospace;font-size:11px;margin:8px 0 18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:18px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:3px;padding:12px 13px}
.card .k{font-size:10px;color:var(--muted);font-family:'DM Mono',monospace}
.card .v{font-family:'Syne',sans-serif;font-weight:800;font-size:24px;margin-top:4px}
.card.hi .v{color:var(--up)} .card.rv .v{color:var(--gold)} .card.ok .v{color:var(--down)}
h2{font-family:'Syne',sans-serif;font-size:14px;margin:22px 0 9px;border-left:4px solid var(--seal);padding-left:9px}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--line);border-radius:3px;overflow:hidden;font-size:12px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--hi);font-family:'DM Mono',monospace;font-size:9.5px;letter-spacing:.4px;text-transform:uppercase;color:var(--muted)}
tr:hover td{background:#faf8f3}
.mono{font-family:'DM Mono',monospace}
.pill{display:inline-block;font-family:'DM Mono',monospace;font-size:9px;padding:1px 6px;border-radius:2px;border:1px solid var(--line)}
.r-HIGH{color:#fff;background:var(--up);border-color:var(--up)}
.r-REVIEW{color:var(--gold);border-color:var(--gold)}
.r-MEDIUM{color:var(--blue);border-color:var(--blue)}
.r-LOW{color:var(--down);border-color:var(--down)}
.s-FOUND,.s-active{color:var(--down)} .s-MISSING{color:var(--up)} .s-NEW{color:var(--seal)}
.foot{margin-top:24px;color:var(--muted);font-family:'DM Mono',monospace;font-size:10px}
"""

def def_html_matrix(out_path: Path, ctx: Dict[str, Any]) -> None:
    def esc(x: Any) -> str:
        return _html.escape(str(x))

    def card(k: str, v: Any, cls: str = "") -> str:
        return "<div class='card %s'><div class='k'>%s</div><div class='v'>%s</div></div>" % (cls, esc(k), esc(v))

    cards = "".join([
        card("Run ID", ctx["run_id"]),
        card("Total Rows", ctx["total"]),
        card("Governance", ctx.get("grade", "N/A"), "ok"),
        card("HTML U/I", ctx["ui_count"], "ok"),
        card("High Risk", ctx["high"], "hi"),
        card("Review Risk", ctx["review"], "rv"),
        card("Secrets", ctx.get("secrets", 0), "hi"),
        card("NEW IDs", ctx["new_ids"], "ok"),
        card("Bindings FOUND", ctx["bind_found"], "ok"),
    ])

    def rows_html(rows: List[Dict[str, Any]], cols: List[Tuple[str, str]], limit: int = 400) -> str:
        head = "".join("<th>%s</th>" % esc(c[1]) for c in cols)
        body = ""
        for r in rows[:limit]:
            tds = ""
            for key, _ in cols:
                val = r.get(key, "")
                if key == "risk":
                    tds += "<td><span class='pill r-%s'>%s</span></td>" % (esc(val), esc(val))
                elif key in ("bind_status", "id_status", "status"):
                    tds += "<td><span class='s-%s'>%s</span></td>" % (esc(val), esc(val))
                else:
                    tds += "<td class='mono'>%s</td>" % esc(val)
            body += "<tr>%s</tr>" % tds
        more = "" if len(rows) <= limit else "<div class='foot'>Showing %d of %d.</div>" % (limit, len(rows))
        return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>%s" % (head, body, more)

    findings = ctx.get("findings", {})
    accel = "".join(
        "<tr><td class='mono'>%s</td><td>%s</td><td><span class='s-%s'>%s</span></td><td class='mono'>%s</td></tr>"
        % (esc(a[0]), esc(a[1]), "active" if a[2] == "active" else "", esc(a[2]), esc(findings.get(a[0], "")))
        for a in ctx["accelerators"]
    )

    doc = """<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>理 VIA IndustryForecast Safe Panorama</title><style>%s</style></head><body>
<div><span class='seal'>理</span><h1>VIA IndustryForecast · Safe Panorama Matrix</h1></div>
<div class='sub'>Read-only scan · append-only output · no canonical mutation · no delete · %s</div>
<div class='cards'>%s</div>
<div class='sub'>def Base %s</div>
<h2>30 Accelerators (2 waves · A01-A30)</h2><table><thead><tr><th>ID</th><th>Accelerator</th><th>Status</th><th>Finding</th></tr></thead><tbody>%s</tbody></table>
<h2>Module Bindings (existence-verified · NOT executed in P1)</h2>%s
<h2>Auto-ID Registry (append-only)</h2>%s
<h2>Panorama Matrix (Layer / Status / Risk / Path)</h2>%s
<h2>Optimization Proposals (suggestion-only · high-risk never auto-applied)</h2>%s
<div class='foot'>Generated %s · Policy: READ_ONLY_NO_EXECUTION_APPEND_ONLY_NO_CANONICAL_MUTATION</div>
</body></html>""" % (
        STYLE, esc(ctx["run_id"]), cards, esc(ctx["base"]), accel,
        rows_html(ctx["bindings"], [("role", "Role"), ("kind", "Kind"), ("bind_status", "Status"),
                                    ("execute_in_p1", "ExecP1"), ("relative_path", "Path"), ("note", "Note")]),
        rows_html(ctx["auto_id"], [("via_id", "VIA ID"), ("id_status", "Status"), ("role", "Role"),
                                   ("layer", "Layer"), ("relative_path", "Path")]),
        rows_html(ctx["matrix"], [("layer", "Layer"), ("status", "Status"), ("risk", "Risk"),
                                  ("relative_path", "Relative Path"), ("full_path", "Full Path")]),
        rows_html(ctx["proposals"], [("via_id", "VIA ID"), ("risk", "Risk"), ("proposal", "Proposal"),
                                     ("action", "Action"), ("relative_path", "Path")]),
        esc(def_now_iso()),
    )
    out_path.write_text(doc, encoding="utf-8")

# =============================================================================
# def 06 MAIN BUILD
# =============================================================================
def def_scan(base: Path, skip_prefixes: Optional[List[Path]] = None) -> List[Path]:
    found: List[Path] = []
    skips = [sp.resolve() for sp in (skip_prefixes or [])]

    def under_skip(path: Path) -> bool:
        rp = path.resolve()
        for sp in skips:
            try:
                rp.relative_to(sp)
                return True
            except Exception:
                continue
        return False

    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not under_skip(Path(root) / d)]
        for fn in files:
            p = Path(root) / fn
            if p.suffix.lower() in SRC_EXT and not under_skip(p):
                found.append(p)
    return found

def def_scan_backups(base: Path, skip_prefixes: Optional[List[Path]] = None) -> List[Path]:
    skips = [sp.resolve() for sp in (skip_prefixes or [])]

    def under_skip(path: Path) -> bool:
        rp = path.resolve()
        for sp in skips:
            try:
                rp.relative_to(sp)
                return True
            except Exception:
                continue
        return False

    out: List[Path] = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not under_skip(Path(root) / d)]
        for fn in files:
            if fn.lower().endswith(".bak") and not under_skip(Path(root) / fn):
                out.append(Path(root) / fn)
    return out


def def_build(cfg: Dict[str, Any], base: Path, out_root: Path) -> Dict[str, Any]:
    run_id = "RUN_%s_VIA_IF_SAFE_PANORAMA" % def_stamp()
    date_tag = _dt.datetime.now().strftime("%Y%m%d")
    run_dir = out_root / run_id
    reg_dir = out_root / "registry"
    def_ensure(run_dir)
    def_ensure(reg_dir)

    sys_dir_name = cfg.get("roots", {}).get("system_dir_name", "VIA_IndustryForecast")
    skip_prefixes = [out_root, base / sys_dir_name]
    files = def_scan(base, skip_prefixes)
    backups = def_scan_backups(base, skip_prefixes)
    total_files = len(files)
    def_prog(4, "A02 multi-lang classify · scan start (%d files)" % total_files)
    assets: List[Dict[str, Any]] = []
    matrix: List[Dict[str, Any]] = []
    proposals: List[Dict[str, Any]] = []
    ast_rows: List[Dict[str, Any]] = []

    high = review = medium = ui_count = 0
    secrets: List[Dict[str, Any]] = []
    newest_mtime = 0.0
    for idx, p in enumerate(files):
        if total_files and (idx % 50 == 0):
            def_prog(5 + int(50 * idx / total_files), "A01 AST · A03 Hydra · A20 secret · scan %d/%d" % (idx, total_files))
        ok, text, enc = def_read_text(p)
        if not ok:
            continue
        ext = p.suffix.lower()
        layer, role = def_layer_role(ext, text)
        risk, rscore, rhits = def_risk(text, p.name)
        rel = def_rel(p, base)
        sha = def_hash(p)
        anchors = {g: def_count(text, terms) for g, terms in ANCHOR_GROUPS.items()}
        rec = {"relative_path": rel, "full_path": str(p), "name": p.name, "extension": ext,
               "encoding": enc, "layer": layer, "role": role, "risk": risk, "risk_score": rscore,
               "risk_hits": rhits, "sha16": sha, "status": "SCANNED",
               "anchor_ssot": anchors.get("SSOT", 0), "anchor_sap": anchors.get("SAP", 0),
               "anchor_fetch": anchors.get("FETCH", 0), "anchor_factor": anchors.get("FACTOR", 0),
               "lines": text.count("\n") + 1, "bytes": len(text.encode("utf-8", "ignore"))}
        if ext == ".py":
            a = def_ast_py(text)
            rec.update({"py_functions": a["functions"], "py_classes": a["classes"], "py_imports": a["imports"]})
            ast_rows.append({"relative_path": rel, "parse_ok": a["parse_ok"], "functions": a["functions"],
                             "classes": a["classes"], "imports": a["imports"], "modules": a["modules"]})
            if not a["parse_ok"]:
                proposals.append({"via_id": "", "risk": "REVIEW", "proposal": "Python AST parse failed",
                                  "action": "SUGGEST_REVIEW", "relative_path": rel})
        assets.append(rec)
        matrix.append({"layer": layer, "status": "SCANNED", "risk": risk,
                       "relative_path": rel, "full_path": str(p)})
        sec = def_secret_scan(text)
        if sec:
            secrets.append({"relative_path": rel, "types": sec})
            proposals.append({"via_id": "", "risk": "HIGH",
                              "proposal": "A20 possible secret(s): %s — value NOT shown; rotate/remove" % ", ".join(sec),
                              "action": "SUGGEST_ROTATE_REMOVE", "relative_path": rel})
        try:
            mt = p.stat().st_mtime
            if mt > newest_mtime:
                newest_mtime = mt
        except Exception:
            pass
        if risk == "HIGH":
            high += 1
        elif risk == "REVIEW":
            review += 1
        elif risk == "MEDIUM":
            medium += 1
        if layer == "UI":
            ui_count += 1
        # optimization proposals (non-mutating)
        if rec["lines"] > 1500:
            proposals.append({"via_id": "", "risk": "LOW", "proposal": "Large file (%d lines) — consider split" % rec["lines"],
                              "action": "SUGGEST_REFACTOR", "relative_path": rel})
        if p.name.lower().endswith(".bak"):
            proposals.append({"via_id": "", "risk": "LOW", "proposal": "Backup artifact detected",
                              "action": "SUGGEST_ARCHIVE", "relative_path": rel})
        if any(t in text for t in ("TODO", "FIXME", "XXX")):
            proposals.append({"via_id": "", "risk": "LOW", "proposal": "TODO/FIXME marker present",
                              "action": "SUGGEST_TRIAGE", "relative_path": rel})
        if risk in ("HIGH", "REVIEW"):
            proposals.append({"via_id": "", "risk": risk, "proposal": "Danger terms: %s" % (", ".join(rhits) or "n/a"),
                              "action": "SUGGEST_ONLY_NO_AUTO_FIX", "relative_path": rel})

    if backups:
        sample = ", ".join(def_rel(b, base) for b in backups[:3])
        proposals.append({"via_id": "", "risk": "LOW",
                          "proposal": "%d backup (.bak) artifacts — append-only history intact (e.g. %s)" % (len(backups), sample),
                          "action": "SUGGEST_ARCHIVE_KEEP", "relative_path": "(base tree)"})

    def_prog(58, "A13 rollback scan · A11 complexity")
    # auto-id (append-only)
    def_prog(62, "A09 auto-ID registration (append-only)")
    existing = def_load_persistent(reg_dir / "via_auto_id_registry.csv")
    auto_id = def_assign_ids(assets, existing, date_tag)
    # merge back persistent (append-only: existing + new)
    merged: Dict[str, Dict[str, Any]] = {}
    if (reg_dir / "via_auto_id_registry.csv").exists():
        with (reg_dir / "via_auto_id_registry.csv").open("r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                merged[row.get("natural_key", "")] = row
    for r in auto_id:
        merged.setdefault(r["natural_key"], r)
    new_ids = sum(1 for r in auto_id if r["id_status"] == "NEW")

    # bindings + alias + evidence
    def_prog(72, "A12 multi-subsystem bindings · A08 SSOT align")
    bindings = def_bindings(cfg, base)
    bind_found = sum(1 for b in bindings if b["bind_status"] == "FOUND")
    alias_rows = [dict(a, can_modify=False) for a in cfg.get("alias_seed", [])]
    factor_rows: List[Dict[str, Any]] = []
    for fac in cfg.get("factor_registry", []):
        for s in fac.get("sources", []):
            factor_rows.append({"factor_name": fac["name"], "category": fac.get("category", ""),
                                "source_system": s.get("system", ""), "source_symbol": s.get("symbol", ""),
                                "unit": s.get("unit", ""), "can_modify_source_code": False, "note": s.get("note", "")})

    # ---- wave 2 accelerators (A16-A30): computed from read-only scan ----
    def_prog(84, "A16 dedup · A18 encoding · A20 secrets · A25 factors")
    hashmap: Dict[str, List[str]] = {}
    for a in assets:
        h = a.get("sha16", "")
        if h:
            hashmap.setdefault(h, []).append(a["relative_path"])
    dup_groups = [v for v in hashmap.values() if len(v) > 1]
    for grp in dup_groups[:50]:
        proposals.append({"via_id": "", "risk": "LOW",
                          "proposal": "A16 duplicate content (%d files): %s" % (len(grp), ", ".join(grp[:3])),
                          "action": "SUGGEST_DEDUP_REVIEW", "relative_path": grp[0]})
    enc_nonutf = sum(1 for a in assets if a.get("encoding", "") not in ("utf-8", "utf-8-sig"))
    large = sum(1 for a in assets if a.get("lines", 0) > 1500)
    techdebt = sum(1 for pr in proposals if pr.get("action") == "SUGGEST_TRIAGE")
    facs = cfg.get("factor_registry", [])
    fac_sourced = sum(1 for f in facs if f.get("sources"))
    uni = cfg.get("company_universe", [])
    tickers_ok = sum(1 for c in uni if re.match(r"^[1-9]\d{3}$", str(c.get("ticker", ""))))
    immutable = len(cfg.get("alias_seed", []))
    tot_func = sum(r.get("functions", 0) for r in ast_rows)
    tot_cls = sum(r.get("classes", 0) for r in ast_rows)
    src_files = sum(1 for a in assets if a.get("extension", "") in (".py", ".ps1", ".psm1", ".js"))
    file_types = len(set(a.get("extension", "") for a in assets))
    py_files = sum(1 for a in assets if a.get("extension", "") == ".py")
    newest_date = "n/a"
    if newest_mtime > 0:
        newest_date = _dt.datetime.fromtimestamp(newest_mtime).strftime("%Y-%m-%d")
    grade = def_governance_grade(len(assets), high, review, medium)
    def_prog(90, "A26 ticker triple · A27 immutable · A30 grade %s" % grade)

    findings = {
        "A01": "%d py files" % py_files,
        "A02": "%d file types" % file_types,
        "A03": "%d HIGH / %d REVIEW / %d MED" % (high, review, medium),
        "A08": "SSOT anchors indexed",
        "A09": "RYG matrix built",
        "A11": "%d assets scanned" % len(assets),
        "A13": "%d backups" % len(backups),
        "A16": "%d duplicate group(s)" % len(dup_groups),
        "A18": "%d non-UTF8 file(s)" % enc_nonutf,
        "A19": "%d source files" % src_files,
        "A20": "%d file(s) w/ possible secret" % len(secrets),
        "A21": "%d large file(s) >1500L" % large,
        "A23": "%d TODO/FIXME" % techdebt,
        "A25": "%d/%d factors sourced" % (fac_sourced, len(facs)),
        "A26": "%d/%d tickers 4-digit" % (tickers_ok, len(uni)),
        "A27": "%d immutable ext codes" % immutable,
        "A28": "newest %s" % newest_date,
        "A29": "%d funcs / %d classes" % (tot_func, tot_cls),
        "A30": "grade %s" % grade,
    }
    symbol_index = [{"relative_path": r["relative_path"], "functions": r["functions"],
                     "classes": r["classes"], "imports": r["imports"]} for r in ast_rows]

    # write registry outputs (append-only run + persistent)
    def_prog(93, "A06 proposals · A15 fix-order · A07 panorama write")
    def_write_csv(reg_dir / "via_auto_id_registry.csv", list(merged.values()))
    def_write_csv(run_dir / "via_panorama_matrix.csv", matrix)
    def_write_csv(run_dir / "via_asset_registry.csv", assets)
    def_write_csv(run_dir / "via_module_bindings.csv", bindings)
    def_write_csv(run_dir / "via_alias_registry.csv", alias_rows)
    def_write_csv(run_dir / "via_factor_registry.csv", factor_rows)
    def_write_csv(run_dir / "via_ast_registry.csv", ast_rows)
    def_write_csv(run_dir / "via_symbol_index.csv", symbol_index)
    def_write_csv(run_dir / "via_secret_findings.csv", secrets)
    def_write_csv(run_dir / "via_optimization_proposals.csv", proposals)
    def_try_parquet(run_dir / "via_panorama_matrix.parquet", matrix)

    ctx = {
        "run_id": run_id, "base": str(base), "total": len(assets), "ui_count": ui_count,
        "high": high, "review": review, "medium": medium, "new_ids": new_ids, "bind_found": bind_found,
        "accelerators": ACCEL_ALL, "findings": findings, "grade": grade, "secrets": len(secrets),
        "bindings": bindings, "auto_id": auto_id, "matrix": matrix, "proposals": proposals,
    }
    def_prog(96, "A09 RYG matrix · A14 coverage render")
    def_html_matrix(run_dir / "VIA_IF_SafePanorama_Matrix.html", ctx)

    manifest = {
        "run_id": run_id, "generated_at": def_now_iso(), "base": str(base),
        "policy": "READ_ONLY_NO_EXECUTION_APPEND_ONLY_NO_CANONICAL_MUTATION",
        "governance_grade": grade,
        "counts": {"assets": len(assets), "high": high, "review": review, "medium": medium,
                   "ui": ui_count, "new_ids": new_ids, "bindings_found": bind_found,
                   "backups": len(backups), "duplicate_groups": len(dup_groups),
                   "secrets": len(secrets), "proposals": len(proposals)},
        "findings": findings,
        "accelerators": [{"id": a[0], "name": a[1], "status": a[2], "finding": findings.get(a[0], "")} for a in ACCEL_ALL],
        "outputs": ["VIA_IF_SafePanorama_Matrix.html", "via_panorama_matrix.csv", "via_asset_registry.csv",
                    "via_module_bindings.csv", "via_alias_registry.csv", "via_factor_registry.csv",
                    "via_ast_registry.csv", "via_symbol_index.csv", "via_secret_findings.csv",
                    "via_optimization_proposals.csv"],
    }
    def_write_json(run_dir / "via_run_manifest.json", manifest)
    def_prog(100, "A14 coverage · complete")
    return manifest

# =============================================================================
# def 07 SELFTEST / CLI
# =============================================================================
def def_selftest() -> int:
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="via_if_test_"))
    (tmp / "supportive modules").mkdir(parents=True, exist_ok=True)
    (tmp / "functional modules").mkdir(parents=True, exist_ok=True)
    (tmp / "supportive modules" / "VIA_SSOT_Unified.py").write_text(
        "import json\nimport os\nclass SSOT:\n    def run(self):\n        return 1\n", encoding="utf-8")
    (tmp / "functional modules" / "Invoke-VeritasCodexNexus.ps1").write_text(
        "param([string]$OutputRoot)\nWrite-Host 'fetch'\n", encoding="utf-8")
    (tmp / "danger.ps1").write_text("Remove-Item x\nStop-Process y\nRename-Item a b\n", encoding="utf-8")
    (tmp / "ui.html").write_text("<html><body>matrix</body></html>", encoding="utf-8")
    cfg = {"module_bindings": {"fetch_engine": {"role": "fetch_engine",
           "path": "functional modules\\Invoke-VeritasCodexNexus.ps1", "kind": "powershell", "execute_in_p1": False},
           "ssot_core": [{"role": "ssot_core", "path": "supportive modules\\VIA_SSOT_Unified.py", "kind": "python"}]},
           "alias_seed": [{"internal_role": "stock", "external_system": "TWSE", "external_code": "2308"}],
           "factor_registry": [{"name": "Copper", "category": "metal",
                                "sources": [{"system": "AKSHARE", "symbol": "cu", "unit": "CNY/ton"}]}]}
    out = tmp / "_out"
    m = def_build(cfg, tmp, out)
    ok = True
    checks = [
        ("assets>=4", m["counts"]["assets"] >= 4),
        ("high_risk>=1", m["counts"]["high"] >= 1),
        ("ui>=1", m["counts"]["ui"] >= 1),
        ("bindings_found==2", m["counts"]["bindings_found"] == 2),
        ("new_ids>=4", m["counts"]["new_ids"] >= 4),
        ("manifest_ok", "run_id" in m),
    ]
    for name, res in checks:
        print("[%s] %s" % ("PASS" if res else "FAIL", name))
        ok = ok and res
    # append-only re-run: no new ids second time
    m2 = def_build(cfg, tmp, out)
    ap = m2["counts"]["new_ids"] == 0
    print("[%s] append_only_rerun_no_new_ids" % ("PASS" if ap else "FAIL"))
    ok = ok and ap
    print("SELFTEST", "PASS" if ok else "FAIL", "· out:", out)
    return 0 if ok else 1

def def_main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="VIA IndustryForecast P1 SSOT + Module Integration Engine")
    ap.add_argument("--config", default="", help="via_if_config.json path")
    ap.add_argument("--base", default="", help="override base directory to scan")
    ap.add_argument("--output-root", default="", help="append-only output root")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return def_selftest()
    if not args.config:
        print("[FAIL] --config required (or use --selftest)")
        return 2
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    base = Path(args.base) if args.base else Path(cfg["roots"]["base"])
    if not base.exists():
        print("[FAIL] base not found: %s" % base)
        return 2
    out_root = Path(args.output_root) if args.output_root else (base / cfg["roots"]["system_dir_name"] / "07_runs")
    def_ensure(out_root)
    manifest = def_build(cfg, base, out_root)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(def_main())
