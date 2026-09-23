# ---------------------------------------------------------------------
# VIA_DefTestAudit_v0100
#
# pytest collects functions named test_*. A generation defect prefixed
# many functions in this tree with "def_", so "def def_test_x()" is a
# test that can never be collected: pytest reports "no tests ran" and
# the run exits looking clean. That is a false green, and it is why the
# v035 backtest engine shipped with zero executed coverage.
#
# This tool finds every one of them, works out which are actually
# collectable once renamed, and writes a repair plan. Nothing is edited
# unless --apply is passed, and every edit keeps a .bak sibling.
# ---------------------------------------------------------------------

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

import argparse
import ast
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

TOOL = "VIA_DefTestAudit"
VERSION = "v0101"

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv",
             # v0101: snapshot/copy/vendor trees are not live code; counting them inflated 5 -> 39
             "rollback", "vendor", "SCOPE_COPY", "VIA_RetiredEngines", "site-packages", "_bytecode_originals"}
DEF_TEST = re.compile(r"\bdef_test_[A-Za-z0-9_]+\b")


def scan_file(path: Path) -> dict:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"path": str(path), "error": str(exc), "targets": []}
    if "def_test_" not in src:
        return None
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        return {"path": str(path), "error": "SyntaxError line {0}".format(exc.lineno),
                "targets": [], "parse_ok": False}

    module_level = set()
    nested = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("def_test_"):
            module_level.add(node.name)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("def_test_"):
            if node.name not in module_level:
                nested.add(node.name)

    names = sorted(set(DEF_TEST.findall(src)))
    targets = []
    for n in names:
        new = n[4:]  # strip the leading "def_"
        if n in module_level:
            verdict = "COLLECTABLE_AFTER_RENAME"
        elif n in nested:
            verdict = "NESTED_STILL_UNCOLLECTABLE"
        else:
            verdict = "REFERENCE_ONLY"
        collides = re.search(r"\bdef\s+" + re.escape(new) + r"\b", src) is not None
        targets.append({
            "old": n, "new": new, "verdict": verdict,
            "occurrences": len(re.findall(r"\b" + re.escape(n) + r"\b", src)),
            "name_collision": collides,
        })
    return {
        "path": str(path), "error": "", "parse_ok": True,
        "module_level": sorted(module_level), "nested": sorted(nested),
        "targets": targets,
    }


def repair_text(src: str, targets) -> tuple:
    changed = 0
    for t in targets:
        if t["name_collision"]:
            continue
        pattern = re.compile(r"\b" + re.escape(t["old"]) + r"\b")
        src, n = pattern.subn(t["new"], src)
        changed += n
    return src, changed


def selftest() -> int:
    """批710(任務 #72):6 條真 import 邊卻一站都沒有。煙測只判得出「載得進來」。"""
    import tempfile
    ran, fails = [], []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" (%s)" % note) if note else ""))

    def mk(td, body):
        f = Path(td) / "x.py"
        f.write_text(body, encoding="utf-8")
        return f

    print("=== def_test_ 稽核 v0102 · 自測(沙盒 · 零網路)===")
    with tempfile.TemporaryDirectory() as td:
        # ① 沒有 def_test_ → 現況回 None(宣告卻是 -> dict)
        r_none = scan_file(mk(td, "def foo():\n    return 1\n"))
        chk("① **現況裁定:檔裡沒有 `def_test_` 時回 `None`,而簽章寫的是 `-> dict`。**"
            "呼叫端一律要先擋 None 再取值。本檢釘住現況(不改行為,改了會動到所有呼叫端),"
            "哪天有人改成回空 dict,這條會亮 —— 那就是有意識的改動,不是意外",
            r_none is None, "(無 def_test_ → %r)" % (r_none,))

        # ② 模組層 vs ③ 巢狀,**負控**互為對照
        r = scan_file(mk(td, "def def_test_a():\n    pass\n\n\ndef outer():\n"
                            "    def def_test_b():\n        pass\n    return def_test_b\n"))
        verd = {t["old"]: t["verdict"] for t in r["targets"]}
        chk("② 模組層的 `def_test_a` 判 **COLLECTABLE_AFTER_RENAME**(改名就收得到);"
            "③ 包在函式裡的 `def_test_b` 判 **NESTED_STILL_UNCOLLECTABLE**(改名也收不到,pytest 不進函式內層)。"
            "**負控**=兩者必須判成不同態:全判同一態的分類器也會讓「有分類」看起來成立",
            verd.get("def_test_a") == "COLLECTABLE_AFTER_RENAME"
            and verd.get("def_test_b") == "NESTED_STILL_UNCOLLECTABLE",
            "(%s)" % verd)

        # ④ 撞名偵測 + repair 正控
        r_col = scan_file(mk(td, "def test_a():\n    pass\n\n\ndef def_test_a():\n    pass\n"))
        col = {t["old"]: t["name_collision"] for t in r_col["targets"]}
        src = "def def_test_a():\n    return def_test_a\n"
        fixed, n_fix = repair_text(src, [{"name_collision": False, "old": "def_test_a", "new": "test_a"}])
        skipped, n_skip = repair_text(src, [{"name_collision": True, "old": "def_test_a", "new": "test_a"}])
        chk("④ 檔裡已經有 `def test_a` 時,`def_test_a` 要標 **name_collision**,而修復必須**跳過**"
            "(硬改會造出兩個同名函式,後面那個把前面那個蓋掉 —— 那比不改更糟)。"
            "**正控**:沒撞名時要真的改得動,而且連內文引用一起改",
            col.get("def_test_a") is True and n_fix == 2 and "def test_a" in fixed and n_skip == 0
            and skipped == src,
            "(撞名旗標 %s · 不撞名改 %d 處 · 撞名改 %d 處)" % (col.get("def_test_a"), n_fix, n_skip))

        # ⑤ 語法壞檔誠實報,不炸
        r_bad = scan_file(mk(td, "def def_test_a(:\n    pass\n"))
        chk("⑤ 語法壞掉的檔要**誠實報 parse_ok=False 並說第幾行**,不可以整支炸掉"
            "(這支是全樹掃描器,一個壞檔炸掉等於整棵樹沒掃)",
            isinstance(r_bad, dict) and r_bad.get("parse_ok") is False and "SyntaxError" in r_bad.get("error", ""),
            "(%s)" % (r_bad.get("error") if isinstance(r_bad, dict) else r_bad))

    print("  [計] %d 檢 OK %d · FAIL %d" % (len(ran), len(ran) - len(fails), len(fails)))
    return 1 if fails else 0


def main(argv=None) -> int:
    _a = sys.argv[1:] if argv is None else list(argv)
    if "--selftest" in _a or "--self-test" in _a:
        return selftest()
    ap = argparse.ArgumentParser(description="audit and repair def_test_ naming defect")
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--go-token", default="")
    args = ap.parse_args(argv)

    root = Path(args.root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    apply_mode = args.apply and args.go_token == "GO_v1"

    findings = []
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            scanned += 1
            if scanned % 2000 == 0:
                sys.stderr.write("SCAN|{0} files\n".format(scanned))
                sys.stderr.flush()
            res = scan_file(Path(dirpath) / fn)
            if res:
                findings.append(res)

    collectable = []
    nested_only = []
    for f in findings:
        if any(t["verdict"] == "COLLECTABLE_AFTER_RENAME" for t in f["targets"]):
            collectable.append(f)
        elif any(t["verdict"] == "NESTED_STILL_UNCOLLECTABLE" for t in f["targets"]):
            nested_only.append(f)

    repaired = []
    if apply_mode:
        stage = out / "_repaired"
        stage.mkdir(parents=True, exist_ok=True)
        for f in collectable:
            p = Path(f["path"])
            src = p.read_text(encoding="utf-8", errors="replace")
            new_src, n = repair_text(src, f["targets"])
            if n == 0:
                continue
            backup = p.with_suffix(p.suffix + ".predeftest.bak")
            if not backup.exists():
                shutil.copy2(p, backup)
            p.write_text(new_src, encoding="utf-8", newline="\n")
            repaired.append({"path": str(p), "replacements": n, "backup": str(backup)})

    total_names = sorted({t["old"] for f in findings for t in f["targets"]})
    payload = {
        "tool": TOOL, "version": VERSION,
        "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root), "python_files_scanned": scanned,
        "files_with_defect": len(findings),
        "files_collectable_after_rename": len(collectable),
        "files_nested_only": len(nested_only),
        "distinct_names": len(total_names),
        "mode": "APPLIED" if apply_mode else "DRY_RUN",
        "repaired": repaired,
        "findings": findings,
    }
    plan = out / "deftest_plan.json"
    plan.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8", newline="\n")
    sys.stderr.write("DONE|files={0} collectable={1} nested={2} mode={3}\n".format(
        len(findings), len(collectable), len(nested_only), payload["mode"]))
    print(json.dumps({k: v for k, v in payload.items() if k != "findings"},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
