#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG070_YahooConsensus v0105 — v0104 薄尾(v0104 一字不動):取收盤價前先查表在不在,不讓「查不到的 SELECT」把交易弄壞。

實錄(2026-11-13 容器全量實跑 VRN_SystemManager v0264 test:VRN_ENG070 FAIL rc 1):
  _duckdb.TransactionException: Current transaction is aborted (please ROLLBACK)
根因:upsert 先 SELECT prices_canonical 取收盤價;庫裡沒有這張表(工作站空庫 / 暫存自測庫)→ 例外被吞(close=NULL 照實),
  但 DuckDB 的規則是「交易裡任何一句失敗 = 整個交易作廢」→ 下一句 DELETE 就炸。v0104 的自測在 BEGIN 裡呼叫 upsert,所以必炸;
  正式 run 若呼叫端開了交易、庫裡又沒有價格層,也會一樣炸(不是只有自測)。
修法(只改這一件):先用 information_schema 查 prices_canonical 在不在(這一句不會失敗),不在就 close=NULL,不去碰會失敗的 SELECT;
  表在才照 v0104 取價。其餘(剖析 · 冪等先刪後插 · 多源共存 · 網路一律經 SUP_MDL740 統包 · 雙同意閘 fail-closed)全照 v0104。
VRN-2 自己的引擎;零網路自測;不用 TA-Lib;不寫同意閘。
用法同 v0104:python VRN_ENG070_YahooConsensus_v0105.py run [codes…] | --status | --selftest
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
# [VIA:NET-BRIDGE] 留名:本版不出網;run 的網路照 v0104 經 SUP_MDL740 統包(雙同意閘 fail-closed)

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0105"
TAG = "VRN_ENG070_YahooConsensus " + VERSION
HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG070_YahooConsensus"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_UPSERT_V0104 = PRIOR.upsert


def __getattr__(name):
    return getattr(PRIOR, name)


def _has_table(con, name: str) -> bool:
    """information_schema 查表:這一句不會因表不存在而失敗 → 不弄壞呼叫端的交易。"""
    return bool(con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [name]).fetchone()[0])


def upsert(con, date: str, code: str, row: dict, symbol: str | None = None) -> None:
    """同 v0104 upsert(先刪後插冪等);只差在取收盤價前先查 prices_canonical 在不在。"""
    PRIOR._ensure_schema(con)
    close_v = None
    if _has_table(con, "prices_canonical"):
        r = con.execute("SELECT close FROM prices_canonical WHERE ticker=? AND date<=? ORDER BY date DESC LIMIT 1",
                        [symbol or f"{code}.TW", date]).fetchone()
        close_v = r[0] if r else None
    tgt = row["target_median"] if row["target_median"] is not None else row["target_mean"]
    upside = (tgt / close_v - 1) if (tgt and close_v) else None
    con.execute("DELETE FROM consensus_daily WHERE date=? AND code=? AND source='YAHOO_QS'", [date, code])
    con.execute("INSERT INTO consensus_daily VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [date, code, "YAHOO_QS", row["target_high"], row["target_low"], row["target_mean"], row["target_median"],
                 row["n_analysts"], row["eps_fy0"], row["eps_fy1"],
                 row["eps_fy1"] if row["eps_fy1"] is not None else row["eps_fy0"], close_v, upside, "YAHOO_DIRECT"])


PRIOR.upsert = upsert                      # v0104 的 run / selftest 用模組全域名 upsert → 換成本版


def selftest() -> int:
    import duckdb
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測(交易內取價不再弄壞交易)===" % TAG, flush=True)
    row = {"target_high": 1500.0, "target_low": 900.0, "target_mean": 1250.0, "target_median": 1200.0,
           "n_analysts": 30, "eps_fy0": 60.0, "eps_fy1": 72.0}
    with tempfile.TemporaryDirectory() as td:
        con = duckdb.connect(str(Path(td) / "a.duckdb"))
        PRIOR._ensure_schema(con)
        con.execute("BEGIN")
        err = ""
        try:
            _UPSERT_V0104(con, "1900-01-01", "T70", row)
        except Exception as exc:  # noqa: BLE001 — 重現桌機 / 容器實錄
            err = type(exc).__name__
        con.close()
        chk("① 重現:v0104 在交易裡、庫沒有 prices_canonical → TransactionException", err == "TransactionException", err or "沒炸")
        con = duckdb.connect(str(Path(td) / "b.duckdb"))
        PRIOR._ensure_schema(con)
        con.execute("BEGIN")
        upsert(con, "1900-01-01", "T70", row)
        upsert(con, "1900-01-01", "T70", row)
        n, close_v = con.execute("SELECT count(*), max(close) FROM consensus_daily WHERE code='T70' AND source='YAHOO_QS'").fetchone()
        con.execute("ROLLBACK")
        chk("② 本版:同一交易裡兩次 upsert 不炸 · 冪等 1 筆 · 沒價格層 close = NULL(照實)", n == 1 and close_v is None, (n, close_v))
        con.execute("CREATE TABLE prices_canonical(ticker VARCHAR, date VARCHAR, close DOUBLE)")
        con.execute("INSERT INTO prices_canonical VALUES ('T70.TW', '1899-12-29', 1000.0)")
        upsert(con, "1900-01-01", "T70", row)
        close_v, up = con.execute("SELECT close, upside_pct FROM consensus_daily WHERE code='T70' AND source='YAHOO_QS'").fetchone()
        chk("③ 有價格層 → 取當日或之前最近收盤 · upside = 中位 / 收盤 − 1", close_v == 1000.0 and abs(up - 0.2) < 1e-9, (close_v, up))
        con.close()
    print("  ── 前版 v0104 自測(換裝本版 upsert 後)──", flush=True)
    rc = PRIOR.selftest()
    chk("④ v0104 自測(原本在 BEGIN 裡炸)換裝後通過", rc == 0, "rc %s" % rc)
    chk("⑤ 換裝:v0104 模組的 upsert 指本版", PRIOR.upsert is upsert)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 不用 TA-Lib · 不寫同意閘 · 本版不自建網路", not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib)", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", TAG, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
