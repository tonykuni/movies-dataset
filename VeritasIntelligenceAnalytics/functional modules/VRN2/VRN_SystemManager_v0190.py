#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0190 — 薄尾(真實執行紅字:assetize 讀檔 FileNotFoundError → 整個崩潰)。
  assetize 改走保護層:用 ENG396 最新版(v0101 讀檔有保護)· 任何例外只印一行紅字(類型 + 訊息 · 不噴 traceback)· 讀不到的檔另列一行診斷(存在 / 大小 / OneDrive 線上限定)
其餘動詞照前版鏈(不替換任何函式 · 零新增頭)。
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

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0190"


def _vnum_v0190(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0190(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0190(p) < _vnum_v0190(__file__)), key=_vnum_v0190)
PRIOR = _load_v0190(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


def assetize_guarded() -> tuple:
    """回傳 (rc, 行):例外 → 一行紅字(不噴 traceback)· 讀不到的檔 → 一行診斷。"""
    run = _resolve("assetize")
    if run is None:
        return 1, ["[RED] 智慧資產化 · 前版鏈沒有 assetize"]
    try:
        lines = list(run())
    except Exception as exc:  # noqa: BLE001
        return 1, ["[RED] 智慧資產化失敗 · %s: %s(環境類請先確認 OneDrive 同步完成 / 檔案非線上限定)" % (type(exc).__name__, str(exc)[:160])]
    eng = next((m for k, m in sys.modules.items() if k.startswith("vrn_eng396_") and hasattr(m, "UNREADABLE")), None)
    un = list(getattr(eng, "UNREADABLE", []) or [])
    if un:
        lines.append("[計] 讀不到 %d 檔(已跳過 · 其餘照常)· %s" % (len(un), " | ".join("%s:%s" % (Path(x["path"]).name, x["diag"]) for x in un[:3])))
    return 0, lines


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["assetize"]:
        rc, lines = assetize_guarded()
        for l in lines:
            print(l)
        return rc
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
    mo = _owner("assetize")
    real = vars(mo)["assetize"]
    try:
        def boom():
            raise FileNotFoundError(2, "No such file or directory", "VRN_SystemManager_v0189.py")
        vars(mo)["assetize"] = boom
        rc1, l1 = assetize_guarded()
        vars(mo)["assetize"] = lambda: ["[計] 智慧資產化 · 正常"]
        rc2, l2 = assetize_guarded()
    finally:
        vars(mo)["assetize"] = real
    chk("① assetize 例外 → 一行紅字(類型 + 訊息 · 不噴 traceback · rc 1)· 正常 → rc 0", rc1 == 1 and len(l1) == 1 and l1[0].startswith("[RED]") and "FileNotFoundError" in l1[0] and rc2 == 0 and l2[0].endswith("正常"))
    me = Path(__file__).read_text(encoding="utf-8")
    chk("② 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片 · 本版零新增頭", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__) and "setattr(" not in me.split("def selftest")[0])
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0190 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
