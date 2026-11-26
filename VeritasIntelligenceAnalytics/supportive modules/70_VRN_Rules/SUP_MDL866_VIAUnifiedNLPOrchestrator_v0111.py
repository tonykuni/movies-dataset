#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""SUP_MDL866 v0111 — 薄尾(v0110 以前一字不動):本檔明寫動詞表 VERBS(含 --brief),行為全部照 v0110

為什麼出這版(2026-11-26 VCGC 收尾實錄):主控台舊本體的省 Token 門(CGC_MDL149 token_roster)以字串在
SUP_MDL866 尾版檔面找 "--brief";v0110 是轉接薄尾,--brief 由前版鏈(v0109 → … → v0106)處理但檔面沒寫,
→ 門判「缺 brief」RED → registry-sync · status 等動詞一律 rc 2、後面不印(同 2026-11-19 CGC_MDL158 漏寫 VERBS 一案)。
本版只把動詞表寫在檔面,main 原樣轉交 v0110;不改任何行為。零網路;零 TA-Lib;不設同意閘。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "SUP_MDL866_VIAUnifiedNLPOrchestrator"
VERSION = "v0111"

# 動詞表(檔面明寫;主控台省 Token 門用字串找 "--brief")。前版鏈處理的動詞照轉交。
VERBS = ("--brief", "-Brief", "status", "text", "pipeline", "pdf", "l1-status", "reconstruct", "unified", "scan",
         "semantic", "intake", "hub-status", "normalize", "html", "md-blocks", "gle-status", "--selftest")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = bad = 0

    def chk(name, cond, note=""):
        nonlocal ok, bad
        ok += bool(cond)
        bad += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}", flush=True)

    chk("① 加速器橋執行時生效(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("② 檔面明寫 \"--brief\"(主控台省 Token 門以字串找)", '"--brief"' in src and "--brief" in VERBS)
    chk("③ 前版是 v0110 以前的尾版(glob 取前版)", _vnum(PRIOR_PATH) < _vnum(__file__) and PRIOR_PATH.name.startswith(_STEM))
    chk("④ 前版公開名稱經本檔轉接(只增不減)",
        all(callable(getattr(sys.modules[__name__], n, None)) for n in ("nlp_hub", "layout_hub", "markdown_hub", "normalize", "html_text", "hub_status")))
    rc = PRIOR.selftest()
    chk("⑤ 前版 v0110 自測照過", rc == 0, f"rc={rc}")
    chk("⑥ 檔面:第 3 行加速器標記 · 零 TA-Lib · 不設同意閘",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"  [計] {_STEM} {VERSION} 自測 OK {ok} · FAIL {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
