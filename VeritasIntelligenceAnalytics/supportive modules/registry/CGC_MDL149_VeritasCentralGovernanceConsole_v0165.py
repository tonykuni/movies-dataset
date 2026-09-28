#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0165 — 薄尾:NLP 與 Layout 走同一個出口

操作員 2026-09-28:「LAYOUT引擎 NLP引擎 都集合成單一出口」。
v0164 以前 `via-vcgc layout …` 有路,NLP 沒有——要跑 NLP 得自己找 SUP_MDL866 哪一版去叫。
本尾版多收三個動詞。tools 交給工具啟用閘尾版(CGC_MDL233_ToolActivate_v*:加速器/網路工具的版本固定,
只有這裡的 activate --apply 能動鎖冊);nlp、door 交給 NLP/Layout 門尾版(CGC_MDL216_NlpLayoutDoor_v*,照尾版律取):
  via-vcgc tools [activate <family> <file> [--apply]]
  via-vcgc nlp <SUP_MDL866 參數>   → 門 → NLP 編排器尾版
  via-vcgc door                     → 門的路線卡(每條路線的尾版 · 版號 · 與座位冊是否一致)
`layout` 照舊由前一版處理(門的 layout 也是交回這一條,不另寫一條)。其餘動詞原樣轉給前一版。
前一版 = 同夾同名「版號小於自己的最新一支」(今天是 v0164)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
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
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
DOOR_STEM = "CGC_MDL216_NlpLayoutDoor"
DOOR_VERBS = ("nlp", "door")
TOOLS_STEM = "CGC_MDL233_ToolActivate"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("vcgc_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def door_tail() -> Path | None:
    hits = [p for p in HERE.glob(DOOR_STEM + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _door():
    p = door_tail()
    if p is None:
        return None
    spec = importlib.util.spec_from_file_location("vcgc_door_" + p.stem, p)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _tools():
    hits = [p for p in HERE.glob(TOOLS_STEM + "_v*.py") if _vnum(p) >= 0]
    if not hits:
        return None
    p = max(hits, key=_vnum)
    spec = importlib.util.spec_from_file_location("vcgc_tools_" + p.stem, p)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _is_door_verb(args) -> bool:
    return bool(args) and args[0] in DOOR_VERBS


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["tools"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
            return 2
        tools = _tools()
        if tools is None:
            print(json.dumps({"via": "vcgc", "state": "ABSENT", "why": TOOLS_STEM + " tail"}, ensure_ascii=False))
            return 2
        return tools.main(args[1:])
    if not _is_door_verb(args):
        return PRIOR.main(argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    door = _door()
    if door is None:
        print(json.dumps({"via": "vcgc", "state": "ABSENT", "why": DOOR_STEM + " tail"}, ensure_ascii=False))
        return 2
    return door.main(args if args[0] == "nlp" else args[1:])


def selftest() -> int:
    routed = (_is_door_verb(["nlp", "text"]) and _is_door_verb(["door"]) and not _is_door_verb(["layout"])
              and not _is_door_verb(["status"]) and not _is_door_verb([]))
    print(f"  [{'OK' if routed else 'FAIL'}] nlp / door 交給門,layout 與其餘動詞照舊給 {PRIOR_PATH.name}")
    p = door_tail()
    print(f"  [{'OK' if p else 'FAIL'}] 門尾版 {p.name if p else 'ABSENT'}")
    body = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0].split('"""', 2)[-1]
    pinned = re.search(r"_v\d{4}\.py", body)
    print(f"  [{'OK' if not pinned else 'FAIL'}] 本支沒有字串釘死任何版號檔名")
    if not (routed and p) or pinned:
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(selftest() if args == ["--selftest"] else main())
