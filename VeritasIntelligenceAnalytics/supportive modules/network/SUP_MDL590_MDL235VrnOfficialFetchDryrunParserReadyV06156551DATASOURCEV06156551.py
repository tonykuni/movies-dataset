# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_OFFICIAL_FETCH_DRYRUN_PARSER_READY_V06156551"


def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
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
    if s in ["OK", "PASS", "YES", "FETCH_OK", "CACHE_OK", "PARSER_READY", "MATCH"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "NO_MATCH", "NETWORK_REVIEW", "FETCH_REVIEW", "PARSER_REVIEW", "PLAN"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data or b"").hexdigest()


def def_find_latest_dir(root: Path, prefix: str) -> Path | None:
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


def def_roc_year(year: Any) -> str:
    y = def_int(year)
    return str(y - 1911) if y > 1911 else ""


def def_build_mops_urls(ticker: str, year: str, statement: str) -> list[dict]:
    roc = def_roc_year(year)
    common = {
        "encodeURIComponent": "1",
        "step": "1",
        "firstin": "1",
        "off": "1",
        "queryName": "co_id",
        "inpuType": "co_id",
        "TYPEK": "all",
        "isnew": "false",
        "co_id": ticker,
        "year": roc,
        "season": "4",
    }
    q = urllib.parse.urlencode(common)

    return [
        {
            "source": "MOPS_T164SB03_MAIN",
            "url": "https://mops.twse.com.tw/mops/web/ajax_t164sb03?" + q,
            "expected": "annual_financial_statement_html",
        },
        {
            "source": "MOPS_T164SB03_OV",
            "url": "https://mopsov.twse.com.tw/mops/web/ajax_t164sb03?" + q,
            "expected": "annual_financial_statement_html",
        },
    ]


def def_fetch_url(url: str, timeout: int) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 VRN-Official-Fetch-DryRun/0.6.15.6.5.5.1",
            "Accept": "text/html,application/xhtml+xml,application/xml,application/json,*/*",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        },
        method="GET",
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            status = getattr(resp, "status", 200)
            ctype = resp.headers.get("content-type", "")
            elapsed = int((time.time() - t0) * 1000)
            text = ""
            used_enc = ""
            for enc in ["utf-8", "cp950", "big5", "latin-1"]:
                try:
                    text = data.decode(enc, errors="ignore")
                    used_enc = enc
                    break
                except Exception:
                    pass
            return {
                "ok": True,
                "status": status,
                "content_type": ctype,
                "bytes": len(data),
                "sha256": def_sha256_bytes(data),
                "elapsed_ms": elapsed,
                "encoding": used_enc,
                "text": text,
                "error": "",
            }
    except Exception as e:
        return {
            "ok": False,
            "status": "",
            "content_type": "",
            "bytes": 0,
            "sha256": "",
            "elapsed_ms": int((time.time() - t0) * 1000),
            "encoding": "",
            "text": "",
            "error": f"{type(e).__name__}: {e}",
        }


def def_value_variants(value: Any) -> list[str]:
    v = def_float(value)
    if v is None:
        return []
    variants = set()
    if abs(v - int(v)) < 1e-9:
        variants.add(str(int(v)))
        variants.add(f"{int(v):,}")
    else:
        variants.add(str(v))
        variants.add(f"{v:,.2f}")

    # def 報告通常是 mn TWD；官方可能是仟元或元，先做 dry-run 粗比對，不視為 final validation。
    for mul in [1000, 1000000]:
        vv = v * mul
        if abs(vv - int(vv)) < 1e-9:
            variants.add(str(int(vv)))
            variants.add(f"{int(vv):,}")
        else:
            variants.add(f"{vv:.2f}")
            variants.add(f"{vv:,.2f}")

    if v == 0:
        variants.add("0")
    return sorted([x for x in variants if x], key=len, reverse=True)


def def_detect_parser_readiness(text: str) -> dict:
    blob = def_flat(text)
    if not blob:
        return {
            "parser readiness": "NO_EVIDENCE_TEXT",
            "table keyword hits": 0,
            "numeric token count": 0,
            "html table tags": 0,
            "ready score": 0,
            "Severity": "WARN",
        }

    keywords = [
        "資產負債表", "綜合損益表", "現金流量表",
        "資產總計", "負債總計", "權益總計",
        "營業收入", "營業利益", "本期淨利",
        "現金及約當現金", "存貨", "應收帳款",
    ]
    hits = sum(1 for k in keywords if k in blob)
    numeric_count = len(re.findall(r"\d{1,3}(?:,\d{3})+|\d+\.\d+|\d+", blob))
    table_tags = len(re.findall(r"<table\b|<tr\b|<td\b", text, flags=re.I))
    score = hits * 12 + min(numeric_count, 200) * 0.2 + min(table_tags, 200) * 0.15

    if score >= 35:
        readiness = "PARSER_READY"
        sev = "OK"
    elif score >= 10:
        readiness = "PARSER_REVIEW"
        sev = "WARN"
    else:
        readiness = "PARSER_NOT_READY"
        sev = "WARN"

    return {
        "parser readiness": readiness,
        "table keyword hits": hits,
        "numeric token count": numeric_count,
        "html table tags": table_tags,
        "ready score": round(score, 2),
        "Severity": sev,
    }


def def_rough_match(work_order: dict, evidence_text: str) -> dict:
    account_raw = def_get(work_order, ["account raw"])
    account_key = def_get(work_order, ["account key"])
    account_canonical = def_get(work_order, ["account canonical"])
    value = def_get(work_order, ["report value"])

    value_hits = []
    for vv in def_value_variants(value):
        if vv and vv in evidence_text:
            value_hits.append(vv)

    account_hit = False
    for token in [account_raw, account_key, account_canonical]:
        token = def_clean(token)
        if token and token in evidence_text:
            account_hit = True
            break

    if value_hits and account_hit:
        route = "ROUGH_MATCH_ACCOUNT_AND_VALUE"
        sev = "OK"
    elif value_hits:
        route = "ROUGH_MATCH_VALUE_ONLY"
        sev = "WARN"
    else:
        route = "NO_ROUGH_MATCH"
        sev = "WARN"

    return {
        "Status Lights": def_light(sev),
        "official work order id": def_get(work_order, ["official work order id"]),
        "ticker": def_get(work_order, ["ticker"]),
        "filename": def_get(work_order, ["filename"]),
        "statement": def_get(work_order, ["statement"]),
        "account raw": account_raw,
        "account canonical": account_canonical,
        "account key": account_key,
        "period year": def_get(work_order, ["period year"]),
        "report value": value,
        "unit": def_get(work_order, ["unit"]),
        "value variants hit": " | ".join(value_hits[:8]),
        "account text hit": "YES" if account_hit else "NO",
        "rough match route": route,
        "db write": "NO",
        "canonical mutation": "NO",
        "ssot mutation": "NO",
        "Severity": sev,
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
            cls = "left" if any(x in k.lower() for x in ["filename", "url", "path", "error", "account", "route", "source", "hit", "cache"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(str(v)).replace(chr(10), '<br>')}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:26px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:25px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;padding:22px 34px}
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
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Official Fetch DryRun Parser Ready v06156551</title><style>{css}</style></head>
<body><header><h1>VRN · Official Historical Fetch Dry Run + Parser Readiness v0.6.15.6.5.5.1</h1>
<div class="sub">official evidence cache only · parser readiness · rough match · no DB / canonical / SSOT</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 7:
        raise SystemExit("usage: py <run_root> <run_dir> <enable_network> <timeout_seconds> <max_network_plans> <max_work_orders_to_match> <sleep_ms>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    enable_network = str(sys.argv[3]).lower() in ["1", "true", "yes", "y"]
    timeout_seconds = def_int(sys.argv[4], 20)
    max_network_plans = def_int(sys.argv[5], 10)
    max_work_orders_to_match = def_int(sys.argv[6], 120)
    sleep_ms = def_int(sys.argv[7], 650) if len(sys.argv) >= 8 else 650

    run_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = run_dir / "official_evidence_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    source = def_find_latest_dir(run_root, "VRN_OFFICIAL_FORECAST_VALIDATION_PREFLIGHT_SEAL_V06156541")
    if not source:
        raise RuntimeError("Cannot find latest VRN_OFFICIAL_FORECAST_VALIDATION_PREFLIGHT_SEAL_V06156541 run.")

    network_plan_csv = source / "vrn_next_official_network_plan_v06156541.csv"
    work_order_csv = source / "vrn_actual_official_validation_work_order_v06156541.csv"

    network_plans = [r for r in def_read_csv(network_plan_csv) if "empty_marker" not in r]
    work_orders = [r for r in def_read_csv(work_order_csv) if "empty_marker" not in r]

    selected_plans = network_plans[:max_network_plans]
    fetch_attempts = []
    parser_readiness = []
    evidence_by_key = {}

    for plan in selected_plans:
        ticker = def_get(plan, ["ticker"])
        year = def_get(plan, ["period year"])
        statement = def_get(plan, ["statement"])
        plan_id = def_get(plan, ["network plan id"])
        evidence_key = f"{ticker}|{year}|{statement}"
        best_text = ""

        for idx, url_info in enumerate(def_build_mops_urls(ticker, year, statement), 1):
            if enable_network:
                res = def_fetch_url(url_info["url"], timeout_seconds)
            else:
                res = {
                    "ok": False,
                    "status": "",
                    "content_type": "",
                    "bytes": 0,
                    "sha256": "",
                    "elapsed_ms": 0,
                    "encoding": "",
                    "text": "",
                    "error": "NETWORK_DISABLED_BY_PARAMETER",
                }

            cache_file = ""
            if res.get("text"):
                cache_path = cache_dir / f"{ticker}_{year}_{statement}_{idx}_{url_info['source']}.html"
                cache_path.write_text(res["text"], encoding="utf-8", errors="ignore")
                cache_file = str(cache_path)
                if len(res["text"]) > len(best_text):
                    best_text = res["text"]

            sev = "OK" if res["ok"] and def_int(res["bytes"]) > 300 else "WARN"
            fetch_attempts.append({
                "Status Lights": def_light(sev),
                "network plan id": plan_id,
                "ticker": ticker,
                "period year": year,
                "statement": statement,
                "source": url_info["source"],
                "url": url_info["url"],
                "http ok": "YES" if res["ok"] else "NO",
                "status": res["status"],
                "content type": res["content_type"],
                "bytes": res["bytes"],
                "sha256": res["sha256"],
                "encoding": res["encoding"],
                "elapsed ms": res["elapsed_ms"],
                "cache file": cache_file,
                "error": res["error"],
                "db write": "NO",
                "canonical mutation": "NO",
                "ssot mutation": "NO",
                "Severity": sev,
            })

            time.sleep(max(sleep_ms, 0) / 1000.0)

        evidence_by_key[evidence_key] = best_text
        ready = def_detect_parser_readiness(best_text)
        parser_readiness.append({
            "Status Lights": def_light(ready["Severity"]),
            "network plan id": plan_id,
            "ticker": ticker,
            "period year": year,
            "statement": statement,
            "evidence key": evidence_key,
            **ready,
            "db write": "NO",
            "canonical mutation": "NO",
            "ssot mutation": "NO",
        })

    rough_matches = []
    for wo in work_orders[:max_work_orders_to_match]:
        key = "|".join([
            def_get(wo, ["ticker"]),
            def_get(wo, ["period year"]),
            def_get(wo, ["statement"]),
        ])
        rough_matches.append(def_rough_match(wo, evidence_by_key.get(key, "")))

    fetch_summary = []
    for k, v in sorted(Counter(r.get("Severity", "") for r in fetch_attempts).items(), key=lambda x: x[0]):
        fetch_summary.append({
            "Status Lights": def_light("OK" if k == "OK" else "WARN"),
            "fetch severity": k,
            "rows": v,
            "Severity": "OK" if k == "OK" else "WARN",
        })

    readiness_summary = []
    for k, v in sorted(Counter(r.get("parser readiness", "") for r in parser_readiness).items(), key=lambda x: (-x[1], x[0])):
        sev = "OK" if k == "PARSER_READY" else "WARN"
        readiness_summary.append({
            "Status Lights": def_light(sev),
            "parser readiness": k,
            "plans": v,
            "Severity": sev,
        })

    match_summary = []
    for k, v in sorted(Counter(r.get("rough match route", "") for r in rough_matches).items(), key=lambda x: (-x[1], x[0])):
        sev = "OK" if k == "ROUGH_MATCH_ACCOUNT_AND_VALUE" else "WARN"
        match_summary.append({
            "Status Lights": def_light(sev),
            "rough match route": k,
            "rows": v,
            "Severity": sev,
        })

    fetch_ok = [r for r in fetch_attempts if r.get("Severity") == "OK"]
    parser_ok = [r for r in parser_readiness if r.get("parser readiness") == "PARSER_READY"]
    rough_best = [r for r in rough_matches if r.get("rough match route") == "ROUGH_MATCH_ACCOUNT_AND_VALUE"]
    rough_value = [r for r in rough_matches if r.get("rough match route") == "ROUGH_MATCH_VALUE_ONLY"]
    rough_none = [r for r in rough_matches if r.get("rough match route") == "NO_ROUGH_MATCH"]

    hard_rules = [
        {"Status Lights": def_light("OK"), "Rule": "NO_DB_WRITE", "Reason": "Only evidence cache and dry-run reports are written.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_CANONICAL_MUTATION", "Reason": "Rough match and parser readiness are not final validation.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_SSOT_MUTATION", "Reason": "No alias update in official fetch dry run.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_RESTORE_NO_OCR", "Reason": "Only official source fetch is tested.", "Severity": "OK"},
    ]

    outputs = {
        "html": str(run_dir / "VRN_Official_Fetch_DryRun_Parser_Readiness_v06156551.html"),
        "json": str(run_dir / "vrn_official_fetch_dryrun_parser_readiness_v06156551.json"),
        "fetch_attempts_csv": str(run_dir / "vrn_official_fetch_attempts_v06156551.csv"),
        "parser_readiness_csv": str(run_dir / "vrn_official_parser_readiness_v06156551.csv"),
        "rough_match_matrix_csv": str(run_dir / "vrn_official_rough_match_matrix_v06156551.csv"),
        "fetch_summary_csv": str(run_dir / "vrn_official_fetch_summary_v06156551.csv"),
        "readiness_summary_csv": str(run_dir / "vrn_official_parser_readiness_summary_v06156551.csv"),
        "match_summary_csv": str(run_dir / "vrn_official_match_summary_v06156551.csv"),
        "hard_rules_csv": str(run_dir / "vrn_official_fetch_hard_rules_v06156551.csv"),
        "evidence_cache_dir": str(cache_dir),
    }

    def_write_csv(Path(outputs["fetch_attempts_csv"]), fetch_attempts)
    def_write_csv(Path(outputs["parser_readiness_csv"]), parser_readiness)
    def_write_csv(Path(outputs["rough_match_matrix_csv"]), rough_matches)
    def_write_csv(Path(outputs["fetch_summary_csv"]), fetch_summary)
    def_write_csv(Path(outputs["readiness_summary_csv"]), readiness_summary)
    def_write_csv(Path(outputs["match_summary_csv"]), match_summary)
    def_write_csv(Path(outputs["hard_rules_csv"]), hard_rules)

    final_pass = enable_network and len(fetch_ok) > 0 and len(parser_ok) > 0

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Network Enabled": "YES" if enable_network else "NO",
        "Source Plans": len(network_plans),
        "Selected Plans": len(selected_plans),
        "Fetch Attempts": len(fetch_attempts),
        "Fetch OK": len(fetch_ok),
        "Parser Ready Plans": len(parser_ok),
        "Work Orders": len(work_orders),
        "Rough Account+Value": len(rough_best),
        "Rough Value Only": len(rough_value),
        "No Rough Match": len(rough_none),
        "DB Write": "NO",
        "Canonical": "NO",
        "SSOT": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "WARN"), "Gate": "OFFICIAL_FETCH_DRYRUN_PARSER_READY_PASS", "Value": "YES" if final_pass else "REVIEW", "Severity": "OK" if final_pass else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "SOURCE_RUN", "Value": str(source), "Severity": "OK"},
        {"Status Lights": def_light("OK" if enable_network else "WARN"), "Gate": "NETWORK_ENABLED", "Value": "YES" if enable_network else "NO", "Severity": "OK" if enable_network else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "SELECTED_NETWORK_PLANS", "Value": len(selected_plans), "Severity": "OK"},
        {"Status Lights": def_light("OK" if fetch_ok else "WARN"), "Gate": "FETCH_OK", "Value": len(fetch_ok), "Severity": "OK" if fetch_ok else "WARN"},
        {"Status Lights": def_light("OK" if parser_ok else "WARN"), "Gate": "PARSER_READY_PLANS", "Value": len(parser_ok), "Severity": "OK" if parser_ok else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    next_steps = [
        {"Status Lights": def_light("PLAN"), "Next Step": "If Parser Ready Plans > 0, build official HTML table parser adapter staging.", "Reason": "Fetched evidence is now stable enough to design parser extraction.", "Severity": "WARN"},
        {"Status Lights": def_light("PLAN"), "Next Step": "Do not write canonical from rough match.", "Reason": "Rough string match is not accounting validation.", "Severity": "WARN"},
        {"Status Lights": def_light("PLAN"), "Next Step": "If Fetch OK = 0, switch route to official CSV/API or MOPS parameter repair.", "Reason": "Endpoint shape may differ by company/year/source.", "Severity": "WARN"},
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
            ("02 Next Steps", next_steps, None),
            ("03 Fetch Summary", fetch_summary, None),
            ("04 Parser Readiness Summary", readiness_summary, None),
            ("05 Match Summary", match_summary, None),
            ("06 Fetch Attempts", fetch_attempts, 2000),
            ("07 Parser Readiness Matrix", parser_readiness, 1000),
            ("08 Rough Match Matrix", rough_matches, 2000),
            ("09 Hard Rules", hard_rules, None),
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