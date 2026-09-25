#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG087 v0104 — two daily lists, both checked.

v0103 stays. It can call the stock list green when only one exchange is
present, and the ETF list green when any holdings row exists.

Two lists update every day:

1. All Taiwan stocks: TWSE (加權) and TPEX (櫃買) both have to be there.
2. Active Taiwan ETF master list: the registry is the list, and every
   daily-holdings ticker must appear in holdings_daily.
"""
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

import importlib.util
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "eng087_v0103", HERE / "VDF_ENG087_MarketListGovernance_v0103.py")
BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(BASE)

ACTIVE_EQUITY = re.compile(r"^00\d{2,3}A$")
TWSE = {"TWSE", "TSE", "上市", "加權"}
TPEX = {"TPEX", "OTC", "TWO", "上櫃", "櫃買"}


def _bare(ticker: str) -> str:
    text = str(ticker or "").strip().upper()
    for tail in (".TWO", ".TW", " TT"):
        if text.endswith(tail):
            text = text[: -len(tail)].strip()
    return text


def split_exchanges(pairs: list[tuple[str, int]]) -> dict:
    out = {"TWSE": 0, "TPEX": 0, "other": 0, "unknown": []}
    for raw, count in pairs:
        label = str(raw or "").strip()
        token = label.upper()
        n = int(count)
        if label in TWSE or token in TWSE:
            out["TWSE"] += n
        elif label in TPEX or token in TPEX:
            out["TPEX"] += n
        else:
            out["other"] += n
            if label and label not in out["unknown"] and len(out["unknown"]) < 8:
                out["unknown"].append(label)
    return out


def verify_etf_master(required: list[str], fetched: set[str]) -> dict:
    """The registry is the master list. Holdings verify the daily names."""
    missing = []
    not_equity = []
    verified = 0
    have = {_bare(item) for item in fetched}
    for ticker in required:
        code = _bare(ticker)
        if not ACTIVE_EQUITY.fullmatch(code):
            not_equity.append(code)
            continue
        if code not in have:
            missing.append(code)
        else:
            verified += 1
    if not required:
        state, why = "RED", "主動式台股 ETF 總清單沒有要驗證持股的檔"
    elif not_equity or missing:
        state = "RED"
        why = f"總清單未驗證: 缺持股 {len(missing)} · 不是主動股票A碼 {len(not_equity)}"
    else:
        state, why = "GREEN", f"主動式台股 ETF 總清單 {verified} 檔持股都已驗證"
    return {
        "required": len(required), "verified": verified, "state": state, "why": why,
        "missing": missing[:20], "not_equity_a": not_equity[:20],
    }


def _count_exchanges(db: Path, table: str, column: str) -> dict:
    con = BASE._open(db)
    if con is None:
        return {"TWSE": 0, "TPEX": 0, "other": 0, "unknown": []}
    try:
        rows = con.execute(
            f"SELECT CAST({BASE._safe_table(column)} AS VARCHAR), COUNT(*) "
            f"FROM {BASE._safe_table(table)} GROUP BY 1"
        ).fetchall()
    finally:
        con.close()
    return split_exchanges([(row[0], row[1]) for row in rows])


def _status_stock(db: Path) -> dict:
    result = BASE._status_stock(db)
    if result.get("state") != "GREEN":
        return result
    column = (result.get("mapping") or {}).get("exchange")
    table = result.get("table")
    if not column or not table:
        result.update(state="RED", why="個股總清單沒有交易所欄，分不開加權與櫃買")
        return result
    counts = _count_exchanges(db, table, column)
    result["exchanges"] = counts
    if counts["TWSE"] == 0 or counts["TPEX"] == 0:
        result.update(state="RED", why=f"個股總清單缺一邊: 加權 {counts['TWSE']} · 櫃買 {counts['TPEX']}")
    else:
        result.update(why=f"個股總清單: 加權 {counts['TWSE']} · 櫃買 {counts['TPEX']}")
    return result


def _status_etf(db: Path) -> dict:
    result = BASE._status_etf(db)
    if result.get("state") != "GREEN":
        return result
    mapping = result.get("mapping") or {}
    reg_col = mapping.get("registry_ticker")
    flag = mapping.get("daily_required")
    con = BASE._open(db)
    if con is None or not reg_col or not flag:
        result.update(state="RED", why="主動式台股 ETF 總清單打不開，不能驗證")
        return result
    try:
        hold_cols = BASE._columns(con, "holdings_daily")
        etf_col = BASE._first(hold_cols, ("etf_ticker", "etf"))
        if not etf_col:
            result.update(state="RED", why="持股表沒有 etf_ticker，總清單無法驗證")
            return result
        required = [row[0] for row in con.execute(
            f"SELECT {BASE._safe_table(reg_col)} FROM \"active_tw_etf_registry\" "
            f"WHERE CAST({BASE._safe_table(flag)} AS BOOLEAN)"
        ).fetchall()]
        fetched = {row[0] for row in con.execute(
            f"SELECT DISTINCT {BASE._safe_table(etf_col)} FROM \"holdings_daily\""
        ).fetchall()}
    finally:
        con.close()
    check = verify_etf_master(required, fetched)
    result["master_check"] = check
    result.update(state=check["state"], why=check["why"])
    return result


def _status() -> dict:
    payload = BASE._status()
    stocks = _status_stock(BASE._env_path("VIA_DB_TW", BASE.DB_TW))
    etf = _status_etf(BASE._env_path("VIA_DB_ACTIVETWETF", BASE.DB_ETF))
    payload["lists"]["tw_stock_universe"] = stocks
    payload["lists"]["active_tw_etf"] = etf
    states = [stocks["state"], etf["state"], payload["lists"]["hot_story_groups"]["state"]]
    payload["verdict"] = (
        "GREEN" if all(item == "GREEN" for item in states)
        else ("ABSENT" if "ABSENT" in states else ("NODATA" if "NODATA" in states else "RED"))
    )
    payload["daily_lists"] = ["tw_stock_universe", "active_tw_etf"]
    payload["engine"] = "VDF_ENG087_MarketListGovernance_v0104.py"
    return payload


def status() -> int:
    payload = _status()
    BASE._write(payload)
    stocks = payload["lists"]["tw_stock_universe"]
    etf = payload["lists"]["active_tw_etf"]
    print(f"[VDF_ENG087 v0104] {payload['verdict']} · 個股 {stocks['state']} · 主動式台股ETF {etf['state']}")
    print(f"  {stocks.get('why', '')}")
    print(f"  {etf.get('why', '')}")
    return 0 if payload["verdict"] == "GREEN" else 2


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    both = split_exchanges([("TWSE", 1000), ("TPEX", 800), ("ETF", 3)])
    one = split_exchanges([("上櫃", 892)])
    chk("both exchanges", both["TWSE"] == 1000 and both["TPEX"] == 800 and both["other"] == 3)
    chk("one side", one["TWSE"] == 0 and one["TPEX"] == 892)
    ok = verify_etf_master(["00981A", "00982A.TW"], {"00981A", "00982A"})
    chk("master verified", ok["state"] == "GREEN" and ok["verified"] == 2)
    gap = verify_etf_master(["00981A", "00983A"], {"00981A"})
    chk("missing holding", gap["state"] == "RED" and gap["missing"] == ["00983A"])
    foreign = verify_etf_master(["00402A"], set())
    chk("empty not verified", foreign["state"] == "RED" and foreign["not_equity_a"] == [])
    bond = verify_etf_master(["00981D"], {"00981D"})
    chk("bond out", bond["state"] == "RED" and bond["not_equity_a"] == ["00981D"])
    none = verify_etf_master([], {"00981A"})
    chk("no master", none["state"] == "RED")
    bad = [name for name, ok_ in checks if not ok_]
    print(f"[VDF_ENG087 v0104] {len(checks) - len(bad)}/{len(checks)}" + (f" FAIL {bad}" if bad else " OK"))
    return 1 if bad else 0


def main() -> int:
    import sys
    if "--selftest" in sys.argv:
        return selftest()
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        return BASE.run_update()
    return status()


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
