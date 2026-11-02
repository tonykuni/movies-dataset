#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL261_UIEngine v0108 — 薄尾:前版鏈自測照模板冊 v0103 那一代跑(v0107 / v0106 自測寫死 1a 色值)· 執行面照尾冊 v0104

操作員 2026-11-02 Release Closure 令(只修缺陷 · 不擴需求)。2026-11-01 共用模板冊出 v0104(= VeritasReportNova Workbench 範本 · 三系統同一套 tokens ·
  systems.VCGC 只差品牌字)→ v0107 讀冊尾版,執行面自動換新(實跑:bg #f5f4f0 · sys #b5291a · 燈四色鎖);但 v0107 本版 ② ③ ④ 與 v0106 的自測把
  v0103 的 1a 值寫死(#f2f1ec · #9e2b25 · #2f6f6f)→ 讀到 v0104 就紅。不是功能壞,是自測綁了那一代的冊(同 HealthMatrix v0116 · VDF_SystemManager v0167)。
  容器補上 duckdb 之後才看清這個原因(之前被缺 duckdb 蓋住)。
本版只改這一件(v0100 … v0107 一字不動):
  ① 跑 v0107 自測(含它的前版鏈)時,v0107 與鏈上每支的 TK_ROOT 暫時指到只放 VIA_UI_Template_SSOT v0100 ~ v0103 副本的暫存根 · 跑完還原(不寫 registry)。
  ② 本版另驗執行面:冊尾版(≥ v0104)經 v0107 design_book 進操作台 · 米白 #f5f4f0 · 印泥紅 sys #b5291a · 燈四色仍鎖 · design.css 純 CSS。
其餘(build · 五頁 · 匯入 · 只收 VCGC 呼叫 · 零網路 · 不碰 TA-Lib)照 v0107。本檔只讀冊、不寫冊、不改他系統的檔(L120)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
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

import contextlib
import importlib.util
import io
import re
import shutil
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL261_UIEngine"
SELF_ID = "VCGC"
ERA_MAX_V0108 = 103            # v0106 / v0107 自測寫死的是 v0103 的冊值(1a)
CSS_BAD_RX_V0108 = re.compile(r"<|@import|url\s*\(|https?:", re.I)


def _vnum_v0108(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path_v0108() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = _vnum_v0108(__file__)
    hits = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0108(p) < me]
    return max(hits, key=_vnum_v0108)


PRIOR_PATH = _prior_path_v0108()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0108", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE
TK_ROOT = PRIOR.TK_ROOT


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


def _chain_v0108() -> list:
    """本版的前版(v0107)起往下:只沿真正的模組走。"""
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def prior_selftest_era() -> tuple:
    """v0107 自測(含前版鏈):TK_ROOT 暫時指到只放 v0100 ~ v0103 冊副本的暫存根 → 跑 → 還原。回 (rc, 換了幾支, 冊數, 末行)。"""
    mods = [m for m in _chain_v0108() if hasattr(m, "TK_ROOT")]
    real = Path(PRIOR.TK_ROOT) / "supportive modules" / "registry"
    with tempfile.TemporaryDirectory(prefix="cgc261_v0108_era_") as era:
        reg = Path(era) / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        n = 0
        for bk in real.glob("VIA_UI_Template_SSOT_v*.json"):
            if 0 <= _vnum_v0108(bk) <= ERA_MAX_V0108:
                shutil.copy2(str(bk), str(reg / bk.name))
                n += 1
        saved = [(m, m.TK_ROOT) for m in mods]
        for m, _ in saved:
            m.TK_ROOT = Path(era)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = PRIOR.selftest()
        finally:
            for m, v in saved:
                m.TK_ROOT = v
    last = (buf.getvalue().strip().splitlines() or ["(無輸出)"])[-1]
    return rc, len(saved), n, last


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    mods = [m for m in _chain_v0108() if hasattr(m, "TK_ROOT")]
    before = [(m, m.TK_ROOT) for m in mods]
    prior_rc, n_mod, n_book, last = prior_selftest_era()
    print(f"=== {TAG} · 薄尾自測(前版鏈照模板冊 v0103 那一代 · 執行面照尾冊)===")
    print("  ── 前版自測(摘末行)── " + last)
    chk("① 前版 %s 自測(含鏈 · 前版用 v0103 以前的冊 %d 本 · 換 %d 支 TK_ROOT)rc 0" % (PRIOR_PATH.stem, n_book, n_mod), prior_rc == 0 and n_mod > 0 and n_book > 0, f"rc {prior_rc}")
    chk("② 跑完已還原:每支 TK_ROOT 回原值(不留換裝)", all(m.TK_ROOT == v for m, v in before))
    d = PRIOR.design_book()
    t = d.get("tokens") or {}
    lamps = {"lamp-green": "#16a34a", "lamp-yellow": "#f59e0b", "lamp-red": "#dc2626", "lamp-gray": "#9ca3af"}
    chk("③ 執行面:冊尾版 %s(≥ v0104)經 design_book 進操作台 · 米白 #f5f4f0 · 印泥紅 sys #b5291a · 燈四色仍鎖" % d.get("book"),
        str(d.get("book") or "") >= "VIA_UI_Template_SSOT_v0104.json" and t.get("bg") == "#f5f4f0" and t.get("sys") == "#b5291a"
        and all(t.get(k) == v for k, v in lamps.items()), {k: t.get(k) for k in ("bg", "sys")})
    css = PRIOR.design_css(d)
    chk("④ design.css 純 CSS(沒有 < · @import · url( · http)· :root 帶 --bg:#f5f4f0", bool(css) and not CSS_BAD_RX_V0108.search(css) and "--bg:#f5f4f0" in css.replace(" ", ""))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋 · 網路工具橋在;不碰 TA-Lib;不寫模板冊;只讀",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and ".write_text(" not in text.split("def selftest", 1)[0])
    good = all(ok)
    print(f"[計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'} · {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
