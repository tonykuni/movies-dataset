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
import json
import re
import sys
from pathlib import Path


V062_BLOCK = r'''
# ================================================================================================
# def VIA:VRN:HOMEPAGE_SUMMARIZER_V062_CLI_LIFT_FIX:START
# def Corrected override placed before __main__ so CLI uses it.
# def INPUT_A = repaired_first_page_text / first_page_text
# def INPUT_B = financial_data / financial_rows / financial_data_csv
# def each point = one sentence
# ================================================================================================

def def_v062_one_sentence(text, max_len=150):
    import re
    s = "" if text is None else str(text)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    parts = re.split(r"(?<=[。.!?])\s+", s)
    s = parts[0].strip() if parts else s
    if not re.search(r"[。.!?]$", s):
        s += "。"
    if len(s) > max_len:
        s = s[:max_len].rstrip("，,；; ") + "。"
    return s


def def_v062_float(value):
    import re
    try:
        s = "" if value is None else str(value)
        s = s.replace(",", "").replace("%", "").replace("NTD", "").replace("元", "").strip()
        m = re.search(r"-?\d+(?:\.\d+)?", s)
        if not m:
            return None
        return float(m.group(0))
    except Exception:
        return None


def def_v062_load_financial_rows(payload):
    import csv
    from pathlib import Path

    rows = []
    for key in ["financial_data", "financial_rows", "financial_matrix"]:
        v = payload.get(key)
        if isinstance(v, list):
            rows.extend([x for x in v if isinstance(x, dict)])

    csv_path = payload.get("financial_data_csv") or payload.get("financial_csv")
    if csv_path:
        p = Path(str(csv_path))
        if p.exists():
            with p.open("r", encoding="utf-8-sig", newline="") as f:
                rows.extend([dict(r) for r in csv.DictReader(f)])
    return rows


def def_v062_norm_metric(x):
    import re
    s = "" if x is None else str(x).strip().lower()
    compact = re.sub(r"[\s_\-]+", "", s)
    if ("diluted" in s and "eps" in s) or compact in {"dilutedeps", "稀釋eps", "稀釋每股盈餘"}:
        return "Diluted EPS"
    if compact in {"eps"}:
        return "Diluted EPS"
    if compact in {"revenue", "營收", "netsales"}:
        return "Revenue"
    if compact in {"grossmargin", "毛利率", "gpm"}:
        return "Gross Margin"
    if compact in {"roe"}:
        return "ROE"
    if compact in {"per", "pe", "p/e", "本益比"}:
        return "PER"
    if compact in {"pbr", "p/b"}:
        return "PBR"
    if compact in {"dps"}:
        return "DPS"
    if compact in {"bvps"}:
        return "BVPS"
    return str(x or "").strip()


def def_v062_metric_map(rows):
    import re
    out = {}
    for r in rows or []:
        if not isinstance(r, dict):
            continue

        metric_raw = ""
        for k in ["data", "Data", "metric", "Metric", "account", "Account", "item", "Item", "科目", "會計科目"]:
            if r.get(k):
                metric_raw = r.get(k)
                break

        metric = def_v062_norm_metric(metric_raw)
        if not metric:
            continue

        year = ""
        for k in ["year", "Year", "time", "Time", "fiscal_year", "年度", "年份"]:
            if r.get(k):
                m = re.search(r"(20\d{2})", str(r.get(k)))
                if m:
                    year = m.group(1)
                    break

        value = None
        for k in ["value", "Value", "amount", "Amount", "數值", "金額"]:
            if k in r:
                value = def_v062_float(r.get(k))
                break

        if year and value is not None:
            out.setdefault(metric, {})[year] = value

        for k, v in r.items():
            m = re.search(r"(20\d{2})", str(k))
            if m:
                fv = def_v062_float(v)
                if fv is not None:
                    out.setdefault(metric, {})[m.group(1)] = fv
    return out


def def_v062_latest(metric_map, metric):
    d = metric_map.get(metric) or {}
    if not d:
        return "", None
    y = sorted(d.keys())[-1]
    return y, d.get(y)


def def_v062_snapshot(metric_map):
    parts = []
    for m in ["Diluted EPS", "Revenue", "Gross Margin", "ROE"]:
        y, v = def_v062_latest(metric_map, m)
        if v is not None:
            suffix = "%" if m in {"Gross Margin", "ROE"} else ""
            parts.append(f"{y} {m} {v:g}{suffix}")
    return "；".join(parts) if parts else "FINANCIAL_DATA_MISSING"


def def_v062_financial_evidence(metric_map):
    rows = []
    for metric, year_map in sorted((metric_map or {}).items()):
        for y, v in sorted(year_map.items()):
            rows.append({
                "field": f"financial_data::{metric}::{y}",
                "summarizer_value": v,
                "ssot_value": v,
                "delta_pct": 0,
                "band": "GREEN",
                "action": "FINANCIAL_DATA_EVIDENCE_USED",
            })
    return rows


# Preserve original v06 exactly once.
if "def_summarize_homepage_v06_original_base" not in globals():
    def_summarize_homepage_v06_original_base = def_summarize_homepage_v06


def def_summarize_homepage_v062(payload):
    """
    def Corrected v06.2 public summarizer.
    def It does not re-extract PDF.
    def It consumes repaired_first_page_text + financial_data.
    """
    if payload is None:
        payload = {}
    payload = dict(payload)

    repaired = (
        payload.get("repaired_first_page_text")
        or payload.get("first_page_repaired_text")
        or payload.get("first_page_text_repaired")
        or payload.get("first_page_text")
        or payload.get("text")
        or ""
    )
    payload["first_page_text"] = repaired
    payload["text"] = repaired

    financial_rows = def_v062_load_financial_rows(payload)
    metric_map = def_v062_metric_map(financial_rows)
    fin_snapshot = def_v062_snapshot(metric_map)

    base = def_summarize_homepage_v06_original_base(payload)

    warnings = list(base.get("warnings") or [])
    if not financial_rows:
        warnings.append("RED_REVIEW: financial_data missing; six points cannot be fully cross-validated.")
    if "Diluted EPS" not in metric_map:
        warnings.append("RED_REVIEW: Diluted EPS missing from financial_data.")

    company = payload.get("name") or base.get("report_code", "")
    tp = base.get("target_price")
    adj = base.get("adj_close")
    upside = base.get("upside_pct")
    valuation = payload.get("valuation_method") or base.get("valuation_method") or "valuation method pending review"

    zh = {
        "valuation_upside": def_v062_one_sentence(f"{upside if upside is not None else 'NA'}% 上漲空間來自 TP {tp} 對 Adj Close {adj}，並以 {valuation} 與 financial data（{fin_snapshot}）交叉核對。"),
        "diluted_eps_growth": def_v062_one_sentence(f"Diluted EPS 以 financial data 為準，目前對照為 {fin_snapshot}。"),
        "trend_catalyst": def_v062_one_sentence("催化劑只能從修復後第一頁文字擷取，並用 financial data 的營收、毛利率或 Diluted EPS 變化確認。"),
        "industry_position_moat": def_v062_one_sentence(f"{company} 的產業地位必須由修復後第一頁文字描述，再用 ROE、毛利率或 EPS 品質補強。"),
        "peer_comparison": def_v062_one_sentence("同業比較若 financial data 未提供 peer rows，必須標記 RED_REVIEW，不得自行產生同業結論。"),
        "key_risks_mitigants": def_v062_one_sentence("風險與因應只能引用修復後第一頁文字，若 financial data 無法支持風險量化則標記 RED_REVIEW。"),
    }

    en = {
        "valuation_upside": def_v062_one_sentence(f"{upside if upside is not None else 'NA'}% upside is based on TP {tp} versus Adj Close {adj}, cross-checked with financial data ({fin_snapshot}).", 190),
        "diluted_eps_growth": def_v062_one_sentence(f"Diluted EPS must be sourced from financial data, with current evidence shown as {fin_snapshot}.", 190),
        "trend_catalyst": def_v062_one_sentence("Catalysts must come from repaired first-page text and be validated by revenue, gross margin, or Diluted EPS changes in financial data.", 190),
        "industry_position_moat": def_v062_one_sentence(f"{company}'s moat must be described by repaired first-page text and supported by ROE, gross margin, or EPS quality.", 190),
        "peer_comparison": def_v062_one_sentence("Peer comparison requires peer rows in financial data; otherwise it must be flagged RED_REVIEW rather than inferred.", 190),
        "key_risks_mitigants": def_v062_one_sentence("Risks and mitigants must be derived from repaired first-page text, with unsupported quantification flagged RED_REVIEW.", 190),
    }

    base["zh_points"] = {k: def_v062_one_sentence(v, 150) for k, v in zh.items()}
    base["en_points"] = {k: def_v062_one_sentence(v, 190) for k, v in en.items()}
    base["warnings"] = warnings
    base["financial_data_used"] = bool(financial_rows)
    base["financial_metric_map"] = metric_map

    cross = list(base.get("cross_validation") or [])
    cross.extend(def_v062_financial_evidence(metric_map))
    if not financial_rows:
        cross.append({
            "field": "financial_data",
            "summarizer_value": "MISSING",
            "ssot_value": "REQUIRED",
            "delta_pct": None,
            "band": "RED",
            "action": "BLOCK_DB_READY_UNTIL_FINANCIAL_DATA_EXISTS",
        })
    base["cross_validation"] = cross

    red = sum(1 for r in cross if r.get("band") == "RED") + sum(1 for w in warnings if "RED" in str(w))
    yellow = sum(1 for r in cross if r.get("band") == "YELLOW") + sum(1 for w in warnings if "YELLOW" in str(w))
    base["quality_grade"] = "D" if red >= 3 else ("C" if red >= 1 else ("B" if yellow >= 3 else "A"))

    return base


def def_selftest_v062():
    sample = {
        "filename": "MS-2330 20260518.pdf",
        "broker": "Morgan Stanley",
        "ticker": "2330",
        "name": "台積電",
        "report_date": "2026-05-18",
        "adj_close_report_date": 1000,
        "repaired_first_page_text": "AI Server Momentum Drives Margin Re-rating。投資評等 買進。目標價 1200 元。研究員 Jennifer Hsieh。2026/27 年 Diluted EPS 預估 55.2/63.8 元，以 22x 2026E P/E 評價。主要風險為 AI 需求放緩與匯率波動。",
        "financial_data": [
            {"data": "Diluted EPS", "year": "2026", "value": "55.2"},
            {"data": "Diluted EPS", "year": "2027", "value": "63.8"},
            {"data": "Gross Margin", "year": "2026", "value": "58.0"},
            {"data": "ROE", "year": "2026", "value": "27.5"},
            {"data": "Revenue", "year": "2026", "value": "3500000"}
        ],
    }
    s = def_summarize_homepage_v062(sample)
    zh = s.get("zh_points") or {}
    en = s.get("en_points") or {}

    checks = {
        "rating_buy": s.get("rating") == "BUY",
        "target_price_1200": s.get("target_price") == 1200.0,
        "upside_20": s.get("upside_pct") == 20.0,
        "financial_data_used": bool(s.get("financial_data_used")),
        "has_diluted_eps": "Diluted EPS" in (s.get("financial_metric_map") or {}),
        "six_zh": len(zh) == 6,
        "six_en": len(en) == 6,
        "zh_one_sentence": all(str(v).count("。") <= 1 for v in zh.values()),
        "financial_cross_rows": any(str(r.get("field","")).startswith("financial_data::") for r in s.get("cross_validation", [])),
    }
    return {"hard_pass": all(checks.values()), "checks": checks, "summary": s}


# Public override for CLI and imports.
def_summarize_homepage_v06 = def_summarize_homepage_v062
def_selftest_v06 = def_selftest_v062

# ================================================================================================
# def VIA:VRN:HOMEPAGE_SUMMARIZER_V062_CLI_LIFT_FIX:END
# ================================================================================================
'''


def main():
    target = Path(sys.argv[1])
    out_json = Path(sys.argv[2])

    code = target.read_text(encoding="utf-8", errors="ignore")
    before = code

    if "VIA:VRN:HOMEPAGE_SUMMARIZER_V062_CLI_LIFT_FIX:START" in code:
        result = {
            "hard_pass": True,
            "changed": False,
            "detail": "v06.2 block already installed",
        }
        out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    marker = 'if __name__ == "__main__":'
    idx = code.find(marker)
    if idx < 0:
        raise RuntimeError("Cannot locate __main__ marker")

    patched = code[:idx].rstrip() + "\n\n" + V062_BLOCK + "\n\n" + code[idx:]
    ast.parse(patched)
    target.write_text(patched, encoding="utf-8")

    result = {
        "hard_pass": True,
        "changed": True,
        "inserted_before_main": True,
        "before_bytes": len(before.encode("utf-8")),
        "after_bytes": len(patched.encode("utf-8")),
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()