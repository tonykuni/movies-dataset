#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_support_bridge_inject_v0100 — 支援模組接橋注入器(錨點區塊;冪等)
======================================================================
稽核令後續:把 [VIA:ANCHOR:SUPPORT:BOOTSTRAP] 標準錨點區塊(MDL011 樣板之
VDF 變體)注入指定引擎。原則:
  ① graceful 全退化 — 橋/核心模組缺席時全部落 None,引擎行為零改變
  ② 冪等 — 檔內已有錨點即跳過(誠實記 SKIP)
  ③ AST 精算注入點 — module docstring 與 __future__ imports 之後
     (在其之前插入會 SyntaxError;首輪設計即防)
  ④ 只注入現役補丁版;原件保存區(engine/)零觸碰
  ⑤ 不 eager 導入 VIA_Runtime_Bridge/VIA_EnvManager(via-datahub 實證
     其 bootstrap 工作站 >180s — 只導 SSOT/Aegis/Celeritas 輕件)
用法:py via_support_bridge_inject_v0100.py <file1.py> [file2.py ...] [--dry-run]
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ANCHOR_START = "# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] ====="
BLOCK = ANCHOR_START + """
# 接橋補丁(2026-08-13 稽核令 TOOL-009 後續:功能引擎統一導入支援模組;
#  graceful 全退化 — 橋/核心缺席零影響;不 eager 導入 Runtime_Bridge/EnvManager 重件)
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
try:
    import VIA_SSOT_Unified as _VIA_SSOT
except Exception:
    _VIA_SSOT = None
try:
    import VeritasAegisNexus as _VIA_AEGIS
except Exception:
    _VIA_AEGIS = None
try:
    import VeritasCeleritas as _VIA_CELERITAS
except Exception:
    _VIA_CELERITAS = None
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====
"""


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
    if "[VIA:ANCHOR:SUPPORT:BOOTSTRAP" in text:
        return "SKIP(錨點已在檔,冪等)"
    line = insertion_line(text)
    lines = text.splitlines(keepends=True)
    new = "".join(lines[:line]) + "\n" + BLOCK + "\n" + "".join(lines[line:])
    ast.parse(new)  # 注入後語法先驗,壞就不落盤
    if not dry:
        path.write_text(new, encoding="utf-8", newline="\n")
    return f"INJECTED @line {line + 1}" + ("(dry-run 未落盤)" if dry else "")


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry = "--dry-run" in sys.argv
    if not args:
        print(__doc__)
        return 2
    fails = 0
    print(f"=== 支援接橋注入器 v0100 · {len(args)} 檔 · {'DRY-RUN' if dry else 'LIVE'} ===")
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
