#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0127 — 薄尾:fetch 動詞 = VDF 獨立擷取系統(MDL008 帶 MDL001–007 核心擷取引擎)

操作員 2026-10-03:「VDF 只留擷取」「先拿舊模組用 vdf manager 建立獨立擷取系統」「MDL 001–099 才是資料引擎」
「放在子系統的大引擎用 MDL,小功能指令用 ENG」「整合測試輸出成功」。
  fetch [list]                         七支核心擷取引擎(冊 VDF_FetchSystem_SSOT_v0100.json)· 檔在否 · 擷取函式 · 輸出契約
  fetch plan [MDL…] [--mode M]         依相依排序列計畫(不執行)
  fetch run [MDL…] --apply [--mode live|fixture|block] [--home 夾]
                                       live 要操作員開 VIA_NET_CONSENT(系統只讀;沒開 rc4 GATED 零出網)
  fetch verify [MDL…] [--home 夾]      輸出契約逐檔驗(在 · 非空 · 列數)
  fetch test                           離線整合測試(fixture 網跑全鏈 → 驗輸出 → 倉內零寫入 → block 網零出網)
本體在 MDL008(子系統大引擎;本管理員只轉交)。其餘動詞全照 v0127(未知動詞拒跑 · 抬頭註明尾版)。
只收 VCGC 呼叫;不碰 TA-Lib;不代設同意閘。
"""
from __future__ import annotations# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
SUB = "VDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
VERBS_v0127 = ('status', 'catalog', 'links', 'records', 'engines', 'bridges', 'tools', 'read', 'sync', 'page', 'launch', 'record', 'matrix', 'measure', 'universe', 'engine', 'params', 'prep', 'start', 'test', 'register', 'policy', 'update', 'ps', 'fetch')


def _vnum_v0127(path) -> int:            # 版本專屬名:元件冊以函式登記,共用名會把前版的紀錄搶走
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0127(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0127(p) < _vnum_v0127(__file__)), key=_vnum_v0127)
PRIOR = _load_v0127(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def verb_problem_v0127(args) -> str:
    """回空字串 = 放行;首詞不是旗標又不在動詞表 → 拒跑理由(中文)。子動詞交各版自己判。"""
    if not args or args[0].startswith("-") or args[0] in VERBS_v0127:
        return ""
    return f"未知動詞 '{args[0]}'(已知:{' · '.join(VERBS_v0127)};旗標 --json · --standalone · --selftest 等照前版)"


def _with_argv_v0127(args, fn):
    """前版多數 main() 讀 sys.argv:暫換成本次參數再交棒,交完還原。"""
    keep = sys.argv
    sys.argv = [keep[0] if keep else str(Path(__file__)), *args]
    try:
        return fn()
    finally:
        sys.argv = keep


FETCH_SYSTEM_V0127 = HERE / "VDF_MDL008_FetchSystem_v0100.py"


def fetch_v0127(rest: list) -> int:
    """fetch 動詞 → MDL008 獨立擷取系統(子系統大引擎);缺席誠實 ABSENT rc3。"""
    tails = sorted(HERE.glob("VDF_MDL008_FetchSystem_v*.py"), key=_vnum_v0127)
    if not tails:
        print(f"[ABSENT] {TAG}:VDF_MDL008_FetchSystem_v*.py 不在這棵樹")
        return 3
    mod = _load_v0127(tails[-1], "vdf_fetch_system_for_v0127")
    return mod.main(rest or ["list"])


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    why = verb_problem_v0127(args)
    if why:
        print(f"[拒跑] {TAG}:{why}")
        return 2
    if args[:1] == ["fetch"]:
        return fetch_v0127(args[1:])
    if (not args or args[0] == "status") and "--json" not in args:
        print(f"[{_STEM}] 尾版 {TAG}(下行抬頭的版號是狀態讀器本體的版,不是尾版)")
    return _with_argv_v0127(args, lambda: PRIOR.main(args))


def selftest() -> int:
    prior_rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(fetch 動詞 → MDL008 獨立擷取系統)===")
    keep = os.environ.get("VIA_FROM_VCGC")
    os.environ["VIA_FROM_VCGC"] = "YES"
    calls, real = [], PRIOR.main
    try:
        PRIOR.main = lambda a=None: calls.append((list(a or []), list(sys.argv[1:]))) or 0
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            bad = [main(a) for a in (["foo"], ["stauts"], ["全台股一行"], ["engin", "params"])]
            good = [main(a) for a in ([], ["status"], ["--json"], ["read", "policy"], ["engine", "list"], ["universe"], ["measure"])]
        out = buf.getvalue()
        chk("① 未知動詞 4 種:rc 2 · 不進前版 · 印 [拒跑] 與真動詞表", set(bad) == {2} and out.count("[拒跑]") == 4
            and all(v in out for v in ("params", "prep", "universe", "launch")) and len(calls) == len(good), (bad, len(calls)))
        chk("② 已知動詞 / 旗標 7 種放行;前版收到的 sys.argv = 本次參數", set(good) == {0}
            and all(c[0] == c[1] for c in calls), calls[:3])
        chk("③ 看狀態印尾版抬頭(--json 不印,不汙染 JSON)", out.count(f"尾版 {TAG}") == 2, out.count(f"尾版 {TAG}"))
    finally:
        PRIOR.main = real
        if keep is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = keep
    os.environ.pop("VIA_FROM_VCGC", None)
    with contextlib.redirect_stdout(io.StringIO()):
        deny = main(["foo"])
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("④ 未經 VCGC 仍先拒(閘在動詞判定之前)", deny == 2)
    text = Path(__file__).read_text(encoding="utf-8")
    os.environ["VIA_FROM_VCGC"] = "YES"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_l = main(["fetch"])
        rc_p = main(["fetch", "plan", "--mode", "fixture"])
        rc_x = main(["fetch", "nope"])
    if keep is None:
        os.environ.pop("VIA_FROM_VCGC", None)
    out = buf.getvalue()
    chk("⑤b fetch 轉 MDL008:list 七支全在 rc0 · plan 依相依排序 · 未知子動詞 rc2", rc_l == 0 and rc_p == 0 and rc_x == 2
        and "MDL007" in out and out.index("MDL001") < out.index("MDL004"), (rc_l, rc_p, rc_x))
    chk("⑤ 加速器橋 · 網路工具橋 · 正典橋在;不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "[VIA:LIB-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) and prior_rc == 0 else 'FAIL'}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
