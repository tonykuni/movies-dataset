#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG242_ThreePeriodDistill v0104 — 薄尾(v0100–v0103 一字不動):蒸餾前先補「標的鍵」,不再把整表當衝突刪光

PR #749 Codex 審查(P1,讀碼屬實):VDF_FetchGroups_SSOT 尾版對 TW_PRICE_VOL 的 tw_daily_prices / tw_trading_daily
只給 date_col、沒給 key_col → v0100 distill_one 的主鍵只有日期 → 同一天不同股票全成 PK_CONFLICT →
「同主鍵不同值不輸出」那道把那幾天的列全部濾掉 → 正常的多檔價量表蒸餾出空表(而且照原子換新覆蓋掉舊檔)。
本版:
  ① key_col 沒給或表裡沒有 → 從表的欄名推「標的鍵」:先看 VDF 自己的欄名同義冊(正規名 code:證券代號 / 股票代號 / ticker / stock_id …),
     再看常見鍵名(index_code · series · series_id · etf_ticker · holding_ticker · indicator · country · symbol · ticker);推到就用,並記 key_inferred。
  ② 推不到鍵、而且「只靠日期當主鍵」會把列刪光(有衝突且輸出 0 列)→ 不換檔,回 NO_KEY(照實說,不寫空表蓋掉舊的)。
  ③ 每段期間仍照 v0100:鍵內最新三期 · 完全重複去掉 · 欄名對齊 · 同主鍵不同值 = PK_CONFLICT 不猜。
不動來源冊(FetchGroups_SSOT 是 VDF 的冊,要補 key_col 另出冊版;本版先在讀的時候補)。唯讀開庫;不出網;不用 TA-Lib;不設同意閘。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
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

import importlib.util
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG242_ThreePeriodDistill"
VERSION = "v0104"
TAG = f"{STEM} {VERSION}"
KEY_NAMES = ("code", "stock_id", "ticker", "symbol", "index_code", "series", "series_id", "etf_ticker", "holding_ticker",
             "indicator", "country", "證券代號", "股票代號", "公司代號", "代號")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{PRIOR_PATH.stem}_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                   # v0100 本體(do_distill 依模組全域名叫 distill_one)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def infer_key(cols: list, nb: dict, date_col) -> str | None:
    """同義冊正規名 code 優先 → 常見鍵名;日期欄不算。推不到回 None。"""
    rev = (nb or {}).get("rev") or {}
    nn = BASE.norm_name
    for c in cols:
        if c != date_col and rev.get(nn(c)) == "code":
            return c
    low = {nn(k) for k in KEY_NAMES}
    for c in cols:
        if c != date_col and nn(c) in low:
            return c
    return None


_ORIG = BASE.distill_one


def distill_one(con, rel: str, date_col, key_col, nb: dict, n: int, out_path: Path) -> dict:
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {rel}").fetchall()]
    inferred = None
    if not key_col or key_col not in cols:
        inferred = infer_key(cols, nb, date_col)
        key_col = inferred or key_col
    if key_col and key_col in cols:
        res = _ORIG(con, rel, date_col, key_col, nb, n, out_path)
        if inferred:
            res["key_inferred"] = inferred
        return res
    probe = out_path.with_name(out_path.name + f".{os.getpid()}.probe.parquet")
    res = _ORIG(con, rel, date_col, None, nb, n, probe)            # 先寫到旁邊試,確定不會把列刪光才換上
    try:
        if res.get("state") == "PK_CONFLICT" and not res.get("rows"):
            return {"state": "NO_KEY", "rows": 0, "pk": res.get("pk"), "pk_conflicts": res.get("pk_conflicts"),
                    "note": "沒有標的鍵:只靠日期當主鍵會把整段刪光 → 不換檔(冊上補 key_col 或欄名同義)"}
        if probe.exists():
            os.replace(probe, out_path)
        return res
    finally:
        if probe.exists():
            probe.unlink()


def _install():
    BASE.distill_one = distill_one
    BASE.TAG = TAG


def _uninstall():
    BASE.distill_one = _ORIG
    BASE.TAG = PRIOR.TAG


_install()


def main() -> int:
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        return selftest()
    return BASE.main()


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    chk("已裝進 v0100 本體(do_distill 叫的 distill_one 是本版)· 橫幅寫本版", BASE.distill_one is distill_one and BASE.TAG == TAG)
    duckdb = BASE._duck()
    nb = BASE.name_book() if callable(getattr(BASE, "name_book", None)) else {"rev": {}}
    con = duckdb.connect()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        con.execute("CREATE TABLE px AS SELECT * FROM (VALUES "
                    "('2026-11-24','2330',1000.0),('2026-11-24','2317',200.0),('2026-11-25','2330',1010.0),('2026-11-25','2317',201.0),"
                    "('2026-11-26','2330',1020.0),('2026-11-26','2317',202.0),('2026-11-21','2330',990.0)) t(date, stock_id, close)")
        old = BASE.distill_one
        _uninstall()
        try:
            r0 = BASE.distill_one(con, "px", "date", None, nb, 3, td / "v0100.parquet")
        finally:
            _install()
        chk("重現 Codex P1:v0100 沒 key_col → 只靠日期 → 多檔同日全衝突 → 0 列",
            r0["state"] == "PK_CONFLICT" and r0["rows"] == 0, r0)
        r1 = distill_one(con, "px", "date", None, nb, 3, td / "v0104.parquet")
        chk("本版:推到標的鍵 stock_id(同義冊 → code)· 每檔最新三期 · 6 列 · 不衝突",
            r1["state"] == "OK" and r1["rows"] == 6 and r1.get("key_inferred") == "stock_id", r1)
        con.execute("CREATE TABLE idx AS SELECT * FROM (VALUES ('2026-11-25','TAIEX',1.0),('2026-11-25','OTC',2.0)) t(date, index_code, v)")
        r2 = distill_one(con, "idx", "date", None, nb, 3, td / "idx.parquet")
        chk("常見鍵名 index_code 也推得到", r2["state"] == "OK" and r2["rows"] == 2 and r2.get("key_inferred") == "index_code", r2)
        con.execute("CREATE TABLE nokey AS SELECT * FROM (VALUES ('2026-11-25', 1.0),('2026-11-25', 2.0)) t(date, v)")
        keep_file = td / "nokey.parquet"
        con.execute(f"COPY (SELECT 1 AS old) TO '{keep_file.as_posix()}' (FORMAT PARQUET)")
        r3 = distill_one(con, "nokey", "date", None, nb, 3, keep_file)
        kept = con.execute(f"SELECT * FROM read_parquet('{keep_file.as_posix()}')").fetchall()
        chk("推不到鍵且只靠日期會刪光 → NO_KEY · 舊檔不被空表蓋掉 · 不留試寫檔",
            r3["state"] == "NO_KEY" and kept == [(1,)] and not list(td.glob("*.probe.parquet")), (r3, kept))
        con.execute("CREATE TABLE daily AS SELECT * FROM (VALUES ('2026-11-24', 1.0),('2026-11-25', 2.0)) t(date, v)")
        r4 = distill_one(con, "daily", "date", None, nb, 3, td / "daily.parquet")
        chk("真的一天一列(沒有鍵也沒衝突)→ 照常輸出 2 列", r4["state"] == "OK" and r4["rows"] == 2, r4)
        r5 = distill_one(con, "px", "date", "stock_id", nb, 3, td / "given.parquet")
        chk("冊上有給 key_col → 照用,不另推(不記 key_inferred)", r5["state"] == "OK" and r5["rows"] == 6 and "key_inferred" not in r5, r5)
        _ = old
    con.close()
    _uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        _install()
    chk("前版 v0103 鏈自測(本版換裝卸下)照過", rc == 0, rc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:雙橋在 · 零 TA-Lib · 不設同意閘",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
