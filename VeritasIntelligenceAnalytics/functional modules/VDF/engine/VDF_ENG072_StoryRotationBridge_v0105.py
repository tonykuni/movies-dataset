#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG072_StoryRotationBridge v0105 — 薄尾:台股庫不在時 export() 照實回 NODATA(自測不再崩)

v0104→v0105(R46 2026-10-02 · 操作員令「單獨測試vdf所有引擎」「實際測試修正至成功」):VDF 74 支逐支經 VCGC 自測,本支 ② 紅後接著
FileNotFoundError 崩掉。量到的:容器裡沒有台股庫 → export() 只回 {"err": "DB_TW 缺"},沒有 state;v0103 自測只認
state == "NODATA" 才走「上游缺料 → 誠實跳過」那條路(批584),於是落到 ② FAIL,再去讀不存在的 parquet → 崩。
v0105:export() 回 err「DB_TW 缺」時,另補 state = NODATA · missing_tables · why(err 原樣保留,既有呼叫端照讀 err 不受影響)。
庫在時一字不動。`--selftest-tail` 只跑本尾版四檢(交接案用)。自測照前版:沒庫 → NODATA rc 2(缺料不是壞掉);有庫 → 照跑八檢。零網路 · 不安裝 · 不用 TA-Lib。
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG072_StoryRotationBridge"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("storyrot_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _owner(attr: str):
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if callable(vars(m).get(attr)) and "INP" in vars(m):
            return m
        m = vars(m).get("PRIOR")
    return None


BODY = _owner("export")
_EXPORT0 = BODY.export


def export(*a, **k) -> dict:
    out = _EXPORT0(*a, **k)
    if isinstance(out, dict) and not out.get("state") and "缺" in str(out.get("err") or ""):
        out["state"] = "NODATA"
        out.setdefault("missing_tables", ["(台股庫檔不在:" + str(out.get("err")) + ")"])
        out.setdefault("why", "台股庫還沒建好/不在本境 → 缺料不是壞掉;工作站有庫時照常匯出(先跑 VDF 擷取 / via-datahome)")
    return out


BODY.export = export                      # 本體 selftest / run 以模組全域叫 export → 走本版


def main() -> int:
    if "--selftest-tail" in sys.argv[1:]:
        return selftest(tail_only=True)
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest(tail_only: bool = False) -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print("=== VDF_ENG072 故事輪動橋 v0105 · 薄尾自測(庫不在 = NODATA,不崩)===")
    keep = BODY.export
    BODY.export = export
    fake = lambda *a, **k: {"files": {}, "stats": {}, "err": "DB_TW 缺"}      # noqa: E731
    real0 = globals()["_EXPORT0"]
    globals()["_EXPORT0"] = fake
    try:
        r = export(do_print=False)
    finally:
        globals()["_EXPORT0"] = real0
    chk("① 庫不在(err「DB_TW 缺」)→ 補 state NODATA + why,err 原樣保留", r.get("state") == "NODATA" and r.get("err") == "DB_TW 缺"
        and r.get("missing_tables"), r.get("state"))
    globals()["_EXPORT0"] = lambda *a, **k: {"files": {"x": 1}, "stats": {}, "state": "OK"}
    try:
        r2 = export(do_print=False)
    finally:
        globals()["_EXPORT0"] = real0
    chk("② 庫在(有 state)→ 一字不動", r2 == {"files": {"x": 1}, "stats": {}, "state": "OK"})
    chk("③ 本體的 export 換成本版(前版自測 / run 經模組全域叫到)", BODY.export is export)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 本支帶加速器橋 · 網路橋;不含 TA-Lib 匯入", "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", src, re.M))
    if tail_only:                         # 交接案用:只驗本尾版四檢(前版八檢要台股庫,缺庫=NODATA 屬環境事實)
        BODY.export = keep
        print(f"  [計] VDF_ENG072 v0105 薄尾 {sum(ok)}/{len(ok)} · 只驗薄尾 · 合計 {'PASS' if all(ok) else 'FAIL'}")
        return 0 if all(ok) else 1
    rc = PRIOR.selftest()
    BODY.export = keep
    good = all(ok)
    st = "PASS" if good and rc == 0 else ("NODATA" if good and rc == 2 else "FAIL")
    print(f"  [計] VDF_ENG072 v0105 薄尾 {sum(ok)}/{len(ok)} · 前版 rc {rc} · 合計 {st}")
    return 0 if st == "PASS" else (2 if st == "NODATA" else 1)


if __name__ == "__main__":
    sys.exit(main())
