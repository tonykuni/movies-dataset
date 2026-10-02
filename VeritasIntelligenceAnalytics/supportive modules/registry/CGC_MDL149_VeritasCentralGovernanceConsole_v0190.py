#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0190 — 薄尾:閘的沿用只沿用「過」(失敗不記、記著的失敗不用)· 骨架節點帶必填欄(Python 3.13 不再警告)

實測(工作站 2026-10-03 貼回 via-vcgc test:136 站 · 紅 94):紅站最後一行幾乎都是
  `[沿用] gate_ok · 鑰匙 c829e6274566b0af · N s 前算的` —— 94 站共用**同一把鑰匙**的同一筆閘結果。
根因(v0188 是本對話框出的):cached() 不分過或不過,回傳值能存 JSON 就記下;鑰匙 = 樹指紋 + SDD / TEST / HANDOFF 報告,
TEST 報告要整輪串測跑完才變 → 第一站閘一次沒過,後面 93 站都沿用那一筆失敗。同一時段直接 `via-vcgc run … probe` 印「政策過」;
政策冊的衝突律 / 還原點兩段只印不擋(_policy_conflict / _policy_restore 一律 return 0),不是那九條律擋的。
本版只改這一件(v0188 / v0189 一字不動,換的是 v0188 模組上的 cached,install() 執行時才取它):
  ① policy(policy_step 回 0 才算過)· gate_ok(回 (True, …) 才算過):過才記、才沿用;沒過一律不記,
     沿用檔裡若是上次的失敗 → 丟掉照算(印 [沿用] … 上次沒過 → 不沿用)。sync_check 等其他照 v0188。
  ② v0189 骨架樹的 ClassDef / FunctionDef 帶必填欄(name · args · body · decorator_list):Python 3.13 起
     「FunctionDef.__init__ missing … 'args' / 'name'」DeprecationWarning 不再印(3.15 會變錯)。收集到的(類別 · 巢狀名 · 行號)不變。
其餘照 v0189(VIA_FROM_VCGC=YES 才放行,同前版)。不碰 TA-Lib;不代設同意閘;零網路。
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

import ast as _real_ast
import contextlib
import functools
import importlib.util
import json
import os
import re
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0190", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0189
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0188 = PRIOR.PRIOR                                     # v0188:cached · install · CACHE


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- ① 閘只沿用「過」
PASS_V0190 = {
    "policy": lambda r: r == 0,
    "gate_ok": lambda r: isinstance(r, (tuple, list)) and len(r) >= 1 and r[0] is True,
}
_CACHED_V0188 = V0188.cached


def cached(name: str, fn, key_fn=None):
    inner = _CACHED_V0188(name, fn, key_fn)
    ok = PASS_V0190.get(name)
    if ok is None:                                       # sync_check 等:照 v0188
        return inner

    @functools.wraps(fn)
    def wrapper(*a, **k):
        path = V0188.CACHE / f"v0188_{name}.json"
        try:
            c = json.loads(path.read_text(encoding="utf-8"))
            ret = tuple(c["ret"]) if c.get("tuple") else c.get("ret")
            if not ok(ret):
                path.unlink()
                print(f"  [沿用] {name} 上次沒過 → 不沿用,照算", file=sys.stderr)
        except (OSError, ValueError, TypeError, KeyError):
            pass
        ret = inner(*a, **k)
        if not ok(ret):
            with contextlib.suppress(OSError):
                path.unlink()                            # 沒過不留給下一站
        return ret

    wrapper.__v0188_cached__ = True
    return wrapper


V0188.cached = cached                                    # v0188 install() 執行時從自己模組全域取 cached → 走本版


# ---------------------------------------------------------------- ② 骨架節點帶必填欄
def _build_v0190(shape: list) -> list:
    nodes = []
    for kind, name, line, kids in shape:
        body = _build_v0190(kids)
        if kind == "c":
            n = _real_ast.ClassDef(name=name, bases=[], keywords=[], body=body, decorator_list=[])
        else:
            n = _real_ast.FunctionDef(name=name, args=_real_ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
                                      body=body, decorator_list=[])
        n.lineno = line
        nodes.append(n)
    return nodes


PRIOR._build_v0189 = _build_v0190                        # v0189 的骨架樹在自己模組全域叫 _build_v0189


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    # 前版鏈自測先跑;v0189 / v0188 的「尾版 = 自己這支檔」檢查,跑前版自測時把 v0189 的 __file__ 暫指目前生效入口(本檔),跑完還原。
    keep_file = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        prior_rc = PRIOR.selftest()
    finally:
        PRIOR.__dict__["__file__"] = keep_file
    print("=== VCGC v0190 · 薄尾自測(閘只沿用「過」· 骨架節點必填欄)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版鏈自測過(v0189 → v0188 → …)", prior_rc == 0, f"rc {prior_rc}")
    keep_cache = V0188.CACHE
    with tempfile.TemporaryDirectory() as td:
        V0188.CACHE = Path(td)
        try:
            calls = {"policy": 0, "gate_ok": 0, "sync_check": 0}
            result = {"policy": 2, "gate_ok": (False, "x")}

            def pol():
                calls["policy"] += 1
                return result["policy"]

            def gate():
                calls["gate_ok"] += 1
                return result["gate_ok"]

            def sync(key=None):
                calls["sync_check"] += 1
                return {"aligned": True}

            fixed = lambda *a, **k: "k1"
            p, g, s = V0188.cached("policy", pol, fixed), V0188.cached("gate_ok", gate, fixed), V0188.cached("sync_check", sync, fixed)
            with contextlib.redirect_stderr(open(os.devnull, "w", encoding="utf-8")):
                p(); p(); g(); g()
                fail_runs = (calls["policy"], calls["gate_ok"])
                result.update(policy=0, gate_ok=(True, "[流程] 政策過"))
                p(); p(); g(); g()
                pass_runs = (calls["policy"], calls["gate_ok"])
                (Path(td) / "v0188_policy.json").write_text(json.dumps({"key": "k1", "t": 9e18, "out": "", "ret": 2, "tuple": False}), encoding="utf-8")
                p()
                stale_fail = calls["policy"]
                s(); s()
        finally:
            V0188.CACHE = keep_cache
    chk("② 沒過的閘不記:policy 回 2 · gate_ok 回 False 時連叫兩次都照算(94 站不再連坐同一筆失敗)", fail_runs == (2, 2), fail_runs)
    chk("③ 過的閘照 v0188 沿用:回 0 / (True, …) 第二次直接沿用", pass_runs == (3, 3), pass_runs)
    chk("④ 沿用檔裡若是上次的失敗 → 丟掉照算", stale_fail == 4, stale_fail)
    chk("⑤ 其他(sync_check)照 v0188 沿用,不受本版影響", calls["sync_check"] == 1, calls["sync_check"])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        tree = _build_v0190([["c", "A", 3, [["f", "m", 4, []]]], ["f", "g", 9, []]])
    got = [(type(n).__name__, n.name, n.lineno, [(type(c).__name__, c.name, c.lineno) for c in n.body]) for n in tree]
    chk("⑥ 骨架節點帶必填欄:建樹不出 DeprecationWarning · 名稱 / 行號 / 巢狀照舊",
        not [x for x in w if issubclass(x.category, DeprecationWarning)]
        and got == [("ClassDef", "A", 3, [("FunctionDef", "m", 4)]), ("FunctionDef", "g", 9, [])] and PRIOR._build_v0189 is _build_v0190, got)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 已裝進前版(v0188.cached · v0189._build_v0189)· 加速器橋在 · 只收 VCGC · 不碰 TA-Lib",
        V0188.cached is cached and "[VIA:ACCEL-BRIDGE" in src and "VIA_FROM_VCGC" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"  [計] VCGC v0190 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv[1:] else main())
