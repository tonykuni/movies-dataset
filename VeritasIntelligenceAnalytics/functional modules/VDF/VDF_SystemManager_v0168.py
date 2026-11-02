#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0168 — 薄尾:修 v0167 自測第 ③ 項驗錯欄(色值在 typekit 的 design 段,不在字級 tokens)

操作員 2026-11-02 Release Closure 令(只修缺陷 · 不擴需求)。雲端容器補上 duckdb 1.5 後跑 VDF 管理器整條自測:前版鏈 v0100 … v0166 全 PASS,
只剩 v0167 本版 ③「冊尾版 v0104 進 VDF typekit · 米白 #f5f4f0 · 燈四色仍鎖」FAIL。根因:v0154 的 typekit_book 只收字級 token(TK_DEFAULT_TOKENS 白名單 ·
設計如此),色值由 v0161 的 design_book 放在 typekit_book()["design"]["tokens"];v0167 的 ③ 去字級 tokens 找 bg → 永遠 None。執行面本來就對(頁面用的是 design 段)。
本版只改這一件(v0100 … v0167 一字不動):
  · 自測照 v0167 的 ① ② ④ ⑤(直接用 v0167 的 prior_selftest_era · 前版鏈照模板冊 v0103 那一代驗)· ③ 改驗 design 段:冊尾版 ≥ v0104 · bg #f5f4f0 · lamp-red #dc2626。
  · 不再呼叫 v0167.selftest()(它的 ③ 驗錯欄 · 會把這個已知誤判帶上來)。
其餘動詞全照 v0167 → v0166。不抓網、不代設同意閘、不碰 TA-Lib、不寫模板冊。
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
import re
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum_v0168(path) -> int:            # 版本專屬名(元件冊以函式登記)
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0168(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0168(p) < _vnum_v0168(__file__)), key=_vnum_v0168)
PRIOR = _load_v0168(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def design_tokens_v0168(tk: dict | None) -> dict:
    """typekit_book() 的色值在 design 段(v0161 design_book);字級 tokens 只收字級白名單(v0154)。"""
    d = (tk or {}).get("design") or {}
    return {"book": d.get("book"), "tokens": d.get("tokens") or {}}


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    mods = [m for m in PRIOR._chain_v0167() if hasattr(m, "TK_ROOT")]
    before = [(m, m.TK_ROOT) for m in mods]
    prior_rc, n_mod, n_book = PRIOR.prior_selftest_era()          # = v0167 ①:v0166 以前的鏈照模板冊 v0103 那一代驗
    print(f"=== {_STEM} {TAG} · 薄尾自測(前版鏈照模板冊 v0103 那一代 · 執行面照尾冊 · ③ 驗 design 段)===")
    chk("① 前版鏈自測(%s 的前版鏈 · v0103 以前的冊 %d 本 · 換 %d 支 TK_ROOT)rc 0" % (PRIOR_PATH.stem, n_book, n_mod), prior_rc == 0 and n_mod > 0 and n_book > 0, f"rc {prior_rc}")
    chk("② 跑完已還原:每支 TK_ROOT 回原值(不留換裝)", all(m.TK_ROOT == v for m, v in before))
    own = PRIOR._tk_owner_v0167()
    tk = own.typekit_book() if own is not None else {}
    dz = design_tokens_v0168(tk)
    toks = dz["tokens"]
    chk("③ 執行面:冊尾版 %s(≥ v0104)的色值進 VDF typekit design 段 · 米白 #f5f4f0 · 燈四色仍鎖(#dc2626)" % dz["book"],
        str(dz["book"] or "") >= "VIA_UI_Template_SSOT_v0104.json" and toks.get("bg") == "#f5f4f0" and toks.get("lamp-red") == "#dc2626", toks.get("bg"))
    bad = design_tokens_v0168({"tokens": {"bg": "#f5f4f0"}})
    chk("③b 字級 tokens 裡有 bg 也不算(只認 design 段)· 沒有 design 段 → 空", bad == {"book": None, "tokens": {}})
    eng = sorted((HERE / "engine").glob("VDF_ENG236_FetchMatrixUI_v*.py"), key=_vnum_v0168)
    chk("④ 擷取矩陣引擎尾版 ≥ v0101(DataFrame 表頭欄 · 印章頁首 · 範本覆蓋):%s" % (eng[-1].name if eng else "—"), bool(eng) and _vnum_v0168(eng[-1]) >= 101)
    text = Path(__file__).read_text(encoding="utf-8")
    head = text.split("def selftest", 1)[0]
    chk("⑤ 加速器橋 · 網路工具橋在;執行面 main 直通前版;不碰 TA-Lib;不代設同意閘;不寫模板冊;不呼叫 v0167 的自測(③ 誤判)",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and "CONSENT\"] =" not in head and "VIA_UI_Template_SSOT_v*.json\").write" not in text and ("PRIOR." + "selftest()") not in text)
    good = all(ok)
    print(f"  [計] {_STEM} {TAG} 本版 {sum(ok)}/{len(ok)} · 前版鏈 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
