#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0167 — 薄尾:前版鏈自測照模板冊 v0103 那一代跑(v0157 · v0161 的字級 / 1c 自測寫死 v0103 的色值)· 執行面照尾冊 v0104

操作員 2026-11-01:「VDF / VCGC CLOSE OUT · 擁有相同的 U/I 模板視覺或動畫視覺鎖定」→ 共用模板冊 VIA_UI_Template_SSOT 出 v0104(= VeritasReportNova Workbench 範本 ·
  三系統同一套 tokens / design.css · systems.VDF 只差品牌字)。VDF 的 typekit 段(v0157 / v0161 起)讀冊尾版,執行面自動換新;但前版鏈自測把 v0103 的值寫死
  (1c 汝窯天青 #cfe0dc / #3c6660 · 主字體微軟正黑體 · 字級 16 / 13 / 12 / 11)→ 讀到 v0104 就紅。不是功能壞,是前版自測綁了那一代的冊(同 v0166 的 ENG087 情況)。
本版只改這一件(v0100 … v0166 一字不動):
  ① 跑前版鏈自測時,鏈上每支的 TK_ROOT 暫時指到只放 VIA_UI_Template_SSOT v0100 ~ v0103 副本的暫存根(前版照它那一代驗)· 跑完還原(不寫 registry)。
  ② 本版另驗執行面:冊尾版(≥ v0104)的 tokens 進 VDF typekit(米白 #f5f4f0 · 燈四色仍鎖)· 擷取矩陣引擎 ENG236 尾版 ≥ v0101(DataFrame 表頭欄 · 印章頁首)。
其餘動詞全照 v0166。不抓網、不代設同意閘、不碰 TA-Lib、不寫模板冊。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔零網路。"""
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
import json
import os
import re
import shutil
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
ERA_MAX_V0167 = 103            # 前版鏈(v0157 · v0161)自測寫死的是 v0103 的冊值


def _vnum_v0167(path) -> int:            # 版本專屬名(元件冊以函式登記)
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0167(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0167(p) < _vnum_v0167(__file__)), key=_vnum_v0167)
PRIOR = _load_v0167(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def _chain_v0167() -> list:
    """前版鏈(只沿真正的模組走:有幾版的 PRIOR 是路徑字串 / Path,不是模組)。"""
    import types
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


def _tk_owner_v0167():
    for m in _chain_v0167():
        if "typekit_book" in vars(m) and hasattr(m, "TK_ROOT"):
            return m
    return None


def prior_selftest_era() -> tuple:
    """前版鏈自測:TK_ROOT 暫時指到只放 v0100 ~ v0103 冊副本的暫存根 → 跑 → 還原。回 (rc, 動了幾支, 冊數)。"""
    mods = [m for m in _chain_v0167() if hasattr(m, "TK_ROOT")]
    own = _tk_owner_v0167()
    real = Path(getattr(own, "TK_ROOT", HERE.parent.parent)) / "supportive modules" / "registry"
    with tempfile.TemporaryDirectory(prefix="vdf_sm0167_era_") as era:
        reg = Path(era) / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        n = 0
        for bk in real.glob("VIA_UI_Template_SSOT_v*.json"):
            if 0 <= _vnum_v0167(bk) <= ERA_MAX_V0167:
                shutil.copy2(str(bk), str(reg / bk.name))
                n += 1
        saved = [(m, m.TK_ROOT) for m in mods]
        for m, _ in saved:
            m.TK_ROOT = Path(era)
        try:
            rc = PRIOR.selftest()
        finally:
            for m, v in saved:
                m.TK_ROOT = v
    return rc, len(saved), n


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    mods = [m for m in _chain_v0167() if hasattr(m, "TK_ROOT")]
    before = [(m, m.TK_ROOT) for m in mods]
    prior_rc, n_mod, n_book = prior_selftest_era()
    print(f"=== {_STEM} {TAG} · 薄尾自測(前版鏈照模板冊 v0103 那一代 · 執行面照尾冊)===")
    chk("① 前版鏈自測(%s · 前版用 v0103 以前的冊 %d 本 · 換 %d 支 TK_ROOT)rc 0" % (PRIOR_PATH.stem, n_book, n_mod), prior_rc == 0 and n_mod > 0 and n_book > 0, f"rc {prior_rc}")
    chk("② 跑完已還原:每支 TK_ROOT 回原值(不留換裝)", all(m.TK_ROOT == v for m, v in before))
    own = _tk_owner_v0167()
    tk = own.typekit_book() if own is not None else {}
    toks = (tk or {}).get("tokens") or {}
    chk("③ 執行面:冊尾版 %s(≥ v0104)進 VDF typekit · 米白 #f5f4f0 · 燈四色仍鎖(#dc2626)" % (tk or {}).get("book"),
        str((tk or {}).get("book") or "") >= "VIA_UI_Template_SSOT_v0104.json" and toks.get("bg") == "#f5f4f0" and toks.get("lamp-red") == "#dc2626", toks.get("bg"))
    eng = sorted((HERE / "engine").glob("VDF_ENG236_FetchMatrixUI_v*.py"), key=_vnum_v0167)
    chk("④ 擷取矩陣引擎尾版 ≥ v0101(DataFrame 表頭欄 · 印章頁首 · 範本覆蓋):%s" % (eng[-1].name if eng else "—"), bool(eng) and _vnum_v0167(eng[-1]) >= 101)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑤ 加速器橋 · 網路工具橋在;執行面 main 直通前版;不碰 TA-Lib;不代設同意閘;不寫模板冊",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and "CONSENT\"] =" not in body and "VIA_UI_Template_SSOT_v*.json\").write" not in text)
    good = all(ok)
    print(f"  [計] {_STEM} {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
