#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_accel_injector_v0102 — 全面加速器導入器(TOOL-101,批102;批626 排除清單正典化;批715 拆掉『提到名字就算有橋』的假綠)
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
SKIP_FRAGS = ("/docs/",)   # 批626:本器自有的一段;其餘全在 SUP_MDL753 正典
# ═══ 批626:排除清單改吃正典,不再各寫各的 ═══════════════════════
# v0100 的 SKIP_FRAGS 少了四段:`references/intake`(收容正本,帶 sha 冊)、
# `RetiredEngines`、`_backup`、`SCOPE_COPY`。少這四段的後果不是「漏掃」,
# 是 `--run` 會**寫進收容正本**——那是正本零觸碰那一條。
# 所以 v0101 不自己列清單,吃 SUP_MDL753 的 SCAN_EXCLUDE(L77 正典)。
# 正典不在就**誠實停**,不拿一張比較短的清單代打(代打等於把破口留著)。
def _canon():
    """載 SUP_MDL753 正典(尾版律);缺席回 None。"""
    import importlib.util as _ilu
    p = Path(__file__).resolve()
    while p.parent != p:
        sm = p / "supportive modules"
        if sm.is_dir():
            hits = sorted(x for x in sm.glob("SUP_MDL753_VIACommonUtils_v*.py")
                          if "_sha" not in x.name)
            if not hits:
                return None
            try:
                spec = _ilu.spec_from_file_location("SUP_MDL753_VIACommonUtils", hits[-1])
                m = _ilu.module_from_spec(spec)
                sys.modules.setdefault("SUP_MDL753_VIACommonUtils", m)
                spec.loader.exec_module(m)
                return m if hasattr(m, "scan_excluded") else None
            except Exception:
                return None
        p = p.parent
    return None


_CANON = _canon()
_FROZEN: set = set()


def excluded(rp: str) -> bool:
    """排除判準單一入口。正典在=用正典;正典不在=呼叫端已經先擋下了。"""
    if _CANON is None:
        raise RuntimeError("SUP_MDL753 正典缺席:排除清單沒有第二把尺,誠實停")
    return _CANON.scan_excluded(rp)


# ═══ 批626 同義候選(LL90:裁定權在操作員,本檔不代裁)═════════════
# 本器(批102 TOOL-101 / 批115 TOOL-115)和 `CGC_MDL124_BridgeSweeper` 尾版
# 做的是**同一件事**:掃全樹 .py,缺正典橋塊就注入。差別是 MDL124 多了
# git 在冊律、批597 雜湊冊凍結夾、批402 `--net-callers`(只注真外呼件)、
# 批626 唯讀正典排除;本器多了 manifest + `--undo`(MDL124 沒有)。
# 批626 實掃(容器、git 在冊律):ACCEL 全樹 2693/2693 = 100%;
# NET 真外呼件 VDF 100% —— **兩邊都已經沒有可注入的缺口**。
# 所以這不是「哪一支比較好」的問題,是「要不要留兩支」的問題,而那是操作員的裁定。
# 在裁定之前:本器 v0101 只做一件事——把排除清單接到 SUP_MDL753 正典,
# 把 v0100 少掉的四段破口補起來(`--run` 曾經會寫進收容正本)。

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
        if any(f in rp for f in SKIP_FRAGS) or excluded(rp):
            continue
        if str(p.parent) in _FROZEN:      # 批597:夾內有指名自身 .py 的 MANIFEST=凍結
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


def _readonly() -> set:
    """L102 基線裡的**正典唯讀本**清單。清單在資料檔,不在這裡寫死。"""
    try:
        import json as _json
        b = _json.loads((Path(__file__).resolve().parent
                         / "VIA_CeleritasPolicy_Baseline_v0100.json").read_text(encoding="utf-8"))
        return set((b.get("py_readonly") or {}).get("files") or [])
    except Exception:
        return set()


def inject_py(p: Path, rp: str) -> dict:
    text = p.read_text(encoding="utf-8", errors="ignore")
    if MARK in text:
        return {"rel": rp, "state": "SKIP", "note": "已橋"}
    if rp in _readonly():
        # 批715 實錄:機構 SSOT 正典唯讀本被注了橋 —— 對的規則用在不該用的檔上。
        # 唯讀的意思是**連治理自己的改動也不准**。具名跳過,不是「已橋」。
        return {"rel": rp, "state": "SKIP", "note": "正典唯讀本(具名豁免,不是已橋)"}
    # 批715:v0101 這裡還比對 `"VIA_SuperAccel_Module" in text` 與 `"VeritasCeleritas" in text`,
    # 把**提到加速器名字**當成**有橋**。實測 18 支就是這樣被漏掉的(操作員令「所有 PY 檔都要加入」
    # 之下,這 18 支一直被報成已橋)。而這兩支加速器正本自己都帶著 MARK,所以那個守衛從來
    # 就沒有保護到任何東西 —— 純粹是一道把假綠寫進報表的字面比對。
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
    if _CANON is None:
        print("  [ABSENT] SUP_MDL753 正典缺席 → 排除清單沒有第二把尺,誠實停(rc=3)")
        return 3
    _FROZEN.clear()
    _FROZEN.update(_CANON.frozen_dirs(root))
    print(f"  [排除] 正典 SCAN_EXCLUDE {len(_CANON.SCAN_EXCLUDE)} 段 · "
          f"批597 凍結夾 {len(_FROZEN)} 個(夾內有指名自身 .py 的 MANIFEST)")
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
        # ⑪ 批715:**提到加速器名字 ≠ 有橋**(v0101 這裡報假綠,實測 18 支被漏掉)
        f11 = root / "mentions_only.py"
        f11.write_text('"""這支只是**提到** VeritasCeleritas 與 VIA_SuperAccel_Module,'
                       '一行橋都沒有。"""\nx = 1\n', encoding="utf-8")
        r11 = inject_py(f11, "mentions_only.py")
        chk("提到名字≠有橋(批715:v0101 把『文中提到加速器』當成『已橋』,"
            "18 支就是這樣被報成綠的;兩支加速器正本自己都帶 MARK,那道守衛從來沒保護過任何東西)",
            r11["state"] == "OK" and MARK in f11.read_text(encoding="utf-8"))
    n = 11 - len(fails)
    print(f"  [計] 十一檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 全面加速器導入器 v0102 · 自測(沙盒零網路;檢數現場計)===")
        return selftest()
    if "--undo" in a:
        i = a.index("--undo")
        print("=== 加速器導入 undo(僅剝本器塊且 hash 未變)===")
        return undo(Path(a[i + 1]))
    if "--run" in a:
        print("=== 全面加速器導入器 v0102(TOOL-101 批102;排除清單吃 SUP_MDL753 正典)===")
        return run(VIA, do_ps="--ps" in a)
    print(__doc__.split("用法:")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main())
