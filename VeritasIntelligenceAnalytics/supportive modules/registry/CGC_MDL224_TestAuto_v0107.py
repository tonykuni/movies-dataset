#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL224_TestAuto v0107 — 薄尾(v0106 … v0100 一字不動):更新尾版站(upd:*)認得 SKIP_ENV → 黃,不再一律紅。

操作員 2026-11-13:「修 CGC_MDL237 和 CGC_MDL278 紅燈」。CGC_MDL237 v0122 / CGC_MDL278 v0101 在缺 DuckDB 的環境把
「Regex 證明引擎不在」照實回 rc 2 並印 [SKIP_ENV](黃 ≠ 綠);但 upd:* 站沒有 yellow_rc,rc 2 一律判紅。
本版只改這一條、而且收得很窄:站 id 以 upd: 開頭 · rc 恰為 2 · 輸出裡有 [SKIP_ENV] 三者同時成立 → YELLOW;
其餘(rc 2 但沒有 [SKIP_ENV] 的參數錯誤 / 崩潰、其他站、其他 rc)一律照前版 lamp_for。
其餘全部照 v0106(→ v0101 本體)。零網路;不碰 TA-Lib;不直派子行程。
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL224_TestAuto"
SKIP_ENV_MARK = "[SKIP_ENV]"


def _vnum_v0107(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0107(p) < _vnum_v0107(__file__)), key=_vnum_v0107)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BODY = PRIOR.BODY
_LAMP_FOR_PRIOR = BODY.lamp_for


def lamp_for(rc: int, station: dict, out: str) -> str:
    if rc == 2 and str((station or {}).get("id", "")).startswith("upd:") and SKIP_ENV_MARK in (out or ""):
        return "YELLOW"
    return _LAMP_FOR_PRIOR(rc, station, out)


BODY.lamp_for = lamp_for


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    print(f"=== {ENGINE} · 薄尾自測(upd:* 站認得 SKIP_ENV)===")
    BODY.lamp_for = _LAMP_FOR_PRIOR                     # 前版鏈自測量前版判法
    try:
        rc = PRIOR.selftest()
    finally:
        BODY.lamp_for = lamp_for
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:200]) if note and not cond else ''}")

    upd = {"id": "upd:CGC_MDL237_NumberingSystem_v0122"}
    chk("① 前版鏈自測過(v0106 → … → v0100)", rc == 0, f"rc {rc}")
    chk("② upd:* · rc 2 · 有 [SKIP_ENV] → YELLOW", lamp_for(2, upd, "...\n  [SKIP_ENV] DuckDB 不在\n") == "YELLOW")
    chk("③ upd:* · rc 2 · 沒有 [SKIP_ENV](參數錯 / 崩潰)→ 照前版 RED", lamp_for(2, upd, "usage: error") == "RED")
    chk("④ upd:* · rc 1 有 [SKIP_ENV] → 照前版 RED;rc 0 → GREEN", lamp_for(1, upd, "[SKIP_ENV]") == "RED" and lamp_for(0, upd, "") == "GREEN")
    chk("⑤ 別的站 rc 2 有 [SKIP_ENV] → 照前版(不擴權);yellow_rc 照舊", lamp_for(2, {"id": "V-x"}, "[SKIP_ENV]") == "RED"
        and lamp_for(2, {"id": "P-entry", "yellow_rc": [2]}, "") == "YELLOW")
    chk("⑥ 本體 run 用的就是本版 lamp_for", BODY.lamp_for is lamp_for)
    src_text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋 · 網路橋在 · 不碰 TA-Lib · 不直派子行程", "[VIA:ACCEL-BRIDGE" in src_text and "[VIA:NET-BRIDGE" in src_text
        and not re.search(r"^\s*(import|from)\s+talib", src_text, re.M) and not re.search(r"^\s*(import|from)\s+sub" + "process", src_text, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) and rc == 0 else 'FAIL'}")
    return 0 if rc == 0 and all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
