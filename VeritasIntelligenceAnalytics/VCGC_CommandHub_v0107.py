#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0107 — 薄尾(v0100–v0106 一字不動):程式與資料分開放時,bak / pano 照樣找得到工具

PR #733 Codex 審查(P2):PS 載入器支援「資料根(VIA_ROOT)≠ 程式樹(VIA_CODE_ROOT)」,v0101 的 search_roots()
  也是先找資料根、再找程式樹;但 v0105 的 bak / pano 只在 VIA_ROOT 底下找 ApplyRun、CGC_SystemManager、
  Graphify boot 行與格式鎖冊 → 分開放的機器上 via-bak 回 1(找不到 ApplyRun)、via-pano 找不到管理器。
本版只補「找工具」這一步(換在定義它的 v0105 那一層):
  tail(d, stem)       先照舊找 d;找不到且 d 在資料根底下 → 依 search_roots() 的順序到其他根的同一相對路徑找
  graphify_boot()     沒給 via 時,用第一個有 Graphify 釋出夾的根(資料根優先)
  lamp_css()          沒給 via 時,用第一個有格式鎖冊的根(資料根優先)
報告、備份、交接筆記照舊寫資料根(VIA_ROOT)。不 import 他系統。零 TA-Lib。
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0107"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name: str):
    """前版鏈上自己定義 name 的那一版(換在真正被讀的那一層;R4 換錯層)。"""
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if name in vars(m):
            return m
        m = vars(m).get("PRIOR") or vars(m).get("P0")
    return None


HUB = _owner("cmd_bak")                     # v0105:bak / pano 與 tail · graphify_boot · lamp_css 都在這
ROOTS = _owner("search_roots")              # v0101:資料根 → 程式樹 → VIA_CODE_ROOT
_TAIL0, _GBOOT0, _CSS0 = HUB.tail, HUB.graphify_boot, HUB.lamp_css


def _roots() -> list:
    """找工具的根:先資料根(與 v0101 / PS Find-ViaTail 同序),再 search_roots() 的其他根。"""
    out = []
    for r in [HUB.VIA_ROOT] + list(ROOTS.search_roots()):
        p = Path(r).resolve()
        if p not in out:
            out.append(p)
    return out


def tail(d: Path, stem: str):
    hit = _TAIL0(d, stem)
    if hit is not None:
        return hit
    try:
        rel = Path(d).resolve().relative_to(Path(HUB.VIA_ROOT).resolve())
    except ValueError:
        return None
    for r in _roots()[1:]:
        hit = _TAIL0(r / rel, stem)
        if hit is not None:
            return hit
    return None


def _first_root(*rel) -> Path:
    for r in _roots():
        if r.joinpath(*rel).exists():
            return r
    return Path(HUB.VIA_ROOT)


def graphify_boot(via: Path = None) -> tuple:
    return _GBOOT0(via if via is not None else _first_root(HUB.AI, "via_graphify_v0101"))


def lamp_css(via: Path = None) -> str:
    if via is None:
        via = next((r for r in _roots() if any((r / HUB.REG).glob("VIA_UI_FormatLock_v*.json"))), Path(HUB.VIA_ROOT))
    return _CSS0(via)


HUB.tail, HUB.graphify_boot, HUB.lamp_css = tail, graphify_boot, lamp_css


def main(argv: list | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 6 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 換在定義它的那一層:tail / graphify_boot / lamp_css 在 v0105,search_roots 在 v0101",
        Path(HUB.__file__).name == "VCGC_CommandHub_v0105.py" and Path(ROOTS.__file__).name == "VCGC_CommandHub_v0101.py"
        and HUB.tail is tail and HUB.graphify_boot is graphify_boot and HUB.lamp_css is lamp_css,
        (getattr(HUB, "__file__", None), getattr(ROOTS, "__file__", None)))
    code_via = Path(ROOTS.CODE_ROOT).resolve()
    keep = (HUB.VIA_ROOT, ROOTS.DATA_ROOT)
    with tempfile.TemporaryDirectory(prefix="hub107_") as td:
        data = Path(td) / "data"
        (data / HUB.AI).mkdir(parents=True)
        try:
            HUB.VIA_ROOT = ROOTS.DATA_ROOT = data                      # 模擬程式與資料分開放
            ar, cm = tail(data / HUB.AI, "VIA_VCGC_ApplyRun"), HUB.manager()
            want_ar = _TAIL0(code_via / HUB.AI, "VIA_VCGC_ApplyRun")
            want_cm = _TAIL0(code_via / HUB.REG, "CGC_SystemManager")
            chk("T2 資料根沒有工具 → 到程式樹找 ApplyRun 與 CGC_SystemManager(Codex 重現的兩個點)",
                ar is not None and ar == want_ar and cm is not None and cm == want_cm, (ar, cm))
            fake = data / HUB.AI / "VIA_VCGC_ApplyRun_v9999.py"
            fake.write_text("# 資料根自己的版本\n", encoding="utf-8")
            chk("T3 資料根有工具時仍以資料根為先(與 v0101 / PS 同序)", tail(data / HUB.AI, "VIA_VCGC_ApplyRun") == fake)
            fake.unlink()
            g0, g1 = _GBOOT0(code_via), graphify_boot()
            chk("T4 Graphify boot 行:資料根沒有 → 用程式樹那份(結果與直接讀程式樹相同)", g0 == g1, (g0[2], g1[2]))
            chk("T5 格式鎖冊的燈色:資料根沒有 → 用程式樹那份", lamp_css() == _CSS0(code_via), len(lamp_css()))
            chk("T6 報告仍寫資料根", Path(HUB.write_report("自測", [{"category": "A", "metric": "m", "status": "GREEN", "detail": "", "action": ""}], None, None)).resolve().is_relative_to(data.resolve()))
        finally:
            HUB.VIA_ROOT, ROOTS.DATA_ROOT = keep
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(原函式)" % PRIOR_PATH.name, flush=True)
    HUB.tail, HUB.graphify_boot, HUB.lamp_css = _TAIL0, _GBOOT0, _CSS0   # 前版自測照它原本的鏈跑(前版自測慣例)
    try:
        rc_prior = PRIOR.selftest()
    finally:
        HUB.tail, HUB.graphify_boot, HUB.lamp_css = tail, graphify_boot, lamp_css
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
