#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL149_VeritasCentralGovernanceConsole v0170 — 薄尾:省 Token 工具是 VCGC 第一步(啟用 · 實測 · 要求 AI 先用)· token 動詞

操作員 2026-09-29:「token saving tools registered. activate them and request ai to utilize them as the first step in vcgc.」
  ① 每個動作第一行:進門(VIA_FROM_VCGC=YES)之後、任何動詞之前,先跑 CGC_MDL226 尾版的第一步(省 Token:鎖上的全景 / NLP
     有沒有啟用、實測能不能用),印它的 ai_line——AI 從這一行知道先用 read → slice → digest。
     紅(沒啟用 / 鎖檔被改 / 實測不過)就停在這一步:不讀政策、不開子系統,印啟用短令,rc2。
     實錄:v0161 的步驟門只擋「會走到 v0161 的動詞」;tools / run / go / events / workflow / sdd 這些後來的動詞由
     v0163–v0169 直接接走,從來沒過步驟門——所以第一步只能放在最上層,每個動詞都先過。
  ② token 動詞:印整張省 Token 卡(ai_directive:第一步做什麼 · 指令原樣可貼 · 什麼時候不用);--json 印卡。事件照 v0168 記。
  ③ v0161 的步驟門(DOOR)改指 CGC_MDL226 尾版(不再字串釘 v0100);它原本寫死的「1 入口 · 2 省Token」那一行,
     換成新次序「1 省Token · 2 入口 · 3 加速器與網路」的實際燈號——同一個次序只有一種說法。
其餘照 v0169(thin tail;__getattr__ 轉接)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。零網路 · 不安裝。
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

import builtins
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("vcgc_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


STEPS_STEM = "CGC_MDL226_StepMatrix"
EVENTS = PRIOR.EVENTS                 # v0168 的事件夾(自測改指暫存夾)
OLD_STEP_LINE = "[步驟] 1 入口 · 2 省Token GREEN · 3 加速器與網路已接 · 政策與子系統在後"
_STEPS: dict = {}


def _steps_tail() -> Path | None:
    hits = sorted(HERE.glob(STEPS_STEM + "_v*.py"), key=_vnum)
    return hits[-1] if hits else None


def steps_module():
    """步驟矩陣尾版(第一步 = 省 Token)。不在回 None。"""
    if "m" not in _STEPS:
        p = _steps_tail()
        _STEPS["m"] = PRIOR._load(p, "steps_for_" + Path(__file__).stem) if p else None
    return _STEPS["m"]


def _v0161():
    for m in list(sys.modules.values()):
        if str(getattr(m, "__file__", "") or "").endswith(_STEM + "_v0161.py"):
            return m
    return None


def _v0161_print(*args, **kwargs):
    """v0161 寫死的舊次序那一行 → 新次序的實際燈號(步驟矩陣尾版剛算的那張卡)。其餘原樣。"""
    if args and args[0] == OLD_STEP_LINE:
        st = sys.modules.get("steps_for_console")
        if st is None or not getattr(st, "LAST", None):
            st = steps_module()
        if st is not None and hasattr(st, "step_line"):
            args = (st.step_line(getattr(st, "LAST", None) or None),) + args[1:]
    return builtins.print(*args, **kwargs)


def _patch_v0161() -> bool:
    m, tail = _v0161(), _steps_tail()
    if m is None or tail is None:
        return False
    m.DOOR = tail
    m.print = _v0161_print
    return True


PATCHED_V0161 = _patch_v0161()


def _event(verb: str, args: list, rc: int, t0: float) -> None:
    try:
        PRIOR.write_event({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "verb": verb,
                           "args": [str(a)[:80] for a in args[1:7]], "rc": rc, "outcome": PRIOR.outcome(rc),
                           "secs": round(time.time() - t0, 1), "head": PRIOR._head()[:12], "error": "",
                           "engine": Path(__file__).stem, "run": os.environ.get("VIA_HUB_RUN", ""),
                           "t0": round(t0, 3), "target": _STEM, "act": verb}, folder=EVENTS)
    except Exception:                                   # 事件寫不進去不擋動作(v0168 同一個規矩)
        pass


def first_step() -> dict | None:
    st = steps_module()
    return st.front() if st is not None else None


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        return PRIOR.main(argv)                          # 門照舊由前一版擋(DENY)
    t0 = time.time()
    card = first_step()
    if card is None:
        print(json.dumps({"step": 1, "id": "token", "lamp": "ABSENT", "why": "CGC_MDL226 步驟矩陣不在"}, ensure_ascii=False))
        return 2
    verb = args[0] if args else ""
    tok = card["token"]
    if verb == "token":
        if "--json" in args:
            print(json.dumps(dict(tok, ai_line=card["ai_line"], order=card["order"]), ensure_ascii=False, indent=1))
        else:
            print("\n".join(card["ai_directive"]))
            s = tok["smoke"]
            print(f"  實測:{' · '.join(k + ('✓' if v else '✗') for k, v in tok['tools'].items())}"
                  f"({'快取 ' + s['at'] if s['cached'] else '剛測 ' + str(s['secs']) + 's'})· 次序 {' → '.join(card['order'])}")
        rc = 0 if not tok["missing"] else 2
        _event("token", args, rc, t0)
        return rc
    print(card["ai_line"], file=sys.stderr if "--json" in args else sys.stdout)   # --json 的 stdout 保持純 JSON
    if tok["missing"]:
        print(json.dumps({"step": 1, "id": "token", "lamp": "RED", "missing": tok["missing"],
                          "activate_hint": tok["activate_hint"], "next": "不讀政策、不開子系統;先修第一步"},
                         ensure_ascii=False, indent=1))
        return 2
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    import contextlib
    import io
    import tempfile
    st = steps_module()
    order = [r[1] for r in getattr(st, "ORDER", ())]
    chk("① 步驟矩陣尾版的第一步是 token(省 Token),v0100 的八步一步不少",
        st is not None and order[:1] == ["token"] and len(order) == 8, " → ".join(order))
    m161 = _v0161()
    chk("② v0161 的步驟門改指步驟矩陣尾版(不再字串釘 v0100);寫死的舊次序那一行改印新次序",
        PATCHED_V0161 and m161 is not None and Path(m161.DOOR) == _steps_tail() and m161.print is _v0161_print)
    global EVENTS
    saved_env = os.environ.get("VIA_FROM_VCGC")
    saved_events = EVENTS
    try:
        os.environ.pop("VIA_FROM_VCGC", None)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_deny = main(["token"])
        chk("③ 門:沒經 via-vcgc 直呼 token → 前一版照擋(DENY rc2),第一步不跑", rc_deny == 2 and "DENY" in buf.getvalue())
        os.environ["VIA_FROM_VCGC"] = "YES"
        with tempfile.TemporaryDirectory() as td:
            EVENTS = Path(td) / "events"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc_tok = main(["token"])
            out = buf.getvalue()
            card = first_step()
            ev = list(EVENTS.glob("EVENTS_*.jsonl"))
            ev_ok = bool(ev) and '"verb": "token"' in ev[0].read_text(encoding="utf-8")
        chk("④ token 動詞:印整張 AI 指令卡(鎖上的全景路徑 · read/slice/digest/--if-etag/pack/--brief · 什麼時候不用)· rc0 · 事件照記",
            rc_tok == 0 and card["token"]["pinned"]["token"] in out and all(
                v in out for v in (" read ", " slice ", " digest ", "--if-etag", " pack ", "--brief", "不用的時候")) and ev_ok,
            f"rc={rc_tok} · 事件 {'有' if ev_ok else '無'}")
        chk("⑤ 每個動作的第一行 = 省 Token 短版(ai_line),以「[第一步 · 省Token] 已啟用 6/6」開頭",
            card["ai_line"].startswith("[第一步 · 省Token] 已啟用 6/6") and card["front_pass"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _v0161_print(OLD_STEP_LINE)
            _v0161_print("其他行照印")
        lines = buf.getvalue().splitlines()
        chk("⑥ v0161 舊次序那一行換成新次序的實際燈號;其他行一字不動",
            len(lines) == 2 and lines[0].startswith("[步驟] 1 省Token GREEN · 2 入口 GREEN") and lines[1] == "其他行照印",
            lines[0][:60] if lines else "")
        red = dict(card, token=dict(card["token"], missing=["read"], activate_hint=["via-vcgc tools activate token X --apply"]),
                   ai_line="[第一步 · 省Token] 紅")
        called = []
        real_first, real_prior_main = globals()["first_step"], PRIOR.main
        globals()["first_step"] = lambda: red
        PRIOR.main = lambda argv=None: called.append(argv) or 0
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc_red = main(["status"])
        finally:
            globals()["first_step"], PRIOR.main = real_first, real_prior_main
        chk("⑦ 負控:第一步紅 → 停在第一步(rc2)、不呼叫任何後面的動詞(政策 / 子系統都不開)、印啟用短令",
            rc_red == 2 and not called and "tools activate token" in buf.getvalue())
    finally:
        EVENTS = saved_events
        if saved_env is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = saved_env
    passed = all(ok)
    print(f"  {Path(__file__).stem} selftest {sum(ok)}/{len(ok)} {'PASS' if passed else 'FAIL'}")
    if not passed:
        return 1
    return PRIOR.selftest()                              # 串前一版(各薄尾同一個規矩:格子只跑尾版,前版的檢不能掉)


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
