#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG051_ActiveTWETF_Holdings v0104 — 薄尾(v0103 一字不改):DuckDB 2.x 相容 —— register 前先取完未完結果。

2026-11-10 容器實測(duckdb 2.0.0):v0103 自測 rc 3 ·
`ResourceInUseException: connection has an unfinished result from execute()`。根因:同一連線上先
`execute("SELECT COUNT(*) …").fetchone()` 只取一列、結果沒取完,DuckDB 2.x 不准接著 `register()`。
本版只在三個會 `con.register(...)` 的函式(def_register_universe_snapshot · def_upsert_holdings ·
def_insert_fetch_status)進入前把連線上未完的結果取完(沒有未完結果時什麼都不做),其餘名稱全數沿用 v0103。
DuckDB 1.x 沒有這條限制 —— 取完未完結果在 1.x 也無副作用。網路 / 同意閘行為不變(本檔不碰)。
"""
from __future__ import annotations
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
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

import importlib.util as _ilu
import json as _json
import sys as _sys
import tempfile as _tempfile
from pathlib import Path as _Path

VERSION = "v0104"
PRIOR = "VDF_ENG051_ActiveTWETF_Holdings_v0103.py"
_WRAPPED = ("def_register_universe_snapshot", "def_upsert_holdings", "def_insert_fetch_status")


def _load_prior():
    p = _Path(__file__).resolve().with_name(PRIOR)
    spec = _ilu.spec_from_file_location("VDF_ENG051_ActiveTWETF_Holdings_v0103", p)
    mod = _ilu.module_from_spec(spec)
    old = _sys.dont_write_bytecode
    _sys.dont_write_bytecode = True
    try:
        _sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    finally:
        _sys.dont_write_bytecode = old
    return mod


B = _load_prior()


def drain_pending(con) -> bool:
    """把連線上未取完的結果取完。回 True = 真的有取;沒有未完結果(或非 DuckDB 連線)回 False,不丟錯。"""
    try:
        con.fetchall()
        return True
    except Exception:  # noqa: BLE001 — 沒有開著的結果集時 duckdb 會丟錯,這裡就是「沒事可做」
        return False


def _wrap(fn):
    def inner(*args, **kwargs):
        con = kwargs.get("con", args[0] if args else None)
        if con is not None:
            drain_pending(con)
        return fn(*args, **kwargs)
    inner.__name__ = fn.__name__
    inner.__doc__ = fn.__doc__
    inner.__wrapped__ = fn
    return inner


for _n in _WRAPPED:
    if hasattr(B, _n) and not hasattr(getattr(B, _n), "__wrapped__"):
        setattr(B, _n, _wrap(getattr(B, _n)))   # 前版內部互呼叫也走包裝(模組全域)

# 前版公開名稱全部轉接(TAILAPI:尾版不少於前版)
for _k in dir(B):
    if not _k.startswith("__") and _k not in globals():
        globals()[_k] = getattr(B, _k)
for _n in _WRAPPED:
    if hasattr(B, _n):
        globals()[_n] = getattr(B, _n)


def selftest() -> int:
    checks = []

    def ck(name, cond, note=""):
        checks.append((name, bool(cond), note))

    try:
        import duckdb
        con = duckdb.connect(":memory:")
        con.execute("CREATE TABLE t AS SELECT * FROM range(3) r(x)")
        con.execute("SELECT COUNT(*) FROM t").fetchone()
        ck("有未完結果 → drain 回 True", drain_pending(con) is True)
        ck("drain 後可再 register", (con.register("v", con.execute("SELECT 1 AS a").df()) or True))
        ck("沒有未完結果 → drain 不丟錯", drain_pending(duckdb.connect(":memory:")) in (True, False))
        ck("非連線物件 → 回 False 不丟錯", drain_pending(object()) is False)
        ck("duckdb 版本有記", bool(duckdb.__version__), duckdb.__version__)
    except ImportError as e:
        ck("duckdb 可載入", False, str(e))
    ck("三個 register 函式都已包裝(前版模組全域)",
       all(hasattr(getattr(B, n), "__wrapped__") for n in _WRAPPED if hasattr(B, n)))
    ck("尾版保有前版公開名稱(TAILAPI)",
       all(n in globals() for n in dir(B) if not n.startswith("_") and callable(getattr(B, n))))
    rep = B.def_self_test(_Path(_tempfile.mkdtemp(prefix="vdf_eng051_v0104_")))
    ck("v0103 本體自測 all_pass(經 v0104 包裝)", rep.get("all_pass") is True,
       str(rep.get("unexpected_exception") or "")[:120])
    ok = sum(1 for _, c, _ in checks if c)
    for name, c, note in checks:
        print(("  [OK]   " if c else "  [FAIL] ") + name + (f" — {note}" if note else ""))
    print(f"[計] VDF_ENG051_ActiveTWETF_Holdings {VERSION} 薄尾 {ok}/{len(checks)} · " + ("PASS" if ok == len(checks) else "FAIL"))
    return 0 if ok == len(checks) else 1


def main(argv=None) -> int:
    argv = list(_sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    _sys.argv = [_sys.argv[0]] + argv
    return B.def_main()


if __name__ == "__main__":
    raise SystemExit(main())
