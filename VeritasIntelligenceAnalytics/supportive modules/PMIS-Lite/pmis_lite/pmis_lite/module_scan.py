"""模組掃描分類器：盤點專案模組，分 SUPPORTIVE（支援）vs FUNCTIONAL（功能）。

判準（多訊號綜合）：
  - fan-in（被幾個模組 import）：高扇入＝底層支援件。
  - 角色關鍵字：schema/encoding/numbering/resilience/store/... ＝ SUPPORTIVE；
    pipeline/classify/bom/report/... 或有 run()/主流程 ＝ FUNCTIONAL。
  - 有 def run(/def main( 或產出檔案 ＝ FUNCTIONAL 傾向。
純 stdlib、離線、不匯入被掃的模組（只做靜態文字分析，安全）。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import os
import re

SUPPORT_HINT = {"schema", "encoding", "numbering", "resilience", "store", "completeness",
                "panorama", "autodetect", "selfcheck", "feedback", "terms", "normalize",
                "presets", "html_ui", "adapters", "mail_chain", "keywords"}
FUNCTIONAL_HINT = {"pipeline", "classify", "stakeholders", "actions", "bom_template",
                   "super_bom", "psu_taxonomy", "self_train", "process_mining",
                   "report_html", "slides", "autocode", "ingest_engine", "module_scan"}


def scan_project(root: str, exts=(".py", ".ps1")) -> dict:
    files = []
    for dp, dns, fns in os.walk(root):
        if any(s in dp for s in ("__pycache__", ".git", "node_modules")):
            continue
        for fn in fns:
            if fn.lower().endswith(exts):
                files.append(os.path.join(dp, fn))
    py = [f for f in files if f.endswith(".py")]
    names = {_modname(f): f for f in py}

    # fan-in：誰 import 誰
    fanin = {n: 0 for n in names}
    for f in py:
        txt = _read(f)
        for n in names:
            if n and re.search(rf"\bimport\s+{re.escape(n)}\b|from\s+\.?\w*\.?{re.escape(n)}\s+import|from\s+\.{re.escape(n)}\s+import", txt):
                if _modname(f) != n:
                    fanin[n] += 1

    inventory = []
    for f in files:
        txt = _read(f)
        name = _modname(f)
        lines = txt.count("\n") + 1
        has_run = bool(re.search(r"def\s+(run|main)\s*\(", txt))
        role = _classify(name, fanin.get(name, 0), has_run, f)
        inventory.append({
            "module": name or os.path.basename(f), "path": f,
            "type": "ps1" if f.endswith(".ps1") else "py",
            "lines": lines, "fan_in": fanin.get(name, 0),
            "has_run": has_run, "role": role,
        })
    inventory.sort(key=lambda x: (x["role"], -x["fan_in"]))
    counts = {}
    for it in inventory:
        counts[it["role"]] = counts.get(it["role"], 0) + 1
    return {"root": root, "count": len(inventory), "by_role": counts, "inventory": inventory}


def _classify(name, fanin, has_run, path):
    base = (name or os.path.basename(path)).lower()
    if any(h in base for h in ("test", "_test")):
        return "TEST"
    if path.endswith(".ps1"):
        return "LAUNCHER/PS"
    if base in SUPPORT_HINT or fanin >= 3:
        return "SUPPORTIVE"
    if base in FUNCTIONAL_HINT or has_run:
        return "FUNCTIONAL"
    if fanin >= 1:
        return "SUPPORTIVE"
    return "OTHER"


def _modname(path):
    b = os.path.basename(path)
    return b[:-3] if b.endswith(".py") else b


def _read(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def import_guide(inventory) -> dict:
    """產生導入指引：支援件先載、功能件後載，附建議 import 順序。"""
    support = [it["module"] for it in inventory if it["role"] == "SUPPORTIVE"]
    functional = [it["module"] for it in inventory if it["role"] == "FUNCTIONAL"]
    return {
        "load_order": ["1) 先載 SUPPORTIVE 支援件（底層）", *[f"   - {s}" for s in support],
                       "2) 再載 FUNCTIONAL 功能件（上層）", *[f"   - {fn}" for fn in functional]],
        "supportive": support, "functional": functional,
    }
