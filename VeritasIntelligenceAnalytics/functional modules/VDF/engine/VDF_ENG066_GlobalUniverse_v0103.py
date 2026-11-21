#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG066_GlobalUniverse v0103 — 薄尾:空庫第一次跑先建 global_daily(若不在),不再一開庫就 CatalogException。

操作員 2026-11-21 令:「三個都是獨立系統 授權給你做到 VDF 輸出資料且快」「VDF/VRN 一定要輸出」。
容器開閘實跑(VDF 啟動器 v0106 · 擷取群 vdf_global_market · e066 → v0102):rc 1「Catalog Error: Table with name global_daily
does not exist」· 網路計數 0;db check 也報 global_daily 缺表(桌機上次 203,924 列)。
根因:v0102 的 run 一開庫就 SELECT count(*) FROM global_daily;這張表在桌機是舊流程早就建好的,本引擎自己從沒建過
→ 空庫(新機、容器、資料庫重建)第一次跑必倒,一個請求都沒發,global_daily 永遠是空的。
本版只改一件事:run 在過了同意閘與日期檢查之後、開庫之前,CREATE TABLE IF NOT EXISTS global_daily
(欄位照 v0102 寫入時用的那 8 欄:date · ticker · open · high · low · close · adj_close · volume;已在 = 零動作、資料不動)。
其餘(宇宙冊 · 雙同意閘 fail-closed · anti-join 只補缺 · 每批落盤)全照 v0102。零網路自測(暫存庫);不代設同意閘;不碰 TA-Lib。
用法同前:run [--cats …] [--start …] [--end …] | --list | --selftest
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
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG066_GlobalUniverse"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
GLOBAL_DAILY_DDL = ("CREATE TABLE IF NOT EXISTS global_daily(date VARCHAR, ticker VARCHAR, open DOUBLE, high DOUBLE, "
                    "low DOUBLE, close DOUBLE, adj_close DOUBLE, volume BIGINT)")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_RUN_V0102 = PRIOR.run


def __getattr__(name):
    return getattr(PRIOR, name)


def ensure_table(db=None) -> bool:
    """global_daily 不在就建(8 欄);回「這次有沒有新建」。已在 = 零動作。"""
    import duckdb
    p = Path(db or PRIOR.DB_GL)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(p))
    try:
        had = bool(con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'global_daily'").fetchone()[0])
        if not had:
            con.execute(GLOBAL_DAILY_DDL)
        return not had
    finally:
        con.close()


def run(cats=None, start: str = None, end=None) -> int:
    """同 v0102 run;過了同意閘與日期檢查才建表(閘沒開 / 日期錯 = 照前版拒跑、零動作)。"""
    start = start or PRIOR.DEFAULT_START
    gates = os.environ.get("VIA_NET_CONSENT") == "YES" and os.environ.get("VIA_SCRAPE_CONSENT") == "YES"
    if gates and PRIOR.DATE_RX.match(start) and (not end or PRIOR.DATE_RX.match(end)):
        if ensure_table():
            print("  [全球宇宙] global_daily 不在 → 建空表(8 欄)後照常補抓", flush=True)
    return _RUN_V0102(cats, start, end)


PRIOR.run = run                                  # v0102 的 main 以模組全域叫 run


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    import tempfile
    import duckdb
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    PRIOR.run = _RUN_V0102
    try:
        rc0 = PRIOR.selftest()
    finally:
        PRIOR.run = run
    print(f"=== {TAG} · 薄尾自測(空庫先建 global_daily;零網路)===")
    chk("⓪ 前版 v0102 八檢自測過", rc0 == 0, f"rc {rc0}")
    keep_db, keep_env = PRIOR.DB_GL, {k: os.environ.get(k) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    keep_net, keep_pick = PRIOR._net, PRIOR.pick_symbols
    with tempfile.TemporaryDirectory(prefix="eng066_v0103_") as td:
        db = Path(td) / "mega" / "vdf_global_market.duckdb"
        try:
            PRIOR.DB_GL = db
            for k in keep_env:
                os.environ[k] = "YES"
            seen = []

            class FakeNet:
                def yahoo_chart(self, batch, se, ee, pause_s=0):
                    seen.append(list(batch))
                    return {"rows": [{"date": "2026-11-20", "ticker": t, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5,
                                      "adj_close": 1.5, "volume": 10} for t in batch]}
            PRIOR._net = lambda: FakeNet()
            PRIOR.pick_symbols = lambda cats: (["^GSPC", "NVDA"], [])
            err = None
            try:
                _RUN_V0102(None, "2026-11-01", None) if db.parent.mkdir(parents=True, exist_ok=True) is None and \
                    duckdb.connect(str(db)).close() is None else None
            except Exception as e:                     # 重現:前版在空庫一開就倒
                err = type(e).__name__ + ": " + str(e)[:80]
            chk("① 重現:前版 v0102 在空庫 run → CatalogException(global_daily 不在)· 沒發請求",
                err is not None and "global_daily" in err and not seen, err)
            rc1 = run(None, "2026-11-01", None)
            con = duckdb.connect(str(db), read_only=True)
            n1 = con.execute("SELECT count(*) FROM global_daily").fetchone()[0]
            cols = [r[0] for r in con.execute("DESCRIBE global_daily").fetchall()]
            con.close()
            chk("② 本版:空庫先建 8 欄表 → 照常補抓寫入 2 列 · rc 0",
                rc1 == 0 and n1 == 2 and cols == ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"], (rc1, n1, cols))
            rc2 = run(None, "2026-11-01", None)
            con = duckdb.connect(str(db), read_only=True)
            n2 = con.execute("SELECT count(*) FROM global_daily").fetchone()[0]
            con.close()
            chk("③ 再跑一次:表已在 = 零動作建表 · anti-join 不重複(仍 2 列)", rc2 == 0 and n2 == 2 and ensure_table(db) is False, n2)
            os.environ["VIA_NET_CONSENT"] = "NO"
            db2 = Path(td) / "gated" / "g.duckdb"
            PRIOR.DB_GL = db2
            rc3 = run(None, "2026-11-01", None)
            chk("④ 同意閘沒開 → 照前版拒跑 rc 2 · 不建庫不建表(零動作)", rc3 == 2 and not db2.exists(), rc3)
        finally:
            PRIOR.DB_GL, PRIOR._net, PRIOR.pick_symbols = keep_db, keep_net, keep_pick
            for k, v in keep_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    chk("⑤ 換裝:v0102 main 叫到的 run = 本版", PRIOR.run is run)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑥ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘(自測外)", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑦ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
