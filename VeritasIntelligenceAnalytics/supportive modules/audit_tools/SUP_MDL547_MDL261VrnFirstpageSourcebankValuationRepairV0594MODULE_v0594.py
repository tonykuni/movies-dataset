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


VERSION = "VRN_FIRSTPAGE_SOURCEBANK_VALUATION_REPAIR_V0594"


# ==================================================================================================
# def 01_CONFIG
# ==================================================================================================
def def_config() -> dict:
    via_root = Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics")
    vrn_root = via_root / "module" / "VRN"
    run_root = vrn_root / "_vrn_operation_ui_runs"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = run_root / f"VRN_FIRSTPAGE_SOURCEBANK_VALUATION_REPAIR_V0594_INNER_{ts}"

    return {
        "via_root": via_root,
        "vrn_root": vrn_root,
        "run_root": run_root,
        "canonical_dir": vrn_root / "_vrn_canonical_active",
        "integrated_root": vrn_root / "_vrn_integrated_trust_runs",
        "stable_root": vrn_root / "_vrn_stable_release",
        "input_dir": vrn_root / "input",
        "supportive_dir": via_root / "module" / "supportive_module",
        "run_dir": run_dir,
        "out_html": run_dir / "VRN_FirstPage_SourceBank_Valuation_Repair_v0594.html",
        "out_json": run_dir / "vrn_firstpage_sourcebank_valuation_repair_v0594.json",
        "out_basic_csv": run_dir / "vrn_basicinfo_valuation_repair_preview_v0594.csv",
        "out_audit_csv": run_dir / "vrn_valuation_repair_audit_v0594.csv",
        "out_source_bank_csv": run_dir / "vrn_firstpage_sourcebank_v0594.csv",
        "out_missing_diag_csv": run_dir / "vrn_valuation_missing_diagnosis_v0594.csv",
        "out_file_matrix_csv": run_dir / "vrn_related_file_matrix_v0594.csv",
        "out_support_csv": run_dir / "vrn_supportive_matrix_v0594.csv",
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
    s = str(x or "").strip().replace("\\", "/").split("/")[-1]
    s = re.sub(r"\.pdf$", "", s, flags=re.I)
    return s.lower()


def def_norm_ticker(x: Any) -> str:
    m = re.search(r"\b[1-9]\d{3}\b", str(x or ""))
    return m.group(0) if m else ""


def def_window(text: str, start: int, end: int, radius: int = 340) -> str:
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    return def_clean_text(text[a:b])


def def_find_latest_files(root: Path, patterns: list[str], max_files: int = 120) -> list[Path]:
    hits = []
    if not root.exists():
        return []
    for pat in patterns:
        try:
            hits.extend(root.rglob(pat))
        except Exception:
            pass
    hits = [p for p in hits if p.exists() and p.is_file()]
    hits = sorted(set(hits), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[:max_files]


def def_severity_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if "ERR" in s or "RED" in s:
        return "🔴 INPUT  🔴 DB  🔴 TRUST"
    if "WARN" in s or "YELLOW" in s or "MISSING" in s:
        return "🟢 INPUT  🟡 DB  🟡 TRUST"
    return "🟢 INPUT  🟢 DB  🟢 TRUST"


# ==================================================================================================
# def 03_VALUATION_LEXICON
# ==================================================================================================
def def_valuation_patterns() -> dict:
    return {
        "PER": [
            r"(?i)\bP\s*/?\s*E\b",
            r"(?i)\bPER\b",
            r"(?i)\bPE\s*ratio\b",
            r"(?i)\bprice[- ]?to[- ]?earnings\b",
            r"(?i)\bearnings\s+multiple\b",
            r"(?i)\bforward\s+P\s*/?\s*E\b",
            r"(?i)\btrailing\s+P\s*/?\s*E\b",
            r"(?i)\bFY\d{2}E?\s*P\s*/?\s*E\b",
            r"(?i)\b\d+(\.\d+)?\s*x\s*(P\s*/?\s*E|PE|PER)\b",
            r"(?i)(P\s*/?\s*E|PE|PER)\s*(of|multiple|ratio)?\s*\d+(\.\d+)?\s*x",
            r"(?i)implying.{0,60}(P\s*/?\s*E|PE|PER).{0,40}\d+(\.\d+)?\s*x",
            r"(?i)our\s+(TP|PT|target price|price target).{0,100}(P\s*/?\s*E|PE|PER)",
            r"(?i)we\s+(derive|value|set).{0,120}(P\s*/?\s*E|PE|PER|earnings multiple)",
            r"(?i)applying.{0,80}\d+(\.\d+)?\s*x.{0,50}(earnings|EPS|P\s*/?\s*E|PE|PER)",
            r"(?i)(sector|peer|historical).{0,40}(average|premium|discount).{0,80}(P\s*/?\s*E|PE|PER|multiple)",
            r"本益比",
            r"預估本益比|目標本益比|合理本益比|常態本益比|歷史本益比|展望年本益比",
            r"本益比評價|本益比法|本益比區間|本益比倍數",
            r"\d+(\.\d+)?\s*倍\s*本益比",
            r"\d+(\.\d+)?\s*x\s*本益比",
            r"以.{0,80}?\d+(\.\d+)?\s*[xX倍]?.{0,30}本益比.{0,70}?評價",
            r"基於.{0,90}?\d+(\.\d+)?\s*[xX倍]?.{0,30}(PER|PE|P/E|本益比)",
            r"評價區間.{0,80}\d+(\.\d+)?\s*[xX倍]\s*[-~–至]\s*\d+(\.\d+)?\s*[xX倍]?.{0,70}(PER|PE|P/E|本益比)",
            r"常態本益比.{0,60}\d+(\.\d+)?\s*[-~–至]\s*\d+(\.\d+)?\s*倍",
            r"給[予與].{0,60}\d+(\.\d+)?\s*倍",
            r"推導目標價.{0,120}(本益比|PER|PE|P/E)",
            r"目標價隱含.{0,120}(本益比|PER|PE|P/E)",
            r"參考同業.{0,120}(本益比|PER|PE|P/E|倍數)",
            r"歷史區間.{0,120}(本益比|PER|PE|P/E|倍數)",
            r"以.{0,30}(明年|後年|202\d年|FY\d{2}).{0,50}EPS.{0,60}(估算|評價|推導)",
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
            r"企業價值.{0,20}EBITDA|EBITDA倍數",
        ],
        "EV/EBIT": [
            r"(?i)\bEV\s*/?\s*EBIT\b",
            r"(?i)\bEV[- ]?to[- ]?EBIT\b",
            r"(?i)\benterprise\s+value\s+to\s+EBIT\b",
            r"(?i)\bEBIT\s+multiple\b",
            r"企業價值.{0,20}EBIT|EBIT倍數",
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
        "PER": r"(?i)(\bP\s*/?\s*E\b|\bPER\b|\bPE\s*ratio\b|price[- ]?to[- ]?earnings|earnings\s+multiple|本益比|EPS)",
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
    return True if not pat else bool(re.search(pat, e))


# ==================================================================================================
# def 04_RELATED_FILES_AND_SOURCE_BANK
# ==================================================================================================
def def_related_file_patterns() -> list[str]:
    return [
        "vrn_basicinfo*.csv",
        "vrn_basicinfo*.json",
        "vrn_*source_text*.csv",
        "vrn_*sentence*.csv",
        "vrn_*first*page*.csv",
        "vrn_*page1*.csv",
        "vrn_*repaired*.csv",
        "vrn_*text*.csv",
        "vrn_*valuation*.csv",
        "VRN_*v05*.json",
        "*.pdf",
    ]


def def_collect_related_files(cfg: dict) -> list[Path]:
    files = []
    for p in [
        cfg["canonical_dir"] / "vrn_basicinfo_active.csv",
        cfg["canonical_dir"] / "vrn_financial_active.csv",
    ]:
        if p.exists():
            files.append(p)

    roots = [
        cfg["run_root"],
        cfg["integrated_root"],
        cfg["stable_root"],
        cfg["input_dir"],
    ]

    for root in roots:
        files.extend(def_find_latest_files(root, def_related_file_patterns(), max_files=180))

    seen = set()
    out = []
    for p in files:
        key = str(p).lower()
        if key not in seen and p.exists():
            seen.add(key)
            out.append(p)
    return out[:220]


def def_extract_pdf_first_page_text(path: Path) -> str:
    if path.suffix.lower() != ".pdf":
        return ""
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            if not pdf.pages:
                return ""
            return def_clean_text(pdf.pages[0].extract_text() or "")
    except Exception:
        return ""


def def_file_matrix(files: list[Path]) -> list[dict]:
    rows = []
    for p in files:
        kind = "PDF" if p.suffix.lower() == ".pdf" else "CSV_OR_JSON"
        size = p.stat().st_size if p.exists() else 0
        rows.append({
            "Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST",
            "Path": str(p),
            "Name": p.name,
            "Type": kind,
            "Size": size,
            "Modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if p.exists() else "",
            "Severity": "OK",
        })
    return rows


def def_row_key(row: dict) -> tuple[str, str]:
    filename = def_norm_filename(def_first(row, ["Filename", "File", "Source File", "source_file", "PDF", "Path"]))
    ticker = def_norm_ticker(def_first(row, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker", "ticker", "Stock Code"]))
    return filename, ticker


def def_pdf_key(path: Path) -> tuple[str, str]:
    name = def_norm_filename(path.name)
    ticker = def_norm_ticker(path.name)
    return name, ticker


def def_source_zone_candidates(row: dict) -> list[tuple[str, str]]:
    zones = []

    def add(zone: str, value: Any):
        if def_nonblank(value):
            zones.append((zone, str(value)))

    for col in [
        "Valuation Method", "Valuation", "Valuation Evidence Text",
        "Target Price", "Rating", "Summary",
        "Source Text", "source_text", "Method", "method",
        "Sentence", "Sentence Text", "Text", "Page Text", "First Page Text",
        "FirstPage Text", "Page1 Text", "Repaired Text", "Body Text",
        "Title", "Main Title", "Subtitle", "Heading", "Chunk Text", "Content",
        "Filename Normalized", "Filename Tokens"
    ]:
        raw = row.get(col, "")
        obj = def_safe_json_loads(raw)
        if obj:
            for k in ["valuation", "target_price", "rating", "analyst", "summary", "body", "title", "page_text", "first_page"]:
                add(f"{col}.{k}", obj.get(k, ""))
        else:
            add(col, raw)

    return zones


def def_build_source_bank(files: list[Path]) -> tuple[dict, list[dict]]:
    bank: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    source_bank_rows = []

    def add_to_bank(key: tuple[str, str], source_path: str, zone: str, text: str):
        text = def_clean_text(text)
        if not text:
            return
        bank.setdefault(key, []).append((source_path, zone, text))

    for p in files:
        if p.suffix.lower() == ".csv":
            rows = def_read_csv(p)
            for r in rows:
                key = def_row_key(r)
                fn, tk = key
                if key == ("", ""):
                    continue

                zones = def_source_zone_candidates(r)
                for zone, text in zones:
                    add_to_bank(key, str(p), zone, text)
                    if tk:
                        add_to_bank(("", tk), str(p), zone, text)
                    if fn:
                        add_to_bank((fn, ""), str(p), zone, text)

                source_bank_rows.append({
                    "Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST" if zones else "🟢 INPUT  🟡 DB  🟡 TRUST",
                    "Source File": str(p),
                    "Filename Key": fn,
                    "Ticker Key": tk,
                    "Rows": len(rows),
                    "Zone Count": len(zones),
                    "Has Source Text": any("source text" in z.lower() for z, _ in zones),
                    "Has First Page Text": any(("first" in z.lower() and "page" in z.lower()) or "page1" in z.lower() for z, _ in zones),
                    "Has Sentence Units": any("sentence" in z.lower() for z, _ in zones),
                    "Severity": "OK" if zones else "WARN",
                })

        elif p.suffix.lower() == ".pdf":
            key = def_pdf_key(p)
            text = def_extract_pdf_first_page_text(p)
            if text:
                add_to_bank(key, str(p), "PDF_FIRST_PAGE_TEXT_LAYER", text)
                if key[1]:
                    add_to_bank(("", key[1]), str(p), "PDF_FIRST_PAGE_TEXT_LAYER", text)
                if key[0]:
                    add_to_bank((key[0], ""), str(p), "PDF_FIRST_PAGE_TEXT_LAYER", text)

            source_bank_rows.append({
                "Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST" if text else "🟢 INPUT  🟡 DB  🟡 TRUST",
                "Source File": str(p),
                "Filename Key": key[0],
                "Ticker Key": key[1],
                "Rows": 1,
                "Zone Count": 1 if text else 0,
                "Has Source Text": False,
                "Has First Page Text": bool(text),
                "Has Sentence Units": False,
                "Severity": "OK" if text else "WARN",
            })

    return bank, source_bank_rows


def def_base_rows(cfg: dict) -> tuple[list[dict], Path, str]:
    candidates = def_find_latest_files(cfg["run_root"], [
        "vrn_basicinfo_valuation_precision_rebind_v0593.csv",
        "vrn_basicinfo_valuation_rebind_v0592.csv",
        "vrn_basicinfo_yfinance_field_fixed_preview_v0589.csv",
        "vrn_basicinfo_yfinance_input_ticker_v0588.csv",
    ], max_files=1)

    if candidates:
        return def_read_csv(candidates[0]), candidates[0], "LATEST_OPERATION_PREVIEW"

    p = cfg["canonical_dir"] / "vrn_basicinfo_active.csv"
    return def_read_csv(p), p, "CANONICAL_ACTIVE"


# ==================================================================================================
# def 05_VALUATION_EXTRACTION
# ==================================================================================================
def def_score_zone(zone: str) -> int:
    z = zone.lower()
    if "valuation evidence" in z:
        return 108
    if "valuation" in z:
        return 104
    if "source text.valuation" in z:
        return 102
    if "target_price" in z or "target price" in z:
        return 92
    if "first" in z and "page" in z:
        return 86
    if "repaired" in z:
        return 84
    if "sentence" in z:
        return 78
    if "body" in z or "content" in z or "text" in z:
        return 70
    if "filename" in z:
        return 25
    return 50


def def_extract_valuation_for_row(row: dict, bank: dict, lex: dict) -> dict:
    fn, tk = def_row_key(row)
    keys = [(fn, tk), ("", tk), (fn, "")]
    zones = []

    # base row zones first
    for z, t in def_source_zone_candidates(row):
        zones.append(("[BASE_ROW]", z, t))

    # bank zones
    seen = set()
    for key in keys:
        for src, zone, text in bank.get(key, []):
            sig = (src, zone, text[:160])
            if sig in seen:
                continue
            seen.add(sig)
            zones.append((src, zone, text))

    matches = []
    for src, zone, text0 in zones:
        text = def_clean_text(text0)
        if not text:
            continue

        for method, patterns in lex.items():
            for pat in patterns:
                try:
                    for m in re.finditer(pat, text, flags=re.MULTILINE):
                        ev = def_window(text, m.start(), m.end(), radius=340)
                        if not def_method_hard_gate(method, ev):
                            continue
                        matches.append({
                            "method": method,
                            "source": src,
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
            "Valuation Source File": "",
            "Valuation Source Zone": "",
            "Valuation Confidence": 0.0,
            "Valuation Rebind Decision": "NO_VALUATION_METHOD_FOUND_AFTER_FIRSTPAGE_SOURCEBANK",
            "Valuation Synonym Match Count": 0,
            "Valuation Source Count": len(zones),
            "Has Source Text": any("source text" in z.lower() for _, z, _ in zones),
            "Has First Page Repaired Text": any(("first" in z.lower() and "page" in z.lower()) or "repaired" in z.lower() for _, z, _ in zones),
            "Has Sentence Units": any("sentence" in z.lower() for _, z, _ in zones),
        }

    def score(m: dict) -> int:
        ev = m["evidence"]
        s = def_score_zone(m["zone"])
        if m["source"] == "[BASE_ROW]":
            s += 4
        if re.search(r"\d+(\.\d+)?\s*(x|X|倍)", ev):
            s += 14
        if re.search(r"目標價|target price|price target|TP|PT", ev, re.I):
            s += 8
        if re.search(r"評價|valuation|value|derive|based on|基於|以|給[予與]|implying|applying", ev, re.I):
            s += 8
        if re.search(r"EPS|每股盈餘", ev, re.I):
            s += 4
        return s

    matches = sorted(matches, key=score, reverse=True)
    best = matches[0]

    methods = []
    for m in matches:
        if m["method"] not in methods:
            methods.append(m["method"])

    # prevent PER-only evidence from carrying PBR
    final_methods = []
    for method in methods:
        m_best = next((m for m in matches if m["method"] == method), None)
        if m_best and def_method_hard_gate(method, m_best["evidence"]):
            final_methods.append(method)

    return {
        "Valuation Method": " + ".join(final_methods[:3]),
        "Valuation Evidence Text": best["evidence"],
        "Valuation Source File": best["source"],
        "Valuation Source Zone": best["zone"],
        "Valuation Confidence": min(0.99, round(score(best) / 140, 2)),
        "Valuation Rebind Decision": "FIRSTPAGE_SOURCEBANK_MULTI_SOURCE_REPAIR",
        "Valuation Synonym Match Count": len(matches),
        "Valuation Source Count": len(zones),
        "Has Source Text": any("source text" in z.lower() for _, z, _ in zones),
        "Has First Page Repaired Text": any(("first" in z.lower() and "page" in z.lower()) or "repaired" in z.lower() for _, z, _ in zones),
        "Has Sentence Units": any("sentence" in z.lower() for _, z, _ in zones),
    }


# ==================================================================================================
# def 06_SUPPORTIVE
# ==================================================================================================
def def_supportive_matrix(cfg: dict) -> list[dict]:
    files = [
        cfg["supportive_dir"] / "VIA_SSOT_Unified.py",
        cfg["supportive_dir"] / "VIA_SSOT_PanoramicAugmenter_v2.ps1",
        cfg["supportive_dir"] / "Invoke-VIA-ALL.ps1",
        cfg["supportive_dir"] / "Invoke-VIA-SupportiveHardGate.ps1",
        cfg["supportive_dir"] / "VIA_Panorama_AST_RuntimeInjector.py",
        cfg["supportive_dir"] / "SUP_MDL001_RuntimeImportFirewall.py",
    ]
    rows = []
    for p in files:
        ok = p.exists()
        rows.append({
            "Status Lights": def_severity_lights("OK" if ok else "ERR"),
            "File": str(p),
            "Name": p.name,
            "Exists": ok,
            "Type": p.suffix,
            "Check": "PRESENT",
            "Status": "OK" if ok else "ERR",
            "Severity": "OK" if ok else "ERR",
        })
    return rows


# ==================================================================================================
# def 07_HTML
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
    if any(k in c for k in ["score", "confidence", "count", "rows", "size"]):
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


def def_table(rows: list[dict], limit: int = 1200) -> str:
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
            collapse = " collapse" if cls == "left" and len(str(val)) > 130 else ""
            cells.append(f"<td class='{cls}{collapse}'>{def_h(val)}</td>")
        trs.append(f"<tr class='{band}'>" + "".join(cells) + "</tr>")

    return "<table><thead><tr>" + th + "</tr></thead><tbody>" + "\n".join(trs) + "</tbody></table>"


def def_render_html(path: Path, result: dict, overview: list[dict], audit: list[dict], missing: list[dict], basic: list[dict], source_bank: list[dict], file_matrix: list[dict], support: list[dict]) -> None:
    cards = [
        ("System Pass", result["system_pass"]),
        ("Basic Rows", result["counts"]["basic_rows"]),
        ("Found", result["counts"]["valuation_found"]),
        ("Missing", result["counts"]["valuation_missing"]),
        ("With Source Text", result["counts"]["with_source_text"]),
        ("With FirstPage", result["counts"]["with_firstpage"]),
        ("With Sentence", result["counts"]["with_sentence_units"]),
        ("Files", result["counts"]["related_files"]),
    ]
    card_html = "".join(f"<div class='stat'><div class='n'>{def_h(v)}</div><div class='l'>{def_h(k)}</div></div>" for k, v in cards)

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN FirstPage SourceBank Valuation Repair v05.9.4</title>
<style>
:root {{
  --bg:#f5f4f0;--sf:#fff;--sf2:#fafaf8;--bd:#dbd9d3;--bl:#4c78a8;--tl:#439a9a;--vi:#7a6daa;
  --gn:#5a9e6f;--gn-l:#cde8d5;--am:#c4943a;--am-l:#f5e2b8;--co:#c96b5a;--co-l:#f5d0c8;
  --i0:#1e1d1a;--i2:#6b6860;--i3:#9c9890;--mo:Consolas,monospace;--sa:"Segoe UI","Microsoft JhengHei",system-ui,sans-serif;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);font-family:var(--sa);font-size:11px;color:var(--i0)}}
.wrap{{max-width:1800px;margin:0 auto;padding:12px}}
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
td{{padding:6px 8px;border:1px solid var(--bd);vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:820px;line-height:1.35;text-align:center}}
td.left{{text-align:left;min-width:260px;max-width:960px}}
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
      <div class="h1"><span>VeritasReportNova</span> FirstPage SourceBank Valuation Repair <span style="font-size:12px;color:var(--i3)">v05.9.4</span></div>
      <div class="sub">panoramic related-file scan · source text · repaired first-page · sentence units · PDF first-page fallback · preview only</div>
    </div>
  </div>

  <div class="tabs">
    <button id="b_overview" class="on" onclick="tab('overview')">01 Overview</button>
    <button id="b_audit" onclick="tab('audit')">02 Valuation Repair</button>
    <button id="b_missing" onclick="tab('missing')">03 Missing Diagnosis</button>
    <button id="b_basic" onclick="tab('basic')">04 BasicInfo Preview</button>
    <button id="b_sourcebank" onclick="tab('sourcebank')">05 Source Bank</button>
    <button id="b_files" onclick="tab('files')">06 Related Files</button>
    <button id="b_support" onclick="tab('support')">07 Supportive</button>
    <button id="b_json" onclick="tab('json')">08 JSON</button>
  </div>

  <div id="overview" class="page on"><div class="statgrid">{card_html}</div><div class="card"><h3>Overview Matrix</h3><div class="tablewrap">{def_table(overview)}</div></div></div>
  <div id="audit" class="page"><div class="card"><h3>Valuation Repair Audit</h3><div class="tablewrap">{def_table(audit)}</div></div></div>
  <div id="missing" class="page"><div class="card"><h3>Missing Diagnosis</h3><div class="tablewrap">{def_table(missing)}</div></div></div>
  <div id="basic" class="page"><div class="card"><h3>BasicInfo Preview</h3><div class="tablewrap">{def_table(basic)}</div></div></div>
  <div id="sourcebank" class="page"><div class="card"><h3>FirstPage / SourceText Source Bank</h3><div class="tablewrap">{def_table(source_bank)}</div></div></div>
  <div id="files" class="page"><div class="card"><h3>Related File Matrix</h3><div class="tablewrap">{def_table(file_matrix)}</div></div></div>
  <div id="support" class="page"><div class="card"><h3>Supportive Matrix</h3><div class="tablewrap">{def_table(support)}</div></div></div>
  <div id="json" class="page"><div class="card"><h3>JSON</h3><pre>{def_h(json.dumps(result, ensure_ascii=False, indent=2))}</pre></div></div>
</div>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 08_MAIN
# ==================================================================================================
def def_main() -> None:
    cfg = def_config()
    cfg["run_dir"].mkdir(parents=True, exist_ok=True)

    files = def_collect_related_files(cfg)
    file_matrix = def_file_matrix(files)
    bank, source_bank_rows = def_build_source_bank(files)
    support_rows = def_supportive_matrix(cfg)

    base_rows, base_src, base_src_type = def_base_rows(cfg)
    lex = def_valuation_patterns()

    audit_rows = []
    basic_out = []
    missing_rows = []

    for row in base_rows:
        r = dict(row)
        old_val = def_first(r, ["Valuation Method", "Valuation"])
        ex = def_extract_valuation_for_row(r, bank, lex)

        found = def_nonblank(ex["Valuation Method"])

        if found:
            r["Valuation Method"] = ex["Valuation Method"]
            r["Valuation Evidence Text"] = ex["Valuation Evidence Text"]
            r["Valuation Source File"] = ex["Valuation Source File"]
            r["Valuation Source Zone"] = ex["Valuation Source Zone"]
            r["Valuation Confidence"] = ex["Valuation Confidence"]
            r["Valuation Rebind Decision"] = ex["Valuation Rebind Decision"]
            r["Valuation Synonym Match Count"] = ex["Valuation Synonym Match Count"]
            r["Valuation Source Count"] = ex["Valuation Source Count"]
            status = "FOUND"
            severity = "OK"
        else:
            r["Valuation Evidence Text"] = ""
            r["Valuation Source File"] = ""
            r["Valuation Source Zone"] = ""
            r["Valuation Confidence"] = 0
            r["Valuation Rebind Decision"] = ex["Valuation Rebind Decision"]
            r["Valuation Synonym Match Count"] = 0
            r["Valuation Source Count"] = ex["Valuation Source Count"]
            status = "MISSING"
            severity = "WARN"

        a = {
            "Status Lights": def_severity_lights(severity),
            "Filename": def_first(r, ["Filename", "File"]),
            "Ticker": def_first(r, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker"]),
            "Name": def_first(r, ["Name"]),
            "Old Valuation Method": old_val,
            "New Valuation Method": r.get("Valuation Method", ""),
            "Valuation Source File": r.get("Valuation Source File", ""),
            "Valuation Source Zone": r.get("Valuation Source Zone", ""),
            "Valuation Confidence": r.get("Valuation Confidence", ""),
            "Valuation Synonym Match Count": r.get("Valuation Synonym Match Count", ""),
            "Valuation Source Count": r.get("Valuation Source Count", ""),
            "Has Source Text": ex["Has Source Text"],
            "Has First Page Repaired Text": ex["Has First Page Repaired Text"],
            "Has Sentence Units": ex["Has Sentence Units"],
            "Valuation Evidence Text": r.get("Valuation Evidence Text", ""),
            "Status": status,
            "Severity": severity,
        }

        audit_rows.append(a)
        basic_out.append(r)

        if not found:
            missing_rows.append({
                **a,
                "Diagnosis": (
                    "Has related text but no valuation anchor."
                    if ex["Valuation Source Count"] > 0
                    else "No related Source Text / repaired first-page / sentence unit found."
                ),
                "Next Fix": (
                    "Need full-document body/table search."
                    if ex["Valuation Source Count"] > 0
                    else "Need M01/M02 repaired first-page source export connected."
                )
            })

    found_count = sum(1 for r in audit_rows if r["Status"] == "FOUND")
    missing_count = sum(1 for r in audit_rows if r["Status"] == "MISSING")
    with_source_text = sum(1 for r in audit_rows if str(r["Has Source Text"]).lower() == "true")
    with_firstpage = sum(1 for r in audit_rows if str(r["Has First Page Repaired Text"]).lower() == "true")
    with_sentence = sum(1 for r in audit_rows if str(r["Has Sentence Units"]).lower() == "true")
    support_errors = sum(1 for r in support_rows if r["Severity"] == "ERR")

    overview = [
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "BASE_SOURCE", "Value": str(base_src), "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "BASE_SOURCE_TYPE", "Value": base_src_type, "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "RELATED_FILES_SCANNED", "Value": len(files), "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "SOURCE_BANK_ROWS", "Value": len(source_bank_rows), "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "VALUATION_FOUND", "Value": found_count, "Severity": "OK"},
        {"Status Lights": def_severity_lights("WARN" if missing_count else "OK"), "Gate": "VALUATION_MISSING", "Value": missing_count, "Severity": "WARN" if missing_count else "OK"},
        {"Status Lights": def_severity_lights("OK"), "Gate": "WITH_SOURCE_TEXT", "Value": with_source_text, "Severity": "OK"},
        {"Status Lights": def_severity_lights("OK"), "Gate": "WITH_FIRSTPAGE_REPAIRED_TEXT", "Value": with_firstpage, "Severity": "OK"},
        {"Status Lights": def_severity_lights("OK"), "Gate": "WITH_SENTENCE_UNITS", "Value": with_sentence, "Severity": "OK"},
        {"Status Lights": def_severity_lights("OK" if support_errors == 0 else "ERR"), "Gate": "SUPPORT_ERRORS", "Value": support_errors, "Severity": "OK" if support_errors == 0 else "ERR"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "NO_STABLE_CANONICAL_MUTATION", "Value": True, "Severity": "OK"},
    ]

    result = {
        "version": VERSION,
        "generated_at": def_now(),
        "system_pass": len(base_rows) > 0 and support_errors == 0,
        "mode": "READ_ONLY_FIRSTPAGE_SOURCEBANK_VALUATION_REPAIR",
        "sources": {
            "base_source": str(base_src),
            "base_source_type": base_src_type,
            "canonical_dir": str(cfg["canonical_dir"]),
            "input_dir": str(cfg["input_dir"]),
            "run_dir": str(cfg["run_dir"]),
        },
        "counts": {
            "basic_rows": len(base_rows),
            "valuation_found": found_count,
            "valuation_missing": missing_count,
            "with_source_text": with_source_text,
            "with_firstpage": with_firstpage,
            "with_sentence_units": with_sentence,
            "related_files": len(files),
            "source_bank_rows": len(source_bank_rows),
            "support_errors": support_errors,
        },
        "outputs": {
            "html": str(cfg["out_html"]),
            "json": str(cfg["out_json"]),
            "basic_csv": str(cfg["out_basic_csv"]),
            "audit_csv": str(cfg["out_audit_csv"]),
            "source_bank_csv": str(cfg["out_source_bank_csv"]),
            "missing_diagnosis_csv": str(cfg["out_missing_diag_csv"]),
            "related_file_matrix_csv": str(cfg["out_file_matrix_csv"]),
            "support_csv": str(cfg["out_support_csv"]),
        },
        "rule_lock": [
            "Source Text is checked explicitly.",
            "Repaired first-page title/body/text is checked explicitly.",
            "Sentence units are checked explicitly.",
            "PDF first-page text layer fallback is attempted if pdfplumber is available.",
            "Valuation method uses report/source text only.",
            "YFinance does not overwrite valuation method.",
            "PBR hard gate remains active.",
            "No stable/canonical mutation."
        ],
    }

    def_write_csv(cfg["out_basic_csv"], basic_out)
    def_write_csv(cfg["out_audit_csv"], audit_rows)
    def_write_csv(cfg["out_source_bank_csv"], source_bank_rows)
    def_write_csv(cfg["out_miss_csv"], missing_rows)
    def_write_csv(cfg["out_file_matrix_csv"], file_matrix)
    def_write_csv(cfg["out_support_csv"], support_rows)
    def_write_json(cfg["out_json"], result)
    def_render_html(cfg["out_html"], result, overview, audit_rows, missing_rows, basic_out, source_bank_rows, file_matrix, support_rows)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise