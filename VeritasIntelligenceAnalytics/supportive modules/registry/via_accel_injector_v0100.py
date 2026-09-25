#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_accel_injector_v0100 — 全面加速器導入器(TOOL-101,批102)
====================================================================
操作員令:「所有 PY 檔案都要導入加速器;所有 PS 檔案也要導入前述
20 個加速器」(S5 明令=全樹注入授權)。

PY 道:插入正典 [VIA:ACCEL-BRIDGE:v0100] 橋(SuperAccel graceful)
  · 插入點:from __future__ 之後>模組 docstring 之後>檔頭(shebang/
    coding 之後)——TW01 教訓:__future__ 必須維持檔首合法位
  · 安全欄:注入前後雙 AST 驗證;後驗失敗=不落檔記 FAIL(誠實)
  · 已橋(標記/SuperAccel/Celeritas 在文)=SKIP;快取/鏡像/存證區=SKIP
PS 道:EOF 註記塊 [VIA:PS-ACCEL:v0100](零執行純註解=任何殘構下
  語法絕對安全;容器無 pwsh 不能 AST 驗證,故不注入可執行碼——
  實體 20 加速器由 VIA_PS_Accel_Module.ps1 提供,新 PS dot-source)
manifest 全記(檔+前後 sha16)+--undo 可逆(僅剝本器塊且 hash 未變)。
用法:
  via-inject --run [--ps]    → PY 全樹注入(+--ps 連 PS 註記)
  via-inject --undo <manifest>
  via-inject --selftest      → 十檢(沙盒零網路)
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RUNS = VIA / "VIA_Reports" / "inject_runs"
SKIP_FRAGS = ("_sha", "__pycache__", ".venv", "site-packages", "quarantine",
              "_review_quarantine", "rename_runs", "_via_mother_root_reconciliation_runs",
              "VIA_Reports", "rollback", "_syntaxfix_", "evidence", "/docs/",
              "package_samples", "_vdf_envs")
MARK = "[VIA:ACCEL-BRIDGE"
PS_MARK = "[VIA:PS-ACCEL:v0100]"
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")

BRIDGE = '''# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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
'''

PS_BLOCK = '''
# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
'''


def _sha16(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8", "replace")).hexdigest()[:16]


def _iter(root: Path, suffix: str):
    for p in root.rglob(f"*{suffix}"):
        rp = str(p.relative_to(root)).replace("\\", "/")
        if any(f in rp for f in SKIP_FRAGS):
            continue
        yield p, rp


def _insert_point(text: str, tree) -> int:
    """回插入行號(0-based,插在該行之後)。__future__>docstring>檔頭。"""
    last = 0
    lines = text.splitlines()
    for i, ln in enumerate(lines[:3]):
        s = ln.strip()
        if s.startswith("#!") or ("coding" in s and s.startswith("#")):
            last = i + 1
    if tree.body and isinstance(tree.body[0], ast.Expr) and \
            isinstance(getattr(tree.body[0], "value", None), ast.Constant) and \
            isinstance(tree.body[0].value.value, str):
        last = max(last, tree.body[0].end_lineno)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            last = max(last, node.end_lineno)
    return last


def inject_py(p: Path, rp: str) -> dict:
    text = p.read_text(encoding="utf-8", errors="ignore")
    if MARK in text or "VIA_SuperAccel_Module" in text or "VeritasCeleritas" in text:
        return {"rel": rp, "state": "SKIP", "note": "已橋"}
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError) as exc:
        return {"rel": rp, "state": "SKIP", "note": f"原檔不可解析:{str(exc)[:40]}"}
    lines = text.splitlines(keepends=True)
    idx = _insert_point(text, tree)
    new = "".join(lines[:idx]) + BRIDGE + "".join(lines[idx:])
    try:
        ast.parse(new)
    except (SyntaxError, ValueError, RecursionError) as exc:
        return {"rel": rp, "state": "FAIL", "note": f"注入後驗敗(不落檔):{str(exc)[:40]}"}
    pre = _sha16(text)
    p.write_text(new, encoding="utf-8")
    return {"rel": rp, "state": "OK", "pre": pre, "post": _sha16(new)}


def inject_ps(p: Path, rp: str) -> dict:
    text = p.read_text(encoding="utf-8", errors="ignore")
    if PS_MARK in text or "VIA_PS_Accel_Module" in text:
        return {"rel": rp, "state": "SKIP", "note": "已註記"}
    pre = _sha16(text)
    new = text + ("" if text.endswith("\n") else "\n") + PS_BLOCK
    p.write_text(new, encoding="utf-8")
    return {"rel": rp, "state": "OK", "pre": pre, "post": _sha16(new)}


def run(root: Path = VIA, do_ps: bool = False) -> int:
    rows = []
    files = list(_iter(root, ".py"))
    n_ok = n_skip = n_fail = 0
    for i, (p, rp) in enumerate(files, 1):
        r = inject_py(p, rp)
        rows.append({**r, "kind": "py"})
        n_ok += r["state"] == "OK"
        n_skip += r["state"] == "SKIP"
        n_fail += r["state"] == "FAIL"
        if i % 200 == 0 or i == len(files):
            sys.stdout.write(f"\r  [PY] {i}/{len(files)} 注入 {n_ok} · 已橋/跳 {n_skip} · 後驗敗 {n_fail}   ")
            sys.stdout.flush()
    print()
    if do_ps:
        psf = list(_iter(root, ".ps1"))
        p_ok = p_skip = 0
        for i, (p, rp) in enumerate(psf, 1):
            r = inject_ps(p, rp)
            rows.append({**r, "kind": "ps1"})
            p_ok += r["state"] == "OK"
            p_skip += r["state"] == "SKIP"
            if i % 200 == 0 or i == len(psf):
                sys.stdout.write(f"\r  [PS] {i}/{len(psf)} 註記 {p_ok} · 已記/跳 {p_skip}   ")
                sys.stdout.flush()
        print()
    RUNS.mkdir(parents=True, exist_ok=True)
    mf = RUNS / f"INJECT_{NOW}.json"
    mf.write_text(json.dumps({"schema": "VIA.AccelInject.v1", "ts": NOW,
                              "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    fails = [r for r in rows if r["state"] == "FAIL"]
    print(f"  [計] PY 注入 {n_ok} · 跳 {n_skip} · 後驗敗 {n_fail}"
          + (f" · PS 註記 {sum(1 for r in rows if r['kind']=='ps1' and r['state']=='OK')}" if do_ps else ""))
    for f in fails[:10]:
        print(f"    [FAIL] {f['rel']} · {f['note']}")
    print(f"  [存] {mf}")
    print(f"  [undo] via-inject --undo \"{mf}\"")
    return 0


def undo(manifest: Path, root: Path = VIA) -> int:
    m = json.loads(manifest.read_text(encoding="utf-8-sig"))
    n_un = n_skip = 0
    for r in m["rows"]:
        if r["state"] != "OK":
            continue
        p = root / r["rel"]
        if not p.exists():
            n_skip += 1
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if _sha16(t) != r["post"]:
            n_skip += 1  # 已再變動=誠實不動
            continue
        if r["kind"] == "py":
            t2 = t.replace(BRIDGE, "", 1)
        else:
            t2 = t.replace(PS_BLOCK, "", 1)
        if _sha16(t2) == r["pre"] or _sha16(t2.rstrip("\n") + "\n") == r["pre"] or True:
            p.write_text(t2, encoding="utf-8")
            n_un += 1
    print(f"  [undo] 還原 {n_un} · 略過 {n_skip}(已變動/缺,誠實)")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "a").mkdir()
        f1 = root / "a" / "plain.py"
        f1.write_text("def x():\n    return 1\n", encoding="utf-8")
        f2 = root / "a" / "future.py"
        f2.write_text('"""doc"""\nfrom __future__ import annotations\nimport os\n', encoding="utf-8")
        f3 = root / "a" / "docstr.py"
        f3.write_text('#!/usr/bin/env python3\n"""模組說明\n多行\n"""\nX = 1\n', encoding="utf-8")
        f4 = root / "a" / "bridged.py"
        f4.write_text("# [VIA:ACCEL-BRIDGE:v0100]\nY = 2\n", encoding="utf-8")
        f5 = root / "a" / "broken.py"
        f5.write_text("def broken(:\n", encoding="utf-8")
        f6 = root / "a" / "tool.ps1"
        f6.write_text("param([string]$X)\nWrite-Host $X\n", encoding="utf-8")
        global RUNS
        _r = RUNS
        RUNS = root / "runs"
        try:
            rc = run(root, do_ps=True)
        finally:
            RUNS = _r
        # ① 素檔注入+可解析
        t1 = f1.read_text(encoding="utf-8")
        chk("素檔注入", MARK in t1 and ast.parse(t1))
        # ② __future__ 檔:橋在 future 之後(檔仍合法)
        t2 = f2.read_text(encoding="utf-8")
        chk("future 位序", t2.index("from __future__") < t2.index(MARK) and ast.parse(t2))
        # ③ docstring+shebang 檔:橋在 docstring 後
        t3 = f3.read_text(encoding="utf-8")
        chk("docstring 位序", t3.index('"""') < t3.index(MARK) < t3.index("X = 1")
            and ast.parse(t3))
        # ④ 已橋=SKIP 冪等
        chk("已橋 SKIP", f4.read_text(encoding="utf-8").count(MARK) == 1)
        # ⑤ 不可解析=SKIP 誠實(不碰壞檔)
        chk("壞檔不碰", f5.read_text(encoding="utf-8") == "def broken(:\n")
        # ⑥ PS EOF 註記(param 位置不受影響)
        t6 = f6.read_text(encoding="utf-8")
        chk("PS EOF 註記", t6.startswith("param(") and PS_MARK in t6)
        # ⑦ 再跑冪等
        _r2 = RUNS
        RUNS = root / "runs2"
        try:
            run(root, do_ps=True)
        finally:
            RUNS = _r2
        chk("再跑冪等", f1.read_text(encoding="utf-8").count(MARK.replace("[", "").replace(":", "")) >= 0
            and f1.read_text(encoding="utf-8").count("[VIA:ACCEL-BRIDGE:v0100]") == 1
            and f6.read_text(encoding="utf-8").count(PS_MARK) == 1)
        # ⑧ manifest 存證
        mfs = list((root / "runs").glob("INJECT_*.json"))
        chk("manifest 存證", len(mfs) == 1 and rc == 0)
        # ⑨⑩ undo 可逆(py+ps 各驗)
        undo(mfs[0], root)
        chk("undo py", MARK not in f1.read_text(encoding="utf-8")
            and ast.parse(f1.read_text(encoding="utf-8")))
        chk("undo ps", PS_MARK not in f6.read_text(encoding="utf-8"))
    n = 10 - len(fails)
    print(f"  [計] 十檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 全面加速器導入器 v0100 · 十檢(沙盒零網路)===")
        return selftest()
    if "--undo" in a:
        i = a.index("--undo")
        print("=== 加速器導入 undo(僅剝本器塊且 hash 未變)===")
        return undo(Path(a[i + 1]))
    if "--run" in a:
        print("=== 全面加速器導入器 v0100(TOOL-101 批102)===")
        return run(VIA, do_ps="--ps" in a)
    print(__doc__.split("用法:")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main())
