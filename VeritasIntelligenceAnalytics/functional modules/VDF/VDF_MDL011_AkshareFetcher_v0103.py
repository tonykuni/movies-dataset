#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL011_AkshareFetcher v0103 — 薄尾:缺套件(polars / duckdb / akshare)= 誠實 NODATA rc 2,不再匯入就崩

實測(2026-10-15 VDF 獨立實測,容器沒 polars):v0102 --selftest rc 1,Traceback 停在 v0100 L891 `import polars as pl`
  (載前版鏈就崩,連用法都印不出)。VDF 律:缺件不是壞掉 → 本版載前版鏈時接 ModuleNotFoundError:
  · 載得起來 → 一切照 v0102(所有動詞、deep-macro、自測);v0102 自測 rc 照實合計(v0102 本版過但前版鏈紅時它回 0 = 假綠,本版改回 2)。
  · 載不起來 → 任何動詞印 [ABSENT] 缺哪個套件 + rc 2(NODATA);--selftest 跑本版自己的檢查後回 2(不算綠)。
  不代裝套件、不抓網、不讀寫同意閘、不碰 TA-Lib。VDF 自己的模組,不載入他系統程式。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL011_AkshareFetcher"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0103(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0103(p) < _vnum_v0103(__file__)), key=_vnum_v0103)


def _load_prior(path: Path):
    """→ (module | None, 缺的套件名 | None)。只接「缺套件」;其他例外照拋(真壞要看得到)。"""
    spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
    except ModuleNotFoundError as exc:
        sys.modules.pop(spec.name, None)
        return None, (exc.name or str(exc))
    return mod, None


PRIOR, MISSING = _load_prior(PRIOR_PATH)


def __getattr__(name):
    if PRIOR is None:
        raise AttributeError(f"{TAG}:前版鏈缺套件 {MISSING},{name} 不可用(NODATA)")
    return getattr(PRIOR, name)


def absent_line() -> str:
    return f"[ABSENT] {TAG}:缺套件 {MISSING}(缺件不是壞掉;裝好後重跑。本檔不代裝)→ rc 2 NODATA"


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(缺套件 = NODATA)===")
    import tempfile
    with tempfile.TemporaryDirectory(prefix="mdl011_v0103_") as td:
        bad = Path(td) / "fake_prior_v0001.py"
        bad.write_text("import via_no_such_pkg_v0103\n", encoding="utf-8")
        boom = Path(td) / "boom_prior_v0001.py"
        boom.write_text("raise ValueError('real defect')\n", encoding="utf-8")
        mod, miss = _load_prior(bad)
        chk("① 前版缺套件 → (None, 套件名),不崩", mod is None and miss == "via_no_such_pkg_v0103", miss)
        try:
            _load_prior(boom)
            raised = False
        except ValueError:
            raised = True
        chk("② 非缺套件的例外照拋(真壞不吞)", raised)
    keep = (globals()["PRIOR"], globals()["MISSING"])
    globals()["PRIOR"], globals()["MISSING"] = None, "polars"
    try:
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_any = main(["fetch", "x"])
        try:
            __getattr__("run_selection")
            ae = False
        except AttributeError:
            ae = True
        chk("③ 缺套件時任何動詞 rc 2 + [ABSENT] 點名套件;取名稱回 AttributeError(不是 NameError 崩)",
            rc_any == 2 and "[ABSENT]" in buf.getvalue() and "polars" in buf.getvalue() and ae, buf.getvalue().strip()[:120])
    finally:
        globals()["PRIOR"], globals()["MISSING"] = keep
    text = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋 · 網路工具橋(def _via_net)在;不碰 TA-Lib;不寫同意閘",
        "VIA:ACCEL-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+" + "talib", text, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_" + "CONSENT", text))
    n = sum(ok)
    if n != len(ok):
        print(f"  [計] {TAG} 本版 {n}/{len(ok)} · FAIL")
        return 1
    if PRIOR is None:
        print("  " + absent_line())
        print(f"  [計] {TAG} 本版 {n}/{len(ok)} · 前版鏈 NODATA(缺 {MISSING})· 合計 NODATA rc 2")
        return 2
    rc0 = PRIOR.selftest()
    print(f"  [計] {TAG} 本版 {n}/{len(ok)} · v0102 鏈 rc {rc0} · 合計 {'PASS' if rc0 == 0 else '照實回 ' + str(rc0 if rc0 in (2, 3) else 2)}")
    return 0 if rc0 == 0 else (rc0 if rc0 in (2, 3) else 2)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if PRIOR is None:
        print(absent_line())
        return 2
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
