#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parameter hub v0111. v0110 (v0109 plus the US macro parameter book) with the full v0109 surface forwarded.

v0110→v0111(側線 2026-09-28 R16-3;全景 TAILAPI + 實跑證實):v0110 只帶 BOOKS 與 selftest,尾版律下所有以 glob 取最新版的呼叫端
都拿不到 v0109 的函式 —— via_conflict_guard 衝突機制 ① 實跑 `AttributeError: '_vpc' has no attribute 'scan_book'`。
本版:BOOKS 用 v0110 那份(含 USMACRO_PARAMS);其餘公開名稱經模組層 __getattr__ 轉到 v0110 已載入的本體(它的 prev = v0109);
呼叫端照慣例傳 m.BOOKS 進 scan_book(conflict_guard 就是這樣),拿到的是含 USMACRO 的那份;本體模組層的狀態一個不改
(改別支模組的全域會讓 v0110 自己的檢查在同一行程裡失真)。命令列 main 照 v0109(v0110 本來就沒有 main)。
前一版用 glob 取(不釘版號);本體讀前一版的 prev(不另載第二份)。
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 前一版 = 同族裡檔名比自己小的最新一支(glob,不釘版號 L54)
_PRIOR_PATH = [p for p in sorted(HERE.glob("via_params_central_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("via_params_central_prior_of_v0111", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
IMPL = getattr(PRIOR, "prev", PRIOR)          # v0110 的 prev = v0109 本體;前一版若本身是本體就用它

BOOKS = list(PRIOR.BOOKS)                     # 本版的冊單 = v0110 那份(含 USMACRO_PARAMS);不回寫本體(不改別支模組的狀態)


def __getattr__(name: str):
    """PEP 562:v0109 本體的公開面照舊可叫(scan_book · find_conflicts · build_index · main …)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(IMPL, name)


def selftest() -> int:
    mod = sys.modules.get(__name__)
    ids = [b["id"] for b in BOOKS]
    checks = [
        ("v0110 的冊單照舊(含 USMACRO_PARAMS · 不重複)", "USMACRO_PARAMS" in ids and len(ids) == len(set(ids))),
        ("轉接:scan_book · find_conflicts · locked_alignment · flatten 叫得到(TAILAPI)",
         all(callable(getattr(mod, n, None)) for n in ("scan_book", "find_conflicts", "locked_alignment", "flatten"))),
        ("不改本體狀態(v0109 的冊單原樣,v0110 的「多一本」照成立)", IMPL.BOOKS is not BOOKS and len(BOOKS) == len(IMPL.BOOKS) + 1),
        ("前一版自測照過", PRIOR.selftest() == 0),
    ]
    root = HERE.parent.parent
    try:
        recs = [IMPL.scan_book(b, root) for b in BOOKS]
        conf = IMPL.find_conflicts(recs)
        checks.append(("實跑:逐冊掃描 + 跨冊衝突比對(conflict_guard ① 的同一條路)", isinstance(conf, list) and len(recs) == len(BOOKS)))
    except Exception as exc:
        checks.append((f"實跑:逐冊掃描 + 跨冊衝突比對 · {type(exc).__name__}: {exc}"[:120], False))
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    bad = [n for n, ok in checks if not ok]
    print(f"  [計] {len(checks)} 檢 OK {len(checks) - len(bad)} · FAIL {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv or len(sys.argv) == 1 and not hasattr(IMPL, "main"):
        raise SystemExit(selftest())
    raise SystemExit(IMPL.main() if hasattr(IMPL, "main") else selftest())
