#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0123 — 薄尾:單引擎啟動冊(動詞 engine;管理員掌握每支引擎的啟動前閘)

操作員(2026-10-02):「參數 · 邏輯 · 輸入輸出 HEADER 下放到 VRN / VDF SYSTEM MANAGER,掌握各引擎啟動器 … 都用 VCGC 工具去檢視
是否依照導入加速器 · 網路工具導入 … 確定好可以進行單引擎啟動 · 提供 VCGC-VDF 所有引擎獨立啟動短指令」。
  engine list [--json]        VDF 引擎尾版逐支:引擎號 · 家族 · 版本 · 中央編號 · 啟動前閘燈 · 單引擎短令;頁 VIA_Reports/tooling/ENGINES_VDF_latest.html
  engine check <引擎> [--json] 啟動前閘(紅 = 讀不過 / 沒有入口 / 缺 L103 加速器或網路工具橋 → 不准啟動;黃 = 未編號 / 沒自測 / 要網路同意閘)
  engine card <引擎>           同 check,另列函數
  <引擎> = 229 · ENG229 · MDL002 · 全名 · 名稱片段;同號異名照實回候選,不猜。
檢視本體是 VCGC 的 CGC_MDL253_ToolingInventory(全景鎖版 AST + 中央編號冊 + 短令冊 + Celeritas 基線具名名單),
兩個管理員共用同一份(VRN_SystemManager v0114 同一個動詞),不各抄一套。真正啟動由短令 via-vdfeng 經 VCGC run 跑,
本支不自己起子行程。其餘動詞全照前版。不抓網、不代設同意閘、不碰 TA-Lib。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
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

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "VDF_SystemManager"
REG = VIA / "supportive modules" / "registry"


def _vnum_v0123(path) -> int:            # 版本專屬名:元件冊以函式登記,共用名會把前版的紀錄搶走
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0123(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0123(p) < _vnum_v0123(__file__)), key=_vnum_v0123)
PRIOR = _load_v0123(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)
ENGINE_TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
_INV = None


def __getattr__(name):
    return getattr(PRIOR, name)


def collect() -> dict:
    return PRIOR.collect()


def book() -> dict:
    return PRIOR.book()


def _inventory_v0123():
    """VCGC 檢視工具 CGC_MDL253 尾版(只讀;兩個管理員共用)。"""
    global _INV
    if _INV is None:
        hits = [p for p in REG.glob("CGC_MDL253_ToolingInventory_v*.py") if _vnum_v0123(p) >= 0]
        if not hits:
            raise RuntimeError("CGC_MDL253_ToolingInventory 不在(先 git pull)")
        _INV = _load_v0123(max(hits, key=_vnum_v0123), "_vdf_mgr_v0123_inventory")
    return _INV


def engine(args: list) -> int:
    try:
        inv = _inventory_v0123()
    except RuntimeError as e:
        print(f"[{ENGINE_TAG}] 啟動冊 ABSENT:{e}")
        return 3
    return inv.engine_main("VDF", list(args), ENGINE_TAG)


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    a = sys.argv[1:]
    if a and a[0] == "engine":
        return engine(a[1:])
    return PRIOR.main()


def selftest() -> int:
    prior_rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    keep = os.environ.pop("VIA_FROM_VCGC", None)
    argv = sys.argv[:]
    sys.argv = [argv[0], "engine", "list"]
    chk("① 未經 VCGC 拒絕(engine 也一樣)", main() == 2)
    os.environ["VIA_FROM_VCGC"] = "YES"
    inv = _inventory_v0123()
    chk("② 檢視本體是 VCGC 的 CGC_MDL253(共用一份 engine_main / gate)", hasattr(inv, "engine_main") and hasattr(inv, "gate"))
    rows = inv.engines("VDF")
    one, _ = inv.resolve(rows, "229")
    g = inv.gate(one, "VDF") if one else {}
    chk("③ 真樹:VDF 引擎冊有料 · 229 解析到 ENG229 · 啟動前閘不紅", len(rows) > 20 and one is not None and g.get("lamp") in ("GREEN", "YELLOW"),
        (len(rows), g.get("lamp")))
    chk("④ 單引擎短令走 VCGC run(不自起子行程)", g.get("launch", {}).get("vcgc", [])[:3] == ["run", "--family", "vdf"])
    sys.argv = [argv[0], "engine", "check", "NO_SUCH_ENGINE_ZZZ"]
    chk("⑤ 找不到的引擎回 3(不猜)", main() == 3)
    sys.argv = argv
    if keep is None:
        os.environ.pop("VIA_FROM_VCGC", None)
    else:
        os.environ["VIA_FROM_VCGC"] = keep
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路工具橋在;不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] {ENGINE_TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
