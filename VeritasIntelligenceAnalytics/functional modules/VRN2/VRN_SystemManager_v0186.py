#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0186 — 薄尾(操作員 2026-10-11「BASIC EPS / DILUTED EPS 要區分 · EPS 則用歷史對照法 · 及兩 EPS 最低數且歷史值對齊」)。
  eps_classify 加歷史對齊(替換一頭):① 名稱寫明基本 / 稀釋 → 照名稱 · 仍做歷史對照 · 不符只標「歷史對照不符」② 單列 EPS → 歷史對照法(前版)
  ③ 兩列 EPS → 先取小 = 稀釋 → 歷史值對齊確認(✓)· 歷史方向相反 → 以歷史為準對調 · 資料庫沒有歷史 → 維持取小 · 標「未經歷史對照」
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import functools
import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0186"


def _vnum_v0186(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0186(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0186(p) < _vnum_v0186(__file__)), key=_vnum_v0186)
PRIOR = _load_v0186(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


def _patch_v(name: str, fn):
    mo = _owner(name)
    if mo is None or getattr(vars(mo)[name], "_v186", False):
        return None
    prev = vars(mo)[name]
    functools.update_wrapper(fn, prev)
    fn._v186 = True
    fn._prev = prev
    setattr(mo, name, fn)
    return prev


def hist_match(row: dict, db: dict) -> tuple:
    """列的歷史年度值 vs 資料庫 → (對上稀釋期數, 對上基本期數, 可比期數)。"""
    pk, ptype = _resolve("_pkey") or (lambda p: None), _resolve("ptype") or (lambda p: "歷史")
    hd = hb = tot = 0
    for c in row.get("cells") or []:
        v, per = c.get("value"), c.get("period")
        k = pk(per)
        if not isinstance(v, (int, float)) or ptype(per) != "歷史" or not k or k[1] or k[0] not in db:
            continue
        tot += 1
        ref, tol = db[k[0]], max(0.011, abs(v) * 0.01)
        hd += 1 if ref.get("diluted") is not None and abs(ref["diluted"] - v) <= tol else 0
        hb += 1 if ref.get("basic") is not None and abs(ref["basic"] - v) <= tol else 0
    return hd, hb, tot


def eps_classify_v186(rows: list, code: str = "", dbe: dict = None) -> list:
    res = {i: [c, w] for i, c, w in eps_classify_v186._prev(rows, code, dbe)}
    db = (dbe or {}).get(code) or {}
    pair = [i for i, (c, w) in res.items() if "兩列" in w]
    if len(pair) == 2:
        a, b = sorted(pair, key=lambda i: res[i][0] != "DILUTED_EPS")          # a = 取小判的稀釋 · b = 基本
        if not db:
            for i in pair:
                res[i][1] += " · 資料庫沒有歷史 → 未經歷史對照"
        else:
            da, ba, ta = hist_match(rows[a], db)
            db_, bb, tb = hist_match(rows[b], db)
            if ta and da == ta:
                res[a][1] += " · 歷史 %d 期 = 資料庫稀釋 → 歷史對齊 ✓" % ta
                res[b][1] += " · 對方已歷史對齊"
            elif tb and db_ == tb and not (ta and da == ta):
                res[a], res[b] = ["BASIC_EPS", "兩列取小原判稀釋 · 歷史推翻 → 改基本"], ["DILUTED_EPS", "歷史 %d 期 = 資料庫稀釋 → 歷史推翻兩列取小 · 改稀釋" % tb]
            else:
                for i in pair:
                    res[i][1] += " · 歷史對不上資料庫(未對齊)"
    for i, (c, w) in res.items():
        if c in ("DILUTED_EPS", "BASIC_EPS") and "名稱寫明" in w and db:
            hd, hb, tot = hist_match(rows[i], db)
            if tot:
                want = hd if c == "DILUTED_EPS" else hb
                res[i][1] += " · 歷史 %d 期%s" % (tot, " 對齊 ✓" if want == tot else " · 歷史對照不符(名稱照保留)")
    return [(i, res[i][0], res[i][1]) for i in sorted(res)]


_patch_v("eps_classify", eps_classify_v186)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    R = lambda lab, vals: {"label_raw": lab, "std": "eps", "cells": [{"period": k, "value": v} for k, v in vals.items()]}  # noqa: E731
    ec = _resolve("eps_classify")
    db = {"1111": {23: {"basic": 10.2, "diluted": 10.0}, 24: {"basic": 12.3, "diluted": 12.0}}}
    two = [R("EPS", {"2023A": 10.2, "2024A": 12.3, "2025F": 14.0}), R("EPS", {"2023A": 10.0, "2024A": 12.0, "2025F": 13.6})]
    r1 = ec(two, "1111", db)
    chk("① 兩列 EPS:取小 = 稀釋 → 歷史 2 期 = 資料庫稀釋 → 歷史對齊 ✓ · %s" % r1[1][2][-22:], [c for _, c, _ in r1] == ["BASIC_EPS", "DILUTED_EPS"] and "對齊 ✓" in r1[1][2])
    db2 = {"2222": {23: {"basic": 10.0, "diluted": 10.2}, 24: {"basic": 12.0, "diluted": 12.3}}}
    r2 = ec(two, "2222", db2)
    chk("② 歷史方向相反(大的那列才 = 資料庫稀釋)→ 以歷史為準對調 · %s" % r2[0][2][-26:], [c for _, c, _ in r2] == ["DILUTED_EPS", "BASIC_EPS"] and "歷史推翻" in r2[0][2])
    r3 = ec(two, "9999", db)
    chk("③ 資料庫沒有這檔歷史 → 維持取小 · 標「未經歷史對照」", [c for _, c, _ in r3] == ["BASIC_EPS", "DILUTED_EPS"] and all("未經歷史對照" in w for _, _, w in r3))
    r4 = ec([R("Diluted EPS (NT$)", {"2023A": 10.2, "2024A": 12.3})], "1111", db)
    chk("④ 名稱寫明稀釋但歷史對上的是基本 → 名稱照保留 · 標「歷史對照不符」", r4[0][1] == "DILUTED_EPS" and "歷史對照不符" in r4[0][2])
    r5 = ec([R("EPS", {"2023A": 10.0, "2024A": 12.0, "2025F": 13.6})], "1111", db)
    chk("⑤ 單列 EPS → 歷史對照法:2 期 = 資料庫稀釋 → 稀釋(前版規則不變)", r5[0][1] == "DILUTED_EPS")
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑦ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0186 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
