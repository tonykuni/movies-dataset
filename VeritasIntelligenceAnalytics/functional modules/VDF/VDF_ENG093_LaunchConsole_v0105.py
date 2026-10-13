#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== VDF_ENG093_LaunchConsole_v0105(2026-10-13)=====
# 薄尾:問參數頁的矩陣把清單先行的兩步(tw_list = VDF_MDL009 台股個股清單自動更新 · etf_list = VDF_MDL010 主動式台股 ETF 清單自動更新)
# 放在最前面、鎖定必跑(勾不掉、不經 -Steps:CGC_MDL134 v0102 在並行道自動先跑),逐一引擎自測也能測它們。
#
# 操作員令(2026-10-13):「要先確令台股個股清單生成引擎自動更新以及主動式台股ETF清單自動更新生成引擎正常作業  輸出作為其他引擎的輸入  VDF 一鍵啟動」。
# 根因:矩陣只列啟動器 $stepBook 的 11 步(Invoke-VIA-VdfFetch v0107),清單兩步不在那一行;v0103 的 validate 只收 $stepBook 的步,
#   所以頁上不能把它們送進 -Steps。本版:steps_matrix() 把兩步放最前(步冊 CGC_MDL125 v0112 起才有;冊上沒有就不列);
#   _matrix_rows() 把它們畫成鎖定列(checked · disabled · class lock,JS 的 boxes() 只數 .stp,「已勾 n/m」與 -Steps 不含它們);
#   decision / validate / 啟動器 / 其餘動詞全照 v0104。
"""VDF_ENG093_LaunchConsole — VDF 一鍵啟動台(問參數頁 + 資料庫狀況頁)
本版 v0105 薄尾見上方檔頭;用法見 USAGE(python VDF_ENG093_LaunchConsole_v0105.py help)。
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
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG093_LaunchConsole"
TAG = "v0105"
LIST_STEPS_V0105 = ("tw_list", "etf_list")
LOCK_NOTE_V0105 = "清單先行 · 必跑(CGC_MDL134 v0102 在並行道自動先跑,不經 -Steps;每次啟動都更新清單)"


def _vnum_v0105(p) -> int:
    import re
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0105(p) < _vnum_v0105(__file__)), key=_vnum_v0105)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + TAG, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner_v0105(name: str):
    import types
    m = PRIOR
    while isinstance(m, types.ModuleType):
        if name in vars(m):
            return m
        m = getattr(m, "PRIOR", None)
    return None


_OWN = _owner_v0105("steps_matrix")          # v0103 本體(問參數頁 · 矩陣 · 動詞)
_ORIG_MATRIX, _ORIG_ROWS, _ORIG_VERSION = _OWN.steps_matrix, _OWN._matrix_rows, _OWN.VERSION


def steps_matrix(since: str, steps: list | None) -> dict:
    """前版矩陣;清單兩步放最前(啟動器步清單沒列也放;步冊沒有就不列,照實)。"""
    want = None
    if steps:
        want = [x for x in LIST_STEPS_V0105 if x not in steps] + list(steps)
    mx = _ORIG_MATRIX(since, want)
    rows = []
    for r in mx.get("rows") or []:
        if r.get("id") in LIST_STEPS_V0105:
            if r.get("missing"):
                continue                     # 步冊還是舊版(沒有清單步)→ 不列、不假裝
            r = dict(r, lock=True, why=((r.get("why") or "") + " · " + LOCK_NOTE_V0105).strip(" ·"))
        rows.append(r)
    mx["rows"] = rows
    return mx


def _matrix_rows(mx: dict, allowed: list) -> str:
    """前版畫列(清單步算 allowed 才有自測鈕與勾);再把清單列改成鎖定列(checked · disabled · class lock)。"""
    html = _ORIG_ROWS(mx, list(allowed) + [x for x in LIST_STEPS_V0105 if x not in allowed])
    for sid in LIST_STEPS_V0105:
        html = html.replace(f"<input type='checkbox' class='stp' value='{sid}' checked>",
                            f"<input type='checkbox' class='lock' value='{sid}' checked disabled title='{LOCK_NOTE_V0105}'>")
    return html


def _patch_v0105(on: bool) -> None:
    _OWN.steps_matrix = steps_matrix if on else _ORIG_MATRIX
    _OWN._matrix_rows = _matrix_rows if on else _ORIG_ROWS
    _OWN.VERSION = TAG[1:] if on else _ORIG_VERSION


_patch_v0105(True)


def main() -> int:
    if "--selftest" in sys.argv[1:] or "--self-test" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · %s" % (note,)) if note != "" else ""))

    print("=== %s %s · 薄尾自測(清單先行鎖定列)===" % (_STEM, TAG))
    d = PRIOR.launcher_defaults()
    mx = steps_matrix(d["since"], d["steps"] or None)
    ids = [r["id"] for r in mx["rows"]]
    chk("v0105-① 真樹:矩陣最前兩列 tw_list · etf_list(鎖定 · 引擎在位 · 步冊 CGC_MDL125 尾版)· 啟動器的步照舊在後",
        ids[:2] == ["tw_list", "etf_list"] and all(r.get("lock") and r.get("engine_ok") and LOCK_NOTE_V0105 in r["why"] for r in mx["rows"][:2])
        and ids[2:] == list(d["steps"]), (ids[:4], mx.get("src")))
    allowed = [s for s in d["steps"] if any(r["id"] == s and not r.get("missing") and r.get("engine_ok") for r in mx["rows"])]
    html = _matrix_rows(mx, allowed)
    chk("v0105-② 鎖定列:兩列 class lock · checked · disabled;其餘 .stp 數 = allowed 數(JS boxes() 與 -Steps 不含清單步)",
        all(f"class='lock' value='{s}' checked disabled" in html for s in LIST_STEPS_V0105) and html.count("class='stp'") == len(allowed)
        and "value='tw_list' checked>" not in html, (html.count("class='stp'"), len(allowed)))
    from datetime import date
    ok1, r1 = PRIOR.validate({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": list(allowed[:2]), "dry": True, "noheal": False}, d, allowed, date(2026, 10, 13))
    ok2, r2 = PRIOR.validate({"action": "launch", "mode": "custom", "since": "2024-03-15", "steps": ["tw_list"], "dry": True, "noheal": False}, d, allowed, date(2026, 10, 13))
    chk("v0105-③ 決定不變:頁上勾的步照舊送 -Steps;清單步不送(validate 照舊只收啟動器的步 → 'tw_list' 被拒,交 CGC_MDL134 自動先跑)",
        ok1 and r1.get("action") == "launch" and "tw_list" not in r1.get("steps", []) and not ok2, (r1.get("steps"), r2))
    chk("v0105-④ 本體已換:v0103 的 steps_matrix / _matrix_rows 指到本版 · 頁首版號 = 本版",
        _OWN.steps_matrix is steps_matrix and _OWN._matrix_rows is _matrix_rows and _OWN.VERSION == TAG[1:])
    ctx = {"ts": "2026-10-13 00:00:00", "defaults": d, "matrix": mx, "allowed": allowed,
           "db": {"state": "ABSENT", "why": "自測不讀目錄", "categories": [], "gaps": [], "frozen": []}, "ready": {"state": "GATED", "gates": {}, "next": []}}
    try:
        page = PRIOR.render_ask(ctx, "t0ken")
    except Exception as exc:
        page = "RENDER FAIL " + type(exc).__name__
    chk("v0105-⑤ 問參數頁渲染:v0105 字樣 · 兩列鎖定在矩陣最前 · 清單先行註記在頁上",
        "VDF_ENG093 v0105" in page and "class='lock' value='tw_list'" in page and "class='lock' value='etf_list'" in page and LOCK_NOTE_V0105 in page
        and page.index("value='etf_list'") < page.index("value='datahome'"), page[:80] if page.startswith("RENDER") else "")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("v0105-⑥ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib · 不代設同意閘 · 不直派子行程",
        "[VIA:ACCEL-BRIDGE:" in src and "[VIA:NET-BRIDGE:" in src and src.index("from __future__") < src.index("[VIA:ACCEL-BRIDGE:")
        and "import " + "talib" not in src and 'environ["VIA_NET_' + 'CONSENT"] = "' not in src and "import " + "subprocess" not in src)
    print("  ── 前版鏈自測(用它們自己的矩陣;VIA_SKIP_PRIOR_SELFTEST=1 略過)──")
    _patch_v0105(False)
    try:
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    finally:
        _patch_v0105(True)
    chk("v0105-⑦ 前版 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("  [計] %s %s 薄尾 %d/%d · %s" % (_STEM, TAG, sum(ok), len(ok), "PASS" if all(ok) else "FAIL"))
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
