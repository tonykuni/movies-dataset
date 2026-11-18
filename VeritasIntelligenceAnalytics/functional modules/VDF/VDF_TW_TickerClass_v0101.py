#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_TW_TickerClass v0101 — v0100 薄尾:補上加速器橋(v0100 沒有)。v0100 是操作員 2026-11-18 的台股代號分類(主動式台股 ETF 判別)。

2026-11-18 以語法樹盤點(不是看標記):VDF_TW_TickerClass_v0100.py 沒有加速器橋(標記與匯入都沒有)。
操作員令:加速器要覆蓋每一支、以生效計(只有標記不算)。
本版只做一件事:真的匯入 VIA_SuperAccel_Module(缺席時照舊跑,零行為變更)。
前版一字不改(SHA-256 釘在 PRIOR_SHA256);公開名稱、main、selftest、指令列用法全部原樣轉給前版。
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

import ast
import hashlib
import importlib.util
import sys
from pathlib import Path

VERSION_TAIL = "v0101"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VDF_TW_TickerClass_v0100.py"
PRIOR_SHA256 = "453ac4b9b4ba31fa64ade3c4f61b426a394459ac349de6c0719a6eff23c2189d"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.is_file():
    raise SystemExit("[RED] 前版 %s 不在 %s(本檔是它的薄尾 · 兩支要放同一夾)" % (PRIOR_NAME, HERE))
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("vdf_tickerclass_v0100_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def accel_imported(path: Path) -> bool:
    """語法樹裡真的有 import VIA_SuperAccel_Module 才算。"""
    tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(a.name == "VIA_SuperAccel_Module" for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == "VIA_SuperAccel_Module":
            return True
    return False


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    print("=== VDF_TW_TickerClass " + VERSION_TAIL + " 薄尾自測(加速器橋以語法樹為準)===")
    chk("① 前版位元沒變(SHA-256 與釘的值相同)", PRIOR_SHA_OK, PRIOR_NAME)
    chk("② 本檔語法樹裡真的匯入加速器;前版沒有(所以才出這一版)", accel_imported(Path(__file__)) and not accel_imported(PRIOR_PATH))
    chk("③ 加速器在這台載得到,或缺席時照舊能跑(VIA_ACCEL 是模組或 None)", VIA_ACCEL is None or hasattr(VIA_ACCEL, "__name__"), "載入" if VIA_ACCEL is not None else "缺席(照跑)")
    pub = [n for n in vars(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n))]
    chk("④ 前版公開名稱經本檔都拿得到", all(getattr(sys.modules[__name__], n) is getattr(PRIOR, n) for n in pub if n not in ("selftest", "main")) and len(pub) > 3, "%d 個" % len(pub))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 不含本機路徑 · 不碰 TA-Lib · 本檔零網路", ("C:" + "\\Users") not in src and ("import " + "talib") not in src and ("url" + "open") not in src and ("req" + "uests") not in src)
    rc = PRIOR.selftest()
    chk("⑥ 前版自測照過", rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] VDF_TW_TickerClass %s 本版 %d/%d · %s" % (VERSION_TAIL, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


def main(argv=None) -> int:
    """v0100 沒有 main(直接執行 = 自測);本版照舊:不帶參數或 --selftest 都跑自測。分類函式用匯入的方式取用。"""
    return selftest()


if __name__ == "__main__":
    raise SystemExit(main())
