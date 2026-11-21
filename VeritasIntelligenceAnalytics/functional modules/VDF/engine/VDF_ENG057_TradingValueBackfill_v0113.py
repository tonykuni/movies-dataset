#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG057_TradingValueBackfill v0113 — 薄尾:交易日曆 = 日價表日期 ∪ 櫃買官方指數日期(Yahoo 缺的交易日官方表也補得到)

操作員 2026-11-21:「輸出驗證」→ 裁定「加官方對帳層」。容器驗證:2021-04-06 是交易日(櫃買官方指數 209.7 · 6488 官方成交
773 / 797 / 764 / 795),可是 tw_daily_prices · tw_trading_daily · tw_chip_inst 三表那天都沒有。
根因:本家族本體(v0107)的交易日曆 trading_days() = 「已庫 tw_daily_prices 實際日期(零猜測)」;日價表來自 Yahoo,
Yahoo 整個市場缺 2021-04-06(^TWII · 0050 · 6488.TWO 都沒有)→ 官方成交表永遠不排那天 → 官方對帳層(VDF_MDL032)也沒得補。
本版只改一件事:載入本體時把 trading_days 換成「原日曆 ∪ 同資料家 tw_index/VDF_TWIndex_Daily.duckdb 的櫃買 / 加權官方日期
(只取原日曆最早到最晚之間,不往前後延伸)」;指數庫不在 = 照原日曆。其餘(抓法 · 寫庫 upsert · 同意尺 · 驗證)全照 v0112。
不代設同意閘;不碰 TA-Lib;零網路自測(暫存庫 · 假本體)。
"""
from __future__ import annotations
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔自己不連網,連網的是回補本體。"""
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
import runpy
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG057_TradingValueBackfill"
VERSION = "v0113"
INDEX_CODES = ("TPEX", "TAIEX")


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_vdf_eng057_prior_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0112(main 以 runpy 跑前版鏈;import 不出網)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def index_db_for(db_tw) -> Path:
    """<資料家>/output_hub/mega/vdf_tw_market.duckdb → <資料家>/output_hub/tw_index/VDF_TWIndex_Daily.duckdb"""
    return Path(db_tw).parent.parent / "tw_index" / "VDF_TWIndex_Daily.duckdb"


def official_days(idx_db, lo: str, hi: str) -> list:
    p = Path(idx_db)
    if not p.is_file() or not lo or not hi:
        return []
    import duckdb
    try:
        con = duckdb.connect(str(p), read_only=True)
    except Exception:
        return []
    try:
        return [r[0] for r in con.execute(
            "SELECT DISTINCT CAST(date AS VARCHAR) FROM tw_index_daily WHERE index_code IN (?, ?) AND CAST(date AS VARCHAR) BETWEEN ? AND ? ORDER BY 1",
            [INDEX_CODES[0], INDEX_CODES[1], lo, hi]).fetchall()]
    except Exception:
        return []
    finally:
        con.close()


def patch_calendar(mod) -> bool:
    """本體(有 trading_days + DB_TW)載完後換日曆;已換過 / 不是本體 = 不動。"""
    td = getattr(mod, "trading_days", None)
    if not callable(td) or not hasattr(mod, "DB_TW") or getattr(td, "_v0113", False):
        return False

    def trading_days():
        days = list(td())
        if not days:
            return days
        extra = official_days(index_db_for(mod.DB_TW), min(days), max(days))
        return sorted(set(days) | set(extra))
    trading_days._v0113 = True
    trading_days._orig = td
    mod.trading_days = trading_days
    return True


_WRAP_V0112 = PRIOR._wrap_spec


def _wrap_spec_v0113(spec, p, hook):
    spec = _WRAP_V0112(spec, p, hook)
    if spec is None or spec.loader is None or p is None or not Path(p).name.startswith(_STEM + "_v"):
        return spec
    loader = spec.loader
    orig_exec = loader.exec_module

    def exec_module(module):
        orig_exec(module)
        if patch_calendar(module):
            hook.used.append(("交易日曆 ∪ 官方指數日", Path(p).name))
    loader.exec_module = exec_module
    return spec


PRIOR._wrap_spec = _wrap_spec_v0113


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    saved = sys.argv
    sys.argv = [str(PRIOR_PATH)] + a
    try:
        with PRIOR._Hook():
            runpy.run_path(str(PRIOR_PATH), run_name="__main__")    # v0112 的 main(它再以 runpy 跑前版鏈;鉤子疊在一起)
        return 0
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    finally:
        sys.argv = saved


def selftest() -> int:
    import duckdb
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""))

    PRIOR._wrap_spec = _WRAP_V0112
    try:
        rc0 = PRIOR.selftest()
    finally:
        PRIOR._wrap_spec = _wrap_spec_v0113
    print("=== %s %s 薄尾自測(交易日曆 ∪ 官方指數日;零網路)===" % (_STEM, VERSION))
    chk("⓪ 前版 v0112 自測過", rc0 == 0, f"rc {rc0}")
    with tempfile.TemporaryDirectory(prefix="eng057_v0113_") as td:
        home = Path(td) / "output_hub"
        (home / "mega").mkdir(parents=True)
        (home / "tw_index").mkdir()
        db_tw = home / "mega" / "vdf_tw_market.duckdb"
        con = duckdb.connect(str(home / "tw_index" / "VDF_TWIndex_Daily.duckdb"))
        con.execute("CREATE TABLE tw_index_daily(date VARCHAR, index_code VARCHAR, close DOUBLE)")
        con.executemany("INSERT INTO tw_index_daily VALUES (?, ?, 1)", [("2020-12-31", "TPEX"), ("2021-04-01", "TPEX"), ("2021-04-06", "TPEX"),
                                                                       ("2021-04-07", "TAIEX"), ("2030-01-02", "TPEX"), ("2021-04-06", "OTHER")])
        con.close()
        mod_src = Path(td) / f"{_STEM}_v9999.py"
        mod_src.write_text("from pathlib import Path\nDB_TW = Path(%r)\ndef trading_days():\n    return ['2021-04-01', '2021-04-07']\n" % str(db_tw),
                           encoding="utf-8")
        with PRIOR._Hook() as h:
            sp = importlib.util.spec_from_file_location("eng057_fake_body", mod_src)
            m = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(m)
        days = m.trading_days()
        chk("① 載本體時換日曆:原 04-01 · 04-07 ∪ 官方 04-06 = 三天;範圍外(2020-12-31 · 2030)與非指數代號不加",
            days == ["2021-04-01", "2021-04-06", "2021-04-07"] and ("交易日曆 ∪ 官方指數日", mod_src.name) in h.used, (days, h.used))
        sp2 = importlib.util.spec_from_file_location("eng057_fake_body2", mod_src)
        m2 = importlib.util.module_from_spec(sp2)
        sp2.loader.exec_module(m2)
        chk("② 鉤子外載入 = 原日曆(離開 with 一定還原)", m2.trading_days() == ["2021-04-01", "2021-04-07"])
        chk("③ 再換一次 = 不動(冪等)", patch_calendar(m) is False and m.trading_days() == days)
        m3 = type("M", (), {})()
        m3.DB_TW = Path(td) / "nohome" / "mega" / "x.duckdb"
        m3.trading_days = lambda: ["2021-04-01"]
        patch_calendar(m3)
        chk("④ 指數庫不在 → 照原日曆(不猜)", m3.trading_days() == ["2021-04-01"])
        m4 = type("M", (), {})()
        m4.DB_TW = db_tw
        m4.trading_days = lambda: []
        patch_calendar(m4)
        chk("⑤ 原日曆空(日價表還沒有)→ 空(不憑指數自己生出日曆)", m4.trading_days() == [])
    chk("⑥ 換裝:v0112 的擴充點 _wrap_spec = 本版", PRIOR._wrap_spec is _wrap_spec_v0113)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and "def _via_net" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print("  [計] %s %s 本版 %d/%d · %s" % (_STEM, VERSION, sum(ok), len(ok), "PASS" if all(ok) else "FAIL"))
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
