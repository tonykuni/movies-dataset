#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0124 — 薄尾:自測隨冊(前版 v0122 ① 寫死「七項輸出」,冊長到 v0103 八項就紅)

實測(2026-10-03 交接 handoff test vdf_universe / vdf_universe_r50 rc 1):main 新增 VDF_InputUniverse_SSOT v0102 / v0103
(加 OUT-08 · 顯示名),v0122 自測 ① `len(outputs) == 7` 讀尾冊 → FAIL;其餘 10 項 OK、v0123 本版 6/6。
不是功能壞,是前版自測把當時的冊寫成常數。本版只改這一件(v0121–v0123 一字不動):
  ① 跑前版鏈自測時,把 v0121 的 book_path 釘回「v0122 出貨時的冊」(v0101;它照那本寫的),跑完還原 ——
     同 v0122 對 v0121 的做法(釘回 v0100)。
  ② 本版另驗尾冊只增不減:v0101 的每一項輸出(OUT-01…OUT-07)尾冊都還在 · 順序仍收在 E-11:xcheck / parquet / lock ·
     xcheck / parquet / lock 三節在。輸出項數照冊算,不寫常數(冊再長也不紅;少了才紅)。
其餘動詞全照前版。不抓網、不代設同意閘、不碰 TA-Lib。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
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
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import importlib.util
import os
import re
import sys
from pathlib import Path

import json

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
SHIPPED_BOOK_V0124 = "VDF_InputUniverse_SSOT_v0101.json"   # v0122 出貨時照的那本冊


def _vnum_v0124(path) -> int:            # 版本專屬名:元件冊以函式登記,共用名會把前版的紀錄搶走
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0124(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0124(p) < _vnum_v0124(__file__)), key=_vnum_v0124)
PRIOR = _load_v0124(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)
ENGINE_TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def __getattr__(name):
    return getattr(PRIOR, name)


def collect() -> dict:
    return PRIOR.collect()


def book() -> dict:
    return PRIOR.book()


def main() -> int:
    return PRIOR.main()


def _book_owner_v0124():
    """沿前版鏈找定義 book_path 的那一版(v0121);找不到回 None。"""
    m = PRIOR
    while m is not None:
        if "book_path" in vars(m):
            return m
        m = vars(m).get("PRIOR")
    return None


def _ids_v0124(bk: dict) -> list:
    outs = bk.get("outputs") or []
    return [o.get("id") if isinstance(o, dict) else o for o in (outs if isinstance(outs, list) else list(outs))]


def check_book_v0124(bk: dict, base: dict) -> tuple:
    """尾冊對出貨冊只增不減:(過不過, 缺的輸出, 輸出項數)。"""
    have, need = _ids_v0124(bk), _ids_v0124(base)
    missing = [x for x in need if x not in have]
    order = (bk.get("loop") or {}).get("order") or []
    ok = (not missing and order[-3:] == ["E-11:xcheck", "E-11:parquet", "E-11:lock"]
          and all(k in bk for k in ("xcheck", "parquet", "lock")))
    return ok, missing, len(have)


def selftest() -> int:
    owner = _book_owner_v0124()
    shipped = HERE / SHIPPED_BOOK_V0124
    keep = owner.book_path if owner is not None else None
    if owner is not None and shipped.is_file():
        owner.book_path = lambda: shipped              # 前版鏈照 v0101 冊寫的:釘回它再跑
    try:
        prior_rc = PRIOR.selftest()
    finally:
        if owner is not None:
            owner.book_path = keep
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 薄尾自測(自測隨冊:前版釘出貨冊 · 尾冊只增不減)===")
    chk("① 前版鏈自測過(v0123 → v0122 → v0121 …;前版照出貨冊 v0101 跑)", prior_rc == 0 and owner is not None and shipped.is_file(),
        f"rc {prior_rc} · 釘 {shipped.name}")
    chk("② 跑完已還原:book_path 回到取尾冊那支(不留釘)", owner is not None and owner.book_path is keep)
    tail = owner.book_path() if owner is not None else None
    bk = json.loads(tail.read_text(encoding="utf-8")) if tail else {}
    base = json.loads(shipped.read_text(encoding="utf-8")) if shipped.is_file() else {}
    good, missing, n = check_book_v0124(bk, base)
    chk("③ 尾冊只增不減:v0101 七項輸出全在 · 順序收在 E-11:xcheck/parquet/lock · 三節在(項數照冊算)", good,
        f"{tail.name if tail else '—'} · 輸出 {n} 項 · 缺 {missing}")
    fake = dict(base, outputs=[o for o in base.get("outputs", []) if (o.get("id") if isinstance(o, dict) else o) != "OUT-06"])
    longer = dict(base, outputs=list(base.get("outputs", [])) + [{"id": "OUT-99"}])
    chk("④ 尺本身:少一項 = 紅(點名缺的)· 多一項 = 照過(冊再長不紅)",
        check_book_v0124(fake, base)[:2] == (False, ["OUT-06"]) and check_book_v0124(longer, base)[0])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路工具橋 · 正典橋在;不碰 TA-Lib;不代設同意閘",
        all(x in text for x in ("[VIA:ACCEL-BRIDGE", "[VIA:NET-BRIDGE", "[VIA:LIB-BRIDGE"))
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and "VIA_NET_CONSENT\"] =" not in text)
    print(f"  [計] {ENGINE_TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) and prior_rc == 0 else 'FAIL'}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
