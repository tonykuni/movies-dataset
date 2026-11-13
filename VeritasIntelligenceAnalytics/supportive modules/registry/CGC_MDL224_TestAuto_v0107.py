#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL224_TestAuto v0107 — 薄尾:串測的家族掃描認得新命名 VIA_VCGC_<MDL|SUP>###_*(政策 L129 ⑦)

操作員 2026-11-13:「VCGC節省或支援工具VIA_VCGC_SUP001_ VCGC本身中央管理VIA_VCGC_MDL001 相同要有版本號 依照命名規定」。
v0101 本體 TAIL_RX 只認 CGC_MDL###_* / CGC_SystemManager → 依新命名出的新家族(第一支:VIA_VCGC_MDL258_ToolMatrix)
不會被串測自動跑 --selftest,也不會在紀錄冊 VIA_VCGC_FunctionLedger 留版本與時間 —— 等於命名律一出就有漏網的家族。
本版只換 BODY.TAIL_RX:舊兩種照認,另認 VIA_VCGC_(MDL|SUP)\\d{3,4}_<名>_vNNNN.py;.json / .jsonl 冊(VIA_VCGC_FunctionInventory…)
與沒有類碼的 VIA_VCGC_<名> 不算家族。v0101–v0106 一字不動。只收 VCGC 呼叫;零網路;不碰 TA-Lib。
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
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL224_TestAuto"


def _vnum_v0107(path) -> int:
    m = re.search(r"[-_]v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0107(p) < _vnum_v0107(__file__)), key=_vnum_v0107)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0106:PS 站章驗整條點源鏈
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = PRIOR.BODY
_TAIL_RX_V0101 = BODY.TAIL_RX
TAIL_RX = re.compile(r"^(?P<fam>(?:CGC_MDL\d+_\w+?|CGC_SystemManager|VIA_VCGC_(?:MDL|SUP)\d{3,4}_\w+?))_v(?P<v>\d{4})\.py$")
BODY.TAIL_RX = TAIL_RX                                    # 本體 discover_families 每次呼叫讀模組全域 → 走本版


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    print(f"=== {ENGINE} · 薄尾自測(串測認得新命名 VIA_VCGC_<MDL|SUP>### 家族)===")
    BODY.TAIL_RX = _TAIL_RX_V0101                         # 前版鏈自測照它自己的尺跑,跑完掛回
    try:
        rc = PRIOR.selftest()
    finally:
        BODY.TAIL_RX = TAIL_RX
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:220]) if note and not cond else ''}")

    chk("① 前版鏈自測過(v0106 → … → v0101);本版換裝還在(BODY.TAIL_RX 是本版)", rc == 0 and BODY.TAIL_RX is TAIL_RX, f"rc {rc}")
    cases = {"CGC_MDL149_VeritasCentralGovernanceConsole_v0192.py": "CGC_MDL149_VeritasCentralGovernanceConsole",
             "CGC_SystemManager_v0101.py": "CGC_SystemManager",
             "VIA_VCGC_MDL258_ToolMatrix_v0100.py": "VIA_VCGC_MDL258_ToolMatrix",
             "VIA_VCGC_SUP001_Foo_Bar_v0101.py": "VIA_VCGC_SUP001_Foo_Bar",
             "VIA_VCGC_FunctionInventory_SSOT_v0225.json": None, "VIA_VCGC_FunctionLedger_v0100.jsonl": None,
             "VIA_VCGC_Matrix_v0100.py": None, "VIA_VCGC_MDL001_NoVer.py": None, "VDF_ENG001_A_v0100.py": None}
    got = {n: (TAIL_RX.match(n).group("fam") if TAIL_RX.match(n) else None) for n in cases}
    chk("② 家族名:舊兩種照認 · VIA_VCGC_MDL / SUP 新名認得 · .json / .jsonl 冊、沒類碼、沒版號、他系統檔不算", got == cases, got)
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        for n in ("CGC_MDL001_A_v0100.py", "CGC_MDL001_A_v0101.py", "VIA_VCGC_SUP002_B_v0100.py", "VIA_VCGC_SUP002_B_v0103.py",
                  "VIA_VCGC_FunctionLedger_v0100.jsonl"):
            (t / n).write_text("# x\n", encoding="utf-8")
        fam = {k: v.name for k, v in BODY.discover_families(t).items()}
        chk("③ discover_families:新舊兩種家族都進來、各取最大版號", fam == {"CGC_MDL001_A": "CGC_MDL001_A_v0101.py",
                                                                         "VIA_VCGC_SUP002_B": "VIA_VCGC_SUP002_B_v0103.py"}, fam)
    reg = BODY.VIA / "supportive modules" / "registry"
    new = BODY.discover_families(reg)
    BODY.TAIL_RX = _TAIL_RX_V0101
    try:
        old = BODY.discover_families(reg)
    finally:
        BODY.TAIL_RX = TAIL_RX
    extra = sorted(set(new) - set(old))
    chk("④ 真樹:舊尺認得的家族一個不少(同一支尾版)· 多出來的只有 VIA_VCGC_<MDL|SUP>### 家族",
        all(new.get(k) == v for k, v in old.items()) and all(re.match(r"VIA_VCGC_(MDL|SUP)\d{3,4}_", k) for k in extra),
        f"舊 {len(old)} · 新 {len(new)} · 多 {extra[:4]}")
    src_text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 不直派子行程", "[VIA:ACCEL-BRIDGE" in src_text and "[VIA:NET-BRIDGE" in src_text
        and not re.search(r"^\s*(import|from)\s+talib", src_text, re.M) and not re.search(r"^\s*(import|from)\s+sub" + "process", src_text, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) and rc == 0 else 'FAIL'}")
    return 0 if rc == 0 and all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
