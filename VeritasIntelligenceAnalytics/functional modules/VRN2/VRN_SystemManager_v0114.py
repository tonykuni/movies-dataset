#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0114 — 薄尾:單引擎啟動冊(動詞 engine;管理員掌握每支引擎的啟動前閘;與 VDF 管理員 v0123 同一個動詞)

操作員(2026-10-02):「下放到 VRN / VDF SYSTEM MANAGER 下掌握各引擎啟動器 … VRN 也可單引擎擷取 … 提供 VCGC-VRN 獨立啟動引擎短指令」。
  engine list [--json]        VRN 引擎尾版逐支:引擎號 · 家族 · 版本 · 中央編號 · 啟動前閘燈 · 單引擎短令;頁 VIA_Reports/tooling/ENGINES_VRN_latest.html
  engine check <引擎> [--json] 啟動前閘(紅 = 讀不過 / 缺 PY 加速器橋 → 不准啟動;沒有 __main__ = 程式庫,不單獨啟動;
                               Celeritas 基線具名唯讀本缺橋 = 黃不擋)
  engine card <引擎>           同 check,另列函數
檢視本體是 VCGC 的 CGC_MDL253_ToolingInventory(兩個管理員共用一份,VDF 與 VRN 不互相匯入)。真正啟動由短令 via-vrneng 經 VCGC run 跑,
本支不自己起子行程。其餘動詞(frame · provenance · outputs …)全照前版。只收 VCGC 呼叫(VIA_FROM_VCGC=YES);不碰 TA-Lib。
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

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = HERE.parents[1] / "supportive modules" / "registry"
_STEM = "VRN_SystemManager"
TAG = "VRN_SystemManager v0114"
_prior = None
_inv = None


def _vnum_v0114(path) -> int:            # 版本專屬名:元件冊以函式登記,共用名會把前版的紀錄搶走
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0114(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _facade_v0114():
    global _prior
    if _prior is None:
        prior = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0114(p) < _vnum_v0114(__file__)), key=_vnum_v0114)
        _prior = _load_v0114(prior, "vrn_manager_prior_for_v0114")
    return _prior


def __getattr__(name: str):
    return getattr(_facade_v0114(), name)


def _inventory_v0114():
    """VCGC 檢視工具 CGC_MDL253 尾版(只讀;兩個管理員共用)。"""
    global _inv
    if _inv is None:
        hits = [p for p in REG.glob("CGC_MDL253_ToolingInventory_v*.py") if _vnum_v0114(p) >= 0]
        if not hits:
            raise RuntimeError("CGC_MDL253_ToolingInventory 不在(先 git pull)")
        _inv = _load_v0114(max(hits, key=_vnum_v0114), "_vrn_mgr_v0114_inventory")
    return _inv


def engine(args: list) -> int:
    try:
        inv = _inventory_v0114()
    except RuntimeError as e:
        print(f"[{TAG}] 啟動冊 ABSENT:{e}")
        return 3
    return inv.engine_main("VRN", list(args), TAG)


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "engine":
        return engine(args[1:])
    return _facade_v0114().main(argv)


def selftest() -> int:
    prior_rc = _facade_v0114().selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    keep = os.environ.pop("VIA_FROM_VCGC", None)
    chk("① 未經 VCGC 拒絕(engine 也一樣)", main(["engine", "list"]) == 2)
    os.environ["VIA_FROM_VCGC"] = "YES"
    inv = _inventory_v0114()
    chk("② 檢視本體是 VCGC 的 CGC_MDL253(與 VDF 管理員同一份)", hasattr(inv, "engine_main") and hasattr(inv, "gate"))
    rows = inv.engines("VRN")
    lamps = {r["eid"]: inv.gate(r, "VRN")["lamp"] for r in rows}
    chk("③ 真樹:VRN 引擎冊有料 · 沒有被擋的紅燈(缺橋 = 修掉或具名)", len(rows) > 20 and "RED" not in lamps.values(),
        (len(rows), sorted(k for k, v in lamps.items() if v == "RED")[:5]))
    g = next((inv.gate(r, "VRN") for r in rows if inv.gate(r, "VRN")["lamp"] == "GREEN"), {})
    chk("④ 綠燈引擎的單引擎短令走 VCGC run(--family vrn)", g.get("launch", {}).get("vcgc", [])[:3] == ["run", "--family", "vrn"]
        and g.get("launch", {}).get("short", "").startswith("via-vrneng "))
    chk("⑤ 找不到的引擎回 3(不猜)", main(["engine", "check", "NO_SUCH_ENGINE_ZZZ"]) == 3)
    if keep is None:
        os.environ.pop("VIA_FROM_VCGC", None)
    else:
        os.environ["VIA_FROM_VCGC"] = keep
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋在;不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    # 只有單獨 --selftest 跑本版自測;其餘子動詞照轉前版
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
