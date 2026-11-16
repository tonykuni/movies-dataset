#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL245_SDDValidator v0108 — v0107 薄尾(v0107 一字不動):本體 rel() 碰到 VIA 樹外的引擎不再整支炸。

實錄(2026-11-13 容器 ssot panorama · 慢性 RED「上下連結@VCGC · 正主呼叫失敗 ValueError」):
  工作流冊登了倉根的 VIA_MCP_Engine/VIA_MCP_Engine_v0103.py(MCP 引擎本來就在 VeritasIntelligenceAnalytics 外);
  本體 v0100 的 rel(p) = p.resolve().relative_to(VIA) → 樹外路徑丟 ValueError → check_engines 整支炸 →
  X-* 列一列都出不來,全景把整個「上下連結」判 RED(假紅;v0107 自測也被同一個錯炸掉)。
本版只換本體的 rel():樹內照舊回 VIA 相對路徑(一字不差);樹外回對 VIA 的相對路徑(../VIA_MCP_Engine/…),不丟例外。
  換裝在本體模組上(BASE.rel = rel),全景沿 PRIOR 鏈走到本體呼叫 check() 時就是新的 rel;其餘全照 v0107。
只讀,不寫冊 · 零網路 · 不用 TA-Lib · 不寫同意閘。
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
# [VIA:NET-BRIDGE] 留名:本版不出網

import contextlib
import importlib.util
import io
import os
import re
import sys
from pathlib import Path

VERSION = "v0108"
ENGINE = "CGC_MDL245_SDDValidator " + VERSION
HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL245_SDDValidator"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_v0108", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_REL_V0100 = BASE.rel


def __getattr__(name):
    return getattr(PRIOR, name)


def rel(p) -> str:
    """樹內 = 照 v0100(VIA 相對 posix);樹外 = 對 VIA 的相對路徑(../…),不丟例外。"""
    rp = Path(p).resolve()
    via = BASE.VIA.resolve()
    try:
        return rp.relative_to(via).as_posix()
    except ValueError:
        return Path(os.path.relpath(rp, via)).as_posix()


BASE.rel = rel                       # 本體 check_engines / exemption / real / closeout 用模組全域名 rel → 換成本版


def main(argv=None):
    if (sys.argv[1:] if argv is None else argv)[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:200]) if note else ''}", flush=True)

    print(f"=== {ENGINE} · 薄尾自測(rel 樹外不炸;其餘照 v0107)===", flush=True)
    via = BASE.VIA.resolve()
    outside = via.parent / "VIA_MCP_Engine" / "VIA_MCP_Engine_v0103.py"
    inside = via / "supportive modules" / "registry" / "x.py"
    err = ""
    try:
        _REL_V0100(outside)
    except ValueError as exc:
        err = type(exc).__name__
    chk("① 重現:v0100 rel 碰到 VIA 樹外的 MCP 引擎 → ValueError", err == "ValueError", err or "沒炸")
    chk("② 本版:樹外回 ../VIA_MCP_Engine/VIA_MCP_Engine_v0103.py,不丟例外", rel(outside) == "../VIA_MCP_Engine/VIA_MCP_Engine_v0103.py", rel(outside))
    chk("③ 樹內一字照 v0100", rel(inside) == _REL_V0100(inside) == "supportive modules/registry/x.py", rel(inside))
    chk("④ 換裝:本體模組的 rel 指本版", BASE.rel is rel)
    try:
        rep = BASE.check(write=False)
        why = ""
    except Exception as exc:  # noqa: BLE001 — 照實記
        rep, why = None, f"{type(exc).__name__}: {str(exc)[:120]}"
    chk("⑤ 本體 check(write=False) 跑完(不再整支炸)", rep is not None, why or "OK")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc = PRIOR.selftest()
        except Exception as exc:  # noqa: BLE001
            rc = f"{type(exc).__name__}"
    out = buf.getvalue()
    print("  ── 前版 v0107 自測(換裝本版 rel 後)──", flush=True)
    print(out, end="")
    chk("⑥ v0107 自測(原本被同一個 ValueError 炸掉)換裝後通過", rc == 0, f"rc {rc}")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 只讀 · 不寫冊 · 不出網 · 不用 TA-Lib", (".write" + "_text(") not in src and not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib)", src, re.M))
    n = sum(ok)
    print(f"  [計] {ENGINE} 薄尾 {n}/{len(ok)} · 合計 {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
