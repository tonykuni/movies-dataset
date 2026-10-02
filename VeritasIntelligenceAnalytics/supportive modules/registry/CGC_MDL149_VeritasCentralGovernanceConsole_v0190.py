#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0190 — 薄尾:每日進度交接進 VCGC 主控台 —— 頂層動詞 `daily` · closeout ⑪ 自動寫清單並提交

操作員(2026-10-02,VCGC-REQ127):「IMPLEMENT IT TO VCGC MAIN.」—— PR #435 的十點每日交接引擎(CGC_MDL140 v0104)
原本只能 `via-vcgc handoff daily` 叫到;本版把它接成 VCGC 主控台的正式功能(正主不變,VCGC 只轉呼叫,L30):
  ① 頂層動詞 `daily [參數]` = `handoff daily [參數]`(經 v0186 執行監控 · v0177 handoff 轉正主);help 多一行。
  ② closeout 收尾 ⑪ 每日交接:①–⑨ 收尾 + ⑩ 全綠閘之後跑一次(子行程走 v0184 的 sub,完整輸出落本輪 closeout 夾):
     沒帶 --apply = `daily --dry-run`(只算只印);--apply = 寫 docs/handoff/daily 清單 + 只增帳,用收尾既有的 commit 提交;
     --push 再推一次(收尾 ⑧ 推在 ⑪ 之前;不強推)。清單燈是報告不改收尾 rc;契約不過 / 沒有判決行 = 收尾 rc 1(黃不是綠)。
     收尾在 ①–⑨ 停下(rc 1)不跑 ⑪;串測中(VIA_VCGC_TEST_ACTIVE=1)略過(V-daily 站另測,防遞迴)。
  ③ 改裝點:v0186 main 以模組全域 `closeout` 派送 → 把 v0186 的 closeout 換成本版;前版檔一字不動。
其餘照 v0189。不碰 TA-Lib;不代設同意閘;不裝套件。
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

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


DAILY_LINE = ("daily [--dry-run] [--data 夾] [--next 任務] [--verify] [--replay 日]  每日進度交接十點 → "
              "docs/handoff/daily/panorama.manifest.json(= handoff daily;closeout ⑪ 收尾自動跑,--apply 寫並提交)")
DAILY_DOC = "docs/handoff/daily"


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _owner(name: str):
    """鏈上第一個定義 name 的模組(新 → 舊);找不到 = None。"""
    return next((m for m in _chain() if name in vars(m)), None)


# ---------------------------------------------------------------- help(同 v0189 的掛法:目前生效入口 = 本版)
_PREV_CATALOG_V0190 = PRIOR.help_catalog
_PREV_SHOW_V0190 = vars(PRIOR).get("_show_help_v0189")
_PATCHED_V0190: list = []


def help_catalog():
    card = _PREV_CATALOG_V0190()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, daily=DAILY_LINE)
    return card


def _show_help_v0190():
    if _PREV_SHOW_V0190 is not None:
        _PREV_SHOW_V0190()
    print("  " + DAILY_LINE)


# ---------------------------------------------------------------- closeout ⑪ 每日交接
_CLOSEOUT_HOST = _owner("closeout")             # v0186:main 以它的模組全域 closeout 派送
_CLOSEOUT_PREV = vars(_CLOSEOUT_HOST)["closeout"]
TEST_ACTIVE = getattr(PRIOR, "TEST_ACTIVE", "VIA_VCGC_TEST_ACTIVE")


def _sub(argv: list, log: Path, timeout: int = 900) -> tuple:
    return PRIOR.sub(argv, log, timeout=timeout)    # v0184:子行程跑主控台 · 完整輸出落檔


def _commit(message: str) -> str:
    return PRIOR.commit(message)                    # v0184:只提交收尾兩夾;沒變 = clean


def _push() -> tuple:
    return PRIOR.git("push", "origin", "HEAD", timeout=600)


def _run_dir(since: float) -> Path:
    """本輪 closeout 的記錄夾(v0184 co-YYYYmmdd-HHMMSS);找不到本輪的 = OUT/daily(不混進別輪)。"""
    out = Path(PRIOR.OUT)
    runs = sorted((p for p in out.glob("co-*") if p.is_dir() and p.stat().st_mtime >= since - 1), key=lambda p: p.name)
    return runs[-1] if runs else out / "daily"


def daily_verdict(text: str):
    """daily 的機讀判決行 {"daily": …};沒有 = None(誠實,不從文字猜)。"""
    for ln in reversed(text.splitlines()):
        ln = ln.strip()
        if ln.startswith('{"daily"'):
            with contextlib.suppress(ValueError):
                return json.loads(ln)
    return None


def closeout(args: list) -> int:
    t0 = time.time()
    rc = _CLOSEOUT_PREV(args)
    if rc == 1:
        return rc
    if os.environ.get(TEST_ACTIVE) == "1":
        print("  ⑪  每日交接 略過:串測中(防遞迴;V-daily 站另測)")
        return rc
    apply, push = "--apply" in args, "--push" in args
    log = _run_dir(t0) / "11_daily.log"
    print("  ⑪  每日交接(十點 → panorama.manifest.json)", flush=True)
    t1 = time.time()
    drc, text = _sub(["handoff", "daily"] + ([] if apply else ["--dry-run"]), log)
    v = daily_verdict(text)
    secs = f"{time.time() - t1:5.1f}s"
    if v is None:
        print(f"  ⑪  每日交接 RED {secs} · rc {drc} · 沒有判決行(看 {log})")
        return 1
    head = (f"  ⑪  每日交接 {str(v.get('lamp')):<6} {secs} · 清單 {v.get('manifest_sha16')} · 契約 {v.get('contract')}"
            f" · {' '.join(k + ':' + str(x)[0] for k, x in (v.get('lamps') or {}).items())}")
    if v.get("contract") != "PASS":
        print(head + f" · 契約不過,不寫(看 {log})")
        return 1
    if not apply:
        print(head + " · 乾跑(--apply 才寫並提交)")
        return rc
    if not v.get("written"):
        print(head + f" · 沒寫入(看 {log})")
        return 1
    state = _commit(f"vcgc closeout: 每日交接清單 · {v.get('day')} · {v.get('lamp')} · {v.get('manifest_sha16')}")
    pushed = ""
    if push and state == "committed":
        prc, out = _push()
        pushed = " · 已推" if prc == 0 else f" · 推送失敗 rc {prc}:{out.strip()[-120:]}"
    print(head + f" · {state}{pushed}")
    return 1 if state.startswith("commit 失敗") or pushed.startswith(" · 推送失敗") else rc


# ---------------------------------------------------------------- 改裝
def _patch(on: bool = True) -> None:
    if on:
        for _m in _chain():
            if vars(_m).get("help_catalog") is _PREV_CATALOG_V0190:
                _m.help_catalog = help_catalog
                _PATCHED_V0190.append((_m, "help_catalog", _PREV_CATALOG_V0190))
            if _PREV_SHOW_V0190 is not None and vars(_m).get("show_current_help") is _PREV_SHOW_V0190:
                _m.show_current_help = _show_help_v0190
                _PATCHED_V0190.append((_m, "show_current_help", _PREV_SHOW_V0190))
        if vars(_CLOSEOUT_HOST).get("closeout") is _CLOSEOUT_PREV:
            _CLOSEOUT_HOST.closeout = closeout
            _PATCHED_V0190.append((_CLOSEOUT_HOST, "closeout", _CLOSEOUT_PREV))
    else:
        for _m, attr, orig in _PATCHED_V0190:
            setattr(_m, attr, orig)
        _PATCHED_V0190.clear()


_patch(True)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest-tail"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
            return 2
        return selftest_tail()
    if args[:1] == ["daily"]:
        return PRIOR.main(["handoff", "daily", *args[1:]])
    return PRIOR.main(argv)


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    # 前版鏈自測先跑(交接案 entry 看鏈底的 [交接入口] fail=0);照 v0189 的作法把前版 __file__ 暫指本檔,跑完還原。
    _patch(False)
    keep_file = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        prior_rc = PRIOR.selftest()
    finally:
        PRIOR.__dict__["__file__"] = keep_file
        _patch(True)
    tail_rc = selftest_tail()
    return 0 if prior_rc == 0 and tail_rc == 0 else 1


def selftest_tail() -> int:
    print("=== VCGC v0190 · 薄尾自測(每日交接進主控台:daily 動詞 · closeout ⑪)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:200]) if note and not cond else ''}")

    seen = []
    keep_main = PRIOR.main
    PRIOR.main = lambda a=None: seen.append(list(a or [])) or 0
    try:
        rc = main(["daily", "--dry-run", "--data", "x/{day}"])
    finally:
        PRIOR.main = keep_main
    chk("① daily 動詞 = handoff daily(參數原樣轉)", rc == 0 and seen == [["handoff", "daily", "--dry-run", "--data", "x/{day}"]], seen)
    chk("② closeout 改裝在 v0186(main 的派送點)· 前版原函數留著轉呼叫",
        vars(_CLOSEOUT_HOST).get("closeout") is closeout and _CLOSEOUT_PREV is not closeout
        and Path(_CLOSEOUT_HOST.__file__).stem.endswith("v0186"), Path(_CLOSEOUT_HOST.__file__).name)

    g = globals()
    keep = {k: g[k] for k in ("_CLOSEOUT_PREV", "_sub", "_commit", "_push", "_run_dir")}
    calls = []
    good = '{"daily": "v0104", "day": "2026-10-02", "lamp": "YELLOW", "manifest_sha16": "abc", "lamps": {"git": "GREEN"}, "written": %s, "contract": "%s"}'

    def scenario(prev_rc, args, out=None, env_test=False, commit_state="committed", push_rc=0):
        calls.clear()
        g["_CLOSEOUT_PREV"] = lambda a: calls.append(("prev", list(a))) or prev_rc
        g["_sub"] = lambda argv, log, timeout=900: calls.append(("sub", list(argv))) or (0, out if out is not None else good % (
            "true" if "--dry-run" not in argv else "false", "PASS"))
        g["_commit"] = lambda msg: calls.append(("commit", msg)) or commit_state
        g["_push"] = lambda: calls.append(("push",)) or (push_rc, "")
        g["_run_dir"] = lambda since: Path(tempfile.gettempdir()) / "vcgc_v0190_selftest"
        keep_env = os.environ.get(TEST_ACTIVE)
        if env_test:
            os.environ[TEST_ACTIVE] = "1"
        else:
            os.environ.pop(TEST_ACTIVE, None)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                got = closeout(list(args))
        finally:
            if keep_env is None:
                os.environ.pop(TEST_ACTIVE, None)
            else:
                os.environ[TEST_ACTIVE] = keep_env
        return got, [c[0] for c in calls], list(calls), buf.getvalue()

    try:
        got, kinds, _, _ = scenario(1, ["--apply"])
        chk("③ 收尾停下(rc 1)→ 不跑 ⑪", got == 1 and kinds == ["prev"], kinds)
        got, kinds, _, txt = scenario(2, ["--apply"], env_test=True)
        chk("④ 串測中 → ⑪ 略過(防遞迴)", got == 2 and kinds == ["prev"] and "⑪  每日交接 略過" in txt, kinds)
        got, kinds, calls_, txt = scenario(2, [])
        chk("⑤ 沒帶 --apply → daily --dry-run · 不提交 · 收尾 rc 原樣",
            got == 2 and kinds == ["prev", "sub"] and calls_[1][1] == ["handoff", "daily", "--dry-run"] and "乾跑" in txt, calls_)
        got, kinds, calls_, txt = scenario(0, ["--apply"])
        chk("⑥ --apply → daily 寫 · 收尾 commit 提交一次 · 不推",
            got == 0 and kinds == ["prev", "sub", "commit"] and calls_[1][1] == ["handoff", "daily"]
            and "每日交接清單 · 2026-10-02 · YELLOW · abc" in calls_[2][1], calls_)
        got, kinds, _, txt = scenario(0, ["--apply", "--push"])
        chk("⑦ --apply --push → 提交後再推一次(⑧ 推在 ⑪ 之前)", got == 0 and kinds == ["prev", "sub", "commit", "push"] and "已推" in txt, kinds)
        got, kinds, _, _ = scenario(0, ["--apply", "--push"], commit_state="clean")
        chk("⑧ 沒變(clean)→ 不推", got == 0 and kinds == ["prev", "sub", "commit"], kinds)
        got, kinds, _, _ = scenario(0, ["--apply"], out=good % ("false", "FAIL"))
        chk("⑨ 契約不過 → 不提交 · 收尾 rc 1(黃不是綠)", got == 1 and kinds == ["prev", "sub"], kinds)
        got, kinds, _, txt = scenario(0, ["--apply"], out="Traceback (most recent call last):\n  boom\n")
        chk("⑩ 沒有判決行(daily 炸)→ 收尾 rc 1 · 不提交", got == 1 and kinds == ["prev", "sub"] and "沒有判決行" in txt, kinds)
        got, kinds, _, txt = scenario(0, ["--apply", "--push"], push_rc=1)
        chk("⑪ 推送失敗 → 收尾 rc 1 照實報", got == 1 and "推送失敗" in txt, txt[-120:])
    finally:
        g.update(keep)
    chk("⑫ 判決行解析:取最後一行 {\"daily\"…};沒有 = None",
        daily_verdict('x\n{"daily": "v0104", "lamp": "RED"}\ny\n') == {"daily": "v0104", "lamp": "RED"} and daily_verdict("no") is None)
    card = help_catalog()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _show_help_v0190()
    chk("⑬ help 目前生效入口 = 本版 · 前版 = v0189 · 多一行 daily", card.get("entry") == Path(__file__).name
        and card.get("previous") == PRIOR_PATH.name and card.get("daily") == DAILY_LINE and DAILY_LINE in buf.getvalue(),
        (card.get("entry"), card.get("previous")))
    owners = {n: Path(_owner(n).__file__).stem[-5:] if _owner(n) else None for n in ("sub", "commit", "git", "OUT")}
    chk("⑭ 收尾工具沿用前版正主(sub · commit · git · OUT 都在 v0184,本版不另寫子行程 / 提交)",
        all(v == "v0184" for v in owners.values()), owners)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑮ 加速器橋 · 網路橋在;不碰 TA-Lib;不強推",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and ("--" + "force") not in text)
    if os.environ.get("VIA_FROM_VCGC") == "YES":
        with tempfile.TemporaryDirectory() as tmp:
            rc_real, out = _sub(["handoff", "daily", "--dry-run", "--no-audit"], Path(tmp) / "daily.log", timeout=600)
        v = daily_verdict(out)
        chk("⑯ 實跑:handoff daily --dry-run --no-audit 經 VCGC 子行程 → 判決行在 · 契約 PASS · 沒寫",
            v is not None and v.get("contract") == "PASS" and v.get("written") is False, (rc_real, out[-200:]))
    print(f"  [計] VCGC v0190 每日交接進主控台 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
