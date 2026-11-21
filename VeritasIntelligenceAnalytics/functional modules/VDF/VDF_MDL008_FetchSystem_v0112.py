#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0112 — 薄尾:--home 先轉絕對路徑(相對路徑在子行程換工作目錄後會巢狀寫到錯的地方)

操作員 2026-11-21:「輸出驗證」。容器實錄(AI 自己下的指令):run e232 e066 --apply --mode live --home VIA_Reports/vdf_fetch/dict
→ 子行程工作目錄 = 資料家上一層 → 相對資料家又被接一次 → 寫進 VIA_Reports/vdf_fetch/VIA_Reports/vdf_fetch/dict/…(新建的空庫),
真的資料家一列沒動、也沒有任何警告;e232 從 2023 起重抓、e066 建了一個沒人讀的新庫。已清掉錯位的目錄並用絕對路徑重跑。
同一類問題 2026-11-20 在兩個啟動器出過(相對 --source → 子行程找不到),當時啟動器加了 abs_paths;擷取系統自己的 run 沒有。
本版只改一件事:main 收到 --home <夾> 先 resolve 成絕對路徑再交 v0111(其餘參數 · 行為一字不動)。不代設同意閘;不碰 TA-Lib。
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


import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0112(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0112(p) < _vnum_v0112(__file__)), key=_vnum_v0112)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def abs_home_v0112(args: list) -> list:
    """--home <夾> / --home=<夾> → 絕對路徑;其餘照原樣。"""
    out, i = [], 0
    while i < len(args):
        a = args[i]
        if a == "--home" and i + 1 < len(args):
            out += [a, str(Path(args[i + 1]).expanduser().resolve())]
            i += 2
            continue
        if a.startswith("--home="):
            out.append("--home=" + str(Path(a.split("=", 1)[1]).expanduser().resolve()))
        else:
            out.append(a)
        i += 1
    return out


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest(deep=False)
    if args == ["--selftest", "--deep"]:
        return selftest(deep=True)
    return PRIOR.main(abs_home_v0112(args))


def selftest(deep: bool = False) -> int:
    import os
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = PRIOR.selftest(deep=deep)
    print(f"=== {TAG} · 薄尾自測(--home 先轉絕對路徑)===")
    chk("⓪ 前版 v0111 自測過" + ("(含前版鏈)" if deep else ""), rc0 == 0, f"rc {rc0}")
    with tempfile.TemporaryDirectory(prefix="mdl008_v0112_") as td:
        keep = os.getcwd()
        os.chdir(td)
        try:
            a = abs_home_v0112(["run", "e232", "--apply", "--home", "VIA_Reports/vdf_fetch/dict", "--mode", "live"])
            b = abs_home_v0112(["run", "--home=rel/dict"])
            c = abs_home_v0112(["plan", "009"])
        finally:
            os.chdir(keep)
    chk("① 相對 --home → 絕對(照本行程工作目錄解)· 其餘參數照順序不動",
        a[:3] == ["run", "e232", "--apply"] and a[3] == "--home" and Path(a[4]).is_absolute() and a[4].endswith("VIA_Reports/vdf_fetch/dict")
        and a[5:] == ["--mode", "live"], a)
    chk("② --home=<相對> 也轉;沒帶 --home 照原樣", b[1].startswith("--home=/") and c == ["plan", "009"], (b, c))
    seen = {}
    real = PRIOR.main
    PRIOR.main = lambda args: seen.setdefault("args", args) and 0
    try:
        main(["run", "e232", "--home", "x/dict"])
    finally:
        PRIOR.main = real
    chk("③ main 交給前版的是絕對路徑", Path(seen.get("args", ["", "", "", "x"])[3]).is_absolute(), seen)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("④ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑤ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
