#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_MDL032_TWPriceReconcile v0101 — 薄尾:刪休市佔位前要官方指數日曆另外證明「那天休市」(PR 707 Codex P1)

v0100 判休市佔位只看「日期不在 tw_trading_daily(官方成交表)而且在它的最早 ~ 最晚之間」;最早 / 最晚不能證明中間完整:
官方成交表若漏抓某個交易日(來源一時失敗 · 擷取中斷),那天量 0 · 開高低收相同的 Yahoo 列(停牌 / 無成交的合法報價)會被當成休市刪掉;
啟動器 v0108 在擷取失敗後也照樣叫對帳 → 一次來源失敗就自動刪掉合法歷史。
本版只改一件事(其餘 · 改官方值 · 補缺 · 帳表 · 備份 · 冪等全照 v0100):
  休市佔位要同時符合 ① 不在官方成交表 ② 不在同資料家官方指數日曆(tw_index/VDF_TWIndex_Daily.duckdb 的櫃買 ∪ 加權)
  ③ 指數日曆在那天前後 16 天內都有日子(那段日曆是完整的)④ 量 0 · 開 = 高 = 低 = 收;
  指數庫不在 / 讀不到 / 那段日曆不完整 → 不刪,計數放 holiday_unverified 照實報。
  (改官方值與補缺本來就只用官方值,擷取失敗時跑也只會少改,不會改錯 → 啟動器照舊每輪跑。)
2026-10-23 那 2,007 列(v0100 已刪)再核:櫃買 · 加權指數那天都沒有、前後都有;證交所官方 2330 10/22 → 10/27 → 確為休市。
用法同 v0100:plan|apply --home <資料家> | --db <vdf_tw_market.duckdb> · --selftest。不出網;不讀寫同意閘;不碰 TA-Lib。
"""
from __future__ import annotations
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
except Exception:  # noqa: BLE001
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。啟動器自己不連網,連網的是各擷取引擎。"""
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL032_TWPriceReconcile"
TAG = "VDF_MDL032_TWPriceReconcile v0101"
WINDOW = 16


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_VIEWS_V0100 = PRIOR._views
_PLAN_V0100 = PRIOR.plan
PRICES, OFFICIAL = PRIOR.PRICES, PRIOR.OFFICIAL


def __getattr__(name):
    return getattr(PRIOR, name)


def index_db_of(con) -> Path | None:
    """本連線主庫(…/output_hub/mega/vdf_tw_market.duckdb)→ …/output_hub/tw_index/VDF_TWIndex_Daily.duckdb。"""
    try:
        p = con.execute("SELECT path FROM duckdb_databases() WHERE database_name = current_database()").fetchone()[0]
    except Exception:
        return None
    return Path(p).parent.parent / "tw_index" / "VDF_TWIndex_Daily.duckdb" if p else None


def _views_v0101(con) -> None:
    _VIEWS_V0100(con)
    con.execute("CREATE OR REPLACE TEMP TABLE hol_cand AS SELECT * FROM hol")
    idx = index_db_of(con)
    ok = False
    if idx is not None and idx.is_file():
        try:
            if "ix_v0101" not in [r[0] for r in con.execute("SELECT database_name FROM duckdb_databases()").fetchall()]:
                con.execute(f"ATTACH '{str(idx)}' AS ix_v0101 (READ_ONLY)")
            con.execute("CREATE OR REPLACE TEMP TABLE ixcal AS SELECT DISTINCT CAST(date AS VARCHAR) AS d FROM ix_v0101.tw_index_daily "
                        "WHERE index_code IN ('TPEX', 'TAIEX')")
            ok = True
        except Exception:
            ok = False
    if not ok:
        con.execute("CREATE OR REPLACE TEMP TABLE ixcal AS SELECT CAST(NULL AS VARCHAR) AS d WHERE false")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE hol AS SELECT h.* FROM hol_cand h
        WHERE h.date NOT IN (SELECT d FROM ixcal)
          AND EXISTS (SELECT 1 FROM ixcal WHERE d < h.date AND d >= CAST(CAST(h.date AS DATE) - INTERVAL {WINDOW} DAY AS VARCHAR))
          AND EXISTS (SELECT 1 FROM ixcal WHERE d > h.date AND d <= CAST(CAST(h.date AS DATE) + INTERVAL {WINDOW} DAY AS VARCHAR))""")


def plan_v0101(con) -> dict:
    out = _PLAN_V0100(con)
    out["holiday_unverified"] = con.execute("SELECT count(*) FROM hol_cand").fetchone()[0] - out["holiday"]
    out["index_calendar_days"] = con.execute("SELECT count(*) FROM ixcal").fetchone()[0]
    return out


PRIOR._views = _views_v0101                       # v0100 plan / apply 以模組全域叫 _views / plan
PRIOR.plan = plan_v0101


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def _fixture_index(idx: Path, days: list) -> None:
    import duckdb
    idx.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(idx))
    con.execute("CREATE TABLE tw_index_daily(date VARCHAR, index_code VARCHAR, close DOUBLE)")
    con.executemany("INSERT INTO tw_index_daily VALUES (?, 'TPEX', 1)", [(d,) for d in days])
    con.close()


def selftest() -> int:
    import duckdb
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    PRIOR._views, PRIOR.plan = _VIEWS_V0100, _PLAN_V0100
    try:
        rc0 = PRIOR.selftest()
    finally:
        PRIOR._views, PRIOR.plan = _views_v0101, plan_v0101
    print(f"=== {TAG} · 薄尾自測(休市要指數日曆另外證明)===")
    chk("⓪ 前版 v0100 自測過(v0100 原判法)", rc0 == 0, f"rc {rc0}")
    days = ["2025-01-02", "2025-01-03", "2025-01-06", "2025-01-07", "2025-01-08", "2025-01-09"]
    with tempfile.TemporaryDirectory(prefix="mdl032_v0101_") as td:
        def make(name, index_days, official_drop=None):
            home = Path(td) / name
            db = home / PRIOR.DB_REL
            db.parent.mkdir(parents=True)
            PRIOR._fixture(db)
            con = duckdb.connect(str(db))
            if official_drop:                              # 官方成交表漏抓某個交易日(來源失敗)
                con.execute(f"DELETE FROM {OFFICIAL} WHERE date = ?", [official_drop])
                con.execute(f"INSERT INTO {PRICES} VALUES (?, '2222.TW', 20, 20, 20, 20, 16, 0)", [official_drop])
                con.execute(f"DELETE FROM {PRICES} WHERE date = ? AND ticker = '2222.TW' AND volume <> 0", [official_drop])
            con.close()
            if index_days is not None:
                _fixture_index(home / "output_hub" / "tw_index" / "VDF_TWIndex_Daily.duckdb", index_days)
            return home, db

        def plan_of(db):
            con = duckdb.connect(str(db), read_only=True)
            try:
                return plan_v0101(con)
            finally:
                con.close()
        _, db1 = make("closed", days)
        p1 = plan_of(db1)
        chk("① 真休市(01-04 週六):指數日曆沒有、前後都有 → 佔位 1 列照刪", p1["holiday"] == 1 and p1["holiday_unverified"] == 0, p1)
        _, db2 = make("missed", days, official_drop="2025-01-07")
        p2 = plan_of(db2)
        con = duckdb.connect(str(db2), read_only=True)
        hol_days = [r[0] for r in con.execute("SELECT 1").fetchall()]
        con.close()
        chk("② Codex P1 重現:官方成交表漏抓 01-07(交易日),那天量 0 的合法 Yahoo 列 → 指數日曆有 01-07 → 不刪",
            "2025-01-07" not in p2["holiday_days"] and p2["holiday"] == 1, p2)
        con = duckdb.connect(str(db2), read_only=True)
        _VIEWS_V0100(con)
        old = [r[0] for r in con.execute("SELECT DISTINCT date FROM hol ORDER BY 1").fetchall()]
        con.close()
        chk("③ 對照:前版 v0100 同一份庫會把 01-07 當休市刪", "2025-01-07" in old, old)
        _, db3 = make("noindex", None)
        p3 = plan_of(db3)
        chk("④ 指數庫不在 → 一列都不刪 · holiday_unverified 照實報", p3["holiday"] == 0 and p3["holiday_unverified"] == 1, p3)
        _, db4 = make("sparse", ["2025-01-02"])
        p4 = plan_of(db4)
        chk("⑤ 指數日曆在那天之後沒有日子(不完整)→ 不刪", p4["holiday"] == 0 and p4["holiday_unverified"] == 1, p4)
        home5, db5 = make("apply", days, official_drop="2025-01-07")
        rc = PRIOR.main(["apply", "--home", str(home5)])
        con = duckdb.connect(str(db5), read_only=True)
        kept = con.execute(f"SELECT count(*) FROM {PRICES} WHERE date = '2025-01-07' AND ticker = '2222.TW'").fetchone()[0]
        gone = con.execute(f"SELECT count(*) FROM {PRICES} WHERE date = '2025-01-04' AND ticker = '1111.TW'").fetchone()[0]
        con.close()
        chk("⑥ apply 走本版判法:01-07 合法列留著 · 01-04 佔位刪掉 · rc 0", rc == 0 and kept == 1 and gone == 0, (rc, kept, gone))
    chk("⑦ 換裝:v0100 的 _views / plan = 本版", PRIOR._views is _views_v0101 and PRIOR.plan is plan_v0101)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑧ 加速器橋 · 網路橋在;不出網;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and "def _via_net" in src
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|talib)", body, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑨ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
