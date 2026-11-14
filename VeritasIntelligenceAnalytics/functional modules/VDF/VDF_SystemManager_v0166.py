#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0166 — 薄尾:自測隨冊也隨引擎(前版鏈照「出貨冊 v0101」跑時,ENG087 取同一代的那一版)

CI 實測(PR #579 · 2026-11-01 run 41321202377「VDF manager self-test through the sole entry」rc 1):
  範圍冊 v0104 + ENG087 v0107 把兩條代號正則改寫成 [0-9](操作員令「正則兩條照你說的改」)。執行面 universe check
  (尾冊 v0104 對尾版 ENG087 v0107)GREEN;但 v0124 跑前版鏈時把 v0121 的 book_path 釘回出貨冊 v0101(\\d 寫法),
  v0121 自測 ⑦ 拿它去比「ENG087 尾版」(已是 [0-9])→ 「IN-01 regex 與 ENG087 STOCK_CODE 不同」→ 一路紅到 v0165。
  不是功能壞,是前版自測把「冊」釘回出貨那一代,「引擎」卻沒有跟著釘。本版只改這一件(v0100 … v0165 一字不動):
  ① 跑前版鏈自測時,v0121 的 _eng087 換成「依當下生效的冊挑 ENG087」:從尾版往回找第一個 STOCK_CODE / ACTIVE_ETF_CODE
     與那本冊 IN-01 / IN-02 code_regex 逐字相同的版本(冊被釘回 v0101 → v0106;尾冊 v0104 → v0107);一個都對不上才用尾版
     (照樣紅,不放水)。跑完還原。
  ② 本版另驗執行面:尾冊對尾版 ENG087 的 universe check 仍 GREEN(真的不一致照紅)。
其餘動詞全照 v0165(並行 engine launch · 擷取矩陣頁籤 · export / tables / fetchmatrix)。不抓網、不代設同意閘、不碰 TA-Lib。
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
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
ENG087_GLOB_V0166 = "VDF_ENG087_MarketListGovernance_v[0-9][0-9][0-9][0-9].py"
SHIPPED_BOOK_V0166 = "VDF_InputUniverse_SSOT_v0101.json"      # v0124 釘回的出貨冊(本版自測用來驗挑版)


def _vnum_v0166(path) -> int:            # 版本專屬名:元件冊以函式登記,共用名會把前版的紀錄搶走
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0166(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0166(p) < _vnum_v0166(__file__)), key=_vnum_v0166)
PRIOR = _load_v0166(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    return PRIOR.main(args)


def _universe_owner_v0166():
    """沿前版鏈找定義 _eng087 與 book_path 的那一版(v0121);找不到回 None。"""
    m = PRIOR
    while m is not None:
        if "_eng087" in vars(m) and "book_path" in vars(m):
            return m
        m = vars(m).get("PRIOR")
    return None


def _patterns_v0166(mod) -> tuple:
    try:
        return (getattr(mod, "STOCK_CODE").pattern, getattr(mod, "ACTIVE_ETF_CODE").pattern)
    except Exception:  # noqa: BLE001 — 載不起來 / 沒有這兩個名字 = 這一版不合格,換下一版
        return (None, None)


def _book_patterns_v0166(path: Path) -> tuple:
    ins = {i.get("id"): i for i in (json.loads(Path(path).read_text(encoding="utf-8")).get("inputs") or []) if isinstance(i, dict)}
    return ((ins.get("IN-01") or {}).get("code_regex"), (ins.get("IN-02") or {}).get("code_regex"))


def eng087_for_book(owner, original, cache: dict):
    """依 owner.book_path() 當下指的冊,挑 ENG087:尾版往回第一個兩條正則逐字相同的版本;都不同 → original()(照樣紅)。"""
    want = _book_patterns_v0166(owner.book_path())
    for p in sorted((HERE / "engine").glob(ENG087_GLOB_V0166), key=_vnum_v0166, reverse=True):
        if p not in cache:
            try:
                cache[p] = _load_v0166(p, "_vdf_eng087_for_book_" + p.stem)
            except Exception:  # noqa: BLE001 — 某一版載不起來就略過那一版(記在 cache 為 None)
                cache[p] = None
        if cache[p] is not None and _patterns_v0166(cache[p]) == want:
            return cache[p]
    return original()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    owner = _universe_owner_v0166()
    original = owner._eng087 if owner is not None else None
    cache = {}
    if owner is not None:
        owner._eng087 = lambda: eng087_for_book(owner, original, cache)      # 前版鏈:冊釘哪一代,引擎就取那一代
    try:
        prior_rc = PRIOR.selftest()
    finally:
        if owner is not None:
            owner._eng087 = original
    print(f"=== {_STEM} {TAG} · 薄尾自測(前版鏈:冊釘出貨代 → ENG087 也取同一代;執行面照尾冊對尾版)===")
    chk("① 前版鏈自測(%s)rc 0" % PRIOR_PATH.stem, prior_rc == 0 and owner is not None, f"rc {prior_rc}")
    chk("② 跑完已還原:v0121 的 _eng087 回到取尾版那支(不留換裝)", owner is not None and owner._eng087 is original)
    if owner is None:
        print(f"  [計] {_STEM} {TAG} 本版 {sum(ok)}/{len(ok)} · FAIL(前版鏈找不到 v0121)")
        return 1
    run = owner.check()
    chk("③ 執行面:尾冊 %s 對 ENG087 尾版 → universe check %s(regex 一致)" % (run.get("book"), run.get("state")),
        run.get("state") == "GREEN" and not [x for x in run.get("problems") or [] if "regex" in x], run.get("problems"))
    shipped = HERE / SHIPPED_BOOK_V0166
    keep_bp = owner.book_path
    try:
        owner.book_path = lambda: shipped
        picked = eng087_for_book(owner, original, {})
        raw = original()
        want = _book_patterns_v0166(shipped)
        chk("④ 挑版:冊釘回 %s(%s)→ 取到 %s(兩條正則逐字相同);直接拿尾版就不同(%s)= 本版要修的那個紅"
            % (shipped.name, want[0], Path(getattr(picked, "__file__", "?")).name, _patterns_v0166(raw)[0]),
            _patterns_v0166(picked) == want and _patterns_v0166(raw) != want)
        owner._eng087 = lambda: eng087_for_book(owner, original, {})
        pinned = owner.check()
        chk("⑤ 冊釘 v0101 + 依冊挑引擎 → v0121 check %s(⑦ 那條不再紅)" % pinned.get("state"),
            not [x for x in pinned.get("problems") or [] if "regex" in x], pinned.get("problems"))
    finally:
        owner.book_path = keep_bp
        owner._eng087 = original
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑥ 加速器橋 · 網路工具橋在;只在自測時換裝(執行面 main 直通前版);不碰 TA-Lib;不代設同意閘",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "owner._eng087 =" not in body.split("def eng087_for_book", 1)[0]
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and "CONSENT\"] =" not in body)
    good = all(ok)
    print(f"  [計] {_STEM} {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
