#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG054_TWDailyBackfill v0111 — 台股日資料歷史回補引擎(薄尾:狀態卡自測不看本機有沒有正式庫;R34 收尾實測)
v0110→v0111(R34 收尾實測):
  v0110 的自測拿**真的**正式庫路徑(v0109 的 DB_TW = VDF/output_hub/mega/vdf_tw_market.duckdb)驗「庫不在 = 失敗、不是綠的零」,
  斷言 present is False —— 只有沒有資料的機器才過。工作站抓過日價(正常狀態)自測就紅 → SDD 的 self:all 紅 →
  已鎖的 VCGC-WKF003 · VDF-WKF004 一跑就判回歸。容器探測輪(本機 output_hub 有庫)正是這樣紅的;收尾輪把容器本機資料
  暫移才綠 —— 綠的是容器,不是工作站。
  現在:狀態卡照前版(db_status() · main() 一字未動,平常讀的仍是正式庫、唯讀);自測把前版載入的 DB_TW 換成暫存路徑,
  五種庫況各驗一次(不在 · 從 2022-07-01 起有列 · 空表 · 起點晚於 2022-07-01 · 沒有日價表),前版自測在「暫存路徑不在」下照跑。
  正式庫零觸碰(不開、不建、不改大小與 mtime)。
  掛法:前版 db_status() / selftest() 經模組全域叫 _load() → 本支換掉它(只有自測設了暫存路徑才改 DB_TW)。零網路 · 不用 TA-Lib。
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
    VIA_ACCEL = None
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG054_TWDailyBackfill"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "VDF_ENG054_TWDailyBackfill_v0110.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("twbackfill_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
_PRIOR_LOAD = PRIOR._load
_TEST_DB: Path | None = None          # 只有自測設;平常 None = 照前版讀正式庫


def _load():
    """v0111:照前版載入回補引擎;自測設了暫存路徑時,DB_TW 指到那裡(正式庫零觸碰)。"""
    m = _PRIOR_LOAD()
    if _TEST_DB is not None:
        m.DB_TW = _TEST_DB
    return m


PRIOR._load = _load


def selftest() -> int:
    global _TEST_DB
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    import tempfile
    print(f"=== VDF_ENG054 台股日資料歷史回補 v{VERSION} · 薄尾自測(零網路;庫只在暫存夾)===")
    os.environ["VIA_FROM_VCGC"] = "YES"
    formal = _PRIOR_LOAD().DB_TW

    def snap(p: Path):
        return (p.stat().st_size, p.stat().st_mtime_ns) if p.is_file() else None

    before, on = snap(formal), None
    try:
        import duckdb
    except ImportError:
        duckdb = None

    def build(p: Path, rows, table=True):
        con = duckdb.connect(str(p))
        try:
            if table:
                con.execute("CREATE TABLE tw_daily_prices(date DATE, ticker VARCHAR, close DOUBLE)")
                for d in rows:
                    con.execute("INSERT INTO tw_daily_prices VALUES (?, '2330.TW', 1.0)", [d])
            else:
                con.execute("CREATE TABLE other(x INTEGER)")
        finally:
            con.close()

    with tempfile.TemporaryDirectory() as td:
        try:
            _TEST_DB = Path(td) / "absent" / "vdf_tw_market.duckdb"
            eng = _load()
            planned = dict(eng.plan([{"yf_ticker": "2330.TW"}], {}, "2026-09-25"))
            c1 = PRIOR.db_status()
            chk("① 庫不在(暫存路徑)→ present False · 失敗點名 database absent · 不算鎖定成功 · 沒有抓;空票起點 2022-07-01",
                c1["present"] is False and "database absent" in c1["failed"] and c1["lock_success"] is False
                and c1["fetched"] is False and planned.get("2330.TW") == PRIOR.START and c1["database"] == str(_TEST_DB),
                " · ".join(c1["failed"]))
            chk("② 前版自測在「暫存路徑不在」下照跑:rc 0(不再看本機有沒有正式庫)", PRIOR.selftest() == 0)
            ok3, note3 = False, "duckdb 缺(本境沒有:誠實不過,不假綠)"
            if duckdb is not None:
                good, empty, late, notab = (Path(td) / f"{n}.duckdb" for n in ("good", "empty", "late", "notab"))
                build(good, ["2022-07-01", "2022-07-04", "2024-01-05"])
                build(empty, [])
                build(late, ["2024-01-02", "2024-01-03"])
                build(notab, [], table=False)
                _TEST_DB = good
                c2 = PRIOR.db_status()
                _TEST_DB = empty
                c3 = PRIOR.db_status()
                _TEST_DB = late
                c4 = PRIOR.db_status()
                _TEST_DB = notab
                c5 = PRIOR.db_status()
                ok3 = (c2["present"] is True and c2["failed"] == [] and c2["lock_success"] is True and c2["rows"] == 3
                       and c2["earliest"] == "2022-07-01" and c2["end"] == "2024-01-05"
                       and c3["failed"] == ["tw_daily_prices empty"] and c3["lock_success"] is False
                       and c4["failed"] == ["earliest 2024-01-02 is after 2022-07-01"] and c4["lock_success"] is False
                       and len(c5["failed"]) == 2 and c5["failed"][0].startswith("tw_daily_prices unreadable: ")
                       and c5["failed"][1] == "tw_daily_prices empty")
                note3 = f"{c2['rows']} 列 · {c3['failed']} · {c4['failed']} · {c5['failed']}"
            chk("③ 有庫四況:從 2022-07-01 起有列 → 鎖定成功、end = 最後一天;空表 · 起點晚於 2022-07-01 · 沒有日價表 → 各自點名失敗",
                ok3, note3)
            on = _load().DB_TW
        finally:
            _TEST_DB = None
    chk("④ 換路徑只在自測設了才生效:設了 → 前版載入的 DB_TW 指到暫存;清掉 → 回到前版的正式庫路徑(不開正式庫);"
        "掛勾在位(前版 db_status / selftest 經模組全域叫到本支 _load)",
        PRIOR._load is _load and on != formal and _load().DB_TW == formal, str(formal)[-48:])
    chk("⑤ 正式庫零觸碰:自測前後在不在 · 大小 · mtime 完全一樣", snap(formal) == before,
        "不在" if before is None else f"{before[0]} 位元組")
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 本支帶加速器橋 · 網路橋;零網路(不 import 抓取套件)· 不含 TA-Lib 匯入",
        "[VIA:ACCEL-BRIDGE" in body and "[VIA:NET-BRIDGE" in body
        and not re.search(r"^\s*(?:import|from)\s+(?:requests|httpx|urllib)\b", body, re.M)
        and not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print(f"  [計] 六檢 OK {sum(ok)} · FAIL {len(ok) - sum(ok)}(② 內串前版自測 1 檢)")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
