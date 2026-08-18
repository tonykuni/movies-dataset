# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import html
import json
import re
import shutil
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_VALUATION_METHOD_SSOT_REBIND_V0592"


def def_config() -> dict:
    via_root = Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics")
    vrn_root = via_root / "module" / "VRN"
    supportive_dir = via_root / "module" / "supportive_module"
    run_root = vrn_root / "_vrn_operation_ui_runs"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = run_root / f"VRN_VALUATION_METHOD_SSOT_REBIND_V0592_INNER_{ts}"

    return {
        "via_root": via_root,
        "vrn_root": vrn_root,
        "supportive_dir": supportive_dir,
        "canonical_dir": vrn_root / "_vrn_canonical_active",
        "run_root": run_root,
        "run_dir": run_dir,
        "backup_dir": run_dir / "backup_before_v0592",
        "ssot_py": supportive_dir / "VIA_SSOT_Unified.py",
        "augmenter_ps1": supportive_dir / "VIA_SSOT_PanoramicAugmenter_v2.ps1",
        "out_html": run_dir / "VRN_Valuation_Method_SSOT_Rebind_v0592.html",
        "out_json": run_dir / "vrn_valuation_method_ssot_rebind_v0592.json",
        "out_basic_csv": run_dir / "vrn_basicinfo_valuation_rebind_v0592.csv",
        "out_audit_csv": run_dir / "vrn_valuation_method_audit_v0592.csv",
        "out_support_csv": run_dir / "vrn_supportive_patch_matrix_v0592.csv",
        "out_lexicon_json": run_dir / "VRN_Valuation_Method_Lexicon_v0592.json",
    }


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


def def_window(text: str, start: int, end: int, radius: int = 280) -> str:
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    return def_clean_text(text[a:b])


def def_find_latest(root: Path, patterns: list[str]) -> Path | None:
    hits = []
    for pat in patterns:
        try:
            hits.extend(root.rglob(pat))
        except Exception:
            pass
    hits = [p for p in hits if p.exists() and p.is_file()]
    if not hits:
        return None
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def def_valuation_lexicon() -> dict:
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
            r"以.{0,50}?\d+(\.\d+)?\s*[xX倍]?.{0,16}本益比.{0,40}?評價",
            r"基於.{0,55}?\d+(\.\d+)?\s*[xX倍]?.{0,20}(PER|PE|P/E|本益比)",
            r"評價區間.{0,50}\d+(\.\d+)?\s*[xX倍]\s*[-~–至]\s*\d+(\.\d+)?\s*[xX倍]?.{0,45}(PER|PE|P/E|本益比)",
            r"常態本益比.{0,40}\d+(\.\d+)?\s*[-~–至]\s*\d+(\.\d+)?\s*倍",
            r"給[予與].{0,30}\d+(\.\d+)?\s*倍",
        ],
        "PBR": [
            r"(?i)\bP\s*/?\s*B\b",
            r"(?i)\bPBR\b",
            r"(?i)\bPBV\b",
            r"(?i)\bprice[- ]?to[- ]?book\b",
            r"股價淨值比|市淨率|淨值比|帳面價值倍數",
            r"\d+(\.\d+)?\s*x\s*(P\s*/?\s*B|PB|PBR|PBV)",
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
            r"(?i)\bP\s*/?\s*S\b",
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
        "Residual Income": [
            r"(?i)\bresidual\s+income\b",
            r"(?i)\bRI\s+model\b",
            r"剩餘收益|剩餘利益|超額報酬模型",
        ],
    }


def def_ssot_block_py() -> str:
    lex = def_valuation_lexicon()
    return f'''
# [VIA:ANCHOR:VRN_VALUATION_METHOD_LEXICON_V0592:START]
# def VRN Valuation Method Lexicon v05.9.2
# def append-only; no deletion; no existing symbol mutation
VRN_VALUATION_METHOD_LEXICON_V0592 = {repr(lex)}

def vrn_get_valuation_method_lexicon_v0592():
    return VRN_VALUATION_METHOD_LEXICON_V0592
# [VIA:ANCHOR:VRN_VALUATION_METHOD_LEXICON_V0592:END]
'''.strip()


def def_ssot_block_ps1() -> str:
    return r'''
# [VIA:ANCHOR:VRN_VALUATION_METHOD_LEXICON_V0592:START]
# def VRN Valuation Method Lexicon v05.9.2
# def append-only; no deletion; no existing symbol mutation
function Get-VRNValuationMethodLexiconV0592 {
    [CmdletBinding()]
    param()
    return [ordered]@{
        PER = @("PER","P/E","PE","price-to-earnings","earnings multiple","本益比","預估本益比","目標本益比","合理本益比","常態本益比","歷史本益比","本益比評價","評價區間")
        PBR = @("PBR","P/B","PB","price-to-book","股價淨值比","市淨率","淨值比")
        EV_EBITDA = @("EV/EBITDA","EV EBITDA","EV-to-EBITDA","EBITDA multiple","企業價值倍數","EBITDA倍數")
        EV_EBIT = @("EV/EBIT","EV EBIT","EV-to-EBIT","EBIT multiple","EBIT倍數")
        DCF = @("DCF","discounted cash flow","WACC","terminal value","折現現金流","現金流折現","終值")
        SOTP = @("SOTP","sum of the parts","segment valuation","分部估值","分項加總")
        DDM = @("DDM","dividend discount model","dividend yield","股利折現","殖利率評價")
        PEG = @("PEG","price earnings growth","本益成長比")
        PS = @("P/S","price to sales","sales multiple","市銷率","營收倍數")
        NAV_RNAV = @("NAV","RNAV","net asset value","資產淨值","重估資產淨值")
        RESIDUAL_INCOME = @("residual income","RI model","剩餘收益")
    }
}
# [VIA:ANCHOR:VRN_VALUATION_METHOD_LEXICON_V0592:END]
'''.strip()


def def_backup(path: Path, backup_dir: Path) -> str:
    if not path.exists():
        return ""
    backup_dir.mkdir(parents=True, exist_ok=True)
    dst = backup_dir / f"{path.name}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(path, dst)
    return str(dst)


def def_append_once(path: Path, anchor: str, block: str) -> dict:
    if not path.exists():
        return {"Path": str(path), "Exists": False, "Action": "MISSING", "Status": "ERR", "Detail": "file missing"}

    txt = path.read_text(encoding="utf-8", errors="ignore")
    if anchor in txt:
        return {"Path": str(path), "Exists": True, "Action": "SKIP_EXISTS", "Status": "OK", "Detail": anchor}

    path.write_text(txt.rstrip() + "\n\n" + block.strip() + "\n", encoding="utf-8")
    return {"Path": str(path), "Exists": True, "Action": "APPENDED", "Status": "OK", "Detail": anchor}


def def_python_ast_ok(path: Path) -> tuple[bool, str]:
    try:
        ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        return True, "AST OK"
    except Exception as e:
        return False, str(e)


def def_patch_supportive(cfg: dict) -> list[dict]:
    rows = []
    items = [
        (cfg["ssot_py"], "VIA_SSOT_Unified.py", "# [VIA:ANCHOR:VRN_VALUATION_METHOD_LEXICON_V0592:START]", def_ssot_block_py(), "PY_AST"),
        (cfg["augmenter_ps1"], "VIA_SSOT_PanoramicAugmenter_v2.ps1", "# [VIA:ANCHOR:VRN_VALUATION_METHOD_LEXICON_V0592:START]", def_ssot_block_ps1(), "PS1_APPEND_ONLY"),
    ]

    for path, name, anchor, block, check in items:
        backup = def_backup(path, cfg["backup_dir"])
        res = def_append_once(path, anchor, block)
        ok = res["Status"] == "OK"
        detail = res["Detail"]

        if path.suffix.lower() == ".py" and path.exists():
            ast_ok, ast_detail = def_python_ast_ok(path)
            ok = ok and ast_ok
            detail += " | " + ast_detail

        if path.suffix.lower() == ".ps1" and path.exists():
            detail += " | PS1_PRESENT"

        rows.append({
            "Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST" if ok else "🔴 INPUT  🔴 DB  🔴 TRUST",
            "File": str(path),
            "Name": name,
            "Backup": backup,
            "Action": res["Action"],
            "Check": check,
            "Status": "OK" if ok else "ERR",
            "Detail": detail,
            "Severity": "OK" if ok else "ERR",
        })

    return rows


def def_resolve_basic_source(cfg: dict) -> tuple[Path, str]:
    latest = def_find_latest(cfg["run_root"], [
        "vrn_basicinfo_yfinance_field_fixed_preview_v0589.csv",
        "vrn_basicinfo_yfinance_input_ticker_v0588.csv",
        "vrn_basicinfo_yfinance_resolved_v0587.csv",
    ])
    if latest:
        return latest, "LATEST_OPERATION_PREVIEW"

    canonical = cfg["canonical_dir"] / "vrn_basicinfo_active.csv"
    return canonical, "CANONICAL_ACTIVE"


def def_collect_zones(row: dict) -> list[tuple[str, str]]:
    zones = []

    direct = def_first(row, ["Valuation Method", "Valuation", "valuation"])
    if direct:
        zones.append(("existing_valuation_method", direct))

    for col in ["Source Text", "source_text", "Method", "method"]:
        raw = def_first(row, [col])
        obj = def_safe_json_loads(raw)
        if obj:
            for k in ["valuation", "target_price", "rating", "analyst"]:
                if def_nonblank(obj.get(k)):
                    zones.append((f"{col}.{k}", str(obj.get(k))))
        elif raw:
            zones.append((col, raw))

    for col in ["Rating", "Target Price", "Filename Normalized", "Filename Tokens"]:
        raw = def_first(row, [col])
        if raw:
            zones.append((col, raw))

    return zones


def def_extract_valuation(row: dict, lex: dict) -> dict:
    zones = def_collect_zones(row)
    matches = []

    for zone, text0 in zones:
        text = def_clean_text(text0)
        if not text:
            continue

        for method, patterns in lex.items():
            for pat in patterns:
                try:
                    for m in re.finditer(pat, text, flags=re.MULTILINE):
                        ev = def_window(text, m.start(), m.end(), radius=280)
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
        }

    priority = {
        "existing_valuation_method": 100,
        "Source Text.valuation": 96,
        "source_text.valuation": 96,
        "Method.valuation": 92,
        "method.valuation": 92,
        "Source Text.target_price": 85,
        "source_text.target_price": 85,
        "Target Price": 78,
        "Source Text": 70,
        "source_text": 70,
        "Rating": 55,
        "Filename Normalized": 20,
        "Filename Tokens": 20,
    }

    def score(m: dict) -> int:
        ev = m["evidence"]
        s = priority.get(m["zone"], 50)
        if re.search(r"\d+(\.\d+)?\s*(x|X|倍)", ev):
            s += 14
        if re.search(r"目標價|target price|price target|TP|PT", ev, re.I):
            s += 8
        if re.search(r"評價|valuation|value|derive|based on|基於|以|給[予與]", ev, re.I):
            s += 8
        return s

    matches = sorted(matches, key=score, reverse=True)
    best = matches[0]

    methods = []
    for m in matches:
        if m["method"] not in methods:
            methods.append(m["method"])

    return {
        "Valuation Method": " + ".join(methods[:3]),
        "Valuation Evidence Text": best["evidence"],
        "Valuation Source Zone": best["zone"],
        "Valuation Confidence": min(0.99, round(score(best) / 130, 2)),
        "Valuation Rebind Decision": "REBIND_FROM_VALUATION_EVIDENCE",
        "Valuation Synonym Match Count": len(matches),
    }


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
    if any(k in c for k in ["filename", "file", "path", "source", "text", "evidence", "reason", "decision", "pattern", "zone", "detail", "backup"]):
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
            collapse = " collapse" if cls == "left" and len(str(val)) > 100 else ""
            cells.append(f"<td class='{cls}{collapse}'>{def_h(val)}</td>")
        trs.append(f"<tr class='{band}'>" + "".join(cells) + "</tr>")

    return "<table><thead><tr>" + th + "</tr></thead><tbody>" + "\n".join(trs) + "</tbody></table>"


def def_render_html(path: Path, result: dict, overview: list[dict], audit: list[dict], basic: list[dict], support: list[dict]) -> None:
    cards = [
        ("System Pass", result["system_pass"]),
        ("Basic Rows", result["counts"]["basic_rows"]),
        ("Found", result["counts"]["valuation_found"]),
        ("Missing", result["counts"]["valuation_missing"]),
        ("Rebound", result["counts"]["valuation_rebound"]),
        ("Support ERR", result["counts"]["support_errors"]),
        ("Methods", result["counts"]["lexicon_methods"]),
        ("Preview Only", True),
    ]
    card_html = "".join(f"<div class='stat'><div class='n'>{def_h(v)}</div><div class='l'>{def_h(k)}</div></div>" for k, v in cards)

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN Valuation Method SSOT Rebind v05.9.2</title>
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
td{{padding:6px 8px;border:1px solid var(--bd);vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:760px;line-height:1.35;text-align:center}}
td.left{{text-align:left;min-width:260px;max-width:860px}}
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
      <div class="h1"><span>VeritasReportNova</span> Valuation Method SSOT Rebind <span style="font-size:12px;color:var(--i3)">v05.9.2</span></div>
      <div class="sub">safe direct invocation · append-only SSOT · valuation evidence · no ScriptBlock variable</div>
    </div>
  </div>

  <div class="tabs">
    <button id="b_overview" class="on" onclick="tab('overview')">01 Overview</button>
    <button id="b_audit" onclick="tab('audit')">02 Valuation Audit</button>
    <button id="b_basic" onclick="tab('basic')">03 BasicInfo Preview</button>
    <button id="b_support" onclick="tab('support')">04 Supportive</button>
    <button id="b_json" onclick="tab('json')">05 JSON</button>
  </div>

  <div id="overview" class="page on"><div class="statgrid">{card_html}</div><div class="card"><h3>Overview Matrix</h3><div class="tablewrap">{def_table(overview)}</div></div></div>
  <div id="audit" class="page"><div class="card"><h3>Valuation Audit</h3><div class="tablewrap">{def_table(audit)}</div></div></div>
  <div id="basic" class="page"><div class="card"><h3>BasicInfo Preview</h3><div class="tablewrap">{def_table(basic)}</div></div></div>
  <div id="support" class="page"><div class="card"><h3>Supportive Patch Matrix</h3><div class="tablewrap">{def_table(support)}</div></div></div>
  <div id="json" class="page"><div class="card"><h3>JSON</h3><pre>{def_h(json.dumps(result, ensure_ascii=False, indent=2))}</pre></div></div>
</div>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    cfg = def_config()
    cfg["run_dir"].mkdir(parents=True, exist_ok=True)
    cfg["backup_dir"].mkdir(parents=True, exist_ok=True)

    support = def_patch_supportive(cfg)

    lex = def_valuation_lexicon()
    def_write_json(cfg["out_lexicon_json"], lex)

    basic_src, src_type = def_resolve_basic_source(cfg)
    rows = def_read_csv(basic_src)

    audit = []
    basic_out = []

    for row in rows:
        r = dict(row)
        old_val = def_first(r, ["Valuation Method", "Valuation"])
        ex = def_extract_valuation(r, lex)

        if def_nonblank(ex["Valuation Method"]):
            r["Valuation Method"] = ex["Valuation Method"]
            r["Valuation Evidence Text"] = ex["Valuation Evidence Text"]
            r["Valuation Source Zone"] = ex["Valuation Source Zone"]
            r["Valuation Confidence"] = ex["Valuation Confidence"]
            r["Valuation Rebind Decision"] = ex["Valuation Rebind Decision"]
            r["Valuation Synonym Match Count"] = ex["Valuation Synonym Match Count"]
            status = "FOUND"
            severity = "OK"
            lights = "🟢 INPUT  🟢 DB  🟢 TRUST"
        else:
            r["Valuation Evidence Text"] = ""
            r["Valuation Source Zone"] = ""
            r["Valuation Confidence"] = 0
            r["Valuation Rebind Decision"] = "NO_VALUATION_METHOD_FOUND"
            r["Valuation Synonym Match Count"] = 0
            status = "MISSING"
            severity = "WARN"
            lights = "🟢 INPUT  🟡 DB  🟡 TRUST"

        audit.append({
            "Status Lights": lights,
            "Filename": def_first(r, ["Filename", "File"]),
            "Ticker": def_first(r, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker"]),
            "Name": def_first(r, ["Name"]),
            "Old Valuation Method": old_val,
            "New Valuation Method": r.get("Valuation Method", ""),
            "Valuation Source Zone": r.get("Valuation Source Zone", ""),
            "Valuation Confidence": r.get("Valuation Confidence", ""),
            "Valuation Synonym Match Count": r.get("Valuation Synonym Match Count", ""),
            "Valuation Evidence Text": r.get("Valuation Evidence Text", ""),
            "Status": status,
            "Severity": severity,
        })

        basic_out.append(r)

    found = sum(1 for x in audit if x["Status"] == "FOUND")
    missing = sum(1 for x in audit if x["Status"] == "MISSING")
    rebound = sum(1 for x in audit if def_nonblank(x["New Valuation Method"]) and x["New Valuation Method"] != x["Old Valuation Method"])
    support_errors = sum(1 for x in support if x["Severity"] == "ERR")

    overview = [
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "BASIC_SOURCE", "Value": str(basic_src), "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "BASIC_SOURCE_TYPE", "Value": src_type, "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "SUPPORTIVE_ERRORS", "Value": support_errors, "Severity": "OK" if support_errors == 0 else "ERR"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "VALUATION_FOUND", "Value": found, "Severity": "OK"},
        {"Status Lights": "🟢 INPUT  🟡 DB  🟡 TRUST" if missing else "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "VALUATION_MISSING", "Value": missing, "Severity": "WARN" if missing else "OK"},
        {"Status Lights": "🟢 INPUT  🟢 DB  🟢 TRUST", "Gate": "NO_STABLE_CANONICAL_MUTATION", "Value": True, "Severity": "OK"},
    ]

    result = {
        "version": VERSION,
        "generated_at": def_now(),
        "system_pass": len(rows) > 0 and support_errors == 0,
        "mode": "SAFE_DIRECT_AIO_APPEND_ONLY_SSOT_AND_READ_ONLY_VALUATION_REBIND",
        "sources": {
            "basic_source": str(basic_src),
            "basic_source_type": src_type,
            "ssot_py": str(cfg["ssot_py"]),
            "augmenter_ps1": str(cfg["augmenter_ps1"]),
            "backup_dir": str(cfg["backup_dir"]),
        },
        "counts": {
            "basic_rows": len(rows),
            "valuation_found": found,
            "valuation_missing": missing,
            "valuation_rebound": rebound,
            "support_errors": support_errors,
            "lexicon_methods": len(lex),
        },
        "outputs": {
            "html": str(cfg["out_html"]),
            "json": str(cfg["out_json"]),
            "basic_csv": str(cfg["out_basic_csv"]),
            "audit_csv": str(cfg["out_audit_csv"]),
            "support_csv": str(cfg["out_support_csv"]),
            "lexicon_json": str(cfg["out_lexicon_json"]),
        },
        "rule_lock": [
            "No $__scriptblock variable invocation",
            "No Bash heredoc in PowerShell",
            "VIA_SSOT_Unified.py append-only",
            "VIA_SSOT_PanoramicAugmenter_v2.ps1 append-only",
            "No stable/canonical mutation",
            "Valuation Method comes from report/source text only",
            "YFinance never overwrites valuation method",
            "Evidence text and source zone are preserved",
        ],
    }

    def_write_csv(cfg["out_basic_csv"], basic_out)
    def_write_csv(cfg["out_audit_csv"], audit)
    def_write_csv(cfg["out_support_csv"], support)
    def_write_json(cfg["out_json"], result)
    def_render_html(cfg["out_html"], result, overview, audit, basic_out, support)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise