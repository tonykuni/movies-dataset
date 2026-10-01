#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG074_FredMacroSSOT v0107 — 薄尾:自測的「今天」固定在測資寫成的月份(引擎行為一字不動)

v0106→v0107(R46 2026-10-02 · 操作員令「單獨測試vdf所有引擎」「實際測試修正至成功」):VDF 74 支逐支經 VCGC 自測,本支 ⑤ 紅:
本體 v0103 自測的假 FRED 回應以 `observation_end=今天` 往回造月資料,斷言卻寫死最新一筆 `== "2026-09-01"` ——
測資是 2026-09 寫的,日曆一翻到 2026-10-01 就紅(實測:295 列 2000-01-01→2026-10-01)。這是測試時鐘的問題,不是擷取壞。
v0107 的自測:把 `datetime` 換成「今天 = 2026-09-24」的測試時鐘,重新載入整條委派鏈(v0106→v0105→v0104→v0103)跑前版自測,
跑完立刻還原;另一檢用真時鐘驗證引擎本身「最新一筆 = 本月 1 日」的行為(換月後該是 10-01 就是 10-01)。
main() / 公開面(FETCH_ACCEL · ssot_path · fetch_series …)全照 v0106。自測零網路(假網路物件);不用 TA-Lib。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
import importlib.util
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_TAIL_PRIOR = [p for p in sorted(HERE.glob("VDF_ENG074_FredMacroSSOT_v*.py")) if p.name < Path(__file__).name][-1]
FROZEN_TODAY = (2026, 9, 24)                     # 本體測資寫成的月份(⑤ 的 2026-09-01 由它而來)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load(_TAIL_PRIOR, "fred_prior_for_v0107")


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def main() -> int:
    return PRIOR.main()


def _frozen_datetime(y: int, m: int, d: int):
    import datetime as _dt

    class FrozenDate(_dt.date):
        @classmethod
        def today(cls):
            return cls(y, m, d)

    class FrozenDateTime(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(y, m, d, 12, 0, 0, tzinfo=tz)

        @classmethod
        def today(cls):
            return cls(y, m, d, 12, 0, 0)

    shim = types.ModuleType("datetime")
    shim.__dict__.update(_dt.__dict__)
    shim.date, shim.datetime = FrozenDate, FrozenDateTime
    return shim


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    import datetime as real_dt
    print("=== VDF_ENG074_FredMacroSSOT v0107 · 薄尾自測(測試時鐘固定 2026-09-24 跑前版;真時鐘另驗)===")
    text = Path(__file__).read_text(encoding="utf-8")
    chk("① 兩座橋在(加速器 · 網路);不含 TA-Lib 匯入", "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text
        and ("import " + "ta" + "lib") not in text)
    # C 擴充(duckdb · pyarrow · polars …)先用真 datetime 載好:它們在 C 層讀 datetime 型別大小,換成測試時鐘的子類別會崩(實測 segfault);
    # 測試時鐘只該作用在重載的 VIA 純 Python 模組(本體 `from datetime import date` 那一句)。
    for _ext in ("numpy", "pandas", "pyarrow", "pyarrow.parquet", "duckdb", "polars"):
        try:
            importlib.import_module(_ext)
        except Exception:
            pass
    saved = sys.modules["datetime"]
    sys.modules["datetime"] = _frozen_datetime(*FROZEN_TODAY)
    try:
        fresh = _load(_TAIL_PRIOR, "fred_prior_frozen_for_v0107")      # 整條鏈在測試時鐘下重載
        rc_prior = fresh.selftest()
    finally:
        sys.modules["datetime"] = saved
    chk("② 前版自測在測試時鐘(2026-09-24)下全過(⑤ 最新一筆 2026-09-01 · ⑥ observation_end=測試今天)", rc_prior == 0, f"rc {rc_prior}")
    chk("③ 跑完時鐘已還原(真 datetime 回到 sys.modules)", sys.modules["datetime"] is real_dt and real_dt.date.today().year >= 2026)
    # ④ 真時鐘:引擎本身以「今天」為 observation_end,最新一筆 = 本月 1 日(換月後跟著換,不寫死)
    import tempfile
    import duckdb
    impl = PRIOR._impl()
    calls = []

    class FakeNet:
        @staticmethod
        def http_json(url):
            import urllib.parse as up
            calls.append(url)
            q = dict(up.parse_qsl(up.urlsplit(url).query))
            d = real_dt.date.fromisoformat(q["observation_end"]).replace(day=1)
            obs = []
            while d.isoformat() >= q["observation_start"] and d.isoformat() >= "2020-01-01":
                obs.append({"date": d.isoformat(), "value": "1.0"})
                d = (d - real_dt.timedelta(days=1)).replace(day=1)
            return {"state": "OK", "data": {"observations": obs}}

    keep = {k: getattr(impl, k) for k in ("DB_GL", "PQ_DIR") if hasattr(impl, k)}
    with tempfile.TemporaryDirectory() as td:
        try:
            if "DB_GL" in keep:
                impl.DB_GL = Path(td) / "gl.duckdb"
            if "PQ_DIR" in keep:
                impl.PQ_DIR = Path(td) / "pq"
            meta = {"fred_id": "R46TEST", "via_code": "US.Test.R46", "freq": "Monthly", "unit": "", "theme": "Test",
                    "sub_theme": "Test", "indicator": "R46", "src": "TEST"}
            r = impl.fetch_series(FakeNet, "k", meta, "2020-01-01", 1000, {}, 0)
            con = duckdb.connect(str(impl.DB_GL), read_only=True)
            mx = con.execute(f"SELECT CAST(MAX(date) AS VARCHAR) FROM {impl.TABLE} WHERE series_id = 'R46TEST'"
                             if "series_id" in [c[1] for c in con.execute(f"PRAGMA table_info('{impl.TABLE}')").fetchall()]
                             else f"SELECT CAST(MAX(date) AS VARCHAR) FROM {impl.TABLE}").fetchone()[0]
            con.close()
            want = real_dt.date.today().replace(day=1).isoformat()
            chk("④ 真時鐘:引擎以今天為 observation_end,最新一筆 = 本月 1 日(不寫死月份)",
                r.get("state") == "OK" and mx == want and f"observation_end={real_dt.date.today().isoformat()}" in calls[0],
                f"{mx} == {want}")
        finally:
            for k, v in keep.items():
                setattr(impl, k, v)
    good = all(ok)
    print(f"  [計] VDF_ENG074 v0107 薄尾 {sum(ok)}/{len(ok)} · 合計 {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
