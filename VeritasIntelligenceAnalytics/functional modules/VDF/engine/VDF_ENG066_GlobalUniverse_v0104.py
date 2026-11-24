#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG066_GlobalUniverse v0104 — 薄尾:宇宙 = 基本冊 + VDF 自有擴充冊(只增不減)。

VDF-REQ050(操作員 2026-11-23「檢查有無沒擷取的」):資金流總覽 Console 用到、VDF 冊上沒有的 22 個 Yahoo 代號
登在 VDF 自己的 functional modules/VDF/VDF_Global_Universe_Ext_v*.json(取尾版)。
基本冊 supportive modules/registry/VIA_Global_Universe_v0100.json 在 VCGC 資料夾,依系統獨立性不改它;
本版只把前版鏈裡 load_roster 換成「基本冊 + 擴充冊尾版」合併(同類別名不覆蓋、代號去重、基本冊在前)。
其餘(雙同意閘 fail-closed · 空庫建表 · anti-join 只補缺 · 每批落盤)全照 v0103。
自測:合併邏輯零網路、不需 duckdb;前版自測需 duckdb,缺則照實標 SKIP(黃),不冒充綠。
用法同前:run [--cats …] [--start …] [--end …] | --list | --selftest
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF_DIR = HERE.parent
_STEM = "VDF_ENG066_GlobalUniverse"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
EXT_GLOB = "VDF_Global_Universe_Ext_v*.json"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner_of(name: str):
    """沿前版鏈找真正定義 name 的模組(load_roster / pick_symbols 在 v0102 本體)。"""
    m = PRIOR
    for _ in range(8):
        if name in vars(m):
            return m
        nxt = vars(m).get("PRIOR")
        if nxt is None:
            break
        m = nxt
    return None


_BASE_MOD = _owner_of("load_roster")
_BASE_LOAD = _BASE_MOD.load_roster


def ext_path(folder: Path = VDF_DIR):
    hits = sorted(folder.glob(EXT_GLOB), key=_vnum)
    return hits[-1] if hits else None


def merge_roster(base: dict, ext: dict | None) -> dict:
    """基本冊在前;擴充類別附加於後;已在基本冊的代號從擴充類別剔除(去重,不覆蓋)。"""
    out = json.loads(json.dumps(base))
    if not ext:
        return out
    have = {s for c in out.get("categories", []) for s in c.get("symbols", [])}
    names = {c.get("cat") for c in out.get("categories", [])}
    for c in ext.get("categories", []):
        syms = [s for s in c.get("symbols", []) if s not in have]
        have.update(syms)
        cat = c.get("cat")
        if cat in names:
            cat = f"{cat}_ext"
        out["categories"].append({**c, "cat": cat, "symbols": syms, "source": "VDF ext"})
    return out


def load_roster() -> dict:
    p = ext_path()
    ext = json.loads(p.read_text(encoding="utf-8")) if p else None
    return merge_roster(_BASE_LOAD(), ext)


_BASE_MOD.load_roster = load_roster          # v0102 的 pick_symbols 以模組全域叫 load_roster


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


def selftest() -> int:
    ok = fail = skip = 0

    def chk(name, cond, note=""):
        nonlocal ok, fail
        ok += bool(cond)
        fail += not cond
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    base = _BASE_LOAD()
    p = ext_path()
    chk("① 擴充冊尾版在位", p is not None, f"({p.name if p else '缺'})")
    ext = json.loads(p.read_text(encoding="utf-8")) if p else {"categories": []}
    merged = load_roster()
    bsyms = [s for c in base["categories"] for s in c["symbols"]]
    msyms = [s for c in merged["categories"] for s in c["symbols"]]
    esyms = [s for c in ext["categories"] for s in c["symbols"]]
    new = [s for s in dict.fromkeys(esyms) if s not in set(bsyms)]
    chk("② 基本冊代號全保留且在前", msyms[:len(bsyms)] == bsyms, f"(基本 {len(bsyms)})")
    base_dup = len(bsyms) - len(set(bsyms))
    chk("③ 擴充冊不帶入新重複(基本冊既有重複照列)", len(msyms) - len(set(msyms)) == base_dup,
        f"(合併 {len(msyms)} · 基本冊既有重複 {base_dup})")
    chk("④ 新增數 = 擴充冊扣除已在基本冊者", len(msyms) - len(bsyms) == len(new), f"(+{len(new)})")
    syms, _pend = _BASE_MOD.pick_symbols(None)
    chk("⑤ pick_symbols 走合併冊(前版鏈實際生效)", set(new) <= set(syms) and len(syms) == len(set(bsyms)) + len(new),
        f"(可抓 {len(syms)} = 基本去重 {len(set(bsyms))} + 新增 {len(new)})")
    t = {"categories": [{"cat": "fx", "zh": "x", "symbols": ["A", "B"]}]}
    e = {"categories": [{"cat": "fx", "zh": "y", "symbols": ["B", "C"]}]}
    m = merge_roster(t, e)
    chk("⑥ 同名類別不覆蓋(改名 _ext)、重複代號剔除", [c["cat"] for c in m["categories"]] == ["fx", "fx_ext"]
        and m["categories"][1]["symbols"] == ["C"])
    chk("⑦ 基本冊檔未被改寫", "Ext" not in Path(_BASE_MOD.ROSTER).name)
    try:
        import duckdb  # noqa: F401
        print("  [..] 前版自測(v0103 鏈)")
        rc = PRIOR.selftest()
        chk("⑧ 前版自測", rc == 0, f"(rc {rc})")
    except ModuleNotFoundError:
        skip += 1
        print("  [SKIP] ⑧ 前版自測需 duckdb(本機缺件)→ 黃,工作站實跑")
    print(f"  [計] {TAG} 自測 OK {ok} · FAIL {fail} · SKIP {skip}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
