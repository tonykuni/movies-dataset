#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""
VDF_ENG054_TWDailyBackfill v0112 — 薄尾:回補工人一跑就倒的那一行補上(清掉非主動式 ETF 時沒給庫路徑)· 加 worker 動詞

2026-11-18 容器開閘實測(VDF_MDL008 e054,擷取冊指向 v0109 回補工人):
  [清單] 雙所 + 主動式台股 ETF 2017 檔落庫 → 例外 TypeError: connect_retry() missing 1 required positional argument: 'path' → rc 1
  tw_daily_prices 沒建起來 → e057 成交值、e056 籌碼接著倒(Table with name tw_daily_prices does not exist)。
根因:v0108 新增 purge_other_etfs()(官方 ETF 冊有回來時,刪掉庫裡不是主動式台股的 ETF),裡面寫成
  con = connect_retry(read_only=False)      ← 少了庫路徑
這一行只有「庫已存在 + 官方 ETF 冊這次有抓到」才會走到,自測全是假網路、走不到,所以 v0108 / v0109 自測都綠、實跑必倒。
這不是環境問題:桌機的庫本來就在,每次真擷取都會倒在這裡。

本版(v0109 一字不動、不重寫):
  ① 回補本體載入後,把它的 connect_retry 換成「沒給路徑 = 用本體當下的 DB_TW」;有給路徑的呼叫照原樣轉交(庫鎖重試律不變)。
  ② main:第一個參數是 worker → 跑回補工人(v0109 的 main,其餘參數原樣交給它:--limit N · --full · --status);
          其他情況照前版(v0110 / v0111 的唯讀狀態卡),所以尾版預設仍然不會自己開始回補。
  ③ 擷取冊要指到本檔並帶 run_args ["worker"](VDF_FetchSystem_SSOT 新版;冊是 VDF 自己的)。
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
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG054_TWDailyBackfill"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("twbackfill_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_PRIOR_LOAD = PRIOR._load              # 前版的載入器(v0111 包過;回傳回補本體模組)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def patch_connect(m):
    """本體的 connect_retry:沒給路徑 = 用本體當下的 DB_TW;有給的照原樣。同一個模組只包一次。"""
    orig = m.connect_retry
    if getattr(orig, "_via_v0112", False):
        return m

    def connect_retry(path=None, read_only: bool = False):
        return orig(m.DB_TW if path is None else path, read_only=read_only)

    connect_retry._via_v0112 = True
    connect_retry._orig = orig
    m.connect_retry = connect_retry
    return m


def _load():
    """照前版載入回補本體,再補上 connect_retry 的預設路徑。"""
    return patch_connect(_PRIOR_LOAD())


# 前版的 _load 不換:狀態卡只讀、走不到清 ETF 那一行;換了反而動到 v0111 自己驗的掛勾。


def worker(argv: list) -> int:
    """跑回補工人:本體 v0109 的 main(--limit N · --full · --status · --selftest 都是它原本的)。"""
    m = _load()
    saved = sys.argv
    sys.argv = [str(getattr(m, "__file__", "VDF_ENG054_worker"))] + list(argv)
    try:
        return int(m.main() or 0)
    finally:
        sys.argv = saved


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] == "worker":
        return worker(a[1:])
    if "--selftest" in a:
        return selftest()
    return PRIOR.main()                # 照前版:唯讀狀態卡,不回補


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== VDF_ENG054 台股日資料歷史回補 v{VERSION} · 薄尾自測(零網路;庫只在暫存夾;正式庫零觸碰)===")
    os.environ["VIA_FROM_VCGC"] = "YES"
    try:
        import duckdb
    except ImportError:
        duckdb = None
    raw = _PRIOR_LOAD()                              # 沒修的本體(負控用)
    formal = raw.DB_TW

    def snap(p: Path):
        return (p.stat().st_size, p.stat().st_mtime_ns) if p.is_file() else None

    before = snap(formal)
    if duckdb is None:
        chk("① duckdb 在(不在就量不到這個錯)", False, "沒有 duckdb:SKIP 不是綠")
    else:
        with tempfile.TemporaryDirectory(prefix="eng054_v0112_") as td:
            db = Path(td) / "vdf_tw_market.duckdb"

            def build():
                if db.exists():
                    db.unlink()
                con = duckdb.connect(str(db))
                con.execute("CREATE TABLE tw_listings (code VARCHAR, name VARCHAR)")
                con.execute(raw.PRICE_DDL)
                con.executemany("INSERT INTO tw_listings VALUES (?, ?)", [("2330", "台積電"), ("0050", "元大台灣50"), ("00981A", "主動統一台股增長"), ("00402A", "主動安聯美國科技")])
                con.executemany("INSERT INTO tw_daily_prices VALUES (?, ?, 1, 1, 1, 1, 1, 1)", [("2026-11-17", t) for t in ("2330", "0050", "00981A", "00402A")])
                con.close()

            def rows():
                con = duckdb.connect(str(db), read_only=True)
                try:
                    return (sorted(r[0] for r in con.execute("SELECT code FROM tw_listings").fetchall()),
                            sorted(r[0] for r in con.execute("SELECT DISTINCT ticker FROM tw_daily_prices").fetchall()))
                finally:
                    con.close()

            build()
            raw.DB_TW = db
            err = ""
            try:
                raw.purge_other_etfs({"00981A"})
            except TypeError as exc:
                err = str(exc)
            chk("① 負控:沒修的本體清 ETF 時真的倒在少路徑(就是實測那個錯)", "path" in err and "connect_retry" in err, err[:90])
            chk("① 負控倒了之後庫沒被動到", rows() == (["00402A", "0050", "00981A", "2330"], ["00402A", "0050", "00981A", "2330"]))

            m = _load()
            m.DB_TW = db
            got = m.purge_other_etfs({"00981A"})
            lst, px = rows()
            chk("② 修好:同一個庫清得掉 —— 被動 ETF(0050)與國外成分 A 碼(00402A)刪,主動式台股 ETF 與個股留",
                lst == ["00981A", "2330"] and px == ["00981A", "2330"] and got == {"listings": 2, "prices": 2}, f"{got} · 清單 {lst}")
            again = m.purge_other_etfs({"00981A"})
            chk("③ 再跑一次零刪除(不會越刪越多)", again == {"listings": 0, "prices": 0} and rows() == (["00981A", "2330"], ["00981A", "2330"]))
            con = m.connect_retry(db, read_only=True)
            n = con.execute("SELECT COUNT(*) FROM tw_daily_prices").fetchone()[0]
            con.close()
            chk("④ 有給路徑的呼叫照原樣(唯讀開得起來)", n == 2)
            chk("⑤ 同一個模組只包一次;原函式留著", patch_connect(m).connect_retry._via_v0112 and m.connect_retry._orig is not m.connect_retry
                and patch_connect(m).connect_retry is m.connect_retry)
            gone = Path(td) / "nope.duckdb"
            m.DB_TW = gone
            chk("⑥ 庫不在:清 ETF 直接回零、不建庫", m.purge_other_etfs({"00981A"}) == {"listings": 0, "prices": 0} and not gone.exists())

            calls = []
            m2 = _load()
            m2.DB_TW = db
            real_main = m2.main
            saved_loader = globals()["_load"]

            def fake_load():
                m2.main = lambda: calls.append(list(sys.argv[1:])) or 0
                return m2

            globals()["_load"] = fake_load
            try:
                rc = main(["worker", "--limit", "3", "--full"])
            finally:
                globals()["_load"] = saved_loader
                m2.main = real_main
            chk("⑦ worker 動詞:其餘參數原樣交給回補工人,跑完 sys.argv 還原", rc == 0 and calls == [["--limit", "3", "--full"]] and "worker" not in sys.argv[1:2])
    status_calls = []
    saved_main = PRIOR.main
    PRIOR.main = lambda: status_calls.append(1) or 0
    try:
        main([])
        main(["--status"])
    finally:
        PRIOR.main = saved_main
    chk("⑧ 沒打 worker:照前版走唯讀狀態卡,不會自己開始回補", len(status_calls) == 2)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋真的匯入 · 網路工具橋在 · 不含本機路徑 · 不釘前版檔名", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "via_net_unified_v*.py" in src
        and ("C:" + "\\Users") not in src and (_STEM + "_v0111.py") not in src.replace("_v0111.py 一字", ""))
    rc_prior = PRIOR.selftest()
    chk("⑩ 前版鏈自測照過(v0111 · v0110 · v0109 本體十二檢)", rc_prior == 0, f"rc {rc_prior}")
    chk("⑪ 正式庫零觸碰(大小與 mtime 沒變)", snap(formal) == before, str(formal.name))
    good = all(ok)
    print(f"[計] VDF_ENG054_TWDailyBackfill v{VERSION} 本版 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
