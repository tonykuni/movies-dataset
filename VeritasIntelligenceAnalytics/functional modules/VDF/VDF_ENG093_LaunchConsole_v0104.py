#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== VDF_ENG093_LaunchConsole_v0104(2026-10-10)=====
# 薄尾:啟動器預設值與步清單沿薄尾鏈讀(2026-10-10 VDF 管理員 engine launch 實測抓到)。
#
# v0103 的 launcher_defaults 只讀最新的 Invoke-VIA-VdfFetch-v*.ps1。R52(2026-10-02)起最新是 v0108 = 薄尾
# (「先清單、再並行全步」,步清單 $stepBook 仍在前版 v0107)→ 讀不到步清單,自測 ③ ⑩ 從那天起紅。
# 本版:沒給 text 時,從最新往前逐支讀:起始日預設取最新那支(param() 的 -Since / -Year),步清單取鏈上第一支有 $stepBook / $steps 的;
# 回傳多一欄 steps_launcher(步清單出自哪支)。給了 text 照 v0103 原樣(自測的合成 / 負控不變)。其餘函式、動詞全照 v0103。
"""VDF_ENG093_LaunchConsole — VDF 一鍵啟動台(問參數頁 + 資料庫狀況頁)
本版 v0104 薄尾見上方檔頭;用法見 USAGE(python VDF_ENG093_LaunchConsole_v0104.py help)。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG093_LaunchConsole"


def _vnum_v0104(p) -> int:
    import re
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0104(p) < _vnum_v0104(__file__)), key=_vnum_v0104)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_ORIG_DEFAULTS = PRIOR.launcher_defaults


def __getattr__(name):
    return getattr(PRIOR, name)


def launcher_defaults(text: str | None = None) -> dict:
    if text is not None:
        return _ORIG_DEFAULTS(text)
    hits = sorted((p for p in PRIOR.VIA.glob("Invoke-VIA-VdfFetch-v*.ps1") if "__pycache__" not in p.parts), key=lambda p: p.name, reverse=True)
    if not hits:
        return _ORIG_DEFAULTS("")
    reads = []
    for p in hits:
        try:
            reads.append((p, _ORIG_DEFAULTS(p.read_text(encoding="utf-8", errors="replace"))))
        except OSError as exc:
            reads.append((p, {"from_launcher": False, "steps_from_launcher": False, "why": "讀不到 %s(%s)" % (p.name, type(exc).__name__)}))
    out = dict(reads[0][1])
    out["launcher"] = hits[0].name
    out["steps_launcher"] = ""
    if not out.get("from_launcher"):
        got = next((d for _p, d in reads if d.get("from_launcher")), None)
        if got:
            out.update(since=got["since"], from_launcher=True)
    got = next(((p, d) for p, d in reads if d.get("steps_from_launcher")), None)
    if got:
        out.update(steps=got[1]["steps"], steps_from_launcher=True, steps_launcher=got[0].name)
    whys = []
    if not out.get("from_launcher"):
        whys.append("啟動器鏈 param() 讀不到起始日預設,暫用 2023-01-01")
    if not out.get("steps_from_launcher"):
        whys.append("啟動器鏈讀不到步清單($stepBook / $steps 那一行)")
    out["why"] = ";".join(whys)
    return out


PRIOR.launcher_defaults = launcher_defaults        # v0103 內部(問參數頁 · 資料矩陣 · 自測)也照鏈讀


def main() -> int:
    if "--selftest" in sys.argv[1:] or "--self-test" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · %s" % (note,)) if note != "" else ""))

    real = launcher_defaults()
    chk("v0104-① 真樹:最新啟動器是薄尾也讀得到步清單(出自鏈上前版)· 起始日照最新那支", real["steps_from_launcher"] and real["from_launcher"]
        and real["steps_launcher"] and real["launcher"], (real["launcher"], real["steps_launcher"], len(real["steps"])))
    with tempfile.TemporaryDirectory() as td:
        keep = PRIOR.VIA
        PRIOR.VIA = Path(td)
        try:
            Path(td, "Invoke-VIA-VdfFetch-v0101.ps1").write_text('param([string]$Year = "2021")\n$stepBook = "a_1,b_2"\n', encoding="utf-8")
            Path(td, "Invoke-VIA-VdfFetch-v0102.ps1").write_text('param([string]$Since = "2024-05-06")\n# thin tail\n', encoding="utf-8")
            syn = launcher_defaults()
            Path(td, "Invoke-VIA-VdfFetch-v0101.ps1").unlink()
            neg = launcher_defaults()
        finally:
            PRIOR.VIA = keep
    chk("v0104-② 合成鏈:起始日取最新(2024-05-06)· 步清單取前版(a_1,b_2)· 負控:鏈上都沒有 → 空清單並講明",
        syn["since"] == "2024-05-06" and syn["steps"] == ["a_1", "b_2"] and syn["steps_launcher"].endswith("v0101.ps1")
        and neg["steps"] == [] and "步清單" in neg["why"], (syn["since"], syn["steps"], neg["why"]))
    body = Path(__file__).read_text(encoding="utf-8")
    chk("v0104-③ 雙橋", "[VIA:ACCEL-BRIDGE:" in body and "[VIA:NET-BRIDGE:" in body)
    print("  ── v0103 自測(原樣;launcher_defaults 已換成鏈讀)──")
    prc = PRIOR.selftest()
    chk("v0104-④ v0103 自測 rc 0", prc == 0, prc)
    print("[計] VDF_ENG093_LaunchConsole_v0104 %d/%d · %s" % (sum(ok), len(ok), "PASS" if all(ok) else "FAIL"))
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
