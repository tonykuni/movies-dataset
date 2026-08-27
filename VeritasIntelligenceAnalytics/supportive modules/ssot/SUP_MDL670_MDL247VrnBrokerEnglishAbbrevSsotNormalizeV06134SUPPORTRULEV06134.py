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
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_BROKER_ENGLISH_ABBREV_SSOT_NORMALIZE_V06134"


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
# def 02_SSOT_BROKER_MAP
# ==================================================================================================
def def_fallback_broker_map() -> dict:
    return {
        # def Taiwan brokers
        "兆豐": "MEGA",
        "兆豐投顧": "MEGA",
        "兆豐證券": "MEGA",
        "華南": "HNCB",
        "華南投顧": "HNCB",
        "華南永昌": "HNCB",
        "國泰": "CATHAY",
        "國泰證期": "CATHAY",
        "國泰證券": "CATHAY",
        "中信": "CTBC",
        "中信投顧": "CTBC",
        "中國信託": "CTBC",
        "CTBC": "CTBC",
        "富邦": "FUBON",
        "富邦投顧": "FUBON",
        "元大": "YUANTA",
        "元大投顧": "YUANTA",
        "凱基": "KGI",
        "凱基投顧": "KGI",
        "統一": "PSC",
        "統一投顧": "PSC",
        "永豐": "SINOPAC",
        "永豐投顧": "SINOPAC",
        "群益": "CLST",
        "群益投顧": "CLST",
        "台新": "TAISHIN",
        "第一金": "FIRST",
        "玉山": "ESUN",
        "康和": "CONCORD",
        "新光": "SKIS",
        "日盛": "JIH SUN",
        "上海商銀": "SCSB",

        # def Global brokers
        "Citi": "CITI",
        "Citigroup": "CITI",
        "CITI": "CITI",
        "GS": "GS",
        "Goldman": "GS",
        "Goldman Sachs": "GS",
        "JP": "JPM",
        "JPM": "JPM",
        "JP Morgan": "JPM",
        "J.P. Morgan": "JPM",
        "JPMorgan": "JPM",
        "MS": "MS",
        "Morgan Stanley": "MS",
        "Daiwa": "DAIWA",
        "DAIWA": "DAIWA",
        "CLST": "CLST",
    }


def def_extract_possible_broker_map_from_ast(ssot_path: Path) -> tuple[dict, list[str]]:
    found = {}
    notes = []

    if not ssot_path.exists():
        return found, ["SSOT_NOT_FOUND"]

    try:
        text = ssot_path.read_text(encoding="utf-8")
    except Exception:
        try:
            text = ssot_path.read_text(encoding="utf-8-sig")
        except Exception as e:
            return found, [f"SSOT_READ_ERROR:{e}"]

    try:
        tree = ast.parse(text)
    except Exception as e:
        return found, [f"SSOT_AST_PARSE_ERROR:{e}"]

    broker_keywords = [
        "broker", "券商", "投顧", "證券", "securities", "research_house",
        "broker_abbrev", "broker_alias", "broker_map"
    ]

    def is_brokerish_name(name: str) -> bool:
        nk = def_norm_key(name)
        return any(def_norm_key(k) in nk for k in broker_keywords)

    def add_pair(k: Any, v: Any, source: str) -> None:
        if not isinstance(k, str):
            return

        # dict value may be string, or dict containing abbrev/code/en
        out = ""
        if isinstance(v, str):
            out = v
        elif isinstance(v, dict):
            for kk in ["abbrev", "abbr", "code", "broker_abbrev", "english_abbrev", "en", "name_en"]:
                if kk in v and isinstance(v.get(kk), str):
                    out = v.get(kk)
                    break

        k2 = def_clean_text(k)
        v2 = def_clean_text(out).upper()

        if k2 and v2 and len(v2) <= 24:
            found[k2] = v2
            notes.append(f"{source}:{k2}->{v2}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [getattr(t, "id", "") for t in node.targets if hasattr(t, "id")]
            target_name = " ".join(targets)

            if not is_brokerish_name(target_name):
                continue

            try:
                val = ast.literal_eval(node.value)
            except Exception:
                continue

            if isinstance(val, dict):
                for k, v in val.items():
                    add_pair(k, v, f"ASSIGN:{target_name}")

            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        keys = list(item.keys())
                        alias = ""
                        abbr = ""

                        for ak in ["alias", "aliases", "name", "name_zh", "raw", "broker", "broker_raw"]:
                            if ak in item:
                                if isinstance(item[ak], list):
                                    alias = item[ak][0] if item[ak] else ""
                                else:
                                    alias = item[ak]
                                break

                        for bk in ["abbrev", "abbr", "code", "broker_abbrev", "english_abbrev", "name_en"]:
                            if bk in item:
                                abbr = item[bk]
                                break

                        if isinstance(alias, str) and isinstance(abbr, str):
                            add_pair(alias, abbr, f"LIST:{target_name}")

                        if isinstance(item.get("aliases"), list) and isinstance(abbr, str):
                            for al in item.get("aliases"):
                                add_pair(al, abbr, f"LIST_ALIASES:{target_name}")

    # extra regex fallback from plain text lines like "兆豐": "MEGA"
    for m in re.finditer(r"""['"]([^'"]{1,30})['"]\s*:\s*['"]([A-Z][A-Z0-9 .&-]{1,24})['"]""", text):
        k, v = m.group(1), m.group(2)
        if any(x in k for x in ["投顧", "證券", "兆豐", "華南", "國泰", "中信", "元大", "凱基", "群益", "富邦", "永豐"]):
            add_pair(k, v, "REGEX_TEXT")

    return found, notes


def def_build_broker_map(ssot_path: Path) -> tuple[dict, list[dict]]:
    fallback = def_fallback_broker_map()
    ssot_map, notes = def_extract_possible_broker_map_from_ast(ssot_path)

    merged = {}
    source_rows = []

    for k, v in fallback.items():
        merged[def_norm_key(k)] = {
            "alias": k,
            "abbrev": v,
            "source": "FALLBACK_SAFE_MAP",
        }

    for k, v in ssot_map.items():
        merged[def_norm_key(k)] = {
            "alias": k,
            "abbrev": v,
            "source": "VIA_SSOT_Unified.py",
        }

    for nk, obj in sorted(merged.items(), key=lambda x: x[0]):
        source_rows.append({
            "Status Lights": def_lights("OK"),
            "Alias": obj["alias"],
            "Broker Abbrev": obj["abbrev"],
            "Source": obj["source"],
            "Severity": "OK",
        })

    return merged, source_rows


def def_normalize_broker(raw: str, filename: str, broker_map: dict) -> tuple[str, str, str]:
    raw0 = def_clean_text(raw)
    filename0 = def_clean_text(filename)

    haystacks = [
        ("BROKER_FIELD", raw0),
        ("FILENAME", filename0),
    ]

    # exact normalized match first
    for source_name, text in haystacks:
        nk = def_norm_key(text)
        if nk in broker_map:
            obj = broker_map[nk]
            return obj["abbrev"], obj["source"], f"{source_name}:exact:{obj['alias']}"

    # contains match, longer aliases first
    candidates = sorted(broker_map.values(), key=lambda x: len(def_norm_key(x["alias"])), reverse=True)

    for source_name, text in haystacks:
        nt = def_norm_key(text)
        for obj in candidates:
            ak = def_norm_key(obj["alias"])
            if ak and ak in nt:
                return obj["abbrev"], obj["source"], f"{source_name}:contains:{obj['alias']}"

    # already English broker code
    upper = raw0.upper().replace(".", "").strip()
    direct_codes = {
        "CITI", "GS", "JPM", "JP", "MS", "DAIWA", "CLST", "CTBC", "MEGA", "HNCB",
        "CATHAY", "YUANTA", "KGI", "FUBON", "SINOPAC", "PSC", "TAISHIN", "FIRST", "ESUN"
    }
    if upper in direct_codes:
        if upper == "JP":
            upper = "JPM"
        return upper, "DIRECT_ENGLISH_CODE", "BROKER_FIELD:direct_code"

    return raw0.upper() if raw0 else "", "UNMAPPED", "NO_MATCH"


# ==================================================================================================
# def 03_HTML
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
<head><meta charset="utf-8"><title>VRN Broker English Abbrev SSOT Normalize v06134</title><style>{css}</style></head>
<body>
<header>
<h1>VRN · Broker English Abbrev SSOT Normalize v0.6.13.4</h1>
<div class="sub">Broker normalized by VIA_SSOT_Unified.py first · English abbreviation only · raw preserved · no canonical mutation</div>
</header>
{card_html}
<main>{body}</main>
<footer>Veritas Intelligence Analytics</footer>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 04_MAIN
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

    source_csv = def_find_latest(run_root, [
        "vrn_v06133_company_master_rule_consolidated.csv",
        "vrn_v06132_company_master_enriched_validated.csv",
        "vrn_v06131_company_report_calibrated_matrix.csv",
    ])

    if not source_csv:
        raise RuntimeError("Cannot find company master CSV from v06133/v06132/v06131")

    rows = def_read_csv(source_csv)
    broker_map, map_rows = def_build_broker_map(ssot_path)

    normalized_rows = []
    review_rows = []

    for row in rows:
        r = dict(row)
        raw_broker = def_first(r, ["Broker"])
        filename = def_first(r, ["Filename"])

        normalized, source, match_reason = def_normalize_broker(raw_broker, filename, broker_map)

        r["Broker Raw"] = raw_broker
        r["Broker"] = normalized
        r["Broker Normalized"] = normalized
        r["Broker Source"] = source
        r["Broker Match Reason"] = match_reason

        if normalized and source != "UNMAPPED":
            r["Broker Normalize Status"] = "OK"
            sev = def_first(r, ["Severity"]) or "OK"
        else:
            r["Broker Normalize Status"] = "REVIEW"
            sev = "WARN"

        r["Severity"] = sev
        r["Status Lights"] = def_lights(sev)

        normalized_rows.append(r)

        if r["Broker Normalize Status"] != "OK":
            review_rows.append(r)

    overview = [
        {"Status Lights": def_lights("OK"), "Gate": "SOURCE_MASTER_CSV", "Value": str(source_csv), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "SSOT_UNIFIED", "Value": str(ssot_path), "Severity": "OK" if ssot_path.exists() else "WARN"},
        {"Status Lights": def_lights("OK"), "Gate": "ROWS", "Value": len(normalized_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "BROKER_MAP_ROWS", "Value": len(map_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "BROKER_NORMALIZED_OK", "Value": sum(1 for r in normalized_rows if r["Broker Normalize Status"] == "OK"), "Severity": "OK"},
        {"Status Lights": def_lights("WARN" if review_rows else "OK"), "Gate": "BROKER_REVIEW_ROWS", "Value": len(review_rows), "Severity": "WARN" if review_rows else "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "BROKER_OUTPUT_POLICY", "Value": "ENGLISH_ABBREV_ONLY", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "BROKER_RAW_PRESERVED", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    html_path = run_dir / "VRN_Broker_English_Abbrev_SSOT_Normalize_v06134.html"
    json_path = run_dir / "vrn_broker_english_abbrev_ssot_normalize_v06134.json"
    overview_csv = run_dir / "vrn_v06134_overview.csv"
    master_csv = run_dir / "vrn_v06134_company_master_broker_english_abbrev.csv"
    review_csv = run_dir / "vrn_v06134_broker_review.csv"
    broker_map_csv = run_dir / "vrn_v06134_broker_map_used.csv"

    manifest_json = config_dir / "VRN_Company_Master_Broker_English_Abbrev_Manifest_v06134.json"
    manifest_csv = config_dir / "VRN_Company_Master_Broker_English_Abbrev_Manifest_v06134.csv"

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_master_csv": str(source_csv),
        "ssot_unified": str(ssot_path),
        "counts": {
            "Rows": len(normalized_rows),
            "Broker OK": sum(1 for r in normalized_rows if r["Broker Normalize Status"] == "OK"),
            "Broker Review": len(review_rows),
            "Broker Map Rows": len(map_rows),
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "overview_csv": str(overview_csv),
            "master_csv": str(master_csv),
            "review_csv": str(review_csv),
            "broker_map_csv": str(broker_map_csv),
            "manifest_json": str(manifest_json),
            "manifest_csv": str(manifest_csv),
        },
        "policy": {
            "broker_output": "ENGLISH_ABBREV_ONLY",
            "ssot_priority": "VIA_SSOT_Unified.py first",
            "fallback": "safe broker map only when SSOT map missing",
            "broker_raw_preserved": "YES",
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
            "no_fake_fill": "YES",
        },
    }

    def_write_csv(overview_csv, overview)
    def_write_csv(master_csv, normalized_rows)
    def_write_csv(review_csv, review_rows)
    def_write_csv(broker_map_csv, map_rows)
    def_write_csv(manifest_csv, normalized_rows)
    def_write_json(manifest_json, {"version": VERSION, "generated_at": result["generated_at"], "company_master": normalized_rows})
    def_write_json(json_path, result)

    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Company Master Broker English Abbrev", normalized_rows),
        ("03 Broker Review", review_rows),
        ("04 Broker Map Used", map_rows),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise