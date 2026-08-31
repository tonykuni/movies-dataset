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

import csv
import html
import json
import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_VALUATION_METHOD_PRECISION_REBIND_V0593"


# ==================================================================================================
# def 01_CONFIG
# ==================================================================================================
def def_config() -> dict:
    via_root = Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics")
    vrn_root = via_root / "module" / "VRN"
    run_root = vrn_root / "_vrn_operation_ui_runs"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = run_root / f"VRN_VALUATION_METHOD_PRECISION_REBIND_V0593_INNER_{ts}"

    return {
        "via_root": via_root,
        "vrn_root": vrn_root,
        "run_root": run_root,
        "canonical_dir": vrn_root / "_vrn_canonical_active",
        "stable_root": vrn_root / "_vrn_stable_release",
        "integrated_root": vrn_root / "_vrn_integrated_trust_runs",
        "supportive_dir": via_root / "module" / "supportive_module",
        "run_dir": run_dir,
        "out_html": run_dir / "VRN_Valuation_Method_Precision_Rebind_v0593.html",
        "out_json": run_dir / "vrn_valuation_method_precision_rebind_v0593.json",
        "out_basic_csv": run_dir / "vrn_basicinfo_valuation_precision_rebind_v0593.csv",
        "out_audit_csv": run_dir / "vrn_valuation_method_precision_audit_v0593.csv",
        "out_source_csv": run_dir / "vrn_valuation_source_matrix_v0593.csv",
        "out_miss_csv": run_dir / "vrn_valuation_missing_review_v0593.csv",
    }


# ==================================================================================================
# def 02_UTILS
# ==================================================================================================
def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_h(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def def_nonblank(x: Any) -> bool:
    return str(x or "").strip() not in ["", "nan", "None", "null", "undefined"]


def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


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
    cols = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_first(row: dict, keys: list[str]) -> str:
    for k in keys:
        if def_nonblank(row.get(k, "")):
            return str(row.get(k)).strip()
    return ""


def def_safe_json_loads(x: Any) -> dict:
    if not def_nonblank(x):
        return {}
    try:
        obj = json.loads(str(x))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def def_norm_filename(x: Any) -> str:
    s = str(x or "").strip()
    s = s.replace("\\", "/")
    return s.split("/")[-1].lower()


def def_norm_ticker(x: Any) -> str:
    return re.sub(r"\D", "", str(x or ""))[:4]


def def_window(text: str, start: int, end: int, radius: int = 300) -> str:
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    return def_clean_text(text[a:b])


def def_find_latest_files(root: Path, patterns: list[str], max_files: int = 60) -> list[Path]:
    hits = []
    for pat in patterns:
        try:
            hits.extend(root.rglob(pat))
        except Exception:
            pass
    hits = [p for p in hits if p.exists() and p.is_file()]
    hits = sorted(set(hits), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[:max_files]


# ==================================================================================================
# def 03_LEXICON_AND_HARD_GATES
# ==================================================================================================
def def_valuation_patterns() -> dict:
    return {
        "PER": [
            r"(?i)\bP\s*/?\s*E\b",
            r"(?i)\bPER\b",
            r"(?i)\bPE\s*ratio\b",
            r"(?i)\bprice[- ]?to[- ]?earnings\b",
            r"(?i)\bearnings\s+multiple\b",
            r"(?i)\b\d+(\.\d+)?\s*x\s*(P\s*/?\s*E|PE|PER)\b",
            r"(?i)(P\s*/?\s*E|PE|PER)\s*(of|multiple|ratio)?\s*\d+(\.\d+)?\s*x",
            r"本益比",
            r"\d+(\.\d+)?\s*倍\s*本益比",
            r"\d+(\.\d+)?\s*x\s*本益比",
            r"以.{0,70}?\d+(\.\d+)?\s*[xX倍]?.{0,24}本益比.{0,55}?評價",
            r"基於.{0,70}?\d+(\.\d+)?\s*[xX倍]?.{0,24}(PER|PE|P/E|本益比)",
            r"評價區間.{0,70}\d+(\.\d+)?\s*[xX倍]\s*[-~–至]\s*\d+(\.\d+)?\s*[xX倍]?.{0,55}(PER|PE|P/E|本益比)",
            r"常態本益比.{0,50}\d+(\.\d+)?\s*[-~–至]\s*\d+(\.\d+)?\s*倍",
            r"給[予與].{0,45}\d+(\.\d+)?\s*倍",
            r"目標價.{0,100}(PER|PE|P/E|本益比)",
        ],
        "PBR": [
            r"(?i)\bP\s*/\s*B\b",
            r"(?i)\bPBR\b",
            r"(?i)\bPBV\b",
            r"(?i)\bprice[- ]?to[- ]?book\b",
            r"(?i)\bbook\s+value\s+multiple\b",
            r"股價淨值比|市淨率|淨值比|帳面價值倍數|每股淨值",
            r"\d+(\.\d+)?\s*x\s*(P\s*/\s*B|PBR|PBV)",
        ],
        "EV/EBITDA": [
            r"(?i)\bEV\s*/?\s*EBITDA\b",
            r"(?i)\bEV[- ]?to[- ]?EBITDA\b",
            r"(?i)\benterprise\s+value\s+to\s+EBITDA\b",
            r"(?i)\bEBITDA\s+multiple\b",
            r"企業價值.{0,16}EBITDA|EBITDA倍數",
        ],
        "EV/EBIT": [
            r"(?i)\bEV\s*/?\s*EBIT\b",
            r"(?i)\bEV[- ]?to[- ]?EBIT\b",
            r"(?i)\benterprise\s+value\s+to\s+EBIT\b",
            r"(?i)\bEBIT\s+multiple\b",
            r"企業價值.{0,16}EBIT|EBIT倍數",
        ],
        "DCF": [
            r"(?i)\bDCF\b",
            r"(?i)\bdiscounted\s+cash\s*flow\b",
            r"(?i)\bWACC\b",
            r"(?i)\bterminal\s+value\b",
            r"折現現金流|現金流折現|自由現金流折現|加權平均資金成本|終值|永續成長率",
        ],
        "SOTP": [
            r"(?i)\bSOTP\b",
            r"(?i)\bsum[- ]of[- ]the[- ]parts\b",
            r"(?i)\bsum\s+of\s+parts\b",
            r"(?i)\bsegment\s+valuation\b",
            r"分部估值|分部評價|分項加總|分部加總|各業務加總|事業群加總|分拆估值",
        ],
        "DDM": [
            r"(?i)\bDDM\b",
            r"(?i)\bdividend\s+discount\b",
            r"(?i)\bdividend\s+yield\b",
            r"股利折現|股利折現模型|殖利率評價|現金股利殖利率|股息折現",
        ],
        "PEG": [
            r"(?i)\bPEG\b",
            r"(?i)\bprice\s+earnings\s+growth\b",
            r"本益成長比|PEG評價",
        ],
        "P/S": [
            r"(?i)\bP\s*/\s*S\b",
            r"(?i)\bprice[- ]?to[- ]?sales\b",
            r"(?i)\bsales\s+multiple\b",
            r"營收倍數|市銷率|股價營收比",
        ],
        "NAV/RNAV": [
            r"(?i)\bRNAV\b",
            r"(?i)\bNAV\b",
            r"(?i)\bnet\s+asset\s+value\b",
            r"資產淨值|重估資產淨值|淨資產價值|資產價值法",
        ],
    }


def def_method_hard_gate(method: str, evidence: str) -> bool:
    e = evidence or ""

    gates = {
        "PER": r"(?i)(\bP\s*/?\s*E\b|\bPER\b|\bPE\s*ratio\b|price[- ]?to[- ]?earnings|earnings\s+multiple|本益比)",
        "PBR": r"(?i)(\bP\s*/\s*B\b|\bPBR\b|\bPBV\b|price[- ]?to[- ]?book|book\s+value|股價淨值比|市淨率|淨值比|帳面價值|每股淨值)",
        "EV/EBITDA": r"(?i)(EV\s*/?\s*EBITDA|EV[- ]?to[- ]?EBITDA|EBITDA\s+multiple|企業價值.{0,20}EBITDA|EBITDA倍數)",
        "EV/EBIT": r"(?i)(EV\s*/?\s*EBIT|EV[- ]?to[- ]?EBIT|EBIT\s+multiple|企業價值.{0,20}EBIT|EBIT倍數)",
        "DCF": r"(?i)(\bDCF\b|discounted\s+cash\s*flow|WACC|terminal\s+value|折現現金流|現金流折現|終值)",
        "SOTP": r"(?i)(\bSOTP\b|sum[- ]of[- ]the[- ]parts|sum\s+of\s+parts|segment\s+valuation|分部估值|分項加總)",
        "DDM": r"(?i)(\bDDM\b|dividend\s+discount|dividend\s+yield|股利折現|殖利率評價)",
        "PEG": r"(?i)(\bPEG\b|price\s+earnings\s+growth|本益成長比)",
        "P/S": r"(?i)(\bP\s*/\s*S\b|price[- ]?to[- ]?sales|sales\s+multiple|市銷率|營收倍數|股價營收比)",
        "NAV/RNAV": r"(?i)(\bRNAV\b|\bNAV\b|net\s+asset\s+value|資產淨值|重估資產淨值|淨資產價值)",
    }

    pat = gates.get(method)
    if not pat:
        return True
    return bool(re.search(pat, e))


# ==================================================================================================
# def 04_SOURCE_COLLECTION
# ==================================================================================================
def def_source_files(cfg: dict) -> list[Path]:
    files = []

    exact = [
        cfg["canonical_dir"] / "vrn_basicinfo_active.csv",
        cfg["canonical_dir"] / "vrn_financial_active.csv",
    ]

    for p in exact:
        if p.exists():
            files.append(p)

    patterns = [
        "vrn_basicinfo_yfinance_field_fixed_preview_v0589.csv",
        "vrn_basicinfo_yfinance_input_ticker_v0588.csv",
        "vrn_basicinfo_*v059*.csv",
        "vrn_basicinfo_*v057*.csv",
        "vrn_basicinfo_*v056*.csv",
        "vrn_source_text_sentence_units*.csv",
        "vrn_*sentence*.csv",
        "vrn_*source_text*.csv",
    ]

    for root in [cfg["run_root"], cfg["integrated_root"], cfg["stable_root"]]:
        files.extend(def_find_latest_files(root, patterns, max_files=80))

    seen = set()
    out = []
    for p in files:
        key = str(p).lower()
        if key not in seen and p.exists():
            seen.add(key)
            out.append(p)

    return out[:120]


def def_row_key(row: dict) -> tuple[str, str]:
    filename = def_norm_filename(def_first(row, ["Filename", "File", "Source File", "source_file"]))
    ticker = def_norm_ticker(def_first(row, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker", "ticker"]))
    return filename, ticker


def def_build_source_bank(files: list[Path]) -> tuple[dict, list[dict]]:
    bank: dict[tuple[str, str], list[tuple[str, dict]]] = {}
    source_matrix = []

    for p in files:
        rows = def_read_csv(p)
        source_matrix.append({
            "Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST" if rows else "🟢 INPUT  🟡 DB  🟡 TRUST",
            "Source File": str(p),
            "Rows": len(rows),
            "Severity": "OK" if rows else "WARN",
        })

        for r in rows:
            key = def_row_key(r)
            if key == ("", ""):
                continue
            bank.setdefault(key, []).append((str(p), r))

            fn, tk = key
            if tk:
                bank.setdefault(("", tk), []).append((str(p), r))
            if fn:
                bank.setdefault((fn, ""), []).append((str(p), r))

    return bank, source_matrix


def def_base_rows(cfg: dict) -> tuple[list[dict], Path, str]:
    latest = def_find_latest_files(cfg["run_root"], ["vrn_basicinfo_yfinance_field_fixed_preview_v0589.csv"], max_files=1)
    if latest:
        return def_read_csv(latest[0]), latest[0], "LATEST_V0589_PREVIEW"

    p = cfg["canonical_dir"] / "vrn_basicinfo_active.csv"
    return def_read_csv(p), p, "CANONICAL_ACTIVE"


def def_collect_zones_for_key(base_row: dict, bank: dict, source_cap: int = 140) -> list[tuple[str, str]]:
    zones: list[tuple[str, str]] = []

    def add(zone: str, text: Any):
        if def_nonblank(text):
            zones.append((zone, str(text)))

    def add_from_row(prefix: str, row: dict):
        add(prefix + ".Valuation Method", def_first(row, ["Valuation Method", "Valuation", "valuation"]))
        add(prefix + ".Valuation Evidence Text", def_first(row, ["Valuation Evidence Text"]))
        add(prefix + ".Target Price", def_first(row, ["Target Price", "Target Price Raw"]))

        for col in ["Source Text", "source_text", "Method", "method"]:
            raw = def_first(row, [col])
            obj = def_safe_json_loads(raw)
            if obj:
                for k in ["valuation", "target_price", "rating", "analyst", "summary", "body"]:
                    add(f"{prefix}.{col}.{k}", obj.get(k, ""))
            else:
                add(prefix + "." + col, raw)

        for col in [
            "Sentence", "Sentence Text", "Text", "Page Text", "First Page Text",
            "Repaired Text", "Body Text", "Chunk Text", "Content",
            "Filename Normalized", "Filename Tokens"
        ]:
            add(prefix + "." + col, row.get(col, ""))

    add_from_row("base", base_row)

    keys = []
    fn, tk = def_row_key(base_row)
    keys.extend([(fn, tk), ("", tk), (fn, "")])

    seen_rows = set()
    count = 0

    for key in keys:
        for src, r in bank.get(key, []):
            rid = (src, id(r))
            if rid in seen_rows:
                continue
            seen_rows.add(rid)
            add_from_row("bank:" + Path(src).name, r)
            count += 1
            if count >= source_cap:
                break

    return zones


# ==================================================================================================
# def 05_EXTRACTION
# ==================================================================================================
def def_extract_valuation(base_row: dict, bank: dict, lex: dict) -> dict:
    zones = def_collect_zones_for_key(base_row, bank)
    matches = []

    for zone, text0 in zones:
        text = def_clean_text(text0)
        if not text:
            continue

        for method, patterns in lex.items():
            for pat in patterns:
                try:
                    for m in re.finditer(pat, text, flags=re.MULTILINE):
                        ev = def_window(text, m.start(), m.end(), radius=300)
                        if not def_method_hard_gate(method, ev):
                            continue
                        matches.append({
                            "method": method,
                            "zone": zone,
                            "pattern": pat,
                            "evidence": ev,
                            "start": m.start(),
                            "end": m.end(),
                        })
                except Exception:
                    pass

    if not matches:
        return {
            "Valuation Method": "",
            "Valuation Evidence Text": "",
            "Valuation Source Zone": "",
            "Valuation Confidence": 0.0,
            "Valuation Rebind Decision": "NO_VALUATION_METHOD_FOUND",
            "Valuation Synonym Match Count": 0,
            "Valuation Source Count": len(zones),
        }

    priority_zone = [
        ("Valuation Method", 105),
        ("Source Text.valuation", 100),
        ("source_text.valuation", 100),
        ("method.valuation", 96),
        ("Source Text.target_price", 92),
        ("source_text.target_price", 92),
        ("Valuation Evidence Text", 90),
        ("Target Price", 82),
        ("First Page Text", 72),
        ("Repaired Text", 72),
        ("Page Text", 70),
        ("Sentence", 68),
        ("Text", 65),
        ("Filename", 20),
    ]

    def score(m: dict) -> int:
        zone = m["zone"]
        ev = m["evidence"]
        s = 50

        for token, pts in priority_zone:
            if token.lower() in zone.lower():
                s = max(s, pts)

        if re.search(r"\d+(\.\d+)?\s*(x|X|倍)", ev):
            s += 14
        if re.search(r"目標價|target price|price target|TP|PT", ev, re.I):
            s += 8
        if re.search(r"評價|valuation|value|derive|based on|基於|以|給[予與]", ev, re.I):
            s += 8
        if m["method"] in ["PER", "PBR", "EV/EBITDA", "EV/EBIT"] and re.search(r"\d+(\.\d+)?", ev):
            s += 4
        return s

    matches = sorted(matches, key=score, reverse=True)

    # def method de-dup with hard gate already applied
    methods = []
    method_best = {}

    for m in matches:
        method = m["method"]
        if method not in method_best:
            method_best[method] = m
        if method not in methods:
            methods.append(method)

    best = matches[0]
    final_methods = methods[:3]

    return {
        "Valuation Method": " + ".join(final_methods),
        "Valuation Evidence Text": best["evidence"],
        "Valuation Source Zone": best["zone"],
        "Valuation Confidence": min(0.99, round(score(best) / 135, 2)),
        "Valuation Rebind Decision": "PRECISION_REBIND_FROM_MULTI_SOURCE_EVIDENCE",
        "Valuation Synonym Match Count": len(matches),
        "Valuation Source Count": len(zones),
    }


# ==================================================================================================
# def 06_HTML_RENDER
# ==================================================================================================
def def_format_header(x: str) -> str:
    acr = {"DB", "API", "ID", "URL", "HTML", "JSON", "CSV", "SQL", "EPS", "ROE", "ROA", "TWD", "USD", "YTD", "QOQ", "YOY"}
    out = []
    for p in str(x or "").replace("_", " ").split():
        u = p.upper()
        if u in acr:
            out.append(u)
        elif re.search(r"[\u4e00-\u9fff]", p):
            out.append(p)
        else:
            out.append(p[:1].upper() + p[1:].lower())
    return " ".join(out)


def def_cell_class(col: str, val: Any) -> str:
    c = col.lower()
    if col == "Status Lights":
        return "status"
    if any(k in c for k in ["filename", "file", "path", "source", "text", "evidence", "reason", "decision", "pattern", "zone", "detail"]):
        return "left"
    if any(k in c for k in ["score", "confidence", "count", "rows"]):
        return "num"
    if len(str(val or "")) > 30:
        return "left"
    return "center"


def def_band(row: dict) -> str:
    s = str(row.get("Severity") or row.get("Status") or "").upper()
    if "ERR" in s or "RED" in s:
        return "red"
    if "WARN" in s or "MISSING" in s or "YELLOW" in s:
        return "yellow"
    return "green"


def def_table(rows: list[dict], limit: int = 1000) -> str:
    if not rows:
        return "<div class='empty'>No rows.</div>"
    rows = rows[:limit]

    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)

    if "Status Lights" in cols:
        cols = ["Status Lights"] + [c for c in cols if c != "Status Lights"]
    else:
        cols = ["Status Lights"] + cols

    th = "".join(f"<th>{def_h(def_format_header(c))}</th>" for c in cols)
    trs = []

    for r in rows:
        band = def_band(r)
        cells = []
        for c in cols:
            val = r.get(c, "")
            if c == "Status Lights" and not val:
                val = "🟢 INPUT  🟢 DB  🟢 TRUST" if band == "green" else "🟢 INPUT  🟡 DB  🟡 TRUST"
            cls = def_cell_class(c, val)
            collapse = " collapse" if cls == "left" and len(str(val)) > 120 else ""
            cells.append(f"<td class='{cls}{collapse}'>{def_h(val)}</td>")
        trs.append(f"<tr class='{band}'>" + "".join(cells) + "</tr>")

    return "<table><thead><tr>" + th + "</tr></thead><tbody>" + "\n".join(trs) + "</tbody></table>"


def def_render_html(path: Path, result: dict, overview: list[dict], audit: list[dict], basic: list[dict], sources: list[dict], missing: list[dict]) -> None:
    cards = [
        ("System Pass", result["system_pass"]),
        ("Basic Rows", result["counts"]["basic_rows"]),
        ("Found", result["counts"]["valuation_found"]),
        ("Missing", result["counts"]["valuation_missing"]),
        ("False PBR Fixed", result["counts"]["false_pbr_fixed"]),
        ("Source Files", result["counts"]["source_files"]),
        ("Preview Only", True),
    ]

    card_html = "".join(f"<div class='stat'><div class='n'>{def_h(v)}</div><div class='l'>{def_h(k)}</div></div>" for k, v in cards)

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN Valuation Method Precision Rebind v05.9.3</title>
<style>
:root {{
  --bg:#f5f4f0;--sf:#fff;--sf2:#fafaf8;--bd:#dbd9d3;--bl:#4c78a8;--tl:#439a9a;--vi:#7a6daa;
  --gn:#5a9e6f;--gn-l:#cde8d5;--am:#c4943a;--am-l:#f5e2b8;--co:#c96b5a;--co-l:#f5d0c8;
  --i0:#1e1d1a;--i2:#6b6860;--i3:#9c9890;--mo:Consolas,monospace;--sa:"Segoe UI","Microsoft JhengHei",system-ui,sans-serif;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);font-family:var(--sa);font-size:11px;color:var(--i0)}}
.wrap{{max-width:1760px;margin:0 auto;padding:12px}}
.hdr{{background:var(--sf);border:1px solid var(--bd);border-radius:16px;padding:16px 18px;margin-bottom:10px;display:flex;gap:12px;position:relative;overflow:hidden}}
.hdr:before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--bl),var(--tl),var(--vi),var(--am),var(--co))}}
.logo{{width:42px;height:42px;border-radius:12px;background:#1e3a5f;color:#8dcff0;display:flex;align-items:center;justify-content:center;font-weight:900;font-family:var(--mo)}}
.h1{{font-size:20px;font-weight:850}}.h1 span{{color:var(--bl)}}.sub{{font-size:10px;color:var(--i3);margin-top:2px}}
.tabs{{display:flex;gap:4px;margin-bottom:10px;flex-wrap:wrap}}
.tabs button{{border:1px solid var(--bd);background:var(--sf);border-radius:999px;padding:8px 14px;font-weight:750;font-size:11px;cursor:pointer;transition:.16s;color:var(--i2)}}
.tabs button:hover{{transform:translateY(-1px);box-shadow:0 8px 18px rgba(30,29,26,.08);border-color:var(--bl);color:var(--bl)}}
.tabs button.on{{background:var(--bl);border-color:var(--bl);color:white}}
.tabs button:active{{transform:scale(.94) translateY(1px);box-shadow:inset 0 2px 8px rgba(0,0,0,.18)}}
.page{{display:none}}.page.on{{display:block}}
.card{{background:var(--sf);border:1px solid var(--bd);border-radius:16px;margin-bottom:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.035)}}
.card h3{{margin:0;padding:10px 12px;background:var(--sf2);border-bottom:1px solid var(--bd);font-size:12px}}
.statgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-bottom:10px}}
.stat{{background:var(--sf);border:1px solid var(--bd);border-radius:14px;padding:10px;transition:.16s}}
.stat:hover{{transform:translateY(-2px) scale(1.01);box-shadow:0 12px 26px rgba(30,29,26,.10)}}
.stat .n{{text-align:right;font-family:var(--mo);font-size:20px;font-weight:900}}.stat .l{{text-align:center;color:var(--i3);font-size:9px;text-transform:uppercase}}
.tablewrap{{overflow:auto;max-height:76vh;border:1px solid var(--bd);border-radius:12px;resize:both;background:var(--sf)}}
table{{border-collapse:collapse;width:max-content;min-width:100%;font-size:10px;table-layout:auto}}
th{{position:sticky;top:0;z-index:2;background:#ef0000;color:#fff;padding:8px 9px;border:1px solid var(--bd);text-align:center;vertical-align:top;white-space:normal;overflow-wrap:anywhere}}
td{{padding:6px 8px;border:1px solid var(--bd);vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:780px;line-height:1.35;text-align:center}}
td.left{{text-align:left;min-width:260px;max-width:900px}}
td.center{{text-align:center}}
td.num{{text-align:right;font-family:var(--mo);font-variant-numeric:tabular-nums;white-space:nowrap}}
td.status{{text-align:center;font-family:var(--mo);font-weight:900;white-space:nowrap;min-width:150px}}
td.collapse{{display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}}
tr.green td{{background:linear-gradient(0deg,rgba(205,232,213,.84),rgba(255,255,255,.92))}}
tr.yellow td{{background:linear-gradient(0deg,rgba(245,226,184,.86),rgba(255,255,255,.92))}}
tr.red td{{background:linear-gradient(0deg,rgba(245,208,200,.9),rgba(255,255,255,.92))}}
pre{{background:#1e1d1a;color:#d1fae5;border-radius:10px;padding:12px;overflow:auto;white-space:pre-wrap}}
</style>
<script>
function tab(id){{
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('on'));
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));
  document.getElementById(id).classList.add('on');
  document.getElementById('b_'+id).classList.add('on');
  try{{ if(navigator.vibrate) navigator.vibrate(18); }}catch(e){{}}
}}
</script>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div class="logo">VRN</div>
    <div>
      <div class="h1"><span>VeritasReportNova</span> Valuation Method Precision Rebind <span style="font-size:12px;color:var(--i3)">v05.9.3</span></div>
      <div class="sub">multi-source panorama · PBR hard gate · false-positive repair · valuation evidence rebind</div>
    </div>
  </div>

  <div class="tabs">
    <button id="b_overview" class="on" onclick="tab('overview')">01 Overview</button>
    <button id="b_audit" onclick="tab('audit')">02 Valuation Audit</button>
    <button id="b_missing" onclick="tab('missing')">03 Missing Review</button>
    <button id="b_basic" onclick="tab('basic')">04 BasicInfo Preview</button>
    <button id="b_sources" onclick="tab('sources')">05 Source Matrix</button>
    <button id="b_json" onclick="tab('json')">06 JSON</button>
  </div>

  <div id="overview" class="page on"><div class="statgrid">{card_html}</div><div class="card"><h3>Overview Matrix</h3><div class="tablewrap">{def_table(overview)}</div></div></div>
  <div id="audit" class="page"><div class="card"><h3>Valuation Audit</h3><div class="tablewrap">{def_table(audit)}</div></div></div>
  <div id="missing" class="page"><div class="card"><h3>Missing Review</h3><div class="tablewrap">{def_table(missing)}</div></div></div>
  <div id="basic" class="page"><div class="card"><h3>BasicInfo Preview</h3><div class="tablewrap">{def_table(basic)}</div></div></div>
  <div id="sources" class="page"><div class="card"><h3>Source Matrix</h3><div class="tablewrap">{def_table(sources)}</div></div></div>
  <div id="json" class="page"><div class="card"><h3>JSON</h3><pre>{def_h(json.dumps(result, ensure_ascii=False, indent=2))}</pre></div></div>
</div>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 07_MAIN
# ==================================================================================================
def def_main() -> None:
    cfg = def_config()
    cfg["run_dir"].mkdir(parents=True, exist_ok=True)

    files = def_source_files(cfg)
    bank, source_matrix = def_build_source_bank(files)

    base, base_src, base_src_type = def_base_rows(cfg)
    lex = def_valuation_patterns()

    audit = []
    basic_out = []
    missing_rows = []
    false_pbr_fixed = 0

    for row in base:
        r = dict(row)
        old_val = def_first(r, ["Valuation Method", "Valuation"])
        ex = def_extract_valuation(r, bank, lex)
        new_val = ex["Valuation Method"]

        # def final false-PBR cleanup：若只因舊值含 PBR 但 evidence 不含 PBR hard-gate，刪 PBR
        if "PBR" in new_val and not def_method_hard_gate("PBR", ex.get("Valuation Evidence Text", "")):
            parts = [p.strip() for p in new_val.split("+") if p.strip() and p.strip() != "PBR"]
            new_val = " + ".join(parts)
            false_pbr_fixed += 1

        if def_nonblank(new_val):
            r["Valuation Method"] = new_val
            r["Valuation Evidence Text"] = ex["Valuation Evidence Text"]
            r["Valuation Source Zone"] = ex["Valuation Source Zone"]
            r["Valuation Confidence"] = ex["Valuation Confidence"]
            r["Valuation Rebind Decision"] = ex["Valuation Rebind Decision"]
            r["Valuation Synonym Match Count"] = ex["Valuation Synonym Match Count"]
            r["Valuation Source Count"] = ex["Valuation Source Count"]
            status = "FOUND"
            severity = "OK"
            lights = "🟢 INPUT  🟢 DB  🟢 TRUST"
        else:
            r["Valuation Evidence Text"] = ""
            r["Valuation Source Zone"] = ""
            r["Valuation Confidence"] = 0
            r["Valuation Rebind Decision"] = "NO_VALUATION_METHOD_FOUND_AFTER_MULTI_SOURCE_SCAN"
            r["Valuation Synonym Match Count"] = 0
            r["Valuation Source Count"] = ex["Valuation Source Count"]
            status = "MISSING"
            severity = "WARN"
            lights = "🟢 INPUT  🟡 DB  🟡 TRUST"

        a = {
            "Status Lights": lights,
            "Filename": def_first(r, ["Filename", "File"]),
            "Ticker": def_first(r, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker"]),
            "Name": def_first(r, ["Name"]),
            "Old Valuation Method": old_val,
            "New Valuation Method": r.get("Valuation Method", ""),
            "Valuation Source Zone": r.get("Valuation Source Zone", ""),
            "Valuation Confidence": r.get("Valuation Confidence", ""),
            "Valuation Synonym Match Count": r.get("Valuation Synonym Match Count", ""),
            "Valuation Source Count": r.get("Valuation Source Count", ""),
            "Valuation Evidence Text": r.get("Valuation Evidence Text", ""),
            "Status": status,
            "Severity": severity,
        }

        audit.append(a)
        basic_out.append(r)

        if status == "MISSING":
            missing_rows.append(a)

    found = sum(1 for x in audit if x["Status"] == "FOUND")
    missing = sum(1 for x in audit if x["Status"] == "MISSING")

    overview = [
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "BASE_SOURCE", "Value": str(base_src), "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "BASE_SOURCE_TYPE", "Value": base_src_type, "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "SOURCE_FILES_SCANNED", "Value": len(files), "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "VALUATION_FOUND", "Value": found, "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟡 DB  🟡 TRUST" if missing else "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "VALUATION_MISSING", "Value": missing, "Severity": "WARN" if missing else "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "PBR_HARD_GATE", "Value": "ENABLED", "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "FALSE_PBR_FIXED", "Value": false_pbr_fixed, "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "NO_STABLE_CANONICAL_MUTATION", "Value": True, "Severity": "OK"},
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": len(base) > 0,
        "mode": "READ_ONLY_MULTI_SOURCE_VALUATION_PRECISION_REBIND",
        "sources": {
            "base_source": str(base_src),
            "base_source_type": base_src_type,
            "source_file_count": len(files),
        },
        "counts": {
            "basic_rows": len(base),
            "valuation_found": found,
            "valuation_missing": missing,
            "false_pbr_fixed": false_pbr_fixed,
            "source_files": len(files),
        },
        "outputs": {
            "html": str(cfg["out_html"]),
            "json": str(cfg["out_json"]),
            "basic_csv": str(cfg["out_basic_csv"]),
            "audit_csv": str(cfg["out_audit_csv"]),
            "source_csv": str(cfg["out_source_csv"]),
            "missing_csv": str(cfg["out_miss_csv"]),
        },
        "rule_lock": [
            "PBR requires hard evidence: P/B, PBR, PBV, price-to-book, 股價淨值比, 市淨率, 淨值比.",
            "PER evidence cannot imply PBR.",
            "Multi-source source bank is used.",
            "No stable/canonical mutation.",
            "YFinance does not provide valuation method.",
        ],
    }

    def_write_csv(cfg["out_basic_csv"], basic_out)
    def_write_csv(cfg["out_audit_csv"], audit)
    def_write_csv(cfg["out_source_csv"], source_matrix)
    def_write_csv(cfg["out_miss_csv"], missing_rows)
    def_write_json(cfg["out_json"], result)
    def_render_html(cfg["out_html"], result, overview, audit, basic_out, source_matrix, missing_rows)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise