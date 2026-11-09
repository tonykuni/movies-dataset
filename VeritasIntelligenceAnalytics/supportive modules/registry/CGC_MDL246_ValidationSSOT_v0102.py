#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL246_ValidationSSOT v0102 — 薄尾:工作流冊 tests 列表式(TST 案)不炸;RC-1 W1 Bug Fix

實錄(2026-11-09,handoff test validation_ssot_v0101 rc 1):
  AttributeError: 'list' object has no attribute 'get' —— 本體 v0100 check() 第 231 行
  `for c in (w.get("tests") or {}).get("cross") or []` 寫死 tests 是字典;工作流冊 v0133 起 WKF022+ 的 tests 是 TST 列表
  ([{code, case, engine|cmd, verb, expect}]),一碰到就整支炸(和 CGC_MDL245 v0107 修的是同一類病,見 LESSON-0006)。
本版只換一支 workflow_books(換裝在位 PRIOR.workflow_books = workflow_books;本體 main / v0101 selftest 都經模組全域拿冊):
  照 v0100 的 workflow_books 讀(L05 一把尺:CGC_MDL245 load_books,讀不到才退回自己找尾版),
  再把每條工作流的列表式 tests 換成字典視圖 {"self": [案名…], "cross": [], "real": [], "tst": 原列表}
  —— TST 列表式不引用任何 X- 交叉代碼,V-XREF 照實給 [](不假造 X-*);原冊檔不動,換的是深拷貝。
check / show / main 全照 v0101 → v0100(v0100 · v0101 一字不動)。只收 VCGC 呼叫;零網路;不碰 TA-Lib。
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

import contextlib
import copy
import importlib.util
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
_STEM = "CGC_MDL246_ValidationSSOT"


def _vnum_v0102(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0102(p) < _vnum_v0102(__file__)), key=_vnum_v0102)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_V0100_BOOKS = BASE.workflow_books


def tests_view(tests):
    """列表式 tests → 字典視圖(cross = []:TST 案不引用 X- 代碼);字典 / None 原樣回。"""
    if isinstance(tests, list):
        return {"self": [str(t.get("case") or t.get("code") or "?") for t in tests if isinstance(t, dict)],
                "cross": [], "real": [], "tst": tests}
    return tests


def normalize_books(books: dict) -> dict:
    """{系統: 冊} 深拷貝,只換列表式 tests;原冊物件不動。"""
    out = {}
    for s, b in (books or {}).items():
        b2 = copy.deepcopy(b) if isinstance(b, dict) else b
        for w in (b2 or {}).get("workflows") or [] if isinstance(b2, dict) else []:
            if isinstance(w.get("tests"), list):
                w["tests"] = tests_view(w["tests"])
        out[s] = b2
    return out


def workflow_books() -> dict:
    """v0100 workflow_books(L05 一把尺)+ 列表式 tests 視圖(本體 check 的 .get("cross") 吃得下)。"""
    return normalize_books(_V0100_BOOKS())


BASE.workflow_books = workflow_books                               # 本體 main / v0101 selftest 都經模組全域拿冊 → 換裝即生效


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    print(f"=== {ENGINE} · 薄尾自測(工作流冊 tests 列表式不炸)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:220]) if note and not cond else ''}")

    lst = [{"code": "VCGC-WKF900-TST001", "case": "C-x", "engine": "x.py", "verb": "--selftest", "expect": "rc 0"}]
    v = tests_view(lst)
    chk("① 列表式 → 視圖:self 列案名 · cross [] · real [] · tst 留原列表;字典 / None 原樣",
        v["self"] == ["C-x"] and v["cross"] == [] and v["tst"] is lst and tests_view({"cross": ["X-COL"]}) == {"cross": ["X-COL"]} and tests_view(None) is None)
    raw = {"VCGC": {"workflows": [{"code": "A", "tests": lst}, {"code": "B", "tests": {"cross": ["X-COL"]}}, {"code": "C"}]}}
    nb = normalize_books(raw)
    chk("② 冊深拷貝:列表式換視圖 · 字典式 / 缺欄照舊 · 原冊物件沒被改",
        isinstance(nb["VCGC"]["workflows"][0]["tests"], dict) and nb["VCGC"]["workflows"][1]["tests"] == {"cross": ["X-COL"]}
        and "tests" not in nb["VCGC"]["workflows"][2] and isinstance(raw["VCGC"]["workflows"][0]["tests"], list))
    chk("③ 本體換裝:v0100 的 workflow_books 指向本版", BASE.workflow_books is workflow_books and PRIOR.workflow_books is workflow_books)
    books = workflow_books()
    n_list = sum(1 for b in _V0100_BOOKS().values() for w in (b or {}).get("workflows") or [] if isinstance(w.get("tests"), list))
    n_left = sum(1 for b in books.values() for w in (b or {}).get("workflows") or [] if isinstance(w.get("tests"), list))
    chk(f"④ 真冊:列表式工作流 {n_list} 條(有,才證得到)→ 視圖後 0 條", n_list > 0 and n_left == 0, (n_list, n_left))
    bp = PRIOR.newest(PRIOR.BOOK_GLOB)
    book = PRIOR._json(bp) or {}
    pol, sdd_text = PRIOR.policy_ids(), PRIOR.chain_text(PRIOR.newest("CGC_MDL245_SDDValidator_v*.py"))
    try:
        rep = PRIOR.check(book=book, books=books, sdd_text=sdd_text, pol_ids=pol)
        crashed = ""
    except Exception as exc:  # noqa: BLE001
        crashed, rep = repr(exc), {"rows": [], "state": "CRASH"}
    notg = [f"{r['rule']}:{r['msg'][:70]}" for r in rep["rows"] if r["lamp"] != "GREEN" and r["rule"] in ("V-CODE", "V-XREF", "V-SDD", "V-OWNER", "V-IMPL", "V-POLICY")]
    chk(f"⑤ 真冊 {bp.name if bp else '-'}:check 整輪跑完不炸 · V-CODE / V-XREF / V-SDD 無紅黃 · 整冊 {rep.get('state')}",
        not crashed and not notg and rep.get("state") == "GREEN", crashed or notg or rep.get("why"))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = PRIOR.selftest()
    print("  ── 前版 v0101 自測(摘末行)── " + (buf.getvalue().strip().splitlines() or ["(無輸出)"])[-1])
    chk("⑥ 前版鏈 v0101 → v0100 自測 rc 0(換裝後它們的真冊檢也過)", prc == 0)
    src = Path(__file__).read_text(encoding="utf-8")
    import ast
    chk("⑦ 檔頭:加速器橋在(__future__ 之後);不碰 TA-Lib;不直派子行程",
        "[VIA:ACCEL-BRIDGE:" in src and src.index("from __future__") < src.index("[VIA:ACCEL-BRIDGE:")
        and "import " + "talib" not in src
        and not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any((x.name or "").split(".")[0] == "sub" + "process" for x in n.names) for n in ast.walk(ast.parse(src))))
    print(f"[計] {ENGINE} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
