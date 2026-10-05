#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0123 — 薄尾:對帳整併 + 獨立 MAIN(批1657 操作員令「推完了 開始對帳整併 v0120-0122」
+「VRN 現在斷開 仍與 VCGC 各自運作下互動 但獨立 MAIN」)。

對帳結論(主機端三尾版入倉後,與倉端 v0119 本體逐一對過):
  · v0120(SSOT 下放第一段)/ v0121(鍵帶副檔名)/ v0122(Index 孤鍵退役)三支皆正規薄尾
    (glob 取前版 · 加速器橋在 · 自測 11/11 含前版鏈),職能=ssot adopt/diff/number pull,
    與 v0119 的深讀七動詞(intake/deepread/layout-check/reconstruct/eps-check/real-test/vdf-fetch)
    **零重疊零衝突**——全數收編正統鏈,一支不動。編號走主機 registry-sync(先 commit 再發號)。
  · 唯一不合:三支 main 還帶舊拒絕閘(「只能經 via-vcgc」),與獨立 MAIN 律衝突而尾版=執行入口。
本版只做一件事:main 的拒絕路改**自立閘座**(對下游引擎兼容,入口誠實印 standalone),
其餘動詞、名稱全走前版鏈(PEP 562);與 VDF v0129+ / CGC_SystemManager_v0112 同款。
自測: python VRN_SystemManager_v0123.py --selftest(獨立 MAIN:不帶閘也要能跑;前版鏈自測原樣印出)
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import os
import re
import sys
from pathlib import Path

TAG = "v0123"
HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"


def _vnum_v0123(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0123(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0123(p) < _vnum_v0123(__file__)),
                 key=_vnum_v0123)
PRIOR = _load_v0123(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":   # 獨立 MAIN:斷開仍互動——自立閘座,入口誠實記
        os.environ["VIA_FROM_VCGC"] = "YES"
        print(f"[VRN] 獨立 MAIN(standalone)· {_STEM} {TAG} · 與 VCGC 各自運作下互動(資料經 vdf-fetch 中介)")
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    import ast
    keep = os.environ.get("VIA_FROM_VCGC")
    os.environ.pop("VIA_FROM_VCGC", None)
    rc_sa = main(["nosuchverb_v0123_probe"])   # 不帶閘:不得被拒,走前版鏈的未知動詞拒跑(rc 2 但非閘拒)
    sa_ok = os.environ.get("VIA_FROM_VCGC") == "YES" and rc_sa == 2
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    no_deny = not any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "print"
                      and any("只能經" in getattr(a, "value", "") for a in n.args if isinstance(a, ast.Constant))
                      for n in ast.walk(fn))
    prior_rc = PRIOR.main(["--selftest"])
    if keep is None:
        os.environ.pop("VIA_FROM_VCGC", None)
    else:
        os.environ["VIA_FROM_VCGC"] = keep
    ok = sa_ok and no_deny and prior_rc == 0
    print(f"  [{'OK' if sa_ok else 'FAIL'}] 獨立 MAIN:不帶閘進 main=自立閘座(未知動詞照前版鏈拒 rc2,非閘拒)")
    print(f"  [{'OK' if no_deny else 'FAIL'}] main 無「只能經 via-vcgc」拒絕路(AST 功能檢)")
    print(f"  [{'OK' if prior_rc == 0 else 'FAIL'}] 前版鏈 {PRIOR_PATH.name} 自測 rc 0(v0120-0122 收編 · 職能零重疊)")
    print(f"[計] {_STEM}_{TAG} 自測 {3 if ok else [sa_ok, no_deny, prior_rc == 0].count(True)}/3 · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
