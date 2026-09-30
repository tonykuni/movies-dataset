"""VDF 受管庫故障與生命周期回歸；只用暫存庫與模擬行情。"""
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


from contextlib import redirect_stdout
from datetime import date
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch


def raises(call):
    try:
        call()
    except (ValueError, OSError):
        return True
    return False


def run_tests(store):
    checks = []
    def check(name, condition):
        checks.append(bool(condition))
        print(("[OK] " if condition else "[FAIL] ") + name)
    def raw(symbol, day, close=100.5):
        return {"date": day, "ticker": symbol, "open": 99.5, "low": 99.0, "high": 102.0,
                "close": close, "adj_close": close, "volume": 3000000000}
    with tempfile.TemporaryDirectory(prefix="vdf-managed-") as temp:
        base = Path(temp)
        root = base / "store"
        valid = base / "products.csv"
        valid.write_text('TICKER,NAME\n0050.TW,元大台灣50\n2330.TW,台積電\n6488.TWO,環球晶\n', encoding="utf-8-sig")
        check("CSV BOM、前導零、市場後綴保留", store.csv_rows(valid)[0] == ("0050.TW", "元大台灣50"))
        for content in ('NAME,TICKER\nA,AAPL\n', 'TICKER,NAME\n2330,台積電\n', 'TICKER,NAME\nAAPL,A\nAAPL,B\n', 'TICKER,NAME\nAAPL,A,B\n', 'TICKER,NAME\n../A,測試\n', 'TICKER,NAME\nAAPL,=1+1\n'):
            bad = base / "bad.csv"
            bad.write_text(content, encoding="utf-8")
            check("CSV 錯誤整批拒絕", raises(lambda: store.csv_rows(bad)))
        check("status 不建空庫", raises(lambda: store.status(root)) and not root.exists())
        store.initialize(root)
        store.initialize(root)
        report = store.import_csv(root, valid)
        check("匯入全數停用零網路", report["added"] == 3 and store.status(root)["active"] == 0)
        check("重匯冪等", store.import_csv(root, valid)["existing"] == 3)
        conflict = base / "conflict.csv"
        conflict.write_text('TICKER,NAME\nNEW,新商品\n2330.TW,錯誤名稱\n', encoding="utf-8")
        check("名稱衝突整批回滾", raises(lambda: store.import_csv(root, conflict)) and store.status(root)["products_count"] == 3)
        with patch.object(store, "_fetch", side_effect=AssertionError("inactive must not fetch")):
            check("停用商品不下載", store.update(root, "2026-09-28")["api_jobs"] == 0)
        check("不存在商品拒絕啟用", raises(lambda: store.activate(root, ["MISSING"], True)))
        store.activate(root, ["0050.TW", "2330.TW"], True)
        with patch.object(store, "_fetch", side_effect=lambda t,s,e: [raw(t, e)]) as fetch:
            report = store.update(root, "2026-09-28")
            check("啟用兩商品真 Parquet 寫入", report["failed"] == 0 and fetch.call_count == 2)
            check("重跑不下載", store.update(root, "2026-09-28")["api_jobs"] == 0 and fetch.call_count == 2)
        with store._connect(root, read_only=True) as con:
            rows = con.execute('SELECT Ticker,Close,Volume,Market_Cap FROM prices ORDER BY Ticker').fetchall()
        check("DuckDB 直接讀 Parquet、小數與 64bit 成交量", rows == [("0050.TW",100.5,3000000000,None),("2330.TW",100.5,3000000000,None)])
        check("實查 16 欄與 checkpoint", store.inspect(root)["state"] == "VERIFIED")
        requests = []
        def incremental(t, s, e):
            requests.append((t, s, e))
            return [raw(t, "2026-09-28"), raw(t, "2026-09-29")]
        with patch.object(store, "_fetch", side_effect=incremental):
            report = store.update(root, "2026-09-29")
        check("增量重疊 3 天、鍵不重複", all(x[1] == "2026-09-25" for x in requests) and all(p["rows"] == 2 and p["added"] == 1 for p in report["products"]))
        with patch.object(store, "_fetch", return_value=[]):
            report = store.update(root, "2026-09-30")
        check("空結果不假成功", report["failed"] == 2 and store.status(root, True)["products"][0]["checked_through"] == date(2026,9,29))
        store.activate(root, ["2330.TW"], False)
        with patch.object(store, "_fetch", side_effect=lambda t,s,e: [raw(t, "2026-09-29", 999.0), raw(t,e)]):
            report = store.update(root, "2026-09-30")
        with store._connect(root, read_only=True) as con:
            old = con.execute("SELECT Close FROM prices WHERE Ticker='0050.TW' AND Date='2026-09-29'").fetchone()[0]
        check("舊值保留、衝突顯示 PARTIAL", old == 100.5 and report["failed"] == 1 and report["products"][0]["conflicts"] == 1)
        check("來源多欄阻止漂移", raises(lambda: store.frame([dict(raw("0050.TW","2026-09-30"), mystery=1)], "0050.TW", "名稱")))
        check("錯商品不污染", raises(lambda: store.frame([raw("OTHER","2026-09-30")], "0050.TW", "名稱")))
        check("小數成交量不截斷", raises(lambda: store.frame([dict(raw("0050.TW","2026-09-30"), volume=1.5)], "0050.TW", "名稱")))
        with store._lock(root):
            check("併發寫入拒絕", raises(lambda: store.activate(root, ["0050.TW"], False)))
        folder = store._product_dir(root, "0050.TW")
        (folder / "old.tmp").write_text("pending")
        with patch.object(store.shutil, "rmtree", side_effect=OSError("injected delete failure")):
            check("刪除失敗照實回報", raises(lambda: store.delete_products(root,["0050.TW"])))
        with patch.object(store, "_fetch", side_effect=AssertionError("deleted must not fetch")):
            check("刪除中商品不復活", store.update(root,"2026-09-30")["api_jobs"] == 0)
        store.delete_products(root,["0050.TW"])
        check("刪除清掉該商品全部檔案、其他商品保留", not folder.exists() and store._product_dir(root,"2330.TW").exists())
        store.delete_products(root,["2330.TW","6488.TWO"])
        check("刪光後 schema 仍鎖定且空庫可讀", store.inspect(root)["state"] == "VERIFIED" and store.status(root)["products_count"] == 0)
        store.import_csv(root, valid)
        legacy = base / "legacy.duckdb"
        import duckdb
        with duckdb.connect(str(legacy)) as con:
            con.execute("CREATE TABLE tw_daily_prices AS SELECT '2026-09-28' AS date,'0050.TW' AS ticker,100.5 AS open,99.0 AS low,102.0 AS high,100.5 AS close,100.5 AS adj_close,3000000000::BIGINT AS volume")
        before = legacy.read_bytes()
        report = store.migrate_legacy(root, legacy)
        check("旧庫唯讀轉存、名稱與前導零保留", report["state"] == "MIGRATED" and legacy.read_bytes() == before and store.sample(root,"0050.TW")["rows"][0][4] == "元大台灣50")
        check("轉存冪等且不自動啟用", store.migrate_legacy(root,legacy)["products"][0]["added"] == 0 and store.status(root)["active"] == 0)
        with patch.object(store, "update", return_value={"failed":0,"state":"OK"}) as update, patch.object(store.time,"sleep") as sleep, redirect_stdout(io.StringIO()):
            rc = store.start(root, interval=60, cycles=2)
        check("常駐啟動先更新、再等待且不呼叫 AI", rc == 0 and update.call_count == 2 and sleep.call_count == 1)
        with patch.dict(store.os.environ, {"VIA_FROM_VCGC":"NO"}), redirect_stdout(io.StringIO()):
            rc = store.main(["contract"])
        check("入口閘有效", rc == 2)
    failed = checks.count(False)
    print(f"[VDF Parquet 回歸] checks={len(checks)}; fail={failed}")
    return 1 if failed else 0
