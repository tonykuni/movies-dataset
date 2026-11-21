#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_MDL022_SafeParallelLaunch v0107 — 薄尾:補標準網路橋(SDD X-ACCEL「缺標準橋:v0106 網路橋」);行為全部轉給 v0106。

操作員 2026-11-21 令:「三個都是獨立系統 授權給你做到 VDF 輸出資料且快」「輸出驗證」。
工作流冊 VDF v0116 第一次把啟動器列成步驟的引擎(VDF-WKF028 / 031)→ SDD X-ACCEL 照律點名 v0106 只有加速器橋、缺網路橋
(CLAUDE.md 2026-11-18:加速器覆蓋全部引擎 · 網路工具覆蓋 VDF 引擎;只有標記不算,要語法樹裡真的有)。
v0106 已併進 main、已鎖成功 → 不改原檔,出本版:只加標準網路橋(graceful,載不到 = None,零行為變更);
main / 自測 / 每個公開名稱全部轉給 v0106(降壓等靜 · 固定 3 道 · 不監控 · --via-db · fixnames 一字不動)。
不代設同意閘;不碰 TA-Lib。用法同前版:run … · check · --selftest
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
except Exception:  # noqa: BLE001
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。啟動器自己不連網,連網的是各擷取引擎。"""
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL022_SafeParallelLaunch"
VERSION = "v0107"
TAG = f"{STEM} {VERSION}"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("vdf_launch_prior_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    import ast
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(補標準網路橋;行為全部轉給前版)===")
    chk("⓪ 前版 %s 自測過(降壓等靜 · 固定 3 道 · 不監控 · --via-db · fixnames)" % PRIOR_PATH.stem, rc0 == 0, f"rc {rc0}")
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assigns = {t.id for n in tree.body if isinstance(n, (ast.Assign, ast.Try)) for s in ([n] if isinstance(n, ast.Assign) else n.body)
               if isinstance(s, ast.Assign) for t in s.targets if isinstance(t, ast.Name)}
    chk("① 語法樹裡真的有兩座標準橋:加速器(VIA_ACCEL)· 網路(VIA_NET_TOOL_PATH · _via_net)",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src and "_via_net" in names
        and {"VIA_NET_TOOL_PATH"} <= assigns, sorted(names))
    net = _via_net()
    chk("② 網路橋載得到工具或誠實 None(不丟例外;啟動器本身不出網)", net is None or hasattr(net, "__name__"))
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("③ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    body = src.split("def selftest", 1)[0]
    chk("④ 不碰 TA-Lib;不寫同意閘", not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
