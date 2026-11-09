#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL245_SDDValidator v0107 — 薄尾:tests 兩種形狀(欄位字典 · TST 列表)都吃得下;RC-1 W1 Bug Fix

RC-1 W0 稽核(2026-11-09)把 ssot panorama 的「上下連結@VCGC」記成 RED,根因不是冊壞,是本體 v0100 寫死
`(w.get("tests") or {}).get(...)`(check_columns 一處 · real 兩處):工作流冊 v0133 裡 WKF022 起的 tests 是
TST 列表([{code, case, engine|cmd, verb, expect}]),一碰到 list 就 AttributeError 整支炸,整組 X-* 列都沒出來(假紅)。
real 的兩處換不到(v0101 / v0102 的 real 包的是本體 real 的函式物件),所以本版在 load_books 出口把列表式 tests
換成字典視圖 TestCases(dict 子類 · .cases 留原列表 · 三欄只在列表齊時由案子推出),本體三處 .get 都吃得下;
再換一支 check_columns(換裝在位 BASE.check_columns = check_columns)照列表式細驗:
  tests 是字典 → 照舊要 self / cross / real 三欄;
  tests 是列表 → 每項要 case · expect · (cmd 或 engine+verb),空列表 = 缺;缺哪項寫 tests[i].欄名;
  tests 是 None / 缺 → 照舊記缺(WKF_COLS 的 tests 欄)—— 冊真缺測試就該 RED,不漂白。
其餘整支照 v0106(X-PEER · X-PEER-TEXT · check / real / lock / closeout)。只讀,不寫冊。
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL245_SDDValidator"
ENGINE = Path(__file__).stem


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_v0107", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_V0100_COLS = BASE.check_columns
_V0100_LOAD = BASE.load_books

TEST_ITEM_COLS = ("case", "expect")       # 列表式每項必備;另外要 cmd 或 engine+verb 其中一組


def _cmd(case) -> str:
    return str(case.get("cmd") or "") + " " + str(case.get("verb") or "")


def tests_missing(tests) -> list:
    """tests 欄缺了什麼(字串列表;空 = 齊)。字典 → self/cross/real;列表 → 每項 case · expect · cmd|engine+verb。"""
    if isinstance(tests, TestCases):
        tests = tests.cases
    if isinstance(tests, dict):
        return ["tests." + c for c in BASE.TEST_COLS if not tests.get(c)]
    if isinstance(tests, list):
        if not tests:
            return ["tests[](空列表)"]
        miss = []
        for i, t in enumerate(tests):
            if not isinstance(t, dict):
                miss.append(f"tests[{i}](不是物件)")
                continue
            miss += [f"tests[{i}].{c}" for c in TEST_ITEM_COLS if not t.get(c)]
            if not (t.get("cmd") or (t.get("engine") and t.get("verb"))):
                miss.append(f"tests[{i}].cmd|engine+verb")
        return miss
    return []    # None / 缺 → WKF_COLS 的 tests 欄位檢會記缺,這裡不重複


class TestCases(dict):
    """TST 列表式 tests 的字典視圖:.cases 是原列表(不動);self/cross/real 三欄只在列表齊時才有值。

    self  = 案子的 cmd/verb 含 --selftest / --run-self-test 的數目(摘要字串);
    cross = 其餘案子(交叉 / 串測)數目;全是自測就寫明「自測即交叉驗」;
    real  = 空字串:列表式不宣告 real_run,本體 real() 不會把它當 ai 實跑。
    列表缺項時三欄全空,讓本體 X-COL 照舊記缺 tests 欄。"""

    def __init__(self, cases):
        self.cases = list(cases)
        if tests_missing(self.cases):
            super().__init__()
            return
        selfs = [c for c in self.cases if "--selftest" in _cmd(c) or "--run-self-test" in _cmd(c)]
        rest = len(self.cases) - len(selfs)
        super().__init__(self=f"TST 自測 {len(selfs)} 案" if selfs else "",
                         cross=f"TST 交叉 {rest} 案" if rest else f"TST {len(self.cases)} 案(自測即交叉驗)",
                         real="")


def _with_views(state: dict) -> dict:
    """同一個 state,只把 wkfs 裡列表式 tests 換成 TestCases 視圖(不動冊檔;原 dict 不改,換的是淺拷貝)。"""
    out = []
    for sub, w in state.get("wkfs") or []:
        t = w.get("tests")
        if isinstance(t, list):
            w2 = dict(w)
            w2["tests"] = TestCases(t)
            out.append((sub, w2))
        else:
            out.append((sub, w))
    state["wkfs"] = out
    state["by_code"] = {w.get("code"): (sub, w) for sub, w in out}
    return state


def load_books() -> dict:
    """v0100 load_books + 列表式 tests 視圖(本體 check / real 三處 .get 都吃得下)。"""
    return _with_views(_V0100_LOAD())


def check_columns(state, rows):
    """X-COL(v0107):tests 列表式不炸;其餘欄位檢照 v0100 本體跑(影子狀態只為過本體的 .get)。"""
    extra = []
    shadow = []
    for sub, w in state["wkfs"]:
        t = w.get("tests")
        if isinstance(t, (list, TestCases)):
            miss = tests_missing(t)
            if miss:
                extra.append((w.get("code"), miss))
            n = len(t.cases if isinstance(t, TestCases) else t)
            w2 = dict(w)
            w2["tests"] = ({c: f"TST 列表 {n} 項" for c in BASE.TEST_COLS} if not miss else None)
            shadow.append((sub, w2))
        else:
            shadow.append((sub, w))
    s2 = dict(state)
    s2["wkfs"] = shadow
    before = len(rows)
    _V0100_COLS(s2, rows)
    if extra:
        # 本體對缺 tests 欄只會寫「tests」;把列表式的細項補進同一條 RED(同碼不另開列)
        for code, miss in extra:
            hit = [r for r in rows[before:] if r.get("rule") == "X-COL" and r.get("ref") == code]
            detail = f"tests 列表式缺項:{', '.join(miss[:6])}"
            if hit:
                hit[0]["msg"] = hit[0]["msg"] + " · " + detail
            else:
                BASE._row(rows, "RED", "X-COL", f"{code} {detail}", code)
        # 補了 RED 就不能同時留 GREEN 總結
        rows[:] = rows[:before] + [r for r in rows[before:] if not (r.get("rule") == "X-COL" and r.get("lamp") == "GREEN")]


BASE.check_columns = check_columns
BASE.load_books = load_books


def __getattr__(name: str):
    return getattr(PRIOR, name)


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {ENGINE} · 薄尾自測(X-COL tests 兩種形狀 · load_books 列表視圖)===")

    def wkf(tests, code="VCGC-WKF900"):
        return {"code": code, "alias": "a", "name": "n", "kind": "procedure",
                "spec": {"goal": "g", "requirements": ["R"], "acceptance": ["a"]}, "plan": {"order": "x"},
                "steps": [{"code": code + "-STP001", "alias": "s", "engine": "x.py", "verb": "v", "what": "w", "match": "m"}],
                "tests": tests}

    def lamps(*ws):
        rows = []
        check_columns({"wkfs": [("VCGC", w) for w in ws]}, rows)
        return [(r["lamp"], r["msg"][:160]) for r in rows if r["rule"] == "X-COL"]

    good_dict = {"self": "s", "cross": "c", "real": "r"}
    good_list = [{"code": "VCGC-WKF900-TST001", "case": "C-x", "engine": "x.py", "verb": "--selftest", "expect": "rc 0"},
                 {"case": "C-y", "cmd": "run x", "expect": "rc 0"}]
    chk("① 字典式齊 + 列表式齊(engine+verb 或 cmd)→ X-COL GREEN,不炸",
        [l for l, _ in lamps(wkf(good_dict), wkf(good_list, "VCGC-WKF901"))] == ["GREEN"], lamps(wkf(good_dict), wkf(good_list, "VCGC-WKF901")))
    chk("② 字典式缺 real → RED 寫 tests.real(v0100 行為照舊)",
        any(l == "RED" and "tests.real" in m for l, m in lamps(wkf({"self": "s", "cross": "c"}))), lamps(wkf({"self": "s", "cross": "c"})))
    bad_list = [{"case": "C-z", "expect": "rc 0"}, {"code": "T", "engine": "x.py", "verb": "--selftest"}]
    got = lamps(wkf(bad_list))
    chk("③ 列表式缺 cmd|engine+verb、缺 case/expect → RED 指到 tests[i].欄名;沒有 GREEN 總結",
        any(l == "RED" and "tests[0].cmd|engine+verb" in m and "tests[1].case" in m for l, m in got) and not any(l == "GREEN" for l, _ in got), got)
    chk("④ 空列表 / None → RED(真缺測試不漂白)",
        any(l == "RED" for l, _ in lamps(wkf([]))) and any(l == "RED" and "tests" in m for l, m in lamps(wkf(None))), (lamps(wkf([])), lamps(wkf(None))))
    w0 = wkf(good_list)
    check_columns({"wkfs": [("VCGC", w0)]}, [])
    chk("⑤ 不動原冊:check_columns 不改 state 裡的 tests 物件", isinstance(w0["tests"], list) and w0["tests"] == good_list)
    v = TestCases(good_list)
    chk("⑥ 視圖:齊的列表 → self 有值 · real 空字串(不冒充 ai 實跑)· .cases 是原列表;缺的列表 → 三欄全空",
        v.get("self") and v.get("real") == "" and v.get("real_run") is None and v.cases == good_list and not TestCases(bad_list).get("self"), dict(v))
    real = BASE.load_books()
    rr = []
    try:
        BASE.check_columns(real, rr)
        crashed = ""
    except Exception as exc:  # noqa: BLE001
        crashed = repr(exc)
    views = [w["code"] for _, w in real["wkfs"] if isinstance(w.get("tests"), TestCases)]
    chk("⑦ 實樹:load_books / check_columns 都是本版 · 真冊列表式工作流拿到視圖(by_code 同步)· 本體 check_columns 不炸",
        not crashed and BASE.check_columns is check_columns and BASE.load_books is load_books and views
        and all(isinstance(real["by_code"][c][1]["tests"], TestCases) for c in views), crashed or (views, [(r["lamp"], r["msg"][:120]) for r in rr]))
    try:
        rep = BASE.check(write=False)
        xcol = [r for r in rep.get("rows") or [] if r.get("rule") == "X-COL"]
        crashed = ""
    except Exception as exc:  # noqa: BLE001
        crashed, xcol, rep = repr(exc), [], {}
    chk("⑧ 實樹:本體 check(write=False) 整輪跑完不炸(RC-1 W0 假紅的根因),X-COL 列有出來", not crashed and xcol, crashed or str(rep)[:200])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    rc = PRIOR.selftest()
    return rc if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
