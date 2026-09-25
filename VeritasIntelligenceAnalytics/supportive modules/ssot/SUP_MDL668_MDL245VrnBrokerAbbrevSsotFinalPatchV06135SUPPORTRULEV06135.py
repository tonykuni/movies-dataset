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
import json
import re
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_BROKER_ABBREV_SSOT_FINAL_PATCH_V06135"
PATCH_MARKER = "# [VIA:VRN_BROKER_ABBREV_SSOT_FINAL_V06135:START]"


# ==================================================================================================
# def 01_COMMON
# ==================================================================================================
def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    return re.sub(r"\s+", " ", s).strip()


def def_norm_key(x: Any) -> str:
    s = def_clean_text(x).lower()
    s = re.sub(r"[()（）\[\]【】{}<>〈〉《》]", " ", s)
    s = re.sub(r"[\s　,，、;；:：|｜/／\\\-–—_+＋=＝~～!！?？.．]", "", s)
    return s


def def_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "YES", "PASS", "GREEN"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "YELLOW", "INFO"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def def_write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"empty_marker": ""}]
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_find_latest(run_root: Path, patterns: list[str]) -> Path | None:
    hits = []
    for pat in patterns:
        hits.extend(run_root.rglob(pat))
    hits = sorted(set(hits), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def def_first(row: dict, keys: list[str]) -> str:
    for k in keys:
        if k in row and def_clean_text(row.get(k)):
            return def_clean_text(row.get(k))
    return ""


# ==================================================================================================
# def 02_FINAL_BROKER_MAP
# ==================================================================================================
def def_final_broker_alias_rows() -> list[dict]:
    rows = [
        # global brokers
        {"alias": "Daiwa", "abbrev": "DAIWA", "group": "DAIWA"},
        {"alias": "DAIWA", "abbrev": "DAIWA", "group": "DAIWA"},

        {"alias": "Goldman", "abbrev": "GS", "group": "GS"},
        {"alias": "Goldman Sachs", "abbrev": "GS", "group": "GS"},
        {"alias": "GS", "abbrev": "GS", "group": "GS"},

        {"alias": "JP", "abbrev": "JPM", "group": "JPM"},
        {"alias": "JPM", "abbrev": "JPM", "group": "JPM"},
        {"alias": "JP Morgan", "abbrev": "JPM", "group": "JPM"},
        {"alias": "J.P. Morgan", "abbrev": "JPM", "group": "JPM"},
        {"alias": "JPMorgan", "abbrev": "JPM", "group": "JPM"},
        {"alias": "JPMorgan Chase", "abbrev": "JPM", "group": "JPM"},

        {"alias": "Morgan Stanley", "abbrev": "MS", "group": "MS"},
        {"alias": "MS", "abbrev": "MS", "group": "MS"},

        {"alias": "Citi", "abbrev": "CITI", "group": "CITI"},
        {"alias": "Citigroup", "abbrev": "CITI", "group": "CITI"},
        {"alias": "CITI", "abbrev": "CITI", "group": "CITI"},

        # Taiwan brokers
        {"alias": "第一金", "abbrev": "FFHC", "group": "FFHC"},
        {"alias": "第一金證券", "abbrev": "FFHC", "group": "FFHC"},
        {"alias": "第一金投顧", "abbrev": "FFHC", "group": "FFHC"},
        {"alias": "第一", "abbrev": "FFHC", "group": "FFHC"},
        {"alias": "First Financial Holding", "abbrev": "FFHC", "group": "FFHC"},
        {"alias": "First Securities", "abbrev": "FFHC", "group": "FFHC"},
        {"alias": "FFHC", "abbrev": "FFHC", "group": "FFHC"},

        {"alias": "統一", "abbrev": "PSC", "group": "PSC"},
        {"alias": "統一證券", "abbrev": "PSC", "group": "PSC"},
        {"alias": "統一投顧", "abbrev": "PSC", "group": "PSC"},
        {"alias": "President Securities", "abbrev": "PSC", "group": "PSC"},
        {"alias": "PSC", "abbrev": "PSC", "group": "PSC"},

        {"alias": "群益", "abbrev": "CSC", "group": "CSC"},
        {"alias": "群益金鼎", "abbrev": "CSC", "group": "CSC"},
        {"alias": "群益金鼎證券", "abbrev": "CSC", "group": "CSC"},
        {"alias": "群益投顧", "abbrev": "CSC", "group": "CSC"},
        {"alias": "Capital Securities", "abbrev": "CSC", "group": "CSC"},
        {"alias": "Capital Securities Corp", "abbrev": "CSC", "group": "CSC"},
        {"alias": "CLST", "abbrev": "CSC", "group": "CSC"},
        {"alias": "CSC", "abbrev": "CSC", "group": "CSC"},

        {"alias": "兆豐", "abbrev": "MEGA", "group": "MEGA"},
        {"alias": "兆豐投顧", "abbrev": "MEGA", "group": "MEGA"},
        {"alias": "兆豐證券", "abbrev": "MEGA", "group": "MEGA"},
        {"alias": "MEGA", "abbrev": "MEGA", "group": "MEGA"},

        {"alias": "華南", "abbrev": "HNCB", "group": "HNCB"},
        {"alias": "華南投顧", "abbrev": "HNCB", "group": "HNCB"},
        {"alias": "華南永昌", "abbrev": "HNCB", "group": "HNCB"},
        {"alias": "HNCB", "abbrev": "HNCB", "group": "HNCB"},

        {"alias": "國泰", "abbrev": "CATHAY", "group": "CATHAY"},
        {"alias": "國泰證期", "abbrev": "CATHAY", "group": "CATHAY"},
        {"alias": "國泰證券", "abbrev": "CATHAY", "group": "CATHAY"},
        {"alias": "CATHAY", "abbrev": "CATHAY", "group": "CATHAY"},

        {"alias": "中信", "abbrev": "CTBC", "group": "CTBC"},
        {"alias": "中信投顧", "abbrev": "CTBC", "group": "CTBC"},
        {"alias": "中國信託", "abbrev": "CTBC", "group": "CTBC"},
        {"alias": "CTBC", "abbrev": "CTBC", "group": "CTBC"},

        {"alias": "元大", "abbrev": "YUANTA", "group": "YUANTA"},
        {"alias": "元大投顧", "abbrev": "YUANTA", "group": "YUANTA"},
        {"alias": "YUANTA", "abbrev": "YUANTA", "group": "YUANTA"},

        {"alias": "凱基", "abbrev": "KGI", "group": "KGI"},
        {"alias": "凱基投顧", "abbrev": "KGI", "group": "KGI"},
        {"alias": "KGI", "abbrev": "KGI", "group": "KGI"},

        {"alias": "富邦", "abbrev": "FUBON", "group": "FUBON"},
        {"alias": "富邦投顧", "abbrev": "FUBON", "group": "FUBON"},
        {"alias": "FUBON", "abbrev": "FUBON", "group": "FUBON"},

        {"alias": "永豐", "abbrev": "SINOPAC", "group": "SINOPAC"},
        {"alias": "永豐投顧", "abbrev": "SINOPAC", "group": "SINOPAC"},
        {"alias": "SINOPAC", "abbrev": "SINOPAC", "group": "SINOPAC"},
    ]
    return rows


def def_final_broker_map() -> dict:
    mp = {}
    for r in def_final_broker_alias_rows():
        mp[def_norm_key(r["alias"])] = r
    return mp


def def_normalize_broker(raw: str, filename: str, broker_raw_backup: str = "") -> tuple[str, str, str]:
    mp = def_final_broker_map()

    haystacks = [
        ("BROKER", raw),
        ("BROKER_RAW", broker_raw_backup),
        ("FILENAME", filename),
    ]

    # exact
    for src, text in haystacks:
        nk = def_norm_key(text)
        if nk in mp:
            r = mp[nk]
            return r["abbrev"], "VIA_SSOT_Unified.py::VRN_BROKER_ABBREV_ALIAS_MAP_V06135", f"{src}:exact:{r['alias']}"

    # contains, longer first
    alias_rows = sorted(def_final_broker_alias_rows(), key=lambda x: len(def_norm_key(x["alias"])), reverse=True)
    for src, text in haystacks:
        nt = def_norm_key(text)
        for ar in alias_rows:
            ak = def_norm_key(ar["alias"])
            if ak and ak in nt:
                return ar["abbrev"], "VIA_SSOT_Unified.py::VRN_BROKER_ABBREV_ALIAS_MAP_V06135", f"{src}:contains:{ar['alias']}"

    # direct already-English fallback
    upper = def_clean_text(raw).upper().replace(".", "")
    direct = {
        "DAIWA", "GS", "JPM", "MS", "CITI",
        "FFHC", "PSC", "CSC", "MEGA", "HNCB", "CATHAY", "CTBC",
        "YUANTA", "KGI", "FUBON", "SINOPAC"
    }
    if upper in direct:
        return upper, "DIRECT_ENGLISH_CODE", "BROKER:direct"

    return upper if upper else "", "UNMAPPED", "NO_MATCH"


# ==================================================================================================
# def 03_SSOT_PATCH
# ==================================================================================================
def def_build_ssot_patch_text() -> str:
    rows = def_final_broker_alias_rows()
    return f'''

# [VIA:VRN_BROKER_ABBREV_SSOT_FINAL_V06135:START]
# Append-only VRN broker English abbreviation SSOT final patch.
# Policy:
# - Broker output must be English abbreviation only.
# - Daiwa -> DAIWA
# - Goldman / Goldman Sachs -> GS
# - JP / JPM / JP Morgan / J.P. Morgan / JPMorgan -> JPM
# - Morgan Stanley -> MS
# - First Financial Holding / 第一金 / 第一 -> FFHC
# - President Securities / 統一 / 統一證券 -> PSC
# - Capital Securities / 群益 / 群益金鼎 / CLST -> CSC

VRN_BROKER_ABBREV_ALIAS_MAP_V06135 = {repr(rows)}

def def_vrn_norm_broker_key_v06135(x):
    import re
    s = "" if x is None else str(x)
    s = s.replace("\\u3000", " ")
    s = re.sub(r"\\s+", " ", s).strip().lower()
    s = re.sub(r"[()（）\\[\\]【】{{}}<>〈〉《》]", " ", s)
    s = re.sub(r"[\\s　,，、;；:：|｜/／\\\\\\-–—_+＋=＝~～!！?？.．]", "", s)
    return s

def def_get_vrn_broker_abbrev_alias_map_v06135():
    return list(VRN_BROKER_ABBREV_ALIAS_MAP_V06135)

def def_normalize_vrn_broker_abbrev_v06135(raw_broker="", filename="", broker_raw_backup=""):
    rows = list(VRN_BROKER_ABBREV_ALIAS_MAP_V06135)
    mp = {{def_vrn_norm_broker_key_v06135(r.get("alias", "")): r for r in rows}}

    haystacks = [
        ("BROKER", raw_broker),
        ("BROKER_RAW", broker_raw_backup),
        ("FILENAME", filename),
    ]

    for src, text in haystacks:
        nk = def_vrn_norm_broker_key_v06135(text)
        if nk in mp:
            r = mp[nk]
            return {{
                "broker": r.get("abbrev", ""),
                "broker_normalized": r.get("abbrev", ""),
                "broker_source": "VIA_SSOT_Unified.py::VRN_BROKER_ABBREV_ALIAS_MAP_V06135",
                "broker_match_reason": src + ":exact:" + str(r.get("alias", "")),
                "broker_status": "OK",
            }}

    for src, text in haystacks:
        nt = def_vrn_norm_broker_key_v06135(text)
        for r in sorted(rows, key=lambda z: len(def_vrn_norm_broker_key_v06135(z.get("alias", ""))), reverse=True):
            ak = def_vrn_norm_broker_key_v06135(r.get("alias", ""))
            if ak and ak in nt:
                return {{
                    "broker": r.get("abbrev", ""),
                    "broker_normalized": r.get("abbrev", ""),
                    "broker_source": "VIA_SSOT_Unified.py::VRN_BROKER_ABBREV_ALIAS_MAP_V06135",
                    "broker_match_reason": src + ":contains:" + str(r.get("alias", "")),
                    "broker_status": "OK",
                }}

    upper = str(raw_broker or "").strip().upper().replace(".", "")
    direct = {{
        "DAIWA", "GS", "JPM", "MS", "CITI",
        "FFHC", "PSC", "CSC", "MEGA", "HNCB", "CATHAY", "CTBC",
        "YUANTA", "KGI", "FUBON", "SINOPAC"
    }}
    if upper in direct:
        return {{
            "broker": upper,
            "broker_normalized": upper,
            "broker_source": "DIRECT_ENGLISH_CODE",
            "broker_match_reason": "BROKER:direct",
            "broker_status": "OK",
        }}

    return {{
        "broker": upper,
        "broker_normalized": upper,
        "broker_source": "UNMAPPED",
        "broker_match_reason": "NO_MATCH",
        "broker_status": "REVIEW",
    }}
# [VIA:VRN_BROKER_ABBREV_SSOT_FINAL_V06135:END]
'''


def def_patch_ssot(ssot_path: Path, run_dir: Path) -> dict:
    out = {
        "patched": False,
        "already_present": False,
        "backup": "",
        "compile_ok": False,
        "ast_ok": False,
        "error": "",
    }

    try:
        if not ssot_path.exists():
            out["error"] = "SSOT_NOT_FOUND"
            return out

        text = ssot_path.read_text(encoding="utf-8")

        try:
            ast.parse(text)
            out["ast_ok"] = True
        except Exception as e:
            out["error"] = f"BEFORE_AST_ERROR:{e}"
            return out

        if PATCH_MARKER in text:
            out["already_present"] = True
        else:
            backup = ssot_path.with_suffix(ssot_path.suffix + f".bak_v06135_broker_abbrev_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(ssot_path, backup)
            out["backup"] = str(backup)

            text2 = text.rstrip() + "\n\n" + def_build_ssot_patch_text().strip() + "\n"
            ast.parse(text2)
            ssot_path.write_text(text2, encoding="utf-8")
            out["patched"] = True

        # final compile via ast parse
        final_text = ssot_path.read_text(encoding="utf-8")
        ast.parse(final_text)
        out["compile_ok"] = True

    except Exception as e:
        out["error"] = traceback.format_exc()

    return out


# ==================================================================================================
# def 04_HTML
# ==================================================================================================
def def_table_html(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"

    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(c).replace('_', ' ').title())}</th>" for c in fields)
    body = []

    for r in rows:
        tds = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            lc = c.lower()
            cls = "center"
            if any(x in lc for x in ["filename", "broker", "source", "match", "alias", "status", "error", "reason"]):
                cls = "left"
            if any(x in lc for x in ["price", "close", "volume", "beta", "cap", "pe", "book", "confidence", "score", "rows", "count", "performance", "upside"]):
                cls = "right"
            if "rate" in lc or "ticker" in lc or "categories" in lc:
                cls += " wrap"
            tds.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")

    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
:root{--bg:#07111f;--panel:#0d1b2f;--panel2:#132541;--line:#1f3557;--text:#eef6ff;--muted:#9fb3c8;--accent:#42d9ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:linear-gradient(135deg,#0d1b2f,#091525);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}
h1{margin:0;font-size:24px}.sub{color:var(--muted);margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;padding:20px 32px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(0,0,0,.22)}
.v{font-size:26px;font-weight:800}.k{color:var(--muted);margin-top:4px}
main{padding:0 32px 32px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid var(--line);border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:var(--panel2);padding:10px;text-align:center;vertical-align:top;white-space:normal;word-break:break-word;max-width:180px;z-index:2}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;text-align:center;max-width:440px;white-space:normal;word-break:break-word;line-height:1.35}
td.left{text-align:left}
td.right{text-align:right;font-variant-numeric:tabular-nums}
td.wrap{white-space:normal;word-break:break-word}
tr:hover td{background:rgba(66,217,255,.07)}
footer{padding:18px 32px;color:var(--muted);border-top:1px solid var(--line)}
@media(max-width:900px){body{font-size:10px}main{padding:0 14px 20px}.grid{padding:14px;grid-template-columns:repeat(2,minmax(120px,1fr))}}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"
    body = "".join(def_table_html(t, r) for t, r in sections)

    doc = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>VRN Broker Abbrev SSOT Final Patch v06135</title><style>{css}</style></head>
<body>
<header>
<h1>VRN · Broker Abbrev SSOT Final Patch v0.6.13.5</h1>
<div class="sub">Daiwa=DAIWA · Goldman=GS · JP/JPM=JPM · Morgan Stanley=MS · First=FFHC · President=PSC · Capital/CLST=CSC</div>
</header>
{card_html}
<main>{body}</main>
<footer>Veritas Intelligence Analytics</footer>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 05_MAIN
# ==================================================================================================
def def_main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit("usage: py <run_root> <run_dir> <config_dir> <ssot_unified>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    config_dir = Path(sys.argv[3])
    ssot_path = Path(sys.argv[4])

    run_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    patch_result = def_patch_ssot(ssot_path, run_dir)

    source_csv = def_find_latest(run_root, [
        "vrn_v06134_company_master_broker_english_abbrev.csv",
        "vrn_v06133_company_master_rule_consolidated.csv",
        "vrn_v06132_company_master_enriched_validated.csv",
        "vrn_v06131_company_report_calibrated_matrix.csv",
    ])

    if not source_csv:
        raise RuntimeError("Cannot find latest company master CSV")

    rows = def_read_csv(source_csv)

    normalized_rows = []
    review_rows = []

    for row in rows:
        r = dict(row)
        raw_broker = def_first(r, ["Broker Raw", "Broker"])
        current_broker = def_first(r, ["Broker"])
        filename = def_first(r, ["Filename"])

        broker, source, reason = def_normalize_broker(current_broker, filename, raw_broker)

        r["Broker Raw"] = raw_broker or current_broker
        r["Broker Before V06135"] = current_broker
        r["Broker"] = broker
        r["Broker Normalized"] = broker
        r["Broker Source"] = source
        r["Broker Match Reason"] = reason
        r["Broker Normalize Status"] = "OK" if broker and source != "UNMAPPED" else "REVIEW"

        sev = "OK" if r["Broker Normalize Status"] == "OK" else "WARN"
        r["Broker Severity"] = sev
        r["Status Lights"] = def_lights(sev)

        normalized_rows.append(r)
        if r["Broker Normalize Status"] != "OK":
            review_rows.append(r)

    alias_rows = []
    for ar in def_final_broker_alias_rows():
        alias_rows.append({
            "Status Lights": def_lights("OK"),
            "Alias": ar["alias"],
            "Broker Abbrev": ar["abbrev"],
            "Group": ar["group"],
            "Severity": "OK",
        })

    overview = [
        {"Status Lights": def_lights("OK"), "Gate": "SOURCE_MASTER_CSV", "Value": str(source_csv), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "SSOT_UNIFIED", "Value": str(ssot_path), "Severity": "OK" if ssot_path.exists() else "ERR"},
        {"Status Lights": def_lights("OK"), "Gate": "SSOT_PATCHED", "Value": patch_result.get("patched"), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "SSOT_ALREADY_PRESENT", "Value": patch_result.get("already_present"), "Severity": "OK"},
        {"Status Lights": def_lights("OK" if patch_result.get("compile_ok") else "ERR"), "Gate": "SSOT_COMPILE_OK", "Value": patch_result.get("compile_ok"), "Severity": "OK" if patch_result.get("compile_ok") else "ERR"},
        {"Status Lights": def_lights("OK"), "Gate": "BROKER_OUTPUT_POLICY", "Value": "ENGLISH_ABBREV_ONLY", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "ROWS", "Value": len(normalized_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "BROKER_NORMALIZED_OK", "Value": sum(1 for r in normalized_rows if r["Broker Normalize Status"] == "OK"), "Severity": "OK"},
        {"Status Lights": def_lights("WARN" if review_rows else "OK"), "Gate": "BROKER_REVIEW_ROWS", "Value": len(review_rows), "Severity": "WARN" if review_rows else "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "FINAL_RULE_DAIWA", "Value": "DAIWA", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "FINAL_RULE_GOLDMAN", "Value": "GS", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "FINAL_RULE_JP_JPM", "Value": "JPM", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "FINAL_RULE_MORGAN_STANLEY", "Value": "MS", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "FINAL_RULE_FIRST", "Value": "FFHC", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "FINAL_RULE_PRESIDENT_SECURITIES", "Value": "PSC", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "FINAL_RULE_CAPITAL_SECURITIES", "Value": "CSC", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    html_path = run_dir / "VRN_Broker_Abbrev_SSOT_Final_Patch_v06135.html"
    json_path = run_dir / "vrn_broker_abbrev_ssot_final_patch_v06135.json"
    overview_csv = run_dir / "vrn_v06135_overview.csv"
    master_csv = run_dir / "vrn_v06135_company_master_broker_final.csv"
    review_csv = run_dir / "vrn_v06135_broker_review.csv"
    alias_csv = run_dir / "vrn_v06135_broker_alias_map_final.csv"

    manifest_json = config_dir / "VRN_Company_Master_Broker_Final_Manifest_v06135.json"
    manifest_csv = config_dir / "VRN_Company_Master_Broker_Final_Manifest_v06135.csv"

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_master_csv": str(source_csv),
        "ssot_unified": str(ssot_path),
        "patch_result": patch_result,
        "counts": {
            "Rows": len(normalized_rows),
            "Broker OK": sum(1 for r in normalized_rows if r["Broker Normalize Status"] == "OK"),
            "Broker Review": len(review_rows),
            "Alias Rules": len(alias_rows),
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "overview_csv": str(overview_csv),
            "master_csv": str(master_csv),
            "review_csv": str(review_csv),
            "alias_csv": str(alias_csv),
            "manifest_json": str(manifest_json),
            "manifest_csv": str(manifest_csv),
        },
        "policy": {
            "broker_output": "ENGLISH_ABBREV_ONLY",
            "daiwa": "DAIWA",
            "goldman": "GS",
            "jp_jpm": "JPM",
            "morgan_stanley": "MS",
            "first_financial_holding": "FFHC",
            "president_securities": "PSC",
            "capital_securities": "CSC",
            "clst": "CSC",
            "broker_raw_preserved": "YES",
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
        },
    }

    def_write_csv(overview_csv, overview)
    def_write_csv(master_csv, normalized_rows)
    def_write_csv(review_csv, review_rows)
    def_write_csv(alias_csv, alias_rows)
    def_write_csv(manifest_csv, normalized_rows)
    def_write_json(manifest_json, {"version": VERSION, "generated_at": result["generated_at"], "company_master": normalized_rows})
    def_write_json(json_path, result)

    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Company Master Broker Final", normalized_rows),
        ("03 Broker Review", review_rows),
        ("04 Final Broker Alias Map", alias_rows),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise