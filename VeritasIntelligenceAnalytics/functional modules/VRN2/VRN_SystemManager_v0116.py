#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0116 — 薄尾:未知動詞拒跑(rc 2 + 列出真動詞)· read logic 不再被 logic 動詞劫走 · 抬頭註明尾版

語意錯誤全景(2026-10-03,側線語意掃描 A3)實測:
  ① `via-vcgc vrn foo` → 落到 v0101 印舊用法(沒有 matrix · logic · provenance · outputs · frame · engine · params · prep)且 rc 0。
  ② `via-vcgc vrn read logic`(v0101 用法明列的讀域)→ v0109 用 `"logic" in sys.argv` 判動詞,整串任何位置有 logic 就改跑
     VRN_ENG113 LogicRollup;使用者要的邏輯域讀卡(ENG082 邏輯庫 · 守門)拿不到。
  ③ 狀態抬頭寫「VRN_SystemManager v0104」(狀態讀器本體的版),實際跑的是尾版。
本版只加三格(v0100–v0115 一字不動):
  ① 首詞不是旗標又不在動詞表 → [拒跑] + 全部動詞(各版 main 實際分派的動詞,AST 盤點),rc 2,不進前版。
  ② 首詞是 read → 直接交 v0108(= v0109 的 _facade 本體,v0110–v0115 不碰 read),繞過 v0109 的整串掃描;logic 動詞(首詞)照舊。
  ③ 看狀態(不帶動詞或 status,且非 --json)先印一行「尾版 vNNNN;下行抬頭版號 = 狀態讀器本體」。
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

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
SUB = "VRN"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
VERBS_v0116 = ('status', 'catalog', 'links', 'records', 'read', 'sync', 'page', 'matrix', 'logic', 'provenance', 'outputs', 'frame', 'engine', 'params', 'prep')


def _vnum_v0116(path) -> int:            # 版本專屬名:元件冊以函式登記,共用名會把前版的紀錄搶走
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0116(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0116(p) < _vnum_v0116(__file__)), key=_vnum_v0116)
PRIOR = _load_v0116(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def verb_problem_v0116(args) -> str:
    """回空字串 = 放行;首詞不是旗標又不在動詞表 → 拒跑理由(中文)。子動詞交各版自己判。"""
    if not args or args[0].startswith("-") or args[0] in VERBS_v0116:
        return ""
    return f"未知動詞 '{args[0]}'(已知:{' · '.join(VERBS_v0116)};旗標 --json · --standalone · --selftest 等照前版)"


def _with_argv_v0116(args, fn):
    """前版多數 main() 讀 sys.argv:暫換成本次參數再交棒,交完還原。"""
    keep = sys.argv
    sys.argv = [keep[0] if keep else str(Path(__file__)), *args]
    try:
        return fn()
    finally:
        sys.argv = keep

READ_HOST_V0116 = HERE / "VRN_SystemManager_v0108.py"      # v0109 _facade() 的本體:read 的真正實作在它下面


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    why = verb_problem_v0116(args)
    if why:
        print(f"[拒跑] {TAG}:{why}")
        return 2
    if args[:1] == ["read"]:
        host = _load_v0116(READ_HOST_V0116, "vrn_read_host_for_v0116")
        return _with_argv_v0116(args, host.main)
    if (not args or args[0] == "status") and "--json" not in args:
        print(f"[{_STEM}] 尾版 {TAG}(下行抬頭的版號是狀態讀器本體的版,不是尾版)")
    return _with_argv_v0116(args, lambda: PRIOR.main(args))


def selftest() -> int:
    prior_rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(未知動詞拒跑 · read logic 歸位 · 抬頭註明尾版)===")
    keep = os.environ.get("VIA_FROM_VCGC")
    os.environ["VIA_FROM_VCGC"] = "YES"
    calls, real = [], PRIOR.main
    try:
        PRIOR.main = lambda a=None: calls.append((list(a or []), list(sys.argv[1:]))) or 0
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            bad = [main(a) for a in (["foo"], ["stauts"], ["redd", "logic"], ["engin", "params"])]
            good = [main(a) for a in ([], ["status"], ["--json"], ["logic"], ["engine", "list"], ["frame"], ["outputs"])]
        out = buf.getvalue()
        chk("① 未知動詞 4 種:rc 2 · 不進前版 · 印 [拒跑] 與真動詞表", set(bad) == {2} and out.count("[拒跑]") == 4
            and all(v in out for v in ("params", "prep", "logic", "frame")) and len(calls) == len(good), (bad, len(calls)))
        chk("② 已知動詞 / 旗標 7 種放行;前版收到的 sys.argv = 本次參數", set(good) == {0}
            and all(c[0] == c[1] for c in calls), calls[:3])
        chk("③ 看狀態印尾版抬頭(--json 不印,不汙染 JSON)", out.count(f"尾版 {TAG}") == 2, out.count(f"尾版 {TAG}"))
    finally:
        PRIOR.main = real
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_read = main(["read", "logic"])
        txt = buf.getvalue()
        card = json.loads(txt[txt.index("{"):]) if "{" in txt else {}
        chk("④ read logic → 邏輯域讀卡(ENG082 邏輯庫),不是 LogicRollup", "ENG113" not in str(card.get("door", ""))
            and "ExtractionLogic" in str(card.get("src", "")), (rc_read, card.get("src"), card.get("door")))
    finally:
        if keep is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = keep
    os.environ.pop("VIA_FROM_VCGC", None)
    with contextlib.redirect_stdout(io.StringIO()):
        deny = main(["foo"])
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("⑤ 未經 VCGC 仍先拒(閘在動詞判定之前)", deny == 2)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋在;不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) and prior_rc == 0 else 'FAIL'}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
