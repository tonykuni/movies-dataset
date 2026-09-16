#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL154_VIAFunctionalAcceptance v0100 — VIA 功能級整合驗收閘

本器是 CGC_MDL149/150/153、VDF_ENG087、VAP_ENG006 與既有 VRN/PDF
驗收結果的唯一彙整入口；不重寫任何引擎，不另造資料庫，不以結構 selftest
冒充真實結果。每站均保存 argv、退出碼、裁決燈、尾端輸出與關鍵產物驗證。

用法:
  python CGC_MDL154_VIAFunctionalAcceptance_v0100.py run [--timeout N]
  python CGC_MDL154_VIAFunctionalAcceptance_v0100.py status
  python CGC_MDL154_VIAFunctionalAcceptance_v0100.py --selftest

判定:
  GREEN          所有必要 gate 通過且實際結果完整
  PARTIAL_BLOCKED 有 PARTIAL/BLOCKED/YELLOW/ABSENT；不得宣稱完工
  RED            有實際程式失敗或完整性錯誤

安全律:
  預設離線、只讀；子站只跑既有 --selftest；不設定網路同意閘；輸出只落
  VIA_Reports/acceptance/；所有非 GREEN 原因原樣保留，供下一位 AI 低額度接手。
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ROOT = VIA.parent
REPORTS = VIA / "VIA_Reports"
OUT = REPORTS / "acceptance"
REG = VIA / "supportive modules" / "registry"
PYTHON = sys.executable
VERSION = "0100"
SCHEMA = "VIA.CGC154.FunctionalAcceptance.v1"


def now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")) if path.is_file() else None
    except Exception:
        return None


def newest(pattern: str, directory: Path) -> Path | None:
    hits = sorted(directory.glob(pattern)) if directory.exists() else []
    return hits[-1] if hits else None


def tail_lines(text: str, n: int = 8) -> list[str]:
    return [line for line in text.splitlines() if line.strip()][-n:]


def child_env() -> dict[str, str]:
    """遵守 L32：驗收子站不繼承 PYTHONHOME，也不代設網路同意。"""
    env = dict(os.environ)
    env.pop("PYTHONHOME", None)
    env.pop("VIA_NET_CONSENT", None)
    env.pop("VIA_SCRAPE_CONSENT", None)
    env.update({"VIA_SELFTEST": "1", "VIA_NO_OPEN": "1", "PYTHONUTF8": "1"})
    return env


def run_station(station: str, argv: list[str], timeout: int) -> dict[str, Any]:
    started = dt.datetime.now()
    try:
        r = subprocess.run(
            argv,
            cwd=str(VIA),
            env=child_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        out, err = r.stdout or "", r.stderr or ""
        rc = r.returncode
        if rc == 0:
            state = "GREEN"
        elif rc == 2:
            state = "YELLOW"
        else:
            state = "RED"
        reason = ""
        if state == "RED":
            reason = next((x for x in reversed(tail_lines(err + "\n" + out, 12)) if "FAIL" in x or "Error" in x or "缺" in x), "子站退出碼非零")
        if state == "YELLOW":
            reason = next((x for x in reversed(tail_lines(out, 12)) if "PARTIAL" in x or "實際" in x), "子站回傳部分通過")
        combined = out + "\n" + err
        score = score_from_text(combined)
        return {
            "station": station,
            "state": state,
            "rc": rc,
            "secs": round((dt.datetime.now() - started).total_seconds(), 2),
            "score": score,
            "reason": reason,
            "argv": [str(x) for x in argv],
            "stdout_tail": tail_lines(out),
            "stderr_tail": tail_lines(err, 4),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "station": station,
            "state": "RED",
            "rc": -1,
            "secs": round((dt.datetime.now() - started).total_seconds(), 2),
            "score": {},
            "reason": f"TIMEOUT>{timeout}s",
            "argv": [str(x) for x in argv],
            "stdout_tail": tail_lines(str(exc.stdout or "")),
            "stderr_tail": tail_lines(str(exc.stderr or "")),
        }
    except Exception as exc:
        return {
            "station": station,
            "state": "RED",
            "rc": -1,
            "secs": round((dt.datetime.now() - started).total_seconds(), 2),
            "score": {},
            "reason": f"{type(exc).__name__}:{str(exc)[:160]}",
            "argv": [str(x) for x in argv],
            "stdout_tail": [],
            "stderr_tail": [],
        }


def score_from_text(text: str) -> dict[str, int]:
    """解析各站自測尾行；解析不到時保持空，不編造通過率。"""
    matches = re.findall(r"OK\s+(\d+)\s*[·|/]\s*FAIL\s+(\d+)", text)
    if not matches:
        matches = re.findall(r"OK\s+(\d+)\s*[·|]\s*FAIL\s+(\d+)", text)
    if not matches:
        return {}
    ok, fail = map(int, matches[-1])
    partial = len(re.findall(r"\[PARTIAL", text))
    total = ok + fail
    return {"ok": ok, "fail": fail, "partial": partial, "total": total, "pass_rate_pct": round(ok * 100 / total, 2) if total else 0.0}


def station_argv() -> list[tuple[str, list[str]]]:
    vcgc = newest("CGC_MDL149_VeritasCentralGovernanceConsole_v*.py", REG)
    family = newest("CGC_MDL150_CentralGovernanceFamily_v*.py", REG)
    workflow = newest("CGC_MDL153_WorkflowComposer_v*.py", REG)
    vap = newest("VAP_ENG006_AcceptanceAudit_v*.py", VIA / "functional modules" / "VAP" / "engine")
    market = newest("VDF_ENG087_MarketListGovernance_v*.py", VIA / "functional modules" / "VDF" / "engine")
    out: list[tuple[str, list[str]]] = []
    if vcgc:
        out.append(("CGC149_VCGC", [PYTHON, str(vcgc), "--selftest"]))
    if family:
        out.append(("CGC150_CentralGovernanceFamily", [PYTHON, str(family), "--selftest"]))
    if workflow:
        out.append(("CGC153_WorkflowComposer", [PYTHON, str(workflow), "--selftest"]))
    if market:
        out.append(("VDF087_MarketListGovernance", [PYTHON, str(market), "--selftest"]))
    if vap:
        out.append(("VAP006_AcceptanceAudit", [PYTHON, str(vap), "--selftest"]))
    return out


def catalog_snapshot() -> dict[str, Any]:
    p = REG / "VIA_Engine_Catalog_v0100.json"
    j = load_json(p) or {}
    rows = j.get("engines") or []
    families = Counter()
    for row in rows:
        canonical = str(row.get("canonical") or "")
        if canonical.startswith("VRN"):
            families["VRN"] += 1
        elif canonical.startswith("VDF"):
            families["VDF"] += 1
        elif canonical.startswith("VAP"):
            families["VAP"] += 1
        elif canonical.startswith("CGC") or canonical.startswith("VIA"):
            families["VIA/Central"] += 1
        else:
            families["Other"] += 1
    return {
        "source": str(p),
        "state": "GREEN" if len(rows) == 804 else ("YELLOW" if rows else "ABSENT"),
        "active_engines": len(rows),
        "selftest_capable": sum(1 for row in rows if row.get("selftest")),
        "selftest_capability_pct": round(sum(1 for row in rows if row.get("selftest")) * 100 / len(rows), 2) if rows else 0.0,
        "families": dict(families),
        "catalog_schema": j.get("schema", ""),
    }


def direct_data_checks() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    market_path = REPORTS / "vdf" / "central_lists" / "MARKET_LISTS_latest.json"
    market = load_json(market_path)
    stock_result = ((market or {}).get("lists", {}).get("tw_stock_universe", {}) or {})
    prices = stock_result.get("prices") or {}
    checks.append({"id": "vdf_market_lists_result", "state": "GREEN" if market and market.get("verdict") == "GREEN" else ("BLOCKED" if not market else "RED"), "source": str(market_path), "detail": {"verdict": (market or {}).get("verdict"), "start_required": (market or {}).get("start_required"), "stock_state": stock_result.get("state"), "stock_rows": stock_result.get("rows"), "price_min": prices.get("min"), "price_max": prices.get("max"), "price_rows": prices.get("rows"), "stock_why": stock_result.get("why"), "etf_holdings_rows": ((market or {}).get("lists", {}).get("active_tw_etf", {}).get("holdings_rows")), "story_groups": ((market or {}).get("lists", {}).get("hot_story_groups", {}).get("groups"))}})
    q_path = REPORTS / "vdf" / "quantguard" / "QUANTGUARD_latest.json"
    q = load_json(q_path)
    checks.append({"id": "vdf_quantguard_result", "state": "GREEN" if q and q.get("state") == "GREEN" else ("BLOCKED" if not q else "RED"), "source": str(q_path), "detail": {"state": (q or {}).get("state"), "accelerator": (q or {}).get("accelerator"), "network_gate": ((q or {}).get("tool_mounts") or {}).get("network_gate")}})
    vrn_path = REPORTS / "handover" / "evidence_b526_vrn_import" / "vrn_pdf_validation_b526.json"
    vrn = load_json(vrn_path)
    vrn_ok = bool(vrn and (vrn.get("vrn") or {}).get("state") == "GREEN" and (vrn.get("vrn") or {}).get("compile_ok") == (vrn.get("vrn") or {}).get("active_python_files") and (vrn.get("vrn") or {}).get("import_ok") == (vrn.get("vrn") or {}).get("active_python_files"))
    checks.append({"id": "vrn_active_tree_result", "state": "GREEN" if vrn_ok else ("BLOCKED" if not vrn else "RED"), "source": str(vrn_path), "detail": {"state": ((vrn or {}).get("vrn") or {}).get("state"), "active_python_files": ((vrn or {}).get("vrn") or {}).get("active_python_files"), "compile_ok": ((vrn or {}).get("vrn") or {}).get("compile_ok"), "import_ok": ((vrn or {}).get("vrn") or {}).get("import_ok")}})
    pdf = (vrn or {}).get("pdf") or {}
    cross = pdf.get("cross_engine") or (vrn or {}).get("cross_engine") or {}
    fitz = pdf.get("fitz") or {}
    plumber = pdf.get("pdfplumber") or {}
    pdf_ok = bool(pdf.get("state") == "GREEN" and fitz.get("state") == "PASS" and plumber.get("state") == "PASS" and cross.get("pages_agree") is True)
    checks.append({"id": "vrn_pdf_dual_engine_result", "state": "GREEN" if pdf_ok else ("BLOCKED" if not vrn else "RED"), "source": str(vrn_path), "detail": {"state": pdf.get("state"), "fitz": fitz.get("state"), "pdfplumber": plumber.get("state"), "pages_agree": cross.get("pages_agree"), "tables": plumber.get("tables")}})
    sample_path = REPORTS / "handover" / "VIA_WINDOWS_SAMPLE_ACCEPTANCE_STATUS_B526.json"
    samples = load_json(sample_path)
    sample_state = (samples or {}).get("vrn_content_acceptance") or (samples or {}).get("state") or ((vrn or {}).get("user_windows_samples") or {}).get("state")
    sample_total = (samples or {}).get("provided_files") or (samples or {}).get("total") or (samples or {}).get("manifest_count")
    checks.append({"id": "windows_original_samples", "state": "GREEN" if sample_state == "GREEN" else ("BLOCKED" if not samples or "BLOCKED" in str(sample_state) or "UNREADABLE" in str(sample_state) else "YELLOW"), "source": str(sample_path), "detail": {"state": sample_state, "total": sample_total, "readable": (samples or {}).get("mounted_readable_files"), "parsed": (samples or {}).get("content_parsed_files"), "reason": (samples or {}).get("reason")}})
    return {"checks": checks}


def database_checks() -> dict[str, Any]:
    import duckdb
    checks: list[dict[str, Any]] = []
    stock = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
    etf = VIA / "functional modules" / "VDF" / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings" / "ActiveTWETF.duckdb"
    for name, path, required in [
        ("stock_duckdb", stock, ("tw_listings_industry", "tw_daily_prices")),
        ("active_etf_duckdb", etf, ("active_tw_etf_universe", "holdings_daily")),
    ]:
        if not path.exists():
            checks.append({"id": name, "state": "BLOCKED", "source": str(path), "detail": "database missing"})
            continue
        try:
            con = duckdb.connect(str(path), read_only=True)
            tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
            counts = {t: int(con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]) for t in required if t in tables}
            duplicate_keys = 0
            if name == "stock_duckdb" and "tw_daily_prices" in tables:
                duplicate_keys = int(con.execute("SELECT COUNT(*) - COUNT(DISTINCT (date, ticker)) FROM tw_daily_prices").fetchone()[0])
            if name == "active_etf_duckdb" and "holdings_daily" in tables:
                duplicate_keys = int(con.execute("SELECT COUNT(*) - COUNT(DISTINCT (portfolio_date, etf_ticker, holding_ticker)) FROM holdings_daily").fetchone()[0])
            con.close()
            ok = all(counts.get(t, 0) > 0 for t in required) and duplicate_keys == 0
            checks.append({"id": name, "state": "GREEN" if ok else "RED", "source": str(path), "detail": {"tables": len(tables), "counts": counts, "duplicate_keys": duplicate_keys, "required": required}})
        except Exception as exc:
            checks.append({"id": name, "state": "RED", "source": str(path), "detail": f"{type(exc).__name__}:{str(exc)[:160]}"})
    return {"checks": checks}


def render_html(payload: dict[str, Any]) -> None:
    rows = payload.get("checks", [])
    colors = {"GREEN": "#15803d", "YELLOW": "#b45309", "PARTIAL": "#b45309", "PARTIAL_BLOCKED": "#b45309", "BLOCKED": "#6b7280", "RED": "#b91c1c"}
    cards = "".join(f'<div class="card"><b>{html.escape(str(r.get("id")))}</b><span style="color:{colors.get(str(r.get("state")), "#374151")}">{html.escape(str(r.get("state")))}</span><p>{html.escape(json.dumps(r.get("detail", r.get("reason", "")), ensure_ascii=False)[:480])}</p></div>' for r in rows)
    stations = payload.get("stations", [])
    station_rows = "".join(f'<tr><td>{html.escape(str(s.get("station")))}</td><td style="color:{colors.get(str(s.get("state")), "#374151")}">{html.escape(str(s.get("state")))}</td><td>{s.get("rc")}</td><td>{html.escape(json.dumps(s.get("score", {}), ensure_ascii=False))}</td><td>{html.escape(str(s.get("reason", "")))}</td></tr>' for s in stations)
    catalog = payload.get("catalog", {})
    families = json.dumps(catalog.get("families", {}), ensure_ascii=False)
    page = f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA 功能驗收 {html.escape(payload.get("verdict", ""))}</title><style>body{{font:13px/1.5 system-ui,'Noto Sans TC',sans-serif;background:#f6f7f9;color:#1f2937;margin:0}}header{{background:#111827;color:#fff;padding:18px 24px}}main{{max-width:1280px;margin:auto;padding:16px}}.kpi{{display:flex;gap:10px;flex-wrap:wrap}}.kpi div,.card{{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:10px 12px}}.kpi div{{min-width:150px}}.kpi b{{display:block;font-size:22px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:10px;margin-top:10px}}.card span{{float:right;font-weight:700}}.card p{{color:#6b7280;white-space:pre-wrap;word-break:break-word}}table{{border-collapse:collapse;width:100%;background:#fff;margin-top:10px}}th,td{{border-bottom:1px solid #e5e7eb;padding:6px;text-align:left;vertical-align:top}}th{{background:#eef2f7}}small{{color:#cbd5e1}}</style><header><h1>VIA 功能級整合驗收 Gate</h1><div>判定：<b>{html.escape(payload.get("verdict", ""))}</b> · {html.escape(payload.get("ts", ""))} · CGC_MDL154 v{VERSION}</div></header><main><div class="kpi"><div><b>{catalog.get("active_engines", 0)}</b>active engines</div><div><b>{payload.get("summary", {}).get("green", 0)}/{payload.get("summary", {}).get("total", 0)}</b>station GREEN</div><div><b>{payload.get("summary", {}).get("pass_rate_pct", 0)}%</b>station GREEN rate</div><div><b>{catalog.get("selftest_capable", 0)}</b>catalog selftest-capable</div></div><h2>中央驗收站</h2><table><tr><th>站</th><th>狀態</th><th>RC</th><th>結構分數</th><th>原因</th></tr>{station_rows}</table><h2>資料與產物 gate</h2><div class="cards">{cards}</div><h2>引擎目錄</h2><p>804 active engines 正本：{html.escape(str(catalog.get("source")))}<br>家族：{html.escape(families)}</p></main></html>'''
    (OUT / "VIA_FUNCTIONAL_ACCEPTANCE_latest.html").write_text(page, encoding="utf-8")


def run(timeout: int = 900) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    stations = [run_station(name, argv, timeout) for name, argv in station_argv()]
    direct = direct_data_checks()["checks"]
    db = database_checks()["checks"]
    checks = direct + db
    red = [x for x in checks if x.get("state") == "RED"] + [x for x in stations if x.get("state") == "RED"]
    yellow = [x for x in checks if x.get("state") in {"YELLOW", "PARTIAL", "BLOCKED", "ABSENT"}] + [x for x in stations if x.get("state") == "YELLOW"]
    if red:
        verdict = "RED"
    elif yellow:
        verdict = "PARTIAL_BLOCKED"
    else:
        verdict = "GREEN"
    green_stations = sum(1 for x in stations if x.get("state") == "GREEN")
    total_stations = len(stations)
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "version": VERSION,
        "ts": now(),
        "verdict": verdict,
        "policy": {"read_only": True, "network": "OFF_BY_DEFAULT", "false_green_block": True, "source_of_truth": "existing central engines and evidence files"},
        "stations": stations,
        "checks": checks,
        "catalog": catalog_snapshot(),
        "summary": {"total": total_stations, "green": green_stations, "red": len(red), "yellow_or_blocked": len(yellow), "pass_rate_pct": round(green_stations * 100 / total_stations, 2) if total_stations else 0.0},
        "next_actions": [
            x.get("id") or x.get("station") for x in (red + yellow)
        ],
    }
    (OUT / "VIA_FUNCTIONAL_ACCEPTANCE_latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    render_html(payload)
    print(f"=== CGC_MDL154 VIA 功能級整合驗收 · {verdict} ===")
    print(f"  中央站 GREEN {green_stations}/{total_stations} · 通過率 {payload['summary']['pass_rate_pct']}% · active engines {payload['catalog']['active_engines']}")
    for s in stations:
        score = json.dumps(s.get("score", {}), ensure_ascii=False)
        print(f"  [{s['state']:<15}] {s['station']:<32} rc={s['rc']} score={score} {s.get('reason', '')}")
    for c in checks:
        print(f"  [{c['state']:<15}] {c['id']:<32} {str(c.get('detail', ''))[:180]}")
    print(f"  JSON: {OUT / 'VIA_FUNCTIONAL_ACCEPTANCE_latest.json'}")
    print(f"  HTML: {OUT / 'VIA_FUNCTIONAL_ACCEPTANCE_latest.html'}")
    return payload


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if "status" in args:
        p = load_json(OUT / "VIA_FUNCTIONAL_ACCEPTANCE_latest.json")
        if not p:
            print("[ABSENT] 尚未執行 CGC_MDL154 run")
            return 2
        print(json.dumps({"verdict": p.get("verdict"), "ts": p.get("ts"), "summary": p.get("summary"), "next_actions": p.get("next_actions")}, ensure_ascii=False, indent=1))
        return 0 if p.get("verdict") == "GREEN" else (2 if p.get("verdict") == "PARTIAL_BLOCKED" else 1)
    timeout = 900
    if "--timeout" in args:
        try:
            timeout = int(args[args.index("--timeout") + 1])
        except Exception:
            pass
    if not args or "run" in args or "--selftest" in args:
        p = run(timeout)
        return 0 if p["verdict"] == "GREEN" else (2 if p["verdict"] == "PARTIAL_BLOCKED" else 1)
    print("用法: run [--timeout N] | status | --selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
