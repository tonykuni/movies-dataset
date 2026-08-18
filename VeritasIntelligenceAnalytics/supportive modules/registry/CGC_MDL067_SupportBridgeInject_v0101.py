#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_support_bridge_inject_v0101 — 支援模組接橋注入器 v2(錨塊升級版)
====================================================================
v0100→v0101(2026-08-12 令:每個引擎導入所有輔助性工具/加速器/網路工具/
自動編號;導入一律透過輔助性工具=bridge-first):
  ① 錨塊 v2:_via_load() 統一導入閘——先過 VRN_SupportBridge(load/get/
     require 任一介面),橋缺席退直導,再缺席落 None(graceful 全退化)
  ② 新增四導入:VIA_SuperAccel_Module(加速器,候上傳)、VIA_NetSupport
     (網路支援模組)、VIA_RegistryCore_v1(自動編號核心,候上傳)+
     自動編號嘗試(auto_register/ensure_code/register_module 任一,全護欄)
  ③ 升級模式:檔內已有 v1 錨塊→標記間整段替換為 v2;已是 v2→SKIP 冪等
  ④ 承 v0100:AST 精算注入點;注入後語法先驗壞不落盤;不 eager 導入
     Runtime_Bridge/EnvManager 重件(>180s 實證)
用法:py via_support_bridge_inject_v0101.py <f1.py> [f2.py ...] [--dry-run]
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ANCHOR_START = "# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] ====="
ANCHOR_END = "# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] ====="
V2_MARK = "接橋補丁 v2"
BLOCK = ANCHOR_START + """
# 接橋補丁 v2(2026-08-12 令:引擎統一導入 輔助/加速器/網路/自動編號;
#  導入一律 bridge-first 過橋;graceful 全退化 — 缺席零影響;
#  不 eager 導入 Runtime_Bridge/EnvManager 重件)
import sys as _via_sys
from pathlib import Path as _via_Path

def _via_bootstrap_support_paths():
    try:
        _self = _via_Path(__file__).resolve()
        roots = [_self.parent]
        p = _self.parent
        for _ in range(4):
            p = p.parent
            roots.append(p)
        for root in roots:
            for name in ("supportive_module", "supportive modules"):
                sup = root / name
                if sup.is_dir():
                    s = str(sup)
                    if s not in _via_sys.path:
                        _via_sys.path.insert(0, s)
    except Exception:
        pass

_via_bootstrap_support_paths()
try:
    from VRN_SupportBridge import BRIDGE as _VIA_BRIDGE
    _VIA_HAS_BRIDGE = True
except Exception:
    _VIA_BRIDGE = None
    _VIA_HAS_BRIDGE = False

def _via_load(_name):
    # 統一導入閘:先過橋(輔助性工具),橋缺退直導,再缺落 None(graceful)
    try:
        if _VIA_BRIDGE is not None:
            for _fn in ("load", "get", "require"):
                _f = getattr(_VIA_BRIDGE, _fn, None)
                if callable(_f):
                    try:
                        _m = _f(_name)
                    except Exception:
                        _m = None
                    if _m is not None:
                        return _m
    except Exception:
        pass
    try:
        return __import__(_name)
    except Exception:
        return None

_VIA_SSOT = _via_load("VIA_SSOT_Unified")
_VIA_AEGIS = _via_load("VeritasAegisNexus")
_VIA_CELERITAS = _via_load("VeritasCeleritas")
_VIA_ACCEL = _via_load("VIA_SuperAccel_Module")   # 加速器(工作站候上傳;graceful)
_VIA_NET = _via_load("VIA_NetSupport")            # 網路支援模組
_VIA_REGCORE = _via_load("VIA_RegistryCore_v1")   # 自動編號核心(工作站候上傳;graceful)
try:
    if _VIA_REGCORE is not None:  # 自動編號:標準介面任一,全護欄不擲例外
        for _fn in ("auto_register", "ensure_code", "register_module"):
            _f = getattr(_VIA_REGCORE, _fn, None)
            if callable(_f):
                _f(__file__)
                break
except Exception:
    pass
""" + ANCHOR_END + "\n"


def insertion_line(text: str) -> int:
    """回傳 0-based 行號:module docstring 與連續 __future__ imports 之後。"""
    tree = ast.parse(text)
    if not tree.body:
        return 0
    line = 0
    idx = 0
    first = tree.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        line = first.end_lineno
        idx = 1
    while idx < len(tree.body):
        stmt = tree.body[idx]
        if isinstance(stmt, ast.ImportFrom) and stmt.module == "__future__":
            line = stmt.end_lineno
            idx += 1
        else:
            break
    if line == 0:
        line = first.lineno - 1
    return line


def inject(path: Path, dry: bool) -> str:
    text = path.read_text(encoding="utf-8")
    if V2_MARK in text:
        return "SKIP(v2 錨塊已在,冪等)"
    if ANCHOR_START in text and ANCHOR_END in text:
        # 升級:v1 錨塊標記間整段替換為 v2
        head, _, rest = text.partition(ANCHOR_START)
        _, _, tail = rest.partition(ANCHOR_END)
        new = head + BLOCK.rstrip("\n") + tail
        verb = "UPGRADED v1→v2"
    else:
        line = insertion_line(text)
        lines = text.splitlines(keepends=True)
        new = "".join(lines[:line]) + "\n" + BLOCK + "\n" + "".join(lines[line:])
        verb = f"INJECTED v2 @line {line + 1}"
    ast.parse(new)  # 語法先驗,壞就不落盤
    if not dry:
        path.write_text(new, encoding="utf-8", newline="\n")
    return verb + ("(dry-run 未落盤)" if dry else "")


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry = "--dry-run" in sys.argv
    if not args:
        print(__doc__)
        return 2
    fails = 0
    print(f"=== 支援接橋注入器 v0101(v2 錨塊)· {len(args)} 檔 · {'DRY-RUN' if dry else 'LIVE'} ===")
    for a in args:
        p = Path(a)
        try:
            r = inject(p, dry)
        except Exception as exc:
            r = f"FAIL {type(exc).__name__}: {exc}"
            fails += 1
        print(f"  [{'OK ' if not r.startswith('FAIL') else 'ERR'}] {p.name}: {r}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
