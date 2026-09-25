#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_py_celeritas_launcher_v0100 — py 加速啟動器(TOOL-091,批87)
====================================================================
操作員令:「py 指令一定要透過 supportive modules\VeritasCeleritas.py
導入加速器 全部都要」。

機制:先把 supportive modules(+accelerator/)插入 sys.path,匯入
VeritasCeleritas 常駐(lazy import/LRU·TTL 快取/pmap 并行/HashEngine
/GCTuner 全家族進 sys.modules,目標腳本 import 即得),再以 runpy
於同進程執行目標腳本(argv 原樣傳遞)。Celeritas 缺席=graceful 零
影響照跑(誠實印註)。CodexNexus 為 PS 側加速道,由 PS 工具鏈承接。

用法:
  via-py <script.py> [args…]     → Celeritas 常駐後執行
  via-py --selftest              → 四檢(沙盒)
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

import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # supportive modules/registry
SUP = HERE.parent                               # supportive modules


def mount_celeritas() -> bool:
    """掛載加速器常駐 sys.modules。
    QA-20260820C:accelerator/ 夾內有 pip 內部件散落的 subprocess.py
    (遮蔽標準庫=Hydra 節點,候操作員裁決隔離)——故絕不把 accelerator/
    插入 sys.path,改用 spec_from_file_location 直載本體;SUP 根無遮蔽
    (已驗)可安全入 path 供支援模組匯入。"""
    s = str(SUP)
    if SUP.is_dir() and s not in sys.path:
        sys.path.insert(0, s)
    if "VeritasCeleritas" in sys.modules:
        return True
    import importlib.util
    for cand in (SUP / "accelerator" / "VeritasCeleritas.py", SUP / "VeritasCeleritas.py"):
        if not cand.exists():
            continue
        try:
            spec = importlib.util.spec_from_file_location("VeritasCeleritas", str(cand))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["VeritasCeleritas"] = mod
            spec.loader.exec_module(mod)
            return True
        except Exception:
            sys.modules.pop("VeritasCeleritas", None)
            continue
    return False


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name}")

    # ① 掛載器:Celeritas 入 sys.modules(倉內在位=必真;缺席環境=誠實跳)
    ok = mount_celeritas()
    if (SUP / "accelerator" / "VeritasCeleritas.py").exists() or (SUP / "VeritasCeleritas.py").exists():
        chk("Celeritas 掛載", ok and "VeritasCeleritas" in sys.modules)
    else:
        print("  [SKIP] Celeritas 掛載(倉內無本體,誠實)")
    # ② 目標腳本同進程可見加速器
    with tempfile.TemporaryDirectory() as td:
        t = Path(td) / "probe.py"
        t.write_text("import sys\nprint('CEL=' + str('VeritasCeleritas' in sys.modules))\n"
                     "print('ARGS=' + ','.join(sys.argv[1:]))\n", encoding="utf-8")
        import contextlib
        import io
        buf = io.StringIO()
        argv0 = sys.argv
        try:
            sys.argv = [str(t), "a1", "a2"]
            with contextlib.redirect_stdout(buf):
                runpy.run_path(str(t), run_name="__main__")
        finally:
            sys.argv = argv0
        out = buf.getvalue()
        chk("同進程加速器可見", ("CEL=True" in out) if ok else ("CEL=" in out))
        # ③ argv 原樣傳遞
        chk("argv 傳遞", "ARGS=a1,a2" in out)
    # ④ xbatch 加速原語煙測(Celeritas 在位才驗)
    if ok:
        import VeritasCeleritas as C
        chk("xbatch 原語", C.xbatch([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]])
    else:
        print("  [SKIP] xbatch(加速器缺席)")
    n = 4 - len(fails)
    print(f"  [計] 四檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.split("用法:")[1])
        return 2
    if args[0] == "--selftest":
        print("=== py 加速啟動器 v0100 · 四檢(沙盒)===")
        return selftest()
    ok = mount_celeritas()
    if not ok:
        print("  [註] Celeritas 缺席,直跑不加速(graceful 誠實)", file=sys.stderr)
    script = args[0]
    if not Path(script).exists():
        print(f"  [FAIL] 腳本不存在:{script}", file=sys.stderr)
        return 2
    sys.argv = args  # 目標腳本視角:argv[0]=script
    runpy.run_path(script, run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main())
