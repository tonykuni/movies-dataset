#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG229_CNNFearGreedHistory v0102 — 薄尾:補齊網路工具橋(v0101 的橋只有半段:有工具路徑、少 `_via_net` 載入函式)。

實錄:CGC_MDL230 覆蓋量尺「③ VDF 全件 · 網路工具橋」標記 136/136、語法樹實讀 135/136,兩法不一致的那一支就是 v0101
(操作員 2026-11-14 令「加速器 網路工具 100% 覆蓋率」)。v0101 一字不動;本支帶完整的兩座橋,其餘照前版。

  bridge            唯讀:兩座橋是不是模組層的實碼(只剖析自己這支;不載入網路工具、不外呼)
  其餘動詞(status / run / dedupe / --selftest 鏈)照前版。
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

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG229_CNNFearGreedHistory"
ENGINE_TAG = _STEM + "_v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _prior_path() -> Path:
    """同族版號小於自己的最新一支(尾版律;不釘版號)。"""
    me = _vnum(__file__)
    olds = sorted((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < me), key=_vnum)
    if not olds:
        raise FileNotFoundError(f"{_STEM}:版號小於 v{me:04d} 的前版不在")
    return olds[-1]


def _load(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR = _load(_prior_path(), "_vdf_eng229_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    """前版公開面照轉(TAILAPI:尾版不少名字)。"""
    return getattr(PRIOR, name)


def bridge_read(text: str) -> dict:
    """一支 .py 的兩座橋是不是模組層實碼(與 CGC_MDL230 量尺同一讀法:加速器 = 匯入;網路工具 = 路徑賦值 + `_via_net` 函式)。"""
    tree = ast.parse(text)
    accel = net_assign = net_fn = False
    for node in tree.body:
        for sub in [node] + (list(node.body) if isinstance(node, ast.Try) else []):
            if isinstance(sub, ast.Import) and any(a.name == "VIA_SuperAccel_Module" for a in sub.names):
                accel = True
            if isinstance(sub, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "VIA_NET_TOOL_PATH" for t in sub.targets):
                net_assign = True
        if isinstance(node, ast.FunctionDef) and node.name == "_via_net":
            net_fn = True
    return {"accel": accel, "net": net_assign and net_fn, "net_path_assign": net_assign, "net_loader_fn": net_fn}


def bridge_state() -> dict:
    r = bridge_read(Path(__file__).read_text(encoding="utf-8"))
    r["engine"] = ENGINE_TAG
    r["net_tool"] = Path(VIA_NET_TOOL_PATH).name if VIA_NET_TOOL_PATH else None
    r["state"] = "OK" if r["accel"] and r["net"] else "GAP"
    return r


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["bridge"]:
        r = bridge_state()
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["state"] == "OK" else 1
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


# ---------------------------------------------------------------- 自測(零外呼;不載入網路工具)
def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    me = bridge_state()
    chk("① 本支兩座橋都是模組層實碼(加速器匯入 · 網路工具路徑 + 載入函式)", me["state"] == "OK", json.dumps(me, ensure_ascii=False))
    old = bridge_read(_prior_path().read_text(encoding="utf-8"))
    chk("② 讀法分得出半段橋:前版有路徑、沒有載入函式 → 不算覆蓋", old["net_path_assign"] and not old["net_loader_fn"] and not old["net"]
        if _vnum(_prior_path()) == 101 else True, _prior_path().name)
    chk("③ `_via_net` 在本支可呼叫;工具路徑指到 via_net_unified 尾版或照實 None(不載入)", callable(globals().get("_via_net"))
        and (VIA_NET_TOOL_PATH is None or re.search(r"via_net_unified_v\d+\.py$", str(VIA_NET_TOOL_PATH))), str(me["net_tool"]))
    mod = sys.modules[__name__]
    names = ("dedupe", "dup_report", "TABLE", "KEYS", "DB_GL", "OUT")
    chk("④ 前版公開面照轉(尾版不少名字)", all(getattr(mod, n, None) is getattr(PRIOR, n) for n in names), " ".join(names))
    print("  -- 前版自測 --")
    prior_ok = PRIOR.selftest() == 0
    chk("⑤ 前版自測鏈", prior_ok, _prior_path().name)
    ok = all(results)
    print(f"  [計] {ENGINE_TAG} 自測 {sum(results)}/{len(results)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
