"""VDF 日價入口回歸：零外呼、暫存真 DuckDB、保留既有資料。"""
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
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

# def 01_PARAMETERS
FIXTURE_DATE = "2026-09-30"
OLD_DATE = "2026-09-29"
SUCCESS_MARKER = "[VDF 派送回歸] fail=0"


def _raises(fn, kind):
    try:
        fn()
    except kind:
        return True
    return False


def _quiet(fn):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn()


def run_tests(engine):
    import duckdb
    failures = []

    def check(name, ok):
        print(("[OK] " if ok else "[FAIL] ") + name)
        if not ok:
            failures.append(name)

    with patch.dict(os.environ, {"VIA_FROM_VCGC": "YES"}):
        with patch.object(engine, "run", return_value=7) as fetch, patch.object(engine, "status", return_value=2) as status:
            check("run 真正派送且保留退出碼", engine.main(["run", "--limit", "2", "--full"]) == 7 and fetch.call_args.args == (2, True, None))
            check("無參數只查狀態", engine.main([]) == 2 and status.call_count == 1 and fetch.call_count == 1)
            check("--status 兼容", engine.main(["--status"]) == 2)
            for argv in (["run", "--start", "2023-07-01"], ["run", "--lim", "2"], ["run", "--limit", "0"], ["status", "--full"], ["run", "--status"], ["run", "--selftest"], ["contract", "--db", "ignored"]):
                check("拒絕不支援/衝突參數 " + " ".join(argv), _quiet(lambda argv=argv: _raises(lambda: engine.main(argv), SystemExit)))
        with patch.dict(os.environ, {"VIA_FROM_VCGC": "NO"}), patch.object(engine, "run") as fetch:
            check("唯一入口拒絕", _quiet(lambda: engine.main(["run"])) == 2 and not fetch.called)
        c = engine.contract()
        check("參數保留不同來源與無日期旗標事實", c["parameters"]["empty_ticker_start"] == engine.PRIOR.START and c["parameters"]["declared_item_params"] == [] and "central_default_start" in c["parameters"])
        check("原始八欄與整合十六欄不冒充實測", len(c["headers"]["raw_ddl"]) == 8 and len(c["headers"]["target_prices_core"]) == 16 and c["headers"]["actual_database_verified"] is False)
        with tempfile.TemporaryDirectory(prefix="via_vdf_dispatch_") as td:
            root = Path(td)
            db = root / engine.DB_NAME
            body, source = engine._prepared(str(db))
            check("路徑、快照與 checkpoint 同資料家", body.DB_TW == db and body.OUT.parent == root and body.CKPT.parent == root and source == "--db")
            check("缺庫 status 不建庫", _quiet(lambda: engine.main(["status", "--db", str(db)])) == 2 and not db.exists())
            with patch.object(engine, "_prepared", return_value=(body, source)), patch.object(body, "gate_open", return_value=False), patch.object(body, "_net_or_none") as net:
                check("網路閘關閉零外呼零建庫", _quiet(lambda: engine.main(["run"])) == 2 and not net.called and not db.exists())
            body.ensure_price_table()
            body.upsert_duckdb("tw_daily_prices", [
                {"date": OLD_DATE, "ticker": "0050.TW", "close": 80.0},
                {"date": OLD_DATE, "ticker": "2330.TW", "close": 1000.5},
            ], ["date", "ticker"])
            body.upsert_duckdb("tw_listings", [{"code": "0050", "market": "TWSE", "name": "preserve"}], ["code", "market"])

            def fake_prices(net, tickers, start, end):
                rows = []
                for ticker in tickers:
                    if ticker == "2330.TW":
                        rows.append({"date": OLD_DATE, "ticker": ticker, "close": 999.0})
                    rows.append({"date": FIXTURE_DATE, "ticker": ticker, "open": 1010.5, "high": 1015.5, "low": 1005.5, "close": 1012.5, "adj_close": 1012.5, "volume": 3000000000.0})
                return {"rows": rows, "failed": []}

            listing = {"code": "2330", "market": "TWSE", "yf_ticker": "2330.TW", "name": "fixture"}
            etf = {"code": "00981A", "market": "TWSE", "yf_ticker": "00981A.TW", "name": "fixture ETF"}
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(engine, "_prepared", return_value=(body, source)))
                stack.enter_context(patch.object(body, "gate_open", return_value=True))
                stack.enter_context(patch.object(body, "_net_or_none", return_value=SimpleNamespace(yahoo_chart=True)))
                stack.enter_context(patch.object(body, "fetch_listings", return_value=([listing], {"TWSE": {"state": "OK", "n": 1}, "TPEX": {"state": "OK", "n": 0}})))
                stack.enter_context(patch.object(body, "fetch_etf_listings", return_value=([etf], "OK")))
                stack.enter_context(patch.object(body, "target_date", return_value=FIXTURE_DATE))
                stack.enter_context(patch.object(body, "_fetch_group", side_effect=fake_prices))
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    rc = engine.main(["run"])
                if rc:
                    print(output.getvalue())
                check("暫存真庫 run 完成新增", rc == 0)
            with duckdb.connect(str(db), read_only=True) as con:
                check("保留被動 ETF 清單與日價", con.execute("SELECT count(*) FROM tw_listings WHERE code='0050'").fetchone()[0] == 1 and con.execute("SELECT close FROM tw_daily_prices WHERE ticker='0050.TW'").fetchone()[0] == 80.0)
                check("相同鍵舊值不覆寫、新列與小數保留", con.execute("SELECT close FROM tw_daily_prices WHERE ticker='2330.TW' AND date=?", [OLD_DATE]).fetchone()[0] == 1000.5 and con.execute("SELECT count(*) FROM tw_daily_prices").fetchone()[0] == 4 and con.execute("SELECT volume FROM tw_daily_prices WHERE ticker='2330.TW' AND date=?", [FIXTURE_DATE]).fetchone()[0] == 3000000000.0)
            row = [{"date": FIXTURE_DATE, "ticker": "2330.TW", "close": 1.0}]
            a = body.write_parquet(row, "snapshot")
            before = a.read_bytes()
            b = body.write_parquet(row, "snapshot")
            check("同秒快照只增不覆寫", a != b and a.read_bytes() == before and b.exists())
            for result in ({"rows": [], "failed": []}, {"rows": [{"ticker": "2330.TW"}], "failed": ["2317.TW"]}):
                dummy = SimpleNamespace(DB_TW=db, START_DATE="2022-07-01", DbBusy=RuntimeError,
                                        gate_open=lambda: True, _fetch_group=lambda *a, result=result: result)

                def fake_run(limit=None, full=False):
                    dummy._fetch_group(None, [], "", 0)
                    return 0

                dummy.run = fake_run
                with patch.object(engine, "_prepared", return_value=(dummy, "fixture")):
                    check("空抓/部分失敗不能假綠", _quiet(lambda: engine.run()) == 2)
            with patch.object(engine, "_database", side_effect=ValueError("ambiguous")):
                check("路徑不明拒絕而不寫錯庫", _quiet(lambda: engine.main(["run"])) == 2)
    print("[VDF 派送回歸] fail=" + str(len(failures)))
    return 1 if failures else 0


def run_manager_tests(manager):
    failures = []

    def check(name, ok):
        print(("[OK] " if ok else "[FAIL] ") + name)
        if not ok:
            failures.append(name)

    c = manager.read("contract")
    check("Manager 直接讀引擎契約", c == manager.read_contract())
    check("HEADER 分層未假稱 DB 實測", manager.read("headers")["actual_database_verified"] is False)
    with patch.object(manager.PRIOR, "read", return_value={"state": "GREEN", "books": ["retained"]}):
        check("參數追加且原欄保留", manager.read("param")["books"] == ["retained"] and manager.read_param()["execution_contract"] == c["parameters"])
    check("measure 黃燈回 rc2", manager.measure_rc({"rc_name": "STALE/NODATA", "open": ["engine"], "cmds_missing": []}) == 2)
    check("measure 紅燈回 rc1", manager.measure_rc({"rc_name": "RED", "open": [], "cmds_missing": []}) == 1)
    check("measure 全綠才 rc0", manager.measure_rc({"rc_name": "GREEN", "open": [], "cmds_missing": []}) == 0)
    with patch.dict(os.environ, {"VIA_FROM_VCGC": "YES"}), patch.object(manager.PRIOR, "main", return_value=7) as original:
        check("既有動詞原樣派送", manager.main(["read", "engine"]) == 7 and original.call_count == 1)
        check("新讀取介面可經 CLI", _quiet(lambda: manager.main(["read", "headers"])) == 0)
    print("[VDF Manager 契約回歸] fail=" + str(len(failures)))
    return 1 if failures else 0
