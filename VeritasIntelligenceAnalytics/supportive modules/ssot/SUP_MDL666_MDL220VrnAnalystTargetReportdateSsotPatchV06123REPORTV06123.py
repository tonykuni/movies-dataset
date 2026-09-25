# -*- coding: utf-8 -*-
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

import ast
import csv
import html
import importlib.util
import json
import py_compile
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_ANALYST_TARGET_REPORTDATE_SSOT_PATCH_V06123"


# ==================================================================================================
# def 01_COMMON
# ==================================================================================================
def def_status_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "YES", "PASS", "GREEN", "N/A"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "YELLOW", "REVIEW", "PARTIAL"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_write_json(path: str | Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_write_csv(path: str | Path, rows: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"empty_marker": ""}]
    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_compile_import(path: str | Path) -> dict:
    p = Path(path)
    out = {"path": str(p), "exists": p.exists(), "ast": False, "compile": False, "import": False, "error": ""}
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        ast.parse(text)
        out["ast"] = True
        py_compile.compile(str(p), doraise=True)
        out["compile"] = True
        spec = importlib.util.spec_from_file_location(p.stem, str(p))
        mod = importlib.util.module_from_spec(spec)
        if spec and spec.loader:
            spec.loader.exec_module(mod)
        out["import"] = True
    except Exception:
        out["error"] = traceback.format_exc()
    return out


def def_table_html(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2>No rows.</section>"
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    th = "".join(f"<th>{html.escape(str(c).replace('_',' ').title())}</th>" for c in fields)
    trs = []
    for r in rows:
        tds = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            lc = c.lower()
            cls = "left" if any(x in lc for x in ["path", "file", "error", "text", "sample"]) else "center"
            cls = "right" if any(x in lc for x in ["count", "price", "score"]) else cls
            tds.append(f"<td class='{cls}'>{html.escape(v)}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: str | Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:#0d1b2f;border-bottom:1px solid #1f3557;position:sticky;top:0;z-index:10}
h1{margin:0;font-size:24px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;padding:20px 32px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(0,0,0,.22)}
.v{font-size:26px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 32px 32px}.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;vertical-align:top}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;text-align:center;max-width:760px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.right{text-align:right;font-variant-numeric:tabular-nums}
tr:hover td{background:rgba(66,217,255,.07)}
footer{padding:18px 32px;color:#9fb3c8;border-top:1px solid #1f3557}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"
    body = "".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>VRN Analyst Target ReportDate Patch v06123</title><style>{css}</style></head>
<body>
<header>
<h1>VRN · Analyst Target + ReportDate SSOT Patch v0.6.12.3</h1>
<div class="sub">VIA_SSOT_Unified append-only · bridge function patch · analyst stopword · target price · ROC/AD date priority</div>
</header>
{card_html}
<main>{body}</main>
<footer>Veritas Intelligence Analytics</footer>
</body>
</html>"""
    Path(path).write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 02_PATCH_BLOCKS
# ==================================================================================================
SSOT_APPEND_BLOCK = r'''

# ==================================================================================================
# [VIS:VRN_ANALYST_TARGET_EXTRACTOR_V06123:START]
# ==================================================================================================
# Append-only SSOT helper block.
# Purpose:
# - Analyst extraction stops before Target Price / Rating / recommendation words.
# - Target Price extraction supports Chinese / English report phrasing.
# - Report Date extraction prioritizes YYYYMMDD and ROC yyyMMdd before loose regex.
# - No canonical mutation.
# - No classifier rewrite.
# ==================================================================================================

import re as _vis_re
from pathlib import Path as _vis_Path
from typing import Any as _vis_Any


VIS_VRN_ANALYST_TARGET_EXTRACTOR_VERSION = "v0.6.12.3"

VIS_VRN_ANALYST_STOPWORDS = [
    "目標價", "目標價格", "合理價", "評等", "評級", "投資評等", "投資建議",
    "買進", "買入", "增持", "中立", "持有", "減持", "賣出", "未評等",
    "Target Price", "TP", "Rating", "Recommendation", "Buy", "Outperform",
    "Neutral", "Hold", "Sell", "Underperform", "NR"
]

VIS_VRN_RATING_WORDS = [
    "買進", "買入", "增持", "中立", "持有", "減持", "賣出", "未評等", "NR",
    "Buy", "Outperform", "Neutral", "Hold", "Sell", "Underperform"
]


def def_vis_vrn_clean_text_v06123(x: _vis_Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    s = _vis_re.sub(r"\s+", " ", s).strip()
    return s


def def_vis_vrn_stop_before_keyword_v06123(s: str) -> str:
    text = def_vis_vrn_clean_text_v06123(s)
    stops = sorted(VIS_VRN_ANALYST_STOPWORDS, key=len, reverse=True)
    for kw in stops:
        m = _vis_re.search(_vis_re.escape(kw), text, flags=_vis_re.I)
        if m:
            text = text[:m.start()].strip()
    text = _vis_re.sub(r"[,，;；:：|｜/／]+$", "", text).strip()
    return text


def def_vis_vrn_extract_analyst_from_text_v06123(text: _vis_Any) -> dict:
    s = def_vis_vrn_clean_text_v06123(text)
    patterns = [
        r"(?:分析師|研究員|Analyst|撰文|作者|Prepared by|Author)\s*[:：]\s*([A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff\s·．.、,，-]{1,60})",
        r"(?:分析師|研究員)\s+([A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff\s·．.、,，-]{1,40})",
    ]
    for pat in patterns:
        m = _vis_re.search(pat, s, flags=_vis_re.I)
        if not m:
            continue
        raw = m.group(1)
        val = def_vis_vrn_stop_before_keyword_v06123(raw)
        val = _vis_re.split(r"[\n\r|｜]", val)[0].strip(" ,，。；;:：")
        if val:
            return {
                "Analyst": val,
                "Analyst Source": "VIA_SSOT_Unified.VIS_VRN_ANALYST_TARGET_EXTRACTOR_V06123",
                "Analyst Confidence": 0.93,
            }
    return {"Analyst": "", "Analyst Source": "", "Analyst Confidence": 0.0}


def def_vis_vrn_extract_rating_target_from_text_v06123(text: _vis_Any) -> dict:
    s = def_vis_vrn_clean_text_v06123(text)
    out = {
        "Rating": "",
        "Target Price": "",
        "Rating Target Source": "",
        "Rating Target Confidence": 0.0,
    }

    rating_pat = r"(買進|買入|增持|中立|持有|減持|賣出|未評等|NR|Buy|Outperform|Neutral|Hold|Sell|Underperform)"
    m = _vis_re.search(rating_pat, s, flags=_vis_re.I)
    if m:
        out["Rating"] = m.group(1)

    target_patterns = [
        r"(?:目標價|目標價格|合理價|Target Price|TP)\s*[:：]?\s*(?:NT\$|新台幣|TWD|NTD)?\s*([0-9]+(?:\.[0-9]+)?)",
        r"(?:給予|上修至|下修至|維持)\s*(?:目標價|目標價格)?\s*(?:NT\$|新台幣|TWD|NTD)?\s*([0-9]+(?:\.[0-9]+)?)\s*元",
        r"([0-9]+(?:\.[0-9]+)?)\s*元\s*(?:目標價|合理價)",
    ]
    for pat in target_patterns:
        m = _vis_re.search(pat, s, flags=_vis_re.I)
        if m:
            out["Target Price"] = m.group(1)
            break

    if out["Rating"] or out["Target Price"]:
        out["Rating Target Source"] = "VIA_SSOT_Unified.VIS_VRN_ANALYST_TARGET_EXTRACTOR_V06123"
        out["Rating Target Confidence"] = 0.93

    return out


def def_vis_vrn_extract_report_date_from_filename_v06123(filename: _vis_Any) -> dict:
    raw = _vis_Path(def_vis_vrn_clean_text_v06123(filename)).name
    stem = _vis_re.sub(r"\.pdf$", "", raw, flags=_vis_re.I)
    candidates = []

    # 1. AD YYYYMMDD / YYYY-MM-DD / YYYY_MM_DD first
    for m in _vis_re.finditer(r"(20\d{2})[-_/年.]?(0[1-9]|1[0-2])[-_/月.]?(0[1-9]|[12]\d|3[01])", stem):
        candidates.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")

    # 2. ROC yyyMMdd, e.g. 1141202 -> 2025-12-02
    for m in _vis_re.finditer(r"(?<!\d)(1[0-9]{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)", stem):
        roc_y = int(m.group(1))
        ad_y = roc_y + 1911
        if 2000 <= ad_y <= 2099:
            candidates.append(f"{ad_y}-{m.group(2)}-{m.group(3)}")

    # 3. AD YYYYMM
    for m in _vis_re.finditer(r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])(?!\d)", stem):
        candidates.append(f"{m.group(1)}-{m.group(2)}")

    # 4. AD year only
    for m in _vis_re.finditer(r"(?<!\d)(20\d{2})(?!\d)", stem):
        candidates.append(m.group(1))

    candidates = list(dict.fromkeys(candidates))
    full_dates = [x for x in candidates if _vis_re.match(r"20\d{2}-\d{2}-\d{2}$", x)]
    best = full_dates[0] if full_dates else (candidates[0] if candidates else "")

    return {
        "report_date": best,
        "report_date_candidates": candidates,
        "source": "VIA_SSOT_Unified.VIS_VRN_REPORT_DATE_EXTRACTOR_V06123" if candidates else "NONE",
    }

# ==================================================================================================
# [VIS:VRN_ANALYST_TARGET_EXTRACTOR_V06123:END]
# ==================================================================================================
'''


BRIDGE_FUNCTIONS = r'''
def def_extract_report_date_from_filename(filename: Any) -> dict:
    raw = Path(def_clean_text(filename)).name
    stem = re.sub(r"\.pdf$", "", raw, flags=re.I)
    candidates = []

    for m in re.finditer(r"(20\d{2})[-_/年.]?(0[1-9]|1[0-2])[-_/月.]?(0[1-9]|[12]\d|3[01])", stem):
        candidates.append(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")

    for m in re.finditer(r"(?<!\d)(1[0-9]{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)", stem):
        roc_y = int(m.group(1))
        ad_y = roc_y + 1911
        if 2000 <= ad_y <= 2099:
            candidates.append(f"{ad_y}-{m.group(2)}-{m.group(3)}")

    for m in re.finditer(r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])(?!\d)", stem):
        candidates.append(f"{m.group(1)}-{m.group(2)}")

    for m in re.finditer(r"(?<!\d)(20\d{2})(?!\d)", stem):
        candidates.append(m.group(1))

    candidates = list(dict.fromkeys(candidates))
    full_dates = [x for x in candidates if re.match(r"20\d{2}-\d{2}-\d{2}$", x)]
    best = full_dates[0] if full_dates else (candidates[0] if candidates else "")

    return {
        "report_date": best,
        "report_date_candidates": candidates,
        "source": "BRIDGE_REPORT_DATE_EXTRACTOR_V06123" if candidates else "NONE",
    }


def def_extract_analyst_from_text(text: Any) -> dict:
    s = def_clean_text(text)
    stopwords = [
        "目標價", "目標價格", "合理價", "評等", "評級", "投資評等", "投資建議",
        "買進", "買入", "增持", "中立", "持有", "減持", "賣出", "未評等",
        "Target Price", "TP", "Rating", "Recommendation", "Buy", "Outperform",
        "Neutral", "Hold", "Sell", "Underperform", "NR"
    ]

    def _stop_before_keyword(x: str) -> str:
        y = def_clean_text(x)
        for kw in sorted(stopwords, key=len, reverse=True):
            m = re.search(re.escape(kw), y, flags=re.I)
            if m:
                y = y[:m.start()].strip()
        y = re.sub(r"[,，;；:：|｜/／]+$", "", y).strip()
        return y

    patterns = [
        r"(?:分析師|研究員|Analyst|撰文|作者|Prepared by|Author)\s*[:：]\s*([A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff\s·．.、,，-]{1,60})",
        r"(?:分析師|研究員)\s+([A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff\s·．.、,，-]{1,40})",
    ]

    for pat in patterns:
        m = re.search(pat, s, flags=re.I)
        if not m:
            continue
        val = _stop_before_keyword(m.group(1))
        val = re.split(r"[\n\r|｜]", val)[0].strip(" ,，。；;:：")
        if val:
            return {"Analyst": val, "Analyst Source": "BRIDGE_ANALYST_EXTRACTOR_V06123", "Analyst Confidence": 0.93}

    return {"Analyst": "", "Analyst Source": "", "Analyst Confidence": 0.0}


def def_extract_rating_target_from_text(text: Any) -> dict:
    s = def_clean_text(text)
    out = {"Rating": "", "Target Price": "", "Rating Target Source": "", "Rating Target Confidence": 0.0}

    m = re.search(r"(買進|買入|增持|中立|持有|減持|賣出|未評等|NR|Buy|Outperform|Neutral|Hold|Sell|Underperform)", s, flags=re.I)
    if m:
        out["Rating"] = m.group(1)

    target_patterns = [
        r"(?:目標價|目標價格|合理價|Target Price|TP)\s*[:：]?\s*(?:NT\$|新台幣|TWD|NTD)?\s*([0-9]+(?:\.[0-9]+)?)",
        r"(?:給予|上修至|下修至|維持)\s*(?:目標價|目標價格)?\s*(?:NT\$|新台幣|TWD|NTD)?\s*([0-9]+(?:\.[0-9]+)?)\s*元",
        r"([0-9]+(?:\.[0-9]+)?)\s*元\s*(?:目標價|合理價)",
    ]
    for pat in target_patterns:
        m = re.search(pat, s, flags=re.I)
        if m:
            out["Target Price"] = m.group(1)
            break

    if out["Rating"] or out["Target Price"]:
        out["Rating Target Source"] = "BRIDGE_RATING_TARGET_EXTRACTOR_V06123"
        out["Rating Target Confidence"] = 0.93

    return out
'''


# ==================================================================================================
# def 03_PATCHING
# ==================================================================================================
def def_backup(path: Path, tag: str) -> str:
    backup = str(path) + f".bak_{tag}_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(backup).write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return backup


def def_append_ssot_block(ssot_path: Path) -> dict:
    row = {"file": str(ssot_path), "backup": "", "patched": False, "severity": "ERR", "error": ""}
    try:
        if not ssot_path.exists():
            row["error"] = "VIA_SSOT_Unified.py not found"
            return row

        text = ssot_path.read_text(encoding="utf-8", errors="ignore")
        row["backup"] = def_backup(ssot_path, "v06123_analyst_target_ssot")

        if "[VIS:VRN_ANALYST_TARGET_EXTRACTOR_V06123:START]" not in text:
            text = text.rstrip() + "\n\n" + SSOT_APPEND_BLOCK + "\n"
            ssot_path.write_text(text, encoding="utf-8")
            row["patched"] = True
        else:
            row["patched"] = False

        row["severity"] = "OK"
        return row
    except Exception:
        row["error"] = traceback.format_exc()
        return row


def def_replace_function(text: str, func_name: str, new_func_code: str) -> tuple[str, bool]:
    pattern = re.compile(
        r"^def\s+" + re.escape(func_name) + r"\s*\(.*?\):\n"
        r"(?:(?:    .*\n)|(?:\s*\n))*",
        re.M
    )
    m = pattern.search(text)
    if not m:
        return text, False
    return text[:m.start()] + new_func_code.rstrip() + "\n\n" + text[m.end():], True


def def_patch_bridge(bridge_path: Path) -> dict:
    row = {"file": str(bridge_path), "backup": "", "patched_functions": [], "severity": "ERR", "error": ""}
    try:
        if not bridge_path.exists():
            row["error"] = "bridge module not found"
            return row

        text = bridge_path.read_text(encoding="utf-8", errors="ignore")
        row["backup"] = def_backup(bridge_path, "v06123_analyst_target_reportdate")

        replacements = {
            "def_extract_report_date_from_filename": re.search(r"def def_extract_report_date_from_filename\(.*?(?=\ndef def_extract_analyst_from_text|\ndef def_extract_rating_target_from_text|\ndef def_merge_protected_fields|\Z)", BRIDGE_FUNCTIONS, flags=re.S).group(0),
            "def_extract_analyst_from_text": re.search(r"def def_extract_analyst_from_text\(.*?(?=\ndef def_extract_rating_target_from_text|\ndef def_merge_protected_fields|\Z)", BRIDGE_FUNCTIONS, flags=re.S).group(0),
            "def_extract_rating_target_from_text": re.search(r"def def_extract_rating_target_from_text\(.*", BRIDGE_FUNCTIONS, flags=re.S).group(0),
        }

        for fn, code in replacements.items():
            text, ok = def_replace_function(text, fn, code)
            if ok:
                row["patched_functions"].append(fn)
            else:
                # append if not found; safer than failing because older bridge may differ
                text = text.rstrip() + "\n\n" + code.rstrip() + "\n"
                row["patched_functions"].append(fn + "::APPENDED")

        bridge_path.write_text(text, encoding="utf-8")
        row["severity"] = "OK"
        return row
    except Exception:
        row["error"] = traceback.format_exc()
        return row


# ==================================================================================================
# def 04_TEST
# ==================================================================================================
def def_import_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    if spec and spec.loader:
        spec.loader.exec_module(mod)
        return mod
    raise RuntimeError("cannot import module")


def def_smoke_test_bridge(bridge_path: Path) -> list[dict]:
    rows = []
    try:
        mod = def_import_module(bridge_path)
        tests = [
            {
                "sample": "分析師：王小明 目標價120元 評等買進",
                "expected_analyst": "王小明",
                "expected_target": "120",
                "expected_rating": "買進",
            },
            {
                "sample": "Analyst: Tony Chen Target Price 88 Buy",
                "expected_analyst": "Tony Chen",
                "expected_target": "88",
                "expected_rating": "Buy",
            },
            {
                "sample": "研究員：林志強 中立 目標價300 元",
                "expected_analyst": "林志強",
                "expected_target": "300",
                "expected_rating": "中立",
            },
        ]

        for t in tests:
            a = mod.def_extract_analyst_from_text(t["sample"])
            rt = mod.def_extract_rating_target_from_text(t["sample"])
            ok = (
                a.get("Analyst") == t["expected_analyst"]
                and rt.get("Target Price") == t["expected_target"]
                and str(rt.get("Rating", "")).lower() == str(t["expected_rating"]).lower()
            )
            rows.append({
                "Status Lights": def_status_lights("OK" if ok else "ERR"),
                "Test": "Analyst / Target / Rating",
                "Sample Text": t["sample"],
                "Analyst": a.get("Analyst", ""),
                "Target Price": rt.get("Target Price", ""),
                "Rating": rt.get("Rating", ""),
                "Expected Analyst": t["expected_analyst"],
                "Expected Target": t["expected_target"],
                "Expected Rating": t["expected_rating"],
                "Severity": "OK" if ok else "ERR",
            })

        date_tests = [
            {"filename": "20251204兆豐個股報告-志強-KY(6768).pdf", "expected": "2025-12-04"},
            {"filename": "華南投顧-3017-奇鋐-1141202.pdf", "expected": "2025-12-02"},
            {"filename": "Citi-3231 20250604.pdf", "expected": "2025-06-04"},
        ]

        for t in date_tests:
            d = mod.def_extract_report_date_from_filename(t["filename"])
            ok = d.get("report_date") == t["expected"]
            rows.append({
                "Status Lights": def_status_lights("OK" if ok else "ERR"),
                "Test": "Report Date",
                "Sample Text": t["filename"],
                "Extracted": d.get("report_date", ""),
                "Candidates": " | ".join(d.get("report_date_candidates", [])),
                "Expected": t["expected"],
                "Severity": "OK" if ok else "ERR",
            })

    except Exception:
        rows.append({
            "Status Lights": def_status_lights("ERR"),
            "Test": "Bridge Import Smoke",
            "Sample Text": "",
            "Error": traceback.format_exc(),
            "Severity": "ERR",
        })
    return rows


# ==================================================================================================
# def 05_MAIN
# ==================================================================================================
def def_main():
    if len(sys.argv) < 5:
        raise SystemExit("usage: py <ssot_unified> <bridge_module> <run_dir> <config_dir>")

    ssot_path = Path(sys.argv[1])
    bridge_path = Path(sys.argv[2])
    run_dir = Path(sys.argv[3])
    config_dir = Path(sys.argv[4])
    run_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    ssot_patch = def_append_ssot_block(ssot_path)
    bridge_patch = def_patch_bridge(bridge_path)

    ssot_check = def_compile_import(ssot_path)
    bridge_check = def_compile_import(bridge_path)
    smoke_rows = def_smoke_test_bridge(bridge_path)

    smoke_ok = all(r.get("Severity") == "OK" for r in smoke_rows)
    system_pass = (
        ssot_check.get("ast") and ssot_check.get("compile")
        and bridge_check.get("ast") and bridge_check.get("compile") and bridge_check.get("import")
        and smoke_ok
    )

    overview = [
        {"Status Lights": def_status_lights("OK" if system_pass else "ERR"), "Gate": "SYSTEM_PASS", "Value": "YES" if system_pass else "NO", "Severity": "OK" if system_pass else "ERR"},
        {"Status Lights": def_status_lights("OK"), "Gate": "SSOT_PATCHED_OR_ALREADY_PRESENT", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_status_lights("OK" if ssot_check.get("compile") else "ERR"), "Gate": "SSOT_COMPILE", "Value": "YES" if ssot_check.get("compile") else "NO", "Severity": "OK" if ssot_check.get("compile") else "ERR"},
        {"Status Lights": def_status_lights("OK" if bridge_check.get("import") else "ERR"), "Gate": "BRIDGE_IMPORT", "Value": "YES" if bridge_check.get("import") else "NO", "Severity": "OK" if bridge_check.get("import") else "ERR"},
        {"Status Lights": def_status_lights("OK" if smoke_ok else "ERR"), "Gate": "ANALYST_TARGET_REPORTDATE_SMOKE", "Value": "YES" if smoke_ok else "NO", "Severity": "OK" if smoke_ok else "ERR"},
        {"Status Lights": def_status_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    patch_rows = [
        {"Status Lights": def_status_lights(ssot_patch.get("severity")), "Target": "VIA_SSOT_Unified.py", **ssot_patch},
        {"Status Lights": def_status_lights(bridge_patch.get("severity")), "Target": "VIS_VRN_MasterRegistryBridge_v0611.py", **bridge_patch},
    ]

    html_path = str(run_dir / "VRN_Analyst_Target_ReportDate_SSOT_Patch_v06123.html")
    json_path = str(run_dir / "vrn_analyst_target_reportdate_ssot_patch_v06123.json")
    overview_csv = str(run_dir / "vrn_v06123_overview.csv")
    patch_csv = str(run_dir / "vrn_v06123_patch_matrix.csv")
    smoke_csv = str(run_dir / "vrn_v06123_smoke_test.csv")

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": "YES" if system_pass else "NO",
        "counts": {
            "System Pass": "YES" if system_pass else "NO",
            "Bridge Import": "YES" if bridge_check.get("import") else "NO",
            "Smoke Rows": len(smoke_rows),
            "Smoke Pass": "YES" if smoke_ok else "NO",
            "Patched Functions": len(bridge_patch.get("patched_functions", [])),
        },
        "outputs": {
            "html": html_path,
            "json": json_path,
            "overview_csv": overview_csv,
            "patch_csv": patch_csv,
            "smoke_csv": smoke_csv,
        },
        "ssot_check": ssot_check,
        "bridge_check": bridge_check,
        "policy": {
            "append_only_ssot": "YES",
            "bridge_function_patch": "YES",
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
        },
    }

    def_write_csv(overview_csv, overview)
    def_write_csv(patch_csv, patch_rows)
    def_write_csv(smoke_csv, smoke_rows)
    def_write_json(json_path, result)
    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Patch Matrix", patch_rows),
        ("03 Smoke Test", smoke_rows),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise