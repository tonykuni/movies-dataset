#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_SystemManager v0125 — 薄尾(v0124 以前一字不動):launch 的 NEXT 也看最後的 overview 步(PR #773 Codex 第三輪 P2)

v0122 的 _next 只看 token 閘與並行各步;只有 overview 失敗 / 逾時時,主機的貼回包會叫人「handoff daily(收工)」,
容器(v0124)則給一般的主機啟動提示 —— 都沒有指向讓總燈變紅的那一步與它的日誌。
本版:NEXT 依 紅 → 黃 → 灰 的順序看 token · 各道 · overview 三段,第一個不綠的步就是 NEXT(指令 + 日誌);
全綠才交給 v0124(容器 → 主機一行;主機 → 收工)。
掛鉤裝在定義 _next 的那一層(v0122);收據 version / 標籤寫 v0125。其餘動詞照 v0124 → … 原樣轉交。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(從 TEMP 跑時改由工作目錄 / VIA_REPO 找倉;graceful) =====
try:
    import os as _sa_os
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_hit = None
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.append(_sa_Path(_sa_os.environ["VIA_REPO"]).resolve())
    for _sa_r in _sa_roots:
        for _sa_q in (_sa_r, *_sa_r.parents):
            for _sa_c in (_sa_q / "supportive modules", _sa_q / "VeritasIntelligenceAnalytics" / "supportive modules"):
                if (_sa_c / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit:
                break
        if _sa_hit:
            break
    if _sa_hit and str(_sa_hit) not in _sa_sys.path:
        _sa_sys.path.insert(0, str(_sa_hit))
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席時照樣載得起來(v0123 的 launch 會把總燈壓到黃)
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_SystemManager"
VERSION = "v0125"
TAG = f"{_STEM} {VERSION}"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


_BELOW = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
if not _BELOW:   # 放錯倉:照實停,不丟例外(同 v0122)
    print(f"[RED] {HERE} 沒有 {_STEM} 前版;這份不是主工作倉。", flush=True)
    raise SystemExit(3)
PRIOR_PATH = max(_BELOW, key=_vnum)
_spec = importlib.util.spec_from_file_location(f"cgc_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _chain():
    m = PRIOR
    while m is not None:
        yield m
        m = vars(m).get("PRIOR")


def _first_defining(name: str):
    """鏈上(由新到舊)第一個在自己 vars 裡寫了 name 的那一層。"""
    return next(m for m in _chain() if name in vars(m))


def _origin_layer(name: str):
    """鏈上最舊的那個 vars 裡有 name 的層 = 原本定義它的那一層(後面的版本可能也定義了同名包裝)。"""
    return [m for m in _chain() if name in vars(m)][-1]


_NEXT_HOME = _origin_layer("_next")          # v0122(launch 經 PRIOR._next 找到這一層)
_LAUNCH_HOME = _first_defining("tally")      # v0123(launch 的收據 version / 標籤讀這一層的全域)
_PREV_NEXT = vars(_NEXT_HOME)["_next"]       # 目前掛著的(v0124 的容器包裝)


def _next(res: dict) -> str:
    """紅 → 黃 → 灰:token · 各道 · overview 三段裡第一個不綠的步;全綠才交給前版。"""
    steps = [res.get("gate_result")] + list(res.get("results") or []) + [res.get("post_result")]
    for want in ("RED", "YELLOW", "GRAY"):
        for s in [x for x in steps if x and x.get("lamp") == want]:
            f = Path(s["file"]).name if s.get("file") else "?"
            return f"python \"{f}\" {' '.join(s.get('argv') or [])}(看 {s.get('log')})"
    return _PREV_NEXT(res)


def install() -> None:
    _NEXT_HOME._next = _next
    _LAUNCH_HOME.VERSION = VERSION
    _LAUNCH_HOME.TAG = TAG


install()


def launch(argv: list, **kw) -> int:
    kw.setdefault("self_file", Path(__file__).resolve())
    return _LAUNCH_HOME.launch(argv, **kw)


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["launch"]:
        return launch(a[1:])
    return PRIOR.main()


_FAKE_POST_RED = ("import os, sys\n"
                  "a = sys.argv[1:]\n"
                  "assert os.environ.get('VIA_FROM_VCGC') == 'YES'\n"
                  "if a[:1] == ['overview']: print('[RED] overview 假紅'); sys.exit(1)\n"
                  "print('[假步] GREEN · fake'); sys.exit(0)\n")


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(("  [OK] " if cond else "  [NG] ") + name + (f" · {note}" if note else ""), flush=True)

    chk("① 加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    below = [p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    chk("② 前版經 glob 載入(本檔之下最大的一版)", PRIOR_PATH == max(below, key=_vnum), PRIOR_PATH.name)
    me_mod = sys.modules[__name__]
    chk("③ TAILAPI:前版公開名稱經本檔轉接(overall · tally · plan · run_steps · cmd_schedule · core_python)",
        all(callable(getattr(me_mod, n, None)) for n in ("overall", "tally", "plan", "run_steps", "cmd_schedule", "core_python")))
    chk("④ 掛鉤裝在定義 _next 的那一層(v0122)· 收據版本層 = v0123",
        vars(_NEXT_HOME)["_next"] is _next and _NEXT_HOME.__name__.endswith("v0123") and _LAUNCH_HOME.__name__.endswith("v0124"),
        f"_next @ {_NEXT_HOME.__name__} · version @ {_LAUNCH_HOME.__name__}")

    def st(name, lamp):
        return {"name": name, "lamp": lamp, "file": f"/x/{name}.py", "argv": [name], "log": f"/tmp/{name}.log"}

    g = st("token", "GREEN")
    res = {"host": "主機", "gate_result": g, "results": [st("test", "GREEN"), st("sdd", "GREEN")], "post_result": st("overview", "RED")}
    n1 = _next(res)
    chk("⑤ 只有 overview 紅 → NEXT 指 overview 與它的日誌(不再叫人收工)", "overview" in n1 and "/tmp/overview.log" in n1, n1[:70])
    res2 = dict(res, results=[st("test", "YELLOW"), st("sdd", "GREEN")], post_result=st("overview", "RED"))
    chk("⑥ 紅優先於黃:overview 紅 · test 黃 → 指 overview", "overview" in _next(res2))
    res3 = dict(res, post_result=st("overview", "GREEN"))
    chk("⑦ 全綠 → 交給前版(主機:收工;容器:主機一行)",
        _next(res3).startswith("via-vcgc handoff daily") and _next(dict(res3, host="容器")) == PRIOR.HOST_NEXT)
    res4 = dict(res, post_result=None)
    chk("⑧ 閘紅停下(沒有 overview)照舊指 token", "token" in _next(dict(res4, gate_result=st("token", "RED"), results=[])))
    saved_no_open = os.environ.pop("VIA_NO_OPEN", None)   # 自測不吃本機狀態(LL-20261128-02)
    try:
        with tempfile.TemporaryDirectory() as td:
            via = Path(td) / "repo" / "VeritasIntelligenceAnalytics"
            reg = via / "supportive modules" / "registry"
            ai = via / "docs" / "handoff" / "ai"
            reg.mkdir(parents=True)
            ai.mkdir(parents=True)
            for f in (reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0100.py", reg / "CGC_MDL158_Fake_v0100.py", ai / "VIA_ReworkGuard_v0100.py"):
                f.write_text(_FAKE_POST_RED, encoding="utf-8")
            (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps(
                {"token": {"path": "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL158_Fake_v0100.py"}}), encoding="utf-8")
            me = reg / "CGC_FakeManager_v0100.py"   # 假管理器夾具(不用本家族名)
            me.write_text(_FAKE_POST_RED, encoding="utf-8")
            out = via / "VIA_Reports" / "vcgc" / "launch"
            lines = []
            rc = _LAUNCH_HOME.launch(["--timeout", "30", "--no-open"], via, reg, me, sys.executable, out, lambda u: True,
                                     lambda m, lamp=None: lines.append(m), 1, True)
            r = json.loads((out / "LAUNCH_latest.json").read_text(encoding="utf-8"))
            pk = (out / "LAUNCH_latest.txt").read_text(encoding="utf-8").splitlines()
            chk("⑨ 端到端:overview 假紅 → 總燈 RED · rc 1 · 收據 version v0125 · 貼回包 NEXT 指 overview",
                rc == 1 and r["lamp"] == "RED" and r["version"] == VERSION and pk[-1].startswith("NEXT:") and "overview" in pk[-1], pk[-1][:80])
    finally:
        if saved_no_open is not None:
            os.environ["VIA_NO_OPEN"] = saved_no_open
    env = dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1")
    env.pop("VIA_NO_OPEN", None)
    pl = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "launch", "--plan", "--plain"], capture_output=True,
                        text=True, encoding="utf-8", errors="replace", env=env, timeout=300)
    chk("⑩ 入口:launch 走本版(真倉 --plan · rc 0 · 本版標籤 · 不寫檔)", pl.returncode == 0 and f"[{TAG}]" in pl.stdout, (pl.stdout.strip().splitlines() or ["?"])[-1][:80])
    pr = subprocess.run([sys.executable, "-X", "utf8", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                        errors="replace", env=env, timeout=1500)
    last = (pr.stdout.strip().splitlines() or ["?"])[-1]
    chk("⑪ 直接前版自測(乾淨子行程)rc 0", pr.returncode == 0, last[:80])
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
