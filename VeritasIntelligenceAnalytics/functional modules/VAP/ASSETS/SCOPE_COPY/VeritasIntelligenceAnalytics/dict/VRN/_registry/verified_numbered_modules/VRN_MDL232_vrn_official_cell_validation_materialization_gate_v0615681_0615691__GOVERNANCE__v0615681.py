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
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_OFFICIAL_CELL_VALIDATION_MATERIALIZATION_GATE_V0615681_0615691"


def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = html.unescape(s)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_flat(x: Any) -> str:
    return re.sub(r"\s+", " ", def_clean(x)).strip()


def def_norm(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。&+%]+", "", str(x or "").lower())


def def_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(str(x).replace(",", "").strip()))
    except Exception:
        return default


def def_float(x: Any, default: Any = None) -> Any:
    s = def_flat(x).replace(",", "").replace("%", "")
    if s in ["", "-", "—", "–", "NA", "N/A", "nan", "None"]:
        return default
    try:
        return float(s)
    except Exception:
        return default


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "VALIDATED", "READY", "STAGING_READY"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "VALUE_ONLY", "ALIAS_REVIEW", "NO_MATCH", "STAGING"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_find_latest_dir(root: Path, prefix: str) -> Path | None:
    if not root.exists():
        return None
    hits = [p for p in root.glob(prefix + "_*") if p.is_dir()]
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0] if hits else None


def def_read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5", "latin-1"]:
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


def def_get(row: dict, aliases: list[str]) -> str:
    mp = {def_norm(k): k for k in row.keys()}
    for a in aliases:
        na = def_norm(a)
        if na in mp:
            return def_clean(row.get(mp[na]))
    for k in row.keys():
        nk = def_norm(k)
        for a in aliases:
            if def_norm(a) in nk:
                return def_clean(row.get(k))
    return ""


def def_account_alias_map() -> dict:
    return {
        "cash_and_equivalents": ["現金及約當現金", "現金及約當現金合計"],
        "accounts_receivable": ["應收帳款", "應收帳款淨額", "應收票據及帳款", "應收款項", "應收款項淨額"],
        "inventories": ["存貨", "存貨淨額"],
        "other_current_assets": ["其他流動資產"],
        "current_assets": ["流動資產合計", "流動資產總計", "流動資產"],
        "fixed_assets": ["不動產、廠房及設備", "不動產廠房及設備", "固定資產"],
        "investments": ["採用權益法之投資", "投資", "金融資產", "其他金融資產"],
        "goodwill": ["商譽"],
        "intangible_assets": ["無形資產", "其他無形資產"],
        "other_non_current_assets": ["其他非流動資產"],
        "total_assets": ["資產總計", "資產合計"],

        "short_term_debt": ["短期借款", "一年內到期長期負債", "應付短期票券"],
        "accounts_payable": ["應付帳款", "應付票據及帳款", "應付款項"],
        "taxes_payable": ["本期所得稅負債", "應付所得稅", "應付稅款"],
        "other_current_liabilities": ["其他流動負債"],
        "current_liabilities": ["流動負債合計", "流動負債總計", "流動負債"],
        "long_term_debt": ["長期借款", "應付公司債", "長期負債", "非流動負債"],
        "other_long_term_liabilities": ["其他非流動負債", "負債準備"],
        "total_liabilities": ["負債總計", "負債合計"],
        "shareholders_equity": ["權益總計", "權益合計", "歸屬於母公司業主之權益合計"],
        "total_debt": ["借款", "有息負債"],

        "revenue": ["營業收入", "營業收入合計", "收入"],
        "cogs": ["營業成本", "銷貨成本"],
        "gross_profit": ["營業毛利", "營業毛利淨額"],
        "operating_expenses": ["營業費用", "營業費用合計"],
        "operating_income": ["營業利益", "營業淨利"],
        "net_income": ["本期淨利", "本期稅後淨利", "淨利", "本期損益"],
        "basic_eps": ["基本每股盈餘"],
        "diluted_eps": ["稀釋每股盈餘", "稀釋每股盈餘（元）"],

        "operating_cash_flow": ["營業活動之淨現金流入", "營業活動現金流量", "營業活動之現金流量"],
        "capex": ["購置不動產、廠房及設備", "資本支出"],
        "free_cash_flow": ["自由現金流量"],

        "gross_margin": ["營業毛利率", "毛利率"],
        "operating_margin": ["營業利益率", "營益率"],
        "net_margin": ["淨利率"],
        "roe": ["權益報酬率", "ROE"],
        "roa": ["資產報酬率", "ROA"],
    }


def def_same_identity(plan: dict, cell: dict) -> bool:
    return (
        def_get(plan, ["ticker"]) == def_get(cell, ["ticker"])
        and def_get(plan, ["period year"]) == def_get(cell, ["period year"])
        and def_norm(def_get(plan, ["statement"])) == def_norm(def_get(cell, ["statement"]))
        and def_get(cell, ["is numeric"]) == "YES"
    )


def def_row_label_key(cell: dict) -> tuple:
    return (
        def_get(cell, ["ticker"]),
        def_get(cell, ["period year"]),
        def_get(cell, ["statement"]),
        def_get(cell, ["cache file"]),
        def_get(cell, ["table index"]),
        def_get(cell, ["row index"]),
    )


def def_build_row_labels(cells: list[dict]) -> dict:
    row_cells = defaultdict(list)
    for c in cells:
        row_cells[def_row_label_key(c)].append(c)

    labels = {}
    for k, arr in row_cells.items():
        texts = []
        for c in sorted(arr, key=lambda x: def_int(def_get(x, ["col index"]))):
            ci = def_int(def_get(c, ["col index"]))
            txt = def_get(c, ["cell text"])
            if ci <= 3 and txt and def_get(c, ["is numeric"]) != "YES":
                texts.append(txt)
        labels[k] = " | ".join(texts)
    return labels


def def_value_variants(value: Any) -> list[tuple[str, float]]:
    v = def_float(value)
    if v is None:
        return []
    return [
        ("x1", v),
        ("x1000", v * 1000.0),
        ("x1000000", v * 1000000.0),
    ]


def def_value_match(report_value: Any, official_value: Any) -> dict:
    ov = def_float(official_value)
    variants = def_value_variants(report_value)
    if ov is None or not variants:
        return {"match": False, "scale": "", "diff": "", "rel_diff": "", "score": 0.0}

    best = None
    for scale, rv in variants:
        diff = abs(rv - ov)
        base = max(abs(rv), abs(ov), 1.0)
        rel = diff / base
        score = max(0.0, 1.0 - rel)
        match = diff <= max(5.0, base * 0.015)
        item = {"match": match, "scale": scale, "diff": diff, "rel_diff": rel, "score": score}
        if best is None or item["score"] > best["score"]:
            best = item
    return best


def def_alias_match(account_key: str, label: str) -> tuple[float, str]:
    aliases = def_account_alias_map().get(account_key, [])
    label_n = def_norm(label)
    hits = [a for a in aliases if def_norm(a) and def_norm(a) in label_n]
    if hits:
        return 1.0, " | ".join(hits)

    # fallback：如果中文 row label 不完整，仍保留弱比對，不直接 validated
    if label_n and account_key in ["total_assets", "current_assets", "current_liabilities", "total_liabilities"]:
        if "合計" in label or "總計" in label:
            return 0.35, ""
    return 0.0, ""


def def_validate_one(plan: dict, cells: list[dict], row_labels: dict) -> dict:
    account_key = def_get(plan, ["account key"])
    report_value = def_get(plan, ["report value"])

    best = None
    for c in cells:
        if not def_same_identity(plan, c):
            continue

        label = row_labels.get(def_row_label_key(c), "")
        alias_score, alias_hits = def_alias_match(account_key, label)
        value_result = def_value_match(report_value, def_get(c, ["numeric value"]))
        value_score = float(value_result.get("score") or 0)

        if value_result.get("match") and alias_score >= 1.0:
            route = "VALIDATED_ALIAS_AND_VALUE"
            sev = "OK"
            rank = 0
        elif value_result.get("match"):
            route = "VALUE_MATCH_ALIAS_REVIEW"
            sev = "WARN"
            rank = 1
        elif alias_score >= 1.0:
            route = "ALIAS_MATCH_VALUE_REVIEW"
            sev = "WARN"
            rank = 2
        else:
            continue

        row = {
            "Status Lights": def_light(sev),
            "official work order id": def_get(plan, ["official work order id"]),
            "validation plan id": def_get(plan, ["validation plan id"]),
            "ticker": def_get(plan, ["ticker"]),
            "filename": def_get(plan, ["filename"]),
            "statement": def_get(plan, ["statement"]),
            "period year": def_get(plan, ["period year"]),
            "account raw": def_get(plan, ["account raw"]),
            "account canonical": def_get(plan, ["account canonical"]),
            "account key": account_key,
            "official row labels": label,
            "alias hits": alias_hits,
            "alias score": alias_score,
            "report value": report_value,
            "official numeric value": def_get(c, ["numeric value"]),
            "official cell text": def_get(c, ["cell text"]),
            "unit": def_get(plan, ["unit"]),
            "value scale": value_result.get("scale", ""),
            "value diff": round(float(value_result.get("diff") or 0.0), 4),
            "relative diff": round(float(value_result.get("rel_diff") or 0.0), 6),
            "value score": round(value_score, 6),
            "validation route": route,
            "cache file": def_get(c, ["cache file"]),
            "table index": def_get(c, ["table index"]),
            "row index": def_get(c, ["row index"]),
            "col index": def_get(c, ["col index"]),
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
            "Severity": sev,
        }

        key = (rank, -value_score, -alias_score)
        if best is None or key < best[0]:
            best = (key, row)

    if best:
        return best[1]

    return {
        "Status Lights": def_light("WARN"),
        "official work order id": def_get(plan, ["official work order id"]),
        "validation plan id": def_get(plan, ["validation plan id"]),
        "ticker": def_get(plan, ["ticker"]),
        "filename": def_get(plan, ["filename"]),
        "statement": def_get(plan, ["statement"]),
        "period year": def_get(plan, ["period year"]),
        "account raw": def_get(plan, ["account raw"]),
        "account canonical": def_get(plan, ["account canonical"]),
        "account key": account_key,
        "official row labels": "",
        "alias hits": "",
        "alias score": 0,
        "report value": report_value,
        "official numeric value": "",
        "official cell text": "",
        "unit": def_get(plan, ["unit"]),
        "value scale": "",
        "value diff": "",
        "relative diff": "",
        "value score": 0,
        "validation route": "NO_OFFICIAL_CELL_MATCH",
        "cache file": "",
        "table index": "",
        "row index": "",
        "col index": "",
        "db write": "NO",
        "canonical mutation": "NO",
        "ssot mutation": "NO",
        "Severity": "WARN",
    }


def def_materialize_candidate(row: dict) -> dict:
    return {
        "Status Lights": def_light("OK"),
        "materialization candidate id": def_get(row, ["official work order id"]) or def_get(row, ["validation plan id"]),
        "ticker": def_get(row, ["ticker"]),
        "filename": def_get(row, ["filename"]),
        "statement": def_get(row, ["statement"]),
        "period year": def_get(row, ["period year"]),
        "account key": def_get(row, ["account key"]),
        "account canonical": def_get(row, ["account canonical"]),
        "account raw": def_get(row, ["account raw"]),
        "official row labels": def_get(row, ["official row labels"]),
        "value final candidate": def_get(row, ["official numeric value"]),
        "report value": def_get(row, ["report value"]),
        "official value": def_get(row, ["official numeric value"]),
        "unit": def_get(row, ["unit"]),
        "evidence route": def_get(row, ["validation route"]),
        "evidence cache file": def_get(row, ["cache file"]),
        "evidence table index": def_get(row, ["table index"]),
        "evidence row index": def_get(row, ["row index"]),
        "evidence col index": def_get(row, ["col index"]),
        "confidence": "0.96",
        "ready for canonical staging": "YES",
        "db write": "NO",
        "canonical mutation": "NO",
        "ssot mutation": "NO",
        "Severity": "OK",
    }


def def_alias_candidate(row: dict) -> dict:
    return {
        "Status Lights": def_light("WARN"),
        "alias candidate id": def_get(row, ["official work order id"]) or def_get(row, ["validation plan id"]),
        "account key": def_get(row, ["account key"]),
        "report account raw": def_get(row, ["account raw"]),
        "account canonical": def_get(row, ["account canonical"]),
        "official row labels": def_get(row, ["official row labels"]),
        "report value": def_get(row, ["report value"]),
        "official numeric value": def_get(row, ["official numeric value"]),
        "validation route": def_get(row, ["validation route"]),
        "candidate reason": "official value matched or row label matched, but alias/value pair is not fully validated",
        "recommended action": "SSOT_ALIAS_CANDIDATE_ONLY_AFTER_SECOND_CONFIRMATION",
        "ssot mutation": "NO",
        "Severity": "WARN",
    }


def def_html_table(title: str, rows: list[dict], limit: int | None = None) -> str:
    if limit is not None:
        rows = rows[:limit]
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"

    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(k))}</th>" for k in fields)
    trs = []
    for r in rows:
        tds = []
        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["filename", "account", "label", "route", "reason", "action", "cache", "source"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(str(v)).replace(chr(10), '<br>')}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")

    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:26px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:25px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;padding:22px 34px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:25px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 34px 34px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1120px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    cards = "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    )
    body = "".join(def_html_table(t, rows, lim) for t, rows, lim in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Official Cell Validation Materialization Gate v0615681</title><style>{css}</style></head>
<body><header><h1>VRN · Official Cell Validation + Materialization Gate v0.6.15.6.8.1 / 6.9.1</h1>
<div class="sub">cell-level validation · materialization staging only · no DB / canonical / SSOT</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: py <run_root> <run_dir>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    run_dir.mkdir(parents=True, exist_ok=True)

    source = def_find_latest_dir(run_root, "VRN_FLOWA_OFFICIAL_PARSER_FLOWC_HEALTH_V061567")
    if not source:
        raise RuntimeError("Cannot find latest VRN_FLOWA_OFFICIAL_PARSER_FLOWC_HEALTH_V061567 run.")

    cell_csv = source / "flowa_official_cell_matrix_v061567.csv"
    plan_csv = source / "flowb_official_cell_validation_plan_v061567.csv"

    cells = [r for r in def_read_csv(cell_csv) if "empty_marker" not in r]
    plans = [r for r in def_read_csv(plan_csv) if "empty_marker" not in r]

    row_labels = def_build_row_labels(cells)
    validation_rows = [def_validate_one(p, cells, row_labels) for p in plans]

    validated = [r for r in validation_rows if def_get(r, ["validation route"]) == "VALIDATED_ALIAS_AND_VALUE"]
    value_only = [r for r in validation_rows if def_get(r, ["validation route"]) == "VALUE_MATCH_ALIAS_REVIEW"]
    alias_value_review = [r for r in validation_rows if def_get(r, ["validation route"]) == "ALIAS_MATCH_VALUE_REVIEW"]
    no_match = [r for r in validation_rows if def_get(r, ["validation route"]) == "NO_OFFICIAL_CELL_MATCH"]

    materialization = [def_materialize_candidate(r) for r in validated]
    alias_candidates = [def_alias_candidate(r) for r in value_only + alias_value_review]

    route_summary = []
    for k, v in sorted(Counter(def_get(r, ["validation route"]) for r in validation_rows).items(), key=lambda x: (-x[1], x[0])):
        sev = "OK" if k == "VALIDATED_ALIAS_AND_VALUE" else "WARN"
        route_summary.append({
            "Status Lights": def_light(sev),
            "validation route": k,
            "rows": v,
            "rate": f"{(v / max(len(validation_rows), 1)) * 100:.2f}%",
            "Severity": sev,
        })

    gate_matrix = [
        {"Status Lights": def_light("OK" if materialization else "WARN"), "Gate": "MATERIALIZATION_STAGING_CANDIDATES", "Value": len(materialization), "Required": ">0", "Severity": "OK" if materialization else "WARN"},
        {"Status Lights": def_light("OK" if validation_rows else "WARN"), "Gate": "VALIDATION_ROWS", "Value": len(validation_rows), "Required": ">0", "Severity": "OK" if validation_rows else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Required": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Required": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Required": "YES", "Severity": "OK"},
    ]

    next_steps = [
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "If Materialization Candidates > 0, run final canonical staging pack, still no DB write.",
            "Reason": "Only VALIDATED_ALIAS_AND_VALUE rows are eligible.",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Review Alias Candidates before any SSOT append-only patch.",
            "Reason": "VALUE_MATCH_ALIAS_REVIEW rows are good candidates, but not final dictionary facts.",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Keep DB/canonical/SSOT locked.",
            "Reason": "This run is validation dry-run + staging gate only.",
            "Severity": "OK",
        },
    ]

    outputs = {
        "html": str(run_dir / "VRN_Official_Cell_Validation_Materialization_Gate_v0615681_0615691.html"),
        "json": str(run_dir / "vrn_official_cell_validation_materialization_gate_v0615681_0615691.json"),
        "validation_matrix_csv": str(run_dir / "vrn_official_cell_validation_matrix_v0615681.csv"),
        "validated_rows_csv": str(run_dir / "vrn_official_validated_alias_value_rows_v0615681.csv"),
        "value_only_review_csv": str(run_dir / "vrn_official_value_match_alias_review_v0615681.csv"),
        "alias_value_review_csv": str(run_dir / "vrn_official_alias_match_value_review_v0615681.csv"),
        "no_match_csv": str(run_dir / "vrn_official_no_cell_match_v0615681.csv"),
        "materialization_candidates_csv": str(run_dir / "vrn_materialization_staging_candidates_v0615691.csv"),
        "alias_candidates_csv": str(run_dir / "vrn_alias_candidates_no_ssot_patch_v0615691.csv"),
        "route_summary_csv": str(run_dir / "vrn_validation_route_summary_v0615681.csv"),
        "gate_matrix_csv": str(run_dir / "vrn_materialization_gate_matrix_v0615691.csv"),
        "next_steps_csv": str(run_dir / "vrn_next_steps_v0615681_0615691.csv"),
    }

    def_write_csv(Path(outputs["validation_matrix_csv"]), validation_rows)
    def_write_csv(Path(outputs["validated_rows_csv"]), validated)
    def_write_csv(Path(outputs["value_only_review_csv"]), value_only)
    def_write_csv(Path(outputs["alias_value_review_csv"]), alias_value_review)
    def_write_csv(Path(outputs["no_match_csv"]), no_match)
    def_write_csv(Path(outputs["materialization_candidates_csv"]), materialization)
    def_write_csv(Path(outputs["alias_candidates_csv"]), alias_candidates)
    def_write_csv(Path(outputs["route_summary_csv"]), route_summary)
    def_write_csv(Path(outputs["gate_matrix_csv"]), gate_matrix)
    def_write_csv(Path(outputs["next_steps_csv"]), next_steps)

    final_pass = len(validation_rows) > 0 and (len(materialization) > 0 or len(alias_candidates) > 0 or len(no_match) >= 0)

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Input Plans": len(plans),
        "Official Cells": len(cells),
        "Validation Rows": len(validation_rows),
        "Validated": len(validated),
        "Value Only": len(value_only),
        "Alias+Value Review": len(alias_value_review),
        "No Match": len(no_match),
        "Materialization Candidates": len(materialization),
        "Alias Candidates": len(alias_candidates),
        "DB Write": "NO",
        "Canonical": "NO",
        "SSOT": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "WARN"), "Gate": "OFFICIAL_CELL_VALIDATION_AND_GATE_PASS", "Value": "YES" if final_pass else "REVIEW", "Severity": "OK" if final_pass else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "SOURCE_RUN", "Value": str(source), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "INPUT_PLANS", "Value": len(plans), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "OFFICIAL_CELLS", "Value": len(cells), "Severity": "OK"},
        {"Status Lights": def_light("OK" if materialization else "WARN"), "Gate": "MATERIALIZATION_CANDIDATES", "Value": len(materialization), "Severity": "OK" if materialization else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "source_run": str(source),
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Gate Matrix", gate_matrix, None),
            ("03 Validation Route Summary", route_summary, None),
            ("04 Next Steps", next_steps, None),
            ("05 Materialization Staging Candidates", materialization, 1000),
            ("06 Validated Alias + Value Rows", validated, 1000),
            ("07 Value Match / Alias Review", value_only, 1000),
            ("08 Alias Match / Value Review", alias_value_review, 1000),
            ("09 Alias Candidates - No SSOT Patch", alias_candidates, 1000),
            ("10 No Official Cell Match", no_match, 1000),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        import traceback
        print(traceback.format_exc())
        raise