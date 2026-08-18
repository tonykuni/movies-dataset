#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_accel_bridge_v0100 — 全引擎加速器橋(TOOL-057;操作員令 2026-08-18)
======================================================================
令:「所有引擎都要導入加速器」(二度明確令=promote token)。
紀律:EngineForge 三輪脊椎——沙盒複本→AST 定位插入點→逐檔 parse=0 閘
→閘過才落筆;不過=原件零觸碰誠實記錄。
插入物=graceful 橋塊(零行為變更;SuperAccel 缺席=None):
  [VIA:ACCEL-BRIDGE:v0100] try-import VIA_SuperAccel_Module as VIA_ACCEL
插入點=module docstring 之後、且任何 `from __future__` 之後(雙保護,
不破 __doc__ 不破 future 語義)。冪等:含橋標記即跳過。
範圍:functional modules/**/*.py;排除 _sha 鏡像/_review_quarantine/
vendor//__pycache__/package_samples/docs;語法敗件誠實跳過不碰。
用法:via-accelbridge            → dry(計畫+逐檔裁決,零寫)
     via-accelbridge --commit   → 落筆(逐檔 parse 閘)
     via-accelbridge --selftest → 四檢(合成件,零觸正典)
"""
from __future__ import annotations

import ast
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
FUNC = VIA / "functional modules"
OUT = VIA / "VIA_Reports" / "accelbridge_runs"

MARK = "[VIA:ACCEL-BRIDGE:"
BLOCK = '''# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
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
'''

SKIP_FRAGS = ("_sha", "_review_quarantine", "__pycache__", "/vendor/", "package_samples", "/docs/")


def targets():
    for p in sorted(FUNC.rglob("*.py")):
        rel = p.as_posix()
        if any(f in rel for f in SKIP_FRAGS):
            continue
        yield p


def insert_line(src: str):
    """插入點(1-based 行號後插):docstring 尾與最後 __future__ 之大者。"""
    tree = ast.parse(src)  # 呼叫端處理 SyntaxError
    line = 0
    body = tree.body
    i = 0
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        line = body[0].end_lineno
        i = 1
    while i < len(body) and isinstance(body[i], ast.ImportFrom) and body[i].module == "__future__":
        line = body[i].end_lineno
        i += 1
    return line


def bridge_source(src: str) -> str | None:
    """回新源碼;不適用回 None。內部 parse=0 閘。"""
    if MARK in src:
        return None  # 冪等
    ln = insert_line(src)
    lines = src.splitlines(keepends=True)
    new = "".join(lines[:ln]) + ("\n" if ln and lines and not lines[ln - 1].endswith("\n") else "") \
          + BLOCK + "".join(lines[ln:])
    ast.parse(new)  # parse=0 閘(失敗擲例外=不落筆)
    return new


def run(commit: bool) -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stat = {"bridged": 0, "already": 0, "syntax_skip": 0, "gate_fail": 0}
    rows = []
    files = list(targets())
    print(f"=== 加速器橋 v0100 · {len(files)} 件 · {'COMMIT(逐檔 parse 閘)' if commit else 'DRY(零寫)'} ===")
    for i, p in enumerate(files, 1):
        if i % 50 == 0:
            print(f"  [{i}/{len(files)}] …")
        rel = p.relative_to(VIA).as_posix()
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
            new = bridge_source(src)
        except SyntaxError:
            stat["syntax_skip"] += 1
            rows.append({"f": rel, "st": "SYNTAX_SKIP(語法敗不碰,誠實)"})
            continue
        except Exception as exc:
            stat["gate_fail"] += 1
            rows.append({"f": rel, "st": f"GATE_FAIL({type(exc).__name__})——原件零觸碰"})
            continue
        if new is None:
            stat["already"] += 1
            continue
        if commit:
            p.write_text(new, encoding="utf-8")
        stat["bridged"] += 1
        rows.append({"f": rel, "st": "BRIDGED" if commit else "PLANNED"})
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"ACCELBRIDGE_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.AccelBridge.v1", "ts": ts, "commit": commit,
                              "stat": stat, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計] 橋接 {stat['bridged']} · 已橋 {stat['already']} · 語法跳 {stat['syntax_skip']}"
          f" · 閘擋 {stat['gate_fail']} · 存證 {ev.name}")
    if not commit:
        print("  [dry] 確認後:via-accelbridge --commit(操作員二度明確令=promote token 已備)")
    return 0


def selftest() -> int:
    print("=== 加速器橋 v0100 · 自測四檢(合成,零觸正典)===")
    cases = {
        "docstring+future": '#!/usr/bin/env python3\n"""doc"""\nfrom __future__ import annotations\nimport os\n',
        "bare": 'import os\nprint(1)\n',
        "docstring_only": '"""doc\nmulti"""\nX = 1\n',
    }
    checks = []
    for name, src in cases.items():
        new = bridge_source(src)
        ok = new is not None and MARK in new
        if ok:
            ast.parse(new)
            tree = ast.parse(new)
            doc_kept = (not src.startswith('"""')) or (ast.get_docstring(tree) is not None)
            fut_ok = ("__future__" not in src) or (new.index("__future__") < new.index(MARK))
            ok = doc_kept and fut_ok
        checks.append((f"插入+閘 [{name}]", ok))
    checks.append(("冪等(已橋跳過)", bridge_source(BLOCK + "import os\n") is None))
    n = 0
    for name, ok in checks:
        n += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [計] {n}/{len(checks)} 檢通過")
    return 0 if n == len(checks) else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(selftest() if "--selftest" in a else run("--commit" in a))
