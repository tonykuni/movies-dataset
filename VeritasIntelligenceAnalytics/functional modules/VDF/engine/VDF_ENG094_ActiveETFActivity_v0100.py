#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Active ETF interval analytics; offline, source-backed, explicit estimates.

VCGC-owned registration; existing ActiveTWETF DuckDB only. `plan` never writes.
Input schema VIA.ETFActivityInput.v1 represents a source-verified interval, not
an inference that legacy Yahoo fetch dates are fund valuation dates. No network
or consent mutation. Missing producer attestations remain REVIEW/NODATA.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from functools import partial as _lb_partial
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

VIA = Path(__file__).resolve().parents[3]
VDF = VIA / "functional modules" / "VDF"
DB = Path(os.environ.get("VIA_DB_ACTIVETWETF") or VDF / "output_hub/active_tw_etf/active_tw_etf_holdings/ActiveTWETF.duckdb")
OUT = VIA / "VIA_Reports" / "etf_activity"
SCHEMA = "VIA.ETFActivityInput.v1"
VERSION = "v0100"
_jwrite = _LIB.UTILS.bind_jwrite()


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def number(value, *, positive=False):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
        return n if math.isfinite(n) and (n > 0 if positive else n >= 0) else None
    except (TypeError, ValueError, OverflowError):
        return None


def iso(value):
    try:
        result = date.fromisoformat(str(value)).isoformat()
        return result if result == value else None
    except (ValueError, TypeError):
        return None


def evidence(record) -> bool:
    """A URL plus an explicit provider observation date; a fetch day is insufficient."""
    if not isinstance(record, dict):
        return False
    try:
        fetched = datetime.fromisoformat(record.get("fetched_at_utc") or "")
        if fetched.utcoffset() is None:
            return False
    except (ValueError, TypeError):
        return False
    return bool(isinstance(record, dict) and str(record.get("source_url", "")).startswith(("https://", "http://"))
                and iso(record.get("as_of")))


def adjustment(record, start, end, issues, tag):
    if not isinstance(record, dict) or record.get("state") != "VERIFIED" or not evidence(record):
        issues.append(tag + ":CORPORATE_ACTIONS_UNVERIFIED")
        return None
    if record.get("start") != start or record.get("end") != end or record.get("as_of") != end:
        issues.append(tag + ":ACTION_INTERVAL_MISMATCH")
        return None
    factor = number(record.get("factor"), positive=True)
    if factor is None:
        issues.append(tag + ":INVALID_ADJUSTMENT_FACTOR")
    return factor


def fund_interval(bundle) -> dict:
    start, end = bundle["start"], bundle["end"]
    issues = []
    previous, current = bundle.get("fund_previous") or {}, bundle.get("fund_current") or {}
    factor = adjustment(bundle.get("fund_adjustment"), start, end, issues, "FUND")
    for name, item, expected in (("previous", previous, start), ("current", current, end)):
        if not evidence(item) or item.get("as_of") != expected:
            issues.append(name + ":SOURCE_ASOF_MISSING_OR_MISMATCH")
        if item.get("currency") != bundle["currency"]:
            issues.append(name + ":CURRENCY_MISMATCH")
        values = [number(item.get(k), positive=True) for k in ("aum", "nav", "units")]
        if any(v is None for v in values):
            issues.append(name + ":AUM_NAV_UNITS_MISSING_OR_INVALID")
        elif abs(values[0] - values[1] * values[2]) > max(1.0, values[0] * 0.005):
            issues.append(name + ":AUM_NAV_UNITS_CONFLICT")
    delta = flow = None
    if not issues:
        delta = float(current["units"]) - float(previous["units"]) * factor
        flow = delta * float(current["nav"])
    return {"state": "REVIEW" if issues else "ESTIMATE", "issues": issues,
            "adjusted_net_units": delta, "net_subscription_value_estimate": flow,
            "previous": previous, "current": current, "unit_adjustment": bundle.get("fund_adjustment"),
            "method": "ADJUSTED_NET_UNITS_X_END_NAV", "currency": bundle["currency"],
            "gross_subscriptions": None, "gross_redemptions": None,
            "note": "Net interval estimate; gross creations/redemptions and cash settlement are not observable from two snapshots."}


def positions(snapshot, expected, currency, tag, issues):
    if not isinstance(snapshot, dict) or not evidence(snapshot) or snapshot.get("as_of") != expected:
        issues.append(tag + ":HOLDINGS_SOURCE_ASOF_MISSING_OR_MISMATCH")
        return {}
    if snapshot.get("complete") is not True:
        issues.append(tag + ":INCOMPLETE_HOLDINGS")
    if snapshot.get("currency") != currency:
        issues.append(tag + ":CURRENCY_MISMATCH")
    rows = snapshot.get("positions")
    if not isinstance(rows, list):
        issues.append(tag + ":INVALID_POSITIONS")
        return {}
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not str(row.get("code", "")).strip():
            issues.append(tag + ":INVALID_POSITION")
            continue
        code = str(row["code"])
        if code in result:
            issues.append(tag + ":DUPLICATE_POSITION:" + code)
        result[code] = number(row.get("shares"))
        if result[code] is None:
            issues.append(tag + ":INVALID_SHARES:" + code)
    return result


def holding_intervals(bundle) -> list:
    start, end, currency = bundle["start"], bundle["end"], bundle["currency"]
    shared = []
    old = positions(bundle.get("holdings_previous"), start, currency, "previous", shared)
    new = positions(bundle.get("holdings_current"), end, currency, "current", shared)
    codes = sorted(set(old) | set(new))
    if not codes:
        if not shared:
            return []
        return [{"code": None, "state": "REVIEW", "issues": shared + ["NO_HOLDING_IDENTITIES"],
                 "net_shares": None, "net_position_value_estimate": None, "price_estimate": None}]
    output = []
    for code in codes:
        issues = list(shared)
        factor = adjustment((bundle.get("holding_adjustments") or {}).get(code), start, end, issues, code)
        price = (bundle.get("prices") or {}).get(code) or {}
        p = number(price.get("price"), positive=True)
        if not evidence(price) or price.get("as_of") != end or price.get("start") != start or price.get("end") != end:
            issues.append("PRICE_INTERVAL_OR_SOURCE_MISMATCH")
        if price.get("currency") != currency or price.get("coverage_complete") is not True:
            issues.append("PRICE_CURRENCY_OR_COVERAGE_UNVERIFIED")
        if p is None or price.get("method") not in ("INTERVAL_VWAP", "END_CLOSE_PROXY"):
            issues.append("PRICE_MISSING_OR_METHOD_UNKNOWN")
        delta = None if shared or factor is None else new.get(code, 0.0) - old.get(code, 0.0) * factor
        value = delta * p if delta is not None and not issues else None
        output.append({"code": code, "state": "REVIEW" if issues else "ESTIMATE", "issues": issues,
                       "net_shares": delta, "price_estimate": p if not issues else None,
                       "previous_shares": old.get(code, 0.0), "current_shares": new.get(code, 0.0), "share_adjustment_factor": factor,
                       "net_position_value_estimate": value, "price_method": price.get("method"),
                       "currency": currency, "source_url": price.get("source_url"),
                       "method": "ADJUSTED_NET_POSITION_CHANGE_X_PRICE_PROXY",
                       "actual_trade_cost": None, "actual_trade_proceeds": None})
    return output


def analyze(bundle) -> dict:
    if not isinstance(bundle, dict) or bundle.get("schema") != SCHEMA:
        raise ValueError("Unknown ETF input schema")
    start, end = iso(bundle.get("start")), iso(bundle.get("end"))
    if not start or not end or start >= end or not re.fullmatch(r"\d{5}A", str(bundle.get("etf_ticker", ""))):
        raise ValueError("Require active equity ETF identity and increasing ISO interval")
    if bundle.get("currency") != "TWD":
        raise ValueError("This Taiwan equity lane requires TWD; FX conversion needs a separate evidenced rate")
    fingerprint = digest(bundle)
    fund = fund_interval(bundle)
    holdings = holding_intervals(bundle)
    snapshot_issues = sorted({v for r in holdings for v in r["issues"] if v.startswith(("previous:", "current:"))})
    state = "ESTIMATE" if fund["state"] == "ESTIMATE" and all(r["state"] == "ESTIMATE" for r in holdings) else "REVIEW"
    return {"schema": "VIA.ETFActivityResult.v1", "engine_version": VERSION, "input_sha256": fingerprint,
            "etf_ticker": bundle["etf_ticker"], "start": start, "end": end, "currency": "TWD", "state": state,
            "source_revision_at": bundle.get("source_revision_at"), "fund": fund, "holdings": holdings,
            "holdings_snapshot_issues": snapshot_issues,
            "holdings_sources": {k: {field: (bundle.get(k) or {}).get(field) for field in ("as_of", "complete", "source_url", "fetched_at_utc")}
                                 for k in ("holdings_previous", "holdings_current")},
            "assumptions": ["Snapshot changes are net positions, not an execution ledger.",
                            "In-kind transfers, intraday round trips, fees and cash balances are not reconstructed.",
                            "Estimated buy/sell prices use positive/negative NET position changes only."]}


def summarize(results) -> list:
    """Quantity-weighted period proxies; any missing interval withholds both averages."""
    groups = {}
    intervals = {}
    for result in results:
        key = (result["etf_ticker"], result["currency"])
        seen = intervals.setdefault(key, [])
        if any(result["start"] < b and result["end"] > a for a, b in seen):
            raise ValueError("Overlapping intervals would double count activity")
        seen.append((result["start"], result["end"]))
        for item in result["holdings"]:
            k = key + (item["code"],)
            g = groups.setdefault(k, {"etf_ticker": k[0], "currency": k[1], "code": k[2],
                                      "buy_qty": 0.0, "sell_qty": 0.0, "buy_value": 0.0, "sell_value": 0.0,
                                      "intervals": 0, "missing_intervals": 0, "price_methods": set()})
            g["intervals"] += 1
            if item["state"] != "ESTIMATE":
                g["missing_intervals"] += 1
                continue
            q, value = item["net_shares"], item["net_position_value_estimate"]
            side = "buy" if q > 0 else "sell"
            g[side + "_qty"] += abs(q)
            g[side + "_value"] += abs(value)
            g["price_methods"].add(item["price_method"])
    output = []
    for key, g in sorted(groups.items(), key=lambda x: str(x[0])):
        spans = sorted(intervals[key[:2]])
        gaps = any(spans[i][1] != spans[i + 1][0] for i in range(len(spans) - 1))
        unknown_snapshot = any(r["etf_ticker"] == key[0] and (r.get("holdings_snapshot_issues") or any(h["code"] is None for h in r["holdings"])) for r in results)
        series = sorted((r for r in results if r["etf_ticker"] == key[0]), key=lambda r: r["start"])
        stock_rows = [next((h for h in r["holdings"] if h["code"] == key[2]), {}) for r in series]
        split_basis = any(h.get("share_adjustment_factor") not in (None, 1.0) for h in stock_rows)
        discontinuity = any(stock_rows[i].get("current_shares", 0.0) != stock_rows[i + 1].get("previous_shares", 0.0)
                            for i in range(len(stock_rows) - 1))
        incomplete = bool(g["missing_intervals"] or gaps or unknown_snapshot or split_basis or discontinuity)
        g.update(start=spans[0][0], end=spans[-1][1], state="REVIEW" if incomplete else "ESTIMATE", interval_gap=gaps,
                 snapshot_discontinuity=discontinuity, period_share_basis_requires_normalization=split_basis)
        for side in ("buy", "sell"):
            g["estimated_average_" + side + "_price"] = g[side + "_value"] / g[side + "_qty"] if not incomplete and g[side + "_qty"] else None
        g["price_methods"] = sorted(g["price_methods"])
        g["method"] = "NET_CHANGE_QUANTITY_WEIGHTED_PRICE_PROXY"
        output.append(g)
    return output


def inspect_database(db=DB) -> dict:
    db = Path(db)
    if not db.is_file():
        return {"state": "NODATA", "reason": "FORMAL_DATABASE_ABSENT", "path": str(db), "tables": {}}
    import duckdb
    with duckdb.connect(str(db), read_only=True) as con:
        names = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        tables = {}
        for name in ("holdings_daily", "fetch_status", "active_tw_etf_registry", "etf_activity_inputs", "etf_activity_results"):
            if name in names:
                tables[name] = {"rows": con.execute('SELECT count(*) FROM "' + name + '"').fetchone()[0],
                                "columns": [r[0] for r in con.execute('DESCRIBE "' + name + '"').fetchall()]}
    return {"state": "READY" if tables.get("etf_activity_inputs", {}).get("rows", 0) else "NODATA", "path": str(db), "tables": tables,
            "reason": "NORMALIZED_SOURCE_INTERVALS_REQUIRED" if "etf_activity_inputs" not in tables else "INPUTS_PRESENT"}


def build(db=DB, inputs=None, *, apply=False) -> dict:
    """Inspect first, process unseen input hashes, preserve revisions in the same DB."""
    status = inspect_database(db)
    cached, source_rows = {}, []
    if Path(db).is_file():
        import duckdb
        with duckdb.connect(str(db), read_only=True) as con:
            if "etf_activity_results" in status["tables"]:
                cached = {r[0]: json.loads(r[1]) for r in con.execute(
                    "SELECT input_sha256,payload_json FROM etf_activity_results WHERE engine_version=?", [VERSION]).fetchall()}
            if inputs is None and "etf_activity_inputs" in status["tables"]:
                source_rows = [json.loads(r[0]) for r in con.execute("SELECT payload_json FROM etf_activity_inputs ORDER BY ingested_at_utc,input_sha256").fetchall()]
    if inputs is not None:
        source_rows = inputs if isinstance(inputs, list) else [inputs]
    unique, selected = {}, {}
    for bundle in source_rows:
        sha = digest(bundle)
        result = unique[sha][1] if sha in unique else cached.get(sha) or analyze(bundle)
        unique[sha] = (bundle, result)
        # A source revision timestamp, never hash ordering or fetch ordering, selects a revision.
        key = (result["etf_ticker"], result["start"], result["end"])
        old = selected.get(key)
        if old and old["input_sha256"] != sha:
            try:
                prior = datetime.fromisoformat(old.get("source_revision_at") or "")
                current = datetime.fromisoformat(result.get("source_revision_at") or "")
                if prior.utcoffset() is None or current.utcoffset() is None or prior == current:
                    raise ValueError("ambiguous revision")
            except (ValueError, TypeError):
                raise ValueError("Conflicting source revisions require distinct timezone-aware source_revision_at") from None
            if prior > current:
                continue
        selected[key] = result
    results = sorted(selected.values(), key=lambda r: (r["etf_ticker"], r["start"], r["end"]))
    summary = summarize(results)
    state = "NODATA" if not results else "ESTIMATE" if all(r["state"] == "ESTIMATE" for r in results) and all(s["state"] == "ESTIMATE" for s in summary) else "REVIEW"
    if apply:
        if not Path(db).is_file():
            raise ValueError("Formal DB absent: refusing to create a replacement database")
        stamp = datetime.now(timezone.utc).isoformat()
        import duckdb
        import pandas as pd
        with duckdb.connect(str(db)) as con:
            con.execute("BEGIN TRANSACTION")
            try:
                for table, rows, keys in (
                    ("etf_activity_inputs", [{"input_sha256": sha, "ingested_at_utc": stamp, "payload_json": canonical(pair[0])} for sha, pair in unique.items()], ["input_sha256"]),
                    ("etf_activity_results", [{"input_sha256": sha, "engine_version": VERSION, "computed_at_utc": stamp, "payload_json": canonical(pair[1])} for sha, pair in unique.items() if sha not in cached], ["input_sha256", "engine_version"])):
                    if rows:
                        con.register("_activity_input", pd.DataFrame(rows))
                        _LIB.UTILS.upsert_select(con, table, "_activity_input", keys)
                        con.unregister("_activity_input")
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
    return {"schema": "VIA.ETFActivityReport.v1", "state": state, "database": status, "intervals": results,
            "summary": summary, "computed": sum(sha not in cached for sha in unique), "cached": sum(sha in cached for sha in unique),
            "production_ready": False, "activation_note": "Official source normalization and workstation coverage still require validation."}


def template_report(report, output: Path) -> Path:
    """Mount through the sole canonical add-on API; no alternative UI or CDN."""
    source = VIA / "VIA_HTML_UI"
    candidates = sorted((VIA / "functional modules/VRN").glob("VRN_ENG090_FinStatementsTemplate_v*.py"))
    spec = importlib.util.spec_from_file_location("activity_template_contract", candidates[-1])
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    integrity = owner.pkg_integrity(source)
    if integrity.get("state") != "GREEN":
        raise ValueError("Canonical UI contract rejected: " + str(integrity))
    ui = output / "ui"
    ui.mkdir(parents=True, exist_ok=True)
    data = canonical(report).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    addon = '''<script id="via-etf-activity-data" type="application/json">DATA</script>
<script>(function(){
const data=JSON.parse(document.getElementById('via-etf-activity-data').textContent);
window.VIA_REGISTER_ADDON({id:'vdf-etf-activity',name:'ETF 持股活動估算',version:'0.1.0',mount(host){
 host.replaceChildren();const h=document.createElement('h3');h.textContent='ETF 持股活動估算 · '+data.state;host.append(h);
 const p=document.createElement('p');p.textContent='依持股淨變化推估；實際成交成本與申贖明細仍需原始資料。正式資料驗收尚未完成。';host.append(p);
 const fundWrap=document.createElement('div');fundWrap.style.overflowX='auto';const fundTable=document.createElement('table');fundTable.style.width='100%';fundTable.dataset.viaEtfFund='true';
 const fundHead=document.createElement('tr');['ETF','資料日','AUM (TWD)','NAV','受益單位','淨申贖金額估計','狀態'].forEach(v=>{const c=document.createElement('th');c.textContent=v;fundHead.append(c)});fundTable.append(fundHead);
 data.intervals.forEach(r=>{const row=document.createElement('tr'),f=r.fund.current;[r.etf_ticker,r.end,f.aum,f.nav,f.units,r.fund.net_subscription_value_estimate,r.fund.state].forEach(v=>{const c=document.createElement('td');c.textContent=v==null?'待補':String(v);row.append(c)});fundTable.append(row)});fundWrap.append(fundTable);host.append(fundWrap);
 const wrap=document.createElement('div');wrap.style.overflowX='auto';const table=document.createElement('table');table.style.width='100%';
 const titles=['ETF','成分','期間','淨增持金額估計','淨減持金額估計','淨增持推估均價','淨減持推估均價','狀態'];const tr=document.createElement('tr');
 titles.forEach(t=>{const c=document.createElement('th');c.textContent=t;tr.append(c)});table.append(tr);
 data.summary.forEach(r=>{const row=document.createElement('tr');[r.etf_ticker,r.code||'待補',r.start+' ~ '+r.end,r.state==='ESTIMATE'?r.buy_value:null,r.state==='ESTIMATE'?r.sell_value:null,r.estimated_average_buy_price,r.estimated_average_sell_price,r.state].forEach(v=>{const c=document.createElement('td');c.textContent=v==null?'待補':String(v);row.append(c)});table.append(row)});
 wrap.append(table);host.append(wrap);const details=document.createElement('details'),s=document.createElement('summary'),pre=document.createElement('pre');s.textContent='來源、基金申贖估算、區間與待補證據';pre.style.whiteSpace='pre-wrap';pre.style.overflowWrap='anywhere';pre.textContent=JSON.stringify(data,null,2);details.append(s,pre);host.append(details);
}});
})();</script>'''.replace("DATA", data, 1)
    for name in ("VIA-Complete-System.html", "VIA-SYNCHRONIZER-Standalone.html", "VIA-UI-Standalone-NoServer.html"):
        text = (source / "ui" / name).read_text(encoding="utf-8")
        if name == "VIA-UI-Standalone-NoServer.html":
            text = text.replace("</body>", addon + "\n</body>")
        (ui / name).write_text(text, encoding="utf-8")
    _jwrite(output / "ETF_ACTIVITY.json", report)
    return ui / "VIA-Complete-System.html"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "build"), nargs="?", default="plan")
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--input", type=Path, help="Source-normalized interval JSON; never generated from guessed source dates")
    parser.add_argument("--apply", action="store_true", help="Persist inputs/results in the existing formal DB")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    if args.command == "plan":
        report = inspect_database(args.db)
    else:
        inputs = json.loads(args.input.read_text(encoding="utf-8")) if args.input else None
        report = build(args.db, inputs, apply=args.apply)
        report["template_entry"] = str(template_report(report, args.out))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["state"] in ("READY", "ESTIMATE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
