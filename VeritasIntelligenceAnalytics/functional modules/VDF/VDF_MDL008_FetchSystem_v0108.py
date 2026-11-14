#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0108 — 薄尾:擷取冊 v0108(MDL009 改指 v0103 · 清單帶 shares_issued 等 T1 欄)

桌機實錄(操作員貼回 2026-11-11 01:07):總控 fetch run MDL009 --apply → [OK] 53.8s,但清單沒有 shares_issued;
ENG238 持股率 1,176,852 列全空。根因:本系統 v0107 載入的是冊 v0106(冊 v0107 是 2026-11-08 才登的 014),兩本都把 009 釘在
VDF_MDL009_TWStockList_v0102.py —— v0103(T1 欄)從沒被總控跑到。
本版只改一列(照 v0102 改指 v0101 的前例):
  · 冊 v0108 = 冊 v0107 原樣,只有 009 → VDF_MDL009_TWStockList_v0103.py(輸出路徑 · 參數 · 次序不變);MDL012 取冊尾版也跟著指 v0103。
  · 本系統載冊:其餘列照 v0107 行為(冊 v0106 的 36 列,不因此把 014 拉進 fetch —— 不擴範圍),009 列取冊 v0108。
其餘(live 改道 · curl_cffi · run 子行程 · 列上限)全照 v0107。不碰 TA-Lib;不讀寫同意閘(只問網路工具)。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
BOOK_V0108 = HERE / "VDF_FetchSystem_SSOT_v0108.json"
MDL009_FILE_V0108 = "VDF_MDL009_TWStockList_v0103.py"


def _vnum_v0108(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0108(p) < _vnum_v0108(__file__)), key=_vnum_v0108)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0105, V0101, BASE = PRIOR.V0105, PRIOR.V0101, PRIOR.BASE
_LOAD_V0107 = PRIOR.load_book_v0107


def __getattr__(name):
    return getattr(PRIOR, name)


def _row009_v0108() -> dict | None:
    try:
        bk = json.loads(BOOK_V0108.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return next((r for r in bk.get("engines", []) if r.get("id") == "009"), None)


def load_book_v0108(path: Path = PRIOR.BOOK_V0106) -> dict:
    """照 v0107 載冊(冊 v0106 的列);只把 009 換成冊 v0108 那一列(檔不在就照舊,不假造)。"""
    bk = _LOAD_V0107(path)
    row = _row009_v0108()
    if row and (HERE / row.get("file", "")).is_file():
        bk["engines"] = [dict(row) if r.get("id") == "009" else r for r in bk["engines"]]
        bk["book_v0108_009"] = row["file"]
    return bk


def _install_v0108() -> None:
    V0101.load_book_v0101, BASE.load_book = load_book_v0108, load_book_v0108
    V0105.PRIOR.load_book_v0104 = V0105.load_book_v0105 = PRIOR.PRIOR.load_book_v0106 = load_book_v0108
    PRIOR.load_book_v0107 = load_book_v0108


def _restore_v0107() -> None:
    PRIOR._install_v0107()
    PRIOR.load_book_v0107 = _LOAD_V0107


_install_v0108()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest(deep=False)
    if args == ["--selftest", "--deep"]:
        return selftest(deep=True)
    return PRIOR.main(args)


def selftest(deep: bool = False) -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    rc0 = None
    if deep:
        _restore_v0107()
        try:
            rc0 = PRIOR.selftest()
        finally:
            _install_v0108()
    print(f"=== {TAG} · 薄尾自測(冊 v0108:MDL009 → v0103)===")
    if deep:
        chk("① v0107 自測過(live curl_cffi 改道 · 冊 v0106 · 列上限)", rc0 == 0, f"rc {rc0}")
    b7 = json.loads((HERE / "VDF_FetchSystem_SSOT_v0107.json").read_text(encoding="utf-8"))
    b8 = json.loads(BOOK_V0108.read_text(encoding="utf-8"))
    e7 = {r["id"]: r for r in b7["engines"]}
    e8 = {r["id"]: r for r in b8["engines"]}
    diff = [k for k in e8 if e8[k] != e7.get(k)]
    chk("② 冊 v0108:只有 009 改指 v0103(檔在)· 其餘 36 列與 v0107 一字不差 · 輸出路徑 / 參數不變",
        diff == ["009"] and e8["009"]["file"] == MDL009_FILE_V0108 and (HERE / MDL009_FILE_V0108).is_file()
        and len(e8) == len(e7) and e8["009"]["outputs"] == e7["009"]["outputs"] and e8["009"]["run_args"] == e7["009"]["run_args"], diff)
    bk = load_book_v0108()
    prev = _LOAD_V0107(PRIOR.BOOK_V0106)
    E, P = {r["id"]: r for r in bk["engines"]}, {r["id"]: r for r in prev["engines"]}
    chk("③ 本系統載冊:009 → v0103 · 其餘列 = v0107 行為(冊 v0106 的列,不把 014 拉進 fetch)",
        E["009"]["file"] == MDL009_FILE_V0108 and set(E) == set(P) and all(E[k] == P[k] for k in E if k != "009")
        and "014" not in E, (E["009"]["file"], len(E)))
    chk("④ 換裝:V0101 / BASE / V0105 / v0106 / v0107 載冊全指本版", V0101.load_book_v0101 is load_book_v0108
        and BASE.load_book is load_book_v0108 and V0105.load_book_v0105 is load_book_v0108 and PRIOR.load_book_v0107 is load_book_v0108)
    keep = globals()["BOOK_V0108"]
    globals()["BOOK_V0108"] = HERE / "__missing_book_v0108__.json"
    try:
        miss = load_book_v0108()
    finally:
        globals()["BOOK_V0108"] = keep
    chk("⑤ 冊 v0108 不在 → 照 v0107(不假造)", {r["id"]: r for r in miss["engines"]}["009"]["file"] == P["009"]["file"])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋(模組層 VIA_NET_TOOL_PATH + def _via_net)在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text
        and "def _via_net" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑦ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    tail = "" if deep else " · 前版鏈自測另跑(--selftest --deep)"
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}{tail}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
